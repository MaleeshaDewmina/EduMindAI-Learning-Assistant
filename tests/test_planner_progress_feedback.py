"""Phase 3: planner validation, ownership, deadlines, feedback and CSRF."""
from datetime import datetime, timedelta

from app.extensions import db
from app.models.study_task import StudyTask
from app.models.progress_log import ProgressLog
from app.models.feedback import Feedback
from app.models.user import User
from app.services.analytics_service import get_task_metrics
from app.services.recommendation_service import generate_recommendation
from tests.test_auth_security import csrf, register, login


def due(days=2):
    return (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M")


def create_task(client, title="Read an article", **kwargs):
    data = {
        "csrf_token": csrf(client, "/planner/"),
        "title": title,
        "deadline": due(),
        "priority": "Medium",
    }
    data.update(kwargs)
    return client.post("/planner/create", data=data, follow_redirects=True)


def post_form(client, path, **kwargs):
    return client.post(path, data={"csrf_token": csrf(client, "/planner/"), **kwargs}, follow_redirects=True)


def test_task_lifecycle_and_no_duplicate_completion(client, app):
    register(client)
    login(client)
    response = create_task(client)
    assert b"Study task created successfully" in response.data
    with app.app_context():
        task = StudyTask.query.filter_by(title="Read an article").one()
        task_id = task.task_id
        assert task.status == "Pending"

    response = post_form(client, f"/planner/complete/{task_id}")
    assert b"Task marked as completed" in response.data
    response = post_form(client, f"/planner/complete/{task_id}")
    assert b"already completed" in response.data
    with app.app_context():
        assert StudyTask.query.get(task_id).status == "Completed"
        assert ProgressLog.query.filter_by(task_id=task_id, activity_type="Task Completed").count() == 1
        assert get_task_metrics(StudyTask.query.get(task_id).user_id)["completion_rate"] == 100


def test_invalid_priority_and_long_title_rejected(client, app):
    register(client)
    login(client)
    bad_priority = create_task(client, title="Unsafe", priority="Critical")
    assert b"Select a valid task priority" in bad_priority.data
    bad_title = create_task(client, title="A" * 151)
    assert b"Task title must contain 1 to 150 characters" in bad_title.data
    with app.app_context():
        assert StudyTask.query.count() == 0


def test_editing_overdue_task_to_future_makes_pending(client, app):
    register(client)
    login(client)
    create_task(client, title="Old deadline", deadline=due(-2))
    with app.app_context():
        task = StudyTask.query.filter_by(title="Old deadline").one()
        task_id = task.task_id
        assert task.status == "Overdue"
    r = post_form(client, f"/planner/edit/{task_id}", title="Old deadline", priority="High", status="Pending", deadline=due(3))
    assert b"Study task updated successfully" in r.data
    with app.app_context():
        task = StudyTask.query.filter_by(task_id=task_id).one()
        assert task.status == "Pending"
        assert task.priority == "High"


def test_invalid_edit_status_does_not_persist(client, app):
    register(client)
    login(client)
    create_task(client)
    with app.app_context():
        task_id = StudyTask.query.first().task_id
    r = post_form(client, f"/planner/edit/{task_id}", title="Tampered", priority="Medium", status="Admin", deadline=due())
    assert b"Choose Pending or Completed" in r.data
    with app.app_context():
        assert StudyTask.query.first().title != "Tampered"


def test_task_ownership_enforced_for_edit_complete_delete(client, app):
    register(client, email="a@example.com")
    login(client, email="a@example.com")
    create_task(client, title="Student A only")
    with app.app_context():
        task_id = StudyTask.query.first().task_id
    post_form(client, "/auth/logout")
    register(client, email="b@example.com")
    login(client, email="b@example.com")
    assert client.get(f"/planner/edit/{task_id}").status_code == 404
    token = csrf(client, "/planner/")
    for url in (f"/planner/complete/{task_id}", f"/planner/delete/{task_id}"):
        response = client.post(url, data={"csrf_token": token})
        assert response.status_code == 404
    with app.app_context():
        assert StudyTask.query.filter_by(task_id=task_id).one().title == "Student A only"


def test_feedback_generation_requires_post_and_csrf(client, app):
    register(client)
    login(client)
    assert client.get("/feedback/generate").status_code == 405
    assert client.post("/feedback/generate").status_code == 400
    feedback_page = client.get("/feedback/")
    assert b'action="/feedback/generate"' in feedback_page.data
    token = csrf(client, "/feedback/")
    response = client.post("/feedback/generate", data={"csrf_token": token}, follow_redirects=True)
    assert b"Personalized feedback generated successfully" in response.data
    with app.app_context():
        assert Feedback.query.count() == 1
        assert Feedback.query.first().feedback_type == "GettingStarted"


def test_recommendation_does_not_misreport_all_completed_or_no_tasks():
    zero = {"total_tasks": 0, "completed_tasks": 0, "pending_tasks": 0, "overdue_tasks": 0, "completion_rate": 0}
    complete = {"total_tasks": 1, "completed_tasks": 1, "pending_tasks": 0, "overdue_tasks": 0, "completion_rate": 100}
    scores = {"engagement_score": 0, "consistency_score": 0, "overall_motivation_score": 50}
    assert generate_recommendation(zero, scores)["feedback_type"] == "GettingStarted"
    finished = generate_recommendation(complete, scores)
    assert "completed" in finished["message"].lower()
    assert "few recorded" not in finished["message"].lower()
