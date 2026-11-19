"""Side-by-side test of idea writers (USER 2026-11-19: "do the side by side test" with OpenAI).

The content engine builds the exact request its 06:00 batch sends (brand, recent titles, what the
numbers taught, the playbook) and answers it with Claude (worker action draft_ideas). This script
puts the same request and JSON schema to OpenAI, then writes both sets, shuffled as A and B, to
.tmp/idea_compare/<time>/ so the owner can judge them blind. Nothing is saved in the CRM or sent to
Telegram, and no video is made.

    python tools/content_studio/compare_idea_writers.py --check     # is the OpenAI key there? (free)
    python tools/content_studio/compare_idea_writers.py [--model gpt-6.2-astra] [--effort medium] [--extra "..."]

Keys: CONTENT_ENGINE_URL / CONTENT_WORKER_SECRET from tools/content_studio/.env (as the worker),
OPENAI_API_KEY from the WAT root .env. Neither is ever printed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = ROOT / ".tmp" / "idea_compare"
sys.path.insert(0, str(HERE))
import worker  # noqa: E402

OPENAI_URL = "https://api.openai.com/v1/responses"
# USD per 1M tokens (input, output), from developers.openai.com/api/docs/models on 2026-11-19.
PRICES = {"gpt-6.2-astra": (8, 40), "gpt-6.2-sol": (2, 10), "gpt-6.1-terra": (1, 5), "gpt-6-luna": (0.10, 0.50)}
CLAUDE = "Claude Opus 5.5 (the engine's writer today)"


def scrub(text: str) -> str:
    """Error text without anything that looks like a key."""
    return re.sub(r"sk-[A-Za-z0-9_\-*.]+", "sk-…", str(text))[:400]


def openai_key() -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"].strip()
    path = ROOT / ".env"
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("OPENAI_API_KEY") and "=" in line:
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value and not value.startswith("<"):
                    return value
    return ""


def post(url: str, body: dict, headers: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        try:
            err = json.loads(detail).get("error") or {}
            detail = f"{err.get('type', '')} {err.get('code', '')}: {err.get('message', '')}" if isinstance(err, dict) else str(err)
        except ValueError:
            pass
        raise RuntimeError(f"HTTP {e.code} {scrub(detail)}") from None


def clip(text, n: int) -> str:
    s = str(text or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def normalize(raw: dict) -> dict:
    """The engine's C.normalizeIdea, so both writers are cut to the same limits."""
    beats = [b for b in (raw.get("beats") or []) if isinstance(b, dict) and b.get("say")][:10]
    facts = [f for f in (raw.get("facts") or []) if isinstance(f, dict) and f.get("claim") and f.get("source")][:6]
    return {
        "title": clip(raw.get("title") or "Untitled idea", 120), "pillar": clip(raw.get("pillar"), 80),
        "hook_line": clip(raw.get("hook_line"), 200), "on_screen_hook": clip(raw.get("on_screen_hook"), 60),
        "concept": clip(raw.get("concept"), 400),
        "beats": [{"say": clip(b["say"], 400), "show": clip(b.get("show"), 400)} for b in beats],
        "facts": [{"claim": clip(f["claim"], 300), "source": clip(f["source"], 200)} for f in facts],
        "caption_seed": clip(raw.get("caption_seed"), 600), "why": clip(raw.get("why"), 300),
    }


def ask_openai(request: dict, model: str, effort: str, key: str) -> tuple[list[dict], dict]:
    body = {
        "model": model,
        "input": [{"role": "system", "content": request["system"]}, {"role": "user", "content": request["prompt"]}],
        "reasoning": {"effort": effort},
        "max_output_tokens": 40000,
        "text": {"format": {"type": "json_schema", "name": "ideas", "schema": request["schema"], "strict": True}},
    }
    started = time.time()
    res = post(OPENAI_URL, body, {"Authorization": f"Bearer {key}"}, timeout=600)
    if res.get("status") == "incomplete":
        raise RuntimeError(f"OpenAI stopped early: {(res.get('incomplete_details') or {}).get('reason')}")
    text, refusal = "", ""
    for item in res.get("output") or []:
        if item.get("type") != "message":
            continue  # reasoning items carry no answer
        for part in item.get("content") or []:
            if part.get("type") == "output_text":
                text += part.get("text", "")
            elif part.get("type") == "refusal":
                refusal += part.get("refusal", "")
    if not text:
        raise RuntimeError(f"OpenAI gave no ideas{': ' + refusal[:300] if refusal else ''}")
    ideas = [normalize(i) for i in json.loads(text).get("ideas", []) if i.get("hook_line")][: request["count"]]
    usage = res.get("usage") or {}
    price_in, price_out = PRICES.get(model, (0, 0))
    tokens_in, tokens_out = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
    return ideas, {"seconds": round(time.time() - started), "input_tokens": tokens_in, "output_tokens": tokens_out,
                   "reasoning_tokens": (usage.get("output_tokens_details") or {}).get("reasoning_tokens"),
                   "usd": round(tokens_in / 1e6 * price_in + tokens_out / 1e6 * price_out, 3)}


