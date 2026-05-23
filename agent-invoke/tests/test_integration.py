"""Integration tests — require a live AI Manager backend.

These tests are skipped automatically if AI Manager is not reachable.
Run with: pytest tests/test_integration.py -v -s
"""

import os
import pytest
import httpx

AI_MANAGER_URL = os.environ.get("AI_MANAGER_URL", "http://127.0.0.1:4810")
INTERNAL_KEY = os.environ.get("BACKEND_INTERNAL_KEY", "proxy-internal-key")


def _backend_available() -> bool:
    try:
        resp = httpx.get(f"{AI_MANAGER_URL}/health", timeout=5.0)
        return resp.status_code == 200
    except Exception:
        return False


skip_if_no_backend = pytest.mark.skipif(
    not _backend_available(),
    reason=f"AI Manager not reachable at {AI_MANAGER_URL}",
)


@skip_if_no_backend
class TestCreateConversationE2E:
    def test_create_conversation_returns_id(self):
        from agent_invoke import api as api_mod

        conv = api_mod.create_conversation(
            model="claude-sonnet-4-5",
            pid="dev",
            cwd="/tmp",
        )
        assert "id" in conv
        assert isinstance(conv["id"], (str, int))

    def test_create_and_send_message(self):
        """Create a conversation and send a message to trigger the agent."""
        from agent_invoke import api as api_mod

        conv = api_mod.create_conversation(
            model="claude-sonnet-4-5",
            pid="dev",
            cwd="/tmp",
        )
        conv_id = conv["id"]

        # Sending a message should succeed (HTTP 200)
        result = api_mod.send_message(conv_id, "ping — respond with just the word: pong")
        assert result is not None

    def test_stream_events_receives_completed(self):
        """Create a conversation, send a message, stream events until completed."""
        from agent_invoke import api as api_mod

        conv = api_mod.create_conversation(
            model="claude-sonnet-4-5",
            pid="dev",
            cwd="/tmp",
        )
        conv_id = conv["id"]

        api_mod.send_message(conv_id, "Say exactly: pong")

        received_types = []
        for event in api_mod.stream_events(conv_id, timeout=120):
            received_types.append(event.get("type"))
            if event.get("type") in ("completed", "stopped", "error"):
                break

        assert any(t in received_types for t in ("completed", "stopped", "error")), (
            f"Expected terminal event, got: {received_types}"
        )

    def test_runner_run_with_cwd(self):
        """Full runner.run() with cwd — verifies text is extracted from events."""
        from agent_invoke import runner

        result = runner.run(
            agent_dir=None,
            prompt="Respond with exactly: pong",
            model="sonnet",
            timeout=120,
            cwd="/tmp",
            pid="dev",
        )
        # Should not be an error and should have some result text
        assert not result["is_error"], f"Got error: {result['result']}"
        assert result["result"], "Expected non-empty result"
        assert result["session_id"] is not None
