# Tross Early Access System

A Python-based early-access system for the **Tross** product (by BytQuest). It sends outreach emails, collects
confirmations from a Gmail inbox, issues access tokens stored in PostgreSQL, and exposes an authentication
endpoint for validating those tokens.

## Repository structure

| File | Purpose |
| --- | --- |
| `send_mails.py` | Standalone SMTP sender. Blasts a hardcoded HTML early-access marketing email to a `recipients` list via Gmail SMTP. |
| `token_db2.py` | Gmail IMAP inbox monitor. Polls every 5s for unread emails with `confirm` in the subject from `ALLOWED_SENDERS`, generates a random 10-character token, and stores it in the Postgres `email_tokens` table. |
| `token_db.py` | FastAPI + SQLAlchemy async fragment exposing a `POST /authenticate` endpoint that validates a token against a `token` table. Note: it depends on `from server import app` and a `get_db` dependency that are **not** included in this repo, so it is not runnable standalone. |

## Prerequisites

- Python 3.x
- A PostgreSQL database
- A Gmail account with an **App Password** (2-Step Verification enabled), since Gmail SMTP/IMAP require it
- Network access to `smtp.gmail.com:587` and `imap.gmail.com:993`

## Dependencies / Installation

Install the third-party packages (gathered from the imports):

```bash
pip install fastapi uvicorn pydantic sqlalchemy psycopg2-binary python-dotenv
```

The following standard-library modules are also used and need no installation:
`smtplib`, `imaplib`, `email`, `random`, `string`, `uuid`, `time`, `os`, `json`, `urllib`.

> Note: you can use `psycopg2` instead of `psycopg2-binary`; the `-binary` package is the convenient choice for local development.

## Configuration

The modules currently use hardcoded, module-level constants. All of the credential and connection placeholders
below are **empty strings/sets** and must be filled in before running:

| File | Constant | Notes |
| --- | --- | --- |
| `send_mails.py` | `EMAIL_ADDRESS` (L7) | Gmail address used to send. Empty by default. |
| `send_mails.py` | `EMAIL_PASSWORD` (L8) | Gmail App Password. Empty by default. |
| `send_mails.py` | `recipients` (L10) | List of recipient email addresses. Contains a single empty string by default. |
| `token_db2.py` | `EMAIL_ADDRESS` | Gmail address to monitor. Empty by default. |
| `token_db2.py` | `EMAIL_PASSWORD` | Gmail App Password. Empty by default. |
| `token_db2.py` | `ALLOWED_SENDERS` | Set of senders permitted to receive tokens. Empty by default. |
| `token_db2.py` | `connection_string` | PostgreSQL DSN. Empty by default. |

The SMTP/IMAP host and port constants are pre-set and generally do not need changing:

- `SMTP_SERVER = "smtp.gmail.com"`
- `SMTP_PORT = 587`
- `IMAP_SERVER = "imap.gmail.com"`

> **Security note:** `python-dotenv` is imported but not yet wired up. Moving these secrets into a `.env` file
> (rather than hardcoding them in source) is a recommended improvement.

## Usage

### 1. Send outreach emails

Edit the constants (`EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `recipients`) in `send_mails.py`, then run:

```bash
python send_mails.py
```

The script prints a confirmation line per recipient (e.g. `✅ Email sent to <recipient>`). The email body and
subject are hardcoded in the script.

### 2. Run the token-issuing monitor

Configure the constants in `token_db2.py`, ensure the target PostgreSQL database exists, then run:

```bash
python token_db2.py
```

The script creates the `email_tokens` table automatically via `create_table_if_not_exists()`, then polls
the inbox every 5 seconds. Stop it with `Ctrl+C`.

### 3. Auth endpoint

This requires an external `server.py` that provides the FastAPI `app` object and the `get_db` dependency
(**not included in this repo**). Once that module is present, run:

```bash
uvicorn server:app
```

The endpoint is `POST /authenticate`.

## How it works / data flow

1. `send_mails.py` sends outreach emails requesting recipients to reply with `confirm`.
2. `token_db2.py` detects the confirmation email, generates a random token, and stores it in the `email_tokens` table.
3. `token_db.py`'s `/authenticate` endpoint validates tokens via `POST` with a JSON body of the form:

   ```json
   { "token": "<token>" }
   ```

## Known limitations / caveats

- Credentials and connection strings are currently hardcoded as **empty placeholders**; there is no `.env` wiring yet.
- `token_db.py` is **incomplete and not runnable standalone**: it is missing the external `server.py` module
  (for `app`) and the `get_db` dependency, and it mixes SQLAlchemy Core access (`Token.select()`, `Token.c`)
  with an ORM-declared model.
- The two database modules operate at different layers (SQLAlchemy async ORM in `token_db.py` vs. raw `psycopg2`
  in `token_db2.py`) and use different table names (`token` vs `email_tokens`).
- There is no `requirements.txt`, no tests, no CI configuration, and no license file present.
- Logging is `print()`-based.
- `token_db2.py` has a duplicate `decode_header` import and an unused `smtplib` import.
