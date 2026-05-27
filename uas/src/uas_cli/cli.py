"""UAS CLI — manage Universal Agent Service from the command line."""

import json
import sys
from typing import Optional

import httpx
import typer

from uas_cli.client import UasClient

app = typer.Typer(help="Universal Agent Service CLI.", no_args_is_help=True)
mcp_app = typer.Typer(help="MCP server management.", no_args_is_help=True)

app.add_typer(mcp_app, name="mcp")

# Global state
_profile_name: Optional[str] = None
_json_output: bool = False


@app.callback()
def main(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name (stable, dev, etc.)"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Universal Agent Service CLI."""
    global _profile_name, _json_output
    _profile_name = profile
    _json_output = json_out


def _client() -> UasClient:
    return UasClient(profile=_profile_name)


def _out(data, fmt_func=None):
    """Output data as JSON or formatted text."""
    if _json_output:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
    elif fmt_func:
        fmt_func(data)
    else:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))


# ══════════════════════════════════════════════════════════════════
# MCP sub-commands
# ══════════════════════════════════════════════════════════════════

@mcp_app.command("status")
def mcp_status():
    """Show MCP server connection status."""
    try:
        data = _client().mcp_status()
    except httpx.ConnectError:
        typer.echo(typer.style("Error: Cannot connect to UAS service.", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    def fmt(d):
        summary = d.get("summary", {})
        servers = d.get("servers", [])
        total = summary.get("total", len(servers))
        connected = summary.get("connected", 0)
        total_tools = summary.get("totalTools", 0)
        tokens = summary.get("toolsTokenEstimate", 0)

        # Header
        tokens_str = ""
        if tokens:
            if tokens >= 1000:
                tokens_str = f" · ~{tokens / 1000:.1f}k tokens overhead"
            else:
                tokens_str = f" · ~{tokens} tokens overhead"
        typer.echo(f"MCP Servers — {connected}/{total} connected · {total_tools} tools{tokens_str}")
        typer.echo("")

        if not servers:
            typer.echo("  No MCP servers configured.")
            return

        # Column widths
        name_w = max(len(s.get("name", "")) for s in servers)
        name_w = max(name_w, 6)  # minimum width for "SERVER"
        tools_w = 5

        typer.echo(f"  {'STATUS':14s} {'SERVER':<{name_w}s}   {'TOOLS':>{tools_w}s}")
        typer.echo(f"  {'─' * (14 + name_w + tools_w + 4)}")

        for s in servers:
            name = s.get("name", "?")
            status = s.get("status", "unknown")
            tool_count = s.get("toolCount", 0)
            error = s.get("error", "")

            if status == "connected":
                icon = typer.style("✓ connected", fg=typer.colors.GREEN)
                tools_str = str(tool_count)
            else:
                icon = typer.style("✗ failed   ", fg=typer.colors.RED)
                tools_str = "—"

            line = f"  {icon}   {name:<{name_w}s}   {tools_str:>{tools_w}s}"
            if error:
                truncated = error[:60] + ("..." if len(error) > 60 else "")
                line += f"     {typer.style(truncated, dim=True)}"
            typer.echo(line)

    _out(data, fmt)


@mcp_app.command("tools")
def mcp_tools(
    server: Optional[str] = typer.Option(None, "--server", "-s", help="Filter by server name"),
):
    """List all discovered MCP tools."""
    try:
        data = _client().mcp_tools(server=server)
    except httpx.ConnectError:
        typer.echo(typer.style("Error: Cannot connect to UAS service.", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    def fmt(d):
        tools = d.get("tools", [])
        total = len(tools)

        typer.echo(f"MCP Tools — {total} total")
        typer.echo("")

        if not tools:
            typer.echo("  No tools discovered.")
            return

        # Compute column widths
        server_w = 6  # minimum for "SERVER"
        tool_w = 4    # minimum for "TOOL"
        for t in tools:
            srv = t.get("server", "")
            # Strip mcp__{server}__ prefix from tool name
            raw_name = t.get("name", "")
            clean_name = _strip_mcp_prefix(raw_name, srv)
            server_w = max(server_w, len(srv))
            tool_w = max(tool_w, len(clean_name))

        # Cap widths for readability
        server_w = min(server_w, 25)
        tool_w = min(tool_w, 40)
        desc_w = 40

        typer.echo(f"  {'SERVER':<{server_w}s}   {'TOOL':<{tool_w}s}   {'DESCRIPTION':<{desc_w}s}")
        typer.echo(f"  {'─' * (server_w + tool_w + desc_w + 6)}")

        for t in tools:
            srv = t.get("server", "?")
            raw_name = t.get("name", "?")
            clean_name = _strip_mcp_prefix(raw_name, srv)
            desc = (t.get("description") or "")[:desc_w]
            desc = desc.replace("\n", " ")

            typer.echo(
                f"  {srv:<{server_w}s}   "
                f"{clean_name:<{tool_w}s}   "
                f"{desc:<{desc_w}s}"
            )

    _out(data, fmt)


@mcp_app.command("reconnect")
def mcp_reconnect(
    name: Optional[str] = typer.Argument(None, help="Server name to reconnect (all if omitted)"),
):
    """Reconnect MCP servers (all or a specific one)."""
    try:
        target = name or "all MCP servers"
        typer.echo(f"Reconnecting {target}...")
        data = _client().mcp_reconnect(server=name)
    except httpx.ConnectError:
        typer.echo(typer.style("Error: Cannot connect to UAS service.", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    def fmt(d):
        summary = d.get("summary", {})
        total = summary.get("total", 0)
        connected = summary.get("connected", 0)
        total_tools = summary.get("totalTools", 0)
        typer.echo(f"Done: {connected}/{total} connected · {total_tools} tools")

    _out(data, fmt)


# ══════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════

def _strip_mcp_prefix(tool_name: str, server_name: str) -> str:
    """Strip the mcp__{server}__ prefix from a tool name."""
    prefix = f"mcp__{server_name}__"
    if tool_name.startswith(prefix):
        return tool_name[len(prefix):]
    return tool_name


if __name__ == "__main__":
    app()
