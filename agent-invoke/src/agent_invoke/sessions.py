"""Session storage — logs all exchanges between callers and agents."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

SESSIONS_DIR = Path(__file__).resolve().parents[4] / "agents" / "sessions"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_session(agent: str, caller: str = "unknown") -> dict:
    session = {
        "id": uuid.uuid4().hex[:12],
        "agent": agent,
        # backend_conversation_id replaces the old claude_session_id
        "backend_conversation_id": None,
        "caller": caller,
        "started": _now(),
        "status": "active",
        "messages": [],
    }
    _write(session)
    return session


def add_message(session_id: str, role: str, content: str) -> dict:
    session = load(session_id)
    session["messages"].append({
        "role": role,
        "content": content,
        "timestamp": _now(),
    })
    _write(session)
    return session


def set_backend_conversation_id(session_id: str, conversation_id: str) -> dict:
    """Store the AI Manager backend conversation ID for this session."""
    session = load(session_id)
    session["backend_conversation_id"] = conversation_id
    # Keep legacy field name populated for forward-compat with older readers
    session["claude_session_id"] = conversation_id
    _write(session)
    return session


# Legacy alias kept for any external callers
def set_claude_session_id(session_id: str, claude_id: str) -> dict:
    return set_backend_conversation_id(session_id, claude_id)


def close_session(session_id: str) -> dict:
    session = load(session_id)
    session["status"] = "closed"
    _write(session)
    return session


def load(session_id: str) -> dict:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_sessions(agent: str | None = None, last: int = 20) -> list[dict]:
    if not SESSIONS_DIR.exists():
        return []
    files = sorted(SESSIONS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    results = []
    for f in files:
        s = json.loads(f.read_text(encoding="utf-8"))
        if agent and s.get("agent") != agent:
            continue
        results.append({
            "id": s["id"],
            "agent": s["agent"],
            "caller": s.get("caller", ""),
            "started": s["started"],
            "status": s["status"],
            "messages_count": len(s.get("messages", [])),
        })
        if len(results) >= last:
            break
    return results


def _write(session: dict) -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{session['id']}.json"
    path.write_text(
        json.dumps(session, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
