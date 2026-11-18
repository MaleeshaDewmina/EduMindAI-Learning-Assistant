"""Search/filter regression checks for the account governance console."""
import re

from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.user import User


TEST_PASSWORD = "DemoSecurePassword123"


def _user(name, email, role, active=True):
    user = User(
        full_name=name,
        email=email,
        role=role,
        is_active=active,
        password_hash=generate_password_hash(TEST_PASSWORD),
    )
    db.session.add(user)
    return user


def _login(client, email):
    """Log in through the real route so fingerprint and role session checks run."""
    page = client.get("/auth/login")
    assert page.status_code == 200
    match = re.search(rb'name="csrf_token"\s+value="([^"]+)"', page.data)
    assert match is not None
    response = client.post(
        "/auth/login",
        data={
            "csrf_token": match.group(1).decode(),
            "email": email,
            "password": TEST_PASSWORD,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Login successful" in response.data


def test_superadmin_combined_search_filters(app, client):
    with app.app_context():
        superadmin = _user("Owner", "owner@example.test", "superadmin")
        _user("Asha Example", "asha@example.test", "student", True)
        _user("Asha Lecturer", "lecturer@example.test", "lecturer", False)
        _user("Other", "other@example.test", "student", False)
        db.session.commit()

    _login(client, "owner@example.test")
    response = client.get("/admin/?q=asha&role=student&status=active")
    assert response.status_code == 200
    assert b"asha@example.test" in response.data
    assert b"lecturer@example.test" not in response.data
    assert b"other@example.test" not in response.data


def test_superadmin_search_finds_older_account_beyond_first_200(app, client):
    with app.app_context():
        superadmin = _user("Owner", "owner@example.test", "superadmin")
        _user("Needle Account", "needle@example.test", "student")
        for i in range(205):
            _user(f"Recent Person {i}", f"recent{i}@example.test", "student")
        db.session.commit()

    _login(client, "owner@example.test")
    response = client.get("/admin/?q=needle")
    assert response.status_code == 200
    assert b"needle@example.test" in response.data
    assert b"1 matching account" in response.data


def test_superadmin_search_treats_sql_wildcards_as_literals(app, client):
    with app.app_context():
        superadmin = _user("Owner", "owner@example.test", "superadmin")
        _user("Percent % Name", "percent@example.test", "student")
        _user("Another Name", "another@example.test", "student")
        db.session.commit()

    _login(client, "owner@example.test")
    response = client.get("/admin/?q=%25")
    assert response.status_code == 200
    assert b"percent@example.test" in response.data
    assert b"another@example.test" not in response.data


def test_admin_cannot_expand_lecturer_scope_using_query_parameters(app, client):
    with app.app_context():
        ordinary_admin = _user("Manager", "manager@example.test", "admin")
        _user("Student Secret", "student@example.test", "student")
        _user("Lecturer Visible", "lecturer@example.test", "lecturer")
        db.session.commit()

    _login(client, "manager@example.test")
    response = client.get("/admin/?q=student&role=student&status=active")
    assert response.status_code == 200
    assert b"student@example.test" not in response.data
    assert b"lecturer@example.test" in response.data
    assert b"account-search" not in response.data


def test_student_cannot_access_account_search(app, client):
    with app.app_context():
        student = _user("Learner", "learner@example.test", "student")
        db.session.commit()
    _login(client, "learner@example.test")
    response = client.get("/admin/?q=lecturer")
    assert response.status_code == 403


def test_superadmin_invalid_filters_do_not_expose_other_accounts(app, client):
    with app.app_context():
        superadmin = _user("Owner", "owner@example.test", "superadmin")
        _user("Learner", "learner@example.test", "student")
        db.session.commit()
    _login(client, "owner@example.test")
    response = client.get("/admin/?role=unknown")
    assert response.status_code == 200
    assert b"No accounts match these filters" in response.data
    assert b"learner@example.test" not in response.data
