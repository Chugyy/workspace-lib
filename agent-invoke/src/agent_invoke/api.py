"""HTTP client for the AI Manager backend API."""

import json
import os
from typing import Iterator

import httpx

AI_MANAGER_URL = os.environ.get("AI_MANAGER_URL", "http://127.0.0.1:4812")
INTERNAL_KEY = os.environ.get("BACKEND_INTERNAL_KEY", "proxy-internal-key")

_HEADERS = {"X-Internal-Key": INTERNAL_KEY}


def _headers() -> dict:
    """Return auth headers, always reading env vars at call time."""
    return {
        "X-Internal-Key": os.environ.get("BACKEND_INTERNAL_KEY", "proxy-internal-key"),
    }


def _base_url() -> str:
    return os.environ.get("AI_MANAGER_URL", "http://127.0.0.1:4812")


def _connection_error(exc: Exception) -> str:
    base = _base_url()
    return (
        f"Cannot connect to AI Manager at {base}: {exc}\n"
        f"Verify that AI Manager is running (check with: curl {base}/health)\n"
        f"You can override the URL with: AI_MANAGER_URL=http://host:port"
    )


def create_conversation(
    model: str,
    pid: str | None = None,
    cwd: str | None = None,
    agent_directory: str | None = None,
    system_prompt_paths: list[str] | None = None,
) -> dict:
    """POST /api/conversations — create a new conversation, return conversation dict.

    Notes on pid handling:
    - Some backend versions require pid to be a non-null string.
    - When pid is not known (--agent-dir mode), we pass a sentinel value "agent-invoke"
      and rely on cwd being set, which takes priority in the backend's send_message job.
    """
    body: dict = {
        "model": model,
        "type": "agent",
        "initiated_by": "agent-invoke",
        # Pass pid always; sentinel "agent-invoke" used when no real pid is known.
        # If the backend supports optional pid (newer versions), the sentinel is harmless.
        # If the backend requires pid (older versions), the sentinel keeps it valid,
        # and cwd takes priority for path resolution in the agent runner.
        "pid": pid if pid else "agent-invoke",
    }
    if cwd:
        body["cwd"] = cwd
    if agent_directory:
        body["agent_directory"] = str(agent_directory)
    if system_prompt_paths is not None:
        body["system_prompt_paths"] = system_prompt_paths

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{_base_url()}/api/conversations",
                json=body,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError as exc:
        raise ConnectionError(_connection_error(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Backend returned {exc.response.status_code}: {exc.response.text}"
        ) from exc


def send_message(conversation_id: str, text: str) -> dict:
    """POST /api/conversations/{id}/messages — trigger agent with prompt."""
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{_base_url()}/api/conversations/{conversation_id}/messages",
                json={"text": text},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError as exc:
        raise ConnectionError(_connection_error(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Backend returned {exc.response.status_code}: {exc.response.text}"
        ) from exc


def stream_events(conversation_id: str, timeout: int = 300) -> Iterator[dict]:
    """GET /api/conversations/{id}/events — SSE stream.

    Yields parsed event dicts until 'completed', 'stopped', or 'error'.
    Raises ConnectionError if backend is not reachable.
    """
    url = f"{_base_url()}/api/conversations/{conversation_id}/events"
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout, connect=10.0)) as client:
            with client.stream("GET", url, headers=_headers()) as response:
                response.raise_for_status()
                buffer = ""
                for chunk in response.iter_text():
                    buffer += chunk
                    while "\n\n" in buffer:
                        block, buffer = buffer.split("\n\n", 1)
                        lines = block.strip().splitlines()
                        data_line = None
                        for line in lines:
                            if line.startswith("data:"):
                                data_line = line[5:].strip()
                            # skip event: and ping lines
                        if data_line is None or data_line == "{}":
                            continue
                        try:
                            event = json.loads(data_line)
                        except json.JSONDecodeError:
                            continue
                        yield event
                        if event.get("type") in ("completed", "stopped", "error"):
                            return
    except httpx.ConnectError as exc:
        raise ConnectionError(_connection_error(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Backend returned {exc.response.status_code}: {exc.response.text}"
        ) from exc


def get_conversation(conversation_id: str) -> dict:
    """GET /api/conversations/{id} — fetch conversation state."""
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{_base_url()}/api/conversations/{conversation_id}",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError as exc:
        raise ConnectionError(_connection_error(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Backend returned {exc.response.status_code}: {exc.response.text}"
        ) from exc
