#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AssemblyAI Transcription Service Template
Source: plugin-premierepro (Killian)

Usage:
    from services.transcription import transcribe_audio
    result = await transcribe_audio("audio.wav", "fr")

Requires:
    pip install assemblyai
    ENV: ASSEMBLYAI_API_KEY

Features:
    - Async transcription (run_in_thread for non-blocking)
    - Word-level timestamps with confidence scores
    - Silence gap detection (disfluency markers)
    - Configurable language and speech model (universal-3-pro)
    - Structured output with segments, words, speakers
"""

import asyncio
import logging
import time
import assemblyai as aai
import uuid
import string
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def configure_assemblyai(api_key: str):
    """Configure AssemblyAI with API key"""
    aai.settings.api_key = api_key


async def transcribe_audio(
    audio_path: str,
    language: str = "fr",
    api_key: str | None = None,
    speaker_id: str | None = None,
    speaker_name: str | None = None,
) -> Dict[str, Any]:
    """
    Transcribe audio file using AssemblyAI

    Args:
        audio_path: Path to audio file (.wav, .mp3, etc.)
        language: Language code (fr, en, es, etc.)
        api_key: AssemblyAI API key (or set via configure_assemblyai)
        speaker_id: UUID for the speaker (auto-generated if None)
        speaker_name: Display name for the speaker

    Returns:
        {
            "text": "Full transcription text",
            "segments": [
                {
                    "start": 0.031,        # seconds
                    "duration": 3.14,       # seconds
                    "speaker": "speaker-uuid",
                    "words": [
                        {
                            "text": "Bonjour",
                            "start": 0.031,     # seconds
                            "duration": 0.5,     # seconds
                            "confidence": 0.98,
                            "eos": False,        # end of sentence
                            "type": "word"       # "word" or "punctuation"
                        }
                    ]
                }
            ],
            "speakers": [{"id": "uuid", "name": "Speaker 1"}],
            "duration": 121.69,
            "word_count": 374,
            "language_detected": "fr"
        }

    Raises:
        FileNotFoundError: Audio file not found
        RuntimeError: Transcription failed
    """
    audio_file = Path(audio_path)
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if api_key:
        configure_assemblyai(api_key)

    # Configure transcription
    config = aai.TranscriptionConfig(
        speech_models=["universal-3-pro"],
        language_code=language
    )

    try:
        logger.info(f"[ASSEMBLYAI] Uploading {audio_path}...")
        t0 = time.time()
        transcriber = aai.Transcriber(config=config)
        transcript = await asyncio.to_thread(transcriber.transcribe, str(audio_file))
        logger.info(f"[ASSEMBLYAI] Response in {time.time()-t0:.2f}s | status={transcript.status}")

        if transcript.status == "error":
            raise RuntimeError(f"Transcription failed: {transcript.error}")

        # Convert to structured format
        default_speaker_id = speaker_id or str(uuid.uuid4())
        language_code = f"{language}-{language}" if language else "fr-fr"

        GAP_THRESHOLD_MS = 300
        segments = []
        current_segment = None
        segment_words = []
        words = transcript.words or []

        for idx, word in enumerate(words):
            if current_segment is None:
                current_segment = {
                    "duration": 0,
                    "language": language_code,
                    "speaker": default_speaker_id,
                    "start": word.start / 1000.0,
                    "words": []
                }

            word_duration = (word.end - word.start) / 1000.0
            is_sentence_end = word.text.strip().endswith(('.', '!', '?', ';'))
            is_punctuation = word.text.strip() in string.punctuation
            word_type = "punctuation" if is_punctuation else "word"

            # Disfluency marker for silence gaps
            if idx > 0:
                prev_end = words[idx - 1].end
                gap_ms = word.start - prev_end
                if gap_ms >= GAP_THRESHOLD_MS:
                    segment_words.append({
                        "confidence": 1.0,
                        "duration": gap_ms / 1000.0,
                        "eos": False,
                        "start": prev_end / 1000.0,
                        "tags": ["disfluency"],
                        "text": "",
                        "type": "word"
                    })

            segment_words.append({
                "confidence": word.confidence if hasattr(word, 'confidence') else 1.0,
                "duration": word_duration,
                "eos": is_sentence_end,
                "start": word.start / 1000.0,
                "tags": [],
                "text": word.text,
                "type": word_type
            })

            segment_duration = (word.end / 1000.0) - current_segment["start"]

            if is_sentence_end or segment_duration > 10.0:
                current_segment["words"] = segment_words
                current_segment["duration"] = segment_duration
                segments.append(current_segment)
                current_segment = None
                segment_words = []

        if current_segment is not None and segment_words:
            last_word = words[-1]
            current_segment["words"] = segment_words
            current_segment["duration"] = (last_word.end / 1000.0) - current_segment["start"]
            segments.append(current_segment)

        word_count = len(words)
        duration = words[-1].end / 1000.0 if words else 0.0

        return {
            "text": transcript.text,
            "segments": segments,
            "speakers": [{"id": default_speaker_id, "name": speaker_name or "Speaker 1"}],
            "duration": duration,
            "word_count": word_count,
            "language_detected": transcript.language_code if hasattr(transcript, 'language_code') else language
        }

    except Exception as e:
        raise RuntimeError(f"Transcription service error: {str(e)}")
