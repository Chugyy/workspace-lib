#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord Bot Service Template (aiohttp, async)
Source: saas-clipping (Come)

Usage:
    from services.discord.bot import get_server, send_direct_message
    server = await get_server("123456789")

Requires:
    pip install aiohttp
    ENV: DISCORD_BOT_TOKEN

Features:
    - Server info, role CRUD, user management
    - Direct messages, message history
    - Invite generation
    - Ban/unban
    - All async with aiohttp
"""

import aiohttp
from typing import Optional, Dict, List

API_BASE = "https://discord.com/api/v10"


def get_bot_headers(bot_token: str) -> Dict[str, str]:
    """Get headers for bot token requests"""
    return {
        'Authorization': f'Bot {bot_token}',
        'Content-Type': 'application/json'
    }


# ============================================================================
# SERVER INFO
# ============================================================================

async def get_server(bot_token: str, server_id: str) -> Dict:
    """Get server information"""
    url = f"{API_BASE}/guilds/{server_id}?with_counts=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=get_bot_headers(bot_token)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "id": data["id"],
                    "name": data["name"],
                    "owner_id": data["owner_id"],
                    "member_count": data.get("approximate_member_count", 0)
                }
            error = await resp.text()
            raise Exception(f"Error fetching server ({resp.status}): {error}")


# ============================================================================
# ROLE MANAGEMENT
# ============================================================================

async def create_role(bot_token: str, server_id: str, role_name: str, color: Optional[int] = None, permissions: str = "0") -> Dict:
    """Create a role in a server"""
    url = f"{API_BASE}/guilds/{server_id}/roles"
    payload = {"name": role_name, "permissions": permissions}
    if color is not None:
        payload["color"] = color
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=get_bot_headers(bot_token), json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {"role_id": data["id"], "name": data["name"], "color": data["color"]}
            error = await resp.text()
            raise Exception(f"Error creating role ({resp.status}): {error}")


async def delete_role(bot_token: str, server_id: str, role_id: str) -> bool:
    """Delete a role from a server"""
    url = f"{API_BASE}/guilds/{server_id}/roles/{role_id}"
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=get_bot_headers(bot_token)) as resp:
            if resp.status == 204:
                return True
            error = await resp.text()
            raise Exception(f"Error deleting role ({resp.status}): {error}")


async def get_role(bot_token: str, server_id: str, role_name: str) -> Optional[Dict]:
    """Find a role by name"""
    url = f"{API_BASE}/guilds/{server_id}/roles"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=get_bot_headers(bot_token)) as resp:
            if resp.status == 200:
                for role in await resp.json():
                    if role["name"] == role_name:
                        return {"id": role["id"], "name": role["name"], "color": role["color"]}
                return None
            error = await resp.text()
            raise Exception(f"Error fetching roles ({resp.status}): {error}")


async def assign_user_role(bot_token: str, server_id: str, user_id: str, role_id: str) -> bool:
    """Assign a role to a user"""
    url = f"{API_BASE}/guilds/{server_id}/members/{user_id}/roles/{role_id}"
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=get_bot_headers(bot_token)) as resp:
            if resp.status == 204:
                return True
            error = await resp.text()
            raise Exception(f"Error assigning role ({resp.status}): {error}")


async def remove_user_role(bot_token: str, server_id: str, user_id: str, role_id: str) -> bool:
    """Remove a role from a user"""
    url = f"{API_BASE}/guilds/{server_id}/members/{user_id}/roles/{role_id}"
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=get_bot_headers(bot_token)) as resp:
            if resp.status == 204:
                return True
            error = await resp.text()
            raise Exception(f"Error removing role ({resp.status}): {error}")


# ============================================================================
# MESSAGING
# ============================================================================

async def send_direct_message(bot_token: str, user_id: str, content: str) -> Dict:
    """Send a DM to a user"""
    dm_url = f"{API_BASE}/users/@me/channels"
    async with aiohttp.ClientSession() as session:
        async with session.post(dm_url, headers=get_bot_headers(bot_token), json={"recipient_id": user_id}) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"Error creating DM channel ({resp.status}): {error}")
            channel_id = (await resp.json())["id"]

        msg_url = f"{API_BASE}/channels/{channel_id}/messages"
        async with session.post(msg_url, headers=get_bot_headers(bot_token), json={"content": content}) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {"message_id": data["id"], "content": data["content"], "sent_at": data["timestamp"]}
            error = await resp.text()
            raise Exception(f"Error sending message ({resp.status}): {error}")


async def send_channel_message(bot_token: str, channel_id: str, content: str) -> Dict:
    """Send a message to a channel"""
    url = f"{API_BASE}/channels/{channel_id}/messages"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=get_bot_headers(bot_token), json={"content": content}) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {"message_id": data["id"], "content": data["content"], "sent_at": data["timestamp"]}
            error = await resp.text()
            raise Exception(f"Error sending message ({resp.status}): {error}")


async def send_embed_message(bot_token: str, user_id: str, embed: Dict) -> Dict:
    """Send a rich embed DM to a user"""
    dm_url = f"{API_BASE}/users/@me/channels"
    async with aiohttp.ClientSession() as session:
        async with session.post(dm_url, headers=get_bot_headers(bot_token), json={"recipient_id": user_id}) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"Error creating DM channel ({resp.status}): {error}")
            channel_id = (await resp.json())["id"]

        msg_url = f"{API_BASE}/channels/{channel_id}/messages"
        async with session.post(msg_url, headers=get_bot_headers(bot_token), json={"embeds": [embed]}) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {"message_id": data["id"], "sent_at": data["timestamp"]}
            error = await resp.text()
            raise Exception(f"Error sending embed ({resp.status}): {error}")


# ============================================================================
# USER MANAGEMENT
# ============================================================================

async def get_user_by_id(bot_token: str, user_id: str) -> Dict:
    """Get user info by ID"""
    url = f"{API_BASE}/users/{user_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=get_bot_headers(bot_token)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "id": data["id"],
                    "username": data["username"],
                    "discriminator": data.get("discriminator", "0"),
                    "global_name": data.get("global_name", data["username"]),
                    "avatar": data.get("avatar")
                }
            error = await resp.text()
            raise Exception(f"Error fetching user ({resp.status}): {error}")


async def remove_user_from_server(bot_token: str, server_id: str, user_id: str) -> bool:
    """Kick a user from a server"""
    url = f"{API_BASE}/guilds/{server_id}/members/{user_id}"
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=get_bot_headers(bot_token)) as resp:
            if resp.status == 204:
                return True
            error = await resp.text()
            raise Exception(f"Error kicking user ({resp.status}): {error}")


async def ban_user(bot_token: str, server_id: str, user_id: str, delete_message_days: int = 0, reason: Optional[str] = None) -> bool:
    """Ban a user from a server"""
    url = f"{API_BASE}/guilds/{server_id}/bans/{user_id}"
    payload = {}
    if delete_message_days > 0:
        payload["delete_message_seconds"] = delete_message_days * 86400
    headers = get_bot_headers(bot_token)
    if reason:
        headers["X-Audit-Log-Reason"] = reason
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json=payload) as resp:
            if resp.status == 204:
                return True
            error = await resp.text()
            raise Exception(f"Error banning user ({resp.status}): {error}")


# ============================================================================
# INVITE MANAGEMENT
# ============================================================================

async def generate_invite_link(bot_token: str, server_id: str, max_age: int = 0, max_uses: int = 0) -> str:
    """Generate an invite link for a server (finds first text channel)"""
    channels_url = f"{API_BASE}/guilds/{server_id}/channels"
    async with aiohttp.ClientSession() as session:
        async with session.get(channels_url, headers=get_bot_headers(bot_token)) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"Error fetching channels ({resp.status}): {error}")
            channels = await resp.json()
            channel_id = next((c["id"] for c in channels if c["type"] == 0), None)
            if not channel_id:
                raise Exception("No text channel found")

        invite_url = f"{API_BASE}/channels/{channel_id}/invites"
        async with session.post(invite_url, headers=get_bot_headers(bot_token), json={"max_age": max_age, "max_uses": max_uses}) as resp:
            if resp.status == 200:
                return f"https://discord.gg/{(await resp.json())['code']}"
            error = await resp.text()
            raise Exception(f"Error creating invite ({resp.status}): {error}")


# ============================================================================
# CHANNEL MANAGEMENT
# ============================================================================

async def create_voice_channel(bot_token: str, server_id: str, name: str, category_id: Optional[str] = None) -> Dict:
    """Create a voice channel in a server"""
    url = f"{API_BASE}/guilds/{server_id}/channels"
    payload = {"name": name, "type": 2}  # 2 = GUILD_VOICE
    if category_id:
        payload["parent_id"] = category_id
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=get_bot_headers(bot_token), json=payload) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                return {"channel_id": data["id"], "name": data["name"]}
            error = await resp.text()
            raise Exception(f"Error creating voice channel ({resp.status}): {error}")


async def delete_channel(bot_token: str, channel_id: str) -> bool:
    """Delete a channel"""
    url = f"{API_BASE}/channels/{channel_id}"
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=get_bot_headers(bot_token)) as resp:
            if resp.status == 200:
                return True
            error = await resp.text()
            raise Exception(f"Error deleting channel ({resp.status}): {error}")


async def move_member_to_channel(bot_token: str, server_id: str, user_id: str, channel_id: str) -> bool:
    """Move a member to a voice channel"""
    url = f"{API_BASE}/guilds/{server_id}/members/{user_id}"
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=get_bot_headers(bot_token), json={"channel_id": channel_id}) as resp:
            if resp.status in [200, 204]:
                return True
            error = await resp.text()
            raise Exception(f"Error moving member ({resp.status}): {error}")
