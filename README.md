# Smart Investment & Portfolio Analytics

An India-focused investment decision-support platform that evaluates a user's financial profile, expenses, risk tolerance, goals, market context, and current portfolio to produce allocation suggestions and goal simulations.

## What This MVP Includes

- A Python analytics engine for:
  - income and expense analysis
  - emergency-fund checks
  - risk profiling
  - allocation recommendations
  - portfolio health scoring
  - goal-based planning
  - Monte Carlo-style scenario simulation
- A local API and static web server
- A polished single-page dashboard for:
  - financial profile
  - investment planner
  - market dashboard
  - portfolio analyzer
  - goal planner
  - AI-style explanation panel

## Project Structure

```text
backend/
  analytics/
    engine.py
    seed.py
  server.py
  tests_smoke.py
frontend/
  index.html
  styles.css
  app.js
README.md
requirements.txt
```

## Run Locally

Use any Python 3.11+ environment with `numpy` and `pandas` installed.

From the project root:

```powershell
python backend/server.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Smoke Test

```powershell
python -m pytest backend/tests_smoke.py
```

If `pytest` is not installed, you can still validate the core engine by importing `backend.analytics.engine` and calling `build_analysis()`.

## Notes

- The platform is framed as an educational analytics tool, not guaranteed financial advice.
- Seed data is included so the UI loads immediately.
- Market data is mocked but structured so a real ETL/API layer can replace it later.
- The current architecture is intentionally lightweight for local development; it can be upgraded to FastAPI, React, PostgreSQL, and scheduled ingestion without changing the core analytics concepts.

