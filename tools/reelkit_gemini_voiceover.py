"""Record a Reelkit project's narration with Gemini TTS instead of Reelkit's own voices.

It writes exactly what `reelkit assets voiceover` writes: one audio file per scene
(assets/vo-<scene>.mp3) and assets/voiceovers.json with each scene's length and word timings.
`reelkit check`, `preview` and `render` then treat the takes like Reelkit recordings.

How:
1. The whole script is spoken in ONE Gemini call (scenes joined by line breaks), so the voice,
   pace and loudness stay the same from scene to scene. The take is kept in assets/voice-takes/.
2. The take is loudness-normalised (-16 LUFS) and resampled to 48 kHz mono.
3. A local speech model (faster-whisper, ivrit-ai's Hebrew turbo model by default) times every
   word; its words are matched letter by letter to the plan's own words, so the timings carry
   the plan's spelling and `onWord(s, "...")` finds them. Words it could not match (a number
   spoken as words, a Latin name) get times spread between their neighbours. Word edges that
   drift into a pause are snapped to the pause measured in the sound (Whisper tends to start a
   word after a pause 0.2-0.3 s early, which would light its caption before it is heard).
4. The take is cut in the silence between scenes, each piece trimmed close to its words.
--scene re-records only those scenes, each in a call of its own (for fixing one line).

Settings live in <project>/gemini-voice.json (written with defaults on first run):
    {"voice": "Sulafat", "model": "gemini-3.8-flash-tts", "style": "...",
     "spoken": {"<sceneId>": "what the voice should say instead of the narration, e.g. with niqqud"}}
"spoken" changes only the sound; voiceovers.json keeps the plan's narration as its text, which is
what Reelkit compares to decide a recording is current.

plan.json must still name a voiceId from `reelkit assets voices` (plan check insists on one). It
is only a label here; the sound is Gemini's. Never run `reelkit assets voiceover --redo` on such a
project: it would replace the Gemini takes with Reelkit's voice. (Without --redo it skips them,
because each entry matches the plan.)

Each run makes one billed Gemini call per take (one for the whole script, or one per --scene).

Usage (with the speech venv, which has faster-whisper):
    .tmp/venv-speech/Scripts/python.exe tools/reelkit_gemini_voiceover.py --project <dir>
    ... --scene hook --scene close        # re-record only those scenes
    ... --record-only                     # record the whole take and stop
    ... --align-only                      # re-time and re-cut the newest take; no API call
"""

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gemini_tts import DEFAULT_MODEL, DEFAULT_VOICE, synthesize  # noqa: E402

PACE_SPEED = {"slow": 0.92, "normal": 1, "fast": 1.1}  # Reelkit's own values (pipeline/schema.ts)
PACE_STYLE = {"slow": "Speak slowly and calmly.", "normal": "", "fast": "Speak at a brisk, energetic pace."}
DEFAULT_STYLE = ("Warm, confident Israeli Hebrew narrator for a short product video aimed at film and TV "
                 "production teams. Natural and conversational, never salesy. Clear diction.")
ASR_MODEL = "ivrit-ai/whisper-large-v3-turbo-ct2"
LEAD_SEC = 0.06   # kept before a scene's first word
TAIL_SEC = 0.14   # kept after its last word
FINALS = str.maketrans("ךםןףץ", "כמנפצ")


def run(cmd: list[str]) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {out.stderr.strip()[-600:]}")
    return out.stdout + out.stderr


def duration(path: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).strip())


def norm_char(ch: str) -> str:
    """A letter as compared between the script and the transcript: Hebrew letters without
    points and with final forms folded, Latin letters lower-cased, digits; everything else dropped."""
    ch = ch.translate(FINALS)
    if "א" <= ch <= "ת" or ch.isdigit():
        return ch
    if ch.isascii() and ch.isalpha():
        return ch.lower()
    return ""


def norm_word(word: str) -> str:
    return "".join(norm_char(c) for c in unicodedata.normalize("NFD", word))


