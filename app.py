#!/usr/bin/env python3
import base64
import csv
import hashlib
import hmac
import html as html_lib
import io
import json
import logging
import os
import platform
import re
import secrets
import shutil
import smtplib
import socket
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from email.utils import formataddr, parseaddr
from email.message import EmailMessage
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.8 fallback guard
    ZoneInfo = None


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"


def load_env_file(path=ROOT / ".env"):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


load_env_file()

DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("DB_PATH", DATA_DIR / "mtg_collection.sqlite"))
LOG_DIR = Path(os.environ.get("LOG_DIR", DATA_DIR / "logs"))
WALLPAPER_DIR = Path(os.environ.get("WALLPAPER_DIR", DATA_DIR / "wallpapers"))
NEWS_IMAGE_DIR = Path(os.environ.get("NEWS_IMAGE_DIR", DATA_DIR / "news-images"))
LOG_FILE = Path(os.environ.get("LOG_FILE", LOG_DIR / "arcaneledger.log"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", str(2 * 1024 * 1024)) or (2 * 1024 * 1024))
LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "5") or 5)
DEFAULT_IMPORT = Path(os.environ.get("DEFAULT_IMPORT", "/Users/kristophr/Downloads/export(1).csv"))
APP_BASE_URL = os.environ.get("APP_BASE_URL", "").strip().rstrip("/")
SCRYFALL_SETS_URL = "https://api.scryfall.com/sets"
SCRYFALL_SET_URL = "https://api.scryfall.com/sets/{set_code}"
SCRYFALL_SEARCH_URL = "https://api.scryfall.com/cards/search"
SCRYFALL_CARD_URL = "https://api.scryfall.com/cards/{set_code}/{collector_number}"
SCRYFALL_ID_URL = "https://api.scryfall.com/cards/{card_id}"
SCRYFALL_QUERY = os.environ.get("SCRYFALL_QUERY", "game:paper")
SCRYFALL_LANGUAGE = os.environ.get("SCRYFALL_LANGUAGE", "en")
SCRYFALL_TIMEOUT_SECONDS = max(5, int(os.environ.get("SCRYFALL_TIMEOUT_SECONDS", "15") or 15))
SCRYFALL_IMPORT_LOOKUP_LIMIT = max(0, int(os.environ.get("SCRYFALL_IMPORT_LOOKUP_LIMIT", "80") or 80))
SCRYFALL_IMPORT_LOOKUP_DELAY = max(0.0, float(os.environ.get("SCRYFALL_IMPORT_LOOKUP_DELAY", "0.12") or 0.12))
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "America/New_York").strip() or "America/New_York"
PRICE_SNAPSHOT_SCHEDULE_ENABLED = os.environ.get("PRICE_SNAPSHOT_SCHEDULE_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}
PRICE_SNAPSHOT_SCHEDULE_TIME = os.environ.get("PRICE_SNAPSHOT_SCHEDULE_TIME", "01:00").strip() or "01:00"
PRICE_SNAPSHOT_DAILY_LIMIT = max(0, int(os.environ.get("PRICE_SNAPSHOT_DAILY_LIMIT", "0") or 0))
PRICE_SNAPSHOT_REQUEST_DELAY = max(0.0, float(os.environ.get("PRICE_SNAPSHOT_REQUEST_DELAY", "0.12") or 0.12))
MAILGUN_API_BASE = os.environ.get("MAILGUN_API_BASE", "https://api.mailgun.net/v3").rstrip("/")
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY", "")
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN", "")
MAILGUN_FROM_EMAIL = os.environ.get("MAILGUN_FROM_EMAIL", "")
MAILGUN_FROM_NAME = os.environ.get("MAILGUN_FROM_NAME", "Arcane Ledger")
STRIPE_API_BASE = os.environ.get("STRIPE_API_BASE", "https://api.stripe.com").rstrip("/")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_MONTHLY = os.environ.get("STRIPE_PRICE_MONTHLY", "")
STRIPE_PRICE_YEARLY = os.environ.get("STRIPE_PRICE_YEARLY", "")
MAIL_DRIVER = os.environ.get("MAIL_DRIVER", "")
MAIL_ENCRYPTION = os.environ.get("MAIL_ENCRYPTION", "").strip().lower()
SMTP_HOST = os.environ.get("SMTP_HOST") or os.environ.get("MAIL_HOST", "")
SMTP_PORT = int((os.environ.get("SMTP_PORT") or os.environ.get("MAIL_PORT") or "587") or 587)
SMTP_USER = os.environ.get("SMTP_USER") or os.environ.get("MAIL_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD") or os.environ.get("MAIL_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM") or os.environ.get("MAIL_FROM_ADDRESS", "")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME") or os.environ.get("MAIL_FROM_NAME") or MAILGUN_FROM_NAME
SMTP_AUTH_METHOD = (os.environ.get("SMTP_AUTH_METHOD") or os.environ.get("MAIL_AUTH_METHOD", "")).strip().upper()
SMTP_SECURE = (
    os.environ.get("SMTP_SECURE", "").strip().lower() in {"1", "true", "yes", "on"}
    or MAIL_ENCRYPTION in {"ssl", "smtps"}
)
SMTP_STARTTLS = (
    os.environ.get("SMTP_STARTTLS", "").strip().lower() not in {"0", "false", "no", "off"}
    if "SMTP_STARTTLS" in os.environ
    else MAIL_ENCRYPTION in {"tls", "starttls"} or not SMTP_SECURE
)
SESSION_COOKIE = "arcaneledger_session"
SESSION_DAYS = int(os.environ.get("SESSION_DAYS", "30"))
SESSION_IDLE_MINUTES = int(os.environ.get("SESSION_IDLE_MINUTES", "30") or 30)
EMAIL_VERIFICATION_MINUTES = int(os.environ.get("EMAIL_VERIFICATION_MINUTES", "30") or 30)
PASSWORD_RESET_MINUTES = int(os.environ.get("PASSWORD_RESET_MINUTES", str(EMAIL_VERIFICATION_MINUTES)) or EMAIL_VERIFICATION_MINUTES)
SUPPORTED_SCRYFALL_LANGUAGES = {"en"}
APP_VERSION = "0.5.0 beta"
USER_AGENT = "arcaneledger/0.5.0"
PROCESS_STARTED_AT = datetime.now(timezone.utc).replace(microsecond=0)
COLOR_ORDER = ("W", "U", "B", "R", "G")
CARD_CONDITIONS = (
    "Near Mint",
    "Lightly Played",
    "Moderately Played",
    "Heavily Played",
    "Damaged",
)
DEFAULT_CARD_CONDITION = "Near Mint"
WALLPAPER_MIME_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_WALLPAPER_BYTES = 5 * 1024 * 1024
MAX_NEWS_IMAGE_BYTES = 5 * 1024 * 1024
CONDITION_ORDER = {condition: index for index, condition in enumerate(CARD_CONDITIONS)}
CONTAINER_TYPES = ("binder", "box", "other")
DEFAULT_CONTAINER_TYPE = "other"
THEMES = {
    "light", "dark", "retro", "neon", "red", "blue", "black", "green", "pride",
    "final-fantasy", "spider-man", "airbender",
}
USER_ROLES = {"admin", "contributor", "pro", "normal"}
PRO_SUBSCRIPTION_STATUSES = {"active", "trialing"}
DEFAULT_NORMAL_ROLE_LIMITS = {
    "containers": 4,
    "decks": 10,
    "wishlists": 10,
}
PRO_FEATURE_LIMIT_KEYS = tuple(DEFAULT_NORMAL_ROLE_LIMITS.keys())
ADMIN_EMAILS = {
    email.strip().lower()
    for email in re.split(r"[,;\s]+", os.environ.get("ADMIN_EMAILS", ""))
    if email.strip()
}
DISALLOWED_DISPLAY_NAME_WORDS = {
    "fuck", "shit", "bitch", "cunt", "asshole", "whore", "slut",
    "nigger", "nigga", "fag", "faggot", "retard", "kike", "spic",
    "chink", "gook", "tranny", "nazi", "hitler",
}


def configure_logging():
    logger = logging.getLogger("arcaneledger")
    if logger.handlers:
        return logger
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logger.setLevel(level)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s")
    formatter.converter = time.gmtime
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except OSError:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.exception("Failed to configure file logging at %s", LOG_FILE)
    return logger


LOGGER = configure_logging()


class ForbiddenError(PermissionError):
    pass


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_iso():
    return date.today().isoformat()


def app_timezone():
    if ZoneInfo:
        try:
            return ZoneInfo(APP_TIMEZONE)
        except Exception:
            LOGGER.warning("Invalid APP_TIMEZONE %r; falling back to UTC.", APP_TIMEZONE)
    return timezone.utc


def app_today_iso():
    return datetime.now(app_timezone()).date().isoformat()


def parse_iso_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def parse_iso_datetime(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def month_label(value):
    return value.strftime("%b %Y")


def money(value, fallback=0.0):
    if value is None:
        return fallback
    text = str(value).strip().replace("$", "").replace(",", "")
    if text == "":
        return fallback
    try:
        parsed = float(text)
    except ValueError:
        return fallback
    return parsed


def normalize(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def card_condition(value):
    text = re.sub(r"\s+", " ", (value or "").strip())
    return text if text in CARD_CONDITIONS else DEFAULT_CARD_CONDITION


def bool_int(value):
    if isinstance(value, str):
        return 1 if value.lower() in {"1", "true", "yes", "on", "graded"} else 0
    return 1 if value else 0


def normalize_email(value):
    return re.sub(r"\s+", "", (value or "").strip().lower())


def validate_email(value):
    email = normalize_email(value)
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("Enter a valid email address.")
    return email


def validate_password(value):
    password = value or ""
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters.")
    checks = (
        re.search(r"[a-z]", password),
        re.search(r"[A-Z]", password),
        re.search(r"[0-9]", password),
        re.search(r"[^A-Za-z0-9]", password),
    )
    if sum(1 for check in checks if check) < 3:
        raise ValueError("Password must include at least three of: lowercase, uppercase, number, symbol.")
    return password


def validate_display_name(value):
    name = re.sub(r"\s+", " ", (value or "").strip())
    if len(name) < 2:
        raise ValueError("Enter a display name.")
    if len(name) > 80:
        raise ValueError("Display name must be 80 characters or fewer.")
    if contains_disallowed_name_word(name):
        raise ValueError("Choose a respectful display name.")
    return name


def profile_slug(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return slug[:80].strip("-") or "user"


def unique_profile_slug(conn, name, user_id=None):
    base = profile_slug(name)
    slug = base
    counter = 2
    while True:
        if user_id:
            row = conn.execute("SELECT 1 FROM users WHERE profile_slug = ? AND id != ?", (slug, user_id)).fetchone()
        else:
            row = conn.execute("SELECT 1 FROM users WHERE profile_slug = ?", (slug,)).fetchone()
        if not row:
            return slug
        suffix = f"-{counter}"
        slug = f"{base[:80 - len(suffix)]}{suffix}".strip("-")
        counter += 1


def validate_unique_display_name(conn, name, user_id=None):
    if user_id:
        exists = conn.execute("SELECT 1 FROM users WHERE lower(name) = lower(?) AND id != ?", (name, user_id)).fetchone()
    else:
        exists = conn.execute("SELECT 1 FROM users WHERE lower(name) = lower(?)", (name,)).fetchone()
    if exists:
        raise ValueError("Display name must be unique.")
    return name


def contains_disallowed_name_word(value):
    normalized = re.sub(r"[^a-z0-9]+", " ", (value or "").lower())
    tokens = set(normalized.split())
    compact = normalized.replace(" ", "")
    return bool(tokens & DISALLOWED_DISPLAY_NAME_WORDS or any(word in compact for word in DISALLOWED_DISPLAY_NAME_WORDS if len(word) >= 4))


def validate_user_content_name(value, label, limit):
    name = re.sub(r"\s+", " ", (value or "").strip())
    if not name:
        raise ValueError(f"{label} is required.")
    if len(name) > limit:
        raise ValueError(f"{label} must be {limit} characters or fewer.")
    if contains_disallowed_name_word(name):
        raise ValueError(f"{label} contains language that is not allowed.")
    return name


def validate_optional_email(value):
    email = (value or "").strip()
    return validate_email(email) if email else ""


def role_for_email(email):
    return "admin" if normalize_email(email) in ADMIN_EMAILS else "normal"


def clean_user_role(value):
    role = (value or "normal").strip().lower()
    if role == "paid":
        return "pro"
    return role if role in USER_ROLES else "normal"


def subscription_period_has_ended(period_end):
    ending = parse_iso_datetime(period_end)
    return bool(ending and ending <= datetime.now(timezone.utc))


def subscription_grants_pro(status, period_end="", cancel_at_period_end=False):
    normalized = (status or "").strip().lower()
    if normalized not in PRO_SUBSCRIPTION_STATUSES:
        return False
    return not (cancel_at_period_end and subscription_period_has_ended(period_end))


def effective_user_role(row):
    if not row:
        return "normal"
    if isinstance(row, sqlite3.Row):
        role = clean_user_role(row["role"] if "role" in row.keys() else role_for_email(row["email"]))
        status = row["subscription_status"] if "subscription_status" in row.keys() else ""
        period_end = row["subscription_current_period_end"] if "subscription_current_period_end" in row.keys() else ""
        cancel_at_period_end = bool(row["subscription_cancel_at_period_end"]) if "subscription_cancel_at_period_end" in row.keys() else False
    else:
        role = clean_user_role(row.get("role"))
        status = row.get("subscription_status", "")
        period_end = row.get("subscription_current_period_end", "")
        cancel_at_period_end = bool(row.get("subscription_cancel_at_period_end", False))
    if role == "admin":
        return "admin"
    if role == "contributor":
        return "contributor"
    if role == "pro" or subscription_grants_pro(status, period_end, cancel_at_period_end):
        return "pro"
    return "normal"


def user_role(conn, user_id):
    row = conn.execute(
        """
        SELECT role, email, subscription_status, subscription_current_period_end, subscription_cancel_at_period_end
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    if not row:
        return "normal"
    return effective_user_role(row)


def enforce_role_limit(conn, user_id, table, label, limit_key, incoming=1):
    role = user_role(conn, user_id)
    limit = normal_role_limits(conn).get(limit_key) if role == "normal" else 0
    if not limit:
        return
    count_queries = {
        "containers": "SELECT COUNT(*) AS count FROM containers WHERE user_id = ?",
        "decks": "SELECT COUNT(*) AS count FROM decks WHERE user_id = ?",
        "wishlists": "SELECT COUNT(*) AS count FROM wishlists WHERE user_id = ?",
    }
    query = count_queries.get(table)
    if not query:
        raise ValueError("Unsupported role-limit target.")
    current = conn.execute(query, (user_id,)).fetchone()["count"] or 0
    if current + max(0, int(incoming or 0)) > limit:
        raise ValueError(f"Normal accounts can create up to {limit} {label}. Upgrade to Pro for unlimited {label}.")


def site_setting(conn, key, fallback=""):
    row = conn.execute("SELECT value FROM site_settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else fallback


def set_site_setting(conn, key, value):
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO site_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """,
        (key, str(value), timestamp),
    )


def normal_role_limits(conn):
    limits = dict(DEFAULT_NORMAL_ROLE_LIMITS)
    for key, default in DEFAULT_NORMAL_ROLE_LIMITS.items():
        value = site_setting(conn, f"normal_limit_{key}", str(default))
        try:
            limits[key] = max(0, int(value))
        except (TypeError, ValueError):
            limits[key] = default
    return limits


def admin_pro_features_payload(conn):
    limits = normal_role_limits(conn)
    return {
        "limits": limits,
        "features": [
            {
                "key": "containers",
                "label": "Max Number of Containers",
                "normal_limit": limits["containers"],
                "pro_limit": "Unlimited",
            },
            {
                "key": "decks",
                "label": "Max Number of Decks",
                "normal_limit": limits["decks"],
                "pro_limit": "Unlimited",
            },
            {
                "key": "wishlists",
                "label": "Max Number of Wishlists",
                "normal_limit": limits["wishlists"],
                "pro_limit": "Unlimited",
            },
        ],
    }


def update_admin_pro_features(conn, payload):
    current = normal_role_limits(conn)
    incoming = payload.get("limits") or payload
    cleaned = {}
    for key in PRO_FEATURE_LIMIT_KEYS:
        raw = incoming.get(key)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise ValueError("Enter whole-number limits.")
        if value < 0:
            raise ValueError("Limits cannot be negative.")
        if value < current[key]:
            raise ValueError("Cannot reduce.")
        cleaned[key] = value
    for key, value in cleaned.items():
        set_site_setting(conn, f"normal_limit_{key}", value)
    conn.commit()
    return {"ok": True, **admin_pro_features_payload(conn)}


def clean_contact_handle(value, field_name, max_length=80):
    text = re.sub(r"\s+", " ", (value or "").strip())
    if len(text) > max_length:
        raise ValueError(f"{field_name} must be {max_length} characters or fewer.")
    if any(char in text for char in "\r\n<>"):
        raise ValueError(f"{field_name} contains unsupported characters.")
    return text


def clean_contact_url(value):
    text = clean_contact_handle(value, "Website", 160)
    if text and not re.match(r"^https?://", text, flags=re.I):
        text = f"https://{text}"
    parsed = urllib.parse.urlparse(text) if text else None
    if text and (parsed.scheme not in {"http", "https"} or not parsed.netloc or " " in text):
        raise ValueError("Enter a valid website URL.")
    return text


def whatnot_profile_url(username):
    handle = clean_contact_handle(username, "Whatnot username").lstrip("@")
    if not handle:
        return ""
    return f"https://www.whatnot.com/user/{urllib.parse.quote(handle)}"


def clean_whatnot_listing_url(value):
    text = clean_contact_handle(value, "Whatnot listing URL", 260)
    if not text:
        return ""
    if not re.match(r"^https?://", text, flags=re.I):
        text = f"https://{text}"
    parsed = urllib.parse.urlparse(text)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host or " " in text:
        raise ValueError("Enter a valid Whatnot listing URL.")
    if host != "whatnot.com" and not host.endswith(".whatnot.com"):
        raise ValueError("Whatnot listing URL must be on whatnot.com.")
    return urllib.parse.urlunparse(("https", parsed.netloc, parsed.path or "/", "", parsed.query, ""))


def clean_profile_text(value, limit=1200):
    text = re.sub(r"\r\n?", "\n", (value or "").strip())
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    if len(text) > limit:
        raise ValueError(f"About me must be {limit} characters or fewer.")
    return text


def clean_purchase_detail(value, label, limit=120):
    text = re.sub(r"\s+", " ", (value or "").strip())
    if len(text) > limit:
        raise ValueError(f"{label} must be {limit} characters or fewer.")
    if any(char in text for char in "\r\n<>"):
        raise ValueError(f"{label} contains unsupported characters.")
    return text


def clean_report_reason(value):
    text = re.sub(r"\r\n?", "\n", (value or "").strip())
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    if not text:
        raise ValueError("Report reason is required.")
    if len(text) > 1200:
        raise ValueError("Report reason must be 1200 characters or fewer.")
    return text


def clean_profile_image(value):
    text = (value or "").strip()
    if not text:
        return ""
    if re.match(r"^https://(?:www\.)?gravatar\.com/avatar/[a-f0-9]{32}(?:\?[A-Za-z0-9._~=&%-]*)?$", text, flags=re.I):
        return text[:500]
    if len(text) > 900_000:
        raise ValueError("Profile picture is too large. Use an image under about 650 KB.")
    if not re.match(r"^data:image/(png|jpe?g|webp|gif);base64,[A-Za-z0-9+/=]+$", text, flags=re.I):
        raise ValueError("Profile picture must be a PNG, JPG, WebP, or GIF image.")
    return text


def gravatar_url(email, size=256):
    normalized = normalize_email(email)
    if not normalized:
        return ""
    digest = hashlib.md5(normalized.encode("utf-8"), usedforsecurity=False).hexdigest()
    return f"https://www.gravatar.com/avatar/{digest}?s={int(size)}&d=identicon&r=g"


def hash_password(password, salt=None, iterations=260000):
    salt_bytes = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, iterations)
    return f"pbkdf2_sha256${iterations}${base64.b64encode(salt_bytes).decode('ascii')}${base64.b64encode(digest).decode('ascii')}"


def verify_password(password, stored):
    try:
        algorithm, iterations, salt_text, digest_text = (stored or "").split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_text.encode("ascii"))
        expected = base64.b64decode(digest_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def clean_theme(value):
    theme = (value or "light").strip().lower()
    return theme if theme in THEMES else "light"


def scryfall_language(value=None):
    language = (value or SCRYFALL_LANGUAGE or "en").strip().lower()
    return language if language in SUPPORTED_SCRYFALL_LANGUAGES else "en"


def scryfall_query_with_language(query, language=None):
    text = (query or "").strip()
    if re.search(r"\blang:[a-z-]+\b", text, flags=re.IGNORECASE):
        return text
    return f"{text} lang:{scryfall_language(language)}".strip()


def debug_log_status():
    return {
        "path": str(LOG_FILE),
        "level": LOG_LEVEL,
        "max_bytes": LOG_MAX_BYTES,
        "backup_count": LOG_BACKUP_COUNT,
        "exists": LOG_FILE.exists(),
        "size": LOG_FILE.stat().st_size if LOG_FILE.exists() else 0,
    }


def read_log_tail(line_count=200, max_bytes=256 * 1024):
    try:
        line_count = max(1, min(int(line_count or 200), 1000))
    except (TypeError, ValueError):
        line_count = 200
    if not LOG_FILE.exists():
        return {**debug_log_status(), "lines": []}
    with LOG_FILE.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - max_bytes))
        data = handle.read().decode("utf-8", errors="replace")
    lines = data.splitlines()[-line_count:]
    return {**debug_log_status(), "lines": lines}


def file_size(path):
    try:
        return Path(path).stat().st_size
    except OSError:
        return 0


def process_memory_bytes():
    statm_path = Path("/proc/self/statm")
    if statm_path.exists():
        try:
            pages = int(statm_path.read_text(encoding="utf-8").split()[1])
            return pages * os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError, IndexError):
            pass
    try:
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        multiplier = 1024 if sys.platform != "darwin" else 1
        return int(value * multiplier)
    except (ImportError, OSError, ValueError):
        return 0


def system_memory_info():
    meminfo_path = Path("/proc/meminfo")
    if meminfo_path.exists():
        values = {}
        try:
            for line in meminfo_path.read_text(encoding="utf-8").splitlines():
                if ":" not in line:
                    continue
                key, raw = line.split(":", 1)
                number = re.search(r"\d+", raw)
                if number:
                    values[key] = int(number.group(0)) * 1024
        except OSError:
            values = {}
        total = values.get("MemTotal", 0)
        available = values.get("MemAvailable", 0)
        return {
            "total_bytes": total,
            "available_bytes": available,
            "used_bytes": max(0, total - available) if total and available else 0,
        }
    total = 0
    try:
        if hasattr(os, "sysconf"):
            total = int(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    except (OSError, ValueError):
        total = 0
    return {"total_bytes": total, "available_bytes": 0, "used_bytes": 0}


def server_details():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    uptime_seconds = max(0, int((now - PROCESS_STARTED_AT).total_seconds()))
    try:
        load_average = list(os.getloadavg())
    except (AttributeError, OSError):
        load_average = []
    try:
        disk = shutil.disk_usage(DATA_DIR)
        disk_payload = {
            "path": str(DATA_DIR),
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
        }
    except OSError:
        disk_payload = {"path": str(DATA_DIR), "total_bytes": 0, "used_bytes": 0, "free_bytes": 0}
    return {
        "app_version": APP_VERSION,
        "user_agent": USER_AGENT,
        "started_at": PROCESS_STARTED_AT.isoformat().replace("+00:00", "Z"),
        "now": now.isoformat().replace("+00:00", "Z"),
        "uptime_seconds": uptime_seconds,
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "pid": os.getpid(),
        "cpu_count": os.cpu_count() or 0,
        "load_average": load_average,
        "process_memory_bytes": process_memory_bytes(),
        "system_memory": system_memory_info(),
        "disk": disk_payload,
        "database": {
            "path": str(DB_PATH),
            "size_bytes": file_size(DB_PATH),
        },
        "logs": debug_log_status(),
    }


def collector_keys(value):
    raw = str(value or "").strip()
    normalized = normalize(raw)
    keys = {normalized}
    pieces = re.split(r"\s*//\s*", raw)
    if pieces:
        stripped = [piece.lstrip("0") or "0" for piece in pieces]
        keys.add(normalize(" // ".join(stripped)))
        keys.add(normalize("".join(stripped)))
        for piece in stripped:
            keys.add(normalize(piece))
    if raw.isdigit():
        keys.add(str(int(raw)))
    return {key for key in keys if key}


def set_aliases(set_code, set_name):
    aliases = {normalize(set_name)}
    code_aliases = {
        "afin": ["Art Series: FINAL FANTASY", "Final Fantasy Art Series"],
        "afic": ["Final Fantasy Scene Box"],
        "fca": ["Universes Beyond: FINAL FANTASY: Through the Ages", "Final Fantasy: Through the Ages"],
        "fic": ["Commander: FINAL FANTASY", "Final Fantasy Commander"],
        "fin": ["Universes Beyond: FINAL FANTASY", "Final Fantasy"],
        "pfin": ["Final Fantasy Promos", "Universes Beyond: FINAL FANTASY Promos"],
        "sld": ["Secret Lair Drop", "Secret Lair Drop Series"],
        "tfic": ["Commander: FINAL FANTASY Tokens", "Final Fantasy Commander Tokens"],
        "tfin": ["Universes Beyond: FINAL FANTASY Tokens", "Final Fantasy Tokens"],
    }
    for alias in code_aliases.get(set_code, []):
        aliases.add(normalize(alias))
    return aliases


def clean_product_name(value):
    text = value or ""
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\bDouble-Sided Token\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bArt Card\b", "", text, flags=re.IGNORECASE)
    text = text.replace(" - ", " ")
    return re.sub(r"\s+", " ", text).strip()


def product_name_candidates(value):
    raw = value or ""
    cleaned = clean_product_name(raw)
    candidates = {raw, cleaned}
    if " - " in raw:
        candidates.add(raw.split(" - ")[-1])
        candidates.add(clean_product_name(raw.split(" - ")[-1]))
    if " Art Card" in raw:
        candidates.add(raw.replace(" Art Card", ""))
    return [candidate for candidate in candidates if candidate]


def import_variant(source):
    explicit = source_value(source, "variant", "Variant", "finish", "Finish", "foil", "Foil")
    if explicit:
        explicit_text = explicit.strip().lower()
        if explicit_text in {"0", "false", "no", "n", "nonfoil", "non-foil", "normal"}:
            return "Normal"
        if "surge" in explicit_text and "foil" in explicit_text:
            return "Surge Foil"
        if "chocobo" in explicit_text and "foil" in explicit_text:
            return "Chocobo Track Foil"
        if "etched" in explicit_text:
            return "Etched Foil"
        if explicit_text in {"1", "true", "yes", "y"} or "foil" in explicit_text:
            return "Foil"
        return explicit.strip()
    text = " ".join([
        source.get("Variance") or "",
        source.get("Product Name") or "",
    ]).lower()
    if "surge foil" in text:
        return "Surge Foil"
    if "chocobo track foil" in text:
        return "Chocobo Track Foil"
    if "etched" in text:
        return "Etched Foil"
    if "foil" in text or "gold-stamped" in text:
        return "Foil"
    return source.get("Variance") or "Normal"


def lookup_set_candidates(set_name, product_name):
    candidates = [set_name]
    text = f"{set_name} {product_name}".lower()
    if "token" in text:
        if "commander" in text:
            candidates.insert(0, "Commander: FINAL FANTASY Tokens")
        elif "final fantasy" in text:
            candidates.insert(0, "Universes Beyond: FINAL FANTASY Tokens")
    if "secret lair drop series" in text:
        candidates.insert(0, "Secret Lair Drop")
    return candidates


def safe_urlopen(req, timeout=30, allowed_schemes=("https",)):
    url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in allowed_schemes:
        raise ValueError(f"Unsupported URL scheme for outbound request: {parsed.scheme or 'missing'}")
    if not parsed.netloc:
        raise ValueError("Outbound request URL must include a host.")
    return urllib.request.urlopen(req, timeout=timeout)  # nosec B310 - scheme and host are validated above.


def request_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with safe_urlopen(req, timeout=SCRYFALL_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


EMAIL_RE = re.compile(r"^[^@\s<>:]+@[^@\s<>:]+\.[^@\s<>:]+$")


def app_base_domain():
    raw = (APP_BASE_URL or "").strip()
    if raw:
        try:
            parsed = urllib.parse.urlparse(raw if "://" in raw else f"https://{raw}")
            host = parsed.hostname or ""
        except ValueError:
            host = raw.replace("https://", "").replace("http://", "").split("/", 1)[0].split(":", 1)[0]
        if host:
            return host.strip().lower()
    return (MAILGUN_DOMAIN or "").strip().lower()


def default_from_email():
    domain = app_base_domain()
    return f"admin@{domain}" if domain else ""


def sender_email(raw_email, fallback=True):
    raw = (raw_email or "").strip()
    if not raw and fallback:
        raw = default_from_email()
    parsed_name, parsed_email = parseaddr(raw)
    del parsed_name
    email = (parsed_email or raw).strip()
    return email if EMAIL_RE.match(email) else ""


def mailgun_configured():
    return bool(MAILGUN_API_KEY and MAILGUN_DOMAIN and sender_email(MAILGUN_FROM_EMAIL))


def smtp_configured():
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD and sender_email(SMTP_FROM, fallback=False))


def email_status():
    smtp_required = {
        "SMTP_HOST": SMTP_HOST,
        "SMTP_USER": SMTP_USER,
        "SMTP_PASSWORD": SMTP_PASSWORD,
        "SMTP_FROM": SMTP_FROM,
    }
    mailgun_required = {
        "MAILGUN_API_KEY": MAILGUN_API_KEY,
        "MAILGUN_DOMAIN": MAILGUN_DOMAIN,
        "MAILGUN_FROM_EMAIL": sender_email(MAILGUN_FROM_EMAIL),
    }
    return {
        "provider": "smtp" if smtp_configured() else "mailgun",
        "configured": smtp_configured() or mailgun_configured(),
        "smtp": {
            "configured": smtp_configured(),
            "host": SMTP_HOST,
            "port": SMTP_PORT,
            "user": SMTP_USER,
            "from": SMTP_FROM,
            "from_name": SMTP_FROM_NAME,
            "secure": SMTP_SECURE,
            "starttls": SMTP_STARTTLS and not SMTP_SECURE,
            "missing": [name for name, value in smtp_required.items() if not value],
        },
        "mailgun": {
            "configured": mailgun_configured(),
            "api_base": MAILGUN_API_BASE,
            "domain": MAILGUN_DOMAIN,
            "from_email": sender_email(MAILGUN_FROM_EMAIL),
            "from_name": MAILGUN_FROM_NAME,
            "missing": [name for name, value in mailgun_required.items() if not value],
        },
    }


def formatted_sender(email, name=""):
    raw_email = (email or "").strip()
    parsed_name, parsed_email = parseaddr(raw_email)
    clean_email = sender_email(raw_email, fallback=False)
    if not clean_email:
        raise ValueError("From address must be a valid email address, like admin@example.com.")
    clean_name = (name or parsed_name or "").strip()
    if clean_name:
        return formataddr((clean_name, clean_email))
    return clean_email


def mailgun_sender(from_email=None):
    return formatted_sender(from_email or MAILGUN_FROM_EMAIL or default_from_email(), MAILGUN_FROM_NAME)


def mailgun_auth_header():
    token = base64.b64encode(f"api:{MAILGUN_API_KEY}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def mailgun_trace():
    trace = {
        "configured": mailgun_configured(),
        "api_base": MAILGUN_API_BASE,
        "domain": MAILGUN_DOMAIN,
        "from_email": sender_email(MAILGUN_FROM_EMAIL),
        "configured_from_email": MAILGUN_FROM_EMAIL,
        "from_name": MAILGUN_FROM_NAME,
        "api_key_present": bool(MAILGUN_API_KEY),
        "api_key_length": len(MAILGUN_API_KEY or ""),
        "api_key_prefix": (MAILGUN_API_KEY[:8] + "...") if MAILGUN_API_KEY else "",
        "region_hint": "eu" if "api.eu.mailgun.net" in MAILGUN_API_BASE else "us",
        "steps": [],
    }

    def step(name, ok, detail=None, **extra):
        item = {"step": name, "ok": bool(ok)}
        if detail:
            item["detail"] = str(detail)
        item.update(extra)
        trace["steps"].append(item)

    if not mailgun_configured():
        step("configuration", False, "Set MAILGUN_API_KEY, MAILGUN_DOMAIN, and MAILGUN_FROM_EMAIL.")
        return trace

    domain_url = f"{MAILGUN_API_BASE}/domains/{urllib.parse.quote(MAILGUN_DOMAIN)}"
    req = urllib.request.Request(domain_url, method="GET")
    req.add_header("Authorization", mailgun_auth_header())
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", USER_AGENT)
    step("request", True, url=domain_url)
    try:
        with safe_urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
            step("domain_lookup", 200 <= response.status < 300, f"{response.status} {response.reason}")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body[:500]
            if isinstance(parsed, dict):
                domain = parsed.get("domain") or parsed
                if isinstance(domain, dict):
                    step(
                        "domain",
                        True,
                        domain_name=domain.get("name"),
                        state=domain.get("state"),
                        type=domain.get("type"),
                    )
            else:
                step("response", True, str(parsed)[:500])
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        hint = ""
        if exc.code == 401:
            hint = "Mailgun rejected the API key or the API region. Verify private API key and MAILGUN_API_BASE."
        elif exc.code == 404:
            hint = "Mailgun accepted the API key but could not find this domain in that region/account."
        step("domain_lookup", False, f"{exc.code} {detail}", hint=hint)
    except Exception as exc:
        step("error", False, f"{type(exc).__name__}: {exc}")
    return trace


def smtp_sender(from_email=None):
    return formatted_sender(from_email or SMTP_FROM, SMTP_FROM_NAME)


def smtp_response_text(message):
    return message.decode("utf-8", errors="replace") if isinstance(message, bytes) else str(message)


def smtp_login(server):
    if not SMTP_AUTH_METHOD:
        return server.login(SMTP_USER, SMTP_PASSWORD)
    methods = {
        "PLAIN": server.auth_plain,
        "LOGIN": server.auth_login,
    }
    if SMTP_AUTH_METHOD not in methods:
        raise ValueError("SMTP_AUTH_METHOD must be PLAIN or LOGIN.")
    return server.auth(SMTP_AUTH_METHOD, methods[SMTP_AUTH_METHOD])


def smtp_trace():
    trace = {
        "configured": smtp_configured(),
        "driver": MAIL_DRIVER,
        "host": SMTP_HOST,
        "port": SMTP_PORT,
        "user": SMTP_USER,
        "from": SMTP_FROM,
        "from_name": SMTP_FROM_NAME,
        "secure": SMTP_SECURE,
        "starttls": SMTP_STARTTLS and not SMTP_SECURE,
        "auth_method": SMTP_AUTH_METHOD or "default",
        "password_present": bool(SMTP_PASSWORD),
        "password_length": len(SMTP_PASSWORD or ""),
        "steps": [],
    }

    def step(name, ok, detail=None, **extra):
        item = {"step": name, "ok": bool(ok)}
        if detail:
            item["detail"] = str(detail)
        item.update(extra)
        trace["steps"].append(item)

    if not smtp_configured():
        step("configuration", False, "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and SMTP_FROM, or MAIL_HOST, MAIL_USERNAME, MAIL_PASSWORD, and MAIL_FROM_ADDRESS.")
        return trace

    server = None
    try:
        server = smtplib.SMTP_SSL(timeout=30) if SMTP_SECURE else smtplib.SMTP(timeout=30)
        code, message = server.connect(SMTP_HOST, SMTP_PORT)
        step("connect_ssl" if SMTP_SECURE else "connect", 200 <= code < 400, f"{code} {smtp_response_text(message)}")
        if getattr(server, "sock", None):
            try:
                step("socket", True, local=str(server.sock.getsockname()), peer=str(server.sock.getpeername()))
            except OSError as exc:
                step("socket", False, f"{type(exc).__name__}: {exc}")
        code, message = server.ehlo()
        step("ehlo", 200 <= code < 400, f"{code} {smtp_response_text(message)}", features=dict(server.esmtp_features))
        if SMTP_STARTTLS and not SMTP_SECURE:
            code, message = server.starttls()
            step("starttls", 200 <= code < 400, f"{code} {smtp_response_text(message)}")
            if getattr(server, "sock", None) and hasattr(server.sock, "cipher"):
                try:
                    step("tls", True, version=server.sock.version(), cipher=str(server.sock.cipher()))
                except Exception as exc:
                    step("tls", False, f"{type(exc).__name__}: {exc}")
            code, message = server.ehlo()
            step("ehlo_after_starttls", 200 <= code < 400, f"{code} {smtp_response_text(message)}", features=dict(server.esmtp_features))
        auth_methods = (server.esmtp_features.get("auth", "") or "").split()
        step("auth_methods", bool(auth_methods), methods=auth_methods)
        try:
            code, message = server.noop()
            step("noop_before_login", 200 <= code < 400, f"{code} {smtp_response_text(message)}")
        except Exception as exc:
            step("noop_before_login", False, f"{type(exc).__name__}: {exc}")
        step("login_attempt", True, method=SMTP_AUTH_METHOD or "smtplib default")
        code, message = smtp_login(server)
        step("login", 200 <= code < 400, f"{code} {smtp_response_text(message)}")
    except Exception as exc:
        step("error", False, f"{type(exc).__name__}: {exc}")
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
    return trace


def smtp_diagnostics():
    result = {
        "configured": smtp_configured(),
        "host": SMTP_HOST,
        "port": SMTP_PORT,
        "user": SMTP_USER,
        "from": SMTP_FROM,
        "secure": SMTP_SECURE,
        "starttls": SMTP_STARTTLS and not SMTP_SECURE,
        "auth_method": SMTP_AUTH_METHOD or "default",
        "password_present": bool(SMTP_PASSWORD),
        "password_length": len(SMTP_PASSWORD or ""),
        "steps": [],
    }

    def step(name, ok, detail=None):
        result["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail) if detail else ""})

    if not smtp_configured():
        step("configuration", False, "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and SMTP_FROM.")
        return result

    server = None
    try:
        if SMTP_SECURE:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
            step("connect_ssl", True)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
            step("connect", True)
        code, message = server.ehlo()
        step("ehlo", 200 <= code < 400, f"{code} {message.decode('utf-8', errors='replace') if isinstance(message, bytes) else message}")
        if SMTP_STARTTLS and not SMTP_SECURE:
            code, message = server.starttls()
            step("starttls", 200 <= code < 400, f"{code} {message.decode('utf-8', errors='replace') if isinstance(message, bytes) else message}")
            code, message = server.ehlo()
            step("ehlo_after_starttls", 200 <= code < 400, f"{code} {message.decode('utf-8', errors='replace') if isinstance(message, bytes) else message}")
        code, message = smtp_login(server)
        step("login", 200 <= code < 400, f"{code} {message.decode('utf-8', errors='replace') if isinstance(message, bytes) else message}")
    except Exception as exc:
        step("error", False, f"{type(exc).__name__}: {exc}")
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
    return result


def encode_multipart_form(fields, attachments=None):
    boundary = f"----arcaneledger-{secrets.token_hex(16)}"
    parts = []
    for name, value in fields:
        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        parts.append(str(value).encode("utf-8"))
        parts.append(b"\r\n")
    for attachment in attachments or []:
        filename = clean_attachment_filename(attachment.get("filename") or "attachment")
        content_type = attachment.get("content_type") or "application/octet-stream"
        content = attachment.get("content") or b""
        if isinstance(content, str):
            content = content.encode("utf-8")
        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(
            (
                f'Content-Disposition: form-data; name="attachment"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        parts.append(content)
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(parts)


def clean_attachment_filename(value):
    filename = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "attachment")).strip(".-")
    return filename[:120] or "attachment"


def send_email(to_email, subject, text=None, html=None, tags=None, from_email=None, attachments=None):
    if smtp_configured():
        return send_smtp_email(to_email, subject, text, html, from_email=from_email, attachments=attachments)
    if not mailgun_configured():
        raise ValueError("Email is not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and SMTP_FROM, or configure Mailgun API settings.")
    return send_mailgun_email(to_email, subject, text, html, tags, from_email=from_email, attachments=attachments)


def validate_email_message(to_email, subject, text=None, html=None):
    recipient = (to_email or "").strip()
    if "@" not in recipient:
        raise ValueError("A valid recipient email address is required.")
    if not (subject or "").strip():
        raise ValueError("Email subject is required.")
    if not text and not html:
        raise ValueError("Email text or HTML body is required.")
    return recipient, subject.strip()


def send_smtp_email(to_email, subject, text=None, html=None, from_email=None, attachments=None):
    recipient, clean_subject = validate_email_message(to_email, subject, text, html)
    message = EmailMessage()
    message["From"] = smtp_sender(from_email)
    message["To"] = recipient
    message["Subject"] = clean_subject
    message.set_content(text or "")
    if html:
        message.add_alternative(html, subtype="html")
    for attachment in attachments or []:
        content = attachment.get("content") or b""
        if isinstance(content, str):
            content = content.encode("utf-8")
        content_type = attachment.get("content_type") or "application/octet-stream"
        maintype, _, subtype = content_type.partition("/")
        if not subtype:
            maintype, subtype = "application", "octet-stream"
        message.add_attachment(
            content,
            maintype=maintype,
            subtype=subtype,
            filename=clean_attachment_filename(attachment.get("filename") or "attachment"),
        )

    if SMTP_SECURE:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            smtp_login(server)
            server.send_message(message)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            if SMTP_STARTTLS:
                server.starttls()
                server.ehlo()
            smtp_login(server)
            server.send_message(message)
    return {"ok": True, "provider": "smtp", "status": "sent"}


def send_mailgun_email(to_email, subject, text=None, html=None, tags=None, from_email=None, attachments=None):
    recipient, clean_subject = validate_email_message(to_email, subject, text, html)

    fields = [
        ("from", mailgun_sender(from_email)),
        ("to", recipient),
        ("subject", clean_subject),
    ]
    if text:
        fields.append(("text", text))
    if html:
        fields.append(("html", html))
    for tag in tags or []:
        fields.append(("o:tag", tag))

    url = f"{MAILGUN_API_BASE}/{urllib.parse.quote(MAILGUN_DOMAIN)}/messages"
    boundary, body = encode_multipart_form(fields, attachments)
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", mailgun_auth_header())
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", USER_AGENT)

    try:
        with safe_urlopen(req, timeout=30) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        hint = ""
        if exc.code == 401:
            hint = " Verify MAILGUN_API_KEY and MAILGUN_API_BASE. Use a private Mailgun API key, not an SMTP password."
        elif exc.code == 404:
            hint = " Verify MAILGUN_DOMAIN and API region."
        raise ValueError(f"Mailgun error {exc.code} at {url}: {detail}{hint}") from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = body
    return {"ok": True, "provider": "mailgun", "status": status, "response": parsed}


def upsert_set_from_card(conn, card, synced_at):
    conn.execute(
        """
        INSERT INTO sets (code, name, set_type, card_count, released_at, parent_set_code, synced_at)
        VALUES (?, ?, ?, 0, ?, NULL, ?)
        ON CONFLICT(code) DO UPDATE SET
            name = excluded.name,
            set_type = excluded.set_type,
            released_at = excluded.released_at,
            synced_at = excluded.synced_at
        """,
        (
            card.get("set"),
            card.get("set_name") or (card.get("set") or "").upper(),
            card.get("set_type"),
            card.get("released_at"),
            synced_at,
        ),
    )


def normalized_color_list(values):
    colors = []
    for value in values or []:
        if value in COLOR_ORDER and value not in colors:
            colors.append(value)
    return colors


def card_colors(card, field="colors"):
    colors = normalized_color_list(card.get(field))
    if colors:
        return colors
    if field == "colors":
        face_colors = []
        for face in card.get("card_faces") or []:
            face_colors.extend(face.get("colors") or [])
        colors = normalized_color_list(face_colors)
        if colors:
            return colors
    return []


def card_type_category(type_line):
    text = (type_line or "").lower()
    if not text:
        return "Unknown"
    if "token" in text:
        return "Token"
    type_checks = (
        ("land", "Land"),
        ("creature", "Creature"),
        ("planeswalker", "Planeswalker"),
        ("battle", "Battle"),
        ("artifact", "Artifact"),
        ("enchantment", "Enchantment"),
        ("instant", "Instant"),
        ("sorcery", "Sorcery"),
        ("plane", "Plane"),
        ("scheme", "Scheme"),
        ("vanguard", "Vanguard"),
        ("conspiracy", "Conspiracy"),
    )
    for needle, label in type_checks:
        if needle in text:
            return label
    return (type_line or "Other").split("—", 1)[0].strip() or "Other"


def upsert_card(conn, card, synced_at):
    upsert_set_from_card(conn, card, synced_at)
    prices = card.get("prices") or {}
    colors = json.dumps(card_colors(card, "colors"))
    color_identity = json.dumps(card_colors(card, "color_identity"))
    type_category = card_type_category(card.get("type_line"))
    conn.execute(
        """
        INSERT INTO cards (
            scryfall_id, oracle_id, name, set_code, set_name, collector_number, rarity,
            type_line, type_category, colors, color_identity, flavor_name, flavor_text, layout, finishes, image_small, image_normal, image_art, scryfall_uri,
            current_usd, current_usd_foil, current_usd_etched, last_synced_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(scryfall_id) DO UPDATE SET
            oracle_id = excluded.oracle_id,
            name = excluded.name,
            set_code = excluded.set_code,
            set_name = excluded.set_name,
            collector_number = excluded.collector_number,
            rarity = excluded.rarity,
            type_line = excluded.type_line,
            type_category = excluded.type_category,
            colors = excluded.colors,
            color_identity = excluded.color_identity,
            flavor_name = excluded.flavor_name,
            flavor_text = excluded.flavor_text,
            layout = excluded.layout,
            finishes = excluded.finishes,
            image_small = excluded.image_small,
            image_normal = excluded.image_normal,
            image_art = excluded.image_art,
            scryfall_uri = excluded.scryfall_uri,
            current_usd = excluded.current_usd,
            current_usd_foil = excluded.current_usd_foil,
            current_usd_etched = excluded.current_usd_etched,
            last_synced_at = excluded.last_synced_at
        """,
        (
            card.get("id"),
            card.get("oracle_id"),
            card.get("name"),
            card.get("set"),
            card.get("set_name"),
            card.get("collector_number"),
            card.get("rarity"),
            card.get("type_line"),
            type_category,
            colors,
            color_identity,
            card.get("flavor_name"),
            card_text(card, "flavor_text"),
            card.get("layout"),
            ",".join(card.get("finishes") or []),
            card_image(card, "small"),
            card_image(card, "normal"),
            card_image(card, "art_crop"),
            card.get("scryfall_uri"),
            money(prices.get("usd")),
            money(prices.get("usd_foil")),
            money(prices.get("usd_etched")),
            synced_at,
        ),
    )


def upsert_price_snapshot_from_card(conn, card, snapshot_date=None):
    prices = card.get("prices") or {}
    conn.execute(
        """
        INSERT INTO price_snapshots (card_id, snapshot_date, usd, usd_foil, usd_etched)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(card_id, snapshot_date) DO UPDATE SET
            usd = excluded.usd,
            usd_foil = excluded.usd_foil,
            usd_etched = excluded.usd_etched
        """,
        (
            card.get("id"),
            snapshot_date or app_today_iso(),
            money(prices.get("usd")),
            money(prices.get("usd_foil")),
            money(prices.get("usd_etched")),
        ),
    )


def upsert_price_snapshot_from_card_row(conn, row, snapshot_date=None):
    if not row:
        return
    conn.execute(
        """
        INSERT INTO price_snapshots (card_id, snapshot_date, usd, usd_foil, usd_etched)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(card_id, snapshot_date) DO UPDATE SET
            usd = excluded.usd,
            usd_foil = excluded.usd_foil,
            usd_etched = excluded.usd_etched
        """,
        (
            row["scryfall_id"],
            snapshot_date or app_today_iso(),
            money(row["current_usd"]),
            money(row["current_usd_foil"]),
            money(row["current_usd_etched"]),
        ),
    )


def scryfall_price(card, variant="Normal"):
    prices = card.get("prices") or {}
    variant_text = (variant or "").lower()
    if "foil" in variant_text and prices.get("usd_foil"):
        return money(prices.get("usd_foil"))
    if "etched" in variant_text and prices.get("usd_etched"):
        return money(prices.get("usd_etched"))
    return money(prices.get("usd"), fallback=money(prices.get("usd_foil"), fallback=money(prices.get("usd_etched"), fallback=0.0)))


def card_image(card, size):
    if card.get("image_uris"):
        return card["image_uris"].get(size)
    faces = card.get("card_faces") or []
    if faces and faces[0].get("image_uris"):
        return faces[0]["image_uris"].get(size)
    return None


def card_text(card, field):
    if card.get(field):
        return card.get(field)
    faces = card.get("card_faces") or []
    values = [face.get(field) for face in faces if face.get(field)]
    return " // ".join(values) if values else None


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sets (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            set_type TEXT,
            card_count INTEGER DEFAULT 0,
            released_at TEXT,
            parent_set_code TEXT,
            synced_at TEXT NOT NULL,
            cached_at TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'en',
            theme TEXT NOT NULL DEFAULT 'light',
            email_verified INTEGER NOT NULL DEFAULT 0,
            store_share_id TEXT UNIQUE,
            public_email TEXT NOT NULL DEFAULT '',
            contact_whatsapp TEXT NOT NULL DEFAULT '',
            contact_signal TEXT NOT NULL DEFAULT '',
            contact_telegram TEXT NOT NULL DEFAULT '',
            contact_discord TEXT NOT NULL DEFAULT '',
            contact_website TEXT NOT NULL DEFAULT '',
            contact_whatnot TEXT NOT NULL DEFAULT '',
            contact_mtg_arena TEXT NOT NULL DEFAULT '',
            contact_mtgo TEXT NOT NULL DEFAULT '',
            contact_instagram TEXT NOT NULL DEFAULT '',
            contact_bluesky TEXT NOT NULL DEFAULT '',
            contact_threads TEXT NOT NULL DEFAULT '',
            about_me TEXT NOT NULL DEFAULT '',
            profile_image TEXT NOT NULL DEFAULT '',
            default_purchase_price REAL NOT NULL DEFAULT 0.01,
            default_sell_price REAL NOT NULL DEFAULT 0,
            profile_slug TEXT UNIQUE,
            role TEXT NOT NULL DEFAULT 'normal',
            is_banned INTEGER NOT NULL DEFAULT 0,
            last_login_at TEXT,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            stripe_price_id TEXT,
            subscription_plan TEXT NOT NULL DEFAULT '',
            subscription_status TEXT NOT NULL DEFAULT '',
            subscription_current_period_end TEXT,
            subscription_cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
            subscription_canceled_at TEXT,
            subscription_ended_at TEXT,
            subscription_updated_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS stripe_events (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            processed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS stripe_subscription_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stripe_subscription_id TEXT NOT NULL,
            stripe_invoice_id TEXT NOT NULL DEFAULT '',
            period_end TEXT NOT NULL DEFAULT '',
            plan TEXT NOT NULL DEFAULT '',
            sent_at TEXT NOT NULL,
            UNIQUE(user_id, stripe_subscription_id, stripe_invoice_id, period_end),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS email_verifications (
            token_hash TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT
        );

        CREATE TABLE IF NOT EXISTS password_resets (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS profile_friends (
            user_id INTEGER NOT NULL,
            friend_user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_id, friend_user_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (friend_user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS profile_wall_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_user_id INTEGER NOT NULL,
            author_user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (profile_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS profile_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            card_id TEXT,
            deck_id INTEGER,
            variant TEXT NOT NULL DEFAULT 'Normal',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE SET NULL,
            FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS profile_post_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            author_user_id INTEGER NOT NULL,
            parent_comment_id INTEGER,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES profile_posts(id) ON DELETE CASCADE,
            FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_comment_id) REFERENCES profile_post_comments(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS cards (
            scryfall_id TEXT PRIMARY KEY,
            oracle_id TEXT,
            name TEXT NOT NULL,
            set_code TEXT NOT NULL,
            set_name TEXT NOT NULL,
            collector_number TEXT NOT NULL,
            rarity TEXT,
            type_line TEXT,
            type_category TEXT,
            colors TEXT,
            color_identity TEXT,
            flavor_name TEXT,
            flavor_text TEXT,
            layout TEXT,
            finishes TEXT,
            image_small TEXT,
            image_normal TEXT,
            image_art TEXT,
            scryfall_uri TEXT,
            current_usd REAL DEFAULT 0,
            current_usd_foil REAL DEFAULT 0,
            current_usd_etched REAL DEFAULT 0,
            last_synced_at TEXT NOT NULL,
            FOREIGN KEY (set_code) REFERENCES sets(code)
        );

        CREATE TABLE IF NOT EXISTS collection (
            user_id INTEGER,
            card_id TEXT NOT NULL,
            share_id TEXT UNIQUE,
            quantity INTEGER NOT NULL DEFAULT 0,
            acquired_date TEXT,
            paid_price REAL NOT NULL DEFAULT 0.01,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            graded INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id, variant),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS card_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            quantity INTEGER NOT NULL DEFAULT 1,
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            purchase_date TEXT NOT NULL,
            total_price REAL NOT NULL DEFAULT 0.01,
            graded INTEGER NOT NULL DEFAULT 0,
            store_name TEXT NOT NULL DEFAULT '',
            store_location TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS card_meta (
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            favorite INTEGER NOT NULL DEFAULT 0,
            missing_list INTEGER NOT NULL DEFAULT 0,
            wishlist INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id, variant),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS wishlist_cards (
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS wishlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            share_id TEXT UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS wishlist_items (
            wishlist_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            quantity INTEGER NOT NULL DEFAULT 1,
            card_json TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (wishlist_id, card_id, variant),
            FOREIGN KEY (wishlist_id) REFERENCES wishlists(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS favorite_decks (
            user_id INTEGER NOT NULL,
            share_id TEXT NOT NULL,
            deck_name TEXT NOT NULL DEFAULT '',
            deck_url TEXT NOT NULL DEFAULT '',
            owner_name TEXT NOT NULL DEFAULT '',
            card_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, share_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS favorite_store_listings (
            user_id INTEGER NOT NULL,
            seller_user_id INTEGER NOT NULL,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, seller_user_id, card_id, variant, card_condition),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (seller_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS card_sales (
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            quantity INTEGER NOT NULL DEFAULT 1,
            asking_price REAL NOT NULL DEFAULT 0.01,
            whatnot_url TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id, variant, card_condition),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            link_url TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT '',
            source_key TEXT NOT NULL DEFAULT '',
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            read_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS admin_email_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            trigger_key TEXT NOT NULL DEFAULT 'user_created',
            to_email TEXT NOT NULL DEFAULT '%email%',
            from_email TEXT NOT NULL DEFAULT '',
            subject TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS home_announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            starts_on TEXT NOT NULL,
            ends_on TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            admin_user_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            published_at TEXT,
            FOREIGN KEY (admin_user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS news_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'published',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            published_at TEXT NOT NULL DEFAULT '',
            scheduled_at TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS site_wallpapers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            original_name TEXT NOT NULL DEFAULT '',
            mime_type TEXT NOT NULL,
            size_bytes INTEGER NOT NULL DEFAULT 0,
            admin_user_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (admin_user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS card_sale_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            quantity INTEGER NOT NULL DEFAULT 1,
            sold_date TEXT NOT NULL,
            sold_price_each REAL NOT NULL DEFAULT 0.01,
            asking_price_each REAL NOT NULL DEFAULT 0.01,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS inventory_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            adjustment_type TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            adjustment_date TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            usd REAL DEFAULT 0,
            usd_foil REAL DEFAULT 0,
            usd_etched REAL DEFAULT 0,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE,
            UNIQUE(card_id, snapshot_date)
        );

        CREATE TABLE IF NOT EXISTS card_notes (
            user_id INTEGER NOT NULL,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            notes TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id, variant),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS card_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS card_comment_votes (
            comment_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (comment_id, user_id),
            FOREIGN KEY (comment_id) REFERENCES card_comments(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS content_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_user_id INTEGER NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            resolution TEXT NOT NULL DEFAULT '',
            admin_user_id INTEGER,
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (reporter_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (admin_user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            share_id TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            internal_notes TEXT NOT NULL DEFAULT '',
            external_notes TEXT NOT NULL DEFAULT '',
            is_private INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS deck_cards (
            deck_id INTEGER NOT NULL,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            quantity INTEGER NOT NULL DEFAULT 1,
            added_at TEXT NOT NULL,
            PRIMARY KEY (deck_id, card_id, variant),
            FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS containers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            share_id TEXT UNIQUE,
            name TEXT NOT NULL,
            storage_type TEXT NOT NULL DEFAULT 'other',
            capacity INTEGER NOT NULL DEFAULT 0,
            strict_unique INTEGER NOT NULL DEFAULT 0,
            location TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS container_cards (
            container_id INTEGER NOT NULL,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            quantity INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (container_id, card_id, variant, card_condition),
            FOREIGN KEY (container_id) REFERENCES containers(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_cards_lookup ON cards(set_code, collector_number, name);
        CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
        CREATE INDEX IF NOT EXISTS idx_collection_quantity ON collection(user_id, quantity);
        CREATE INDEX IF NOT EXISTS idx_card_purchases_card ON card_purchases(user_id, card_id, variant, purchase_date);
        CREATE INDEX IF NOT EXISTS idx_wishlist_items_user_card ON wishlist_items(user_id, card_id, variant);
        CREATE INDEX IF NOT EXISTS idx_deck_cards_card ON deck_cards(card_id, variant);
        CREATE INDEX IF NOT EXISTS idx_container_cards_card ON container_cards(card_id, variant, card_condition);
        CREATE INDEX IF NOT EXISTS idx_card_sales_card ON card_sales(user_id, card_id, variant, card_condition);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_notifications_source ON notifications(user_id, source_type, source_key);
        CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, updated_at);
        CREATE INDEX IF NOT EXISTS idx_admin_email_templates_trigger ON admin_email_templates(trigger_key);
        CREATE INDEX IF NOT EXISTS idx_home_announcements_status_dates ON home_announcements(status, starts_on, ends_on);
        CREATE INDEX IF NOT EXISTS idx_news_posts_status_date ON news_posts(status, published_at DESC, id DESC);
        CREATE INDEX IF NOT EXISTS idx_news_posts_author ON news_posts(author_user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_card_sale_journal_card ON card_sale_journal(user_id, card_id, variant, card_condition, sold_date);
        CREATE INDEX IF NOT EXISTS idx_inventory_adjustments_card ON inventory_adjustments(user_id, card_id, variant, card_condition, adjustment_date);
        CREATE INDEX IF NOT EXISTS idx_snapshots_date ON price_snapshots(snapshot_date);
        CREATE INDEX IF NOT EXISTS idx_card_notes_card ON card_notes(card_id, variant);
        CREATE INDEX IF NOT EXISTS idx_card_comments_card ON card_comments(card_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_card_comment_votes_user ON card_comment_votes(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_content_reports_status ON content_reports(status, created_at);
        CREATE INDEX IF NOT EXISTS idx_content_reports_target ON content_reports(target_type, target_id);
        CREATE INDEX IF NOT EXISTS idx_profile_friends_user ON profile_friends(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_profile_wall_user ON profile_wall_messages(profile_user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_profile_posts_user ON profile_posts(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_profile_comments_post ON profile_post_comments(post_id, created_at);
        """
    )
    migrate_sets_schema(conn)
    migrate_cards_schema(conn)
    migrate_collection_schema(conn)
    migrate_card_meta_schema(conn)
    migrate_purchases_schema(conn)
    migrate_decks_schema(conn)
    migrate_containers_schema(conn)
    migrate_card_sales_schema(conn)
    migrate_notifications_schema(conn)
    migrate_profile_social_schema(conn)
    migrate_card_comments_schema(conn)
    migrate_content_reports_schema(conn)
    migrate_news_schema(conn)
    migrate_user_schema(conn)
    for key, value in DEFAULT_NORMAL_ROLE_LIMITS.items():
        if not conn.execute("SELECT 1 FROM site_settings WHERE key = ?", (f"normal_limit_{key}",)).fetchone():
            set_site_setting(conn, f"normal_limit_{key}", value)
    ensure_collection_share_ids(conn)
    ensure_deck_share_ids(conn)
    ensure_wishlist_share_ids(conn)
    ensure_container_share_ids(conn)
    conn.commit()


def migrate_sets_schema(conn):
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(sets)").fetchall()}
    if "cached_at" not in columns:
        conn.execute("ALTER TABLE sets ADD COLUMN cached_at TEXT")


def migrate_cards_schema(conn):
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(cards)").fetchall()}
    if "flavor_name" not in columns:
        conn.execute("ALTER TABLE cards ADD COLUMN flavor_name TEXT")
    if "flavor_text" not in columns:
        conn.execute("ALTER TABLE cards ADD COLUMN flavor_text TEXT")
    if "type_category" not in columns:
        conn.execute("ALTER TABLE cards ADD COLUMN type_category TEXT")
        conn.execute("UPDATE cards SET type_category = COALESCE(NULLIF(type_category, ''), CASE WHEN type_line IS NULL OR trim(type_line) = '' THEN 'Unknown' ELSE type_line END)")
    if "colors" not in columns:
        conn.execute("ALTER TABLE cards ADD COLUMN colors TEXT")
    if "color_identity" not in columns:
        conn.execute("ALTER TABLE cards ADD COLUMN color_identity TEXT")
    conn.execute(
        """
        UPDATE cards
        SET type_category = CASE
            WHEN type_category IS NOT NULL AND trim(type_category) != '' AND type_category != type_line THEN type_category
            WHEN lower(COALESCE(type_line, '')) LIKE '%token%' THEN 'Token'
            WHEN lower(COALESCE(type_line, '')) LIKE '%land%' THEN 'Land'
            WHEN lower(COALESCE(type_line, '')) LIKE '%creature%' THEN 'Creature'
            WHEN lower(COALESCE(type_line, '')) LIKE '%planeswalker%' THEN 'Planeswalker'
            WHEN lower(COALESCE(type_line, '')) LIKE '%battle%' THEN 'Battle'
            WHEN lower(COALESCE(type_line, '')) LIKE '%artifact%' THEN 'Artifact'
            WHEN lower(COALESCE(type_line, '')) LIKE '%enchantment%' THEN 'Enchantment'
            WHEN lower(COALESCE(type_line, '')) LIKE '%instant%' THEN 'Instant'
            WHEN lower(COALESCE(type_line, '')) LIKE '%sorcery%' THEN 'Sorcery'
            WHEN type_line IS NULL OR trim(type_line) = '' THEN 'Unknown'
            ELSE trim(type_line)
        END
        WHERE type_category IS NULL
           OR trim(type_category) = ''
           OR type_category = type_line
        """
    )


def migrate_collection_schema(conn):
    columns = conn.execute("PRAGMA table_info(collection)").fetchall()
    column_names = {col["name"] for col in columns}
    if "graded" not in column_names:
        conn.execute("ALTER TABLE collection ADD COLUMN graded INTEGER NOT NULL DEFAULT 0")
    placeholders = ", ".join("?" for _ in CARD_CONDITIONS)
    conn.execute(
        f"""
        UPDATE collection
        SET card_condition = ?
        WHERE card_condition IS NULL
           OR trim(card_condition) = ''
           OR card_condition NOT IN ({placeholders})
        """,
        (DEFAULT_CARD_CONDITION, *CARD_CONDITIONS),
    )
    if "user_id" in column_names:
        return
    card_id_pk = [col for col in columns if col["name"] == "card_id" and col["pk"] == 1]
    variant_pk = [col for col in columns if col["name"] == "variant" and col["pk"] == 2]
    if not card_id_pk or variant_pk:
        if "share_id" not in column_names:
            conn.execute("ALTER TABLE collection ADD COLUMN share_id TEXT")
        return
    conn.executescript(
        """
        ALTER TABLE collection RENAME TO collection_old;
        CREATE TABLE collection (
            card_id TEXT NOT NULL,
            share_id TEXT UNIQUE,
            quantity INTEGER NOT NULL DEFAULT 0,
            acquired_date TEXT,
            paid_price REAL NOT NULL DEFAULT 0.01,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            graded INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (card_id, variant),
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );
        INSERT INTO collection (card_id, quantity, acquired_date, paid_price, variant, card_condition, graded, notes, updated_at)
        SELECT card_id, quantity, acquired_date, paid_price, COALESCE(NULLIF(variant, ''), 'Normal'), COALESCE(NULLIF(card_condition, ''), 'Near Mint'), graded, notes, updated_at
        FROM collection_old;
        DROP TABLE collection_old;
        """
    )


def migrate_card_meta_schema(conn):
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(card_meta)").fetchall()}
    if "missing_list" not in columns:
        conn.execute("ALTER TABLE card_meta ADD COLUMN missing_list INTEGER NOT NULL DEFAULT 0")
    if "wishlist" not in columns:
        conn.execute("ALTER TABLE card_meta ADD COLUMN wishlist INTEGER NOT NULL DEFAULT 0")


def migrate_purchases_schema(conn):
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(card_purchases)").fetchall()}
    if "card_condition" not in columns:
        conn.execute("ALTER TABLE card_purchases ADD COLUMN card_condition TEXT NOT NULL DEFAULT 'Near Mint'")
    if "graded" not in columns:
        conn.execute("ALTER TABLE card_purchases ADD COLUMN graded INTEGER NOT NULL DEFAULT 0")
    if "store_name" not in columns:
        conn.execute("ALTER TABLE card_purchases ADD COLUMN store_name TEXT NOT NULL DEFAULT ''")
    if "store_location" not in columns:
        conn.execute("ALTER TABLE card_purchases ADD COLUMN store_location TEXT NOT NULL DEFAULT ''")
    if "notes" not in columns:
        conn.execute("ALTER TABLE card_purchases ADD COLUMN notes TEXT NOT NULL DEFAULT ''")
    conn.execute(
        f"""
        UPDATE card_purchases
        SET card_condition = ?
        WHERE card_condition IS NULL
           OR trim(card_condition) = ''
           OR card_condition NOT IN ({", ".join("?" for _ in CARD_CONDITIONS)})
        """,
        (DEFAULT_CARD_CONDITION, *CARD_CONDITIONS),
    )
    conn.execute(
        """
        INSERT INTO card_purchases (card_id, variant, quantity, card_condition, purchase_date, total_price, graded, store_name, store_location, created_at)
        SELECT col.card_id,
               COALESCE(NULLIF(col.variant, ''), 'Normal'),
               col.quantity,
               COALESCE(NULLIF(col.card_condition, ''), ?),
               COALESCE(NULLIF(col.acquired_date, ''), ?),
               MAX(col.quantity * COALESCE(col.paid_price, 0.01), 0.01),
               COALESCE(col.graded, 0),
               '',
               '',
               COALESCE(NULLIF(col.updated_at, ''), ?)
        FROM collection col
        WHERE col.quantity > 0
          AND NOT EXISTS (
              SELECT 1
              FROM card_purchases cp
              WHERE cp.card_id = col.card_id
                AND cp.variant = COALESCE(NULLIF(col.variant, ''), 'Normal')
          )
        """,
        (DEFAULT_CARD_CONDITION, today_iso(), now_iso()),
    )


def migrate_decks_schema(conn):
    deck_columns = {col["name"] for col in conn.execute("PRAGMA table_info(decks)").fetchall()}
    if "description" not in deck_columns:
        conn.execute("ALTER TABLE decks ADD COLUMN description TEXT NOT NULL DEFAULT ''")
    if "internal_notes" not in deck_columns:
        conn.execute("ALTER TABLE decks ADD COLUMN internal_notes TEXT NOT NULL DEFAULT ''")
    if "external_notes" not in deck_columns:
        conn.execute("ALTER TABLE decks ADD COLUMN external_notes TEXT NOT NULL DEFAULT ''")
    if "is_private" not in deck_columns:
        conn.execute("ALTER TABLE decks ADD COLUMN is_private INTEGER NOT NULL DEFAULT 0")
    deck_card_columns = {col["name"] for col in conn.execute("PRAGMA table_info(deck_cards)").fetchall()}
    if "quantity" not in deck_card_columns:
        conn.execute("ALTER TABLE deck_cards ADD COLUMN quantity INTEGER NOT NULL DEFAULT 1")
    conn.execute(
        """
        UPDATE deck_cards
        SET quantity = 1
        WHERE quantity IS NULL OR quantity < 1
        """
    )


def migrate_containers_schema(conn):
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(containers)").fetchall()}
    if "share_id" not in columns:
        conn.execute("ALTER TABLE containers ADD COLUMN share_id TEXT")
    if "storage_type" not in columns:
        conn.execute("ALTER TABLE containers ADD COLUMN storage_type TEXT NOT NULL DEFAULT 'other'")
    if "capacity" not in columns:
        conn.execute("ALTER TABLE containers ADD COLUMN capacity INTEGER NOT NULL DEFAULT 0")
    if "strict_unique" not in columns:
        conn.execute("ALTER TABLE containers ADD COLUMN strict_unique INTEGER NOT NULL DEFAULT 0")
    placeholders = ", ".join("?" for _ in CONTAINER_TYPES)
    conn.execute(
        f"""
        UPDATE containers
        SET storage_type = ?
        WHERE storage_type IS NULL
           OR trim(storage_type) = ''
           OR storage_type NOT IN ({placeholders})
        """,
        (DEFAULT_CONTAINER_TYPE, *CONTAINER_TYPES),
    )
    conn.execute(
        """
        UPDATE containers
        SET capacity = 0
        WHERE capacity IS NULL OR capacity < 0
        """
    )
    conn.execute(
        """
        UPDATE containers
        SET strict_unique = 0
        WHERE strict_unique IS NULL OR strict_unique NOT IN (0, 1)
        """
    )
    card_columns = table_columns(conn, "container_cards")
    card_pk = table_pk(conn, "container_cards")
    if "card_condition" not in card_columns or card_pk != ["container_id", "card_id", "variant", "card_condition"]:
        condition_select = "COALESCE(NULLIF(card_condition, ''), 'Near Mint')" if "card_condition" in card_columns else "'Near Mint'"
        conn.execute("DROP TABLE IF EXISTS container_cards_condition_migration")
        conn.execute(
            """
            CREATE TABLE container_cards_condition_migration (
                container_id INTEGER NOT NULL,
                card_id TEXT NOT NULL,
                variant TEXT NOT NULL DEFAULT 'Normal',
                card_condition TEXT NOT NULL DEFAULT 'Near Mint',
                quantity INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (container_id, card_id, variant, card_condition),
                FOREIGN KEY (container_id) REFERENCES containers(id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            f"""
            INSERT OR REPLACE INTO container_cards_condition_migration (
                container_id, card_id, variant, card_condition, quantity, updated_at
            )
            SELECT container_id,
                   card_id,
                   COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
                   {condition_select} AS card_condition,
                   COALESCE(SUM(quantity), 0) AS quantity,
                   COALESCE(MAX(updated_at), ?) AS updated_at
            FROM container_cards
            GROUP BY container_id, card_id, COALESCE(NULLIF(variant, ''), 'Normal'), {condition_select}
            """,
            (now_iso(),),
        )
        conn.execute("DROP TABLE container_cards")
        conn.execute("ALTER TABLE container_cards_condition_migration RENAME TO container_cards")
    conn.execute("DROP INDEX IF EXISTS idx_container_cards_card")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_container_cards_card ON container_cards(card_id, variant, card_condition)")


def migrate_card_sales_schema(conn):
    columns = conn.execute("PRAGMA table_info(card_sales)").fetchall()
    column_names = {col["name"] for col in columns}
    if "user_id" in column_names:
        if "whatnot_url" not in column_names:
            conn.execute("ALTER TABLE card_sales ADD COLUMN whatnot_url TEXT NOT NULL DEFAULT ''")
        conn.execute("UPDATE card_sales SET whatnot_url = '' WHERE whatnot_url IS NULL")
        placeholders = ", ".join("?" for _ in CARD_CONDITIONS)
        conn.execute(
            f"""
            UPDATE card_sales
            SET card_condition = ?
            WHERE card_condition IS NULL
               OR trim(card_condition) = ''
               OR card_condition NOT IN ({placeholders})
            """,
            (DEFAULT_CARD_CONDITION, *CARD_CONDITIONS),
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_card_sales_card ON card_sales(user_id, card_id, variant, card_condition)"
        )
        return
    condition_pk = [col for col in columns if col["name"] == "card_condition" and col["pk"] == 3]
    if "card_condition" not in column_names or not condition_pk:
        conn.executescript(
            """
            ALTER TABLE card_sales RENAME TO card_sales_old;
            CREATE TABLE card_sales (
                card_id TEXT NOT NULL,
                variant TEXT NOT NULL DEFAULT 'Normal',
                card_condition TEXT NOT NULL DEFAULT 'Near Mint',
                quantity INTEGER NOT NULL DEFAULT 1,
                asking_price REAL NOT NULL DEFAULT 0.01,
                whatnot_url TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (card_id, variant, card_condition),
                FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
            );
            """
        )
        whatnot_select = "COALESCE(whatnot_url, '')" if "whatnot_url" in column_names else "''"
        if "card_condition" in column_names:
            conn.execute(
                f"""
                INSERT INTO card_sales (card_id, variant, card_condition, quantity, asking_price, whatnot_url, updated_at)
                SELECT card_id,
                       COALESCE(NULLIF(variant, ''), 'Normal'),
                       COALESCE(NULLIF(card_condition, ''), 'Near Mint'),
                       quantity,
                       asking_price,
                       {whatnot_select},
                       updated_at
                FROM card_sales_old
                """
            )
        else:
            conn.execute(
                f"""
                INSERT INTO card_sales (card_id, variant, card_condition, quantity, asking_price, whatnot_url, updated_at)
                SELECT card_id,
                       COALESCE(NULLIF(variant, ''), 'Normal'),
                       'Near Mint',
                       quantity,
                       asking_price,
                       {whatnot_select},
                       updated_at
                FROM card_sales_old
                """
            )
        conn.execute("DROP TABLE card_sales_old")
    placeholders = ", ".join("?" for _ in CARD_CONDITIONS)
    conn.execute(
        f"""
        UPDATE card_sales
        SET card_condition = ?
        WHERE card_condition IS NULL
           OR trim(card_condition) = ''
           OR card_condition NOT IN ({placeholders})
        """,
        (DEFAULT_CARD_CONDITION, *CARD_CONDITIONS),
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_card_sales_card ON card_sales(card_id, variant, card_condition)"
    )
    if "whatnot_url" not in table_columns(conn, "card_sales"):
        conn.execute("ALTER TABLE card_sales ADD COLUMN whatnot_url TEXT NOT NULL DEFAULT ''")
    conn.execute("UPDATE card_sales SET whatnot_url = '' WHERE whatnot_url IS NULL")


def table_columns(conn, table):
    return {col["name"] for col in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def table_pk(conn, table):
    return [col["name"] for col in sorted(conn.execute(f"PRAGMA table_info({table})").fetchall(), key=lambda col: col["pk"]) if col["pk"]]


def migrate_collection_user_schema(conn):
    columns = table_columns(conn, "collection")
    if "user_id" in columns and table_pk(conn, "collection") == ["user_id", "card_id", "variant"]:
        return
    conn.executescript(
        """
        ALTER TABLE collection RENAME TO collection_old_user_migration;
        CREATE TABLE collection (
            user_id INTEGER,
            card_id TEXT NOT NULL,
            share_id TEXT UNIQUE,
            quantity INTEGER NOT NULL DEFAULT 0,
            acquired_date TEXT,
            paid_price REAL NOT NULL DEFAULT 0.01,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            graded INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id, variant),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );
        """
    )
    user_select = "user_id" if "user_id" in columns else "NULL"
    share_select = "share_id" if "share_id" in columns else "NULL"
    graded_select = "graded" if "graded" in columns else "0"
    notes_select = "notes" if "notes" in columns else "NULL"
    conn.execute(
        f"""
        INSERT INTO collection (user_id, card_id, share_id, quantity, acquired_date, paid_price, variant, card_condition, graded, notes, updated_at)
        SELECT {user_select}, card_id, {share_select}, quantity, acquired_date, paid_price,
               COALESCE(NULLIF(variant, ''), 'Normal'),
               COALESCE(NULLIF(card_condition, ''), ?),
               {graded_select}, {notes_select}, updated_at
        FROM collection_old_user_migration
        """,
        (DEFAULT_CARD_CONDITION,),
    )
    conn.execute("DROP TABLE collection_old_user_migration")


def migrate_card_meta_user_schema(conn):
    columns = table_columns(conn, "card_meta")
    if "user_id" in columns and table_pk(conn, "card_meta") == ["user_id", "card_id", "variant"]:
        return
    conn.executescript(
        """
        ALTER TABLE card_meta RENAME TO card_meta_old_user_migration;
        CREATE TABLE card_meta (
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            favorite INTEGER NOT NULL DEFAULT 0,
            missing_list INTEGER NOT NULL DEFAULT 0,
            wishlist INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id, variant),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );
        """
    )
    user_select = "user_id" if "user_id" in columns else "NULL"
    missing_select = "missing_list" if "missing_list" in columns else "0"
    wishlist_select = "wishlist" if "wishlist" in columns else "0"
    conn.execute(
        f"""
        INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, wishlist, updated_at)
        SELECT {user_select}, card_id, COALESCE(NULLIF(variant, ''), 'Normal'),
               COALESCE(favorite, 0), COALESCE({missing_select}, 0), COALESCE({wishlist_select}, 0), updated_at
        FROM card_meta_old_user_migration
        """
    )
    conn.execute("DROP TABLE card_meta_old_user_migration")


def migrate_wishlist_cards_user_schema(conn):
    columns = table_columns(conn, "wishlist_cards")
    if "user_id" in columns and table_pk(conn, "wishlist_cards") == ["user_id", "card_id"]:
        return
    conn.executescript(
        """
        ALTER TABLE wishlist_cards RENAME TO wishlist_cards_old_user_migration;
        CREATE TABLE wishlist_cards (
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    user_select = "user_id" if "user_id" in columns else "NULL"
    conn.execute(
        f"""
        INSERT INTO wishlist_cards (user_id, card_id, variant, card_json, updated_at)
        SELECT {user_select}, card_id, COALESCE(NULLIF(variant, ''), 'Normal'), card_json, updated_at
        FROM wishlist_cards_old_user_migration
        """
    )
    conn.execute("DROP TABLE wishlist_cards_old_user_migration")


def migrate_wishlists_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS wishlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            share_id TEXT UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS wishlist_items (
            wishlist_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            quantity INTEGER NOT NULL DEFAULT 1,
            card_json TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (wishlist_id, card_id, variant),
            FOREIGN KEY (wishlist_id) REFERENCES wishlists(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    if "share_id" not in table_columns(conn, "wishlists"):
        conn.execute("ALTER TABLE wishlists ADD COLUMN share_id TEXT")
    if "quantity" not in table_columns(conn, "wishlist_items"):
        conn.execute("ALTER TABLE wishlist_items ADD COLUMN quantity INTEGER NOT NULL DEFAULT 1")
    conn.execute(
        """
        UPDATE wishlist_items
        SET quantity = 1
        WHERE quantity IS NULL OR quantity < 1
        """
    )


def migrate_favorite_decks_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS favorite_decks (
            user_id INTEGER NOT NULL,
            share_id TEXT NOT NULL,
            deck_name TEXT NOT NULL DEFAULT '',
            deck_url TEXT NOT NULL DEFAULT '',
            owner_name TEXT NOT NULL DEFAULT '',
            card_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, share_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )


def migrate_favorite_store_listings_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS favorite_store_listings (
            user_id INTEGER NOT NULL,
            seller_user_id INTEGER NOT NULL,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, seller_user_id, card_id, variant, card_condition),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (seller_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_favorite_store_user ON favorite_store_listings(user_id, updated_at)")
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_favorite_store_listing
        ON favorite_store_listings(seller_user_id, card_id, variant, card_condition)
        """
    )


def cross_entity_name_exists(conn, user_id, name, exclude_table=None, exclude_id=None):
    normalized_name = re.sub(r"\s+", " ", (name or "").strip())
    if not normalized_name:
        return False
    for table in ("decks", "containers", "wishlists"):
        params = [user_id, normalized_name]
        exclude_sql = ""
        if exclude_table == table and exclude_id is not None:
            exclude_sql = " AND id != ?"
            params.append(exclude_id)
        if conn.execute(
            f"SELECT 1 FROM {table} WHERE user_id = ? AND lower(name) = lower(?) {exclude_sql} LIMIT 1",
            params,
        ).fetchone():
            return True
    return False


def unique_default_wishlist_name(conn, user_id):
    base = "Wishlist"
    candidate = base
    suffix = 2
    while cross_entity_name_exists(conn, user_id, candidate):
        candidate = f"{base} {suffix}"
        suffix += 1
    return candidate


def ensure_default_wishlist(conn, user_id):
    row = conn.execute(
        "SELECT id FROM wishlists WHERE user_id = ? ORDER BY created_at, id LIMIT 1",
        (user_id,),
    ).fetchone()
    if row:
        return row["id"]
    timestamp = now_iso()
    cursor = conn.execute(
        "INSERT INTO wishlists (user_id, share_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, new_wishlist_share_id(conn), unique_default_wishlist_name(conn, user_id), timestamp, timestamp),
    )
    return cursor.lastrowid


def migrate_legacy_wishlist_for_user(conn, user_id):
    wishlist_id = None
    timestamp = now_iso()
    meta_rows = conn.execute(
        """
        SELECT card_id, COALESCE(NULLIF(variant, ''), 'Normal') AS variant, updated_at
        FROM card_meta
        WHERE user_id = ? AND COALESCE(wishlist, 0) = 1
        """,
        (user_id,),
    ).fetchall()
    card_rows = conn.execute(
        """
        SELECT card_id, COALESCE(NULLIF(variant, ''), 'Normal') AS variant, card_json, updated_at
        FROM wishlist_cards
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchall()
    if not meta_rows and not card_rows:
        return
    wishlist_id = ensure_default_wishlist(conn, user_id)
    for row in meta_rows:
        conn.execute(
            """
            INSERT INTO wishlist_items (wishlist_id, user_id, card_id, variant, card_json, updated_at)
            VALUES (?, ?, ?, ?, NULL, ?)
            ON CONFLICT(wishlist_id, card_id, variant) DO NOTHING
            """,
            (wishlist_id, user_id, row["card_id"], row["variant"], row["updated_at"] or timestamp),
        )
    for row in card_rows:
        conn.execute(
            """
            INSERT INTO wishlist_items (wishlist_id, user_id, card_id, variant, card_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(wishlist_id, card_id, variant) DO UPDATE SET
                card_json = COALESCE(excluded.card_json, wishlist_items.card_json),
                updated_at = excluded.updated_at
            """,
            (wishlist_id, user_id, row["card_id"], row["variant"], row["card_json"], row["updated_at"] or timestamp),
        )


def migrate_legacy_wishlists(conn):
    user_ids = {
        row["user_id"]
        for row in conn.execute(
            """
            SELECT user_id FROM card_meta WHERE user_id IS NOT NULL AND COALESCE(wishlist, 0) = 1
            UNION
            SELECT user_id FROM wishlist_cards WHERE user_id IS NOT NULL
            """
        ).fetchall()
    }
    for user_id in sorted(user_ids):
        migrate_legacy_wishlist_for_user(conn, user_id)


def migrate_card_sales_user_schema(conn):
    columns = table_columns(conn, "card_sales")
    if "user_id" in columns and table_pk(conn, "card_sales") == ["user_id", "card_id", "variant", "card_condition"]:
        if "whatnot_url" not in columns:
            conn.execute("ALTER TABLE card_sales ADD COLUMN whatnot_url TEXT NOT NULL DEFAULT ''")
        conn.execute("UPDATE card_sales SET whatnot_url = '' WHERE whatnot_url IS NULL")
        return
    conn.executescript(
        """
        ALTER TABLE card_sales RENAME TO card_sales_old_user_migration;
        CREATE TABLE card_sales (
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            quantity INTEGER NOT NULL DEFAULT 1,
            asking_price REAL NOT NULL DEFAULT 0.01,
            whatnot_url TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id, variant, card_condition),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );
        """
    )
    user_select = "user_id" if "user_id" in columns else "NULL"
    whatnot_select = "COALESCE(whatnot_url, '')" if "whatnot_url" in columns else "''"
    conn.execute(
        f"""
        INSERT INTO card_sales (user_id, card_id, variant, card_condition, quantity, asking_price, whatnot_url, updated_at)
        SELECT {user_select}, card_id, COALESCE(NULLIF(variant, ''), 'Normal'),
               COALESCE(NULLIF(card_condition, ''), ?), quantity, asking_price, {whatnot_select}, updated_at
        FROM card_sales_old_user_migration
        """,
        (DEFAULT_CARD_CONDITION,),
    )
    conn.execute("DROP TABLE card_sales_old_user_migration")


def migrate_notifications_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            link_url TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT '',
            source_key TEXT NOT NULL DEFAULT '',
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            read_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    columns = table_columns(conn, "notifications")
    additions = {
        "link_url": "TEXT NOT NULL DEFAULT ''",
        "source_type": "TEXT NOT NULL DEFAULT ''",
        "source_key": "TEXT NOT NULL DEFAULT ''",
        "is_read": "INTEGER NOT NULL DEFAULT 0",
        "created_at": "TEXT NOT NULL DEFAULT ''",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
        "read_at": "TEXT",
    }
    for name, definition in additions.items():
        if name not in columns:
            conn.execute(f"ALTER TABLE notifications ADD COLUMN {name} {definition}")
    timestamp = now_iso()
    conn.execute("UPDATE notifications SET created_at = ? WHERE COALESCE(created_at, '') = ''", (timestamp,))
    conn.execute("UPDATE notifications SET updated_at = created_at WHERE COALESCE(updated_at, '') = ''")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_notifications_source ON notifications(user_id, source_type, source_key)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, updated_at)")


def migrate_profile_social_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile_friends (
            user_id INTEGER NOT NULL,
            friend_user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_id, friend_user_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (friend_user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS profile_wall_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_user_id INTEGER NOT NULL,
            author_user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (profile_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS profile_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            card_id TEXT,
            deck_id INTEGER,
            variant TEXT NOT NULL DEFAULT 'Normal',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE SET NULL,
            FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS profile_post_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            author_user_id INTEGER NOT NULL,
            parent_comment_id INTEGER,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES profile_posts(id) ON DELETE CASCADE,
            FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_comment_id) REFERENCES profile_post_comments(id) ON DELETE CASCADE
        );
        """
    )
    columns = table_columns(conn, "profile_posts")
    if "card_id" not in columns:
        conn.execute("ALTER TABLE profile_posts ADD COLUMN card_id TEXT")
    if "deck_id" not in columns:
        conn.execute("ALTER TABLE profile_posts ADD COLUMN deck_id INTEGER")
    if "variant" not in columns:
        conn.execute("ALTER TABLE profile_posts ADD COLUMN variant TEXT NOT NULL DEFAULT 'Normal'")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_profile_friends_user ON profile_friends(user_id, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_profile_wall_user ON profile_wall_messages(profile_user_id, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_profile_posts_user ON profile_posts(user_id, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_profile_posts_card ON profile_posts(card_id, variant, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_profile_posts_deck ON profile_posts(deck_id, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_profile_comments_post ON profile_post_comments(post_id, created_at)")


def migrate_card_comments_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS card_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS card_comment_votes (
            comment_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (comment_id, user_id),
            FOREIGN KEY (comment_id) REFERENCES card_comments(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_comments_card ON card_comments(card_id, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_comment_votes_user ON card_comment_votes(user_id, created_at)")


def migrate_content_reports_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS content_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_user_id INTEGER NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            resolution TEXT NOT NULL DEFAULT '',
            admin_user_id INTEGER,
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (reporter_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (admin_user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_content_reports_status ON content_reports(status, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_content_reports_target ON content_reports(target_type, target_id)")


def migrate_news_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS news_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'published',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            published_at TEXT NOT NULL DEFAULT '',
            scheduled_at TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    columns = table_columns(conn, "news_posts")
    if "scheduled_at" not in columns:
        conn.execute("ALTER TABLE news_posts ADD COLUMN scheduled_at TEXT NOT NULL DEFAULT ''")
    conn.execute("UPDATE news_posts SET status = 'published' WHERE trim(COALESCE(status, '')) = ''")
    conn.execute("UPDATE news_posts SET status = 'draft' WHERE status NOT IN ('draft', 'scheduled', 'published')")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_news_posts_status_date ON news_posts(status, published_at DESC, id DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_news_posts_author ON news_posts(author_user_id, created_at DESC)")


def add_user_id_column(conn, table):
    if "user_id" not in table_columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")


def migrate_user_schema(conn):
    add_user_id_column(conn, "card_purchases")
    add_user_id_column(conn, "card_sale_journal")
    add_user_id_column(conn, "decks")
    add_user_id_column(conn, "containers")
    migrate_collection_user_schema(conn)
    migrate_card_meta_user_schema(conn)
    migrate_wishlist_cards_user_schema(conn)
    migrate_card_sales_user_schema(conn)
    migrate_wishlists_schema(conn)
    migrate_favorite_decks_schema(conn)
    migrate_favorite_store_listings_schema(conn)
    user_columns = table_columns(conn, "users")
    if "name" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN name TEXT NOT NULL DEFAULT ''")
    if "language" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'en'")
    if "theme" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN theme TEXT NOT NULL DEFAULT 'light'")
    if "email_verified" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")
    if "store_share_id" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN store_share_id TEXT")
    if "role" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'normal'")
    if "is_banned" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER NOT NULL DEFAULT 0")
    if "last_login_at" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN last_login_at TEXT")
    for column, definition in {
        "stripe_customer_id": "TEXT",
        "stripe_subscription_id": "TEXT",
        "stripe_price_id": "TEXT",
        "subscription_plan": "TEXT NOT NULL DEFAULT ''",
        "subscription_status": "TEXT NOT NULL DEFAULT ''",
        "subscription_current_period_end": "TEXT",
        "subscription_cancel_at_period_end": "INTEGER NOT NULL DEFAULT 0",
        "subscription_canceled_at": "TEXT",
        "subscription_ended_at": "TEXT",
        "subscription_updated_at": "TEXT",
    }.items():
        if column not in user_columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
    for column in (
        "public_email", "contact_whatsapp", "contact_signal", "contact_telegram", "contact_discord",
        "contact_website", "contact_whatnot", "contact_mtg_arena", "contact_mtgo", "contact_instagram", "contact_bluesky", "contact_threads", "about_me", "profile_image",
    ):
        if column not in user_columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")
    for column, definition in {
        "default_purchase_price": "REAL NOT NULL DEFAULT 0.01",
        "default_sell_price": "REAL NOT NULL DEFAULT 0",
    }.items():
        if column not in user_columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
    if "profile_slug" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN profile_slug TEXT")
    conn.execute("UPDATE users SET name = email WHERE trim(COALESCE(name, '')) = ''")
    conn.execute("UPDATE users SET email_verified = 1 WHERE email_verified = 0 AND trim(COALESCE(password_hash, '')) != ''")
    ensure_unique_user_display_names(conn)
    rows = conn.execute("SELECT id, name, email, profile_slug FROM users ORDER BY id").fetchall()
    for row in rows:
        if not row["profile_slug"]:
            conn.execute("UPDATE users SET profile_slug = ? WHERE id = ?", (unique_profile_slug(conn, row["name"] or row["email"], row["id"]), row["id"]))
    conn.execute("UPDATE users SET role = 'pro' WHERE role = 'paid'")
    conn.execute("UPDATE users SET role = 'normal' WHERE role NOT IN ('admin', 'contributor', 'pro', 'normal') OR trim(COALESCE(role, '')) = ''")
    for email in ADMIN_EMAILS:
        conn.execute("UPDATE users SET role = 'admin', is_banned = 0 WHERE lower(email) = ?", (email,))
    rows = conn.execute("SELECT id FROM users WHERE store_share_id IS NULL OR store_share_id = ''").fetchall()
    for row in rows:
        conn.execute("UPDATE users SET store_share_id = ? WHERE id = ?", (new_store_share_id(conn), row["id"]))
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS email_verifications (
            token_hash TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT
        );

        CREATE TABLE IF NOT EXISTS password_resets (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_name_unique ON users(lower(name))")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_profile_slug ON users(profile_slug)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role, is_banned)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_stripe_subscription ON users(stripe_subscription_id)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_store_share_id ON users(store_share_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, expires_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_email_verifications_email ON email_verifications(email, expires_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id, expires_at)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_decks_user_name ON decks(user_id, lower(name))")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_containers_user_name ON containers(user_id, lower(name))")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_wishlists_user_name ON wishlists(user_id, lower(name))")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_wishlists_share_id ON wishlists(share_id)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_containers_share_id ON containers(share_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wishlist_items_user_card ON wishlist_items(user_id, card_id, variant)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_favorite_decks_user ON favorite_decks(user_id, updated_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_favorite_store_user ON favorite_store_listings(user_id, updated_at)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_collection_share_id ON collection(share_id)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_decks_share_id ON decks(share_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_collection_user_quantity ON collection(user_id, quantity)")
    migrate_legacy_wishlists(conn)


def ensure_unique_user_display_names(conn):
    seen = set()
    rows = conn.execute("SELECT id, name, email FROM users ORDER BY id").fetchall()
    for row in rows:
        try:
            base = validate_display_name(row["name"] or (row["email"] or "user").split("@", 1)[0])
        except ValueError:
            base = validate_display_name((row["email"] or "user").split("@", 1)[0])
        candidate = base
        counter = 2
        while candidate.lower() in seen:
            suffix = f" {counter}"
            candidate = f"{base[:80 - len(suffix)]}{suffix}"
            counter += 1
        seen.add(candidate.lower())
        if candidate != row["name"]:
            conn.execute("UPDATE users SET name = ? WHERE id = ?", (candidate, row["id"]))


def user_payload(row):
    if not row:
        return None
    role = effective_user_role(row)
    subscription_status = row["subscription_status"] if "subscription_status" in row.keys() else ""
    stripe_price_id = row["stripe_price_id"] if "stripe_price_id" in row.keys() else ""
    subscription_plan = row["subscription_plan"] if "subscription_plan" in row.keys() else ""
    subscription_plan = subscription_plan or stripe_plan_for_price_id(stripe_price_id)
    return {
        "id": row["id"],
        "name": row["name"] if "name" in row.keys() else row["email"],
        "email": row["email"],
        "language": scryfall_language(row["language"]),
        "theme": clean_theme(row["theme"]),
        "email_verified": bool(row["email_verified"]),
        "role": role,
        "account_role": clean_user_role(row["role"] if "role" in row.keys() else role_for_email(row["email"])),
        "is_admin": role == "admin",
        "is_contributor": role in {"admin", "contributor"},
        "is_pro": role in {"admin", "contributor", "pro"},
        "subscription_status": subscription_status,
        "stripe_price_id": stripe_price_id,
        "subscription_plan": subscription_plan,
        "subscription_plan_label": stripe_plan_label(subscription_plan),
        "subscription_current_period_end": row["subscription_current_period_end"] if "subscription_current_period_end" in row.keys() else "",
        "subscription_cancel_at_period_end": bool(row["subscription_cancel_at_period_end"]) if "subscription_cancel_at_period_end" in row.keys() else False,
        "subscription_canceled_at": row["subscription_canceled_at"] if "subscription_canceled_at" in row.keys() else "",
        "subscription_ended_at": row["subscription_ended_at"] if "subscription_ended_at" in row.keys() else "",
        "has_stripe_customer": bool(row["stripe_customer_id"]) if "stripe_customer_id" in row.keys() else False,
        "is_banned": bool(row["is_banned"]) if "is_banned" in row.keys() else False,
        "public_email": row["public_email"] if "public_email" in row.keys() else "",
        "contact_whatsapp": row["contact_whatsapp"] if "contact_whatsapp" in row.keys() else "",
        "contact_signal": row["contact_signal"] if "contact_signal" in row.keys() else "",
        "contact_telegram": row["contact_telegram"] if "contact_telegram" in row.keys() else "",
        "contact_discord": row["contact_discord"] if "contact_discord" in row.keys() else "",
        "contact_website": row["contact_website"] if "contact_website" in row.keys() else "",
        "contact_whatnot": row["contact_whatnot"] if "contact_whatnot" in row.keys() else "",
        "whatnot_url": whatnot_profile_url(row["contact_whatnot"]) if "contact_whatnot" in row.keys() and row["contact_whatnot"] else "",
        "contact_mtg_arena": row["contact_mtg_arena"] if "contact_mtg_arena" in row.keys() else "",
        "contact_mtgo": row["contact_mtgo"] if "contact_mtgo" in row.keys() else "",
        "contact_instagram": row["contact_instagram"] if "contact_instagram" in row.keys() else "",
        "contact_bluesky": row["contact_bluesky"] if "contact_bluesky" in row.keys() else "",
        "contact_threads": row["contact_threads"] if "contact_threads" in row.keys() else "",
        "about_me": row["about_me"] if "about_me" in row.keys() else "",
        "profile_image": row["profile_image"] if "profile_image" in row.keys() else "",
        "gravatar_url": gravatar_url(row["email"]),
        "default_purchase_price": money(row["default_purchase_price"] if "default_purchase_price" in row.keys() else 0.01, fallback=0.01),
        "default_sell_price": money(row["default_sell_price"] if "default_sell_price" in row.keys() else 0, fallback=0),
        "profile_slug": row["profile_slug"] if "profile_slug" in row.keys() else profile_slug(row["name"] if "name" in row.keys() else row["email"]),
        "profile_url": f"/user/{urllib.parse.quote(row['profile_slug'])}" if "profile_slug" in row.keys() and row["profile_slug"] else "",
        "store_share_id": row["store_share_id"] if "store_share_id" in row.keys() else "",
        "last_login_at": row["last_login_at"] if "last_login_at" in row.keys() else "",
        "created_at": row["created_at"],
    }


def session_hash(token):
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def create_session(conn, user_id):
    token = secrets.token_urlsafe(32)
    created = now_iso()
    expires = session_expires_at()
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (session_hash(token), user_id, created, expires),
    )
    conn.execute("UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?", (created, created, user_id))
    return token, expires


def session_expires_at():
    return (datetime.now(timezone.utc) + timedelta(minutes=SESSION_IDLE_MINUTES)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def cookie_header(token, expires_at=None, clear=False):
    if clear:
        return f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
    max_age = SESSION_IDLE_MINUTES * 60
    return f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}"


def parse_cookies(header):
    cookies = {}
    for part in (header or "").split(";"):
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies[name.strip()] = value.strip()
    return cookies


def current_user_from_token(conn, token):
    if not token:
        return None
    token_hash = session_hash(token)
    row = conn.execute(
        """
        SELECT u.*, s.token_hash AS session_token_hash
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token_hash = ? AND s.expires_at > ?
        """,
        (token_hash, now_iso()),
    ).fetchone()
    if row:
        if int(row["is_banned"] if "is_banned" in row.keys() else 0):
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
            conn.commit()
            return None
        timestamp = now_iso()
        conn.execute("UPDATE sessions SET expires_at = ? WHERE token_hash = ?", (session_expires_at(), token_hash))
        conn.execute("UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?", (timestamp, timestamp, row["id"]))
        conn.commit()
    else:
        conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_iso(),))
        conn.commit()
    return row


def adopt_legacy_data(conn, user_id):
    for table in ("collection", "card_purchases", "card_meta", "wishlist_cards", "card_sales", "card_sale_journal", "inventory_adjustments", "decks", "containers", "favorite_store_listings"):
        if "user_id" in table_columns(conn, table):
            conn.execute(f"UPDATE {table} SET user_id = ? WHERE user_id IS NULL", (user_id,))
    migrate_legacy_wishlist_for_user(conn, user_id)


def verification_base_url():
    return APP_BASE_URL or "http://127.0.0.1:8000"


def public_app_config(conn):
    return {
        "app_base_url": APP_BASE_URL,
        "app_version": APP_VERSION,
        "email_configured": smtp_configured() or mailgun_configured(),
        "stripe_configured": stripe_checkout_configured(),
        "server_claimed": app_has_users(conn),
        "wallpaper": current_site_wallpaper(conn),
    }


def changelog_payload():
    if CHANGELOG_PATH.exists():
        text = CHANGELOG_PATH.read_text(encoding="utf-8").strip()
    else:
        text = f"# Changelog\n\n## {APP_VERSION}\n\n- Release notes have not been written yet."
    return {"version": APP_VERSION, "changelog": text}


def stripe_checkout_configured():
    return bool(STRIPE_SECRET_KEY and (STRIPE_PRICE_MONTHLY or STRIPE_PRICE_YEARLY))


def stripe_webhook_configured():
    return bool(STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET)


def stripe_price_for_plan(plan):
    plan = (plan or "").strip().lower()
    if plan in {"month", "monthly"}:
        return STRIPE_PRICE_MONTHLY, "monthly"
    if plan in {"year", "yearly", "annual", "annually"}:
        return STRIPE_PRICE_YEARLY, "yearly"
    raise ValueError("Choose monthly or yearly billing.")


def stripe_api_request(method, path, params=None):
    if not STRIPE_SECRET_KEY:
        raise ValueError("Stripe is not configured on this server.")
    method = method.upper()
    url = f"{STRIPE_API_BASE}{path}"
    data = None
    headers = {
        "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
        "User-Agent": USER_AGENT,
    }
    if params:
        encoded = urllib.parse.urlencode(params)
        if method == "GET":
            url = f"{url}?{encoded}"
        else:
            data = encoded.encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with safe_urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(detail)
            message = payload.get("error", {}).get("message") or detail
        except json.JSONDecodeError:
            message = detail or exc.reason
        raise ValueError(f"Stripe error {exc.code}: {message}") from exc


def stripe_customer_for_user(conn, user):
    customer_id = user["stripe_customer_id"] if "stripe_customer_id" in user.keys() else ""
    if customer_id:
        return customer_id
    payload = stripe_api_request("POST", "/v1/customers", [
        ("email", user["email"]),
        ("name", user["name"] or user["email"]),
        ("metadata[user_id]", str(user["id"])),
    ])
    customer_id = payload.get("id")
    if not customer_id:
        raise ValueError("Stripe did not return a customer id.")
    timestamp = now_iso()
    conn.execute(
        "UPDATE users SET stripe_customer_id = ?, subscription_updated_at = ?, updated_at = ? WHERE id = ?",
        (customer_id, timestamp, timestamp, user["id"]),
    )
    conn.commit()
    return customer_id


def billing_return_url(kind):
    base = verification_base_url()
    return f"{base}/settings?billing={urllib.parse.quote(kind)}"


def create_stripe_checkout_session(conn, user, payload):
    if not stripe_checkout_configured():
        raise ValueError("Stripe Checkout is not configured on this server.")
    price_id, plan = stripe_price_for_plan((payload or {}).get("plan"))
    if not price_id:
        raise ValueError(f"The Stripe {plan} price is not configured.")
    customer_id = stripe_customer_for_user(conn, user)
    session = stripe_api_request("POST", "/v1/checkout/sessions", [
        ("mode", "subscription"),
        ("customer", customer_id),
        ("client_reference_id", str(user["id"])),
        ("line_items[0][price]", price_id),
        ("line_items[0][quantity]", "1"),
        ("success_url", billing_return_url("success")),
        ("cancel_url", billing_return_url("cancelled")),
        ("allow_promotion_codes", "true"),
        ("metadata[user_id]", str(user["id"])),
        ("metadata[plan]", plan),
        ("subscription_data[metadata][user_id]", str(user["id"])),
        ("subscription_data[metadata][plan]", plan),
    ])
    return {"ok": True, "url": session.get("url"), "session_id": session.get("id")}


def create_stripe_portal_session(conn, user):
    if not STRIPE_SECRET_KEY:
        raise ValueError("Stripe is not configured on this server.")
    customer_id = user["stripe_customer_id"] if "stripe_customer_id" in user.keys() else ""
    if not customer_id:
        raise ValueError("No billing profile found yet. Choose an upgrade plan first.")
    session = stripe_api_request("POST", "/v1/billing_portal/sessions", [
        ("customer", customer_id),
        ("return_url", billing_return_url("portal")),
    ])
    return {"ok": True, "url": session.get("url")}


def unix_to_iso(value):
    try:
        timestamp = int(value or 0)
    except (TypeError, ValueError):
        return ""
    if timestamp <= 0:
        return ""
    return datetime.fromtimestamp(timestamp, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def format_email_date(value):
    parsed = parse_iso_datetime(value)
    if not parsed:
        return ""
    return parsed.astimezone(timezone.utc).strftime("%b %-d, %Y")


def stripe_subscription_price_id(subscription):
    items = ((subscription or {}).get("items") or {}).get("data") or []
    if not items:
        return ""
    price = (items[0] or {}).get("price") or {}
    return price.get("id") or ""


def stripe_plan_for_price_id(price_id, fallback=""):
    if price_id and STRIPE_PRICE_MONTHLY and price_id == STRIPE_PRICE_MONTHLY:
        return "monthly"
    if price_id and STRIPE_PRICE_YEARLY and price_id == STRIPE_PRICE_YEARLY:
        return "yearly"
    clean_fallback = (fallback or "").strip().lower()
    return clean_fallback if clean_fallback in {"monthly", "yearly"} else ""


def stripe_plan_label(plan):
    return {"monthly": "Pro Monthly", "yearly": "Pro Yearly"}.get((plan or "").strip().lower(), "Pro")


def stripe_subscription_receipt_details(subscription, plan=""):
    subscription = subscription or {}
    price_id = stripe_subscription_price_id(subscription)
    plan = stripe_plan_for_price_id(price_id, plan or (subscription.get("metadata") or {}).get("plan"))
    latest_invoice = subscription.get("latest_invoice") or ""
    if isinstance(latest_invoice, dict):
        latest_invoice = latest_invoice.get("id") or ""
    return {
        "subscription_id": subscription.get("id") or "",
        "invoice_id": latest_invoice,
        "plan": plan,
        "plan_label": stripe_plan_label(plan),
        "status": (subscription.get("status") or "").strip().lower() or "active",
        "period_start": unix_to_iso(subscription.get("current_period_start")),
        "period_end": unix_to_iso(subscription.get("current_period_end")),
        "cancel_at_period_end": bool(subscription.get("cancel_at_period_end")),
    }


def subscription_receipt_text(user, details):
    display_name = user["name"] if "name" in user.keys() and user["name"] else user["email"]
    purchased = format_email_date(details.get("period_start")) or format_email_date(now_iso())
    renews = format_email_date(details.get("period_end")) or "the end of your current billing period"
    renewal_label = "Membership access ends" if details.get("cancel_at_period_end") else "Membership renews"
    return "\n".join([
        f"Hi {display_name},",
        "",
        "Thanks for supporting Arcane Ledger.",
        "",
        f"Subscription: {details.get('plan_label') or 'Pro'}",
        f"Status: {details.get('status') or 'active'}",
        f"Purchase date: {purchased}",
        f"{renewal_label}: {renews}",
        "",
        f"Manage your membership from Settings: {verification_base_url()}/settings",
        "",
        "This receipt was sent to your Arcane Ledger account email.",
    ])


def subscription_receipt_html(user, details):
    display_name = html_lib.escape(user["name"] if "name" in user.keys() and user["name"] else user["email"])
    plan_label = html_lib.escape(details.get("plan_label") or "Pro")
    status = html_lib.escape(details.get("status") or "active")
    purchased = html_lib.escape(format_email_date(details.get("period_start")) or format_email_date(now_iso()))
    renews = html_lib.escape(format_email_date(details.get("period_end")) or "the end of your current billing period")
    renewal_label = "Membership access ends" if details.get("cancel_at_period_end") else "Membership renews"
    settings_url = html_lib.escape(f"{verification_base_url()}/settings")
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:620px;margin:0 auto;color:#17211f;">
      <h1 style="font-size:24px;margin:0 0 12px;">Arcane Ledger membership receipt</h1>
      <p style="line-height:1.5;">Hi {display_name}, thanks for supporting Arcane Ledger.</p>
      <table style="width:100%;border-collapse:collapse;margin:18px 0;border:1px solid #dbe2df;border-radius:10px;overflow:hidden;">
        <tr><th align="left" style="padding:10px 12px;background:#eef5f1;">Subscription</th><td style="padding:10px 12px;">{plan_label}</td></tr>
        <tr><th align="left" style="padding:10px 12px;background:#eef5f1;">Status</th><td style="padding:10px 12px;">{status}</td></tr>
        <tr><th align="left" style="padding:10px 12px;background:#eef5f1;">Purchase date</th><td style="padding:10px 12px;">{purchased}</td></tr>
        <tr><th align="left" style="padding:10px 12px;background:#eef5f1;">{html_lib.escape(renewal_label)}</th><td style="padding:10px 12px;">{renews}</td></tr>
      </table>
      <p style="line-height:1.5;">You can manage your membership from <a href="{settings_url}">Arcane Ledger Settings</a>.</p>
      <p style="font-size:12px;color:#66706d;">This receipt was sent to your Arcane Ledger account email.</p>
    </div>
    """


def send_subscription_receipt(conn, user_id, subscription, plan=""):
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return {"ok": False, "skipped": "user_not_found"}
    details = stripe_subscription_receipt_details(subscription, plan)
    if not details["subscription_id"]:
        return {"ok": False, "skipped": "missing_subscription_id"}
    receipt_key = (
        user["id"],
        details["subscription_id"],
        details["invoice_id"],
        details["period_end"],
    )
    if conn.execute(
        """
        SELECT 1
        FROM stripe_subscription_receipts
        WHERE user_id = ? AND stripe_subscription_id = ? AND stripe_invoice_id = ? AND period_end = ?
        """,
        receipt_key,
    ).fetchone():
        return {"ok": True, "skipped": "already_sent"}
    result = send_email(
        user["email"],
        f"Arcane Ledger receipt: {details['plan_label']}",
        text=subscription_receipt_text(user, details),
        html=subscription_receipt_html(user, details),
        tags=["arcane-ledger", "subscription-receipt"],
    )
    conn.execute(
        """
        INSERT INTO stripe_subscription_receipts
            (user_id, stripe_subscription_id, stripe_invoice_id, period_end, plan, sent_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (*receipt_key, details["plan"], now_iso()),
    )
    return {"ok": True, "email": user["email"], "provider": result.get("provider"), "status": result.get("status")}


def update_user_from_stripe_subscription(conn, subscription, previous_role_override=None):
    subscription = subscription or {}
    subscription_id = subscription.get("id") or ""
    customer_id = subscription.get("customer") or ""
    metadata = subscription.get("metadata") or {}
    user_id = metadata.get("user_id")
    row = None
    if user_id:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row and subscription_id:
        row = conn.execute("SELECT * FROM users WHERE stripe_subscription_id = ?", (subscription_id,)).fetchone()
    if not row and customer_id:
        row = conn.execute("SELECT * FROM users WHERE stripe_customer_id = ?", (customer_id,)).fetchone()
    if not row:
        LOGGER.warning("Stripe subscription %s did not match a user.", subscription_id)
        return None
    previous_role = previous_role_override or effective_user_role(row)
    status = (subscription.get("status") or "").strip().lower()
    price_id = stripe_subscription_price_id(subscription)
    plan = stripe_plan_for_price_id(price_id, metadata.get("plan"))
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE users
        SET stripe_customer_id = COALESCE(NULLIF(?, ''), stripe_customer_id),
            stripe_subscription_id = COALESCE(NULLIF(?, ''), stripe_subscription_id),
            stripe_price_id = COALESCE(NULLIF(?, ''), stripe_price_id),
            subscription_plan = COALESCE(NULLIF(?, ''), subscription_plan),
            subscription_status = ?,
            subscription_current_period_end = ?,
            subscription_cancel_at_period_end = ?,
            subscription_canceled_at = ?,
            subscription_ended_at = ?,
            subscription_updated_at = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            customer_id,
            subscription_id,
            price_id,
            plan,
            status,
            unix_to_iso(subscription.get("current_period_end")),
            1 if subscription.get("cancel_at_period_end") else 0,
            unix_to_iso(subscription.get("canceled_at")),
            unix_to_iso(subscription.get("ended_at")),
            timestamp,
            timestamp,
            row["id"],
        ),
    )
    updated = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
    send_membership_role_change_emails(
        conn,
        row["id"],
        previous_role,
        effective_user_role(updated),
        subscription=subscription,
        plan=plan,
    )
    return row["id"]


def update_user_from_checkout_session(conn, session):
    session = session or {}
    user_id = (session.get("metadata") or {}).get("user_id") or session.get("client_reference_id")
    if not user_id:
        LOGGER.warning("Stripe checkout session %s did not include a user id.", session.get("id"))
        return None
    existing_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    previous_role = effective_user_role(existing_user) if existing_user else "normal"
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE users
        SET stripe_customer_id = COALESCE(NULLIF(?, ''), stripe_customer_id),
            stripe_subscription_id = COALESCE(NULLIF(?, ''), stripe_subscription_id),
            subscription_status = CASE
                WHEN COALESCE(subscription_status, '') = '' THEN 'active'
                ELSE subscription_status
            END,
            subscription_updated_at = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (session.get("customer") or "", session.get("subscription") or "", timestamp, timestamp, user_id),
    )
    subscription_id = session.get("subscription")
    if subscription_id:
        try:
            subscription = stripe_api_request("GET", f"/v1/subscriptions/{urllib.parse.quote(subscription_id)}")
            update_user_from_stripe_subscription(conn, subscription, previous_role_override=previous_role)
            try:
                send_subscription_receipt(conn, int(user_id), subscription, (session.get("metadata") or {}).get("plan"))
            except Exception as exc:
                LOGGER.warning("Could not send Stripe subscription receipt for user %s: %s", user_id, exc)
        except ValueError as exc:
            LOGGER.warning("Could not retrieve Stripe subscription %s: %s", subscription_id, exc)
    return user_id


def verify_stripe_signature(raw_body, signature_header):
    if not STRIPE_WEBHOOK_SECRET:
        raise ForbiddenError("Stripe webhook secret is not configured.")
    parts = {}
    for item in (signature_header or "").split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            parts.setdefault(key, []).append(value)
    timestamp_values = parts.get("t") or []
    signatures = parts.get("v1") or []
    if not timestamp_values or not signatures:
        raise ForbiddenError("Stripe webhook signature is missing.")
    timestamp = int(timestamp_values[0])
    if abs(int(time.time()) - timestamp) > 300:
        raise ForbiddenError("Stripe webhook signature timestamp is outside the allowed tolerance.")
    signed_payload = str(timestamp).encode("utf-8") + b"." + raw_body
    expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, signature) for signature in signatures):
        raise ForbiddenError("Stripe webhook signature verification failed.")


def handle_stripe_webhook(conn, raw_body, signature_header):
    verify_stripe_signature(raw_body, signature_header)
    event = json.loads(raw_body.decode("utf-8"))
    event_id = event.get("id")
    event_type = event.get("type") or ""
    if not event_id:
        raise ValueError("Stripe webhook event is missing an id.")
    if conn.execute("SELECT 1 FROM stripe_events WHERE id = ?", (event_id,)).fetchone():
        return {"ok": True, "duplicate": True}
    data_object = ((event.get("data") or {}).get("object") or {})
    if event_type == "checkout.session.completed":
        update_user_from_checkout_session(conn, data_object)
    elif event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
        update_user_from_stripe_subscription(conn, data_object)
    elif event_type == "invoice.paid":
        subscription_id = data_object.get("subscription")
        if subscription_id:
            try:
                subscription = stripe_api_request("GET", f"/v1/subscriptions/{urllib.parse.quote(subscription_id)}")
                update_user_from_stripe_subscription(conn, subscription)
            except ValueError as exc:
                LOGGER.warning("Could not refresh subscription after invoice.paid: %s", exc)
    timestamp = now_iso()
    conn.execute(
        "INSERT INTO stripe_events (id, type, created_at, processed_at) VALUES (?, ?, ?, ?)",
        (event_id, event_type, unix_to_iso(event.get("created")) or timestamp, timestamp),
    )
    conn.commit()
    return {"ok": True, "event": event_type}


def app_has_users(conn=None):
    if conn is not None:
        return bool(conn.execute("SELECT 1 FROM users LIMIT 1").fetchone())
    with connect() as local_conn:
        init_db(local_conn)
        return app_has_users(local_conn)


def render_email_template_text(value, variables):
    rendered = str(value or "")
    for key, replacement in variables.items():
        rendered = rendered.replace(f"%{key}%", str(replacement or ""))
    return rendered


def admin_email_template_variables(user):
    display_name = user["name"] if "name" in user.keys() and user["name"] else user["email"]
    base_url = verification_base_url()
    domain_name = app_base_domain()
    from_email = sender_email(MAILGUN_FROM_EMAIL) or sender_email(SMTP_FROM, fallback=False) or default_from_email()
    today = datetime.now(timezone.utc).date()
    last_login = user["last_login_at"] if "last_login_at" in user.keys() and user["last_login_at"] else ""
    last_login_at = parse_iso_datetime(last_login)
    last_login_date = last_login_at.date() if last_login_at else None
    days_inactive = (today - last_login_date).days if last_login_date else ""
    return {
        "appname": "Arcane Ledger",
        "appversion": APP_VERSION,
        "baseurl": base_url,
        "domainname": domain_name,
        "fromemail": from_email,
        "supportemail": from_email,
        "displayname": display_name,
        "username": display_name,
        "email": user["email"],
        "useremail": user["email"],
        "date": today.isoformat(),
        "lastlogin": last_login,
        "lastlogindate": last_login_date.isoformat() if last_login_date else "",
        "daysinactive": days_inactive,
        "inactive_days": days_inactive,
        "year": today.year,
    }


ADMIN_EMAIL_TEMPLATE_TRIGGERS = {
    "user_created",
    "inactive_30_days",
    "inactive_60_days",
    "inactive_90_days",
    "subscription_upgraded_pro",
    "subscription_downgraded_normal",
}


def admin_email_template_row(row):
    return {
        "id": str(row["id"]),
        "name": row["name"] or "",
        "trigger": row["trigger_key"] or "user_created",
        "to_email": row["to_email"] or "%email%",
        "from_email": row["from_email"] or "",
        "subject": row["subject"] or "",
        "body": row["body"] or "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_admin_email_templates(conn):
    rows = conn.execute(
        """
        SELECT id, name, trigger_key, to_email, from_email, subject, body, created_at, updated_at
        FROM admin_email_templates
        ORDER BY updated_at DESC, name COLLATE NOCASE
        """
    ).fetchall()
    return {"templates": [admin_email_template_row(row) for row in rows]}


def save_admin_email_template(conn, payload):
    name = re.sub(r"\s+", " ", (payload.get("name") or "").strip())
    if not name:
        raise ValueError("Template name is required.")
    if len(name) > 80:
        raise ValueError("Template name must be 80 characters or fewer.")
    trigger_key = (payload.get("trigger") or payload.get("trigger_key") or "user_created").strip()
    if trigger_key not in ADMIN_EMAIL_TEMPLATE_TRIGGERS:
        raise ValueError("Choose a valid email trigger.")
    to_email = (payload.get("to_email") or "%email%").strip()
    from_email = (payload.get("from_email") or "").strip()
    subject = (payload.get("subject") or "").strip()
    body = payload.get("body") or ""
    if len(to_email) > 200:
        raise ValueError("To field must be 200 characters or fewer.")
    if len(from_email) > 200:
        raise ValueError("From field must be 200 characters or fewer.")
    if len(subject) > 160:
        raise ValueError("Subject must be 160 characters or fewer.")
    if len(body) > 20000:
        raise ValueError("Template body must be 20,000 characters or fewer.")
    timestamp = now_iso()
    raw_id = str(payload.get("id") or "")
    template_id = int(raw_id) if raw_id.isdigit() else 0
    if template_id:
        existing = conn.execute("SELECT id FROM admin_email_templates WHERE id = ?", (template_id,)).fetchone()
        if not existing:
            raise KeyError("Email template not found")
        conn.execute(
            """
            UPDATE admin_email_templates
            SET name = ?, trigger_key = ?, to_email = ?, from_email = ?, subject = ?, body = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, trigger_key, to_email, from_email, subject, body, timestamp, template_id),
        )
    else:
        cursor = conn.execute(
            """
            INSERT INTO admin_email_templates (name, trigger_key, to_email, from_email, subject, body, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, trigger_key, to_email, from_email, subject, body, timestamp, timestamp),
        )
        template_id = cursor.lastrowid
    conn.commit()
    row = conn.execute(
        """
        SELECT id, name, trigger_key, to_email, from_email, subject, body, created_at, updated_at
        FROM admin_email_templates
        WHERE id = ?
        """,
        (template_id,),
    ).fetchone()
    return {"ok": True, "template": admin_email_template_row(row), "templates": list_admin_email_templates(conn)["templates"]}


def delete_admin_email_template(conn, template_id):
    cursor = conn.execute("DELETE FROM admin_email_templates WHERE id = ?", (template_id,))
    if cursor.rowcount == 0:
        raise KeyError("Email template not found")
    conn.commit()
    return {"ok": True, "deleted": template_id, "templates": list_admin_email_templates(conn)["templates"]}


ANNOUNCEMENT_STATUSES = {"draft", "published"}


def announcement_row(row):
    return {
        "id": str(row["id"]),
        "subject": row["subject"] or "",
        "body": row["body"] or "",
        "starts_on": row["starts_on"] or "",
        "ends_on": row["ends_on"] or "",
        "status": row["status"] or "draft",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "published_at": row["published_at"] or "",
    }


def list_admin_announcements(conn):
    rows = conn.execute(
        """
        SELECT id, subject, body, starts_on, ends_on, status, created_at, updated_at, published_at
        FROM home_announcements
        ORDER BY updated_at DESC, starts_on DESC, id DESC
        """
    ).fetchall()
    return {"announcements": [announcement_row(row) for row in rows]}


def active_home_announcements(conn):
    today = today_iso()
    rows = conn.execute(
        """
        SELECT id, subject, body, starts_on, ends_on, status, created_at, updated_at, published_at
        FROM home_announcements
        WHERE status = 'published'
          AND starts_on <= ?
          AND ends_on >= ?
        ORDER BY starts_on DESC, updated_at DESC, id DESC
        """,
        (today, today),
    ).fetchall()
    return [announcement_row(row) for row in rows]


def clean_announcement_payload(payload, status):
    subject = re.sub(r"\s+", " ", (payload.get("subject") or "").strip())
    if not subject:
        raise ValueError("Announcement subject is required.")
    if len(subject) > 160:
        raise ValueError("Announcement subject must be 160 characters or fewer.")
    body = payload.get("body") or ""
    if len(body) > 20000:
        raise ValueError("Announcement body must be 20,000 characters or fewer.")
    starts_on = (payload.get("starts_on") or today_iso()).strip()
    ends_on = (payload.get("ends_on") or starts_on).strip()
    if not parse_iso_date(starts_on):
        raise ValueError("Beginning date must be a valid date.")
    if not parse_iso_date(ends_on):
        raise ValueError("Display until date must be a valid date.")
    if ends_on < starts_on:
        raise ValueError("Display until date cannot be before the beginning date.")
    status = (status or payload.get("status") or "draft").strip().lower()
    if status not in ANNOUNCEMENT_STATUSES:
        raise ValueError("Choose draft or publish.")
    return {
        "subject": subject,
        "body": body,
        "starts_on": starts_on,
        "ends_on": ends_on,
        "status": status,
    }


def save_home_announcement(conn, admin_user_id, payload):
    cleaned = clean_announcement_payload(payload, payload.get("status"))
    timestamp = now_iso()
    raw_id = str(payload.get("id") or "")
    announcement_id = int(raw_id) if raw_id.isdigit() else 0
    published_at = timestamp if cleaned["status"] == "published" else None
    if announcement_id:
        existing = conn.execute(
            "SELECT id, published_at FROM home_announcements WHERE id = ?",
            (announcement_id,),
        ).fetchone()
        if not existing:
            raise KeyError("Announcement not found")
        published_at = existing["published_at"] or (timestamp if cleaned["status"] == "published" else None)
        conn.execute(
            """
            UPDATE home_announcements
            SET subject = ?, body = ?, starts_on = ?, ends_on = ?, status = ?, admin_user_id = ?,
                updated_at = ?, published_at = ?
            WHERE id = ?
            """,
            (
                cleaned["subject"], cleaned["body"], cleaned["starts_on"], cleaned["ends_on"], cleaned["status"],
                admin_user_id, timestamp, published_at, announcement_id,
            ),
        )
    else:
        cursor = conn.execute(
            """
            INSERT INTO home_announcements (
                subject, body, starts_on, ends_on, status, admin_user_id, created_at, updated_at, published_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cleaned["subject"], cleaned["body"], cleaned["starts_on"], cleaned["ends_on"], cleaned["status"],
                admin_user_id, timestamp, timestamp, published_at,
            ),
        )
        announcement_id = cursor.lastrowid
    conn.commit()
    row = conn.execute(
        """
        SELECT id, subject, body, starts_on, ends_on, status, created_at, updated_at, published_at
        FROM home_announcements
        WHERE id = ?
        """,
        (announcement_id,),
    ).fetchone()
    return {
        "ok": True,
        "announcement": announcement_row(row),
        "announcements": list_admin_announcements(conn)["announcements"],
    }


NEWS_POST_STATUSES = {"draft", "scheduled", "published"}


def news_post_row(row, include_body=False):
    body = row["body"] or ""
    excerpt = re.sub(r"\s+", " ", body).strip()
    if len(excerpt) > 220:
        excerpt = f"{excerpt[:217].rstrip()}..."
    payload = {
        "id": int(row["id"]),
        "title": row["title"] or "",
        "excerpt": excerpt,
        "status": row["status"] or "published",
        "author": {
            "id": int(row["author_user_id"]),
            "name": row["author_name"] or row["author_email"] or "Contributor",
            "email": row["author_email"] or "",
            "profile_slug": row["author_profile_slug"] or "",
            "profile_url": f"/user/{urllib.parse.quote(row['author_profile_slug'])}" if row["author_profile_slug"] else "",
            "role": effective_user_role({
                "role": row["author_role"] or "normal",
                "subscription_status": row["author_subscription_status"] or "",
                "subscription_current_period_end": row["author_subscription_current_period_end"] or "",
                "subscription_cancel_at_period_end": bool(row["author_subscription_cancel_at_period_end"] or 0),
            }),
        },
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "published_at": row["published_at"] or "",
        "scheduled_at": row["scheduled_at"] or "",
    }
    if include_body:
        payload["body"] = body
    return payload


def news_post_select(include_body=False):
    body_column = "np.body" if include_body else "'' AS body"
    return f"""
        SELECT np.id, np.author_user_id, np.title, {body_column}, np.status,
               np.created_at, np.updated_at, np.published_at, np.scheduled_at,
               u.name AS author_name, u.email AS author_email, u.profile_slug AS author_profile_slug,
               u.role AS author_role, u.subscription_status AS author_subscription_status,
               u.subscription_current_period_end AS author_subscription_current_period_end,
               u.subscription_cancel_at_period_end AS author_subscription_cancel_at_period_end
        FROM news_posts np
        JOIN users u ON u.id = np.author_user_id
    """


def publish_due_news_posts(conn):
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE news_posts
        SET status = 'published', published_at = scheduled_at, scheduled_at = '', updated_at = ?
        WHERE status = 'scheduled'
          AND scheduled_at != ''
          AND scheduled_at <= ?
        """,
        (timestamp, timestamp),
    )


def list_news_posts(conn, query_string=""):
    publish_due_news_posts(conn)
    conn.commit()
    params = urllib.parse.parse_qs(query_string or "")
    search = re.sub(r"\s+", " ", (params.get("search", [""])[0] or "").strip().lower())
    sql = news_post_select(include_body=True) + """
        WHERE np.status = 'published'
          AND (? = '' OR lower(np.body) LIKE ?)
        ORDER BY datetime(np.published_at) DESC, np.id DESC
        LIMIT 100
    """
    rows = conn.execute(sql, (search, f"%{search}%")).fetchall()
    return {"posts": [news_post_row(row, include_body=False) for row in rows], "search": search}


def news_post_detail(conn, post_id):
    publish_due_news_posts(conn)
    conn.commit()
    row = conn.execute(
        news_post_select(include_body=True) + """
        WHERE np.id = ? AND np.status = 'published'
        """,
        (post_id,),
    ).fetchone()
    if not row:
        raise KeyError("News article not found.")
    return {"post": news_post_row(row, include_body=True)}


def list_my_news_posts(conn, user):
    if not is_contributor_user(user):
        raise ForbiddenError("Contributor access required.")
    publish_due_news_posts(conn)
    conn.commit()
    rows = conn.execute(
        news_post_select(include_body=True) + """
        WHERE np.author_user_id = ?
        ORDER BY
          CASE np.status WHEN 'draft' THEN 0 WHEN 'scheduled' THEN 1 ELSE 2 END,
          datetime(COALESCE(NULLIF(np.scheduled_at, ''), NULLIF(np.published_at, ''), np.updated_at)) DESC,
          np.id DESC
        """,
        (user["id"],),
    ).fetchall()
    posts = [news_post_row(row, include_body=True) for row in rows]
    return {
        "drafts": [post for post in posts if post["status"] in {"draft", "scheduled"}],
        "published": [post for post in posts if post["status"] == "published"],
    }


def clean_news_payload(payload, action):
    title = validate_user_content_name(payload.get("title") or payload.get("subject"), "News subject", 160)
    body = (payload.get("body") or "").strip()
    if len(body) > 50000:
        raise ValueError("News article body must be 50,000 characters or fewer.")
    action = (action or payload.get("action") or payload.get("status") or "draft").strip().lower()
    if action in {"publish", "published"}:
        status = "published"
    elif action in {"schedule", "scheduled"}:
        status = "scheduled"
    else:
        status = "draft"
    if status in {"published", "scheduled"} and not body:
        raise ValueError("News article body is required before publishing.")
    scheduled_at = ""
    if status == "scheduled":
        scheduled = parse_iso_datetime(payload.get("scheduled_at") or payload.get("publish_at"))
        if not scheduled:
            raise ValueError("Choose a valid scheduled publish date and time.")
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=timezone.utc)
        scheduled_at = scheduled.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if scheduled_at <= now_iso():
            status = "published"
            scheduled_at = ""
    return title, body, status, scheduled_at


def save_news_post(conn, user, payload):
    if not is_contributor_user(user):
        raise ForbiddenError("Contributor access required.")
    title, body, status, scheduled_at = clean_news_payload(payload, payload.get("action"))
    timestamp = now_iso()
    published_at = timestamp if status == "published" else ""
    raw_id = str(payload.get("id") or "")
    post_id = int(raw_id) if raw_id.isdigit() else 0
    if post_id:
        existing = conn.execute("SELECT * FROM news_posts WHERE id = ?", (post_id,)).fetchone()
        if not existing:
            raise KeyError("News article not found.")
        if int(existing["author_user_id"]) != int(user["id"]) and not is_admin_user(user):
            raise ForbiddenError("You can only edit your own news articles.")
        if status == "published" and existing["status"] == "published" and existing["published_at"]:
            published_at = existing["published_at"]
        conn.execute(
            """
            UPDATE news_posts
            SET title = ?, body = ?, status = ?, updated_at = ?, published_at = ?, scheduled_at = ?
            WHERE id = ?
            """,
            (title, body, status, timestamp, published_at, scheduled_at, post_id),
        )
    else:
        cursor = conn.execute(
            """
            INSERT INTO news_posts (author_user_id, title, body, status, created_at, updated_at, published_at, scheduled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user["id"], title, body, status, timestamp, timestamp, published_at, scheduled_at),
        )
        post_id = cursor.lastrowid
    conn.commit()
    mine = list_my_news_posts(conn, user)
    return {
        "ok": True,
        "post": news_post_for_author(conn, user, post_id),
        **mine,
    }


def news_post_for_author(conn, user, post_id):
    row = conn.execute(
        news_post_select(include_body=True) + """
        WHERE np.id = ?
        """,
        (post_id,),
    ).fetchone()
    if not row:
        raise KeyError("News article not found.")
    if int(row["author_user_id"]) != int(user["id"]) and not is_admin_user(user):
        raise ForbiddenError("You can only access your own news articles.")
    return news_post_row(row, include_body=True)


def unpublish_news_post(conn, user, post_id):
    if not is_contributor_user(user):
        raise ForbiddenError("Contributor access required.")
    existing = conn.execute("SELECT * FROM news_posts WHERE id = ?", (post_id,)).fetchone()
    if not existing:
        raise KeyError("News article not found.")
    if int(existing["author_user_id"]) != int(user["id"]) and not is_admin_user(user):
        raise ForbiddenError("You can only unpublish your own news articles.")
    conn.execute(
        "UPDATE news_posts SET status = 'draft', published_at = '', scheduled_at = '', updated_at = ? WHERE id = ?",
        (now_iso(), post_id),
    )
    conn.commit()
    return {"ok": True, **list_my_news_posts(conn, user)}


def delete_news_post(conn, user, post_id):
    if not is_contributor_user(user):
        raise ForbiddenError("Contributor access required.")
    existing = conn.execute("SELECT * FROM news_posts WHERE id = ?", (post_id,)).fetchone()
    if not existing:
        raise KeyError("News article not found.")
    if int(existing["author_user_id"]) != int(user["id"]) and not is_admin_user(user):
        raise ForbiddenError("You can only delete your own news articles.")
    conn.execute("DELETE FROM news_posts WHERE id = ?", (post_id,))
    conn.commit()
    return {"ok": True, **list_my_news_posts(conn, user)}


def wallpaper_url(filename):
    return f"/media/wallpapers/{urllib.parse.quote(filename)}"


def news_image_url(filename):
    return f"/media/news-images/{urllib.parse.quote(filename)}"


def site_wallpaper_row(row):
    return {
        "id": str(row["id"]),
        "filename": row["filename"],
        "original_name": row["original_name"] or row["filename"],
        "mime_type": row["mime_type"],
        "size_bytes": int(row["size_bytes"] or 0),
        "url": wallpaper_url(row["filename"]),
        "created_at": row["created_at"],
    }


def list_site_wallpapers(conn):
    rows = conn.execute(
        """
        SELECT id, filename, original_name, mime_type, size_bytes, created_at
        FROM site_wallpapers
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()
    return {"wallpapers": [site_wallpaper_row(row) for row in rows]}


def current_site_wallpaper(conn):
    rows = conn.execute(
        """
        SELECT id, filename, original_name, mime_type, size_bytes, created_at
        FROM site_wallpapers
        ORDER BY created_at ASC, id ASC
        """
    ).fetchall()
    if not rows:
        return None
    index = date.today().toordinal() % len(rows)
    return site_wallpaper_row(rows[index])


def clean_wallpaper_original_name(value):
    text = re.sub(r"\s+", " ", (value or "").strip())
    text = text.replace("/", "").replace("\\", "")
    return text[:120] or "Wallpaper"


def decode_wallpaper_data_url(data_url):
    text = (data_url or "").strip()
    match = re.match(r"^data:(image/(?:png|jpe?g|webp|gif));base64,([A-Za-z0-9+/=\s]+)$", text, flags=re.I)
    if not match:
        raise ValueError("Wallpaper must be a PNG, JPG, WebP, or GIF image.")
    mime_type = match.group(1).lower()
    extension = WALLPAPER_MIME_TYPES.get(mime_type)
    if not extension:
        raise ValueError("Wallpaper must be a PNG, JPG, WebP, or GIF image.")
    try:
        image_bytes = base64.b64decode(re.sub(r"\s+", "", match.group(2)), validate=True)
    except Exception as exc:
        raise ValueError("Wallpaper image data could not be decoded.") from exc
    if not image_bytes:
        raise ValueError("Wallpaper image is empty.")
    if len(image_bytes) > MAX_WALLPAPER_BYTES:
        raise ValueError("Wallpaper is too large. Use an image under 5 MB.")
    return mime_type, extension, image_bytes


def add_site_wallpaper(conn, admin_user_id, payload):
    mime_type, extension, image_bytes = decode_wallpaper_data_url(payload.get("image"))
    original_name = clean_wallpaper_original_name(payload.get("name") or payload.get("original_name"))
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{int(time.time())}-{secrets.token_hex(8)}{extension}"
    path = WALLPAPER_DIR / filename
    path.write_bytes(image_bytes)
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO site_wallpapers (filename, original_name, mime_type, size_bytes, admin_user_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (filename, original_name, mime_type, len(image_bytes), admin_user_id, timestamp),
    )
    conn.commit()
    row = conn.execute(
        """
        SELECT id, filename, original_name, mime_type, size_bytes, created_at
        FROM site_wallpapers
        WHERE id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    return {
        "ok": True,
        "wallpaper": site_wallpaper_row(row),
        "wallpapers": list_site_wallpapers(conn)["wallpapers"],
        "current": current_site_wallpaper(conn),
    }


def clean_media_original_name(value, fallback):
    text = re.sub(r"\s+", " ", (value or "").strip())
    text = text.replace("/", "").replace("\\", "")
    return text[:120] or fallback


def decode_image_data_url(data_url, label, max_bytes):
    text = (data_url or "").strip()
    match = re.match(r"^data:(image/(?:png|jpe?g|webp|gif));base64,([A-Za-z0-9+/=\s]+)$", text, flags=re.I)
    if not match:
        raise ValueError(f"{label} must be a PNG, JPG, WebP, or GIF image.")
    mime_type = match.group(1).lower()
    extension = WALLPAPER_MIME_TYPES.get(mime_type)
    if not extension:
        raise ValueError(f"{label} must be a PNG, JPG, WebP, or GIF image.")
    try:
        image_bytes = base64.b64decode(re.sub(r"\s+", "", match.group(2)), validate=True)
    except Exception as exc:
        raise ValueError(f"{label} image data could not be decoded.") from exc
    if not image_bytes:
        raise ValueError(f"{label} image is empty.")
    if len(image_bytes) > max_bytes:
        raise ValueError(f"{label} is too large. Use an image under {max_bytes // (1024 * 1024)} MB.")
    return mime_type, extension, image_bytes


def add_news_image(conn, user, payload):
    if not is_contributor_user(user):
        raise ForbiddenError("Contributor access required.")
    mime_type, extension, image_bytes = decode_image_data_url(payload.get("image"), "News image", MAX_NEWS_IMAGE_BYTES)
    original_name = clean_media_original_name(payload.get("name") or payload.get("original_name"), "News image")
    NEWS_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{int(time.time())}-u{int(user['id'])}-{secrets.token_hex(8)}{extension}"
    path = NEWS_IMAGE_DIR / filename
    path.write_bytes(image_bytes)
    url = news_image_url(filename)
    return {
        "ok": True,
        "filename": filename,
        "original_name": original_name,
        "mime_type": mime_type,
        "size_bytes": len(image_bytes),
        "url": url,
        "markdown": f"![{original_name}]({url})",
    }


def delete_site_wallpaper(conn, wallpaper_id):
    row = conn.execute(
        "SELECT id, filename FROM site_wallpapers WHERE id = ?",
        (wallpaper_id,),
    ).fetchone()
    if not row:
        raise KeyError("Wallpaper not found")
    conn.execute("DELETE FROM site_wallpapers WHERE id = ?", (wallpaper_id,))
    conn.commit()
    try:
        path = (WALLPAPER_DIR / row["filename"]).resolve()
        if WALLPAPER_DIR.resolve() in path.parents and path.exists():
            path.unlink()
    except OSError:
        LOGGER.warning("Could not delete wallpaper file %s", row["filename"], exc_info=True)
    return {
        "ok": True,
        "deleted": str(wallpaper_id),
        "wallpapers": list_site_wallpapers(conn)["wallpapers"],
        "current": current_site_wallpaper(conn),
    }


def send_admin_email_template_test(conn, admin_user, payload):
    del conn
    variables = admin_email_template_variables(admin_user)
    name = str(payload.get("name") or "Template").strip()[:80] or "Template"
    from_email = render_email_template_text(payload.get("from_email") or "", variables).strip()
    if from_email and not sender_email(from_email, fallback=False):
        raise ValueError("Template From must be a valid email address.")
    subject = render_email_template_text(payload.get("subject") or f"%appname% test: {name}", variables).strip()
    if not subject:
        raise ValueError("Template subject is required.")
    body = render_email_template_text(payload.get("body") or "", variables).strip()
    if not body:
        raise ValueError("Template body is required.")
    result = send_email(
        admin_user["email"],
        subject,
        body,
        tags=["arcaneledger", "template-test"],
        from_email=from_email or None,
    )
    return {
        "ok": True,
        "email": admin_user["email"],
        "provider": result.get("provider"),
        "status": result.get("status"),
        "message": f"Test successfully sent to {admin_user['email']}.",
    }


def subscription_email_template_variables(subscription=None, plan="", membership_level=""):
    details = stripe_subscription_receipt_details(subscription or {}, plan)
    period_start = details.get("period_start") or ""
    period_end = details.get("period_end") or ""
    return {
        "membershiplevel": membership_level or "Pro",
        "subscriptionplan": details.get("plan_label") or "Pro",
        "subscriptionstatus": details.get("status") or "",
        "subscriptionid": details.get("subscription_id") or "",
        "subscriptionrenewaldate": format_email_date(period_end),
        "subscriptionrenews": format_email_date(period_end),
        "subscriptionenddate": format_email_date(period_end),
        "subscriptionends": format_email_date(period_end),
        "subscriptionstartdate": format_email_date(period_start),
        "billingurl": f"{verification_base_url()}/settings",
    }


def send_admin_email_templates_for_trigger(conn, user, trigger_key, extra_variables=None):
    if trigger_key not in ADMIN_EMAIL_TEMPLATE_TRIGGERS:
        raise ValueError("Choose a valid email trigger.")
    if not user:
        return {"ok": False, "skipped": "user_not_found", "sent": 0}
    rows = conn.execute(
        """
        SELECT id, name, trigger_key, to_email, from_email, subject, body, created_at, updated_at
        FROM admin_email_templates
        WHERE trigger_key = ?
        ORDER BY updated_at DESC, id DESC
        """,
        (trigger_key,),
    ).fetchall()
    if not rows:
        return {"ok": True, "skipped": "no_templates", "sent": 0}
    variables = admin_email_template_variables(user)
    variables.update(extra_variables or {})
    sent = []
    for row in rows:
        name = row["name"] or "Template"
        to_email = render_email_template_text(row["to_email"] or "%email%", variables).strip()
        from_email = render_email_template_text(row["from_email"] or "", variables).strip()
        subject = render_email_template_text(row["subject"] or f"%appname%: {name}", variables).strip()
        body = render_email_template_text(row["body"] or "", variables).strip()
        if not body:
            LOGGER.warning("Skipping email template %s for %s because the body is empty.", row["id"], trigger_key)
            continue
        if from_email and not sender_email(from_email, fallback=False):
            LOGGER.warning("Skipping email template %s for %s because From is invalid.", row["id"], trigger_key)
            continue
        try:
            result = send_email(
                to_email,
                subject,
                body,
                tags=["arcaneledger", trigger_key],
                from_email=from_email or None,
            )
            sent.append({"id": row["id"], "provider": result.get("provider"), "status": result.get("status")})
        except Exception as exc:
            LOGGER.warning("Could not send email template %s for trigger %s to user %s: %s", row["id"], trigger_key, user["id"], exc)
    return {"ok": True, "sent": len(sent), "templates": sent}


def send_membership_role_change_emails(conn, user_id, previous_role, next_role, subscription=None, plan=""):
    previous_role = clean_user_role(previous_role)
    next_role = clean_user_role(next_role)
    trigger_key = ""
    membership_level = ""
    if previous_role != "pro" and next_role == "pro":
        trigger_key = "subscription_upgraded_pro"
        membership_level = "Pro"
    elif previous_role == "pro" and next_role == "normal":
        trigger_key = "subscription_downgraded_normal"
        membership_level = "Normal"
    if not trigger_key:
        return {"ok": True, "skipped": "no_membership_transition"}
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return {"ok": False, "skipped": "user_not_found"}
    variables = subscription_email_template_variables(subscription, plan, membership_level)
    variables["previousrole"] = previous_role
    variables["newrole"] = next_role
    return send_admin_email_templates_for_trigger(conn, user, trigger_key, variables)


def verification_url(token):
    return f"{verification_base_url()}/verify-email/{urllib.parse.quote(token)}"


def password_reset_url(token):
    return f"{verification_base_url()}/reset-password/{urllib.parse.quote(token)}"


def start_registration(conn, payload):
    email = validate_email(payload.get("email"))
    password = validate_password(payload.get("password"))
    return complete_registration(conn, {"email": email, "password": password, "name": email.split("@", 1)[0], "legacy_direct": True})


def claim_server(conn, payload):
    if app_has_users(conn):
        raise ValueError("This server has already been claimed. Please log in or create an account.")
    email = validate_email(payload.get("email"))
    name = validate_display_name(payload.get("name") or email.split("@", 1)[0])
    password = validate_password(payload.get("password"))
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO users (id, name, email, password_hash, language, theme, email_verified, store_share_id, profile_slug, role, is_banned, created_at, updated_at)
        VALUES (1, ?, ?, ?, ?, ?, 1, ?, ?, 'admin', 0, ?, ?)
        """,
        (
            name,
            email,
            hash_password(password),
            scryfall_language(payload.get("language")),
            clean_theme(payload.get("theme")),
            new_store_share_id(conn),
            unique_profile_slug(conn, name),
            timestamp,
            timestamp,
        ),
    )
    adopt_legacy_data(conn, 1)
    token, expires_at = create_session(conn, 1)
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
    return {"ok": True, "user": user_payload(user), "session_token": token, "expires_at": expires_at}


def request_registration_email(conn, payload):
    email = validate_email(payload.get("email"))
    timestamp = now_iso()
    cleanup_email_verifications(conn)
    if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        raise ValueError("An account with that email already exists.")
    token = secrets.token_urlsafe(36)
    expires = (datetime.now(timezone.utc) + timedelta(minutes=EMAIL_VERIFICATION_MINUTES)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    conn.execute("UPDATE email_verifications SET used_at = ? WHERE email = ? AND used_at IS NULL", (timestamp, email))
    conn.execute(
        "INSERT INTO email_verifications (token_hash, email, created_at, expires_at, used_at) VALUES (?, ?, ?, ?, NULL)",
        (session_hash(token), email, timestamp, expires),
    )
    url = verification_url(token)
    send_email(
        email,
        "Verify your Arcane Ledger account",
        f"Welcome to Arcane Ledger.\n\nVerify your email and finish creating your account:\n{url}\n\nThis link expires in {EMAIL_VERIFICATION_MINUTES} minutes.",
        html=f"""
        <p>Welcome to Arcane Ledger.</p>
        <p><a href="{url}">Verify your email and finish creating your account</a>.</p>
        <p>This link expires in {EMAIL_VERIFICATION_MINUTES} minutes.</p>
        """,
        tags=["arcaneledger", "account-verification"],
    )
    conn.commit()
    return {"ok": True, "email": email, "message": "Check your email for a verification link."}


def cleanup_email_verifications(conn):
    conn.execute("DELETE FROM email_verifications WHERE used_at IS NOT NULL OR expires_at <= ?", (now_iso(),))


def cleanup_password_resets(conn):
    conn.execute("DELETE FROM password_resets WHERE used_at IS NOT NULL OR expires_at <= ?", (now_iso(),))


def verification_from_token(conn, token):
    cleanup_email_verifications(conn)
    token_hash = session_hash(token)
    row = conn.execute(
        """
        SELECT *
        FROM email_verifications
        WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?
        """,
        (token_hash, now_iso()),
    ).fetchone()
    if not row:
        raise ValueError("Verification link is invalid or expired.")
    return row


def verify_registration_token(conn, token):
    row = verification_from_token(conn, token)
    if conn.execute("SELECT 1 FROM users WHERE email = ?", (row["email"],)).fetchone():
        raise ValueError("An account with that email already exists.")
    conn.commit()
    return {"ok": True, "email": row["email"]}


def complete_registration(conn, payload):
    token = (payload.get("token") or "").strip()
    legacy_direct = bool(payload.get("legacy_direct"))
    if legacy_direct:
        email = validate_email(payload.get("email"))
    else:
        if not token:
            raise ValueError("Verification token is required.")
        verification = verification_from_token(conn, token)
        email = verification["email"]
    if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        raise ValueError("An account with that email already exists.")
    name = validate_display_name(payload.get("name"))
    validate_unique_display_name(conn, name)
    password = validate_password(payload.get("password"))
    timestamp = now_iso()
    role = role_for_email(email)
    cursor = conn.execute(
        """
        INSERT INTO users (name, email, password_hash, language, theme, email_verified, store_share_id, profile_slug, role, is_banned, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, 0, ?, ?)
        """,
        (name, email, hash_password(password), scryfall_language(payload.get("language")), clean_theme(payload.get("theme")), new_store_share_id(conn), unique_profile_slug(conn, name), role, timestamp, timestamp),
    )
    user_id = cursor.lastrowid
    if not legacy_direct:
        conn.execute("UPDATE email_verifications SET used_at = ? WHERE token_hash = ?", (timestamp, session_hash(token)))
    adopt_legacy_data(conn, user_id)
    token, expires_at = create_session(conn, user_id)
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return {"ok": True, "user": user_payload(user), "session_token": token, "expires_at": expires_at}


def request_password_reset(conn, payload):
    email = validate_email(payload.get("email"))
    timestamp = now_iso()
    cleanup_password_resets(conn)
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    message = "If that email has an Arcane Ledger account, a password reset link has been sent."
    if not user:
        conn.commit()
        return {"ok": True, "message": message}
    token = secrets.token_urlsafe(36)
    expires = (datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_MINUTES)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    conn.execute("UPDATE password_resets SET used_at = ? WHERE user_id = ? AND used_at IS NULL", (timestamp, user["id"]))
    conn.execute(
        """
        INSERT INTO password_resets (token_hash, user_id, email, created_at, expires_at, used_at)
        VALUES (?, ?, ?, ?, ?, NULL)
        """,
        (session_hash(token), user["id"], email, timestamp, expires),
    )
    url = password_reset_url(token)
    safe_url = html_lib.escape(url)
    send_email(
        email,
        "Reset your Arcane Ledger password",
        f"Reset your Arcane Ledger password:\n{url}\n\nThis link expires in {PASSWORD_RESET_MINUTES} minutes. If you did not request this, you can ignore this email.",
        html=f"""
        <p>Reset your Arcane Ledger password.</p>
        <p><a href="{safe_url}">Choose a new password</a>.</p>
        <p>This link expires in {PASSWORD_RESET_MINUTES} minutes. If you did not request this, you can ignore this email.</p>
        """,
        tags=["arcaneledger", "password-reset"],
    )
    conn.commit()
    return {"ok": True, "message": message}


def password_reset_from_token(conn, token):
    cleanup_password_resets(conn)
    token_hash = session_hash(token)
    row = conn.execute(
        """
        SELECT pr.*, u.email AS user_email
        FROM password_resets pr
        JOIN users u ON u.id = pr.user_id
        WHERE pr.token_hash = ? AND pr.used_at IS NULL AND pr.expires_at > ?
        """,
        (token_hash, now_iso()),
    ).fetchone()
    if not row:
        raise ValueError("Password reset link is invalid or expired.")
    return row


def verify_password_reset_token(conn, token):
    row = password_reset_from_token(conn, token)
    conn.commit()
    return {"ok": True, "email": row["email"] or row["user_email"]}


def complete_password_reset(conn, payload):
    token = (payload.get("token") or "").strip()
    if not token:
        raise ValueError("Password reset token is required.")
    reset = password_reset_from_token(conn, token)
    password = validate_password(payload.get("password"))
    timestamp = now_iso()
    conn.execute(
        "UPDATE users SET password_hash = ?, email_verified = 1, updated_at = ? WHERE id = ?",
        (hash_password(password), timestamp, reset["user_id"]),
    )
    conn.execute("UPDATE password_resets SET used_at = ? WHERE token_hash = ?", (timestamp, session_hash(token)))
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (reset["user_id"],))
    session_token, expires_at = create_session(conn, reset["user_id"])
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (reset["user_id"],)).fetchone()
    return {"ok": True, "user": user_payload(user), "session_token": session_token, "expires_at": expires_at}


def login_user(conn, payload):
    email = validate_email(payload.get("email"))
    password = payload.get("password") or ""
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("Email or password is incorrect.")
    if int(user["is_banned"] if "is_banned" in user.keys() else 0):
        raise PermissionError("This account has been banned.")
    token, expires_at = create_session(conn, user["id"])
    conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_iso(),))
    conn.commit()
    return {"ok": True, "user": user_payload(user), "session_token": token, "expires_at": expires_at}


def logout_user(conn, token):
    if token:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (session_hash(token),))
        conn.commit()
    return {"ok": True}


def update_user_settings(conn, user_id, payload):
    language = scryfall_language(payload.get("language"))
    theme = clean_theme(payload.get("theme"))
    display_name = validate_display_name(payload.get("name"))
    validate_unique_display_name(conn, display_name, user_id)
    profile_slug_value = unique_profile_slug(conn, display_name, user_id)
    public_email = validate_optional_email(payload.get("public_email"))
    contact_whatsapp = clean_contact_handle(payload.get("contact_whatsapp"), "WhatsApp username")
    contact_signal = clean_contact_handle(payload.get("contact_signal"), "Signal username")
    contact_telegram = clean_contact_handle(payload.get("contact_telegram"), "Telegram username")
    contact_discord = clean_contact_handle(payload.get("contact_discord"), "Discord username")
    contact_website = clean_contact_url(payload.get("contact_website"))
    contact_whatnot = clean_contact_handle(payload.get("contact_whatnot"), "Whatnot username")
    contact_mtg_arena = clean_contact_handle(payload.get("contact_mtg_arena"), "MtG Arena username")
    contact_mtgo = clean_contact_handle(payload.get("contact_mtgo"), "MTGO username")
    contact_instagram = clean_contact_handle(payload.get("contact_instagram"), "Instagram username")
    contact_bluesky = clean_contact_handle(payload.get("contact_bluesky"), "Bluesky username")
    contact_threads = clean_contact_handle(payload.get("contact_threads"), "Threads username")
    about_me = clean_profile_text(payload.get("about_me"))
    profile_image = clean_profile_image(payload.get("profile_image"))
    default_purchase_price = money(payload.get("default_purchase_price"), fallback=0.01)
    if default_purchase_price <= 0:
        default_purchase_price = 0.01
    default_sell_price = money(payload.get("default_sell_price"), fallback=0)
    if default_sell_price < 0:
        default_sell_price = 0
    conn.execute(
        """
        UPDATE users
        SET name = ?, profile_slug = ?, language = ?, theme = ?, public_email = ?, contact_whatsapp = ?,
            contact_signal = ?, contact_telegram = ?, contact_discord = ?, contact_website = ?,
            contact_whatnot = ?, contact_mtg_arena = ?, contact_mtgo = ?, contact_instagram = ?,
            contact_bluesky = ?, contact_threads = ?, about_me = ?, profile_image = ?,
            default_purchase_price = ?, default_sell_price = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            display_name,
            profile_slug_value,
            language,
            theme,
            public_email,
            contact_whatsapp,
            contact_signal,
            contact_telegram,
            contact_discord,
            contact_website,
            contact_whatnot,
            contact_mtg_arena,
            contact_mtgo,
            contact_instagram,
            contact_bluesky,
            contact_threads,
            about_me,
            profile_image,
            default_purchase_price,
            default_sell_price,
            now_iso(),
            user_id,
        ),
    )
    conn.commit()
    return {"ok": True, "user": user_payload(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())}


def clear_user_data(conn, user_id):
    for table in ("container_cards", "deck_cards", "wishlist_items"):
        id_column = "container_id" if table == "container_cards" else "deck_id" if table == "deck_cards" else "wishlist_id"
        owner_table = "containers" if table == "container_cards" else "decks" if table == "deck_cards" else "wishlists"
        conn.execute(
            f"DELETE FROM {table} WHERE {id_column} IN (SELECT id FROM {owner_table} WHERE user_id = ?)",
            (user_id,),
        )
    conn.execute("DELETE FROM favorite_store_listings WHERE user_id = ? OR seller_user_id = ?", (user_id, user_id))
    conn.execute(
        "DELETE FROM card_comment_votes WHERE user_id = ? OR comment_id IN (SELECT id FROM card_comments WHERE user_id = ?)",
        (user_id, user_id),
    )
    conn.execute("DELETE FROM card_comments WHERE user_id = ?", (user_id,))
    for table in ("notifications", "favorite_decks", "card_notes", "card_sale_journal", "card_sales", "inventory_adjustments", "wishlist_cards", "card_meta", "card_purchases", "collection", "wishlists", "containers", "decks"):
        conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
    conn.commit()
    return {"ok": True}


def delete_user_profile(conn, user_id):
    clear_user_data(conn, user_id)
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return {"ok": True}


def is_admin_user(user):
    if not user:
        return False
    if isinstance(user, sqlite3.Row):
        role = clean_user_role(user["role"] if "role" in user.keys() else role_for_email(user["email"]))
        return role == "admin" and not int(user["is_banned"] if "is_banned" in user.keys() else 0)
    return clean_user_role(user.get("role")) == "admin" and not bool(user.get("is_banned"))


def is_contributor_user(user):
    if not user:
        return False
    if isinstance(user, sqlite3.Row):
        role = effective_user_role(user)
        banned = bool(user["is_banned"] if "is_banned" in user.keys() else 0)
    else:
        role = effective_user_role(user)
        banned = bool(user.get("is_banned"))
    return role in {"admin", "contributor"} and not banned


def admin_user_payload(row):
    email = row["email"]
    role = clean_user_role(row["role"] if "role" in row.keys() else role_for_email(email))
    keys = set(row.keys())
    return {
        "id": row["id"],
        "name": row["name"],
        "email": email,
        "role": role,
        "is_admin": role == "admin",
        "is_banned": bool(row["is_banned"] if "is_banned" in row.keys() else 0),
        "email_verified": bool(row["email_verified"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "owned_quantity": int(row["owned_quantity"] or 0) if "owned_quantity" in keys else 0,
        "deck_count": int(row["deck_count"] or 0) if "deck_count" in keys else 0,
        "container_count": int(row["container_count"] or 0) if "container_count" in keys else 0,
        "for_sale_quantity": int(row["for_sale_quantity"] or 0) if "for_sale_quantity" in keys else 0,
        "protected_admin": normalize_email(email) in ADMIN_EMAILS,
    }


def list_admin_users(conn):
    rows = conn.execute(
        """
        SELECT u.*,
               COALESCE(c.owned_quantity, 0) AS owned_quantity,
               COALESCE(d.deck_count, 0) AS deck_count,
               COALESCE(ct.container_count, 0) AS container_count,
               COALESCE(s.for_sale_quantity, 0) AS for_sale_quantity
        FROM users u
        LEFT JOIN (
            SELECT user_id, SUM(quantity) AS owned_quantity
            FROM collection
            GROUP BY user_id
        ) c ON c.user_id = u.id
        LEFT JOIN (
            SELECT user_id, COUNT(*) AS deck_count
            FROM decks
            GROUP BY user_id
        ) d ON d.user_id = u.id
        LEFT JOIN (
            SELECT user_id, COUNT(*) AS container_count
            FROM containers
            GROUP BY user_id
        ) ct ON ct.user_id = u.id
        LEFT JOIN (
            SELECT user_id, SUM(quantity) AS for_sale_quantity
            FROM card_sales
            GROUP BY user_id
        ) s ON s.user_id = u.id
        ORDER BY CASE lower(COALESCE(u.role, 'normal')) WHEN 'admin' THEN 0 WHEN 'contributor' THEN 1 WHEN 'pro' THEN 2 ELSE 3 END, lower(u.email)
        """
    ).fetchall()
    return {"users": [admin_user_payload(row) for row in rows], "roles": ["admin", "contributor", "pro", "normal"]}


def update_admin_user(conn, acting_user_id, target_user_id, payload):
    target = conn.execute("SELECT * FROM users WHERE id = ?", (target_user_id,)).fetchone()
    if not target:
        raise KeyError("User not found.")
    previous_role = effective_user_role(target)
    protected_admin = normalize_email(target["email"]) in ADMIN_EMAILS
    next_role = clean_user_role(payload.get("role", target["role"] if "role" in target.keys() else role_for_email(target["email"])))
    next_banned = bool_int(payload.get("is_banned", target["is_banned"] if "is_banned" in target.keys() else 0))
    if protected_admin and next_role != "admin":
        raise ValueError("Seed admin accounts cannot be demoted.")
    if protected_admin and next_banned:
        raise ValueError("Seed admin accounts cannot be banned.")
    if int(target_user_id) == int(acting_user_id) and (next_role != "admin" or next_banned):
        raise ValueError("You cannot remove your own admin access.")
    timestamp = now_iso()
    conn.execute(
        "UPDATE users SET role = ?, is_banned = ?, updated_at = ? WHERE id = ?",
        (next_role, next_banned, timestamp, target_user_id),
    )
    if next_banned:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (target_user_id,))
    updated = conn.execute("SELECT * FROM users WHERE id = ?", (target_user_id,)).fetchone()
    send_membership_role_change_emails(conn, target_user_id, previous_role, effective_user_role(updated))
    conn.commit()
    return {"ok": True, "user": admin_user_payload(updated), **list_admin_users(conn)}


def admin_delete_user(conn, acting_user_id, target_user_id):
    target = conn.execute("SELECT * FROM users WHERE id = ?", (target_user_id,)).fetchone()
    if not target:
        raise KeyError("User not found.")
    if int(target_user_id) == int(acting_user_id):
        raise ValueError("Use Settings to delete your own profile.")
    if normalize_email(target["email"]) in ADMIN_EMAILS:
        raise ValueError("Seed admin accounts cannot be deleted.")
    clear_user_data(conn, target_user_id)
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (target_user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (target_user_id,))
    conn.commit()
    return {"ok": True, **list_admin_users(conn)}


REPORT_TARGET_TYPES = {"card_comment", "profile_post", "profile_comment"}
MODERATOR_REMOVED_TEXT = "this was removed by a moderator"


def clean_report_target_type(value):
    target_type = (value or "").strip().lower()
    if target_type not in REPORT_TARGET_TYPES:
        raise ValueError("That content cannot be reported.")
    return target_type


def report_target_row(conn, target_type, target_id):
    if target_type == "card_comment":
        return conn.execute(
            """
            SELECT cc.id, cc.body, cc.created_at, cc.card_id, NULL AS parent_id,
                   u.id AS author_id, u.name AS author_name, u.email AS author_email, u.profile_slug AS author_slug,
                   c.name AS context_name, c.flavor_name AS context_flavor_name
            FROM card_comments cc
            JOIN users u ON u.id = cc.user_id
            LEFT JOIN cards c ON c.scryfall_id = cc.card_id
            WHERE cc.id = ?
            """,
            (target_id,),
        ).fetchone()
    if target_type == "profile_post":
        return conn.execute(
            """
            SELECT p.id, p.body, p.created_at, p.card_id, p.deck_id AS parent_id,
                   u.id AS author_id, u.name AS author_name, u.email AS author_email, u.profile_slug AS author_slug,
                   COALESCE(NULLIF(c.flavor_name, ''), c.name, d.name, 'Blog post') AS context_name,
                   c.flavor_name AS context_flavor_name
            FROM profile_posts p
            JOIN users u ON u.id = p.user_id
            LEFT JOIN cards c ON c.scryfall_id = p.card_id
            LEFT JOIN decks d ON d.id = p.deck_id
            WHERE p.id = ?
            """,
            (target_id,),
        ).fetchone()
    if target_type == "profile_comment":
        return conn.execute(
            """
            SELECT c.id, c.body, c.created_at, NULL AS card_id, c.post_id AS parent_id,
                   u.id AS author_id, u.name AS author_name, u.email AS author_email, u.profile_slug AS author_slug,
                   'Blog comment' AS context_name, NULL AS context_flavor_name
            FROM profile_post_comments c
            JOIN users u ON u.id = c.author_user_id
            WHERE c.id = ?
            """,
            (target_id,),
        ).fetchone()
    return None


def report_target_payload(conn, target_type, target_id):
    row = report_target_row(conn, target_type, target_id)
    if not row:
        return None
    return {
        "type": target_type,
        "id": target_id,
        "body": row["body"] or "",
        "created_at": row["created_at"],
        "context_name": row["context_flavor_name"] or row["context_name"] or "",
        "card_id": row["card_id"],
        "parent_id": row["parent_id"],
        "author": {
            "id": row["author_id"],
            "name": row["author_name"],
            "email": row["author_email"],
            "profile_slug": row["author_slug"],
            "profile_url": f"/user/{urllib.parse.quote(row['author_slug'])}" if row["author_slug"] else "",
        },
    }


def create_content_report(conn, reporter_user_id, payload):
    target_type = clean_report_target_type(payload.get("target_type"))
    target_id = int(payload.get("target_id") or 0)
    if target_id <= 0:
        raise ValueError("Report target is required.")
    if not report_target_row(conn, target_type, target_id):
        raise KeyError("Reported content not found")
    reason = clean_report_reason(payload.get("reason"))
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO content_reports (reporter_user_id, target_type, target_id, reason, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """,
        (reporter_user_id, target_type, target_id, reason, timestamp, timestamp),
    )
    conn.commit()
    return {"ok": True, "message": "Report submitted."}


def list_content_reports(conn):
    rows = conn.execute(
        """
        SELECT r.*, reporter.name AS reporter_name, reporter.email AS reporter_email, reporter.profile_slug AS reporter_slug,
               admin.name AS admin_name, admin.email AS admin_email
        FROM content_reports r
        JOIN users reporter ON reporter.id = r.reporter_user_id
        LEFT JOIN users admin ON admin.id = r.admin_user_id
        ORDER BY CASE r.status WHEN 'pending' THEN 0 ELSE 1 END, r.created_at DESC
        LIMIT 200
        """
    ).fetchall()
    reports = []
    for row in rows:
        reports.append({
            "id": row["id"],
            "target_type": row["target_type"],
            "target_id": row["target_id"],
            "reason": row["reason"],
            "status": row["status"],
            "resolution": row["resolution"],
            "created_at": row["created_at"],
            "resolved_at": row["resolved_at"],
            "reporter": {
                "name": row["reporter_name"],
                "email": row["reporter_email"],
                "profile_slug": row["reporter_slug"],
                "profile_url": f"/user/{urllib.parse.quote(row['reporter_slug'])}" if row["reporter_slug"] else "",
            },
            "admin": {
                "name": row["admin_name"],
                "email": row["admin_email"],
            } if row["admin_user_id"] else None,
            "target": report_target_payload(conn, row["target_type"], row["target_id"]),
        })
    return {"reports": reports}


def mark_report_target_removed(conn, target_type, target_id):
    timestamp = now_iso()
    if target_type == "card_comment":
        cursor = conn.execute(
            "UPDATE card_comments SET body = ?, updated_at = ? WHERE id = ?",
            (MODERATOR_REMOVED_TEXT, timestamp, target_id),
        )
    elif target_type == "profile_post":
        cursor = conn.execute(
            "UPDATE profile_posts SET body = ?, updated_at = ? WHERE id = ?",
            (MODERATOR_REMOVED_TEXT, timestamp, target_id),
        )
    elif target_type == "profile_comment":
        cursor = conn.execute(
            "UPDATE profile_post_comments SET body = ? WHERE id = ?",
            (MODERATOR_REMOVED_TEXT, target_id),
        )
    else:
        raise ValueError("That content cannot be moderated.")
    if cursor.rowcount == 0:
        raise KeyError("Reported content not found")


def resolve_content_report(conn, admin_user_id, report_id, payload):
    action = (payload.get("action") or "").strip().lower()
    if action not in {"keep", "remove"}:
        raise ValueError("Choose a moderation action.")
    report = conn.execute("SELECT * FROM content_reports WHERE id = ?", (report_id,)).fetchone()
    if not report:
        raise KeyError("Report not found")
    if action == "remove":
        mark_report_target_removed(conn, report["target_type"], report["target_id"])
    timestamp = now_iso()
    resolution = "reviewed_removed" if action == "remove" else "reviewed_ok"
    conn.execute(
        """
        UPDATE content_reports
        SET status = 'resolved',
            resolution = ?,
            admin_user_id = ?,
            resolved_at = ?,
            updated_at = ?
        WHERE target_type = ? AND target_id = ? AND status = 'pending'
        """,
        (resolution, admin_user_id, timestamp, timestamp, report["target_type"], report["target_id"]),
    )
    conn.commit()
    return {"ok": True, **list_content_reports(conn)}


def new_share_id(conn):
    while True:
        share_id = secrets.token_urlsafe(9)
        exists = conn.execute("SELECT 1 FROM collection WHERE share_id = ?", (share_id,)).fetchone()
        if not exists:
            return share_id


def ensure_collection_share_ids(conn):
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(collection)").fetchall()}
    if "share_id" not in columns:
        conn.execute("ALTER TABLE collection ADD COLUMN share_id TEXT")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_collection_share_id ON collection(share_id)")
    rows = conn.execute(
        """
        SELECT user_id, card_id, variant
        FROM collection
        WHERE share_id IS NULL OR share_id = ''
        """
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE collection SET share_id = ? WHERE user_id IS ? AND card_id = ? AND variant = ?",
            (new_share_id(conn), row["user_id"], row["card_id"], row["variant"]),
        )


def new_deck_share_id(conn):
    while True:
        share_id = secrets.token_urlsafe(9)
        exists = conn.execute("SELECT 1 FROM decks WHERE share_id = ?", (share_id,)).fetchone()
        if not exists:
            return share_id


def new_wishlist_share_id(conn):
    while True:
        share_id = secrets.token_urlsafe(9)
        exists = conn.execute("SELECT 1 FROM wishlists WHERE share_id = ?", (share_id,)).fetchone()
        if not exists:
            return share_id


def new_container_share_id(conn):
    while True:
        share_id = secrets.token_urlsafe(9)
        exists = conn.execute("SELECT 1 FROM containers WHERE share_id = ?", (share_id,)).fetchone()
        if not exists:
            return share_id


def new_store_share_id(conn):
    while True:
        share_id = secrets.token_urlsafe(9)
        exists = conn.execute("SELECT 1 FROM users WHERE store_share_id = ?", (share_id,)).fetchone()
        if not exists:
            return share_id


def ensure_deck_share_ids(conn):
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(decks)").fetchall()}
    if "share_id" not in columns:
        conn.execute("ALTER TABLE decks ADD COLUMN share_id TEXT")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_decks_share_id ON decks(share_id)")
    rows = conn.execute(
        """
        SELECT id
        FROM decks
        WHERE share_id IS NULL OR share_id = ''
        """
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE decks SET share_id = ? WHERE id = ?",
            (new_deck_share_id(conn), row["id"]),
        )


def ensure_wishlist_share_ids(conn):
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(wishlists)").fetchall()}
    if "share_id" not in columns:
        conn.execute("ALTER TABLE wishlists ADD COLUMN share_id TEXT")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_wishlists_share_id ON wishlists(share_id)")
    rows = conn.execute(
        """
        SELECT id
        FROM wishlists
        WHERE share_id IS NULL OR share_id = ''
        """
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE wishlists SET share_id = ? WHERE id = ?",
            (new_wishlist_share_id(conn), row["id"]),
        )


def ensure_container_share_ids(conn):
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(containers)").fetchall()}
    if "share_id" not in columns:
        conn.execute("ALTER TABLE containers ADD COLUMN share_id TEXT")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_containers_share_id ON containers(share_id)")
    rows = conn.execute(
        """
        SELECT id
        FROM containers
        WHERE share_id IS NULL OR share_id = ''
        """
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE containers SET share_id = ? WHERE id = ?",
            (new_container_share_id(conn), row["id"]),
        )


def sync_catalog(conn):
    init_db(conn)
    synced_at = now_iso()
    sets_payload = request_json(SCRYFALL_SETS_URL)
    all_sets = sets_payload.get("data", [])

    for item in all_sets:
        conn.execute(
            """
            INSERT INTO sets (code, name, set_type, card_count, released_at, parent_set_code, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                set_type = excluded.set_type,
                card_count = excluded.card_count,
                released_at = excluded.released_at,
                parent_set_code = excluded.parent_set_code,
                synced_at = excluded.synced_at
            """,
            (
                item.get("code"),
                item.get("name"),
                item.get("set_type"),
                item.get("card_count") or 0,
                item.get("released_at"),
                item.get("parent_set_code"),
                synced_at,
            ),
        )

    query = scryfall_query_with_language(SCRYFALL_QUERY.strip() or "game:paper")
    params = {
        "q": query,
        "unique": "prints",
        "include_extras": "true",
        "include_variations": "true",
        "order": "set",
    }
    url = SCRYFALL_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    cards_seen = 0
    while url:
        payload = request_json(url)
        for card in payload.get("data", []):
            upsert_card(conn, card, synced_at)
            cards_seen += 1
        url = payload.get("next_page") if payload.get("has_more") else None
        if url:
            time.sleep(0.08)
    conn.commit()
    return {"sets": len(all_sets), "query": query, "cards": cards_seen}


def upsert_set_metadata(conn, item, synced_at, cached_at=None):
    conn.execute(
        """
        INSERT INTO sets (code, name, set_type, card_count, released_at, parent_set_code, synced_at, cached_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(code) DO UPDATE SET
            name = excluded.name,
            set_type = excluded.set_type,
            card_count = excluded.card_count,
            released_at = excluded.released_at,
            parent_set_code = excluded.parent_set_code,
            synced_at = excluded.synced_at,
            cached_at = COALESCE(excluded.cached_at, sets.cached_at)
        """,
        (
            item.get("code"),
            item.get("name"),
            item.get("set_type"),
            item.get("card_count") or 0,
            item.get("released_at"),
            item.get("parent_set_code"),
            synced_at,
            cached_at,
        ),
    )


def cache_set_catalog(conn, set_code, force=False):
    code = (set_code or "").strip().lower()
    if not code:
        return {"set": code, "cached": False, "cards": 0}
    existing = conn.execute("SELECT cached_at FROM sets WHERE code = ?", (code,)).fetchone()
    if existing and existing["cached_at"] and not force:
        return {"set": code, "cached": True, "cards": 0, "skipped": True}

    synced_at = now_iso()
    set_payload = request_json(SCRYFALL_SET_URL.format(set_code=urllib.parse.quote(code)))
    upsert_set_metadata(conn, set_payload, synced_at, cached_at=synced_at)

    params = {
        "q": scryfall_query_with_language(f"e:{code} game:paper"),
        "unique": "prints",
        "include_extras": "true",
        "include_variations": "true",
        "order": "set",
    }
    url = SCRYFALL_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    cards_seen = 0
    while url:
        payload = request_json(url)
        for card in payload.get("data", []):
            upsert_card(conn, card, synced_at)
            cards_seen += 1
        url = payload.get("next_page") if payload.get("has_more") else None
        if url:
            time.sleep(0.08)
    conn.execute("UPDATE sets SET cached_at = ? WHERE code = ?", (synced_at, code))
    conn.commit()
    return {"set": code, "cached": True, "cards": cards_seen}


def cache_owned_sets(conn, user_id=None):
    user_filter = "AND col.user_id = ?" if user_id is not None else ""
    params = [user_id] if user_id is not None else []
    rows = conn.execute(
        f"""
        SELECT DISTINCT c.set_code
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        WHERE col.quantity > 0 {user_filter}
        ORDER BY c.set_code
        """,
        params,
    ).fetchall()
    results = []
    for row in rows:
        results.append(cache_set_catalog(conn, row["set_code"]))
    return {"sets": results}


def card_summary(card, owned_quantity=0):
    prices = card.get("prices") or {}
    colors = card_colors(card, "colors")
    color_identity = card_colors(card, "color_identity")
    return {
        "scryfall_id": card.get("id"),
        "name": card.get("name"),
        "flavor_name": card.get("flavor_name") or "",
        "display_name": card.get("flavor_name") or card.get("name"),
        "set_code": card.get("set"),
        "set_name": card.get("set_name"),
        "set_type": card.get("set_type"),
        "collector_number": card.get("collector_number"),
        "rarity": card.get("rarity"),
        "type_line": card.get("type_line"),
        "type_category": card_type_category(card.get("type_line")),
        "colors": colors,
        "color_identity": color_identity,
        "flavor_text": card_text(card, "flavor_text") or "",
        "finishes": card.get("finishes") or [],
        "promo": bool(card.get("promo")),
        "promo_types": card.get("promo_types") or [],
        "image_small": card_image(card, "small"),
        "image_normal": card_image(card, "normal"),
        "scryfall_uri": card.get("scryfall_uri"),
        "prices": {
            "usd": money(prices.get("usd")),
            "usd_foil": money(prices.get("usd_foil")),
            "usd_etched": money(prices.get("usd_etched")),
        },
        "owned_quantity": owned_quantity,
    }


def scryfall_card_detail_payload(card, variant="Normal", user_id=None, conn=None):
    summary = card_summary(card, 0)
    price = scryfall_price(card, variant)
    summary.update({
        "variant": variant or "Normal",
        "quantity": 0,
        "paid_price": 0.01,
        "acquired_date": "",
        "card_condition": DEFAULT_CARD_CONDITION,
        "graded": 0,
        "notes": "",
        "favorite": 0,
        "missing_list": 0,
        "wishlist": 0,
        "display_price": price,
        "market_price": price,
        "owned_value": 0,
        "total_value": 0,
        "gain_loss": 0,
        "purchases": [],
        "movements": [],
        "deck_memberships": [],
        "container_memberships": [],
        "catalog_only": True,
    })
    if conn is not None and user_id is not None and summary.get("scryfall_id"):
        meta = conn.execute(
            """
            SELECT favorite, missing_list, wishlist
            FROM card_meta
            WHERE user_id = ? AND card_id = ? AND variant = ?
            """,
            (user_id, summary["scryfall_id"], variant or "Normal"),
        ).fetchone()
        if meta:
            summary["favorite"] = meta["favorite"] or 0
            summary["missing_list"] = meta["missing_list"] or 0
            summary["wishlist"] = meta["wishlist"] or 0
    return summary


def owned_quantities_for_cards(conn, card_ids, user_id=None):
    if not card_ids:
        return {}
    placeholders = ",".join("?" for _ in card_ids)
    user_filter = "AND user_id = ?" if user_id is not None else "AND user_id IS NULL"
    values = list(card_ids) + ([user_id] if user_id is not None else [])
    rows = conn.execute(
        f"""
        SELECT card_id, COALESCE(SUM(quantity), 0) AS owned_quantity
        FROM collection
        WHERE card_id IN ({placeholders}) {user_filter}
        GROUP BY card_id
        """,
        values,
    ).fetchall()
    return {row["card_id"]: row["owned_quantity"] or 0 for row in rows}


def variant_summaries_for_cards(conn, card_ids, user_id=None):
    if not card_ids or user_id is None:
        return {}
    unique_ids = list(dict.fromkeys(card_id for card_id in card_ids if card_id))
    if not unique_ids:
        return {}
    placeholders = ",".join("?" for _ in unique_ids)
    summaries = {}
    collection_rows = conn.execute(
        f"""
        SELECT card_id, COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
               COALESCE(SUM(quantity), 0) AS quantity
        FROM collection
        WHERE user_id = ? AND card_id IN ({placeholders}) AND COALESCE(quantity, 0) > 0
        GROUP BY card_id, COALESCE(NULLIF(variant, ''), 'Normal')
        """,
        [user_id] + unique_ids,
    ).fetchall()
    for row in collection_rows:
        card_id = row["card_id"]
        variant = row["variant"] or "Normal"
        summaries.setdefault(card_id, {})[variant] = {
            "variant": variant,
            "quantity": int(row["quantity"] or 0),
            "conditions": [],
        }
    purchase_rows = conn.execute(
        f"""
        SELECT card_id, COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
               COALESCE(NULLIF(card_condition, ''), ?) AS card_condition,
               COALESCE(SUM(quantity), 0) AS quantity
        FROM card_purchases
        WHERE user_id = ? AND card_id IN ({placeholders})
        GROUP BY card_id, COALESCE(NULLIF(variant, ''), 'Normal'), COALESCE(NULLIF(card_condition, ''), ?)
        HAVING COALESCE(SUM(quantity), 0) > 0
        """,
        [DEFAULT_CARD_CONDITION, user_id] + unique_ids + [DEFAULT_CARD_CONDITION],
    ).fetchall()
    for row in purchase_rows:
        card_id = row["card_id"]
        variant = row["variant"] or "Normal"
        summary = summaries.setdefault(card_id, {}).setdefault(variant, {
            "variant": variant,
            "quantity": 0,
            "conditions": [],
        })
        summary["conditions"].append({
            "card_condition": card_condition(row["card_condition"]),
            "quantity": int(row["quantity"] or 0),
        })
    for variants in summaries.values():
        for summary in variants.values():
            if not summary["conditions"] and summary["quantity"] > 0:
                summary["conditions"].append({
                    "card_condition": DEFAULT_CARD_CONDITION,
                    "quantity": summary["quantity"],
                })
            summary["conditions"].sort(key=lambda item: (CONDITION_ORDER.get(item["card_condition"], 99), item["card_condition"]))
    def sort_key(item):
        variant = item["variant"] or "Normal"
        return (0 if variant.lower() == "normal" else 1, variant.lower())
    return {
        card_id: sorted(variants.values(), key=sort_key)
        for card_id, variants in summaries.items()
    }


def wishlist_flags_for_cards(conn, card_ids, user_id=None):
    if not card_ids:
        return {}
    placeholders = ",".join("?" for _ in card_ids)
    flags = {}
    user_filter = "AND user_id = ?" if user_id is not None else "AND user_id IS NULL"
    values = list(card_ids) + ([user_id] if user_id is not None else [])
    rows = conn.execute(
        f"""
        SELECT card_id, MAX(COALESCE(wishlist, 0)) AS wishlist
        FROM card_meta
        WHERE card_id IN ({placeholders}) {user_filter}
        GROUP BY card_id
        """,
        values,
    ).fetchall()
    flags.update({row["card_id"]: row["wishlist"] or 0 for row in rows})
    rows = conn.execute(
        f"""
        SELECT card_id, 1 AS wishlist
        FROM wishlist_items
        WHERE card_id IN ({placeholders}) {user_filter}
        """,
        values,
    ).fetchall()
    flags.update({row["card_id"]: row["wishlist"] or 0 for row in rows})
    rows = conn.execute(
        f"""
        SELECT card_id, 1 AS wishlist
        FROM wishlist_cards
        WHERE card_id IN ({placeholders}) {user_filter}
        """,
        values,
    ).fetchall()
    flags.update({row["card_id"]: row["wishlist"] or 0 for row in rows})
    return flags


def search_scryfall_cards(conn, query, language=None, order=None, user_id=None):
    text = (query or "").strip()
    if len(text) < 2:
        return {"cards": []}
    allowed_orders = {"released", "name", "set", "rarity", "color", "usd", "edhrec"}
    order_value = order if order in allowed_orders else "released"
    params = {
        "q": scryfall_query_with_language(f"{text} game:paper", language),
        "unique": "prints",
        "include_extras": "true",
        "include_variations": "true",
        "order": order_value,
        "dir": "desc",
    }
    url = SCRYFALL_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    try:
        payload = request_json(url)
    except urllib.error.HTTPError as exc:
        if exc.code == HTTPStatus.NOT_FOUND:
            return {"cards": []}
        raise
    scryfall_cards = payload.get("data", [])[:24]
    card_ids = [card.get("id") for card in scryfall_cards if card.get("id")]
    owned_quantities = owned_quantities_for_cards(conn, card_ids, user_id)
    variant_summaries = variant_summaries_for_cards(conn, card_ids, user_id)
    wishlist_flags = wishlist_flags_for_cards(conn, card_ids, user_id)
    cards = []
    for card in scryfall_cards:
        summary = card_summary(card, owned_quantities.get(card.get("id"), 0))
        summary["variant_summaries"] = variant_summaries.get(card.get("id"), [])
        summary["wishlist"] = wishlist_flags.get(card.get("id"), 0)
        cards.append(summary)
    return {"cards": cards}


def scryfall_card_by_id(conn, card_id, user_id=None):
    card_id = (card_id or "").strip()
    if not card_id:
        raise ValueError("Choose a Scryfall card first.")
    card = request_json(SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id)))
    owned_quantity = owned_quantities_for_cards(conn, [card.get("id")], user_id).get(card.get("id"), 0)
    summary = card_summary(card, owned_quantity)
    summary["variant_summaries"] = variant_summaries_for_cards(conn, [card.get("id")], user_id).get(card.get("id"), [])
    summary["wishlist"] = wishlist_flags_for_cards(conn, [card.get("id")], user_id).get(card.get("id"), 0)
    return {"card": summary}


def variant_price_from_row(card, variant):
    def card_value(key):
        if isinstance(card, sqlite3.Row):
            return card[key] if key in card.keys() else 0
        return card.get(key, 0) if isinstance(card, dict) else 0

    prices = card_value("prices") or {}
    if not isinstance(prices, dict):
        prices = {}
    current_usd = card_value("current_usd") or prices.get("usd") or 0
    current_usd_foil = card_value("current_usd_foil") or prices.get("usd_foil") or 0
    current_usd_etched = card_value("current_usd_etched") or prices.get("usd_etched") or 0
    variant_text = (variant or "").lower()
    if "etched" in variant_text and current_usd_etched:
        return current_usd_etched
    if "foil" in variant_text and current_usd_foil:
        return current_usd_foil
    return current_usd or current_usd_foil or current_usd_etched or 0


def aggregate_variant_market_value(card, variant_summaries):
    return sum(
        int(summary.get("quantity") or 0) * float(variant_price_from_row(card, summary.get("variant") or "Normal") or 0)
        for summary in variant_summaries or []
    )


def card_collection_financial_summary(conn, user_id, card_id):
    row = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity,
               COALESCE(SUM(quantity * paid_price), 0) AS total_paid,
               MIN(NULLIF(acquired_date, '')) AS first_obtained
        FROM collection
        WHERE user_id = ? AND card_id = ? AND COALESCE(quantity, 0) > 0
        """,
        (user_id, card_id),
    ).fetchone()
    quantity = int(row["quantity"] or 0) if row else 0
    total_paid = float(row["total_paid"] or 0) if row else 0.0
    return {
        "owned_quantity": quantity,
        "total_paid": total_paid,
        "average_paid": (total_paid / quantity) if quantity > 0 else 0,
        "first_obtained": row["first_obtained"] if row else "",
    }


def apply_card_collection_financials(card, conn, user_id, card_id):
    summary = card_collection_financial_summary(conn, user_id, card_id)
    total_value = aggregate_variant_market_value(card, card.get("variant_summaries") or [])
    if card.get("variant_summaries"):
        card["owned_value"] = total_value
        card["total_value"] = total_value
    else:
        total_value = float(card.get("total_value") or card.get("owned_value") or 0)
    card["owned_quantity"] = summary["owned_quantity"]
    card["total_paid"] = summary["total_paid"]
    card["average_paid"] = summary["average_paid"]
    card["first_obtained"] = summary["first_obtained"] or card.get("acquired_date") or ""
    card["gain_loss"] = total_value - summary["total_paid"]
    return card


def validate_selected_card(card, payload):
    expected = {
        "name": payload.get("expected_name"),
        "set": payload.get("expected_set_code"),
        "collector_number": payload.get("expected_collector_number"),
        "image_normal": payload.get("expected_image_normal"),
    }
    actual = {
        "name": card.get("name"),
        "set": card.get("set"),
        "collector_number": card.get("collector_number"),
        "image_normal": card_image(card, "normal"),
    }
    for field, expected_value in expected.items():
        if expected_value and str(expected_value) != str(actual.get(field) or ""):
            raise ValueError("Selected Scryfall card changed before save. Please search and choose the card again.")


def record_card_purchase(conn, user_id, card_id, variant, quantity, condition, purchase_date, total_price, store_name="", store_location="", graded=0, notes=""):
    quantity = max(1, int(quantity or 1))
    total_price = money(total_price, fallback=0.01)
    if total_price <= 0:
        total_price = 0.01
    store_name = clean_purchase_detail(store_name, "Store name")
    store_location = clean_purchase_detail(store_location, "Store location")
    notes = (notes or "").strip()
    if len(notes) > 1000:
        raise ValueError("Purchase notes must be 1,000 characters or fewer.")
    conn.execute(
        """
        INSERT INTO card_purchases (user_id, card_id, variant, quantity, card_condition, purchase_date, total_price, graded, store_name, store_location, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            card_id,
            variant or "Normal",
            quantity,
            card_condition(condition),
            purchase_date or today_iso(),
            total_price,
            bool_int(graded),
            store_name,
            store_location,
            notes,
            now_iso(),
        ),
    )


def rollup_collection_from_purchases(conn, user_id, card_id, variant):
    variant = variant or "Normal"
    aggregate = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity,
               COALESCE(SUM(total_price), 0) AS total_paid,
               MIN(purchase_date) AS first_purchase,
               MAX(COALESCE(graded, 0)) AS graded
        FROM card_purchases
        WHERE user_id = ? AND card_id = ? AND variant = ?
        """,
        (user_id, card_id, variant),
    ).fetchone()
    quantity = int(aggregate["quantity"] or 0)
    if quantity <= 0:
        conn.execute("DELETE FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?", (user_id, card_id, variant))
        return None
    latest = conn.execute(
        """
        SELECT card_condition, notes
        FROM card_purchases
        WHERE user_id = ? AND card_id = ? AND variant = ?
        ORDER BY purchase_date DESC, id DESC
        LIMIT 1
        """,
        (user_id, card_id, variant),
    ).fetchone()
    existing = conn.execute(
        """
        SELECT share_id, graded, notes
        FROM collection
        WHERE user_id = ? AND card_id = ? AND variant = ?
        """,
        (user_id, card_id, variant),
    ).fetchone()
    share_id = (existing["share_id"] if existing and existing["share_id"] else new_share_id(conn))
    graded = int(aggregate["graded"] or 0)
    notes = (existing["notes"] if existing and existing["notes"] else (latest["notes"] if latest and "notes" in latest.keys() else "")) or ""
    average_paid = money(aggregate["total_paid"], fallback=0.01) / quantity
    conn.execute(
        """
        INSERT INTO collection (user_id, card_id, share_id, quantity, acquired_date, paid_price, variant, card_condition, graded, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
            share_id = COALESCE(collection.share_id, excluded.share_id),
            quantity = excluded.quantity,
            acquired_date = excluded.acquired_date,
            paid_price = excluded.paid_price,
            card_condition = excluded.card_condition,
            graded = excluded.graded,
            notes = excluded.notes,
            updated_at = excluded.updated_at
        """,
        (
            user_id,
            card_id,
            share_id,
            quantity,
            aggregate["first_purchase"] or today_iso(),
            average_paid,
            variant,
            card_condition(latest["card_condition"] if latest else DEFAULT_CARD_CONDITION),
            graded,
            notes or "",
            now_iso(),
        ),
    )
    conn.execute(
        "UPDATE card_meta SET wishlist = 0, updated_at = ? WHERE user_id = ? AND card_id = ? AND variant = ?",
        (now_iso(), user_id, card_id, variant),
    )
    conn.execute("DELETE FROM wishlist_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
    return conn.execute(
        "SELECT * FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?",
        (user_id, card_id, variant),
    ).fetchone()


def add_card_to_collection(conn, user_id, payload):
    card_id = payload.get("scryfall_id") or payload.get("card_id")
    if not card_id:
        raise ValueError("Choose a Scryfall card first.")

    url = SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id))
    synced_at = now_iso()
    scryfall_card = request_json(url)
    validate_selected_card(scryfall_card, payload)
    upsert_card(conn, scryfall_card, synced_at)
    if not payload.get("skip_set_cache"):
        cache_set_catalog(conn, scryfall_card.get("set"))

    purchase_rows = payload.get("purchases")
    if not isinstance(purchase_rows, list):
        purchase_rows = [{
            "variant": payload.get("variant") or "Normal",
            "quantity": payload.get("quantity") or 1,
            "paid_price": payload.get("paid_price") or 0.01,
            "acquired_date": payload.get("acquired_date") or today_iso(),
            "card_condition": payload.get("card_condition") or DEFAULT_CARD_CONDITION,
            "graded": payload.get("graded") or 0,
        }]

    global_store_name = payload.get("store_name") or ""
    global_store_location = payload.get("store_location") or ""
    global_notes = (payload.get("notes") or "").strip()
    if len(global_notes) > 1000:
        raise ValueError("Purchase notes must be 1,000 characters or fewer.")
    normalized_rows = []
    for row in purchase_rows:
        if not isinstance(row, dict):
            continue
        quantity = int(money(row.get("quantity"), fallback=0))
        if quantity <= 0:
            continue
        paid_price = money(row.get("paid_price"), fallback=0.01)
        if paid_price <= 0:
            raise ValueError("Price paid per card must be greater than $0.00.")
        purchase_date = row.get("acquired_date") or row.get("purchase_date") or today_iso()
        normalized_rows.append({
            "variant": row.get("variant") or "Normal",
            "quantity": quantity,
            "paid_price": paid_price,
            "purchase_date": purchase_date,
            "card_condition": card_condition(row.get("card_condition")),
            "graded": bool_int(row.get("graded")),
            "store_name": row.get("store_name") or global_store_name,
            "store_location": row.get("store_location") or global_store_location,
            "notes": (row.get("notes") or global_notes).strip(),
        })
    if not normalized_rows:
        raise ValueError("No quantity detected.")

    card = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    variants = []
    total_added = 0
    for row in normalized_rows:
        record_card_purchase(
            conn,
            user_id,
            card_id,
            row["variant"],
            row["quantity"],
            row["card_condition"],
            row["purchase_date"],
            row["quantity"] * row["paid_price"],
            row["store_name"],
            row["store_location"],
            row["graded"],
            row["notes"],
        )
        if row["variant"] not in variants:
            variants.append(row["variant"])
        total_added += row["quantity"]
    collection_rows = []
    for variant in variants:
        collection_row = rollup_collection_from_purchases(conn, user_id, card_id, variant)
        if collection_row:
            collection_rows.append(dict(collection_row))
    upsert_price_snapshot_from_card(conn, scryfall_card)
    conn.execute("DELETE FROM wishlist_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
    conn.commit()
    return {
        "ok": True,
        "card": dict(card),
        "quantity": sum(int(row.get("quantity") or 0) for row in collection_rows),
        "quantity_added": total_added,
        "variant": variants[0] if variants else "Normal",
        "variants": variants,
        "current_value": variant_price_from_row(card, variants[0] if variants else "Normal"),
    }


def lookup_maps(conn):
    rows = conn.execute("SELECT scryfall_id, name, set_name, set_code, collector_number FROM cards").fetchall()
    by_set_number = {}
    by_name_number = {}
    by_name = {}
    for row in rows:
        name_key = normalize(row["name"])
        number_keys = collector_keys(row["collector_number"])
        for set_key in set_aliases(row["set_code"], row["set_name"]):
            for number_key in number_keys:
                by_set_number[(set_key, number_key)] = row["scryfall_id"]
        for number_key in number_keys:
            by_name_number[(name_key, number_key)] = row["scryfall_id"]
        by_name.setdefault(name_key, row["scryfall_id"])
        by_name.setdefault(normalize(row["name"].split("//")[0]), row["scryfall_id"])
    return by_set_number, by_name_number, by_name


def import_csv(conn, csv_path, user_id=None):
    init_db(conn)
    path = Path(csv_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    existing_share_ids = {
        (row["card_id"], row["variant"]): row["share_id"]
        for row in conn.execute(
            "SELECT card_id, variant, share_id FROM collection WHERE user_id IS ? AND share_id IS NOT NULL AND share_id != ''",
            (user_id,),
        ).fetchall()
    }
    used_share_ids = {value for value in existing_share_ids.values() if value}
    by_set_number, by_name_number, by_name = lookup_maps(conn)
    imported = 0
    unmatched = []
    records = {}
    updated_at = now_iso()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for source in reader:
            quantity = int(money(source.get("Quantity"), fallback=0))
            if quantity <= 0:
                continue
            paid = money(source.get("Average Cost Paid"), fallback=0.01)
            if paid <= 0:
                paid = 0.01
            set_name = source.get("Set") or ""
            product_name = source.get("Product Name") or ""
            card_number = source.get("Card Number") or ""
            card_id = None
            for candidate_set in lookup_set_candidates(set_name, product_name):
                for number_key in collector_keys(card_number):
                    card_id = by_set_number.get((normalize(candidate_set), number_key))
                    if card_id:
                        break
                if card_id:
                    break
            if not card_id:
                for candidate in product_name_candidates(product_name):
                    for number_key in collector_keys(card_number):
                        card_id = by_name_number.get((normalize(candidate), number_key))
                        if card_id:
                            break
                    if card_id:
                        break
            if not card_id:
                for candidate in product_name_candidates(product_name):
                    card_id = by_name.get(normalize(candidate))
                    if card_id:
                        break
            if not card_id:
                unmatched.append({
                    "name": product_name,
                    "set": set_name,
                    "number": card_number,
                    "quantity": quantity,
                })
                continue
            variant = import_variant(source)
            key = (card_id, variant)
            if key not in records:
                records[key] = {
                    "card_id": card_id,
                    "variant": variant,
                    "quantity": 0,
                    "paid_total": 0.0,
                    "acquired_date": source.get("Date Added") or today_iso(),
                    "card_condition": card_condition(source.get("Card Condition")),
                    "graded": bool_int(source.get("Graded")),
                    "notes": [],
                }
            record = records[key]
            record["quantity"] += quantity
            record["paid_total"] += quantity * paid
            acquired_date = source.get("Date Added") or today_iso()
            if acquired_date and (not record["acquired_date"] or acquired_date < record["acquired_date"]):
                record["acquired_date"] = acquired_date
            if source.get("Card Condition"):
                record["card_condition"] = card_condition(source.get("Card Condition"))
            if source.get("Graded"):
                record["graded"] = bool_int(source.get("Graded"))
            if source.get("Notes"):
                record["notes"].append(source.get("Notes"))
            imported += 1
    conn.execute("DELETE FROM collection WHERE user_id IS ?", (user_id,))
    for record in records.values():
        paid_price = record["paid_total"] / record["quantity"] if record["quantity"] else 0.01
        share_id = existing_share_ids.get((record["card_id"], record["variant"]))
        if not share_id:
            share_id = new_share_id(conn)
            while share_id in used_share_ids:
                share_id = new_share_id(conn)
        used_share_ids.add(share_id)
        conn.execute(
            """
            INSERT INTO collection (user_id, card_id, share_id, quantity, acquired_date, paid_price, variant, card_condition, graded, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
                share_id = COALESCE(collection.share_id, excluded.share_id),
                quantity = excluded.quantity,
                acquired_date = excluded.acquired_date,
                paid_price = excluded.paid_price,
                card_condition = excluded.card_condition,
                graded = excluded.graded,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                record["card_id"],
                share_id,
                record["quantity"],
                record["acquired_date"],
                paid_price,
                record["variant"],
                record["card_condition"],
                record["graded"],
                "; ".join(record["notes"]),
                updated_at,
            ),
        )
        conn.execute(
            "UPDATE card_meta SET wishlist = 0, updated_at = ? WHERE user_id IS ? AND card_id = ? AND variant = ?",
            (updated_at, user_id, record["card_id"], record["variant"]),
        )
        conn.execute("DELETE FROM wishlist_cards WHERE user_id IS ? AND card_id = ?", (user_id, record["card_id"]))
    conn.commit()
    return {"imported_rows": imported, "unmatched_rows": unmatched}


def source_value(source, *names):
    lowered = {str(key).strip().lower(): value for key, value in source.items()}
    for name in names:
      value = lowered.get(name.lower())
      if value is not None and str(value).strip() != "":
          return str(value).strip()
    return ""


def import_row_from_source(source, line_number, source_format):
    name = source_value(source, "name", "Name", "Product Name", "card_name")
    set_name = source_value(source, "set_name", "Set", "Set Name", "set")
    set_code = source_value(source, "set_code", "Set Code", "Edition")
    collector_number = source_value(source, "collector_number", "Card Number", "Collector Number", "number")
    quantity = int(money(source_value(source, "quantity", "Quantity", "Count"), fallback=0))
    if quantity <= 0:
        quantity = 1 if name else 0
    paid_price = money(source_value(source, "paid_price", "Price Paid", "Average Cost Paid", "Purchase Price"), fallback=0.01)
    if paid_price <= 0:
        paid_price = 0.01
    entry = {
        "line": line_number,
        "format": source_format,
        "scryfall_id": source_value(source, "scryfall_id", "Scryfall ID", "card_id"),
        "name": name,
        "set_name": set_name,
        "set_code": set_code,
        "collector_number": collector_number,
        "quantity": quantity,
        "paid_price": paid_price,
        "acquired_date": source_value(source, "acquired_date", "Date Acquired", "Date Added") or today_iso(),
        "variant": import_variant(source),
        "card_condition": card_condition(source_value(source, "card_condition", "Condition", "Card Condition")),
        "graded": bool_int(source_value(source, "graded", "Graded")),
        "notes": source_value(source, "notes", "Notes"),
    }
    if not entry["name"]:
        entry["error"] = "Missing card name."
    elif entry["quantity"] <= 0:
        entry["error"] = "Quantity is missing or invalid."
    return entry


def import_card_summary_from_row(row):
    if not row:
        return None
    card = with_value_aliases(dict(row))
    return {
        "scryfall_id": card.get("scryfall_id"),
        "name": card.get("name"),
        "display_name": card.get("flavor_name") or card.get("name"),
        "set_code": card.get("set_code"),
        "set_name": card.get("set_name"),
        "collector_number": card.get("collector_number"),
        "rarity": card.get("rarity"),
        "type_line": card.get("type_line"),
        "type_category": card.get("type_category"),
        "colors": card.get("colors"),
        "color_identity": card.get("color_identity"),
        "image_small": card.get("image_small"),
        "image_normal": card.get("image_normal"),
        "scryfall_uri": card.get("scryfall_uri"),
    }


def local_import_match(conn, entry, lookup_data=None):
    if entry.get("error"):
        return None
    if entry.get("scryfall_id"):
        row = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (entry["scryfall_id"],)).fetchone()
        if row:
            return {"source": "local", "confidence": "exact id", "card": import_card_summary_from_row(row)}
    by_set_number, by_name_number, by_name = lookup_data or lookup_maps(conn)
    card_id = None
    for candidate_set in lookup_set_candidates(entry.get("set_code") or entry.get("set_name"), entry.get("name")):
        for number_key in collector_keys(entry.get("collector_number")):
            card_id = by_set_number.get((normalize(candidate_set), number_key))
            if card_id:
                break
        if card_id:
            break
    if not card_id:
        for candidate in product_name_candidates(entry.get("name")):
            for number_key in collector_keys(entry.get("collector_number")):
                card_id = by_name_number.get((normalize(candidate), number_key))
                if card_id:
                    break
            if card_id:
                break
    if not card_id:
        for candidate in product_name_candidates(entry.get("name")):
            card_id = by_name.get(normalize(candidate))
            if card_id:
                break
    if not card_id:
        return None
    row = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    return {"source": "local", "confidence": "best guess", "card": import_card_summary_from_row(row)}


def scryfall_import_match(entry):
    if entry.get("scryfall_id"):
        card = request_json(SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(entry["scryfall_id"])))
        return {"source": "scryfall", "confidence": "exact id", "card": card_summary(card)}
    name = entry.get("name") or ""
    number = entry.get("collector_number") or ""
    set_code = (entry.get("set_code") or "").strip().lower()
    set_filter = f" e:{set_code}" if set_code else ""
    queries = []
    if name and number:
        queries.append(f'!"{name}" cn:{number}{set_filter} game:paper')
        queries.append(f'{name} cn:{number}{set_filter} game:paper')
    if name:
        queries.append(f'!"{name}"{set_filter} game:paper')
        queries.append(f'{name}{set_filter} game:paper')
    for query in queries:
        payload = request_json(f"{SCRYFALL_SEARCH_URL}?{urllib.parse.urlencode({'q': scryfall_query_with_language(query), 'unique': 'prints', 'order': 'set'})}")
        cards = payload.get("data") or []
        if cards:
            card = cards[0]
            return {"source": "scryfall", "confidence": "best guess", "card": card_summary(card)}
    return None


def import_match_cache_key(entry):
    if entry.get("scryfall_id"):
        return ("id", str(entry.get("scryfall_id")).strip())
    return (
        "query",
        normalize(entry.get("name")),
        normalize(entry.get("set_code") or entry.get("set_name")),
        normalize(entry.get("collector_number")),
    )


def preview_import_entries(conn, entries):
    preview = []
    issues = []
    lookup_data = lookup_maps(conn)
    scryfall_cache = {}
    scryfall_lookup_count = 0
    for index, source_entry in enumerate(entries, start=1):
        entry = dict(source_entry or {})
        if not entry.get("line"):
            entry["line"] = index
        row_id = f"row-{entry['line']}"
        if entry.get("error"):
            issues.append({"line": entry["line"], "name": entry.get("name"), "error": entry["error"]})
            preview.append({"id": row_id, "checked": False, "entry": entry, "match": None, "status": "bad"})
            continue
        match = local_import_match(conn, entry, lookup_data)
        if not match:
            cache_key = import_match_cache_key(entry)
            if cache_key in scryfall_cache:
                match = scryfall_cache[cache_key]
            elif SCRYFALL_IMPORT_LOOKUP_LIMIT and scryfall_lookup_count >= SCRYFALL_IMPORT_LOOKUP_LIMIT:
                issues.append({
                    "line": entry["line"],
                    "name": entry.get("name"),
                    "error": f"Scryfall auto-match skipped after {SCRYFALL_IMPORT_LOOKUP_LIMIT} unique lookup(s). Use manual match for this row or raise SCRYFALL_IMPORT_LOOKUP_LIMIT.",
                })
            else:
                try:
                    if scryfall_lookup_count and SCRYFALL_IMPORT_LOOKUP_DELAY:
                        time.sleep(SCRYFALL_IMPORT_LOOKUP_DELAY)
                    scryfall_lookup_count += 1
                    match = scryfall_import_match(entry)
                    scryfall_cache[cache_key] = match
                except urllib.error.HTTPError as exc:
                    if exc.code == 429:
                        issues.append({"line": entry["line"], "name": entry.get("name"), "error": "Scryfall rate limit reached. Wait a minute, then manually match or retry the preview."})
                    else:
                        issues.append({"line": entry["line"], "name": entry.get("name"), "error": f"Scryfall lookup failed: HTTP {exc.code}"})
                    scryfall_cache[cache_key] = None
                except Exception as exc:
                    issues.append({"line": entry["line"], "name": entry.get("name"), "error": f"Scryfall lookup failed: {exc}"})
                    scryfall_cache[cache_key] = None
        if not match:
            issues.append({"line": entry["line"], "name": entry.get("name"), "error": "No match found."})
        preview.append({
            "id": row_id,
            "checked": bool(match),
            "entry": entry,
            "match": match,
            "status": "matched" if match else "unmatched",
        })
    if scryfall_lookup_count:
        LOGGER.info("Import preview used %s Scryfall lookup(s) for %s row(s)", scryfall_lookup_count, len(entries))
    return {"rows": preview, "issues": issues}


def preview_import_rows(conn, rows, source_format):
    entries = [import_row_from_source(source, index, source_format) for index, source in enumerate(rows, start=1)]
    return preview_import_entries(conn, entries)


def parse_csv_import_text(text):
    if not text or not text.strip():
        raise ValueError("CSV file is empty.")
    try:
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("CSV is missing a header row.")
        rows = list(reader)
    except csv.Error as exc:
        raise ValueError(f"Invalid CSV: {exc}")
    if any(None in row for row in rows):
        raise ValueError("Invalid CSV: rows have more values than headers. Quote fields that contain commas.")
    if not rows:
        raise ValueError("CSV has no rows to import.")
    return rows


def parse_json_import_text(text):
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}")
    if isinstance(payload, dict) and isinstance(payload.get("cards"), list):
        payload = payload["cards"]
    if not isinstance(payload, list):
        raise ValueError("JSON import only accepts an Arcane Ledger export array.")
    return payload


IMPORT_FIELD_DEFINITIONS = [
    {"key": "name", "label": "Card title", "required": True, "aliases": ["name", "card name", "product name", "title"]},
    {"key": "set_name", "label": "Set name", "required": False, "aliases": ["set", "set name", "expansion"]},
    {"key": "set_code", "label": "Set code", "required": False, "aliases": ["set code", "set_code", "edition code"]},
    {"key": "collector_number", "label": "Collector number", "required": False, "aliases": ["collector number", "card number", "number", "cn"]},
    {"key": "quantity", "label": "Quantity", "required": False, "aliases": ["quantity", "qty", "count", "owned"]},
    {"key": "paid_price", "label": "Price paid each", "required": False, "aliases": ["price paid", "paid price", "average cost paid", "cost", "price"]},
    {"key": "acquired_date", "label": "Date acquired", "required": False, "aliases": ["date acquired", "date added", "acquired date", "added"]},
    {"key": "variant", "label": "Variant", "required": False, "aliases": ["variant", "finish", "foil", "printing"]},
    {"key": "card_condition", "label": "Condition", "required": False, "aliases": ["condition", "card condition"]},
    {"key": "graded", "label": "Graded", "required": False, "aliases": ["graded", "is graded"]},
    {"key": "notes", "label": "Notes", "required": False, "aliases": ["notes", "note"]},
    {"key": "scryfall_id", "label": "Scryfall ID", "required": False, "aliases": ["scryfall id", "scryfall_id", "card_id", "id"]},
]

MOXFIELD_CSV_HEADERS = [
    "Count",
    "Name",
    "Edition",
    "Condition",
    "Language",
    "Foil",
    "Collector Number",
    "Alter",
    "Playtest Card",
    "Purchase Price",
]

MOXFIELD_IMPORT_MAPPING = {
    "name": "Name",
    "set_name": "",
    "set_code": "Edition",
    "collector_number": "Collector Number",
    "quantity": "Count",
    "paid_price": "Purchase Price",
    "acquired_date": "",
    "variant": "Foil",
    "card_condition": "Condition",
    "graded": "",
    "notes": "",
    "scryfall_id": "",
}


def is_moxfield_like_import(source_format):
    return (source_format or "").lower() in {"moxfield", "arena"}


def csv_import_headers(text, source_format=None):
    rows = parse_csv_import_text(text)
    reader = csv.DictReader(io.StringIO(text))
    headers = [header for header in (reader.fieldnames or []) if header]
    mapping = dict(MOXFIELD_IMPORT_MAPPING) if is_moxfield_like_import(source_format) else suggest_csv_import_mapping(headers)
    return {"headers": headers, "row_count": len(rows), "mapping": mapping, "fields": IMPORT_FIELD_DEFINITIONS}


def suggest_csv_import_mapping(headers):
    normalized_headers = {normalize(header): header for header in headers}
    mapping = {}
    for field in IMPORT_FIELD_DEFINITIONS:
        selected = ""
        for alias in field["aliases"]:
            if normalize(alias) in normalized_headers:
                selected = normalized_headers[normalize(alias)]
                break
        if not selected:
            for header in headers:
                header_key = normalize(header)
                if any(normalize(alias) in header_key or header_key in normalize(alias) for alias in field["aliases"]):
                    selected = header
                    break
        mapping[field["key"]] = selected
    return mapping


def apply_csv_import_mapping(rows, mapping):
    mapped = []
    mapping = mapping or {}
    for row in rows:
        source = {}
        for field in IMPORT_FIELD_DEFINITIONS:
            header = mapping.get(field["key"]) or ""
            source[field["key"]] = row.get(header, "") if header else ""
        mapped.append(source)
    return mapped


def aggregate_import_preview_rows(preview_rows):
    aggregated = {}
    output = []
    for row in preview_rows:
        match_card = ((row.get("match") or {}).get("card") or {})
        entry = row.get("entry") or {}
        card_id = match_card.get("scryfall_id")
        if not card_id:
            output.append(row)
            continue
        variant = entry.get("variant") or "Normal"
        condition = card_condition(entry.get("card_condition"))
        key = (card_id, variant, condition)
        if key not in aggregated:
            clone = json.loads(json.dumps(row))
            clone["source_rows"] = [entry]
            clone["entry"]["quantity"] = int(entry.get("quantity") or 0)
            clone["entry"]["paid_total"] = money(entry.get("paid_price"), fallback=0.01) * int(entry.get("quantity") or 0)
            clone["entry"]["line"] = str(entry.get("line") or "")
            aggregated[key] = clone
            output.append(clone)
        else:
            target = aggregated[key]
            quantity = int(entry.get("quantity") or 0)
            target["source_rows"].append(entry)
            target["entry"]["quantity"] = int(target["entry"].get("quantity") or 0) + quantity
            target["entry"]["paid_total"] = money(target["entry"].get("paid_total"), fallback=0) + (money(entry.get("paid_price"), fallback=0.01) * quantity)
            if target["entry"]["quantity"] > 0:
                target["entry"]["paid_price"] = round(target["entry"]["paid_total"] / target["entry"]["quantity"], 4)
            lines = [str(item.get("line")) for item in target["source_rows"] if item.get("line")]
            target["entry"]["line"] = ", ".join(lines)
    for index, row in enumerate(output, start=1):
        row["id"] = f"group-{index}"
    return output


def import_csv_mapped_preview(conn, payload):
    text = payload.get("text") or ""
    mapping = payload.get("mapping") or {}
    rows = parse_csv_import_text(text)
    mapped = apply_csv_import_mapping(rows, mapping)
    preview = preview_import_rows(conn, mapped, "csv")
    preview["rows"] = aggregate_import_preview_rows(preview["rows"])
    return preview


def import_csv_mapped_entries(payload):
    text = payload.get("text") or ""
    mapping = payload.get("mapping") or {}
    rows = parse_csv_import_text(text)
    mapped = apply_csv_import_mapping(rows, mapping)
    entries = [import_row_from_source(source, index, "csv") for index, source in enumerate(mapped, start=1)]
    invalid = [
        {"line": entry["line"], "name": entry.get("name"), "error": entry["error"]}
        for entry in entries
        if entry.get("error")
    ]
    return {"entries": entries, "issues": invalid, "row_count": len(entries)}


def import_entries_match_preview(conn, payload):
    entries = payload.get("entries") or []
    if not isinstance(entries, list):
        raise ValueError("Import entries are required.")
    return preview_import_entries(conn, entries)


def looks_like_card_import_row(item):
    if not isinstance(item, dict):
        return False
    keys = {str(key).lower() for key in item.keys()}
    return bool(keys & {"scryfall_id", "card_id", "name", "card_name", "quantity", "collector_number", "set_name", "set_code"})


def looks_like_deck_import(item):
    return isinstance(item, dict) and isinstance(item.get("cards"), list) and bool(item.get("name") or item.get("deck_name"))


def looks_like_wishlist_import(item):
    return isinstance(item, dict) and isinstance(item.get("cards") or item.get("items"), list) and bool(item.get("name") or item.get("wishlist_name"))


def classify_json_import_payload(payload):
    if isinstance(payload, dict):
        payload_format = str(payload.get("format") or payload.get("type") or "").lower()
        if "wishlist" in payload_format or isinstance(payload.get("wishlists"), list) or isinstance(payload.get("wishlist"), dict):
            return "wishlists"
        if isinstance(payload.get("decks"), list) or looks_like_deck_import(payload.get("deck")) or looks_like_deck_import(payload):
            return "decks"
        if isinstance(payload.get("collection"), list) or isinstance(payload.get("cards"), list):
            if isinstance(payload.get("decks"), list) or isinstance(payload.get("wishlists"), list):
                return "full"
            return "cards"
    if isinstance(payload, list):
        if payload and all(looks_like_wishlist_import(item) for item in payload if isinstance(item, dict)):
            return "wishlists"
        if payload and all(looks_like_deck_import(item) for item in payload if isinstance(item, dict)):
            return "decks"
        if payload and all(looks_like_card_import_row(item) for item in payload if isinstance(item, dict)):
            return "cards"
    return "unknown"


def json_import_source_for_kind(payload, kind):
    if kind == "cards":
        if isinstance(payload, dict):
            return payload.get("collection") or payload.get("cards") or []
        return payload
    if kind == "decks":
        if isinstance(payload, dict) and isinstance(payload.get("decks"), list):
            return {"decks": payload.get("decks")}
        if isinstance(payload, dict) and isinstance(payload.get("deck"), dict):
            return {"decks": [payload.get("deck")]}
        return {"decks": payload if isinstance(payload, list) else [payload]}
    if kind == "full":
        return {
            "cards": payload.get("collection") or payload.get("cards") or [],
            "decks": payload.get("decks") or [],
            "wishlists": payload.get("wishlists") or [],
        }
    if kind == "wishlists":
        if isinstance(payload, dict) and isinstance(payload.get("wishlists"), list):
            return {"wishlists": payload.get("wishlists")}
        if isinstance(payload, dict) and isinstance(payload.get("wishlist"), dict):
            return {"wishlists": [payload.get("wishlist")]}
    return payload


def import_json_wizard_preview(conn, user_id, payload):
    text = payload.get("text") or ""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}")
    kind = classify_json_import_payload(parsed)
    if kind == "cards":
        source = json_import_source_for_kind(parsed, kind)
        preview = preview_import_rows(conn, source, "json")
        preview["rows"] = aggregate_import_preview_rows(preview["rows"])
        return {"ok": True, "kind": "cards", "label": f"{len(preview['rows'])} collection card group(s) found", "cards": preview, "can_commit": True}
    if kind == "decks":
        source = json_import_source_for_kind(parsed, kind)
        preview = preview_deck_import(conn, user_id, source)
        return {"ok": True, "kind": "decks", "label": f"{len(preview['decks'])} deck(s) found", "decks": preview, "can_commit": not any(deck.get("needs_rename") for deck in preview.get("decks", []))}
    if kind == "full":
        source = json_import_source_for_kind(parsed, kind)
        card_preview = preview_import_rows(conn, source.get("cards") or [], "json") if source.get("cards") else {"rows": [], "issues": []}
        card_preview["rows"] = aggregate_import_preview_rows(card_preview["rows"])
        deck_preview = preview_deck_import(conn, user_id, {"decks": source.get("decks") or []}) if source.get("decks") else {"decks": [], "normalized_decks": []}
        wishlist_preview = preview_wishlist_import(conn, user_id, {"wishlists": source.get("wishlists") or []}) if source.get("wishlists") else {"wishlists": [], "normalized_wishlists": []}
        return {
            "ok": True,
            "kind": "full",
            "label": f"Full data bundle: {len(card_preview['rows'])} card group(s), {len(deck_preview.get('decks', []))} deck(s), {len(wishlist_preview.get('wishlists', []))} wishlist(s)",
            "cards": card_preview,
            "decks": deck_preview,
            "wishlists": wishlist_preview,
            "can_commit": not any(deck.get("needs_rename") for deck in deck_preview.get("decks", [])) and not any(wishlist.get("needs_rename") for wishlist in wishlist_preview.get("wishlists", [])),
        }
    if kind == "wishlists":
        source = json_import_source_for_kind(parsed, kind)
        preview = preview_wishlist_import(conn, user_id, source)
        return {"ok": True, "kind": "wishlists", "label": f"{len(preview['wishlists'])} wishlist(s) found", "wishlists": preview, "can_commit": not any(wishlist.get("needs_rename") for wishlist in preview.get("wishlists", []))}
    return {"ok": True, "kind": "unknown", "label": "Unknown JSON import", "can_commit": False, "issues": ["Arcane Ledger could not determine whether this JSON contains cards, decks, wishlists, or a full export."]}


def commit_import_wizard_json(conn, user_id, payload):
    kind = payload.get("kind")
    imported = {"cards": 0, "decks": 0, "wishlists": 0}
    skipped = []
    if kind in {"cards", "full"}:
        result = commit_import_rows(conn, user_id, {"rows": payload.get("rows") or []})
        imported["cards"] = result.get("imported_rows", 0)
        skipped.extend(result.get("skipped_rows") or [])
    if kind in {"decks", "full"}:
        deck_payload = {"decks": payload.get("decks") or []}
        if deck_payload["decks"]:
            result = commit_deck_import(conn, user_id, deck_payload)
            imported["decks"] = result.get("imported", 0)
    if kind in {"wishlists", "full"}:
        wishlist_payload = {"wishlists": payload.get("wishlists") or []}
        if wishlist_payload["wishlists"]:
            result = commit_wishlist_import(conn, user_id, wishlist_payload)
            imported["wishlists"] = result.get("imported", 0)
            skipped.extend(result.get("skipped_rows") or [])
    return {"ok": True, "imported": imported, "skipped_rows": skipped}


def import_preview(conn, payload):
    source_format = (payload.get("format") or "").lower()
    text = payload.get("text") or ""
    if source_format == "csv":
        return preview_import_rows(conn, parse_csv_import_text(text), "csv")
    if source_format == "json":
        return preview_import_rows(conn, parse_json_import_text(text), "json")
    raise ValueError("Choose CSV or JSON import.")


def commit_import_rows(conn, user_id, payload):
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError("Import rows are required.")
    imported = 0
    skipped = []
    touched_sets = set()
    for item in rows:
        if not item.get("checked"):
            continue
        entry = item.get("entry") or {}
        card_id = item.get("card_id") or ((item.get("match") or {}).get("card") or {}).get("scryfall_id")
        if not card_id:
            skipped.append({"line": entry.get("line"), "name": entry.get("name"), "error": "No Scryfall card selected."})
            continue
        result = add_card_to_collection(conn, user_id, {
            "scryfall_id": card_id,
            "quantity": entry.get("quantity") or 1,
            "paid_price": entry.get("paid_price") or 0.01,
            "acquired_date": entry.get("acquired_date") or today_iso(),
            "variant": entry.get("variant") or "Normal",
            "card_condition": entry.get("card_condition") or DEFAULT_CARD_CONDITION,
            "graded": entry.get("graded") or 0,
            "skip_set_cache": True,
        })
        if result.get("card", {}).get("set_code"):
            touched_sets.add(result["card"]["set_code"])
        imported += 1
    for set_code in sorted(touched_sets):
        cache_set_catalog(conn, set_code)
    return {"ok": True, "imported_rows": imported, "skipped_rows": skipped}


CONTAINER_ALLOCATION_IMPORT_FIELDS = [
    {"key": "card_id", "label": "Card ID", "aliases": ["card_id", "scryfall_id", "scryfall id", "id"]},
    {"key": "variant", "label": "Variant", "aliases": ["variant", "finish", "printing"]},
    {"key": "card_condition", "label": "Condition", "aliases": ["condition", "card_condition", "card condition"]},
    {"key": "quantity", "label": "Quantity", "aliases": ["quantity", "qty", "count", "quantity to allocate"]},
    {"key": "container_id", "label": "Container ID", "aliases": ["container_id", "container id", "container", "box id", "binder id"]},
]


def parse_container_allocation_import_text(text, source_format=None):
    text = (text or "").strip()
    if not text:
        raise ValueError("Container allocation import is empty.")
    fmt = (source_format or "").strip().lower()
    if fmt == "auto":
        fmt = ""
    if not fmt:
        fmt = "json" if text[:1] in "[{" else "csv"
    if fmt == "csv":
        return parse_csv_import_text(text), "csv"
    if fmt == "json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}")
        if isinstance(payload, dict):
            rows = payload.get("allocations") or payload.get("rows") or payload.get("container_allocations")
        else:
            rows = payload
        if not isinstance(rows, list):
            raise ValueError("JSON container allocation import must be an array or contain an allocations array.")
        if not rows:
            raise ValueError("JSON container allocation import has no rows.")
        if not all(isinstance(row, dict) for row in rows):
            raise ValueError("Each container allocation row must be an object.")
        return rows, "json"
    raise ValueError("Choose CSV or JSON for container allocation import.")


def container_allocation_entry_from_source(source, line_number):
    card_id = source_value(source, "card_id", "scryfall_id", "Scryfall ID", "Card ID", "id")
    variant = source_value(source, "variant", "Variant", "finish", "Finish") or "Normal"
    condition = card_condition(source_value(source, "card_condition", "Condition", "Card Condition"))
    quantity = int(money(source_value(source, "quantity", "Quantity", "qty", "Quantity to Allocate"), fallback=0))
    container_id = int(money(source_value(source, "container_id", "Container ID", "container", "Container"), fallback=0))
    return {
        "line": line_number,
        "card_id": (card_id or "").strip(),
        "variant": (variant or "Normal").strip() or "Normal",
        "card_condition": condition,
        "quantity": quantity,
        "container_id": container_id,
    }


def normalize_container_allocation_import_rows(rows):
    entries = []
    for index, source in enumerate(rows or [], start=1):
        if not isinstance(source, dict):
            continue
        entry = container_allocation_entry_from_source(source, source.get("line") or index)
        if source.get("checked") is not None:
            entry["checked"] = bool(source.get("checked"))
        entries.append(entry)
    return entries


def container_allocation_card_summary(row):
    if not row:
        return None
    return {
        "scryfall_id": row["scryfall_id"],
        "name": row["name"],
        "display_name": row["flavor_name"] or row["name"],
        "set_code": row["set_code"],
        "set_name": row["set_name"],
        "collector_number": row["collector_number"],
        "image_small": row["image_small"],
        "image_normal": row["image_normal"],
    }


def validate_container_allocation_entries(conn, user_id, entries):
    container_rows = conn.execute(
        """
        SELECT ct.id, ct.name, COALESCE(ct.storage_type, 'other') AS storage_type,
               COALESCE(ct.strict_unique, 0) AS strict_unique,
               COALESCE(ct.capacity, 0) AS capacity,
               COALESCE(SUM(cc.quantity), 0) AS stored_quantity
        FROM containers ct
        LEFT JOIN container_cards cc ON cc.container_id = ct.id
        WHERE ct.user_id = ?
        GROUP BY ct.id
        """,
        (user_id,),
    ).fetchall()
    containers = {int(row["id"]): dict(row) for row in container_rows}
    requested_by_bucket = {}
    requested_by_container = {}
    requested_by_strict_slot = {}
    preview_rows = []
    valid_count = 0
    valid_quantity = 0

    for index, entry in enumerate(entries or [], start=1):
        entry = dict(entry or {})
        errors = []
        warnings = []
        card_id = (entry.get("card_id") or "").strip()
        variant = (entry.get("variant") or "Normal").strip() or "Normal"
        condition = card_condition(entry.get("card_condition"))
        quantity = int(entry.get("quantity") or 0)
        container_id = int(entry.get("container_id") or 0)
        card = None
        container = containers.get(container_id)
        owned = 0
        allocated = 0
        available_before = 0
        available_after = 0
        remaining_before = None
        remaining_after = None

        if not card_id:
            errors.append("Card ID is required.")
        else:
            card = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
            if not card:
                errors.append("Card ID was not found in the local catalog.")
        if quantity <= 0:
            errors.append("Quantity must be at least 1.")
        if not container_id:
            errors.append("Container ID is required.")
        elif not container:
            errors.append("Container ID was not found for your account.")

        if card and quantity > 0:
            owned = condition_owned_quantity(conn, user_id, card_id, variant, condition)
            allocated = allocated_quantity(conn, user_id, card_id, variant, condition)
            available_before = max(0, owned - allocated)
            bucket = (card_id, variant, condition)
            already_requested = requested_by_bucket.get(bucket, 0)
            available_for_row = max(0, available_before - already_requested)
            available_after = max(0, available_for_row - quantity)
            if owned <= 0:
                errors.append("You do not own that card with this variant and condition.")
            elif quantity > available_for_row:
                errors.append(f"Only {available_for_row} uncontainered copy/copies are available.")

        if container and quantity > 0:
            capacity = int(container.get("capacity") or 0)
            stored = int(container.get("stored_quantity") or 0)
            if capacity > 0:
                already_requested_container = requested_by_container.get(container_id, 0)
                remaining_before = max(0, capacity - stored - already_requested_container)
                remaining_after = max(0, remaining_before - quantity)
                if quantity > remaining_before:
                    errors.append(f"{container['name']} only has space for {remaining_before} more card/copy.")
            else:
                warnings.append("Container capacity is not set, so space was not limited.")
            if card and int(container.get("strict_unique") or 0):
                existing_strict_quantity, strict_card = container_strict_existing_quantity(conn, container_id, card_id)
                strict_key = (container_id, strict_card["set_code"] if strict_card else "", strict_card["collector_number"] if strict_card else "")
                already_requested_strict = requested_by_strict_slot.get(strict_key, 0)
                strict_remaining = max(0, 1 - existing_strict_quantity - already_requested_strict)
                if quantity > strict_remaining:
                    errors.append(
                        f"{container['name']} has Strict enabled. Only {strict_remaining} more card/copy is allowed for {container_strict_slot_label(strict_card)}."
                    )

        checked = bool(entry.get("checked", True)) and not errors
        if checked:
            requested_by_bucket[(card_id, variant, condition)] = requested_by_bucket.get((card_id, variant, condition), 0) + quantity
            requested_by_container[container_id] = requested_by_container.get(container_id, 0) + quantity
            if container and int(container.get("strict_unique") or 0) and card:
                strict_quantity_row = conn.execute(
                    "SELECT set_code, collector_number FROM cards WHERE scryfall_id = ?",
                    (card_id,),
                ).fetchone()
                strict_key = (container_id, strict_quantity_row["set_code"], strict_quantity_row["collector_number"])
                requested_by_strict_slot[strict_key] = requested_by_strict_slot.get(strict_key, 0) + quantity
            valid_count += 1
            valid_quantity += quantity

        preview_rows.append({
            "id": f"container-import-{index}",
            "line": entry.get("line") or index,
            "checked": checked,
            "status": "valid" if not errors else "blocked",
            "errors": errors,
            "warnings": warnings,
            "card_id": card_id,
            "variant": variant,
            "card_condition": condition,
            "quantity": quantity,
            "container_id": container_id,
            "card": container_allocation_card_summary(card),
            "container": {
                "id": container_id,
                "name": container["name"],
                "storage_type": container["storage_type"],
                "strict_unique": bool(container["strict_unique"]),
                "capacity": int(container["capacity"] or 0),
                "stored_quantity": int(container["stored_quantity"] or 0),
            } if container else None,
            "owned_quantity": owned,
            "allocated_quantity": allocated,
            "available_before": available_before,
            "available_after": available_after,
            "container_remaining_before": remaining_before,
            "container_remaining_after": remaining_after,
        })

    return {
        "ok": True,
        "rows": preview_rows,
        "summary": {
            "total_rows": len(preview_rows),
            "valid_rows": valid_count,
            "blocked_rows": len(preview_rows) - valid_count,
            "valid_quantity": valid_quantity,
        },
    }


def preview_container_allocation_import(conn, user_id, payload):
    rows, source_format = parse_container_allocation_import_text(payload.get("text") or "", payload.get("format"))
    entries = normalize_container_allocation_import_rows(rows)
    preview = validate_container_allocation_entries(conn, user_id, entries)
    preview["format"] = source_format
    preview["fields"] = CONTAINER_ALLOCATION_IMPORT_FIELDS
    return preview


def commit_container_allocation_import(conn, user_id, payload):
    source_rows = payload.get("rows") or []
    if not isinstance(source_rows, list):
        raise ValueError("Container allocation rows are required.")
    requested = [row for row in source_rows if row.get("checked")]
    if not requested:
        raise ValueError("Choose at least one valid row to import.")
    entries = normalize_container_allocation_import_rows(requested)
    preview = validate_container_allocation_entries(conn, user_id, entries)
    blocked = [row for row in preview["rows"] if row.get("errors")]
    if blocked:
        raise ValueError("Fix invalid container allocation rows before confirming.")
    timestamp = now_iso()
    touched_containers = set()
    total_quantity = 0
    for row in preview["rows"]:
        quantity = int(row.get("quantity") or 0)
        if quantity <= 0:
            continue
        conn.execute(
            """
            INSERT INTO container_cards (container_id, card_id, variant, card_condition, quantity, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(container_id, card_id, variant, card_condition) DO UPDATE SET
                quantity = container_cards.quantity + excluded.quantity,
                updated_at = excluded.updated_at
            """,
            (
                int(row["container_id"]),
                row["card_id"],
                row["variant"] or "Normal",
                card_condition(row["card_condition"]),
                quantity,
                timestamp,
            ),
        )
        touched_containers.add(int(row["container_id"]))
        total_quantity += quantity
    if touched_containers:
        placeholders = ", ".join("?" for _ in touched_containers)
        conn.execute(
            f"UPDATE containers SET updated_at = ? WHERE user_id = ? AND id IN ({placeholders})",
            (timestamp, user_id, *sorted(touched_containers)),
        )
    conn.commit()
    return {
        "ok": True,
        "imported_rows": len(preview["rows"]),
        "allocated_quantity": total_quantity,
        "containers": list_containers(conn, user_id),
    }


def current_price_sql(alias="c"):
    return (
        f"CASE "
        f"WHEN lower(coalesce(col.variant, '')) LIKE '%etched%' AND {alias}.current_usd_etched > 0 THEN {alias}.current_usd_etched "
        f"WHEN lower(coalesce(col.variant, '')) LIKE '%foil%' AND {alias}.current_usd_foil > 0 THEN {alias}.current_usd_foil "
        f"WHEN {alias}.current_usd > 0 THEN {alias}.current_usd "
        f"WHEN {alias}.current_usd_foil > 0 THEN {alias}.current_usd_foil "
        f"WHEN {alias}.current_usd_etched > 0 THEN {alias}.current_usd_etched "
        f"ELSE 0 END"
    )


def collection_value_history(conn, user_id, months=24):
    first_acquired = conn.execute(
        "SELECT MIN(acquired_date) AS first_acquired FROM collection WHERE user_id = ? AND quantity > 0 AND acquired_date IS NOT NULL AND acquired_date != ''",
        (user_id,),
    ).fetchone()["first_acquired"]
    first_date = parse_iso_date(first_acquired)
    if not first_date:
        return []

    current_month = date.today().replace(day=1)
    rolling_start = add_months(current_month, -(months - 1))
    first_month = first_date.replace(day=1)
    start_month = max(first_month, rolling_start)

    points = []
    cursor = start_month
    while cursor <= current_month:
        key = cursor.strftime("%Y-%m")
        next_month = add_months(cursor, 1)
        month_end = min(date.today(), next_month - timedelta(days=1))
        month_start = cursor.isoformat()
        month_end_text = month_end.isoformat()
        price_expr = (
            "CASE "
            "WHEN lower(coalesce(col.variant, '')) LIKE '%etched%' AND COALESCE(ps.usd_etched, 0) > 0 THEN ps.usd_etched "
            "WHEN lower(coalesce(col.variant, '')) LIKE '%foil%' AND COALESCE(ps.usd_foil, 0) > 0 THEN ps.usd_foil "
            "WHEN COALESCE(ps.usd, 0) > 0 THEN ps.usd "
            "WHEN COALESCE(ps.usd_foil, 0) > 0 THEN ps.usd_foil "
            "WHEN COALESCE(ps.usd_etched, 0) > 0 THEN ps.usd_etched "
            "WHEN lower(coalesce(col.variant, '')) LIKE '%etched%' AND c.current_usd_etched > 0 THEN c.current_usd_etched "
            "WHEN lower(coalesce(col.variant, '')) LIKE '%foil%' AND c.current_usd_foil > 0 THEN c.current_usd_foil "
            "WHEN c.current_usd > 0 THEN c.current_usd "
            "WHEN c.current_usd_foil > 0 THEN c.current_usd_foil "
            "WHEN c.current_usd_etched > 0 THEN c.current_usd_etched "
            "ELSE 0 END"
        )
        row = conn.execute(
            f"""
            SELECT
              ROUND(COALESCE(SUM(CASE WHEN col.acquired_date <= ? THEN col.quantity * ({price_expr}) ELSE 0 END), 0), 2) AS value,
              ROUND(COALESCE(SUM(CASE WHEN col.acquired_date >= ? AND col.acquired_date <= ? THEN col.quantity * ({price_expr}) ELSE 0 END), 0), 2) AS added_value
            FROM collection col
            JOIN cards c ON c.scryfall_id = col.card_id
            LEFT JOIN price_snapshots ps
              ON ps.card_id = col.card_id
             AND ps.snapshot_date = (
                SELECT MAX(ps2.snapshot_date)
                FROM price_snapshots ps2
                WHERE ps2.card_id = col.card_id
                  AND ps2.snapshot_date <= ?
             )
            WHERE col.user_id = ?
              AND col.quantity > 0
              AND col.acquired_date IS NOT NULL
              AND col.acquired_date != ''
            """,
            (month_end_text, month_start, month_end_text, month_end_text, user_id),
        ).fetchone()
        points.append({
            "date": key,
            "label": month_label(cursor),
            "added_value": round(row["added_value"] or 0, 2),
            "value": round(row["value"] or 0, 2),
        })
        cursor = add_months(cursor, 1)
    return points


def set_completion(conn, user_id, limit=10):
    rows = conn.execute(
        """
        SELECT
            COALESCE(s.code, c.set_code) AS set_code,
            COALESCE(s.name, c.set_name) AS set_name,
            COALESCE(s.cached_at, '') AS cached_at,
            COUNT(DISTINCT c.scryfall_id) AS total_cards,
            COUNT(DISTINCT CASE WHEN col.quantity > 0 THEN c.scryfall_id END) AS owned_cards
        FROM cards c
        LEFT JOIN sets s ON s.code = c.set_code
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = c.scryfall_id
        GROUP BY c.set_code
        HAVING owned_cards > 0 AND total_cards > 0
        ORDER BY (owned_cards * 1.0 / total_cards) DESC, owned_cards DESC, set_name
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    result = []
    for row in rows:
        total = row["total_cards"] or 0
        owned = row["owned_cards"] or 0
        result.append({
            **dict(row),
            "completion_percent": round((owned / total * 100) if total else 0, 1),
        })
    return result


def set_detail(conn, user_id, set_code):
    price_expr = current_price_sql("c")
    row = conn.execute(
        f"""
        SELECT
            s.code AS set_code,
            COALESCE(s.name, MAX(c.set_name), s.code) AS set_name,
            COALESCE(s.cached_at, '') AS cached_at,
            COUNT(DISTINCT c.scryfall_id) AS total_cards,
            COUNT(DISTINCT CASE WHEN col.quantity > 0 THEN c.scryfall_id END) AS owned_cards,
            COALESCE(SUM(
                CASE
                    WHEN COALESCE(col.quantity, 0) > 0
                    THEN COALESCE(col.quantity, 0) * COALESCE(col.paid_price, 0)
                    ELSE 0
                END
            ), 0) AS total_paid,
            COALESCE(SUM(
                CASE
                    WHEN COALESCE(col.quantity, 0) > 0
                    THEN COALESCE(col.quantity, 0) * ({price_expr})
                    ELSE 0
                END
            ), 0) AS total_market_value
        FROM cards c
        LEFT JOIN sets s ON s.code = c.set_code
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = c.scryfall_id
        WHERE c.set_code = ?
        GROUP BY c.set_code
        """,
        (user_id, set_code),
    ).fetchone()
    if not row:
        raise KeyError("Set not found")
    total = row["total_cards"] or 0
    owned = row["owned_cards"] or 0
    return {
        **dict(row),
        "completion_percent": round((owned / total * 100) if total else 0, 1),
        "delta": float(row["total_market_value"] or 0) - float(row["total_paid"] or 0),
    }


def dashboard(conn, user_id):
    price_expr = current_price_sql("c")
    totals = conn.execute(
        f"""
        SELECT
            COUNT(DISTINCT c.scryfall_id) AS catalog_cards,
            COALESCE(SUM(col.quantity), 0) AS owned_cards,
            COALESCE(SUM(col.quantity * col.paid_price), 0) AS paid_total,
            COALESCE(SUM(col.quantity * ({price_expr})), 0) AS current_total,
            COUNT(DISTINCT CASE WHEN col.quantity > 0 THEN col.card_id END) AS owned_unique
        FROM cards c
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = c.scryfall_id
        """,
        (user_id,),
    ).fetchone()
    deck_count = conn.execute("SELECT COUNT(*) AS count FROM decks WHERE user_id = ?", (user_id,)).fetchone()["count"]
    cards_in_decks = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM (
            SELECT DISTINCT dc.card_id, COALESCE(NULLIF(dc.variant, ''), 'Normal') AS variant
            FROM deck_cards dc
            JOIN decks d ON d.id = dc.deck_id
            JOIN collection col
              ON col.user_id = d.user_id
             AND col.card_id = dc.card_id
             AND col.variant = COALESCE(NULLIF(dc.variant, ''), 'Normal')
            WHERE d.user_id = ? AND col.quantity > 0
        )
        """,
        (user_id,),
    ).fetchone()["count"]
    container_count = conn.execute("SELECT COUNT(*) AS count FROM containers WHERE user_id = ?", (user_id,)).fetchone()["count"]
    uncontained_cards = conn.execute(
        """
        SELECT COALESCE(SUM(
            CASE
                WHEN col.quantity - COALESCE(stored.quantity, 0) > 0
                THEN col.quantity - COALESCE(stored.quantity, 0)
                ELSE 0
            END
        ), 0) AS count
        FROM collection col
        LEFT JOIN (
            SELECT cc.card_id, COALESCE(NULLIF(cc.variant, ''), 'Normal') AS variant, SUM(cc.quantity) AS quantity
            FROM container_cards cc
            JOIN containers c ON c.id = cc.container_id
            WHERE c.user_id = ?
            GROUP BY cc.card_id, COALESCE(NULLIF(cc.variant, ''), 'Normal')
        ) stored
          ON stored.card_id = col.card_id
         AND stored.variant = COALESCE(NULLIF(col.variant, ''), 'Normal')
        WHERE col.user_id = ? AND col.quantity > 0
        """,
        (user_id, user_id),
    ).fetchone()["count"]
    favorite_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM collection col
        JOIN card_meta meta ON meta.user_id = col.user_id AND meta.card_id = col.card_id AND meta.variant = col.variant
        WHERE col.user_id = ? AND col.quantity > 0 AND COALESCE(meta.favorite, 0) = 1
        """,
        (user_id,),
    ).fetchone()["count"]
    favorite_deck_count = conn.execute(
        "SELECT COUNT(*) AS count FROM favorite_decks WHERE user_id = ?",
        (user_id,),
    ).fetchone()["count"]
    favorite_store_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM favorite_store_listings fav
        JOIN card_sales sale
          ON sale.user_id = fav.seller_user_id
         AND sale.card_id = fav.card_id
         AND sale.variant = fav.variant
         AND sale.card_condition = fav.card_condition
         AND COALESCE(sale.quantity, 0) > 0
        WHERE fav.user_id = ?
        """,
        (user_id,),
    ).fetchone()["count"]
    wishlist_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM (
            SELECT DISTINCT wi.card_id, wi.variant
            FROM wishlist_items wi
            LEFT JOIN collection col ON col.user_id = wi.user_id AND col.card_id = wi.card_id AND COALESCE(col.quantity, 0) > 0
            WHERE wi.user_id = ? AND col.card_id IS NULL
        )
        """,
        (user_id,),
    ).fetchone()["count"]
    sale_summary = conn.execute(
        """
        SELECT
            COALESCE(SUM(quantity), 0) AS count,
            COALESCE(SUM(quantity * asking_price), 0) AS asking_total
        FROM card_sales
        WHERE user_id = ? AND quantity > 0
        """,
        (user_id,),
    ).fetchone()
    top = rows_to_dicts(conn.execute(
        f"""
        SELECT c.*, col.quantity, col.paid_price, col.variant, col.acquired_date,
               COALESCE(meta.favorite, 0) AS favorite,
               ({price_expr}) AS display_price,
               col.quantity * ({price_expr}) AS owned_value,
               col.quantity * (({price_expr}) - col.paid_price) AS gain_loss
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        LEFT JOIN card_meta meta ON meta.user_id = col.user_id AND meta.card_id = col.card_id AND meta.variant = col.variant
        WHERE col.user_id = ? AND col.quantity > 0
        ORDER BY owned_value DESC, c.name
        LIMIT 10
        """,
        (user_id,),
    ).fetchall())
    recent = rows_to_dicts(conn.execute(
        f"""
        SELECT c.*,
               SUM(col.quantity) AS quantity,
               COALESCE(
                   MAX(CASE
                       WHEN COALESCE(NULLIF(col.variant, ''), 'Normal') != 'Normal'
                       THEN COALESCE(NULLIF(col.variant, ''), 'Normal')
                   END),
                   'Normal'
               ) AS variant,
               MAX(COALESCE(p.last_purchase_date, NULLIF(col.acquired_date, ''), col.updated_at)) AS added_at,
               SUM(col.quantity * ({price_expr})) AS owned_value
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        LEFT JOIN (
            SELECT user_id,
                   card_id,
                   MAX(COALESCE(NULLIF(purchase_date, ''), created_at)) AS last_purchase_date
            FROM card_purchases
            WHERE user_id = ? AND quantity > 0
            GROUP BY user_id, card_id
        ) p ON p.user_id = col.user_id AND p.card_id = col.card_id
        WHERE col.user_id = ? AND col.quantity > 0
        GROUP BY col.card_id
        ORDER BY datetime(added_at) DESC, added_at DESC, c.name
        LIMIT 10
        """,
        (user_id, user_id),
    ).fetchall())
    history = collection_value_history(conn, user_id)
    set_breakdown = rows_to_dicts(conn.execute(
        f"""
        SELECT c.set_name, SUM(col.quantity) AS quantity,
               SUM(col.quantity * ({price_expr})) AS value
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        WHERE col.user_id = ? AND col.quantity > 0
        GROUP BY c.set_name
        ORDER BY value DESC
        """,
        (user_id,),
    ).fetchall())
    result = dict(totals)
    result["deck_count"] = deck_count
    result["cards_in_decks"] = cards_in_decks
    result["container_count"] = container_count
    result["uncontained_cards"] = uncontained_cards
    result["favorite_count"] = favorite_count + favorite_deck_count + favorite_store_count
    result["wishlist_count"] = wishlist_count
    result["sale_count"] = sale_summary["count"] or 0
    result["sale_asking_total"] = sale_summary["asking_total"] or 0
    result["total_value"] = result["current_total"]
    result["gain_loss"] = result["current_total"] - result["paid_total"]
    result["gain_loss_percent"] = (result["gain_loss"] / result["paid_total"] * 100) if result["paid_total"] else 0
    result["top_cards"] = top
    result["recent_cards"] = recent
    result["history"] = history
    result["set_breakdown"] = set_breakdown
    result["set_completion"] = set_completion(conn, user_id)
    return result


def home_stats(conn):
    price_expr = current_price_sql("c")
    totals = conn.execute(
        f"""
        SELECT
            COUNT(DISTINCT u.id) AS user_count,
            COALESCE(SUM(CASE WHEN COALESCE(col.quantity, 0) > 0 THEN col.quantity ELSE 0 END), 0) AS cataloged_cards,
            COUNT(DISTINCT CASE WHEN COALESCE(col.quantity, 0) > 0 THEN col.card_id END) AS unique_cards,
            COALESCE(SUM(CASE WHEN COALESCE(col.quantity, 0) > 0 THEN col.quantity * ({price_expr}) ELSE 0 END), 0) AS total_value
        FROM users u
        LEFT JOIN collection col ON col.user_id = u.id
        LEFT JOIN cards c ON c.scryfall_id = col.card_id
        """
    ).fetchone()
    deck_count = conn.execute("SELECT COUNT(*) AS count FROM decks").fetchone()["count"] or 0
    container_count = conn.execute("SELECT COUNT(*) AS count FROM containers").fetchone()["count"] or 0
    wishlist_count = conn.execute("SELECT COUNT(*) AS count FROM wishlists").fetchone()["count"] or 0
    sale_summary = conn.execute(
        """
        SELECT
            COUNT(*) AS listing_count,
            COALESCE(SUM(quantity), 0) AS sale_quantity,
            COALESCE(SUM(quantity * asking_price), 0) AS asking_total
        FROM card_sales
        WHERE COALESCE(quantity, 0) > 0
        """
    ).fetchone()
    daily_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM (
            SELECT col.card_id, COALESCE(NULLIF(col.variant, ''), 'Normal') AS variant
            FROM collection col
            WHERE COALESCE(col.quantity, 0) > 0
            GROUP BY col.card_id, COALESCE(NULLIF(col.variant, ''), 'Normal')
        )
        """
    ).fetchone()["count"] or 0
    todays_card = None
    if daily_count:
        offset = int(date.today().strftime("%Y%m%d")) % int(daily_count)
        row = conn.execute(
            f"""
            SELECT c.scryfall_id, c.name, c.flavor_name, c.flavor_text, c.set_code, c.set_name,
                   c.collector_number, c.rarity, c.type_line, c.type_category, c.colors, c.color_identity,
                   c.image_small, c.image_normal, c.scryfall_uri,
                   COALESCE(NULLIF(col.variant, ''), 'Normal') AS variant,
                   COALESCE(SUM(col.quantity), 0) AS quantity,
                   ({price_expr}) AS display_price
            FROM collection col
            JOIN cards c ON c.scryfall_id = col.card_id
            WHERE COALESCE(col.quantity, 0) > 0
            GROUP BY col.card_id, COALESCE(NULLIF(col.variant, ''), 'Normal')
            ORDER BY lower(c.name), lower(c.set_code), c.collector_number, variant
            LIMIT 1 OFFSET ?
            """,
            (offset,),
        ).fetchone()
        if row:
            todays_card = with_value_aliases(dict(row))
    return {
        "user_count": int(totals["user_count"] or 0),
        "cataloged_cards": int(totals["cataloged_cards"] or 0),
        "unique_cards": int(totals["unique_cards"] or 0),
        "deck_count": int(deck_count),
        "container_count": int(container_count),
        "wishlist_count": int(wishlist_count),
        "total_value": float(totals["total_value"] or 0),
        "sale_listing_count": int(sale_summary["listing_count"] or 0),
        "sale_quantity": int(sale_summary["sale_quantity"] or 0),
        "sale_asking_total": float(sale_summary["asking_total"] or 0),
        "announcements": active_home_announcements(conn),
        "todays_card": todays_card,
    }


def search_hero_cards(conn, limit=5):
    rows = conn.execute(
        """
        SELECT c.scryfall_id, c.name, c.flavor_name, c.set_code, c.set_name,
               c.collector_number, c.image_small, c.image_normal, c.scryfall_uri,
               COALESCE(NULLIF(col.variant, ''), 'Normal') AS variant,
               COALESCE(SUM(col.quantity), 0) AS quantity
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        WHERE COALESCE(col.quantity, 0) > 0
          AND COALESCE(c.image_normal, c.image_small, '') != ''
        GROUP BY col.card_id, COALESCE(NULLIF(col.variant, ''), 'Normal')
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (max(1, min(5, int(limit or 5))),),
    ).fetchall()
    return [with_value_aliases(dict(row)) for row in rows]


def rows_to_dicts(rows):
    return [with_value_aliases(dict(row)) for row in rows]


def with_value_aliases(row):
    if "display_price" in row and "market_price" not in row:
        row["market_price"] = row["display_price"]
    if "current_value" in row and "market_price" not in row:
        row["market_price"] = row["current_value"]
    if "owned_value" in row and "total_value" not in row:
        row["total_value"] = row["owned_value"]
    elif "quantity" in row and "market_price" in row and "total_value" not in row:
        row["total_value"] = (row.get("quantity") or 0) * (row.get("market_price") or 0)
    return row


def name_exists(conn, table, name, user_id, exclude_id=None):
    if table not in {"decks", "containers", "wishlists"}:
        raise ValueError("Unsupported name check.")
    return cross_entity_name_exists(conn, user_id, name, exclude_table=table, exclude_id=exclude_id)


def list_decks(conn, user_id):
    rows = conn.execute(
        """
        SELECT d.id, d.share_id, d.name,
               COALESCE(d.description, '') AS description,
               COALESCE(d.external_notes, '') AS external_notes,
               COALESCE(d.is_private, 0) AS is_private,
               d.created_at, d.updated_at,
               COALESCE(SUM(dc.quantity), 0) AS card_count,
               COUNT(dc.card_id) AS unique_card_count,
               (
                   SELECT GROUP_CONCAT(image, '|||')
                   FROM (
                       SELECT DISTINCT COALESCE(NULLIF(c2.image_normal, ''), NULLIF(c2.image_small, '')) AS image
                       FROM deck_cards dc2
                       JOIN cards c2 ON c2.scryfall_id = dc2.card_id
                       WHERE dc2.deck_id = d.id
                         AND COALESCE(NULLIF(c2.image_normal, ''), NULLIF(c2.image_small, '')) IS NOT NULL
                       ORDER BY RANDOM()
                       LIMIT 5
                   )
               ) AS preview_images
        FROM decks d
        LEFT JOIN deck_cards dc ON dc.deck_id = d.id
        WHERE d.user_id = ?
        GROUP BY d.id
        ORDER BY d.updated_at DESC, d.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    decks = rows_to_dicts(rows)
    for deck in decks:
        deck["preview_images"] = [image for image in (deck.get("preview_images") or "").split("|||") if image][:5]
    return decks


def create_deck(conn, user_id, payload):
    name = validate_user_content_name(payload.get("name"), "Deck name", 20)
    if name_exists(conn, "decks", name, user_id):
        raise ValueError("Deck name must be unique across your decks, containers, and wishlists.")
    enforce_role_limit(conn, user_id, "decks", "decks", "decks")
    description = clean_deck_text(payload.get("description"), 500, "Description")
    internal_notes = clean_deck_text(payload.get("internal_notes"), 2000, "Internal notes")
    external_notes = clean_deck_text(payload.get("external_notes"), 2000, "External notes")
    is_private = bool_int(payload.get("is_private"))
    timestamp = now_iso()
    share_id = new_deck_share_id(conn)
    cursor = conn.execute(
        """
        INSERT INTO decks (user_id, share_id, name, description, internal_notes, external_notes, is_private, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, share_id, name, description, internal_notes, external_notes, is_private, timestamp, timestamp),
    )
    conn.commit()
    return {
        "ok": True,
        "deck": {
            "id": cursor.lastrowid,
            "share_id": share_id,
            "name": name,
            "description": description,
            "internal_notes": internal_notes,
            "external_notes": external_notes,
            "is_private": is_private,
            "created_at": timestamp,
            "updated_at": timestamp,
            "card_count": 0,
            "unique_card_count": 0,
        },
    }


def clean_deck_text(value, limit, label):
    text = str(value or "").strip()
    if len(text) > limit:
        raise ValueError(f"{label} must be {limit} characters or fewer.")
    return text


def update_deck(conn, user_id, deck_id, payload):
    deck = conn.execute("SELECT id, name FROM decks WHERE id = ? AND user_id = ?", (deck_id, user_id)).fetchone()
    if not deck:
        raise KeyError("Deck not found")
    name = validate_user_content_name(payload.get("name") or deck["name"], "Deck name", 20)
    if name_exists(conn, "decks", name, user_id, exclude_id=deck_id):
        raise ValueError("Deck name must be unique across your decks, containers, and wishlists.")
    description = clean_deck_text(payload.get("description"), 500, "Description")
    internal_notes = clean_deck_text(payload.get("internal_notes"), 2000, "Internal notes")
    external_notes = clean_deck_text(payload.get("external_notes"), 2000, "External notes")
    is_private = bool_int(payload.get("is_private"))
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE decks
        SET name = ?,
            description = ?,
            internal_notes = ?,
            external_notes = ?,
            is_private = ?,
            updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (name, description, internal_notes, external_notes, is_private, timestamp, deck_id, user_id),
    )
    conn.commit()
    return {"ok": True, "deck": deck_detail(conn, user_id, deck_id)}


def deck_cards(conn, user_id, deck_id):
    price_expr = current_price_sql("c")
    rows = conn.execute(
        f"""
        SELECT c.*, dc.variant, dc.quantity AS deck_quantity, dc.added_at,
               COALESCE(col.quantity, 0) AS quantity,
               COALESCE(col.paid_price, 0.01) AS paid_price,
               COALESCE(col.card_condition, 'Near Mint') AS card_condition,
               COALESCE(col.graded, 0) AS graded,
               col.acquired_date,
               col.share_id,
               ({price_expr}) AS display_price,
               COALESCE(dc.quantity, 0) * ({price_expr}) AS deck_value
        FROM deck_cards dc
        JOIN cards c ON c.scryfall_id = dc.card_id
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = dc.card_id AND col.variant = dc.variant
        WHERE dc.deck_id = ?
        ORDER BY c.name COLLATE NOCASE, dc.variant
        """,
        (user_id, deck_id),
    ).fetchall()
    cards = rows_to_dicts(rows)
    for card in cards:
        deck_quantity = int(card.get("deck_quantity") or 0)
        owned_quantity = int(card.get("quantity") or 0)
        card["owned_quantity"] = owned_quantity
        card["short_quantity"] = max(0, deck_quantity - owned_quantity)
    return cards


def deck_detail(conn, user_id, deck_id):
    deck = conn.execute(
        """
        SELECT d.id, d.share_id, d.name,
               COALESCE(d.description, '') AS description,
               COALESCE(d.internal_notes, '') AS internal_notes,
               COALESCE(d.external_notes, '') AS external_notes,
               COALESCE(d.is_private, 0) AS is_private,
               d.created_at, d.updated_at,
               COALESCE(SUM(dc.quantity), 0) AS card_count,
               COUNT(dc.card_id) AS unique_card_count
        FROM decks d
        LEFT JOIN deck_cards dc ON dc.deck_id = d.id
        WHERE d.id = ? AND d.user_id = ?
        GROUP BY d.id
        """,
        (deck_id, user_id),
    ).fetchone()
    if not deck:
        raise KeyError("Deck not found")
    payload = dict(deck)
    payload["cards"] = deck_cards(conn, user_id, deck_id)
    return payload


def deck_export_card(card):
    return {
        "scryfall_id": card.get("scryfall_id") or card.get("card_id") or "",
        "name": card.get("name") or "",
        "set_code": card.get("set_code") or "",
        "set_name": card.get("set_name") or "",
        "collector_number": card.get("collector_number") or "",
        "rarity": card.get("rarity") or "",
        "variant": card.get("variant") or "Normal",
        "quantity": int(card.get("deck_quantity") or card.get("quantity") or 1),
        "type_line": card.get("type_line") or "",
        "type_category": card.get("type_category") or "",
        "colors": card.get("colors") or "",
        "color_identity": card.get("color_identity") or "",
        "image_small": card.get("image_small") or "",
        "image_normal": card.get("image_normal") or "",
        "scryfall_uri": card.get("scryfall_uri") or "",
    }


def deck_export_payload(conn, user_id):
    decks = []
    for deck in list_decks(conn, user_id):
        detail = deck_detail(conn, user_id, deck["id"])
        decks.append({
            "name": detail.get("name") or "Deck",
            "description": detail.get("description") or "",
            "internal_notes": detail.get("internal_notes") or "",
            "external_notes": detail.get("external_notes") or "",
            "is_private": bool_int(detail.get("is_private")),
            "cards": [deck_export_card(card) for card in detail.get("cards") or []],
        })
    return {
        "format": "arcaneledger.decks",
        "version": 1,
        "exported_at": now_iso(),
        "deck_count": len(decks),
        "decks": decks,
    }


def export_decks_csv(conn, user_id):
    output = io.StringIO()
    fieldnames = [
        "deck_name", "description", "internal_notes", "external_notes", "is_private",
        "scryfall_id", "card_name", "set_code", "set_name", "collector_number",
        "rarity", "variant", "quantity", "type_line", "type_category",
        "colors", "color_identity", "image_small", "image_normal", "scryfall_uri",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for deck in deck_export_payload(conn, user_id)["decks"]:
        cards = deck.get("cards") or []
        if not cards:
            writer.writerow({
                "deck_name": deck.get("name") or "",
                "description": deck.get("description") or "",
                "internal_notes": deck.get("internal_notes") or "",
                "external_notes": deck.get("external_notes") or "",
                "is_private": bool_int(deck.get("is_private")),
            })
            continue
        for card in cards:
            writer.writerow({
                "deck_name": deck.get("name") or "",
                "description": deck.get("description") or "",
                "internal_notes": deck.get("internal_notes") or "",
                "external_notes": deck.get("external_notes") or "",
                "is_private": bool_int(deck.get("is_private")),
                "scryfall_id": card.get("scryfall_id") or "",
                "card_name": card.get("name") or "",
                "set_code": card.get("set_code") or "",
                "set_name": card.get("set_name") or "",
                "collector_number": card.get("collector_number") or "",
                "rarity": card.get("rarity") or "",
                "variant": card.get("variant") or "Normal",
                "quantity": card.get("quantity") or 1,
                "type_line": card.get("type_line") or "",
                "type_category": card.get("type_category") or "",
                "colors": card.get("colors") or "",
                "color_identity": card.get("color_identity") or "",
                "image_small": card.get("image_small") or "",
                "image_normal": card.get("image_normal") or "",
                "scryfall_uri": card.get("scryfall_uri") or "",
            })
    return output.getvalue()


def parse_decks_csv(text):
    try:
        reader = csv.DictReader(io.StringIO(text or ""))
        if not reader.fieldnames:
            raise ValueError("CSV file is missing a header row.")
        normalized_headers = {field.strip().lower(): field for field in reader.fieldnames if field}
        if "deck_name" not in normalized_headers:
            raise ValueError("CSV must include a deck_name column.")
        decks = {}
        for row_number, row in enumerate(reader, start=2):
            row = {str(key or "").strip().lower(): (value or "").strip() for key, value in row.items()}
            name = row.get("deck_name") or row.get("name") or ""
            if not name:
                continue
            deck = decks.setdefault(name, {
                "name": name,
                "description": row.get("description") or "",
                "internal_notes": row.get("internal_notes") or "",
                "external_notes": row.get("external_notes") or "",
                "is_private": bool_int(row.get("is_private")),
                "cards": [],
            })
            card_id = row.get("scryfall_id") or row.get("card_id") or row.get("id") or ""
            if not card_id:
                continue
            deck["cards"].append({
                "scryfall_id": card_id,
                "name": row.get("card_name") or row.get("name") or "",
                "set_code": row.get("set_code") or "",
                "set_name": row.get("set_name") or "",
                "collector_number": row.get("collector_number") or "",
                "rarity": row.get("rarity") or "",
                "variant": row.get("variant") or "Normal",
                "quantity": row.get("quantity") or 1,
                "type_line": row.get("type_line") or "",
                "type_category": row.get("type_category") or "",
                "colors": row.get("colors") or "",
                "color_identity": row.get("color_identity") or "",
                "image_small": row.get("image_small") or "",
                "image_normal": row.get("image_normal") or "",
                "scryfall_uri": row.get("scryfall_uri") or "",
                "row_number": row_number,
            })
        if not decks:
            raise ValueError("CSV did not include any decks.")
        return list(decks.values())
    except csv.Error as exc:
        raise ValueError(f"CSV is not valid: {exc}") from exc


def parse_moxfield_deck_line(line, row_number):
    raw = (line or "").strip()
    if not raw or raw.startswith("#"):
        return None
    match = re.match(r"^\s*(\d+)\s+(.+?)\s*$", raw)
    if not match:
        return {
            "row_number": row_number,
            "raw": raw,
            "error": "Line must start with an amount followed by a card name.",
        }
    quantity = max(1, int(match.group(1)))
    rest = match.group(2).strip()
    variant = "Foil" if re.search(r"\*F\*", rest, flags=re.IGNORECASE) else "Normal"
    rest = re.sub(r"\s*\*F\*\s*", " ", rest, flags=re.IGNORECASE).strip()
    set_code = ""
    set_match = re.search(r"\(([A-Za-z0-9:_-]{2,12})\)", rest)
    if set_match:
        set_code = set_match.group(1).strip().lower()
        rest = (rest[:set_match.start()] + " " + rest[set_match.end():]).strip()
    collector_number = ""
    number_match = re.search(r"\s+([A-Za-z0-9][A-Za-z0-9-]*[A-Za-z]?)\s*$", rest)
    if number_match and any(char.isdigit() for char in number_match.group(1)):
        collector_number = number_match.group(1).strip()
        rest = rest[:number_match.start()].strip()
    name = re.sub(r"\s+", " ", rest).strip()
    if not name:
        return {
            "row_number": row_number,
            "raw": raw,
            "error": "Card name is missing.",
        }
    return {
        "row_number": row_number,
        "raw": raw,
        "quantity": quantity,
        "name": name,
        "set_code": set_code,
        "collector_number": collector_number,
        "variant": variant,
    }


def parse_moxfield_deck_text(text):
    rows = []
    errors = []
    for row_number, line in enumerate((text or "").splitlines(), start=1):
        parsed = parse_moxfield_deck_line(line, row_number)
        if not parsed:
            continue
        if parsed.get("error"):
            errors.append(parsed)
        else:
            rows.append(parsed)
    if not rows and errors:
        raise ValueError("Moxfield deck import did not include any usable card rows.")
    if not rows:
        raise ValueError("Paste at least one Moxfield deck line.")
    return rows, errors


def is_moxfield_like_deck_import(source_format):
    return (source_format or "").lower() in {"moxfield_deck", "arena_deck"}


def preview_moxfield_deck_import(conn, user_id, payload):
    content = payload.get("content") or payload.get("text") or ""
    source_format = (payload.get("format") or "moxfield_deck").lower()
    deck_label = "Magic Arena Deck" if source_format == "arena_deck" else "Moxfield Deck"
    rows, parse_errors = parse_moxfield_deck_text(content)
    entries = []
    for row in rows:
        entries.append({
            "line": row["row_number"],
            "format": source_format if is_moxfield_like_deck_import(source_format) else "moxfield_deck",
            "name": row["name"],
            "set_code": row.get("set_code") or "",
            "set_name": "",
            "collector_number": row.get("collector_number") or "",
            "quantity": row["quantity"],
            "paid_price": 0.01,
            "acquired_date": today_iso(),
            "variant": row.get("variant") or "Normal",
            "card_condition": DEFAULT_CARD_CONDITION,
            "graded": 0,
            "raw": row.get("raw") or "",
        })
    matched = preview_import_entries(conn, entries)
    card_rows = []
    cards = []
    card_count = 0
    unique_cards = set()
    for row in matched.get("rows") or []:
        entry = row.get("entry") or {}
        match_card = ((row.get("match") or {}).get("card") or {})
        card_id = match_card.get("scryfall_id") or ""
        variant = entry.get("variant") or "Normal"
        quantity = max(1, int(entry.get("quantity") or 1))
        if card_id:
            cards.append({
                **match_card,
                "scryfall_id": card_id,
                "variant": variant,
                "quantity": quantity,
                "deck_quantity": quantity,
                "row_number": entry.get("line"),
                "raw": entry.get("raw") or "",
            })
            card_count += quantity
            unique_cards.add((card_id, variant))
        card_rows.append({
            **row,
            "quantity": quantity,
            "variant": variant,
            "raw": entry.get("raw") or "",
        })
    deck = {
        "index": 1,
        "name": re.sub(r"\s+", " ", (payload.get("name") or deck_label).strip())[:20] or deck_label,
        "original_name": payload.get("name") or deck_label,
        "description": "",
        "internal_notes": "",
        "external_notes": "",
        "is_private": 0,
        "cards": cards,
    }
    issues_by_index = deck_import_name_issues(conn, user_id, [deck])
    parse_issue_messages = [
        f"Line {item['row_number']}: {item['error']}"
        for item in parse_errors
    ]
    unmatched = [row for row in card_rows if not ((row.get("match") or {}).get("card") or {}).get("scryfall_id")]
    issues = list(dict.fromkeys((issues_by_index.get(1, []) or []) + parse_issue_messages))
    if unmatched:
        issues.append(f"{len(unmatched)} card row(s) need a Scryfall match before importing.")
    preview = {
        "index": 1,
        "name": deck["name"],
        "original_name": deck["original_name"],
        "card_count": card_count,
        "unique_card_count": len(unique_cards),
        "issues": issues,
        "needs_rename": bool(issues_by_index.get(1)),
    }
    return {
        "ok": True,
        "format": source_format if is_moxfield_like_deck_import(source_format) else "moxfield_deck",
        "decks": [preview],
        "normalized_decks": [deck],
        "card_rows": card_rows,
        "issues": matched.get("issues") or [],
    }


def normalize_import_deck_source(payload):
    payload = payload or {}
    source = payload.get("decks") if isinstance(payload.get("decks"), list) else None
    content = payload.get("content") or payload.get("json") or ""
    import_format = (payload.get("format") or "json").lower()
    if source is None:
        if import_format == "csv":
            source = parse_decks_csv(content)
        else:
            try:
                parsed = json.loads(content) if isinstance(content, str) else content
            except json.JSONDecodeError as exc:
                raise ValueError("Deck JSON is not valid JSON.") from exc
            if isinstance(parsed, list):
                source = parsed
            elif isinstance(parsed, dict) and isinstance(parsed.get("decks"), list):
                source = parsed["decks"]
            elif isinstance(parsed, dict):
                source = [parsed.get("deck") if isinstance(parsed.get("deck"), dict) else parsed]
            else:
                raise ValueError("Deck JSON must be an object, an array, or an Arcane Ledger decks export.")
    decks = []
    for index, deck_source in enumerate(source or [], start=1):
        if not isinstance(deck_source, dict):
            continue
        cards = deck_source.get("cards") or []
        if not isinstance(cards, list):
            cards = []
        name = re.sub(r"\s+", " ", (deck_source.get("name") or deck_source.get("deck_name") or "").strip())
        decks.append({
            "index": index,
            "name": name,
            "original_name": name,
            "description": str(deck_source.get("description") or "")[:500],
            "internal_notes": str(deck_source.get("internal_notes") or "")[:2000],
            "external_notes": str(deck_source.get("external_notes") or "")[:2000],
            "is_private": bool_int(deck_source.get("is_private")),
            "cards": cards,
        })
    if not decks:
        raise ValueError("Import did not include any decks.")
    return decks


def deck_import_name_issues(conn, user_id, decks):
    issues_by_index = {}
    seen = {}
    for deck in decks:
        issues = []
        name = re.sub(r"\s+", " ", (deck.get("name") or "").strip())
        deck["name"] = name
        try:
            validate_user_content_name(name, "Deck name", 20)
        except ValueError as exc:
            issues.append(str(exc))
        lower_name = name.lower()
        if lower_name:
            if lower_name in seen:
                issues.append("Deck name is duplicated in this import.")
                issues_by_index.setdefault(seen[lower_name], []).append("Deck name is duplicated in this import.")
            else:
                seen[lower_name] = deck["index"]
            if cross_entity_name_exists(conn, user_id, name):
                issues.append("Deck name already exists in your account.")
        if issues:
            issues_by_index.setdefault(deck["index"], []).extend(issues)
    return issues_by_index


def preview_deck_import(conn, user_id, payload):
    if is_moxfield_like_deck_import(payload.get("format")):
        return preview_moxfield_deck_import(conn, user_id, payload)
    decks = normalize_import_deck_source(payload)
    issues_by_index = deck_import_name_issues(conn, user_id, decks)
    preview = []
    for deck in decks:
        card_count = 0
        unique_cards = set()
        for card in deck.get("cards") or []:
            if not isinstance(card, dict):
                continue
            card_id = card.get("scryfall_id") or card.get("card_id") or card.get("id")
            if not card_id:
                continue
            variant = card.get("variant") or "Normal"
            quantity = max(1, int(money(card.get("deck_quantity") or card.get("quantity"), fallback=1)))
            card_count += quantity
            unique_cards.add((str(card_id), str(variant)))
        preview.append({
            "index": deck["index"],
            "name": deck.get("name") or "",
            "original_name": deck.get("original_name") or "",
            "card_count": card_count,
            "unique_card_count": len(unique_cards),
            "issues": list(dict.fromkeys(issues_by_index.get(deck["index"], []))),
            "needs_rename": bool(issues_by_index.get(deck["index"])),
        })
    return {"ok": True, "decks": preview, "normalized_decks": decks}


def normalize_import_wishlist_source(payload):
    payload = payload or {}
    source = payload.get("wishlists") if isinstance(payload, dict) and isinstance(payload.get("wishlists"), list) else None
    if source is None:
        if isinstance(payload, dict) and isinstance(payload.get("wishlist"), dict):
            source = [payload.get("wishlist")]
        elif isinstance(payload, list):
            source = payload
        elif isinstance(payload, dict):
            source = [payload]
        else:
            source = []
    wishlists = []
    for index, wishlist_source in enumerate(source or [], start=1):
        if not isinstance(wishlist_source, dict):
            continue
        cards = wishlist_source.get("cards") or wishlist_source.get("items") or []
        if not isinstance(cards, list):
            cards = []
        name = re.sub(r"\s+", " ", (wishlist_source.get("name") or wishlist_source.get("wishlist_name") or "").strip())
        normalized_cards = []
        for row_number, card in enumerate(cards, start=1):
            if not isinstance(card, dict):
                continue
            normalized_cards.append({
                **card,
                "scryfall_id": card.get("scryfall_id") or card.get("card_id") or card.get("id") or "",
                "name": card.get("name") or card.get("display_name") or card.get("card_name") or "",
                "set_code": card.get("set_code") or card.get("set") or "",
                "set_name": card.get("set_name") or "",
                "collector_number": card.get("collector_number") or card.get("card_number") or "",
                "variant": card.get("variant") or "Normal",
                "quantity": max(1, int(money(card.get("wishlist_quantity") or card.get("quantity") or card.get("deck_quantity"), fallback=1))),
                "row_number": card.get("row_number") or row_number,
            })
        wishlists.append({
            "index": index,
            "name": name,
            "original_name": name,
            "cards": normalized_cards,
        })
    if not wishlists:
        raise ValueError("Import did not include any wishlists.")
    return wishlists


def wishlist_import_name_issues(conn, user_id, wishlists):
    issues_by_index = {}
    seen = {}
    for wishlist in wishlists:
        issues = []
        name = re.sub(r"\s+", " ", (wishlist.get("name") or "").strip())
        wishlist["name"] = name
        try:
            validate_user_content_name(name, "Wishlist name", 30)
        except ValueError as exc:
            issues.append(str(exc))
        lower_name = name.lower()
        if lower_name:
            if lower_name in seen:
                issues.append("Wishlist name is duplicated in this import.")
                issues_by_index.setdefault(seen[lower_name], []).append("Wishlist name is duplicated in this import.")
            else:
                seen[lower_name] = wishlist["index"]
            if cross_entity_name_exists(conn, user_id, name):
                issues.append("Wishlist name already exists in your account.")
        if issues:
            issues_by_index.setdefault(wishlist["index"], []).extend(issues)
    return issues_by_index


def preview_wishlist_import(conn, user_id, payload):
    wishlists = normalize_import_wishlist_source(payload)
    issues_by_index = wishlist_import_name_issues(conn, user_id, wishlists)
    preview = []
    for wishlist in wishlists:
        card_count = 0
        unique_cards = set()
        missing_ids = 0
        for card in wishlist.get("cards") or []:
            card_id = card.get("scryfall_id") or card.get("card_id") or card.get("id")
            if not card_id:
                missing_ids += 1
                continue
            variant = card.get("variant") or "Normal"
            quantity = max(1, int(money(card.get("wishlist_quantity") or card.get("quantity"), fallback=1)))
            card_count += quantity
            unique_cards.add((str(card_id), str(variant)))
        issues = list(dict.fromkeys(issues_by_index.get(wishlist["index"], [])))
        if missing_ids:
            issues.append(f"{missing_ids} card row(s) are missing Scryfall IDs and will be skipped.")
        preview.append({
            "index": wishlist["index"],
            "name": wishlist.get("name") or "",
            "original_name": wishlist.get("original_name") or "",
            "card_count": card_count,
            "unique_card_count": len(unique_cards),
            "issues": issues,
            "needs_rename": bool(issues_by_index.get(wishlist["index"])),
        })
    return {"ok": True, "wishlists": preview, "normalized_wishlists": wishlists}


def json_list(value):
    if isinstance(value, list):
        return json.dumps(normalized_color_list(value))
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return "[]"
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return json.dumps(normalized_color_list(parsed))
        except json.JSONDecodeError:
            pass
        return json.dumps(normalized_color_list([part.strip() for part in re.split(r"[,/ ]+", stripped) if part.strip()]))
    return "[]"


def ensure_import_card_cached(conn, card):
    card_id = card.get("scryfall_id") or card.get("card_id") or card.get("id")
    if not card_id:
        raise ValueError("Every imported deck card needs a scryfall_id.")
    if conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone():
        return
    name = card.get("name") or card.get("display_name") or card.get("card_name")
    set_code = (card.get("set_code") or card.get("set") or "").lower()
    set_name = card.get("set_name") or (set_code.upper() if set_code else "")
    collector_number = card.get("collector_number") or ""
    if not (name and set_code and set_name and collector_number):
        cache_card_by_id(conn, str(card_id))
        return
    timestamp = now_iso()
    upsert_set_metadata(conn, {"code": set_code, "name": set_name}, timestamp)
    display_price = money(card.get("display_price") or card.get("market_price") or card.get("current_usd"))
    conn.execute(
        """
        INSERT INTO cards (
            scryfall_id, oracle_id, name, set_code, set_name, collector_number, rarity,
            type_line, type_category, colors, color_identity, flavor_name, flavor_text, layout,
            finishes, image_small, image_normal, image_art, scryfall_uri,
            current_usd, current_usd_foil, current_usd_etched, last_synced_at
        )
        VALUES (?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', 'normal', '', ?, ?, '', ?, ?, ?, ?, ?)
        ON CONFLICT(scryfall_id) DO NOTHING
        """,
        (
            card_id,
            name,
            set_code,
            set_name,
            collector_number,
            card.get("rarity") or "",
            card.get("type_line") or "",
            card.get("type_category") or card_type_category(card.get("type_line")),
            json_list(card.get("colors")),
            json_list(card.get("color_identity")),
            card.get("image_small") or "",
            card.get("image_normal") or "",
            card.get("scryfall_uri") or "",
            display_price,
            money(card.get("current_usd_foil")),
            money(card.get("current_usd_etched")),
            timestamp,
        ),
    )


def commit_deck_import(conn, user_id, payload):
    decks = normalize_import_deck_source(payload)
    issues_by_index = deck_import_name_issues(conn, user_id, decks)
    if issues_by_index:
        raise ValueError("Resolve duplicate or invalid deck names before importing.")
    enforce_role_limit(conn, user_id, "decks", "decks", "decks", len(decks))
    timestamp = now_iso()
    imported = []
    for deck in decks:
        requested = {}
        card_payloads = {}
        for card in deck.get("cards") or []:
            if not isinstance(card, dict):
                continue
            card_id = card.get("scryfall_id") or card.get("card_id") or card.get("id")
            if not card_id:
                continue
            variant = card.get("variant") or "Normal"
            quantity = max(1, int(money(card.get("deck_quantity") or card.get("quantity"), fallback=1)))
            key = (str(card_id), str(variant))
            requested[key] = requested.get(key, 0) + quantity
            card_payloads[key] = card
        for key in requested:
            ensure_import_card_cached(conn, card_payloads[key])
        cursor = conn.execute(
            """
            INSERT INTO decks (user_id, share_id, name, description, internal_notes, external_notes, is_private, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                new_deck_share_id(conn),
                deck["name"],
                clean_deck_text(deck.get("description"), 500, "Description"),
                clean_deck_text(deck.get("internal_notes"), 2000, "Internal notes"),
                clean_deck_text(deck.get("external_notes"), 2000, "External notes"),
                bool_int(deck.get("is_private")),
                timestamp,
                timestamp,
            ),
        )
        deck_id = cursor.lastrowid
        for (card_id, variant), quantity in requested.items():
            conn.execute(
                """
                INSERT INTO deck_cards (deck_id, card_id, variant, quantity, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (deck_id, card_id, variant, quantity, timestamp),
            )
        imported.append(deck_detail(conn, user_id, deck_id))
    conn.commit()
    return {"ok": True, "imported": len(imported), "decks": imported}


def commit_wishlist_import(conn, user_id, payload):
    wishlists = normalize_import_wishlist_source(payload)
    issues_by_index = wishlist_import_name_issues(conn, user_id, wishlists)
    if issues_by_index:
        raise ValueError("Resolve duplicate or invalid wishlist names before importing.")
    enforce_role_limit(conn, user_id, "wishlists", "wishlists", "wishlists", len(wishlists))
    timestamp = now_iso()
    imported = []
    skipped = []
    for wishlist in wishlists:
        cursor = conn.execute(
            "INSERT INTO wishlists (user_id, share_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, new_wishlist_share_id(conn), wishlist["name"], timestamp, timestamp),
        )
        wishlist_id = cursor.lastrowid
        requested = {}
        card_payloads = {}
        for card in wishlist.get("cards") or []:
            if not isinstance(card, dict):
                continue
            card_id = card.get("scryfall_id") or card.get("card_id") or card.get("id")
            if not card_id:
                skipped.append({"wishlist": wishlist["name"], "row": card.get("row_number"), "error": "Missing Scryfall ID."})
                continue
            variant = card.get("variant") or "Normal"
            quantity = max(1, int(money(card.get("wishlist_quantity") or card.get("quantity"), fallback=1)))
            key = (str(card_id), str(variant))
            requested[key] = requested.get(key, 0) + quantity
            card_payloads[key] = card
        for (card_id, variant), quantity in requested.items():
            card_payload = card_payloads[(card_id, variant)]
            try:
                ensure_import_card_cached(conn, card_payload)
            except Exception:
                cache_card_by_id(conn, card_id)
            summary_json = None
            if not conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone():
                summary = wishlist_payload_summary(card_id, {"card": card_payload, "variant": variant})
                summary_json = json.dumps(summary)
            conn.execute(
                """
                INSERT INTO wishlist_items (wishlist_id, user_id, card_id, variant, quantity, card_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(wishlist_id, card_id, variant) DO UPDATE SET
                    quantity = wishlist_items.quantity + excluded.quantity,
                    card_json = COALESCE(excluded.card_json, wishlist_items.card_json),
                    updated_at = excluded.updated_at
                """,
                (wishlist_id, user_id, card_id, variant, quantity, summary_json, timestamp),
            )
            conn.execute(
                """
                INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, wishlist, updated_at)
                VALUES (?, ?, ?, 0, 0, 1, ?)
                ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
                    wishlist = 1,
                    updated_at = excluded.updated_at
                """,
                (user_id, card_id, variant, timestamp),
            )
        imported.append(wishlist_detail(conn, user_id, wishlist_id))
    conn.commit()
    return {"ok": True, "imported": len(imported), "wishlists": imported, "skipped_rows": skipped}


def import_deck_json(conn, user_id, payload):
    source = payload or {}
    if isinstance(source.get("json"), str):
        try:
            source = json.loads(source["json"])
        except json.JSONDecodeError as exc:
            raise ValueError("Deck JSON is not valid JSON.") from exc
    if not isinstance(source, dict):
        raise ValueError("Deck JSON must be an object.")
    deck_source = source.get("deck") if isinstance(source.get("deck"), dict) else source
    cards = deck_source.get("cards") or source.get("cards") or []
    if not isinstance(cards, list):
        raise ValueError("Deck JSON cards must be a list.")
    name = validate_user_content_name(deck_source.get("name") or source.get("name"), "Deck name", 20)
    if name_exists(conn, "decks", name, user_id):
        raise ValueError("Deck name must be unique across your decks, containers, and wishlists.")
    enforce_role_limit(conn, user_id, "decks", "decks", "decks")
    description = clean_deck_text(deck_source.get("description"), 500, "Description")
    internal_notes = clean_deck_text(deck_source.get("internal_notes"), 2000, "Internal notes")
    external_notes = clean_deck_text(deck_source.get("external_notes"), 2000, "External notes")
    is_private = bool_int(deck_source.get("is_private"))
    requested = {}
    labels = {}
    for card in cards:
        if not isinstance(card, dict):
            continue
        card_id = card.get("scryfall_id") or card.get("card_id") or card.get("id")
        if not card_id:
            continue
        variant = card.get("variant") or "Normal"
        quantity = max(1, int(money(card.get("deck_quantity") or card.get("quantity"), fallback=1)))
        key = (str(card_id), str(variant))
        requested[key] = requested.get(key, 0) + quantity
        labels[key] = card.get("name") or card.get("display_name") or str(card_id)
    if not requested:
        raise ValueError("Deck JSON does not include any cards.")
    for (card_id, _variant), _quantity in requested.items():
        if not conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone():
            cache_card_by_id(conn, card_id)
    timestamp = now_iso()
    share_id = new_deck_share_id(conn)
    cursor = conn.execute(
        """
        INSERT INTO decks (user_id, share_id, name, description, internal_notes, external_notes, is_private, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, share_id, name, description, internal_notes, external_notes, is_private, timestamp, timestamp),
    )
    deck_id = cursor.lastrowid
    for (card_id, variant), quantity in requested.items():
        conn.execute(
            """
            INSERT INTO deck_cards (deck_id, card_id, variant, quantity, added_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (deck_id, card_id, variant, quantity, timestamp),
        )
    conn.commit()
    return {"ok": True, "deck": deck_detail(conn, user_id, deck_id), "imported": len(requested)}


def shared_deck(conn, share_id, viewer_user_id=None):
    deck = conn.execute(
        """
        SELECT d.id, d.user_id, d.name, d.share_id,
               COALESCE(d.is_private, 0) AS is_private,
               COALESCE(u.name, u.email, 'Arcane Ledger user') AS owner_name,
               u.email AS owner_email, u.role AS owner_role, u.subscription_status AS owner_subscription_status
        FROM decks d
        LEFT JOIN users u ON u.id = d.user_id
        WHERE d.share_id = ?
        """,
        (share_id,),
    ).fetchone()
    if not deck:
        raise KeyError("Shared deck not found")
    payload = deck_detail(conn, deck["user_id"], deck["id"])
    payload.pop("internal_notes", None)
    payload["readonly"] = True
    payload["owner_user_id"] = deck["user_id"]
    payload["owner_name"] = deck["owner_name"]
    owner_role = effective_user_role({
        "email": deck["owner_email"],
        "role": deck["owner_role"],
        "subscription_status": deck["owner_subscription_status"],
    })
    payload["owner_role"] = owner_role
    payload["owner_is_pro"] = owner_role in {"admin", "contributor", "pro"}
    return payload


def shared_deck_for_viewer(conn, share_id, viewer_user_id=None):
    payload = shared_deck(conn, share_id, viewer_user_id)
    is_owner = bool(viewer_user_id and int(viewer_user_id) == int(payload.get("owner_user_id") or 0))
    payload["viewer_is_owner"] = is_owner
    payload["can_favorite"] = bool(viewer_user_id and not is_owner)
    payload["can_import"] = bool(viewer_user_id and not is_owner)
    payload["favorite_deck"] = False
    if viewer_user_id and not is_owner:
        payload["favorite_deck"] = bool(conn.execute(
            "SELECT 1 FROM favorite_decks WHERE user_id = ? AND share_id = ?",
            (viewer_user_id, share_id),
        ).fetchone())
    return payload


def deck_share_url(deck):
    share_id = deck.get("share_id") if isinstance(deck, dict) else deck["share_id"]
    return f"{verification_base_url()}/decks/{urllib.parse.quote(share_id)}"


def store_share_url(store_share_id):
    return f"{verification_base_url()}/stores/{urllib.parse.quote(store_share_id)}"


def favorites_share_url(store_share_id):
    return f"{verification_base_url()}/favorites/{urllib.parse.quote(store_share_id)}"


def public_display_name(user_row, fallback_prefix="Seller"):
    name = (user_row["name"] if user_row and "name" in user_row.keys() else "") or ""
    share_id = (user_row["store_share_id"] if user_row and "store_share_id" in user_row.keys() else "") or ""
    if name and "@" not in name:
        return name
    suffix = share_id[:6] if share_id else "user"
    return f"{fallback_prefix} {suffix}"


def unique_import_wishlist_name(conn, user_id, base):
    clean_base = re.sub(r"\s+", " ", (base or "Imported Deck").strip()) or "Imported Deck"
    clean_base = clean_base[:30].strip() or "Imported Deck"
    candidate = clean_base
    suffix = 2
    while cross_entity_name_exists(conn, user_id, candidate):
        suffix_text = f" {suffix}"
        candidate = f"{clean_base[:30 - len(suffix_text)].rstrip()}{suffix_text}"
        suffix += 1
    return candidate


def list_favorite_decks(conn, user_id):
    rows = conn.execute(
        """
        SELECT fd.share_id, fd.deck_name AS name, fd.deck_url, fd.owner_name,
               fd.card_count, fd.created_at, fd.updated_at,
               d.id AS deck_id,
               u.email AS owner_email, u.role AS owner_role, u.subscription_status AS owner_subscription_status,
               CASE WHEN d.id IS NULL THEN 1 ELSE 0 END AS unavailable
        FROM favorite_decks fd
        LEFT JOIN decks d ON d.share_id = fd.share_id
        LEFT JOIN users u ON u.id = d.user_id
        WHERE fd.user_id = ?
        ORDER BY fd.updated_at DESC, fd.deck_name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    decks = rows_to_dicts(rows)
    for deck in decks:
        owner_role = effective_user_role({
            "email": deck.get("owner_email"),
            "role": deck.get("owner_role"),
            "subscription_status": deck.get("owner_subscription_status"),
        })
        deck["owner_role"] = owner_role
        deck["owner_is_pro"] = owner_role in {"admin", "contributor", "pro"}
    return decks


def sale_listing_key(seller_user_id, card_id, variant, condition):
    return f"{seller_user_id}:{card_id}:{variant or 'Normal'}:{card_condition(condition)}"


def purge_store_listing_favorites(conn, seller_user_id, card_id, variant=None, condition=None):
    params = [seller_user_id, card_id]
    where = "seller_user_id = ? AND card_id = ?"
    if variant is not None:
        where += " AND variant = ?"
        params.append(variant or "Normal")
    if condition is not None:
        where += " AND card_condition = ?"
        params.append(card_condition(condition))
    conn.execute(f"DELETE FROM favorite_store_listings WHERE {where}", params)


def list_favorite_store_listings(conn, user_id):
    price_expr = (
        "CASE "
        "WHEN lower(coalesce(fav.variant, '')) LIKE '%etched%' AND c.current_usd_etched > 0 THEN c.current_usd_etched "
        "WHEN lower(coalesce(fav.variant, '')) LIKE '%foil%' AND c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd > 0 THEN c.current_usd "
        "WHEN c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd_etched > 0 THEN c.current_usd_etched "
        "ELSE 0 END"
    )
    rows = conn.execute(
        f"""
        SELECT fav.seller_user_id, fav.card_id, fav.variant, fav.card_condition,
               fav.created_at, fav.updated_at,
               c.*,
               sale.quantity AS sale_quantity,
               sale.asking_price,
               sale.quantity AS quantity,
               sale.quantity * sale.asking_price AS sale_asking_total,
               sale.quantity * sale.asking_price AS owned_value,
               ({price_expr}) AS display_price,
               sale.quantity * ({price_expr}) AS market_total,
               COALESCE(u.name, '') AS seller_name,
               COALESCE(u.email, '') AS seller_email,
               COALESCE(u.store_share_id, '') AS store_share_id,
               u.role AS seller_role,
               u.subscription_status AS seller_subscription_status
        FROM favorite_store_listings fav
        JOIN card_sales sale
          ON sale.user_id = fav.seller_user_id
         AND sale.card_id = fav.card_id
         AND sale.variant = fav.variant
         AND sale.card_condition = fav.card_condition
         AND COALESCE(sale.quantity, 0) > 0
        JOIN cards c ON c.scryfall_id = fav.card_id
        JOIN users u ON u.id = fav.seller_user_id
        WHERE fav.user_id = ?
        ORDER BY fav.updated_at DESC, c.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    listings = []
    for row in rows:
        listing = with_value_aliases(dict(row))
        if not listing.get("store_share_id"):
            listing["store_share_id"] = new_store_share_id(conn)
            conn.execute("UPDATE users SET store_share_id = ? WHERE id = ?", (listing["store_share_id"], listing["seller_user_id"]))
        listing["seller_name"] = public_display_name(
            {
                "name": listing.get("seller_name") or listing.get("seller_email") or "",
                "email": listing.get("seller_email") or "",
                "store_share_id": listing.get("store_share_id") or "",
            },
            "Seller",
        )
        seller_role = effective_user_role({
            "email": listing.get("seller_email"),
            "role": listing.get("seller_role"),
            "subscription_status": listing.get("seller_subscription_status"),
        })
        listing["seller_role"] = seller_role
        listing["seller_is_pro"] = seller_role in {"admin", "contributor", "pro"}
        listing["store_url"] = store_share_url(listing["store_share_id"])
        listing["favorite_store"] = True
        listing["listing_key"] = sale_listing_key(
            listing["seller_user_id"],
            listing["card_id"],
            listing["variant"],
            listing["card_condition"],
        )
        listings.append(listing)
    conn.commit()
    return listings


def shared_favorites(conn, store_share_id):
    owner = conn.execute(
        """
        SELECT id, name, email, store_share_id
        FROM users
        WHERE store_share_id = ?
        """,
        (store_share_id,),
    ).fetchone()
    if not owner:
        raise KeyError("Shared favorites not found.")
    return {
        "cards": list_cards(conn, "owned=owned&favorite=1&sort=value&limit=5000", owner["id"]),
        "decks": list_favorite_decks(conn, owner["id"]),
        "store": list_favorite_store_listings(conn, owner["id"]),
        "readonly": True,
        "owner_name": public_display_name(owner, "Collector"),
        "share_id": owner["store_share_id"],
        "share_url": favorites_share_url(owner["store_share_id"]),
    }


def favorites_email_text(payload, share_url, sender_name):
    lines = [
        f"{sender_name or 'An Arcane Ledger user'} shared Arcane Ledger favorites with you.",
        share_url,
        "",
        "Favorite cards:",
    ]
    for card in payload.get("cards") or []:
        set_text = " ".join(part for part in [
            card.get("set_name") or "",
            f"#{card.get('collector_number')}" if card.get("collector_number") else "",
            card.get("variant") or "",
        ] if part).strip()
        lines.append(f"- {card_email_title(card)} ({set_text})")
    if not (payload.get("cards") or []):
        lines.append("- No favorite cards.")
    lines.extend(["", "Favorite decks:"])
    for deck in payload.get("decks") or []:
        lines.append(f"- {deck.get('name') or 'Deck'} by {deck.get('owner_name') or 'Arcane Ledger user'}")
    if not (payload.get("decks") or []):
        lines.append("- No favorite decks.")
    lines.extend(["", "Favorite store listings:"])
    for listing in payload.get("store") or []:
        lines.append(f"- {card_email_title(listing)} from {listing.get('seller_name') or 'Seller'}")
    if not (payload.get("store") or []):
        lines.append("- No favorite store listings.")
    return "\n".join(lines)


def favorites_email_html(payload, share_url, sender_name):
    safe_sender = html_lib.escape(sender_name or "An Arcane Ledger user")
    safe_url = html_lib.escape(share_url)

    def list_items(items, formatter, empty_text):
        if not items:
            return f"<li style=\"padding:6px 0;color:#586661;\">{html_lib.escape(empty_text)}</li>"
        return "\n".join(f"<li style=\"padding:6px 0;\">{formatter(item)}</li>" for item in items)

    card_items = list_items(
        payload.get("cards") or [],
        lambda card: f"<strong>{html_lib.escape(card_email_title(card))}</strong> <span style=\"color:#586661;\">{html_lib.escape(card.get('set_name') or '')}</span>",
        "No favorite cards.",
    )
    deck_items = list_items(
        payload.get("decks") or [],
        lambda deck: f"<strong>{html_lib.escape(deck.get('name') or 'Deck')}</strong> <span style=\"color:#586661;\">by {html_lib.escape(deck.get('owner_name') or 'Arcane Ledger user')}</span>",
        "No favorite decks.",
    )
    store_items = list_items(
        payload.get("store") or [],
        lambda listing: f"<strong>{html_lib.escape(card_email_title(listing))}</strong> <span style=\"color:#586661;\">from {html_lib.escape(listing.get('seller_name') or 'Seller')}</span>",
        "No favorite store listings.",
    )
    return f"""
    <!doctype html>
    <html>
      <body style="margin:0;background:#f4f7f5;color:#111816;font-family:Arial,Helvetica,sans-serif;">
        <div style="max-width:760px;margin:0 auto;padding:24px;">
          <h1 style="margin:0 0 8px;font-size:28px;line-height:1.1;">Shared Favorites</h1>
          <p style="margin:0 0 16px;color:#586661;">{safe_sender} shared Arcane Ledger favorites with you.</p>
          <p style="margin:0 0 20px;">
            <a href="{safe_url}" style="display:inline-block;background:#111816;color:#ffffff;text-decoration:none;padding:10px 14px;border-radius:8px;font-weight:700;">Open favorites</a>
          </p>
          <p style="margin:0 0 16px;color:#303936;word-break:break-all;">{safe_url}</p>
          <section style="background:#ffffff;border:1px solid #d7dedb;border-radius:8px;padding:16px;margin-bottom:14px;">
            <h2 style="margin:0 0 8px;font-size:18px;">Cards</h2>
            <ul style="margin:0;padding-left:20px;">{card_items}</ul>
          </section>
          <section style="background:#ffffff;border:1px solid #d7dedb;border-radius:8px;padding:16px;margin-bottom:14px;">
            <h2 style="margin:0 0 8px;font-size:18px;">Decks</h2>
            <ul style="margin:0;padding-left:20px;">{deck_items}</ul>
          </section>
          <section style="background:#ffffff;border:1px solid #d7dedb;border-radius:8px;padding:16px;">
            <h2 style="margin:0 0 8px;font-size:18px;">Store</h2>
            <ul style="margin:0;padding-left:20px;">{store_items}</ul>
          </section>
        </div>
      </body>
    </html>
    """


def email_favorites(conn, user, store_share_id, payload):
    recipient = validate_email(payload.get("email"))
    if not store_share_id or store_share_id != (user["store_share_id"] if "store_share_id" in user.keys() else ""):
        raise ValueError("You can only email your own favorites list.")
    favorites = shared_favorites(conn, store_share_id)
    share_url = favorites_share_url(store_share_id)
    sender_name = user["name"] or user["email"]
    subject = f"Arcane Ledger: {sender_name} sharing favorites"
    result = send_email(
        recipient,
        subject,
        text=favorites_email_text(favorites, share_url, sender_name),
        html=favorites_email_html(favorites, share_url, sender_name),
        tags=["arcaneledger", "favorites-share"],
    )
    return {"ok": True, "email": recipient, "provider": result.get("provider"), "status": result.get("status")}


def update_favorite_store_listing(conn, user_id, payload):
    seller_user_id = int(money(payload.get("seller_user_id"), fallback=0))
    card_id = payload.get("card_id") or payload.get("scryfall_id")
    variant = payload.get("variant") or "Normal"
    condition = card_condition(payload.get("card_condition"))
    if not seller_user_id or not card_id:
        raise ValueError("Choose a store listing.")
    if seller_user_id == user_id:
        raise ValueError("This is already your store listing.")
    sale = conn.execute(
        """
        SELECT quantity
        FROM card_sales
        WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ? AND COALESCE(quantity, 0) > 0
        """,
        (seller_user_id, card_id, variant, condition),
    ).fetchone()
    if not sale:
        purge_store_listing_favorites(conn, seller_user_id, card_id, variant, condition)
        conn.commit()
        raise KeyError("Store listing is no longer available.")
    favorite = bool(payload.get("favorite"))
    if favorite:
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO favorite_store_listings (
                user_id, seller_user_id, card_id, variant, card_condition, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, seller_user_id, card_id, variant, card_condition) DO UPDATE SET
                updated_at = excluded.updated_at
            """,
            (user_id, seller_user_id, card_id, variant, condition, timestamp, timestamp),
        )
    else:
        conn.execute(
            """
            DELETE FROM favorite_store_listings
            WHERE user_id = ? AND seller_user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
            """,
            (user_id, seller_user_id, card_id, variant, condition),
        )
    conn.commit()
    return {"ok": True, "favorite": favorite}


def public_deck_preview_cards(conn, deck_id, viewer_user_id=None, limit=10):
    price_expr = current_price_sql("c")
    rows = conn.execute(
        f"""
        SELECT c.scryfall_id, c.name, c.flavor_name,
               c.set_name, c.collector_number, c.type_line, c.type_category,
               c.colors, c.color_identity, c.image_small, c.image_normal,
               c.scryfall_uri, dc.variant, dc.quantity AS deck_quantity,
               COALESCE(col.quantity, 0) AS quantity,
               ({price_expr}) AS display_price
        FROM deck_cards dc
        JOIN cards c ON c.scryfall_id = dc.card_id
        LEFT JOIN collection col
          ON col.user_id = ?
         AND col.card_id = dc.card_id
         AND col.variant = dc.variant
        WHERE dc.deck_id = ?
        ORDER BY dc.quantity DESC, c.name COLLATE NOCASE, dc.variant
        LIMIT ?
        """,
        (viewer_user_id or -1, deck_id, int(limit or 10)),
    ).fetchall()
    return rows_to_dicts(rows)


def list_public_decks(conn, viewer_user_id=None):
    rows = conn.execute(
        """
        SELECT d.id, d.share_id, d.user_id, d.name,
               COALESCE(d.description, '') AS description,
               COALESCE(d.external_notes, '') AS external_notes,
               COALESCE(u.name, u.email, 'Arcane Ledger user') AS owner_name,
               u.email AS owner_email, u.role AS owner_role, u.subscription_status AS owner_subscription_status,
               d.created_at, d.updated_at,
               COALESCE(SUM(dc.quantity), 0) AS card_count,
               COUNT(dc.card_id) AS unique_card_count,
               (
                   SELECT GROUP_CONCAT(image, '|||')
                   FROM (
                       SELECT DISTINCT COALESCE(NULLIF(c2.image_normal, ''), NULLIF(c2.image_small, '')) AS image
                       FROM deck_cards dc2
                       JOIN cards c2 ON c2.scryfall_id = dc2.card_id
                       WHERE dc2.deck_id = d.id
                         AND COALESCE(NULLIF(c2.image_normal, ''), NULLIF(c2.image_small, '')) IS NOT NULL
                       ORDER BY RANDOM()
                       LIMIT 5
                   )
               ) AS preview_images
        FROM decks d
        LEFT JOIN users u ON u.id = d.user_id
        LEFT JOIN deck_cards dc ON dc.deck_id = d.id
        WHERE COALESCE(d.is_private, 0) = 0
        GROUP BY d.id
        ORDER BY d.updated_at DESC, d.name COLLATE NOCASE
        LIMIT 200
        """
    ).fetchall()
    decks = rows_to_dicts(rows)
    for deck in decks:
        owner_role = effective_user_role({
            "email": deck.get("owner_email"),
            "role": deck.get("owner_role"),
            "subscription_status": deck.get("owner_subscription_status"),
        })
        deck["owner_role"] = owner_role
        deck["owner_is_pro"] = owner_role in {"admin", "contributor", "pro"}
        deck["preview_images"] = [image for image in (deck.get("preview_images") or "").split("|||") if image][:5]
        deck["cards"] = public_deck_preview_cards(conn, deck["id"], viewer_user_id, 10)
        deck["viewer_is_owner"] = bool(viewer_user_id and int(viewer_user_id) == int(deck.get("user_id") or 0))
        deck["can_favorite"] = bool(viewer_user_id and not deck["viewer_is_owner"])
        deck["can_import"] = bool(viewer_user_id and not deck["viewer_is_owner"])
        deck["favorite_deck"] = False
        if viewer_user_id and not deck["viewer_is_owner"]:
            deck["favorite_deck"] = bool(conn.execute(
                "SELECT 1 FROM favorite_decks WHERE user_id = ? AND share_id = ?",
                (viewer_user_id, deck["share_id"]),
            ).fetchone())
        deck["deck_url"] = deck_share_url(deck)
    return decks


def update_favorite_deck(conn, user_id, share_id, payload):
    deck = shared_deck(conn, share_id)
    if int(deck.get("owner_user_id") or 0) == int(user_id):
        raise ValueError("This is already your deck.")
    favorite = bool(payload.get("favorite"))
    if favorite:
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO favorite_decks (user_id, share_id, deck_name, deck_url, owner_name, card_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, share_id) DO UPDATE SET
                deck_name = excluded.deck_name,
                deck_url = excluded.deck_url,
                owner_name = excluded.owner_name,
                card_count = excluded.card_count,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                share_id,
                deck.get("name") or "Deck",
                deck_share_url(deck),
                deck.get("owner_name") or "Arcane Ledger user",
                int(deck.get("card_count") or 0),
                timestamp,
                timestamp,
            ),
        )
    else:
        conn.execute("DELETE FROM favorite_decks WHERE user_id = ? AND share_id = ?", (user_id, share_id))
    conn.commit()
    return {"ok": True, "favorite": favorite, "deck": shared_deck_for_viewer(conn, share_id, user_id)}


def email_shared_deck(conn, user, share_id, payload):
    recipient = validate_email(payload.get("email"))
    deck = shared_deck_for_viewer(conn, share_id, user["id"])
    share_url = deck_share_url(deck)
    sender_name = user["name"] or user["email"]
    subject = f"Arcane Ledger: {sender_name} sharing deck: {deck['name']}"
    result = send_email(
        recipient,
        subject,
        text=shared_list_email_text(deck, share_url, sender_name, "deck"),
        html=shared_list_email_html(deck, share_url, sender_name, "deck"),
        tags=["arcaneledger", "deck-share"],
    )
    return {"ok": True, "email": recipient, "provider": result.get("provider"), "status": result.get("status")}


def import_shared_deck_to_deck(conn, user_id, share_id, payload=None):
    deck = shared_deck(conn, share_id)
    if int(deck.get("owner_user_id") or 0) == int(user_id):
        raise ValueError("This deck is already in your account.")
    payload = payload or {}
    name = validate_user_content_name(payload.get("name") or deck.get("name") or "Imported Deck", "Deck name", 20)
    replace = bool(payload.get("replace"))
    existing_deck = conn.execute(
        "SELECT id FROM decks WHERE user_id = ? AND lower(name) = lower(?)",
        (user_id, name),
    ).fetchone()
    if existing_deck and not replace:
        return {"ok": False, "duplicate": True, "name": name}
    if not existing_deck and cross_entity_name_exists(conn, user_id, name):
        raise ValueError("Deck name must be unique across your decks, containers, and wishlists.")
    if not existing_deck:
        enforce_role_limit(conn, user_id, "decks", "decks", "decks")
    timestamp = now_iso()
    imported = 0
    if existing_deck:
        deck_id = existing_deck["id"]
        conn.execute(
            """
            UPDATE decks
            SET description = ?, internal_notes = '', external_notes = '', updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (clean_deck_text(deck.get("description"), 500, "Description"), timestamp, deck_id, user_id),
        )
        conn.execute("DELETE FROM deck_cards WHERE deck_id = ?", (deck_id,))
    else:
        cursor = conn.execute(
            """
            INSERT INTO decks (user_id, share_id, name, description, internal_notes, external_notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, '', '', ?, ?)
            """,
            (
                user_id,
                new_deck_share_id(conn),
                name,
                clean_deck_text(deck.get("description"), 500, "Description"),
                timestamp,
                timestamp,
            ),
        )
        deck_id = cursor.lastrowid
    for card in deck.get("cards") or []:
        card_id = card.get("scryfall_id") or card.get("card_id")
        if not card_id:
            continue
        variant = card.get("variant") or "Normal"
        conn.execute(
            """
            INSERT INTO deck_cards (deck_id, card_id, variant, quantity, added_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (deck_id, card_id, variant, max(1, int(card.get("deck_quantity") or card.get("quantity") or 1)), timestamp),
        )
        imported += 1
    conn.commit()
    return {
        "ok": True,
        "deck": deck_detail(conn, user_id, deck_id),
        "imported": imported,
        "replaced": bool(existing_deck),
    }


def add_cards_to_deck(conn, user_id, deck_id, payload):
    deck = conn.execute("SELECT id FROM decks WHERE id = ? AND user_id = ?", (deck_id, user_id)).fetchone()
    if not deck:
        raise KeyError("Deck not found")
    cards = payload.get("cards") or []
    if not isinstance(cards, list) or not cards:
        raise ValueError("Choose at least one card.")

    timestamp = now_iso()
    added = 0
    for item in cards:
        card_id = item.get("card_id") or item.get("scryfall_id")
        variant = item.get("variant") or "Normal"
        quantity = max(1, int(money(item.get("quantity"), fallback=1)))
        if not card_id:
            continue
        if not conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone():
            cache_card_by_id(conn, card_id)
        conn.execute(
            """
            INSERT INTO deck_cards (deck_id, card_id, variant, quantity, added_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(deck_id, card_id, variant) DO UPDATE SET
                quantity = deck_cards.quantity + excluded.quantity,
                added_at = excluded.added_at
            """,
            (deck_id, card_id, variant, quantity, timestamp),
        )
        added += quantity
    conn.execute("UPDATE decks SET updated_at = ? WHERE id = ?", (timestamp, deck_id))
    conn.commit()
    return {"ok": True, "added": added, "deck_id": deck_id}


def remove_card_from_deck(conn, user_id, deck_id, payload):
    deck = conn.execute("SELECT id FROM decks WHERE id = ? AND user_id = ?", (deck_id, user_id)).fetchone()
    if not deck:
        raise KeyError("Deck not found")
    card_id = payload.get("card_id") or payload.get("scryfall_id")
    variant = payload.get("variant") or "Normal"
    if not card_id:
        raise ValueError("Card is required.")
    cursor = conn.execute(
        "DELETE FROM deck_cards WHERE deck_id = ? AND card_id = ? AND variant = ?",
        (deck_id, card_id, variant),
    )
    conn.execute("UPDATE decks SET updated_at = ? WHERE id = ?", (now_iso(), deck_id))
    conn.commit()
    return {"ok": True, "removed": cursor.rowcount}


def delete_deck(conn, user_id, deck_id):
    deck = conn.execute("SELECT share_id FROM decks WHERE id = ? AND user_id = ?", (deck_id, user_id)).fetchone()
    if not deck:
        raise KeyError("Deck not found")
    cursor = conn.execute("DELETE FROM decks WHERE id = ? AND user_id = ?", (deck_id, user_id))
    if cursor.rowcount == 0:
        raise KeyError("Deck not found")
    if deck["share_id"]:
        conn.execute("DELETE FROM favorite_decks WHERE share_id = ?", (deck["share_id"],))
    conn.commit()
    return {"ok": True, "deleted": deck_id}


def allocated_quantity(conn, user_id, card_id, variant, condition=None, exclude_container_id=None):
    params = [user_id, card_id, variant]
    condition_sql = ""
    if condition is not None:
        condition_sql = " AND COALESCE(NULLIF(cc.card_condition, ''), ?) = ?"
        params.extend([DEFAULT_CARD_CONDITION, card_condition(condition)])
    exclude_sql = ""
    if exclude_container_id is not None:
        exclude_sql = " AND cc.container_id != ?"
        params.append(exclude_container_id)
    row = conn.execute(
        f"""
        SELECT COALESCE(SUM(quantity), 0) AS quantity
        FROM container_cards cc
        JOIN containers c ON c.id = cc.container_id
        WHERE c.user_id = ? AND cc.card_id = ? AND cc.variant = ?{condition_sql}{exclude_sql}
        """,
        params,
    ).fetchone()
    return int(row["quantity"] or 0)


def deck_allocated_quantity(conn, user_id, card_id, variant):
    row = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity
        FROM deck_cards dc
        JOIN decks d ON d.id = dc.deck_id
        WHERE d.user_id = ? AND dc.card_id = ? AND COALESCE(NULLIF(dc.variant, ''), 'Normal') = ?
        """,
        (user_id, card_id, variant or "Normal"),
    ).fetchone()
    return int(row["quantity"] or 0)


def owned_quantity(conn, user_id, card_id, variant):
    row = conn.execute(
        "SELECT COALESCE(quantity, 0) AS quantity FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?",
        (user_id, card_id, variant),
    ).fetchone()
    return int(row["quantity"] or 0) if row else 0


def list_containers(conn, user_id):
    price_expr = (
        "CASE "
        "WHEN lower(coalesce(cc.variant, '')) LIKE '%etched%' AND c.current_usd_etched > 0 THEN c.current_usd_etched "
        "WHEN lower(coalesce(cc.variant, '')) LIKE '%foil%' AND c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd > 0 THEN c.current_usd "
        "WHEN c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd_etched > 0 THEN c.current_usd_etched "
        "ELSE 0 END"
    )
    rows = conn.execute(
        f"""
        SELECT ct.id, ct.share_id, ct.name, COALESCE(ct.storage_type, 'other') AS storage_type,
               COALESCE(ct.strict_unique, 0) AS strict_unique,
               COALESCE(ct.capacity, 0) AS capacity,
               ct.location, ct.notes, ct.created_at, ct.updated_at,
               COUNT(cc.card_id) AS card_count,
               COALESCE(SUM(cc.quantity), 0) AS stored_quantity,
               COALESCE(SUM(cc.quantity * ({price_expr})), 0) AS container_value
        FROM containers ct
        LEFT JOIN container_cards cc ON cc.container_id = ct.id
        LEFT JOIN cards c ON c.scryfall_id = cc.card_id
        WHERE ct.user_id = ?
        GROUP BY ct.id
        ORDER BY ct.updated_at DESC, ct.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    containers = rows_to_dicts(rows)
    set_rows = conn.execute(
        """
        SELECT cc.container_id, lower(c.set_code) AS set_code
        FROM container_cards cc
        JOIN containers ct ON ct.id = cc.container_id
        JOIN cards c ON c.scryfall_id = cc.card_id
        WHERE ct.user_id = ? AND COALESCE(cc.quantity, 0) > 0
        GROUP BY cc.container_id, lower(c.set_code)
        ORDER BY lower(c.set_code) COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    set_codes_by_container = {}
    for row in set_rows:
        set_codes_by_container.setdefault(int(row["container_id"]), []).append((row["set_code"] or "").upper())
    for container in containers:
        capacity = int(container.get("capacity") or 0)
        stored = int(container.get("stored_quantity") or 0)
        container["set_codes"] = set_codes_by_container.get(int(container.get("id") or 0), [])
        container["remaining_capacity"] = max(0, capacity - stored) if capacity > 0 else None
        container["fill_percent"] = round(min(100, (stored / capacity) * 100), 1) if capacity > 0 else None
    return containers


def container_storage_stats(conn, user_id, container_id):
    price_expr = (
        "CASE "
        "WHEN lower(coalesce(cc.variant, '')) LIKE '%etched%' AND c.current_usd_etched > 0 THEN c.current_usd_etched "
        "WHEN lower(coalesce(cc.variant, '')) LIKE '%foil%' AND c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd > 0 THEN c.current_usd "
        "WHEN c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd_etched > 0 THEN c.current_usd_etched "
        "ELSE 0 END"
    )
    row = conn.execute(
        f"""
        SELECT COALESCE(ct.capacity, 0) AS capacity,
               COALESCE(SUM(cc.quantity), 0) AS stored_quantity,
               COUNT(cc.card_id) AS card_count,
               COALESCE(SUM(cc.quantity * ({price_expr})), 0) AS container_value
        FROM containers ct
        LEFT JOIN container_cards cc ON cc.container_id = ct.id
        LEFT JOIN cards c ON c.scryfall_id = cc.card_id
        WHERE ct.id = ? AND ct.user_id = ?
        GROUP BY ct.id
        """,
        (container_id, user_id),
    ).fetchone()
    if not row:
        return {"capacity": 0, "stored_quantity": 0, "card_count": 0, "container_value": 0, "remaining_capacity": None, "fill_percent": None}
    stats = dict(row)
    capacity = int(stats.get("capacity") or 0)
    stored = int(stats.get("stored_quantity") or 0)
    stats["remaining_capacity"] = max(0, capacity - stored) if capacity > 0 else None
    stats["fill_percent"] = round(min(100, (stored / capacity) * 100), 1) if capacity > 0 else None
    return stats


def clean_limited_text(payload, key, label, limit, required=False):
    value = re.sub(r"\s+", " ", (payload.get(key) or "").strip())
    if required and not value:
        raise ValueError(f"{label} is required.")
    if len(value) > limit:
        raise ValueError(f"{label} must be {limit} characters or fewer.")
    return value


def clean_container_type(value):
    storage_type = (value or DEFAULT_CONTAINER_TYPE).strip().lower()
    return storage_type if storage_type in CONTAINER_TYPES else DEFAULT_CONTAINER_TYPE


def clean_container_capacity(value):
    try:
        capacity = int(value)
    except (TypeError, ValueError):
        capacity = 0
    if capacity < 1:
        raise ValueError("Container capacity must be at least 1 card.")
    if capacity > 100000:
        raise ValueError("Container capacity must be 100,000 cards or fewer.")
    return capacity


def container_strict_slot_label(row):
    if not row:
        return "that collector number"
    return f"{(row['set_code'] or '').upper()} #{row['collector_number'] or '?'}"


def validate_container_strict_existing(conn, container_id, container_name):
    duplicate = conn.execute(
        """
        SELECT c.set_code, c.collector_number, COALESCE(SUM(cc.quantity), 0) AS quantity
        FROM container_cards cc
        JOIN cards c ON c.scryfall_id = cc.card_id
        WHERE cc.container_id = ?
        GROUP BY c.set_code, c.collector_number
        HAVING COALESCE(SUM(cc.quantity), 0) > 1
        ORDER BY c.set_code COLLATE NOCASE, c.collector_number COLLATE NOCASE
        LIMIT 1
        """,
        (container_id,),
    ).fetchone()
    if duplicate:
        raise ValueError(
            f"{container_name} already has {int(duplicate['quantity'] or 0)} cards for {container_strict_slot_label(duplicate)}. "
            "Remove extras before enabling Strict."
        )


def validate_container_strict_additions(conn, container_id, additions, exclude_card_id=None):
    additions = [item for item in additions or [] if int(item.get("quantity") or 0) > 0 and item.get("card_id")]
    if not additions:
        return
    container = conn.execute(
        "SELECT id, name, COALESCE(strict_unique, 0) AS strict_unique FROM containers WHERE id = ?",
        (container_id,),
    ).fetchone()
    if not container or not int(container["strict_unique"] or 0):
        return
    existing_params = [container_id]
    exclude_sql = ""
    if exclude_card_id:
        exclude_sql = " AND cc.card_id != ?"
        existing_params.append(exclude_card_id)
    existing_rows = conn.execute(
        f"""
        SELECT c.set_code, c.collector_number, COALESCE(SUM(cc.quantity), 0) AS quantity
        FROM container_cards cc
        JOIN cards c ON c.scryfall_id = cc.card_id
        WHERE cc.container_id = ?{exclude_sql}
        GROUP BY c.set_code, c.collector_number
        """,
        existing_params,
    ).fetchall()
    slot_counts = {
        (row["set_code"] or "", row["collector_number"] or ""): int(row["quantity"] or 0)
        for row in existing_rows
    }
    card_ids = sorted({item["card_id"] for item in additions})
    placeholders = ", ".join("?" for _ in card_ids)
    card_rows = conn.execute(
        f"""
        SELECT scryfall_id, set_code, collector_number
        FROM cards
        WHERE scryfall_id IN ({placeholders})
        """,
        card_ids,
    ).fetchall()
    cards = {row["scryfall_id"]: row for row in card_rows}
    for item in additions:
        card = cards.get(item["card_id"])
        if not card:
            continue
        key = (card["set_code"] or "", card["collector_number"] or "")
        slot_counts[key] = slot_counts.get(key, 0) + int(item.get("quantity") or 0)
        if slot_counts[key] > 1:
            raise ValueError(
                f"{container['name']} has Strict enabled. Only 1 card is allowed for {container_strict_slot_label(card)}."
            )


def container_strict_existing_quantity(conn, container_id, card_id):
    row = conn.execute(
        """
        SELECT c.set_code, c.collector_number,
               (
                 SELECT COALESCE(SUM(cc.quantity), 0)
                 FROM container_cards cc
                 JOIN cards existing ON existing.scryfall_id = cc.card_id
                 WHERE cc.container_id = ?
                   AND existing.set_code = c.set_code
                   AND existing.collector_number = c.collector_number
               ) AS quantity
        FROM cards c
        WHERE c.scryfall_id = ?
        """,
        (container_id, card_id),
    ).fetchone()
    if not row:
        return 0, None
    return int(row["quantity"] or 0), row


def create_container(conn, user_id, payload):
    name = validate_user_content_name(payload.get("name"), "Container name", 30)
    if name_exists(conn, "containers", name, user_id):
        raise ValueError("Container name must be unique across your decks, containers, and wishlists.")
    enforce_role_limit(conn, user_id, "containers", "containers", "containers")
    storage_type = clean_container_type(payload.get("storage_type"))
    capacity = clean_container_capacity(payload.get("capacity"))
    strict_unique = bool_int(payload.get("strict_unique"))
    location = clean_limited_text(payload, "location", "Container location", 30)
    notes = (payload.get("notes") or "").strip()
    if len(notes) > 500:
        raise ValueError("Notes / Description must be 500 characters or fewer.")
    timestamp = now_iso()
    share_id = new_container_share_id(conn)
    cursor = conn.execute(
        """
        INSERT INTO containers (user_id, share_id, name, storage_type, capacity, strict_unique, location, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, share_id, name, storage_type, capacity, strict_unique, location, notes, timestamp, timestamp),
    )
    conn.commit()
    return {
        "ok": True,
        "container": {
            "id": cursor.lastrowid,
            "share_id": share_id,
            "name": name,
            "storage_type": storage_type,
            "capacity": capacity,
            "strict_unique": bool(strict_unique),
            "location": location,
            "notes": notes,
            "created_at": timestamp,
            "updated_at": timestamp,
            "card_count": 0,
            "stored_quantity": 0,
            "container_value": 0,
            "remaining_capacity": capacity,
            "fill_percent": 0,
        },
    }


def update_container(conn, user_id, container_id, payload):
    exists = conn.execute("SELECT id FROM containers WHERE id = ? AND user_id = ?", (container_id, user_id)).fetchone()
    if not exists:
        raise KeyError("Container not found")
    name = validate_user_content_name(payload.get("name"), "Container name", 30)
    if name_exists(conn, "containers", name, user_id, exclude_id=container_id):
        raise ValueError("Container name must be unique across your decks, containers, and wishlists.")
    storage_type = clean_container_type(payload.get("storage_type"))
    capacity = clean_container_capacity(payload.get("capacity"))
    strict_unique = bool_int(payload.get("strict_unique"))
    stored = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS stored_quantity
        FROM container_cards
        WHERE container_id = ?
        """,
        (container_id,),
    ).fetchone()
    stored_quantity = int(stored["stored_quantity"] or 0) if stored else 0
    if capacity < stored_quantity:
        raise ValueError(f"Container capacity cannot be lower than the {stored_quantity} cards currently stored.")
    if strict_unique:
        validate_container_strict_existing(conn, container_id, name)
    location = clean_limited_text(payload, "location", "Container location", 30)
    notes = (payload.get("notes") or "").strip()
    if len(notes) > 500:
        raise ValueError("Notes / Description must be 500 characters or fewer.")
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE containers
        SET name = ?, storage_type = ?, capacity = ?, strict_unique = ?, location = ?, notes = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (name, storage_type, capacity, strict_unique, location, notes, timestamp, container_id, user_id),
    )
    conn.commit()
    container = container_detail(conn, user_id, container_id)
    return {"ok": True, "container": container}


def container_cards(conn, user_id, container_id):
    price_expr = current_price_sql("c")
    rows = conn.execute(
        f"""
        SELECT c.*, cc.variant, COALESCE(NULLIF(cc.card_condition, ''), ?) AS card_condition,
               cc.quantity AS stored_quantity, cc.updated_at,
               COALESCE(col.quantity, 0) AS quantity,
               COALESCE(col.paid_price, 0.01) AS paid_price,
               COALESCE(col.graded, 0) AS graded,
               col.acquired_date,
               col.share_id,
               ({price_expr}) AS display_price,
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value
        FROM container_cards cc
        JOIN cards c ON c.scryfall_id = cc.card_id
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = cc.card_id AND col.variant = cc.variant
        WHERE cc.container_id = ?
        ORDER BY c.set_code COLLATE NOCASE,
                 CASE
                     WHEN c.collector_number GLOB '[0-9]*' THEN CAST(c.collector_number AS INTEGER)
                     ELSE 999999
                 END,
                 c.collector_number COLLATE NOCASE,
                 c.name COLLATE NOCASE,
                 cc.variant COLLATE NOCASE,
                 cc.card_condition COLLATE NOCASE
        """,
        (DEFAULT_CARD_CONDITION, user_id, container_id),
    ).fetchall()
    return rows_to_dicts(rows)


def container_detail(conn, user_id, container_id):
    container = conn.execute(
        """
        SELECT c.id, c.share_id, c.name, COALESCE(c.storage_type, 'other') AS storage_type,
               COALESCE(c.strict_unique, 0) AS strict_unique,
               COALESCE(c.capacity, 0) AS capacity,
               c.location, c.notes, c.created_at, c.updated_at,
               COUNT(cc.card_id) AS card_count,
               COALESCE(SUM(cc.quantity), 0) AS stored_quantity
        FROM containers c
        LEFT JOIN container_cards cc ON cc.container_id = c.id
        WHERE c.id = ? AND c.user_id = ?
        GROUP BY c.id
        """,
        (container_id, user_id),
    ).fetchone()
    if not container:
        raise KeyError("Container not found")
    payload = dict(container)
    payload.update(container_storage_stats(conn, user_id, container_id))
    payload["cards"] = container_cards(conn, user_id, container_id)
    return payload


def shared_container(conn, share_id):
    container = conn.execute("SELECT id, user_id FROM containers WHERE share_id = ?", (share_id,)).fetchone()
    if not container:
        raise KeyError("Shared container not found")
    payload = container_detail(conn, container["user_id"], container["id"])
    payload["readonly"] = True
    return payload


def container_share_url(container):
    share_id = container.get("share_id") if isinstance(container, dict) else container["share_id"]
    return f"{verification_base_url()}/containers/{urllib.parse.quote(share_id)}"


def add_cards_to_container(conn, user_id, container_id, payload):
    container = conn.execute(
        """
        SELECT ct.id, ct.name, COALESCE(ct.capacity, 0) AS capacity,
               COALESCE(ct.strict_unique, 0) AS strict_unique,
               COALESCE(SUM(cc.quantity), 0) AS stored_quantity
        FROM containers ct
        LEFT JOIN container_cards cc ON cc.container_id = ct.id
        WHERE ct.id = ? AND ct.user_id = ?
        GROUP BY ct.id
        """,
        (container_id, user_id),
    ).fetchone()
    if not container:
        raise KeyError("Container not found")
    cards = payload.get("cards") or []
    if not isinstance(cards, list) or not cards:
        raise ValueError("Choose at least one card.")

    timestamp = now_iso()
    added = 0
    capacity = int(container["capacity"] or 0)
    remaining_capacity = capacity - int(container["stored_quantity"] or 0) if capacity > 0 else None
    validate_container_strict_additions(conn, container_id, [
        {
            "card_id": item.get("card_id") or item.get("scryfall_id"),
            "quantity": max(0, int(item.get("quantity") or 0)),
        }
        for item in cards
    ])
    for item in cards:
        card_id = item.get("card_id") or item.get("scryfall_id")
        variant = item.get("variant") or "Normal"
        item_condition = card_condition(item.get("card_condition"))
        quantity = max(0, int(item.get("quantity") or 0))
        if not card_id or quantity <= 0:
            continue
        owned = condition_owned_quantity(conn, user_id, card_id, variant, item_condition)
        if owned <= 0:
            raise ValueError("Only owned cards can be stored in containers.")
        existing = conn.execute(
            """
            SELECT COALESCE(quantity, 0) AS quantity
            FROM container_cards
            WHERE container_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
            """,
            (container_id, card_id, variant, item_condition),
        ).fetchone()
        current_here = int(existing["quantity"] or 0) if existing else 0
        allocated_elsewhere = allocated_quantity(conn, user_id, card_id, variant, item_condition, exclude_container_id=container_id)
        max_here = owned - allocated_elsewhere
        if current_here + quantity > max_here:
            available = max(0, max_here - current_here)
            raise ValueError(f"Only {available} unassigned copy/copies are available for this card.")
        if remaining_capacity is not None and quantity > remaining_capacity:
            raise ValueError(f"{container['name']} only has space for {max(0, remaining_capacity)} more card/copy.")
        conn.execute(
            """
            INSERT INTO container_cards (container_id, card_id, variant, card_condition, quantity, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(container_id, card_id, variant, card_condition) DO UPDATE SET
                quantity = container_cards.quantity + excluded.quantity,
                updated_at = excluded.updated_at
            """,
            (container_id, card_id, variant, item_condition, quantity, timestamp),
        )
        added += quantity
        if remaining_capacity is not None:
            remaining_capacity -= quantity
    conn.execute("UPDATE containers SET updated_at = ? WHERE id = ?", (timestamp, container_id))
    conn.commit()
    return {"ok": True, "added": added, "container_id": container_id}


def update_card_container_allocations(conn, user_id, card_id, payload):
    card_id = (card_id or payload.get("card_id") or payload.get("scryfall_id") or "").strip()
    if not card_id:
        raise ValueError("Card is required.")
    containers = rows_to_dicts(conn.execute(
        "SELECT id FROM containers WHERE user_id = ?",
        (user_id,),
    ).fetchall())
    if not containers:
        raise ValueError("Create a container first.")
    valid_container_ids = {int(container["id"]) for container in containers}
    allocations = payload.get("allocations") or []
    if not isinstance(allocations, list):
        raise ValueError("Container allocations are required.")
    normalized = []
    totals_by_bucket = {}
    totals_by_container = {}
    touched_buckets = set()
    for allocation in allocations:
        if not isinstance(allocation, dict):
            continue
        container_id = int(allocation.get("container_id") or 0)
        quantity = max(0, int(allocation.get("quantity") or 0))
        variant = allocation.get("variant") or payload.get("variant") or "Normal"
        condition = card_condition(allocation.get("card_condition") or payload.get("card_condition"))
        if container_id not in valid_container_ids:
            raise ValueError("One of those containers was not found.")
        bucket = (variant, condition)
        touched_buckets.add(bucket)
        normalized.append({
            "container_id": container_id,
            "variant": variant,
            "card_condition": condition,
            "quantity": quantity,
        })
        totals_by_bucket[bucket] = totals_by_bucket.get(bucket, 0) + quantity
        totals_by_container[container_id] = totals_by_container.get(container_id, 0) + quantity
    if not touched_buckets:
        raise ValueError("Container allocations are required.")
    owned_by_bucket = {
        bucket: condition_owned_quantity(conn, user_id, card_id, bucket[0], bucket[1])
        for bucket in touched_buckets
    }
    if not any(quantity > 0 for quantity in owned_by_bucket.values()):
        raise ValueError("Only owned cards can be stored in containers.")
    for bucket, total in totals_by_bucket.items():
        owned = owned_by_bucket.get(bucket, 0)
        if total > owned:
            raise ValueError(f"Only {owned} {bucket[0]} {bucket[1]} copy/copies are owned.")

    container_limits = {
        int(row["id"]): {
            "name": row["name"],
            "capacity": int(row["capacity"] or 0),
            "stored_other": int(row["stored_other"] or 0),
        }
        for row in conn.execute(
            """
            SELECT ct.id, ct.name, COALESCE(ct.capacity, 0) AS capacity,
                   COALESCE(SUM(
                     CASE
                       WHEN cc.card_id = ? THEN 0
                       ELSE cc.quantity
                     END
                   ), 0) AS stored_other
            FROM containers ct
            LEFT JOIN container_cards cc ON cc.container_id = ct.id
            WHERE ct.user_id = ?
            GROUP BY ct.id
            """,
            (card_id, user_id),
        ).fetchall()
    }
    for container_id, quantity in totals_by_container.items():
        limit = container_limits.get(container_id)
        if not limit or limit["capacity"] <= 0:
            continue
        available_space = max(0, limit["capacity"] - limit["stored_other"])
        if quantity > available_space:
            raise ValueError(f"{limit['name']} only has space for {available_space} more card/copy.")
    for container_id in {item["container_id"] for item in normalized}:
        validate_container_strict_additions(
            conn,
            container_id,
            [
                {"card_id": card_id, "quantity": item["quantity"]}
                for item in normalized
                if item["container_id"] == container_id
            ],
            exclude_card_id=card_id,
        )

    previous_rows = conn.execute(
        """
        SELECT cc.container_id
        FROM container_cards cc
        JOIN containers c ON c.id = cc.container_id
        WHERE c.user_id = ? AND cc.card_id = ?
        """,
        (user_id, card_id),
    ).fetchall()
    touched = {int(row["container_id"]) for row in previous_rows}
    touched.update(item["container_id"] for item in normalized)
    timestamp = now_iso()
    conn.execute(
        """
        DELETE FROM container_cards
        WHERE card_id = ?
          AND container_id IN (SELECT id FROM containers WHERE user_id = ?)
        """,
        (card_id, user_id),
    )
    for item in normalized:
        if item["quantity"] <= 0:
            continue
        conn.execute(
            """
            INSERT INTO container_cards (container_id, card_id, variant, card_condition, quantity, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (item["container_id"], card_id, item["variant"], item["card_condition"], item["quantity"], timestamp),
        )
    if touched:
        placeholders = ", ".join("?" for _ in touched)
        conn.execute(
            f"UPDATE containers SET updated_at = ? WHERE user_id = ? AND id IN ({placeholders})",
            (timestamp, user_id, *sorted(touched)),
        )
    conn.commit()
    total = sum(totals_by_bucket.values())
    owned_total = sum(owned_by_bucket.values())
    return {
        "ok": True,
        "stored": total,
        "unassigned": max(0, owned_total - total),
        "containers": list_containers(conn, user_id),
    }


def remove_card_from_container(conn, user_id, container_id, payload):
    container = conn.execute("SELECT id FROM containers WHERE id = ? AND user_id = ?", (container_id, user_id)).fetchone()
    if not container:
        raise KeyError("Container not found")
    card_id = payload.get("card_id") or payload.get("scryfall_id")
    variant = payload.get("variant") or "Normal"
    condition = card_condition(payload.get("card_condition")) if payload.get("card_condition") else None
    if not card_id:
        raise ValueError("Card is required.")
    if condition:
        cursor = conn.execute(
            "DELETE FROM container_cards WHERE container_id = ? AND card_id = ? AND variant = ? AND card_condition = ?",
            (container_id, card_id, variant, condition),
        )
    else:
        cursor = conn.execute(
            "DELETE FROM container_cards WHERE container_id = ? AND card_id = ? AND variant = ?",
            (container_id, card_id, variant),
        )
    conn.execute("UPDATE containers SET updated_at = ? WHERE id = ?", (now_iso(), container_id))
    conn.commit()
    return {"ok": True, "removed": cursor.rowcount}


def delete_container(conn, user_id, container_id):
    cursor = conn.execute("DELETE FROM containers WHERE id = ? AND user_id = ?", (container_id, user_id))
    if cursor.rowcount == 0:
        raise KeyError("Container not found")
    conn.commit()
    return {"ok": True, "deleted": container_id}


def list_cards(conn, query, user_id):
    params = urllib.parse.parse_qs(query)
    search = (params.get("search", [""])[0] or "").strip()
    owned = params.get("owned", ["all"])[0]
    favorite = params.get("favorite", [""])[0]
    missing_list = params.get("missing_list", [""])[0]
    wishlist = params.get("wishlist", [""])[0]
    for_sale = params.get("for_sale", [""])[0]
    sort = params.get("sort", ["value"])[0]
    set_code = (params.get("set", [""])[0] or "").strip().lower()
    set_codes = []
    for raw_value in params.get("set_code", []) + params.get("sets", []):
        for value in str(raw_value or "").split(","):
            normalized = value.strip().lower()
            if normalized and normalized not in set_codes:
                set_codes.append(normalized)
    container_filter = (params.get("container", [""])[0] or "").strip().lower()
    limit = min(int(params.get("limit", ["250"])[0] or 250), 5000)
    where = []
    values = []
    if set_codes:
        placeholders = ", ".join("?" for _ in set_codes)
        where.append(f"lower(c.set_code) IN ({placeholders})")
        values.extend(set_codes)
    elif set_code:
        where.append("lower(c.set_code) = ?")
        values.append(set_code)
    if search:
        where.append("(c.name LIKE ? OR c.flavor_name LIKE ? OR c.flavor_text LIKE ? OR c.set_name LIKE ? OR c.collector_number LIKE ? OR c.type_line LIKE ? OR c.type_category LIKE ? OR c.colors LIKE ? OR c.color_identity LIKE ?)")
        needle = f"%{search}%"
        values.extend([needle, needle, needle, needle, needle, needle, needle, needle, needle])
    if owned == "owned":
        where.append("COALESCE(col.quantity, 0) > 0")
    elif owned == "missing":
        where.append("COALESCE(col.quantity, 0) = 0")
    if favorite in {"1", "true", "yes"}:
        where.append("COALESCE(meta.favorite, 0) = 1")
    if missing_list in {"1", "true", "yes"}:
        where.append("COALESCE(meta.missing_list, 0) = 1")
    if wishlist in {"1", "true", "yes"}:
        where.append("COALESCE(meta.wishlist, 0) = 1")
        where.append("COALESCE(col.quantity, 0) = 0")
    if for_sale in {"1", "true", "yes"}:
        where.append("COALESCE(sale.sale_quantity, 0) > 0")
    price_expr = current_price_sql("c")
    allocated_expr = """
        COALESCE((
            SELECT SUM(cc.quantity)
            FROM container_cards cc
            JOIN containers ct ON ct.id = cc.container_id
            WHERE ct.user_id = ? AND cc.card_id = c.scryfall_id AND cc.variant = COALESCE(col.variant, 'Normal')
        ), 0)
    """
    deck_allocated_expr = """
        COALESCE((
            SELECT SUM(dc.quantity)
            FROM deck_cards dc
            JOIN decks dt ON dt.id = dc.deck_id
            WHERE dt.user_id = ? AND dc.card_id = c.scryfall_id AND dc.variant = COALESCE(col.variant, 'Normal')
        ), 0)
    """
    if container_filter in {"yes", "true", "1", "in", "contained"}:
        where.append(f"({allocated_expr}) > 0")
        values.append(user_id)
    elif container_filter in {"no", "false", "0", "out", "uncontained"}:
        where.append(f"COALESCE(col.quantity, 0) - ({allocated_expr}) > 0")
        values.append(user_id)
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    sort_map = {
        "name": "c.name COLLATE NOCASE ASC",
        "set": "c.set_name COLLATE NOCASE ASC, CAST(c.collector_number AS INTEGER), c.collector_number",
        "price": f"display_price DESC, c.name",
        "value": "owned_value DESC, display_price DESC, c.name",
        "gain": "gain_loss DESC, c.name",
        "acquired": "col.acquired_date DESC, c.name",
        "favorite": "meta.updated_at DESC, c.name",
        "set-owned": "CASE WHEN COALESCE(col.quantity, 0) > 0 THEN 0 ELSE 1 END, CAST(c.collector_number AS INTEGER), c.collector_number, c.name",
    }
    order_sql = sort_map.get(sort, sort_map["value"])
    rows = conn.execute(
        f"""
        SELECT c.*, COALESCE(col.quantity, 0) AS quantity, COALESCE(col.paid_price, 0.01) AS paid_price,
               COALESCE(col.variant, 'Normal') AS variant, col.share_id, col.acquired_date,
               COALESCE(col.card_condition, 'Near Mint') AS card_condition,
               COALESCE(col.graded, 0) AS graded,
               col.notes,
               COALESCE(sale.whatnot_url, '') AS whatnot_url,
               COALESCE(meta.favorite, 0) AS favorite,
               COALESCE(meta.missing_list, 0) AS missing_list,
               COALESCE(meta.wishlist, 0) AS wishlist,
               COALESCE(sale.sale_quantity, 0) AS sale_quantity,
               COALESCE(sale.sale_price, ({price_expr})) AS sale_price,
               ({allocated_expr}) AS container_quantity,
               ({deck_allocated_expr}) AS deck_quantity,
               MAX(COALESCE(col.quantity, 0) - ({allocated_expr}), 0) AS unassigned_quantity,
               COALESCE(col.quantity, 0) AS saleable_quantity,
               ({price_expr}) AS display_price,
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value,
               COALESCE(col.quantity, 0) * (({price_expr}) - COALESCE(col.paid_price, 0.01)) AS gain_loss
        FROM cards c
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = c.scryfall_id
        LEFT JOIN card_meta meta ON meta.user_id = ? AND meta.card_id = c.scryfall_id AND meta.variant = COALESCE(col.variant, 'Normal')
        LEFT JOIN (
            SELECT card_id, variant, SUM(quantity) AS sale_quantity, MAX(asking_price) AS sale_price, MAX(whatnot_url) AS whatnot_url
            FROM card_sales
            WHERE user_id = ?
            GROUP BY card_id, variant
        ) sale ON sale.card_id = c.scryfall_id AND sale.variant = COALESCE(col.variant, 'Normal')
        {where_sql}
        ORDER BY {order_sql}
        LIMIT ?
        """,
        [user_id, user_id, user_id, user_id, user_id, user_id] + values + [limit],
    ).fetchall()
    cards = rows_to_dicts(rows)
    variant_summaries = variant_summaries_for_cards(conn, [card.get("scryfall_id") for card in cards], user_id)
    condition_inventory = {}
    card_keys = [(card.get("scryfall_id"), card.get("variant") or "Normal") for card in cards]
    if card_keys:
        purchase_rows = conn.execute(
            """
            SELECT card_id, COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
                   COALESCE(NULLIF(card_condition, ''), ?) AS card_condition,
                   SUM(quantity) AS quantity
            FROM card_purchases
            WHERE user_id = ?
            GROUP BY card_id, COALESCE(NULLIF(variant, ''), 'Normal'), COALESCE(NULLIF(card_condition, ''), ?)
            """,
            (DEFAULT_CARD_CONDITION, user_id, DEFAULT_CARD_CONDITION),
        ).fetchall()
        for row in purchase_rows:
            key = (row["card_id"], row["variant"])
            condition_inventory.setdefault(key, []).append({
                "card_condition": card_condition(row["card_condition"]),
                "quantity": row["quantity"],
            })
        sale_rows = conn.execute(
            """
            SELECT card_id, COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
                   COALESCE(NULLIF(card_condition, ''), ?) AS card_condition,
                   quantity AS sale_quantity,
                   asking_price AS sale_price,
                   COALESCE(whatnot_url, '') AS whatnot_url
            FROM card_sales
            WHERE user_id = ?
            """,
            (DEFAULT_CARD_CONDITION, user_id),
        ).fetchall()
        sale_lookup = {
            (row["card_id"], row["variant"], card_condition(row["card_condition"])): row
            for row in sale_rows
        }
        for card in cards:
            key = (card.get("scryfall_id"), card.get("variant") or "Normal")
            buckets = condition_inventory.get(key)
            if not buckets:
                buckets = [{
                    "card_condition": card_condition(card.get("card_condition")),
                    "quantity": card.get("quantity") or 0,
                }]
            for bucket in buckets:
                sale = sale_lookup.get((key[0], key[1], bucket["card_condition"]))
                bucket["sale_quantity"] = sale["sale_quantity"] if sale else 0
                bucket["sale_price"] = sale["sale_price"] if sale else card.get("display_price") or 0.01
                bucket["whatnot_url"] = sale["whatnot_url"] if sale else ""
                bucket_quantity = int(bucket.get("quantity") or 0)
                bucket["sale_available_quantity"] = bucket_quantity
            card["condition_inventory"] = buckets
    memberships = {}
    deck_rows = conn.execute(
        """
        SELECT dc.card_id, COALESCE(NULLIF(dc.variant, ''), 'Normal') AS variant,
               COALESCE(dc.quantity, 1) AS deck_quantity,
               d.id, d.share_id, d.name
        FROM deck_cards dc
        JOIN decks d ON d.id = dc.deck_id
        WHERE d.user_id = ?
        ORDER BY d.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    for deck in deck_rows:
        key = (deck["card_id"], deck["variant"])
        memberships.setdefault(key, []).append({
            "id": deck["id"],
            "share_id": deck["share_id"],
            "name": deck["name"],
            "deck_quantity": deck["deck_quantity"],
        })
    for card in cards:
        key = (card.get("scryfall_id"), card.get("variant") or "Normal")
        card["deck_memberships"] = memberships.get(key, [])
    container_memberships = {}
    container_rows = conn.execute(
        """
        SELECT cc.card_id, COALESCE(NULLIF(cc.variant, ''), 'Normal') AS variant,
               COALESCE(NULLIF(cc.card_condition, ''), ?) AS card_condition,
               cc.quantity, c.id, c.name, COALESCE(c.storage_type, 'other') AS storage_type,
               c.location
        FROM container_cards cc
        JOIN containers c ON c.id = cc.container_id
        WHERE c.user_id = ?
        ORDER BY c.name COLLATE NOCASE
        """,
        (DEFAULT_CARD_CONDITION, user_id),
    ).fetchall()
    for container in container_rows:
        key = (container["card_id"], container["variant"])
        container_memberships.setdefault(key, []).append({
            "id": container["id"],
            "name": container["name"],
            "storage_type": container["storage_type"],
            "location": container["location"],
            "quantity": container["quantity"],
            "card_condition": card_condition(container["card_condition"]),
        })
    for card in cards:
        key = (card.get("scryfall_id"), card.get("variant") or "Normal")
        card["container_memberships"] = container_memberships.get(key, [])
        card["variant_summaries"] = variant_summaries.get(card.get("scryfall_id"), [])
    return cards


def list_wishlists(conn, user_id):
    rows = conn.execute(
        """
        SELECT w.id, w.share_id, w.name, w.created_at, w.updated_at,
               COALESCE(SUM(wi.quantity), 0) AS item_count,
               COUNT(DISTINCT wi.card_id || '::' || wi.variant) AS unique_card_count
        FROM wishlists w
        LEFT JOIN wishlist_items wi ON wi.wishlist_id = w.id
        WHERE w.user_id = ?
        GROUP BY w.id
        ORDER BY w.updated_at DESC, w.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    return rows_to_dicts(rows)


def create_wishlist(conn, user_id, payload):
    name = validate_user_content_name(payload.get("name"), "Wishlist name", 30)
    if name_exists(conn, "wishlists", name, user_id):
        raise ValueError("Wishlist name must be unique across your decks, containers, and wishlists.")
    enforce_role_limit(conn, user_id, "wishlists", "wishlists", "wishlists")
    timestamp = now_iso()
    share_id = new_wishlist_share_id(conn)
    cursor = conn.execute(
        "INSERT INTO wishlists (user_id, share_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, share_id, name, timestamp, timestamp),
    )
    conn.commit()
    return {
        "ok": True,
        "wishlist": {
            "id": cursor.lastrowid,
            "share_id": share_id,
            "name": name,
            "created_at": timestamp,
            "updated_at": timestamp,
            "item_count": 0,
            "unique_card_count": 0,
        },
    }


def wishlist_detail(conn, user_id, wishlist_id, query=""):
    wishlist = conn.execute(
        """
        SELECT id, share_id, name, created_at, updated_at
        FROM wishlists
        WHERE id = ? AND user_id = ?
        """,
        (wishlist_id, user_id),
    ).fetchone()
    if not wishlist:
        raise KeyError("Wishlist not found")
    payload = dict(wishlist)
    payload["cards"] = list_wishlist_cards(conn, query, user_id, wishlist_id=wishlist_id)
    payload["item_count"] = len(payload["cards"])
    payload["unique_card_count"] = len({(card.get("scryfall_id"), card.get("variant") or "Normal") for card in payload["cards"]})
    return payload


def shared_wishlist(conn, share_id):
    wishlist = conn.execute("SELECT id, user_id FROM wishlists WHERE share_id = ?", (share_id,)).fetchone()
    if not wishlist:
        raise KeyError("Shared wishlist not found")
    payload = wishlist_detail(conn, wishlist["user_id"], wishlist["id"])
    payload["readonly"] = True
    return payload


def wishlist_share_url(wishlist):
    share_id = wishlist.get("share_id") if isinstance(wishlist, dict) else wishlist["share_id"]
    return f"{verification_base_url()}/wishlists/{urllib.parse.quote(share_id)}"


def card_email_title(card):
    return card.get("flavor_name") or card.get("display_name") or card.get("name") or "Card"


def wishlist_email_html(wishlist, share_url, sender_name):
    cards = wishlist.get("cards") or []
    rows = []
    for card in cards:
        title = html_lib.escape(card_email_title(card))
        set_text = html_lib.escape(" ".join(part for part in [
            card.get("set_name") or "",
            f"#{card.get('collector_number')}" if card.get("collector_number") else "",
        ] if part).strip())
        type_text = html_lib.escape(card.get("type_line") or card.get("type_category") or "")
        colors = card.get("colors")
        if isinstance(colors, str):
            try:
                colors = json.loads(colors)
            except json.JSONDecodeError:
                colors = [colors] if colors else []
        color_text = html_lib.escape(", ".join(colors or card.get("color_identity") or []) or "Colorless")
        price_text = money(card.get("display_price"), fallback=0)
        rows.append(f"""
          <tr>
            <td style="padding:10px 8px;border-bottom:1px solid #d7dedb;">
              <strong>{title}</strong><br>
              <span style="color:#586661;">{set_text}</span>
            </td>
            <td style="padding:10px 8px;border-bottom:1px solid #d7dedb;color:#303936;">{type_text}</td>
            <td style="padding:10px 8px;border-bottom:1px solid #d7dedb;color:#303936;">{color_text}</td>
            <td style="padding:10px 8px;border-bottom:1px solid #d7dedb;text-align:right;">${price_text:.2f}</td>
          </tr>
        """)
    list_rows = "\n".join(rows) or """
      <tr>
        <td colspan="4" style="padding:14px 8px;color:#586661;">This wishlist does not have any cards yet.</td>
      </tr>
    """
    safe_sender = html_lib.escape(sender_name or "An Arcane Ledger user")
    safe_name = html_lib.escape(wishlist.get("name") or "Wishlist")
    safe_url = html_lib.escape(share_url)
    return f"""
    <!doctype html>
    <html>
      <body style="margin:0;background:#f4f7f5;color:#111816;font-family:Arial,Helvetica,sans-serif;">
        <div style="max-width:760px;margin:0 auto;padding:24px;">
          <h1 style="margin:0 0 8px;font-size:28px;line-height:1.1;">{safe_name}</h1>
          <p style="margin:0 0 16px;color:#586661;">{safe_sender} shared this Arcane Ledger wishlist with you.</p>
          <p style="margin:0 0 20px;">
            <a href="{safe_url}" style="display:inline-block;background:#111816;color:#ffffff;text-decoration:none;padding:10px 14px;border-radius:8px;font-weight:700;">Open wishlist</a>
          </p>
          <p style="margin:0 0 16px;color:#303936;word-break:break-all;">{safe_url}</p>
          <table role="presentation" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;background:#ffffff;border:1px solid #d7dedb;border-radius:8px;overflow:hidden;">
            <thead>
              <tr style="background:#e9efec;text-align:left;">
                <th style="padding:10px 8px;">Card</th>
                <th style="padding:10px 8px;">Type</th>
                <th style="padding:10px 8px;">Colors</th>
                <th style="padding:10px 8px;text-align:right;">Market</th>
              </tr>
            </thead>
            <tbody>
              {list_rows}
            </tbody>
          </table>
        </div>
      </body>
    </html>
    """


def wishlist_email_text(wishlist, share_url, sender_name):
    lines = [
        f"{sender_name or 'An Arcane Ledger user'} shared this Arcane Ledger wishlist with you: {wishlist.get('name') or 'Wishlist'}",
        share_url,
        "",
        "Cards:",
    ]
    for card in wishlist.get("cards") or []:
        set_text = " ".join(part for part in [
            card.get("set_name") or "",
            f"#{card.get('collector_number')}" if card.get("collector_number") else "",
        ] if part).strip()
        lines.append(f"- {card_email_title(card)} ({set_text})")
    if not (wishlist.get("cards") or []):
        lines.append("- No cards yet.")
    return "\n".join(lines)


def email_wishlist(conn, user, wishlist_id, payload):
    recipient = validate_email(payload.get("email"))
    wishlist = wishlist_detail(conn, user["id"], wishlist_id)
    share_url = wishlist_share_url(wishlist)
    sender_name = user["name"] or user["email"]
    subject = f"Arcane Ledger: {sender_name} sharing wishlist: {wishlist['name']}"
    result = send_email(
        recipient,
        subject,
        text=wishlist_email_text(wishlist, share_url, sender_name),
        html=wishlist_email_html(wishlist, share_url, sender_name),
        tags=["arcaneledger", "wishlist-share"],
    )
    return {"ok": True, "email": recipient, "provider": result.get("provider"), "status": result.get("status")}


def set_share_url(store_share_id, set_code):
    return (
        f"{verification_base_url()}/sets/shared/"
        f"{urllib.parse.quote(store_share_id or '')}/"
        f"{urllib.parse.quote((set_code or '').lower())}"
    )


def set_share_payload(conn, user_id, set_code):
    detail = set_detail(conn, user_id, set_code)
    cards = list_cards(conn, urllib.parse.urlencode({
        "set": set_code,
        "owned": "all",
        "sort": "set-owned",
        "limit": "5000",
    }), user_id)
    detail["name"] = detail.get("set_name") or detail.get("set_code") or "Set"
    detail["cards"] = cards
    detail["description"] = (
        f"{detail.get('completion_percent', 0)}% complete "
        f"({detail.get('owned_cards', 0)} / {detail.get('total_cards', 0)} unique prints)"
    )
    return detail


def shared_set(conn, store_share_id, set_code):
    owner = conn.execute(
        """
        SELECT id, COALESCE(name, email) AS name, store_share_id
        FROM users
        WHERE store_share_id = ?
        """,
        (store_share_id,),
    ).fetchone()
    if not owner:
        raise KeyError("Shared set not found")
    payload = set_share_payload(conn, owner["id"], set_code)
    payload["readonly"] = True
    payload["owner_name"] = owner["name"] or "Arcane Ledger user"
    payload["store_share_id"] = owner["store_share_id"]
    return payload


def email_set(conn, user, set_code, payload):
    recipient = validate_email(payload.get("email"))
    set_code = (set_code or "").strip().lower()
    set_payload = set_share_payload(conn, user["id"], set_code)
    store_share_id = user["store_share_id"] if "store_share_id" in user.keys() else ""
    share_url = set_share_url(store_share_id, set_code)
    sender_name = user["name"] or user["email"]
    subject = f"Arcane Ledger: {sender_name} sharing set: {set_payload['name']}"
    result = send_email(
        recipient,
        subject,
        text=shared_list_email_text(set_payload, share_url, sender_name, "set"),
        html=shared_list_email_html(set_payload, share_url, sender_name, "set"),
        tags=["arcaneledger", "set-share"],
    )
    return {"ok": True, "email": recipient, "provider": result.get("provider"), "status": result.get("status")}


def email_card_colors(card):
    colors = card.get("colors")
    if isinstance(colors, str):
        try:
            colors = json.loads(colors)
        except json.JSONDecodeError:
            colors = [colors] if colors else []
    identity = card.get("color_identity")
    if isinstance(identity, str):
        try:
            identity = json.loads(identity)
        except json.JSONDecodeError:
            identity = [identity] if identity else []
    return ", ".join(colors or identity or []) or "Colorless"


def share_list_quantity(card, entity_type):
    if entity_type == "deck":
        return int(card.get("deck_quantity") or card.get("quantity") or 0)
    if entity_type == "container":
        return int(card.get("stored_quantity") or card.get("quantity") or 0)
    if entity_type == "set":
        return int(card.get("quantity") or 0)
    return int(card.get("quantity") or 1)


def shared_list_email_html(payload, share_url, sender_name, entity_type):
    cards = payload.get("cards") or []
    label = entity_type.title()
    rows = []
    for card in cards:
        title = html_lib.escape(card_email_title(card))
        set_text = html_lib.escape(" ".join(part for part in [
            card.get("set_name") or "",
            f"#{card.get('collector_number')}" if card.get("collector_number") else "",
            card.get("variant") or "",
        ] if part).strip())
        type_text = html_lib.escape(card.get("type_line") or card.get("type_category") or "")
        color_text = html_lib.escape(email_card_colors(card))
        quantity = share_list_quantity(card, entity_type)
        price_text = money(card.get("display_price"), fallback=0)
        rows.append(f"""
          <tr>
            <td style="padding:10px 8px;border-bottom:1px solid #d7dedb;">
              <strong>{title}</strong><br>
              <span style="color:#586661;">{set_text}</span>
            </td>
            <td style="padding:10px 8px;border-bottom:1px solid #d7dedb;color:#303936;">{type_text}</td>
            <td style="padding:10px 8px;border-bottom:1px solid #d7dedb;color:#303936;">{color_text}</td>
            <td style="padding:10px 8px;border-bottom:1px solid #d7dedb;text-align:right;">{quantity}</td>
            <td style="padding:10px 8px;border-bottom:1px solid #d7dedb;text-align:right;">${price_text:.2f}</td>
          </tr>
        """)
    list_rows = "\n".join(rows) or f"""
      <tr>
        <td colspan="5" style="padding:14px 8px;color:#586661;">This {entity_type} does not have any cards yet.</td>
      </tr>
    """
    safe_sender = html_lib.escape(sender_name or "An Arcane Ledger user")
    safe_name = html_lib.escape(payload.get("name") or label)
    safe_url = html_lib.escape(share_url)
    safe_entity = html_lib.escape(entity_type)
    public_notes = []
    if payload.get("description"):
        public_notes.append(f"<p style=\"margin:0 0 10px;color:#303936;line-height:1.45;\">{html_lib.escape(payload.get('description') or '')}</p>")
    if entity_type == "deck" and payload.get("external_notes"):
        public_notes.append(f"<p style=\"margin:0 0 16px;color:#586661;line-height:1.45;\">{html_lib.escape(payload.get('external_notes') or '')}</p>")
    public_notes_html = "\n".join(public_notes)
    return f"""
    <!doctype html>
    <html>
      <body style="margin:0;background:#f4f7f5;color:#111816;font-family:Arial,Helvetica,sans-serif;">
        <div style="max-width:820px;margin:0 auto;padding:24px;">
          <h1 style="margin:0 0 8px;font-size:28px;line-height:1.1;">{safe_name}</h1>
          <p style="margin:0 0 16px;color:#586661;">{safe_sender} shared this Arcane Ledger {safe_entity} with you.</p>
          {public_notes_html}
          <p style="margin:0 0 20px;">
            <a href="{safe_url}" style="display:inline-block;background:#111816;color:#ffffff;text-decoration:none;padding:10px 14px;border-radius:8px;font-weight:700;">Open {safe_entity}</a>
          </p>
          <p style="margin:0 0 16px;color:#303936;word-break:break-all;">{safe_url}</p>
          <table role="presentation" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;background:#ffffff;border:1px solid #d7dedb;border-radius:8px;overflow:hidden;">
            <thead>
              <tr style="background:#e9efec;text-align:left;">
                <th style="padding:10px 8px;">Card</th>
                <th style="padding:10px 8px;">Type</th>
                <th style="padding:10px 8px;">Colors</th>
                <th style="padding:10px 8px;text-align:right;">Qty</th>
                <th style="padding:10px 8px;text-align:right;">Market</th>
              </tr>
            </thead>
            <tbody>
              {list_rows}
            </tbody>
          </table>
        </div>
      </body>
    </html>
    """


def shared_list_email_text(payload, share_url, sender_name, entity_type):
    lines = [
        f"{sender_name or 'An Arcane Ledger user'} shared this Arcane Ledger {entity_type} with you: {payload.get('name') or entity_type.title()}",
        share_url,
        "",
    ]
    if payload.get("description"):
        lines.extend([payload.get("description") or "", ""])
    if entity_type == "deck" and payload.get("external_notes"):
        lines.extend([payload.get("external_notes") or "", ""])
    lines.append("Cards:")
    for card in payload.get("cards") or []:
        set_text = " ".join(part for part in [
            card.get("set_name") or "",
            f"#{card.get('collector_number')}" if card.get("collector_number") else "",
            card.get("variant") or "",
        ] if part).strip()
        lines.append(f"- {card_email_title(card)} ({set_text}) x{share_list_quantity(card, entity_type)}")
    if not (payload.get("cards") or []):
        lines.append("- No cards yet.")
    return "\n".join(lines)


def email_deck(conn, user, deck_id, payload):
    recipient = validate_email(payload.get("email"))
    deck = deck_detail(conn, user["id"], deck_id)
    share_url = deck_share_url(deck)
    sender_name = user["name"] or user["email"]
    subject = f"Arcane Ledger: {sender_name} sharing deck: {deck['name']}"
    result = send_email(
        recipient,
        subject,
        text=shared_list_email_text(deck, share_url, sender_name, "deck"),
        html=shared_list_email_html(deck, share_url, sender_name, "deck"),
        tags=["arcaneledger", "deck-share"],
    )
    return {"ok": True, "email": recipient, "provider": result.get("provider"), "status": result.get("status")}


def email_container(conn, user, container_id, payload):
    recipient = validate_email(payload.get("email"))
    container = container_detail(conn, user["id"], container_id)
    share_url = container_share_url(container)
    sender_name = user["name"] or user["email"]
    subject = f"Arcane Ledger: {sender_name} sharing container: {container['name']}"
    result = send_email(
        recipient,
        subject,
        text=shared_list_email_text(container, share_url, sender_name, "container"),
        html=shared_list_email_html(container, share_url, sender_name, "container"),
        tags=["arcaneledger", "container-share"],
    )
    return {"ok": True, "email": recipient, "provider": result.get("provider"), "status": result.get("status")}


def delete_wishlist(conn, user_id, wishlist_id):
    cursor = conn.execute("DELETE FROM wishlists WHERE id = ? AND user_id = ?", (wishlist_id, user_id))
    if cursor.rowcount == 0:
        raise KeyError("Wishlist not found")
    conn.commit()
    return {"ok": True, "deleted": wishlist_id}


def remove_wishlist_items(conn, user_id, wishlist_id, payload):
    if not conn.execute("SELECT 1 FROM wishlists WHERE id = ? AND user_id = ?", (wishlist_id, user_id)).fetchone():
        raise KeyError("Wishlist not found")
    cards = payload.get("cards") or []
    if not isinstance(cards, list) or not cards:
        raise ValueError("Choose at least one wishlist card.")
    timestamp = now_iso()
    removed = 0
    touched = set()
    for item in cards:
        if not isinstance(item, dict):
            continue
        card_id = (item.get("card_id") or item.get("scryfall_id") or "").strip()
        variant = item.get("variant") or "Normal"
        if not card_id:
            continue
        cursor = conn.execute(
            """
            DELETE FROM wishlist_items
            WHERE user_id = ? AND wishlist_id = ? AND card_id = ? AND variant = ?
            """,
            (user_id, wishlist_id, card_id, variant),
        )
        removed += cursor.rowcount
        touched.add((card_id, variant))
    for card_id, variant in touched:
        still_wishlisted = conn.execute(
            """
            SELECT 1
            FROM wishlist_items
            WHERE user_id = ? AND card_id = ? AND variant = ?
            LIMIT 1
            """,
            (user_id, card_id, variant),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, wishlist, updated_at)
            VALUES (?, ?, ?, 0, 0, ?, ?)
            ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
                wishlist = excluded.wishlist,
                updated_at = excluded.updated_at
            """,
            (user_id, card_id, variant, 1 if still_wishlisted else 0, timestamp),
        )
        if not still_wishlisted:
            conn.execute("DELETE FROM wishlist_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
    conn.execute("UPDATE wishlists SET updated_at = ? WHERE id = ? AND user_id = ?", (timestamp, wishlist_id, user_id))
    conn.commit()
    return {"ok": True, "removed": removed, "wishlist": wishlist_detail(conn, user_id, wishlist_id)}


def list_wishlist_cards(conn, query, user_id, wishlist_id=None):
    params = urllib.parse.parse_qs(query)
    search = (params.get("search", [""])[0] or "").strip().lower()
    sort = params.get("sort", ["set"])[0]
    limit = min(int(params.get("limit", ["5000"])[0] or 5000), 5000)
    wishlist_filter = ""
    values = [user_id]
    if wishlist_id is not None:
        wishlist_filter = "AND wi.wishlist_id = ?"
        values.append(wishlist_id)
    search_filter = ""
    if search:
        search_filter = """
          AND (
              c.name LIKE ? OR c.flavor_name LIKE ? OR c.set_name LIKE ? OR
              c.collector_number LIKE ? OR c.type_line LIKE ? OR c.type_category LIKE ?
          )
        """
        needle = f"%{search}%"
        values.extend([needle, needle, needle, needle, needle, needle])
    sort_map = {
        "name": "c.name COLLATE NOCASE ASC",
        "price": "display_price DESC, c.name",
        "set": "c.set_name COLLATE NOCASE ASC, CAST(c.collector_number AS INTEGER), c.collector_number, c.name",
    }
    order_sql = sort_map.get(sort, sort_map["set"])
    price_expr = current_price_sql("c")
    cards = rows_to_dicts(conn.execute(
        f"""
        SELECT c.*, wi.variant, COALESCE(wi.quantity, 1) AS wishlist_quantity,
               COALESCE(col.quantity, 0) AS owned_quantity,
               COALESCE(col.quantity, 0) AS quantity,
               NULL AS share_id, NULL AS acquired_date,
               0.01 AS paid_price,
               ? AS card_condition,
               0 AS graded,
               '' AS notes,
               0 AS favorite,
               0 AS missing_list,
               1 AS wishlist,
               wi.wishlist_id,
               w.name AS wishlist_name,
               ({price_expr}) AS display_price,
               0 AS owned_value,
               0 AS gain_loss,
               CASE WHEN COALESCE(col.quantity, 0) >= COALESCE(wi.quantity, 1) THEN 1 ELSE 0 END AS fulfilled
        FROM wishlist_items wi
        JOIN wishlists w ON w.id = wi.wishlist_id
        JOIN cards c ON c.scryfall_id = wi.card_id
        LEFT JOIN collection col ON col.user_id = wi.user_id AND col.card_id = wi.card_id AND col.variant = wi.variant AND COALESCE(col.quantity, 0) > 0
        WHERE wi.user_id = ?
          {wishlist_filter}
          {search_filter}
        ORDER BY {order_sql}
        LIMIT ?
        """,
        [DEFAULT_CARD_CONDITION] + values + [limit],
    ).fetchall())
    seen = {(card.get("scryfall_id"), card.get("variant") or "Normal") for card in cards}
    card_json_values = [user_id]
    card_json_filter = ""
    if wishlist_id is not None:
        card_json_filter = "AND wi.wishlist_id = ?"
        card_json_values.append(wishlist_id)
    rows = conn.execute(
        f"""
        SELECT wi.card_id, wi.variant, COALESCE(wi.quantity, 1) AS wishlist_quantity,
               wi.card_json, wi.wishlist_id, w.name AS wishlist_name,
               COALESCE(col.quantity, 0) AS owned_quantity
        FROM wishlist_items wi
        JOIN wishlists w ON w.id = wi.wishlist_id
        LEFT JOIN cards c ON c.scryfall_id = wi.card_id
        LEFT JOIN collection col ON col.user_id = wi.user_id AND col.card_id = wi.card_id AND col.variant = wi.variant AND COALESCE(col.quantity, 0) > 0
        WHERE wi.user_id = ?
          AND c.scryfall_id IS NULL
          {card_json_filter}
        ORDER BY wi.updated_at DESC
        """,
        card_json_values,
    ).fetchall()
    for row in rows:
        key = (row["card_id"], row["variant"] or "Normal")
        if key in seen and wishlist_id is None:
            continue
        try:
            card = json.loads(row["card_json"] or "{}")
        except json.JSONDecodeError:
            continue
        haystack = " ".join(str(card.get(key) or "") for key in (
            "name", "flavor_name", "display_name", "set_code", "set_name", "collector_number", "type_line", "type_category"
        )).lower()
        if search and search not in haystack:
            continue
        prices = card.get("prices") or {}
        card.update({
            "scryfall_id": card.get("scryfall_id") or row["card_id"],
            "variant": row["variant"] or card.get("variant") or "Normal",
            "quantity": int(row["owned_quantity"] or 0),
            "owned_quantity": int(row["owned_quantity"] or 0),
            "wishlist_quantity": int(row["wishlist_quantity"] or 1),
            "fulfilled": 1 if int(row["owned_quantity"] or 0) >= int(row["wishlist_quantity"] or 1) else 0,
            "wishlist": 1,
            "wishlist_id": row["wishlist_id"],
            "wishlist_name": row["wishlist_name"],
            "catalog_only": True,
            "display_price": prices.get("usd") or prices.get("usd_foil") or prices.get("usd_etched") or 0,
            "owned_value": 0,
            "gain_loss": 0,
            "favorite": 0,
            "missing_list": 0,
            "card_condition": DEFAULT_CARD_CONDITION,
        })
        cards.append(card)
        seen.add(key)
    if sort == "name":
        cards.sort(key=lambda card: (card.get("flavor_name") or card.get("name") or "").lower())
    elif sort == "price":
        cards.sort(key=lambda card: float(card.get("display_price") or 0), reverse=True)
    else:
        cards.sort(key=lambda card: (
            str(card.get("set_name") or "").lower(),
            str(card.get("collector_number") or ""),
            (card.get("flavor_name") or card.get("name") or "").lower(),
        ))
    return cards[:limit]


def list_sale_cards(conn, query, user_id):
    params = urllib.parse.parse_qs(query)
    search = (params.get("search", [""])[0] or "").strip()
    sort = params.get("sort", ["value"])[0]
    limit = min(int(params.get("limit", ["5000"])[0] or 5000), 5000)
    where = ["sale.user_id = ?", "COALESCE(sale.quantity, 0) > 0"]
    values = [user_id]
    if search:
        where.append("(c.name LIKE ? OR c.flavor_name LIKE ? OR c.set_name LIKE ? OR c.collector_number LIKE ? OR c.type_line LIKE ? OR sale.card_condition LIKE ?)")
        needle = f"%{search}%"
        values.extend([needle, needle, needle, needle, needle, needle])
    where_sql = "WHERE " + " AND ".join(where)
    price_expr = current_price_sql("c")
    sort_map = {
        "name": "c.name COLLATE NOCASE ASC, sale.card_condition",
        "set": "c.set_name COLLATE NOCASE ASC, CAST(c.collector_number AS INTEGER), c.collector_number, sale.card_condition",
        "price": f"display_price DESC, c.name",
        "value": "sale_value DESC, display_price DESC, c.name",
        "gain": "sale_value DESC, c.name",
        "acquired": "sale.updated_at DESC, c.name",
    }
    order_sql = sort_map.get(sort, sort_map["value"])
    rows = conn.execute(
        f"""
        SELECT c.*, COALESCE(col.quantity, 0) AS owned_quantity,
               COALESCE(inv.quantity, col.quantity, sale.quantity) AS quantity,
               COALESCE(col.paid_price, 0.01) AS paid_price,
               sale.variant AS variant,
               col.share_id,
               col.acquired_date,
               sale.card_condition AS card_condition,
               COALESCE(col.graded, 0) AS graded,
               col.notes,
               COALESCE(meta.favorite, 0) AS favorite,
               COALESCE(meta.missing_list, 0) AS missing_list,
               COALESCE(meta.wishlist, 0) AS wishlist,
               sale.quantity AS sale_quantity,
               sale.asking_price AS sale_price,
               ({price_expr}) AS display_price,
               sale.quantity * sale.asking_price AS sale_value,
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value,
               COALESCE(col.quantity, 0) * (({price_expr}) - COALESCE(col.paid_price, 0.01)) AS gain_loss
        FROM card_sales sale
        JOIN cards c ON c.scryfall_id = sale.card_id
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = sale.card_id AND col.variant = sale.variant
        LEFT JOIN card_meta meta ON meta.user_id = ? AND meta.card_id = sale.card_id AND meta.variant = sale.variant
        LEFT JOIN (
            SELECT card_id, COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
                   COALESCE(NULLIF(card_condition, ''), ?) AS card_condition,
                   SUM(quantity) AS quantity
            FROM card_purchases
            WHERE user_id = ?
            GROUP BY card_id, COALESCE(NULLIF(variant, ''), 'Normal'), COALESCE(NULLIF(card_condition, ''), ?)
        ) inv ON inv.card_id = sale.card_id AND inv.variant = sale.variant AND inv.card_condition = sale.card_condition
        {where_sql}
        ORDER BY {order_sql}
        LIMIT ?
        """,
        [user_id, user_id, DEFAULT_CARD_CONDITION, user_id, DEFAULT_CARD_CONDITION] + values + [limit],
    ).fetchall()
    return rows_to_dicts(rows)


def price_for_variant_from_row(card_row, variant):
    variant_key = (variant or "Normal").lower()
    if "etched" in variant_key and card_row["current_usd_etched"]:
        return float(card_row["current_usd_etched"] or 0)
    if "foil" in variant_key and card_row["current_usd_foil"]:
        return float(card_row["current_usd_foil"] or 0)
    return float(card_row["current_usd"] or card_row["current_usd_foil"] or card_row["current_usd_etched"] or 0)


def list_notifications(conn, user_id, limit=100):
    limit = min(max(int(money(limit, fallback=100)), 1), 250)
    rows = rows_to_dicts(conn.execute(
        """
        SELECT id, subject, body, link_url, source_type, is_read, created_at, updated_at, read_at
        FROM notifications
        WHERE user_id = ?
        ORDER BY is_read ASC, updated_at DESC, id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall())
    unread = conn.execute(
        "SELECT COUNT(*) AS count FROM notifications WHERE user_id = ? AND COALESCE(is_read, 0) = 0",
        (user_id,),
    ).fetchone()["count"] or 0
    return {"notifications": rows, "unread_count": int(unread)}


def mark_notification_read(conn, user_id, notification_id):
    timestamp = now_iso()
    cursor = conn.execute(
        """
        UPDATE notifications
        SET is_read = 1, read_at = COALESCE(read_at, ?)
        WHERE id = ? AND user_id = ?
        """,
        (timestamp, notification_id, user_id),
    )
    if cursor.rowcount == 0:
        raise KeyError("Notification not found")
    conn.commit()
    return {"ok": True, **list_notifications(conn, user_id)}


def notify_wishlist_users_for_sale(conn, seller_user_id, card_id, variant, sale_condition, quantity, asking_price):
    card = conn.execute(
        """
        SELECT scryfall_id, name, flavor_name, current_usd, current_usd_foil, current_usd_etched
        FROM cards
        WHERE scryfall_id = ?
        """,
        (card_id,),
    ).fetchone()
    if not card:
        return 0
    seller = conn.execute(
        "SELECT id, name, email, store_share_id FROM users WHERE id = ?",
        (seller_user_id,),
    ).fetchone()
    if not seller:
        return 0
    store_share_id = seller["store_share_id"] or new_store_share_id(conn)
    if not seller["store_share_id"]:
        conn.execute("UPDATE users SET store_share_id = ? WHERE id = ?", (store_share_id, seller_user_id))
    seller_name = public_display_name({**dict(seller), "store_share_id": store_share_id}, "Seller")
    title = card_email_title(dict(card))
    market_price = price_for_variant_from_row(card, variant)
    store_url = store_share_url(store_share_id)
    subject = "A Card on your wishlist is for sale!"
    body = (
        f"The card - {title} was just listed for sale on {seller_name}'s store. "
        f"They have {int(quantity or 0)} for sale. "
        f"They're asking ${float(asking_price or 0):.2f}. "
        f"The current market value of this card is ${float(market_price or 0):.2f}."
    )
    rows = conn.execute(
        """
        SELECT DISTINCT user_id
        FROM (
            SELECT user_id FROM wishlist_items WHERE card_id = ? AND user_id IS NOT NULL AND user_id != ?
            UNION
            SELECT user_id FROM wishlist_cards WHERE card_id = ? AND user_id IS NOT NULL AND user_id != ?
            UNION
            SELECT user_id FROM card_meta WHERE card_id = ? AND COALESCE(wishlist, 0) = 1 AND user_id IS NOT NULL AND user_id != ?
        )
        """,
        (card_id, seller_user_id, card_id, seller_user_id, card_id, seller_user_id),
    ).fetchall()
    timestamp = now_iso()
    source_key = f"sale:{seller_user_id}:{card_id}:{variant or 'Normal'}:{sale_condition or DEFAULT_CARD_CONDITION}"
    notified = 0
    for row in rows:
        conn.execute(
            """
            INSERT INTO notifications (
                user_id, subject, body, link_url, source_type, source_key, is_read, created_at, updated_at, read_at
            )
            VALUES (?, ?, ?, ?, 'wishlist-sale', ?, 0, ?, ?, NULL)
            ON CONFLICT(user_id, source_type, source_key) DO UPDATE SET
                subject = excluded.subject,
                body = excluded.body,
                link_url = excluded.link_url,
                is_read = 0,
                updated_at = excluded.updated_at,
                read_at = NULL
            """,
            (row["user_id"], subject, body, store_url, source_key, timestamp, timestamp),
        )
        notified += 1
    return notified


def card_deck_references(conn, card_id):
    rows = conn.execute(
        """
        SELECT d.id, d.share_id, d.name, COALESCE(u.name, '') AS owner_name,
               u.email AS owner_email, u.role AS owner_role, u.subscription_status AS owner_subscription_status,
               COALESCE(u.store_share_id, '') AS store_share_id,
               COALESCE(SUM(dc.quantity), 0) AS deck_quantity,
               COUNT(DISTINCT COALESCE(NULLIF(dc.variant, ''), 'Normal')) AS variant_count
        FROM deck_cards dc
        JOIN decks d ON d.id = dc.deck_id
        LEFT JOIN users u ON u.id = d.user_id
        WHERE dc.card_id = ?
        GROUP BY d.id
        ORDER BY d.name COLLATE NOCASE
        """,
        (card_id,),
    ).fetchall()
    decks = []
    for row in rows:
        deck = dict(row)
        deck["owner_name"] = public_display_name(row, "User")
        owner_role = effective_user_role({
            "email": deck.get("owner_email"),
            "role": deck.get("owner_role"),
            "subscription_status": deck.get("owner_subscription_status"),
        })
        deck["owner_role"] = owner_role
        deck["owner_is_pro"] = owner_role in {"admin", "contributor", "pro"}
        deck["deck_url"] = deck_share_url(deck)
        decks.append(deck)
    return {"decks": decks}


def card_sale_sellers(conn, card_id):
    rows = conn.execute(
        """
        SELECT u.id, COALESCE(u.name, '') AS name, COALESCE(u.email, '') AS email,
               COALESCE(u.store_share_id, '') AS store_share_id, u.role, u.subscription_status,
               COALESCE(SUM(sale.quantity), 0) AS sale_quantity,
               MIN(sale.asking_price) AS min_asking_price,
               MAX(sale.asking_price) AS max_asking_price,
               COUNT(DISTINCT COALESCE(NULLIF(sale.variant, ''), 'Normal')) AS variant_count
        FROM card_sales sale
        JOIN users u ON u.id = sale.user_id
        WHERE sale.card_id = ? AND COALESCE(sale.quantity, 0) > 0
        GROUP BY u.id
        ORDER BY COALESCE(SUM(sale.quantity), 0) DESC, u.name COLLATE NOCASE
        """,
        (card_id,),
    ).fetchall()
    sellers = []
    for row in rows:
        seller = dict(row)
        if not seller.get("store_share_id"):
            seller["store_share_id"] = new_store_share_id(conn)
            conn.execute("UPDATE users SET store_share_id = ? WHERE id = ?", (seller["store_share_id"], row["id"]))
        seller["seller_name"] = public_display_name(row, "Seller")
        seller_role = effective_user_role(row)
        seller["seller_role"] = seller_role
        seller["seller_is_pro"] = seller_role in {"admin", "contributor", "pro"}
        seller["store_url"] = store_share_url(seller["store_share_id"])
        sellers.append(seller)
    conn.commit()
    return {"sellers": sellers}


def list_store_front_cards(conn, query, current_user_id=None):
    params = urllib.parse.parse_qs(query)
    search = (params.get("search", [""])[0] or "").strip()
    sort = params.get("sort", ["value"])[0]
    limit = min(int(params.get("limit", ["5000"])[0] or 5000), 5000)
    where = ["COALESCE(sale.quantity, 0) > 0"]
    values = []
    if search:
        where.append("(c.name LIKE ? OR c.flavor_name LIKE ? OR c.set_name LIKE ? OR c.collector_number LIKE ? OR c.type_line LIKE ?)")
        needle = f"%{search}%"
        values.extend([needle, needle, needle, needle, needle])
    where_sql = "WHERE " + " AND ".join(where)
    price_expr = (
        "CASE "
        "WHEN lower(coalesce(sale.variant, '')) LIKE '%etched%' AND c.current_usd_etched > 0 THEN c.current_usd_etched "
        "WHEN lower(coalesce(sale.variant, '')) LIKE '%foil%' AND c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd > 0 THEN c.current_usd "
        "WHEN c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd_etched > 0 THEN c.current_usd_etched "
        "ELSE 0 END"
    )
    sort_map = {
        "name": "c.name COLLATE NOCASE ASC",
        "set": "c.set_name COLLATE NOCASE ASC, CAST(c.collector_number AS INTEGER), c.collector_number",
        "price": f"display_price DESC, c.name",
        "value": "sale_asking_total DESC, display_price DESC, c.name",
        "sellers": "seller_count DESC, sale_quantity DESC, c.name",
        "quantity": "sale_quantity DESC, c.name",
    }
    order_sql = sort_map.get(sort, sort_map["value"])
    rows = rows_to_dicts(conn.execute(
        f"""
        SELECT c.*,
               MIN(COALESCE(NULLIF(sale.variant, ''), 'Normal')) AS variant,
               COALESCE(SUM(sale.quantity), 0) AS quantity,
               COALESCE(SUM(sale.quantity), 0) AS sale_quantity,
               COALESCE(SUM(sale.quantity * sale.asking_price), 0) AS sale_asking_total,
               MIN(sale.asking_price) AS min_asking_price,
               MAX(sale.asking_price) AS max_asking_price,
               COUNT(DISTINCT sale.user_id) AS seller_count,
               COUNT(DISTINCT COALESCE(NULLIF(sale.variant, ''), 'Normal')) AS variant_count,
               MAX(CASE WHEN LOWER(COALESCE(NULLIF(sale.variant, ''), 'Normal')) != 'normal' THEN 1 ELSE 0 END) AS has_special_variant,
               ({price_expr}) AS display_price,
               COALESCE(SUM(sale.quantity * ({price_expr})), 0) AS market_total,
               COALESCE(SUM(sale.quantity * sale.asking_price), 0) AS owned_value,
               COALESCE(SUM(sale.quantity * (sale.asking_price - ({price_expr}))), 0) AS gain_loss
        FROM card_sales sale
        JOIN cards c ON c.scryfall_id = sale.card_id
        {where_sql}
        GROUP BY c.scryfall_id
        ORDER BY {order_sql}
        LIMIT ?
        """,
        values + [limit],
    ).fetchall())
    for card in rows:
        card["variant_summaries"] = store_front_variant_summaries(conn, card["scryfall_id"])
        card["condition_inventory"] = [
            {
                "variant": summary["variant"],
                "card_condition": condition["card_condition"],
                "quantity": condition["quantity"],
            }
            for summary in card["variant_summaries"]
            for condition in summary.get("conditions", [])
        ]
        card["favorite_store_count"] = 0
        card["favorite_store"] = False
        if current_user_id:
            favorite_row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM favorite_store_listings fav
                JOIN card_sales sale
                  ON sale.user_id = fav.seller_user_id
                 AND sale.card_id = fav.card_id
                 AND sale.variant = fav.variant
                 AND sale.card_condition = fav.card_condition
                 AND COALESCE(sale.quantity, 0) > 0
                WHERE fav.user_id = ? AND fav.card_id = ?
                """,
                (current_user_id, card["scryfall_id"]),
            ).fetchone()
            card["favorite_store_count"] = int((favorite_row and favorite_row["count"]) or 0)
            card["favorite_store"] = card["favorite_store_count"] > 0
    return rows


def store_front_variant_summaries(conn, card_id):
    rows = conn.execute(
        """
        SELECT COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
               COALESCE(NULLIF(card_condition, ''), ?) AS card_condition,
               COALESCE(SUM(quantity), 0) AS quantity
        FROM card_sales
        WHERE card_id = ? AND COALESCE(quantity, 0) > 0
        GROUP BY COALESCE(NULLIF(variant, ''), 'Normal'), COALESCE(NULLIF(card_condition, ''), ?)
        ORDER BY variant COLLATE NOCASE, card_condition COLLATE NOCASE
        """,
        (DEFAULT_CARD_CONDITION, card_id, DEFAULT_CARD_CONDITION),
    ).fetchall()
    summaries = {}
    for row in rows:
        variant = row["variant"] or "Normal"
        entry = summaries.setdefault(variant, {"variant": variant, "quantity": 0, "conditions": []})
        quantity = int(row["quantity"] or 0)
        entry["quantity"] += quantity
        entry["conditions"].append({"card_condition": row["card_condition"] or DEFAULT_CARD_CONDITION, "quantity": quantity})
    return list(summaries.values())


def store_front_card_detail(conn, card_id, current_user_id=None):
    card = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    price_expr = (
        "CASE "
        "WHEN lower(coalesce(sale.variant, '')) LIKE '%etched%' AND c.current_usd_etched > 0 THEN c.current_usd_etched "
        "WHEN lower(coalesce(sale.variant, '')) LIKE '%foil%' AND c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd > 0 THEN c.current_usd "
        "WHEN c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd_etched > 0 THEN c.current_usd_etched "
        "ELSE 0 END"
    )
    card_payload = with_value_aliases(dict(conn.execute(
        f"""
        SELECT c.*,
               MIN(COALESCE(NULLIF(sale.variant, ''), 'Normal')) AS variant,
               COALESCE(SUM(sale.quantity), 0) AS quantity,
               COALESCE(SUM(sale.quantity), 0) AS sale_quantity,
               COALESCE(SUM(sale.quantity * sale.asking_price), 0) AS sale_asking_total,
               MIN(sale.asking_price) AS min_asking_price,
               MAX(sale.asking_price) AS max_asking_price,
               COUNT(DISTINCT sale.user_id) AS seller_count,
               COUNT(DISTINCT COALESCE(NULLIF(sale.variant, ''), 'Normal')) AS variant_count,
               MAX(CASE WHEN LOWER(COALESCE(NULLIF(sale.variant, ''), 'Normal')) != 'normal' THEN 1 ELSE 0 END) AS has_special_variant,
               ({price_expr}) AS display_price,
               COALESCE(SUM(sale.quantity * ({price_expr})), 0) AS market_total,
               COALESCE(SUM(sale.quantity * sale.asking_price), 0) AS owned_value,
               COALESCE(SUM(sale.quantity * (sale.asking_price - ({price_expr}))), 0) AS gain_loss
        FROM cards c
        LEFT JOIN card_sales sale ON sale.card_id = c.scryfall_id AND COALESCE(sale.quantity, 0) > 0
        WHERE c.scryfall_id = ?
        GROUP BY c.scryfall_id
        """,
        (card_id,),
    ).fetchone()))
    card_payload["variant_summaries"] = store_front_variant_summaries(conn, card_id)
    seller_rows = conn.execute(
        """
        SELECT u.id AS user_id, COALESCE(u.name, '') AS name, COALESCE(u.email, '') AS email,
               COALESCE(u.store_share_id, '') AS store_share_id, u.role, u.subscription_status,
               COALESCE(NULLIF(sale.variant, ''), 'Normal') AS variant,
               COALESCE(NULLIF(sale.card_condition, ''), ?) AS card_condition,
               COALESCE(sale.quantity, 0) AS sale_quantity,
               sale.asking_price,
               COALESCE(sale.whatnot_url, '') AS whatnot_url
        FROM card_sales sale
        JOIN users u ON u.id = sale.user_id
        WHERE sale.card_id = ? AND COALESCE(sale.quantity, 0) > 0
        ORDER BY sale.asking_price ASC, u.name COLLATE NOCASE, sale.variant COLLATE NOCASE, sale.card_condition COLLATE NOCASE
        """,
        (DEFAULT_CARD_CONDITION, card_id),
    ).fetchall()
    sellers = []
    for row in seller_rows:
        seller = dict(row)
        if not seller.get("store_share_id"):
            seller["store_share_id"] = new_store_share_id(conn)
            conn.execute("UPDATE users SET store_share_id = ? WHERE id = ?", (seller["store_share_id"], row["user_id"]))
        seller["seller_name"] = public_display_name(row, "Seller")
        seller_role = effective_user_role(row)
        seller["seller_role"] = seller_role
        seller["seller_is_pro"] = seller_role in {"admin", "contributor", "pro"}
        seller["store_url"] = store_share_url(seller["store_share_id"])
        seller["is_current_user"] = bool(current_user_id and int(current_user_id) == int(row["user_id"]))
        seller["favorite_store"] = False
        if current_user_id and not seller["is_current_user"]:
            seller["favorite_store"] = bool(conn.execute(
                """
                SELECT 1
                FROM favorite_store_listings
                WHERE user_id = ? AND seller_user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
                """,
                (current_user_id, row["user_id"], card_id, seller["variant"], seller["card_condition"]),
            ).fetchone())
        seller["listing_key"] = sale_listing_key(row["user_id"], card_id, seller["variant"], seller["card_condition"])
        sellers.append(seller)
    card_payload["favorite_store"] = any(seller.get("favorite_store") for seller in sellers)
    card_payload["favorite_store_count"] = sum(1 for seller in sellers if seller.get("favorite_store"))
    conn.commit()
    return {"card": card_payload, "sellers": sellers}


def profile_url_from_slug(slug):
    return f"{verification_base_url()}/user/{urllib.parse.quote(slug or '')}"


def public_profile_contacts(user):
    contact_email = user["public_email"] or user["email"]
    contacts = [
        {"label": "Email", "value": contact_email, "href": f"mailto:{contact_email}"},
        {"label": "Discord", "value": user["contact_discord"], "href": ""},
        {"label": "Instagram", "value": user["contact_instagram"], "href": f"https://instagram.com/{user['contact_instagram'].lstrip('@')}" if user["contact_instagram"] else ""},
        {"label": "Bluesky", "value": user["contact_bluesky"], "href": f"https://bsky.app/profile/{user['contact_bluesky'].lstrip('@')}" if user["contact_bluesky"] else ""},
        {"label": "Threads", "value": user["contact_threads"], "href": f"https://threads.net/@{user['contact_threads'].lstrip('@')}" if user["contact_threads"] else ""},
        {"label": "WhatsApp", "value": user["contact_whatsapp"], "href": ""},
        {"label": "Signal", "value": user["contact_signal"], "href": ""},
        {"label": "Telegram", "value": user["contact_telegram"], "href": f"https://t.me/{user['contact_telegram'].lstrip('@')}" if user["contact_telegram"] else ""},
        {"label": "Website", "value": user["contact_website"], "href": user["contact_website"]},
        {"label": "Whatnot", "value": user["contact_whatnot"], "href": whatnot_profile_url(user["contact_whatnot"]) if user["contact_whatnot"] else ""},
    ]
    return [contact for contact in contacts if contact["value"]]


def public_profile_stats(conn, user_id):
    price_expr = (
        "CASE "
        "WHEN lower(coalesce(col.variant, '')) LIKE '%etched%' AND c.current_usd_etched > 0 THEN c.current_usd_etched "
        "WHEN lower(coalesce(col.variant, '')) LIKE '%foil%' AND c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd > 0 THEN c.current_usd "
        "WHEN c.current_usd_foil > 0 THEN c.current_usd_foil "
        "WHEN c.current_usd_etched > 0 THEN c.current_usd_etched "
        "ELSE 0 END"
    )
    row = conn.execute(
        f"""
        SELECT COALESCE(SUM(col.quantity), 0) AS owned_quantity,
               COUNT(DISTINCT col.card_id) AS unique_cards,
               COALESCE(SUM(col.quantity * ({price_expr})), 0) AS collection_value
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        WHERE col.user_id = ? AND COALESCE(col.quantity, 0) > 0
        """,
        (user_id,),
    ).fetchone()
    deck_count = conn.execute(
        "SELECT COUNT(*) AS count FROM decks WHERE user_id = ? AND COALESCE(is_private, 0) = 0",
        (user_id,),
    ).fetchone()
    sale_row = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) AS quantity, COUNT(*) AS listings FROM card_sales WHERE user_id = ? AND COALESCE(quantity, 0) > 0",
        (user_id,),
    ).fetchone()
    return {
        "owned_quantity": int(row["owned_quantity"] or 0),
        "unique_cards": int(row["unique_cards"] or 0),
        "collection_value": float(row["collection_value"] or 0),
        "public_deck_count": int(deck_count["count"] or 0),
        "sale_quantity": int(sale_row["quantity"] or 0),
        "sale_listing_count": int(sale_row["listings"] or 0),
    }


def public_profile_decks(conn, user_id):
    rows = conn.execute(
        """
        SELECT d.id, d.share_id, d.name,
               COALESCE(d.description, '') AS description,
               d.updated_at,
               COALESCE(SUM(dc.quantity), 0) AS card_count,
               COUNT(dc.card_id) AS unique_card_count,
               (
                   SELECT GROUP_CONCAT(image, '|||')
                   FROM (
                       SELECT DISTINCT COALESCE(NULLIF(c2.image_normal, ''), NULLIF(c2.image_small, '')) AS image
                       FROM deck_cards dc2
                       JOIN cards c2 ON c2.scryfall_id = dc2.card_id
                       WHERE dc2.deck_id = d.id
                         AND COALESCE(NULLIF(c2.image_normal, ''), NULLIF(c2.image_small, '')) IS NOT NULL
                       ORDER BY RANDOM()
                       LIMIT 5
                   )
               ) AS preview_images
        FROM decks d
        LEFT JOIN deck_cards dc ON dc.deck_id = d.id
        WHERE d.user_id = ? AND COALESCE(d.is_private, 0) = 0
        GROUP BY d.id
        ORDER BY d.updated_at DESC, d.name COLLATE NOCASE
        LIMIT 12
        """,
        (user_id,),
    ).fetchall()
    decks = rows_to_dicts(rows)
    for deck in decks:
        deck["preview_images"] = [image for image in (deck.get("preview_images") or "").split("|||") if image][:5]
        deck["deck_url"] = deck_share_url(deck)
    return decks


def clean_profile_activity_text(value, label, limit=1200):
    text = re.sub(r"\r\n?", "\n", (value or "").strip())
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    if not text:
        raise ValueError(f"{label} is required.")
    if len(text) > limit:
        raise ValueError(f"{label} must be {limit} characters or fewer.")
    return text


def profile_user_by_slug(conn, slug):
    normalized_slug = profile_slug(slug)
    user = conn.execute(
        """
        SELECT id, name, email, created_at, store_share_id, public_email, contact_whatsapp, contact_signal,
               contact_telegram, contact_discord, contact_website, contact_whatnot, contact_mtg_arena, contact_mtgo,
               contact_instagram, contact_bluesky,
               contact_threads, about_me, profile_image, profile_slug, role, subscription_status
        FROM users
        WHERE profile_slug = ? AND COALESCE(is_banned, 0) = 0
        """,
        (normalized_slug,),
    ).fetchone()
    if not user:
        raise KeyError("User profile not found")
    return user


def profile_actor_payload(row):
    role = effective_user_role(row)
    return {
        "id": row["id"],
        "name": row["name"],
        "profile_slug": row["profile_slug"],
        "profile_url": f"/user/{urllib.parse.quote(row['profile_slug'])}" if row["profile_slug"] else "",
        "profile_image": row["profile_image"] if "profile_image" in row.keys() else "",
        "role": role,
        "is_pro": role in {"admin", "contributor", "pro"},
    }


def profile_friend_rows(conn, user_id):
    rows = conn.execute(
        """
        SELECT u.id, u.name, u.email, u.profile_slug, u.profile_image, u.role, u.subscription_status, f.created_at
        FROM profile_friends f
        JOIN users u ON u.id = f.friend_user_id
        WHERE f.user_id = ? AND COALESCE(u.is_banned, 0) = 0
        ORDER BY f.created_at DESC, u.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    friends = []
    for row in rows:
        friend = profile_actor_payload(row)
        friend["created_at"] = row["created_at"]
        friends.append(friend)
    return friends


def profile_wall_rows(conn, profile_user_id):
    rows = conn.execute(
        """
        SELECT m.id, m.body, m.created_at,
               u.id AS author_id, u.name, u.email, u.profile_slug, u.profile_image,
               u.role, u.subscription_status
        FROM profile_wall_messages m
        JOIN users u ON u.id = m.author_user_id
        WHERE m.profile_user_id = ? AND COALESCE(u.is_banned, 0) = 0
        ORDER BY m.created_at DESC
        LIMIT 30
        """,
        (profile_user_id,),
    ).fetchall()
    messages = []
    for row in rows:
        role = effective_user_role(row)
        messages.append({
            "id": row["id"],
            "body": row["body"],
            "created_at": row["created_at"],
            "author": {
                "id": row["author_id"],
                "name": row["name"],
                "profile_slug": row["profile_slug"],
                "profile_url": f"/user/{urllib.parse.quote(row['profile_slug'])}" if row["profile_slug"] else "",
                "profile_image": row["profile_image"],
                "role": role,
                "is_pro": role in {"admin", "contributor", "pro"},
            },
        })
    return messages


def profile_post_rows(conn, profile_user_id, limit=20):
    limit = max(1, min(int(limit or 20), 5000))
    post_rows = conn.execute(
        """
        SELECT p.id, p.body, p.card_id, p.deck_id, p.variant, p.created_at, p.updated_at,
               c.scryfall_id, c.name, c.flavor_name, c.set_code, c.set_name, c.collector_number,
               c.rarity, c.type_line, c.colors, c.image_small, c.image_normal, c.scryfall_uri,
               c.current_usd, c.current_usd_foil, c.current_usd_etched,
               d.share_id AS deck_share_id, d.name AS deck_name, d.description AS deck_description,
               d.is_private AS deck_is_private,
               COALESCE(SUM(dc.quantity), 0) AS deck_card_count,
               COUNT(dc.card_id) AS deck_unique_card_count,
               (
                   SELECT GROUP_CONCAT(image, '|||')
                   FROM (
                       SELECT DISTINCT COALESCE(NULLIF(c2.image_normal, ''), NULLIF(c2.image_small, '')) AS image
                       FROM deck_cards dc2
                       JOIN cards c2 ON c2.scryfall_id = dc2.card_id
                       WHERE dc2.deck_id = d.id
                         AND COALESCE(NULLIF(c2.image_normal, ''), NULLIF(c2.image_small, '')) IS NOT NULL
                       ORDER BY RANDOM()
                       LIMIT 5
                   )
               ) AS deck_preview_images
        FROM profile_posts p
        LEFT JOIN cards c ON c.scryfall_id = p.card_id
        LEFT JOIN decks d ON d.id = p.deck_id
        LEFT JOIN deck_cards dc ON dc.deck_id = d.id
        WHERE p.user_id = ?
        GROUP BY p.id
        ORDER BY p.created_at DESC
        LIMIT ?
        """,
        (profile_user_id, limit),
    ).fetchall()
    posts = []
    for row in post_rows:
        post = {
            "id": row["id"],
            "body": row["body"],
            "card_id": row["card_id"],
            "deck_id": row["deck_id"],
            "variant": row["variant"] or "Normal",
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "card": None,
            "deck": None,
        }
        if row["scryfall_id"]:
            post["card"] = {
                "scryfall_id": row["scryfall_id"],
                "name": row["name"],
                "flavor_name": row["flavor_name"],
                "set_code": row["set_code"],
                "set_name": row["set_name"],
                "collector_number": row["collector_number"],
                "rarity": row["rarity"],
                "type_line": row["type_line"],
                "colors": row["colors"],
                "image_small": row["image_small"],
                "image_normal": row["image_normal"],
                "scryfall_uri": row["scryfall_uri"],
                "current_usd": row["current_usd"],
                "current_usd_foil": row["current_usd_foil"],
                "current_usd_etched": row["current_usd_etched"],
                "variant": row["variant"] or "Normal",
                "display_price": price_for_variant_from_row(row, row["variant"] or "Normal"),
            }
        if row["deck_id"]:
            post["deck"] = {
                "id": row["deck_id"],
                "share_id": row["deck_share_id"],
                "name": row["deck_name"],
                "description": row["deck_description"],
                "is_private": row["deck_is_private"],
                "card_count": row["deck_card_count"],
                "unique_card_count": row["deck_unique_card_count"],
                "preview_images": [image for image in (row["deck_preview_images"] or "").split("|||") if image][:5],
                "deck_url": deck_share_url({"share_id": row["deck_share_id"]}) if row["deck_share_id"] else "",
            }
        posts.append(post)
    if not posts:
        return []
    post_ids = [post["id"] for post in posts]
    placeholders = ",".join("?" for _ in post_ids)
    comment_rows = conn.execute(
        f"""
        SELECT c.id, c.post_id, c.parent_comment_id, c.body, c.created_at,
               u.id AS author_id, u.name, u.email, u.profile_slug, u.profile_image,
               u.role, u.subscription_status
        FROM profile_post_comments c
        JOIN users u ON u.id = c.author_user_id
        WHERE c.post_id IN ({placeholders}) AND COALESCE(u.is_banned, 0) = 0
        ORDER BY c.created_at ASC
        """,
        post_ids,
    ).fetchall()
    comments_by_post = {post["id"]: [] for post in posts}
    for row in comment_rows:
        role = effective_user_role(row)
        comments_by_post.setdefault(row["post_id"], []).append({
            "id": row["id"],
            "post_id": row["post_id"],
            "parent_comment_id": row["parent_comment_id"],
            "body": row["body"],
            "created_at": row["created_at"],
            "author": {
                "id": row["author_id"],
                "name": row["name"],
                "profile_slug": row["profile_slug"],
                "profile_url": f"/user/{urllib.parse.quote(row['profile_slug'])}" if row["profile_slug"] else "",
                "profile_image": row["profile_image"],
                "role": role,
                "is_pro": role in {"admin", "contributor", "pro"},
            },
        })
    for post in posts:
        post["comments"] = comments_by_post.get(post["id"], [])
    return posts


def profile_posts_for_card(conn, card_id, variant=None):
    card = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    params = [card_id]
    variant_filter = ""
    if variant:
        variant_filter = " AND COALESCE(p.variant, 'Normal') = ?"
        params.append(variant)
    rows = conn.execute(
        f"""
        SELECT p.id, p.body, p.variant, p.created_at,
               u.id AS author_id, u.name, u.email, u.profile_slug, u.profile_image,
               u.role, u.subscription_status
        FROM profile_posts p
        JOIN users u ON u.id = p.user_id
        WHERE p.card_id = ? {variant_filter} AND COALESCE(u.is_banned, 0) = 0
        ORDER BY p.created_at DESC
        LIMIT 50
        """,
        params,
    ).fetchall()
    card_payload = dict(card)
    card_payload["variant"] = variant or "Normal"
    card_payload["display_price"] = price_for_variant_from_row(card, variant or "Normal")
    posts = []
    for row in rows:
        role = effective_user_role(row)
        posts.append({
            "id": row["id"],
            "body": row["body"],
            "variant": row["variant"] or "Normal",
            "created_at": row["created_at"],
            "author": {
                "id": row["author_id"],
                "name": row["name"],
                "profile_slug": row["profile_slug"],
                "profile_url": f"/user/{urllib.parse.quote(row['profile_slug'])}" if row["profile_slug"] else "",
                "profile_image": row["profile_image"],
                "role": role,
                "is_pro": role in {"admin", "contributor", "pro"},
            },
        })
    return {
        "card": card_payload,
        "posts": posts,
    }


def public_user_profile(conn, slug, viewer_user_id=None, view="profile"):
    view = (view or "profile").lower()
    if view not in {"profile", "blog", "favorites"}:
        view = "profile"
    user = profile_user_by_slug(conn, slug)
    role = effective_user_role(user)
    is_self = bool(viewer_user_id and int(viewer_user_id) == int(user["id"]))
    is_friend = False
    if viewer_user_id and not is_self:
        is_friend = bool(conn.execute(
            "SELECT 1 FROM profile_friends WHERE user_id = ? AND friend_user_id = ?",
            (viewer_user_id, user["id"]),
        ).fetchone())
    stats = public_profile_stats(conn, user["id"])
    full_view = view in {"blog", "favorites"}
    favorite_limit = 5000 if full_view else 6
    post_limit = 5000 if full_view else 3
    favorite_cards = list_cards(conn, f"owned=owned&favorite=1&sort=favorite&limit={favorite_limit}", user["id"])
    store_url = store_share_url(user["store_share_id"]) if stats["sale_quantity"] > 0 else ""
    payload = {
        "view": view,
        "name": user["name"],
        "profile_slug": user["profile_slug"],
        "profile_url": profile_url_from_slug(user["profile_slug"]),
        "profile_image": user["profile_image"],
        "role": role,
        "is_pro": role in {"admin", "contributor", "pro"},
        "about_me": user["about_me"],
        "member_since": user["created_at"],
        "contacts": public_profile_contacts(user),
        "whatnot_username": user["contact_whatnot"],
        "whatnot_url": whatnot_profile_url(user["contact_whatnot"]) if user["contact_whatnot"] else "",
        "mtg_arena_username": user["contact_mtg_arena"],
        "mtgo_username": user["contact_mtgo"],
        "stats": stats,
        "favorites": favorite_cards,
        "public_decks": public_profile_decks(conn, user["id"]),
        "store_url": store_url,
        "wall_messages": profile_wall_rows(conn, user["id"]),
        "posts": profile_post_rows(conn, user["id"], post_limit),
        "is_self": is_self,
        "is_friend": is_friend,
        "can_add_friend": bool(viewer_user_id and not is_self and not is_friend),
        "can_post_wall": bool(viewer_user_id),
        "can_post_blog": is_self,
        "can_comment": bool(viewer_user_id),
        "readonly": not is_self,
    }
    if is_self:
        payload["friends"] = profile_friend_rows(conn, user["id"])
    return payload


def add_profile_friend(conn, user_id, slug):
    target = profile_user_by_slug(conn, slug)
    if int(target["id"]) == int(user_id):
        raise ValueError("You cannot add yourself as a friend.")
    conn.execute(
        """
        INSERT OR IGNORE INTO profile_friends (user_id, friend_user_id, created_at)
        VALUES (?, ?, ?)
        """,
        (user_id, target["id"], now_iso()),
    )
    conn.commit()
    return {"ok": True, "profile": public_user_profile(conn, target["profile_slug"], user_id)}


def add_profile_wall_message(conn, user_id, slug, payload):
    target = profile_user_by_slug(conn, slug)
    body = clean_profile_activity_text(payload.get("body"), "Message", 800)
    conn.execute(
        """
        INSERT INTO profile_wall_messages (profile_user_id, author_user_id, body, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (target["id"], user_id, body, now_iso()),
    )
    conn.commit()
    return {"ok": True, "profile": public_user_profile(conn, target["profile_slug"], user_id)}


def add_profile_post(conn, user_id, slug, payload):
    target = profile_user_by_slug(conn, slug)
    if int(target["id"]) != int(user_id):
        raise ForbiddenError("Only the profile owner can post blog updates.")
    body = clean_profile_activity_text(payload.get("body"), "Post", 2400)
    card_id = (payload.get("card_id") or "").strip()
    deck_id = payload.get("deck_id")
    deck_id = int(deck_id) if deck_id not in (None, "", 0, "0") else None
    variant = (payload.get("variant") or "Normal").strip() or "Normal"
    if card_id:
        if not conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone():
            raise KeyError("Card not found")
    else:
        card_id = None
    if deck_id:
        if not conn.execute("SELECT 1 FROM decks WHERE id = ? AND user_id = ?", (deck_id, user_id)).fetchone():
            raise KeyError("Deck not found")
    created = now_iso()
    conn.execute(
        """
        INSERT INTO profile_posts (user_id, body, card_id, deck_id, variant, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, body, card_id, deck_id, variant, created, created),
    )
    conn.commit()
    return {"ok": True, "profile": public_user_profile(conn, target["profile_slug"], user_id)}


def add_profile_post_comment(conn, user_id, post_id, payload):
    post = conn.execute(
        """
        SELECT p.id, p.user_id, u.profile_slug
        FROM profile_posts p
        JOIN users u ON u.id = p.user_id
        WHERE p.id = ?
        """,
        (post_id,),
    ).fetchone()
    if not post:
        raise KeyError("Profile post not found")
    parent_id = payload.get("parent_comment_id")
    parent_id = int(parent_id) if parent_id not in (None, "", 0, "0") else None
    if parent_id:
        parent = conn.execute(
            "SELECT 1 FROM profile_post_comments WHERE id = ? AND post_id = ?",
            (parent_id, post_id),
        ).fetchone()
        if not parent:
            raise ValueError("Reply target was not found.")
    body = clean_profile_activity_text(payload.get("body"), "Comment", 1000)
    conn.execute(
        """
        INSERT INTO profile_post_comments (post_id, author_user_id, parent_comment_id, body, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (post_id, user_id, parent_id, body, now_iso()),
    )
    conn.commit()
    return {"ok": True, "profile": public_user_profile(conn, post["profile_slug"], user_id)}


def shared_store(conn, share_id):
    user = conn.execute(
        """
        SELECT id, name, email, store_share_id, public_email, contact_whatsapp, contact_signal,
               contact_telegram, contact_discord, contact_website, contact_whatnot, role, subscription_status
        FROM users
        WHERE store_share_id = ?
        """,
        (share_id,),
    ).fetchone()
    if not user:
        raise KeyError("Store not found")
    cards = list_sale_cards(conn, "sort=value&limit=5000", user["id"])
    contact_email = user["public_email"] or user["email"]
    contacts = [
        {"label": "Email", "value": contact_email, "href": f"mailto:{contact_email}"},
        {"label": "WhatsApp", "value": user["contact_whatsapp"], "href": ""},
        {"label": "Signal", "value": user["contact_signal"], "href": ""},
        {"label": "Telegram", "value": user["contact_telegram"], "href": f"https://t.me/{user['contact_telegram'].lstrip('@')}" if user["contact_telegram"] else ""},
        {"label": "Discord", "value": user["contact_discord"], "href": ""},
        {"label": "Website", "value": user["contact_website"], "href": user["contact_website"]},
        {"label": "Whatnot", "value": user["contact_whatnot"], "href": whatnot_profile_url(user["contact_whatnot"]) if user["contact_whatnot"] else ""},
    ]
    seller_role = effective_user_role(user)
    return {
        "share_id": share_id,
        "seller_name": public_display_name(user, "Seller"),
        "seller_role": seller_role,
        "seller_is_pro": seller_role in {"admin", "contributor", "pro"},
        "contact_email": contact_email,
        "contacts": [contact for contact in contacts if contact["value"]],
        "cards": cards,
        "card_count": len(cards),
        "sale_quantity": sum(int(card.get("sale_quantity") or 0) for card in cards),
        "readonly": True,
    }


def shared_card_identity(conn, share_id):
    row = conn.execute(
        """
        SELECT card_id, COALESCE(NULLIF(variant, ''), 'Normal') AS variant
        FROM collection
        WHERE share_id = ?
        """,
        (share_id,),
    ).fetchone()
    if not row:
        raise KeyError("Shared card not found")
    return row


def shared_card(conn, share_id, user_id=None):
    identity = shared_card_identity(conn, share_id)
    if user_id:
        card = card_detail(conn, user_id, identity["card_id"], identity["variant"])
        if not card.get("share_id"):
            card["share_id"] = share_id
        card["shared_source_id"] = share_id
        card["personalized"] = True
        return card
    row = conn.execute(
        """
        SELECT c.*, ? AS share_id, ? AS variant,
               0 AS quantity,
               CASE
                   WHEN lower(?) LIKE '%etched%' AND c.current_usd_etched > 0 THEN c.current_usd_etched
                   WHEN lower(?) LIKE '%foil%' AND c.current_usd_foil > 0 THEN c.current_usd_foil
                   WHEN c.current_usd > 0 THEN c.current_usd
                   WHEN c.current_usd_foil > 0 THEN c.current_usd_foil
                   WHEN c.current_usd_etched > 0 THEN c.current_usd_etched
                   ELSE 0
               END AS display_price,
               1 AS readonly
        FROM cards c
        WHERE c.scryfall_id = ?
        """,
        (share_id, identity["variant"], identity["variant"], identity["variant"], identity["card_id"]),
    ).fetchone()
    if not row:
        raise KeyError("Shared card not found")
    return dict(row)


def card_share_url(card):
    share_id = card.get("share_id") if isinstance(card, dict) else card["share_id"]
    return f"{verification_base_url()}/cards/{urllib.parse.quote(share_id)}"


def card_public_url(card):
    if isinstance(card, dict):
        card_id = card.get("scryfall_id") or card.get("card_id") or ""
        variant = card.get("variant") or "Normal"
    else:
        card_id = card["scryfall_id"]
        variant = card["variant"] or "Normal"
    return f"{verification_base_url()}/card/{urllib.parse.quote(card_id)}/{urllib.parse.quote(variant)}"


def news_public_url(post_id):
    return f"{verification_base_url()}/news/{urllib.parse.quote(str(post_id))}"


def news_email_html(post, share_url, sender_name):
    title = html_lib.escape(post.get("title") or "Arcane Ledger News")
    safe_sender = html_lib.escape(sender_name or "An Arcane Ledger user")
    safe_url = html_lib.escape(share_url)
    body = html_lib.escape(post.get("body") or "").replace("\n", "<br>")
    return f"""
    <!doctype html>
    <html>
      <body style="margin:0;background:#f4f7f5;color:#111816;font-family:Arial,Helvetica,sans-serif;">
        <div style="max-width:760px;margin:0 auto;padding:24px;">
          <h1 style="margin:0 0 8px;font-size:28px;line-height:1.1;">{title}</h1>
          <p style="margin:0 0 16px;color:#586661;">{safe_sender} shared this Arcane Ledger news article with you.</p>
          <p style="margin:0 0 20px;">
            <a href="{safe_url}" style="display:inline-block;background:#111816;color:#ffffff;text-decoration:none;padding:10px 14px;border-radius:8px;font-weight:700;">Open article</a>
          </p>
          <p style="margin:0 0 16px;color:#303936;word-break:break-all;">{safe_url}</p>
          <div style="background:#ffffff;border:1px solid #d7dedb;border-radius:8px;padding:16px;line-height:1.55;color:#303936;">{body}</div>
        </div>
      </body>
    </html>
    """


def news_email_text(post, share_url, sender_name):
    return "\n".join([
        f"{sender_name or 'An Arcane Ledger user'} shared this Arcane Ledger news article with you: {post.get('title') or 'News article'}",
        share_url,
        "",
        post.get("body") or "",
    ])


def email_news_post(conn, user, post_id, payload):
    recipient = validate_email(payload.get("email"))
    post = news_post_detail(conn, post_id)["post"]
    share_url = news_public_url(post_id)
    sender_name = user["name"] or user["email"]
    subject = f"Arcane Ledger: {sender_name} sharing news: {post.get('title') or 'News article'}"
    result = send_email(
        recipient,
        subject,
        text=news_email_text(post, share_url, sender_name),
        html=news_email_html(post, share_url, sender_name),
        tags=["arcaneledger", "news-share"],
    )
    return {"ok": True, "email": recipient, "provider": result.get("provider"), "status": result.get("status")}


def card_email_html(card, share_url, sender_name):
    title = html_lib.escape(card_email_title(card))
    safe_sender = html_lib.escape(sender_name or "An Arcane Ledger user")
    safe_url = html_lib.escape(share_url)
    set_text = html_lib.escape(" ".join(part for part in [
        card.get("set_name") or "",
        f"#{card.get('collector_number')}" if card.get("collector_number") else "",
        card.get("variant") or "",
    ] if part).strip())
    type_text = html_lib.escape(card.get("type_line") or card.get("type_category") or "")
    color_text = html_lib.escape(email_card_colors(card))
    market = money(card.get("display_price"), fallback=0)
    image_url = html_lib.escape(card.get("image_normal") or card.get("image_small") or "")
    image_html = f'<p><img src="{image_url}" alt="{title}" style="max-width:260px;width:100%;border-radius:12px;"></p>' if image_url else ""
    return f"""
    <!doctype html>
    <html>
      <body style="margin:0;background:#f4f7f5;color:#111816;font-family:Arial,Helvetica,sans-serif;">
        <div style="max-width:680px;margin:0 auto;padding:24px;">
          <h1 style="margin:0 0 8px;font-size:28px;line-height:1.1;">{title}</h1>
          <p style="margin:0 0 16px;color:#586661;">{safe_sender} shared this Arcane Ledger card with you.</p>
          <p style="margin:0 0 20px;">
            <a href="{safe_url}" style="display:inline-block;background:#111816;color:#ffffff;text-decoration:none;padding:10px 14px;border-radius:8px;font-weight:700;">Open card</a>
          </p>
          <p style="margin:0 0 16px;color:#303936;word-break:break-all;">{safe_url}</p>
          {image_html}
          <table role="presentation" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;background:#ffffff;border:1px solid #d7dedb;border-radius:8px;overflow:hidden;">
            <tbody>
              <tr><th style="text-align:left;padding:10px 8px;background:#e9efec;">Set</th><td style="padding:10px 8px;">{set_text}</td></tr>
              <tr><th style="text-align:left;padding:10px 8px;background:#e9efec;">Type</th><td style="padding:10px 8px;">{type_text}</td></tr>
              <tr><th style="text-align:left;padding:10px 8px;background:#e9efec;">Colors</th><td style="padding:10px 8px;">{color_text}</td></tr>
              <tr><th style="text-align:left;padding:10px 8px;background:#e9efec;">Market</th><td style="padding:10px 8px;">${market:.2f}</td></tr>
            </tbody>
          </table>
        </div>
      </body>
    </html>
    """


def card_email_text(card, share_url, sender_name):
    set_text = " ".join(part for part in [
        card.get("set_name") or "",
        f"#{card.get('collector_number')}" if card.get("collector_number") else "",
        card.get("variant") or "",
    ] if part).strip()
    return "\n".join([
        f"{sender_name or 'An Arcane Ledger user'} shared this Arcane Ledger card with you: {card_email_title(card)}",
        share_url,
        "",
        f"Set: {set_text}",
        f"Type: {card.get('type_line') or card.get('type_category') or ''}",
        f"Colors: {email_card_colors(card)}",
        f"Market: ${money(card.get('display_price'), fallback=0):.2f}",
    ])


def email_card(conn, user, card_id, payload):
    variant = payload.get("variant") or "Normal"
    card = card_detail(conn, user["id"], card_id, variant)
    recipient = validate_email(payload.get("email"))
    share_url = card_public_url(card)
    sender_name = user["name"] or user["email"]
    subject = f"Arcane Ledger: {sender_name} sharing card: {card_email_title(card)}"
    result = send_email(
        recipient,
        subject,
        text=card_email_text(card, share_url, sender_name),
        html=card_email_html(card, share_url, sender_name),
        tags=["arcaneledger", "card-share"],
    )
    return {"ok": True, "email": recipient, "provider": result.get("provider"), "status": result.get("status")}


def purchase_history(conn, user_id, card_id, variant):
    return rows_to_dicts(conn.execute(
        """
        SELECT purchase_date,
               card_condition,
               COALESCE(graded, 0) AS graded,
               store_name,
               store_location,
               GROUP_CONCAT(DISTINCT NULLIF(notes, '')) AS notes,
               SUM(quantity) AS quantity,
               SUM(total_price) AS total_price,
               ROUND(SUM(total_price) / SUM(quantity), 2) AS price_each,
               MIN(created_at) AS created_at
        FROM card_purchases
        WHERE user_id = ? AND card_id = ? AND variant = ?
        GROUP BY purchase_date, card_condition, COALESCE(graded, 0), store_name, store_location
        ORDER BY purchase_date DESC, created_at DESC
        """,
        (user_id, card_id, variant or "Normal"),
    ).fetchall())


def movement_history(conn, user_id, card_id, variant=None):
    variant_filter = "" if variant in (None, "", "All") else (variant or "Normal")
    variant_where = "AND variant = ?" if variant_filter else ""
    params = (user_id, card_id, variant_filter) if variant_filter else (user_id, card_id)
    purchases = rows_to_dicts(conn.execute(
        f"""
        SELECT 'buy' AS movement_type,
               id AS movement_id,
               COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
               purchase_date AS movement_date,
               card_condition,
               COALESCE(graded, 0) AS graded,
               quantity,
               total_price AS total_amount,
               ROUND(total_price / quantity, 2) AS price_each,
               created_at,
               store_name,
               store_location,
               notes,
               NULL AS asking_price_each
        FROM card_purchases
        WHERE user_id = ? AND card_id = ? {variant_where}
        """,
        params,
    ).fetchall())
    adjustments = rows_to_dicts(conn.execute(
        f"""
        SELECT 'adjust' AS movement_type,
               id AS movement_id,
               COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
               adjustment_type,
               adjustment_date AS movement_date,
               card_condition,
               quantity,
               0 AS total_amount,
               0 AS price_each,
               created_at,
               '' AS store_name,
               '' AS store_location,
               note
        FROM inventory_adjustments
        WHERE user_id = ? AND card_id = ? {variant_where}
        """,
        params,
    ).fetchall())
    sales = rows_to_dicts(conn.execute(
        f"""
        SELECT 'sell' AS movement_type,
               id AS movement_id,
               COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
               sold_date AS movement_date,
               card_condition,
               quantity,
               quantity * sold_price_each AS total_amount,
               sold_price_each AS price_each,
               created_at,
               '' AS store_name,
               '' AS store_location,
               '' AS note,
               asking_price_each
        FROM card_sale_journal
        WHERE user_id = ? AND card_id = ? {variant_where}
        """,
        params,
    ).fetchall())
    movements = purchases + sales + adjustments
    return sorted(
        movements,
        key=lambda item: (
            item.get("movement_date") or "",
            item.get("created_at") or "",
            1 if item.get("movement_type") == "sell" else 0,
        ),
        reverse=True,
    )


def purchase_entry_ledger(conn, user_id, card_id, movement_id):
    try:
        purchase_id = int(movement_id)
    except (TypeError, ValueError):
        raise ValueError("Choose a purchase entry to view.")
    source = conn.execute(
        """
        SELECT id, purchase_date, store_name, store_location
        FROM card_purchases
        WHERE user_id = ? AND card_id = ? AND id = ?
        """,
        (user_id, card_id, purchase_id),
    ).fetchone()
    if not source:
        raise KeyError("Purchase entry not found.")
    rows = conn.execute(
        """
        SELECT cp.id, cp.card_id, cp.variant, cp.quantity, cp.card_condition,
               COALESCE(cp.graded, 0) AS graded, cp.purchase_date, cp.total_price,
               ROUND(cp.total_price / cp.quantity, 2) AS price_each,
               cp.store_name, cp.store_location, cp.notes, cp.created_at,
               c.name, c.flavor_name, c.set_code, c.set_name, c.collector_number,
               c.rarity, c.type_line, c.image_small, c.image_normal, c.scryfall_uri
        FROM card_purchases cp
        JOIN cards c ON c.scryfall_id = cp.card_id
        WHERE cp.user_id = ?
          AND cp.purchase_date = ?
          AND COALESCE(cp.store_name, '') = COALESCE(?, '')
          AND COALESCE(cp.store_location, '') = COALESCE(?, '')
        ORDER BY c.set_code COLLATE NOCASE, CAST(c.collector_number AS INTEGER), c.collector_number COLLATE NOCASE,
                 COALESCE(NULLIF(c.flavor_name, ''), c.name) COLLATE NOCASE,
                 cp.variant COLLATE NOCASE, cp.card_condition COLLATE NOCASE, cp.id
        """,
        (user_id, source["purchase_date"], source["store_name"], source["store_location"]),
    ).fetchall()
    entries = []
    for row in rows:
        entries.append({
            "id": row["id"],
            "card_id": row["card_id"],
            "name": row["name"],
            "flavor_name": row["flavor_name"],
            "display_name": row["flavor_name"] or row["name"],
            "set_code": row["set_code"],
            "set_name": row["set_name"],
            "collector_number": row["collector_number"],
            "rarity": row["rarity"],
            "type_line": row["type_line"],
            "image_small": row["image_small"],
            "image_normal": row["image_normal"],
            "scryfall_uri": row["scryfall_uri"],
            "variant": row["variant"] or "Normal",
            "card_condition": card_condition(row["card_condition"]),
            "graded": int(row["graded"] or 0),
            "quantity": int(row["quantity"] or 0),
            "purchase_date": row["purchase_date"],
            "total_price": float(row["total_price"] or 0),
            "price_each": float(row["price_each"] or 0),
            "store_name": row["store_name"] or "",
            "store_location": row["store_location"] or "",
            "notes": row["notes"] or "",
            "created_at": row["created_at"],
        })
    total_quantity = sum(int(entry["quantity"] or 0) for entry in entries)
    total_paid = round(sum(float(entry["total_price"] or 0) for entry in entries), 2)
    return {
        "purchase_date": source["purchase_date"],
        "store_name": source["store_name"] or "",
        "store_location": source["store_location"] or "",
        "entry_count": len(entries),
        "total_quantity": total_quantity,
        "total_paid": total_paid,
        "average_paid": round(total_paid / total_quantity, 2) if total_quantity > 0 else 0,
        "entries": entries,
    }


def condition_inventory_for_card(conn, user_id, card_id):
    rows = conn.execute(
        """
        SELECT COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
               COALESCE(NULLIF(card_condition, ''), ?) AS card_condition,
               COALESCE(SUM(quantity), 0) AS quantity
        FROM card_purchases
        WHERE user_id = ? AND card_id = ?
        GROUP BY COALESCE(NULLIF(variant, ''), 'Normal'), COALESCE(NULLIF(card_condition, ''), ?)
        HAVING COALESCE(SUM(quantity), 0) > 0
        ORDER BY variant, card_condition
        """,
        (DEFAULT_CARD_CONDITION, user_id, card_id, DEFAULT_CARD_CONDITION),
    ).fetchall()
    total_by_variant = {}
    for row in rows:
        total_by_variant[row["variant"]] = total_by_variant.get(row["variant"], 0) + int(row["quantity"] or 0)
    deck_by_variant = {
        row["variant"]: int(row["quantity"] or 0)
        for row in conn.execute(
            """
            SELECT COALESCE(NULLIF(dc.variant, ''), 'Normal') AS variant,
                   COALESCE(SUM(dc.quantity), 0) AS quantity
            FROM deck_cards dc
            JOIN decks d ON d.id = dc.deck_id
            WHERE d.user_id = ? AND dc.card_id = ?
            GROUP BY COALESCE(NULLIF(dc.variant, ''), 'Normal')
            """,
            (user_id, card_id),
        ).fetchall()
    }
    sale_by_bucket = {
        (row["variant"], card_condition(row["card_condition"])): row
        for row in conn.execute(
            """
            SELECT COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
                   COALESCE(NULLIF(card_condition, ''), ?) AS card_condition,
                   COALESCE(quantity, 0) AS sale_quantity,
                   COALESCE(asking_price, 0.01) AS sale_price,
                   COALESCE(whatnot_url, '') AS whatnot_url
            FROM card_sales
            WHERE user_id = ? AND card_id = ?
            """,
            (DEFAULT_CARD_CONDITION, user_id, card_id),
        ).fetchall()
    }
    inventory = []
    saleable_remaining = {variant: max(0, total - deck_by_variant.get(variant, 0)) for variant, total in total_by_variant.items()}
    for row in rows:
        variant = row["variant"]
        condition = card_condition(row["card_condition"])
        sale_row = sale_by_bucket.get((variant, condition))
        quantity = int(row["quantity"] or 0)
        available = min(quantity, saleable_remaining.get(variant, quantity))
        saleable_remaining[variant] = max(0, saleable_remaining.get(variant, 0) - quantity)
        inventory.append({
            "variant": variant,
            "card_condition": condition,
            "quantity": quantity,
            "available_quantity": available,
            "sale_available_quantity": quantity,
            "sale_quantity": int(sale_row["sale_quantity"] or 0) if sale_row else 0,
            "sale_price": float(sale_row["sale_price"] or 0.01) if sale_row else 0.01,
            "whatnot_url": sale_row["whatnot_url"] if sale_row else "",
            "deck_reserved_quantity": max(0, deck_by_variant.get(variant, 0)),
        })
    return inventory


def card_deck_memberships(conn, user_id, card_id, variant):
    rows = conn.execute(
        """
        SELECT d.id, d.share_id, d.name, COALESCE(dc.quantity, 1) AS deck_quantity
        FROM deck_cards dc
        JOIN decks d ON d.id = dc.deck_id
        WHERE d.user_id = ? AND dc.card_id = ? AND COALESCE(NULLIF(dc.variant, ''), 'Normal') = ?
        ORDER BY d.name COLLATE NOCASE
        """,
        (user_id, card_id, variant or "Normal"),
    ).fetchall()
    return rows_to_dicts(rows)


def card_container_memberships(conn, user_id, card_id, variant=None):
    variant_filter = ""
    params = [DEFAULT_CARD_CONDITION, user_id, card_id]
    if variant:
        variant_filter = " AND COALESCE(NULLIF(cc.variant, ''), 'Normal') = ?"
        params.append(variant or "Normal")
    rows = conn.execute(
        f"""
        SELECT COALESCE(NULLIF(cc.variant, ''), 'Normal') AS variant,
               COALESCE(NULLIF(cc.card_condition, ''), ?) AS card_condition,
               cc.quantity, c.id, c.name, COALESCE(c.storage_type, 'other') AS storage_type,
               c.location
        FROM container_cards cc
        JOIN containers c ON c.id = cc.container_id
        WHERE c.user_id = ? AND cc.card_id = ?{variant_filter}
        ORDER BY c.name COLLATE NOCASE, cc.variant, cc.card_condition
        """,
        params,
    ).fetchall()
    memberships = rows_to_dicts(rows)
    for membership in memberships:
        membership["card_condition"] = card_condition(membership.get("card_condition"))
    return memberships


def snapshot_price_for_variant(row, variant):
    variant_text = (variant or "Normal").lower()
    values = {
        "normal": row["usd"] if "usd" in row.keys() else row.get("usd"),
        "foil": row["usd_foil"] if "usd_foil" in row.keys() else row.get("usd_foil"),
        "etched": row["usd_etched"] if "usd_etched" in row.keys() else row.get("usd_etched"),
    }
    if "etched" in variant_text and values["etched"]:
        return float(values["etched"] or 0)
    if "foil" in variant_text and values["foil"]:
        return float(values["foil"] or 0)
    for key in ("normal", "foil", "etched"):
        if values[key]:
            return float(values[key] or 0)
    return 0.0


def card_price_history(conn, card_id, variant="Normal", days=92):
    cutoff = (datetime.now(app_timezone()).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """
        SELECT snapshot_date, COALESCE(usd, 0) AS usd, COALESCE(usd_foil, 0) AS usd_foil,
               COALESCE(usd_etched, 0) AS usd_etched
        FROM price_snapshots
        WHERE card_id = ? AND snapshot_date >= ?
        ORDER BY snapshot_date ASC
        """,
        (card_id, cutoff),
    ).fetchall()
    points = []
    for row in rows:
        value = snapshot_price_for_variant(row, variant)
        if value > 0:
            points.append({"date": row["snapshot_date"], "value": round(value, 2)})
    return points


def card_price_histories(conn, card_id, variants=None, days=92):
    requested = []
    for variant in variants or ["Normal"]:
        variant = variant or "Normal"
        if variant not in requested:
            requested.append(variant)
    if "Normal" not in requested:
        requested.insert(0, "Normal")
    return [
        {
            "variant": variant,
            "points": card_price_history(conn, card_id, variant, days),
        }
        for variant in requested
    ]


def card_aggregate_stats(conn, card_id):
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT user_id) AS user_count,
               COALESCE(SUM(quantity), 0) AS total_quantity
        FROM collection
        WHERE card_id = ? AND quantity > 0
        """,
        (card_id,),
    ).fetchone()
    deck_count = conn.execute(
        """
        SELECT COUNT(DISTINCT dc.deck_id) AS deck_count
        FROM deck_cards dc
        JOIN decks d ON d.id = dc.deck_id
        WHERE dc.card_id = ?
        """,
        (card_id,),
    ).fetchone()["deck_count"] or 0
    favorite_count = conn.execute(
        """
        SELECT COUNT(DISTINCT user_id) AS favorite_count
        FROM card_meta
        WHERE card_id = ? AND COALESCE(favorite, 0) = 1
        """,
        (card_id,),
    ).fetchone()["favorite_count"] or 0
    wishlist_count = conn.execute(
        """
        SELECT COUNT(DISTINCT user_id) AS wishlist_count
        FROM (
            SELECT user_id FROM wishlist_items WHERE card_id = ?
            UNION
            SELECT user_id FROM wishlist_cards WHERE card_id = ?
            UNION
            SELECT user_id FROM card_meta WHERE card_id = ? AND COALESCE(wishlist, 0) = 1
        )
        WHERE user_id IS NOT NULL
        """,
        (card_id, card_id, card_id),
    ).fetchone()["wishlist_count"] or 0
    sale_user_count = conn.execute(
        """
        SELECT COUNT(DISTINCT user_id) AS sale_user_count
        FROM card_sales
        WHERE card_id = ? AND COALESCE(quantity, 0) > 0
        """,
        (card_id,),
    ).fetchone()["sale_user_count"] or 0
    return {
        "user_count": int(row["user_count"] or 0),
        "total_quantity": int(row["total_quantity"] or 0),
        "deck_count": int(deck_count),
        "favorite_count": int(favorite_count),
        "wishlist_count": int(wishlist_count),
        "sale_user_count": int(sale_user_count),
    }


def card_private_notes(conn, user_id, card_id, variant="Normal"):
    variant = variant or "Normal"
    row = conn.execute(
        "SELECT notes FROM card_notes WHERE user_id = ? AND card_id = ? AND variant = ?",
        (user_id, card_id, variant),
    ).fetchone()
    if row:
        return row["notes"] or ""
    legacy = conn.execute(
        "SELECT notes FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?",
        (user_id, card_id, variant),
    ).fetchone()
    return legacy["notes"] if legacy and legacy["notes"] else ""


def update_card_private_notes(conn, user_id, card_id, payload):
    variant = payload.get("variant") or "Normal"
    notes = (payload.get("notes") or "").strip()
    if len(notes) > 5000:
        raise ValueError("Notes must be 5000 characters or fewer.")
    conn.execute(
        """
        INSERT INTO card_notes (user_id, card_id, variant, notes, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
            notes = excluded.notes,
            updated_at = excluded.updated_at
        """,
        (user_id, card_id, variant, notes, now_iso()),
    )
    conn.commit()
    return {"ok": True, "notes": notes}


def card_comments(conn, user_id, card_id):
    rows = conn.execute(
        """
        SELECT cc.id, cc.card_id, cc.body, cc.created_at, cc.updated_at,
               u.id AS author_id, u.name, u.email, u.profile_slug, u.profile_image,
               u.role, u.subscription_status,
               COUNT(v.user_id) AS upvote_count,
               MAX(CASE WHEN v.user_id = ? THEN 1 ELSE 0 END) AS user_upvoted
        FROM card_comments cc
        JOIN users u ON u.id = cc.user_id
        LEFT JOIN card_comment_votes v ON v.comment_id = cc.id
        WHERE cc.card_id = ? AND COALESCE(u.is_banned, 0) = 0
        GROUP BY cc.id
        ORDER BY cc.created_at DESC
        LIMIT 80
        """,
        (user_id, card_id),
    ).fetchall()
    comments = []
    for row in rows:
        role = effective_user_role(row)
        comments.append({
            "id": row["id"],
            "card_id": row["card_id"],
            "body": row["body"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "upvote_count": int(row["upvote_count"] or 0),
            "user_upvoted": bool(row["user_upvoted"]),
            "can_upvote": int(row["author_id"]) != int(user_id),
            "author": {
                "id": row["author_id"],
                "name": row["name"],
                "profile_slug": row["profile_slug"],
                "profile_url": f"/user/{urllib.parse.quote(row['profile_slug'])}" if row["profile_slug"] else "",
                "profile_image": row["profile_image"],
                "role": role,
                "is_pro": role in {"admin", "contributor", "pro"},
            },
        })
    return comments


def add_card_comment(conn, user_id, card_id, payload):
    if not conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone():
        raise KeyError("Card not found")
    body = clean_profile_activity_text(payload.get("body"), "Comment", 1000)
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO card_comments (card_id, user_id, body, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (card_id, user_id, body, timestamp, timestamp),
    )
    conn.commit()
    return {"ok": True, "comments": card_comments(conn, user_id, card_id)}


def toggle_card_comment_upvote(conn, user_id, comment_id):
    comment = conn.execute(
        """
        SELECT id, card_id, user_id
        FROM card_comments
        WHERE id = ?
        """,
        (comment_id,),
    ).fetchone()
    if not comment:
        raise KeyError("Comment not found")
    if int(comment["user_id"]) == int(user_id):
        raise ValueError("You cannot upvote your own comment.")
    existing = conn.execute(
        "SELECT 1 FROM card_comment_votes WHERE comment_id = ? AND user_id = ?",
        (comment_id, user_id),
    ).fetchone()
    if existing:
        conn.execute(
            "DELETE FROM card_comment_votes WHERE comment_id = ? AND user_id = ?",
            (comment_id, user_id),
        )
        upvoted = False
    else:
        conn.execute(
            """
            INSERT INTO card_comment_votes (comment_id, user_id, created_at)
            VALUES (?, ?, ?)
            """,
            (comment_id, user_id, now_iso()),
        )
        upvoted = True
    conn.commit()
    return {"ok": True, "upvoted": upvoted, "comments": card_comments(conn, user_id, comment["card_id"])}


def card_detail(conn, user_id, card_id, variant="Normal"):
    variant = variant or "Normal"
    price_expr = current_price_sql("c")
    row = conn.execute(
        f"""
        SELECT c.*, col.share_id, COALESCE(col.quantity, 0) AS quantity,
               COALESCE(col.paid_price, 0.01) AS paid_price,
               COALESCE(col.variant, ?) AS variant,
               COALESCE(col.acquired_date, '') AS acquired_date,
               COALESCE(col.card_condition, 'Near Mint') AS card_condition,
               COALESCE(col.graded, 0) AS graded,
               COALESCE(col.notes, '') AS notes,
               COALESCE(meta.favorite, 0) AS favorite,
               COALESCE(meta.missing_list, 0) AS missing_list,
               COALESCE(meta.wishlist, 0) AS wishlist,
               ({price_expr}) AS display_price,
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value,
               COALESCE(col.quantity, 0) * (({price_expr}) - COALESCE(col.paid_price, 0.01)) AS gain_loss
        FROM cards c
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = c.scryfall_id AND col.variant = ?
        LEFT JOIN card_meta meta ON meta.user_id = ? AND meta.card_id = c.scryfall_id AND meta.variant = COALESCE(col.variant, ?)
        WHERE c.scryfall_id = ?
        """,
        (variant, user_id, variant, user_id, variant, card_id),
    ).fetchone()
    if not row:
        scryfall_card = request_json(SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id)))
        card = scryfall_card_detail_payload(scryfall_card, variant, user_id=user_id, conn=conn)
        card["variant_summaries"] = variant_summaries_for_cards(conn, [card_id], user_id).get(card_id, [])
        apply_card_collection_financials(card, conn, user_id, card_id)
        card["price_history"] = card_price_history(conn, card_id, variant)
        variants = [item.get("variant") for item in card.get("variant_summaries") or []] or [variant]
        card["price_histories"] = card_price_histories(conn, card_id, variants)
        card["aggregate_stats"] = card_aggregate_stats(conn, card_id)
        card["private_notes"] = card_private_notes(conn, user_id, card_id, variant)
        card["comments"] = card_comments(conn, user_id, card_id)
        return card
    card = dict(row)
    card["purchases"] = purchase_history(conn, user_id, card_id, variant)
    card["movements"] = movement_history(conn, user_id, card_id)
    card["selected_variant_movements"] = movement_history(conn, user_id, card_id, variant)
    card["condition_inventory"] = condition_inventory_for_card(conn, user_id, card_id)
    card["variant_summaries"] = variant_summaries_for_cards(conn, [card_id], user_id).get(card_id, [])
    apply_card_collection_financials(card, conn, user_id, card_id)
    card["deck_memberships"] = card_deck_memberships(conn, user_id, card_id, variant)
    card["container_memberships"] = card_container_memberships(conn, user_id, card_id)
    sale = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS sale_quantity,
               COALESCE(MAX(asking_price), 0) AS sale_price,
               COALESCE(MAX(whatnot_url), '') AS whatnot_url
        FROM card_sales
        WHERE user_id = ? AND card_id = ? AND COALESCE(NULLIF(variant, ''), 'Normal') = ?
        """,
        (user_id, card_id, variant),
    ).fetchone()
    container_quantity = sum(int(item.get("quantity") or 0) for item in card["container_memberships"])
    card["container_quantity"] = container_quantity
    card["unassigned_quantity"] = max(0, int(card.get("quantity") or 0) - container_quantity)
    card["sale_quantity"] = int(sale["sale_quantity"] or 0) if sale else 0
    card["sale_price"] = float(sale["sale_price"] or 0) if sale else 0
    card["whatnot_url"] = sale["whatnot_url"] if sale else ""
    card["price_history"] = card_price_history(conn, card_id, variant)
    variants = [item.get("variant") for item in card.get("variant_summaries") or []] or [variant]
    card["price_histories"] = card_price_histories(conn, card_id, variants)
    card["aggregate_stats"] = card_aggregate_stats(conn, card_id)
    card["private_notes"] = card_private_notes(conn, user_id, card_id, variant)
    card["comments"] = card_comments(conn, user_id, card_id)
    return card


def public_card_detail(conn, card_id, variant="Normal"):
    variant = variant or "Normal"
    row = conn.execute(
        """
        SELECT c.*, ? AS variant,
               0 AS quantity,
               CASE
                   WHEN lower(?) LIKE '%etched%' AND c.current_usd_etched > 0 THEN c.current_usd_etched
                   WHEN lower(?) LIKE '%foil%' AND c.current_usd_foil > 0 THEN c.current_usd_foil
                   WHEN c.current_usd > 0 THEN c.current_usd
                   WHEN c.current_usd_foil > 0 THEN c.current_usd_foil
                   WHEN c.current_usd_etched > 0 THEN c.current_usd_etched
                   ELSE 0
               END AS display_price,
               1 AS readonly
        FROM cards c
        WHERE c.scryfall_id = ?
        """,
        (variant, variant, variant, card_id),
    ).fetchone()
    if not row:
        scryfall_card = request_json(SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id)))
        card = scryfall_card_detail_payload(scryfall_card, variant)
        card["readonly"] = 1
        return card
    return dict(row)


def add_card_purchase(conn, user_id, card_id, payload):
    card = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    variant = payload.get("variant") or "Normal"
    quantity = max(1, int(money(payload.get("quantity"), fallback=1)))
    total_price = money(payload.get("total_price"), fallback=0.01)
    if total_price <= 0:
        total_price = 0.01
    purchase_date = payload.get("purchase_date") or today_iso()
    record_card_purchase(
        conn,
        user_id,
        card_id,
        variant,
        quantity,
        payload.get("card_condition"),
        purchase_date,
        total_price,
        payload.get("store_name"),
        payload.get("store_location"),
        payload.get("graded", 0),
        payload.get("notes"),
    )
    rollup_collection_from_purchases(conn, user_id, card_id, variant)
    upsert_price_snapshot_from_card_row(conn, card)
    conn.commit()
    return {"ok": True, "card": card_detail(conn, user_id, card_id, variant)}


def available_condition_quantity(conn, user_id, card_id, variant, condition):
    wanted_variant = variant or "Normal"
    wanted_condition = card_condition(condition)
    for bucket in condition_inventory_for_card(conn, user_id, card_id):
        if bucket["variant"] == wanted_variant and bucket["card_condition"] == wanted_condition:
            listed = conn.execute(
                """
                SELECT COALESCE(SUM(quantity), 0) AS quantity
                FROM card_sales
                WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
                """,
                (user_id, card_id, wanted_variant, wanted_condition),
            ).fetchone()
            return max(0, int(bucket["available_quantity"] or 0) - int((listed and listed["quantity"]) or 0))
    return 0


def adjust_card_inventory(conn, user_id, card_id, payload):
    card = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    variant = payload.get("variant") or "Normal"
    condition = card_condition(payload.get("card_condition"))
    action = (payload.get("adjustment_type") or "increase").strip().lower()
    if action not in {"increase", "decrease"}:
        raise ValueError("Choose whether to increase or decrease inventory.")
    quantity = int(money(payload.get("quantity"), fallback=1))
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")
    adjustment_date = payload.get("adjustment_date") or today_iso()
    if action == "increase":
        record_card_purchase(conn, user_id, card_id, variant, quantity, condition, adjustment_date, max(quantity * 0.01, 0.01))
        upsert_price_snapshot_from_card_row(conn, card)
    else:
        available = available_condition_quantity(conn, user_id, card_id, variant, condition)
        if quantity > available:
            raise ValueError(f"Only {available} copy/copies are available to remove for {variant} / {condition}. Remove deck assignments or sale listings first.")
        decrement_purchase_quantity(conn, user_id, card_id, variant, condition, quantity)
    conn.execute(
        """
        INSERT INTO inventory_adjustments (
            user_id, card_id, variant, card_condition, adjustment_type, quantity, adjustment_date, note, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, card_id, variant, condition, action, quantity, adjustment_date, payload.get("note") or "", now_iso()),
    )
    rollup_collection_from_purchases(conn, user_id, card_id, variant)
    conn.commit()
    return {"ok": True, "card": card_detail(conn, user_id, card_id, variant)}


def add_card_direct_sale(conn, user_id, card_id, payload):
    card = conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    variant = payload.get("variant") or "Normal"
    condition = card_condition(payload.get("card_condition"))
    quantity = int(money(payload.get("quantity"), fallback=1))
    if quantity < 1:
        raise ValueError("Sold quantity must be at least 1.")
    available = available_condition_quantity(conn, user_id, card_id, variant, condition)
    if quantity > available:
        raise ValueError(f"Only {available} copy/copies are available to sell for {variant} / {condition}.")
    sold_date = payload.get("sold_date") or today_iso()
    sold_price_each = money(payload.get("sold_price_each"), fallback=0.01)
    if sold_price_each <= 0:
        raise ValueError("Sold price must be greater than $0.00.")
    conn.execute(
        """
        INSERT INTO card_sale_journal (
            user_id, card_id, variant, card_condition, quantity, sold_date, sold_price_each, asking_price_each, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, card_id, variant, condition, quantity, sold_date, sold_price_each, sold_price_each, now_iso()),
    )
    decrement_purchase_quantity(conn, user_id, card_id, variant, condition, quantity)
    sale_row = conn.execute(
        """
        SELECT quantity
        FROM card_sales
        WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
        """,
        (user_id, card_id, variant, condition),
    ).fetchone()
    if sale_row:
        remaining_sale_quantity = max(0, int(sale_row["quantity"] or 0) - quantity)
        if remaining_sale_quantity:
            conn.execute(
                """
                UPDATE card_sales
                SET quantity = ?, updated_at = ?
                WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
                """,
                (remaining_sale_quantity, now_iso(), user_id, card_id, variant, condition),
            )
        else:
            conn.execute(
                "DELETE FROM card_sales WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?",
                (user_id, card_id, variant, condition),
            )
    rollup_collection_from_purchases(conn, user_id, card_id, variant)
    conn.commit()
    return {"ok": True, "card": card_detail(conn, user_id, card_id, variant)}


def update_collection(conn, user_id, card_id, payload):
    card = conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    quantity = max(0, int(payload.get("quantity") or 0))
    variant = payload.get("variant") or "Normal"
    original_variant = payload.get("original_variant") or variant
    paid_price = money(payload.get("paid_price"), fallback=0.01)
    if paid_price <= 0:
        paid_price = 0.01
    existing_collection = conn.execute(
        "SELECT share_id FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?",
        (user_id, card_id, original_variant),
    ).fetchone()
    existing_meta = conn.execute(
        "SELECT favorite, missing_list, wishlist FROM card_meta WHERE user_id = ? AND card_id = ? AND variant = ?",
        (user_id, card_id, original_variant),
    ).fetchone()
    current_allocated = allocated_quantity(conn, user_id, card_id, original_variant)
    if original_variant != variant and current_allocated > 0:
        raise ValueError("Remove this card from containers before changing its variant.")
    if quantity < current_allocated:
        raise ValueError(f"This card has {current_allocated} copy/copies stored in containers.")
    if quantity == 0:
        conn.execute("DELETE FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?", (user_id, card_id, original_variant))
    else:
        share_id = existing_collection["share_id"] if existing_collection and existing_collection["share_id"] else new_share_id(conn)
        if original_variant != variant:
            target_collection = conn.execute(
                "SELECT share_id FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?",
                (user_id, card_id, variant),
            ).fetchone()
            if target_collection and target_collection["share_id"]:
                share_id = target_collection["share_id"]
            conn.execute("DELETE FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?", (user_id, card_id, original_variant))
            conn.execute(
                "UPDATE card_purchases SET variant = ? WHERE user_id = ? AND card_id = ? AND variant = ?",
                (variant, user_id, card_id, original_variant),
            )
        conn.execute(
            """
            INSERT INTO collection (user_id, card_id, share_id, quantity, acquired_date, paid_price, variant, card_condition, graded, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
                share_id = COALESCE(collection.share_id, excluded.share_id),
                quantity = excluded.quantity,
                acquired_date = excluded.acquired_date,
                paid_price = excluded.paid_price,
                variant = excluded.variant,
                card_condition = excluded.card_condition,
                graded = excluded.graded,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                card_id,
                share_id,
                quantity,
                payload.get("acquired_date") or today_iso(),
                paid_price,
                variant,
                card_condition(payload.get("card_condition")),
                bool_int(payload.get("graded")),
                payload.get("notes") or "",
                now_iso(),
            ),
        )
        if existing_meta and original_variant != variant:
            conn.execute(
                """
                INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, wishlist, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
                    favorite = excluded.favorite,
                    missing_list = excluded.missing_list,
                    wishlist = excluded.wishlist,
                    updated_at = excluded.updated_at
                """,
                (user_id, card_id, variant, existing_meta["favorite"], existing_meta["missing_list"], existing_meta["wishlist"], now_iso()),
            )
        if quantity > 0:
            conn.execute(
                "UPDATE card_meta SET wishlist = 0, updated_at = ? WHERE user_id = ? AND card_id = ? AND variant = ?",
                (now_iso(), user_id, card_id, variant),
            )
            conn.execute(
                "DELETE FROM wishlist_items WHERE user_id = ? AND card_id = ?",
                (user_id, card_id),
            )
            conn.execute("DELETE FROM wishlist_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
    conn.commit()
    return {"ok": True}


def delete_collection_entry(conn, user_id, card_id, payload):
    variant = payload.get("variant") or "Normal"
    current_allocated = allocated_quantity(conn, user_id, card_id, variant)
    if current_allocated > 0:
        raise ValueError("Remove this card from containers before deleting it from your collection.")
    cursor = conn.execute(
        "DELETE FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?",
        (user_id, card_id, variant),
    )
    if cursor.rowcount == 0:
        raise KeyError("Collection entry not found")
    conn.execute(
        "DELETE FROM card_purchases WHERE user_id = ? AND card_id = ? AND variant = ?",
        (user_id, card_id, variant),
    )
    conn.commit()
    return {"ok": True, "deleted": {"card_id": card_id, "variant": variant}}


def update_favorite(conn, user_id, card_id, payload):
    card = conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    variant = payload.get("variant") or "Normal"
    favorite = 1 if payload.get("favorite") else 0
    conn.execute(
        """
        INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, updated_at)
        VALUES (?, ?, ?, ?, 0, ?)
        ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
            favorite = excluded.favorite,
            updated_at = excluded.updated_at
        """,
        (user_id, card_id, variant, favorite, now_iso()),
    )
    conn.commit()
    return {"ok": True, "favorite": bool(favorite)}


def wishlist_payload_summary(card_id, payload):
    candidate = payload.get("card") or payload.get("summary") or {}
    if candidate and candidate.get("scryfall_id"):
        summary = {
            "scryfall_id": candidate.get("scryfall_id") or card_id,
            "name": candidate.get("name") or "",
            "flavor_name": candidate.get("flavor_name") or "",
            "display_name": candidate.get("display_name") or candidate.get("flavor_name") or candidate.get("name") or "",
            "set_code": candidate.get("set_code") or "",
            "set_name": candidate.get("set_name") or "",
            "collector_number": candidate.get("collector_number") or "",
            "rarity": candidate.get("rarity") or "",
            "type_line": candidate.get("type_line") or "",
            "type_category": candidate.get("type_category") or card_type_category(candidate.get("type_line")),
            "colors": candidate.get("colors") or [],
            "color_identity": candidate.get("color_identity") or [],
            "flavor_text": candidate.get("flavor_text") or "",
            "finishes": candidate.get("finishes") or [],
            "image_small": candidate.get("image_small") or "",
            "image_normal": candidate.get("image_normal") or "",
            "scryfall_uri": candidate.get("scryfall_uri") or "",
            "prices": candidate.get("prices") or {},
            "owned_quantity": 0,
            "quantity": 0,
            "variant": payload.get("variant") or candidate.get("variant") or "Normal",
            "wishlist": 1,
            "catalog_only": True,
        }
        return summary
    scryfall_card = request_json(SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id)))
    summary = card_summary(scryfall_card, 0)
    summary["quantity"] = 0
    summary["variant"] = payload.get("variant") or "Normal"
    summary["wishlist"] = 1
    summary["catalog_only"] = True
    return summary


def cache_card_by_id(conn, card_id, scryfall_card=None):
    if scryfall_card is None:
        scryfall_card = request_json(SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id)))
    upsert_card(conn, scryfall_card, now_iso())
    return scryfall_card


def update_wishlist(conn, user_id, card_id, payload):
    card = conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    variant = payload.get("variant") or "Normal"
    wishlist = 1 if payload.get("wishlist") else 0
    wishlist_id = payload.get("wishlist_id")
    if wishlist_id in ("", None):
        wishlist_id = None
    else:
        wishlist_id = int(wishlist_id)
        if not conn.execute("SELECT 1 FROM wishlists WHERE id = ? AND user_id = ?", (wishlist_id, user_id)).fetchone():
            raise KeyError("Wishlist not found")
    if wishlist and wishlist_id is None:
        wishlist_id = ensure_default_wishlist(conn, user_id)
    summary_json = None
    scryfall_card_to_cache = None
    if wishlist:
        owned = conn.execute(
            """
            SELECT 1
            FROM collection
            WHERE user_id = ? AND card_id = ? AND COALESCE(quantity, 0) > 0
            LIMIT 1
            """,
            (user_id, card_id),
        ).fetchone()
        if owned:
            raise ValueError("Owned cards cannot be added to Wishlist.")
        if payload.get("card") or not card:
            if payload.get("card"):
                summary_json = json.dumps(wishlist_payload_summary(card_id, payload))
            else:
                scryfall_card_to_cache = request_json(SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id)))
                summary = card_summary(scryfall_card_to_cache, 0)
                summary["quantity"] = 0
                summary["variant"] = variant
                summary["wishlist"] = 1
                summary["catalog_only"] = True
                summary_json = json.dumps(summary)
    if not card:
        if wishlist:
            cache_card_by_id(conn, card_id, scryfall_card_to_cache)
            conn.execute(
                """
                INSERT INTO wishlist_items (wishlist_id, user_id, card_id, variant, card_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(wishlist_id, card_id, variant) DO UPDATE SET
                    card_json = excluded.card_json,
                    updated_at = excluded.updated_at
                """,
                (wishlist_id, user_id, card_id, variant, summary_json, now_iso()),
            )
            conn.execute("UPDATE wishlists SET updated_at = ? WHERE id = ?", (now_iso(), wishlist_id))
            conn.execute(
                """
                INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, wishlist, updated_at)
                VALUES (?, ?, ?, 0, 0, 1, ?)
                ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
                    wishlist = 1,
                    updated_at = excluded.updated_at
                """,
                (user_id, card_id, variant, now_iso()),
            )
        else:
            if wishlist_id is None:
                conn.execute("DELETE FROM wishlist_items WHERE user_id = ? AND card_id = ?", (user_id, card_id))
                conn.execute("DELETE FROM wishlist_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
            else:
                conn.execute("DELETE FROM wishlist_items WHERE user_id = ? AND wishlist_id = ? AND card_id = ? AND variant = ?", (user_id, wishlist_id, card_id, variant))
                conn.execute("UPDATE wishlists SET updated_at = ? WHERE id = ?", (now_iso(), wishlist_id))
        conn.commit()
        return {"ok": True, "wishlist": bool(wishlist), "catalog_only": True}
    if wishlist:
        conn.execute(
            """
            INSERT INTO wishlist_items (wishlist_id, user_id, card_id, variant, card_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(wishlist_id, card_id, variant) DO UPDATE SET
                card_json = COALESCE(excluded.card_json, wishlist_items.card_json),
                updated_at = excluded.updated_at
            """,
            (wishlist_id, user_id, card_id, variant, summary_json, now_iso()),
        )
        conn.execute("UPDATE wishlists SET updated_at = ? WHERE id = ?", (now_iso(), wishlist_id))
    else:
        if wishlist_id is None:
            conn.execute("DELETE FROM wishlist_items WHERE user_id = ? AND card_id = ? AND variant = ?", (user_id, card_id, variant))
        else:
            conn.execute("DELETE FROM wishlist_items WHERE user_id = ? AND wishlist_id = ? AND card_id = ? AND variant = ?", (user_id, wishlist_id, card_id, variant))
            conn.execute("UPDATE wishlists SET updated_at = ? WHERE id = ?", (now_iso(), wishlist_id))
        conn.execute("DELETE FROM wishlist_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
    still_wishlisted = conn.execute(
        """
        SELECT 1
        FROM wishlist_items
        WHERE user_id = ? AND card_id = ? AND variant = ?
        LIMIT 1
        """,
        (user_id, card_id, variant),
    ).fetchone()
    conn.execute(
        """
        INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, wishlist, updated_at)
        VALUES (?, ?, ?, 0, 0, ?, ?)
        ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
            wishlist = excluded.wishlist,
            updated_at = excluded.updated_at
        """,
        (user_id, card_id, variant, 1 if still_wishlisted else 0, now_iso()),
    )
    conn.commit()
    return {"ok": True, "wishlist": bool(still_wishlisted), "wishlist_id": wishlist_id}


def add_set_missing_to_missing_list(conn, user_id, set_code):
    set_code = (set_code or "").strip().lower()
    if not set_code:
        raise ValueError("Set code is required.")
    exists = conn.execute("SELECT 1 FROM cards WHERE lower(set_code) = ? LIMIT 1", (set_code,)).fetchone()
    if not exists:
        raise KeyError("Set not found")
    rows = conn.execute(
        """
        SELECT c.scryfall_id,
               COALESCE(meta.missing_list, 0) AS missing_list
        FROM cards c
        LEFT JOIN card_meta meta ON meta.user_id = ? AND meta.card_id = c.scryfall_id AND meta.variant = 'Normal'
        WHERE lower(c.set_code) = ?
          AND NOT EXISTS (
              SELECT 1
              FROM collection col
              WHERE col.user_id = ?
                AND col.card_id = c.scryfall_id
                AND COALESCE(col.quantity, 0) > 0
          )
        """,
        (user_id, set_code, user_id),
    ).fetchall()
    timestamp = now_iso()
    added = 0
    for row in rows:
        if not row["missing_list"]:
            added += 1
        conn.execute(
            """
            INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, updated_at)
            VALUES (?, ?, 'Normal', 0, 1, ?)
            ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
                missing_list = 1,
                updated_at = excluded.updated_at
            """,
            (user_id, row["scryfall_id"], timestamp),
        )
    conn.commit()
    return {"ok": True, "added": added, "tagged": len(rows), "set_code": set_code}


def set_missing_wishlist_name(set_name):
    suffix = " Missing List"
    name = (set_name or "Set").strip() or "Set"
    max_base = max(1, 30 - len(suffix))
    if len(name) + len(suffix) > 30:
        name = name[:max_base].rstrip()
    return f"{name}{suffix}"


def create_set_missing_wishlist(conn, user_id, set_code):
    set_code = (set_code or "").strip().lower()
    if not set_code:
        raise ValueError("Set code is required.")
    set_row = conn.execute(
        """
        SELECT COALESCE(s.name, MAX(c.set_name), ?) AS set_name
        FROM cards c
        LEFT JOIN sets s ON s.code = c.set_code
        WHERE lower(c.set_code) = ?
        GROUP BY c.set_code
        """,
        (set_code.upper(), set_code),
    ).fetchone()
    if not set_row:
        raise KeyError("Set not found")
    wishlist_name = set_missing_wishlist_name(set_row["set_name"])
    if cross_entity_name_exists(conn, user_id, wishlist_name):
        raise ValueError(f'A wishlist named "{wishlist_name}" already exists.')
    enforce_role_limit(conn, user_id, "wishlists", "wishlists", "wishlists")
    rows = conn.execute(
        """
        SELECT c.scryfall_id
        FROM cards c
        WHERE lower(c.set_code) = ?
          AND NOT EXISTS (
              SELECT 1
              FROM collection col
              WHERE col.user_id = ?
                AND col.card_id = c.scryfall_id
                AND COALESCE(col.quantity, 0) > 0
          )
        ORDER BY c.collector_number COLLATE NOCASE, c.name COLLATE NOCASE
        """,
        (set_code, user_id),
    ).fetchall()
    timestamp = now_iso()
    share_id = new_wishlist_share_id(conn)
    cursor = conn.execute(
        "INSERT INTO wishlists (user_id, share_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, share_id, wishlist_name, timestamp, timestamp),
    )
    wishlist_id = cursor.lastrowid
    for row in rows:
        conn.execute(
            """
            INSERT INTO wishlist_items (wishlist_id, user_id, card_id, variant, quantity, updated_at)
            VALUES (?, ?, ?, 'Normal', 1, ?)
            ON CONFLICT(wishlist_id, card_id, variant) DO UPDATE SET
                quantity = excluded.quantity,
                updated_at = excluded.updated_at
            """,
            (wishlist_id, user_id, row["scryfall_id"], timestamp),
        )
        conn.execute(
            """
            INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, wishlist, updated_at)
            VALUES (?, ?, 'Normal', 0, 0, 1, ?)
            ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
                wishlist = 1,
                updated_at = excluded.updated_at
            """,
            (user_id, row["scryfall_id"], timestamp),
        )
    conn.commit()
    return {
        "ok": True,
        "added": len(rows),
        "set_code": set_code,
        "wishlist": wishlist_detail(conn, user_id, wishlist_id),
    }


def update_cards_missing_list(conn, user_id, payload):
    cards = payload.get("cards") or []
    if not isinstance(cards, list) or not cards:
        raise ValueError("Choose at least one card.")
    missing_list = 1 if payload.get("missing_list", True) else 0
    timestamp = now_iso()
    updated = 0
    skipped_owned = 0
    for item in cards:
        if not isinstance(item, dict):
            continue
        card_id = item.get("card_id") or item.get("scryfall_id")
        variant = item.get("variant") or "Normal"
        if not card_id:
            continue
        card = conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
        if not card:
            if not missing_list:
                continue
            cache_card_by_id(conn, card_id)
        if missing_list:
            owned = conn.execute(
                """
                SELECT 1
                FROM collection
                WHERE user_id = ?
                  AND card_id = ?
                  AND COALESCE(quantity, 0) > 0
                LIMIT 1
                """,
                (user_id, card_id),
            ).fetchone()
            if owned:
                skipped_owned += 1
                continue
        conn.execute(
            """
            INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
            ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
                missing_list = excluded.missing_list,
                updated_at = excluded.updated_at
            """,
            (user_id, card_id, variant, missing_list, timestamp),
        )
        updated += 1
    conn.commit()
    return {"ok": True, "updated": updated, "skipped_owned": skipped_owned}


def update_cards_for_sale(conn, user_id, payload):
    cards = payload.get("cards") or []
    if not isinstance(cards, list) or not cards:
        raise ValueError("Choose at least one card.")
    for_sale = 1 if payload.get("for_sale", True) else 0
    timestamp = now_iso()
    updated = 0
    skipped = 0
    notifications = 0
    for item in cards:
        if not isinstance(item, dict):
            skipped += 1
            continue
        card_id = item.get("card_id") or item.get("scryfall_id")
        variant = item.get("variant") or "Normal"
        sale_condition = card_condition(item.get("card_condition"))
        if not card_id:
            skipped += 1
            continue
        if not for_sale:
            if item.get("card_condition"):
                cursor = conn.execute(
                    "DELETE FROM card_sales WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?",
                    (user_id, card_id, variant, sale_condition),
                )
                purge_store_listing_favorites(conn, user_id, card_id, variant, sale_condition)
            else:
                rows_to_purge = conn.execute(
                    """
                    SELECT variant, card_condition
                    FROM card_sales
                    WHERE user_id = ? AND card_id = ? AND variant = ?
                    """,
                    (user_id, card_id, variant),
                ).fetchall()
                cursor = conn.execute(
                    "DELETE FROM card_sales WHERE user_id = ? AND card_id = ? AND variant = ?",
                    (user_id, card_id, variant),
                )
                for row in rows_to_purge:
                    purge_store_listing_favorites(conn, user_id, card_id, row["variant"], row["card_condition"])
            updated += cursor.rowcount
            continue
        owned = conn.execute(
            """
            SELECT quantity, card_condition
            FROM collection
            WHERE user_id = ? AND card_id = ? AND variant = ? AND COALESCE(quantity, 0) > 0
            """,
            (user_id, card_id, variant),
        ).fetchone()
        if not owned:
            skipped += 1
            continue
        condition_owned = conn.execute(
            """
            SELECT SUM(quantity) AS quantity
            FROM card_purchases
            WHERE user_id = ?
              AND card_id = ?
              AND COALESCE(NULLIF(variant, ''), 'Normal') = ?
              AND COALESCE(NULLIF(card_condition, ''), ?) = ?
            """,
            (user_id, card_id, variant, DEFAULT_CARD_CONDITION, sale_condition),
        ).fetchone()
        max_quantity = int((condition_owned and condition_owned["quantity"]) or 0)
        if max_quantity <= 0 and sale_condition == card_condition(owned["card_condition"]):
            max_quantity = int(owned["quantity"] or 0)
        existing_other_sale = conn.execute(
            """
            SELECT COALESCE(SUM(quantity), 0) AS quantity
            FROM card_sales
            WHERE user_id = ?
              AND card_id = ?
              AND variant = ?
              AND card_condition != ?
            """,
            (user_id, card_id, variant, sale_condition),
        ).fetchone()
        saleable_for_condition = max_quantity
        if max_quantity <= 0:
            saleable_for_condition = max(0, int(owned["quantity"] or 0) - int((existing_other_sale and existing_other_sale["quantity"]) or 0))
        quantity = int(money(item.get("quantity"), fallback=1))
        if quantity < 1:
            raise ValueError("Sale quantity must be at least 1.")
        if quantity > max_quantity:
            raise ValueError("Sale quantity cannot exceed owned quantity.")
        if quantity > saleable_for_condition:
            raise ValueError(f"Only {saleable_for_condition} copy/copies are available to list for sale.")
        card_price = conn.execute(
            """
            SELECT current_usd, current_usd_foil, current_usd_etched
            FROM cards
            WHERE scryfall_id = ?
            """,
            (card_id,),
        ).fetchone()
        variant_key = variant.lower()
        if card_price and "etched" in variant_key and card_price["current_usd_etched"]:
            fallback_price = card_price["current_usd_etched"]
        elif card_price and "foil" in variant_key and card_price["current_usd_foil"]:
            fallback_price = card_price["current_usd_foil"]
        elif card_price:
            fallback_price = card_price["current_usd"] or card_price["current_usd_foil"] or card_price["current_usd_etched"] or 0.01
        else:
            fallback_price = 0.01
        asking_price = money(item.get("asking_price"), fallback=fallback_price)
        if asking_price <= 0:
            asking_price = 0.01
        whatnot_url = clean_whatnot_listing_url(item.get("whatnot_url"))
        conn.execute(
            """
            INSERT INTO card_sales (user_id, card_id, variant, card_condition, quantity, asking_price, whatnot_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, card_id, variant, card_condition) DO UPDATE SET
                quantity = excluded.quantity,
                asking_price = excluded.asking_price,
                whatnot_url = excluded.whatnot_url,
                updated_at = excluded.updated_at
            """,
            (user_id, card_id, variant, sale_condition, quantity, asking_price, whatnot_url, timestamp),
        )
        notifications += notify_wishlist_users_for_sale(conn, user_id, card_id, variant, sale_condition, quantity, asking_price)
        updated += 1
    conn.commit()
    return {"ok": True, "updated": updated, "skipped": skipped, "notifications": notifications}


def condition_owned_quantity(conn, user_id, card_id, variant, condition):
    row = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity
        FROM card_purchases
        WHERE user_id = ?
          AND card_id = ?
          AND COALESCE(NULLIF(variant, ''), 'Normal') = ?
          AND COALESCE(NULLIF(card_condition, ''), ?) = ?
        """,
        (user_id, card_id, variant or "Normal", DEFAULT_CARD_CONDITION, card_condition(condition)),
    ).fetchone()
    return int((row and row["quantity"]) or 0)


def decrement_purchase_quantity(conn, user_id, card_id, variant, condition, quantity):
    remaining = int(quantity or 0)
    if remaining <= 0:
        return
    rows = conn.execute(
        """
        SELECT id, quantity, total_price
        FROM card_purchases
        WHERE user_id = ?
          AND card_id = ?
          AND COALESCE(NULLIF(variant, ''), 'Normal') = ?
          AND COALESCE(NULLIF(card_condition, ''), ?) = ?
          AND quantity > 0
        ORDER BY purchase_date ASC, id ASC
        """,
        (user_id, card_id, variant or "Normal", DEFAULT_CARD_CONDITION, card_condition(condition)),
    ).fetchall()
    for row in rows:
        if remaining <= 0:
            break
        row_quantity = int(row["quantity"] or 0)
        if row_quantity <= 0:
            continue
        take = min(row_quantity, remaining)
        if take >= row_quantity:
            conn.execute("DELETE FROM card_purchases WHERE id = ?", (row["id"],))
        else:
            unit_price = money(row["total_price"], fallback=0.01) / row_quantity
            new_quantity = row_quantity - take
            conn.execute(
                """
                UPDATE card_purchases
                SET quantity = ?, total_price = ?
                WHERE id = ?
                """,
                (new_quantity, max(unit_price * new_quantity, 0.01), row["id"]),
            )
        remaining -= take
    if remaining > 0:
        raise ValueError("Sold quantity cannot exceed owned quantity for that condition.")


def mark_card_sold(conn, user_id, payload):
    card_id = payload.get("card_id") or payload.get("scryfall_id")
    if not card_id:
        raise ValueError("Choose a card to mark sold.")
    variant = payload.get("variant") or "Normal"
    sale_condition = card_condition(payload.get("card_condition"))
    sale_row = conn.execute(
        """
        SELECT quantity, asking_price
        FROM card_sales
        WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
        """,
        (user_id, card_id, variant, sale_condition),
    ).fetchone()
    if not sale_row:
        raise KeyError("Sale listing not found")
    quantity = int(money(payload.get("quantity"), fallback=sale_row["quantity"]))
    if quantity < 1:
        raise ValueError("Sold quantity must be at least 1.")
    if quantity > int(sale_row["quantity"] or 0):
        raise ValueError("Sold quantity cannot exceed the listed sale quantity.")
    owned_quantity = condition_owned_quantity(conn, user_id, card_id, variant, sale_condition)
    if quantity > owned_quantity:
        raise ValueError("Sold quantity cannot exceed owned quantity for that condition.")
    sold_date = payload.get("sold_date") or today_iso()
    sold_price_each = money(payload.get("sold_price_each"), fallback=sale_row["asking_price"])
    if sold_price_each <= 0:
        raise ValueError("Sold price must be greater than $0.00.")
    asking_price_each = money(sale_row["asking_price"], fallback=0.01)
    conn.execute(
        """
        INSERT INTO card_sale_journal (
            user_id, card_id, variant, card_condition, quantity, sold_date, sold_price_each, asking_price_each, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, card_id, variant, sale_condition, quantity, sold_date, sold_price_each, asking_price_each, now_iso()),
    )
    decrement_purchase_quantity(conn, user_id, card_id, variant, sale_condition, quantity)
    remaining_sale_quantity = int(sale_row["quantity"] or 0) - quantity
    if remaining_sale_quantity > 0:
        conn.execute(
            """
            UPDATE card_sales
            SET quantity = ?, updated_at = ?
            WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
            """,
            (remaining_sale_quantity, now_iso(), user_id, card_id, variant, sale_condition),
        )
    else:
        conn.execute(
            "DELETE FROM card_sales WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?",
            (user_id, card_id, variant, sale_condition),
        )
        purge_store_listing_favorites(conn, user_id, card_id, variant, sale_condition)
    collection_row = rollup_collection_from_purchases(conn, user_id, card_id, variant)
    conn.commit()
    return {
        "ok": True,
        "sold": {
            "card_id": card_id,
            "variant": variant,
            "card_condition": sale_condition,
            "quantity": quantity,
            "sold_date": sold_date,
            "sold_price_each": sold_price_each,
        },
        "remaining_quantity": collection_row["quantity"] if collection_row else 0,
        "remaining_sale_quantity": remaining_sale_quantity,
    }


def delete_card_movement(conn, user_id, card_id, payload):
    movement_type = payload.get("movement_type")
    movement_id = int(money(payload.get("movement_id"), fallback=0))
    variant = payload.get("variant") or "Normal"
    if movement_type not in {"buy", "sell", "adjust"} or movement_id <= 0:
        raise ValueError("Choose a valid card history entry.")
    if movement_type == "sell":
        sale = conn.execute(
            """
            SELECT *
            FROM card_sale_journal
            WHERE id = ? AND user_id = ? AND card_id = ? AND variant = ?
            """,
            (movement_id, user_id, card_id, variant),
        ).fetchone()
        if not sale:
            raise KeyError("Sale journal entry not found")
        condition = card_condition(sale["card_condition"])
        existing_purchase = conn.execute(
            """
            SELECT id, quantity, total_price
            FROM card_purchases
            WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
            ORDER BY purchase_date ASC, id ASC
            LIMIT 1
            """,
            (user_id, card_id, variant, condition),
        ).fetchone()
        fallback_unit = 0.01
        collection_row = conn.execute(
            "SELECT paid_price FROM collection WHERE user_id = ? AND card_id = ? AND variant = ?",
            (user_id, card_id, variant),
        ).fetchone()
        if existing_purchase and int(existing_purchase["quantity"] or 0) > 0:
            fallback_unit = money(existing_purchase["total_price"], fallback=0.01) / int(existing_purchase["quantity"])
        elif collection_row:
            fallback_unit = money(collection_row["paid_price"], fallback=0.01)
        restored_total = max(fallback_unit * int(sale["quantity"] or 0), 0.01)
        if existing_purchase:
            conn.execute(
                """
                UPDATE card_purchases
                SET quantity = quantity + ?,
                    total_price = total_price + ?
                WHERE id = ?
                """,
                (int(sale["quantity"] or 0), restored_total, existing_purchase["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO card_purchases (user_id, card_id, variant, quantity, card_condition, purchase_date, total_price, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    card_id,
                    variant,
                    int(sale["quantity"] or 0),
                    condition,
                    sale["sold_date"] or today_iso(),
                    restored_total,
                    now_iso(),
                ),
            )
        conn.execute(
            """
            INSERT INTO card_sales (user_id, card_id, variant, card_condition, quantity, asking_price, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, card_id, variant, card_condition) DO UPDATE SET
                quantity = card_sales.quantity + excluded.quantity,
                asking_price = excluded.asking_price,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                card_id,
                variant,
                condition,
                int(sale["quantity"] or 0),
                money(sale["asking_price_each"], fallback=sale["sold_price_each"]),
                now_iso(),
            ),
        )
        conn.execute("DELETE FROM card_sale_journal WHERE id = ? AND user_id = ?", (movement_id, user_id))
        rollup_collection_from_purchases(conn, user_id, card_id, variant)
        conn.commit()
        return {"ok": True, "deleted": {"movement_type": movement_type, "movement_id": movement_id}, "card": card_detail(conn, user_id, card_id, variant)}

    if movement_type == "adjust":
        adjustment = conn.execute(
            """
            SELECT *
            FROM inventory_adjustments
            WHERE id = ? AND user_id = ? AND card_id = ? AND variant = ?
            """,
            (movement_id, user_id, card_id, variant),
        ).fetchone()
        if not adjustment:
            raise KeyError("Inventory adjustment not found")
        condition = card_condition(adjustment["card_condition"])
        quantity = int(adjustment["quantity"] or 0)
        if adjustment["adjustment_type"] == "increase":
            available = available_condition_quantity(conn, user_id, card_id, variant, condition)
            if quantity > available:
                raise ValueError("Remove related deck assignments or sale listings before deleting this inventory adjustment.")
            decrement_purchase_quantity(conn, user_id, card_id, variant, condition, quantity)
        else:
            record_card_purchase(conn, user_id, card_id, variant, quantity, condition, adjustment["adjustment_date"] or today_iso(), max(quantity * 0.01, 0.01))
        conn.execute("DELETE FROM inventory_adjustments WHERE id = ? AND user_id = ?", (movement_id, user_id))
        rollup_collection_from_purchases(conn, user_id, card_id, variant)
        conn.commit()
        return {"ok": True, "deleted": {"movement_type": movement_type, "movement_id": movement_id}, "card": card_detail(conn, user_id, card_id, variant)}

    purchase = conn.execute(
        """
        SELECT *
        FROM card_purchases
        WHERE id = ? AND user_id = ? AND card_id = ? AND variant = ?
        """,
        (movement_id, user_id, card_id, variant),
    ).fetchone()
    if not purchase:
        raise KeyError("Purchase journal entry not found")
    condition = card_condition(purchase["card_condition"])
    sale_total = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity
        FROM card_sale_journal
        WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
        """,
        (user_id, card_id, variant, condition),
    ).fetchone()["quantity"]
    listed_total = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity
        FROM card_sales
        WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ?
        """,
        (user_id, card_id, variant, condition),
    ).fetchone()["quantity"]
    remaining_purchase_total = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity
        FROM card_purchases
        WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ? AND id != ?
        """,
        (user_id, card_id, variant, condition, movement_id),
    ).fetchone()["quantity"]
    if int(remaining_purchase_total or 0) < int(sale_total or 0) + int(listed_total or 0):
        raise ValueError("Remove related sold entries and For Sale listings before deleting this purchase entry.")
    remaining_owned = int(conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity
        FROM card_purchases
        WHERE user_id = ? AND card_id = ? AND variant = ? AND card_condition = ? AND id != ?
        """,
        (user_id, card_id, variant, condition, movement_id),
    ).fetchone()["quantity"] or 0)
    if remaining_owned < allocated_quantity(conn, user_id, card_id, variant, condition):
        raise ValueError("Move cards out of containers before deleting this purchase entry.")
    conn.execute("DELETE FROM card_purchases WHERE id = ? AND user_id = ?", (movement_id, user_id))
    rollup_collection_from_purchases(conn, user_id, card_id, variant)
    conn.commit()
    return {"ok": True, "deleted": {"movement_type": movement_type, "movement_id": movement_id}, "card": card_detail(conn, user_id, card_id, variant)}


def refresh_card_metadata(conn, card_id):
    card = conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    url = SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id))
    scryfall_card = request_json(url)
    synced_at = now_iso()
    upsert_card(conn, scryfall_card, synced_at)
    owned = conn.execute(
        "SELECT 1 FROM collection WHERE card_id = ? AND quantity > 0 LIMIT 1",
        (card_id,),
    ).fetchone()
    if owned:
        upsert_price_snapshot_from_card(conn, scryfall_card)
    conn.commit()
    refreshed = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    return {"ok": True, "card": dict(refreshed), "refreshed_at": synced_at}


def scryfall_card_json(card_id):
    card_id = (card_id or "").strip()
    if not card_id:
        raise ValueError("Card id is required.")
    url = SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id))
    return request_json(url)


def refresh_owned_price_snapshots(conn, user_id=None, limit=250, force=False, request_delay=None):
    limit = max(0, int(limit or 0))
    snapshot_date = app_today_iso()
    delay = PRICE_SNAPSHOT_REQUEST_DELAY if request_delay is None else max(0.0, float(request_delay or 0))
    skip_existing = "" if force else "AND NOT EXISTS (SELECT 1 FROM price_snapshots ps WHERE ps.card_id = c.scryfall_id AND ps.snapshot_date = ?)"
    limit_clause = "LIMIT ?" if limit > 0 else ""
    if user_id is None:
        params = [snapshot_date] if not force else []
        if limit > 0:
            params.append(limit)
        rows = conn.execute(
            f"""
            SELECT DISTINCT c.scryfall_id, c.name, c.last_synced_at
            FROM cards c
            JOIN collection col ON col.card_id = c.scryfall_id
            WHERE col.quantity > 0
              {skip_existing}
            ORDER BY c.last_synced_at ASC, c.name COLLATE NOCASE
            {limit_clause}
            """,
            params,
        ).fetchall()
    else:
        params = [user_id]
        if not force:
            params.append(snapshot_date)
        if limit > 0:
            params.append(limit)
        rows = conn.execute(
            f"""
            SELECT DISTINCT c.scryfall_id, c.name, c.last_synced_at
            FROM cards c
            JOIN collection col ON col.card_id = c.scryfall_id
            WHERE col.user_id = ? AND col.quantity > 0
              {skip_existing}
            ORDER BY c.last_synced_at ASC, c.name COLLATE NOCASE
            {limit_clause}
            """,
            params,
        ).fetchall()
    refreshed = []
    failed = []
    synced_at = now_iso()
    for index, row in enumerate(rows):
        if index and delay:
            time.sleep(delay)
        try:
            scryfall_card = request_json(SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(row["scryfall_id"])))
            upsert_card(conn, scryfall_card, synced_at)
            upsert_price_snapshot_from_card(conn, scryfall_card, snapshot_date)
            refreshed.append({
                "scryfall_id": row["scryfall_id"],
                "name": row["name"],
            })
        except Exception as exc:
            LOGGER.warning("Failed to refresh price snapshot for %s: %s", row["scryfall_id"], exc)
            failed.append({
                "scryfall_id": row["scryfall_id"],
                "name": row["name"],
                "error": str(exc),
            })
    conn.commit()
    return {
        "ok": True,
        "snapshot_date": snapshot_date,
        "refreshed": len(refreshed),
        "failed": len(failed),
        "limit": limit,
        "force": bool(force),
        "scope": "global" if user_id is None else "user",
        "cards": refreshed,
        "errors": failed,
    }


def refresh_missing_color_metadata(conn, user_id=None, limit=100):
    limit = max(1, min(int(limit or 100), 500))
    rows = conn.execute(
        """
        SELECT DISTINCT c.scryfall_id, c.name
        FROM cards c
        JOIN collection col ON col.card_id = c.scryfall_id
        WHERE col.quantity > 0
          AND (? IS NULL OR col.user_id = ?)
          AND (
              c.colors IS NULL OR trim(c.colors) = ''
              OR c.color_identity IS NULL OR trim(c.color_identity) = ''
          )
        ORDER BY c.last_synced_at ASC, c.name
        LIMIT ?
        """,
        (user_id, user_id, limit),
    ).fetchall()
    refreshed = []
    failed = []
    synced_at = now_iso()
    for row in rows:
        try:
            scryfall_card = request_json(SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(row["scryfall_id"])))
            upsert_card(conn, scryfall_card, synced_at)
            refreshed.append({"scryfall_id": row["scryfall_id"], "name": row["name"]})
            time.sleep(0.075)
        except Exception as exc:
            failed.append({"scryfall_id": row["scryfall_id"], "name": row["name"], "error": str(exc)})
    conn.commit()
    remaining = conn.execute(
        """
        SELECT COUNT(DISTINCT c.scryfall_id) AS count
        FROM cards c
        JOIN collection col ON col.card_id = c.scryfall_id
        WHERE col.quantity > 0
          AND (? IS NULL OR col.user_id = ?)
          AND (
              c.colors IS NULL OR trim(c.colors) = ''
              OR c.color_identity IS NULL OR trim(c.color_identity) = ''
          )
        """
    , (user_id, user_id)).fetchone()["count"]
    return {
        "ok": True,
        "refreshed": len(refreshed),
        "failed": failed,
        "remaining": remaining,
    }


def parse_schedule_time(value):
    match = re.match(r"^([0-2]?\d):([0-5]\d)$", (value or "").strip())
    if not match:
        LOGGER.warning("Invalid PRICE_SNAPSHOT_SCHEDULE_TIME %r; using 01:00.", value)
        return 1, 0
    hour = int(match.group(1))
    minute = int(match.group(2))
    if hour > 23:
        LOGGER.warning("Invalid PRICE_SNAPSHOT_SCHEDULE_TIME hour %r; using 01:00.", value)
        return 1, 0
    return hour, minute


def seconds_until_next_snapshot_run(now=None):
    tz = app_timezone()
    now = now or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    hour, minute = parse_schedule_time(PRICE_SNAPSHOT_SCHEDULE_TIME)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return max(1.0, (target - now).total_seconds())


def run_scheduled_price_snapshot_once():
    with connect() as conn:
        init_db(conn)
        result = refresh_owned_price_snapshots(
            conn,
            user_id=None,
            limit=PRICE_SNAPSHOT_DAILY_LIMIT,
            force=False,
            request_delay=PRICE_SNAPSHOT_REQUEST_DELAY,
        )
    LOGGER.info(
        "Daily price snapshot complete for %s: refreshed=%s failed=%s limit=%s",
        result.get("snapshot_date"),
        result.get("refreshed"),
        result.get("failed"),
        result.get("limit"),
    )
    return result


def price_snapshot_scheduler_loop(stop_event):
    LOGGER.info(
        "Daily price snapshot scheduler enabled at %s %s; limit=%s delay=%ss",
        PRICE_SNAPSHOT_SCHEDULE_TIME,
        APP_TIMEZONE,
        "all" if PRICE_SNAPSHOT_DAILY_LIMIT <= 0 else PRICE_SNAPSHOT_DAILY_LIMIT,
        PRICE_SNAPSHOT_REQUEST_DELAY,
    )
    while not stop_event.wait(seconds_until_next_snapshot_run()):
        try:
            run_scheduled_price_snapshot_once()
        except Exception as exc:
            LOGGER.exception("Daily price snapshot failed: %s", exc)


def start_price_snapshot_scheduler():
    if not PRICE_SNAPSHOT_SCHEDULE_ENABLED:
        LOGGER.info("Daily price snapshot scheduler disabled.")
        return None
    stop_event = threading.Event()
    thread = threading.Thread(
        target=price_snapshot_scheduler_loop,
        args=(stop_event,),
        name="price-snapshot-scheduler",
        daemon=True,
    )
    thread.start()
    return stop_event


def export_rows(conn, user_id):
    price_expr = current_price_sql("c")
    return conn.execute(
        f"""
        SELECT c.scryfall_id, c.name, c.set_code, c.set_name, c.collector_number, c.rarity, c.type_line,
               COALESCE(c.type_category, '') AS type_category,
               COALESCE(c.colors, '') AS colors,
               COALESCE(c.color_identity, '') AS color_identity,
               COALESCE(col.quantity, 0) AS quantity, COALESCE(col.acquired_date, '') AS acquired_date,
               COALESCE(col.paid_price, 0.01) AS paid_price, COALESCE(col.variant, 'Normal') AS variant,
               COALESCE(col.card_condition, 'Near Mint') AS card_condition,
               COALESCE(col.graded, 0) AS graded,
               COALESCE(col.notes, '') AS notes,
               COALESCE(meta.favorite, 0) AS favorite,
               COALESCE(meta.wishlist, 0) AS wishlist,
               ({price_expr}) AS current_value,
               ({price_expr}) AS market_price,
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value,
               COALESCE(col.quantity, 0) * ({price_expr}) AS total_value,
               c.scryfall_uri
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        LEFT JOIN card_meta meta ON meta.user_id = col.user_id AND meta.card_id = col.card_id AND meta.variant = col.variant
        WHERE col.user_id = ? AND col.quantity > 0
        ORDER BY owned_value DESC, c.name
        """
        ,
        (user_id,),
    ).fetchall()


def export_csv(conn, user_id):
    rows = export_rows(conn, user_id)
    output = io.StringIO()
    writer = csv.writer(output)
    keys = export_keys()
    headers = [
        "Scryfall ID", "Name", "Set Code", "Set", "Card Number", "Rarity", "Type", "Type Category", "Colors", "Color Identity", "Quantity", "Date Acquired",
        "Price Paid", "Variant", "Condition", "Graded", "Notes", "Favorite", "Wishlist", "Market Price", "Total Value", "Scryfall URL",
    ]
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row[key] for key in keys])
    return output.getvalue()


def export_moxfield_csv(conn, user_id):
    rows = export_rows(conn, user_id)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=MOXFIELD_CSV_HEADERS)
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "Count": int(row["quantity"] or 0),
            "Name": row["name"],
            "Edition": row["set_code"],
            "Condition": row["card_condition"],
            "Language": "English",
            "Foil": "true" if str(row["variant"] or "").lower() != "normal" else "false",
            "Collector Number": row["collector_number"],
            "Alter": "false",
            "Playtest Card": "false",
            "Purchase Price": row["paid_price"],
        })
    return output.getvalue()


def export_keys():
    return [
        "scryfall_id", "name", "set_code", "set_name", "collector_number", "rarity", "type_line", "type_category", "colors", "color_identity", "quantity", "acquired_date",
        "paid_price", "variant", "card_condition", "graded", "notes", "favorite", "wishlist", "market_price", "total_value", "scryfall_uri"
    ]


def export_json(conn, user_id):
    keys = export_keys()
    return [
        {key: row[key] for key in keys}
        for row in export_rows(conn, user_id)
    ]


REPORT_FIELD_LABELS = {
    "card_id": "Card ID",
    "card_name": "Card Name",
    "rules_name": "Rules Name",
    "flavor_name": "Printed Name",
    "set_name": "Set",
    "set_code": "Set Code",
    "collector_number": "Collector #",
    "variant": "Variant",
    "condition": "Condition",
    "quantity": "Quantity",
    "market_price": "Market Price",
    "total_value": "Total Value",
    "average_paid": "Average Paid",
    "total_paid": "Total Paid",
    "delta": "Delta",
    "type_line": "Type",
    "colors": "Colors",
    "rarity": "Rarity",
    "first_obtained": "First Obtained",
    "favorite": "Favorite",
    "for_sale_quantity": "For Sale Qty",
    "asking_price": "Asking Price",
    "container_quantity": "Container Qty",
    "deck_quantity": "Deck Qty",
    "notes": "Notes",
}

DEFAULT_REPORT_FIELDS = [
    "card_name", "set_code", "variant", "condition", "quantity", "market_price", "total_value", "delta",
]
MONEY_REPORT_FIELDS = {"market_price", "total_value", "average_paid", "total_paid", "delta", "asking_price"}


def selected_report_fields(payload):
    requested = payload.get("fields") if isinstance(payload, dict) else []
    fields = [field for field in requested if isinstance(field, str) and field in REPORT_FIELD_LABELS]
    if not fields:
        fields = list(DEFAULT_REPORT_FIELDS)
    return [{"key": field, "label": REPORT_FIELD_LABELS[field]} for field in fields]


def report_money(value):
    try:
        return f"${float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def report_display_value(key, value):
    if value is None:
        return ""
    if key in MONEY_REPORT_FIELDS:
        return report_money(value)
    if key == "favorite":
        return "Yes" if int(value or 0) else "No"
    return str(value)


def build_collection_report(conn, user_id, payload):
    payload = payload or {}
    filters = payload.get("filters") or {}
    fields = selected_report_fields(payload)
    price_expr = current_price_sql("c")
    total_paid_expr = "COALESCE(inv.total_paid, 0)"
    where = ["COALESCE(inv.quantity, 0) > 0"]
    params = []
    search = str(filters.get("search") or "").strip()
    if search:
        like = f"%{search.lower()}%"
        where.append(
            """
            (
                lower(c.name) LIKE ?
                OR lower(COALESCE(c.flavor_name, '')) LIKE ?
                OR lower(c.set_name) LIKE ?
                OR lower(c.set_code) LIKE ?
                OR lower(COALESCE(c.type_line, '')) LIKE ?
                OR lower(COALESCE(col.notes, '')) LIKE ?
            )
            """
        )
        params.extend([like] * 6)
    set_filter = str(filters.get("set") or "").strip()
    if set_filter:
        normalized_set = set_filter.lower()
        if re.fullmatch(r"[a-z0-9]{2,6}", normalized_set):
            where.append("lower(c.set_code) = ?")
            params.append(normalized_set)
        else:
            like = f"%{normalized_set}%"
            where.append("(lower(c.set_code) LIKE ? OR lower(c.set_name) LIKE ?)")
            params.extend([like, like])
    variant = str(filters.get("variant") or "").strip()
    if variant:
        where.append("lower(inv.variant) = lower(?)")
        params.append(variant)
    condition = str(filters.get("condition") or "").strip()
    if condition:
        where.append("lower(inv.condition) = lower(?)")
        params.append(condition)
    try:
        min_quantity = int(filters.get("min_quantity") or 0)
    except (TypeError, ValueError):
        min_quantity = 0
    if min_quantity > 0:
        where.append("COALESCE(inv.quantity, 0) >= ?")
        params.append(min_quantity)
    try:
        max_quantity = int(filters.get("max_quantity") or 0)
    except (TypeError, ValueError):
        max_quantity = 0
    if max_quantity > 0:
        where.append("COALESCE(inv.quantity, 0) <= ?")
        params.append(max_quantity)
    if filters.get("favorites_only"):
        where.append("COALESCE(meta.favorite, 0) = 1")
    if filters.get("for_sale_only"):
        where.append("COALESCE(sale.for_sale_quantity, 0) > 0")
    rows = conn.execute(
        f"""
        WITH inventory AS (
            SELECT user_id,
                   card_id,
                   COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
                   COALESCE(NULLIF(card_condition, ''), ?) AS condition,
                   SUM(COALESCE(total_price, 0)) AS total_paid,
                   SUM(COALESCE(quantity, 0)) AS quantity,
                   MIN(purchase_date) AS first_obtained
            FROM card_purchases
            WHERE user_id = ?
              AND COALESCE(quantity, 0) > 0
            GROUP BY user_id, card_id, COALESCE(NULLIF(variant, ''), 'Normal'), COALESCE(NULLIF(card_condition, ''), ?)
        ),
        sale AS (
            SELECT card_id,
                   COALESCE(NULLIF(variant, ''), 'Normal') AS variant,
                   COALESCE(NULLIF(card_condition, ''), ?) AS condition,
                   SUM(COALESCE(quantity, 0)) AS for_sale_quantity,
                   AVG(COALESCE(asking_price, 0)) AS asking_price
            FROM card_sales
            WHERE user_id = ?
            GROUP BY card_id, COALESCE(NULLIF(variant, ''), 'Normal'), COALESCE(NULLIF(card_condition, ''), ?)
        ),
        container_totals AS (
            SELECT cc.card_id,
                   COALESCE(NULLIF(cc.variant, ''), 'Normal') AS variant,
                   COALESCE(NULLIF(cc.card_condition, ''), ?) AS condition,
                   SUM(COALESCE(cc.quantity, 0)) AS container_quantity
            FROM container_cards cc
            JOIN containers con ON con.id = cc.container_id
            WHERE con.user_id = ?
            GROUP BY cc.card_id, COALESCE(NULLIF(cc.variant, ''), 'Normal'), COALESCE(NULLIF(cc.card_condition, ''), ?)
        ),
        deck_totals AS (
            SELECT dc.card_id,
                   COALESCE(NULLIF(dc.variant, ''), 'Normal') AS variant,
                   SUM(COALESCE(dc.quantity, 0)) AS deck_quantity
            FROM deck_cards dc
            JOIN decks d ON d.id = dc.deck_id
            WHERE d.user_id = ?
            GROUP BY dc.card_id, COALESCE(NULLIF(dc.variant, ''), 'Normal')
        )
        SELECT inv.card_id AS card_id,
               COALESCE(NULLIF(c.flavor_name, ''), c.name) AS card_name,
               c.name AS rules_name,
               COALESCE(c.flavor_name, '') AS flavor_name,
               c.set_name,
               c.set_code,
               c.collector_number,
               inv.variant AS variant,
               inv.condition AS condition,
               COALESCE(inv.quantity, 0) AS quantity,
               ({price_expr}) AS market_price,
               COALESCE(inv.quantity, 0) * ({price_expr}) AS total_value,
               CASE
                   WHEN COALESCE(inv.quantity, 0) > 0 THEN COALESCE(inv.total_paid, 0) / inv.quantity
                   ELSE COALESCE(col.paid_price, 0)
               END AS average_paid,
               {total_paid_expr} AS total_paid,
               (COALESCE(inv.quantity, 0) * ({price_expr})) - ({total_paid_expr}) AS delta,
               COALESCE(c.type_line, '') AS type_line,
               COALESCE(c.colors, '') AS colors,
               COALESCE(c.rarity, '') AS rarity,
               COALESCE(inv.first_obtained, col.acquired_date, '') AS first_obtained,
               COALESCE(meta.favorite, 0) AS favorite,
               COALESCE(sale.for_sale_quantity, 0) AS for_sale_quantity,
               COALESCE(sale.asking_price, 0) AS asking_price,
               COALESCE(container_totals.container_quantity, 0) AS container_quantity,
               COALESCE(deck_totals.deck_quantity, 0) AS deck_quantity,
               COALESCE(col.notes, '') AS notes
        FROM inventory inv
        JOIN cards c ON c.scryfall_id = inv.card_id
        LEFT JOIN collection col ON col.user_id = inv.user_id AND col.card_id = inv.card_id AND COALESCE(col.variant, 'Normal') = inv.variant
        LEFT JOIN card_meta meta ON meta.user_id = inv.user_id AND meta.card_id = inv.card_id AND meta.variant = inv.variant
        LEFT JOIN sale ON sale.card_id = inv.card_id AND sale.variant = inv.variant AND sale.condition = inv.condition
        LEFT JOIN container_totals ON container_totals.card_id = inv.card_id AND container_totals.variant = inv.variant AND container_totals.condition = inv.condition
        LEFT JOIN deck_totals ON deck_totals.card_id = inv.card_id AND deck_totals.variant = inv.variant
        WHERE {" AND ".join(where)}
        ORDER BY total_value DESC, c.name COLLATE NOCASE, inv.variant COLLATE NOCASE, inv.condition COLLATE NOCASE
        LIMIT 1000
        """,
        (
            DEFAULT_CARD_CONDITION, user_id, DEFAULT_CARD_CONDITION,
            DEFAULT_CARD_CONDITION, user_id, DEFAULT_CARD_CONDITION,
            DEFAULT_CARD_CONDITION, user_id, DEFAULT_CARD_CONDITION,
            user_id,
            *params,
        ),
    ).fetchall()
    return {
        "fields": fields,
        "rows": [
            {field["key"]: row[field["key"]] for field in fields}
            for row in rows
        ],
    }


def collection_report_html(report, title="Arcane Ledger Collection Report"):
    fields = report.get("fields") or []
    rows = report.get("rows") or []
    header = "".join(f"<th>{html_lib.escape(field['label'])}</th>" for field in fields)
    body = "".join(
        "<tr>" + "".join(
            f"<td>{html_lib.escape(report_display_value(field['key'], row.get(field['key'])))}</td>"
            for field in fields
        ) + "</tr>"
        for row in rows
    )
    if not body:
        body = f"<tr><td colspan=\"{len(fields) or 1}\">No rows matched this report.</td></tr>"
    return f"""
    <h2>{html_lib.escape(title)}</h2>
    <p>{len(rows):,} row{'s' if len(rows) != 1 else ''} generated from your collection.</p>
    <table border="1" cellspacing="0" cellpadding="6">
      <thead><tr>{header}</tr></thead>
      <tbody>{body}</tbody>
    </table>
    """


def collection_report_csv(report):
    output = io.StringIO()
    fields = report.get("fields") or []
    rows = report.get("rows") or []
    writer = csv.writer(output)
    writer.writerow([field["label"] for field in fields])
    for row in rows:
        writer.writerow([
            report_display_value(field["key"], row.get(field["key"]))
            for field in fields
        ])
    return output.getvalue()


def email_collection_report(conn, user, payload):
    to_email = normalize_email((payload or {}).get("to_email") or user["email"])
    if not to_email:
        raise ValueError("Enter an email address.")
    report = build_collection_report(conn, user["id"], payload or {})
    html_body = collection_report_html(report)
    csv_body = collection_report_csv(report)
    text_lines = ["Arcane Ledger Collection Report", f"{len(report.get('rows') or []):,} rows"]
    for row in report.get("rows", [])[:25]:
        text_lines.append(" | ".join(
            report_display_value(field["key"], row.get(field["key"]))
            for field in report.get("fields", [])
        ))
    result = send_email(
        to_email,
        "Arcane Ledger Collection Report",
        "\n".join(text_lines),
        html_body,
        tags=["arcane-ledger", "collection-report"],
        attachments=[{
            "filename": "arcaneledger-collection-report.csv",
            "content_type": "text/csv",
            "content": csv_body,
        }],
    )
    return {"ok": True, "message": f"Report emailed to {to_email}.", "email": result}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, fmt, *args):
        message = "%s - %s" % (self.address_string(), fmt % args)
        sys.stderr.write(f"{message}\n")
        LOGGER.info(message)

    def log_exception(self, exc):
        LOGGER.exception(
            "%s %s failed for %s: %s",
            self.command,
            self.path,
            self.client_address[0] if self.client_address else "unknown",
            exc,
        )

    def send_json(self, payload, status=HTTPStatus.OK, cookie=None):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        elif getattr(self, "_refresh_session_cookie", None):
            self.send_header("Set-Cookie", cookie_header(self._refresh_session_cookie))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def send_wallpaper_file(self, filename):
        filename = urllib.parse.unquote(filename or "")
        if not re.match(r"^[A-Za-z0-9._-]+$", filename):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        path = (WALLPAPER_DIR / filename).resolve()
        wallpaper_root = WALLPAPER_DIR.resolve()
        if wallpaper_root not in path.parents or not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        suffix = path.suffix.lower()
        content_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(suffix, "application/octet-stream")
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=86400")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_news_image_file(self, filename):
        filename = urllib.parse.unquote(filename or "")
        if not re.match(r"^[A-Za-z0-9._-]+$", filename):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        path = (NEWS_IMAGE_DIR / filename).resolve()
        image_root = NEWS_IMAGE_DIR.resolve()
        if image_root not in path.parents or not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        suffix = path.suffix.lower()
        content_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(suffix, "application/octet-stream")
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=86400")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def session_token(self):
        return parse_cookies(self.headers.get("Cookie", "")).get(SESSION_COOKIE)

    def current_user(self, conn):
        token = self.session_token()
        user = current_user_from_token(conn, token)
        if user and token:
            self._refresh_session_cookie = token
        return user

    def require_user(self, conn):
        user = self.current_user(conn)
        if not user:
            raise PermissionError("Please log in to use this feature.")
        return user

    def require_admin(self, conn):
        user = self.require_user(conn)
        if not is_admin_user(user):
            raise ForbiddenError("Admin access required.")
        return user

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        media_match = re.match(r"^/media/wallpapers/([^/]+)$", parsed.path)
        if media_match:
            return self.send_wallpaper_file(media_match.group(1))
        media_match = re.match(r"^/media/news-images/([^/]+)$", parsed.path)
        if media_match:
            return self.send_news_image_file(media_match.group(1))
        try:
            with connect() as conn:
                init_db(conn)
                if parsed.path == "/api/health":
                    return self.send_json({"ok": True, "status": "healthy"})
                if parsed.path == "/api/config":
                    return self.send_json(public_app_config(conn))
                if parsed.path == "/api/changelog":
                    return self.send_json(changelog_payload())
                if parsed.path == "/api/auth/session":
                    user = self.current_user(conn)
                    return self.send_json({"authenticated": bool(user), "user": user_payload(user)})
                if parsed.path == "/api/auth/verification":
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(verify_registration_token(conn, params.get("token", [""])[0]))
                if parsed.path == "/api/auth/password-reset":
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(verify_password_reset_token(conn, params.get("token", [""])[0]))
                if parsed.path == "/api/home":
                    return self.send_json(home_stats(conn))
                if parsed.path == "/api/news":
                    return self.send_json(list_news_posts(conn, parsed.query))
                if parsed.path == "/api/news/mine":
                    user = self.require_user(conn)
                    return self.send_json(list_my_news_posts(conn, user))
                match = re.match(r"^/api/news/([0-9]+)$", parsed.path)
                if match:
                    return self.send_json(news_post_detail(conn, int(match.group(1))))
                if parsed.path == "/api/search/hero-cards":
                    return self.send_json({"cards": search_hero_cards(conn)})
                if parsed.path == "/api/dashboard":
                    user = self.require_user(conn)
                    return self.send_json(dashboard(conn, user["id"]))
                if parsed.path == "/api/email/status":
                    return self.send_json(email_status())
                if parsed.path == "/api/debug/logs":
                    self.require_admin(conn)
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(read_log_tail(params.get("lines", [200])[0]))
                if parsed.path == "/api/admin/users":
                    self.require_admin(conn)
                    return self.send_json(list_admin_users(conn))
                if parsed.path == "/api/admin/server":
                    self.require_admin(conn)
                    return self.send_json(server_details())
                if parsed.path == "/api/admin/logs":
                    self.require_admin(conn)
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(read_log_tail(params.get("lines", [200])[0]))
                if parsed.path == "/api/admin/reports":
                    self.require_admin(conn)
                    return self.send_json(list_content_reports(conn))
                if parsed.path == "/api/admin/email-templates":
                    self.require_admin(conn)
                    return self.send_json(list_admin_email_templates(conn))
                if parsed.path == "/api/admin/announcements":
                    self.require_admin(conn)
                    return self.send_json(list_admin_announcements(conn))
                if parsed.path == "/api/admin/pro-features":
                    self.require_admin(conn)
                    return self.send_json(admin_pro_features_payload(conn))
                if parsed.path == "/api/admin/wallpapers":
                    self.require_admin(conn)
                    payload = list_site_wallpapers(conn)
                    payload["current"] = current_site_wallpaper(conn)
                    return self.send_json(payload)
                if parsed.path == "/api/cards/for-sale":
                    user = self.require_user(conn)
                    return self.send_json({"cards": list_sale_cards(conn, parsed.query, user["id"])})
                if parsed.path == "/api/store-front":
                    user = self.current_user(conn)
                    return self.send_json({"cards": list_store_front_cards(conn, parsed.query, user["id"] if user else None)})
                match = re.match(r"^/api/store-front/([^/]+)$", parsed.path)
                if match:
                    user = self.current_user(conn)
                    return self.send_json(store_front_card_detail(
                        conn,
                        urllib.parse.unquote(match.group(1)),
                        user["id"] if user else None,
                    ))
                if parsed.path == "/api/notifications":
                    user = self.require_user(conn)
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(list_notifications(conn, user["id"], params.get("limit", [100])[0]))
                if parsed.path == "/api/cards/wishlist":
                    user = self.require_user(conn)
                    return self.send_json({"cards": list_wishlist_cards(conn, parsed.query, user["id"])})
                if parsed.path == "/api/wishlists":
                    user = self.require_user(conn)
                    return self.send_json({"wishlists": list_wishlists(conn, user["id"])})
                if parsed.path == "/api/favorite-decks":
                    user = self.require_user(conn)
                    return self.send_json({"decks": list_favorite_decks(conn, user["id"])})
                if parsed.path == "/api/favorite-store-listings":
                    user = self.require_user(conn)
                    return self.send_json({"listings": list_favorite_store_listings(conn, user["id"])})
                match = re.match(r"^/api/wishlists/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(wishlist_detail(conn, user["id"], int(match.group(1)), parsed.query))
                if parsed.path == "/api/cards":
                    user = self.require_user(conn)
                    return self.send_json({"cards": list_cards(conn, parsed.query, user["id"])})
                match = re.match(r"^/api/cards/([^/]+)/public$", parsed.path)
                if match:
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(public_card_detail(
                        conn,
                        urllib.parse.unquote(match.group(1)),
                        params.get("variant", ["Normal"])[0],
                    ))
                match = re.match(r"^/api/cards/([^/]+)/detail$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(card_detail(
                        conn,
                        user["id"],
                        urllib.parse.unquote(match.group(1)),
                        params.get("variant", ["Normal"])[0],
                    ))
                match = re.match(r"^/api/cards/([^/]+)/purchase-entry$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(purchase_entry_ledger(
                        conn,
                        user["id"],
                        urllib.parse.unquote(match.group(1)),
                        params.get("movement_id", [""])[0],
                    ))
                match = re.match(r"^/api/cards/([^/]+)/scryfall-json$", parsed.path)
                if match:
                    return self.send_json(scryfall_card_json(urllib.parse.unquote(match.group(1))))
                match = re.match(r"^/api/cards/([^/]+)/posts$", parsed.path)
                if match:
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(profile_posts_for_card(
                        conn,
                        urllib.parse.unquote(match.group(1)),
                        params.get("variant", [None])[0],
                    ))
                match = re.match(r"^/api/cards/([^/]+)/deck-references$", parsed.path)
                if match:
                    self.require_user(conn)
                    return self.send_json(card_deck_references(conn, urllib.parse.unquote(match.group(1))))
                match = re.match(r"^/api/cards/([^/]+)/sale-sellers$", parsed.path)
                if match:
                    self.require_user(conn)
                    return self.send_json(card_sale_sellers(conn, urllib.parse.unquote(match.group(1))))
                if parsed.path == "/api/decks":
                    user = self.require_user(conn)
                    return self.send_json({"decks": list_decks(conn, user["id"])})
                if parsed.path == "/api/browse-decks":
                    user = self.current_user(conn)
                    return self.send_json({"decks": list_public_decks(conn, user["id"] if user else None)})
                if parsed.path == "/api/decks/export.json":
                    user = self.require_user(conn)
                    data = json.dumps(deck_export_payload(conn, user["id"]), indent=2).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=arcaneledger-decks.json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if parsed.path == "/api/decks/export.csv":
                    user = self.require_user(conn)
                    data = export_decks_csv(conn, user["id"]).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=arcaneledger-decks.csv")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                match = re.match(r"^/api/decks/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(deck_detail(conn, user["id"], int(match.group(1))))
                if parsed.path == "/api/containers":
                    user = self.require_user(conn)
                    return self.send_json({"containers": list_containers(conn, user["id"])})
                match = re.match(r"^/api/containers/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(container_detail(conn, user["id"], int(match.group(1))))
                if parsed.path == "/api/sets":
                    user = self.require_user(conn)
                    return self.send_json({"sets": set_completion(conn, user["id"], 5000)})
                match = re.match(r"^/api/sets/([^/]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(set_detail(conn, user["id"], urllib.parse.unquote(match.group(1)).lower()))
                match = re.match(r"^/api/shared/([^/]+)$", parsed.path)
                if match:
                    user = self.current_user(conn)
                    return self.send_json(shared_card(conn, urllib.parse.unquote(match.group(1)), user["id"] if user else None))
                match = re.match(r"^/api/shared-decks/([^/]+)$", parsed.path)
                if match:
                    user = self.current_user(conn)
                    return self.send_json(shared_deck_for_viewer(
                        conn,
                        urllib.parse.unquote(match.group(1)),
                        user["id"] if user else None,
                    ))
                match = re.match(r"^/api/shared-wishlists/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(shared_wishlist(conn, urllib.parse.unquote(match.group(1))))
                match = re.match(r"^/api/shared-containers/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(shared_container(conn, urllib.parse.unquote(match.group(1))))
                match = re.match(r"^/api/shared-sets/([^/]+)/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(shared_set(
                        conn,
                        urllib.parse.unquote(match.group(1)),
                        urllib.parse.unquote(match.group(2)).lower(),
                    ))
                match = re.match(r"^/api/stores/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(shared_store(conn, urllib.parse.unquote(match.group(1))))
                match = re.match(r"^/api/users/profile/([^/]+)$", parsed.path)
                if match:
                    user = self.current_user(conn)
                    query_params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(public_user_profile(
                        conn,
                        urllib.parse.unquote(match.group(1)),
                        user["id"] if user else None,
                        query_params.get("view", ["profile"])[0],
                    ))
                match = re.match(r"^/api/shared-favorites/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(shared_favorites(conn, urllib.parse.unquote(match.group(1))))
                if parsed.path == "/api/scryfall/search":
                    params = urllib.parse.parse_qs(parsed.query)
                    user = self.current_user(conn)
                    return self.send_json(search_scryfall_cards(
                        conn,
                        params.get("q", [""])[0],
                        params.get("lang", [None])[0],
                        params.get("order", [None])[0],
                        user["id"] if user else None,
                    ))
                match = re.match(r"^/api/scryfall/cards/([^/]+)$", parsed.path)
                if match:
                    user = self.current_user(conn)
                    return self.send_json(scryfall_card_by_id(conn, urllib.parse.unquote(match.group(1)), user["id"] if user else None))
                if parsed.path == "/api/export.csv":
                    user = self.require_user(conn)
                    data = export_csv(conn, user["id"]).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=arcaneledger-collection.csv")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if parsed.path == "/api/export.moxfield.csv":
                    user = self.require_user(conn)
                    data = export_moxfield_csv(conn, user["id"]).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=arcaneledger-moxfield-collection.csv")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if parsed.path == "/api/export.json":
                    user = self.require_user(conn)
                    data = json.dumps(export_json(conn, user["id"]), indent=2).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=arcaneledger-collection.json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except ForbiddenError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
        except PermissionError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.UNAUTHORIZED)
        except Exception as exc:
            self.log_exception(exc)
            return self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        if (
            re.match(r"^/(cards|sets|decks|wishlists|containers)/[^/]+/?$", parsed.path)
            or re.match(r"^/sets/shared/[^/]+/[^/]+/?$", parsed.path)
            or re.match(r"^/card/[^/]+/[^/]+/?$", parsed.path)
            or re.match(r"^/stores/[^/]+/?$", parsed.path)
            or re.match(r"^/user/[^/]+(?:/(?:blog|favorites))?/?$", parsed.path)
            or re.match(r"^/favorites/[^/]+/?$", parsed.path)
            or re.match(r"^/news/[0-9]+/?$", parsed.path)
            or re.match(r"^/verify-email/[^/]+/?$", parsed.path)
            or re.match(r"^/reset-password/[^/]+/?$", parsed.path)
            or re.match(r"^/(news|dashboard|favorites|collection|reports|sets|decks|browse-decks|containers|missing-list|for-sale|store-front|wishlist|notifications|admin|settings|search|import)/?$", parsed.path)
        ):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            with connect() as conn:
                init_db(conn)
                if parsed.path == "/api/auth/register-start":
                    return self.send_json(request_registration_email(conn, self.read_json()))
                if parsed.path == "/api/auth/claim-server":
                    result = claim_server(conn, self.read_json())
                    token = result.pop("session_token")
                    return self.send_json(result, HTTPStatus.CREATED, cookie=cookie_header(token, result.get("expires_at")))
                if parsed.path == "/api/auth/register-complete":
                    result = complete_registration(conn, self.read_json())
                    token = result.pop("session_token")
                    return self.send_json(result, HTTPStatus.CREATED, cookie=cookie_header(token, result.get("expires_at")))
                if parsed.path == "/api/auth/password-reset-start":
                    return self.send_json(request_password_reset(conn, self.read_json()))
                if parsed.path == "/api/auth/password-reset-complete":
                    result = complete_password_reset(conn, self.read_json())
                    token = result.pop("session_token")
                    return self.send_json(result, cookie=cookie_header(token, result.get("expires_at")))
                if parsed.path == "/api/auth/register":
                    result = start_registration(conn, self.read_json())
                    token = result.pop("session_token")
                    return self.send_json(result, HTTPStatus.CREATED, cookie=cookie_header(token, result.get("expires_at")))
                if parsed.path == "/api/auth/login":
                    result = login_user(conn, self.read_json())
                    token = result.pop("session_token")
                    return self.send_json(result, cookie=cookie_header(token, result.get("expires_at")))
                if parsed.path == "/api/auth/logout":
                    result = logout_user(conn, self.session_token())
                    return self.send_json(result, cookie=cookie_header("", clear=True))
                if parsed.path == "/api/user/clear-data":
                    user = self.require_user(conn)
                    return self.send_json(clear_user_data(conn, user["id"]))
                if parsed.path == "/api/billing/checkout":
                    user = self.require_user(conn)
                    return self.send_json(create_stripe_checkout_session(conn, user, self.read_json()))
                if parsed.path == "/api/billing/portal":
                    user = self.require_user(conn)
                    return self.send_json(create_stripe_portal_session(conn, user))
                if parsed.path == "/api/stripe/webhook":
                    return self.send_json(handle_stripe_webhook(conn, self.read_body(), self.headers.get("Stripe-Signature", "")))
                if parsed.path == "/api/reports":
                    user = self.require_user(conn)
                    return self.send_json(create_content_report(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/news":
                    user = self.require_user(conn)
                    return self.send_json(save_news_post(conn, user, self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/news/images":
                    user = self.require_user(conn)
                    return self.send_json(add_news_image(conn, user, self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/news/([0-9]+)/unpublish$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(unpublish_news_post(conn, user, int(match.group(1))))
                if parsed.path == "/api/collection-report":
                    user = self.require_user(conn)
                    return self.send_json(build_collection_report(conn, user["id"], self.read_json()))
                if parsed.path == "/api/collection-report/email":
                    user = self.require_user(conn)
                    return self.send_json(email_collection_report(conn, user, self.read_json()))
                if parsed.path == "/api/admin/email-templates/test":
                    user = self.require_admin(conn)
                    return self.send_json(send_admin_email_template_test(conn, user, self.read_json()))
                if parsed.path == "/api/admin/email-templates":
                    self.require_admin(conn)
                    return self.send_json(save_admin_email_template(conn, self.read_json()))
                if parsed.path == "/api/admin/announcements":
                    user = self.require_admin(conn)
                    return self.send_json(save_home_announcement(conn, user["id"], self.read_json()))
                if parsed.path == "/api/admin/wallpapers":
                    user = self.require_admin(conn)
                    return self.send_json(add_site_wallpaper(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/sync":
                    return self.send_json(sync_catalog(conn))
                if parsed.path == "/api/import":
                    user = self.require_user(conn)
                    payload = self.read_json()
                    return self.send_json(import_csv(conn, payload.get("path") or DEFAULT_IMPORT, user["id"]))
                if parsed.path == "/api/import/preview":
                    return self.send_json(import_preview(conn, self.read_json()))
                if parsed.path == "/api/import/csv/headers":
                    self.require_user(conn)
                    payload = self.read_json()
                    return self.send_json(csv_import_headers(payload.get("text") or "", payload.get("format")))
                if parsed.path == "/api/import/csv/entries":
                    self.require_user(conn)
                    return self.send_json(import_csv_mapped_entries(self.read_json()))
                if parsed.path == "/api/import/csv/match":
                    self.require_user(conn)
                    return self.send_json(import_csv_mapped_preview(conn, self.read_json()))
                if parsed.path == "/api/import/entries/match":
                    self.require_user(conn)
                    return self.send_json(import_entries_match_preview(conn, self.read_json()))
                if parsed.path == "/api/import/json/preview":
                    user = self.require_user(conn)
                    return self.send_json(import_json_wizard_preview(conn, user["id"], self.read_json()))
                if parsed.path == "/api/import/commit":
                    user = self.require_user(conn)
                    return self.send_json(commit_import_rows(conn, user["id"], self.read_json()))
                if parsed.path == "/api/import/json/commit":
                    user = self.require_user(conn)
                    return self.send_json(commit_import_wizard_json(conn, user["id"], self.read_json()))
                if parsed.path == "/api/import/container-allocations/preview":
                    user = self.require_user(conn)
                    return self.send_json(preview_container_allocation_import(conn, user["id"], self.read_json()))
                if parsed.path == "/api/import/container-allocations/commit":
                    user = self.require_user(conn)
                    return self.send_json(commit_container_allocation_import(conn, user["id"], self.read_json()))
                if parsed.path == "/api/cards":
                    user = self.require_user(conn)
                    return self.send_json(add_card_to_collection(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/cards/refresh-missing-colors":
                    user = self.require_user(conn)
                    payload = self.read_json()
                    return self.send_json(refresh_missing_color_metadata(conn, user["id"], payload.get("limit", 100)))
                if parsed.path == "/api/prices/snapshots/refresh":
                    user = self.require_user(conn)
                    payload = self.read_json()
                    return self.send_json(refresh_owned_price_snapshots(
                        conn,
                        user["id"],
                        payload.get("limit", 250),
                        force=True,
                    ))
                if parsed.path == "/api/cards/missing-list":
                    user = self.require_user(conn)
                    return self.send_json(update_cards_missing_list(conn, user["id"], self.read_json()))
                if parsed.path == "/api/cards/for-sale":
                    user = self.require_user(conn)
                    return self.send_json(update_cards_for_sale(conn, user["id"], self.read_json()))
                match = re.match(r"^/api/notifications/([0-9]+)/read$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(mark_notification_read(conn, user["id"], int(match.group(1))))
                if parsed.path == "/api/cards/sold":
                    user = self.require_user(conn)
                    return self.send_json(mark_card_sold(conn, user["id"], self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/email$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(email_card(conn, user, urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/purchases$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_card_purchase(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/cards/([^/]+)/inventory$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(adjust_card_inventory(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/direct-sale$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_card_direct_sale(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/cards/([^/]+)/comments$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_card_comment(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/card-comments/([0-9]+)/upvote$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(toggle_card_comment_upvote(conn, user["id"], int(match.group(1))))
                if parsed.path == "/api/decks":
                    user = self.require_user(conn)
                    return self.send_json(create_deck(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/decks/import":
                    user = self.require_user(conn)
                    return self.send_json(import_deck_json(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/decks/import/preview":
                    user = self.require_user(conn)
                    return self.send_json(preview_deck_import(conn, user["id"], self.read_json()))
                if parsed.path == "/api/decks/import/commit":
                    user = self.require_user(conn)
                    return self.send_json(commit_deck_import(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/wishlists":
                    user = self.require_user(conn)
                    return self.send_json(create_wishlist(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/decks/([0-9]+)/email$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(email_deck(conn, user, int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/wishlists/([0-9]+)/email$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(email_wishlist(conn, user, int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/favorites/([^/]+)/email$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(email_favorites(conn, user, urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/sets/([^/]+)/email$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(email_set(conn, user, urllib.parse.unquote(match.group(1)).lower(), self.read_json()))
                match = re.match(r"^/api/news/([0-9]+)/email$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(email_news_post(conn, user, int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/shared-decks/([^/]+)/favorite$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(update_favorite_deck(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()))
                if parsed.path == "/api/store-front/favorite":
                    user = self.require_user(conn)
                    return self.send_json(update_favorite_store_listing(conn, user["id"], self.read_json()))
                match = re.match(r"^/api/shared-decks/([^/]+)/email$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(email_shared_deck(conn, user, urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/shared-decks/([^/]+)/import$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(import_shared_deck_to_deck(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/decks/([0-9]+)/cards$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_cards_to_deck(conn, user["id"], int(match.group(1)), self.read_json()))
                if parsed.path == "/api/containers":
                    user = self.require_user(conn)
                    return self.send_json(create_container(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/containers/([0-9]+)/email$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(email_container(conn, user, int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/containers/([0-9]+)/cards$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_cards_to_container(conn, user["id"], int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/containers$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(update_card_container_allocations(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/collection$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(update_collection(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/favorite$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(update_favorite(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/wishlist$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(update_wishlist(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/refresh$", parsed.path)
                if match:
                    self.require_user(conn)
                    return self.send_json(refresh_card_metadata(conn, urllib.parse.unquote(match.group(1))))
                match = re.match(r"^/api/sets/([^/]+)/missing-list$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_set_missing_to_missing_list(conn, user["id"], urllib.parse.unquote(match.group(1)).lower()))
                match = re.match(r"^/api/sets/([^/]+)/missing-wishlist$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(create_set_missing_wishlist(conn, user["id"], urllib.parse.unquote(match.group(1)).lower()), HTTPStatus.CREATED)
                match = re.match(r"^/api/users/profile/([^/]+)/friend$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_profile_friend(conn, user["id"], urllib.parse.unquote(match.group(1))))
                match = re.match(r"^/api/users/profile/([^/]+)/wall$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_profile_wall_message(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/users/profile/([^/]+)/posts$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_profile_post(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/profile/posts/([0-9]+)/comments$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_profile_post_comment(conn, user["id"], int(match.group(1)), self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/admin/reports/([0-9]+)/resolve$", parsed.path)
                if match:
                    user = self.require_admin(conn)
                    return self.send_json(resolve_content_report(conn, user["id"], int(match.group(1)), self.read_json()))
        except urllib.error.URLError as exc:
            LOGGER.warning("%s %s network error: %s", self.command, self.path, exc)
            return self.send_json({"error": f"Network error: {exc}"}, HTTPStatus.BAD_GATEWAY)
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except ForbiddenError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
        except PermissionError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.UNAUTHORIZED)
        except Exception as exc:
            self.log_exception(exc)
            return self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        return self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            with connect() as conn:
                init_db(conn)
                match = re.match(r"^/api/admin/users/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_admin(conn)
                    return self.send_json(update_admin_user(conn, user["id"], int(match.group(1)), self.read_json()))
                if parsed.path == "/api/admin/pro-features":
                    self.require_admin(conn)
                    return self.send_json(update_admin_pro_features(conn, self.read_json()))
                if parsed.path == "/api/user/settings":
                    user = self.require_user(conn)
                    return self.send_json(update_user_settings(conn, user["id"], self.read_json()))
                match = re.match(r"^/api/containers/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(update_container(conn, user["id"], int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/decks/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(update_deck(conn, user["id"], int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/notes$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(update_card_private_notes(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()))
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except ForbiddenError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
        except PermissionError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.UNAUTHORIZED)
        except Exception as exc:
            self.log_exception(exc)
            return self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        return self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            with connect() as conn:
                init_db(conn)
                match = re.match(r"^/api/admin/users/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_admin(conn)
                    return self.send_json(admin_delete_user(conn, user["id"], int(match.group(1))))
                match = re.match(r"^/api/admin/wallpapers/([0-9]+)$", parsed.path)
                if match:
                    self.require_admin(conn)
                    return self.send_json(delete_site_wallpaper(conn, int(match.group(1))))
                match = re.match(r"^/api/admin/email-templates/([0-9]+)$", parsed.path)
                if match:
                    self.require_admin(conn)
                    return self.send_json(delete_admin_email_template(conn, int(match.group(1))))
                match = re.match(r"^/api/news/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(delete_news_post(conn, user, int(match.group(1))))
                if parsed.path == "/api/user/profile":
                    user = self.require_user(conn)
                    result = delete_user_profile(conn, user["id"])
                    return self.send_json(result, cookie=cookie_header("", clear=True))
                match = re.match(r"^/api/decks/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(delete_deck(conn, user["id"], int(match.group(1))))
                match = re.match(r"^/api/wishlists/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(delete_wishlist(conn, user["id"], int(match.group(1))))
                match = re.match(r"^/api/wishlists/([0-9]+)/cards$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(remove_wishlist_items(conn, user["id"], int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/decks/([0-9]+)/cards$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(remove_card_from_deck(conn, user["id"], int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/containers/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(delete_container(conn, user["id"], int(match.group(1))))
                match = re.match(r"^/api/containers/([0-9]+)/cards$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(remove_card_from_container(conn, user["id"], int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/collection$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(delete_collection_entry(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/movements$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(delete_card_movement(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()))
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except ForbiddenError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
        except PermissionError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.UNAUTHORIZED)
        except Exception as exc:
            self.log_exception(exc)
            return self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        return self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)


def serve(host="127.0.0.1", port=8000):
    with connect() as conn:
        init_db(conn)
    snapshot_scheduler_stop = start_price_snapshot_scheduler()
    server = ThreadingHTTPServer((host, port), Handler)
    display_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    LOGGER.info("Arcane Ledger starting at http://%s:%s with database %s", display_host, port, DB_PATH)
    print(f"Arcane Ledger running at http://{display_host}:{port}")
    try:
        server.serve_forever()
    finally:
        if snapshot_scheduler_stop:
            snapshot_scheduler_stop.set()


def main(argv):
    command = argv[1] if len(argv) > 1 else "serve"
    if command == "log-status":
        print(json.dumps(debug_log_status(), indent=2))
        return 0
    if command in {"logs", "log-tail"}:
        line_count = argv[2] if len(argv) > 2 else 200
        payload = read_log_tail(line_count)
        print("\n".join(payload["lines"]))
        return 0
    with connect() as conn:
        init_db(conn)
        if command == "sync":
            print(json.dumps(sync_catalog(conn), indent=2))
            return 0
        if command == "import":
            path = argv[2] if len(argv) > 2 else DEFAULT_IMPORT
            print(json.dumps(import_csv(conn, path), indent=2))
            return 0
        if command == "seed":
            sync_result = sync_catalog(conn)
            import_result = import_csv(conn, argv[2] if len(argv) > 2 else DEFAULT_IMPORT)
            print(json.dumps({"sync": sync_result, "import": import_result}, indent=2))
            return 0
        if command == "cache-owned-sets":
            print(json.dumps(cache_owned_sets(conn), indent=2))
            return 0
        if command == "refresh-missing-colors":
            limit = int(argv[2]) if len(argv) > 2 else 100
            print(json.dumps(refresh_missing_color_metadata(conn, limit), indent=2))
            return 0
        if command == "refresh-price-snapshots":
            limit = int(argv[2]) if len(argv) > 2 else 250
            print(json.dumps(refresh_owned_price_snapshots(conn, limit=limit), indent=2))
            return 0
        if command == "email-status":
            print(json.dumps(email_status(), indent=2))
            return 0
        if command == "email-diagnose":
            print(json.dumps(smtp_diagnostics(), indent=2))
            return 0
        if command == "email-trace":
            print(json.dumps(smtp_trace(), indent=2))
            return 0
        if command == "email-mailgun-trace":
            print(json.dumps(mailgun_trace(), indent=2))
            return 0
        if command == "email-test":
            if len(argv) < 3:
                print("Usage: python3 app.py email-test recipient@example.com [subject]")
                return 2
            subject = argv[3] if len(argv) > 3 else "Arcane Ledger Mailgun test"
            result = send_email(
                argv[2],
                subject,
                "Arcane Ledger Mailgun is configured correctly.",
                tags=["arcaneledger", "test"],
            )
            print(json.dumps(result, indent=2))
            return 0
    if command == "serve":
        port = int(os.environ.get("PORT", argv[2] if len(argv) > 2 else 8000))
        host = os.environ.get("HOST", "127.0.0.1")
        serve(host, port)
        return 0
    print("Usage: python3 app.py [serve [port] | sync | import [csv_path] | seed [csv_path] | cache-owned-sets | refresh-missing-colors [limit] | refresh-price-snapshots [limit] | email-status | email-diagnose | email-trace | email-mailgun-trace | email-test recipient@example.com [subject] | log-status | logs [lines]]")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception:
        LOGGER.exception("Command failed: %s", " ".join(sys.argv[1:]) or "serve")
        raise
