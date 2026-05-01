#!/usr/bin/env python3
"""
Telegram client for sending notifications and messages.
Simple wrapper around Telegram Bot API using only standard libraries.
"""

import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any
import os


class TelegramClient:
    """Simple Telegram Bot API client using urllib."""

    def __init__(self, bot_token: str, default_chat_id: Optional[int] = None):
        """
        Initialize Telegram client.

        Args:
            bot_token: Telegram bot token from BotFather
            default_chat_id: Default chat ID for sending messages
        """
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(
        self,
        text: str,
        chat_id: Optional[int] = None,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False
    ) -> Dict[str, Any]:
        """
        Send a text message.

        Args:
            text: Message text to send
            chat_id: Target chat ID (uses default if not specified)
            parse_mode: Message formatting (None, 'Markdown', or 'HTML')
            disable_notification: Send silently

        Returns:
            Response dictionary from Telegram API
        """
        target_chat_id = chat_id or self.default_chat_id
        if not target_chat_id:
            raise ValueError("No chat_id specified and no default chat_id set")

        data = {
            "chat_id": target_chat_id,
            "text": text,
            "disable_notification": disable_notification
        }

        if parse_mode:
            data["parse_mode"] = parse_mode

        return self._api_request("sendMessage", data)

    def send_notification(
        self,
        title: str,
        message: str,
        chat_id: Optional[int] = None,
        emoji: str = "🔔"
    ) -> Dict[str, Any]:
        """
        Send a formatted notification message.

        Args:
            title: Notification title
            message: Notification message
            chat_id: Target chat ID (uses default if not specified)
            emoji: Emoji to use in title

        Returns:
            Response dictionary from Telegram API
        """
        text = f"{emoji} *{title}*\n\n{message}"
        return self.send_message(text, chat_id=chat_id, parse_mode="Markdown")

    def send_alert(
        self,
        message: str,
        level: str = "info",
        chat_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send an alert with appropriate emoji and formatting.

        Args:
            message: Alert message
            level: Alert level ('info', 'warning', 'error', 'success')
            chat_id: Target chat ID (uses default if not specified)

        Returns:
            Response dictionary from Telegram API
        """
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }

        emoji = emoji_map.get(level.lower(), "📢")
        title = level.upper()

        return self.send_notification(title, message, chat_id=chat_id, emoji=emoji)

    def get_updates(self, offset: Optional[int] = None) -> Dict[str, Any]:
        """
        Get updates (messages) sent to the bot.

        Args:
            offset: Identifier of the first update to return

        Returns:
            Response dictionary from Telegram API
        """
        data = {}
        if offset is not None:
            data["offset"] = offset

        return self._api_request("getUpdates", data)

    def get_me(self) -> Dict[str, Any]:
        """
        Get basic information about the bot.

        Returns:
            Response dictionary from Telegram API
        """
        return self._api_request("getMe", {})

    def _api_request(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to Telegram Bot API.

        Args:
            method: API method name
            data: Request data dictionary

        Returns:
            Response dictionary from Telegram API
        """
        url = f"{self.base_url}/{method}"

        # Convert data to JSON
        json_data = json.dumps(data).encode('utf-8')

        # Create request
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={'Content-Type': 'application/json'}
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"Telegram API error: {e.code} - {error_body}")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to config file (defaults to assets/config.json)

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Default to assets/config.json relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, '..', 'assets', 'config.json')

    with open(config_path, 'r') as f:
        return json.load(f)


def create_client(config_path: Optional[str] = None) -> TelegramClient:
    """
    Create a TelegramClient from config file.

    Args:
        config_path: Path to config file (defaults to assets/config.json)

    Returns:
        Configured TelegramClient instance
    """
    config = load_config(config_path)
    return TelegramClient(
        bot_token=config['bot_token'],
        default_chat_id=config.get('chat_id')
    )


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Telegram notification client')
    parser.add_argument('action', choices=['send', 'notify', 'alert', 'test'])
    parser.add_argument('--text', help='Message text')
    parser.add_argument('--title', help='Notification title')
    parser.add_argument('--level', default='info', choices=['info', 'warning', 'error', 'success'],
                        help='Alert level')
    parser.add_argument('--chat-id', type=int, help='Target chat ID (overrides config default)')
    args = parser.parse_args()

    client = create_client()
    chat_id = args.chat_id or None

    if args.action == 'send':
        if not args.text:
            print("--text required for send", file=sys.stderr)
            sys.exit(1)
        result = client.send_message(args.text, chat_id=chat_id)
    elif args.action == 'notify':
        if not args.title or not args.text:
            print("--title and --text required for notify", file=sys.stderr)
            sys.exit(1)
        result = client.send_notification(args.title, args.text, chat_id=chat_id)
    elif args.action == 'alert':
        if not args.text:
            print("--text required for alert", file=sys.stderr)
            sys.exit(1)
        result = client.send_alert(args.text, level=args.level, chat_id=chat_id)
    elif args.action == 'test':
        bot_info = client.get_me()
        print(f"Connected: {bot_info['result']['first_name']}")
        result = client.send_notification("Test", "Bot opérationnel")

    if result.get('ok'):
        print("OK")
    else:
        print(f"Error: {result}", file=sys.stderr)
        sys.exit(1)
