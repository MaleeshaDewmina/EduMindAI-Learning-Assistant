# EduMind AI — Phase 1 security and authentication patch (16 October 2026)

This PATCH is based on the code in the uploaded EduMindAI.zip and the preceding clean-source snapshot. It modifies only the listed source files. It DOES NOT include .env, database credentials, a local MySQL dump, a virtual environment or participant data.

## Before applying (Windows PowerShell)

1. Close the running Flask terminal.
2. Back up the entire `C:\Users\DELL\EduMindAI` folder (and separately back up your MySQL database).
3. Unzip this patch INSIDE `C:\Users\DELL\EduMindAI` so that `app`, `config.py`, `run.py`, `requirements.txt` and `tests` are at project-root level. Select overwrite for the patched source files. **Do not replace your real .env**.
4. Open PowerShell in your EduMindAI project root.
5. Activate the existing venv: `.\venv\Scripts\Activate.ps1`
6. Install the new dependency: `python -m pip install Flask-WTF==1.2.2` (or `python -m pip install -r requirements.txt`).
7. Generate a random SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
8. Open your LOCAL `.env`, replace the previous SECRET_KEY value with the generated value. Never share that value. Existing login sessions will be invalidated.
9. Your original archive contained real-looking credential fields. Rotate the old Groq API key and any exposed remote credentials. Update local `.env` with replacements.
10. Run `python -m pip install pytest` if pytest is missing.
11. Run `python -m pytest tests -q` and record the actual results.
12. Run `python run.py` and manually test login, invalid login, creating/editing/deleting/completing tasks, chatbot, questionnaires, mobile UI and logout.

## Changes

- Login success is confined to a valid password; invalid passwords stay logged out.
- Registration checks name/email/password/age on the server and safely handles duplicate emails.
- Flask-WTF CSRF protection applied to all existing POST forms (including logout).
- Logout, task completion and task deletion changed from GET to POST.
- Deleting a task detaches dependent progress log rows (while preserving the history).
- Removed the public `/db-test` endpoint that exposed database exception details.
- Flask interactive debugger is disabled in `run.py`.
- SECRET_KEY now must be present and at least 32 characters. Cookie defaults are tightened.
- Added isolated SQLite-based regression tests; **the original MySQL data is never touched by these tests**.

## Known limitations / next phase

- Automated tests HAVE NOT been executed in the assistant's environment because Flask and Flask-WTF packages were unavailable there. Python AST parsing and source/template inspections were run. The student should run pytest locally and share results.
- CSRF requires a network/browser cookie. Old open forms should be refreshed after applying the patch.
- Password hashing uses Werkzeug's configured default, not a custom encryption algorithm.
- This patch is a starting point, not a security certification. Test all routes and behavior on your own PC before the supervisor demonstration.
- Database configuration and `.env` values are not supplied. If the student has made newer local changes to affected files, compare and merge rather than overwriting blindly.
- Validation for tasks, chatbot message lengths, API timeout/rate limits, evaluation questionnaire design, lecturer role and research ethics are separate follow-up tasks.
