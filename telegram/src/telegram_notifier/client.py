"""Telegram Bot API client using urllib."""

import json
import sys
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR.parent / ".profiles"))


class TelegramClient:
    """Simple Telegram Bot API client."""

    def __init__(self, bot_token: str, default_chat_id: Optional[int] = None):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, chat_id: Optional[int] = None,
                     parse_mode: Optional[str] = None,
                     disable_notification: bool = False) -> Dict[str, Any]:
        target_chat_id = chat_id or self.default_chat_id
        if not target_chat_id:
            raise ValueError("No chat_id specified and no default chat_id set")
        data = {"chat_id": target_chat_id, "text": text,
                "disable_notification": disable_notification}
        if parse_mode:
            data["parse_mode"] = parse_mode
        return self._api_request("sendMessage", data)

    def send_notification(self, title: str, message: str,
                          chat_id: Optional[int] = None,
                          emoji: str = "🔔") -> Dict[str, Any]:
        text = f"{emoji} *{title}*\n\n{message}"
        return self.send_message(text, chat_id=chat_id, parse_mode="Markdown")

    def send_alert(self, message: str, level: str = "info",
                   chat_id: Optional[int] = None) -> Dict[str, Any]:
        emoji_map = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
        emoji = emoji_map.get(level.lower(), "📢")
        return self.send_notification(level.upper(), message, chat_id=chat_id, emoji=emoji)

    def get_updates(self, offset: Optional[int] = None) -> Dict[str, Any]:
        data = {}
        if offset is not None:
            data["offset"] = offset
        return self._api_request("getUpdates", data)

    def get_me(self) -> Dict[str, Any]:
        return self._api_request("getMe", {})

    def _api_request(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{method}"
        json_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=json_data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"Telegram API error: {e.code} - {error_body}")


def load_config(config_path=None, profile=None) -> Dict[str, Any]:
    """Load config from profile resolver, with legacy fallback."""
    if config_path is not None:
        with open(config_path, "r") as f:
            return json.load(f)
    try:
        from resolver import resolve
        return resolve("telegram", profile)
    except Exception:
        # Legacy fallback
        legacy = SKILL_DIR / "assets" / "config.json"
        if legacy.exists():
            with open(legacy, "r") as f:
                return json.load(f)
        raise


def create_client(config_path=None, profile=None) -> TelegramClient:
    config = load_config(config_path, profile=profile)
    return TelegramClient(
        bot_token=config["bot_token"],
        default_chat_id=config.get("chat_id"),
    )
