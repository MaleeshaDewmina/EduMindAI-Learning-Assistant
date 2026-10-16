import re

from app.extensions import db
from app.models.user import User
from werkzeug.security import check_password_hash


def csrf(client, path):
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(rb'name="csrf_token"\s+value="([^"]+)"', response.data)
    assert match, f"CSRF token missing from {path}"
    return match.group(1).decode("utf-8")


def register(client, email="student@example.com", password="SafePass12345"):
    token = csrf(client, "/auth/register")
    return client.post("/auth/register", data={
        "csrf_token": token,
        "full_name": "Test Student",
        "email": email,
        "password": password,
        "confirm_password": password,
        "age": "21",
        "university": "Example University",
    }, follow_redirects=True)


def login(client, email="student@example.com", password="SafePass12345"):
    token = csrf(client, "/auth/login")
    return client.post("/auth/login", data={
        "csrf_token": token,
        "email": email,
        "password": password,
    }, follow_redirects=True)


def test_registration_hashes_password(client, app):
    result = register(client)
    assert result.status_code == 200
    assert b"Account created successfully" in result.data
    with app.app_context():
        user = User.query.filter_by(email="student@example.com").first()
        assert user is not None
        assert user.password_hash != "SafePass12345"
        assert check_password_hash(user.password_hash, "SafePass12345")


def test_valid_login_and_logout(client):
    register(client)
    result = login(client)
    assert result.status_code == 200
    assert b"Login successful" in result.data
    assert client.get("/dashboard/").status_code == 200
    # Logout must use a POST with CSRF.
    token = csrf(client, "/planner/")
    result = client.post("/auth/logout", data={"csrf_token": token}, follow_redirects=True)
    assert result.status_code == 200
    assert b"You have been logged out" in result.data
    assert client.get("/dashboard/").status_code == 302


def test_bad_password_does_not_log_user_in(client):
    register(client)
    result = login(client, password="WrongPassword999")
    assert b"Invalid email or password" in result.data
    assert b"Login successful" not in result.data
    assert client.get("/dashboard/").status_code == 302


def test_invalid_age_is_rejected(client, app):
    token = csrf(client, "/auth/register")
    result = client.post("/auth/register", data={
        "csrf_token": token, "full_name": "Student", "email": "wrong@example.com",
        "password": "GoodPassword123", "confirm_password": "GoodPassword123",
        "age": "not-a-number"
    }, follow_redirects=True)
    assert b"Age must be a whole number" in result.data
    with app.app_context():
        assert User.query.filter_by(email="wrong@example.com").first() is None


def test_no_csrf_is_rejected(client):
    result = client.post("/auth/login", data={"email": "a@b.com", "password": "anything"})
    assert result.status_code == 400


def test_get_cannot_modify_tasks_or_logout(client):
    register(client)
    login(client)
    assert client.get("/auth/logout").status_code == 405
    assert client.get("/planner/complete/999").status_code == 405
    assert client.get("/planner/delete/999").status_code == 405
