"""Kokoro ONNX TTS engine with sentence-level pacing and silence injection.

Cross-platform (Linux x86_64 + macOS Apple Silicon).
Uses kokoro-onnx for fast CPU inference (~0.25x RTF).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

# Default sample rate for Kokoro
SAMPLE_RATE = 24000

# Sentence splitter: split on . ! ? ; followed by space or end, or on double newlines
_SENTENCE_RE = re.compile(r'(?<=[.!?;])\s+')
_PARAGRAPH_RE = re.compile(r'\n\s*\n')


@dataclass
class PauseConfig:
    """Controls silence injection between segments."""
    after_clause: float = 0.10       # seconds — after , : within a sentence
    after_sentence: float = 0.28     # seconds — after . ! ?
    after_paragraph: float = 0.55    # seconds — after blank line
    variance: float = 0.05           # random jitter (+/- seconds)
    speed: float = 1.0               # speech speed multiplier (0.5–2.0)


@dataclass
class TTSResult:
    """Result of TTS generation."""
    audio: np.ndarray
    sample_rate: int
    duration: float              # seconds
    generation_time: float       # seconds
    text_chars: int
    rtf: float                   # real-time factor (< 1 = faster than realtime)


class TTSEngine:
    """High-level TTS engine wrapping kokoro-onnx with pacing control."""

    # Voice mappings
    VOICES_FR = ["ff_siwis"]
    VOICES_EN = [
        "af_heart", "af_bella", "af_nova", "af_sky",
        "am_adam", "am_echo", "am_michael",
    ]
    VOICES_EN_GB = ["bf_alice", "bf_emma", "bm_daniel", "bm_george"]

    def __init__(
        self,
        model_path: str | Path | None = None,
        voices_path: str | Path | None = None,
    ):
        assets_dir = Path(__file__).parent.parent.parent
        self._model_path = str(model_path or assets_dir / "models" / "kokoro-v1.0.onnx")
        self._voices_path = str(voices_path or assets_dir / "models" / "voices-v1.0.bin")
        self._kokoro: Kokoro | None = None

    def _load(self) -> Kokoro:
        if self._kokoro is None:
            self._kokoro = Kokoro(self._model_path, self._voices_path)
        return self._kokoro

    def generate(
        self,
        text: str,
        voice: str = "ff_siwis",
        lang: str = "fr-fr",
        pause: PauseConfig | None = None,
        preprocess: bool = True,
    ) -> TTSResult:
        """Generate speech from text with natural pacing.

        Args:
            text: Input text (markdown OK if preprocess=True).
            voice: Kokoro voice name.
            lang: Language code for phonemizer (fr-fr, en-us, en-gb).
            pause: Pause configuration. None = defaults.
            preprocess: Apply markdown-to-speech preprocessor.
        """
        import time

        if pause is None:
            pause = PauseConfig()

        # Preprocess if requested
        if preprocess:
            from tts_engine.preprocessor import preprocess_for_speech
            text = preprocess_for_speech(text)

        kokoro = self._load()
        rng = np.random.default_rng()

        t0 = time.time()

        # Split into paragraphs, then sentences
        paragraphs = _PARAGRAPH_RE.split(text.strip())
        all_audio: list[np.ndarray] = []

        for p_idx, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            sentences = _SENTENCE_RE.split(paragraph)

            for s_idx, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Generate audio for this sentence
                try:
                    samples, sr = kokoro.create(
                        sentence, voice=voice, speed=pause.speed, lang=lang,
                    )
                    all_audio.append(samples)
                except Exception as e:
                    # Skip sentences that fail (e.g., too short, weird chars)
                    continue

                # Add pause after sentence (except last in paragraph)
                if s_idx < len(sentences) - 1:
                    silence = _make_silence(pause.after_sentence, pause.variance, rng)
                    all_audio.append(silence)

            # Add pause after paragraph (except last)
            if p_idx < len(paragraphs) - 1:
                silence = _make_silence(pause.after_paragraph, pause.variance, rng)
                all_audio.append(silence)

        if not all_audio:
            raise RuntimeError("No audio generated — text may be empty after preprocessing.")

        audio = np.concatenate(all_audio)
        t_gen = time.time() - t0
        duration = len(audio) / SAMPLE_RATE

        return TTSResult(
            audio=audio,
            sample_rate=SAMPLE_RATE,
            duration=duration,
            generation_time=t_gen,
            text_chars=len(text),
            rtf=t_gen / duration if duration > 0 else 0,
        )

    def save(
        self,
        text: str,
        output_path: str | Path,
        voice: str = "ff_siwis",
        lang: str = "fr-fr",
        pause: PauseConfig | None = None,
        preprocess: bool = True,
        fmt: str = "wav",
    ) -> tuple[Path, TTSResult]:
        """Generate and save to file. Returns (path, result)."""
        result = self.generate(text, voice=voice, lang=lang, pause=pause, preprocess=preprocess)
        output_path = Path(output_path)
        sf.write(str(output_path), result.audio, result.sample_rate, format=fmt)
        return output_path, result

    def get_voices(self) -> list[str]:
        """List available voice names."""
        kokoro = self._load()
        return kokoro.get_voices()


def _make_silence(duration: float, variance: float, rng: np.random.Generator) -> np.ndarray:
    """Create a silence array with random jitter."""
    actual = max(0.05, duration + rng.uniform(-variance, variance))
    return np.zeros(int(actual * SAMPLE_RATE), dtype=np.float32)
