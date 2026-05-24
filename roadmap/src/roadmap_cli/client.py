"""HTTP client for AI Manager Roadmap API."""

import os
import sys
from pathlib import Path
from typing import Any, Optional

import httpx

# Profile resolver
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".profiles"))

_DEFAULT_URL = "http://127.0.0.1:4810"
_DEFAULT_KEY = "proxy-internal-key"


def _load_config(profile: Optional[str] = None) -> dict:
    """Load backend URL and internal key from profile or env."""
    try:
        from resolver import resolve
        config = resolve("roadmap", profile)
        return {
            "backend_url": config.get("backend_url") or config.get("BACKEND_URL") or _DEFAULT_URL,
            "internal_key": config.get("internal_key") or config.get("INTERNAL_KEY") or _DEFAULT_KEY,
        }
    except Exception:
        pass

    return {
        "backend_url": os.environ.get("BACKEND_URL", _DEFAULT_URL),
        "internal_key": os.environ.get("BACKEND_INTERNAL_KEY", _DEFAULT_KEY),
    }


class RoadmapClient:
    """Synchronous HTTP client for the AI Manager Roadmap API."""

    def __init__(self, profile: Optional[str] = None):
        config = _load_config(profile)
        self.base_url = config["backend_url"].rstrip("/")
        self.headers = {"X-Internal-Key": config["internal_key"]}
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        )

    def _url(self, path: str) -> str:
        if path == "/":
            return "/api/roadmaps"
        return f"/api/roadmaps{path}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        resp = self._client.request(method, self._url(path), **kwargs)
        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                pass
            raise httpx.HTTPStatusError(
                f"{resp.status_code}: {detail}",
                request=resp.request,
                response=resp,
            )
        if resp.status_code == 204:
            return None
        return resp.json()

    # ── Roadmap CRUD ──────────────────────────────────────────────

    def list_roadmaps(self, pid: Optional[str] = None) -> list:
        params = {}
        if pid:
            params["pid"] = pid
        return self._request("GET", "/", params=params)

    def get_roadmap(self, roadmap_id: str) -> dict:
        return self._request("GET", f"/{roadmap_id}")

    def create_roadmap(
        self,
        name: str,
        pid: Optional[str] = None,
        description: Optional[str] = None,
        path: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {"name": name}
        if pid:
            body["pid"] = pid
        if description:
            body["description"] = description
        if path:
            body["path"] = path
        return self._request("POST", "/", json=body)

    def update_roadmap(self, roadmap_id: str, **fields) -> dict:
        body = {k: v for k, v in fields.items() if v is not None}
        return self._request("PATCH", f"/{roadmap_id}", json=body)

    def delete_roadmap(self, roadmap_id: str) -> None:
        self._request("DELETE", f"/{roadmap_id}")

    def duplicate_roadmap(self, roadmap_id: str) -> dict:
        return self._request("POST", f"/{roadmap_id}/duplicate")

    # ── Roadmap state & control ───────────────────────────────────

    def get_state(self, roadmap_id: str) -> dict:
        return self._request("GET", f"/{roadmap_id}/state")

    def get_graph(self, roadmap_id: str) -> dict:
        return self._request("GET", f"/{roadmap_id}/graph")

    def start_roadmap(self, roadmap_id: str) -> dict:
        return self._request("POST", f"/{roadmap_id}/start")

    def stop_roadmap(self, roadmap_id: str, hard: bool = False) -> dict:
        params = {"hard": "true"} if hard else {}
        return self._request("POST", f"/{roadmap_id}/stop", params=params)

    def pause_roadmap(self, roadmap_id: str) -> dict:
        return self._request("POST", f"/{roadmap_id}/pause")

    def get_executions(self, roadmap_id: str) -> list:
        return self._request("GET", f"/{roadmap_id}/executions")

    # ── Task CRUD ─────────────────────────────────────────────────

    def list_tasks(self, roadmap_id: str) -> list:
        return self._request("GET", f"/{roadmap_id}/tasks")

    def get_task(self, roadmap_id: str, task_id: str) -> dict:
        return self._request("GET", f"/{roadmap_id}/tasks/{task_id}")

    def create_task(self, roadmap_id: str, name: str, **fields) -> dict:
        body: dict[str, Any] = {"name": name}
        for k in ("description", "parent_id", "position", "script_path",
                   "template_ref", "run_config", "trigger_event",
                   "cron_expression", "sub_roadmap_id"):
            if fields.get(k) is not None:
                body[k] = fields[k]
        return self._request("POST", f"/{roadmap_id}/tasks", json=body)

    def update_task(self, roadmap_id: str, task_id: str, **fields) -> dict:
        body = {k: v for k, v in fields.items() if v is not None}
        return self._request("PATCH", f"/{roadmap_id}/tasks/{task_id}", json=body)

    def delete_task(self, roadmap_id: str, task_id: str) -> None:
        self._request("DELETE", f"/{roadmap_id}/tasks/{task_id}")

    def reorder_tasks(self, roadmap_id: str, task_ids: list[str]) -> None:
        self._request("POST", f"/{roadmap_id}/tasks/reorder", json={"task_ids": task_ids})

    # ── Task lifecycle ────────────────────────────────────────────

    def start_task(self, roadmap_id: str, task_id: str) -> dict:
        return self._request("POST", f"/{roadmap_id}/tasks/{task_id}/start")

    def cancel_task(self, roadmap_id: str, task_id: str) -> dict:
        return self._request("POST", f"/{roadmap_id}/tasks/{task_id}/cancel")

    def retry_task(self, roadmap_id: str, task_id: str) -> dict:
        return self._request("POST", f"/{roadmap_id}/tasks/{task_id}/retry")

    def check_task(self, roadmap_id: str, task_id: str) -> dict:
        return self._request("POST", f"/{roadmap_id}/tasks/{task_id}/check")

    def uncheck_task(self, roadmap_id: str, task_id: str) -> dict:
        return self._request("POST", f"/{roadmap_id}/tasks/{task_id}/uncheck")

    def reset_task(self, roadmap_id: str, task_id: str) -> dict:
        return self._request("POST", f"/{roadmap_id}/tasks/{task_id}/reset")

    def get_task_state(self, roadmap_id: str, task_id: str) -> dict:
        return self._request("GET", f"/{roadmap_id}/tasks/{task_id}/state")

    # ── Dependencies ──────────────────────────────────────────────

    def list_dependencies(self, roadmap_id: str) -> list:
        return self._request("GET", f"/{roadmap_id}/dependencies")

    def create_dependency(
        self,
        roadmap_id: str,
        task_id: str,
        depends_on: str,
        dep_type: str = "finish_to_start",
    ) -> dict:
        body = {
            "task_id": task_id,
            "depends_on": depends_on,
            "dep_type": dep_type,
        }
        return self._request("POST", f"/{roadmap_id}/dependencies", json=body)

    def delete_dependency(self, roadmap_id: str, dep_id: str) -> None:
        self._request("DELETE", f"/{roadmap_id}/dependencies/{dep_id}")

    # ── Blocks ────────────────────────────────────────────────────

    def list_blocks(
        self,
        roadmap_id: str,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list:
        params = {}
        if task_id:
            params["task_id"] = task_id
        if status:
            params["status"] = status
        return self._request("GET", f"/{roadmap_id}/blocks", params=params)

    def create_block(
        self,
        roadmap_id: str,
        content: str,
        task_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {"content": content}
        if task_id:
            body["task_id"] = task_id
        if source:
            body["source"] = source
        return self._request("POST", f"/{roadmap_id}/blocks", json=body)
