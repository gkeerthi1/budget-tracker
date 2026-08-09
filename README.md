# Budget Tracker

A web app to record income and expenses, set monthly budget limits (overall and
per-category), and get threshold notifications when spending gets close to the limit.
Built for CISC 594 as a two-version semester project.

## Stack
- **Backend:** Python 3.11+, Flask, SQLite
- **Frontend:** Angular
- **Testing:** pytest, Flask test client, Playwright

## Backend setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
The API runs at http://127.0.0.1:5000. Check http://127.0.0.1:5000/api/health.

## Running tests
```bash
cd backend
source venv/bin/activate
pytest
```

## Branching
- `master` is always working and protected (PR + 1 approval required).
- Features are built on `feature/*` branches, merged via reviewed PRs.
- Releases are tagged: `v1.0` after Version 1, `v2.0` after Version 2.
