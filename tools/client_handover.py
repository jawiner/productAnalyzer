"""Build the hand-over package for a client who leaves a Mashtech monthly plan,
or (with --one-time) for a client who paid once and gets the site on their own
Cloudflare Pages account at delivery.

One command produces everything the client keeps (site files ready to upload, the
source, their content) plus a checklist and a message for you. See
workflows/client_handover.md for when and how to use it.

    python tools/client_handover.py websites/el-nof-panorama --client "וילה אל נוף" \
        --domain villa-el-nof-panorama.co.il --plan premium

    python tools/client_handover.py websites/tnufa-physio --client "תנופה" \
        --domain tnufa.co.il --plan starter --one-time --live-date 2026-12-01

What it does, in order:
  1. Copies the source from the last commit (what is live), never .env files.
  2. Freezes Intake Studio edits: if the site loads the Intake Studio editor (cms.js),
     the published texts, photos and videos are downloaded and the site gets a local
     copy of the loader that reads them from its own folder. With nothing published,
     the loader is simply removed (the site's own HTML is the content).
  3. Builds the site if it has a build step (in a temp copy; your folder is untouched).
  4. Scans everything for secrets and stops if it finds one (names only, never values).
  5. Writes website.zip, source.zip and README.txt into one client zip, plus
     owner-checklist.md and message-to-client.txt for you.

Output: .tmp/handover/<name>-<date>/ in the WAT root (disposable; regenerate any time).
Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WAT_ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "mashtech-handover/1.0"

# Never shipped, whatever git says.
EXCLUDE_DIRS = {".git", "node_modules", ".vercel", ".tmp", "dist", "dist-ssr", ".next", "out",
                "__pycache__", ".playwright-cli", ".playwright-mcp", ".cache", ".turbo", ".claude"}
EXCLUDE_FILE_RE = re.compile(r"(^\.env(\..*)?$)|(\.log$)|(\.production-backup$)|(^\.DS_Store$)|(^Thumbs\.db$)", re.I)
TEXT_EXT = {".html", ".htm", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".json", ".css", ".md", ".txt",
            ".xml", ".svg", ".yml", ".yaml", ".toml", ".env", ".example", ".py", ".sh", ".map", ".webmanifest"}

# Hosts run by Mashtech that a client loses when the plan ends (shown in README + checklist).
MASHTECH_SERVICES = {
    "intake-studio-eight.vercel.app": "עורך התוכן (Intake Studio)",
}

SECRET_PATTERNS = [
    ("OpenAI/Anthropic key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}")),
    ("Stripe live key", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{16,}")),
    ("GitHub token", re.compile(r"\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Resend key", re.compile(r"\bre_[A-Za-z0-9]{8,}_[A-Za-z0-9]{16,}")),
    ("Slack token", re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}")),
    ("Telegram bot token", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{30,}\b")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("Service-role variable", re.compile(r"SERVICE_ROLE_KEY\s*[=:]\s*['\"]?[A-Za-z0-9._-]{20,}")),
]
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.(eyJ[A-Za-z0-9_-]{8,})\.[A-Za-z0-9_-]{8,}")
GOOGLE_KEY_RE = re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")
CMS_TAG_RE = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']*/cms\.js)[\"'][^>]*>\s*</script>\s*", re.I)
EXT_URL_RE = re.compile(r"""(?:src|href|action)\s*=\s*["'](https?://[^"'\s>]+)""", re.I)


# ----------------------------------------------------------------------------- helpers

def say(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str) -> None:
    print(f"\nSTOPPED: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def run(cmd: list[str] | str, cwd: Path, log: Path | None = None, shell: bool = False) -> subprocess.CompletedProcess:
    res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, shell=shell)
    if log is not None:
        with open(log, "ab") as fh:
            fh.write(b"\n$ " + (cmd if isinstance(cmd, str) else " ".join(cmd)).encode() + b"\n")
            fh.write(res.stdout or b"")
            fh.write(res.stderr or b"")
    return res


def http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def copy_filtered(src: Path, dst: Path) -> None:
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            if EXCLUDE_FILE_RE.search(f):
                continue
            shutil.copy2(Path(root) / f, dst / rel / f)


def strip_env_files(folder: Path) -> list[str]:
    removed = []
    for p in folder.rglob("*"):
        if p.is_file() and re.match(r"^\.env(\..*)?$", p.name, re.I) and not p.name.lower().endswith(".example"):
            removed.append(str(p.relative_to(folder)))
            p.unlink()
    return removed


def zip_dir(folder: Path, zip_path: Path) -> int:
    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(folder).as_posix())
                count += 1
    return count


def text_files(folder: Path):
    for p in folder.rglob("*"):
        if p.is_file() and (p.suffix.lower() in TEXT_EXT or p.name.lower().startswith(".env")):
            try:
                yield p, p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue


# ----------------------------------------------------------------------------- 1. source

