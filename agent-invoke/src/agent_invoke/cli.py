"""CLI entry point — Typer app for agent invocation."""

import json
import os
from typing import Optional

import typer

from agent_invoke import runner, sessions

app = typer.Typer(
    name="agent-invoke",
    help="Invoke shared agents and manage conversations.",
    no_args_is_help=True,
)


def _caller() -> str:
    """Detect caller PID from cwd."""
    cwd = os.getcwd()
    if "/pids/" in cwd:
        return cwd.split("/pids/")[1].split("/")[0]
    return "unknown"


def _print_result(result: dict, session_id: str | None = None, raw_json: bool = False):
    if raw_json:
        output = {"result": result["result"], "session_id": session_id}
        if result.get("cost_usd"):
            output["cost_usd"] = result["cost_usd"]
        typer.echo(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        typer.echo(result["result"])
        if session_id:
            typer.echo(f"\n--- session: {session_id} ---")


@app.command()
def ask(
    agent: str = typer.Argument(help="Agent name (e.g. context-search)"),
    prompt: str = typer.Argument(help="Prompt to send"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    timeout: int = typer.Option(300, help="Timeout in seconds"),
    max_turns: int = typer.Option(0, help="Override max turns (0 = use agent default)"),
    output_json: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """One-shot query — no session persistence."""
    agent_dir, meta = runner.resolve_agent(agent)
    result = runner.run(
        agent_dir=agent_dir,
        prompt=prompt,
        model=model or meta.get("model", "sonnet"),
        max_turns=max_turns or meta.get("max_turns", 10),
        timeout=timeout,
    )
    _print_result(result, raw_json=output_json)
    if result["is_error"]:
        raise typer.Exit(1)


@app.command()
def chat(
    agent: str = typer.Argument(help="Agent name"),
    prompt: str = typer.Argument(help="Prompt to send"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    timeout: int = typer.Option(300, help="Timeout in seconds"),
    max_turns: int = typer.Option(0, help="Override max turns"),
    output_json: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Start a persistent conversation session."""
    agent_dir, meta = runner.resolve_agent(agent)
    session = sessions.create_session(agent, caller=_caller())
    sessions.add_message(session["id"], "caller", prompt)

    result = runner.run(
        agent_dir=agent_dir,
        prompt=prompt,
        model=model or meta.get("model", "sonnet"),
        max_turns=max_turns or meta.get("max_turns", 10),
        timeout=timeout,
    )

    if result["session_id"]:
        sessions.set_claude_session_id(session["id"], result["session_id"])

    sessions.add_message(session["id"], "agent", result["result"])

    if result["is_error"]:
        sessions.close_session(session["id"])

    _print_result(result, session_id=session["id"], raw_json=output_json)
    if result["is_error"]:
        raise typer.Exit(1)


@app.command()
def resume(
    session_id: str = typer.Argument(help="Session ID to resume"),
    prompt: str = typer.Argument(help="Follow-up prompt"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    timeout: int = typer.Option(300, help="Timeout in seconds"),
    max_turns: int = typer.Option(0, help="Override max turns"),
    output_json: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Continue an existing conversation."""
    session = sessions.load(session_id)
    agent_dir, meta = runner.resolve_agent(session["agent"])

    claude_sid = session.get("claude_session_id")
    if not claude_sid:
        typer.echo("No claude session to resume. Starting new conversation.")

    sessions.add_message(session_id, "caller", prompt)

    result = runner.run(
        agent_dir=agent_dir,
        prompt=prompt,
        model=model or meta.get("model", "sonnet"),
        max_turns=max_turns or meta.get("max_turns", 10),
        timeout=timeout,
        resume_session_id=claude_sid,
    )

    # Update claude session ID if it changed
    if result["session_id"] and result["session_id"] != claude_sid:
        sessions.set_claude_session_id(session_id, result["session_id"])

    sessions.add_message(session_id, "agent", result["result"])

    if result["is_error"]:
        sessions.close_session(session_id)

    _print_result(result, session_id=session_id, raw_json=output_json)
    if result["is_error"]:
        raise typer.Exit(1)


@app.command(name="sessions")
def list_sessions_cmd(
    agent: Optional[str] = typer.Option(None, help="Filter by agent"),
    last: int = typer.Option(20, help="Number of sessions to show"),
    output_json: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """List conversation sessions."""
    items = sessions.list_sessions(agent=agent, last=last)
    if output_json:
        typer.echo(json.dumps(items, indent=2, ensure_ascii=False))
        return
    if not items:
        typer.echo("No sessions found.")
        return
    for s in items:
        status_mark = "+" if s["status"] == "active" else "-"
        typer.echo(
            f"  [{status_mark}] {s['id']}  {s['agent']}  "
            f"{s['messages_count']} msgs  {s['started']}  (from {s['caller']})"
        )


@app.command(name="session")
def view_session_cmd(
    session_id: str = typer.Argument(help="Session ID to view"),
    output_json: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """View a session's full conversation."""
    s = sessions.load(session_id)
    if output_json:
        typer.echo(json.dumps(s, indent=2, ensure_ascii=False))
        return
    typer.echo(f"Session: {s['id']}  Agent: {s['agent']}  Status: {s['status']}")
    typer.echo(f"Started: {s['started']}  Caller: {s.get('caller', '?')}")
    typer.echo("---")
    for msg in s.get("messages", []):
        label = "CALLER" if msg["role"] == "caller" else "AGENT"
        typer.echo(f"\n[{label}] {msg['timestamp']}")
        typer.echo(msg["content"])


@app.command(name="agents")
def list_agents_cmd(
    output_json: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """List available agents."""
    agents = runner.list_agents()
    if output_json:
        typer.echo(json.dumps(agents, indent=2, ensure_ascii=False))
        return
    if not agents:
        typer.echo("No agents found in lib/ (type: agent)")
        return
    for a in agents:
        typer.echo(f"  {a['id']:20s}  {a['model']:8s}  {a['description']}")


if __name__ == "__main__":
    app()
