"""OpenAI gpt-image-2 client for image generation and editing."""

import base64
import time
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os

TOOL_DIR = Path(__file__).parent.parent.parent
load_dotenv(TOOL_DIR / ".env")

# Aspect ratio + resolution → pixel size (all multiples of 16, within gpt-image-2 limits)
SIZE_MAP = {
    ("1:1", "1k"): "1024x1024",
    ("1:1", "2k"): "2048x2048",
    ("1:1", "4k"): "2880x2880",
    ("16:9", "1k"): "1024x576",
    ("16:9", "2k"): "2560x1440",
    ("16:9", "4k"): "3840x2160",
    ("9:16", "1k"): "576x1024",
    ("9:16", "2k"): "1440x2560",
    ("9:16", "4k"): "2160x3840",
    ("4:3", "1k"): "1024x768",
    ("4:3", "2k"): "2048x1536",
    ("4:3", "4k"): "3072x2304",
    ("3:4", "1k"): "768x1024",
    ("3:4", "2k"): "1536x2048",
    ("3:4", "4k"): "2304x3072",
}

QUALITY_OPTIONS = {"low", "medium", "high"}


class OpenAIImageClient:
    """Client for OpenAI gpt-image-2 image generation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in .env or environment")

        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)

    def _resolve_size(
        self,
        aspect_ratio: str = "1:1",
        resolution: str = "1k",
        size_override: Optional[str] = None,
    ) -> str:
        """Resolve final pixel size from aspect ratio + resolution, or direct override."""
        if size_override:
            # Validate: must be WxH, multiples of 16
            parts = size_override.lower().split("x")
            if len(parts) != 2:
                raise ValueError(f"Invalid size '{size_override}'. Expected format: WIDTHxHEIGHT (e.g. 1920x1080)")
            w, h = int(parts[0]), int(parts[1])
            if w % 16 != 0 or h % 16 != 0:
                # Auto-round to nearest multiple of 16
                w = round(w / 16) * 16
                h = round(h / 16) * 16
            if max(w, h) >= 3840:
                raise ValueError(f"Max edge must be < 3840px. Got {max(w, h)}px.")
            total = w * h
            if total < 655_360 or total > 8_294_400:
                raise ValueError(f"Total pixels must be 655,360–8,294,400. Got {total:,}.")
            return f"{w}x{h}"

        key = (aspect_ratio, resolution)
        if key not in SIZE_MAP:
            raise ValueError(
                f"Unsupported format/resolution combo: {aspect_ratio} @ {resolution}. "
                f"Available: {list(SIZE_MAP.keys())}"
            )
        return SIZE_MAP[key]

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        resolution: str = "1k",
        quality: str = "high",
        num_images: int = 1,
        size_override: Optional[str] = None,
    ) -> list[bytes]:
        """Generate images from text prompt. Returns list of raw PNG bytes."""
        if quality not in QUALITY_OPTIONS:
            raise ValueError(f"Quality must be one of {QUALITY_OPTIONS}. Got '{quality}'.")

        size = self._resolve_size(aspect_ratio, resolution, size_override)

        result = self.client.images.generate(
            model="gpt-image-2",
            prompt=prompt,
            n=num_images,
            size=size,
            quality=quality,
        )

        images = []
        for item in result.data:
            img_bytes = base64.b64decode(item.b64_json)
            images.append(img_bytes)

        return images

    def edit(
        self,
        prompt: str,
        image_paths: list[Path],
        aspect_ratio: str = "1:1",
        resolution: str = "1k",
        quality: str = "high",
        num_images: int = 1,
        size_override: Optional[str] = None,
    ) -> list[bytes]:
        """Edit images using a prompt + reference images. Returns list of raw PNG bytes."""
        if quality not in QUALITY_OPTIONS:
            raise ValueError(f"Quality must be one of {QUALITY_OPTIONS}. Got '{quality}'.")

        size = self._resolve_size(aspect_ratio, resolution, size_override)

        # Open all image files
        files = []
        try:
            for p in image_paths:
                files.append(open(p, "rb"))

            # Single image → pass directly, multiple → pass as list
            image_input = files[0] if len(files) == 1 else files

            result = self.client.images.edit(
                model="gpt-image-2",
                image=image_input,
                prompt=prompt,
                n=num_images,
                size=size,
                quality=quality,
            )
        finally:
            for f in files:
                f.close()

        images = []
        for item in result.data:
            img_bytes = base64.b64decode(item.b64_json)
            images.append(img_bytes)

        return images

    def save_image(self, img_bytes: bytes, output_path: Path) -> Path:
        """Save raw image bytes to a file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        return output_path


def create_openai_client(api_key: Optional[str] = None) -> OpenAIImageClient:
    return OpenAIImageClient(api_key=api_key)
