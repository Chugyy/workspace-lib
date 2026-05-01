"""Authentication manager for ERP API."""

import json
import sys
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR.parent / ".profiles"))


def _get_opener():
    proxy_handler = urllib.request.ProxyHandler()
    return urllib.request.build_opener(proxy_handler)


def load_config(config_path: Optional[str] = None, profile: Optional[str] = None) -> Dict[str, Any]:
    """Load config from profile resolver, with legacy fallback."""
    if config_path is not None:
        with open(config_path, "r") as f:
            return json.load(f)
    try:
        from resolver import resolve
        return resolve("erp", profile)
    except Exception:
        legacy = SKILL_DIR / "assets" / "config.json"
        if legacy.exists():
            with open(legacy, "r") as f:
                return json.load(f)
        raise


def load_token(token_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if token_path is None:
        token_path = SKILL_DIR / "assets" / "token.json"
    try:
        with open(token_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_token(token_data: Dict[str, Any], token_path: Optional[str] = None) -> None:
    if token_path is None:
        token_path = SKILL_DIR / "assets" / "token.json"
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)


def login(email: str, password: str, api_url: str) -> Dict[str, Any]:
    url = f"{api_url}/api/auth/login"
    data = {"email": email, "password": password}
    json_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=json_data, headers={"Content-Type": "application/json"})
    try:
        opener = _get_opener()
        with opener.open(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        if e.code == 401:
            raise Exception("Authentication failed: Invalid credentials")
        elif e.code == 400:
            raise Exception("Bad request: Invalid email or password format")
        else:
            raise Exception(f"Login error ({e.code}): {error_body}")


def ensure_authenticated(config_path: Optional[str] = None, token_path: Optional[str] = None) -> str:
    token_data = load_token(token_path)
    if token_data and "accessToken" in token_data:
        return token_data["accessToken"]

    config = load_config(config_path)
    token_response = login(
        email=config["email"],
        password=config["password"],
        api_url=config["api_url"],
    )
    save_token(token_response, token_path)
    return token_response["accessToken"]
