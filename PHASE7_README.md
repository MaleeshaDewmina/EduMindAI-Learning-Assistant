# EduMind AI — Phase 7: Safer Markdown Tables and Browser Protections

**Source:** The latest `EduMindAI(3).zip` as provided by the student after Phase 6. This is a small overlay; no existing database schema or migrations change.

## Included changes

- **AI answer formatting:** `markdown-it-py` parses CommonMark including headers, lists, block quotes, tables, fenced code and clickable ordinary web links. Raw HTML is disabled, and Bleach allowlists safe HTML tags/attributes/protocols. Embedded images, arbitrary HTML/CSS/JavaScript and unsafe link protocols are removed. Do not treat model-generated links as trustworthy.
- **Groq prompt:** asks the model for valid Markdown table structure when tables are useful, and prefers short lists on narrow interfaces.
- **Styling:** readable tables, code blocks, headings, bullets, quotations, and horizontal scrolling for wide tables. Works with current CSS variables and dark mode.
- **Browser protection:** `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `private, no-store` for authenticated HTML pages. A restrictive CSP was intentionally not added because the current app uses inline scripts and external CSS/JS; testing is required before deploying with one.
- **Attachment parsing:** max 1000 ZIP entries for DOCX; max 16 MiB total declared uncompressed DOCX data; first-25-PDF-page truncation is now correctly reported. Files are still capped at 5 MiB and excerpts at 10,000 characters.
- **Regression tests:** eight added cases. All 42 existing tests must continue passing.

## Apply on Windows

1. Stop Flask and back up the complete local project. Do not move or overwrite `.env`, `venv`, `.git`, your MySQL database or SPSS/participant data.
2. Extract ZIP and copy **its contents** into `C:\Users\DELL\EduMindAI`, merging `app/` and `tests/`.
3. Install two new requirements:

```powershell
cd C:\Users\DELL\EduMindAI
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Test (expected: **50 passed** if the 42 prior tests are present):

```powershell
.\venv\Scripts\python.exe -m pytest tests -q
```

5. Start Flask and hard-refresh with `Ctrl+Shift+R`:

```powershell
.\venv\Scripts\python.exe run.py
```

6. Ask the chatbot to make a 3-column Markdown comparison table and a short Python code example. Confirm proper rendering, copy, listen, light/dark modes, and mobile scrolling. Also test invalid attachments.

## Git after local verification

```powershell
git status
git add app/services/chat_formatting.py app/services/attachment_service.py app/services/groq_service.py app/static/css/chat_studio.css app/templates/base.html app/__init__.py requirements.txt tests/test_phase7_markdown_security.py PHASE7_README.md
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: render AI markdown safely and harden document parsing"
git push
```

Review staged files for secrets before committing. Keep this repo private and arrange ethics/supervisor decisions in parallel.

## Verification status

This environment can parse and locally smoke-test the Markdown renderer, but cannot run the Flask suite or connect to the student's MySQL or Groq services because the full dependencies and network are unavailable. Run the complete regression suite on the Windows PC.

## Security limits

This is a learning/research prototype, not a production security certification. Browser speech APIs may use third-party speech services. AI answers can be wrong, Markdown links may lead to external sites, and untrusted PDF/DOCX processing remains a residual risk. Do not upload confidential university documents without permission.
