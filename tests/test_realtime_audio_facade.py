"""Tests for the OpenAI /v1/audio/* pure helpers (stdlib-only; no [realtime] extra).

The FastAPI routes (model_gear/realtime/app.py) need fastapi/httpx and are not
installed offline; the logic they delegate to lives here and is tested directly.
"""

from __future__ import annotations

import io
import wave

import pytest

from model_gear.realtime.audio_facade import (
    SUPPORTED_FORMATS,
    SpeechRequestError,
    parse_speech_request,
    pcm_to_container,
)

# --- pcm_to_container -----------------------------------------------------


def test_pcm_passthrough_is_untouched() -> None:
    data, media_type = pcm_to_container(b"\x01\x02\x03\x04", "pcm")
    assert data == b"\x01\x02\x03\x04"
    assert media_type == "audio/pcm"


def test_wav_wraps_pcm_in_a_self_describing_container() -> None:
    pcm = b"\x00\x00\x10\x20" * 50
    data, media_type = pcm_to_container(pcm, "wav", rate=22050)
    assert media_type == "audio/wav"
    with wave.open(io.BytesIO(data)) as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2  # 16-bit
        assert wf.getframerate() == 22050
        assert wf.readframes(wf.getnframes()) == pcm


def test_unsupported_container_format_raises() -> None:
    with pytest.raises(SpeechRequestError):
        pcm_to_container(b"\x00\x00", "mp3")


def test_supported_formats_are_wav_and_pcm() -> None:
    assert set(SUPPORTED_FORMATS) == {"wav", "pcm"}


# --- parse_speech_request -------------------------------------------------


def test_minimal_request_defaults_to_wav() -> None:
    p = parse_speech_request({"input": "Reachy is online."})
    assert p.input == "Reachy is online."
    assert p.response_format == "wav"  # default (OpenAI default mp3 isn't encodable yet)
    assert p.voice is None
    assert p.speed is None


def test_voice_format_and_speed_multiplier() -> None:
    p = parse_speech_request(
        {"input": "hi", "voice": "alloy", "response_format": "PCM", "speed": 1.25}
    )
    assert p.voice == "alloy"
    assert p.response_format == "pcm"  # lower-cased
    assert p.speed == 125  # OpenAI 1.25x → Magpie percentage


def test_missing_input_is_rejected() -> None:
    with pytest.raises(SpeechRequestError):
        parse_speech_request({"voice": "alloy"})


def test_blank_input_is_rejected() -> None:
    with pytest.raises(SpeechRequestError):
        parse_speech_request({"input": "   "})


def test_unsupported_response_format_is_rejected_early() -> None:
    with pytest.raises(SpeechRequestError):
        parse_speech_request({"input": "hi", "response_format": "mp3"})


def test_non_object_body_is_rejected() -> None:
    with pytest.raises(SpeechRequestError):
        parse_speech_request(["not", "a", "dict"])


def test_non_numeric_speed_is_rejected() -> None:
    with pytest.raises(SpeechRequestError):
        parse_speech_request({"input": "hi", "speed": "fast"})
