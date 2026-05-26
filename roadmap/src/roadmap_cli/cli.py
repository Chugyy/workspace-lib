"""Roadmap CLI — manage AI Manager roadmaps from the command line."""

import json
import sys
from typing import Optional

import httpx
import typer

from roadmap_cli.client import RoadmapClient

app = typer.Typer(help="Manage AI Manager roadmaps, tasks, and dependencies.", no_args_is_help=True)
task_app = typer.Typer(help="Task operations within a roadmap.", no_args_is_help=True)
dep_app = typer.Typer(help="Dependency operations within a roadmap.", no_args_is_help=True)
block_app = typer.Typer(help="Block (notes/annotations) operations.", no_args_is_help=True)

exec_app = typer.Typer(help="Execution operations within a roadmap.", no_args_is_help=True)

app.add_typer(task_app, name="task")
app.add_typer(dep_app, name="dep")
app.add_typer(block_app, name="block")
app.add_typer(exec_app, name="exec")

_profile_name: Optional[str] = None
_json_output: bool = False


@app.callback()
def main(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name (stable, dev, etc.)"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Roadmap CLI for AI Manager."""
    global _profile_name, _json_output
    _profile_name = profile
    _json_output = json_out


def _client() -> RoadmapClient:
    return RoadmapClient(profile=_profile_name)


def _out(data, fmt_func=None):
    """Output data as JSON or formatted text."""
    if _json_output:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
    elif fmt_func:
        fmt_func(data)
    else:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))


def _short_id(full_id: str) -> str:
    """Show first 8 chars of UUID for readability."""
    return full_id[:8] if full_id and len(full_id) > 8 else (full_id or "")


def _status_icon(status: str) -> str:
    icons = {
        "active": "+", "running": ">", "completed": "x",
        "failed": "!", "cancelled": "-", "pending": ".",
        "checked": "x", "stopped": "#", "paused": "~",
        "skipped": "/",
    }
    return icons.get(status, "?")


# ══════════════════════════════════════════════════════════════════
# ROADMAP commands (top-level)
# ══════════════════════════════════════════════════════════════════

