"""
Automatic checks: domain registration dates, site certificates, and whether the
API keys in .env still work.

Nothing here prints or returns a secret. Errors are reduced to a status code or
an exception class name, because request errors can carry the URL or headers.
Every key test uses a free "who am I / list" call, never one that costs money.
"""

import base64
import json
import re
import smtplib
import socket
import ssl
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from dotenv import dotenv_values

import rules

ROOT = Path(__file__).resolve().parent.parent.parent
TIMEOUT = 20

OK, PROBLEM, UNKNOWN = "ok", "problem", "unknown"


@dataclass
class Check:
    key: str
    name: str
    type: str
    state: str            # ok | problem | unknown
    expires: date | None = None
    detail: str = ""      # shown to the user; never contains a secret


# --- hosts and domains ---------------------------------------------------------

TWO_PART_SUFFIXES = {
    "co.il", "org.il", "net.il", "ac.il", "gov.il", "muni.il", "k12.il", "idf.il",
    "co.uk", "org.uk", "me.uk", "com.au", "net.au", "org.au", "co.nz", "com.br",
    "co.za", "co.in", "com.tr", "com.mx", "co.jp",
}
# Addresses on someone else's domain: there is no registration of yours to renew.
SHARED_SUFFIXES = (
    "vercel.app", "netlify.app", "github.io", "pages.dev", "web.app", "firebaseapp.com",
    "supabase.co", "onrender.com", "herokuapp.com", "base44.app", "workers.dev", "fly.dev",
)


def host_of(name: str) -> str | None:
    """'https://www.Example.co.il/page' -> 'www.example.co.il'. None if it isn't a host."""
    s = re.sub(r"^[a-z]+://", "", (name or "").strip().lower())
    s = s.split("/")[0].split(":")[0].strip(".")
    return s if re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", s) else None


def registrable(host: str) -> str | None:
    """The part you pay a registrar for: www.mashtech.co.il -> mashtech.co.il.
    None for addresses on a shared host (x.vercel.app)."""
    if any(host == s or host.endswith("." + s) for s in SHARED_SUFFIXES):
        return None
    labels = host.split(".")
    size = 3 if ".".join(labels[-2:]) in TWO_PART_SUFFIXES else 2
    return ".".join(labels[-size:]) if len(labels) >= size else None


MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_date(text: str) -> date | None:
    """Reads the date formats registries use. Day-first when the year comes last."""
    s = (text or "").strip()
    try:
        m = re.match(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", s)
        if m:
            return date(int(m[1]), int(m[2]), int(m[3]))
        m = re.match(r"(\d{1,2})[-./](\d{1,2})[-./](\d{4})", s)
        if m:
            return date(int(m[3]), int(m[2]), int(m[1]))
        m = re.match(r"(\d{1,2})[-\s]([A-Za-z]{3})[A-Za-z]*[-\s,]+(\d{4})", s)
        if m and m[2].lower() in MONTHS:
            return date(int(m[3]), MONTHS[m[2].lower()], int(m[1]))
    except ValueError:
        return None
    return None


WHOIS_EXPIRY = re.compile(
    r"(?im)^\s*(?:registry expiry date|registrar registration expiration date|expiration date|"
    r"expiry date|expiration time|expires on|expires|expire|paid-till|validity|renewal date)"
    r"\s*[:.]+\s*(.+?)\s*$")


def parse_whois_expiry(text: str) -> date | None:
    for match in WHOIS_EXPIRY.finditer(text or ""):
        found = parse_date(match.group(1))
        if found:
            return found
    return None


def _whois(server: str, query: str) -> str:
    with socket.create_connection((server, 43), timeout=TIMEOUT) as sock:
        sock.sendall((query + "\r\n").encode("ascii"))
        chunks = []
        while True:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)
    return b"".join(chunks).decode("utf-8", errors="replace")


def _rdap_expiry(domain: str) -> date | None:
    r = requests.get(f"https://rdap.org/domain/{domain}", timeout=TIMEOUT,
                     headers={"Accept": "application/rdap+json"})
    if r.status_code != 200:
        return None
    for event in r.json().get("events", []):
        if event.get("eventAction") == "expiration":
            return parse_date(event.get("eventDate", ""))
    return None


def _whois_expiry(domain: str) -> date | None:
    referral = _whois("whois.iana.org", domain.rsplit(".", 1)[1])
    server = re.search(r"(?im)^whois:\s*(\S+)", referral)
    if not server:
        return None
    return parse_whois_expiry(_whois(server.group(1), domain))


