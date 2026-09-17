# Tross — Early Access

Tross is a Gmail-driven early-access token distribution system. It sends promotional emails to a list of recipients, monitors an inbox for confirmation replies, assigns each confirmed (allowed) sender a unique token, and validates those tokens through a FastAPI authentication endpoint.

> **Status / caveats.** This repository is a loose collection of three standalone Python scripts. There is **no dependency manifest** (no `requirements.txt`, `pyproject.toml`, `Pipfile`, or `setup.py`), **no `server` module**, and **no web frontend build**. `token_db.py` imports a `server` module and a `get_db` dependency that are **not present in this repo**, so the FastAPI API cannot run as-is without providing them. See the notes in each section below.

## Architecture / components

### `send_mails.py` — standalone SMTP email blast
Sends a hardcoded "Tross — Early Access" HTML promo to a list of recipients over Gmail SMTP.

- **Entry point:** `python send_mails.py` (`if __name__ == "__main__":` → `send_email()`).
- **Transport:** `smtp.gmail.com` on port `587` using `STARTTLS` (`smtplib.SMTP` + `.starttls()` + login).
- **Config constants:** `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `recipients` (a list), plus `subject` and `html_body` (the hardcoded HTML body / subject being sent).

### `token_db2.py` — IMAP Gmail inbox monitor / token assigner
Polls a Gmail inbox over IMAP and assigns a unique 10-character alphanumeric token to allowed senders whose subject contains `confirm`, persisting tokens in PostgreSQL.

- **Entry point:** `python token_db2.py`. It runs a loop that checks the inbox every **5 seconds**; press **Ctrl+C** to stop.
- **Transport:** IMAP over SSL against `IMAP_SERVER` (`imap.gmail.com`), selecting the `inbox` and searching for `UNSEEN` messages.
- **Token format:** `generate_token(length=10)` using `random.choices` over `string.ascii_letters + string.digits`.
- **Storage:** a `psycopg2` connection pool (`psycopg2.pool.SimpleConnectionPool`) backed by a PostgreSQL table:

  ```sql
  CREATE TABLE IF NOT EXISTS email_tokens (
      email      VARCHAR PRIMARY KEY,
      token      VARCHAR,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```

  New tokens are inserted with `INSERT ... ON CONFLICT DO NOTHING`, and existing tokens are looked up with `SELECT token FROM email_tokens WHERE email = %s`.
- **Config:** `IMAP_SERVER`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `ALLOWED_SENDERS` (a `set`), and `connection_string` (the PostgreSQL DSN).
- **Environment loading:** already imports `dotenv` / `load_dotenv` (so `.env` values can be read), though the constants themselves are currently hardcoded placeholders.

### `token_db.py` — FastAPI token-authentication module
Defines the request model and ORM entity for token validation, and registers a `POST /authenticate` endpoint.

- **`AuthReq`** — a `pydantic` `BaseModel` with a single field: `token: str`.
- **`Token`** — a SQLAlchemy ORM model (`declarative_base()`) mapped to the table `token`, with columns `id` (`Mapped[int]`, primary key) and `token`.
- **`POST /authenticate`** — the `authenticate(auth_req: AuthReq, db=Depends(get_db))` handler looks up the supplied token via `Token.select().where(Token.c.token == token)` and calls `db.execute(query).fetchone()`, raising `HTTPException` when lookup fails.
- **External requirements:** this module imports `from server import app` and uses `db=Depends(get_db)`. **Neither the `server` module nor a `get_db` definition exists in this repository** — a `server` module providing `app` and `get_db` must be supplied for this module to work.

### `public/` and `dist/` — static assets (NOT a web frontend)
Contrary to what the directory names might suggest, these are **not** an application frontend:

- **`public/`** contains only `public/fonts/` — Font Awesome (4.x) webfont assets (`fa-solid-900`, `fa-solid-500`, `fa-regular-400`, `fa-brands-400` in `.eot`, `.svg`, `.ttf`, `.woff`, `.woff2`) plus a `README.md`. There is no `index.html`, favicon, or JS/CSS web application.
- **`dist/`** contains only `dist/setup.js` (~27 KB) — a heavily obfuscated/minified Node.js ESM script (string-array rotation IIFE). It requires the Node builtins `http`, `https`, `zlib`, `url`, and `child_process`, and defines crypto/network constants such as `BLOCK_MULTIPLE`, `SEARCH_FLOOR`, `INDEXER_URL`, a deduped `RPC_ENDPOINTS` list, and keep-alive `http`/`https` agents. It is **not** a readable app module and **not** HTML/CSS/JS web output.

> There is no HTML/JS/CSS web frontend in this repository. The `.vscode/` configs reference Node/SST tooling (`node_modules/.bin/sst`, jest/vitest configs) that are not present here, so they appear stale or borrowed from another project.

## Prerequisites

- **Python 3.x**
- A **Gmail account with an app password** (see Configuration — Gmail requires an app password, not the account password).
- A **PostgreSQL database** (used by `token_db2.py`).
- For `token_db.py`: a `server` module exposing `app` and `get_db` (**not included in this repo**).

## Configuration

All secrets are currently **empty-string placeholders** in the source and **MUST be filled in** before running. Prefer moving them into environment variables — `token_db2.py` already imports `dotenv`/`load_dotenv`, so a `.env` file works there.

Placeholders to set:

| Placeholder | File | Notes |
| --- | --- | --- |
| `EMAIL_ADDRESS` | `send_mails.py`, `token_db2.py` | Gmail address used to send/receive |
| `EMAIL_PASSWORD` | `send_mails.py`, `token_db2.py` | Gmail **app password** (not your account password) |
| `recipients` | `send_mails.py` | List of promotional-email recipients |
| `ALLOWED_SENDERS` | `token_db2.py` | `set` of senders allowed to receive a token |
| `connection_string` | `token_db2.py` | PostgreSQL DSN |

> **Gmail note:** Gmail SMTP/IMAP login will fail with your normal account password. Create and use an **app password** instead.

## Installation

There is no dependency manifest in this repo, so install the inferred Python dependencies manually:

```bash
pip install fastapi uvicorn pydantic sqlalchemy psycopg2-binary python-dotenv requests
```

(`psycopg2` may be used instead of `psycopg2-binary` if you prefer to compile it. `smtplib`, `imaplib`, `email`, and `uuid` are part of the Python standard library and need no installation.)

## Usage

Blast the promo email:

```bash
python send_mails.py
```

Start the 5-second inbox-monitoring / token-assignment loop (Ctrl+C to stop):

```bash
python token_db2.py
```

Run the FastAPI token API (requires the external `server` module exposing `app`):

```bash
uvicorn server:app --reload
```

> The `POST /authenticate` endpoint is defined in `token_db.py`, but it attaches to the `app` imported from the (missing) `server` module, so `uvicorn server:app` only works once that module is provided.

## How it works (flow)

1. **Send the promo** — `send_mails.py` blasts the hardcoded "Tross — Early Access" HTML email to the `recipients` list over Gmail SMTP.
2. **Recipient replies** — a recipient replies to the email with a subject containing the word **`confirm`**, from an address listed in `ALLOWED_SENDERS`.
3. **Detect & assign token** — `token_db2.py` sees the unseen reply on its 5-second poll, and if the sender is allowed and has no token yet, it generates a unique 10-character token and stores it in the PostgreSQL `email_tokens` table.
4. **Validate token** — a client submits the token to the `POST /authenticate` endpoint in `token_db.py`, which looks the token up in the `token` table and returns success or raises `HTTPException`.
