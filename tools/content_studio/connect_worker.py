"""One-time setup of this PC as the content engine's video PC.

Reads the worker key from the Mapflow database (read-only query through the Supabase CLI you're
signed in to), writes it to tools/content_studio/.env without printing it, checks that the
content-engine function accepts it, and registers the WAT-ContentStudio scheduled task.

Run from the wat-framework folder:
    python tools/content_studio/connect_worker.py
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAPFLOW = HERE.parent.parent / "saas" / "mapflow-crm"
PROJECT = "ginzdkemoribpqpwspix"


def main() -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as f:
        f.write("select secret from public.content_worker_secret limit 1;")
        sql = f.name
    try:
        # A terminal gets a table by default and an agent session gets {"rows": [...]}: ask for JSON
        # outside agent mode, so both runs see the same plain list of rows.
        run = subprocess.run(f'npx supabase db query --agent no --output-format json --remote={PROJECT} --read-only -f "{sql}"',
                             shell=True, cwd=MAPFLOW, capture_output=True, text=True, encoding="utf-8")
    finally:
        Path(sql).unlink(missing_ok=True)
    out = run.stdout or ""
    try:
        data = json.loads(out[min(i for i in (out.find("["), out.find("{")) if i >= 0):])
        rows = data["rows"] if isinstance(data, dict) else data
        secret = rows[0]["secret"]
    except Exception:
        # Never print stdout here: it could hold the key. The CLI's error line is safe to show.
        reason = next((line.strip() for line in (run.stderr or "").splitlines() if line.strip()), "no error text")
        print("Couldn't read the worker key from the database.")
        print("Supabase CLI said:", reason[:300])
        return 1
    if not re.fullmatch(r"[0-9a-f]{64}", secret or ""):
        print("The worker key in the database doesn't look right.")
        return 1
    (HERE / ".env").write_text(
        f"CONTENT_ENGINE_URL=https://{PROJECT}.supabase.co/functions/v1/content-engine\n"
        f"CONTENT_WORKER_SECRET={secret}\n"
        "CONTENT_VIDEO_ROOT=C:/Users/97254/lifemaxing-independent/marketing/video/daily\n", encoding="utf-8")
    print("1/3 Worker key saved in tools/content_studio/.env (git-ignored).")

    check = subprocess.run([sys.executable, str(HERE / "worker.py"), "--check"], capture_output=True, text=True, encoding="utf-8")
    ok = "connection OK" in check.stdout
    print("2/3 Connection to the content engine:", "OK" if ok else "FAILED")
    if not ok:
        print(check.stdout[-600:])
        return 1

    task = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "setup_schedule.ps1")],
                          capture_output=True, text=True)
    print("3/3", (task.stdout or task.stderr).strip()[-400:])
    return 0 if task.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
