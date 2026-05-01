#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord OAuth2 Authentication Service Template
Source: saas-clipping (Come)

Usage:
    from services.discord.auth import get_oauth_url, exchange_code_for_token, get_user_from_token
    url = get_oauth_url()
    tokens = await exchange_code_for_token(code)
    user = await get_user_from_token(tokens["access_token"])

Requires:
    pip install aiohttp
    ENV: DISCORD_OAUTH_CLIENT_ID, DISCORD_OAUTH_CLIENT_SECRET, DISCORD_OAUTH_REDIRECT_URI

Features:
    - OAuth2 authorization URL generation
    - Code-to-token exchange
    - User info retrieval from token
    - Token refresh
    - Token validity check with auto-refresh
"""

import aiohttp
from typing import Dict
from datetime import datetime, timedelta

DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_OAUTH_URL = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL = f"{DISCORD_API_BASE}/oauth2/token"
DISCORD_USER_URL = f"{DISCORD_API_BASE}/users/@me"
DISCORD_GUILDS_URL = f"{DISCORD_API_BASE}/users/@me/guilds"


def get_oauth_url(client_id: str, redirect_uri: str, scopes: str = "identify email guilds") -> str:
    """Generate Discord OAuth2 URL"""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes
    }
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{DISCORD_OAUTH_URL}?{query_string}"


async def exchange_code_for_token(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str
) -> Dict:
    """
    Exchange OAuth2 code for access tokens

    Returns:
        {"access_token": str, "token_type": "Bearer", "expires_in": int,
         "refresh_token": str, "scope": str}
    """
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_TOKEN_URL, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}) as resp:
            if resp.status == 200:
                return await resp.json()
            error = await resp.text()
            raise Exception(f"Failed to exchange code ({resp.status}): {error}")


async def get_user_from_token(access_token: str) -> Dict:
    """
    Get user info from Discord access token

    Returns:
        {"id": str, "username": str, "discriminator": str, "avatar": str, "email": str, ...}
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(DISCORD_USER_URL, headers={"Authorization": f"Bearer {access_token}"}) as resp:
            if resp.status == 200:
                return await resp.json()
            error = await resp.text()
            raise Exception(f"Failed to get user info ({resp.status}): {error}")


async def get_user_guilds(access_token: str) -> list:
    """
    Get guilds the user is a member of

    Returns:
        List of guild dicts: [{"id": str, "name": str, "icon": str, "owner": bool, "permissions": int}, ...]
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(DISCORD_GUILDS_URL, headers={"Authorization": f"Bearer {access_token}"}) as resp:
            if resp.status == 200:
                return await resp.json()
            error = await resp.text()
            raise Exception(f"Failed to get guilds ({resp.status}): {error}")


async def refresh_access_token(
    refresh_token: str,
    client_id: str,
    client_secret: str
) -> Dict:
    """Refresh an expired access token"""
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_TOKEN_URL, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}) as resp:
            if resp.status == 200:
                return await resp.json()
            error = await resp.text()
            raise Exception(f"Failed to refresh token ({resp.status}): {error}")
