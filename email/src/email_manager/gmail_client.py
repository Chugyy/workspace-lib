"""Gmail client using google-auth + gmail API (replaces simplegmail/oauth2client)."""

import base64
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://mail.google.com/"]
TOKEN_PATH = Path(__file__).parent.parent.parent / "assets" / "gmail_token_v2.json"


def authenticate(credentials_path: str = "credentials.json") -> "googleapiclient.discovery.Resource":
    """Load credentials from token file and return Gmail API service."""
    if not TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"Token not found at {TOKEN_PATH}. Run the OAuth flow to generate it."
        )

    token_data = json.loads(TOKEN_PATH.read_text())
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(google.auth.transport.requests.Request())
        # Persist refreshed token
        token_data["token"] = creds.token
        token_data["expiry"] = creds.expiry.isoformat() if creds.expiry else None
        TOKEN_PATH.write_text(json.dumps(token_data, indent=2))

    return build("gmail", "v1", credentials=creds)


def list_emails(
    service,
    max_results: int = 10,
    unread_only: bool = False,
    sender: Optional[str] = None,
    subject: Optional[str] = None,
) -> List[Dict]:
    query_parts = []
    if unread_only:
        query_parts.append("is:unread")
    if sender:
        query_parts.append(f"from:{sender}")
    if subject:
        query_parts.append(f"subject:{subject}")
    query = " ".join(query_parts)

    result = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    emails = []
    for m in messages:
        msg = service.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        emails.append({
            "id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })
    return emails


def read_email(service, message_id: str) -> Dict:
    msg = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

    # Extract plain text body
    body = ""
    payload = msg["payload"]
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain" and "data" in part.get("body", {}):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                break
    elif "body" in payload and "data" in payload["body"]:
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

    return {
        "id": msg["id"],
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "plain_text": body,
        "html": "",
        "attachments": [],
    }


def send_email(
    service,
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    html: bool = False,
) -> bool:
    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if from_email:
        msg["From"] = from_email
    msg.attach(MIMEText(body, "html" if html else "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    return bool(result.get("id"))


def create_draft(
    service,
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    html: bool = False,
) -> bool:
    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if from_email:
        msg["From"] = from_email
    msg.attach(MIMEText(body, "html" if html else "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result = service.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()
    return bool(result.get("id"))


def search_emails(service, query: str, max_results: int = 10) -> List[Dict]:
    result = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    messages = result.get("messages", [])
    emails = []
    for m in messages:
        msg = service.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        emails.append({
            "id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })
    return emails
