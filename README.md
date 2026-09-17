# Tross Early Access

A small Python toolkit for sending early-access marketing emails and issuing access tokens.

**Tross by BytQuest.**

## Features

- **Marketing email sender** (`send_mails.py`): sends a hardcoded HTML early-access email to a list of recipients via Gmail SMTP (STARTTLS, `smtp.gmail.com:587`).
- **Inbox monitor & token issuer** (`token_db2.py`): polls a Gmail inbox via IMAP (`imap.gmail.com`), looks for `UNSEEN` messages whose subject contains `"confirm"` from allowlisted senders, generates a random 10-character alphanumeric token, and stores it in PostgreSQL (table `email_tokens(email PRIMARY KEY, token, created_at)`), skipping duplicates via `ON CONFLICT DO NOTHING`.
- **Token auth service** (`token_db.py`): a partial FastAPI + SQLAlchemy async module exposing `POST /authenticate` to validate a token.
  - **Note:** this module is incomplete / non-runnable as committed — it imports `app` from a missing `server` module and references an undefined `get_db`.

## Repository structure

```
.
├── send_mails.py    # Sends the hardcoded HTML early-access email to a recipient list via Gmail SMTP
├── token_db.py      # Partial FastAPI + SQLAlchemy async module exposing POST /authenticate (incomplete)
├── token_db2.py     # Polls a Gmail inbox via IMAP and issues/stores tokens in PostgreSQL
├── dist/            # Build output (contains setup.js); not otherwise documented here
└── public/          # Static assets (fonts/); not otherwise documented here
```

## Prerequisites

- **Python 3.9+** — the code uses `Mapped[...]` typing and f-strings.
- A **Gmail account** with an **App Password** (2FA enabled) for both SMTP and IMAP access.
- A **PostgreSQL database**.

### Third-party dependencies

As actually imported by the source files:

- `psycopg2`
- `python-dotenv`
- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `pydantic`
- `requests`

Standard-library modules used: `smtplib`, `imaplib`, `email`, `uuid`, `random`, `string`, `time`, `asyncio`, `json`, `os`, `urllib`.

## Installation

```bash
pip install psycopg2-binary python-dotenv fastapi uvicorn sqlalchemy pydantic requests
```

Suggested `requirements.txt`:

```txt
psycopg2-binary
python-dotenv
fastapi
uvicorn
sqlalchemy
pydantic
requests
```

## Configuration

The following placeholder constants **must be filled in before running**:

| File | Constant | Description |
| --- | --- | --- |
| `send_mails.py` | `EMAIL_ADDRESS` | Gmail address used to send the email. |
| `send_mails.py` | `EMAIL_PASSWORD` | Gmail App Password for that account. |
| `send_mails.py` | `recipients` | List of recipient email addresses. |
| `token_db2.py` | `EMAIL_ADDRESS` | Gmail address to monitor via IMAP. |
| `token_db2.py` | `EMAIL_PASSWORD` | Gmail App Password for that account. |
| `token_db2.py` | `ALLOWED_SENDERS` | Set of email addresses permitted to trigger token issuance. |
| `token_db2.py` | `connection_string` | PostgreSQL DSN used to build the connection pool. |

> **Note:** `dotenv.load_dotenv()` is imported in `token_db2.py` but is **never called**, so `.env` loading is currently not active. Either call `load_dotenv()` at startup or export the values as environment variables.

## Usage

### Send the marketing email

```bash
python send_mails.py
```

Sends the HTML early-access email to every address in `recipients`.

### Run the inbox monitor & token issuer

```bash
python token_db2.py
```

Creates the `email_tokens` table if it does not exist, then polls the inbox every **5 seconds** until you press **Ctrl+C**.

### Token auth service

`token_db.py` **cannot be run standalone** — it depends on a missing `server` module (which must provide `app`) and an undefined `get_db` dependency. These must be supplied before it can run.

## How the token flow works

1. A confirmation email is received in the monitored Gmail inbox.
2. The sender is checked against `ALLOWED_SENDERS`.
3. If the subject contains `"confirm"` and the sender is allowlisted, a token is generated via `generate_token(10)`.
4. The token is stored in the `email_tokens` table (skipping duplicates via `ON CONFLICT DO NOTHING`).
5. (Intended) The token is validated by the FastAPI `POST /authenticate` endpoint.

## Notes / known limitations

- Credentials are committed as **empty placeholders**; fill them in (or use environment variables) before running.
- `token_db.py` is **incomplete** and not runnable as committed.
- The contents of `dist/` and `public/` are **not documented here** — verify before relying on them.
