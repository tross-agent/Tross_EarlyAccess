# Tross (Early Access) — Backend Scripts

A small **mixed Python / Node.js** codebase. It contains Python scripts used by the
*Tross by BytQuest* early-access flow (the product name and marketing copy appear in
`send_mails.py`), a FastAPI-based token authentication module, a Gmail inbox poller
that hands out access tokens, and an obfuscated Node.js bootstrap script.

There are **no build manifests** in this repository — no `requirements.txt`,
`pyproject.toml`, `package.json`, or lockfiles are committed. Dependencies are
documented below and must be installed manually.

---

## Repository Structure

```text
.
├── send_mails.py          # Gmail SMTP sender for the "Tross early access" HTML email
├── token_db.py            # FastAPI token-auth module (Pydantic + SQLAlchemy models)
├── token_db2.py           # Gmail IMAP inbox poller that assigns access tokens
├── dist/
│   └── setup.js           # Obfuscated Node.js ESM bootstrap/loader (see warning)
└── public/
    └── fonts/             # FontAwesome font assets (woff2/woff/ttf/svg/eot)
        └── README.md      # Upstream FontAwesome vendor readme
```

| Path | Purpose |
| --- | --- |
| `token_db.py` | FastAPI-based token authentication module. Defines a Pydantic `AuthReq` model (`token: str`) and a SQLAlchemy declarative `Token` model (table `token`: `id` primary key, `token` UUID column). Exposes a `POST /authenticate` endpoint. **Note:** this file does `from server import app` and calls `get_db()`, neither of which exist in this repository — the host FastAPI `app` and the DB session provider must be supplied externally. |
| `token_db2.py` | Gmail IMAP inbox poller that assigns access tokens. Monitors UNSEEN emails containing `confirm` from allowlisted senders (`ALLOWED_SENDERS`), generates a random 10-character token with `generate_token()`, and stores the email→token mapping in a PostgreSQL table `email_tokens` using `psycopg2.pool.SimpleConnectionPool`. Key helpers: `create_table_if_not_exists()`, `token_exists()`, `store_token()`, `check_emails()`. Polls every 5 seconds. |
| `send_mails.py` | Gmail SMTP sender for the "Tross early access" HTML email. `send_email()` opens STARTTLS on `smtp.gmail.com:587` and sends a `MIMEMultipart('alternative')` message per recipient. |
| `dist/setup.js` | Obfuscated Node.js ESM bootstrap/loader. **Flagged:** the file is intentionally obfuscated and resolves JSON-RPC endpoints, locates the last transaction of a `SENDER` address, and executes remote-fetched code through a detached `node -e` child process. See the Security Warning section below. |
| `public/fonts/` | FontAwesome font assets (woff2/woff/ttf/svg/eot) plus an upstream vendor `README.md`. |

---

## Prerequisites

- **Python 3** with the following packages:
  - `fastapi`
  - `uvicorn`
  - `sqlalchemy`
  - `pydantic`
  - `psycopg2-binary`
  - `python-dotenv`
- **PostgreSQL** database (used by `token_db2.py`).
- **Node.js** (needed to run `dist/setup.js`).

> No `requirements.txt` or `package.json` is committed to this repository, so the
> dependencies above must be installed manually, e.g.:
>
> ```bash
> pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary python-dotenv
> ```

---

## Configuration

Several module-level constants are **placeholders and must be filled in** before the
scripts will run.

### `token_db2.py` (lines 13–17)

```python
EMAIL_ADDRESS = ""      # Gmail account used to poll the inbox
EMAIL_PASSWORD = ""     # App password for the account above
ALLOWED_SENDERS = {""}  # Set of sender addresses allowed to receive a token
connection_string = ''  # PostgreSQL connection string for SimpleConnectionPool
```

`token_db2.py` additionally loads environment variables via `dotenv.load_dotenv()`,
so the values may also be supplied through a local `.env` file instead of editing the
source.

### `send_mails.py` (lines 8–11)

```python
EMAIL_ADDRESS = ""   # Gmail account used to send mail
EMAIL_PASSWORD = ""  # App password for the account above
recipients = [""]    # List of recipient email addresses
```

---

## Usage

### Start the IMAP poller (`token_db2.py`)

Polls the inbox in a loop, assigning tokens to qualifying "confirm" emails.

```bash
python token_db2.py
```

### Send the marketing email (`send_mails.py`)

Sends the "Tross early access" HTML email to each address in `recipients`.

```bash
python send_mails.py
```

### `token_db.py`

`token_db.py` is a FastAPI **router/module**, not a standalone script. It imports the
host application (`from server import app`) and depends on an external `get_db()`
session provider. It therefore **cannot be run on its own** — it must be mounted into
or imported by the host `server` application, which is not part of this repository.

---

## ⚠️ Security Warning

**Exercise caution with `dist/setup.js`.** This file is intentionally obfuscated and
its behavior includes resolving JSON-RPC endpoints, locating the last transaction of a
`SENDER` address, and executing remote-fetched code via a detached `node -e` child
process. Running it means executing code fetched from a remote source. Review and
de-obfuscate it, or run it only in a sandboxed environment you control.

**Keep credentials out of source control.** `token_db.py`, `token_db2.py`, and
`send_mails.py` currently contain empty credential placeholders. When you fill them in
(or use a `.env` file), make sure real secrets are never committed — add them to
`.gitignore` and prefer environment variables where possible.
