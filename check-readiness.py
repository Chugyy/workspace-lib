#!/usr/bin/env python3
"""
PID Readiness Check — validates that a PID is fully configured.

Checks:
  1. .claude/.env exists and all variables from .env.example are filled
  2. .mcp.json exists and is valid JSON
  3. Lib tool dependencies (reads .mcp.json.example for referenced tools)

Usage:
    python3 ../../lib/check-readiness.py                 # Auto-detect PID from cwd
    python3 ../../lib/check-readiness.py /path/to/pid    # Explicit PID path
    python3 ../../lib/check-readiness.py --json           # JSON output for agents
    python3 ../../lib/check-readiness.py --lib email      # Check a lib tool instead

Exit codes:
    0  All checks passed (READY)
    1  Some checks failed (NOT READY or PARTIAL)
    2  Invalid arguments or path
"""

import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Placeholder detection
# ---------------------------------------------------------------------------

# Patterns that indicate a value was never filled in.
# Each pattern is matched against the *entire* value (case-insensitive).
PLACEHOLDER_PATTERNS: list[re.Pattern] = [
    re.compile(r"^your[-_]", re.IGNORECASE),
    re.compile(r"^sk-ant-x{4,}", re.IGNORECASE),
    re.compile(r"^ghp_x{4,}", re.IGNORECASE),
    re.compile(r"^xoxb-x{4,}", re.IGNORECASE),
    re.compile(r"^xxxx", re.IGNORECASE),
    re.compile(r"^sk_live_\.{3}$", re.IGNORECASE),
    re.compile(r"^CHANGE[-_]?ME$", re.IGNORECASE),
    re.compile(r"^TODO$", re.IGNORECASE),
    re.compile(r"^<.+>$"),  # <your-value-here>
    re.compile(r"^\$\{.+\}$"),  # ${VAR} — unexpanded placeholder
    re.compile(r"^/path/to/", re.IGNORECASE),
]


def is_placeholder(value: str) -> bool:
    """Return True if *value* looks like an unfilled placeholder."""
    if not value or not value.strip():
        return True
    value = value.strip()
    return any(p.search(value) for p in PLACEHOLDER_PATTERNS)


# ---------------------------------------------------------------------------
# .env parsing
# ---------------------------------------------------------------------------

class EnvVar(NamedTuple):
    key: str
    value: str
    comment: str  # help text from .env.example (lines above the key)


def parse_env_file(path: Path) -> list[EnvVar]:
    """Parse a .env file, preserving comments as help text for each variable.

    Section headers (``# === Name ===``) are skipped so that only
    descriptive comments end up attached to variables.
    """
    if not path.exists():
        return []
    vars_: list[EnvVar] = []
    pending_comments: list[str] = []
    section_header_re = re.compile(r"^#\s*===.*===\s*$")
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            pending_comments = []
            continue
        if stripped.startswith("#"):
            if section_header_re.match(stripped):
                # Section header — reset and skip
                pending_comments = []
                continue
            pending_comments.append(stripped.lstrip("# ").strip())
            continue
        if "=" not in stripped:
            pending_comments = []
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        comment = " | ".join(pending_comments) if pending_comments else ""
        vars_.append(EnvVar(key=key, value=value, comment=comment))
        pending_comments = []
    return vars_


def env_as_dict(vars_: list[EnvVar]) -> dict[str, EnvVar]:
    return {v.key: v for v in vars_}


# ---------------------------------------------------------------------------
# Check: .env
# ---------------------------------------------------------------------------

class EnvCheckResult(NamedTuple):
    exists: bool
    required_vars: list[EnvVar]   # from .env.example
    configured: list[str]         # keys with real values
    placeholders: list[str]       # keys still holding placeholder values
    missing_keys: list[str]       # keys in example but absent from .env


def check_env(pid_root: Path) -> EnvCheckResult:
    """Check .claude/.env against .claude/.env.example."""
    example_path = pid_root / ".claude" / ".env.example"
    env_path = pid_root / ".claude" / ".env"

    if not example_path.exists():
        # No .env.example means no env requirements
        return EnvCheckResult(
            exists=env_path.exists(),
            required_vars=[],
            configured=[],
            placeholders=[],
            missing_keys=[],
        )

    required = parse_env_file(example_path)

    if not env_path.exists():
        return EnvCheckResult(
            exists=False,
            required_vars=required,
            configured=[],
            placeholders=[],
            missing_keys=[v.key for v in required],
        )

    actual = env_as_dict(parse_env_file(env_path))
    configured: list[str] = []
    placeholders: list[str] = []
    missing_keys: list[str] = []

    for rv in required:
        if rv.key not in actual:
            missing_keys.append(rv.key)
        elif is_placeholder(actual[rv.key].value):
            placeholders.append(rv.key)
        else:
            configured.append(rv.key)

    return EnvCheckResult(
        exists=True,
        required_vars=required,
        configured=configured,
        placeholders=placeholders,
        missing_keys=missing_keys,
    )


