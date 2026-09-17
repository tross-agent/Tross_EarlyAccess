# Tross — Email & Token-Auth Early Access

> A small Python email + token-auth toolkit that drives the Tross early-access signup flow: outbound early-access emails, token lookups, and an IMAP "confirm" inbox monitor.

## Overview

This repository contains the scripts behind the **Tross early-access flow**. It is assembled
from a lightweight **Python email + token-auth toolkit**: one module sends the early-access
announcement email over Gmail SMTP, one module exposes a FastAPI route that authenticates a
supplied token against a database, and one module watches a Gmail inbox over IMAP for
confirmation replies, generates one-time tokens, and stores them in PostgreSQL.

The repo is a loose collection of scripts rather than a packaged application. There is no
`requirements.txt`, no packaging metadata, and the Python modules do not import one another —
each is intended to be run independently (see [Usage](#usage)).

## Repository structure

```
.
├── send_mails.py          # Gmail SMTP early-access email sender
├── token_db.py            # FastAPI auth route + SQLAlchemy Token model
├── token_db2.py           # Gmail IMAP monitor + token generation + PostgreSQL storage
├── dist/
│   └── setup.js           # Bundled/obfuscated build artifact (NOT runnable source)
└── public/
    └── fonts/             # Font Awesome font assets + attribution README
```

## Components

### `send_mails.py` — early-access email sender

Sends the hardcoded early-access HTML email to a list of recipients over Gmail SMTP.

- Connects to `smtp.gmail.com:587` and calls `starttls()` before authenticating.
- `send_email()` (defined at `send_mails.py:38`) builds the `MIMEText` HTML message and
  delivers it to `recipients`.
- Configuration constants live at the top of the file:
  - `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD` — lines 6–9
  - `recipients` — line 11
  - `subject` — line 13
  - `html_body` — line 15

### `token_db.py` — FastAPI token-authentication route

A route module for a FastAPI application.

- `AuthReq` — a Pydantic request model (line 21) carrying the token supplied by the client.
- `Token` — a SQLAlchemy model mapped to the table `token` (`__tablename__ = 'token'`,
  lines 25–30).
- `POST /authenticate` (~line 27) — looks up the supplied token in the database and raises
  `HTTPException` if the token is missing or invalid.

> **Note:** this module is not standalone. It depends on `from server import app` and a
> `get_db` dependency. `server.py` **does not exist in this repository**, so `token_db.py`
> cannot run on its own — it is intended to be imported by an external FastAPI entry point.

### `token_db2.py` — Gmail IMAP confirm-inbox monitor

Watches a Gmail inbox over IMAP for confirmation replies and issues one-time tokens.

- Connects to `imap.gmail.com`, reads **UNSEEN** messages, and matches `"confirm"` subjects
  from the allow-listed senders in `ALLOWED_SENDERS`.
- Generates a random token via `generate_token()` (line 25).
- Stores tokens in the PostgreSQL table `email_tokens` using `psycopg2` pool patterns.
- Helpers:
  - `create_table_if_not_exists()` — line 28
  - `token_exists()` — line 41
  - `store_token()` — line 49
  - `check_emails()` — line 60
- Under `__main__` (line 91) it runs an infinite loop, polling every 5 seconds.

### `public/fonts/` — Font Awesome font assets

Static font assets used by the Blockchain Explorer front-end:

- Font Awesome free icon set: `fa-solid-900`, `fa-regular-400`, `fa-brands-400`
  (each provided as `.woff2`, `.woff`, `.ttf`, `.svg`, `.eot`).
- `README.md` in this directory documents the app's custom font stack
  (`BlockchainFont-Regular/Bold`, `TechMono-Regular`) and notes that the application falls
  back to system fonts when the custom fonts are absent. The fonts are referenced by
  `public/index.html`.

### `dist/setup.js` — bundled build artifact (do not run)

`dist/setup.js` is a single-line, minified/**obfuscated** JavaScript bundle (~27 KB). It is a
build output, not human-readable source — there is no JavaScript source tree in this
repository, and no Python module imports it.

Inspection of the bundle shows it imports Node built-ins (`http`, `https`, `zlib`, `URL`,
`spawn`) and defines remote-endpoint/keep-alive HTTP logic. Its top-level behavior fetches
content from a remote URL and then `eval()`s that content and launches it via a detached
`spawn(...)`. **This is suspicious "dropper"-style behavior.**

⚠️ **Do not run `dist/setup.js`.** It is not a setup script, installer, or build tool for this
project, and executing it would download and execute untrusted remote code. It is documented
here only so the file is not mistaken for legitimate tooling.

## Configuration

All credentials are currently **hardcoded placeholders** and must be supplied before the
scripts will work.

| File | Constant(s) | Location | Purpose |
| --- | --- | --- | --- |
| `send_mails.py` | `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD` | lines 6–9 | Gmail SMTP connection + login |
| `send_mails.py` | `recipients` | line 11 | List of email recipients |
| `token_db2.py` | `IMAP_SERVER`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `ALLOWED_SENDERS`, `connection_string` | lines 12–17 | IMAP inbox + PostgreSQL connection |

**Recommendation:** move these values out of source and into environment variables / a `.env`
file. `token_db2.py` already imports `load_dotenv` but does not currently call it — wiring it
up is the natural first step.

## Installation

Python dependencies inferred from the imports:

- **Standard library** (no install required): `smtplib`, `email`, `imaplib`, `random`, `time`.
- **Third-party**: `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`,
  `psycopg2` (or `psycopg2-binary`), `python-dotenv`.

There is **no `requirements.txt`** in this repository yet. To install the third-party
dependencies manually:

```bash
pip install fastapi uvicorn pydantic sqlalchemy psycopg2-binary python-dotenv
```

## Usage

Each script is run independently:

```bash
# Send the early-access email to the configured recipients
python send_mails.py

# Start the IMAP confirm-inbox monitor (polls every 5s; runs until stopped)
python token_db2.py
```

`token_db.py` is **not runnable on its own**. It is a route module for an external FastAPI
application (`server.py`) that must provide the `app` object and the `get_db` dependency. To
use it, mount its routes on that application and launch it with an ASGI server, e.g.:

```bash
uvicorn server:app --reload
```

## Security note

The credentials in `send_mails.py` and `token_db2.py` are committed as **placeholders only**.
Never commit real SMTP/IMAP passwords or database connection strings to version control — use
environment variables or a `.env` file that is excluded via `.gitignore`. Additionally, do not
run `dist/setup.js`; as described above, it is an obfuscated artifact that downloads and
executes remote code.