def export_source(site: Path, dest: Path, warnings: list[str]) -> str:
    """Last commit of the site (what is live). Falls back to a filtered folder copy."""
    dest.mkdir(parents=True, exist_ok=True)
    top = run(["git", "rev-parse", "--show-toplevel"], site)
    if top.returncode == 0:
        toplevel = Path(top.stdout.decode().strip())
        prefix = site.resolve().relative_to(toplevel.resolve()).as_posix() if site.resolve() != toplevel.resolve() else ""
        tree = f"HEAD:{prefix}" if prefix else "HEAD"
        has = run(["git", "cat-file", "-e", tree], toplevel)
        if has.returncode == 0:
            dirty = run(["git", "status", "--porcelain", "--", "."], site).stdout.decode().strip()
            if dirty:
                n = len(dirty.splitlines())
                warnings.append(f"{n} uncommitted change(s) in the site folder are NOT in the package "
                                "(it uses the last commit, which is what is live). Commit them first if they should go.")
            arch = run(["git", "archive", "--format=tar", tree], toplevel)
            if arch.returncode != 0:
                fail("git archive failed: " + arch.stderr.decode(errors="ignore")[:200])
            with tarfile.open(fileobj=io.BytesIO(arch.stdout)) as t:
                t.extractall(dest, filter="data")
            commit = run(["git", "rev-parse", "--short", "HEAD"], toplevel).stdout.decode().strip()
            return f"git commit {commit}"
    warnings.append("The site folder is not in git, so the package is a copy of the folder as it is now.")
    copy_filtered(site, dest)
    return "folder copy (not in git)"


def detect_kind(src: Path) -> tuple[str, dict]:
    pkg = src / "package.json"
    if pkg.exists():
        data = json.loads(pkg.read_text(encoding="utf-8"))
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        if "next" in deps:
            return "next", data
        if data.get("scripts", {}).get("build"):
            return "build", data
    return "static", {}


def output_dir(src: Path) -> str:
    vj = src / "vercel.json"
    if vj.exists():
        try:
            out = json.loads(vj.read_text(encoding="utf-8")).get("outputDirectory")
            if out:
                return out
        except json.JSONDecodeError:
            pass
    return "dist"


# ----------------------------------------------------------------------------- 2. CMS freeze

def find_cms(src: Path) -> list[tuple[Path, str, str]]:
    """(html file, loader url, site key) for every Intake Studio loader tag in the source."""
    found = []
    for p in src.rglob("*.html"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        html = p.read_text(encoding="utf-8", errors="ignore")
        for m in CMS_TAG_RE.finditer(html):
            key = re.search(r"data-site=[\"']([^\"']+)", m.group(0))
            if key and m.group(1).startswith(("http://", "https://")):
                found.append((p, m.group(1), key.group(1)))
    return found


def media_name(url: str) -> str:
    base = Path(urllib.parse.urlparse(url).path).name or "file"
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)[-60:]
    return hashlib.sha1(url.encode()).hexdigest()[:10] + "-" + base


def freeze_cms(src: Path, kind: str, override_json: Path | None, notes: list[str], warnings: list[str]) -> dict:
    tags = find_cms(src)
    if not tags:
        return {"used": False}
    loader_url = tags[0][1]
    key = tags[0][2]
    api = f"{urllib.parse.urlparse(loader_url).scheme}://{urllib.parse.urlparse(loader_url).netloc}"
    if override_json:
        content = json.loads(override_json.read_text(encoding="utf-8"))
    else:
        content = json.loads(http_get(f"{api}/api/cms-content?site={urllib.parse.quote(key)}"))
    fields = content.get("fields") or {}
    files_touched = sorted({str(p.relative_to(src)) for p, _, _ in tags})

    if not fields:
        for p in {p for p, _, _ in tags}:
            p.write_text(CMS_TAG_RE.sub("", p.read_text(encoding="utf-8")), encoding="utf-8")
        notes.append("Intake Studio: nothing was published, so the editor loader was removed. The site's own text and photos are the content.")
        return {"used": True, "fields": 0, "media": 0, "key": key, "files": files_touched}

    base = src / "public" if kind == "build" else src
    media_dir = base / "cms-media"
    media_dir.mkdir(parents=True, exist_ok=True)
    downloaded: dict[str, str] = {}
    for fkey, f in fields.items():
        v = f.get("v")
        if not isinstance(v, dict):
            continue
        for attr in ("url", "poster", "src"):
            u = v.get(attr)
            if isinstance(u, str) and u.startswith(("http://", "https://")):
                if u not in downloaded:
                    name = media_name(u)
                    try:
                        (media_dir / name).write_bytes(http_get(u, timeout=180))
                    except Exception as e:  # noqa: BLE001
                        fail(f"could not download the media for '{fkey}' ({type(e).__name__}). Nothing was written.")
                    downloaded[u] = "/cms-media/" + name
                v[attr] = downloaded[u]
    content["frozen"] = {"by": "Mashtech hand-over", "date": dt.date.today().isoformat()}
    (base / "cms-content.json").write_text(json.dumps(content, ensure_ascii=False, indent=1), encoding="utf-8")

    loader = http_get(loader_url).decode("utf-8")
    url_re = re.compile(r'var url = API \+ "/api/cms-content\?site=" \+ encodeURIComponent\(KEY\)[^\n]*;')
    if not url_re.search(loader) or "function ping(version) {" not in loader:
        fail("the live cms.js loader changed shape, so it can't be frozen safely. Update freeze_cms() in tools/client_handover.py.")
    loader = url_re.sub('var url = new URL("cms-content.json", script.src).href; // frozen copy: content ships with the site', loader)
    loader = loader.replace("function ping(version) {", "function ping(version) { return; // frozen copy: nothing to report", 1)
    header = f"/* Frozen copy of the Intake Studio loader, made {dt.date.today().isoformat()} for the hand-over of this site.\n   It reads cms-content.json from this site and calls no outside service. */\n"
    (base / "cms.js").write_text(header + loader, encoding="utf-8")

    for p in {p for p, _, _ in tags}:
        html = p.read_text(encoding="utf-8")

        def local(m: re.Match) -> str:
            tag = re.sub(r"\bsrc=[\"'][^\"']*/cms\.js[\"']", 'src="/cms.js"', m.group(0))
            return re.sub(r"\sdata-api=[\"'][^\"']*[\"']", "", tag)

        p.write_text(CMS_TAG_RE.sub(local, html), encoding="utf-8")
    notes.append(f"Intake Studio: {len(fields)} published field(s) and {len(downloaded)} media file(s) are frozen into the site (cms-content.json + cms-media/).")
    return {"used": True, "fields": len(fields), "media": len(downloaded), "key": key, "files": files_touched}


