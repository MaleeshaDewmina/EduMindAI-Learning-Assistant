"""Phase 7 Markdown and privacy regression checks. No live Groq calls."""

from io import BytesIO
from app.extensions import db
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.services.chat_formatting import format_ai_reply
from app.services.attachment_service import AttachmentError, extract_reference_document
from tests.test_auth_security import register, login


def test_markdown_tables_lists_and_fenced_code():
    raw = """## Study tips

| Topic | Minutes |
| --- | ---: |
| Revision | 20 |

- Break work into steps

```python
print('learn')
```"""
    output = str(format_ai_reply(raw))
    assert "<table>" in output and "<th>Topic</th>" in output
    assert "<td>Revision</td>" in output and "<td>20</td>" in output
    assert "<h2>Study tips</h2>" in output and "<li>Break work into steps</li>" in output
    assert "<pre>" in output and "print" in output


def test_raw_script_html_attributes_are_not_executable():
    raw = "<script>alert(1)</script>\n<img src=x onerror=alert(2)>\n**Bold**"
    output = str(format_ai_reply(raw))
    assert "<script" not in output and "<img" not in output
    assert "&lt;img" in output and "&lt;script" in output  # visible escaped text, not DOM nodes
    assert "<strong>Bold</strong>" in output


def test_markup_links_are_protocol_restricted_and_images_not_embedded():
    raw = "[bad](javascript:alert(1)) [data](data:text/html,boom) [good](https://example.org) ![remote](https://example.org/tracker.png)"
    output = str(format_ai_reply(raw))
    assert "href=\"javascript:" not in output
    assert "href=\"data:" not in output
    assert '<a href="https://example.org">good</a>' in output
    assert "<img" not in output


def test_saved_chat_renders_table_without_leaking_markup(client, app):
    register(client)
    login(client)
    with app.app_context():
        user = User.query.filter_by(email="student@example.com").one()
        db.session.add(ChatMessage(
            user_id=user.user_id, user_message="Explain this table", 
            ai_response="| Item | Result |\n|---|---|\n| A | <script>bad</script> |"
        ))
        db.session.commit()
    response = client.get("/chatbot/")
    assert response.status_code == 200 and b"<table>" in response.data
    assert b"<script>bad</script>" not in response.data


def test_authenticated_pages_receive_browser_security_headers(client):
    register(client)
    login(client)
    response = client.get("/chatbot/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "no-store" in response.headers["Cache-Control"]


def test_public_html_is_not_marked_as_account_private(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "no-store" not in response.headers.get("Cache-Control", "")


def test_invalid_pdf_fails_cleanly():
    class Upload:
        filename = "chapter.pdf"
        stream = BytesIO(b"%PDF-\nnot actually valid PDF")
    try:
        extract_reference_document(Upload())
    except AttachmentError as error:
        assert "could not" in str(error).lower() or "not a valid" in str(error).lower()
    else:
        raise AssertionError("Malformed PDF was accepted")


def test_docx_rejects_oversized_uncompressed_payload():
    from zipfile import ZipFile, ZIP_DEFLATED
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", b"a" * (16 * 1024 * 1024 + 1))
    class Upload:
        def __init__(self, data):
            self.filename = "unsafe.docx"
            self.stream = BytesIO(data)
    try:
        extract_reference_document(Upload(output.getvalue()))
    except AttachmentError as error:
        assert "invalid" in str(error).lower() or "too complex" in str(error).lower()
    else:
        raise AssertionError("Large uncompressed DOCX content was accepted")
