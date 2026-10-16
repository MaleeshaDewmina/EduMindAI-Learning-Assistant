# EduMind AI — Phase 5 (Evaluation module, v2 draft)

## IMPORTANT: ethics/research approval

This pilot questionnaire has **not** been validated as a psychological scale or approved for your current LMU project. Do not recruit participants, collect new participant responses or treat historical HND responses as EduMind AI usage outcomes without the necessary supervisor/institutional ethics clearance. The existing pre-test/post-test values are still stored and visible as legacy records, and are **not** mixed with Phase 5 scores. Only actual fresh accounts beginning study usage after their pre-test can represent a true before/after evaluation.

## Installation order on Windows

1. Backup your working `C:\Users\DELL\EduMindAI` folder and export your `edumind_ai_db` database via MySQL Workbench.
2. **Before replacing the Python files**, inspect and run `database/evaluation_items_phase5.sql` in MySQL Workbench using your local development database. This only adds the new item response table. It does not change existing evaluation rows. Confirm the SQL script's database name is correct.
3. Stop Flask with `Ctrl+C`.
4. Copy the **contents** of this patch into `C:\Users\DELL\EduMindAI`, merging folders and overwriting matching files. Never copy any `.env` or `.git` directory; this patch contains neither.
5. Run:
   ```powershell
   cd C:\Users\DELL\EduMindAI
   .\venv\Scripts\python.exe -m pytest tests -q
   .\venv\Scripts\python.exe run.py
   ```
6. Test using a **new test account**, with no genuine participant data: submit pre-test, verify post-test unlocking, submit post-test, verify item means and results. Check a second account sees no responses from the first. Existing legacy records should remain displayed with a legacy label.
7. If all checks pass, stage *only reviewed files*, commit, and push:
   ```powershell
   git status
   git add app/__init__.py app/models/evaluation_item_response.py app/routes/evaluation_routes.py app/services/evaluation_instrument.py app/templates/evaluation/form.html app/templates/evaluation/index.html database/evaluation_items_phase5.sql tests/test_evaluation_phase5.py PHASE5_README.md
   git diff --cached --check
   git diff --cached --name-only
   git commit -m "feat: add versioned matched evaluation questionnaire"
   git push
   ```

## Important design decisions

- **Same nine item wordings** in pre/post: three motivation, three confidence, three growth-mindset-oriented belief statements. They are exploratory custom questions requiring supervisor review and pilot validation.
- **Stage-specific questions are different**: E1 is *expected usefulness* before use; U1–U3 ask about actual experiences after use. They must never be numerically treated as the same measurement.
- Existing `evaluation_responses` columns are kept for backwards compatibility. Full v2 item scores are stored with an explicit instrument-version value in a new table `evaluation_item_responses` and are the only source of paired comparison scores. Pre-stage `usability_rating` stores E1 expected usefulness, while post-stage `usability_rating` stores U1 ease of navigation. **Never compare those legacy integers as pre/post usability.** Core integer fields store rounded scale means solely for legacy compatibility; never use the rounded integers for research analysis.
- The UI allows one v2 pre-test and one v2 post-test per user and prevents a v2 post-test before a v2 pre-test. There is no assessment of actual time spent using the system between stages—this must be controlled by the research protocol and verified via consented activity records.
- Pre-existing v1 rows are preserved and labelled legacy. They do not prevent a revised v2 pre-test.
- This questionnaire does not constitute a validated motivational or mindset measure. Even a matched pre/post difference without a control group is descriptive and **cannot establish causation**.
- Study accounts contain email addresses, so do not describe the collected data as anonymous. Seek approval for consent, pseudonymisation, data retention and whether any usage data is linked to questionnaire responses.

## Planned research protocol (for supervisor review only)

1. Approve instruments, information sheets, consent procedure, recruitment and required ethics clearance.
2. Recruit eligible participants on a voluntary basis; create accounts before prior study usage.
3. Record genuine pre-test before using the study features; define and document the usage period.
4. Allow planned system use and collect only approved activity data.
5. Record post-test, then analyse paired responses, missingness, scale reliability and limitations.
6. Keep HND 2025 dataset separate. Secondary analysis of it requires appropriate permission.

## Files included

- `app/__init__.py`: register the new model
- `app/models/evaluation_item_response.py`: item-level rating storage
- `app/routes/evaluation_routes.py`: stage validation and matched-score summary
- `app/services/evaluation_instrument.py`: one source of question wording
- `app/templates/evaluation/form.html` and `index.html`: revised user interface
- `database/evaluation_items_phase5.sql`: explicit MySQL migration
- `tests/test_evaluation_phase5.py`: regression tests
- `PHASE5_README.md`: this file

## Test target

24 earlier tests + 10 new Phase 5 tests = **34 expected tests**. This is only a target until pytest is executed on your Windows environment. Python source compilation, questionnaire consistency and template syntax were checked offline.
