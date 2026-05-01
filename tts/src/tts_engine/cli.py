#!/usr/bin/env python3
"""TTS Engine CLI - Text-to-speech with Kokoro ONNX + natural pacing."""
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Text-to-speech with Kokoro ONNX. Supports French & English, markdown preprocessing, natural pauses.")


@app.command("say")
def say(
    text: Optional[str] = typer.Argument(None, help="Text to synthesize (or pipe via stdin)."),
    voice: str = typer.Option("ff_siwis", "--voice", "-v", help="Voice name (ff_siwis=FR, af_heart=EN)."),
    lang: str = typer.Option("fr-fr", "--lang", "-l", help="Language (fr-fr, en-us, en-gb)."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (default: play info only)."),
    speed: float = typer.Option(0.95, "--speed", "-s", help="Speech speed (0.5-2.0)."),
    pause_sentence: float = typer.Option(0.28, "--pause-sentence", help="Pause after sentence (seconds)."),
    pause_paragraph: float = typer.Option(0.55, "--pause-paragraph", help="Pause after paragraph (seconds)."),
    raw: bool = typer.Option(False, "--raw", "-r", help="Skip markdown preprocessing."),
):
    """Generate speech from text with natural pacing.

    Handles markdown (strips mermaid/code blocks, converts tables),
    pronounces tech acronyms correctly (SaaS, API, IoT...),
    and inserts natural pauses between sentences and paragraphs.

    Examples:
        tts say "Bonjour Hugo." -o hello.wav
        tts say "Hello world." -v af_heart -l en-us -o hello_en.wav
        cat article.md | tts say -o article.wav
    """
    from tts_engine.engine import TTSEngine, PauseConfig

    text = _read_text(text)
    pause = PauseConfig(
        after_sentence=pause_sentence,
        after_paragraph=pause_paragraph,
        speed=speed,
    )

    engine = TTSEngine()

    if output:
        path, result = engine.save(
            text, output, voice=voice, lang=lang,
            pause=pause, preprocess=not raw,
        )
        typer.echo(
            f"Saved: {path} | "
            f"{result.duration:.1f}s audio | "
            f"{result.generation_time:.1f}s gen | "
            f"RTF: {result.rtf:.2f}x"
        )
    else:
        result = engine.generate(
            text, voice=voice, lang=lang,
            pause=pause, preprocess=not raw,
        )
        typer.echo(
            f"Generated: {result.duration:.1f}s audio | "
            f"{result.generation_time:.1f}s gen | "
            f"RTF: {result.rtf:.2f}x | "
            f"Use -o file.wav to save."
        )


@app.command("generate")
def generate(
    text: Optional[str] = typer.Argument(None, help="Text to synthesize (or pipe via stdin)."),
    output: str = typer.Option("output.wav", "--output", "-o", help="Output file path."),
    voice: str = typer.Option("ff_siwis", "--voice", "-v", help="Voice name."),
    lang: str = typer.Option("fr-fr", "--lang", "-l", help="Language code."),
    speed: float = typer.Option(1.0, "--speed", "-s", help="Speech speed."),
    raw: bool = typer.Option(False, "--raw", "-r", help="Skip markdown preprocessing."),
):
    """Generate audio file from text (simple mode, no pause control)."""
    from kokoro_onnx import Kokoro
    import soundfile as sf

    text = _read_text(text)

    if not raw:
        from tts_engine.preprocessor import preprocess_for_speech
        text = preprocess_for_speech(text)

    assets = Path(__file__).parent.parent.parent
    kokoro = Kokoro(
        str(assets / "models" / "kokoro-v1.0.onnx"),
        str(assets / "models" / "voices-v1.0.bin"),
    )

    typer.echo(f"Generating with voice={voice}, lang={lang}...")
    samples, sr = kokoro.create(text, voice=voice, speed=speed, lang=lang)
    sf.write(output, samples, sr)
    typer.echo(f"Saved: {output} ({Path(output).stat().st_size / 1024:.1f} KB)")


@app.command("voices")
def voices():
    """List available voices by language."""
    from tts_engine.engine import TTSEngine
    engine = TTSEngine()
    all_voices = engine.get_voices()

    typer.echo("Available voices:")
    for lang_prefix, lang_name in [("ff_", "French"), ("af_", "English US (F)"), ("am_", "English US (M)"), ("bf_", "English GB (F)"), ("bm_", "English GB (M)")]:
        matches = [v for v in all_voices if v.startswith(lang_prefix)]
        if matches:
            typer.echo(f"  {lang_name}: {', '.join(matches)}")

    remaining = [v for v in all_voices if not any(v.startswith(p) for p in ["ff_", "af_", "am_", "bf_", "bm_"])]
    if remaining:
        typer.echo(f"  Other: {', '.join(sorted(remaining)[:10])}...")


@app.command("preview")
def preview(
    text: Optional[str] = typer.Argument(None, help="Text to preview preprocessing on (or pipe via stdin)."),
):
    """Preview what the preprocessor does to your text (no audio generation)."""
    from tts_engine.preprocessor import preprocess_for_speech

    text = _read_text(text)
    clean = preprocess_for_speech(text)

    typer.echo(f"--- Input: {len(text)} chars ---")
    typer.echo(f"--- Output: {len(clean)} chars ({100 - len(clean)/len(text)*100:.0f}% removed) ---\n")
    typer.echo(clean)


def _read_text(text: Optional[str]) -> str:
    """Read text from argument or stdin."""
    if text is None:
        if sys.stdin.isatty():
            typer.echo("Error: provide text as argument or pipe via stdin", err=True)
            raise typer.Exit(1)
        text = sys.stdin.read().strip()
    if not text:
        typer.echo("Error: empty text", err=True)
        raise typer.Exit(1)
    return text


if __name__ == "__main__":
    app()
