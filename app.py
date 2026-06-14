#!/usr/bin/env python3
import base64
import csv
import hashlib
import hmac
import io
import json
import logging
import os
import re
import secrets
import smtplib
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("DB_PATH", DATA_DIR / "mtg_collection.sqlite"))
LOG_DIR = Path(os.environ.get("LOG_DIR", DATA_DIR / "logs"))
LOG_FILE = Path(os.environ.get("LOG_FILE", LOG_DIR / "foilfolio.log"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", str(2 * 1024 * 1024)) or (2 * 1024 * 1024))
LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "5") or 5)
DEFAULT_IMPORT = Path(os.environ.get("DEFAULT_IMPORT", "/Users/kristophr/Downloads/export(1).csv"))
SCRYFALL_SETS_URL = "https://api.scryfall.com/sets"
SCRYFALL_SET_URL = "https://api.scryfall.com/sets/{set_code}"
SCRYFALL_SEARCH_URL = "https://api.scryfall.com/cards/search"
SCRYFALL_CARD_URL = "https://api.scryfall.com/cards/{set_code}/{collector_number}"
SCRYFALL_ID_URL = "https://api.scryfall.com/cards/{card_id}"
SCRYFALL_QUERY = os.environ.get("SCRYFALL_QUERY", "game:paper")
SCRYFALL_LANGUAGE = os.environ.get("SCRYFALL_LANGUAGE", "en")
MAILGUN_API_BASE = os.environ.get("MAILGUN_API_BASE", "https://api.mailgun.net/v3").rstrip("/")
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY", "")
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN", "")
MAILGUN_FROM_EMAIL = os.environ.get("MAILGUN_FROM_EMAIL", "")
MAILGUN_FROM_NAME = os.environ.get("MAILGUN_FROM_NAME", "FoilFolio")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587") or 587)
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", MAILGUN_FROM_NAME)
SMTP_SECURE = os.environ.get("SMTP_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"}
SMTP_STARTTLS = os.environ.get("SMTP_STARTTLS", "true").strip().lower() not in {"0", "false", "no", "off"}
SESSION_COOKIE = "foilfolio_session"
SESSION_DAYS = int(os.environ.get("SESSION_DAYS", "30"))
SUPPORTED_SCRYFALL_LANGUAGES = {"en"}
USER_AGENT = "foilfolio/0.1"
COLOR_ORDER = ("W", "U", "B", "R", "G")
CARD_CONDITIONS = (
    "Near Mint",
    "Lightly Played",
    "Moderately Played",
    "Heavily Played",
    "Damaged",
)
DEFAULT_CARD_CONDITION = "Near Mint"
CONTAINER_TYPES = ("binder", "box", "other")
DEFAULT_CONTAINER_TYPE = "other"
THEMES = {"light", "dark", "retro", "neon", "red", "blue", "black", "green", "pride"}


def configure_logging():
    logger = logging.getLogger("foilfolio")
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


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_iso():
    return date.today().isoformat()


def parse_iso_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
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


def request_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def mailgun_configured():
    return bool(MAILGUN_API_KEY and MAILGUN_DOMAIN and MAILGUN_FROM_EMAIL)


def smtp_configured():
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD and SMTP_FROM)


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
        "MAILGUN_FROM_EMAIL": MAILGUN_FROM_EMAIL,
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
            "from_email": MAILGUN_FROM_EMAIL,
            "from_name": MAILGUN_FROM_NAME,
            "missing": [name for name, value in mailgun_required.items() if not value],
        },
    }


def mailgun_sender():
    if MAILGUN_FROM_NAME:
        return f"{MAILGUN_FROM_NAME} <{MAILGUN_FROM_EMAIL}>"
    return MAILGUN_FROM_EMAIL


def smtp_sender():
    if SMTP_FROM_NAME:
        return f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
    return SMTP_FROM


