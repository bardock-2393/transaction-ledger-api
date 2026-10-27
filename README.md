# Transaction Ledger API

A backend API for a simple transaction ledger: create accounts, record credit/debit
transactions, read balances, and page through transaction history. Built with
FastAPI, SQLAlchemy, and SQLite.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000`. A SQLite file `ledger.db` is created
in the project root on first run (tables are created automatically on startup).

Interactive API documentation (the API Documentation deliverable for this
assessment) is served at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Run tests

```bash
pytest
```

Tests run against an isolated in-memory SQLite database per test — they do not
touch `ledger.db`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/accounts` | Create an account (`{"name": "..."}`) |
| GET | `/accounts/{id}/balance` | Get an account's current balance |
| POST | `/accounts/{id}/transactions` | Add a credit/debit transaction |
| GET | `/accounts/{id}/transactions` | List transactions (filter/paginate/sort) |
| POST | `/transfers` | Transfer money between two accounts (bonus) |

Amounts are sent and returned as **decimal strings** (e.g. `"10.50"`), not raw
JSON numbers — see `ASSUMPTIONS.md`.

See `ASSUMPTIONS.md` for the design decisions behind error codes, IDs, and
money handling.
