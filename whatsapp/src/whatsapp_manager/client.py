"""
Unipile WhatsApp API Client

Complete integration with Unipile API for WhatsApp messaging.
Based on official Unipile API documentation.
"""

import httpx
import asyncio
import re
from typing import Optional, Dict, Any, List
from pathlib import Path


# ============================================================================
# EXCEPTIONS
# ============================================================================

class UnipileError(Exception):
    """Base exception for Unipile API errors"""
    pass


class UnauthorizedError(UnipileError):
    """401 - Invalid API key"""
    pass


class AccountDisconnectedError(UnipileError):
    """403 - Account is disconnected"""
    pass


class NotFoundError(UnipileError):
    """404 - Resource not found"""
    pass


class RateLimitError(UnipileError):
    """429 - Rate limit exceeded"""
    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after


class InternalServerError(UnipileError):
    """500 - Internal server error"""
    pass


class InvalidPhoneNumberError(UnipileError):
    """Invalid phone number format"""
    pass


class PhoneNotOnWhatsAppError(UnipileError):
    """Phone number not registered on WhatsApp"""
    pass


class UnprocessableEntityError(UnipileError):
    """422 - Unprocessable entity (often means phone not on WhatsApp)"""
    pass


# ============================================================================
# MAIN CLIENT
# ============================================================================

