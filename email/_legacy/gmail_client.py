#!/usr/bin/env python3
"""
Gmail client using simplegmail library.
Provides simple functions to list, read, and send emails via Gmail API.

Installation: pip install simplegmail
"""

from simplegmail import Gmail
from simplegmail.query import construct_query
from typing import List, Dict, Optional
import json
import os


def authenticate(credentials_path: str = 'credentials.json') -> Gmail:
    """
    Authenticate with Gmail API using OAuth2.

    Args:
        credentials_path: Path to OAuth2 credentials JSON file

    Returns:
        Authenticated Gmail instance

    Note:
        First time will open browser for authorization.
        Token saved in gmail-token.json for future use.
    """
    gmail = Gmail(client_secret_file=credentials_path)
    return gmail


def list_emails(gmail: Gmail, max_results: int = 10, unread_only: bool = False,
                sender: Optional[str] = None, subject: Optional[str] = None) -> List[Dict]:
    """
    List emails with optional filters.

    Args:
        gmail: Authenticated Gmail instance
        max_results: Maximum number of emails to retrieve
        unread_only: Only fetch unread emails
        sender: Filter by sender email
        subject: Filter by subject keywords

    Returns:
        List of email dictionaries with id, from, subject, date, snippet
    """
    query_params = {}
    if unread_only:
        query_params['unread'] = True
    if sender:
        query_params['sender'] = sender
    if subject:
        query_params['subject'] = subject

    messages = gmail.get_messages(query=construct_query(query_params))

    emails = []
    for msg in messages[:max_results]:  # Limit results with slice
        emails.append({
            'id': msg.id,
            'from': msg.sender,
            'subject': msg.subject,
            'date': msg.date,
            'snippet': msg.snippet
        })

    return emails


def read_email(gmail: Gmail, message_id: str) -> Dict:
    """
    Read full email content by ID.

    Args:
        gmail: Authenticated Gmail instance
        message_id: Gmail message ID

    Returns:
        Dictionary with from, to, subject, date, plain_text, html, attachments
    """
    # Use internal API to build message from ID
    message_ref = {'id': message_id}
    msg = gmail._build_message_from_ref('me', message_ref, attachments='reference')

    return {
        'id': msg.id,
        'from': msg.sender,
        'to': msg.recipient,
        'subject': msg.subject,
        'date': msg.date,
        'plain_text': msg.plain,
        'html': msg.html,
        'attachments': [att.filename for att in msg.attachments] if msg.attachments else []
    }


def send_email(gmail: Gmail, to: str, subject: str, body: str,
               from_email: Optional[str] = None, html: bool = False) -> bool:
    """
    Send email via Gmail.

    Args:
        gmail: Authenticated Gmail instance
        to: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email (optional, uses authenticated account)
        html: If True, body is HTML; otherwise plain text

    Returns:
        True if sent successfully
    """
    params = {
        'to': to,
        'subject': subject,
        'sender': from_email
    }

    if html:
        params['msg_html'] = body
    else:
        params['msg_plain'] = body

    message = gmail.send_message(**params)
    return message is not None


def create_draft(gmail: Gmail, to: str, subject: str, body: str,
                 from_email: Optional[str] = None, html: bool = False) -> bool:
    """
    Create draft email in Gmail.

    Args:
        gmail: Authenticated Gmail instance
        to: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email (optional)
        html: If True, body is HTML; otherwise plain text

    Returns:
        True if draft created successfully
    """
    params = {
        'to': to,
        'subject': subject,
        'sender': from_email
    }

    if html:
        params['msg_html'] = body
    else:
        params['msg_plain'] = body

    draft = gmail.create_draft(**params)
    return draft is not None


def search_emails(gmail: Gmail, query: str, max_results: int = 10) -> List[Dict]:
    """
    Search emails using Gmail query syntax.

    Args:
        gmail: Authenticated Gmail instance
        query: Gmail search query (e.g., "from:user@example.com newer_than:2d")
        max_results: Maximum results

    Returns:
        List of email dictionaries

    Examples:
        - "from:john@example.com"
        - "subject:invoice"
        - "newer_than:7d"
        - "has:attachment"
    """
    messages = gmail.get_messages(query=query)

    emails = []
    for msg in messages[:max_results]:  # Limit results with slice
        emails.append({
            'id': msg.id,
            'from': msg.sender,
            'subject': msg.subject,
            'date': msg.date,
            'snippet': msg.snippet
        })

    return emails


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Gmail client')
    parser.add_argument('action', choices=['list', 'read', 'send', 'search'])
    parser.add_argument('--max', type=int, default=10, help='Max results')
    parser.add_argument('--unread', action='store_true', help='Unread only')
    parser.add_argument('--sender', help='Filter by sender')
    parser.add_argument('--subject', help='Filter by subject')
    parser.add_argument('--id', help='Message ID (for read)')
    parser.add_argument('--to', help='Recipient email')
    parser.add_argument('--body', help='Email body')
    parser.add_argument('--html', action='store_true', help='Body is HTML')
    parser.add_argument('--query', help='Gmail search query')
    args = parser.parse_args()

    config_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'config.json')
    with open(config_path) as f:
        config = json.load(f)

    gmail = authenticate(config['gmail']['credentials'])

    if args.action == 'list':
        emails = list_emails(gmail, max_results=args.max, unread_only=args.unread,
                             sender=args.sender, subject=args.subject)
        for e in emails:
            print(f"[{e['id']}] {e['date']} | From: {e['from']} | {e['subject']}")

    elif args.action == 'read':
        if not args.id:
            print("--id required", file=sys.stderr)
            sys.exit(1)
        e = read_email(gmail, args.id)
        print(f"From: {e['from']}\nTo: {e['to']}\nSubject: {e['subject']}\nDate: {e['date']}\n\n{e['plain_text']}")

    elif args.action == 'send':
        if not args.to or not args.subject or not args.body:
            print("--to, --subject, --body required", file=sys.stderr)
            sys.exit(1)
        ok = send_email(gmail, args.to, args.subject, args.body, html=args.html)
        print("Sent" if ok else "Failed")

    elif args.action == 'search':
        if not args.query:
            print("--query required", file=sys.stderr)
            sys.exit(1)
        emails = search_emails(gmail, args.query, max_results=args.max)
        for e in emails:
            print(f"[{e['id']}] {e['date']} | From: {e['from']} | {e['subject']}")
