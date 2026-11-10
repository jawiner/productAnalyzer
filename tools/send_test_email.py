"""Send a test copy of a marketing email to yourself, through your own Gmail.

The message goes to GMAIL_ADDRESS, the account that sends it, or to the one inbox named with
--to (one address only, e.g. another inbox of yours), so this can't reach a real list by mistake.
Merge tags (Brevo / mail-merge) get sample values, and [[FILL_INS]] stay visible (yellow in the
HTML) unless you pass --set KEY=VALUE.

Needs two lines in the WAT root .env (an app password, not the account password):
    GMAIL_ADDRESS=you@gmail.com
    GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
Create the app password at https://myaccount.google.com/apppasswords (2-Step Verification on).

Usage:
    python tools/send_test_email.py --html path/main.he.html --text path/main.he.txt \
        --subject "פרסומת: נועה פנויה ב-14?" [--set SENDER_NAME="..."] [--dry-run]
Leave out --html to send plain text only (the cold email and its follow-ups):
    python tools/send_test_email.py --text path/cold-consent.he.txt --subject "פרסומת: אילוצי קאסט"
"""

import argparse
import mimetypes
import re
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SAMPLE = {
    "FIRSTNAME": "יעל", "COMPANY": "תמר הפקות",
    # Template 1 of production-teams/openings.md, with a sample production.
    "OPENING": 'ראיתי שהצילומים של "הקיץ האחרון" מתחילים בינואר. בשלב הזה בדרך כלל אוספים אילוצים '
               'מכל שחקן ומכל סוכן בוואטסאפ, ומעתיקים הכול לאקסל.',
}
LABELS = {
    "SENDER_NAME": "שם השולח", "SENDER_ROLE": "תפקיד", "LEGAL_NAME": "שם משפטי",
    "ADDRESS": "כתובת העסק", "PHONE": "טלפון", "REPLY_TO_EMAIL": "מייל לתשובות",
    "FREE_OFFER": "ההצעה החינמית, מילה במילה", "PS_OFFER": "ההצעה האישית",
    "LIST_REASON": "למה הם ברשימה",
}
MARK = '<mark style="background:#FFE58A;color:#14130F;padding:0 4px;border-radius:3px;">[{}]</mark>'


def read_env(path):
    """Read KEY=VALUE lines without printing anything."""
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def connect():
    """Port 465, or 587 if its handshake fails. Runs before any upload, so it can't send twice.

    The long timeout is for embedded images: at 30 s a 640 KB message timed out mid-upload.
    On a flaky connection 465 failed about half its handshakes while 587 kept working (2026-11-09).
    """
    context = ssl.create_default_context()
    try:
        return smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=180)
    except (ssl.SSLError, OSError):
        smtp = smtplib.SMTP("smtp.gmail.com", 587, timeout=180)
        smtp.starttls(context=context)
        return smtp


def fill(content, is_html, sets, self_address):
    """Sample values for merge tags; fill-ins from --set, else left visible."""
    first = sets.get("FIRSTNAME", SAMPLE["FIRSTNAME"])
    company = sets.get("COMPANY", SAMPLE["COMPANY"])
    content = re.sub(r"\{% if contact\.FIRSTNAME %\} \{\{ contact\.FIRSTNAME \}\}\{% endif %\}",
                     (" " + first) if first else "", content)
    content = re.sub(r'\{\{ contact\.COMPANY \| default : "[^"]*" \}\}', company, content)
    content = content.replace("{{COMPANY}}", company)
    content = content.replace("{{OPENING}}", sets.get("OPENING", SAMPLE["OPENING"]))
    content = content.replace("{{ unsubscribe }}", "#unsubscribe-test" if is_html else "(קישור הסרה)")
    # Reply / "הסר" / "כן" links come back to you in a test.
    content = content.replace("mailto:[[REPLY_TO_EMAIL]]", "mailto:" + self_address)

    def placeholder(match):
        key = match.group(1)
        if key in sets:
            return sets[key]
        label = LABELS.get(key, key)
        return MARK.format(label) if is_html else "[" + label + "]"

    return re.sub(r"\[\[([A-Z_]+)\]\]", placeholder, content)


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Hebrew subjects on a Windows console
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--html", help="HTML part; leave out to send plain text only")
    parser.add_argument("--text", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--from-name", default="Castly · בדיקה")
    parser.add_argument("--to", help="one test inbox to send to instead of GMAIL_ADDRESS")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="fill a [[KEY]] fill-in or override FIRSTNAME / COMPANY")
    parser.add_argument("--inline", action="append", default=[], metavar="CID=PATH",
                        help="embed an image in the HTML part; the HTML refers to it as src=\"cid:CID\"")
    parser.add_argument("--dry-run", action="store_true", help="build the message and save it as .eml, don't send")
    args = parser.parse_args()

    sets = {}
    for item in args.set:
        if "=" not in item:
            sys.exit(f"--set needs KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        sets[key.strip()] = value

    env = read_env(ROOT / ".env")
    address = env.get("GMAIL_ADDRESS", "")
    password = env.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if not args.dry_run:
        if not address or not password:
            sys.exit("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must both be in the WAT root .env")
        if len(password) != 16:
            sys.exit("GMAIL_APP_PASSWORD doesn't look like an app password (expected 16 letters). "
                     "Create one at https://myaccount.google.com/apppasswords")
    self_address = address or "you@example.com"
    to = (args.to or self_address).strip()
    if not re.fullmatch(r"[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+", to):
        sys.exit("--to takes exactly one email address")

    text = fill(Path(args.text).read_text(encoding="utf-8"), False, sets, self_address)
    html = fill(Path(args.html).read_text(encoding="utf-8"), True, sets, self_address) if args.html else None
    size = f"HTML {len(html.encode('utf-8'))} bytes" if html else "plain text only"

    msg = EmailMessage()
    msg["Subject"] = args.subject
    msg["From"] = formataddr((args.from_name, self_address))
    msg["To"] = to
    msg["Message-ID"] = make_msgid(domain=self_address.split("@")[-1])
    msg.set_content(text, charset="utf-8")
    if html:
        msg.add_alternative(html, subtype="html", charset="utf-8")
        html_part = msg.get_payload()[1]
        for item in args.inline:
            if "=" not in item:
                sys.exit(f"--inline needs CID=PATH, got: {item}")
            cid, path = item.split("=", 1)
            kind = mimetypes.guess_type(path)[0] or "application/octet-stream"
            maintype, subtype = kind.split("/", 1)
            html_part.add_related(Path(path).read_bytes(), maintype=maintype, subtype=subtype,
                                  cid=f"<{cid}>", disposition="inline", filename=Path(path).name)

    if args.dry_run:
        out = ROOT / ".tmp" / "test-email.eml"
        out.parent.mkdir(exist_ok=True)
        out.write_bytes(bytes(msg))
        print(f"dry run: built '{args.subject}' ({size}), saved to {out}")
        return

    try:
        with connect() as smtp:
            smtp.login(address, password)
            smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        sys.exit("Gmail refused the login. Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env "
                 "(it must be an app password, and 2-Step Verification must be on).")
    print(f"sent '{args.subject}' from {self_address} to {to}, {size}, {len(args.inline)} embedded images")


if __name__ == "__main__":
    main()
