"""
Turns the raw per-project data collected by collect.py into a single
chronological timeline of meaningful accomplishments for the day.

Usage:
    python tools/daily_summary/format_report.py [--date YYYY-MM-DD]

Runs collect.py itself, then writes:
    .tmp/daily_summaries/<date>.md
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="YYYY-MM-DD, defaults to today")
    args = parser.parse_args()

    collect_script = os.path.join(WORKSPACE_ROOT, "tools", "daily_summary", "collect.py")
    cmd = [sys.executable, collect_script]
    if args.date:
        cmd += ["--date", args.date]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE_ROOT)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(1)

    raw_path = result.stdout.strip().splitlines()[-1]
    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    day = data["date"]
    projects = data["projects"]

    # Build one cross-project timeline, deduping commits that show up in more
    # than one repo (e.g. a project that used to live nested inside another
    # one shows the same commit hash in both histories).
    seen_hashes = set()
    timeline = []
    for p in projects:
        if not p["is_git"]:
            continue
        for c in p["commits"]:
            if c["hash"] in seen_hashes:
                continue
            seen_hashes.add(c["hash"])
            timeline.append({
                "time": c["time"],
                "project": p["project"],
                "subject": c["subject"],
            })

    timeline.sort(key=lambda e: e["time"])

    # Non-git folders: only surface them if something actually changed, as a
    # terse line, not a file list.
    non_git_activity = []
    for p in projects:
        if p["is_git"]:
            continue
        if p["changed_files"]:
            first_time = p["changed_files"][0]["time"]
            non_git_activity.append({
                "time": first_time,
                "project": p["project"],
                "count": len(p["changed_files"]),
            })

    # In-progress (uncommitted) work, one line per project.
    in_progress = [
        p["project"] for p in projects
        if p["is_git"] and p.get("uncommitted_count", 0) > 0
    ]

    entries = [f"- **{e['time']}** [{e['project']}] {e['subject']}" for e in timeline]
    entries += [
        f"- **{e['time']}** [{e['project']}] {e['count']} file(s) edited (no git history)"
        for e in non_git_activity
    ]
    entries.sort(key=lambda line: line.split("**")[1])

    out = [f"# Daily Summary — {day}\n"]

    if not entries:
        out.append("No commits or file changes today.\n")
    else:
        out.append("## Timeline\n")
        out.extend(entries)

    if in_progress:
        out.append("\n## Still in progress (uncommitted)\n")
        out.append(", ".join(in_progress))

    report = "\n".join(out) + "\n"

    out_dir = os.path.join(WORKSPACE_ROOT, ".tmp", "daily_summaries")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{day}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(out_path)


if __name__ == "__main__":
    main()
