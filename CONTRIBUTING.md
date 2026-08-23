# Contributing Guide

Thanks for your interest in improving Smart Investment & Portfolio Analytics.

## Ways to Contribute

- Report bugs
- Suggest improvements to the analytics logic or UX
- Improve documentation
- Add tests
- Contribute new features aligned with the project roadmap

## Development Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Run the application:

```powershell
python backend/server.py
```

Run tests:

```powershell
pytest backend/tests_smoke.py
```

## Contribution Expectations

- Keep changes focused and well-scoped
- Prefer readable code over clever code
- Add or update tests when behavior changes
- Update documentation when setup, architecture, or features change
- Avoid mixing refactors with unrelated functional changes

## Pull Request Checklist

- The branch is up to date with `main`
- The feature or fix is clearly explained
- Tests were added or updated when appropriate
- Local tests pass
- Documentation was updated where needed

## Project Scope Notes

- This project is an educational analytics platform
- Do not market outputs as guaranteed financial advice
- Preserve the India-focused investment context unless a change intentionally broadens scope

## Communication

For larger changes, open an issue first so the direction can be discussed before implementation begins.
