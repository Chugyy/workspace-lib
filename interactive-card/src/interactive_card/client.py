"""HTTP client for AI Manager backend."""

import json
import os

import httpx


def _get_config() -> tuple[str, str]:
    """Get backend URL and API key from environment."""
    url = os.environ.get("BACKEND_URL", "http://127.0.0.1:4810")
    key = os.environ.get("BACKEND_INTERNAL_KEY", "proxy-internal-key")
    return url, key


def create_conversation(
    card: dict,
    title: str | None = None,
    pid: str = "system",
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """Create an interactive conversation in the AI Manager.

    Args:
        card: Interactive card dict with 'body' and 'actions' keys.
        title: Optional text shown above the card.
        pid: PID for the conversation (default: system).
        model: AI model (used if user replies in chat).

    Returns:
        Conversation dict with 'id', 'status', etc.
    """
    url, key = _get_config()

    first_message = {"interactive": card}
    if title:
        first_message["content"] = title

    payload = {
        "pid": pid,
        "model": model,
        "type": "human",
        "initiated_by": "proxy",
        "first_message": first_message,
    }

    resp = httpx.post(
        f"{url}/api/conversations",
        headers={"X-Internal-Key": key, "Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def test_connection() -> dict:
    """Test connectivity to the backend."""
    url, _ = _get_config()
    resp = httpx.get(f"{url}/health", timeout=5)
    resp.raise_for_status()
    return resp.json()
