#!/usr/bin/env python3
"""
ERP API client for managing leads, notes, and users.
Provides complete CRUD operations using only urllib.
"""

import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List
import os
from auth_manager import load_config, ensure_authenticated


def _get_opener():
    """Get urllib opener with proxy support from environment."""
    proxy_handler = urllib.request.ProxyHandler()
    opener = urllib.request.build_opener(proxy_handler)
    return opener


class ERPClient:
    """Client for interacting with Personal Dashboard ERP API."""

    def __init__(self, api_url: str, token: str):
        """
        Initialize ERP client.

        Args:
            api_url: Base API URL
            token: JWT access token
        """
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response dictionary

        Raises:
            Exception: On HTTP error
        """
        url = f"{self.api_url}{endpoint}"

        # Add query parameters
        if params:
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            if params:
                query_string = urllib.parse.urlencode(params)
                url = f"{url}?{query_string}"

        # Prepare request
        json_data = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=json_data, headers=self.headers, method=method)

        try:
            opener = _get_opener()
            with opener.open(req) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data) if response_data else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get('message', error_body)
            except:
                error_msg = error_body

            if e.code == 401:
                raise Exception(f"Unauthorized: Invalid or expired token")
            elif e.code == 403:
                raise Exception(f"Forbidden: You don't own this resource")
            elif e.code == 404:
                raise Exception(f"Not found: Resource doesn't exist")
            elif e.code == 400:
                raise Exception(f"Bad request: {error_msg}")
            elif e.code == 409:
                raise Exception(f"Conflict: {error_msg}")
            else:
                raise Exception(f"API error ({e.code}): {error_msg}")

    # ========== LEADS METHODS ==========

    def create_lead(
        self,
        name: str,
        email: str,
        first_name: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        address: Optional[str] = None,
        socials: Optional[str] = None,
        status: str = "to_contact",
        heat_level: str = "cold",
        interested: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new lead.

        Args:
            name: Lead last name (required)
            email: Lead email (required)
            first_name: Lead first name
            phone: Phone number
            company: Company name
            address: Address
            socials: Social media links
            status: Lead status (to_contact, contacted, no_response, to_call_back, action_required, appointment_scheduled)
            heat_level: Heat level (cold, warm, hot, very_hot)
            interested: Whether lead is interested

        Returns:
            Dictionary with created lead ID
        """
        data = {
            "name": name,
            "email": email,
            "status": status,
            "heatLevel": heat_level,
            "interested": interested
        }

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
        """
        Get lead details by ID.

        Args:
            lead_id: Lead ID

        Returns:
            Complete lead object
        """
        return self._request("GET", f"/api/leads/{lead_id}")

    def list_leads(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        heat_level: Optional[str] = None,
        interested: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "updated_at",
        order: str = "desc"
    ) -> Dict[str, Any]:
        """
        List leads with pagination and filters.

        Args:
            page: Page number (min 1)
            limit: Items per page (max 2000)
            status: Filter by status
            heat_level: Filter by heat level
            interested: Filter by interest
            search: Fulltext search (name, firstName, email, company)
            sort_by: Sort field (updated_at, created_at, name, email)
            order: Sort order (asc, desc)

        Returns:
            Dictionary with leads array and pagination metadata
        """
        params = {
            "page": page,
            "limit": limit,
            "sortBy": sort_by,
            "order": order
        }

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
        """
        Update lead fields.

        Args:
            lead_id: Lead ID
            **updates: Fields to update (name, firstName, email, phone, company, etc.)

        Returns:
            Updated lead object
        """
        # Convert snake_case to camelCase for API
        data = {}
        field_mapping = {
            'first_name': 'firstName',
            'heat_level': 'heatLevel'
        }

        for key, value in updates.items():
            api_key = field_mapping.get(key, key)
            data[api_key] = value

        return self._request("PUT", f"/api/leads/{lead_id}", data=data)

    def delete_lead(self, lead_id: int) -> Dict[str, Any]:
        """
        Delete lead permanently (cascade deletes notes).

        Args:
            lead_id: Lead ID

        Returns:
            Confirmation message
        """
        return self._request("DELETE", f"/api/leads/{lead_id}")

    def search_leads(self, query: str, **filters) -> Dict[str, Any]:
        """
        Search leads with fulltext query.

        Args:
            query: Search string (searches name, firstName, email, company)
            **filters: Additional filters (status, heat_level, etc.)

        Returns:
            Dictionary with matching leads
        """
        return self.list_leads(search=query, **filters)

    # ========== NOTES METHODS ==========

    def create_note(
        self,
        lead_id: int,
        title: str,
        content: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a note attached to a lead.

        Args:
            lead_id: Lead ID
            title: Note title (required)
            content: Note content (required)
            description: Optional note description

        Returns:
            Dictionary with created note ID
        """
        data = {
            "leadId": lead_id,
            "title": title,
            "content": content
        }

        if description:
            data["description"] = description

        return self._request("POST", "/api/notes", data=data)

    def get_note(self, note_id: int) -> Dict[str, Any]:
        """
        Get note details by ID.

        Args:
            note_id: Note ID

        Returns:
            Complete note object
        """
        return self._request("GET", f"/api/notes/{note_id}")

    def update_note(self, note_id: int, **updates) -> Dict[str, Any]:
        """
        Update note fields.

        Args:
            note_id: Note ID
            **updates: Fields to update (title, description, content)

        Returns:
            Updated note object
        """
        return self._request("PUT", f"/api/notes/{note_id}", data=updates)

    def delete_note(self, note_id: int) -> Dict[str, Any]:
        """
        Delete note permanently.

        Args:
            note_id: Note ID

        Returns:
            Confirmation message
        """
        return self._request("DELETE", f"/api/notes/{note_id}")

    def list_lead_notes(self, lead_id: int) -> List[Dict[str, Any]]:
        """
        Get all notes for a lead.

        Args:
            lead_id: Lead ID

        Returns:
            List of notes sorted by newest first
        """
        result = self._request("GET", f"/api/leads/{lead_id}/notes")
        return result.get("notes", [])

    # ========== USER METHODS ==========

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get user profile by ID.

        Args:
            user_id: User ID

        Returns:
            User profile object
        """
        return self._request("GET", f"/api/users/{user_id}")


# ========== HELPER FUNCTIONS ==========

def create_client(config_path: Optional[str] = None) -> ERPClient:
    """
    Create ERPClient with automatic authentication.

    Args:
        config_path: Path to config file

    Returns:
        Configured ERPClient instance
    """
    config = load_config(config_path)
    token = ensure_authenticated(config_path)

    return ERPClient(
        api_url=config['api_url'],
        token=token
    )


def format_lead_summary(lead: Dict[str, Any]) -> str:
    """
    Format lead for concise display.

    Args:
        lead: Lead object

    Returns:
        Formatted string
    """
    lines = [
        f"ID: {lead.get('id')}",
        f"Name: {lead.get('firstName', '')} {lead.get('name', '')}".strip(),
        f"Email: {lead.get('email', 'N/A')}",
        f"Company: {lead.get('company', 'N/A')}",
        f"Phone: {lead.get('phone', 'N/A')}",
        f"Status: {lead.get('status', 'N/A')}",
        f"Heat: {lead.get('heatLevel', 'N/A')}",
        f"Interested: {'Yes' if lead.get('interested') else 'No'}"
    ]
    return "\n".join(lines)


def format_note_summary(note: Dict[str, Any]) -> str:
    """
    Format note for display.

    Args:
        note: Note object

    Returns:
        Formatted string
    """
    lines = [
        f"ID: {note.get('id')}",
        f"Lead ID: {note.get('leadId')}",
        f"Title: {note.get('title', 'N/A')}",
        f"Description: {note.get('description', 'N/A')}",
        f"Content: {note.get('content', 'N/A')[:100]}..."
    ]
    return "\n".join(lines)


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='ERP client')
    parser.add_argument('action', choices=[
        'list-leads', 'get-lead', 'create-lead', 'update-lead', 'delete-lead',
        'create-note', 'list-notes', 'get-note', 'delete-note'
    ])
    # Lead args
    parser.add_argument('--id', type=int, help='Lead or note ID')
    parser.add_argument('--name', help='Lead last name')
    parser.add_argument('--first-name', help='Lead first name')
    parser.add_argument('--email', help='Lead email')
    parser.add_argument('--phone', help='Phone number')
    parser.add_argument('--company', help='Company name')
    parser.add_argument('--status', help='Lead status')
    parser.add_argument('--heat-level', help='Heat level (cold/warm/hot/very_hot)')
    parser.add_argument('--search', help='Search query')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--page', type=int, default=1)
    # Note args
    parser.add_argument('--lead-id', type=int, help='Lead ID for notes')
    parser.add_argument('--title', help='Note title')
    parser.add_argument('--content', help='Note content')
    args = parser.parse_args()

    client = create_client()

    if args.action == 'list-leads':
        result = client.list_leads(
            page=args.page, limit=args.limit,
            status=args.status, heat_level=args.heat_level, search=args.search
        )
        for lead in result.get('leads', []):
            print(format_lead_summary(lead))
            print("---")

    elif args.action == 'get-lead':
        if not args.id:
            print("--id required", file=sys.stderr); sys.exit(1)
        print(format_lead_summary(client.get_lead(args.id)))

    elif args.action == 'create-lead':
        if not args.name or not args.email:
            print("--name and --email required", file=sys.stderr); sys.exit(1)
        result = client.create_lead(
            name=args.name, email=args.email,
            first_name=args.first_name, phone=args.phone,
            company=args.company, status=args.status or 'to_contact',
            heat_level=args.heat_level or 'cold'
        )
        print(f"Created lead ID: {result.get('id')}")

    elif args.action == 'update-lead':
        if not args.id:
            print("--id required", file=sys.stderr); sys.exit(1)
        updates = {k: v for k, v in {
            'name': args.name, 'first_name': args.first_name,
            'email': args.email, 'phone': args.phone,
            'company': args.company, 'status': args.status,
            'heat_level': args.heat_level
        }.items() if v is not None}
        print(format_lead_summary(client.update_lead(args.id, **updates)))

    elif args.action == 'delete-lead':
        if not args.id:
            print("--id required", file=sys.stderr); sys.exit(1)
        print(client.delete_lead(args.id))

    elif args.action == 'create-note':
        if not args.lead_id or not args.title or not args.content:
            print("--lead-id, --title, --content required", file=sys.stderr); sys.exit(1)
        result = client.create_note(args.lead_id, args.title, args.content)
        print(f"Created note ID: {result.get('id')}")

    elif args.action == 'list-notes':
        if not args.lead_id:
            print("--lead-id required", file=sys.stderr); sys.exit(1)
        for note in client.list_lead_notes(args.lead_id):
            print(format_note_summary(note))
            print("---")

    elif args.action == 'get-note':
        if not args.id:
            print("--id required", file=sys.stderr); sys.exit(1)
        print(format_note_summary(client.get_note(args.id)))

    elif args.action == 'delete-note':
        if not args.id:
            print("--id required", file=sys.stderr); sys.exit(1)
        print(client.delete_note(args.id))
