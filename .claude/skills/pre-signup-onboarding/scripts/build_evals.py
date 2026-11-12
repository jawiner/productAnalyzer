#!/usr/bin/env python3
"""Generate evals/<case>/ folders from references/evaluation-cases.md.

references/evaluation-cases.md is the single source for the evaluation cases.
This script turns each "## Case: <name>" section into the folder layout that
`claude plugin eval` reads:

    evals/<name>/prompt.md           run settings + the prompt
    evals/<name>/case.yaml           name + expected outcome
    evals/<name>/graders/NN-*.md     one pass criterion per file

Usage (from anywhere):
    python scripts/build_evals.py           write the folders
    python scripts/build_evals.py --check   report differences, write nothing

Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CASES_MD = SKILL_DIR / "references" / "evaluation-cases.md"
EVALS_DIR = SKILL_DIR / "evals"

PROMPT_SETTINGS = """---
tags: [pre-signup-onboarding]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---
"""

GRADER_HEADER = """---
type: llm
focus: trace
weight: 1
---
"""

CASE_RE = re.compile(r"^## Case: ([a-z][a-z0-9-]*)\s*$", re.M)
RESERVED = {"results", "mocks", "node_modules", "files", "true", "false", "null"}


def slug(text: str, limit: int = 40) -> str:
    """Short file-name slug from the first whole words of a criterion."""
    out = ""
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if len(out) + len(word) + 1 > limit:
            break
        out = f"{out}-{word}" if out else word
    return out or "criterion"


def section(body: str, heading: str) -> str:
    """Text under '### <heading>' up to the next heading or rule."""
    m = re.search(rf"^### {re.escape(heading)}\s*$", body, re.M)
    if not m:
        return ""
    rest = body[m.end():]
    end = re.search(r"^(#{2,3} |---\s*$)", rest, re.M)
    return rest[: end.start()] if end else rest


def list_items(text: str, marker: str) -> list[str]:
    """Items of a markdown list. Continuation lines are joined to their item."""
    items: list[str] = []
    for line in text.splitlines():
        m = re.match(marker, line)
        if m:
            items.append(line[m.end():].strip())
        elif line.strip() and items and line.startswith((" ", "\t")):
            items[-1] += " " + line.strip()
    return items


def parse_cases(md_path: Path = CASES_MD) -> list[dict]:
    text = md_path.read_text(encoding="utf-8")
    matches = list(CASE_RE.finditer(text))
    cases = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        # A later "## " heading that is not a case ends the last case.
        stop = re.search(r"^## (?!Case: )", body, re.M)
        if stop:
            body = body[: stop.start()]
        fence = re.search(r"```text\n(.*?)\n```", section(body, "Prompt"), re.S)
        cases.append(
            {
                "name": m.group(1),
                "prompt": fence.group(1).strip() if fence else "",
                "expected": list_items(section(body, "Expected behaviors"), r"^- "),
                "criteria": list_items(section(body, "Pass criteria"), r"^\d+\. "),
            }
        )
    return cases


def validate(cases: list[dict]) -> list[str]:
    problems = []
    seen = set()
    for c in cases:
        n = c["name"]
        if n in seen:
            problems.append(f"{n}: duplicate case name")
        seen.add(n)
        if n in RESERVED:
            problems.append(f"{n}: reserved case name")
        if not c["prompt"]:
            problems.append(f"{n}: no prompt found (needs a ```text block under '### Prompt')")
        if "---" in c["prompt"].splitlines():
            problems.append(f"{n}: prompt contains a bare '---' line")
        if not c["expected"]:
            problems.append(f"{n}: no expected behaviors")
        if not c["criteria"]:
            problems.append(f"{n}: no pass criteria")
    if not cases:
        problems.append("no '## Case: <name>' sections found")
    return problems


def render(case: dict) -> dict[str, str]:
    """Relative path -> file content for one case."""
    files = {
        "prompt.md": PROMPT_SETTINGS + "\n" + case["prompt"] + "\n",
        "case.yaml": (
            'schema_version: "1.1"\n'
            f"name: {case['name']}\n"
            "expected_outcome: |\n"
            + "".join(f"  {line}\n" for line in case["expected"])
        ),
    }
    for i, criterion in enumerate(case["criteria"], 1):
        files[f"graders/{i:02d}-{slug(criterion)}.md"] = GRADER_HEADER + "\n" + criterion + "\n"
    return files


def diff(cases: list[dict]) -> list[str]:
    """Differences between evals/ on disk and what the markdown would generate."""
    out = []
    for case in cases:
        root = EVALS_DIR / case["name"]
        want = render(case)
        for rel, content in want.items():
            path = root / rel
            if not path.exists():
                out.append(f"missing: evals/{case['name']}/{rel}")
            elif path.read_text(encoding="utf-8") != content:
                out.append(f"out of date: evals/{case['name']}/{rel}")
        graders = root / "graders"
        if graders.is_dir():
            for path in sorted(graders.glob("*.md")):
                if f"graders/{path.name}" not in want:
                    out.append(f"stale: evals/{case['name']}/graders/{path.name}")
    if EVALS_DIR.is_dir():
        names = {c["name"] for c in cases}
        for path in sorted(EVALS_DIR.iterdir()):
            if path.is_dir() and path.name not in names and path.name != "results":
                out.append(f"no matching case in evaluation-cases.md: evals/{path.name}/")
    return out


def write(cases: list[dict]) -> int:
    count = 0
    for case in cases:
        root = EVALS_DIR / case["name"]
        want = render(case)
        graders = root / "graders"
        if graders.is_dir():
            # Graders are derived files: drop the ones the markdown no longer produces.
            for path in graders.glob("*.md"):
                if f"graders/{path.name}" not in want:
                    path.unlink()
        for rel, content in want.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
            count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="report differences, write nothing")
    args = ap.parse_args()

    cases = parse_cases()
    problems = validate(cases)
    if problems:
        for p in problems:
            print(f"ERROR  {p}")
        return 1

    if args.check:
        differences = diff(cases)
        for d in differences:
            print(f"DIFF   {d}")
        print(f"{len(cases)} cases, {len(differences)} differences")
        return 1 if differences else 0

    count = write(cases)
    leftover = [d for d in diff(cases) if d.startswith("no matching case")]
    for d in leftover:
        print(f"NOTE   {d} (not removed; delete it by hand if it is obsolete)")
    print(f"wrote {count} files for {len(cases)} cases under {EVALS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
