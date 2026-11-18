"""Hand a video made in a Claude session (an AI-footage remake) to the content engine.

The owner picked "With AI footage" for a remake, so it was made in a session (Higgsfield clips,
after the owner saw the credit cost) instead of by the video PC. This puts it into the usual
pipeline: the idea is approved, the files are uploaded, and the video goes to Telegram for
approval and then posting, exactly like one the PC made.

  python tools/content_studio/deliver_video.py --list
  python tools/content_studio/deliver_video.py --idea <idea id> --project <folder with out/>

The project folder needs out/final.mp4 (1080x1920, with sound), out/review.mp4 and out/caption.txt;
out/cover.jpg is optional. They are checked before anything changes. Uses the worker's key from
tools/content_studio/.env (never printed).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from worker import Engine, check_deliverables, load_env, log, put_file


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--idea")
    ap.add_argument("--project")
    ap.add_argument("--list", action="store_true", help="remakes waiting for AI footage")
    ap.add_argument("--show", metavar="IDEA_ID", help="everything about one of them, as JSON (beats, format, brand)")
    args = ap.parse_args()
    env = load_env()
    engine = Engine(env["CONTENT_ENGINE_URL"], env["CONTENT_WORKER_SECRET"])

    if args.show:
        idea = next((i for i in engine.call("ai_waiting").get("ideas") or [] if i["id"] == args.show), None)
        print(json.dumps(idea, ensure_ascii=False, indent=1) if idea else "That idea isn't waiting for AI footage.")
        return 0 if idea else 1

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
