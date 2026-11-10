"""
Collects today's changes across the workspace: the top-level wat-framework
repo, every nested git repo (one per project folder), and non-git project
folders (summarized by file mtimes since no git history exists).

Usage:
    python tools/daily_summary/collect.py [--date YYYY-MM-DD]

Writes structured JSON to .tmp/daily_summaries/<date>_raw.json and prints
the path on stdout (last line) so calling scripts can pick it up.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GIT_AUTHOR_EMAIL = "myanir4@gmail.com"


def run(cmd, cwd):
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except Exception:
        return ""


# Projects live in category folders (websites/, saas/, internal/); anything
# still sitting directly under the root is picked up too.
CATEGORY_DIRS = ("websites", "saas", "internal")


def find_project_dirs(root):
    dirs = []
    for entry in sorted(os.listdir(root)):
        full = os.path.join(root, entry)
        if not os.path.isdir(full):
            continue
        if entry.startswith(".") or entry in ("tools", "workflows"):
            continue
        if entry in CATEGORY_DIRS:
            for sub in sorted(os.listdir(full)):
                sub_full = os.path.join(full, sub)
                if os.path.isdir(sub_full) and not sub.startswith("."):
                    dirs.append(sub_full)
        else:
            dirs.append(full)
    return dirs


def find_git_repos(root):
    repos = [root]
    for full in find_project_dirs(root):
        if os.path.isdir(os.path.join(full, ".git")):
            repos.append(full)
    return repos


def find_non_git_dirs(root, git_repos):
    git_set = set(git_repos)
    return [d for d in find_project_dirs(root) if d not in git_set]


def collect_git_repo(repo_path, since, until, label):
    log = run(
        [
            "git", "log",
            f"--since={since}", f"--until={until}",
            f"--author={GIT_AUTHOR_EMAIL}",
            "--pretty=format:%H|%h|%ad|%s", "--date=format:%H:%M",
        ],
        repo_path,
    )

    commits = []
    for line in log.splitlines():
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        full_hash, short_hash, time_str, subject = parts
        commits.append({
            "hash": full_hash,
            "short_hash": short_hash,
            "time": time_str,
            "subject": subject,
        })

    status = run(["git", "status", "--porcelain"], repo_path)
    uncommitted_count = len(status.splitlines()) if status else 0

    return {
        "project": label,
        "is_git": True,
        "commits": commits,
        "uncommitted_count": uncommitted_count,
    }


def collect_non_git_dir(dir_path, since_dt, label):
    changed_files = []
    for dirpath, dirnames, filenames in os.walk(dir_path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
        for f in filenames:
            full = os.path.join(dirpath, f)
            try:
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full))
            except OSError:
                continue
            if mtime >= since_dt:
                rel = os.path.relpath(full, dir_path)
                changed_files.append({"time": mtime.strftime("%H:%M"), "path": rel})

    changed_files.sort(key=lambda x: x["time"])

    return {
        "project": label,
        "is_git": False,
        "changed_files": changed_files,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="YYYY-MM-DD, defaults to today")
    args = parser.parse_args()

    if args.date:
        day = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        day = datetime.date.today()

    since_dt = datetime.datetime.combine(day, datetime.time.min)
    until_dt = since_dt + datetime.timedelta(days=1)
    since = since_dt.strftime("%Y-%m-%d 00:00:00")
    until = until_dt.strftime("%Y-%m-%d 00:00:00")

    git_repos = find_git_repos(WORKSPACE_ROOT)
    non_git_dirs = find_non_git_dirs(WORKSPACE_ROOT, git_repos)

    projects = []
    for repo in git_repos:
        label = "wat-framework" if repo == WORKSPACE_ROOT else os.path.basename(repo)
        projects.append(collect_git_repo(repo, since, until, label))

    for d in non_git_dirs:
        projects.append(collect_non_git_dir(d, since_dt, os.path.basename(d)))

    out_dir = os.path.join(WORKSPACE_ROOT, ".tmp", "daily_summaries")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{day.isoformat()}_raw.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"date": day.isoformat(), "projects": projects}, f, indent=2)

    print(out_path)


if __name__ == "__main__":
    main()