# ----------------------------------------------------------------------------- 3. build

def build_site(src: Path, log: Path) -> Path:
    win = os.name == "nt"
    install = ["npm", "ci", "--no-audit", "--no-fund"] if (src / "package-lock.json").exists() else ["npm", "install", "--no-audit", "--no-fund"]
    say("  installing packages (a few minutes the first time)...")
    r = run(" ".join(install) if win else install, src, log, shell=win)
    if r.returncode != 0:
        fail(f"package install failed; see {log}")
    say("  building...")
    r = run("npm run build" if win else ["npm", "run", "build"], src, log, shell=win)
    if r.returncode != 0:
        fail(f"the build failed; see {log}")
    out = src / output_dir(src)
    if not (out / "index.html").exists():
        fail(f"the build finished but {out.name}/index.html is missing")
    return out


def env_names(src: Path) -> list[str]:
    names = set()
    for p, text in text_files(src):
        if p.name.lower().endswith(".example"):
            names.update(re.findall(r"^\s*([A-Z][A-Z0-9_]{2,})\s*=", text, re.M))
        names.update(re.findall(r"import\.meta\.env\.([A-Z][A-Z0-9_]+)", text))
        names.update(re.findall(r"process\.env\.([A-Z][A-Z0-9_]+)", text))
    names.discard("NODE_ENV")
    return sorted(names)


# ----------------------------------------------------------------------------- 4. checks

def secret_scan(folders: list[Path]) -> tuple[list[str], list[str]]:
    hard, soft = [], []
    for folder in folders:
        for p, text in text_files(folder):
            rel = f"{folder.name}/{p.relative_to(folder).as_posix()}"
            is_example = p.name.lower().endswith(".example")
            for label, rx in SECRET_PATTERNS:
                if is_example and label == "Service-role variable":
                    continue  # placeholder values in .env.example
                if rx.search(text):
                    hard.append(f"{rel}: {label}")
            for m in JWT_RE.finditer(text):
                try:
                    pad = m.group(1) + "=" * (-len(m.group(1)) % 4)
                    role = json.loads(base64.urlsafe_b64decode(pad)).get("role")
                except Exception:  # noqa: BLE001
                    role = None
                if role == "service_role":
                    hard.append(f"{rel}: Supabase service-role key")
                elif role not in ("anon", None):
                    soft.append(f"{rel}: token with role '{role}'")
            if GOOGLE_KEY_RE.search(text):
                soft.append(f"{rel}: Google API key (fine if it is a browser key limited to the site's domain)")
    return sorted(set(hard)), sorted(set(soft))


SUPABASE_RE = re.compile(r"https://([a-z0-9-]+)\.supabase\.co", re.I)
BOOKING_MARKERS = ("data-booking-mount", "booking/widget.js", "booking-platform")

# One-time clients: the site goes onto Cloudflare Pages in the client's account (free plan, business use allowed).
# Folder uploads take files up to 25 MiB, and the dashboard upload takes up to 1,000 files.
CF_MAX_FILE = 25 * 1024 * 1024
CF_DASHBOARD_MAX_FILES = 1000
FREE_FIX_DAYS = 30  # one-time clients get free fixes for this many days after go-live


def outside_hosts(folder: Path) -> tuple[list[str], bool]:
    """Outside hosts the site loads or calls, and whether it embeds the Mashtech booking widget."""
    hosts, booking = set(), False
    for p, text in text_files(folder):
        if p.suffix.lower() not in (".html", ".htm", ".js", ".mjs"):
            continue
        for u in EXT_URL_RE.findall(text):
            h = urllib.parse.urlparse(u).netloc.lower()
            if h:
                hosts.add(h)
        for ref in SUPABASE_RE.findall(text):
            hosts.add(f"{ref.lower()}.supabase.co")
        if any(m in text for m in BOOKING_MARKERS):
            booking = True
    return sorted(hosts), booking


# ----------------------------------------------------------------------------- 5. documents

