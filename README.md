# Tross Early Access

**Tross early-access** is a small set of Python scripts by **BytQuest** that
automate an invite-only early-access programme. They (a) send early-access
invitation emails to a list of recipients, (b) monitor a Gmail inbox and mint
early-access tokens when a confirmation email arrives, and (c) expose a FastAPI
endpoint that authenticates a submitted token against the database.

## Components

| File | Description |
| --- | --- |
| `send_mails.py` | Sends a pre-built HTML marketing email (subject **"Early Access to Tross — Build Faster, Debug Smarter"**) to a list of recipients over Gmail SMTP using `smtplib` (`smtp.gmail.com:587` + `STARTTLS`). Key constants: `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `recipients`. Main function: `send_email()`. Run via `python send_mails.py`. |
| `token_db2.py` | Polls a Gmail inbox over IMAP (`imap.gmail.com`) every 5 seconds for UNSEEN emails whose subject contains "confirm" from `ALLOWED_SENDERS`. For each, it generates a 10-character alphanumeric token and stores it in a PostgreSQL table `email_tokens` (using a `psycopg2` connection pool). Functions: `generate_token()`, `create_table_if_not_exists()`, `token_exists()`, `store_token()`, `check_emails()`. Run via `python token_db2.py` (loops until `Ctrl+C`). |
| `token_db.py` | FastAPI module defining a SQLAlchemy `Token` model (table `token`) and a `POST /authenticate` endpoint that validates a submitted token. Depends on a `server` module (`from server import app`) that is **not present** in the repository root — see [Notes / known limitations](#notes--known-limitations). |

## Prerequisites

- **Python 3.x**
- A **Gmail account** with an **App Password** enabled for SMTP and IMAP access.
- A **PostgreSQL** database.

## Installation

`smtplib` and `email` are part of the Python standard library and are **not**
listed below. Install the inferred third-party dependencies with:

```bash
pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary python-dotenv requests
```

There is currently no `requirements.txt` in the repository. Creating one (e.g.
via `pip freeze > requirements.txt`) is recommended.

## Configuration

Credentials are currently stored as **empty module-level string constants** that
must be filled in before running:

- **`send_mails.py`**: `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `recipients`
- **`token_db2.py`**: `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `ALLOWED_SENDERS`,
  `connection_string`

> **Security note:** Move these secrets out of source and into environment
> variables / a `.env` file. `token_db2.py` already imports `python-dotenv`, so
> it can be wired up to load them directly.

## Usage

Send the early-access invitation emails:

```bash
python send_mails.py
```

Start the inbox monitor that mints and stores tokens (runs until `Ctrl+C`):

```bash
python token_db2.py
```

Run the FastAPI authentication service:

```bash
uvicorn <module>:app --reload
```

> Note: `token_db.py` imports `app` from a `server` module (`from server import
> app`) that is not present in the repository root, so the module cannot be run
> as-is.

## Notes / known limitations

- **Plain-text secrets:** credentials are currently empty string constants in
  the source files and must be populated manually before running.
- **Incomplete API module:** `token_db.py` references an undefined `get_db`
  dependency and an external `server` module that is not included, so it cannot
  run standalone.
- **Unrelated assets:** `dist/setup.js` and the Font Awesome assets under
  `public/` exist in the repository but are not part of the documented flow.

## License

See the repository for license details. © BytQuest.
