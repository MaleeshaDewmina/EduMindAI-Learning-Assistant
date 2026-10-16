"""Enhancement regression tests; all Groq calls are stubbed."""
from io import BytesIO

from app.extensions import db
from app.models.chat_message import ChatMessage
from app.services.attachment_service import AttachmentError, extract_reference_document
from tests.test_auth_security import register, login, csrf


class Uploaded:
    def __init__(self, name, data):
        self.filename = name
        self.stream = BytesIO(data)


def test_text_attachment_extracts_no_file_storage():
    name, excerpt, truncated = extract_reference_document(Uploaded('Chapter 1.md', b'# Study notes\nThe key idea is spaced repetition.'))
    assert name.endswith('.md')
    assert 'spaced repetition' in excerpt
    assert truncated is False


def test_attachment_validation_rejects_binary_unsupported_and_oversized():
    for item in (Uploaded('script.exe', b'malware'), Uploaded('report.txt', b'\x00\x99'), Uploaded('long.md', b'x' * (5 * 1024 * 1024 + 1))):
        try:
            extract_reference_document(item)
        except AttachmentError:
            pass
        else:
            raise AssertionError('Unsafe attachment was accepted')


def test_docx_extracts_paragraph():
    from docx import Document
    doc = Document();doc.add_paragraph('Plan small goals and track progress.')
    output=BytesIO();doc.save(output)
    name, text, truncated=extract_reference_document(Uploaded('goals.docx',output.getvalue()))
    assert name=='goals.docx' and 'Plan small goals' in text and not truncated


def test_invalid_scanned_pdf_reports_no_readable_text():
    from pypdf import PdfWriter
    writer=PdfWriter();writer.add_blank_page(width=72,height=72)
    output=BytesIO();writer.write(output)
    try:
        extract_reference_document(Uploaded('scanned.pdf',output.getvalue()))
    except AttachmentError as exc:
        assert 'readable text' in str(exc).lower()
    else:
        raise AssertionError('Empty PDF was accepted')


def test_chatbot_accepts_attached_study_doc_and_never_persists_contents(client, app, monkeypatch):
    register(client);login(client)
    calls=[]
    def fake_groq(message, context, attachment_context=None):
        calls.append((message, context, attachment_context))
        return 'The document is about healthy study habits.'
    monkeypatch.setattr('app.routes.chatbot_routes.generate_ai_response',fake_groq)
    token=csrf(client, '/chatbot/')
    result=client.post('/chatbot/', data={'csrf_token':token,'message':'Summarise the key ideas.', 'attachment':(BytesIO(b'Never store my document content!'), 'study.txt')}, content_type='multipart/form-data', follow_redirects=True)
    assert result.status_code==200
    assert len(calls)==1
    assert 'Never store my document content!' in calls[0][2]
    with app.app_context():
        record=ChatMessage.query.one()
        assert 'study.txt' in record.user_message
        assert 'Never store my document content!' not in record.user_message
        assert 'Never store my document content!' not in record.ai_response


def test_invalid_attachment_never_calls_groq(client, app, monkeypatch):
    register(client);login(client)
    def no_call(*args,**kwargs):raise AssertionError('Provider should not be called')
    monkeypatch.setattr('app.routes.chatbot_routes.generate_ai_response',no_call)
    token=csrf(client,'/chatbot/')
    result=client.post('/chatbot/', data={'csrf_token':token,'message':'Please read','attachment':(BytesIO(b'garbage'),'virus.exe')}, content_type='multipart/form-data', follow_redirects=True)
    assert result.status_code==200
    assert b'Unsupported file' in result.data
    with app.app_context():assert ChatMessage.query.count()==0


def test_attachment_only_message_is_allowed(client,app,monkeypatch):
    register(client);login(client)
    sent=[]
    def fake(message,context,attachment_context=None):
        sent.append((message,attachment_context));return 'Three takeaways.'
    monkeypatch.setattr('app.routes.chatbot_routes.generate_ai_response',fake)
    res=client.post('/chatbot/',data={'csrf_token':csrf(client,'/chatbot/'),'message':'','attachment':(BytesIO(b'hello lesson'), 'lesson.txt')}, content_type='multipart/form-data',follow_redirects=True)
    assert res.status_code==200 and 'Summarise' in sent[0][0] and 'hello lesson' in sent[0][1]


def test_chat_studio_controls_and_shared_nav_render(client):
    register(client);login(client)
    r=client.get('/chatbot/')
    assert r.status_code==200
    assert b'enctype="multipart/form-data"' in r.data
    assert b'id="chat-attachment"' in r.data
    assert b'id="voice-input-btn"' in r.data
    assert b'chat_studio.js' in r.data
    assert b'Primary navigation' in r.data
    dash=client.get('/dashboard/')
    assert b'Every study session' in dash.data
