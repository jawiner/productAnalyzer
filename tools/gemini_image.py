"""Make (or edit) one image with Google's Gemini image models and save it as a PNG.

Uses generateContent (POST /v1beta/models/<model>:generateContent) with responseModalities IMAGE.
Pass --ref to hand the model one or more existing images to edit or to match.

Needs one line in the WAT root .env:
    GEMINI_API_KEY=...
The key goes only into the request header. It is never printed or written anywhere.
On the free tier, image models may have no quota at all (HTTP 429 "limit: 0"); with billing on,
every call is charged per image, so don't loop on it.

Usage:
    python tools/gemini_image.py --prompt "a cat" --out .tmp/cat.png
    python tools/gemini_image.py --prompt-file shot.txt --out out.png --aspect 16:9 --size 2K
    python tools/gemini_image.py --prompt "remove the title" --ref in.png --out fixed.png
    python tools/gemini_image.py --check        # says whether GEMINI_API_KEY is set; no API call

Models (2026-11): gemini-3-pro-image (best text and detail), gemini-3.1-flash-image (faster,
cheaper), gemini-3.1-flash-lite-image, gemini-2.5-flash-image (no --size).
Aspect ratios: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9. Sizes: 1K, 2K, 4K.
"""

import argparse
import base64
import io
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3-pro-image"


def api_key() -> str:
    load_dotenv(ROOT / ".env", override=True)
    return os.getenv("GEMINI_API_KEY") or ""


def _find_image(node):
    """The last inline image anywhere in the answer, as (base64 data, mime type)."""
    found = None
    if isinstance(node, dict):
        blob = node.get("inlineData") or node.get("inline_data")
        if isinstance(blob, dict) and blob.get("data"):
            mime = blob.get("mimeType") or blob.get("mime_type") or ""
            if mime.startswith("image/"):
                found = (blob["data"], mime)
        for value in node.values():
            found = _find_image(value) or found
    elif isinstance(node, list):
        for value in node:
            found = _find_image(value) or found
    return found


def _find_text(node) -> str:
    if isinstance(node, dict):
        return " ".join(filter(None, [node.get("text") if isinstance(node.get("text"), str) else ""]
                               + [_find_text(v) for v in node.values() if isinstance(v, (dict, list))]))
    if isinstance(node, list):
        return " ".join(filter(None, (_find_text(v) for v in node)))
    return ""


def generate(prompt: str, refs: list[Path] | None = None, model: str = DEFAULT_MODEL,
             aspect: str | None = "16:9", size: str | None = None, timeout: int = 300) -> bytes:
    """One image call. Returns PNG bytes. Raises RuntimeError with the API's reason on failure."""
    key = api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in the WAT root .env")
    parts = [{"text": prompt}]
    for ref in refs or []:
        mime = mimetypes.guess_type(ref.name)[0] or "image/png"
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(ref.read_bytes()).decode()}})
    image_config = {}
    if aspect:
        image_config["aspectRatio"] = aspect
    if size:
        image_config["imageSize"] = size
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": image_config},
    }
    req = urllib.request.Request(
        ENDPOINT.format(model=model), data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:800]
        raise RuntimeError(f"Gemini image answered HTTP {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach Gemini image: {e.reason}") from None

    image = _find_image(data)
    if not image:
        reason = _find_text(data) or json.dumps(data, ensure_ascii=False)[:400]
        raise RuntimeError("Gemini returned no image. It said: " + reason[:600])
    raw = base64.b64decode(image[0])
    if image[1] == "image/png":
        return raw
    buf = io.BytesIO()
    Image.open(io.BytesIO(raw)).save(buf, "PNG")
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description="Gemini image: prompt (+ optional reference images) to a PNG.")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--prompt", help="what to draw")
    src.add_argument("--prompt-file", type=Path, help="a UTF-8 file with the prompt")
    ap.add_argument("--ref", type=Path, action="append", default=[], help="an image to edit or match (repeatable)")
    ap.add_argument("--out", type=Path, help="where to write the PNG")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--aspect", default="16:9", help="aspect ratio, or 'none' to leave it to the model")
    ap.add_argument("--size", help="1K, 2K or 4K (not for gemini-2.5-flash-image)")
    ap.add_argument("--check", action="store_true", help="only say whether GEMINI_API_KEY is set")
    args = ap.parse_args()

    if args.check:
        print("GEMINI_API_KEY is set." if api_key() else "GEMINI_API_KEY is NOT set in the WAT root .env.")
        return 0 if api_key() else 1
    prompt = args.prompt if args.prompt is not None else (args.prompt_file.read_text(encoding="utf-8") if args.prompt_file else None)
    if not prompt or not args.out:
        ap.error("--prompt or --prompt-file, and --out, are required (or use --check)")
    aspect = None if args.aspect == "none" else args.aspect
    try:
        png = generate(prompt.strip(), refs=args.ref, model=args.model, aspect=aspect, size=args.size)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(png)
    with Image.open(io.BytesIO(png)) as im:
        w, h = im.size
    print(f"Wrote {args.out} ({w}x{h}, {args.model})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