def readme(ctx: dict) -> str:
    services_he = "\n".join(f"  - {s}" for s in ctx["lost_he"]) or "  - אין. האתר לא תלוי בשירותים שלי."
    services_en = "\n".join(f"  - {s}" for s in ctx["lost_en"]) or "  - None. The site doesn't depend on my services."
    if not ctx["has_website"] and ctx["kind"] != "next":
        how_he = ("בחבילה הזו יש רק את קוד המקור (source.zip). מפתח צריך להריץ בו npm ci ואז npm run build,\n"
                  "ולהעלות את התיקייה שנוצרת לכל שירות אחסון. אחר כך מעדכנים את רשומות ה־DNS בחשבון הדומיין.")
        how_en = ("This package holds the source only (source.zip). A developer runs npm ci, then npm run build,\n"
                  "and uploads the folder it makes to any host. Then update the DNS records in your domain account.")
    elif ctx["kind"] == "next":
        how_he = ("האתר הזה הוא אפליקציה שצריכה שרת (Next.js), ולכן אין לו קבצים מוכנים להעלאה.\n"
                  "הדרך הפשוטה: חשבון חינמי ב־Vercel ‏(vercel.com), ייבוא של קבצי source.zip, ופריסה.")
        how_en = ("This site is an app that needs a server (Next.js), so there is no ready-to-upload folder.\n"
                  "Simplest route: a free Vercel account (vercel.com), import the files from source.zip, deploy.")
    else:
        how_he = ("1. פתחו את website.zip. בתוכו כל קבצי האתר, מוכנים להעלאה כמו שהם.\n"
                  "2. העלו את התיקייה לכל שירות אחסון לאתרים סטטיים, למשל Netlify (גוררים את התיקייה לאתר),\n"
                  "   Cloudflare Pages, או תיקיית public_html באחסון רגיל.\n"
                  "3. שירות האחסון ייתן לכם רשומות DNS. היכנסו לחשבון הדומיין שלכם והחליפו בהן את הרשומות הקיימות.")
        how_en = ("1. Open website.zip. It holds every file of the site, ready to upload as is.\n"
                  "2. Upload the folder to any static host, e.g. Netlify (drag the folder onto the site),\n"
                  "   Cloudflare Pages, or the public_html folder of a regular host.\n"
                  "3. The host gives you DNS records. In your domain account, replace the current records with them.")
    env_he = ("\nלמפתח שימשיך את האתר: הקוד משתמש בהגדרות האלה (רק השמות; הערכים לא נמסרים):\n  " + ", ".join(ctx["env"])) if ctx["env"] else ""
    env_en = ("\nFor the next developer: the code reads these settings (names only; values are not handed over):\n  " + ", ".join(ctx["env"])) if ctx["env"] else ""
    build_en = f"\nBuild: npm ci && npm run build  ->  {ctx['outdir']}/" if ctx["kind"] == "build" else ""
    cms_he = "\nהשינויים שעשיתם בעורך התוכן כלולים בקבצים (cms-content.json ותיקיית cms-media)." if ctx["cms_frozen"] else ""
    cms_en = "\nThe edits you made in the content editor are included (cms-content.json and the cms-media folder)." if ctx["cms_frozen"] else ""
    web_he = "  - website.zip: האתר עצמו, מוכן להעלאה.\n" if ctx["has_website"] else ""
    web_en = "  - website.zip: the site itself, ready to upload.\n" if ctx["has_website"] else ""
    return f"""האתר {ctx['client']} — חבילת מסירה
{'=' * 40}
תאריך: {ctx['date']}{('   דומיין: ' + ctx['domain']) if ctx['domain'] else ''}

מה יש כאן
{web_he}  - source.zip: קוד המקור, למפתח שימשיך לעבוד על האתר.
  - הקובץ הזה.

הכול שלכם: הדומיין רשום על שמכם ובחשבון שלכם, והטקסטים, התמונות והלוגו שייכים לכם.{cms_he}

איך מעלים את האתר לאחסון אחר
{how_he}

מה מפסיק לעבוד עם סיום המנוי
{services_he}
{env_he}

שאלות? יניר משטא, Mashtech · וואטסאפ 054-996-1663 · mashtatech@gmail.com


{ctx['client']} — hand-over package
{'=' * 40}
Date: {ctx['date']}{('   Domain: ' + ctx['domain']) if ctx['domain'] else ''}

What's inside
{web_en}  - source.zip: the source code, for a developer who carries on.
  - this file.

It's all yours: the domain is registered in your name and account, and the texts, photos and logo are yours.{cms_en}

Moving the site to another host
{how_en}

What stops when the plan ends
{services_en}
{env_en}{build_en}

Questions? Yanir Mashta, Mashtech · WhatsApp +972 54-996-1663 · mashtatech@gmail.com
"""


