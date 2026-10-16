# EduMind AI — Phase 4 Chatbot UX & Privacy Patch (16 October 2026)

## Purpose
Apply **only after** Phase 3 and the Feedback & Groq Hotfix. The user has demonstrated 20 passing tests and a working Groq response.

## Changes (no database migration needed)
- Escapes all model-generated text, then renders **bold** and line breaks without trusting HTML from the model.
- Keeps the user message escaped by Jinja as before.
- Adds a 2,000-character limit on chatbot requests (HTML + server-side).
- Adds a CSRF-protected `POST /chatbot/clear` action, allowing a student to remove only their own saved chat records. The action requires user confirmation in the browser.
- Shows a concise reminder that AI is fallible and not to provide sensitive information.
- Improves mobile/dark-theme formatting and increments the CSS cache version.
- Adds four regression tests; expected total: **24** passing tests if all prior 20 remain.

## Installation (Windows PowerShell)
1. Stop Flask using `Ctrl+C`. Back up your working `C:\Users\DELL\EduMindAI` folder and MySQL if you plan to clear real conversations.
2. Extract this ZIP into the root of your existing EduMindAI project, merging folders and replacing matching files. **Do not create a nested Phase4 directory**.
3. Do NOT remove, replace, or share `.env`. This ZIP contains no credentials or database backup.
4. Run:

```powershell
cd C:\Users\DELL\EduMindAI
.\venv\Scripts\python.exe -m pytest tests -q
.\venv\Scripts\python.exe run.py
```

## Manual acceptance checklist
- Ask the Groq chatbot `Give me **three** ways to prepare for an exam` and verify bold headings and paragraphs display without literal `**`.
- Submit 2,001 characters (via a crafted POST in a test, not manually necessary); application should reject.
- Check `Clear Chat History` only when messages exist; it prompts before deletion; cancel does nothing.
- If confirmed, current user's saved chat is permanently deleted; another user's messages are unaffected.
- Check desktop and mobile theme/layout.

## Important research/ethics note
Do not clear real participant data without following their consent, data retention rules and approved procedure. For removing legacy test messages, the clear button deletes the entire current student's chat history. The button is optional.

## Validation statement
This patch is a source-level fix. Syntax, template structure, and ZIP archive were validated in the preparation environment; **Flask integration tests must be run on your Windows environment**. It is not a claim of complete security certification.
