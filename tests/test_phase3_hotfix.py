"""Hotfix regression coverage; no live Groq API or MySQL is called."""
from types import SimpleNamespace

from app.models.chat_message import ChatMessage
from app.models.feedback import Feedback
from app.services import groq_service
from app.services.groq_service import AIServiceError
from tests.test_auth_security import csrf, login, register


def test_replacement_groq_model_is_used(app, monkeypatch):
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Try one small step."))])

    monkeypatch.setattr(groq_service, "Groq", lambda api_key: SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions())))
    with app.app_context():
        app.config.update(GROQ_API_KEY="fake-test-api-key", GROQ_MODEL="openai/gpt-oss-20b")
        response = groq_service.generate_ai_response("Help me study", "Completed tasks: 1")
        assert response == "Try one small step."
        assert captured["model"] == "openai/gpt-oss-20b"


def test_failed_groq_call_not_saved_to_chat_history(client, app, monkeypatch):
    register(client)
    login(client)

    def unavailable(*args, **kwargs):
        raise AIServiceError("The AI assistant is temporarily unavailable.")

    monkeypatch.setattr("app.routes.chatbot_routes.generate_ai_response", unavailable)
    response = client.post("/chatbot/", data={"csrf_token": csrf(client, "/chatbot/"), "message": "Hello"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"temporarily unavailable" in response.data
    with app.app_context():
        assert ChatMessage.query.count() == 0


def test_feedback_consistency_category_in_sqlite(app, client, monkeypatch):
    register(client)
    login(client)
    monkeypatch.setattr("app.services.feedback_service.get_task_metrics", lambda user_id: {
        "total_tasks": 5,
        "completed_tasks": 3,
        "pending_tasks": 2,
        "overdue_tasks": 0,
        "completion_rate": 60,
    })
    monkeypatch.setattr("app.services.feedback_service.calculate_motivation_score", lambda user_id: {
        "engagement_score": 50,
        "consistency_score": 20,
    })
    response = client.post("/feedback/generate", data={"csrf_token": csrf(client,"/feedback/")}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert Feedback.query.one().feedback_type == "Consistency"