SHARED_NOTE = "Address on a shared host, so only its certificate is checked"
NO_DATE_NOTE = "Couldn't read the expiry date from the registry. Type it in Expires"


def domain_lookup(host: str) -> tuple[date | None, str]:
    """(registration expiry or None, note for the row when there is no date)."""
    domain = registrable(host)
    if not domain:
        return None, SHARED_NOTE
    for lookup in (_rdap_expiry, _whois_expiry):
        try:
            found = lookup(domain)
        except (requests.RequestException, OSError, ValueError):
            continue
        if found:
            return found, ""
    return None, NO_DATE_NOTE


def ssl_lookup(host: str) -> Check:
    key, name = f"ssl:{host}", f"{host} certificate"
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
        expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), tz=timezone.utc).date()
        return Check(key, name, rules.T_SSL, OK, expires, "Renewed by the host by itself")
    except ssl.SSLCertVerificationError as exc:
        reason = (getattr(exc, "verify_message", "") or "not trusted").rstrip(".")
        return Check(key, name, rules.T_SSL, PROBLEM, None,
                     f"The site's certificate isn't valid ({reason}). Visitors see a security warning.")
    except (OSError, ValueError, KeyError):
        return Check(key, name, rules.T_SSL, UNKNOWN, None, "Couldn't connect to the site today")


# --- API keys ------------------------------------------------------------------

REJECTED = "The service rejected this key (answer {code}). It expired or was revoked"


def _http(method: str, url: str, *, bad=(401,), **kwargs):
    """(state, detail, response or None). Never lets a request error escape: its text
    can include the URL and with it a key."""
    try:
        r = requests.request(method, url, timeout=TIMEOUT, **kwargs)
    except requests.RequestException as exc:
        return UNKNOWN, f"Couldn't reach the service today ({type(exc).__name__})", None
    if r.status_code == 200:
        return OK, "Key works", r
    if r.status_code in bad:
        return PROBLEM, REJECTED.format(code=r.status_code), r
    return UNKNOWN, f"Unexpected answer from the service ({r.status_code})", r


def _anthropic(value, env):
    return _http("GET", "https://api.anthropic.com/v1/models", params={"limit": 1}, bad=(401, 403),
                 headers={"x-api-key": value, "anthropic-version": "2023-06-01"})[:2] + (None,)


def _gemini(value, env):
    return _http("GET", "https://generativelanguage.googleapis.com/v1beta/models",
                 params={"pageSize": 1}, bad=(400, 401, 403),
                 headers={"x-goog-api-key": value})[:2] + (None,)


def _openai(value, env):
    return _http("GET", "https://api.openai.com/v1/models",
                 headers={"Authorization": f"Bearer {value}"})[:2] + (None,)


def _notion(value, env):
    return _http("GET", "https://api.notion.com/v1/users/me",
                 headers={"Authorization": f"Bearer {value}", "Notion-Version": "2022-06-28"})[:2] + (None,)


def _supabase(value, env):
    return _http("GET", "https://api.supabase.com/v1/projects",
                 headers={"Authorization": f"Bearer {value}"})[:2] + (None,)


def _firecrawl(value, env):
    state, detail, r = _http("GET", "https://api.firecrawl.dev/v1/team/credit-usage",
                             headers={"Authorization": f"Bearer {value}"})
    if state == OK:
        try:
            left = r.json().get("data", {}).get("remaining_credits")
            if isinstance(left, (int, float)):
                detail = f"Key works, {int(left):,} credits left"
        except ValueError:
            pass
    return state, detail, None


def _telegram(value, env):
    return _http("GET", f"https://api.telegram.org/bot{value}/getMe", bad=(401, 404))[:2] + (None,)


def _whatsapp(value, env):
    state, detail, r = _http("GET", "https://graph.facebook.com/v21.0/debug_token",
                             params={"input_token": value, "access_token": value}, bad=(400, 401))
    if state != OK:
        return state, detail, None
    try:
        data = r.json().get("data", {})
    except ValueError:
        return UNKNOWN, "Unexpected answer from the service", None
    if not data.get("is_valid"):
        return PROBLEM, "Meta says this token is no longer valid", None
    stamp = data.get("expires_at") or 0
    expires = datetime.fromtimestamp(stamp, tz=timezone.utc).date() if stamp else None
    return OK, "Token works" if expires else "Token works, no end date", expires


