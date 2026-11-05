"""Ensure branded report emails are safe and keep a plain-text alternative."""
from email.message import EmailMessage
from types import SimpleNamespace

from app.services.report_email_html import report_email_html
from app.services.email_delivery import send_email


def sample():
    student = SimpleNamespace(user_id=42, full_name="<img src=x onerror=alert(1)>")
    data = dict(
        total=5, completed=3, pending=2, overdue=0,
        completion=60.0, activity_events=13, active_days=4, indicator=39.3,
    )
    return student, data


def test_student_email_is_branded_and_hides_name():
    student, data = sample()
    html = report_email_html(student, data, "student", "https://edumind.example.test")
    assert "<!doctype html>" in html
    assert "EduMind AI" in html and "Your learning progress" in html
    assert "60.0%" in html and "Recorded events" in html
    assert "href=\"https://edumind.example.test/progress/\"" in html
    assert student.full_name not in html
    assert "questionnaire answers" in html


def test_lecturer_email_escapes_student_name():
    student, data = sample()
    html = report_email_html(student, data, "lecturer", "https://edumind.example.test")
    assert "AUTHORISED LECTURER COPY" in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert student.full_name not in html
    assert "/lecturer/students/42" in html


def test_unsafe_url_is_not_linked():
    student, data = sample()
    for base in ("http://edumind.example.test", "https://evil.example/a", "javascript:alert(1)"):
        html = report_email_html(student, data, "student", base)
        assert "View progress dashboard" not in html


def test_completion_progress_bar_is_bounded():
    student, data = sample()
    data["completion"] = 130
    html = report_email_html(student, data, "student")
    assert "100.0%" in html
    assert 'width="100%" bgcolor="#5645dd"' in html
    data["completion"] = -20
    html = report_email_html(student, data, "student")
    assert 'width="0%" bgcolor="#5645dd"' in html


def test_test_outbox_contains_html_and_text(app):
    student, data = sample()
    html = report_email_html(student, data, "student")
    with app.app_context():
        send_email("recipient@example.test", "Progress", "Text fallback", html_body=html)
        sent = app.extensions["edumind_test_outbox"][-1]
        assert sent["body"] == "Text fallback"
        assert sent["html_body"] == html
        assert sent["to"] == "recipient@example.test"
