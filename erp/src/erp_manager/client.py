"""ERP API client for managing leads, notes, and users."""

import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List
from erp_manager.auth import load_config, ensure_authenticated


def _get_opener():
    proxy_handler = urllib.request.ProxyHandler()
    return urllib.request.build_opener(proxy_handler)


class ERPClient:
    """Client for interacting with Personal Dashboard ERP API."""

    def __init__(self, api_url: str, token: str):
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.api_url}{endpoint}"
        if params:
            params = {k: v for k, v in params.items() if v is not None}
            if params:
                url = f"{url}?{urllib.parse.urlencode(params)}"

        json_data = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=json_data, headers=self.headers, method=method)

        try:
            opener = _get_opener()
            with opener.open(req) as response:
                response_data = response.read().decode("utf-8")
                return json.loads(response_data) if response_data else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                error_msg = json.loads(error_body).get("message", error_body)
            except Exception:
                error_msg = error_body
            if e.code == 401:
                raise Exception("Unauthorized: Invalid or expired token")
            elif e.code == 403:
                raise Exception("Forbidden: You don't own this resource")
            elif e.code == 404:
                raise Exception("Not found: Resource doesn't exist")
            elif e.code == 400:
                raise Exception(f"Bad request: {error_msg}")
            elif e.code == 409:
                raise Exception(f"Conflict: {error_msg}")
            else:
                raise Exception(f"API error ({e.code}): {error_msg}")

    # ========== LEADS ==========

    def create_lead(self, name: str, email: str, first_name: Optional[str] = None,
                    phone: Optional[str] = None, company: Optional[str] = None,
                    address: Optional[str] = None, socials: Optional[str] = None,
                    status: str = "to_contact", heat_level: str = "cold",
                    interested: bool = True) -> Dict[str, Any]:
        data = {"name": name, "email": email, "status": status,
                "heatLevel": heat_level, "interested": interested}
        if first_name:
            data["firstName"] = first_name
        if phone:
            data["phone"] = phone
        if company:
            data["company"] = company
        if address:
            data["address"] = address
        if socials:
            data["socials"] = socials
        return self._request("POST", "/api/leads", data=data)

    def get_lead(self, lead_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/leads/{lead_id}")

    def list_leads(self, page: int = 1, limit: int = 20, status: Optional[str] = None,
                   heat_level: Optional[str] = None, interested: Optional[bool] = None,
                   search: Optional[str] = None, sort_by: str = "updated_at",
                   order: str = "desc") -> Dict[str, Any]:
        params = {"page": page, "limit": limit, "sortBy": sort_by, "order": order}
        if status:
            params["status"] = status
        if heat_level:
            params["heatLevel"] = heat_level
        if interested is not None:
            params["interested"] = str(interested).lower()
        if search:
            params["search"] = search
        return self._request("GET", "/api/leads", params=params)

    def update_lead(self, lead_id: int, **updates) -> Dict[str, Any]:
        field_mapping = {"first_name": "firstName", "heat_level": "heatLevel"}
        data = {field_mapping.get(k, k): v for k, v in updates.items()}
        return self._request("PUT", f"/api/leads/{lead_id}", data=data)

    def delete_lead(self, lead_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/leads/{lead_id}")

    def search_leads(self, query: str, **filters) -> Dict[str, Any]:
        return self.list_leads(search=query, **filters)

    # ========== NOTES ==========

    def create_note(self, lead_id: int, title: str, content: str,
                    description: Optional[str] = None) -> Dict[str, Any]:
        data = {"leadId": lead_id, "title": title, "content": content}
        if description:
            data["description"] = description
        return self._request("POST", "/api/notes", data=data)

    def get_note(self, note_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/notes/{note_id}")

    def update_note(self, note_id: int, **updates) -> Dict[str, Any]:
        return self._request("PUT", f"/api/notes/{note_id}", data=updates)

    def delete_note(self, note_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/notes/{note_id}")

    def list_lead_notes(self, lead_id: int) -> List[Dict[str, Any]]:
        result = self._request("GET", f"/api/leads/{lead_id}/notes")
        return result.get("notes", [])

    # ========== USERS ==========

    def get_user(self, user_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/users/{user_id}")


def create_client(config_path: Optional[str] = None) -> ERPClient:
    config = load_config(config_path)
    token = ensure_authenticated(config_path)
    return ERPClient(api_url=config["api_url"], token=token)


def format_lead(lead: Dict[str, Any]) -> str:
    return "\n".join([
        f"ID: {lead.get('id')}",
        f"Name: {lead.get('firstName', '')} {lead.get('name', '')}".strip(),
        f"Email: {lead.get('email', 'N/A')}",
        f"Company: {lead.get('company', 'N/A')}",
        f"Phone: {lead.get('phone', 'N/A')}",
        f"Status: {lead.get('status', 'N/A')}",
        f"Heat: {lead.get('heatLevel', 'N/A')}",
        f"Interested: {'Yes' if lead.get('interested') else 'No'}",
    ])


def format_note(note: Dict[str, Any]) -> str:
    content_preview = (note.get("content", "N/A") or "")[:100]
    return "\n".join([
        f"ID: {note.get('id')}",
        f"Lead ID: {note.get('leadId')}",
        f"Title: {note.get('title', 'N/A')}",
        f"Description: {note.get('description', 'N/A')}",
        f"Content: {content_preview}...",
    ])
