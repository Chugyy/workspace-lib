#!/usr/bin/env python3
"""
Environment detector — identifies which device the agent is running on.

Usage:
    python3 ../lib/detect-env.py          # Human-readable output
    python3 ../lib/detect-env.py --json   # JSON output
    python3 ../lib/detect-env.py --short  # Just the device name

Known environments:
    - VPS: hostname contains "dedibox", Linux
    - Mac: Darwin OS

Fields:
    preview_host  Host to use in preview URLs shown to the user.
                  On VPS this is the public IP (not localhost) so the
                  developer can open the link from their local machine.
"""

import json
import platform
import sys
from pathlib import Path


def _get_public_ip() -> str | None:
    """Try to get public IP for preview URLs on VPS."""
    try:
        import urllib.request
        return urllib.request.urlopen("https://api.ipify.org", timeout=3).read().decode().strip()
    except Exception:
        return None


def detect() -> dict:
    hostname = platform.node()
    system = platform.system()

    # Detect environment from hostname and OS
    # Add your own server hostnames here
    if system == "Linux" and ("dedibox" in hostname.lower() or "vps" in hostname.lower()):
        device = "vps"
        label = f"VPS ({hostname})"
        location = "Remote server"
        # Try to get public IP for preview URLs
        preview_host = _get_public_ip() or "localhost"
    elif system == "Darwin":
        device = "mac"
        label = "Mac (local)"
        location = "Local machine"
        preview_host = "localhost"
    elif system == "Windows":
        device = "windows"
        label = "Windows (local)"
        location = "Local machine"
        preview_host = "localhost"
    else:
        device = "unknown"
        label = f"Unknown ({hostname})"
        location = "?"
        preview_host = "localhost"

    return {
        "device": device,
        "label": label,
        "hostname": hostname,
        "os": system,
        "location": location,
        "arch": platform.machine(),
        "preview_host": preview_host,
    }


if __name__ == "__main__":
    env = detect()

    if "--json" in sys.argv:
        print(json.dumps(env, indent=2))
    elif "--short" in sys.argv:
        print(env["device"])
    else:
        print(f"🖥️  {env['label']}")
        print(f"   hostname:     {env['hostname']}")
        print(f"   os:           {env['os']} {env['arch']}")
        print(f"   location:     {env['location']}")
        print(f"   preview_host: {env['preview_host']}")
