# EduMind AI Phase 2 — Dashboard Analytics (16 October 2026)

## Apply
1. **Back up** the entire existing EduMindAI project and STOP the Flask server (Ctrl+C).
2. Extract this ZIP. Copy its `app/` and `tests/` folders into `C:\Users\DELL\EduMindAI`, merging folders and replacing files with the same names.
3. **Do not replace** `.env`, your MySQL database, `venv/`, or your original user data. These are not included.
4. From VS Code PowerShell:

   ```powershell
   cd C:\Users\DELL\EduMindAI
   .\venv\Scripts\python.exe -m pytest tests -q
   .\venv\Scripts\python.exe run.py
   ```

5. Open http://127.0.0.1:5000/dashboard/ after logging in and press Ctrl+Shift+R to refresh cached CSS/JS.

## Changes
- Three real-data charts: current task statuses, weekly completed tasks/recorded actions, indicator breakdown.
- The server provides per-user chart values; no hard-coded demonstration numbers.
- Contextual insight does not recommend completing nonexistent pending tasks.
- The motivation indicator is explicitly a behavioural proxy, not a validated psychological scale.
- Fixes missing-image 404 by removing a reference to a nonexistent login background image.
- Adds an SVG favicon and links it in the base template.
- Supports existing dark-mode toggle, mobile screens and no-task empty states.
- Provides four Phase 2 tests, using the in-memory SQLite fixture from Phase 1.

## Verification limits
- This patch was checked by static compilation/inspection. Runtime execution with your MySQL database and API was NOT performed here.
- Chart.js is currently loaded from a public CDN. Browser internet access is required for graphs to render; the fallback message explains this.
- All chart dates are UTC, matching the current database storage conventions. The last-seven-days graph is last seven calendar dates, including today.
- `calculate_motivation_score` currently persists a new score each time it is called; this is an existing analytics limitation and should be addressed before collecting evaluation data.
- Do NOT use behavioural scores as psychological motivation measurements.
- SECRET_KEY printed in any screenshot is exposed: generate a NEW one in your local `.env` and do not share it.

## Changed files
- app/routes/dashboard_routes.py
- app/services/dashboard_service.py (new)
- app/templates/dashboard/index.html
- app/static/js/dashboard_charts.js (new)
- app/static/css/app.css
- app/templates/base.html
- app/static/images/favicon.svg (new)
- tests/test_dashboard_analytics.py (new)
