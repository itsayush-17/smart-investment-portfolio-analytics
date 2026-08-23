# Smart Investment & Portfolio Analytics

[![CI](https://github.com/itsayush-17/smart-investment-portfolio-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/itsayush-17/smart-investment-portfolio-analytics/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-0b7285.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-1f6feb.svg)](https://www.python.org/)

An India-focused investment decision-support platform that analyzes a user's income, expenses, risk tolerance, financial goals, current portfolio, and market conditions to generate data-driven allocation guidance and scenario planning.

This project is positioned as an educational analytics tool, not a source of guaranteed financial advice.

## Highlights

- Personalized investment planning based on income, expenses, goals, and risk posture
- Emergency-fund readiness checks before recommending more aggressive allocations
- Portfolio analytics with diversification, concentration, and health scoring
- Goal-based monthly investment planning for major life events and retirement
- Monte Carlo-style simulation for conservative, base, and optimistic outcomes
- India-focused market and sector dashboard with international context
- Plain-language explanation layer that translates analytics into understandable insights

## Core Features

### Financial Planning Engine

- Monthly income and expense analysis
- Investable surplus estimation
- Emergency reserve gap calculation
- Goal prioritization and SIP estimates

### Investment Recommendation Engine

- Risk profiling based on age, horizon, stability, and loss tolerance
- Asset-allocation suggestions across equity, debt, gold, cash, and international exposure
- Monthly amount split across recommended asset buckets

### Portfolio Analyzer

- Asset allocation breakdown
- Sector concentration review
- Diversification scoring
- Portfolio health score and alignment score

### Market Intelligence

- Indian and global index snapshot
- Macro indicators such as inflation, yields, rates, and currency
- Sector comparison and simple market-regime classification

## Architecture

```text
Market + Macro Inputs
        |
        v
Seeded Data / Future ETL Layer
        |
        v
Analytics Engine
  - cash flow
  - emergency fund
  - risk score
  - allocation model
  - portfolio review
  - goal planning
  - simulation
        |
        v
Local API Server
        |
        v
Interactive Dashboard
```

## Tech Stack

- Backend: Python
- Analytics: NumPy, Pandas
- Frontend: HTML, CSS, JavaScript
- Serving: built-in Python HTTP server
- CI: GitHub Actions

## Repository Structure

```text
backend/
  analytics/
    __init__.py
    engine.py
    seed.py
  server.py
  tests_smoke.py
frontend/
  app.js
  index.html
  styles.css
.github/
  ISSUE_TEMPLATE/
  workflows/
CODE_OF_CONDUCT.md
CONTRIBUTING.md
LICENSE
README.md
SECURITY.md
requirements.txt
requirements-dev.txt
```

## Quick Start

### 1. Clone the repository

```powershell
git clone https://github.com/itsayush-17/smart-investment-portfolio-analytics.git
cd smart-investment-portfolio-analytics
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Run the app

```powershell
python backend/server.py
```

Open `http://127.0.0.1:8000`.

## Running Tests

```powershell
pytest backend/tests_smoke.py
```

## API Endpoints

- `GET /api/bootstrap`
  Returns the seeded analysis payload and market snapshot for initial page load.
- `GET /api/analyze`
  Returns the default analysis payload.
- `POST /api/analyze`
  Accepts a partial profile payload and recalculates the analytics response.

## Roadmap

- Replace seeded market data with scheduled ingestion from trusted APIs
- Upgrade the server layer to FastAPI
- Persist users, goals, and transactions in PostgreSQL
- Add authentication and multi-user support
- Add downloadable reports and richer visualizations
- Introduce historical portfolio tracking and rebalancing alerts

## Responsible Use

- This repository is intended for educational and analytical use.
- Returns and risk estimates are model-driven assumptions, not guarantees.
- Historical patterns and simulated outcomes do not ensure future performance.
- Users should validate important financial decisions with licensed professionals.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](./CONTRIBUTING.md) before opening a pull request.

## License

This project is licensed under the [MIT License](./LICENSE).

## Acknowledgments

This repository is designed to demonstrate a resume-worthy end-to-end analytics project spanning financial modeling, decision-support systems, backend engineering, frontend dashboards, and developer workflow hygiene.
