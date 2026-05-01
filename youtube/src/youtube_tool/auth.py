"""OAuth2 authentication for YouTube Data API v3."""

import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

TOOL_DIR = Path(__file__).parent.parent.parent
CREDENTIALS_DIR = TOOL_DIR / "credentials"
CLIENT_SECRET = CREDENTIALS_DIR / "client_secret.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def get_credentials() -> Credentials:
    """Get valid OAuth2 credentials. Triggers browser flow if needed."""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception:
            creds = None

    if creds and creds.valid:
        return creds

    # Fresh auth flow — adapt client_secret format for InstalledAppFlow
    secret_data = json.loads(CLIENT_SECRET.read_text())

    # Convert "web" format to "installed" format if needed
    if "web" in secret_data and "installed" not in secret_data:
        web = secret_data["web"]
        secret_data = {
            "installed": {
                "client_id": web["client_id"],
                "client_secret": web["client_secret"],
                "project_id": web.get("project_id", ""),
                "auth_uri": web["auth_uri"],
                "token_uri": web["token_uri"],
                "auth_provider_x509_cert_url": web.get("auth_provider_x509_cert_url", ""),
                "redirect_uris": ["http://localhost"],
            }
        }

    flow = InstalledAppFlow.from_client_config(secret_data, SCOPES)
    creds = flow.run_local_server(port=8080, prompt="consent")
    _save_token(creds)
    return creds


def _save_token(creds: Credentials):
    """Save credentials to token.json."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())


def get_youtube_service():
    """Build and return an authenticated YouTube API service."""
    import httplib2
    import google_auth_httplib2
    from googleapiclient.discovery import build

    creds = get_credentials()
    http = httplib2.Http(timeout=120)
    authed_http = google_auth_httplib2.AuthorizedHttp(creds, http=http)
    return build("youtube", "v3", http=authed_http)
