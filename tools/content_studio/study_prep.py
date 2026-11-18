"""Get a marketing video (or page) ready for Claude to study, for the video playbook.

Runs in the speech venv (faster-whisper + yt-dlp):
  .tmp/venv-speech/Scripts/python.exe -X utf8 tools/content_studio/study_prep.py --out DIR --url URL
  .tmp/venv-speech/Scripts/python.exe -X utf8 tools/content_studio/study_prep.py --out DIR --file video.mp4

Writes into DIR:
  media/video.mp4      the video (links), or the file given
  transcript.txt       what is said, "[m:ss] text" per line
  frames/t*.png        stills: every 0.5 s for the first 3 s (the hook), then spread over the rest
  packet.json          duration, language, words a minute, cut times and shot lengths, frame list,
                       title / creator / description from the site, or the text of a web page,
                       and {"error", "code"} when it can't (code: login, too_long, too_big,
                       unavailable, download)

Downloaded files are untrusted: they are only read as data (ffmpeg, whisper), never run.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

MAX_SECONDS = 60 * 60
MAX_BYTES = 400 * 1024 * 1024
HOOK_SECONDS = 3.0
MAX_FRAMES = 36
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
INFO_KEYS = ("title", "uploader", "channel", "creator", "description", "duration", "webpage_url", "extractor_key",
             "upload_date", "view_count", "like_count", "comment_count", "language", "tags")


def run(cmd: list[str], timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                          creationflags=NO_WINDOW)


class Failure(Exception):
    def __init__(self, message: str, code: str = "download"):
        super().__init__(message)
        self.code = code


# ---- Getting the video ----------------------------------------------------------------------

def classify(stderr: str) -> tuple[str, str]:
    text = stderr.lower()
    if any(k in text for k in ("login required", "log in", "sign in to confirm", "cookies", "private", "rate-limit", "empty media response")):
        return "login", "The site wants a login before it lets the video be downloaded."
    if "unsupported url" in text:
        return "unsupported", "Not a video page."
    if any(k in text for k in ("video unavailable", "has been removed", "not available", "http error 404")):
        return "unavailable", "The video isn't available (removed, private or region-locked)."
    if "file is larger than max-filesize" in text:
        return "too_big", "The video is over 400 MB."
    last = [l for l in stderr.strip().splitlines() if l.strip()][-1:] or ["yt-dlp failed"]
    return "download", last[0][-300:]


def download(url: str, media: Path) -> dict:
    media.mkdir(parents=True, exist_ok=True)
    base = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-progress", "--no-warnings", "--restrict-filenames",
            "--socket-timeout", "30", "--retries", "3"]
    probe = run(base + ["--dump-single-json", "--skip-download", url], timeout=180)
    if probe.returncode != 0:
        code, message = classify(probe.stderr)
        raise Failure(message, code)
    info = json.loads(probe.stdout or "{}")
    if info.get("is_live"):
        raise Failure("It's a live stream; send the recording once it's over.", "unavailable")
    duration = float(info.get("duration") or 0)
    if duration > MAX_SECONDS:
        raise Failure(f"It's {duration / 60:.0f} minutes long (the limit is 60).", "too_long")
    # "res" is the shorter side, so a vertical 720p video stays 720 wide (on-screen text
    # stays readable). Long videos get smaller pictures: the frames only need the gist.
    res = 720 if duration <= 300 else 480 if duration <= 1200 else 360
    got = run(base + ["-f", "bv*+ba/b", "-S", f"res:{res},ext:mp4:m4a", "--merge-output-format", "mp4",
                      "--max-filesize", str(MAX_BYTES), "-o", str(media / "video.%(ext)s"), url], timeout=1800)
    files = sorted(p for p in media.glob("video.*") if p.suffix in (".mp4", ".mkv", ".webm", ".mov"))
    if got.returncode != 0 or not files:
        code, message = classify(got.stderr or "no file")
        raise Failure(message, code)
    return {"video": str(files[0]), "info": {k: info.get(k) for k in INFO_KEYS if info.get(k) not in (None, "", [])}}


class _Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "aside"}

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.depth = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.depth += 1
        if tag == "title":
            self._in_title = True
        if tag in ("p", "br", "li", "h1", "h2", "h3", "h4", "div", "section", "article", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self.depth:
            self.parts.append(data)


def fetch_page(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) study-prep/1.0",
                                               "Accept-Language": "en,he;q=0.8"})
    with urllib.request.urlopen(req, timeout=40) as r:
        kind = r.headers.get("Content-Type", "")
        if "html" not in kind and "text" not in kind:
            raise Failure(f"The link is a {kind or 'file'}, not a page or a video.", "unsupported")
        raw = r.read(3_000_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
    parser = _Text()
    parser.feed(raw)
    text = html.unescape("".join(parser.parts))
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    if len(text) < 200:
        raise Failure("The page has almost no text the PC can read (it may need a login or JavaScript).", "unavailable")
    return {"title": html.unescape(parser.title.strip())[:200], "text": text[:60_000]}


# ---- Looking at it --------------------------------------------------------------------------

def probe(video: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(video)], 120)
    data = json.loads(out.stdout or "{}")
    streams = data.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    return {"duration": float(data.get("format", {}).get("duration") or 0), "width": v.get("width"), "height": v.get("height"),
            "has_video": bool(v), "has_audio": any(s.get("codec_type") == "audio" for s in streams)}


def cuts(video: Path, duration: float) -> list[float]:
    """Scene changes (hard cuts and big jumps), from the first 10 minutes."""
    limit = min(duration, 600)
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-t", f"{limit:.2f}", "-i", str(video), "-an",
               "-vf", "scale=320:-2,select='gt(scene,0.32)',showinfo", "-f", "null", "-"], 900)
    times = [float(m.group(1)) for m in re.finditer(r"pts_time:([0-9.]+)", out.stderr)]
    # Fades trigger several frames in a row: keep one per 0.25 s.
    kept: list[float] = []
    for t in times:
        if not kept or t - kept[-1] >= 0.25:
            kept.append(round(t, 2))
    return kept


def frame_times(duration: float, cut_times: list[float]) -> list[float]:
    hook = [round(x * 0.5, 2) for x in range(int(HOOK_SECONDS / 0.5) + 1) if x * 0.5 < duration]
    rest_slots = MAX_FRAMES - len(hook)
    span = max(0.0, duration - HOOK_SECONDS)
    if span <= 0:
        return hook
    step = max(2.0, span / rest_slots)
    times = [HOOK_SECONDS + step * (i + 1) for i in range(rest_slots) if HOOK_SECONDS + step * (i + 1) < duration - 0.2]
    # Just after a cut shows the new shot best; snap a slot to a nearby cut.
    snapped = []
    for t in times:
        near = [c for c in cut_times if abs(c - t) <= step / 2]
        snapped.append(round(min(near, key=lambda c: abs(c - t)) + 0.3, 2) if near else round(t, 2))
    return sorted(set(hook + snapped))[:MAX_FRAMES]


def grab_frames(video: Path, frames: Path, times: list[float]) -> list[dict]:
    frames.mkdir(parents=True, exist_ok=True)
    out = []
    for t in times:
        name = f"t{int(round(t * 100)):06d}.png"
        path = frames / name
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
             "-vf", "scale='min(540,iw)':-2", "-pix_fmt", "rgb24", str(path)], 120)
        if path.exists() and path.stat().st_size > 0:
            out.append({"t": t, "file": f"frames/{name}"})
    return out


def pcm(video: Path, seconds: float | None = None):
    import numpy as np
    cmd = ["ffmpeg", "-v", "error", "-i", str(video)]
    if seconds:
        cmd += ["-t", str(seconds)]
    raw = subprocess.run(cmd + ["-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, creationflags=NO_WINDOW).stdout
    return np.frombuffer(raw, dtype=np.float32)


def transcribe(video: Path) -> dict:
    from faster_whisper import WhisperModel
    audio = pcm(video)
    if audio.size < 16000:
        return {"language": None, "segments": []}
    # The multilingual model only tells the language; English gets the fast English model,
    # Hebrew the Hebrew one (the Hebrew model hears Hebrew in everything, so it can't decide).
    detector = WhisperModel("small", device="cpu", compute_type="int8")
    lang, prob, _ = detector.detect_language(audio[: 16000 * 30])
    if lang == "en":
        model = WhisperModel("small.en", device="cpu", compute_type="int8")
    elif lang == "he":
        model = WhisperModel("ivrit-ai/whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8")
    else:
        model = detector
    segments, _ = model.transcribe(audio, language=lang, vad_filter=True, beam_size=1)
    rows = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segments if s.text.strip()]
    return {"language": lang, "language_confidence": round(float(prob), 3), "segments": rows}


def clock(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


# ---- Main -----------------------------------------------------------------------------------

def prepare(out: Path, url: str | None, file: str | None) -> dict:
    packet: dict = {"url": url, "kind": "video"}
    media = out / "media"
    video: Path | None = None
    if file:
        video = Path(file)
    elif url:
        try:
            got = download(url, media)
            video = Path(got["video"])
            packet["site"] = got["info"]
        except Failure as e:
            if e.code != "unsupported":
                raise
            page = fetch_page(url)
            (out / "page.txt").write_text(page["text"], encoding="utf-8")
            packet.update({"kind": "page", "site": {"title": page["title"]}, "page_chars": len(page["text"])})
            return packet

    info = probe(video)
    if not info["has_video"] and not info["has_audio"]:
        raise Failure("The file has no picture or sound ffmpeg can read.", "unavailable")
    if info["duration"] > MAX_SECONDS:
        raise Failure(f"It's {info['duration'] / 60:.0f} minutes long (the limit is 60).", "too_long")
    duration = info["duration"]
    packet.update({"duration_s": round(duration, 2), "size": [info["width"], info["height"]], "has_audio": info["has_audio"]})

    cut_times = cuts(video, duration) if info["has_video"] else []
    shots = [b - a for a, b in zip([0.0] + cut_times, cut_times + [min(duration, 600)]) if b - a > 0]
    packet["cuts"] = {
        "times": cut_times[:300],
        "count": len(cut_times),
        "in_first_3s": sum(1 for c in cut_times if c <= HOOK_SECONDS),
        "average_shot_s": round(sum(shots) / len(shots), 2) if shots else None,
        "longest_shot_s": round(max(shots), 2) if shots else None,
        "note": "Scene changes found by ffmpeg (hard cuts and big jumps; slow zooms and text changes on a still background are not counted).",
    }
    packet["frames"] = grab_frames(video, out / "frames", frame_times(duration, cut_times)) if info["has_video"] else []

    speech = transcribe(video) if info["has_audio"] else {"language": None, "segments": []}
    words = sum(len(s["text"].split()) for s in speech["segments"])
    spoken = sum(s["end"] - s["start"] for s in speech["segments"])
    first = speech["segments"][0] if speech["segments"] else None
    packet["speech"] = {
        "language": speech.get("language"),
        "words": words,
        "words_per_minute": round(words / (duration / 60)) if duration > 5 and words else 0,
        "speaking_share": round(spoken / duration, 2) if duration else 0,
        "first_words_at_s": first["start"] if first else None,
        "first_line": first["text"] if first else None,
    }
    lines = [f"[{clock(s['start'])}] {s['text']}" for s in speech["segments"]]
    (out / "transcript.txt").write_text("\n".join(lines) if lines else "(no speech found)", encoding="utf-8")
    return packet


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--url")
    ap.add_argument("--file")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # A retry starts clean (a given --file may sit in media/, so that folder stays then).
    shutil.rmtree(out / "frames", ignore_errors=True)
    if not args.file:
        shutil.rmtree(out / "media", ignore_errors=True)
    try:
        packet = prepare(out, args.url, args.file)
    except Failure as e:
        packet = {"url": args.url, "error": str(e), "code": e.code}
    except Exception as e:  # noqa: BLE001 - reported to the owner, not raised
        packet = {"url": args.url, "error": f"{type(e).__name__}: {e}"[:500], "code": "prep"}
    (out / "packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: packet.get(k) for k in ("kind", "duration_s", "error", "code")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
