"""Turn text into speech with Google's Gemini TTS and save it as a WAV file.

Uses the Interactions API (POST /v1beta/interactions, the documented way as of 2026-11) with a
prebuilt voice. Hebrew is supported by gemini-3.8-flash-tts. The answer is a 24 kHz mono 16-bit
WAV; a headerless PCM answer is wrapped in a WAV header here.

Needs one line in the WAT root .env:
    GEMINI_API_KEY=...
The key goes only into the request header. It is never printed or written anywhere.
Every call is billed to that key (TTS output is charged per audio token), so don't loop on it.

Usage:
    python tools/gemini_tts.py --text "שלום, זו בדיקה." --out .tmp/hello.wav
    python tools/gemini_tts.py --text-file script.txt --out out.wav --voice Sulafat \
        --style "warm, confident, natural pace"
    python tools/gemini_tts.py --check        # says whether GEMINI_API_KEY is set; no API call

Voices: Zephyr (bright), Puck (upbeat), Charon (informative), Kore (firm), Fenrir (excitable),
Leda (youthful), Orus (firm), Aoede (breezy), Callirrhoe (easy-going), Autonoe (bright),
Enceladus (breathy), Iapetus (clear), Umbriel (easy-going), Algieba (smooth), Despina (smooth),
Erinome (clear), Algenib (gravelly), Rasalgethi (informative), Laomedeia (upbeat),
Achernar (soft), Alnilam (firm), Schedar (even), Gacrux (mature), Pulcherrima (forward),
Achird (friendly), Zubenelgenubi (casual), Vindemiatrix (gentle), Sadachbia (lively),
Sadaltager (knowledgeable), Sulafat (warm).
The text is read verbatim: put delivery directions in --style, not in the text. Inline tags such
as <short pause> are allowed in the text.
"""

import argparse
import base64
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_MODEL = "gemini-3.8-flash-tts"
DEFAULT_VOICE = "Sulafat"


def api_key() -> str:
    load_dotenv(ROOT / ".env", override=True)
    return os.getenv("GEMINI_API_KEY") or ""


def pcm_to_wav(pcm: bytes, rate: int = 24000, channels: int = 1) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def _find_audio(node):
    """The last audio part anywhere in the answer, as (base64 data, mime type)."""
    found = None
    if isinstance(node, dict):
        if node.get("type") == "audio" and node.get("data"):
            found = (node["data"], node.get("mime_type") or node.get("mimeType") or "")
        for value in node.values():
            found = _find_audio(value) or found
    elif isinstance(node, list):
        for value in node:
            found = _find_audio(value) or found
    return found


def synthesize(text: str, voice: str = DEFAULT_VOICE, style: str | None = None,
               model: str = DEFAULT_MODEL, timeout: int = 300) -> bytes:
    """One TTS call. Returns WAV bytes. Raises RuntimeError with the API's reason on failure."""
    key = api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in the WAT root .env")
    content = {"type": "text", "text": text}
    if style:
        content["annotations"] = [{"type": "speech_metadata", "style": style}]
    body = {
        "model": model,
        "input": [{"type": "user_input", "content": [content]}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:800]
        raise RuntimeError(f"Gemini TTS answered HTTP {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach Gemini TTS: {e.reason}") from None

    audio = _find_audio(data)
    if not audio:
        raise RuntimeError("Gemini TTS returned no audio. Answer started: " + json.dumps(data, ensure_ascii=False)[:400])
    raw = base64.b64decode(audio[0])
    if raw[:4] == b"RIFF":
        return raw
    rate = int(m.group(1)) if (m := re.search(r"rate=(\d+)", audio[1])) else 24000
    return pcm_to_wav(raw, rate)


def main() -> int:
    ap = argparse.ArgumentParser(description="Gemini TTS: text to a WAV file.")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--text", help="the words to speak")
    src.add_argument("--text-file", type=Path, help="a UTF-8 file with the words to speak")
    ap.add_argument("--out", type=Path, help="where to write the WAV")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--style", help="delivery direction, e.g. 'warm, unhurried, conversational'")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--check", action="store_true", help="only say whether GEMINI_API_KEY is set")
    args = ap.parse_args()

    if args.check:
        print("GEMINI_API_KEY is set." if api_key() else "GEMINI_API_KEY is NOT set in the WAT root .env.")
        return 0 if api_key() else 1
    text = args.text if args.text is not None else (args.text_file.read_text(encoding="utf-8") if args.text_file else None)
    if not text or not args.out:
        ap.error("--text or --text-file, and --out, are required (or use --check)")
    try:
        wav = synthesize(text.strip(), voice=args.voice, style=args.style, model=args.model)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(wav)
    with wave.open(io.BytesIO(wav)) as w:
        seconds = w.getnframes() / w.getframerate()
    print(f"Wrote {args.out} ({seconds:.2f} s, voice {args.voice}, {args.model})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