def smtp_diagnostics():
    result = {
        "configured": smtp_configured(),
        "host": SMTP_HOST,
        "port": SMTP_PORT,
        "user": SMTP_USER,
        "from": SMTP_FROM,
        "secure": SMTP_SECURE,
        "starttls": SMTP_STARTTLS and not SMTP_SECURE,
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
        code, message = server.login(SMTP_USER, SMTP_PASSWORD)
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


def encode_multipart_form(fields):
    boundary = f"----foilfolio-{secrets.token_hex(16)}"
    parts = []
    for name, value in fields:
        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        parts.append(str(value).encode("utf-8"))
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(parts)


def send_email(to_email, subject, text=None, html=None, tags=None):
    if smtp_configured():
        return send_smtp_email(to_email, subject, text, html)
    if not mailgun_configured():
        raise ValueError("Email is not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and SMTP_FROM, or configure Mailgun API settings.")
    return send_mailgun_email(to_email, subject, text, html, tags)


def validate_email_message(to_email, subject, text=None, html=None):
    recipient = (to_email or "").strip()
    if "@" not in recipient:
        raise ValueError("A valid recipient email address is required.")
    if not (subject or "").strip():
        raise ValueError("Email subject is required.")
    if not text and not html:
        raise ValueError("Email text or HTML body is required.")
    return recipient, subject.strip()


def send_smtp_email(to_email, subject, text=None, html=None):
    recipient, clean_subject = validate_email_message(to_email, subject, text, html)
    message = EmailMessage()
    message["From"] = smtp_sender()
    message["To"] = recipient
    message["Subject"] = clean_subject
    message.set_content(text or "")
    if html:
        message.add_alternative(html, subtype="html")

    if SMTP_SECURE:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            if SMTP_STARTTLS:
                server.starttls()
                server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
    return {"ok": True, "provider": "smtp", "status": "sent"}


def send_mailgun_email(to_email, subject, text=None, html=None, tags=None):
    recipient, clean_subject = validate_email_message(to_email, subject, text, html)

    fields = [
        ("from", mailgun_sender()),
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
    boundary, body = encode_multipart_form(fields)
    req = urllib.request.Request(url, data=body, method="POST")
    token = base64.b64encode(f"api:{MAILGUN_API_KEY}".encode("utf-8")).decode("ascii")
    req.add_header("Authorization", f"Basic {token}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", USER_AGENT)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Mailgun error {exc.code}: {detail}") from exc

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
            today_iso(),
            money(prices.get("usd")),
            money(prices.get("usd_foil")),
            money(prices.get("usd_etched")),
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
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'en',
            theme TEXT NOT NULL DEFAULT 'light',
            email_verified INTEGER NOT NULL DEFAULT 0,
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

        CREATE TABLE IF NOT EXISTS card_sales (
            user_id INTEGER,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT NOT NULL DEFAULT 'Near Mint',
            quantity INTEGER NOT NULL DEFAULT 1,
            asking_price REAL NOT NULL DEFAULT 0.01,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id, variant, card_condition),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
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

        CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            share_id TEXT UNIQUE,
            name TEXT NOT NULL,
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
            name TEXT NOT NULL,
            storage_type TEXT NOT NULL DEFAULT 'other',
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
            quantity INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (container_id, card_id, variant),
            FOREIGN KEY (container_id) REFERENCES containers(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_cards_lookup ON cards(set_code, collector_number, name);
        CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
        CREATE INDEX IF NOT EXISTS idx_collection_quantity ON collection(user_id, quantity);
        CREATE INDEX IF NOT EXISTS idx_card_purchases_card ON card_purchases(user_id, card_id, variant, purchase_date);
        CREATE INDEX IF NOT EXISTS idx_deck_cards_card ON deck_cards(card_id, variant);
        CREATE INDEX IF NOT EXISTS idx_container_cards_card ON container_cards(card_id, variant);
        CREATE INDEX IF NOT EXISTS idx_card_sales_card ON card_sales(user_id, card_id, variant, card_condition);
        CREATE INDEX IF NOT EXISTS idx_card_sale_journal_card ON card_sale_journal(user_id, card_id, variant, card_condition, sold_date);
        CREATE INDEX IF NOT EXISTS idx_snapshots_date ON price_snapshots(snapshot_date);
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
    migrate_user_schema(conn)
    ensure_collection_share_ids(conn)
    ensure_deck_share_ids(conn)
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
        INSERT INTO card_purchases (card_id, variant, quantity, card_condition, purchase_date, total_price, created_at)
        SELECT col.card_id,
               COALESCE(NULLIF(col.variant, ''), 'Normal'),
               col.quantity,
               COALESCE(NULLIF(col.card_condition, ''), ?),
               COALESCE(NULLIF(col.acquired_date, ''), ?),
               MAX(col.quantity * COALESCE(col.paid_price, 0.01), 0.01),
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
    columns = {col["name"] for col in conn.execute("PRAGMA table_info(deck_cards)").fetchall()}
    if "quantity" not in columns:
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
    if "storage_type" not in columns:
        conn.execute("ALTER TABLE containers ADD COLUMN storage_type TEXT NOT NULL DEFAULT 'other'")
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


def migrate_card_sales_schema(conn):
    columns = conn.execute("PRAGMA table_info(card_sales)").fetchall()
    column_names = {col["name"] for col in columns}
    if "user_id" in column_names:
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
                updated_at TEXT NOT NULL,
                PRIMARY KEY (card_id, variant, card_condition),
                FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
            );
            """
        )
        if "card_condition" in column_names:
            conn.execute(
                """
                INSERT INTO card_sales (card_id, variant, card_condition, quantity, asking_price, updated_at)
                SELECT card_id,
                       COALESCE(NULLIF(variant, ''), 'Normal'),
                       COALESCE(NULLIF(card_condition, ''), 'Near Mint'),
                       quantity,
                       asking_price,
                       updated_at
                FROM card_sales_old
                """
            )
        else:
            conn.execute(
                """
                INSERT INTO card_sales (card_id, variant, card_condition, quantity, asking_price, updated_at)
                SELECT card_id,
                       COALESCE(NULLIF(variant, ''), 'Normal'),
                       'Near Mint',
                       quantity,
                       asking_price,
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


def migrate_card_sales_user_schema(conn):
    columns = table_columns(conn, "card_sales")
    if "user_id" in columns and table_pk(conn, "card_sales") == ["user_id", "card_id", "variant", "card_condition"]:
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
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, card_id, variant, card_condition),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );
        """
    )
    user_select = "user_id" if "user_id" in columns else "NULL"
    conn.execute(
        f"""
        INSERT INTO card_sales (user_id, card_id, variant, card_condition, quantity, asking_price, updated_at)
        SELECT {user_select}, card_id, COALESCE(NULLIF(variant, ''), 'Normal'),
               COALESCE(NULLIF(card_condition, ''), ?), quantity, asking_price, updated_at
        FROM card_sales_old_user_migration
        """,
        (DEFAULT_CARD_CONDITION,),
    )
    conn.execute("DROP TABLE card_sales_old_user_migration")


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
    user_columns = table_columns(conn, "users")
    if "language" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'en'")
    if "theme" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN theme TEXT NOT NULL DEFAULT 'light'")
    if "email_verified" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, expires_at)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_decks_user_name ON decks(user_id, lower(name))")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_containers_user_name ON containers(user_id, lower(name))")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_collection_share_id ON collection(share_id)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_decks_share_id ON decks(share_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_collection_user_quantity ON collection(user_id, quantity)")


def user_payload(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "language": scryfall_language(row["language"]),
        "theme": clean_theme(row["theme"]),
        "email_verified": bool(row["email_verified"]),
        "created_at": row["created_at"],
    }


def session_hash(token):
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def create_session(conn, user_id):
    token = secrets.token_urlsafe(32)
    created = now_iso()
    expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (session_hash(token), user_id, created, expires),
    )
    return token, expires


def cookie_header(token, expires_at=None, clear=False):
    if clear:
        return f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
    max_age = SESSION_DAYS * 24 * 60 * 60
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
    row = conn.execute(
        """
        SELECT u.*
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token_hash = ? AND s.expires_at > ?
        """,
        (session_hash(token), now_iso()),
    ).fetchone()
    return row


def adopt_legacy_data(conn, user_id):
    for table in ("collection", "card_purchases", "card_meta", "wishlist_cards", "card_sales", "card_sale_journal", "decks", "containers"):
        if "user_id" in table_columns(conn, table):
            conn.execute(f"UPDATE {table} SET user_id = ? WHERE user_id IS NULL", (user_id,))


def register_user(conn, payload):
    email = validate_email(payload.get("email"))
    password = validate_password(payload.get("password"))
    timestamp = now_iso()
    if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        raise ValueError("An account with that email already exists.")
    cursor = conn.execute(
        """
        INSERT INTO users (email, password_hash, language, theme, email_verified, created_at, updated_at)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        """,
        (email, hash_password(password), scryfall_language(payload.get("language")), clean_theme(payload.get("theme")), timestamp, timestamp),
    )
    user_id = cursor.lastrowid
    adopt_legacy_data(conn, user_id)
    token, expires_at = create_session(conn, user_id)
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return {"ok": True, "user": user_payload(user), "session_token": token, "expires_at": expires_at}


def login_user(conn, payload):
    email = validate_email(payload.get("email"))
    password = payload.get("password") or ""
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("Email or password is incorrect.")
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
    conn.execute(
        "UPDATE users SET language = ?, theme = ?, updated_at = ? WHERE id = ?",
        (language, theme, now_iso(), user_id),
    )
    conn.commit()
    return {"ok": True, "user": user_payload(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())}


def clear_user_data(conn, user_id):
    for table in ("container_cards", "deck_cards"):
        id_column = "container_id" if table == "container_cards" else "deck_id"
        owner_table = "containers" if table == "container_cards" else "decks"
        conn.execute(
            f"DELETE FROM {table} WHERE {id_column} IN (SELECT id FROM {owner_table} WHERE user_id = ?)",
            (user_id,),
        )
    for table in ("card_sale_journal", "card_sales", "wishlist_cards", "card_meta", "card_purchases", "collection", "containers", "decks"):
        conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
    conn.commit()
    return {"ok": True}


def delete_user_profile(conn, user_id):
    clear_user_data(conn, user_id)
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return {"ok": True}


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
        "collector_number": card.get("collector_number"),
        "rarity": card.get("rarity"),
        "type_line": card.get("type_line"),
        "type_category": card_type_category(card.get("type_line")),
        "colors": colors,
        "color_identity": color_identity,
        "flavor_text": card_text(card, "flavor_text") or "",
        "finishes": card.get("finishes") or [],
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
    wishlist_flags = wishlist_flags_for_cards(conn, card_ids, user_id)
    cards = []
    for card in scryfall_cards:
        summary = card_summary(card, owned_quantities.get(card.get("id"), 0))
        summary["wishlist"] = wishlist_flags.get(card.get("id"), 0)
        cards.append(summary)
    return {"cards": cards}


def variant_price_from_row(card, variant):
    variant_text = (variant or "").lower()
    if "etched" in variant_text and card["current_usd_etched"]:
        return card["current_usd_etched"]
    if "foil" in variant_text and card["current_usd_foil"]:
        return card["current_usd_foil"]
    return card["current_usd"] or card["current_usd_foil"] or card["current_usd_etched"] or 0


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


def record_card_purchase(conn, user_id, card_id, variant, quantity, condition, purchase_date, total_price):
    quantity = max(1, int(quantity or 1))
    total_price = money(total_price, fallback=0.01)
    if total_price <= 0:
        total_price = 0.01
    conn.execute(
        """
        INSERT INTO card_purchases (user_id, card_id, variant, quantity, card_condition, purchase_date, total_price, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            card_id,
            variant or "Normal",
            quantity,
            card_condition(condition),
            purchase_date or today_iso(),
            total_price,
            now_iso(),
        ),
    )


