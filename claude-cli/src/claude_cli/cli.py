"""Claude CLI — call Claude models from shell scripts."""

import json
import os
import sys
from enum import Enum
from typing import Optional

import typer
from anthropic import Anthropic

app = typer.Typer(help="Call Claude models from shell scripts.")


@app.callback()
def callback():
    """Claude CLI — call Claude models from shell scripts."""
    pass

MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6-20250514",
    "opus": "claude-opus-4-6-20250514",
}


class ModelName(str, Enum):
    haiku = "haiku"
    sonnet = "sonnet"
    opus = "opus"


@app.command()
def ask(
    prompt: str = typer.Argument(None, help="The prompt to send to Claude. If omitted, reads from stdin."),
    model: ModelName = typer.Option(ModelName.haiku, help="Model alias: haiku, sonnet, opus"),
    system: Optional[str] = typer.Option(None, help="Optional system prompt"),
    json_output: bool = typer.Option(False, "--json", help="Request JSON response and validate it"),
    max_tokens: int = typer.Option(4096, help="Max tokens in response"),
):
    """Send a prompt to Claude and print the response to stdout."""
    if prompt is None:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        if not prompt:
            typer.echo("Error: No prompt provided (pass as argument or pipe via stdin)", err=True)
            raise typer.Exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        typer.echo("Error: ANTHROPIC_API_KEY environment variable not set", err=True)
        raise typer.Exit(1)

    model_id = MODEL_MAP[model.value]

    # Build user message
    user_content = prompt
    if json_output:
        user_content += "\n\nRespond ONLY with valid JSON, no markdown fences, no explanation."

    # Build messages
    messages = [{"role": "user", "content": user_content}]

    # Build kwargs
    kwargs = {
        "model": model_id,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(**kwargs)
    except Exception as e:
        typer.echo(f"Error calling Anthropic API: {e}", err=True)
        raise typer.Exit(1)

    # Extract text
    text = response.content[0].text.strip()

    # Validate JSON if requested
    if json_output:
        try:
            json.loads(text)
        except json.JSONDecodeError:
            typer.echo(f"Error: Response is not valid JSON: {text}", err=True)
            raise typer.Exit(1)

    # Print to stdout for piping
    print(text)


if __name__ == "__main__":
    app()