# ---------------------------------------------------------------------------
# Check: .mcp.json
# ---------------------------------------------------------------------------

class McpCheckResult(NamedTuple):
    exists: bool
    valid_json: bool | None  # None if file doesn't exist
    error: str | None        # JSON parse error if invalid


def check_mcp(pid_root: Path) -> McpCheckResult:
    """Check if .mcp.json exists and is valid JSON."""
    mcp_path = pid_root / ".mcp.json"
    if not mcp_path.exists():
        return McpCheckResult(exists=False, valid_json=None, error=None)
    try:
        json.loads(mcp_path.read_text())
        return McpCheckResult(exists=True, valid_json=True, error=None)
    except json.JSONDecodeError as e:
        return McpCheckResult(exists=True, valid_json=False, error=str(e))


# ---------------------------------------------------------------------------
# Check: lib tool
# ---------------------------------------------------------------------------

class LibCheckResult(NamedTuple):
    exists: bool
    env_exists: bool
    required_vars: list[EnvVar]
    configured: list[str]
    placeholders: list[str]
    missing_keys: list[str]
    has_venv: bool
    has_setup: bool


def check_lib_tool(lib_root: Path) -> LibCheckResult:
    """Check a lib tool's readiness (.env, venv, setup)."""
    example_path = lib_root / ".env.example"
    env_path = lib_root / ".env"

    required: list[EnvVar] = []
    if example_path.exists():
        required = parse_env_file(example_path)

    configured: list[str] = []
    placeholders: list[str] = []
    missing_keys: list[str] = []

    if required and env_path.exists():
        actual = env_as_dict(parse_env_file(env_path))
        for rv in required:
            if rv.key not in actual:
                missing_keys.append(rv.key)
            elif is_placeholder(actual[rv.key].value):
                placeholders.append(rv.key)
            else:
                configured.append(rv.key)
    elif required:
        missing_keys = [v.key for v in required]

    return LibCheckResult(
        exists=lib_root.exists(),
        env_exists=env_path.exists(),
        required_vars=required,
        configured=configured,
        placeholders=placeholders,
        missing_keys=missing_keys,
        has_venv=(lib_root / ".venv").is_dir(),
        has_setup=(lib_root / "setup.sh").exists(),
    )


# ---------------------------------------------------------------------------
# Rendering — human-readable
# ---------------------------------------------------------------------------

def render_human(pid_name: str, env_result: EnvCheckResult, mcp_result: McpCheckResult) -> str:
    lines: list[str] = []
    issues = 0

    lines.append(f"=== PID Readiness Check: {pid_name} ===")
    lines.append("")

    # --- .env ---
    if not env_result.required_vars:
        lines.append(".env status: ✅ N/A (no .env.example found)")
    elif not env_result.exists:
        issues += 1
        lines.append(".env status: ❌ MISSING")
        lines.append("  Required variables (from .env.example):")
        for v in env_result.required_vars:
            help_text = f" ({v.comment})" if v.comment else ""
            lines.append(f"  - {v.key}{help_text}")
        lines.append("")
        lines.append("  Fix: cp .claude/.env.example .claude/.env && edit .claude/.env")
    else:
        total = len(env_result.required_vars)
        ok = len(env_result.configured)
        bad = len(env_result.placeholders) + len(env_result.missing_keys)
        if bad == 0:
            lines.append(f".env status: ✅ OK ({ok}/{total} variables configured)")
        else:
            issues += bad
            lines.append(f".env status: ⚠️  PARTIAL ({ok}/{total} variables configured)")

        req_dict = {v.key: v for v in env_result.required_vars}
        for key in env_result.configured:
            lines.append(f"  ✅ {key}: configured")
        for key in env_result.placeholders:
            help_text = f" ({req_dict[key].comment})" if key in req_dict and req_dict[key].comment else ""
            lines.append(f"  ❌ {key}: placeholder value{help_text}")
        for key in env_result.missing_keys:
            help_text = f" ({req_dict[key].comment})" if key in req_dict and req_dict[key].comment else ""
            lines.append(f"  ❌ {key}: not set{help_text}")

    lines.append("")

    # --- .mcp.json ---
    if not mcp_result.exists:
        issues += 1
        lines.append(".mcp.json status: ❌ MISSING")
        lines.append("  Run: python3 .claude/build.py")
    elif not mcp_result.valid_json:
        issues += 1
        lines.append(f".mcp.json status: ❌ INVALID JSON")
        lines.append(f"  Error: {mcp_result.error}")
        lines.append("  Fix: regenerate with python3 .claude/build.py")
    else:
        lines.append(".mcp.json status: ✅ OK")

    lines.append("")

    # --- Overall ---
    if issues == 0:
        lines.append("Overall: READY")
    elif len(env_result.configured) > 0 and issues > 0:
        lines.append(f"Overall: PARTIAL — {issues} issue(s) to fix")
    else:
        lines.append(f"Overall: NOT READY — {issues} issue(s) to fix")

    return "\n".join(lines)


