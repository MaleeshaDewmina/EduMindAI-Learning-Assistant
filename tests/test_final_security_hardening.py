"""Post-feature-freeze controls: persistent login throttling and role-scoped identity views."""
from datetime import datetime, timedelta

from app.extensions import db
from app.models.email_action_event import EmailActionEvent
from app.models.user import User
import re
from werkzeug.security import generate_password_hash

PW = "DemoSecurePassword123"


def token(client, path):
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(rb'name="csrf_token"\\s+value="([^"]+)"', response.data)
    assert match
    return match.group(1).decode()


def seed(app):
    with app.app_context():
        for name, role in (
            ("student", "student"),
            ("teacher", "lecturer"),
            ("operator", "admin"),
            ("owner", "superadmin"),
        ):
            db.session.add(User(
                full_name=name.capitalize(), email=f"{name}@example.test",
                password_hash=generate_password_hash(PW), role=role, is_active=True,
            ))
        db.session.commit()


def sign_in(client, email):
    return client.post("/auth/login", data={
        "csrf_token": token(client, "/auth/login"),
        "email": email, "password": PW,
    }, follow_redirects=True)


def create(client, role, email):
    return client.post("/admin/accounts", data={
        "csrf_token": token(client, "/admin/"),
        "full_name": "New Staff", "email": email,
        "role": role, "current_password": PW,
    }, follow_redirects=True)


def _bad_login(client, email, password="not-the-password"):
    return client.post("/auth/login", data={
        "csrf_token": token(client, "/auth/login"),
        "email": email,
        "password": password,
    }, follow_redirects=True)


def test_login_repeated_failures_are_throttled_for_existing_user(client, app):
    seed(app)
    for attempt in range(8):
        response = _bad_login(client, "student@example.test")
        assert response.status_code == 200
        assert b"Invalid email or password" in response.data

    blocked = _bad_login(client, "student@example.test", PW)
    assert blocked.status_code == 429
    assert b"Too many login attempts" in blocked.data
    assert client.get("/dashboard/").status_code == 302
    with app.app_context():
        events = EmailActionEvent.query.filter_by(purpose="login_failure").all()
        assert len(events) == 8
        assert all(e.address_digest != "student@example.test" for e in events)
        assert all(e.ip_digest and e.ip_digest != e.address_digest for e in events)


def test_unknown_address_is_rate_limited_without_account_leak(client, app):
    for _ in range(8):
        response = _bad_login(client, "missing@example.test")
        assert b"Invalid email or password" in response.data
    blocked = _bad_login(client, "missing@example.test")
    assert blocked.status_code == 429
    assert b"Too many login attempts" in blocked.data
    with app.app_context():
        assert User.query.filter_by(email="missing@example.test").count() == 0


def test_rate_limit_is_address_scoped_and_expires(client, app):
    seed(app)
    for _ in range(8):
        _bad_login(client, "STUDENT@EXAMPLE.TEST")
    assert _bad_login(client, "student@example.test", PW).status_code == 429
    # A different account isn't blocked merely because it uses the same network.
    result = sign_in(client, "teacher@example.test")
    assert result.status_code == 200
    assert b"Login successful" in result.data
    with app.app_context():
        # Expire the events without sleeping for 15 minutes.
        for event in EmailActionEvent.query.filter_by(purpose="login_failure").all():
            event.created_at = datetime.utcnow() - timedelta(minutes=16)
        db.session.commit()
    # A separate client exercises a fresh unauthenticated session after expiration.
    fresh = app.test_client()
    result = sign_in(fresh, "student@example.test")
    assert result.status_code == 200
    assert b"Login successful" in result.data


def test_superadmin_cannot_provision_student_unknown_or_superadmin_roles(client, app):
    seed(app)
    sign_in(client, "owner@example.test")
    for role in ("student", "superadmin", "root", "", "administrator"):
        response = create(client, role, email=f"unsafe-{role or 'blank'}@example.test")
        assert response.status_code == 403
    with app.app_context():
        assert User.query.count() == 4


def test_admin_index_hides_student_and_privileged_identities(client, app):
    seed(app)
    sign_in(client, "operator@example.test")
    content = client.get("/admin/").data
    assert b"teacher@example.test" in content
    assert b"student@example.test" not in content
    assert b"owner@example.test" not in content
    assert b"operator@example.test" not in content
    assert b"Lecturers you can manage" in content
    assert b"Showing up to 200 most recent Lecturer accounts" in content


def test_superadmin_still_sees_full_user_overview(client, app):
    seed(app)
    sign_in(client, "owner@example.test")
    content = client.get("/admin/").data
    assert b"student@example.test" in content
    assert b"teacher@example.test" in content
    assert b"operator@example.test" in content
    assert b"owner@example.test" in content
    assert b"Students" in content and b"Super Admins" in content
