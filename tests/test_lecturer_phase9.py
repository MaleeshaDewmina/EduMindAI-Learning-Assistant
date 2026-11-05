"""Phase 9 tests: role isolation, consent and read-only reporting."""
import re
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.user import User
from app.models.lecturer_access_grant import LecturerAccessGrant
from app.models.study_task import StudyTask
from app.models.activity_log import UserActivityLog
from app.models.motivation_score import MotivationScore
from app.models.chat_message import ChatMessage
from app.models.evaluation_response import EvaluationResponse

PASSWORD = 'SafeTestPassword123'


def csrf(client, path):
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code)
    match = re.search(rb'name="csrf_token"\s+value="([^"]+)"', response.data)
    assert match, path
    return match.group(1).decode()


def login(client, email):
    result = client.post('/auth/login', data={'csrf_token': csrf(client, '/auth/login'),
                                             'email': email, 'password': PASSWORD}, follow_redirects=True)
    assert result.status_code == 200
    return result


def logout(client, path='/lecturer/sharing'):
    return client.post('/auth/logout', data={'csrf_token': csrf(client, path)}, follow_redirects=True)


def seed(app):
    with app.app_context():
        for email, role in [('one@example.test', 'student'), ('two@example.test', 'student'),
                            ('lecturer@example.test', 'lecturer'),
                            ('otherlecturer@example.test', 'lecturer')]:
            db.session.add(User(full_name=email.split('@')[0], email=email, role=role,
                                password_hash=generate_password_hash(PASSWORD)))
        db.session.commit()
        return {u.email: u.user_id for u in User.query.all()}


def grant(client, email='lecturer@example.test'):
    return client.post('/lecturer/sharing/grant', data={'csrf_token': csrf(client, '/lecturer/sharing'),
                                                       'lecturer_email': email}, follow_redirects=True)


def test_public_register_cannot_choose_lecturer(client, app):
    result = client.post('/auth/register', data={
        'csrf_token': csrf(client, '/auth/register'), 'full_name': 'S',
        'email': 'new@example.test', 'password': PASSWORD, 'confirm_password': PASSWORD,
        'age': '21', 'role': 'lecturer'}, follow_redirects=True)
    assert result.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email='new@example.test').one().role == 'student'


def test_lecturer_login_and_student_route_separation(client, app):
    seed(app)
    assert b'Lecturer Dashboard' in login(client, 'lecturer@example.test').data
    for path in ['/dashboard/', '/planner/', '/progress/', '/chatbot/', '/feedback/', '/evaluation/']:
        assert client.get(path).status_code == 302


def test_student_cannot_view_lecturer_area(client, app):
    ids = seed(app)
    login(client, 'one@example.test')
    assert client.get('/lecturer/').status_code == 403
    assert client.get('/lecturer/students/' + str(ids['one@example.test'])).status_code == 403


def test_only_existing_lecturer_can_receive_share(client, app):
    seed(app)
    login(client, 'one@example.test')
    assert b'No authorised lecturer account' in grant(client, 'two@example.test').data
    assert b'access granted' in grant(client).data.lower()
    grant(client)
    with app.app_context():
        assert LecturerAccessGrant.query.count() == 1


def test_lecturer_sees_only_shared_student(client, app):
    ids = seed(app)
    login(client, 'one@example.test')
    grant(client)
    logout(client)
    login(client, 'lecturer@example.test')
    assert b'one@example.test' in client.get('/lecturer/').data
    assert b'two@example.test' not in client.get('/lecturer/').data
    assert client.get(f'/lecturer/students/{ids["one@example.test"]}').status_code == 200
    assert client.get(f'/lecturer/students/{ids["two@example.test"]}').status_code == 404


def test_different_lecturer_not_authorised(client, app):
    ids = seed(app)
    login(client, 'one@example.test')
    grant(client)
    logout(client)
    login(client, 'otherlecturer@example.test')
    assert b'one@example.test' not in client.get('/lecturer/').data
    assert client.get(f'/lecturer/students/{ids["one@example.test"]}').status_code == 404


def test_student_can_revoke_and_access_stops_immediately(client, app):
    ids = seed(app)
    login(client, 'one@example.test')
    grant(client)
    with app.app_context():
        gid = LecturerAccessGrant.query.one().grant_id
    result = client.post(f'/lecturer/sharing/revoke/{gid}',
                         data={'csrf_token': csrf(client, '/lecturer/sharing')}, follow_redirects=True)
    assert b'access revoked' in result.data.lower()
    logout(client)
    login(client, 'lecturer@example.test')
    assert client.get(f'/lecturer/students/{ids["one@example.test"]}').status_code == 404


def test_grant_and_revoke_require_post_with_csrf(client, app):
    seed(app)
    login(client, 'one@example.test')
    assert client.get('/lecturer/sharing/grant').status_code == 405
    assert client.post('/lecturer/sharing/grant', data={'lecturer_email': 'lecturer@example.test'}).status_code == 400
    grant(client)
    with app.app_context():
        gid = LecturerAccessGrant.query.one().grant_id
    assert client.get(f'/lecturer/sharing/revoke/{gid}').status_code == 405
    assert client.post(f'/lecturer/sharing/revoke/{gid}').status_code == 400
    with app.app_context():
        assert LecturerAccessGrant.query.count() == 1


