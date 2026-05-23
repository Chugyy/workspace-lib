"""Unit tests for api.py — mock httpx to verify request shape."""

import json
from unittest.mock import MagicMock, patch, call
import pytest

import agent_invoke.api as api_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(status_code: int, body: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    resp.text = json.dumps(body)
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        from httpx import HTTPStatusError, Request, Response
        resp.raise_for_status.side_effect = HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


# ---------------------------------------------------------------------------
# create_conversation
# ---------------------------------------------------------------------------

class TestCreateConversation:
    def test_sends_correct_body_with_pid(self):
        mock_resp = _mock_response(200, {"id": "conv-123"})

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.post.return_value = mock_resp

            result = api_mod.create_conversation(
                model="claude-sonnet-4-5",
                pid="dev",
                cwd="/workspace/pids/dev",
                agent_directory="/workspace/pids/dev/.agent",
            )

        assert result == {"id": "conv-123"}
        posted = client_instance.post.call_args
        body = posted.kwargs["json"]
        assert body["model"] == "claude-sonnet-4-5"
        assert body["pid"] == "dev"
        assert body["cwd"] == "/workspace/pids/dev"
        assert body["agent_directory"] == "/workspace/pids/dev/.agent"
        assert body["type"] == "agent"
        assert body["initiated_by"] == "agent-invoke"
        # Header check
        assert posted.kwargs["headers"]["X-Internal-Key"] == "proxy-internal-key"

    def test_sends_sentinel_pid_without_explicit_pid(self):
        """When no pid is supplied, a sentinel 'agent-invoke' is sent for backward compat."""
        mock_resp = _mock_response(200, {"id": "conv-456"})

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.post.return_value = mock_resp

            result = api_mod.create_conversation(
                model="claude-sonnet-4-5",
                cwd="/tmp/myagent",
                agent_directory="/tmp/myagent/.agent",
            )

        assert result["id"] == "conv-456"
        body = client_instance.post.call_args.kwargs["json"]
        # pid is always sent (sentinel when not explicitly provided)
        assert body["pid"] == "agent-invoke"
        assert body["cwd"] == "/tmp/myagent"

    def test_connection_error_raises_connection_error(self):
        import httpx

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.post.side_effect = httpx.ConnectError("refused")

            with pytest.raises(ConnectionError) as exc_info:
                api_mod.create_conversation(model="claude-sonnet-4-5")

        assert "AI Manager" in str(exc_info.value)
        assert "AI_MANAGER_URL" in str(exc_info.value)

    def test_http_4xx_raises_runtime_error(self):
        mock_resp = _mock_response(401, {"detail": "Unauthorized"})

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.post.return_value = mock_resp

            with pytest.raises(RuntimeError) as exc_info:
                api_mod.create_conversation(model="claude-sonnet-4-5")

        assert "401" in str(exc_info.value)


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------

class TestSendMessage:
    def test_sends_text_to_correct_endpoint(self):
        mock_resp = _mock_response(200, {"id": "conv-123", "status": "active"})

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.post.return_value = mock_resp

            result = api_mod.send_message("conv-123", "hello world")

        assert result["id"] == "conv-123"
        posted = client_instance.post.call_args
        assert "/api/conversations/conv-123/messages" in posted.args[0]
        assert posted.kwargs["json"] == {"text": "hello world"}


# ---------------------------------------------------------------------------
# stream_events
# ---------------------------------------------------------------------------

class TestStreamEvents:
    def test_yields_assistant_events_and_stops_at_completed(self):
        """stream_events should yield events and stop when 'completed' is received."""
        sse_data = (
            "data: {\"type\": \"assistant\", \"blocks\": [{\"type\": \"text\", \"text\": \"pong\"}]}\n\n"
            "data: {\"type\": \"completed\"}\n\n"
        )

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            response_mock = MagicMock()
            response_mock.__enter__ = MagicMock(return_value=response_mock)
            response_mock.__exit__ = MagicMock(return_value=False)
            response_mock.raise_for_status = MagicMock()
            response_mock.iter_text.return_value = iter([sse_data])

            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.stream.return_value = response_mock

            events = list(api_mod.stream_events("conv-123", timeout=30))

        types = [e["type"] for e in events]
        assert "assistant" in types
        assert "completed" in types
        # Should stop after completed
        assert types[-1] == "completed"

    def test_stops_at_error_event(self):
        sse_data = (
            "data: {\"type\": \"error\", \"message\": \"boom\"}\n\n"
        )

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            response_mock = MagicMock()
            response_mock.__enter__ = MagicMock(return_value=response_mock)
            response_mock.__exit__ = MagicMock(return_value=False)
            response_mock.raise_for_status = MagicMock()
            response_mock.iter_text.return_value = iter([sse_data])

            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.stream.return_value = response_mock

            events = list(api_mod.stream_events("conv-123", timeout=30))

        assert events[0]["type"] == "error"

    def test_skips_ping_lines(self):
        sse_data = (
            "event: ping\ndata: {}\n\n"
            "data: {\"type\": \"completed\"}\n\n"
        )

        with patch("agent_invoke.api.httpx.Client") as MockClient:
            response_mock = MagicMock()
            response_mock.__enter__ = MagicMock(return_value=response_mock)
            response_mock.__exit__ = MagicMock(return_value=False)
            response_mock.raise_for_status = MagicMock()
            response_mock.iter_text.return_value = iter([sse_data])

            client_instance = MockClient.return_value.__enter__.return_value
            client_instance.stream.return_value = response_mock

            events = list(api_mod.stream_events("conv-123", timeout=30))

        # Only the completed event should be returned (ping skipped)
        assert len(events) == 1
        assert events[0]["type"] == "completed"