@app.command("list")
def list_roadmaps(
    pid: Optional[str] = typer.Option(None, "--pid", help="Filter by PID"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    mode: Optional[str] = typer.Option(None, "--mode", help="Filter by mode (autonomous, callable)"),
):
    """List all roadmaps."""
    data = _client().list_roadmaps(pid=pid, tag=tag, status=status, mode=mode)

    def fmt(items):
        if not items:
            typer.echo("No roadmaps found.")
            return
        typer.echo(f"{'ID':10s} {'STATUS':10s} {'MODE':12s} {'PID':15s} NAME")
        typer.echo("-" * 70)
        for r in items:
            sid = _short_id(r["id"])
            st = r.get("status", "?")
            md = r.get("mode", "?")
            pid_val = r.get("pid") or "-"
            typer.echo(f"{sid:10s} {st:10s} {md:12s} {pid_val:15s} {r['name']}")

    _out(data, fmt)


@app.command("show")
def show_roadmap(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID (full or prefix)"),
):
    """Show roadmap details."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().get_roadmap(rid)

    def fmt(r):
        typer.echo(f"Roadmap: {r['name']}")
        typer.echo(f"ID:      {r['id']}")
        typer.echo(f"Status:  {r.get('status', '?')}")
        if r.get("pid"):
            typer.echo(f"PID:     {r['pid']}")
        if r.get("description"):
            typer.echo(f"Desc:    {r['description']}")
        if r.get("mode"):
            typer.echo(f"Mode:    {r['mode']}")
        if r.get("concurrency"):
            typer.echo(f"Concur:  {r['concurrency']}")
        if r.get("tags"):
            typer.echo(f"Tags:    {', '.join(r['tags'])}")
        if r.get("inputs_schema"):
            typer.echo(f"Inputs:  {json.dumps(r['inputs_schema'])}")
        typer.echo(f"Created: {r.get('created_at', '?')}")
        typer.echo(f"Updated: {r.get('updated_at', '?')}")

    _out(data, fmt)


@app.command("create")
def create_roadmap(
    name: str = typer.Argument(..., help="Roadmap name"),
    pid: Optional[str] = typer.Option(None, "--pid", help="Associate with a PID"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Description"),
    mode: str = typer.Option("autonomous", "--mode", help="Mode: autonomous or callable"),
    concurrency: str = typer.Option("parallel", "--concurrency", help="Concurrency: parallel or single"),
    tag: Optional[list[str]] = typer.Option(None, "--tag", help="Tags (repeatable)"),
    inputs_schema: Optional[str] = typer.Option(None, "--inputs-schema", help="Inputs schema JSON for callable mode"),
):
    """Create a new roadmap."""
    schema = json.loads(inputs_schema) if inputs_schema else None
    data = _client().create_roadmap(
        name, pid=pid, description=description,
        mode=mode, concurrency=concurrency, tags=tag, inputs_schema=schema,
    )

    def fmt(r):
        typer.echo(f"Created roadmap: {r['name']} ({_short_id(r['id'])})")

    _out(data, fmt)


@app.command("update")
def update_roadmap(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New name"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="New description"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status (active, stopped, paused)"),
    mode: Optional[str] = typer.Option(None, "--mode", help="Mode: autonomous or callable"),
    concurrency: Optional[str] = typer.Option(None, "--concurrency", help="Concurrency: parallel or single"),
    tag: Optional[list[str]] = typer.Option(None, "--tag", help="Tags (replaces existing)"),
    inputs_schema: Optional[str] = typer.Option(None, "--inputs-schema", help="Inputs schema JSON"),
):
    """Update a roadmap."""
    rid = _resolve_roadmap_id(roadmap_id)
    fields = {}
    if name is not None:
        fields["name"] = name
    if description is not None:
        fields["description"] = description
    if status is not None:
        fields["status"] = status
    if mode is not None:
        fields["mode"] = mode
    if concurrency is not None:
        fields["concurrency"] = concurrency
    if tag is not None:
        fields["tags"] = tag
    if inputs_schema is not None:
        fields["inputs_schema"] = json.loads(inputs_schema)
    data = _client().update_roadmap(rid, **fields)

    def fmt(r):
        typer.echo(f"Updated roadmap: {r['name']} ({_short_id(r['id'])})")

    _out(data, fmt)


@app.command("delete")
def delete_roadmap(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a roadmap and all its tasks."""
    rid = _resolve_roadmap_id(roadmap_id)
    if not force:
        confirm = typer.confirm(f"Delete roadmap {_short_id(rid)}? This removes all tasks.")
        if not confirm:
            raise typer.Abort()
    _client().delete_roadmap(rid)
    typer.echo(f"Deleted roadmap {_short_id(rid)}")


@app.command("duplicate")
def duplicate_roadmap(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID to duplicate"),
):
    """Deep copy a roadmap with all tasks and dependencies."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().duplicate_roadmap(rid)

    def fmt(r):
        typer.echo(f"Duplicated to: {r['name']} ({_short_id(r['id'])})")

    _out(data, fmt)


@app.command("state")
def roadmap_state(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    expand_subs: bool = typer.Option(False, "--expand-subs", help="Expand sub-roadmap tasks"),
):
    """Show roadmap with enriched task states (runtime status from aggregator)."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().get_state(rid, expand_subs=expand_subs)

    def fmt(state):
        r = state.get("roadmap", state)
        typer.echo(f"Roadmap: {r.get('name', '?')} [{r.get('status', '?')}]")
        typer.echo("")
        tasks = state.get("tasks", [])
        if not tasks:
            typer.echo("  No tasks.")
            return
        typer.echo(f"  {'':2s} {'ID':10s} {'STATUS':12s} {'POS':4s} NAME")
        typer.echo(f"  {'-' * 50}")
        for t in tasks:
            icon = _status_icon(t.get("status", t.get("state", "pending")))
            sid = _short_id(t["id"])
            status = t.get("status", t.get("state", "pending"))
            pos = str(t.get("position", 0))
            indent = "  " if t.get("parent_id") else ""
            typer.echo(f"  [{icon}] {sid:10s} {status:12s} {pos:4s} {indent}{t['name']}")

    _out(data, fmt)


@app.command("graph")
def roadmap_graph(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    expand_subs: bool = typer.Option(False, "--expand-subs", help="Expand sub-roadmap tasks"),
):
    """Show topological dependency graph with levels."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().get_graph(rid, expand_subs=expand_subs)

    def fmt(g):
        levels = g.get("levels", [])
        if not levels:
            typer.echo("No dependency graph (no tasks or dependencies).")
            return
        for i, level in enumerate(levels):
            typer.echo(f"Level {i}:")
            for t in level:
                name = t.get("name", t.get("id", "?"))
                sid = _short_id(t.get("id", ""))
                typer.echo(f"  {sid}  {name}")
            typer.echo("")

    _out(data, fmt)


@app.command("start")
def start_roadmap(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
):
    """Start a roadmap (activates and launches level-0 tasks)."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().start_roadmap(rid)
    typer.echo(f"Started roadmap {_short_id(rid)}")
    if _json_output:
        typer.echo(json.dumps(data, indent=2))


@app.command("stop")
def stop_roadmap(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    hard: bool = typer.Option(False, "--hard", help="Cancel running tasks too"),
):
    """Stop a roadmap."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().stop_roadmap(rid, hard=hard)
    typer.echo(f"Stopped roadmap {_short_id(rid)}" + (" (hard)" if hard else ""))
    if _json_output:
        typer.echo(json.dumps(data, indent=2))


@app.command("pause")
def pause_roadmap(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
):
    """Pause a roadmap (no new tasks trigger, running ones continue)."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().pause_roadmap(rid)
    typer.echo(f"Paused roadmap {_short_id(rid)}")
    if _json_output:
        typer.echo(json.dumps(data, indent=2))


@app.command("execute")
def execute_roadmap(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    inputs: Optional[str] = typer.Option(None, "--inputs", "-i", help="JSON inputs for callable roadmaps"),
):
    """Create and start a new execution (supports callable roadmap inputs)."""
    rid = _resolve_roadmap_id(roadmap_id)
    parsed_inputs = json.loads(inputs) if inputs else None
    data = _client().execute_roadmap(rid, inputs=parsed_inputs)

    def fmt(r):
        exec_data = r.get("execution", {})
        typer.echo(f"Execution started: {_short_id(exec_data.get('id', ''))}")
        started = r.get("started_tasks", [])
        if started:
            typer.echo(f"  Launched {len(started)} task(s)")

    _out(data, fmt)


# ══════════════════════════════════════════════════════════════════
# EXEC sub-commands
# ══════════════════════════════════════════════════════════════════

@exec_app.command("list")
def list_executions(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
):
    """List all executions for a roadmap."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().get_executions(rid)

    def fmt(execs):
        if not execs:
            typer.echo("No executions.")
            return
        typer.echo(f"{'ID':10s} {'STATUS':12s} {'CREATED':20s} PARENT")
        typer.echo("-" * 60)
        for e in execs:
            sid = _short_id(e["id"])
            status = e.get("status", "?")
            created = (e.get("created_at") or "?")[:19]
            parent = _short_id(e.get("parent_task_id") or "") or "-"
            typer.echo(f"{sid:10s} {status:12s} {created:20s} {parent}")

    _out(data, fmt)


@exec_app.command("state")
def execution_state(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    execution_id: str = typer.Argument(..., help="Execution ID"),
    depth: int = typer.Option(1, "--depth", help="Sub-roadmap traversal depth (0-5)"),
):
    """Show execution state with task progress."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().get_execution_state(rid, execution_id, depth=depth)

    def fmt(s):
        progress = s.get("progress", {})
        typer.echo(f"Execution: {_short_id(execution_id)}")
        typer.echo(f"Progress:  {progress.get('completed', 0)}/{progress.get('total', 0)} ({progress.get('percent', 0)}%)")
        typer.echo("")
        tasks = s.get("tasks", [])
        if tasks:
            typer.echo(f"  {'ID':10s} {'STATE':12s} NAME")
            typer.echo(f"  {'-' * 40}")
            for t in tasks:
                icon = _status_icon(t.get("state", "pending"))
                sid = _short_id(t["task_id"])
                typer.echo(f"  [{icon}] {sid:10s} {t.get('state', 'pending'):12s} {t['name']}")

    _out(data, fmt)


@exec_app.command("stop")
def stop_execution(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    execution_id: str = typer.Argument(..., help="Execution ID"),
    hard: bool = typer.Option(False, "--hard", help="Cancel running tasks"),
):
    """Stop a specific execution."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().stop_execution(rid, execution_id, hard=hard)
    typer.echo(f"Stopped execution {_short_id(execution_id)}" + (" (hard)" if hard else ""))
    if _json_output:
        typer.echo(json.dumps(data, indent=2))


# ══════════════════════════════════════════════════════════════════
# TASK sub-commands
# ══════════════════════════════════════════════════════════════════

@task_app.command("list")
def list_tasks(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
):
    """List all tasks in a roadmap."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().list_tasks(rid)

    def fmt(tasks):
        if not tasks:
            typer.echo("No tasks.")
            return
        typer.echo(f"{'ID':10s} {'POS':4s} {'PARENT':10s} NAME")
        typer.echo("-" * 50)
        for t in tasks:
            sid = _short_id(t["id"])
            pos = str(t.get("position", 0))
            parent = _short_id(t.get("parent_id") or "") or "-"
            typer.echo(f"{sid:10s} {pos:4s} {parent:10s} {t['name']}")

    _out(data, fmt)


@task_app.command("show")
def show_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Argument(..., help="Task ID"),
):
    """Show task details with runtime state."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    data = _client().get_task_state(rid, tid)

    def fmt(t):
        typer.echo(f"Task:        {t.get('name', '?')}")
        typer.echo(f"ID:          {t.get('id', '?')}")
        typer.echo(f"Status:      {t.get('status', t.get('state', '?'))}")
        if t.get("description"):
            typer.echo(f"Description: {t['description']}")
        if t.get("parent_id"):
            typer.echo(f"Parent:      {t['parent_id']}")
        if t.get("script_path"):
            typer.echo(f"Script:      {t['script_path']}")
        if t.get("trigger_event"):
            typer.echo(f"Trigger:     {t['trigger_event']}")
        if t.get("cron_expression"):
            typer.echo(f"Cron:        {t['cron_expression']}")
        if t.get("sub_roadmap_id"):
            typer.echo(f"Sub-RM:      {t['sub_roadmap_id']}")
        if t.get("run_config"):
            typer.echo(f"Run config:  {json.dumps(t['run_config']) if isinstance(t['run_config'], dict) else t['run_config']}")
        typer.echo(f"Position:    {t.get('position', 0)}")

    _out(data, fmt)


@task_app.command("add")
def add_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    name: str = typer.Argument(..., help="Task name"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Description"),
    parent: Optional[str] = typer.Option(None, "--parent", help="Parent task ID"),
    position: Optional[int] = typer.Option(None, "--pos", help="Position (ordering)"),
    script: Optional[str] = typer.Option(None, "--script", help="Script path"),
    trigger: Optional[str] = typer.Option(None, "--trigger", help="Trigger event type"),
    cron: Optional[str] = typer.Option(None, "--cron", help="Cron expression"),
    sub_roadmap: Optional[str] = typer.Option(None, "--sub-roadmap", help="Sub-roadmap ID for delegation"),
):
    """Add a task to a roadmap."""
    rid = _resolve_roadmap_id(roadmap_id)
    pid = None
    if parent:
        pid = _resolve_task_id(rid, parent)
    data = _client().create_task(
        rid, name,
        description=description,
        parent_id=pid,
        position=position,
        script_path=script,
        trigger_event=trigger,
        cron_expression=cron,
        sub_roadmap_id=sub_roadmap,
    )

    def fmt(t):
        typer.echo(f"Added task: {t['name']} ({_short_id(t['id'])})")

    _out(data, fmt)


@task_app.command("update")
def update_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Argument(..., help="Task ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New name"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="New description"),
    script: Optional[str] = typer.Option(None, "--script", help="New script path"),
    position: Optional[int] = typer.Option(None, "--pos", help="New position"),
    trigger: Optional[str] = typer.Option(None, "--trigger", help="Trigger event type"),
    cron: Optional[str] = typer.Option(None, "--cron", help="Cron expression"),
):
    """Update a task."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    data = _client().update_task(
        rid, tid,
        name=name, description=description, script_path=script,
        position=position, trigger_event=trigger, cron_expression=cron,
    )

    def fmt(t):
        typer.echo(f"Updated task: {t['name']} ({_short_id(t['id'])})")

    _out(data, fmt)


