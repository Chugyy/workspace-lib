"""
HTTP client for the Process Manager API.

All operations go through the AI Manager backend — this CLI
is a thin presentation layer.
"""

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("PM_API_URL", "http://127.0.0.1:4810")
API_KEY = os.getenv("PM_API_KEY", "proxy-internal-key")

_HEADERS = {"X-Internal-Key": API_KEY}
_TIMEOUT = 15


def _url(path: str) -> str:
    return f"{API_URL}{path}"


def _handle_error(resp: httpx.Response):
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        print(f"Error ({resp.status_code}): {detail}", file=sys.stderr)
        sys.exit(1)


def list_processes(category: str | None = None) -> dict:
    params = {}
    if category:
        params["category"] = category
    resp = httpx.get(_url("/api/processes"), headers=_HEADERS, params=params, timeout=_TIMEOUT)
    _handle_error(resp)
    return resp.json()


def get_process(name: str) -> dict:
    resp = httpx.get(_url(f"/api/processes/{name}"), headers=_HEADERS, timeout=_TIMEOUT)
    _handle_error(resp)
    return resp.json()


def start(name: str) -> dict:
    resp = httpx.post(_url(f"/api/processes/{name}/start"), headers=_HEADERS, timeout=_TIMEOUT)
    _handle_error(resp)
    return resp.json()


def stop(name: str) -> dict:
    resp = httpx.post(_url(f"/api/processes/{name}/stop"), headers=_HEADERS, timeout=_TIMEOUT)
    _handle_error(resp)
    return resp.json()


def restart(name: str) -> dict:
    resp = httpx.post(_url(f"/api/processes/{name}/restart"), headers=_HEADERS, timeout=_TIMEOUT)
    _handle_error(resp)
    return resp.json()


def logs(name: str, lines: int = 50) -> dict:
    resp = httpx.get(
        _url(f"/api/processes/{name}/logs"),
        headers=_HEADERS,
        params={"lines": lines},
        timeout=_TIMEOUT,
    )
    _handle_error(resp)
    return resp.json()


def health() -> dict:
    resp = httpx.get(_url("/api/processes/health"), headers=_HEADERS, timeout=_TIMEOUT)
    _handle_error(resp)
    return resp.json()


def add(
    name: str,
    script: str,
    cwd: str | None = None,
    category: str = "other",
    port: int | None = None,
    health_endpoint: str | None = None,
) -> dict:
    body = {
        "name": name,
        "script": script,
        "cwd": cwd,
        "category": category,
        "port": port,
        "health": health_endpoint,
    }
    resp = httpx.post(_url("/api/processes"), headers=_HEADERS, json=body, timeout=_TIMEOUT)
    _handle_error(resp)
    return resp.json()


def remove(name: str) -> dict:
    resp = httpx.delete(_url(f"/api/processes/{name}"), headers=_HEADERS, timeout=_TIMEOUT)
    _handle_error(resp)
    return resp.json()


# --- Dokploy ---

def dokploy_action(application_id: str, action: str) -> dict:
    """Perform an action (start/stop/redeploy) on a Dokploy application."""
    resp = httpx.post(
        _url(f"/api/processes/dokploy/{application_id}/{action}"),
        headers=_HEADERS,
        timeout=30,  # Dokploy actions can be slower
    )
    _handle_error(resp)
    return resp.json()