def test_student_cannot_revoke_other_student_grant(client, app):
    seed(app)
    login(client, 'one@example.test')
    grant(client)
    with app.app_context():
        gid = LecturerAccessGrant.query.one().grant_id
    logout(client)
    login(client, 'two@example.test')
    assert client.post(f'/lecturer/sharing/revoke/{gid}',
                       data={'csrf_token': csrf(client, '/lecturer/sharing')}).status_code == 404


def test_report_excludes_chat_and_comments(client, app):
    ids = seed(app)
    with app.app_context():
        uid = ids['one@example.test']
        db.session.add(ChatMessage(user_id=uid, user_message='PRIVATE CHAT MARKER',
                                   ai_response='SECRET ANSWER', message_type='General'))
        db.session.add(EvaluationResponse(user_id=uid, evaluation_type='PreTest',
            motivation_rating=1, confidence_rating=2, growth_mindset_rating=3,
            usability_rating=4, feedback_comments='PRIVATE COMMENT MARKER'))
        db.session.commit()
    login(client, 'one@example.test')
    grant(client)
    logout(client)
    login(client, 'lecturer@example.test')
    result = client.get(f'/lecturer/students/{ids["one@example.test"]}')
    assert result.status_code == 200
    assert b'PRIVATE CHAT MARKER' not in result.data
    assert b'SECRET ANSWER' not in result.data
    assert b'PRIVATE COMMENT MARKER' not in result.data


def test_report_does_not_write_metrics_or_mutate_task_status(client, app):
    """Lecturer views must not change saved task status, activity, or scores.

    Authenticate and grant access BEFORE creating the overdue Pending task:
    the normal student-login redirect visits the student dashboard, which
    intentionally updates overdue statuses and stores motivation-score history.
    """
    ids = seed(app)
    uid = ids['one@example.test']

    # Establish authorisation first; these student requests may legitimately
    # run analytics and modify student-side history.
    login(client, 'one@example.test')
    grant(client)
    logout(client)
    login(client, 'lecturer@example.test')

    # Create the specific test data after student requests have finished.
    with app.app_context():
        task = StudyTask(
            user_id=uid,
            title='Past deadline',
            deadline=datetime.utcnow() - timedelta(days=2),
            status='Pending',
        )
        db.session.add(task)
        db.session.add(UserActivityLog(
            user_id=uid,
            activity_name='Test',
            created_at=datetime.utcnow(),
        ))
        db.session.commit()
        task_id = task.task_id
        scores_before = MotivationScore.query.filter_by(user_id=uid).count()
        activities_before = UserActivityLog.query.filter_by(user_id=uid).count()

    # Both lecturer routes must report data without writing to student records.
    assert client.get('/lecturer/').status_code == 200
    assert client.get(f'/lecturer/students/{uid}').status_code == 200

    with app.app_context():
        db.session.expire_all()
        saved_task = db.session.get(StudyTask, task_id)
        assert saved_task is not None
        assert saved_task.status == 'Pending'
        assert MotivationScore.query.filter_by(user_id=uid).count() == scores_before
        assert UserActivityLog.query.filter_by(user_id=uid).count() == activities_before


def test_redesigned_dashboard_empty_state(client, app):
    seed(app)
    login(client, 'lecturer@example.test')
    response = client.get('/lecturer/')
    assert response.status_code == 200
    assert b'No shared student reports yet' in response.data
    assert b'A clearer view of' in response.data
    assert b'0 shared' in response.data


def test_redesigned_dashboard_aggregates_only_authorised_students(client, app):
    ids = seed(app)
    login(client, 'one@example.test')
    grant(client)
    logout(client)
    login(client, 'lecturer@example.test')

    with app.app_context():
        db.session.add(StudyTask(
            user_id=ids['one@example.test'], title='Complete lesson',
            deadline=datetime.utcnow() + timedelta(days=3), status='Completed',
        ))
        db.session.add(StudyTask(
            user_id=ids['two@example.test'], title='Unshared private task',
            deadline=datetime.utcnow() - timedelta(days=3), status='Overdue',
        ))
        db.session.add(UserActivityLog(
            user_id=ids['one@example.test'], activity_name='Study',
            created_at=datetime.utcnow(),
        ))
        db.session.commit()
    response = client.get('/lecturer/')
    assert response.status_code == 200
    assert b'one@example.test' in response.data
    assert b'two@example.test' not in response.data
    assert b'Unshared private task' not in response.data
    assert b'Task completion' in response.data
    assert b'100.0%' in response.data
    assert b'1 shared' in response.data
    assert b'View full report' in response.data
    assert b'Active this week' in response.data


def test_redesigned_dashboard_shows_email_permission_only_when_granted(client, app):
    seed(app)
    login(client, 'one@example.test')
    grant(client)
    with app.app_context():
        gid = LecturerAccessGrant.query.one().grant_id
    logout(client)
    login(client, 'lecturer@example.test')
    first = client.get('/lecturer/')
    assert b'Dashboard access only' in first.data
    assert b'Email reports allowed' not in first.data
    logout(client, '/lecturer/')
    login(client, 'one@example.test')
    response = client.post(f'/lecturer/sharing/email-permission/{gid}', data={
        'csrf_token': csrf(client, '/lecturer/sharing'),
        'email_allowed': 'on'
    }, follow_redirects=True)
    assert response.status_code == 200
    logout(client)
    login(client, 'lecturer@example.test')
    second = client.get('/lecturer/')
    assert b'Email reports allowed' in second.data