def checklist(ctx: dict) -> str:
    premium = ctx["plan"] == "premium"
    booking = ctx["booking"]
    cms = ctx["cms_used"]
    lines = [
        f"# Hand-over checklist: {ctx['client']} ({ctx['name']})",
        "",
        f"Package built {ctx['date']} from {ctx['source_ref']}. Client zip: `{ctx['client_zip']}`",
        "",
        "## Before you send",
        "- [ ] The plan ends at the end of the month already paid for, and the minimum term is over"
        " (3 months Starter/Professional, 6 months Premium).",
        "- [ ] Opened website.zip locally and the site looks right (`python -m http.server` inside the folder).",
        "- [ ] Sent the client zip and `message-to-client.txt` (WhatsApp or email).",
        "",
        "## After the client has moved the domain (not before, or the site goes dark)",
        "- [ ] Checked the domain now answers from the new host.",
        f"- [ ] Vercel: removed {ctx['domain'] or 'the domain'} from the project, then paused or deleted the project.",
        "- [ ] GitHub: kept the repo private as an archive, or transferred it to the client if they asked.",
    ]
    if cms:
        lines.append("- [ ] Intake Studio: archived the site and removed the client's editor access.")
    if booking or premium:
        lines += [
            "- [ ] Booking: deactivated the business on the booking platform.",
            "- [ ] If the client asked for their booking history: exported their appointments and customers"
            " (see workflows/client_handover.md, 'Booking data').",
        ]
    if premium:
        lines.append("- [ ] Premium services switched off: online payment, missed-call SMS, review collection.")
    lines += [
        "- [ ] Stopped the monthly charge; kept the invoices.",
        "- [ ] LeadFlow: marked the client as a former client.",
        "",
        "## Notes from the build",
    ]
    lines += [f"- {n}" for n in ctx["notes"]] or ["- None."]
    if ctx["warnings"]:
        lines += ["", "## Warnings"] + [f"- {w}" for w in ctx["warnings"]]
    if ctx["soft"]:
        lines += ["", "## Check these (not blocking)"] + [f"- {s}" for s in ctx["soft"]]
    lines += ["", "## Outside services the site still loads", ""] + ([f"- {h}" for h in ctx["hosts"]] or ["- None."])
    return "\n".join(lines) + "\n"


def client_message(ctx: dict) -> str:
    return f"""היי{(' ' + ctx['contact']) if ctx['contact'] else ''},
מצורפת חבילת המסירה של האתר {ctx['client']}. יש בה את כל קבצי האתר מוכנים להעלאה, את קוד המקור, וקובץ הסבר קצר (README.txt) איך מעבירים את האתר לאחסון אחר.
הדומיין כבר רשום על שמכם ונשאר שלכם. כשהאתר יעלה אצל האחסון החדש, תעדכנו את רשומות ה־DNS בחשבון הדומיין, ותכתבו לי. רק אחרי זה אנתק אותו אצלי, כדי שלא יהיה רגע שבו האתר לא באוויר.
תודה על העבודה המשותפת, ואם תצטרכו משהו אני כאן.
יניר
"""


# ----------------------------------------------------------------------------- 5b. one-time clients

def not_included(ctx: dict) -> tuple[list[str], list[str]]:
    """What a one-time client doesn't get, in Hebrew and English."""
    he = ["מערכת העריכה העצמית (אפשר עדיין לשנות טקסטים ותמונות ישירות בקבצים)",
          "גיבויים (website.zip הוא הגיבוי שלכם)",
          f"טיפול בתקלות אחרי {ctx['fixes_until_he']}",
          "עדכונים חודשיים"]
    en = ["the self-editing system (texts and photos can still be changed in the files)",
          "backups (website.zip is your backup)",
          f"fixes after {ctx['fixes_until']}",
          "monthly updates"]
    he += [x for x in ctx["lost_he"] if not x.startswith("עורך התוכן")]
    en += [x for x in ctx["lost_en"] if not x.startswith("the content editor") and x not in MASHTECH_SERVICES]
    return he, en


