# read_inbox_and_assign_tokens_db.py
import imaplib
import email
import os
from email.header import decode_header
import time
import random
import string
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from email.header import decode_header
import smtplib

IMAP_SERVER = "imap.gmail.com"
EMAIL_ADDRESS = "" #bytQuest's credentials
EMAIL_PASSWORD = ""
ALLOWED_SENDERS = {""}#list of allowed email addresses

connection_string='' #connection string to the database

connection_pool = pool.SimpleConnectionPool(
    1,10,connection_string
)
if connection_pool:
    print("Connection pool created successfully")

def generate_token(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_table_if_not_exists():
    print("created table")
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS email_tokens (
                    email VARCHAR PRIMARY KEY,
                    token VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    finally:
        connection_pool.putconn(conn)

def token_exists(email_addr):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT token FROM email_tokens WHERE email = %s", (email_addr,))
            return cur.fetchone()
    finally:
        connection_pool.putconn(conn)

def store_token(email_addr, token):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO email_tokens (email, token) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (email_addr, token)
            )
            conn.commit()
    finally:
        print("token stored")
        connection_pool.putconn(conn)

def check_emails():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")
    print("Checking for new emails...")
    status, messages = mail.search(None, '(UNSEEN)')
    email_ids = messages[0].split()

    for eid in reversed(email_ids):
        _, msg_data = mail.fetch(eid, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                sender = email.utils.parseaddr(msg["From"])[1]
                print(f"📧 New email from: {sender}")
                print(f"Subject: {msg['Subject']}")
                print(f"Body: {msg.get_payload(decode=True)}")
                raw_subject = msg["Subject"]
                if raw_subject:
                    subject, encoding = decode_header(raw_subject)[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")
                    if "confirm" in subject.lower():
                        # your logic here
                        print("Confirmed email found")
                else:
                    print("No subject found")

                if "confirm" in subject.lower() and sender in ALLOWED_SENDERS:
                    if not token_exists(sender):
                        token = generate_token()
                        store_token(sender, token)
                        print(f"✅ Token assigned to {sender}: {token}")

    mail.logout()

if __name__ == "__main__":
    create_table_if_not_exists()
    print("📨 Monitoring inbox... (Press Ctrl+C to stop)")
    try:
        while True:
            check_emails()
            time.sleep(5)
    except KeyboardInterrupt:
        print("🛑 Stopped monitoring.")
    finally:
        connection_pool.closeall()