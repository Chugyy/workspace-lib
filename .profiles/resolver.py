"""
Profile resolver for workspace CLI tools.

Resolution order:
1. Explicit profile name (--profile argument)
2. Environment variable override (<TOOL_ID>_PROFILE=name)
3. _default file in tool's profile directory
4. Single-profile fallback (if only one profile exists, use it)

Usage in any CLI:
    from resolver import resolve
    config = resolve("telegram", profile_name)
"""

import json
import os
from pathlib import Path
from typing import Optional


PROFILES_DIR = Path(__file__).parent


class ProfileNotFoundError(Exception):
    """Raised when a requested profile does not exist."""
    pass


class NoProfileError(Exception):
    """Raised when no profile can be resolved for a tool."""
    pass


def resolve(tool_id: str, profile: Optional[str] = None) -> dict:
    """Resolve and load a profile for the given tool.

    Args:
        tool_id: Tool identifier (e.g., "telegram", "whatsapp")
        profile: Explicit profile name. If None, resolution chain is used.

    Returns:
        dict: Profile configuration data.

    Raises:
        ProfileNotFoundError: If the requested profile does not exist.
        NoProfileError: If no profile can be resolved.
    """
    tool_dir = PROFILES_DIR / tool_id

    # 1. Explicit profile name
    if profile:
        return _load_profile(tool_dir, profile)

    # 2. Environment variable override (TELEGRAM_PROFILE, WHATSAPP_PROFILE, etc.)
    env_key = f"{tool_id.upper().replace('-', '_')}_PROFILE"
    env_profile = os.environ.get(env_key)
    if env_profile:
        return _load_profile(tool_dir, env_profile)

    # 3. _default file
    default_file = tool_dir / "_default"
    if default_file.exists():
        default_name = default_file.read_text().strip()
        if default_name:
            return _load_profile(tool_dir, default_name)

    # 4. Single-profile fallback
    if tool_dir.exists():
        profiles = list(tool_dir.glob("*.json"))
        if len(profiles) == 1:
            return json.loads(profiles[0].read_text())

    raise NoProfileError(
        f"No profile found for '{tool_id}'. "
        f"Run: profile add {tool_id} <name>"
    )


def _load_profile(tool_dir: Path, name: str) -> dict:
    """Load a specific profile by name."""
    path = tool_dir / f"{name}.json"
    if not path.exists():
        available = list_profiles(tool_dir.name)
        raise ProfileNotFoundError(
            f"Profile '{name}' not found for '{tool_dir.name}'. "
            f"Available: {available}"
        )
    return json.loads(path.read_text())


def list_profiles(tool_id: str) -> list[str]:
    """List available profile names for a tool."""
    tool_dir = PROFILES_DIR / tool_id
    if not tool_dir.exists():
        return []
    return sorted(p.stem for p in tool_dir.glob("*.json"))


def get_default(tool_id: str) -> Optional[str]:
    """Get the default profile name for a tool, or None."""
    default_file = PROFILES_DIR / tool_id / "_default"
    if default_file.exists():
        name = default_file.read_text().strip()
        return name if name else None
    return None


def set_default(tool_id: str, profile_name: str) -> None:
    """Set the default profile for a tool."""
    tool_dir = PROFILES_DIR / tool_id
    if not (tool_dir / f"{profile_name}.json").exists():
        raise ProfileNotFoundError(
            f"Profile '{profile_name}' not found for '{tool_id}'."
        )
    (tool_dir / "_default").write_text(profile_name + "\n")


def save_profile(tool_id: str, profile_name: str, data: dict) -> Path:
    """Save profile data to disk."""
    tool_dir = PROFILES_DIR / tool_id
    tool_dir.mkdir(parents=True, exist_ok=True)
    path = tool_dir / f"{profile_name}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


def remove_profile(tool_id: str, profile_name: str) -> None:
    """Remove a profile."""
    tool_dir = PROFILES_DIR / tool_id
    path = tool_dir / f"{profile_name}.json"
    if not path.exists():
        raise ProfileNotFoundError(
            f"Profile '{profile_name}' not found for '{tool_id}'."
        )
    path.unlink()

    # If this was the default, remove the _default file
    default_file = tool_dir / "_default"
    if default_file.exists() and default_file.read_text().strip() == profile_name:
        default_file.unlink()
