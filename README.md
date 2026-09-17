# Tross — Early Access & Token Authentication Backend (by BytQuest)

A small backend that collects early-access requests, issues access tokens, and validates them. It is built from Python components (a FastAPI/Flask-style server module plus standalone scripts) and JS/static frontend assets.

## Project structure

```
.
├── send_mails.py       # Sends early-access marketing emails (Gmail SMTP)
├── token_db.py         # FastAPI token authentication endpoint
├── token_db2.py        # Gmail IMAP inbox monitor + PostgreSQL token store
├── dist/               # Built JS assets (setup.js)
└── public/             # Static assets (Font Awesome fonts)
```

## Components

### `send_mails.py`

Sends an HTML early-access invitation email over Gmail SMTP (`smtp.gmail.com:587` with STARTTLS).

- Config constants: `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD` (lines 6-8).
- `recipients` list (~line 11) — the destination addresses.
- `send_email()` (~line 25) — connects, calls `starttls()` and `login()`, then sends the HTML message to each recipient.
- Runs via `python send_mails.py` (guarded by `if __name__ == "__main__"` ~line 38).

### `token_db.py`

A FastAPI app exposing `POST /authenticate`.

- Defines `AuthReq(BaseModel)` with field `token: str`.
- Defines a SQLAlchemy `Token` model mapped to table `token`.
- Depends on an external `server` module (`from server import app`) and a `get_db` dependency that is **not defined in this file** — see Prerequisites.

### `token_db2.py`

A long-running Gmail IMAP monitor that assigns access tokens and stores them in PostgreSQL.

- `generate_token(length=10)` — generates a random alphanumeric token.
- `create_table_if_not_exists()` — creates table `email_tokens` with columns `email` (PK), `token`, `created_at`.
- `token_exists(email_addr)` — looks up an existing token for an email address.
- `store_token(email_addr, token)` — inserts a token (`INSERT ... ON CONFLICT DO NOTHING`).
- `check_emails()` — polls UNSEEN messages every 5s; assigns a token when the subject contains `confirm` and the sender is in `ALLOWED_SENDERS`.
- Key constants: `IMAP_SERVER`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `ALLOWED_SENDERS`, `connection_string`, and `connection_pool` (a psycopg2 `SimpleConnectionPool`).
- Runs via `python token_db2.py`.

## Prerequisites & dependencies

- Python 3.x.
- An external `server.py` module that provides the FastAPI `app` and the `get_db` dependency. These are referenced by `token_db.py` but are **missing from this repository**, so `token_db.py` will not run until `server.py` is added.
- Third-party libraries used across the scripts:
  - `sqlalchemy`, `fastapi`, `pydantic`, `uvicorn`
  - `psycopg2` (including `psycopg2.pool`)
  - `python-dotenv` (`dotenv.load_dotenv`)
  - `requests`
- Python standard-library modules: `smtplib`, `imaplib`, `email`, `uuid`, `random`, `string`, `time`.
- `dist/` and `public/` hold the JS and static frontend assets (Font Awesome under `public/fonts/`).

## Configuration

The following placeholder values must be filled in before running:

- `EMAIL_ADDRESS` / `EMAIL_PASSWORD` — in both `send_mails.py` and `token_db2.py`.
- `recipients` — in `send_mails.py`.
- `ALLOWED_SENDERS` and `connection_string` — in `token_db2.py`.

`token_db2.py` imports `python-dotenv` (`load_dotenv`), so credentials can be supplied via a `.env` file. Storing secrets in environment variables rather than hardcoding them is recommended.

## Usage

Send the early-access invitation emails:

```bash
python send_mails.py
```

Start the inbox monitor (Ctrl+C to stop):

```bash
python token_db2.py
```

Run the FastAPI service that serves `token_db.py` (requires `server.py` to exist and expose `app`):

```bash
uvicorn server:app --reload
```

## Security note

Real credentials and connection strings must not be committed to the repository. Replace placeholders with environment variables (for example via a `.env` file that is kept out of version control).

## License / attribution

The Font Awesome assets under `public/fonts/` carry their own license — see `public/fonts/README.md`.
