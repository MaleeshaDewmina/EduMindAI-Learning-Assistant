"""Ephemeral, bounded text extraction for chatbot study references.

Files are processed in memory and never written into the uploads directory or database.
The extracted excerpt is sent to the configured Groq model for the current request.
"""
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from werkzeug.utils import secure_filename

MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
MAX_DOCUMENT_CHARS = 10000
MAX_DOCX_UNCOMPRESSED = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class AttachmentError(ValueError):
    """Explain a safe file-validation failure to the current user."""


def extract_reference_document(upload):
    """Return (safe filename, bounded text excerpt, was_truncated).

    Does not persist the original file. In particular, an image-only PDF does not
    magically become searchable; the project deliberately performs no OCR.
    """
    raw_name = (getattr(upload, "filename", "") or "").strip()
    safe_name = secure_filename(raw_name)[:110]
    if not safe_name:
        raise AttachmentError("Choose a PDF, DOCX, TXT or Markdown document.")
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise AttachmentError("Unsupported file. Attach a PDF, DOCX, TXT or Markdown document (up to 5 MB).")

    # A bounded read prevents a large upload from being loaded into memory.
    binary = upload.stream.read(MAX_ATTACHMENT_BYTES + 1)
    if len(binary) > MAX_ATTACHMENT_BYTES:
        raise AttachmentError("The document is too large. Please choose a file up to 5 MB.")
    if not binary:
        raise AttachmentError("The attached document is empty.")

    try:
        if extension == ".pdf":
            if not binary.startswith(b"%PDF-"):
                raise AttachmentError("This file is not a valid PDF document.")
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(binary), strict=False)
            if reader.is_encrypted:
                raise AttachmentError("Password-protected PDFs are not supported.")
            chunks = []
            total = 0
            for page in reader.pages[:25]:
                part = (page.extract_text() or "")[:MAX_DOCUMENT_CHARS + 1]
                chunks.append(part)
                total += len(part)
                if total > MAX_DOCUMENT_CHARS:
                    break
            text = "\n".join(chunks)
        elif extension == ".docx":
            if not binary.startswith(b"PK"):
                raise AttachmentError("This file is not a valid DOCX document.")
            with ZipFile(BytesIO(binary)) as archive:
                names = {item.filename for item in archive.infolist()}
                total_uncompressed = sum(item.file_size for item in archive.infolist())
                if "word/document.xml" not in names or total_uncompressed > MAX_DOCX_UNCOMPRESSED:
                    raise AttachmentError("The DOCX document is invalid or too complex to process safely.")
            from docx import Document
            doc = Document(BytesIO(binary))
            parts = []
            total = 0
            for paragraph in doc.paragraphs:
                chunk = paragraph.text
                parts.append(chunk)
                total += len(chunk)
                if total > MAX_DOCUMENT_CHARS:
                    break
            if total < MAX_DOCUMENT_CHARS:
                for table in doc.tables:
                    for row in table.rows:
                        chunk = " | ".join(cell.text for cell in row.cells)
                        parts.append(chunk)
                        total += len(chunk)
                        if total > MAX_DOCUMENT_CHARS:
                            break
                    if total > MAX_DOCUMENT_CHARS:
                        break
            text = "\n".join(parts)
        else:
            if b"\x00" in binary:
                raise AttachmentError("The selected text file appears to be binary.")
            text = binary.decode("utf-8-sig")
    except AttachmentError:
        raise
    except (UnicodeDecodeError, ValueError, BadZipFile, KeyError, OSError, TypeError, RuntimeError) as exc:
        raise AttachmentError("We could not read this document. Check its format and try another file.") from exc
    except Exception as exc:
        # PDF parser errors vary; do not leak document contents or stack traces to the UI.
        raise AttachmentError("We could not extract text from this document.") from exc

    text = text.replace("\x00", "").strip()
    if not text:
        raise AttachmentError("No readable text was found. For scanned PDFs, use a text-based version.")
    is_truncated = len(text) > MAX_DOCUMENT_CHARS
    return safe_name, text[:MAX_DOCUMENT_CHARS], is_truncated