@task_app.command("delete")
def delete_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Argument(..., help="Task ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a task."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    if not force:
        confirm = typer.confirm(f"Delete task {_short_id(tid)}?")
        if not confirm:
            raise typer.Abort()
    _client().delete_task(rid, tid)
    typer.echo(f"Deleted task {_short_id(tid)}")


@task_app.command("check")
def check_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Argument(..., help="Task ID"),
    execution_id: Optional[str] = typer.Option(None, "--execution-id", "-e", help="Scope to execution"),
):
    """Mark a task as manually completed."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    _client().check_task(rid, tid, execution_id=execution_id)
    typer.echo(f"Checked task {_short_id(tid)}")


@task_app.command("uncheck")
def uncheck_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Argument(..., help="Task ID"),
    execution_id: Optional[str] = typer.Option(None, "--execution-id", "-e", help="Scope to execution"),
):
    """Remove manual completion mark from a task."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    _client().uncheck_task(rid, tid, execution_id=execution_id)
    typer.echo(f"Unchecked task {_short_id(tid)}")


@task_app.command("start")
def start_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Argument(..., help="Task ID"),
    execution_id: Optional[str] = typer.Option(None, "--execution-id", "-e", help="Scope to execution"),
):
    """Start task execution."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    _client().start_task(rid, tid, execution_id=execution_id)
    typer.echo(f"Started task {_short_id(tid)}")


@task_app.command("cancel")
def cancel_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Argument(..., help="Task ID"),
    execution_id: Optional[str] = typer.Option(None, "--execution-id", "-e", help="Scope to execution"),
):
    """Cancel a running task."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    _client().cancel_task(rid, tid, execution_id=execution_id)
    typer.echo(f"Cancelled task {_short_id(tid)}")