class UnipileWhatsAppClient:
    """
    Client for Unipile WhatsApp API integration.

    Features:
    - Account management (QR code generation, connection)
    - Webhook configuration
    - Chat management
    - Message sending (text, images, videos, audio, documents)
    - Error handling with custom exceptions
    """

    def __init__(self, dsn: str, api_key: str):
        """
        Initialize Unipile WhatsApp client.

        Args:
            dsn: API base URL (e.g., https://api1.unipile.com:13111)
            api_key: Your Unipile API key
        """
        self.dsn = dsn.rstrip('/')
        self.api_key = api_key
        self.base_url = f"{self.dsn}/api/v1"
        self.headers = {
            "X-API-KEY": self.api_key,
            "accept": "application/json"
        }

    # ========================================================================
    # ACCOUNT MANAGEMENT
    # ========================================================================

    async def create_account(self) -> Dict[str, Any]:
        """
        Generate QR code for new WhatsApp connection.

        Returns:
            dict: {
                "id": str,
                "provider": "WHATSAPP",
                "status": "WAITING_QR_SCAN",
                "qr_code": str,
                "code": str,
                "created_at": str
            }

        Usage:
            result = await client.create_account()
            account_id = result["id"]
            qr_code = result["qr_code"]
            # Display QR code to user for scanning
        """
        return await self._make_request(
            method="POST",
            endpoint="/accounts",
            json={"provider": "WHATSAPP"}
        )

    async def reconnect_account(self, account_id: str) -> Dict[str, Any]:
        """
        Regenerate QR code for existing account reconnection.

        Args:
            account_id: Unipile account ID

        Returns:
            dict: {
                "id": str,
                "provider": "WHATSAPP",
                "status": "WAITING_QR_SCAN",
                "qr_code": str,
                "code": str
            }
        """
        return await self._make_request(
            method="PATCH",
            endpoint=f"/accounts/{account_id}",
            json={"reconnect": True}
        )

    async def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Check account connection status.

        Args:
            account_id: Unipile account ID

        Returns:
            dict: {
                "id": str,
                "provider": "WHATSAPP",
                "status": str,  # WAITING_QR_SCAN, OK, CREDENTIALS, DISCONNECTED, EXPIRED
                "name": str (if connected),
                "provider_id": str (phone number if connected),
                "is_active": bool,
                "connected_at": str
            }
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/accounts/{account_id}"
        )

    async def poll_until_connected(
        self,
        account_id: str,
        interval: int = 3,
        max_attempts: int = 60
    ) -> Dict[str, Any]:
        """
        Poll account status until connected or timeout.

        Args:
            account_id: Unipile account ID
            interval: Polling interval in seconds (default: 3)
            max_attempts: Maximum polling attempts (default: 60)

        Returns:
            dict: Final account status

        Raises:
            TimeoutError: If connection not established within max_attempts
        """
        for attempt in range(max_attempts):
            status = await self.get_account_status(account_id)

            if status.get("status") == "OK":
                return status

            if attempt < max_attempts - 1:
                await asyncio.sleep(interval)

        raise TimeoutError(
            f"Account connection timeout after {max_attempts * interval} seconds"
        )

    # ========================================================================
    # WEBHOOK MANAGEMENT
    # ========================================================================

    async def create_webhook(
        self,
        url: str,
        source: str = "messaging",
        headers: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Create webhook for receiving events.

        Args:
            url: Your webhook endpoint URL
            source: Event source ("messaging" or "account")
            headers: Optional custom headers to include in webhook requests

        Returns:
            dict: {
                "id": str,
                "request_url": str,
                "source": str,
                "headers": list,
                "active": bool,
                "created_at": str
            }

        Note:
            Your endpoint must respond with HTTP 200 within 30 seconds.
        """
        payload = {
            "request_url": url,
            "source": source
        }

        if headers:
            payload["headers"] = headers

        return await self._make_request(
            method="POST",
            endpoint="/webhooks",
            json=payload
        )

    async def list_webhooks(self) -> List[Dict[str, Any]]:
        """
        List all configured webhooks.

        Returns:
            list: List of webhook objects
        """
        result = await self._make_request(
            method="GET",
            endpoint="/webhooks"
        )
        return result.get("items", [])

    async def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: Webhook ID to delete

        Returns:
            bool: True if deleted successfully
        """
        await self._make_request(
            method="DELETE",
            endpoint=f"/webhooks/{webhook_id}"
        )
        return True

    # ========================================================================
    # CHAT MANAGEMENT
    # ========================================================================

    async def get_chats(
        self,
        account_id: str,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all conversations for an account.

        Args:
            account_id: Unipile account ID
            cursor: Pagination cursor (optional)

        Returns:
            dict: {
                "object": "ChatList",
                "items": [
                    {
                        "id": str,
                        "account_id": str,
                        "title": str,
                        "attendees": list,
                        "last_message": dict,
                        "is_group": bool
                    }
                ],
                "cursor": str (next page cursor)
            }
        """
        params = {"account_id": account_id}
        if cursor:
            params["cursor"] = cursor

        return await self._make_request(
            method="GET",
            endpoint="/chats",
            params=params
        )

    async def get_chat_messages(
        self,
        chat_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get message history for a chat.

        Args:
            chat_id: Chat ID
            limit: Number of messages to retrieve (default: 50)

        Returns:
            dict: Message list with pagination info
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/chats/{chat_id}/messages",
            params={"limit": limit}
        )

    # ========================================================================
    # USER/PHONE VERIFICATION
    # ========================================================================

    async def check_phone_exists_on_whatsapp(
        self,
        account_id: str,
        phone: str
    ) -> bool:
        """
        Check if a phone number is registered on WhatsApp.

        Uses Unipile's GET /users/{identifier} endpoint to verify if a phone
        number exists on WhatsApp before attempting to send a message.

        Args:
            account_id: Your Unipile account ID
            phone: Phone number to check (E.164 format: +33612345678)

        Returns:
            bool: True if number exists on WhatsApp, False otherwise

        Raises:
            PhoneNotOnWhatsAppError: If phone number is not registered on WhatsApp

        Note:
            - This is a proxy call to WhatsApp - does NOT sync user into Unipile
            - The phone number should be in E.164 format but without the '+'
            - Example: +33612345678 → use '33612345678' as identifier
        """
        # Remove '+' from phone for Unipile API (uses plain digits)
        phone_identifier = phone.lstrip('+')

        try:
            result = await self._make_request(
                method="GET",
                endpoint=f"/users/{phone_identifier}",
                params={"account_id": account_id}
            )
            # If we get a response, the number exists on WhatsApp
            return True

        except (NotFoundError, UnprocessableEntityError) as e:
            # 404 or 422 means the phone number is not on WhatsApp
            raise PhoneNotOnWhatsAppError(
                f"Phone number {phone} is not registered on WhatsApp"
            )

    # ========================================================================
    # PHONE NUMBER VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_phone_number(phone: str) -> None:
        """
        Validate phone number format (E.164).

        E.164 format: +[country code][number]
        - Must start with +
        - Followed by 1-15 digits
        - No spaces, dashes, or other characters

        Args:
            phone: Phone number to validate

        Raises:
            InvalidPhoneNumberError: If format is invalid

        Examples:
            Valid: +33612345678, +262692593845, +14155552671
            Invalid: +0, +, 33612345678, +abcd, +1234567890123456
        """
        # E.164 regex: + followed by 1-15 digits
        pattern = r'^\+[1-9]\d{1,14}$'

        if not re.match(pattern, phone):
            raise InvalidPhoneNumberError(
                f"Invalid phone number format: '{phone}'. "
                f"Expected E.164 format: +[country code][number] (e.g., +33612345678)"
            )

    # ========================================================================
    # MESSAGE SENDING
    # ========================================================================

    async def send_text_message(
        self,
        chat_id: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Send simple text message.

        Args:
            chat_id: Target chat ID
            text: Message content

        Returns:
            dict: {
                "id": str,
                "chat_id": str,
                "text": str,
                "type": "text",
                "timestamp": str,
                "status": "sent",
                "provider_message_id": str
            }
        """
        data = {"text": text}

        return await self._make_request(
            method="POST",
            endpoint=f"/chats/{chat_id}/messages",
            data=data
        )

    async def send_message_with_attachments(
        self,
        chat_id: str,
        text: str,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Send message with multiple attachments.

        Args:
            chat_id: Target chat ID
            text: Message content
            file_paths: List of file paths to attach

        Returns:
            dict: Message object with attachments info

        Limits:
            - Max 15 MB per file
            - Supported: JPG, PNG, GIF, WEBP, MP4, AVI, MOV, OGG, MP3, WAV, PDF, DOC, XLS
        """
        files = []
        data = {"text": text}

        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            files.append(
                ("attachments", (path.name, open(file_path, "rb")))
            )

        try:
            return await self._make_request(
                method="POST",
                endpoint=f"/chats/{chat_id}/messages",
                data=data,
                files=files
            )
        finally:
            # Close all opened files
            for _, (_, file_obj) in files:
                file_obj.close()

    async def send_image(
        self,
        chat_id: str,
        image_path: str,
        caption: str = ""
    ) -> Dict[str, Any]:
        """
        Send image message.

        Args:
            chat_id: Target chat ID
            image_path: Path to image file
            caption: Optional image caption

        Returns:
            dict: Message object
        """
        return await self.send_message_with_attachments(
            chat_id=chat_id,
            text=caption,
            file_paths=[image_path]
        )

    async def send_video(
        self,
        chat_id: str,
        video_path: str,
        caption: str = ""
    ) -> Dict[str, Any]:
        """
        Send video message.

        Args:
            chat_id: Target chat ID
            video_path: Path to video file
            caption: Optional video caption

        Returns:
            dict: Message object
        """
        return await self.send_message_with_attachments(
            chat_id=chat_id,
            text=caption,
            file_paths=[video_path]
        )

    async def send_audio(
        self,
        chat_id: str,
        audio_path: str
    ) -> Dict[str, Any]:
        """
        Send audio/voice message.

        Args:
            chat_id: Target chat ID
            audio_path: Path to audio file (OGG, MP3, WAV, AAC)

        Returns:
            dict: Message object
        """
        return await self.send_message_with_attachments(
            chat_id=chat_id,
            text="",
            file_paths=[audio_path]
        )

    async def start_new_conversation(
        self,
        account_id: str,
        phone: str,
        text: str,
        file_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Start new conversation with a phone number.

        Args:
            account_id: Your Unipile account ID
            phone: Recipient phone number (E.164 format: +33612345678)
            text: Initial message
            file_paths: Optional attachments

        Returns:
            dict: {
                "id": str,
                "chat_id": str,
                "text": str,
                "timestamp": str,
                "chat": {
                    "id": str,
                    "attendees": list
                }
            }

        Raises:
            InvalidPhoneNumberError: If phone number format is invalid
            PhoneNotOnWhatsAppError: If phone number is not registered on WhatsApp
        """
        # Step 1: Validate phone number format
        self._validate_phone_number(phone)

        # Step 2: Check if phone number exists on WhatsApp
        await self.check_phone_exists_on_whatsapp(account_id, phone)

        data = {
            "account_id": account_id,
            "text": text,
            "attendees_ids": phone
        }

        files = []
        if file_paths:
            for file_path in file_paths:
                path = Path(file_path)
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")

                files.append(
                    ("attachments", (path.name, open(file_path, "rb")))
                )

        try:
            return await self._make_request(
                method="POST",
                endpoint="/chats",
                data=data,
                files=files if files else None
            )
        except UnprocessableEntityError as e:
            # 422 error during message send also means phone not on WhatsApp
            raise PhoneNotOnWhatsAppError(
                f"Phone number {phone} is not registered on WhatsApp (422: {str(e)})"
            )
        finally:
            for _, (_, file_obj) in files:
                file_obj.close()

    # ========================================================================
    # MEDIA / ATTACHMENTS
    # ========================================================================

    async def download_attachment(
        self,
        message_id: str,
        attachment_id: str,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Download an attachment from a message.

        Endpoint: GET /api/v1/messages/{message_id}/attachments/{attachment_id}

        Args:
            message_id: Unipile message ID (field "id" in message object, NOT provider_id)
            attachment_id: Attachment ID (field "id" in attachment object = provider_id of attachment)
            output_path: Optional file path to save the attachment on disk

        Returns:
            bytes: Raw file content (already decrypted by Unipile)

        Raises:
            NotFoundError: Message or attachment not found
            UnauthorizedError: Invalid API key
            AccountDisconnectedError: Account disconnected

        Notes:
            - Unipile handles WhatsApp media decryption transparently
            - message_id comes from the "id" field of the message (not "provider_id")
            - attachment_id comes from attachments[n]["id"] (= same as message["provider_id"])

        Example:
            data = await client.download_attachment(
                message_id="kLR2ZebfWIy3Y6WeOPzIuw",
                attachment_id="3EB0C98DE493248B2CC757",
                output_path="/tmp/voice.ogg"
            )
        """
        data = await self._make_request_bytes(
            endpoint=f"/messages/{message_id}/attachments/{attachment_id}"
        )

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        return data

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Unipile API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/accounts")
            params: Query parameters
            json: JSON payload
            data: Form data
            files: File uploads

        Returns:
            dict: API response

        Raises:
            UnauthorizedError: Invalid API key
            AccountDisconnectedError: Account disconnected
            NotFoundError: Resource not found
            RateLimitError: Rate limit exceeded
            InternalServerError: Server error
        """
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Prepare request kwargs
            kwargs = {"headers": self.headers}

            if params:
                kwargs["params"] = params

            if json:
                kwargs["json"] = json
                kwargs["headers"]["content-type"] = "application/json"

            if data or files:
                kwargs["data"] = data
                if files:
                    kwargs["files"] = files

            # Make request
            response = await client.request(method, url, **kwargs)

            # Handle errors
            if response.status_code >= 400:
                self._handle_error(response)

            # Return JSON response
            if response.content:
                return response.json()
            return {}

    def _handle_error(self, response: httpx.Response) -> None:
        """
        Parse error response and raise appropriate exception.

        Args:
            response: httpx Response object

        Raises:
            UnauthorizedError: 401 status
            AccountDisconnectedError: 403 status
            NotFoundError: 404 status
            RateLimitError: 429 status
            InternalServerError: 500 status
            UnipileError: Other errors
        """
        status = response.status_code

        try:
            error_data = response.json()
            message = error_data.get("message", "Unknown error")
        except Exception:
            message = response.text or f"HTTP {status}"

        if status == 401:
            raise UnauthorizedError(f"Invalid API key: {message}")

        elif status == 403:
            raise AccountDisconnectedError(f"Account disconnected: {message}")

        elif status == 404:
            raise NotFoundError(f"Resource not found: {message}")

        elif status == 422:
            raise UnprocessableEntityError(f"Unprocessable entity: {message}")

        elif status == 429:
            retry_after = error_data.get("retry_after", 60)
            raise RateLimitError(message, retry_after=retry_after)

        elif status >= 500:
            raise InternalServerError(f"Server error: {message}")

        else:
            raise UnipileError(f"API error ({status}): {message}")

    async def _make_request_bytes(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Make HTTP GET request and return raw bytes (for media/attachments).

        Args:
            endpoint: API endpoint
            params: Optional query parameters

        Returns:
            bytes: Raw response content

        Raises:
            Same exceptions as _make_request
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "X-API-KEY": self.api_key,
            "accept": "application/octet-stream"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            kwargs = {"headers": headers}
            if params:
                kwargs["params"] = params

            response = await client.request("GET", url, **kwargs)

            if response.status_code >= 400:
                self._handle_error(response)

            return response.content


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json as _json
    import sys
    import os

    def _load_config():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, '..', 'assets', 'config.json')
        with open(config_path) as f:
            return _json.load(f)

    async def _run(args):
        config = _load_config()
        client = UnipileWhatsAppClient(
            dsn=config['unipile']['dsn'],
            api_key=config['unipile']['api_key']
        )

        if args.action == 'send-text':
            result = await client.send_text_message(args.chat_id, args.text)
        elif args.action == 'send-image':
            result = await client.send_image(args.chat_id, args.image, args.caption or "")
        elif args.action == 'send-video':
            result = await client.send_video(args.chat_id, args.video, args.caption or "")
        elif args.action == 'send-audio':
            result = await client.send_audio(args.chat_id, args.audio)
        elif args.action == 'new-conversation':
            files = args.files.split(',') if args.files else None
            result = await client.start_new_conversation(
                config['unipile']['account_id'], args.phone, args.text, files
            )
        elif args.action == 'get-chats':
            result = await client.get_chats(config['unipile']['account_id'])
        elif args.action == 'get-messages':
            result = await client.get_chat_messages(args.chat_id, args.limit or 50)
        elif args.action == 'download-attachment':
            result = await client.download_attachment(args.message_id, args.attachment_id, args.output)
            if isinstance(result, bytes):
                print(f"Downloaded {len(result)} bytes to {args.output}")
                return
        else:
            print(f"Unknown action: {args.action}", file=sys.stderr)
            sys.exit(1)

        print(_json.dumps(result, indent=2, default=str))

    parser = argparse.ArgumentParser(description='WhatsApp client via Unipile API')
    parser.add_argument('action', choices=[
        'send-text', 'send-image', 'send-video', 'send-audio',
        'new-conversation', 'get-chats', 'get-messages', 'download-attachment'
    ])
    parser.add_argument('--chat-id', help='Chat ID')
    parser.add_argument('--text', help='Message text')
    parser.add_argument('--image', help='Image file path')
    parser.add_argument('--video', help='Video file path')
    parser.add_argument('--audio', help='Audio file path')
    parser.add_argument('--caption', help='Media caption')
    parser.add_argument('--phone', help='Phone number E.164 format (+33...)')
    parser.add_argument('--files', help='Comma-separated file paths for attachments')
    parser.add_argument('--limit', type=int, help='Message limit')
    parser.add_argument('--message-id', help='Message ID')
    parser.add_argument('--attachment-id', help='Attachment ID')
    parser.add_argument('--output', help='Output file path for download')

    asyncio.run(_run(parser.parse_args()))
