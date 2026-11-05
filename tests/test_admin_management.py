"""Super Admin / Admin role separation and account-management regression tests."""
import re

from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from app.models.user import User
from app.models.activity_log import UserActivityLog

PW = "DemoSecurePassword123"


def token(client, path):
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code)
    match = re.search(rb'name="csrf_token"\s+value="([^"]+)"', response.data)
    assert match, path
    return match.group(1).decode()


def seed(app):
    with app.app_context():
        for name, role in [
            ("student", "student"),
            ("teacher", "lecturer"),
            ("operator", "admin"),
            ("owner", "superadmin"),
        ]:
            db.session.add(User(
                full_name=name.capitalize(),
                email=f"{name}@example.test",
                password_hash=generate_password_hash(PW),
                role=role, is_active=True,
            ))
        db.session.commit()
        return {u.email:u.user_id for u in User.query.all()}


def sign_in(client, email):
    return client.post("/auth/login", data={
        "csrf_token": token(client, "/auth/login"),
        "email": email, "password": PW,
    }, follow_redirects=True)


def sign_out(client, page):
    return client.post("/auth/logout", data={
        "csrf_token": token(client, page)
    }, follow_redirects=True)


def create(client, role, email="newstaff@example.test", password=PW):
    return client.post("/admin/accounts", data={
        "csrf_token": token(client, "/admin/"),
        "full_name": "New Staff", "email": email,
        "role": role, "current_password": password,
    }, follow_redirects=True)


def test_students_and_lecturers_cannot_access_admin_area(client, app):
    seed(app)
    assert client.get("/admin/").status_code == 302
    sign_in(client, "student@example.test")
    assert client.get("/admin/").status_code == 403
    assert client.post("/admin/accounts", data={"role":"admin"}).status_code == 400
    sign_out(client, "/dashboard/")
    sign_in(client, "teacher@example.test")
    assert client.get("/admin/").status_code == 302  # Lecturer redirected to their area.


def test_superadmin_can_create_admin_with_email_setup(client, app):
    seed(app)
    login = sign_in(client, "owner@example.test")
    assert b"Super Admin Console" in login.data
    response = create(client, "admin")
    assert b"Account created" in response.data
    with app.app_context():
        new = User.query.filter_by(email="newstaff@example.test").one()
        assert new.role == "admin"
        assert new.is_active is True
        assert not check_password_hash(new.password_hash, "SharedPassword")
        assert UserActivityLog.query.filter_by(activity_name="Admin account created").count() == 1
    invitation = app.extensions["edumind_test_outbox"][-1]
    assert invitation["to"] == "newstaff@example.test"
    assert "reset-password" in invitation["body"]


def test_admin_can_create_lecturer_not_admin_or_superadmin(client, app):
    seed(app)
    sign_in(client, "operator@example.test")
    assert b"Admin Console" in client.get("/admin/").data
    assert b'value="admin"' not in client.get("/admin/").data
    assert create(client, "admin").status_code == 403
    assert create(client, "superadmin").status_code == 403
    with app.app_context():
        assert User.query.filter_by(email="newstaff@example.test").count() == 0
    result = create(client, "lecturer")
    assert b"Account created" in result.data
    with app.app_context():
        assert User.query.filter_by(email="newstaff@example.test").one().role == "lecturer"


def test_wrong_current_password_blocks_staff_creation(client, app):
    seed(app)
    sign_in(client, "owner@example.test")
    result = create(client, "admin", password="wrongpassword")
    assert b"Current password is incorrect" in result.data
    with app.app_context():
        assert User.query.filter_by(email="newstaff@example.test").count() == 0


def test_existing_account_cannot_be_silently_promoted(client, app):
    seed(app)
    sign_in(client, "owner@example.test")
    response = create(client, "admin", email="student@example.test")
    assert b"already registered" in response.data
    with app.app_context():
        assert User.query.filter_by(email="student@example.test").one().role == "student"


def test_superadmin_can_suspend_but_not_self_or_other_superadmin(client, app):
    ids = seed(app)
    sign_in(client, "owner@example.test")
    page = "/admin/"
    token_ = token(client, page)
    assert client.post(f"/admin/accounts/{ids['owner@example.test']}/status",
        data={"csrf_token":token_, "current_password":PW,"active":"false"}).status_code == 403
    student_id = ids["student@example.test"]
    result = client.post(f"/admin/accounts/{student_id}/status", data={
        "csrf_token":token_, "current_password":PW,"active":"false"
    }, follow_redirects=True)
    assert b"Account status updated" in result.data
    with app.app_context():
        student = db.session.get(User, student_id)
        assert student.is_active is False
        assert UserActivityLog.query.filter_by(activity_name="Account suspended").count() == 1


def test_admin_cannot_change_students_or_superadmin(client, app):
    ids = seed(app)
    sign_in(client, "operator@example.test")
    for email in ("student@example.test", "owner@example.test", "operator@example.test"):
        response = client.post(f"/admin/accounts/{ids[email]}/status", data={
            "csrf_token":token(client, "/admin/"),
            "current_password":PW, "active":"false",
        })
        assert response.status_code == 403


def test_csrf_protects_adding_staff_and_status(client, app):
    ids = seed(app)
    sign_in(client, "owner@example.test")
    assert client.post("/admin/accounts", data={
        "role":"admin", "email":"test@example.test"
    }).status_code == 400
    assert client.post(f"/admin/accounts/{ids['teacher@example.test']}/status",
        data={"active":"false"}).status_code == 400


def test_privileged_roles_redirect_away_from_student_routes(client, app):
    seed(app)
    for email in ("operator@example.test", "owner@example.test"):
        sign_in(client, email)
        for path in ("/dashboard/", "/planner/", "/progress/", "/chatbot/", "/evaluation/", "/lecturer/"):
            response = client.get(path)
            assert response.status_code == 302, (email, path)
            assert response.location.endswith("/admin/")
        sign_out(client, "/admin/")


def test_public_registration_cannot_choose_privileged_role(client, app):
    registration = client.post("/auth/register", data={
        "csrf_token":token(client, "/auth/register"),
        "full_name":"Visitor","email":"visitor@example.test",
        "password":PW,"confirm_password":PW,"role":"superadmin","age":"21"
    }, follow_redirects=True)
    assert registration.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email="visitor@example.test").one().role == "student"


def test_inactive_session_kicked_out(client, app):
    ids = seed(app)
    sign_in(client, "operator@example.test")
    with app.app_context():
        person = db.session.get(User, ids["operator@example.test"])
        person.is_active = False
        db.session.commit()
    result = client.get("/admin/")
    assert result.status_code == 302
    assert result.location.endswith("/auth/login")
