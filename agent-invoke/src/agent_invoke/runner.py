"""Runner — spawns claude processes in agent directories."""

import json
import subprocess
from pathlib import Path

import yaml

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


def run(
    agent_dir: Path,
    prompt: str,
    model: str = "sonnet",
    max_turns: int = 10,
    timeout: int = 300,
    resume_session_id: str | None = None,
) -> dict:
    """Spawn claude in agent directory and return parsed result.

    Returns dict with keys: result, session_id, cost_usd, num_turns, is_error
    """
    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--model", model,
        "--max-turns", str(max_turns),
    ]

    if resume_session_id:
        cmd.extend(["--resume", resume_session_id])

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(agent_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {
            "result": f"Timeout after {timeout}s",
            "session_id": None,
            "cost_usd": 0,
            "num_turns": 0,
            "is_error": True,
        }

    if proc.returncode != 0 and not proc.stdout.strip():
        return {
            "result": proc.stderr.strip() or f"Process exited with code {proc.returncode}",
            "session_id": None,
            "cost_usd": 0,
            "num_turns": 0,
            "is_error": True,
        }

    # Parse JSON output — handle both single object and stream
    output_text = proc.stdout.strip()
    try:
        data = json.loads(output_text)
    except json.JSONDecodeError:
        # Stream mode: take last valid JSON line
        lines = [l for l in output_text.splitlines() if l.strip().startswith("{")]
        if lines:
            try:
                data = json.loads(lines[-1])
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

    return {
        "result": data.get("result", output_text),
        "session_id": data.get("session_id"),
        "cost_usd": data.get("cost_usd", 0),
        "num_turns": data.get("num_turns", 0),
        "is_error": data.get("is_error", False),
    }
