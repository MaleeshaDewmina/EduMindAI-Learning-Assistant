# EduMind AI — Phase 6: Learning Studio UI + Document and Voice Chat

**Source base:** User-provided `EduMindAI(2).zip` after the Phase 5 evaluation feature. This is a focused source overlay, not a whole-project replacement.

## Design direction

- **Palette:** deep midnight navy `#10182e`, electric indigo `#5145e8`, fresh mint `#26bdac`, cool off-white `#f4f6fc` (dark mode retained).
- **Typography:** Plus Jakarta Sans headings, DM Sans body, with Segoe UI/system fallbacks. Google Fonts requires connectivity; the app still works without it.
- **Navigation:** one shared Jinja sidebar, active-page highlighting, contextual mobile drawer, theme toggle and reduced-motion support.
- **Dashboard:** gradient welcome hero and real-data task completion ring, restyled progress cards/charts.
- **All pages:** consistent cards, forms, inputs, tables, focus indicators and responsive layout. No hard-coded study outcome numbers.
- **Chatbot:** conversation layout, safe formatting from existing filter, quick prompts, response copy, browser dictation, browser read-aloud, file attachment feedback and server-side validation.

## Supported attachments

| Type | Result |
| --- | --- |
| `.pdf` | Extract embedded text from first 25 pages. Scanned/image-only PDFs need OCR externally. |
| `.docx` | Extract paragraphs and table text. |
| `.txt`, `.md` | Extract UTF-8 text. |

Size limit: **5 MiB/file**. A maximum of **10,000 extracted characters** is supplied to the configured Groq AI model per request; truncated documents show a notice. The Flask request limit increases from 1 MiB to 6 MiB to accommodate file + form overhead. Only one document per message.

- Files are parsed *in memory*, not stored on disk or in the database.
- Existing `chat_messages` records retain only the student's question and a sanitised filename, plus the AI reply. Generated replies may themselves paraphrase submitted content.
- **The extracted document content is sent to the external Groq API**. Do not upload confidential university records, personal data or participant research materials without explicit permission.
- Filename and size checks do not make arbitrary documents risk free. This is a research prototype, not a production file-processing service.
- The document is treated as **untrusted reference data** in the prompt; it cannot be guaranteed that a language model will never be influenced by prompt-injection content.

## Voice controls

- **Speak:** Browser SpeechRecognition/WebKitSpeechRecognition where available (often Chrome/Edge), with microphone permission. It appends text to the input; it does *not* send the message automatically. Some browser implementations send microphone data to their speech providers.
- **Listen:** Browser speechSynthesis to read the chosen AI response aloud. Click Stop audio to cancel. Voice quality and supported languages depend on OS and browser.
- Not supported: uploaded audio transcription, voice-to-voice Groq streaming, offline guarantees, screenshot/vision understanding, or storing voice recordings. Unsupported browser controls are disabled automatically.

## Installation (Windows PowerShell)

1. Stop Flask using `Ctrl+C`. Make a backup of `C:\Users\DELL\EduMindAI` and your MySQL database.
2. Extract this archive to Downloads. Copy its **contents**, not the parent folder, into `C:\Users\DELL\EduMindAI`. Merge matching `app/` and `tests/` folders, replace matching files. Keep your `.env`, `.git` and `venv` untouched.
3. Install the extra PDF and Word readers:

```powershell
cd C:\Users\DELL\EduMindAI
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Run tests:

```powershell
.\venv\Scripts\python.exe -m pytest tests -q
```

Expected **42 tests** if your existing 34 tests and these 8 new tests are all present. Treat 42 as a target until confirmed on your PC.

5. Start locally:

```powershell
.\venv\Scripts\python.exe run.py
```

6. In Chrome visit `http://127.0.0.1:5000`. Press `Ctrl+Shift+R` to bypass cached CSS/JS. Test **Dashboard, Planner, Progress, Feedback, Evaluation, Register/Login**, and the chat in both themes, on desktop and mobile widths.

## Manual chat checks

- [ ] Text-only chat still sends/receives and existing history remains.
- [ ] Quick-prompt chips fill, but don't send, a message.
- [ ] Attach `.txt` (few sentences), ask for a summary; answer reflects file content.
- [ ] Repeat with a text-based PDF and DOCX.
- [ ] Reject unsupported `.exe` and over-5-MiB file without calling Groq.
- [ ] A document-only message generates a summary.
- [ ] Refresh chat: old document body must not appear in stored question/history.
- [ ] Dictate a question where supported; review transcription before sending.
- [ ] Read an AI reply aloud, then stop it.
- [ ] Copy an AI reply.
- [ ] Confirm mobile drawer opens/closes, and focus/controls work.
- [ ] Confirm both light/dark themes and reduced-motion settings.

## Code verification completed here

- Python source syntax parsed; all Jinja templates parsed.
- New JavaScript syntax checked with Node.
- Static screenshot previews of desktop dashboard/chat and mobile chat inspected, including no horizontal overflow at 390px.
- File extraction smoke-checked independently for TXT, DOCX, empty PDF and invalid types/size using an isolated import stub (the full Flask environment was unavailable).
- **Full Flask/SQLite test suite, Groq live calls, browser microphone, speech synthesis and live MySQL not executed here.** Run locally before making a release claim.

## Git workflow after tests pass

```powershell
git status
git add app/templates app/routes/chatbot_routes.py app/services/groq_service.py app/services/attachment_service.py app/static/css/studio.css app/static/css/chat_studio.css app/static/js/studio.js app/static/js/chat_studio.js config.py requirements.txt tests/test_phase6_ui_attachments.py PHASE6_UI_AND_MULTIMODAL_README.md
git diff --cached --check
git diff --cached --name-only
git commit -m "feat: redesign learning studio and add document and voice chat"
git push
```

**Never stage `.env`, `.git`, `venv`, SPSS data or participant records.** If local changes differ from the uploaded source, review the diff before overwriting.

## Research scope

This patch is a UI/interaction enhancement, **not evidence of improved student motivation or growth mindset**. The questionnaire still requires supervisor review and ethics approval before genuine data collection. Don't let cosmetic features displace the November 3 submission, formal testing or dissertation writing.
