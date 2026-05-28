"""CLI entry point — Typer app for agent invocation."""

import json
import os
from pathlib import Path
from typing import List, Optional

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
    agent_or_prompt: str = typer.Argument(help="Agent name (PID mode) or prompt (runtime mode with --cwd)"),
    prompt: Optional[str] = typer.Argument(None, help="Prompt to send (when agent name is first arg)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model (e.g. sonnet, opus, or full ID)"),
    timeout: int = typer.Option(300, help="Timeout in seconds"),
    max_turns: int = typer.Option(0, help="Override max turns (0 = use agent default, kept for compat)"),
    output_json: bool = typer.Option(False, "--json", help="Raw JSON output"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory (runtime mode or tool execution)"),
    agent_dir: Optional[str] = typer.Option(None, "--agent-dir", help="Path to agent directory (skips registry lookup)"),
    prompt_file: Optional[List[str]] = typer.Option(None, "--prompt-file", "-f", help="File(s) to use as system prompt"),
    sdk: Optional[str] = typer.Option(None, "--sdk", help="SDK for model routing (e.g. opencode-sdk, claude-sdk)"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider for model routing (e.g. anthropic, openai)"),
):
    """One-shot query — no session persistence.

    PID mode:     ask <agent> <prompt> [--model sonnet] [--cwd /path]
    Runtime mode: ask --cwd /path <prompt> [--agent-dir /path/.agent] [--prompt-file /path/file.md]
    Direct path:  ask --agent-dir /path <ignored> <prompt>
    """
    # Determine mode and extract actual agent name / prompt
    if agent_dir:
        # --agent-dir mode: skip registry, first positional is ignored as agent name,
        # second positional is the prompt. If only one positional given, it is the prompt.
        if prompt is not None:
            actual_prompt = prompt
        else:
            actual_prompt = agent_or_prompt
        agent_path = Path(agent_dir)
        resolved_model = model or "sonnet"
        system_paths = [str(Path(p).resolve()) for p in prompt_file] if prompt_file else None
        result = runner.run(
            agent_dir=agent_path,
            prompt=actual_prompt,
            model=resolved_model,
            timeout=timeout,
            cwd=cwd,
            agent_directory=agent_dir,
            system_prompt_paths=system_paths,
            sdk=sdk,
            provider=provider,
        )
    elif prompt is not None:
        # Two positional args: <agent> <prompt> → PID mode (rétrocompat)
        agent_name = agent_or_prompt
        actual_prompt = prompt
        agent_path, meta = runner.resolve_agent(agent_name)
        system_paths = [str(Path(p).resolve()) for p in prompt_file] if prompt_file else None
        result = runner.run(
            agent_dir=agent_path,
            prompt=actual_prompt,
            model=model or meta.get("model", "sonnet"),
            max_turns=max_turns or meta.get("max_turns", 10),
            timeout=timeout,
            cwd=cwd,
            pid=agent_name,
            system_prompt_paths=system_paths,
            sdk=sdk,
            provider=provider,
        )
    elif cwd:
        # Runtime mode: --cwd given, single positional is the prompt
        actual_prompt = agent_or_prompt
        system_paths = [str(Path(p).resolve()) for p in prompt_file] if prompt_file else None
        result = runner.run(
            agent_dir=None,
            prompt=actual_prompt,
            model=model or "sonnet",
            timeout=timeout,
            cwd=cwd,
            agent_directory=agent_dir,
            system_prompt_paths=system_paths,
            sdk=sdk,
            provider=provider,
        )
    else:
        typer.echo(
            "Error: provide either '<agent> <prompt>' (PID mode) or "
            "'--cwd <path> <prompt>' (runtime mode) or '--agent-dir <path> <prompt>'.",
            err=True,
        )
        raise typer.Exit(1)

    _print_result(result, raw_json=output_json)
    if result["is_error"]:
        raise typer.Exit(1)


@app.command()
def chat(
    agent: str = typer.Argument(help="Agent name"),
    prompt: str = typer.Argument(help="Prompt to send"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model (e.g. sonnet, opus, or full ID)"),
    timeout: int = typer.Option(300, help="Timeout in seconds"),
    max_turns: int = typer.Option(0, help="Override max turns (kept for compat)"),
    output_json: bool = typer.Option(False, "--json", help="Raw JSON output"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory for tool execution"),
    agent_dir: Optional[str] = typer.Option(None, "--agent-dir", help="Path to agent directory (alternative to <agent> name)"),
    prompt_file: Optional[List[str]] = typer.Option(None, "--prompt-file", "-f", help="File(s) to use as system prompt"),
    sdk: Optional[str] = typer.Option(None, "--sdk", help="SDK for model routing (e.g. opencode-sdk, claude-sdk)"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider for model routing (e.g. anthropic, openai)"),
):
    """Start a persistent conversation session."""
    system_paths = [str(Path(p).resolve()) for p in prompt_file] if prompt_file else None

    if agent_dir:
        agent_path = Path(agent_dir)
        meta: dict = {}
        resolved_model = model or "sonnet"
    else:
        agent_path, meta = runner.resolve_agent(agent)
        resolved_model = model or meta.get("model", "sonnet")

    session = sessions.create_session(agent, caller=_caller())
    sessions.add_message(session["id"], "caller", prompt)

    result = runner.run(
        agent_dir=agent_path,
        prompt=prompt,
        model=resolved_model,
        max_turns=max_turns or meta.get("max_turns", 10),
        timeout=timeout,
        cwd=cwd,
        agent_directory=agent_dir,
        pid=agent if not agent_dir else None,
        system_prompt_paths=system_paths,
        sdk=sdk,
        provider=provider,
    )

    if result["session_id"]:
        sessions.set_backend_conversation_id(session["id"], result["session_id"])

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
    max_turns: int = typer.Option(0, help="Override max turns (kept for compat)"),
    output_json: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Continue an existing conversation by sending a follow-up message to the backend."""
    session = sessions.load(session_id)
    agent_name = session["agent"]

    # Resolve backend conversation ID (new field), fall back to legacy claude_session_id
    backend_conv_id = session.get("backend_conversation_id") or session.get("claude_session_id")

    if not backend_conv_id:
        typer.echo(
            "No backend conversation to resume. "
            "Start a new conversation with `agent-invoke chat`.",
            err=True,
        )
        raise typer.Exit(1)

    # Resolve agent for model defaults
    try:
        _, meta = runner.resolve_agent(agent_name)
        resolved_model = model or meta.get("model", "sonnet")
    except FileNotFoundError:
        resolved_model = model or "sonnet"
        meta = {}

    sessions.add_message(session_id, "caller", prompt)

    result = runner.run(
        agent_dir=None,
        prompt=prompt,
        model=resolved_model,
        max_turns=max_turns or meta.get("max_turns", 10),
        timeout=timeout,
        resume_session_id=backend_conv_id,
    )

    # Update backend conversation ID if it changed (shouldn't, but keep defensive)
    if result["session_id"] and result["session_id"] != backend_conv_id:
        sessions.set_backend_conversation_id(session_id, result["session_id"])

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
