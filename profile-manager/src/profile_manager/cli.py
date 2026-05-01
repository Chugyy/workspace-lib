#!/usr/bin/env python3
"""Profile Manager CLI — manage credential profiles for workspace tools."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml

app = typer.Typer(help="Manage credential profiles for workspace tools.")

# Resolve paths
PROFILES_DIR = Path(__file__).parent.parent.parent.parent / ".profiles"
LIB_DIR = PROFILES_DIR.parent

sys.path.insert(0, str(PROFILES_DIR))
from resolver import (
    list_profiles,
    get_default,
    set_default,
    save_profile,
    remove_profile,
    resolve,
    ProfileNotFoundError,
)


def _get_tool_meta(tool_id: str) -> dict:
    """Load meta.yaml for a tool."""
    meta_path = LIB_DIR / tool_id / "meta.yaml"
    if not meta_path.exists():
        return {}
    with open(meta_path) as f:
        return yaml.safe_load(f) or {}


def _mask_value(value, show: bool = False) -> str:
    """Mask a secret value for display."""
    if show:
        return str(value)
    s = str(value)
    if len(s) <= 8:
        return "***"
    return s[:4] + "***" + s[-4:]


def _print_config(data: dict, show_secrets: bool = False, indent: int = 0):
    """Pretty-print a config dict with masked secrets."""
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            typer.echo(f"{prefix}{key}:")
            _print_config(value, show_secrets, indent + 1)
        else:
            display = _mask_value(value, show_secrets)
            typer.echo(f"{prefix}{key}: {display}")


@app.command("list")
def list_cmd(
    tool: Optional[str] = typer.Argument(None, help="Tool ID (omit to list all)"),
):
    """List tools and their profiles."""
    if tool:
        profiles = list_profiles(tool)
        default = get_default(tool)
        if not profiles:
            typer.echo(f"No profiles for '{tool}'.")
            raise typer.Exit(1)
        for p in profiles:
            marker = " (default)" if p == default else ""
            typer.echo(f"  {p}{marker}")
    else:
        # List all tools that have profiles
        if not PROFILES_DIR.exists():
            typer.echo("No profiles configured.")
            return
        tool_dirs = sorted(
            d for d in PROFILES_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
        )
        if not tool_dirs:
            typer.echo("No profiles configured.")
            return
        for tool_dir in tool_dirs:
            profiles = list_profiles(tool_dir.name)
            default = get_default(tool_dir.name)
            default_marker = f" [default: {default}]" if default else ""
            typer.echo(f"{tool_dir.name}: {', '.join(profiles)}{default_marker}")


@app.command("show")
def show(
    tool: str = typer.Argument(..., help="Tool ID"),
    name: str = typer.Argument(..., help="Profile name"),
    secrets: bool = typer.Option(False, "--secrets", help="Show unmasked secrets"),
):
    """Display a profile's configuration."""
    try:
        data = resolve(tool, name)
    except (ProfileNotFoundError, Exception) as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

    default = get_default(tool)
    marker = " (default)" if name == default else ""
    typer.echo(f"\n{tool}/{name}{marker}:")
    typer.echo("─" * 40)
    _print_config(data, show_secrets=secrets)
    typer.echo()


@app.command("add")
def add(
    tool: str = typer.Argument(..., help="Tool ID"),
    name: str = typer.Argument(..., help="Profile name"),
    make_default: bool = typer.Option(False, "--default", "-d", help="Set as default"),
):
    """Create a new profile interactively."""
    meta = _get_tool_meta(tool)
    requires = meta.get("requires", {})
    env_vars = requires.get("env", [])

    if not env_vars:
        typer.echo(f"Warning: no env requirements found in {tool}/meta.yaml")
        typer.echo("Creating empty profile. Edit manually.")
        data = {}
    else:
        typer.echo(f"\nAdding profile '{name}' for {tool}...")
        typer.echo(f"Required credentials (from meta.yaml):\n")
        data = {}
        for item in env_vars:
            if isinstance(item, dict):
                for var_name, help_text in item.items():
                    value = typer.prompt(f"  {var_name} [{help_text}]")
                    data[var_name] = value
            elif isinstance(item, str):
                value = typer.prompt(f"  {item}")
                data[item] = value

    path = save_profile(tool, name, data)
    typer.echo(f"\nProfile saved: {path}")

    # Set as default if requested or if it's the only profile
    if make_default or len(list_profiles(tool)) == 1:
        set_default(tool, name)
        typer.echo(f"Set as default profile for {tool}.")


@app.command("set-default")
def set_default_cmd(
    tool: str = typer.Argument(..., help="Tool ID"),
    name: str = typer.Argument(..., help="Profile name"),
):
    """Set the default profile for a tool."""
    try:
        set_default(tool, name)
        typer.echo(f"Default profile for {tool} set to '{name}'.")
    except ProfileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("remove")
def remove(
    tool: str = typer.Argument(..., help="Tool ID"),
    name: str = typer.Argument(..., help="Profile name"),
):
    """Remove a profile."""
    try:
        remove_profile(tool, name)
        typer.echo(f"Profile '{name}' removed for {tool}.")
    except ProfileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("import")
def import_cmd(
    tool: str = typer.Argument(..., help="Tool ID"),
    name: str = typer.Argument("default", help="Profile name to create"),
    make_default: bool = typer.Option(True, "--default/--no-default", help="Set as default"),
):
    """Import a profile from an existing assets/config.json or .env file."""
    tool_dir = LIB_DIR / tool

    # Try assets/config.json first
    config_json = tool_dir / "assets" / "config.json"
    if config_json.exists():
        with open(config_json) as f:
            data = json.load(f)
        path = save_profile(tool, name, data)
        typer.echo(f"Imported from {config_json} → {path}")
        if make_default:
            set_default(tool, name)
            typer.echo(f"Set as default profile for {tool}.")
        return

    # Try .env file
    env_file = tool_dir / ".env"
    if env_file.exists():
        data = {}
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip("'").strip('"')
        path = save_profile(tool, name, data)
        typer.echo(f"Imported from {env_file} → {path}")
        if make_default:
            set_default(tool, name)
            typer.echo(f"Set as default profile for {tool}.")
        return

    typer.echo(f"No config.json or .env found in {tool_dir}")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
