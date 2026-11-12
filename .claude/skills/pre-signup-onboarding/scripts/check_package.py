#!/usr/bin/env python3
"""Check that the pre-signup-onboarding skill package is consistent.

Checks:
  1. SKILL.md frontmatter: name, description, known keys, length limits.
  2. File layout: the expected files exist; SKILL.md stays under 500 lines.
  3. Links: every relative markdown link resolves; every reference file is
     linked from SKILL.md; long reference files have a contents list.
  4. Sources: every numbered source in references/research.md has a URL, and
     every [R: n] / [V: n] citation in the package points at a real source.
  5. Evaluation cases: evals/ matches references/evaluation-cases.md.

Usage:
    python scripts/check_package.py           offline checks
    python scripts/check_package.py --urls    also request each source URL

Exit code 0 when there are no errors. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True  # keep __pycache__ out of the skill folder
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_evals  # noqa: E402

KNOWN_KEYS = {
    "name", "description", "argument-hint", "allowed-tools", "disable-model-invocation",
    "user-invocable", "model", "effort", "context", "agent", "hooks", "paths",
    "when_to_use", "license", "compatibility", "metadata", "version",
}
EXPECTED_FILES = [
    "SKILL.md",
    "references/research.md",
    "references/entry-patterns.md",
    "references/question-design.md",
    "references/screens-and-copy.md",
    "references/signup-handoff.md",
    "references/measurement.md",
    "references/templates.md",
    "references/worked-examples.md",
    "references/evaluation-cases.md",
    "scripts/build_evals.py",
    "scripts/check_package.py",
]
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SOURCE_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|(.*)$", re.M)
CITE_RE = re.compile(r"\[(?:R|V)(?:[^\]]*?):\s*([^\]]+)\]")

errors: list[str] = []
warnings: list[str] = []
notes: list[str] = []


def err(msg: str) -> None:
    if msg not in errors:
        errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def strip_fences(text: str) -> str:
    """Remove fenced code blocks so links inside templates are not checked."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        err("SKILL.md: does not start with a '---' frontmatter line")
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        err("SKILL.md: frontmatter is not closed with '---'")
        return {}, text
    block, body = text[4:end], text[end + 4:]
    data: dict[str, str] = {}
    for n, line in enumerate(block.splitlines(), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s?(.*)$", line)
        if not m:
            err(f"SKILL.md line {n}: not a 'key: value' line (multi-line values are not used here)")
            continue
        key, value = m.group(1), m.group(2).strip()
        quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"
        if quoted:
            value = value[1:-1]
        elif re.search(r":\s", value) or value.endswith(":"):
            err(f"SKILL.md line {n}: '{key}' has an unquoted value containing ': ', which breaks YAML")
        elif value[:1] in "[{>|*&!%@`#":
            err(f"SKILL.md line {n}: '{key}' starts with a YAML special character; quote the value")
        data[key] = value
    return data, body


def check_frontmatter() -> None:
    path = SKILL_DIR / "SKILL.md"
    if not path.exists():
        err("SKILL.md is missing")
        return
    text = path.read_text(encoding="utf-8")
    data, body = parse_frontmatter(text)

    name = data.get("name", "")
    if not name:
        err("frontmatter: 'name' is missing")
    else:
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            err(f"frontmatter: name '{name}' must be lowercase letters, digits and single hyphens")
        if len(name) > 64:
            err(f"frontmatter: name is {len(name)} characters (limit 64)")
        if name != SKILL_DIR.name:
            err(f"frontmatter: name '{name}' does not match the folder '{SKILL_DIR.name}'")

    desc = data.get("description", "")
    if not desc:
        err("frontmatter: 'description' is missing")
    else:
        if len(desc) > 1024:
            err(f"frontmatter: description is {len(desc)} characters (limit 1024)")
        if "<" in desc or ">" in desc:
            err("frontmatter: description contains '<' or '>'")
        notes.append(f"description length: {len(desc)} of 1024 characters")

    for key in data:
        if key not in KNOWN_KEYS:
            warn(f"frontmatter: unknown key '{key}'")

    lines = body.count("\n") + 1
    notes.append(f"SKILL.md body: {lines} lines")
    if lines > 500:
        err(f"SKILL.md body is {lines} lines (keep it under 500; move detail to references/)")


def check_layout() -> None:
    for rel in EXPECTED_FILES:
        if not (SKILL_DIR / rel).is_file():
            err(f"layout: {rel} is missing")
    for path in sorted((SKILL_DIR / "references").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if text.count("\n") > 300 and "## Contents" not in text:
            warn(f"layout: references/{path.name} is over 300 lines and has no '## Contents'")


def md_files() -> list[Path]:
    files = [SKILL_DIR / "SKILL.md"] + sorted((SKILL_DIR / "references").glob("*.md"))
    return [f for f in files if f.is_file()]


def check_links() -> None:
    linked_from_skill: set[Path] = set()
    total = 0
    for path in md_files():
        text = strip_fences(path.read_text(encoding="utf-8"))
        for target in LINK_RE.findall(text):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            total += 1
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                err(f"link: {path.relative_to(SKILL_DIR).as_posix()} -> {target} does not exist")
            elif path.name == "SKILL.md":
                linked_from_skill.add(resolved)
        # Paths written as code (`references/x.md`, `scripts/x.py`) must exist too.
        for target in re.findall(r"`((?:references|scripts)/[A-Za-z0-9_.-]+)`", text):
            if not (SKILL_DIR / target).exists():
                err(f"path: {path.relative_to(SKILL_DIR).as_posix()} mentions `{target}`, which does not exist")
    notes.append(f"relative links checked: {total}")
    for ref in sorted((SKILL_DIR / "references").glob("*.md")):
        if ref.resolve() not in linked_from_skill:
            err(f"link: references/{ref.name} is not linked from SKILL.md")


def source_urls() -> dict[int, str]:
    path = SKILL_DIR / "references" / "research.md"
    if not path.is_file():
        return {}
    found: dict[int, str] = {}
    for num, rest in SOURCE_ROW_RE.findall(path.read_text(encoding="utf-8")):
        m = re.search(r"\]\((https?://[^)\s]+)\)", rest)
        if m:
            found[int(num)] = m.group(1)
        else:
            err(f"sources: source {num} in references/research.md has no URL")
    return found


def cited_numbers(spec: str) -> set[int]:
    nums: set[int] = set()
    for a, b in re.findall(r"(\d+)(?:\s*[–-]\s*(\d+))?", spec):
        lo, hi = int(a), int(b) if b else int(a)
        nums.update(range(lo, hi + 1))
    return nums


def check_sources() -> dict[int, str]:
    urls = source_urls()
    if not urls:
        err("sources: no numbered sources with URLs found in references/research.md")
        return urls
    top = max(urls)
    missing = [n for n in range(1, top + 1) if n not in urls]
    if missing:
        err(f"sources: numbering has gaps: {missing}")
    notes.append(f"sources with URLs: {len(urls)}")
    for path in md_files():
        text = path.read_text(encoding="utf-8")
        for spec in CITE_RE.findall(text):
            for n in cited_numbers(spec):
                if n not in urls:
                    err(f"sources: {path.relative_to(SKILL_DIR).as_posix()} cites source {n}, which is not in research.md")
    return urls


def check_evals() -> None:
    cases = build_evals.parse_cases()
    for p in build_evals.validate(cases):
        err(f"evals: {p}")
    for d in build_evals.diff(cases):
        err(f"evals: {d} (run: python scripts/build_evals.py)")
    notes.append(f"evaluation cases: {len(cases)}, pass criteria: {sum(len(c['criteria']) for c in cases)}")


def check_urls(urls: dict[int, str]) -> None:
    """Request each source URL. Sites that refuse scripts are reported, not failed."""
    for num, url in sorted(urls.items()):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (link check)"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                print(f"  URL {num:>2}  {resp.status}  {url}")
        except urllib.error.HTTPError as e:
            print(f"  URL {num:>2}  {e.code}  {url}")
            if e.code in (404, 410):
                # Some sites (ftc.gov, for one) answer scripts with 404 for pages that exist.
                warn(f"sources: source {num} returned {e.code} to this script; open it in a browser to confirm: {url}")
        except Exception as e:  # network errors, timeouts, TLS
            print(f"  URL {num:>2}  ERR  {url}  ({type(e).__name__})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--urls", action="store_true", help="also request each source URL (needs network)")
    args = ap.parse_args()

    check_frontmatter()
    check_layout()
    check_links()
    urls = check_sources()
    check_evals()
    if args.urls:
        print("Requesting source URLs:")
        check_urls(urls)

    for n in notes:
        print(f"  info   {n}")
    for w in warnings:
        print(f"  WARN   {w}")
    for e in errors:
        print(f"  ERROR  {e}")
    print(f"{'FAIL' if errors else 'OK'}: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