def rollup_collection_from_purchases(conn, user_id, card_id, variant):
    variant = variant or "Normal"
    aggregate = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity,
               COALESCE(SUM(total_price), 0) AS total_paid,
               MIN(purchase_date) AS first_purchase
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
        SELECT card_condition
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
    graded = int(existing["graded"] or 0) if existing else 0
    notes = existing["notes"] if existing else ""
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
    quantity = max(1, int(money(payload.get("quantity"), fallback=1)))
    paid_price = money(payload.get("paid_price"), fallback=0.01)
    if paid_price <= 0:
        paid_price = 0.01
    purchase_unit_price = paid_price
    purchase_date = payload.get("acquired_date") or today_iso()
    acquired_date = purchase_date
    variant = payload.get("variant") or "Normal"
    purchase_condition = card_condition(payload.get("card_condition"))

    url = SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id))
    synced_at = now_iso()
    scryfall_card = request_json(url)
    validate_selected_card(scryfall_card, payload)
    upsert_card(conn, scryfall_card, synced_at)
    if not payload.get("skip_set_cache"):
        cache_set_catalog(conn, scryfall_card.get("set"))

    existing = conn.execute(
        """
        SELECT quantity, paid_price, acquired_date, card_condition, graded, notes, share_id
        FROM collection
        WHERE user_id = ? AND card_id = ? AND variant = ?
        """,
        (user_id, card_id, variant),
    ).fetchone()
    if existing:
        new_quantity = existing["quantity"] + quantity
        paid_price = (
            (existing["quantity"] * existing["paid_price"]) + (quantity * paid_price)
        ) / new_quantity
        if existing["acquired_date"] and acquired_date:
            acquired_date = min(existing["acquired_date"], acquired_date)
        else:
            acquired_date = existing["acquired_date"] or acquired_date
        card_condition_value = card_condition(existing["card_condition"])
        graded = int(existing["graded"] or 0)
        notes = existing["notes"] or ""
        share_id = existing["share_id"] or new_share_id(conn)
    else:
        new_quantity = quantity
        card_condition_value = card_condition(payload.get("card_condition"))
        graded = bool_int(payload.get("graded"))
        notes = ""
        share_id = new_share_id(conn)

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
        (user_id, card_id, share_id, new_quantity, acquired_date, paid_price, variant, card_condition_value, graded, notes, now_iso()),
    )
    card = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    record_card_purchase(conn, user_id, card_id, variant, quantity, purchase_condition, purchase_date, quantity * purchase_unit_price)
    collection_row = rollup_collection_from_purchases(conn, user_id, card_id, variant)
    conn.execute("DELETE FROM wishlist_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
    conn.commit()
    return {
        "ok": True,
        "card": dict(card),
        "quantity": collection_row["quantity"] if collection_row else new_quantity,
        "variant": variant,
        "current_value": variant_price_from_row(card, variant),
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
    set_code = source_value(source, "set_code", "Set Code")
    collector_number = source_value(source, "collector_number", "Card Number", "Collector Number", "number")
    quantity = int(money(source_value(source, "quantity", "Quantity"), fallback=0))
    if quantity <= 0:
        quantity = 1 if name else 0
    paid_price = money(source_value(source, "paid_price", "Price Paid", "Average Cost Paid"), fallback=0.01)
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
        "variant": source_value(source, "variant", "Variant", "Variance") or import_variant(source),
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


def local_import_match(conn, entry):
    if entry.get("error"):
        return None
    if entry.get("scryfall_id"):
        row = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (entry["scryfall_id"],)).fetchone()
        if row:
            return {"source": "local", "confidence": "exact id", "card": import_card_summary_from_row(row)}
    by_set_number, by_name_number, by_name = lookup_maps(conn)
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
    queries = []
    if name and number:
        queries.append(f'!"{name}" cn:{number} game:paper')
        queries.append(f'{name} cn:{number} game:paper')
    if name:
        queries.append(f'!"{name}" game:paper')
        queries.append(f'{name} game:paper')
    for query in queries:
        payload = request_json(f"{SCRYFALL_SEARCH_URL}?{urllib.parse.urlencode({'q': scryfall_query_with_language(query), 'unique': 'prints', 'order': 'set'})}")
        cards = payload.get("data") or []
        if cards:
            card = cards[0]
            return {"source": "scryfall", "confidence": "best guess", "card": card_summary(card)}
    return None


def preview_import_rows(conn, rows, source_format):
    preview = []
    issues = []
    for index, source in enumerate(rows, start=1):
        entry = import_row_from_source(source, index, source_format)
        if entry.get("error"):
            issues.append({"line": entry["line"], "name": entry.get("name"), "error": entry["error"]})
            preview.append({"id": f"row-{index}", "checked": False, "entry": entry, "match": None, "status": "bad"})
            continue
        match = local_import_match(conn, entry)
        if not match:
            try:
                match = scryfall_import_match(entry)
            except Exception as exc:
                issues.append({"line": entry["line"], "name": entry.get("name"), "error": f"Scryfall lookup failed: {exc}"})
        if not match:
            issues.append({"line": entry["line"], "name": entry.get("name"), "error": "No match found."})
        preview.append({
            "id": f"row-{index}",
            "checked": bool(match),
            "entry": entry,
            "match": match,
            "status": "matched" if match else "unmatched",
        })
    return {"rows": preview, "issues": issues}


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
        raise ValueError("JSON import only accepts a FoilFolio export array.")
    return payload


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
    price_expr = current_price_sql("c")
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

    acquired_rows = conn.execute(
        f"""
        SELECT substr(col.acquired_date, 1, 7) AS acquired_month,
               ROUND(SUM(col.quantity * ({price_expr})), 2) AS acquired_value
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        WHERE col.user_id = ?
          AND col.quantity > 0
          AND col.acquired_date IS NOT NULL
          AND col.acquired_date != ''
        GROUP BY acquired_month
        ORDER BY acquired_month
        """,
        (user_id,),
    ).fetchall()
    acquired_by_month = {
        row["acquired_month"]: row["acquired_value"] or 0
        for row in acquired_rows
    }

    prior_total = conn.execute(
        f"""
        SELECT ROUND(COALESCE(SUM(col.quantity * ({price_expr})), 0), 2) AS value
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        WHERE col.user_id = ?
          AND col.quantity > 0
          AND col.acquired_date IS NOT NULL
          AND col.acquired_date != ''
          AND col.acquired_date < ?
        """,
        (user_id, start_month.isoformat()),
    ).fetchone()["value"] or 0

    points = []
    total = prior_total
    cursor = start_month
    while cursor <= current_month:
        key = cursor.strftime("%Y-%m")
        total += acquired_by_month.get(key, 0)
        points.append({
            "date": key,
            "label": month_label(cursor),
            "added_value": round(acquired_by_month.get(key, 0), 2),
            "value": round(total, 2),
        })
        cursor = add_months(cursor, 1)
    return points


def set_completion(conn, user_id, limit=10):
    rows = conn.execute(
        """
        SELECT
            s.code AS set_code,
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
    row = conn.execute(
        """
        SELECT
            s.code AS set_code,
            COALESCE(s.name, MAX(c.set_name), s.code) AS set_name,
            COALESCE(s.cached_at, '') AS cached_at,
            COUNT(DISTINCT c.scryfall_id) AS total_cards,
            COUNT(DISTINCT CASE WHEN col.quantity > 0 THEN c.scryfall_id END) AS owned_cards
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
    wishlist_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM (
            SELECT meta.card_id, meta.variant
            FROM card_meta meta
            LEFT JOIN collection col ON col.user_id = meta.user_id AND col.card_id = meta.card_id AND col.variant = meta.variant
            WHERE meta.user_id = ? AND COALESCE(meta.wishlist, 0) = 1 AND COALESCE(col.quantity, 0) = 0
            UNION
            SELECT wc.card_id, wc.variant
            FROM wishlist_cards wc
            WHERE wc.user_id = ?
        )
        """,
        (user_id, user_id),
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
    result["favorite_count"] = favorite_count
    result["wishlist_count"] = wishlist_count
    result["sale_count"] = sale_summary["count"] or 0
    result["sale_asking_total"] = sale_summary["asking_total"] or 0
    result["total_value"] = result["current_total"]
    result["gain_loss"] = result["current_total"] - result["paid_total"]
    result["gain_loss_percent"] = (result["gain_loss"] / result["paid_total"] * 100) if result["paid_total"] else 0
    result["top_cards"] = top
    result["history"] = history
    result["set_breakdown"] = set_breakdown
    result["set_completion"] = set_completion(conn, user_id)
    return result


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
    if table not in {"decks", "containers"}:
        raise ValueError("Unsupported name check.")
    params = [user_id, name]
    exclude_sql = ""
    if exclude_id is not None:
        exclude_sql = " AND id != ?"
        params.append(exclude_id)
    return conn.execute(
        f"SELECT 1 FROM {table} WHERE user_id = ? AND lower(name) = lower(?) {exclude_sql} LIMIT 1",
        params,
    ).fetchone() is not None


def list_decks(conn, user_id):
    rows = conn.execute(
        """
        SELECT d.id, d.share_id, d.name, d.created_at, d.updated_at,
               COALESCE(SUM(dc.quantity), 0) AS card_count,
               COUNT(dc.card_id) AS unique_card_count
        FROM decks d
        LEFT JOIN deck_cards dc ON dc.deck_id = d.id
        WHERE d.user_id = ?
        GROUP BY d.id
        ORDER BY d.updated_at DESC, d.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    return rows_to_dicts(rows)


def create_deck(conn, user_id, payload):
    name = re.sub(r"\s+", " ", (payload.get("name") or "").strip())
    if not name:
        raise ValueError("Deck name is required.")
    if len(name) > 20:
        raise ValueError("Deck name must be 20 characters or fewer.")
    if name_exists(conn, "decks", name, user_id):
        raise ValueError("Deck name must be unique.")
    timestamp = now_iso()
    share_id = new_deck_share_id(conn)
    cursor = conn.execute(
        """
        INSERT INTO decks (user_id, share_id, name, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, share_id, name, timestamp, timestamp),
    )
    conn.commit()
    return {
        "ok": True,
        "deck": {
            "id": cursor.lastrowid,
            "share_id": share_id,
            "name": name,
            "created_at": timestamp,
            "updated_at": timestamp,
            "card_count": 0,
            "unique_card_count": 0,
        },
    }


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
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value
        FROM deck_cards dc
        JOIN cards c ON c.scryfall_id = dc.card_id
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = dc.card_id AND col.variant = dc.variant
        WHERE dc.deck_id = ?
        ORDER BY c.name COLLATE NOCASE, dc.variant
        """,
        (user_id, deck_id),
    ).fetchall()
    return rows_to_dicts(rows)


def deck_detail(conn, user_id, deck_id):
    deck = conn.execute(
        """
        SELECT d.id, d.share_id, d.name, d.created_at, d.updated_at,
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


def shared_deck(conn, share_id):
    deck = conn.execute("SELECT id, user_id FROM decks WHERE share_id = ?", (share_id,)).fetchone()
    if not deck:
        raise KeyError("Shared deck not found")
    payload = deck_detail(conn, deck["user_id"], deck["id"])
    payload["readonly"] = True
    return payload


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
        owned = conn.execute(
            """
            SELECT COALESCE(quantity, 0) AS quantity
            FROM collection
            WHERE user_id = ? AND card_id = ? AND variant = ? AND quantity > 0
            """,
            (user_id, card_id, variant),
        ).fetchone()
        if not owned:
            continue
        owned_count = int(owned["quantity"] or 0)
        existing = conn.execute(
            """
            SELECT COALESCE(quantity, 0) AS quantity
            FROM deck_cards
            WHERE deck_id = ? AND card_id = ? AND variant = ?
            """,
            (deck_id, card_id, variant),
        ).fetchone()
        current_deck_count = int(existing["quantity"] or 0) if existing else 0
        if current_deck_count + quantity > owned_count:
            available = max(0, owned_count - current_deck_count)
            raise ValueError(f"Only {available} copy/copies are available to add for this card.")
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
    cursor = conn.execute("DELETE FROM decks WHERE id = ? AND user_id = ?", (deck_id, user_id))
    if cursor.rowcount == 0:
        raise KeyError("Deck not found")
    conn.commit()
    return {"ok": True, "deleted": deck_id}


def allocated_quantity(conn, user_id, card_id, variant, exclude_container_id=None):
    params = [user_id, card_id, variant]
    exclude_sql = ""
    if exclude_container_id is not None:
        exclude_sql = " AND cc.container_id != ?"
        params.append(exclude_container_id)
    row = conn.execute(
        f"""
        SELECT COALESCE(SUM(quantity), 0) AS quantity
        FROM container_cards cc
        JOIN containers c ON c.id = cc.container_id
        WHERE c.user_id = ? AND cc.card_id = ? AND cc.variant = ?{exclude_sql}
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
    rows = conn.execute(
        """
        SELECT c.id, c.name, COALESCE(c.storage_type, 'other') AS storage_type,
               c.location, c.notes, c.created_at, c.updated_at,
               COUNT(cc.card_id) AS card_count,
               COALESCE(SUM(cc.quantity), 0) AS stored_quantity
        FROM containers c
        LEFT JOIN container_cards cc ON cc.container_id = c.id
        WHERE c.user_id = ?
        GROUP BY c.id
        ORDER BY c.updated_at DESC, c.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    return rows_to_dicts(rows)


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


def create_container(conn, user_id, payload):
    name = clean_limited_text(payload, "name", "Container name", 30, required=True)
    if name_exists(conn, "containers", name, user_id):
        raise ValueError("Container name must be unique.")
    storage_type = clean_container_type(payload.get("storage_type"))
    location = clean_limited_text(payload, "location", "Container location", 30)
    notes = (payload.get("notes") or "").strip()
    if len(notes) > 500:
        raise ValueError("Notes / Description must be 500 characters or fewer.")
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO containers (user_id, name, storage_type, location, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, name, storage_type, location, notes, timestamp, timestamp),
    )
    conn.commit()
    return {
        "ok": True,
        "container": {
            "id": cursor.lastrowid,
            "name": name,
            "storage_type": storage_type,
            "location": location,
            "notes": notes,
            "created_at": timestamp,
            "updated_at": timestamp,
            "card_count": 0,
            "stored_quantity": 0,
        },
    }


def update_container(conn, user_id, container_id, payload):
    exists = conn.execute("SELECT id FROM containers WHERE id = ? AND user_id = ?", (container_id, user_id)).fetchone()
    if not exists:
        raise KeyError("Container not found")
    name = clean_limited_text(payload, "name", "Container name", 30, required=True)
    if name_exists(conn, "containers", name, user_id, exclude_id=container_id):
        raise ValueError("Container name must be unique.")
    storage_type = clean_container_type(payload.get("storage_type"))
    location = clean_limited_text(payload, "location", "Container location", 30)
    notes = (payload.get("notes") or "").strip()
    if len(notes) > 500:
        raise ValueError("Notes / Description must be 500 characters or fewer.")
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE containers
        SET name = ?, storage_type = ?, location = ?, notes = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (name, storage_type, location, notes, timestamp, container_id, user_id),
    )
    conn.commit()
    container = container_detail(conn, user_id, container_id)
    return {"ok": True, "container": container}


def container_cards(conn, user_id, container_id):
    price_expr = current_price_sql("c")
    rows = conn.execute(
        f"""
        SELECT c.*, cc.variant, cc.quantity AS stored_quantity, cc.updated_at,
               COALESCE(col.quantity, 0) AS quantity,
               COALESCE(col.paid_price, 0.01) AS paid_price,
               COALESCE(col.card_condition, 'Near Mint') AS card_condition,
               COALESCE(col.graded, 0) AS graded,
               col.acquired_date,
               col.share_id,
               ({price_expr}) AS display_price,
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value
        FROM container_cards cc
        JOIN cards c ON c.scryfall_id = cc.card_id
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = cc.card_id AND col.variant = cc.variant
        WHERE cc.container_id = ?
        ORDER BY c.name COLLATE NOCASE, cc.variant
        """,
        (user_id, container_id),
    ).fetchall()
    return rows_to_dicts(rows)


def container_detail(conn, user_id, container_id):
    container = conn.execute(
        """
        SELECT c.id, c.name, COALESCE(c.storage_type, 'other') AS storage_type,
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
    payload["cards"] = container_cards(conn, user_id, container_id)
    return payload


def add_cards_to_container(conn, user_id, container_id, payload):
    container = conn.execute("SELECT id FROM containers WHERE id = ? AND user_id = ?", (container_id, user_id)).fetchone()
    if not container:
        raise KeyError("Container not found")
    cards = payload.get("cards") or []
    if not isinstance(cards, list) or not cards:
        raise ValueError("Choose at least one card.")

    timestamp = now_iso()
    added = 0
    for item in cards:
        card_id = item.get("card_id") or item.get("scryfall_id")
        variant = item.get("variant") or "Normal"
        quantity = max(0, int(item.get("quantity") or 0))
        if not card_id or quantity <= 0:
            continue
        owned = owned_quantity(conn, user_id, card_id, variant)
        if owned <= 0:
            raise ValueError("Only owned cards can be stored in containers.")
        existing = conn.execute(
            """
            SELECT COALESCE(quantity, 0) AS quantity
            FROM container_cards
            WHERE container_id = ? AND card_id = ? AND variant = ?
            """,
            (container_id, card_id, variant),
        ).fetchone()
        current_here = int(existing["quantity"] or 0) if existing else 0
        allocated_elsewhere = allocated_quantity(conn, user_id, card_id, variant, exclude_container_id=container_id)
        max_here = owned - allocated_elsewhere
        if current_here + quantity > max_here:
            available = max(0, max_here - current_here)
            raise ValueError(f"Only {available} unassigned copy/copies are available for this card.")
        conn.execute(
            """
            INSERT INTO container_cards (container_id, card_id, variant, quantity, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(container_id, card_id, variant) DO UPDATE SET
                quantity = container_cards.quantity + excluded.quantity,
                updated_at = excluded.updated_at
            """,
            (container_id, card_id, variant, quantity, timestamp),
        )
        added += quantity
    conn.execute("UPDATE containers SET updated_at = ? WHERE id = ?", (timestamp, container_id))
    conn.commit()
    return {"ok": True, "added": added, "container_id": container_id}


def remove_card_from_container(conn, user_id, container_id, payload):
    container = conn.execute("SELECT id FROM containers WHERE id = ? AND user_id = ?", (container_id, user_id)).fetchone()
    if not container:
        raise KeyError("Container not found")
    card_id = payload.get("card_id") or payload.get("scryfall_id")
    variant = payload.get("variant") or "Normal"
    if not card_id:
        raise ValueError("Card is required.")
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
    limit = min(int(params.get("limit", ["250"])[0] or 250), 5000)
    where = []
    values = []
    if set_code:
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
    where_sql = "WHERE " + " AND ".join(where) if where else ""
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
    sort_map = {
        "name": "c.name COLLATE NOCASE ASC",
        "set": "c.set_name COLLATE NOCASE ASC, CAST(c.collector_number AS INTEGER), c.collector_number",
        "price": f"display_price DESC, c.name",
        "value": "owned_value DESC, display_price DESC, c.name",
        "gain": "gain_loss DESC, c.name",
        "acquired": "col.acquired_date DESC, c.name",
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
               COALESCE(meta.favorite, 0) AS favorite,
               COALESCE(meta.missing_list, 0) AS missing_list,
               COALESCE(meta.wishlist, 0) AS wishlist,
               COALESCE(sale.sale_quantity, 0) AS sale_quantity,
               COALESCE(sale.sale_price, ({price_expr})) AS sale_price,
               ({allocated_expr}) AS container_quantity,
               ({deck_allocated_expr}) AS deck_quantity,
               MAX(COALESCE(col.quantity, 0) - ({allocated_expr}), 0) AS unassigned_quantity,
               MAX(COALESCE(col.quantity, 0) - ({deck_allocated_expr}), 0) AS saleable_quantity,
               ({price_expr}) AS display_price,
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value,
               COALESCE(col.quantity, 0) * (({price_expr}) - COALESCE(col.paid_price, 0.01)) AS gain_loss
        FROM cards c
        LEFT JOIN collection col ON col.user_id = ? AND col.card_id = c.scryfall_id
        LEFT JOIN card_meta meta ON meta.user_id = ? AND meta.card_id = c.scryfall_id AND meta.variant = COALESCE(col.variant, 'Normal')
        LEFT JOIN (
            SELECT card_id, variant, SUM(quantity) AS sale_quantity, MAX(asking_price) AS sale_price
            FROM card_sales
            WHERE user_id = ?
            GROUP BY card_id, variant
        ) sale ON sale.card_id = c.scryfall_id AND sale.variant = COALESCE(col.variant, 'Normal')
        {where_sql}
        ORDER BY {order_sql}
        LIMIT ?
        """,
        [user_id, user_id, user_id, user_id, user_id, user_id, user_id] + values + [limit],
    ).fetchall()
    cards = rows_to_dicts(rows)
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
                   asking_price AS sale_price
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
            saleable_remaining = max(0, int(card.get("saleable_quantity") or 0))
            for bucket in buckets:
                sale = sale_lookup.get((key[0], key[1], bucket["card_condition"]))
                bucket["sale_quantity"] = sale["sale_quantity"] if sale else 0
                bucket["sale_price"] = sale["sale_price"] if sale else card.get("display_price") or 0.01
                bucket_quantity = int(bucket.get("quantity") or 0)
                bucket["sale_available_quantity"] = min(bucket_quantity, saleable_remaining)
                saleable_remaining = max(0, saleable_remaining - bucket_quantity)
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
               cc.quantity, c.id, c.name, COALESCE(c.storage_type, 'other') AS storage_type,
               c.location
        FROM container_cards cc
        JOIN containers c ON c.id = cc.container_id
        WHERE c.user_id = ?
        ORDER BY c.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    for container in container_rows:
        key = (container["card_id"], container["variant"])
        container_memberships.setdefault(key, []).append({
            "id": container["id"],
            "name": container["name"],
            "storage_type": container["storage_type"],
            "location": container["location"],
            "quantity": container["quantity"],
        })
    for card in cards:
        key = (card.get("scryfall_id"), card.get("variant") or "Normal")
        card["container_memberships"] = container_memberships.get(key, [])
    return cards


def list_wishlist_cards(conn, query, user_id):
    params = urllib.parse.parse_qs(query)
    search = (params.get("search", [""])[0] or "").strip().lower()
    sort = params.get("sort", ["set"])[0]
    limit = min(int(params.get("limit", ["5000"])[0] or 5000), 5000)
    cards = list_cards(conn, urllib.parse.urlencode({
        "owned": "missing",
        "wishlist": "1",
        "sort": sort,
        "limit": str(limit),
        "search": params.get("search", [""])[0] or "",
    }), user_id)
    seen = {card.get("scryfall_id") for card in cards}
    rows = conn.execute(
        """
        SELECT card_id, variant, card_json
        FROM wishlist_cards
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """
    , (user_id,)).fetchall()
    for row in rows:
        if row["card_id"] in seen:
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
            "quantity": 0,
            "owned_quantity": 0,
            "wishlist": 1,
            "catalog_only": True,
            "display_price": prices.get("usd") or prices.get("usd_foil") or prices.get("usd_etched") or 0,
            "owned_value": 0,
            "gain_loss": 0,
            "favorite": 0,
            "missing_list": 0,
            "card_condition": DEFAULT_CARD_CONDITION,
        })
        cards.append(card)
        seen.add(row["card_id"])
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


def shared_card(conn, share_id):
    price_expr = current_price_sql("c")
    row = conn.execute(
        f"""
        SELECT c.*, col.share_id, col.quantity, col.paid_price, col.variant, col.acquired_date,
               COALESCE(col.card_condition, 'Near Mint') AS card_condition,
               COALESCE(col.graded, 0) AS graded,
               col.notes, COALESCE(meta.favorite, 0) AS favorite,
               ({price_expr}) AS display_price,
               col.quantity * ({price_expr}) AS owned_value,
               col.quantity * (({price_expr}) - col.paid_price) AS gain_loss
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        LEFT JOIN card_meta meta ON meta.user_id = col.user_id AND meta.card_id = col.card_id AND meta.variant = col.variant
        WHERE col.share_id = ? AND col.quantity > 0
        """,
        (share_id,),
    ).fetchone()
    if not row:
        raise KeyError("Shared card not found")
    return dict(row)


def purchase_history(conn, user_id, card_id, variant):
    return rows_to_dicts(conn.execute(
        """
        SELECT purchase_date,
               card_condition,
               SUM(quantity) AS quantity,
               SUM(total_price) AS total_price,
               ROUND(SUM(total_price) / SUM(quantity), 2) AS price_each,
               MIN(created_at) AS created_at
        FROM card_purchases
        WHERE user_id = ? AND card_id = ? AND variant = ?
        GROUP BY purchase_date, card_condition
        ORDER BY purchase_date DESC, created_at DESC
        """,
        (user_id, card_id, variant or "Normal"),
    ).fetchall())


def movement_history(conn, user_id, card_id, variant):
    variant = variant or "Normal"
    purchases = rows_to_dicts(conn.execute(
        """
        SELECT 'buy' AS movement_type,
               id AS movement_id,
               purchase_date AS movement_date,
               card_condition,
               quantity,
               total_price AS total_amount,
               ROUND(total_price / quantity, 2) AS price_each,
               created_at,
               NULL AS asking_price_each
        FROM card_purchases
        WHERE user_id = ? AND card_id = ? AND variant = ?
        """,
        (user_id, card_id, variant),
    ).fetchall())
    sales = rows_to_dicts(conn.execute(
        """
        SELECT 'sell' AS movement_type,
               id AS movement_id,
               sold_date AS movement_date,
               card_condition,
               quantity,
               quantity * sold_price_each AS total_amount,
               sold_price_each AS price_each,
               created_at,
               asking_price_each
        FROM card_sale_journal
        WHERE user_id = ? AND card_id = ? AND variant = ?
        """,
        (user_id, card_id, variant),
    ).fetchall())
    movements = purchases + sales
    return sorted(
        movements,
        key=lambda item: (
            item.get("movement_date") or "",
            item.get("created_at") or "",
            1 if item.get("movement_type") == "sell" else 0,
        ),
        reverse=True,
    )


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


def card_container_memberships(conn, user_id, card_id, variant):
    rows = conn.execute(
        """
        SELECT cc.quantity, c.id, c.name, COALESCE(c.storage_type, 'other') AS storage_type,
               c.location
        FROM container_cards cc
        JOIN containers c ON c.id = cc.container_id
        WHERE c.user_id = ? AND cc.card_id = ? AND COALESCE(NULLIF(cc.variant, ''), 'Normal') = ?
        ORDER BY c.name COLLATE NOCASE
        """,
        (user_id, card_id, variant or "Normal"),
    ).fetchall()
    return rows_to_dicts(rows)


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
        raise KeyError("Card not found")
    card = dict(row)
    card["purchases"] = purchase_history(conn, user_id, card_id, variant)
    card["movements"] = movement_history(conn, user_id, card_id, variant)
    card["deck_memberships"] = card_deck_memberships(conn, user_id, card_id, variant)
    card["container_memberships"] = card_container_memberships(conn, user_id, card_id, variant)
    return card


def add_card_purchase(conn, user_id, card_id, payload):
    card = conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    variant = payload.get("variant") or "Normal"
    quantity = max(1, int(money(payload.get("quantity"), fallback=1)))
    total_price = money(payload.get("total_price"), fallback=0.01)
    if total_price <= 0:
        total_price = 0.01
    purchase_date = payload.get("purchase_date") or today_iso()
    record_card_purchase(conn, user_id, card_id, variant, quantity, payload.get("card_condition"), purchase_date, total_price)
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


def update_wishlist(conn, user_id, card_id, payload):
    card = conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    variant = payload.get("variant") or "Normal"
    wishlist = 1 if payload.get("wishlist") else 0
    if not card:
        if wishlist:
            summary = wishlist_payload_summary(card_id, payload)
            conn.execute(
                """
                INSERT INTO wishlist_cards (user_id, card_id, variant, card_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, card_id) DO UPDATE SET
                    variant = excluded.variant,
                    card_json = excluded.card_json,
                    updated_at = excluded.updated_at
                """,
                (user_id, card_id, variant, json.dumps(summary), now_iso()),
            )
        else:
            conn.execute("DELETE FROM wishlist_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
        conn.commit()
        return {"ok": True, "wishlist": bool(wishlist), "catalog_only": True}
    if wishlist:
        owned = conn.execute(
            """
            SELECT COALESCE(quantity, 0) AS quantity
            FROM collection
            WHERE user_id = ? AND card_id = ? AND variant = ?
            """,
            (user_id, card_id, variant),
        ).fetchone()
        if owned and int(owned["quantity"] or 0) > 0:
            raise ValueError("Owned cards cannot be added to Wishlist.")
    conn.execute(
        """
        INSERT INTO card_meta (user_id, card_id, variant, favorite, missing_list, wishlist, updated_at)
        VALUES (?, ?, ?, 0, 0, ?, ?)
        ON CONFLICT(user_id, card_id, variant) DO UPDATE SET
            wishlist = excluded.wishlist,
            updated_at = excluded.updated_at
        """,
        (user_id, card_id, variant, wishlist, now_iso()),
    )
    if not wishlist:
        conn.execute("DELETE FROM wishlist_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
    conn.commit()
    return {"ok": True, "wishlist": bool(wishlist)}


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
            continue
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
            else:
                cursor = conn.execute(
                    "DELETE FROM card_sales WHERE user_id = ? AND card_id = ? AND variant = ?",
                    (user_id, card_id, variant),
                )
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
        deck_quantity = deck_allocated_quantity(conn, user_id, card_id, variant)
        saleable_total = max(0, int(owned["quantity"] or 0) - deck_quantity)
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
        saleable_for_condition = max(0, saleable_total - int((existing_other_sale and existing_other_sale["quantity"]) or 0))
        quantity = int(money(item.get("quantity"), fallback=1))
        if quantity < 1:
            raise ValueError("Sale quantity must be at least 1.")
        if quantity > max_quantity:
            raise ValueError("Sale quantity cannot exceed owned quantity.")
        if quantity > saleable_for_condition:
            if saleable_for_condition <= 0:
                raise ValueError("These cards cannot be sold as they are in a deck. Please remove them from the deck before selling or removing these cards from your collection.")
            raise ValueError(f"Only {saleable_for_condition} copy/copies are available to sell because deck cards are reserved.")
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
        conn.execute(
            """
            INSERT INTO card_sales (user_id, card_id, variant, card_condition, quantity, asking_price, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, card_id, variant, card_condition) DO UPDATE SET
                quantity = excluded.quantity,
                asking_price = excluded.asking_price,
                updated_at = excluded.updated_at
            """,
            (user_id, card_id, variant, sale_condition, quantity, asking_price, timestamp),
        )
        updated += 1
    conn.commit()
    return {"ok": True, "updated": updated, "skipped": skipped}


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
    if movement_type not in {"buy", "sell"} or movement_id <= 0:
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
        WHERE user_id = ? AND card_id = ? AND variant = ? AND id != ?
        """,
        (user_id, card_id, variant, movement_id),
    ).fetchone()["quantity"] or 0)
    if remaining_owned < allocated_quantity(conn, user_id, card_id, variant):
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
    conn.commit()
    refreshed = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    return {"ok": True, "card": dict(refreshed), "refreshed_at": synced_at}


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
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def session_token(self):
        return parse_cookies(self.headers.get("Cookie", "")).get(SESSION_COOKIE)

    def current_user(self, conn):
        return current_user_from_token(conn, self.session_token())

    def require_user(self, conn):
        user = self.current_user(conn)
        if not user:
            raise PermissionError("Please log in to use this feature.")
        return user

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            with connect() as conn:
                init_db(conn)
                if parsed.path == "/api/health":
                    return self.send_json({"ok": True, "status": "healthy"})
                if parsed.path == "/api/auth/session":
                    user = self.current_user(conn)
                    return self.send_json({"authenticated": bool(user), "user": user_payload(user)})
                if parsed.path == "/api/dashboard":
                    user = self.require_user(conn)
                    return self.send_json(dashboard(conn, user["id"]))
                if parsed.path == "/api/email/status":
                    return self.send_json(email_status())
                if parsed.path == "/api/debug/logs":
                    self.require_user(conn)
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(read_log_tail(params.get("lines", [200])[0]))
                if parsed.path == "/api/cards/for-sale":
                    user = self.require_user(conn)
                    return self.send_json({"cards": list_sale_cards(conn, parsed.query, user["id"])})
                if parsed.path == "/api/cards/wishlist":
                    user = self.require_user(conn)
                    return self.send_json({"cards": list_wishlist_cards(conn, parsed.query, user["id"])})
                if parsed.path == "/api/cards":
                    user = self.require_user(conn)
                    return self.send_json({"cards": list_cards(conn, parsed.query, user["id"])})
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
                if parsed.path == "/api/decks":
                    user = self.require_user(conn)
                    return self.send_json({"decks": list_decks(conn, user["id"])})
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
                match = re.match(r"^/api/sets/([^/]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(set_detail(conn, user["id"], urllib.parse.unquote(match.group(1)).lower()))
                match = re.match(r"^/api/shared/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(shared_card(conn, urllib.parse.unquote(match.group(1))))
                match = re.match(r"^/api/shared-decks/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(shared_deck(conn, urllib.parse.unquote(match.group(1))))
                if parsed.path == "/api/shared-favorites":
                    user = self.require_user(conn)
                    return self.send_json({
                        "cards": list_cards(conn, "owned=owned&favorite=1&sort=value&limit=5000", user["id"]),
                        "readonly": True,
                    })
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
                if parsed.path == "/api/export.csv":
                    user = self.require_user(conn)
                    data = export_csv(conn, user["id"]).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=foilfolio-collection.csv")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if parsed.path == "/api/export.json":
                    user = self.require_user(conn)
                    data = json.dumps(export_json(conn, user["id"]), indent=2).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=foilfolio-collection.json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except PermissionError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.UNAUTHORIZED)
        except Exception as exc:
            self.log_exception(exc)
            return self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        if (
            re.match(r"^/(cards|sets|decks)/[^/]+/?$", parsed.path)
            or re.match(r"^/card/[^/]+/[^/]+/?$", parsed.path)
            or re.match(r"^/favorites/shared/?$", parsed.path)
            or re.match(r"^/(favorites|collection|decks|containers|missing-list|for-sale|wishlist|search|import)/?$", parsed.path)
        ):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            with connect() as conn:
                init_db(conn)
                if parsed.path == "/api/auth/register":
                    result = register_user(conn, self.read_json())
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
                if parsed.path == "/api/sync":
                    return self.send_json(sync_catalog(conn))
                if parsed.path == "/api/import":
                    user = self.require_user(conn)
                    payload = self.read_json()
                    return self.send_json(import_csv(conn, payload.get("path") or DEFAULT_IMPORT, user["id"]))
                if parsed.path == "/api/import/preview":
                    return self.send_json(import_preview(conn, self.read_json()))
                if parsed.path == "/api/import/commit":
                    user = self.require_user(conn)
                    return self.send_json(commit_import_rows(conn, user["id"], self.read_json()))
                if parsed.path == "/api/cards":
                    user = self.require_user(conn)
                    return self.send_json(add_card_to_collection(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/cards/refresh-missing-colors":
                    user = self.require_user(conn)
                    payload = self.read_json()
                    return self.send_json(refresh_missing_color_metadata(conn, user["id"], payload.get("limit", 100)))
                if parsed.path == "/api/cards/missing-list":
                    user = self.require_user(conn)
                    return self.send_json(update_cards_missing_list(conn, user["id"], self.read_json()))
                if parsed.path == "/api/cards/for-sale":
                    user = self.require_user(conn)
                    return self.send_json(update_cards_for_sale(conn, user["id"], self.read_json()))
                if parsed.path == "/api/cards/sold":
                    user = self.require_user(conn)
                    return self.send_json(mark_card_sold(conn, user["id"], self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/purchases$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_card_purchase(conn, user["id"], urllib.parse.unquote(match.group(1)), self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/decks":
                    user = self.require_user(conn)
                    return self.send_json(create_deck(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/decks/([0-9]+)/cards$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_cards_to_deck(conn, user["id"], int(match.group(1)), self.read_json()))
                if parsed.path == "/api/containers":
                    user = self.require_user(conn)
                    return self.send_json(create_container(conn, user["id"], self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/containers/([0-9]+)/cards$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(add_cards_to_container(conn, user["id"], int(match.group(1)), self.read_json()))
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
        except urllib.error.URLError as exc:
            LOGGER.warning("%s %s network error: %s", self.command, self.path, exc)
            return self.send_json({"error": f"Network error: {exc}"}, HTTPStatus.BAD_GATEWAY)
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
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
                if parsed.path == "/api/user/settings":
                    user = self.require_user(conn)
                    return self.send_json(update_user_settings(conn, user["id"], self.read_json()))
                match = re.match(r"^/api/containers/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(update_container(conn, user["id"], int(match.group(1)), self.read_json()))
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
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
                if parsed.path == "/api/user/profile":
                    user = self.require_user(conn)
                    result = delete_user_profile(conn, user["id"])
                    return self.send_json(result, cookie=cookie_header("", clear=True))
                match = re.match(r"^/api/decks/([0-9]+)$", parsed.path)
                if match:
                    user = self.require_user(conn)
                    return self.send_json(delete_deck(conn, user["id"], int(match.group(1))))
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
        except PermissionError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.UNAUTHORIZED)
        except Exception as exc:
            self.log_exception(exc)
            return self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        return self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)


def serve(host="127.0.0.1", port=8000):
    with connect() as conn:
        init_db(conn)
    server = ThreadingHTTPServer((host, port), Handler)
    display_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    LOGGER.info("FoilFolio starting at http://%s:%s with database %s", display_host, port, DB_PATH)
    print(f"FoilFolio running at http://{display_host}:{port}")
    server.serve_forever()


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
        if command == "email-status":
            print(json.dumps(email_status(), indent=2))
            return 0
        if command == "email-diagnose":
            print(json.dumps(smtp_diagnostics(), indent=2))
            return 0
        if command == "email-test":
            if len(argv) < 3:
                print("Usage: python3 app.py email-test recipient@example.com [subject]")
                return 2
            subject = argv[3] if len(argv) > 3 else "FoilFolio Mailgun test"
            result = send_email(
                argv[2],
                subject,
                "FoilFolio Mailgun is configured correctly.",
                tags=["foilfolio", "test"],
            )
            print(json.dumps(result, indent=2))
            return 0
    if command == "serve":
        port = int(os.environ.get("PORT", argv[2] if len(argv) > 2 else 8000))
        host = os.environ.get("HOST", "127.0.0.1")
        serve(host, port)
        return 0
    print("Usage: python3 app.py [serve [port] | sync | import [csv_path] | seed [csv_path] | cache-owned-sets | refresh-missing-colors [limit] | email-status | email-diagnose | email-test recipient@example.com [subject] | log-status | logs [lines]]")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception:
        LOGGER.exception("Command failed: %s", " ".join(sys.argv[1:]) or "serve")
        raise
