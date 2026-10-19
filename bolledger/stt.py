"""Whisper STT wrapper: faster-whisper, lazy model load, Hindi/Hinglish.

Model downloads once to ~/.cache/huggingface. 'base' is the default: fast enough
on CPU for short utterances; set BOLLEDGER_WHISPER_MODEL=small for better accuracy.
"""
import os

_model = None


def load_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        name = os.environ.get("BOLLEDGER_WHISPER_MODEL", "base")
        _model = WhisperModel(name, device="cpu", compute_type="int8")
    return _model


def available() -> bool:
    try:
        import faster_whisper  # noqa
        return True
    except ImportError:
        return False


def transcribe(wav_path: str, language: str = "hi") -> dict:
    """Transcribe a WAV file. Returns {text, language, duration_s}."""
    model = load_model()
    # Devanagari-biased prompt: without it the base model sometimes emits
    # Arabic-script Urdu for Hindi speech, which the NLU cannot read.
    segments, info = model.transcribe(
        wav_path, language=language, vad_filter=True,
        initial_prompt="रमेश को पांच सौ रुपये उधार दिया। आज का हिसाब दिखाओ।",
    )
    text = " ".join(s.text.strip() for s in segments).strip()
    return {"text": text, "language": info.language, "duration_s": round(info.duration, 2)}
