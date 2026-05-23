"""Unit tests for cli.py — verify option parsing via CliRunner."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agent_invoke.cli import app

runner = CliRunner()


def _mock_run_result(text="pong", is_error=False, session_id="conv-abc"):
    return {
        "result": text,
        "session_id": session_id,
        "cost_usd": 0.001,
        "num_turns": 1,
        "is_error": is_error,
    }


# ---------------------------------------------------------------------------
# ask command
# ---------------------------------------------------------------------------

class TestAskCommand:
    def test_ask_by_name_calls_resolve_agent_and_run(self, tmp_path):
        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
        ):
            mock_resolve.return_value = (tmp_path, {"model": "sonnet", "max_turns": 10})
            mock_run.return_value = _mock_run_result()

            result = runner.invoke(app, ["ask", "context-search", "hello"])

        assert result.exit_code == 0
        assert "pong" in result.output
        mock_resolve.assert_called_once_with("context-search")

    def test_ask_with_model_override(self, tmp_path):
        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
        ):
            mock_resolve.return_value = (tmp_path, {"model": "sonnet", "max_turns": 10})
            mock_run.return_value = _mock_run_result()

            runner.invoke(app, ["ask", "--model", "opus", "context-search", "hello"])

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["model"] == "opus"

    def test_ask_with_cwd_option(self, tmp_path):
        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
        ):
            mock_resolve.return_value = (tmp_path, {"model": "sonnet", "max_turns": 10})
            mock_run.return_value = _mock_run_result()

            runner.invoke(app, ["ask", "--cwd", "/tmp/mydir", "context-search", "hello"])

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["cwd"] == "/tmp/mydir"

    def test_ask_with_agent_dir_skips_resolve(self, tmp_path):
        """When --agent-dir is set, resolve_agent should NOT be called."""
        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
        ):
            mock_run.return_value = _mock_run_result()

            result = runner.invoke(
                app,
                ["ask", "--agent-dir", str(tmp_path), "ignored-name", "hello"],
            )

        assert result.exit_code == 0
        mock_resolve.assert_not_called()
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["agent_directory"] == str(tmp_path)

    def test_ask_error_exits_with_code_1(self, tmp_path):
        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
        ):
            mock_resolve.return_value = (tmp_path, {"model": "sonnet", "max_turns": 10})
            mock_run.return_value = _mock_run_result(is_error=True)

            result = runner.invoke(app, ["ask", "context-search", "hello"])

        assert result.exit_code == 1

    def test_ask_json_output(self, tmp_path):
        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
        ):
            mock_resolve.return_value = (tmp_path, {"model": "sonnet", "max_turns": 10})
            mock_run.return_value = _mock_run_result(session_id="conv-xyz")

            result = runner.invoke(app, ["ask", "--json", "context-search", "hello"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["result"] == "pong"
        # ask command does not persist a local session, so session_id is None in output
        assert data["session_id"] is None


# ---------------------------------------------------------------------------
# chat command
# ---------------------------------------------------------------------------

class TestChatCommand:
    def test_chat_stores_session(self, tmp_path):
        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
            patch("agent_invoke.cli.sessions.create_session") as mock_create,
            patch("agent_invoke.cli.sessions.add_message") as mock_add,
            patch("agent_invoke.cli.sessions.set_backend_conversation_id") as mock_set,
        ):
            mock_resolve.return_value = (tmp_path, {"model": "sonnet", "max_turns": 10})
            mock_run.return_value = _mock_run_result(session_id="conv-123")
            mock_create.return_value = {"id": "sess-abc", "agent": "context-search"}

            result = runner.invoke(app, ["chat", "context-search", "hello"])

        assert result.exit_code == 0
        mock_create.assert_called_once()
        mock_set.assert_called_once_with("sess-abc", "conv-123")

    def test_chat_with_cwd_and_agent_dir(self, tmp_path):
        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
            patch("agent_invoke.cli.sessions.create_session") as mock_create,
            patch("agent_invoke.cli.sessions.add_message"),
            patch("agent_invoke.cli.sessions.set_backend_conversation_id"),
        ):
            mock_run.return_value = _mock_run_result()
            mock_create.return_value = {"id": "sess-xyz", "agent": "myagent"}

            runner.invoke(
                app,
                ["chat", "--cwd", "/tmp/x", "--agent-dir", str(tmp_path), "myagent", "hi"],
            )

        mock_resolve.assert_not_called()
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["cwd"] == "/tmp/x"
        assert call_kwargs["agent_directory"] == str(tmp_path)


# ---------------------------------------------------------------------------
# resume command
# ---------------------------------------------------------------------------

class TestResumeCommand:
    def test_resume_uses_backend_conversation_id(self, tmp_path):
        session_data = {
            "id": "sess-abc",
            "agent": "context-search",
            "backend_conversation_id": "conv-999",
            "status": "active",
            "messages": [],
        }

        with (
            patch("agent_invoke.cli.sessions.load") as mock_load,
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
            patch("agent_invoke.cli.sessions.add_message"),
            patch("agent_invoke.cli.sessions.set_backend_conversation_id"),
        ):
            mock_load.return_value = session_data
            mock_resolve.return_value = (tmp_path, {"model": "sonnet", "max_turns": 10})
            mock_run.return_value = _mock_run_result(session_id="conv-999")

            result = runner.invoke(app, ["resume", "sess-abc", "follow-up"])

        assert result.exit_code == 0
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["resume_session_id"] == "conv-999"
        assert call_kwargs["agent_dir"] is None

    def test_resume_fails_without_conversation_id(self):
        session_data = {
            "id": "sess-noid",
            "agent": "context-search",
            "backend_conversation_id": None,
            "claude_session_id": None,
            "status": "active",
            "messages": [],
        }

        with patch("agent_invoke.cli.sessions.load") as mock_load:
            mock_load.return_value = session_data
            result = runner.invoke(app, ["resume", "sess-noid", "hello"])

        assert result.exit_code == 1

    def test_resume_falls_back_to_claude_session_id(self, tmp_path):
        """Old sessions with claude_session_id should still work."""
        session_data = {
            "id": "sess-old",
            "agent": "context-search",
            "backend_conversation_id": None,
            "claude_session_id": "conv-legacy",
            "status": "active",
            "messages": [],
        }

        with (
            patch("agent_invoke.cli.sessions.load") as mock_load,
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
            patch("agent_invoke.cli.sessions.add_message"),
            patch("agent_invoke.cli.sessions.set_backend_conversation_id"),
        ):
            mock_load.return_value = session_data
            mock_resolve.return_value = (tmp_path, {"model": "sonnet", "max_turns": 10})
            mock_run.return_value = _mock_run_result(session_id="conv-legacy")

            result = runner.invoke(app, ["resume", "sess-old", "hello"])

        assert result.exit_code == 0
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["resume_session_id"] == "conv-legacy"


# ---------------------------------------------------------------------------
# New options are visible in --help
# ---------------------------------------------------------------------------

class TestHelpOutput:
    def test_ask_help_shows_cwd_option(self):
        result = runner.invoke(app, ["ask", "--help"])
        assert "--cwd" in result.output

    def test_ask_help_shows_agent_dir_option(self):
        result = runner.invoke(app, ["ask", "--help"])
        assert "--agent-dir" in result.output

    def test_ask_help_shows_model_option(self):
        result = runner.invoke(app, ["ask", "--help"])
        assert "--model" in result.output

    def test_ask_help_shows_prompt_file_option(self):
        result = runner.invoke(app, ["ask", "--help"])
        assert "--prompt-file" in result.output

    def test_chat_help_shows_cwd_and_agent_dir(self):
        result = runner.invoke(app, ["chat", "--help"])
        assert "--cwd" in result.output
        assert "--agent-dir" in result.output

    def test_chat_help_shows_prompt_file_option(self):
        result = runner.invoke(app, ["chat", "--help"])
        assert "--prompt-file" in result.output


# ---------------------------------------------------------------------------
# Runtime mode (--cwd without agent name)
# ---------------------------------------------------------------------------

class TestAskRuntimeMode:
    def test_runtime_mode_with_cwd_only(self, tmp_path):
        """ask --cwd /path 'prompt' should call runner.run without resolve_agent."""
        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
        ):
            mock_run.return_value = _mock_run_result()

            result = runner.invoke(
                app,
                ["ask", "--cwd", str(tmp_path), "hello from runtime"],
            )

        assert result.exit_code == 0, result.output
        mock_resolve.assert_not_called()
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["prompt"] == "hello from runtime"
        assert call_kwargs["cwd"] == str(tmp_path)
        assert call_kwargs["agent_dir"] is None

    def test_runtime_mode_with_prompt_file(self, tmp_path):
        """--prompt-file should be resolved and passed as system_prompt_paths."""
        prompt_file = tmp_path / "instructions.md"
        prompt_file.write_text("You are a helpful assistant.")

        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
        ):
            mock_run.return_value = _mock_run_result()

            result = runner.invoke(
                app,
                [
                    "ask",
                    "--cwd", str(tmp_path),
                    "--prompt-file", str(prompt_file),
                    "hello with system prompt",
                ],
            )

        assert result.exit_code == 0, result.output
        mock_resolve.assert_not_called()
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["system_prompt_paths"] == [str(prompt_file)]

    def test_pid_mode_with_prompt_file(self, tmp_path):
        """--prompt-file in PID mode should be passed as system_prompt_paths."""
        prompt_file = tmp_path / "extra.md"
        prompt_file.write_text("Additional context.")

        with (
            patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve,
            patch("agent_invoke.cli.runner.run") as mock_run,
        ):
            mock_resolve.return_value = (tmp_path, {"model": "sonnet", "max_turns": 10})
            mock_run.return_value = _mock_run_result()

            result = runner.invoke(
                app,
                [
                    "ask",
                    "--prompt-file", str(prompt_file),
                    "context-search",
                    "hello",
                ],
            )

        assert result.exit_code == 0, result.output
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["system_prompt_paths"] == [str(prompt_file)]

    def test_runtime_mode_fails_without_cwd_or_agent_dir_with_single_arg(self):
        """Single positional arg without --cwd or --agent-dir should error."""
        with patch("agent_invoke.cli.runner.resolve_agent") as mock_resolve:
            mock_resolve.side_effect = FileNotFoundError("not found")
            result = runner.invoke(app, ["ask", "just-a-prompt"])

        # Either FileNotFoundError (treated as agent lookup failure) or our explicit error
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# system_prompt_paths support in api.create_conversation
# ---------------------------------------------------------------------------

class TestApiSystemPromptPaths:
    def test_system_prompt_paths_included_in_body(self):
        from agent_invoke import api as api_mod

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "conv-sp"}
        mock_resp.text = '{"id": "conv-sp"}'
        mock_resp.raise_for_status = MagicMock()

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.post.return_value = mock_resp

            api_mod.create_conversation(
                model="claude-sonnet-4-5",
                pid="dev",
                system_prompt_paths=["/path/a.md", "/path/b.md"],
            )

        body = client_instance.post.call_args.kwargs["json"]
        assert body["system_prompt_paths"] == ["/path/a.md", "/path/b.md"]

    def test_system_prompt_paths_omitted_when_none(self):
        from agent_invoke import api as api_mod

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "conv-nsp"}
        mock_resp.text = '{"id": "conv-nsp"}'
        mock_resp.raise_for_status = MagicMock()

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.post.return_value = mock_resp

            api_mod.create_conversation(
                model="claude-sonnet-4-5",
                pid="dev",
            )

        body = client_instance.post.call_args.kwargs["json"]
        assert "system_prompt_paths" not in body