def readme_one_time(ctx: dict) -> str:
    no_he, no_en = not_included(ctx)
    until_he, until_en = ctx["fixes_until_he"], ctx["fixes_until"]
    cms_he = "\nהשינויים שעשיתם בעורך התוכן כלולים בקבצים (cms-content.json ותיקיית cms-media)." if ctx["cms_frozen"] else ""
    cms_en = "\nThe edits you made in the content editor are included (cms-content.json and the cms-media folder)." if ctx["cms_frozen"] else ""
    env_he = ("\nלמפתח שימשיך את האתר: הקוד משתמש בהגדרות האלה (רק השמות; הערכים לא נמסרים):\n  " + ", ".join(ctx["env"])) if ctx["env"] else ""
    env_en = ("\nFor the next developer: the code reads these settings (names only; values are not handed over):\n  " + ", ".join(ctx["env"])) if ctx["env"] else ""
    build_en = f"\nBuild: npm ci && npm run build  ->  {ctx['outdir']}/" if ctx["kind"] == "build" else ""
    dom_he = ("   דומיין: " + ctx["domain"]) if ctx["domain"] else ""
    dom_en = ("   Domain: " + ctx["domain"]) if ctx["domain"] else ""
    list_he = "\n".join(f"  - {x}" for x in no_he)
    list_en = "\n".join(f"  - {x}" for x in no_en)
    return f"""האתר {ctx['client']} — חבילת מסירה (תשלום חד־פעמי)
{'=' * 40}
תאריך: {ctx['date']}{dom_he}

מה יש כאן
  - website.zip: האתר עצמו, בדיוק הקבצים שבאוויר. שמרו אותו, הוא הגיבוי שלכם.
  - source.zip: קוד המקור, למפתח שימשיך לעבוד על האתר.
  - הקובץ הזה.

הכול שלכם: האתר מאוחסן ב־Cloudflare Pages בחשבון החינמי שלכם, הדומיין רשום על שמכם ובחשבון שלכם, והטקסטים, התמונות והלוגו שייכים לכם.{cms_he}

מה כלול
  - הקמת האתר בחשבון Cloudflare שלכם וחיבור הדומיין.
  - תיקון כל תקלה בלי תשלום עד {until_he}.

מה לא כלול
{list_he}

כל שינוי אחרי {until_he} מקבל הצעת מחיר לפני שמתחילים. רוצים לעבור למנוי בהמשך? אפשר בכל שלב.

שמרו את פרטי הכניסה ל־Cloudflare ולחשבון הדומיין. בלעדיהם אי אפשר לשנות את האתר.

איך מעלים גרסה חדשה של האתר (למי שישנה אותו)
1. פותחים את website.zip ומשנים את הקבצים.
2. ב־Cloudflare נכנסים ל־Workers & Pages, בוחרים את הפרויקט של האתר, לוחצים Create deployment וגוררים את התיקייה.
{env_he}

שאלות? יניר משטא, Mashtech · וואטסאפ 054-996-1663 · mashtatech@gmail.com


{ctx['client']} — hand-over package (one-time payment)
{'=' * 40}
Date: {ctx['date']}{dom_en}

What's inside
  - website.zip: the site itself, exactly the files that are live. Keep it: it's your backup.
  - source.zip: the source code, for a developer who carries on.
  - this file.

It's all yours: the site is hosted on Cloudflare Pages in your own free account, the domain is registered in your name and account, and the texts, photos and logo are yours.{cms_en}

Included
  - Setting the site up in your Cloudflare account and connecting the domain.
  - Fixing any problem at no charge until {until_en}.

Not included
{list_en}

Any change after {until_en} gets a quote before work starts. Want to switch to the monthly plan later? You can at any time.

Keep your Cloudflare and domain-account logins safe. Without them nobody can change the site.

Uploading a new version of the site (for whoever changes it)
1. Open website.zip and change the files.
2. In Cloudflare, open Workers & Pages, pick the site's project, click Create deployment and drop in the folder.
{env_en}{build_en}

Questions? Yanir Mashta, Mashtech · WhatsApp +972 54-996-1663 · mashtatech@gmail.com
"""


def checklist_one_time(ctx: dict) -> str:
    dom = ctx["domain"] or "the domain"
    www = f"www.{ctx['domain']}" if ctx["domain"] else "the www address"
    lines = [
        f"# One-time set-up checklist: {ctx['client']} ({ctx['name']})",
        "",
        f"Package built {ctx['date']} from {ctx['source_ref']}. Client zip: `{ctx['client_zip']}`",
        f"Go-live {ctx['live_date']}; free fixes until {ctx['fixes_until']} ({FREE_FIX_DAYS} days).",
        "",
        "## Before you start",
        "- [ ] The one-time price is paid (Starter ₪1,690 / Professional ₪3,190, or what the quote says).",
        "- [ ] Opened website.zip locally and the site looks right (`python -m http.server` inside the folder).",
        "- [ ] The client opened a free Cloudflare account with their own email and password,"
        " and added you as a member (Manage Account → Members).",
        "",
        "## Put the site on the client's Cloudflare",
        "- [ ] Workers & Pages → Create → Pages → Upload assets: named the project and dropped in the unzipped website folder.",
        "- [ ] Opened the `<project>.pages.dev` address and checked every page, on a phone too.",
        "- [ ] Email first: if the domain has email (MX records, e.g. Google Workspace), checked that Cloudflare"
        " copied those records before changing anything. If they're missing, the client's email stops.",
        f"- [ ] Pages project → Custom domains: added {dom} and {www}.",
        "- [ ] In the client's domain account: replaced the nameservers with the two Cloudflare gives. The domain stays registered in their name.",
        f"- [ ] {dom} opens from Cloudflare with https (the lock), and the client's email still works.",
        "",
        "## After the domain answers from Cloudflare (not before, or the site goes dark)",
        f"- [ ] If the site ran on your Vercel (preview or an earlier plan): removed {dom} from the project, then paused or deleted the project.",
        "- [ ] GitHub: kept the repo private as an archive, or transferred it to the client if they asked.",
    ]
    if ctx["cms_used"]:
        lines.append("- [ ] Intake Studio: archived the site and removed the client's editor access.")
    if ctx["booking"]:
        lines.append("- [ ] Booking: the site embeds the booking widget, which isn't part of a one-time sale."
                     " Swapped it for a WhatsApp or phone link, or deactivated the business on the booking platform.")
    lines += [
        "- [ ] Sent the client zip and `message-to-client.txt` (WhatsApp or email).",
        f"- [ ] Put {ctx['fixes_until']} in your calendar: the end of free fixes.",
        f"- [ ] On {ctx['fixes_until']}: removed yourself as a member of their Cloudflare account,"
        " or stayed on with the client's OK for paid changes.",
        "- [ ] No monthly charge set up; kept the invoice.",
        "- [ ] LeadFlow: marked the client as a one-time client.",
        "",
        "## Notes from the build",
    ]
    lines += [f"- {n}" for n in ctx["notes"]] or ["- None."]
    if ctx["warnings"]:
        lines += ["", "## Warnings"] + [f"- {w}" for w in ctx["warnings"]]
    if ctx["soft"]:
        lines += ["", "## Check these (not blocking)"] + [f"- {x}" for x in ctx["soft"]]
    lines += ["", "## Outside services the site still loads", ""] + ([f"- {h}" for h in ctx["hosts"]] or ["- None."])
    return "\n".join(lines) + "\n"


