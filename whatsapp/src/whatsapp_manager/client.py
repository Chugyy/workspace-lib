"""
WAHA WhatsApp API Client

Integration with WAHA (WhatsApp HTTP API) — self-hosted, open-source.
Replaces the previous Unipile-based client with the same public interface.

WAHA docs: https://waha.devlike.pro/
"""

import base64
import httpx
import re
from typing import Optional, Dict, Any, List
from pathlib import Path


# ============================================================================
# EXCEPTIONS
# ============================================================================

class WAHAError(Exception):
    """Base exception for WAHA API errors."""
    pass


class UnauthorizedError(WAHAError):
    """401 - Invalid API key."""
    pass


class SessionNotFoundError(WAHAError):
    """404 - Session not found or not started."""
    pass


class NotFoundError(WAHAError):
    """404 - Resource not found."""
    pass


class SessionNotReadyError(WAHAError):
    """Session exists but is not in WORKING state (e.g. SCAN_QR_CODE)."""
    pass


class RateLimitError(WAHAError):
    """429 - Rate limit exceeded."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class InternalServerError(WAHAError):
    """500 - Internal server error."""
    pass


class InvalidPhoneNumberError(WAHAError):
    """Invalid phone number format."""
    pass


class PhoneNotOnWhatsAppError(WAHAError):
    """Phone number not registered on WhatsApp."""
    pass


class UnprocessableEntityError(WAHAError):
    """422 - Unprocessable entity."""
    pass


# ============================================================================
# HELPERS
# ============================================================================

def phone_to_chat_id(phone: str) -> str:
    """
    Convert E.164 phone number to WAHA chatId format.

    +33612345678 → 33612345678@c.us
    """
    digits = re.sub(r'\D', '', phone)
    return f"{digits}@c.us"


def _file_to_base64(file_path: str) -> str:
    """Read a file and return base64-encoded content."""
    return base64.b64encode(Path(file_path).read_bytes()).decode()


def _guess_mimetype(file_path: str) -> str:
    """Guess MIME type from file extension."""
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp",
        ".mp4": "video/mp4", ".avi": "video/avi",
        ".mov": "video/quicktime", ".mkv": "video/x-matroska",
        ".ogg": "audio/ogg; codecs=opus", ".opus": "audio/ogg; codecs=opus",
        ".mp3": "audio/mpeg", ".m4a": "audio/mp4",
        ".aac": "audio/aac", ".wav": "audio/wav",
        ".webm": "audio/webm",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    return mime_map.get(ext, "application/octet-stream")


# ============================================================================
# MAIN CLIENT
# ============================================================================

class WAHAClient:
    """
    Client for WAHA (WhatsApp HTTP API) integration.

    Features:
    - Session management (QR code, status)
    - Chat management (list chats, get messages)
    - Message sending (text, images, videos, audio, documents)
    - Media download
    - Phone number verification
    - Webhook configuration
    """

    def __init__(self, base_url: str, api_key: str, session: str = "default"):
        """
        Initialize WAHA client.

        Args:
            base_url: WAHA server URL (e.g., http://localhost:3000)
            api_key: WAHA API key (WHATSAPP_API_KEY)
            session: Session name (default: "default")
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = session
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def get_session_status(self) -> Dict[str, Any]:
        """
        Get current session status.

        Returns:
            dict with 'status' field: STARTING, SCAN_QR_CODE, WORKING, FAILED, STOPPED
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/api/sessions/{self.session}"
        )

    async def get_qr_code(self) -> Dict[str, Any]:
        """
        Get QR code for session authentication.

        Returns:
            dict: QR code data (image/base64)
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/api/{self.session}/auth/qr",
            params={"format": "raw"}
        )

    async def start_session(self) -> Dict[str, Any]:
        """Start the WhatsApp session."""
        return await self._make_request(
            method="POST",
            endpoint="/api/sessions/start",
            json={"name": self.session}
        )

    async def stop_session(self) -> Dict[str, Any]:
        """Stop the WhatsApp session."""
        return await self._make_request(
            method="POST",
            endpoint="/api/sessions/stop",
            json={"name": self.session}
        )

    # ========================================================================
    # PHONE VERIFICATION
    # ========================================================================

    @staticmethod
    def _validate_phone_number(phone: str) -> None:
        """
        Validate phone number format (E.164).

        Args:
            phone: Phone number to validate

        Raises:
            InvalidPhoneNumberError: If format is invalid
        """
        pattern = r'^\+[1-9]\d{1,14}$'
        if not re.match(pattern, phone):
            raise InvalidPhoneNumberError(
                f"Invalid phone number format: '{phone}'. "
                f"Expected E.164 format: +[country code][number] (e.g., +33612345678)"
            )

    async def check_phone_exists_on_whatsapp(self, phone: str) -> Dict[str, Any]:
        """
        Check if a phone number is registered on WhatsApp.

        Args:
            phone: Phone number (E.164 format: +33612345678)

        Returns:
            dict: {"numberExists": bool, "chatId": str}

        Raises:
            PhoneNotOnWhatsAppError: If phone is not on WhatsApp
        """
        digits = re.sub(r'\D', '', phone)
        result = await self._make_request(
            method="GET",
            endpoint="/api/contacts/check-exists",
            params={"phone": digits, "session": self.session}
        )

        if not result.get("numberExists"):
            raise PhoneNotOnWhatsAppError(
                f"Phone number {phone} is not registered on WhatsApp"
            )

        return result

    # ========================================================================
    # CHAT MANAGEMENT
    # ========================================================================

    async def get_chats(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        List all conversations.

        Args:
            limit: Max chats to return
            offset: Pagination offset

        Returns:
            dict with list of chat objects
        """
        chats = await self._make_request(
            method="GET",
            endpoint=f"/api/{self.session}/chats",
            params={"limit": limit, "offset": offset}
        )
        # Normalize to a consistent format
        if isinstance(chats, list):
            return {"items": chats}
        return chats

    async def get_chat_messages(
        self,
        chat_id: str,
        limit: int = 50,
        download_media: bool = True
    ) -> Dict[str, Any]:
        """
        Get message history for a chat.

        Args:
            chat_id: WAHA chat ID (e.g., 33612345678@c.us)
            limit: Number of messages to retrieve
            download_media: Whether to include media URLs

        Returns:
            dict with 'items' list of message objects
        """
        messages = await self._make_request(
            method="GET",
            endpoint=f"/api/{self.session}/chats/{chat_id}/messages",
            params={
                "limit": limit,
                "downloadMedia": str(download_media).lower()
            }
        )
        if isinstance(messages, list):
            return {"items": messages}
        return messages

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
            dict: Message result
        """
        return await self._make_request(
            method="POST",
            endpoint="/api/sendText",
            json={
                "session": self.session,
                "chatId": chat_id,
                "text": text
            }
        )

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
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {image_path}")

        return await self._make_request(
            method="POST",
            endpoint="/api/sendImage",
            json={
                "session": self.session,
                "chatId": chat_id,
                "file": {
                    "mimetype": _guess_mimetype(image_path),
                    "filename": path.name,
                    "data": _file_to_base64(image_path)
                },
                "caption": caption
            }
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
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {video_path}")

        return await self._make_request(
            method="POST",
            endpoint="/api/sendVideo",
            json={
                "session": self.session,
                "chatId": chat_id,
                "file": {
                    "mimetype": _guess_mimetype(video_path),
                    "filename": path.name,
                    "data": _file_to_base64(video_path)
                },
                "caption": caption
            }
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
            audio_path: Path to audio file
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {audio_path}")

        return await self._make_request(
            method="POST",
            endpoint="/api/sendVoice",
            json={
                "session": self.session,
                "chatId": chat_id,
                "file": {
                    "mimetype": _guess_mimetype(audio_path),
                    "data": _file_to_base64(audio_path)
                }
            }
        )

    async def send_file(
        self,
        chat_id: str,
        file_path: str,
        caption: str = ""
    ) -> Dict[str, Any]:
        """
        Send document/file.

        Args:
            chat_id: Target chat ID
            file_path: Path to file
            caption: Optional caption
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        return await self._make_request(
            method="POST",
            endpoint="/api/sendFile",
            json={
                "session": self.session,
                "chatId": chat_id,
                "file": {
                    "mimetype": _guess_mimetype(file_path),
                    "filename": path.name,
                    "data": _file_to_base64(file_path)
                },
                "caption": caption
            }
        )

    async def send_message_with_attachments(
        self,
        chat_id: str,
        text: str,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Send message with attachments.
        WAHA sends one file per request, so we send text first then files.

        Args:
            chat_id: Target chat ID
            text: Message text
            file_paths: List of file paths
        """
        # Send text message first (if any)
        result = None
        if text:
            result = await self.send_text_message(chat_id, text)

        # Send each file
        for fp in file_paths:
            mime = _guess_mimetype(fp)
            if mime.startswith("image/"):
                result = await self.send_image(chat_id, fp)
            elif mime.startswith("video/"):
                result = await self.send_video(chat_id, fp)
            elif mime.startswith("audio/"):
                result = await self.send_audio(chat_id, fp)
            else:
                result = await self.send_file(chat_id, fp)

        return result or {}

    async def start_new_conversation(
        self,
        phone: str,
        text: str,
        file_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Start new conversation with a phone number.

        Args:
            phone: Recipient phone number (E.164 format: +33612345678)
            text: Initial message
            file_paths: Optional attachments

        Raises:
            InvalidPhoneNumberError: If phone number format is invalid
            PhoneNotOnWhatsAppError: If phone is not on WhatsApp
        """
        self._validate_phone_number(phone)
        check_result = await self.check_phone_exists_on_whatsapp(phone)
        chat_id = check_result.get("chatId", phone_to_chat_id(phone))

        if file_paths:
            return await self.send_message_with_attachments(chat_id, text, file_paths)
        else:
            return await self.send_text_message(chat_id, text)

    # ========================================================================
    # MEDIA DOWNLOAD
    # ========================================================================

    async def download_media(
        self,
        chat_id: str,
        message_id: str,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Download media from a message.

        WAHA stores media and provides a URL in message.media.url.
        We fetch the message with downloadMedia=true, then download the file.

        Args:
            chat_id: Chat ID containing the message
            message_id: Message ID
            output_path: Optional file path to save

        Returns:
            bytes: Raw file content
        """
        # Get message with media URL
        msg = await self._make_request(
            method="GET",
            endpoint=f"/api/{self.session}/chats/{chat_id}/messages/{message_id}",
            params={"downloadMedia": "true"}
        )

        media_url = None
        if isinstance(msg, dict):
            media = msg.get("media")
            if media:
                media_url = media.get("url")

        if not media_url:
            raise NotFoundError(f"No media found in message {message_id}")

        # Download the actual file
        data = await self._download_file(media_url)

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        return data

    async def _download_file(self, url: str) -> bytes:
        """Download a file from a URL (media storage)."""
        # If relative URL, prepend base_url
        if url.startswith("/"):
            url = f"{self.base_url}{url}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {"X-Api-Key": self.api_key}
            response = await client.get(url, headers=headers)

            if response.status_code >= 400:
                self._handle_error(response)

            return response.content

    # ========================================================================
    # WEBHOOK MANAGEMENT
    # ========================================================================

    async def configure_webhooks(
        self,
        url: str,
        events: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Configure webhooks for the session.

        In WAHA, webhooks are configured per-session at start/update time.

        Args:
            url: Webhook endpoint URL
            events: Event types (e.g., ["message", "message.ack", "session.status"])
        """
        if events is None:
            events = ["message", "message.any"]

        return await self._make_request(
            method="PUT",
            endpoint=f"/api/sessions/{self.session}",
            json={
                "config": {
                    "webhooks": [{
                        "url": url,
                        "events": events
                    }]
                }
            }
        )

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to WAHA API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON payload

        Returns:
            dict or list: API response
        """
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            kwargs: Dict[str, Any] = {"headers": dict(self.headers)}

            if params:
                kwargs["params"] = params

            if json:
                kwargs["json"] = json

            response = await client.request(method, url, **kwargs)

            if response.status_code >= 400:
                self._handle_error(response)

            if response.content:
                return response.json()
            return {}

    def _handle_error(self, response: httpx.Response) -> None:
        """Parse error response and raise appropriate exception."""
        status = response.status_code

        try:
            error_data = response.json()
            # WAHA uses "error" field (not "message") for error descriptions
            message = error_data.get("error") or error_data.get("message", "Unknown error")
            if isinstance(message, list):
                message = "; ".join(str(m) for m in message)

            # Detect session-not-ready errors (WAHA returns 422 with status field)
            session_status = error_data.get("status")
            if session_status and session_status != "WORKING":
                raise SessionNotReadyError(
                    f"Session '{error_data.get('session', self.session)}' is in "
                    f"'{session_status}' state. Expected: WORKING. "
                    f"Scan QR code at: {self.base_url}/dashboard"
                )
        except SessionNotReadyError:
            raise
        except Exception:
            message = response.text or f"HTTP {status}"

        if status == 401:
            raise UnauthorizedError(f"Invalid API key: {message}")
        elif status == 404:
            raise NotFoundError(f"Not found: {message}")
        elif status == 422:
            raise UnprocessableEntityError(f"Unprocessable entity: {message}")
        elif status == 429:
            raise RateLimitError(message, retry_after=60)
        elif status >= 500:
            raise InternalServerError(f"Server error: {message}")
        else:
            raise WAHAError(f"API error ({status}): {message}")
