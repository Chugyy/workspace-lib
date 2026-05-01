#!/usr/bin/env python3
"""
IMAP/SMTP email client using built-in Python libraries.
Provides simple functions to list, read, and send emails via IMAP/SMTP.

No external dependencies required - uses imaplib, smtplib, and email packages.
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import List, Dict, Optional
import json
import os
from datetime import datetime


def connect_imap(host: str, email_address: str, password: str, port: int = 993):
    """
    Connect to IMAP server with SSL.

    Args:
        host: IMAP server host
        email_address: Email address
        password: Email password or app password
        port: IMAP port (default 993 for SSL)

    Returns:
        Connected IMAP4_SSL instance
    """
    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(email_address, password)
    return imap


def list_emails(host: str, email_address: str, password: str,
                folder: str = 'INBOX', limit: int = 10,
                unread_only: bool = False) -> List[Dict]:
    """
    List emails from IMAP server.

    Args:
        host: IMAP server host
        email_address: Email address
        password: Email password
        folder: Mailbox folder (default 'INBOX')
        limit: Maximum number of emails
        unread_only: Only fetch unread emails

    Returns:
        List of email dictionaries with id, from, subject, date, snippet
    """
    imap = connect_imap(host, email_address, password)
    imap.select(folder)

    # Search criteria
    search_criteria = 'UNSEEN' if unread_only else 'ALL'
    status, messages = imap.search(None, search_criteria)

    if status != 'OK':
        imap.close()
        imap.logout()
        return []

    email_ids = messages[0].split()
    email_ids = email_ids[-limit:]  # Get last N emails

    emails = []
    for email_id in reversed(email_ids):
        status, msg_data = imap.fetch(email_id, '(RFC822)')
        if status != 'OK':
            continue

        msg = email.message_from_bytes(msg_data[0][1])

        # Decode subject
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8')

        # Decode from
        from_header, encoding = decode_header(msg['From'])[0]
        if isinstance(from_header, bytes):
            from_header = from_header.decode(encoding or 'utf-8')

        # Get body snippet
        body = get_email_body(msg)
        snippet = body[:200] if body else ''

        emails.append({
            'id': email_id.decode(),
            'from': from_header,
            'subject': subject,
            'date': msg['Date'],
            'snippet': snippet
        })

    imap.close()
    imap.logout()
    return emails


def read_email(host: str, email_address: str, password: str,
               email_id: str, folder: str = 'INBOX') -> Dict:
    """
    Read full email content by ID.

    Args:
        host: IMAP server host
        email_address: Email address
        password: Email password
        email_id: Email ID to read
        folder: Mailbox folder

    Returns:
        Dictionary with from, to, subject, date, body, attachments
    """
    imap = connect_imap(host, email_address, password)
    imap.select(folder)

    status, msg_data = imap.fetch(email_id.encode(), '(RFC822)')
    if status != 'OK':
        imap.close()
        imap.logout()
        return {}

    msg = email.message_from_bytes(msg_data[0][1])

    # Decode headers
    subject, encoding = decode_header(msg['Subject'])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or 'utf-8')

    from_header, encoding = decode_header(msg['From'])[0]
    if isinstance(from_header, bytes):
        from_header = from_header.decode(encoding or 'utf-8')

    # Get body
    body = get_email_body(msg)

    # Get attachments
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                attachments.append(part.get_filename())

    imap.close()
    imap.logout()

    return {
        'id': email_id,
        'from': from_header,
        'to': msg['To'],
        'subject': subject,
        'date': msg['Date'],
        'body': body,
        'attachments': attachments
    }


def get_email_body(msg) -> str:
    """Extract plain text body from email message."""
    body = ''

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition'))

            if content_type == 'text/plain' and 'attachment' not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode()
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            pass

    return body


def send_email(smtp_host: str, email_address: str, password: str,
               to: str, subject: str, body: str,
               port: int = 587, html: bool = False) -> bool:
    """
    Send email via SMTP.

    Args:
        smtp_host: SMTP server host
        email_address: Sender email address
        password: Email password or app password
        to: Recipient email address
        subject: Email subject
        body: Email body content
        port: SMTP port (default 587 for TLS)
        html: If True, body is HTML; otherwise plain text

    Returns:
        True if sent successfully
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative') if html else MIMEText(body, 'plain')

        if html:
            msg.attach(MIMEText(body, 'html'))

        msg['From'] = email_address
        msg['To'] = to
        msg['Subject'] = subject

        # Connect and send
        server = smtplib.SMTP(smtp_host, port)
        server.starttls()
        server.login(email_address, password)
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def search_emails(host: str, email_address: str, password: str,
                  sender: Optional[str] = None, subject: Optional[str] = None,
                  limit: int = 10) -> List[Dict]:
    """
    Search emails with filters.

    Args:
        host: IMAP server host
        email_address: Email address
        password: Email password
        sender: Filter by sender email
        subject: Filter by subject keywords
        limit: Maximum results

    Returns:
        List of email dictionaries
    """
    imap = connect_imap(host, email_address, password)
    imap.select('INBOX')

    # Build search criteria
    criteria = []
    if sender:
        criteria.append(f'FROM "{sender}"')
    if subject:
        criteria.append(f'SUBJECT "{subject}"')

    search_string = ' '.join(criteria) if criteria else 'ALL'
    status, messages = imap.search(None, search_string)

    if status != 'OK':
        imap.close()
        imap.logout()
        return []

    email_ids = messages[0].split()
    email_ids = email_ids[-limit:]

    emails = []
    for email_id in reversed(email_ids):
        status, msg_data = imap.fetch(email_id, '(RFC822)')
        if status != 'OK':
            continue

        msg = email.message_from_bytes(msg_data[0][1])

        subject_decoded, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject_decoded, bytes):
            subject_decoded = subject_decoded.decode(encoding or 'utf-8')

        from_header, encoding = decode_header(msg['From'])[0]
        if isinstance(from_header, bytes):
            from_header = from_header.decode(encoding or 'utf-8')

        emails.append({
            'id': email_id.decode(),
            'from': from_header,
            'subject': subject_decoded,
            'date': msg['Date']
        })

    imap.close()
    imap.logout()
    return emails


# Example usage
if __name__ == '__main__':
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'config.json')
    with open(config_path) as f:
        config = json.load(f)

    imap_config = config['imap_smtp']

    # List recent emails
    print("=== Recent Emails ===")
    emails = list_emails(
        imap_config['imap_host'],
        imap_config['email'],
        imap_config['password'],
        limit=5
    )

    for email in emails:
        print(f"From: {email['from']}")
        print(f"Subject: {email['subject']}")
        print(f"Date: {email['date']}")
        print()
