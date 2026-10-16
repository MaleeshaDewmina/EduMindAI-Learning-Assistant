# EduMind AI — Phase 3: Planner / Progress / Feedback

**Use after installing and locally verifying the Phase 1 and Phase 2 patches.**

## What changed

1. Planner checks 1–150 character titles, 100-character subjects, 3000-character descriptions, priority, status and deadline on the **server**. It does not rely on browser validation alone.
2. Completion is idempotent: clicking Done twice does not duplicate the Task Completed progress event.
3. Editing an overdue task to a future deadline can return it to Pending. Completed tasks preserve original completion timestamps unless reopened.
4. Task edit and delete remain restricted by the authenticated user's ID.
5. Generate Feedback now requires POST and an anti-CSRF token, so opening a link cannot create feedback records.
6. Feedback rules now handle no-tasks and all-completed situations and describe app activity without claiming to diagnose motivation.
7. Progress and feedback pages explicitly describe the index as a *custom behavioural measure*, not validated psychology.
8. Seven new automated tests cover these behaviours.

## Installation (Windows / VS Code)

1. Stop Flask with Ctrl+C and make a copy of the entire EduMindAI project folder.
2. Extract ZIP, copy its contents into `C:\Users\DELL\EduMindAI`, and merge/replace only matching files. **Do not overwrite your .env.**
3. In VS Code PowerShell:

```powershell
cd C:\Users\DELL\EduMindAI
.\venv\Scripts\python.exe -m pytest tests -q
.\venv\Scripts\python.exe run.py
```

4. In the browser: create task, edit deadline, mark done, revisit it, open Progress, generate Feedback, open Dashboard. Check the counts agree on all pages.

## Expected results and limitations

- Previous phases had **10 passing tests** on the user's computer. This adds **7 tests**, so **17 passing** is the intended result if the complete test suite is present and no regressions occur.
- Automated tests here run using SQLite in memory; test critical behaviour manually on your actual MySQL database as well.
- This patch does not yet alter the research evaluation forms, which need supervisor-approved matching pre/post questions before participants use them.
- The app currently stores naive UTC timestamps; `datetime-local` has no timezone. Verify deadline interpretation for your local timezone before participant evaluation.
- Existing `datetime.utcnow()` deprecation warnings may still appear. They are not test failures.
- Every page-load currently stores a `motivation_scores` snapshot, a topic to improve before final reporting if it affects research data quality.