def script_words(text: str) -> list[str]:
    """The narration split as Reelkit splits it: on spaces, punctuation kept on its word."""
    return [w for w in re.split(r"\s+", text.strip()) if w]


def transcribe(wav: Path, prompt: str, model_name: str) -> list[dict]:
    import numpy as np
    from faster_whisper import WhisperModel  # only in the speech venv

    # Decode with ffmpeg (16 kHz mono float) and hand the samples over: faster-whisper's own decoder
    # (PyAV) breaks when the installed av version differs from the one it was written for.
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio, language="he", word_timestamps=True, beam_size=5,
                                   initial_prompt=prompt, vad_filter=False, condition_on_previous_text=False)
    words = []
    for seg in segments:
        for w in seg.words or []:
            words.append({"word": w.word.strip(), "start": float(w.start), "end": float(w.end)})
    return words


def silences(wav: Path, noise_db: int = -38, min_sec: float = 0.1) -> list[tuple[float, float]]:
    """The pauses in a take, measured from its sound (ffmpeg silencedetect)."""
    log = run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af", f"silencedetect=noise={noise_db}dB:d={min_sec}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    if len(ends) < len(starts):
        ends.append(duration(wav))
    return list(zip(starts, ends))


def snap_to_silences(per_scene: list[list[dict]], pauses: list[tuple[float, float]]) -> None:
    """Whisper's word edges drift into pauses (a word after a pause often 'starts' 0.2-0.3 s early).
    A word that starts inside a measured pause starts when the pause ends; one that ends inside a
    pause ends when it begins. Captions then never light before the word is heard."""
    words = [w for scene in per_scene for w in scene]
    for a, b in pauses:
        for w in words:
            if a <= w["startSec"] < b and w["endSec"] > b:
                w["startSec"] = b
            if a < w["endSec"] <= b and w["startSec"] < a:
                w["endSec"] = a
            # A whole sentence pause inside one word (a word whose times were spread, not heard):
            # the word belongs to the side of the pause where most of it lies.
            if b - a >= 0.2 and w["startSec"] < a and w["endSec"] > b:
                before, after = a - w["startSec"], w["endSec"] - b
                if before < 0.15 and after >= before:
                    w["startSec"] = b
                elif after < 0.15:
                    w["endSec"] = a
    for prev, w in zip(words, words[1:]):
        if w["startSec"] < prev["endSec"]:
            w["startSec"] = prev["endSec"]
        w["endSec"] = max(w["endSec"], w["startSec"] + 0.08)


def align(scenes_words: list[list[str]], heard: list[dict]) -> tuple[list[list[dict]], list[float]]:
    """Give every script word a start and end in the take. Returns timings per scene and the share
    of each scene's letters that were matched to the transcript."""
    flat = [(si, w) for si, ws in enumerate(scenes_words) for w in ws]
    s_chars, s_owner = [], []
    for k, (_, w) in enumerate(flat):
        for c in norm_word(w):
            s_chars.append(c)
            s_owner.append(k)
    h_chars, h_time = [], []
    for hw in heard:
        letters = norm_word(hw["word"])
        n = len(letters)
        for j, c in enumerate(letters):
            t0 = hw["start"] + (hw["end"] - hw["start"]) * j / n
            t1 = hw["start"] + (hw["end"] - hw["start"]) * (j + 1) / n
            h_chars.append(c)
            h_time.append((t0, t1))
    match = {}
    for a, b, size in difflib.SequenceMatcher(None, s_chars, h_chars, autojunk=False).get_matching_blocks():
        for i in range(size):
            match[a + i] = b + i

    starts, ends = [None] * len(flat), [None] * len(flat)
    for k in range(len(flat)):
        idx = [i for i, o in enumerate(s_owner) if o == k and i in match]
        if idx:
            starts[k] = h_time[match[idx[0]]][0]
            ends[k] = h_time[match[idx[-1]]][1]
    # Unmatched words: spread them, by letter count, between the matched neighbours.
    k = 0
    end_of_take = heard[-1]["end"] if heard else 0.0
    while k < len(flat):
        if starts[k] is not None:
            k += 1
            continue
        j = k
        while j < len(flat) and starts[j] is None:
            j += 1
        lo = ends[k - 1] if k > 0 else (heard[0]["start"] if heard else 0.0)
        hi = starts[j] if j < len(flat) else end_of_take
        sizes = [max(1, len(norm_word(flat[m][1]))) for m in range(k, j)]
        total, t = sum(sizes), lo
        for m, size in zip(range(k, j), sizes):
            span = (hi - lo) * size / total
            starts[m], ends[m] = t, t + span
            t += span
        k = j
    # Keep them in order and never shorter than 80 ms.
    for k in range(len(flat)):
        if k and starts[k] < ends[k - 1]:
            starts[k] = ends[k - 1]
        ends[k] = max(ends[k], starts[k] + 0.08)

    per_scene, cover = [[] for _ in scenes_words], []
    for k, (si, w) in enumerate(flat):
        per_scene[si].append({"word": w, "startSec": starts[k], "endSec": ends[k]})
    for si in range(len(scenes_words)):
        own = [i for i, o in enumerate(s_owner) if flat[o][0] == si]
        cover.append(sum(1 for i in own if i in match) / max(1, len(own)))
    return per_scene, cover