def _gmail(value, env):
    address = env.get("GMAIL_ADDRESS")
    if not address:
        return UNKNOWN, "GMAIL_ADDRESS is missing, so the password can't be tested", None
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=TIMEOUT) as server:
            server.login(address, value.replace(" ", ""))
        return OK, "Password works", None
    except smtplib.SMTPAuthenticationError:
        return PROBLEM, "Gmail rejected this app password. Create a new one in the Google account", None
    except (OSError, smtplib.SMTPException) as exc:
        return UNKNOWN, f"Couldn't reach Gmail today ({type(exc).__name__})", None


# First match wins. Names that match nothing are only looked at for a built-in end date.
PROBES = [
    (r"^ANTHROPIC_API_KEY", _anthropic),
    (r"^(GEMINI|GOOGLE_AI|GOOGLE_GENAI)_API_KEY", _gemini),
    (r"^OPENAI_API_KEY", _openai),
    (r"^NOTION_(TOKEN|API_KEY)", _notion),
    (r"^SUPABASE_ACCESS_TOKEN", _supabase),
    (r"^FIRECRAWL_API_KEY", _firecrawl),
    (r"^TELEGRAM_BOT_TOKEN", _telegram),
    (r"^WHATSAPP_ACCESS_TOKEN", _whatsapp),
    (r"^GMAIL_APP_PASSWORD", _gmail),
]
SECRET_NAME = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|PASS$", re.I)


def jwt_expiry(value: str) -> date | None:
    """End date written inside a JWT-style key (Supabase keys and many others)."""
    parts = (value or "").split(".")
    if len(parts) != 3:
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
        stamp = payload.get("exp")
        return datetime.fromtimestamp(stamp, tz=timezone.utc).date() if stamp else None
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def env_files(cfg: dict) -> list[tuple[str, Path]]:
    files = [("wat-framework", ROOT / ".env")]
    for entry in cfg.get("extra_env_files", []):
        path = Path(entry["path"])
        files.append((entry["label"], path if path.is_absolute() else ROOT / path))
    return files


def _google_oauth() -> Check | None:
    """token.json (Google sign-in used by the Sheets/Gmail tools): does the refresh still work?"""
    path = ROOT / "token.json"
    if not path.exists():
        return None
    key, name = "token:google-oauth", "Google sign-in (token.json)"
    try:
        token = json.loads(path.read_text(encoding="utf-8"))
        body = {"grant_type": "refresh_token", "refresh_token": token["refresh_token"],
                "client_id": token["client_id"], "client_secret": token["client_secret"]}
    except (ValueError, KeyError, OSError):
        return Check(key, name, rules.T_TOKEN, UNKNOWN, None, "token.json couldn't be read")
    try:
        r = requests.post(token.get("token_uri") or "https://oauth2.googleapis.com/token",
                          data=body, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return Check(key, name, rules.T_TOKEN, UNKNOWN, None,
                     f"Couldn't reach Google today ({type(exc).__name__})")
    if r.status_code == 200:
        return Check(key, name, rules.T_TOKEN, OK, None, "Sign-in works")
    if r.status_code in (400, 401):
        return Check(key, name, rules.T_TOKEN, PROBLEM, None,
                     "The Google sign-in expired. Delete token.json and sign in again")
    return Check(key, name, rules.T_TOKEN, UNKNOWN, None, f"Unexpected answer from Google ({r.status_code})")


def token_checks(cfg: dict) -> tuple[list[Check], list[str]]:
    """(checks, names of secrets that have no automatic test)."""
    checks, unchecked, seen = [], [], {}
    for label, path in env_files(cfg):
        if not path.exists():
            continue
        env = dotenv_values(path)
        for var, value in env.items():
            if not value:
                continue
            probe = next((fn for pattern, fn in PROBES if re.search(pattern, var)), None)
            expires = jwt_expiry(value)
            if not probe:
                if expires:
                    checks.append(Check(f"token:{label}:{var}", f"{var} ({label})", rules.T_TOKEN,
                                        OK, expires, "End date read from the key itself"))
                elif SECRET_NAME.search(var):
                    unchecked.append(f"{var} ({label})")
                continue
            # The same key in two files is tested once.
            cache_key = (probe.__name__, value)
            if cache_key not in seen:
                seen[cache_key] = probe(value, env)
            state, detail, probe_expires = seen[cache_key]
            checks.append(Check(f"token:{label}:{var}", f"{var} ({label})", rules.T_TOKEN,
                                state, probe_expires or expires, detail))
    google = _google_oauth()
    if google:
        checks.append(google)
    return checks, unchecked
