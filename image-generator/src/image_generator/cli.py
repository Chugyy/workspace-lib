"""Image Generator CLI — supports OpenAI (gpt-image-2) and NanoBanana providers."""

import sys
import typer
import requests
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

TOOL_DIR = Path(__file__).parent.parent.parent

# Profile resolver — load credentials from profile
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".profiles"))
_profile_name: Optional[str] = None


def _load_profile():
    """Load profile and inject into os.environ for client compatibility."""
    try:
        from resolver import resolve
        config = resolve("image-generator", _profile_name)
        for key, value in config.items():
            if isinstance(value, str):
                os.environ.setdefault(key, value)
    except Exception:
        # Fallback to legacy .env
        load_dotenv(TOOL_DIR / ".env")


app = typer.Typer(help="Generate images via OpenAI gpt-image-2 or NanoBanana API.")


@app.callback()
def main(profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name")):
    global _profile_name
    _profile_name = profile
    _load_profile()


PERSONAL_CLOUD_URL = "https://personal-cloud-api.multimodal-house.fr"


def _upload_to_cloud(file_path: Path, cloud_key: str, prefix: str) -> str:
    """Upload a generated image to Personal Cloud and make it public. Returns the public URL."""
    object_key = f"{prefix.strip('/')}/{file_path.name}"

    # Upload
    with open(file_path, "rb") as f:
        resp = requests.put(
            f"{PERSONAL_CLOUD_URL}/v1/objects/{object_key}",
            headers={"Authorization": f"Bearer {cloud_key}"},
            files={"file": (file_path.name, f, "image/png")},
        )
    if not resp.ok:
        typer.echo(f"  Cloud upload failed ({resp.status_code}): {resp.text}")
        return ""

    # Make public
    requests.patch(
        f"{PERSONAL_CLOUD_URL}/v1/objects/{object_key}",
        headers={"Authorization": f"Bearer {cloud_key}", "Content-Type": "application/json"},
        json={"visibility": "public"},
    )

    return f"{PERSONAL_CLOUD_URL}/public/content/{object_key}"

DEFAULT_OUTPUT = TOOL_DIR / "output"


def _openai_client():
    from image_generator.openai_client import create_openai_client
    return create_openai_client()


def _nanobanana_client():
    from image_generator.client import create_client
    return create_client()


@app.command("generate")
def generate(
    prompt: str = typer.Option(..., "--prompt", "-p", help="Image generation prompt"),
    ref: Optional[str] = typer.Option(None, "--ref", "-r", help="Reference images: local paths or URLs, comma-separated"),
    provider: str = typer.Option("openai", "--provider", help="Provider: openai (default), nanobanana"),
    model: str = typer.Option("pro", "--model", "-m", help="NanoBanana model: base, pro. Ignored for OpenAI."),
    format: str = typer.Option("1:1", "--format", "-f", help="Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4"),
    resolution: str = typer.Option("1k", "--resolution", help="Resolution: 1k, 2k, 4k"),
    quality: str = typer.Option("high", "--quality", "-q", help="OpenAI quality: low, medium, high. Ignored for NanoBanana."),
    size: Optional[str] = typer.Option(None, "--size", "-s", help="Exact pixel size (e.g. 1920x1080). Overrides format+resolution. OpenAI only."),
    output: Path = typer.Option(DEFAULT_OUTPUT, "--output", "-o", help="Output directory"),
    num: int = typer.Option(1, "--num", "-n", help="Number of images (1-4 nanobanana, 1-8 openai)"),
    name: str = typer.Option("generated", "--name", help="Output filename prefix"),
    cloud_upload: bool = typer.Option(False, "--cloud-upload", help="Upload generated images to Personal Cloud automatically"),
    cloud_prefix: str = typer.Option("thumbnails", "--cloud-prefix", help="Object key prefix in Personal Cloud (e.g. thumbnails/04-mon-slug)"),
):
    """Generate or edit images from a text prompt, optionally with reference images."""
    output.mkdir(parents=True, exist_ok=True)

    cloud_key = os.getenv("PERSONAL_CLOUD_KEY", "") if cloud_upload else ""
    if cloud_upload and not cloud_key:
        typer.echo("Warning: --cloud-upload set but PERSONAL_CLOUD_KEY not found in .env. Skipping upload.")
        cloud_upload = False

    if provider == "openai":
        _generate_openai(prompt, ref, format, resolution, quality, size, output, num, name, cloud_upload, cloud_key, cloud_prefix)
    elif provider == "nanobanana":
        _generate_nanobanana(prompt, ref, model, format, resolution, output, num, name, cloud_upload, cloud_key, cloud_prefix)
    else:
        typer.echo(f"Unknown provider '{provider}'. Use 'openai' or 'nanobanana'.")
        raise typer.Exit(1)


def _generate_openai(prompt, ref, format, resolution, quality, size, output, num, name, cloud_upload=False, cloud_key="", cloud_prefix="thumbnails"):
    """Generate via OpenAI gpt-image-2."""
    client = _openai_client()

    size_label = size or f"{format} @ {resolution}"
    typer.echo(f"Provider: OpenAI (gpt-image-2) | Size: {size_label} | Quality: {quality}")

    # Resolve local reference images
    ref_paths = []
    if ref:
        for item in ref.split(","):
            item = item.strip()
            if not item:
                continue
            path = Path(item)
            if path.exists():
                ref_paths.append(path)
            else:
                typer.echo(f"Warning: ref '{item}' is not a local file. OpenAI edit requires local files. Skipping.")

    typer.echo(f"Generating {num} image(s)...")

    if ref_paths:
        typer.echo(f"Edit mode — {len(ref_paths)} reference image(s)")
        images = client.edit(
            prompt=prompt,
            image_paths=ref_paths,
            aspect_ratio=format,
            resolution=resolution,
            quality=quality,
            num_images=num,
            size_override=size,
        )
    else:
        images = client.generate(
            prompt=prompt,
            aspect_ratio=format,
            resolution=resolution,
            quality=quality,
            num_images=num,
            size_override=size,
        )

    saved = []
    for i, img_bytes in enumerate(images):
        suffix = f"-{chr(97 + i)}" if len(images) > 1 else ""
        out_path = output / f"{name}{suffix}.png"
        client.save_image(img_bytes, out_path)
        saved.append(str(out_path))
        typer.echo(f"Saved: {out_path}")
        if cloud_upload and cloud_key:
            public_url = _upload_to_cloud(out_path, cloud_key, cloud_prefix)
            if public_url:
                typer.echo(f"  ☁ Cloud: {public_url}")

    typer.echo(f"Done. {len(saved)} image(s) generated.")


def _generate_nanobanana(prompt, ref, model, format, resolution, output, num, name, cloud_upload=False, cloud_key="", cloud_prefix="thumbnails"):
    """Generate via NanoBanana (legacy)."""
    client = _nanobanana_client()

    typer.echo(f"Provider: NanoBanana | Model: {model} | Format: {format} | Resolution: {resolution}")

    # Resolve reference images (local files → upload, URLs → pass through)
    ref_urls = []
    if ref:
        for item in ref.split(","):
            item = item.strip()
            if not item:
                continue
            path = Path(item)
            if path.exists():
                typer.echo(f"Uploading reference: {path.name}...")
                url = client.upload_ref_image(path)
                if url:
                    ref_urls.append(url)
                else:
                    typer.echo(f"Warning: failed to upload {path.name}, skipping.")
            else:
                ref_urls.append(item)

    typer.echo(f"Generating {num} image(s)...")

    urls = client.generate_and_wait(
        prompt=prompt,
        model=model,
        resolution=resolution,
        aspect_ratio=format,
        image_urls=ref_urls or None,
        num_images=num,
    )

    saved = []
    for i, url in enumerate(urls):
        suffix = f"-{chr(97 + i)}" if len(urls) > 1 else ""
        out_path = output / f"{name}{suffix}.png"
        client.download_image(url, out_path)
        saved.append(str(out_path))
        typer.echo(f"Saved: {out_path}")
        if cloud_upload and cloud_key:
            public_url = _upload_to_cloud(out_path, cloud_key, cloud_prefix)
            if public_url:
                typer.echo(f"  ☁ Cloud: {public_url}")

    typer.echo(f"Done. {len(saved)} image(s) generated.")


@app.command("models")
def models():
    """List available models and providers."""
    typer.echo("=== OpenAI (default) ===")
    typer.echo("  gpt-image-2 — Reasoning-based generation, 2K+ resolution, text rendering, up to 8 images/prompt")
    typer.echo("    Quality: low ($0.006/img), medium ($0.05/img), high ($0.21/img)")
    typer.echo("    Formats: 1:1, 16:9, 9:16, 4:3, 3:4")
    typer.echo("    Resolutions: 1k, 2k, 4k (or custom via --size)")
    typer.echo("")
    typer.echo("=== NanoBanana (--provider nanobanana) ===")
    from image_generator.client import MODELS
    for model_name, cfg in MODELS.items():
        typer.echo(f"  {model_name} — {cfg['description']} [resolutions: {', '.join(sorted(cfg['resolutions']))}]")


@app.command("test")
def test(
    provider: str = typer.Option("openai", "--provider", help="Provider to test: openai, nanobanana"),
):
    """Test API connection."""
    if provider == "openai":
        typer.echo("Testing OpenAI gpt-image-2 connection...")
        client = _openai_client()
        images = client.generate(
            prompt="A simple blue circle on white background",
            aspect_ratio="1:1",
            resolution="1k",
            quality="low",
            num_images=1,
        )
        typer.echo(f"Success. Generated {len(images)} image(s), {len(images[0]):,} bytes.")
    elif provider == "nanobanana":
        typer.echo("Testing NanoBanana API connection...")
        client = _nanobanana_client()
        task_id = client.generate("A simple blue circle on white background", model="base")
        typer.echo(f"Task submitted: {task_id}")
        result = client.poll_result(task_id)
        typer.echo(f"Success. Status: {result.get('status')}")
    else:
        typer.echo(f"Unknown provider '{provider}'.")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
