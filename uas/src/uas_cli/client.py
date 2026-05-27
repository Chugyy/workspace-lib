"""HTTP client for Universal Agent Service (UAS) API."""

import os
import sys
from pathlib import Path
from typing import Any, Optional

import httpx

# Profile resolver
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".profiles"))

_DEFAULT_URL = "http://127.0.0.1:4820"
_DEFAULT_TOKEN = ""


def _load_config(profile: Optional[str] = None) -> dict:
    """Load UAS URL and auth token from profile or env."""
    try:
        from resolver import resolve
        config = resolve("uas", profile)
        return {
            "uas_url": config.get("uas_url") or config.get("UAS_URL") or _DEFAULT_URL,
            "uas_auth_token": config.get("uas_auth_token") or config.get("UAS_AUTH_TOKEN") or _DEFAULT_TOKEN,
        }
    except Exception:
        pass

    return {
        "uas_url": os.environ.get("UAS_URL", _DEFAULT_URL),
        "uas_auth_token": os.environ.get("UAS_AUTH_TOKEN", _DEFAULT_TOKEN),
    }


class UasClient:
    """Synchronous HTTP client for the UAS API."""

    def __init__(self, profile: Optional[str] = None):
        config = _load_config(profile)
        self.base_url = config["uas_url"].rstrip("/")
        headers = {}
        token = config["uas_auth_token"]
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0,
            follow_redirects=True,
        )

    def _request(self, method: str, path: str, **kwargs) -> Any:
        resp = self._client.request(method, path, **kwargs)
        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                # If response is HTML or very long, truncate it
                if len(detail) > 200 or "<html" in detail.lower():
                    detail = f"HTTP {resp.status_code} (non-JSON response from server)"
            raise httpx.HTTPStatusError(
                f"{resp.status_code}: {detail}",
                request=resp.request,
                response=resp,
            )
        if resp.status_code == 204:
            return None
        return resp.json()

    # ── MCP operations ───────────────────────────────────────────

    def mcp_status(self) -> dict:
        """GET /v1/mcp/status"""
        return self._request("GET", "/v1/mcp/status")

    def mcp_tools(self, server: Optional[str] = None) -> dict:
        """GET /v1/mcp/tools?server=name"""
        params = {}
        if server:
            params["server"] = server
        return self._request("GET", "/v1/mcp/tools", params=params)

    def mcp_reconnect(self, server: Optional[str] = None) -> dict:
        """POST /v1/mcp/reconnect"""
        body = {}
        if server:
            body["server"] = server
        return self._request("POST", "/v1/mcp/reconnect", json=body if body else None)
