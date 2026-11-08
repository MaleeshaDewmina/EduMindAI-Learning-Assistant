# EduMind AI — Feedback + Groq hotfix (16 October 2026)

These changes build on your locally working Phase 3 copy.

## What the screenshots establish
- MySQL Error 1265 while saving `feedback_type='Consistency'`.
- Groq 404 for `llama-3.1-8b-instant` (deprecated for free/developer tiers on 16 August 2026).

## Installation
1. Back up `C:\Users\DELL\EduMindAI` and back up your MySQL database.
2. Stop Flask (Ctrl+C).
3. Copy the patch contents (`app`, `config.py`, `tests`) into your project root, merging folders. Do not copy your `.env` or expose API keys.
4. Open MySQL Workbench and execute `database/feedback_type_migration.sql` step-by-step. Inspect the column first. The ALTER converts the category from an old MySQL ENUM to the VARCHAR(30) specified by the current ORM model. MySQL DDL commits immediately; make a backup first.
5. Optionally add `GROQ_MODEL=openai/gpt-oss-20b` to the local `.env`. This is also the new default.
6. Run ` .\venv\Scripts\python.exe -m pytest tests -q` (20 tests targeted if all earlier files exist).
7. Restart Flask: ` .\venv\Scripts\python.exe run.py`.
8. Test Generate Feedback and ask the chatbot 'Explain a study strategy'. Use only test data and check no raw API errors enter chat history.

## How to verify which models your own Groq key can use
This command prints MODEL IDs, never the API key:

```powershell
.\venv\Scripts\python.exe -c "from dotenv import load_dotenv; load_dotenv(); import os; from groq import Groq; print('\n'.join(sorted(m.id for m in Groq(api_key=os.environ['GROQ_API_KEY']).models.list().data)))"
```

If `openai/gpt-oss-20b` is not accessible to your account, select an available chat-completion model and set `GROQ_MODEL=<that exact model id>` in your local `.env`.

## Limits
This patch does NOT perform a MySQL migration automatically; run the SQL only after backing up. The automated tests use SQLite, not your live MySQL. Syntax parsing passed in the build environment, but running Flask tests and live Groq requests requires your machine.
