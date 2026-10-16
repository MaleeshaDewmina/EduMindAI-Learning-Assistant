"""Phase 4: no live Groq requests; verifies safe presentation and chat privacy."""
from app.extensions import db
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.services.chat_formatting import format_ai_reply
from tests.test_auth_security import register, login, csrf


def test_ai_reply_formatting_is_escaped_and_bold():
    html = str(format_ai_reply("1. **Use a schedule**\n<script>alert('x')</script>"))
    assert "<strong>Use a schedule</strong>" in html
    assert "<br>" in html
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_chat_reply_renders_safe_emphasis(client, app):
    register(client)
    login(client)
    with app.app_context():
        user = User.query.filter_by(email="student@example.com").one()
        db.session.add(ChatMessage(user_id=user.user_id, user_message="hi", ai_response="**Plan one task**\nThen review."))
        db.session.commit()
    response = client.get("/chatbot/")
    assert response.status_code == 200
    assert b"<strong>Plan one task</strong>" in response.data
    assert b"Clear Chat History" in response.data


def test_overlong_chat_message_is_rejected_without_calling_provider(client, app, monkeypatch):
    register(client)
    login(client)

    def no_call(*args, **kwargs):
        raise AssertionError("Groq must not be called for oversized messages")

    monkeypatch.setattr("app.routes.chatbot_routes.generate_ai_response", no_call)
    res = client.post("/chatbot/", data={"csrf_token": csrf(client, "/chatbot/"), "message": "a" * 2001}, follow_redirects=True)
    assert res.status_code == 200
    assert b"within 2000 characters" in res.data
    with app.app_context():
        assert ChatMessage.query.count() == 0


def test_clear_chat_requires_post_and_csrf_and_only_deletes_current_user(client, app):
    register(client)
    login(client)
    other_client = app.test_client()
    register(other_client, "other@example.com")
    login(other_client, "other@example.com")
    with app.app_context():
        user = User.query.filter_by(email="student@example.com").one()
        other = User.query.filter_by(email="other@example.com").one()
        db.session.add(ChatMessage(user_id=user.user_id, user_message="mine", ai_response="first"))
        db.session.add(ChatMessage(user_id=other.user_id, user_message="other", ai_response="second"))
        db.session.commit()
    assert client.get("/chatbot/clear").status_code == 405
    assert client.post("/chatbot/clear").status_code == 400
    res = client.post("/chatbot/clear", data={"csrf_token": csrf(client, "/chatbot/")}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Cleared 1 saved conversation" in res.data
    with app.app_context():
        items = ChatMessage.query.all()
        assert len(items) == 1 and items[0].user_message == "other"