@task_app.command("retry")
def retry_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Argument(..., help="Task ID"),
    execution_id: Optional[str] = typer.Option(None, "--execution-id", "-e", help="Scope to execution"),
):
    """Retry a failed task."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    _client().retry_task(rid, tid, execution_id=execution_id)
    typer.echo(f"Retried task {_short_id(tid)}")


@task_app.command("reset")
def reset_task(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Argument(..., help="Task ID"),
    execution_id: Optional[str] = typer.Option(None, "--execution-id", "-e", help="Scope to execution"),
):
    """Reset a task to pending state."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    _client().reset_task(rid, tid, execution_id=execution_id)
    typer.echo(f"Reset task {_short_id(tid)}")


# ══════════════════════════════════════════════════════════════════
# DEPENDENCY sub-commands
# ══════════════════════════════════════════════════════════════════

@dep_app.command("list")
def list_deps(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
):
    """List all task dependencies."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().list_dependencies(rid)

    def fmt(deps):
        if not deps:
            typer.echo("No dependencies.")
            return
        typer.echo(f"{'DEP_ID':10s} {'TASK':10s} {'DEPENDS_ON':10s} TYPE")
        typer.echo("-" * 50)
        for d in deps:
            typer.echo(
                f"{_short_id(d['id']):10s} "
                f"{_short_id(d['task_id']):10s} "
                f"{_short_id(d['depends_on']):10s} "
                f"{d.get('dep_type', 'finish_to_start')}"
            )

    _out(data, fmt)


@dep_app.command("add")
def add_dep(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: str = typer.Option(..., "--task", "-t", help="Task that depends"),
    depends_on: str = typer.Option(..., "--on", help="Task that must finish first"),
    dep_type: str = typer.Option("finish_to_start", "--type", help="Dependency type"),
):
    """Add a task dependency (with cycle detection)."""
    rid = _resolve_roadmap_id(roadmap_id)
    tid = _resolve_task_id(rid, task_id)
    did = _resolve_task_id(rid, depends_on)
    data = _client().create_dependency(rid, tid, did, dep_type)

    def fmt(d):
        typer.echo(f"Added dependency: {_short_id(tid)} depends on {_short_id(did)}")

    _out(data, fmt)


@dep_app.command("remove")
def remove_dep(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    dep_id: str = typer.Argument(..., help="Dependency ID"),
):
    """Remove a dependency."""
    rid = _resolve_roadmap_id(roadmap_id)
    _client().delete_dependency(rid, dep_id)
    typer.echo(f"Removed dependency {_short_id(dep_id)}")


# ══════════════════════════════════════════════════════════════════
# BLOCK sub-commands
# ══════════════════════════════════════════════════════════════════

@block_app.command("list")
def list_blocks(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    task_id: Optional[str] = typer.Option(None, "--task", "-t", help="Filter by task"),
):
    """List blocks (notes/annotations) in a roadmap."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().list_blocks(rid, task_id=task_id)

    def fmt(blocks):
        if not blocks:
            typer.echo("No blocks.")
            return
        for b in blocks:
            sid = _short_id(b["id"])
            src = b.get("source") or "-"
            preview = (b.get("content") or "")[:60].replace("\n", " ")
            task = _short_id(b.get("task_id") or "") or "-"
            typer.echo(f"[{sid}] task={task} src={src}  {preview}")

    _out(data, fmt)