def message_one_time(ctx: dict) -> str:
    where = f" בכתובת {ctx['domain']}" if ctx["domain"] else ""
    return f"""היי{(' ' + ctx['contact']) if ctx['contact'] else ''},
האתר {ctx['client']} באוויר{where}, בחשבון ה־Cloudflare שלכם.
מצורפת חבילת המסירה: כל קבצי האתר (שמרו אותם, זה הגיבוי שלכם), קוד המקור, וקובץ הסבר קצר (README.txt).
עד {ctx['fixes_until_he']} אני מתקן כל תקלה בלי תשלום. אחרי זה כל שינוי מקבל הצעת מחיר לפני שמתחילים.
שמרו את פרטי הכניסה ל־Cloudflare ולחשבון הדומיין, כי בלעדיהם אי אפשר לשנות את האתר. ואם תרצו לעבור למנוי בהמשך, אפשר בכל שלב.
תודה על העבודה המשותפת!
יניר
"""


# ----------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description="Build the hand-over package for a client site.")
    ap.add_argument("site", help="path to the site folder, e.g. websites/el-nof-panorama")
    ap.add_argument("--client", help="client or business name for the documents (default: folder name)")
    ap.add_argument("--contact", default="", help="first name for the WhatsApp message")
    ap.add_argument("--domain", default="", help="the site's domain, e.g. villa-el-nof-panorama.co.il")
    ap.add_argument("--plan", choices=["starter", "professional", "premium"], default="starter")
    ap.add_argument("--skip-build", action="store_true", help="don't build; ship the source only (for a quick look)")
    ap.add_argument("--one-time", action="store_true",
                    help="one-time client (Starter/Professional): set-up checklist for their own Cloudflare Pages, not a leaving checklist")
    ap.add_argument("--live-date", default="", help="one-time: go-live date YYYY-MM-DD (default today); free fixes run 30 days from it")
    ap.add_argument("--out", default=str(WAT_ROOT / ".tmp" / "handover"))
    ap.add_argument("--cms-content-file", type=Path, help="testing: use this JSON instead of the live Intake Studio content")
    args = ap.parse_args()
    if args.one_time and args.plan == "premium":
        fail("Premium is monthly only (booking, payments, SMS and reviews run through the plan), so it has no one-time hand-over.")
    if args.one_time and args.skip_build:
        fail("--one-time needs the built site (website.zip) for Cloudflare Pages; drop --skip-build.")
    try:
        live_date = dt.date.fromisoformat(args.live_date) if args.live_date else dt.date.today()
    except ValueError:
        fail(f"--live-date must look like 2026-12-01, not {args.live_date!r}")
    fixes_until = live_date + dt.timedelta(days=FREE_FIX_DAYS)

    site = Path(args.site).resolve()
    if not site.is_dir():
        fail(f"no such folder: {site}")
    name = site.name
    date = dt.date.today().isoformat()
    out = Path(args.out) / (f"{name}-onetime-{date}" if args.one_time else f"{name}-{date}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    log = out / "build.log"
    notes: list[str] = []
    warnings: list[str] = []

    with tempfile.TemporaryDirectory(prefix="handover-") as tmp:
        work = Path(tmp)
        src = work / "source"
        say(f"1/5 copying the source of {name}")
        source_ref = export_source(site, src, warnings)
        removed = strip_env_files(src)
        if removed:
            warnings.append("Removed committed .env file(s) from the package: " + ", ".join(removed) + ". Rotate any secret they held.")
        kind, _pkg = detect_kind(src)
        say(f"    {source_ref}; kind: {kind}")
        if args.one_time and kind == "next":
            fail("Next.js app: it needs a server, so it can't go on Cloudflare Pages as a folder upload."
                 " Quote this one-time hand-over separately.")

        say("2/5 freezing Intake Studio content")
        cms = freeze_cms(src, kind, args.cms_content_file, notes, warnings)
        if not cms["used"]:
            say("    not connected to Intake Studio")

        say("3/5 building the site files")
        website = None
        outdir = output_dir(src) if kind == "build" else ""
        if kind == "static":
            website = work / "website"
            copy_filtered(src, website)
        elif kind == "build" and not args.skip_build:
            build_src = work / "build"
            shutil.copytree(src, build_src)
            website = build_site(build_src, log)
        elif kind == "build":
            warnings.append("--skip-build: no website.zip; the client gets the source only.")
        else:
            notes.append("Next.js app: needs a Node host (e.g. Vercel); no static website.zip.")
        if website is not None and not (website / "index.html").exists():
            fail("the site files have no index.html at the top. " + (" ".join(warnings) or
                 "Check that the folder (and its last commit) is the site that is live."))
        if website is not None and cms.get("fields"):
            if not (website / "cms-content.json").exists():
                fail("the frozen content didn't reach the site files")
        envs = env_names(src)
        if envs and kind == "build" and website is not None:
            warnings.append("The build ran without any settings (.env is never copied). The code reads: "
                            + ", ".join(envs) + ". If the site needs them at build time, check the built copy.")

        if website is not None:
            files = [f for f in website.rglob("*") if f.is_file()]
            big = [f"{f.relative_to(website).as_posix()} ({f.stat().st_size / 2**20:.0f} MiB)"
                   for f in files if f.stat().st_size > CF_MAX_FILE]
            to = warnings if args.one_time else notes
            if big:
                to.append("Cloudflare Pages takes files up to 25 MiB; compress or move these first: " + ", ".join(big))
            if len(files) > CF_DASHBOARD_MAX_FILES:
                to.append(f"{len(files)} files: the Cloudflare dashboard upload takes up to {CF_DASHBOARD_MAX_FILES};"
                          " use `npx wrangler pages deploy <folder>` instead.")

        say("4/5 scanning for secrets")
        scan_dirs = [d for d in (src, website) if d is not None]
        hard, soft = secret_scan(scan_dirs)
        if hard:
            for h in hard:
                print(f"    SECRET: {h}", file=sys.stderr)
            fail("possible secrets in the package (listed above, values not shown). Remove them from the site and commit, then run again.")
        hosts, booking = outside_hosts(website or src)
        intake_left = [h for h in hosts if h in MASHTECH_SERVICES]
        if intake_left and cms.get("used"):
            fail("the site still loads Intake Studio after freezing: " + ", ".join(intake_left))
        lost_he, lost_en = [], []
        if args.plan == "premium" or booking:
            lost_he.append("מערכת התורים וההזמנות (עמוד קביעת התור יפסיק לקבל תורים; כדאי להחליף אותו בקישור לוואטסאפ או לטלפון)")
            lost_en.append("online booking (the booking page stops taking appointments; swap it for a WhatsApp or phone link)")
        if booking:
            notes.append("The site embeds the Mashtech booking widget: switch the business off on the booking platform once the client has moved.")
        if args.plan == "premium":
            lost_he += ["התשלום האונליין", "הודעות ה־SMS אחרי שיחה שלא נענתה", "איסוף הביקורות בגוגל"]
            lost_en += ["online payment", "missed-call SMS", "Google review collection"]
        if cms.get("used"):
            lost_he.append("עורך התוכן (אפשר עדיין לשנות טקסטים ותמונות ישירות בקבצים)")
            lost_en.append("the content editor (texts and photos can still be changed in the files)")
        for h in hosts:
            if h in MASHTECH_SERVICES and not cms.get("used"):
                lost_he.append(MASHTECH_SERVICES[h])
                lost_en.append(h)

        say("5/5 packing")
        client_dir = work / "client"
        client_dir.mkdir()
        n_src = zip_dir(src, client_dir / "source.zip")
        n_web = zip_dir(website, client_dir / "website.zip") if website is not None else 0
        ctx = {
            "name": name, "client": args.client or name, "contact": args.contact, "domain": args.domain,
            "plan": args.plan, "date": date, "kind": kind, "outdir": outdir, "env": envs,
            "cms_used": cms.get("used", False), "cms_frozen": bool(cms.get("fields")),
            "lost_he": lost_he, "lost_en": lost_en, "notes": notes, "warnings": warnings, "booking": booking,
            "has_website": website is not None,
            "soft": soft, "hosts": hosts, "source_ref": source_ref,
            "one_time": args.one_time, "live_date": live_date.isoformat(),
            "fixes_until": fixes_until.isoformat(), "fixes_until_he": fixes_until.strftime("%d.%m.%Y"),
        }
        (client_dir / "README.txt").write_text((readme_one_time if args.one_time else readme)(ctx), encoding="utf-8")
        client_zip = out / f"handover-{out.name}.zip"
        ctx["client_zip"] = str(client_zip)
        zip_dir(client_dir, client_zip)
        (out / "owner-checklist.md").write_text((checklist_one_time if args.one_time else checklist)(ctx), encoding="utf-8")
        (out / "message-to-client.txt").write_text((message_one_time if args.one_time else client_message)(ctx), encoding="utf-8")

    say("")
    say(f"Done: {out}" + (f"  (one-time; free fixes until {fixes_until.isoformat()})" if args.one_time else ""))
    web_part = f"website.zip {n_web} files, " if n_web else "no website.zip, "
    say(f"  client zip : {client_zip.name}  ({web_part}source.zip {n_src} files, README.txt)")
    say("  for you    : owner-checklist.md, message-to-client.txt" + (", build.log" if log.exists() else ""))
    for w in warnings:
        say(f"  WARNING: {w}")
    for s in soft:
        say(f"  check: {s}")


if __name__ == "__main__":
    main()
