"""Runner — invokes agents via the AI Manager backend API."""

from pathlib import Path
from typing import Optional

import yaml

from agent_invoke import api


def _find_workspace_root() -> Path:
    """Walk up from this file to find the directory containing lib/ and pids/."""
    p = Path(__file__).resolve()
    while p != p.parent:
        if (p / "lib").is_dir() and (p / "pids").is_dir():
            return p
        p = p.parent
    raise RuntimeError("Cannot find workspace root (directory with lib/ and pids/)")


WORKSPACE_ROOT = _find_workspace_root()
LIB_DIR = WORKSPACE_ROOT / "lib"
PIDS_DIR = WORKSPACE_ROOT / "pids"


def _scan_agents_in(base_dir: Path, max_depth: int = 2) -> list[dict]:
    """Scan for meta.yaml with type: agent up to max_depth levels deep."""
    agents = []
    if not base_dir.exists():
        return agents
    for depth in range(1, max_depth + 1):
        pattern = "/".join(["*"] * depth) + "/meta.yaml"
        for meta_path in sorted(base_dir.glob(pattern)):
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            if meta and meta.get("id") and meta.get("type") == "agent":
                agents.append({
                    "id": meta["id"],
                    "description": meta.get("description", ""),
                    "model": meta.get("model", "sonnet"),
                    "max_turns": meta.get("max_turns", 10),
                    "path": str(meta_path.parent.relative_to(WORKSPACE_ROOT)),
                })
    # Deduplicate by id (first found wins)
    seen = set()
    unique = []
    for a in agents:
        if a["id"] not in seen:
            seen.add(a["id"])
            unique.append(a)
    return unique


def list_agents() -> list[dict]:
    """List all available agents from pids/ and lib/."""
    return _scan_agents_in(PIDS_DIR) + _scan_agents_in(LIB_DIR, max_depth=1)


def resolve_agent(name: str) -> tuple[Path, dict]:
    """Resolve agent directory and config. Searches pids/ then lib/."""
    # Search pids/ first (direct child or nested under a profile)
    for candidate in [PIDS_DIR / name, *sorted(PIDS_DIR.glob(f"*/{name}"))]:
        meta_path = candidate / "meta.yaml"
        if meta_path.exists():
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            if meta.get("type") == "agent":
                return candidate, meta

    # Fallback to lib/
    agent_dir = LIB_DIR / name
    meta_path = agent_dir / "meta.yaml"
    if meta_path.exists():
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        if meta.get("type") == "agent":
            return agent_dir, meta

    raise FileNotFoundError(f"Agent not found: {name} (searched pids/ and lib/)")


def _expand_model(model: str) -> str:
    """Expand short model names to full Anthropic model IDs."""
    _ALIASES = {
        "sonnet": "claude-sonnet-4-5",
        "opus": "claude-opus-4-5",
        "haiku": "claude-haiku-4-5",
        "sonnet-4": "claude-sonnet-4-5",
        "opus-4": "claude-opus-4-5",
        # Legacy aliases
        "claude-sonnet-4-20250514": "claude-sonnet-4-5",
    }
    return _ALIASES.get(model, model)


