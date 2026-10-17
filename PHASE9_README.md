# EduMind AI — Phase 9: Lecturer role with student-controlled sharing

This ZIP is a **source overlay** for the existing Phase 7/8 application. It is not a full project replacement. It does not contain the `.env`, a MySQL database or student records.

## What it implements

- **Student** (primary internal actor): existing features; additionally grant and revoke specific lecturer permission through **Share Progress**.
- **Lecturer** (secondary internal actor): read-only dashboard of students who have **explicitly granted** access; task statistics, behavioural indicators and summary of the draft questionnaire constructs. **Not** raw answers, chat history, uploaded files, free-text comments or passwords.
- **Groq AI Service** (external supporting UML actor): existing AI chatbot API; no new role or database user.
- Student and Lecturer are separate login roles. Lecturer accounts are created by an authorised operator using a local terminal script; the public register form cannot create lecturer accounts.
- SQL migration adds `users.role` and `lecturer_access_grants`. All pre-existing users remain `student`.
- Reporting is read-only. Lecturer views calculate pending/overdue status in memory, without changing `study_tasks` or writing `motivation_scores`.

## Before installation — REQUIRED

1. **Back up** your existing `C:\Users\DELL\EduMindAI` project and your MySQL `edumind_ai_db` using Workbench's Data Export.
2. **Stop Flask** (`Ctrl + C`).
3. **First execute the migration** `database/lecturer_role_phase9.sql` in MySQL Workbench, selecting the FULL script (`Ctrl+A` then Execute). Do not drop or recreate any existing tables.
4. Check `SHOW COLUMNS FROM users LIKE 'role';` and `SHOW TABLES LIKE 'lecturer_access_grants';`. If your old users had an account with a non-student role pre-existing, confirm it manually.
5. **Then** merge this ZIP's **contents** into `C:\Users\DELL\EduMindAI` (only matching source files replaced). Preserve local `.env`, `.git`, `venv`, and existing project files.

**Why SQL first?** The updated User model reads the newly added `role` column. Running updated code against an old schema may fail at login; the migration must be completed first.

## Test before creating accounts

From VS Code PowerShell:

```powershell
cd C:\Users\DELL\EduMindAI
.\venv\Scripts\python.exe -m pytest tests -q
```

Expected target: **61 passed** if all previous 50 tests are installed, plus 11 new lecturer tests. This target **has not been runtime-verified** in the build environment. If tests fail, share the first traceback and do not commit yet. Automated tests use a separate SQLite test database; manually test the live MySQL migration.

## Create the lecturer login securely

**After** migration and passing tests, run in the local PowerShell terminal:

```powershell
.\venv\Scripts\python.exe scripts\create_lecturer.py
```

Provide the lecturer's **verified** full name, email and a unique password at the password prompts. The password input is hidden. Do not paste lecturer credentials or screenshots of the password into chat. The script refuses an existing email rather than silently promoting a student.

**Demo note:** Use a verified test lecturer account for a project demo. Do not create an account impersonating Ms. Hashini or another person without permission.

## Live demo — two browsers or separate browser profiles

1. Student signs in as an ordinary student. In the sidebar choose **Share Progress**. Initially no grants should exist.
2. Enter the lecturer's verified account email and select **Grant access** (CSRF-protected POST).
3. In a separate incognito window / browser profile, log in as the lecturer at `/auth/login` using the *same login screen*. Lecturer is redirected to `/lecturer/`.
4. Lecturer sees only students who grant access. Select **View report** to see read-only progress and questionnaire construct means.
5. Confirm lecturer has **no** student study-planner, chatbot or evaluation-forms access, and cannot browse other students' `/lecturer/students/<id>` URLs.
6. Student revokes permission from **Share Progress**. Reload the lecturer report: it must now show `404` and the student must disappear from the lecturer dashboard.
7. Confirm all existing student features still work and no data has been lost.

**Ethics/privacy:** Access permission in the application does not constitute ethics approval or research participation consent. Do not expose genuine identifiable student records to a lecturer until authorisation, student privacy notices and institutional approval are confirmed. Avoid including student names/emails in published screenshots.

## GitHub

After reviewing staged files for credentials and running tests:

```powershell
git status
git add app/__init__.py app/models/user.py app/models/lecturer_access_grant.py app/routes/auth_routes.py app/routes/lecturer_routes.py app/services/lecturer_reporting.py app/templates/base.html app/templates/partials/sidebar.html app/templates/lecturer app/static/css/lecturer.css database/lecturer_role_phase9.sql scripts/create_lecturer.py tests/test_lecturer_phase9.py docs/lecturer_use_cases_phase9.md PHASE9_README.md
git diff --cached --check
git diff --cached --name-only
git commit -m "feat: add consent-controlled lecturer reporting role"
git push
```

Never commit `.env`, real participant exports or lecturer passwords.

## Known boundaries

- Student invitation/consent is scoped to **read-only limited reports**. There is no lecturer task editing, enrolment management, attendance register or cross-department access.
- Groq is an **external actor**, not a human user role.
- Draft pre/post scores are **exploratory self-report means** rather than a validated motivational assessment; the 50/25/25 score is a custom behavioural proxy.
- Automatic dataset export and research participant management are out of scope and should not be represented as implemented.
- Current application timestamps use naive UTC; a full timestamp migration needs separate verified work.
- Before public deployment, audit role setup, revocation, retention, login rate limiting, transport security, logging and privacy policies.