def render_lib_human(tool_name: str, result: LibCheckResult) -> str:
    lines: list[str] = []
    issues = 0

    lines.append(f"=== Lib Tool Readiness Check: {tool_name} ===")
    lines.append("")

    if not result.exists:
        lines.append(f"Tool directory not found.")
        lines.append(f"Overall: NOT READY — directory missing")
        return "\n".join(lines)

    # --- .env ---
    if not result.required_vars:
        lines.append(".env status: ✅ N/A (no credentials required)")
    elif not result.env_exists:
        issues += 1
        lines.append(".env status: ❌ MISSING")
        lines.append("  Required variables (from .env.example):")
        for v in result.required_vars:
            help_text = f" ({v.comment})" if v.comment else ""
            lines.append(f"  - {v.key}{help_text}")
        lines.append("")
        lines.append("  Fix: cp .env.example .env && edit .env")
    else:
        total = len(result.required_vars)
        ok = len(result.configured)
        bad = len(result.placeholders) + len(result.missing_keys)
        if bad == 0:
            lines.append(f".env status: ✅ OK ({ok}/{total} variables configured)")
        else:
            issues += bad
            lines.append(f".env status: ⚠️  PARTIAL ({ok}/{total} variables configured)")

        req_dict = {v.key: v for v in result.required_vars}
        for key in result.configured:
            lines.append(f"  ✅ {key}: configured")
        for key in result.placeholders:
            help_text = f" ({req_dict[key].comment})" if key in req_dict and req_dict[key].comment else ""
            lines.append(f"  ❌ {key}: placeholder value{help_text}")
        for key in result.missing_keys:
            help_text = f" ({req_dict[key].comment})" if key in req_dict and req_dict[key].comment else ""
            lines.append(f"  ❌ {key}: not set{help_text}")

    lines.append("")

    # --- venv / setup ---
    if result.has_setup and not result.has_venv:
        issues += 1
        lines.append(f"venv status: ❌ MISSING (setup.sh exists but .venv/ not found)")
        lines.append("  Run: ./setup.sh")
    elif result.has_venv:
        lines.append("venv status: ✅ OK")
    elif result.has_setup:
        lines.append("venv status: ⚠️  setup.sh exists, .venv not created yet")
    else:
        lines.append("venv status: ✅ N/A (no setup.sh)")

    lines.append("")

    # --- Overall ---
    if issues == 0:
        lines.append("Overall: READY")
    else:
        lines.append(f"Overall: NOT READY — {issues} issue(s) to fix")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rendering — JSON (for AI agents)
# ---------------------------------------------------------------------------

def render_json(pid_name: str, env_result: EnvCheckResult, mcp_result: McpCheckResult) -> str:
    total = len(env_result.required_vars)
    ok = len(env_result.configured)
    bad = len(env_result.placeholders) + len(env_result.missing_keys)

    if total == 0:
        env_status = "n/a"
    elif not env_result.exists:
        env_status = "missing"
    elif bad == 0:
        env_status = "ok"
    else:
        env_status = "partial"

    if not mcp_result.exists:
        mcp_status = "missing"
    elif not mcp_result.valid_json:
        mcp_status = "invalid"
    else:
        mcp_status = "ok"

    if env_status in ("ok", "n/a") and mcp_status == "ok":
        overall = "ready"
    elif ok > 0:
        overall = "partial"
    else:
        overall = "not_ready"

    data = {
        "pid": pid_name,
        "overall": overall,
        "env": {
            "status": env_status,
            "total": total,
            "configured": ok,
            "issues": bad,
            "configured_keys": env_result.configured,
            "placeholder_keys": env_result.placeholders,
            "missing_keys": env_result.missing_keys,
        },
        "mcp": {
            "status": mcp_status,
            "error": mcp_result.error,
        },
    }
    return json.dumps(data, indent=2)


