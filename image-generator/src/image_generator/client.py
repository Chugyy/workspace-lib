"""NanoBanana API client — supports base and pro models."""

import time
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os
import base64

TOOL_DIR = Path(__file__).parent.parent.parent

load_dotenv(TOOL_DIR / ".env")

API_BASE = "https://api.nanobananaapi.ai/api/v1/nanobanana"
POLL_INTERVAL = 3
MAX_POLLS = 120

# Model → endpoint mapping (verified against real API)
MODELS = {
    "base": {
        "endpoint": "/generate",
        "description": "Gemini 2.5 Flash — fast & cheap ($0.02/img)",
        "resolutions": {"1k"},
    },
    "pro": {
        "endpoint": "/generate-pro",
        "description": "Gemini 3 Pro — studio-grade ($0.09-0.12/img)",
        "resolutions": {"1k", "2k", "4k"},
    },
}

DEFAULT_MODEL = "pro"
DEFAULT_RESOLUTION = "1k"

ASPECT_RATIOS = {
    "1:1": "1:1",
    "16:9": "16:9",
    "9:16": "9:16",
    "4:3": "4:3",
    "3:4": "3:4",
}


class NanoBananaClient:
    """Client for nanobananaapi.ai REST API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NANOBANANA_API_KEY")
        if not self.api_key:
            raise ValueError("NANOBANANA_API_KEY not set in .env or environment")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        resolution: str = DEFAULT_RESOLUTION,
        aspect_ratio: str = "1:1",
        image_urls: Optional[list[str]] = None,
    ) -> str:
        """Submit a generation task. Returns task_id."""
        if model not in MODELS:
            raise ValueError(f"Unknown model '{model}'. Available: {list(MODELS.keys())}")

        cfg = MODELS[model]
        if resolution not in cfg["resolutions"]:
            raise ValueError(
                f"Model '{model}' doesn't support resolution '{resolution}'. "
                f"Available: {cfg['resolutions']}"
            )

        url = f"{API_BASE}{cfg['endpoint']}"

        payload = {
            "prompt": prompt,
            "aspectRatio": ASPECT_RATIOS.get(aspect_ratio, aspect_ratio),
        }

        # Base model requires explicit type (API has typo: IAMGE not IMAGE)
        if model == "base":
            payload["type"] = "IMAGETOIAMGE" if image_urls else "TEXTTOIAMGE"

        # Pro supports resolution param
        if model == "pro":
            res_map = {"1k": "1K", "2k": "2K", "4k": "4K"}
            payload["resolution"] = res_map.get(resolution, resolution.upper())

        if image_urls:
            payload["imageUrls"] = image_urls

        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        body = resp.json()
        data = body.get("data") or {}
        if body.get("code") != 200:
            raise RuntimeError(f"API error: {body.get('msg')} — {body}")
        task_id = data.get("taskId")
        if not task_id:
            raise RuntimeError(f"No taskId in response: {body}")
        return task_id

    def poll_result(self, task_id: str) -> dict:
        """Poll until generation completes. Returns result dict."""
        for _ in range(MAX_POLLS):
            resp = requests.get(
                f"{API_BASE}/record-info",
                params={"taskId": task_id},
                headers=self.headers,
            )
            resp.raise_for_status()
            body = resp.json()
            data = body.get("data") or {}

            if data.get("errorCode") or data.get("errorMessage"):
                raise RuntimeError(
                    f"Generation failed: {data.get('errorMessage')} ({data.get('errorCode')})"
                )

            if data.get("successFlag") == 1:
                return data

            time.sleep(POLL_INTERVAL)

        raise TimeoutError(f"Generation timed out after {MAX_POLLS * POLL_INTERVAL}s")

    def _extract_image_urls(self, result: dict) -> list[str]:
        """Extract image URLs from poll result."""
        urls = []
        response = result.get("response") or {}
        if response.get("resultImageUrl"):
            urls.append(response["resultImageUrl"])
        if response.get("originImageUrl"):
            urls.append(response["originImageUrl"])
        for key in ("imageUrls", "images", "resultImageUrls"):
            if result.get(key):
                urls.extend(result[key] if isinstance(result[key], list) else [result[key]])
        return urls

    def generate_and_wait(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        resolution: str = DEFAULT_RESOLUTION,
        aspect_ratio: str = "1:1",
        image_urls: Optional[list[str]] = None,
        num_images: int = 1,
    ) -> list[str]:
        """Generate image(s) and wait for results. Returns list of image URLs."""
        all_urls = []
        for _ in range(num_images):
            task_id = self.generate(prompt, model, resolution, aspect_ratio, image_urls)
            result = self.poll_result(task_id)
            urls = self._extract_image_urls(result)
            if urls:
                all_urls.append(urls[0])

        if not all_urls:
            raise RuntimeError("No images returned")
        return all_urls

    def download_image(self, url: str, output_path: Path) -> Path:
        """Download an image from URL to local path."""
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return output_path

    def upload_ref_image(self, image_path: Path) -> Optional[str]:
        """Upload a local image to a public host. Returns URL or None."""
        if not image_path.exists():
            return None

        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()

        try:
            resp = requests.post(
                "https://freeimage.host/api/1/upload",
                data={"key": "6d207e02198a847aa98d0a2a901485a5", "source": img_data, "format": "json"},
                timeout=30,
            )
            if resp.status_code == 200:
                url = resp.json().get("image", {}).get("url")
                if url:
                    return url
        except Exception:
            pass

        try:
            with open(image_path, "rb") as f:
                resp = requests.post("https://0x0.st", files={"file": f}, timeout=30)
                if resp.status_code == 200:
                    return resp.text.strip()
        except Exception:
            pass

        return None


def create_client(api_key: Optional[str] = None) -> NanoBananaClient:
    return NanoBananaClient(api_key=api_key)
