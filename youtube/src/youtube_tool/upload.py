"""Upload videos and thumbnails to YouTube via Google API."""

import socket
from pathlib import Path
from typing import Optional

from googleapiclient.http import MediaFileUpload

# Force IPv4 globally — IPv6 not routable on this server
_orig_getaddrinfo = socket.getaddrinfo

def _ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    results = _orig_getaddrinfo(host, port, family, type, proto, flags)
    ipv4 = [r for r in results if r[0] == socket.AF_INET]
    return ipv4 if ipv4 else results

socket.getaddrinfo = _ipv4_only


def upload_video(
    file_path: str,
    title: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    category: str = "22",  # 22 = People & Blogs
    privacy: str = "private",
    thumbnail_path: Optional[str] = None,
    publish_at: Optional[str] = None,
) -> dict:
    """Upload a video to YouTube.

    Returns dict with: id, url, title, status.
    """
    from youtube_tool.auth import get_youtube_service

    youtube = get_youtube_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category,
        },
        "status": {
            "privacyStatus": "private" if publish_at else privacy,
            "selfDeclaredMadeForKids": False,
            **({"publishAt": publish_at} if publish_at else {}),
        },
    }

    media = MediaFileUpload(
        file_path,
        mimetype="video/*",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = _resumable_upload(request)
    video_id = response["id"]

    # Upload thumbnail if provided
    if thumbnail_path and Path(thumbnail_path).exists():
        set_thumbnail(video_id, thumbnail_path)

    return {
        "id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": title,
        "status": privacy,
    }


def set_thumbnail(video_id: str, thumbnail_path: str) -> dict:
    """Set a custom thumbnail for a video.

    Image must be JPG/PNG, under 2MB, 1280x720 recommended.
    Channel must be verified for custom thumbnails.
    """
    from youtube_tool.auth import get_youtube_service

    youtube = get_youtube_service()

    media = MediaFileUpload(thumbnail_path, mimetype="image/png")
    response = youtube.thumbnails().set(
        videoId=video_id,
        media_body=media,
    ).execute()

    return {
        "video_id": video_id,
        "thumbnails": response.get("items", [{}])[0].get("default", {}),
    }


def get_video_details(video_id: str) -> dict:
    """Get video snippet (title, description, tags, categoryId)."""
    from youtube_tool.auth import get_youtube_service

    youtube = get_youtube_service()
    response = youtube.videos().list(
        part="snippet",
        id=video_id,
    ).execute()

    items = response.get("items", [])
    if not items:
        raise ValueError(f"Video not found: {video_id}")

    snippet = items[0]["snippet"]
    return {
        "id": video_id,
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "tags": snippet.get("tags", []),
        "categoryId": snippet.get("categoryId", "22"),
    }


def update_video(
    video_id: str,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    category: str | None = None,
) -> dict:
    """Update an existing video's metadata (title, description, tags, category).

    Only provided fields are updated; others are preserved from the current video.
    """
    from youtube_tool.auth import get_youtube_service

    current = get_video_details(video_id)
    youtube = get_youtube_service()

    body = {
        "id": video_id,
        "snippet": {
            "title": title if title is not None else current["title"],
            "description": description if description is not None else current["description"],
            "tags": tags if tags is not None else current["tags"],
            "categoryId": category if category is not None else current["categoryId"],
        },
    }

    response = youtube.videos().update(
        part="snippet",
        body=body,
    ).execute()

    return {
        "id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": response["snippet"]["title"],
        "description": response["snippet"]["description"][:100] + "...",
    }


def _resumable_upload(request) -> dict:
    """Execute a resumable upload with progress."""
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"Upload: {progress}%")
    return response
