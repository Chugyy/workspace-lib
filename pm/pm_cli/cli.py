"""
Process Manager CLI.

Thin client over the AI Manager Process API.
Usage: pm <command> [args]
"""

import click

from pm_cli import client


# --- Formatting helpers ---

_STATUS_ICONS = {
    "online": "\033[32m●\033[0m",   # green
    "stopped": "\033[90m○\033[0m",   # gray
    "stopping": "\033[33m◐\033[0m",  # yellow
    "errored": "\033[31m✖\033[0m",   # red
    "unknown": "\033[90m?\033[0m",
}

_CATEGORY_ORDER = ["core", "connector", "service", "agent", "worker", "other"]


def _status_icon(status: str) -> str:
    return _STATUS_ICONS.get(status, _STATUS_ICONS["unknown"])


_DOKPLOY_STATUS_ICONS = {
    "running": "\033[32m●\033[0m",   # green
    "done": "\033[32m●\033[0m",      # green (alias)
    "idle": "\033[33m○\033[0m",      # yellow
    "error": "\033[31m✖\033[0m",     # red
}


def _dokploy_status_icon(status: str) -> str:
    return _DOKPLOY_STATUS_ICONS.get(status, _STATUS_ICONS.get("unknown", "?"))


def _print_process_table(processes: list[dict], dokploy_apps: list[dict] | None = None):
    """Print processes grouped by category, then Dokploy apps by project."""
    if not processes and not dokploy_apps:
        click.echo("No processes found.")
        return

    # --- Local processes (pm2) ---
    if processes:
        click.echo(f"\n  \033[1;4mLOCAL PROCESSES (pm2)\033[0m")

        by_cat: dict[str, list[dict]] = {}
        for p in processes:
            cat = p.get("category", "other")
            by_cat.setdefault(cat, []).append(p)

        for cat in _CATEGORY_ORDER:
            group = by_cat.pop(cat, [])
            if not group:
                continue
            click.echo(f"\n  \033[1m{cat.upper()}\033[0m")
            click.echo(f"  {'Name':<28s} {'Status':<10s} {'PID':>7s} {'CPU':>5s} {'Memory':>10s} {'Uptime':>10s} {'↻':>4s}")
            click.echo(f"  {'─'*28} {'─'*10} {'─'*7} {'─'*5} {'─'*10} {'─'*10} {'─'*4}")
            for p in group:
                icon = _status_icon(p["status"])
                pid = str(p["pid"] or "—")
                cpu = f"{p['cpu']}%" if p["status"] == "online" else "—"
                mem = p.get("memory_human", "—") if p["status"] == "online" else "—"
                uptime = p.get("uptime", "—") if p["status"] == "online" else "—"
                restarts = str(p.get("restarts", 0))
                click.echo(f"  {icon} {p['name']:<26s} {p['status']:<10s} {pid:>7s} {cpu:>5s} {mem:>10s} {uptime:>10s} {restarts:>4s}")

        # Remaining categories
        for cat, group in by_cat.items():
            if group:
                click.echo(f"\n  \033[1m{cat.upper()}\033[0m")
                for p in group:
                    icon = _status_icon(p["status"])
                    click.echo(f"  {icon} {p['name']:<26s} {p['status']}")

    # --- Dokploy apps ---
    if dokploy_apps:
        click.echo(f"\n  \033[1;4mDEPLOYED SERVICES (Dokploy)\033[0m")

        by_project: dict[str, list[dict]] = {}
        for app in dokploy_apps:
            proj = app.get("project", "Unknown")
            by_project.setdefault(proj, []).append(app)

        for project, apps in by_project.items():
            click.echo(f"\n  \033[1m{project}\033[0m")
            for app in apps:
                icon = _dokploy_status_icon(app["status"])
                app_type = app.get("type", "application")
                type_tag = f" [{app_type}]" if app_type != "application" else ""
                app_id_short = app.get("applicationId", "")[:12]
                click.echo(f"  {icon} {app['name']:<26s} {app['status']:<10s} {app_id_short}{type_tag}")

    click.echo()


# --- CLI ---

@click.group()
def cli():
    """Process Manager — manage internal processes."""
    pass


@cli.command("list")
@click.option("--category", "-c", help="Filter by category (core, connector, service, agent, worker)")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def list_cmd(category: str | None, as_json: bool):
    """List all processes."""
    data = client.list_processes(category=category)
    if as_json:
        import json
        click.echo(json.dumps(data, indent=2))
    else:
        _print_process_table(data.get("processes", []), data.get("dokploy", []))