def render_lib_json(tool_name: str, result: LibCheckResult) -> str:
    total = len(result.required_vars)
    ok = len(result.configured)
    bad = len(result.placeholders) + len(result.missing_keys)

    if not result.exists:
        env_status = "missing_dir"
    elif total == 0:
        env_status = "n/a"
    elif not result.env_exists:
        env_status = "missing"
    elif bad == 0:
        env_status = "ok"
    else:
        env_status = "partial"

    if not result.exists:
        overall = "not_ready"
    elif env_status in ("ok", "n/a") and (not result.has_setup or result.has_venv):
        overall = "ready"
    else:
        overall = "not_ready"

    data = {
        "tool": tool_name,
        "overall": overall,
        "env": {
            "status": env_status,
            "total": total,
            "configured": ok,
            "issues": bad,
            "configured_keys": result.configured,
            "placeholder_keys": result.placeholders,
            "missing_keys": result.missing_keys,
        },
        "venv": {
            "has_setup": result.has_setup,
            "has_venv": result.has_venv,
        },
    }
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# PID detection
# ---------------------------------------------------------------------------

def detect_pid_root(cwd: Path) -> Path | None:
    """Walk up from cwd looking for a directory containing .claude/CLAUDE.md."""
    current = cwd.resolve()
    for _ in range(10):  # max 10 levels up
        if (current / ".claude" / "CLAUDE.md").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def resolve_lib_path(name: str) -> Path | None:
    """Resolve a lib tool path from its name."""
    script_dir = Path(__file__).resolve().parent  # lib/
    candidate = script_dir / name
    if candidate.is_dir():
        return candidate
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    output_json = "--json" in args
    if "--json" in args:
        args.remove("--json")

    # --- Lib tool mode ---
    if "--lib" in args:
        idx = args.index("--lib")
        args.remove("--lib")
        if not args:
            print("ERROR: --lib requires a tool name", file=sys.stderr)
            print("Usage: python3 check-readiness.py --lib <tool-name>", file=sys.stderr)
            return 2
        tool_name = args[idx] if idx < len(args) else args[0]
        lib_path = resolve_lib_path(tool_name)
        if lib_path is None:
            print(f"ERROR: lib tool '{tool_name}' not found in {Path(__file__).resolve().parent}", file=sys.stderr)
            return 2
        result = check_lib_tool(lib_path)
        if output_json:
            print(render_lib_json(tool_name, result))
        else:
            print(render_lib_human(tool_name, result))
        return 0 if result.exists and not result.missing_keys and not result.placeholders and (not result.has_setup or result.has_venv) else 1

    # --- PID mode ---
    if args:
        pid_root = Path(args[0]).resolve()
        if not pid_root.is_dir():
            print(f"ERROR: {pid_root} is not a directory", file=sys.stderr)
            return 2
        if not (pid_root / ".claude").is_dir():
            print(f"ERROR: {pid_root} does not contain a .claude/ directory", file=sys.stderr)
            return 2
    else:
        pid_root = detect_pid_root(Path.cwd())
        if pid_root is None:
            print("ERROR: Could not detect PID root from current directory.", file=sys.stderr)
            print("  Run from inside a PID directory or pass the path as argument.", file=sys.stderr)
            print("  Usage: python3 check-readiness.py [/path/to/pid] [--json]", file=sys.stderr)
            return 2

    pid_name = pid_root.name
    env_result = check_env(pid_root)
    mcp_result = check_mcp(pid_root)

    if output_json:
        print(render_json(pid_name, env_result, mcp_result))
    else:
        print(render_human(pid_name, env_result, mcp_result))

    # Exit code
    total_issues = len(env_result.placeholders) + len(env_result.missing_keys)
    if not mcp_result.exists or (mcp_result.exists and not mcp_result.valid_json):
        total_issues += 1
    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
