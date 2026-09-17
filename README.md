# Tross by BytQuest — Early-Access System

An email-driven onboarding flow that markets early access to **Tross**, monitors confirmation
emails, and issues/stores access tokens.

The system is composed of three small Python scripts:

1. Send the Tross early-access HTML marketing email to a list of recipients.
2. Monitor a Gmail inbox for confirmation replies from approved senders.
3. Generate and store a unique access token for each confirmed request in PostgreSQL.

---

## Features

- 📧 **Send the Tross early-access marketing email** — an HTML email promoting *"Early Access to
  Tross — Build Faster, Debug Smarter"* delivered via SMTP to a list of recipients.
- 📥 **Monitor a Gmail inbox for confirmation replies** — polls the inbox for unseen messages,
  filters those whose subject contains `confirm` and whose sender is allow-listed, then issues a
  token.
- 🔑 **Generate and store access tokens in PostgreSQL** — each confirmed email is assigned a
  random 10-character alphanumeric token persisted in an `email_tokens` table.
- ✅ **Authenticate tokens via a FastAPI endpoint** — a `POST /authenticate` endpoint validates a
  submitted token against the database.

---

## Repository Structure

```text
.
├── send_mails.py     # Sends the Tross early-access HTML marketing email via SMTP.
├── token_db2.py      # Gmail IMAP monitor that issues & stores access tokens in PostgreSQL.
├── token_db.py       # FastAPI service exposing POST /authenticate for token validation.
├── dist/             # Build output (contains setup.js).
└── public/           # Static assets (fonts/).
```

> Note: `server.py` is referenced by `token_db.py` but is **not present** at the repository root
> (see [Notes & Limitations](#notes--limitations)).

---

## Components

### `send_mails.py`

Sends the early-access marketing email to every recipient in the `recipients` list.

- `send_email()` opens an `smtplib.SMTP(SMTP_SERVER, SMTP_PORT)` connection to
  `smtp.gmail.com:587`, calls `starttls()`, and then `login()` with the configured credentials.
- For each address in `recipients`, it builds a `MIMEMultipart('alternative')` message (From / To /
  Subject headers plus the HTML body) and calls `sendmail()`.
- Prints `✅ Email sent to {recipient}` for each successfully delivered message, then calls
  `server.quit()`.

Run it with:

```bash
python send_mails.py
```

**Configuration placeholders:**

| Placeholder      | Location   | Description                                          |
| ---------------- | ---------- | ---------------------------------------------------- |
| `EMAIL_ADDRESS`  | lines 5–8  | Gmail (SMTP) account address used to log in.         |
| `EMAIL_PASSWORD` | lines 5–8  | Gmail app password for the above account.            |
| `recipients`     | line 10    | List of destination email addresses.                 |
| `subject`        | —          | Email subject line.                                  |
| `html_body`      | —          | The HTML marketing email content.                    |

---

### `token_db2.py`

A Gmail IMAP monitor that turns confirmation replies into stored access tokens.

- Connects to `imap.gmail.com` and, inside `check_emails()`, logs in, selects `inbox`, and searches
  for `(UNSEEN)` messages.
- Iterates over the fetched messages and keeps only those whose subject **contains `"confirm"`**
  and whose sender is present in `ALLOWED_SENDERS`.
- For each new match, `generate_token()` assigns a random **10-character alphanumeric** token, and
  `store_token()` writes it (with the sender's email) into the PostgreSQL `email_tokens` table.
- `create_table_if_not_exists()` ensures the `email_tokens` table exists
  (`email` PRIMARY KEY, `token`, `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`).
- Uses `psycopg2` with a `SimpleConnectionPool(1, 10, connection_string)` and loops **every 5
  seconds** until interrupted with `Ctrl+C`.

Run it with:

```bash
python token_db2.py
```

**Configuration placeholders:**

| Placeholder         | Description                                             |
| ------------------- | ------------------------------------------------------- |
| `EMAIL_ADDRESS`     | Gmail (IMAP) account address used to log in.            |
| `EMAIL_PASSWORD`    | Gmail app password for the above account.               |
| `ALLOWED_SENDERS`   | Collection of sender addresses allowed to receive tokens. |
| `connection_string` | PostgreSQL DSN for connection pooling.                  |

---

### `token_db.py`

A FastAPI service that validates access tokens. It imports `app` and `get_db` from a `server`
module.

- Defines the SQLAlchemy `Token` model backed by the `token` table:
  - `id` — primary key (`Mapped[int]`).
  - `token` — token value (`Mapped[uuid]`).
- Defines the `AuthReq` Pydantic model with a single `token: str` field.
- Exposes a `POST /authenticate` endpoint that accepts an `AuthReq`, looks the submitted token up
  against the database, and returns the result — raising an `HTTPException` on failure.

> This module depends on a `server` module (not present at the repo root) that must provide the
> FastAPI `app`, the database engine/session, and the `get_db` dependency.

---

## Configuration / Environment

All credentials are currently **hardcoded placeholders** that must be replaced before running:

- `EMAIL_ADDRESS` — Gmail account address (SMTP and/or IMAP).
- `EMAIL_PASSWORD` — Gmail app password.
- `ALLOWED_SENDERS` — senders permitted to trigger token issuance.
- `recipients` — email marketing recipients.
- `connection_string` — PostgreSQL connection string.

A Gmail account must have **app passwords** enabled (and IMAP + SMTP access) for the mail features
to work. It is strongly recommended to move secrets out of the source and into a `.env` file — the
code already imports `dotenv` (specifically in `token_db2.py`).

---

## Installation

No `requirements.txt` is currently provided, so install the required packages directly:

```bash
pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary python-dotenv requests
```

- Requires **Python 3.9+** (the code uses PEP 585 / PEP 604-style typing and SQLAlchemy
  `Mapped` / `mapped_column`).
- **PostgreSQL** is required for `token_db2.py` and `token_db.py`.

---

## Usage

1. **Install dependencies**

   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary python-dotenv requests
   ```

2. **Configure credentials**

   Fill in `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `ALLOWED_SENDERS`, `recipients`, and
   `connection_string` in the respective scripts (or a `.env` file).

3. **Send the marketing email**

   ```bash
   python send_mails.py
   ```

4. **Start the inbox monitor**

   ```bash
   python token_db2.py
   ```

   This polls the inbox every 5 seconds and stores a token for each valid confirmation until you
   stop it with `Ctrl+C`.

5. **Run the FastAPI app**

   Expose the `POST /authenticate` endpoint via the `server` module / uvicorn:

   ```bash
   uvicorn server:app --reload
   ```

---

## Notes & Limitations

- Several placeholders are declared but unused / empty by default and **must be replaced** before
  the scripts will function.
- `token_db.py` imports from a `server` module that is **referenced but absent from the repository
  root**; you must supply it to run the authentication service.
- Credentials are currently hardcoded placeholders — treat them as secrets and move them to a
  `.env` file or your environment.

---

## Contributing

Contributions are welcome. Please open an issue or submit a pull request describing your change.

## License / Contact

For questions, reach out to **bytquest@gmail.com**.