@block_app.command("add")
def add_block(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    content: str = typer.Argument(..., help="Block content (markdown)"),
    task_id: Optional[str] = typer.Option(None, "--task", "-t", help="Associate with task"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Source (user, agent, etc.)"),
):
    """Add a block (note/annotation) to a roadmap."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().create_block(rid, content, task_id=task_id, source=source)

    def fmt(b):
        typer.echo(f"Added block {_short_id(b['id'])}")

    _out(data, fmt)


@block_app.command("update")
def update_block(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    block_id: str = typer.Argument(..., help="Block ID"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="New content"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status (active/archived)"),
    source: Optional[str] = typer.Option(None, "--source", help="New source"),
    task_id: Optional[str] = typer.Option(None, "--task", "-t", help="Re-associate with task"),
):
    """Update a block."""
    rid = _resolve_roadmap_id(roadmap_id)
    data = _client().update_block(rid, block_id, content=content, status=status,
                                  source=source, task_id=task_id)

    def fmt(b):
        typer.echo(f"Updated block {_short_id(b.get('id', block_id))}")

    _out(data, fmt)


@block_app.command("delete")
def delete_block(
    roadmap_id: str = typer.Argument(..., help="Roadmap ID"),
    block_id: str = typer.Argument(..., help="Block ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a block."""
    rid = _resolve_roadmap_id(roadmap_id)
    if not force:
        confirm = typer.confirm(f"Delete block {_short_id(block_id)}?")
        if not confirm:
            raise typer.Abort()
    _client().delete_block(rid, block_id)
    typer.echo(f"Deleted block {_short_id(block_id)}")


# ══════════════════════════════════════════════════════════════════
# ID resolution helpers
# ══════════════════════════════════════════════════════════════════

def _resolve_roadmap_id(prefix: str) -> str:
    """Resolve a roadmap ID from prefix or full UUID."""
    if len(prefix) >= 32:
        return prefix
    # Search by prefix
    try:
        roadmaps = _client().list_roadmaps()
        matches = [r for r in roadmaps if r["id"].startswith(prefix)]
        if len(matches) == 1:
            return matches[0]["id"]
        if len(matches) == 0:
            # Try matching by name (case-insensitive)
            matches = [r for r in roadmaps if prefix.lower() in r["name"].lower()]
            if len(matches) == 1:
                return matches[0]["id"]
            typer.echo(f"No roadmap found matching '{prefix}'", err=True)
            raise typer.Exit(1)
        typer.echo(f"Ambiguous prefix '{prefix}', matches {len(matches)} roadmaps:", err=True)
        for r in matches:
            typer.echo(f"  {_short_id(r['id'])}  {r['name']}", err=True)
        raise typer.Exit(1)
    except httpx.HTTPStatusError:
        return prefix


def _resolve_task_id(roadmap_id: str, prefix: str) -> str:
    """Resolve a task ID from prefix or full UUID."""
    if len(prefix) >= 32:
        return prefix
    try:
        tasks = _client().list_tasks(roadmap_id)
        matches = [t for t in tasks if t["id"].startswith(prefix)]
        if len(matches) == 1:
            return matches[0]["id"]
        if len(matches) == 0:
            # Try matching by name
            matches = [t for t in tasks if prefix.lower() in t["name"].lower()]
            if len(matches) == 1:
                return matches[0]["id"]
            typer.echo(f"No task found matching '{prefix}'", err=True)
            raise typer.Exit(1)
        typer.echo(f"Ambiguous prefix '{prefix}', matches {len(matches)} tasks:", err=True)
        for t in matches:
            typer.echo(f"  {_short_id(t['id'])}  {t['name']}", err=True)
        raise typer.Exit(1)
    except httpx.HTTPStatusError:
        return prefix


if __name__ == "__main__":
    app()
