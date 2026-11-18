"""Hand a video made in a Claude session (an AI-footage remake) to the content engine.

The owner picked "With AI footage" for a remake, so it was made in a session (Higgsfield clips,
after the owner saw the credit cost) instead of by the video PC. This puts it into the usual
pipeline: the idea is approved, the files are uploaded, and the video goes to Telegram for
approval and then posting, exactly like one the PC made.

  python tools/content_studio/deliver_video.py --list
  python tools/content_studio/deliver_video.py --footage <idea id> <clip.mp4> [<clip.mp4> ...]
      the usual way: the AI clips go to the video PC, which assembles the whole remake
      (kept clip, AI presenter, app screens, end card) like any video and sends it for approval.
      Each clip must be a vertical (about 9:16) mp4, 2 to 30 s long, with sound (add --silent-ok
      for b-roll without speech). The idea must be waiting for AI footage. Clips from an earlier
      try are cleared first, so only these go to the PC.
  python tools/content_studio/deliver_video.py --check-clips <clip.mp4> [...] [--silent-ok]
      only the clip check, offline: nothing is sent or copied
  python tools/content_studio/deliver_video.py --idea <idea id> --project <folder with out/>
      a video finished entirely in the session

The project folder needs out/final.mp4 (1080x1920, with sound), out/review.mp4 and out/caption.txt;
out/cover.jpg is optional. They are checked before anything changes. Uses the worker's key from
tools/content_studio/.env (never printed).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import playbook
from worker import Engine, check_deliverables, ffprobe, load_env, log, put_file

# An AI clip the PC can build a vertical remake from.
CLIP_MIN_S, CLIP_MAX_S = 2.0, 30.0
CLIP_RATIO = (1.6, 1.95)  # height / width; 9:16 is 1.78


def check_clip(path: Path, need_audio: bool = True) -> list[str]:
    """What is wrong with one AI clip (an empty list when it is fine). Offline, uses ffprobe."""
    if not path.is_file():
        return [f"{path}: not found"]
    if path.suffix.lower() != ".mp4":
        return [f"{path.name}: not an .mp4"]
    try:
        info = ffprobe(path)
    except (ValueError, OSError) as e:
        return [f"{path.name}: ffprobe could not read it ({e.__class__.__name__})"]
    w, h, d = info.get("width"), info.get("height"), info.get("duration") or 0
    if not w or not h:
        return [f"{path.name}: no video track"]
    problems = []
    if not CLIP_RATIO[0] <= h / w <= CLIP_RATIO[1]:
        problems.append(f"{path.name}: {w}x{h} is not vertical 9:16 (wrong aspect ratio)")
    if not CLIP_MIN_S <= d <= CLIP_MAX_S:
        problems.append(f"{path.name}: {d:.1f} s long, expected {CLIP_MIN_S:.0f} to {CLIP_MAX_S:.0f} s")
    if need_audio and not info.get("audio"):
        problems.append(f"{path.name}: no sound track (pass --silent-ok if it is b-roll without speech)")
    return problems


def check_clips(clips: list[Path], need_audio: bool = True) -> list[str]:
    return [p for c in clips for p in check_clip(c, need_audio)]


def stage_footage(engine, idea_id: str, clips: list[Path], target_root: Path, need_audio: bool = True) -> tuple[bool, str]:
    """Check the clips, check the idea waits for footage, replace any earlier clips, then queue it.

    Nothing is copied or queued unless every check passes."""
    problems = check_clips(clips, need_audio)
    if problems:
        return False, "Not queued, fix these first:\n- " + "\n- ".join(problems)
    waiting = engine.call("ai_waiting").get("ideas") or []
    if not any(i.get("id") == idea_id for i in waiting):
        return False, (f"Not queued: idea {idea_id} isn't waiting for AI footage. Tap 🎥 With AI footage on its card "
                       "in @MashtechVideoBot first, then check it shows up in --list.")
    target = target_root / idea_id
    target.mkdir(parents=True, exist_ok=True)
    old = sorted(target.glob("*.mp4"))
    for f in old:
        f.unlink()  # our own copies from an earlier try; the PC would use every mp4 in this folder
    for n, c in enumerate(clips, 1):
        shutil.copy2(c, target / f"ai-{n}.mp4")
    engine.call("queue_ai_remake", idea_id=idea_id)
    cleared = f" (replaced {len(old)} older clip(s))" if old else ""
    return True, f"Queued: {len(clips)} AI clip(s) in {target}{cleared}. The video PC assembles the remake and sends it to Telegram."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--idea")
    ap.add_argument("--project")
    ap.add_argument("--list", action="store_true", help="remakes waiting for AI footage")
    ap.add_argument("--show", metavar="IDEA_ID", help="everything about one of them, as JSON (beats, format, brand)")
    ap.add_argument("--footage", nargs="+", metavar="ARG", help="IDEA_ID then the AI clips: the PC assembles the remake")
    ap.add_argument("--check-clips", nargs="+", metavar="CLIP", help="only check clips (offline), send nothing")
    ap.add_argument("--silent-ok", action="store_true", help="clips may have no sound (b-roll without speech)")
    args = ap.parse_args()

    if args.check_clips:
        problems = check_clips([Path(c) for c in args.check_clips], not args.silent_ok)
        print("Clips OK." if not problems else "Problems:\n- " + "\n- ".join(problems))
        return 1 if problems else 0

    if args.footage:
        if len(args.footage) < 2:
            ap.error("--footage needs the idea id and at least one clip")
        idea_id, clips = args.footage[0], [Path(c) for c in args.footage[1:]]
        problems = check_clips(clips, not args.silent_ok)  # offline, before any call
        if problems:
            print("Not queued, fix these first:\n- " + "\n- ".join(problems))
            return 1

    env = load_env()
    engine = Engine(env["CONTENT_ENGINE_URL"], env["CONTENT_WORKER_SECRET"])

    if args.show:
        idea = next((i for i in engine.call("ai_waiting").get("ideas") or [] if i["id"] == args.show), None)
        print(json.dumps(idea, ensure_ascii=False, indent=1) if idea else "That idea isn't waiting for AI footage.")
        return 0 if idea else 1

    if args.footage:
        ok, message = stage_footage(engine, idea_id, clips, playbook.AI_FOOTAGE, not args.silent_ok)
        print(message)
        if ok:
            log(f"footage queued for idea {idea_id}: {len(clips)} clip(s)")
        return 0 if ok else 1

    if args.list:
        waiting = engine.call("ai_waiting").get("ideas") or []
        for i in waiting:
            print(f"{i['id']}  {i['title']}  (remake of {i.get('reference') or 'an ad'})")
        if not waiting:
            print("No remake is waiting for AI footage.")
        return 0

    if not args.idea or not args.project:
        ap.error("--idea and --project are needed (or --list)")
    project = Path(args.project)
    meta, problems = check_deliverables(project)
    if problems:
        print("Not delivered, fix these first:\n- " + "\n- ".join(problems))
        return 1

    video = engine.call("adopt_idea", idea_id=args.idea)["video"]
    log(f"deliver {video['id']} for idea {args.idea} from {project}")
    urls = engine.call("upload_urls", video_id=video["id"])
    put_file(urls["final.mp4"]["url"], project / "out" / "final.mp4", "video/mp4")
    put_file(urls["review.mp4"]["url"], project / "out" / "review.mp4", "video/mp4")
    has_cover = (project / "out" / "cover.jpg").exists()
    if has_cover:
        put_file(urls["cover.jpg"]["url"], project / "out" / "cover.jpg", "image/jpeg")
    engine.call("done", video_id=video["id"], caption=meta["caption"], duration_s=meta["duration_s"], project_dir=str(project),
                has_cover=has_cover, report={"summary": "Made with AI footage in a Claude session.", "playbook_used": [], "route": "ai_footage"})
    print(f"Delivered: video {video['id']} ({meta['duration_s']} s) is on its way to Telegram for approval.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