def as_markdown(label: str, ideas: list[dict]) -> str:
    lines = [f"## Set {label}", ""]
    for n, i in enumerate(ideas, 1):
        lines += [f"### {label}{n}. {i['title']}", f"- **On screen, frame 1:** {i['on_screen_hook']}",
                  f"- **First line said:** {i['hook_line']}", f"- **Idea:** {i['concept']}", "- **What it says:**"]
        lines += [f"  {k}. {b['say']}" for k, b in enumerate(i["beats"], 1)]
        lines += [f"- **Why it works:** {i['why']}",
                  "- **Facts:** " + "; ".join(f"{f['claim']} ({f['source']})" for f in i["facts"]), ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", default="gpt-6.2-astra", choices=sorted(PRICES))
    ap.add_argument("--effort", default="medium", help="OpenAI reasoning effort (the engine runs Claude at medium)")
    ap.add_argument("--extra", default="", help="the same extra note goes to both writers")
    ap.add_argument("--check", action="store_true", help="only say whether the OpenAI key is there")
    args = ap.parse_args()

    key = openai_key()
    if args.check or not key:
        print(f"OpenAI key: {'found' if key else 'missing'} (OPENAI_API_KEY in {ROOT / '.env'})")
        return 0 if key else 2
    env = worker.load_env()
    if not env.get("CONTENT_ENGINE_URL") or not env.get("CONTENT_WORKER_SECRET"):
        print("The worker's engine URL or key is missing in tools/content_studio/.env")
        return 2

    print("Claude: writing ideas through the engine (same request as the 06:00 batch)…", flush=True)
    started = time.time()
    draft = post(env["CONTENT_ENGINE_URL"], {"action": "draft_ideas", "extra": args.extra},
                 {"x-content-worker": env["CONTENT_WORKER_SECRET"]}, timeout=300)
    claude = {"ideas": [normalize(i) for i in draft.get("ideas", [])], "seconds": round(time.time() - started)}
    print(f"Claude: {len(claude['ideas'])} ideas in {claude['seconds']} s", flush=True)

    print(f"OpenAI: same request to {args.model} (effort {args.effort})…", flush=True)
    openai_ideas, stats = ask_openai(draft, args.model, args.effort, key)
    print(f"OpenAI: {len(openai_ideas)} ideas in {stats['seconds']} s, "
          f"{stats['input_tokens']} in / {stats['output_tokens']} out tokens, about ${stats['usd']}", flush=True)

    writers = [(CLAUDE, claude["ideas"]), (f"OpenAI {args.model}", openai_ideas)]
    random.shuffle(writers)
    folder = OUT / dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "compare.md").write_text(
        f"# Video ideas, two writers, same request ({draft.get('today')})\n\n"
        "Which set would you rather make? Judge them blind; reveal.json says who wrote which.\n\n"
        + as_markdown("A", writers[0][1]) + "\n" + as_markdown("B", writers[1][1]), encoding="utf-8")
    (folder / "reveal.json").write_text(json.dumps({
        "A": writers[0][0], "B": writers[1][0], "openai": {"model": args.model, "effort": args.effort, **stats},
        "claude_seconds": claude["seconds"], "extra": args.extra}, indent=2), encoding="utf-8")
    (folder / "request.json").write_text(json.dumps({"system": draft["system"], "prompt": draft["prompt"],
                                                     "count": draft["count"]}, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "ideas.json").write_text(json.dumps({"A": writers[0][1], "B": writers[1][1]}, indent=2,
                                                  ensure_ascii=False), encoding="utf-8")
    print(f"Written: {folder / 'compare.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