def _build_route_id(
    model: str,
    sdk: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    """Build a model route ID for UAS routing.

    If sdk and provider are given, constructs `sdk:provider:model_id`.
    Otherwise returns the plain (alias-expanded) model ID and lets the
    backend infer the routing via its default resolution logic.
    """
    expanded = _expand_model(model)
    if sdk and provider:
        return f"{sdk}:{provider}:{expanded}"
    if sdk:
        # sdk without provider — not a full route, use plain model
        # and let the backend resolve provider from UAS
        return expanded
    return expanded


def _collect_text(events: list[dict]) -> str:
    """Extract concatenated assistant text from a list of SSE events."""
    parts = []
    for event in events:
        if event.get("type") == "assistant":
            for block in event.get("blocks", []):
                if block.get("type") == "text":
                    parts.append(block["text"])
    return "".join(parts).strip()


def run(
    agent_dir: Optional[Path],
    prompt: str,
    model: str = "sonnet",
    max_turns: int = 10,
    timeout: int = 300,
    # resume_session_id is now a backend conversation_id
    resume_session_id: Optional[str] = None,
    # Runtime overrides
    cwd: Optional[str] = None,
    agent_directory: Optional[str] = None,
    pid: Optional[str] = None,
    system_prompt_paths: Optional[list] = None,
    # Routing overrides (construct route ID: sdk:provider:model_id)
    sdk: Optional[str] = None,
    provider: Optional[str] = None,
) -> dict:
    """Invoke agent via AI Manager API and return assembled result.

    Returns dict with keys: result, session_id, cost_usd, num_turns, is_error
    """
    full_model = _build_route_id(model, sdk=sdk, provider=provider)

    try:
        # --- Resume: reuse existing backend conversation ---
        if resume_session_id:
            conversation_id = resume_session_id
            try:
                api.send_message(conversation_id, prompt)
            except RuntimeError as exc:
                return {
                    "result": str(exc),
                    "session_id": conversation_id,
                    "cost_usd": 0,
                    "num_turns": 0,
                    "is_error": True,
                }
        else:
            # --- New conversation: resolve cwd and agent_directory ---
            resolved_cwd = cwd
            resolved_agent_dir = agent_directory

            if resolved_cwd is None and agent_dir is not None:
                # Default cwd = agent_dir itself
                resolved_cwd = str(agent_dir)

            if resolved_agent_dir is None and agent_dir is not None:
                # Look for .agent/ sub-directory (PID layout)
                agent_dot_dir = agent_dir / ".agent"
                if agent_dot_dir.is_dir():
                    resolved_agent_dir = str(agent_dot_dir)
                else:
                    resolved_agent_dir = str(agent_dir)

            conv = api.create_conversation(
                model=full_model,
                pid=pid,
                cwd=resolved_cwd,
                agent_directory=resolved_agent_dir,
                system_prompt_paths=system_prompt_paths,
            )
            conversation_id = conv["id"]

            try:
                api.send_message(conversation_id, prompt)
            except RuntimeError as exc:
                return {
                    "result": str(exc),
                    "session_id": conversation_id,
                    "cost_usd": 0,
                    "num_turns": 0,
                    "is_error": True,
                }

        # --- Stream events and collect result ---
        collected_events: list[dict] = []
        is_error = False
        error_message = ""
        cost_usd = 0.0
        num_turns = 0

        for event in api.stream_events(conversation_id, timeout=timeout):
            etype = event.get("type")

            if etype == "assistant":
                collected_events.append(event)

            elif etype == "error":
                is_error = True
                error_message = event.get("message", "Unknown error")

            elif etype == "usage_update":
                # Approximate cost — rough estimation, backend tracks more precisely
                input_tok = event.get("input_tokens", 0)
                output_tok = event.get("output_tokens", 0)
                # ~$3/Mtok input, ~$15/Mtok output (Sonnet 4.5 pricing approx)
                cost_usd += (input_tok * 3 + output_tok * 15) / 1_000_000
                num_turns += 1

            elif etype in ("completed", "stopped"):
                break

            elif etype == "idle":
                # No agent was running — conversation may already be done
                break

        result_text = _collect_text(collected_events)
        if is_error and not result_text:
            result_text = error_message or "Agent returned an error"

        return {
            "result": result_text,
            "session_id": conversation_id,
            "cost_usd": round(cost_usd, 6),
            "num_turns": num_turns,
            "is_error": is_error,
        }

    except ConnectionError as exc:
        return {
            "result": str(exc),
            "session_id": None,
            "cost_usd": 0,
            "num_turns": 0,
            "is_error": True,
        }
    except Exception as exc:
        return {
            "result": f"Unexpected error: {exc}",
            "session_id": None,
            "cost_usd": 0,
            "num_turns": 0,
            "is_error": True,
        }