@cli.command()
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def info(name: str, as_json: bool):
    """Get details of a process."""
    data = client.get_process(name)
    if as_json:
        import json
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"\n  \033[1m{data['name']}\033[0m")
        click.echo(f"  Status:    {_status_icon(data['status'])} {data['status']}")
        click.echo(f"  Category:  {data.get('category', '—')}")
        click.echo(f"  PID:       {data.get('pid') or '—'}")
        click.echo(f"  CPU:       {data.get('cpu', 0)}%")
        click.echo(f"  Memory:    {data.get('memory_human', '—')}")
        click.echo(f"  Uptime:    {data.get('uptime', '—')}")
        click.echo(f"  Restarts:  {data.get('restarts', 0)}")
        click.echo(f"  Script:    {data.get('script', '—')}")
        click.echo(f"  CWD:       {data.get('cwd', '—')}")
        if data.get("port"):
            click.echo(f"  Port:      {data['port']}")
        click.echo()


@cli.command()
@click.argument("name")
def start(name: str):
    """Start a process."""
    client.start(name)
    click.echo(f"  ▶ {name} started")


@cli.command()
@click.argument("name")
def stop(name: str):
    """Stop a process."""
    client.stop(name)
    click.echo(f"  ⏹ {name} stopped")


@cli.command()
@click.argument("name")
def restart(name: str):
    """Restart a process."""
    client.restart(name)
    click.echo(f"  ⟳ {name} restarted")


@cli.command()
@click.argument("name")
@click.option("--lines", "-n", default=50, help="Number of lines to show")
def logs(name: str, lines: int):
    """Show recent logs for a process."""
    data = client.logs(name, lines=lines)
    click.echo(data.get("output", ""))


@cli.command()
@click.argument("name")
@click.option("--script", "-s", required=True, help="Path to start script")
@click.option("--cwd", help="Working directory")
@click.option("--category", "-c", default="other", help="Category (connector, service, agent, worker)")
@click.option("--port", "-p", type=int, help="Port number (for health checks)")
@click.option("--health", "-h", "health_endpoint", help="Health check path (e.g. /health)")
def add(name: str, script: str, cwd: str | None, category: str, port: int | None, health_endpoint: str | None):
    """Add and start a new process."""
    client.add(name, script, cwd=cwd, category=category, port=port, health_endpoint=health_endpoint)
    click.echo(f"  ✓ {name} added and started")


@cli.command()
@click.argument("name")
@click.confirmation_option(prompt="Remove this process?")
def remove(name: str):
    """Stop and remove a process."""
    client.remove(name)
    click.echo(f"  ✓ {name} removed")


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def health(as_json: bool):
    """Run health checks on all processes."""
    data = client.health()
    checks = data.get("checks", [])
    if as_json:
        import json
        click.echo(json.dumps(data, indent=2))
    else:
        if not checks:
            click.echo("  No health checks configured.")
            return
        click.echo()
        for c in checks:
            icon = "✓" if c["status"] == "healthy" else "✗"
            color = "\033[32m" if c["status"] == "healthy" else "\033[31m"
            click.echo(f"  {color}{icon}\033[0m {c['name']:<26s} {c['status']:<12s} {c.get('url', '')}")
        click.echo()


# --- Dokploy commands ---

@cli.group("dokploy")
def dokploy_group():
    """Manage Dokploy deployed services."""
    pass


@dokploy_group.command("start")
@click.argument("application_id")
def dokploy_start(application_id: str):
    """Start a Dokploy application."""
    client.dokploy_action(application_id, "start")
    click.echo(f"  ▶ Dokploy app {application_id[:12]} — start requested")


@dokploy_group.command("stop")
@click.argument("application_id")
def dokploy_stop(application_id: str):
    """Stop a Dokploy application."""
    client.dokploy_action(application_id, "stop")
    click.echo(f"  ⏹ Dokploy app {application_id[:12]} — stop requested")


@dokploy_group.command("redeploy")
@click.argument("application_id")
def dokploy_redeploy(application_id: str):
    """Redeploy a Dokploy application."""
    client.dokploy_action(application_id, "redeploy")
    click.echo(f"  🚀 Dokploy app {application_id[:12]} — redeploy requested")


def main():
    cli()


if __name__ == "__main__":
    main()
