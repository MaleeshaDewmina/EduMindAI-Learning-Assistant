"""Phase 10 regression tests use only in-memory SQLite and intercepted mail."""
import re
from datetime import datetime, timedelta
from urllib.parse import urlsplit

from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from app.models.user import User
from app.models.lecturer_access_grant import LecturerAccessGrant
from app.models.email_action_event import EmailActionEvent


PASSWORD = "SafeTestPassword123"


def csrf(client, url):
    response = client.get(url)
    assert response.status_code == 200, (url, response.status_code)
    match = re.search(rb'name="csrf_token"\s+value="([^"]+)"', response.data)
    assert match, url
    return match.group(1).decode()


def register(client, email="student@example.test"):
    return client.post("/auth/register", data={
        "csrf_token": csrf(client, "/auth/register"),
        "email": email, "full_name": "Student Example",
        "password": PASSWORD, "confirm_password": PASSWORD,
        "age": "21"
    }, follow_redirects=True)


def login(client, email="student@example.test", password=PASSWORD):
    return client.post("/auth/login", data={
        "csrf_token": csrf(client, "/auth/login"),
        "email": email, "password": password
    }, follow_redirects=True)


def logout(client):
    return client.post("/auth/logout", data={
        "csrf_token": csrf(client, "/progress/")
    }, follow_redirects=True)


def forgot(client, email):
    return client.post("/auth/forgot-password", data={
        "csrf_token": csrf(client, "/auth/forgot-password"),
        "email": email
    }, follow_redirects=True)


def reset_path(app):
    body = app.extensions["edumind_test_outbox"][-1]["body"]
    url = re.search(r'https?://[^\s]+', body).group(0)
    return urlsplit(url).path


def test_show_password_controls_and_forgot_link(client):
    login_page = client.get("/auth/login")
    assert b"data-toggle-password" in login_page.data
    assert b"Forgot password?" in login_page.data
    assert b"/auth/forgot-password" in login_page.data
    assert b"data-toggle-password" in client.get("/auth/register").data


def test_unknown_and_known_recovery_same_message(client, app):
    register(client)
    one = forgot(client, "student@example.test")
    assert b"If an eligible account exists" in one.data
    assert app.extensions["edumind_test_outbox"][-1]["to"] == "student@example.test"
    two = forgot(client, "unknown@example.test")
    assert b"If an eligible account exists" in two.data
    with app.app_context():
        assert EmailActionEvent.query.filter_by(purpose="reset").count() == 2


def test_reset_is_single_use_and_changes_password(client, app):
    register(client)
    forgot(client, "student@example.test")
    path = reset_path(app)
    assert client.get(path).status_code == 200
    response = client.post(path, data={
        "csrf_token": csrf(client, path),
        "password": "NewVeryStrongPassword123",
        "confirm_password": "NewVeryStrongPassword123",
    }, follow_redirects=True)
    assert b"Password updated" in response.data
    assert client.get(path).status_code == 302
    assert b"Invalid email or password" in login(client).data
    assert b"Login successful" in login(client, password="NewVeryStrongPassword123").data
    with app.app_context():
        user = User.query.filter_by(email="student@example.test").one()
        assert check_password_hash(user.password_hash, "NewVeryStrongPassword123")


def test_reset_rejects_expired_token_and_wrong_confirm(client, app):
    register(client)
    forgot(client, "student@example.test")
    path = reset_path(app)
    response = client.post(path, data={
        "csrf_token": csrf(client, path),
        "password": "NewVeryStrongPassword123",
        "confirm_password": "DoesNotMatch123",
    }, follow_redirects=True)
    assert b"Passwords do not match" in response.data
    with app.app_context():
        event = EmailActionEvent.query.filter_by(purpose="reset").one()
        event.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()
    assert client.get(path).status_code == 302


def test_forgot_post_requires_csrf(client):
    response = client.post("/auth/forgot-password", data={"email": "a@example.test"})
    assert response.status_code == 400


def test_recovery_rate_limit_per_address(client, app):
    register(client)
    for _ in range(5):
        forgot(client, "student@example.test")
    with app.app_context():
        assert EmailActionEvent.query.filter_by(purpose="reset").count() == 3
    assert len(app.extensions["edumind_test_outbox"]) == 3


def test_student_can_email_only_own_report(client, app):
    register(client)
    login(client)
    response = client.post("/api/reports/email", data={
        "csrf_token": csrf(client, "/progress/")
    }, follow_redirects=True)
    assert b"Progress report sent" in response.data
    mail = app.extensions["edumind_test_outbox"][-1]
    assert mail["to"] == "student@example.test"
    assert "Study tasks" not in mail["body"] or "Tasks" in mail["body"]
    assert "individual item responses" in mail["body"]
    blocked = client.post("/api/reports/email", data={
        "csrf_token": csrf(client, "/progress/"),
        "student_id": "999", "recipient": "attacker@example.test"
    })
    assert blocked.status_code == 403


def test_progress_email_is_rate_limited(client, app):
    register(client)
    login(client)
    for _ in range(4):
        client.post("/api/reports/email", data={"csrf_token": csrf(client, "/progress/")})
    assert len(app.extensions["edumind_test_outbox"]) == 3


def test_lecturer_needs_grant_and_separate_email_permission(client, app):
    register(client)
    with app.app_context():
        student = User.query.filter_by(email="student@example.test").one()
        lecturer = User(full_name="Lecturer", email="lecturer@example.test",
                        role="lecturer", password_hash=generate_password_hash(PASSWORD))
        db.session.add(lecturer)
        db.session.commit()
        student_id, lecturer_id = student.user_id, lecturer.user_id
    login(client)
    # Student grants view access, but email consent remains OFF.
    grant_result = client.post("/lecturer/sharing/grant", data={
        "csrf_token": csrf(client, "/lecturer/sharing"),
        "lecturer_email": "lecturer@example.test"
    }, follow_redirects=True)
    assert b"access granted" in grant_result.data.lower()
    with app.app_context():
        grant = LecturerAccessGrant.query.one()
        assert grant.email_allowed is False
        grant_id = grant.grant_id
    logout(client)
    login(client, email="lecturer@example.test")
    no_email = client.post("/api/reports/email", data={
        "csrf_token": csrf(client, f"/lecturer/students/{student_id}"),
        "student_id": str(student_id)
    })
    assert no_email.status_code == 404
    # Lecturer may not email reports of other students.
    no_grant = client.post("/api/reports/email", data={
        "csrf_token": csrf(client, f"/lecturer/students/{student_id}"),
        "student_id": "9999"
    })
    assert no_grant.status_code == 404
    token = csrf(client, f"/lecturer/students/{student_id}")
    client.post("/auth/logout", data={"csrf_token": token})
    login(client)
    client.post(f"/lecturer/sharing/email-permission/{grant_id}", data={
        "csrf_token": csrf(client, "/lecturer/sharing"),
        "email_allowed": "on"
    })
    logout(client)
    login(client, email="lecturer@example.test")
    response = client.post("/api/reports/email", data={
        "csrf_token": csrf(client, f"/lecturer/students/{student_id}"),
        "student_id": str(student_id), "recipient": "attacker@example.test"
    }, follow_redirects=True)
    assert b"Progress report sent" in response.data
    assert app.extensions["edumind_test_outbox"][-1]["to"] == "lecturer@example.test"


def test_email_report_requires_csrf(client):
    register(client)
    login(client)
    assert client.post("/api/reports/email").status_code == 400
