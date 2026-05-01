"""IMAP/SMTP email client using built-in Python libraries."""

import imaplib
import smtplib
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import List, Dict, Optional


def connect_imap(host: str, email_address: str, password: str, port: int = 993):
    """Connect to IMAP server with SSL."""
    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(email_address, password)
    return imap


def get_email_body(msg) -> str:
    """Extract plain text body from email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode()
                    break
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except Exception:
            pass
    return body


def list_emails(
    host: str,
    email_address: str,
    password: str,
    folder: str = "INBOX",
    limit: int = 10,
    unread_only: bool = False,
) -> List[Dict]:
    imap = connect_imap(host, email_address, password)
    imap.select(folder)

    search_criteria = "UNSEEN" if unread_only else "ALL"
    status, messages = imap.search(None, search_criteria)

    if status != "OK":
        imap.close()
        imap.logout()
        return []

    email_ids = messages[0].split()
    email_ids = email_ids[-limit:]

    emails = []
    for email_id in reversed(email_ids):
        status, msg_data = imap.fetch(email_id, "(RFC822)")
        if status != "OK":
            continue

        msg = email_lib.message_from_bytes(msg_data[0][1])

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        from_header, encoding = decode_header(msg["From"])[0]
        if isinstance(from_header, bytes):
            from_header = from_header.decode(encoding or "utf-8")

        body = get_email_body(msg)
        snippet = body[:200] if body else ""

        emails.append({
            "id": email_id.decode(),
            "from": from_header,
            "subject": subject,
            "date": msg["Date"],
            "snippet": snippet,
        })

    imap.close()
    imap.logout()
    return emails


def read_email(
    host: str,
    email_address: str,
    password: str,
    email_id: str,
    folder: str = "INBOX",
) -> Dict:
    imap = connect_imap(host, email_address, password)
    imap.select(folder)

    status, msg_data = imap.fetch(email_id.encode(), "(RFC822)")
    if status != "OK":
        imap.close()
        imap.logout()
        return {}

    msg = email_lib.message_from_bytes(msg_data[0][1])

    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8")

    from_header, encoding = decode_header(msg["From"])[0]
    if isinstance(from_header, bytes):
        from_header = from_header.decode(encoding or "utf-8")

    body = get_email_body(msg)

    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                attachments.append(part.get_filename())

    imap.close()
    imap.logout()

    return {
        "id": email_id,
        "from": from_header,
        "to": msg["To"],
        "subject": subject,
        "date": msg["Date"],
        "body": body,
        "attachments": attachments,
    }


def send_email(
    smtp_host: str,
    email_address: str,
    password: str,
    to: str,
    subject: str,
    body: str,
    port: int = 587,
    html: bool = False,
) -> bool:
    try:
        msg = MIMEMultipart("alternative") if html else MIMEText(body, "plain")
        if html:
            msg.attach(MIMEText(body, "html"))
        msg["From"] = email_address
        msg["To"] = to
        msg["Subject"] = subject

        server = smtplib.SMTP(smtp_host, port)
        server.starttls()
        server.login(email_address, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def search_emails(
    host: str,
    email_address: str,
    password: str,
    sender: Optional[str] = None,
    subject: Optional[str] = None,
    limit: int = 10,
) -> List[Dict]:
    imap = connect_imap(host, email_address, password)
    imap.select("INBOX")

    criteria = []
    if sender:
        criteria.append(f'FROM "{sender}"')
    if subject:
        criteria.append(f'SUBJECT "{subject}"')

    search_string = " ".join(criteria) if criteria else "ALL"
    status, messages = imap.search(None, search_string)

    if status != "OK":
        imap.close()
        imap.logout()
        return []

    email_ids = messages[0].split()
    email_ids = email_ids[-limit:]

    emails = []
    for email_id in reversed(email_ids):
        status, msg_data = imap.fetch(email_id, "(RFC822)")
        if status != "OK":
            continue

        msg = email_lib.message_from_bytes(msg_data[0][1])

        subject_decoded, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject_decoded, bytes):
            subject_decoded = subject_decoded.decode(encoding or "utf-8")

        from_header, encoding = decode_header(msg["From"])[0]
        if isinstance(from_header, bytes):
            from_header = from_header.decode(encoding or "utf-8")

        emails.append({
            "id": email_id.decode(),
            "from": from_header,
            "subject": subject_decoded,
            "date": msg["Date"],
        })

    imap.close()
    imap.logout()
    return emails