def cut(src: Path, start: float, end: float, out: Path) -> float:
    length = end - start
    fade = f"afade=t=in:d=0.012,afade=t=out:st={max(0.0, length - 0.03):.3f}:d=0.03"
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(src),
         "-af", fade, "-ar", "48000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "192k", str(out)])
    return duration(out)


def normalise(src: Path, out: Path) -> None:
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(out)])


def record_and_cut(project: Path, plan: dict, cfg: dict, scenes: list[dict], take: Path | None,
                   asr_model: str, done: dict, record_only: bool = False) -> list[str]:
    """One take for the given scenes (record it unless a take is given), timed and cut per scene."""
    takes = project / "assets" / "voice-takes"
    takes.mkdir(parents=True, exist_ok=True)
    spoken = [cfg.get("spoken", {}).get(s["id"]) or s["narration"] for s in scenes]
    if take is None:
        style = " ".join(x for x in [cfg.get("style") or DEFAULT_STYLE, PACE_STYLE[plan.get("pace", "normal")]] if x)
        wav = synthesize("\n".join(spoken), voice=cfg.get("voice", DEFAULT_VOICE), style=style,
                         model=cfg.get("model", DEFAULT_MODEL))
        tag = scenes[0]["id"] if len(scenes) == 1 else "all"
        take = takes / f"take-{tag}-{time.strftime('%Y%m%d-%H%M%S')}.wav"
        take.write_bytes(wav)
        print(f"Recorded {take.name} with {cfg.get('voice', DEFAULT_VOICE)} ({cfg.get('model', DEFAULT_MODEL)}).")
    if record_only:
        return [f"Take saved: assets/voice-takes/{take.name}. Time and cut it with --align-only."]
    norm = take.with_suffix(".norm.wav")
    normalise(take, norm)
    # The transcript is cached beside the take (per model), so re-cutting doesn't re-run the model.
    cache = take.with_name(f"{take.stem}.words-{re.sub(r'[^A-Za-z0-9]+', '_', asr_model)}.json")
    if cache.exists():
        heard = json.loads(cache.read_text(encoding="utf-8"))
    else:
        heard = transcribe(norm, " ".join(s["narration"] for s in scenes), asr_model)
        cache.write_text(json.dumps(heard, ensure_ascii=False, indent=1), encoding="utf-8")
    if not heard:
        raise RuntimeError(f"The speech model heard no words in {take.name}.")
    timed, cover = align([script_words(s["narration"]) for s in scenes], heard)
    snap_to_silences(timed, silences(norm))
    take_len = duration(norm)

    notes = []
    for i, s in enumerate(scenes):
        words = timed[i]
        first, last = words[0]["startSec"], words[-1]["endSec"]
        start = max(0.0, first - LEAD_SEC)
        end = min(take_len, last + TAIL_SEC)
        if i > 0:
            start = max(start, (timed[i - 1][-1]["endSec"] + first) / 2)
        if i + 1 < len(scenes):
            end = min(end, (last + timed[i + 1][0]["startSec"]) / 2)
        key = f"assets/vo-{s['id']}.mp3"
        length = cut(norm, start, end, project / key)
        shifted = [{"word": w["word"], "startSec": round(w["startSec"] - start, 3),
                    "endSec": round(min(w["endSec"] - start, length), 3)} for w in words]
        entry = {"key": key, "durationSec": round(length, 3), "words": shifted, "text": s["narration"],
                 "speed": PACE_SPEED[plan.get("pace", "normal")], "source": f"gemini:{cfg.get('voice', DEFAULT_VOICE)}",
                 "take": take.name}
        if plan.get("voiceId"):
            entry["voiceId"] = plan["voiceId"]
        done[s["id"]] = entry
        flag = "" if cover[i] >= 0.7 else "  <- check this scene's timings by ear"
        notes.append(f"{s['id']}: {length:.2f}s, {len(words)} words, {cover[i]:.0%} of letters matched{flag}")
    return notes


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # Hebrew in messages; the Windows console default is cp1252
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Record a Reelkit project's narration with Gemini TTS.")
    ap.add_argument("--project", type=Path, required=True, help="the Reelkit project folder (has plan.json)")
    ap.add_argument("--scene", action="append", default=[], help="re-record only this scene (repeatable)")
    ap.add_argument("--align-only", action="store_true", help="re-time and re-cut the newest whole take")
    ap.add_argument("--record-only", action="store_true", help="record the whole take and stop (no timing, no cutting)")
    ap.add_argument("--asr-model", default=ASR_MODEL, help=f"faster-whisper model for word times (default {ASR_MODEL})")
    args = ap.parse_args()

    project = args.project.resolve()
    plan = json.loads((project / "plan.json").read_text(encoding="utf-8"))
    if plan.get("voice") == "none":
        print("This plan has no voice (voice is \"none\"). Nothing to record.")
        return 0
    if not shutil.which("ffmpeg"):
        print("ffmpeg is not on the path.", file=sys.stderr)
        return 1
    cfg_path = project / "gemini-voice.json"
    if not cfg_path.exists():
        cfg_path.write_text(json.dumps({"voice": DEFAULT_VOICE, "model": DEFAULT_MODEL, "style": DEFAULT_STYLE, "spoken": {}},
                                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    vo_path = project / "assets" / "voiceovers.json"
    done = json.loads(vo_path.read_text(encoding="utf-8")) if vo_path.exists() else {}
    by_id = {s["id"]: s for s in plan["scenes"]}
    unknown = [x for x in args.scene if x not in by_id]
    if unknown:
        print(f"No scene {', '.join(unknown)}. The scenes are: {', '.join(by_id)}.", file=sys.stderr)
        return 1

    try:
        if args.scene:
            notes = []
            for sid in args.scene:
                notes += record_and_cut(project, plan, cfg, [by_id[sid]], None, args.asr_model, done)
        else:
            take = None
            if args.align_only:
                whole = sorted((project / "assets" / "voice-takes").glob("take-all-*[0-9].wav"))
                if not whole:
                    print("No whole take yet. Run without --align-only first.", file=sys.stderr)
                    return 1
                take = whole[-1]
            notes = record_and_cut(project, plan, cfg, plan["scenes"], take, args.asr_model, done, args.record_only)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1
    if args.record_only:
        print("\n".join(notes))
        return 0

    vo_path.write_text(json.dumps(done, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(notes))
    print(f"Wrote {vo_path.relative_to(project)}. Next: `reelkit check` (it builds manifest.json from these).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
