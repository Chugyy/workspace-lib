#!/usr/bin/env python3
"""
Authentication manager for ERP API.
Handles login, token persistence, and automatic authentication.
"""

import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any
import os


def _get_opener():
    """Get urllib opener with proxy support from environment."""
    proxy_handler = urllib.request.ProxyHandler()
    opener = urllib.request.build_opener(proxy_handler)
    return opener


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to config file (defaults to assets/config.json)

    Returns:
        Configuration dictionary with api_url, email, password
    """
    if config_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, '..', 'assets', 'config.json')

    with open(config_path, 'r') as f:
        return json.load(f)


def load_token(token_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load authentication token from file.

    Args:
        token_path: Path to token file (defaults to assets/token.json)

    Returns:
        Token dictionary with accessToken, tokenType, userId or None if not found
    """
    if token_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(script_dir, '..', 'assets', 'token.json')

    try:
        with open(token_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_token(token_data: Dict[str, Any], token_path: Optional[str] = None) -> None:
    """
    Save authentication token to file.

    Args:
        token_data: Token dictionary containing accessToken, tokenType, userId
        token_path: Path to token file (defaults to assets/token.json)
    """
    if token_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(script_dir, '..', 'assets', 'token.json')

    with open(token_path, 'w') as f:
        json.dump(token_data, f, indent=2)


def login(email: str, password: str, api_url: str) -> Dict[str, Any]:
    """
    Authenticate user and get access token.

    Args:
        email: User email
        password: User password
        api_url: Base API URL

    Returns:
        Token response with accessToken, tokenType, userId

    Raises:
        Exception: On authentication failure
    """
    url = f"{api_url}/api/auth/login"
    data = {
        "email": email,
        "password": password
    }

    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=json_data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        opener = _get_opener()
        with opener.open(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        if e.code == 401:
            raise Exception(f"Authentication failed: Invalid credentials")
        elif e.code == 400:
            raise Exception(f"Bad request: Invalid email or password format")
        else:
            raise Exception(f"Login error ({e.code}): {error_body}")


def register(email: str, password: str, name: Optional[str], api_url: str) -> Dict[str, Any]:
    """
    Register a new user account.

    Args:
        email: User email
        password: User password
        name: Optional user name
        api_url: Base API URL

    Returns:
        Token response with accessToken, tokenType, userId

    Raises:
        Exception: On registration failure
    """
    url = f"{api_url}/api/auth/register"
    data = {
        "email": email,
        "password": password
    }
    if name:
        data["name"] = name

    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=json_data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        opener = _get_opener()
        with opener.open(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        if e.code == 409:
            raise Exception(f"Registration failed: Email already exists")
        elif e.code == 400:
            raise Exception(f"Bad request: Invalid email or password format")
        else:
            raise Exception(f"Registration error ({e.code}): {error_body}")


def ensure_authenticated(config_path: Optional[str] = None, token_path: Optional[str] = None) -> str:
    """
    Ensure user is authenticated, performing login if necessary.

    Args:
        config_path: Path to config file
        token_path: Path to token file

    Returns:
        Access token string

    Raises:
        Exception: On authentication failure
    """
    # Try to load existing token
    token_data = load_token(token_path)

    if token_data and 'accessToken' in token_data:
        return token_data['accessToken']

    # No valid token, perform login
    config = load_config(config_path)

    token_response = login(
        email=config['email'],
        password=config['password'],
        api_url=config['api_url']
    )

    # Save token for future use
    save_token(token_response, token_path)

    return token_response['accessToken']


# Example usage
if __name__ == '__main__':
    try:
        print("Testing authentication...")
        token = ensure_authenticated()
        print(f"✓ Authentication successful")
        print(f"Token: {token[:20]}...")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
