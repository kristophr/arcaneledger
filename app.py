#!/usr/bin/env python3
import csv
import io
import json
import os
import re
import secrets
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("DB_PATH", DATA_DIR / "mtg_collection.sqlite"))
DEFAULT_IMPORT = Path(os.environ.get("DEFAULT_IMPORT", "/Users/kristophr/Downloads/export(1).csv"))
SCRYFALL_SETS_URL = "https://api.scryfall.com/sets"
SCRYFALL_SET_URL = "https://api.scryfall.com/sets/{set_code}"
SCRYFALL_SEARCH_URL = "https://api.scryfall.com/cards/search"
SCRYFALL_CARD_URL = "https://api.scryfall.com/cards/{set_code}/{collector_number}"
SCRYFALL_ID_URL = "https://api.scryfall.com/cards/{card_id}"
SCRYFALL_QUERY = os.environ.get("SCRYFALL_QUERY", "game:paper")
SCRYFALL_LANGUAGE = os.environ.get("SCRYFALL_LANGUAGE", "en")
SUPPORTED_SCRYFALL_LANGUAGES = {"en"}
USER_AGENT = "fiolfolio/0.1"


def now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


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


def scryfall_language(value=None):
    language = (value or SCRYFALL_LANGUAGE or "en").strip().lower()
    return language if language in SUPPORTED_SCRYFALL_LANGUAGES else "en"


def scryfall_query_with_language(query, language=None):
    text = (query or "").strip()
    if re.search(r"\blang:[a-z-]+\b", text, flags=re.IGNORECASE):
        return text
    return f"{text} lang:{scryfall_language(language)}".strip()


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


def upsert_card(conn, card, synced_at):
    upsert_set_from_card(conn, card, synced_at)
    prices = card.get("prices") or {}
    conn.execute(
        """
        INSERT INTO cards (
            scryfall_id, oracle_id, name, set_code, set_name, collector_number, rarity,
            type_line, flavor_name, flavor_text, layout, finishes, image_small, image_normal, image_art, scryfall_uri,
            current_usd, current_usd_foil, current_usd_etched, last_synced_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(scryfall_id) DO UPDATE SET
            oracle_id = excluded.oracle_id,
            name = excluded.name,
            set_code = excluded.set_code,
            set_name = excluded.set_name,
            collector_number = excluded.collector_number,
            rarity = excluded.rarity,
            type_line = excluded.type_line,
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

        CREATE TABLE IF NOT EXISTS cards (
            scryfall_id TEXT PRIMARY KEY,
            oracle_id TEXT,
            name TEXT NOT NULL,
            set_code TEXT NOT NULL,
            set_name TEXT NOT NULL,
            collector_number TEXT NOT NULL,
            rarity TEXT,
            type_line TEXT,
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
            card_id TEXT NOT NULL,
            share_id TEXT UNIQUE,
            quantity INTEGER NOT NULL DEFAULT 0,
            acquired_date TEXT,
            paid_price REAL NOT NULL DEFAULT 0.01,
            variant TEXT NOT NULL DEFAULT 'Normal',
            card_condition TEXT,
            notes TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (card_id, variant),
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS card_meta (
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            favorite INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (card_id, variant),
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
            share_id TEXT UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS deck_cards (
            deck_id INTEGER NOT NULL,
            card_id TEXT NOT NULL,
            variant TEXT NOT NULL DEFAULT 'Normal',
            added_at TEXT NOT NULL,
            PRIMARY KEY (deck_id, card_id, variant),
            FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE,
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_cards_lookup ON cards(set_code, collector_number, name);
        CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
        CREATE INDEX IF NOT EXISTS idx_collection_quantity ON collection(quantity);
        CREATE INDEX IF NOT EXISTS idx_deck_cards_card ON deck_cards(card_id, variant);
        CREATE INDEX IF NOT EXISTS idx_snapshots_date ON price_snapshots(snapshot_date);
        """
    )
    migrate_sets_schema(conn)
    migrate_cards_schema(conn)
    migrate_collection_schema(conn)
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


def migrate_collection_schema(conn):
    columns = conn.execute("PRAGMA table_info(collection)").fetchall()
    card_id_pk = [col for col in columns if col["name"] == "card_id" and col["pk"] == 1]
    variant_pk = [col for col in columns if col["name"] == "variant" and col["pk"] == 2]
    if not card_id_pk or variant_pk:
        if "share_id" not in {col["name"] for col in columns}:
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
            card_condition TEXT,
            notes TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (card_id, variant),
            FOREIGN KEY (card_id) REFERENCES cards(scryfall_id) ON DELETE CASCADE
        );
        INSERT INTO collection (card_id, quantity, acquired_date, paid_price, variant, card_condition, notes, updated_at)
        SELECT card_id, quantity, acquired_date, paid_price, COALESCE(NULLIF(variant, ''), 'Normal'), card_condition, notes, updated_at
        FROM collection_old;
        DROP TABLE collection_old;
        """
    )


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
        SELECT card_id, variant
        FROM collection
        WHERE share_id IS NULL OR share_id = ''
        """
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE collection SET share_id = ? WHERE card_id = ? AND variant = ?",
            (new_share_id(conn), row["card_id"], row["variant"]),
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


def cache_owned_sets(conn):
    rows = conn.execute(
        """
        SELECT DISTINCT c.set_code
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        WHERE col.quantity > 0
        ORDER BY c.set_code
        """
    ).fetchall()
    results = []
    for row in rows:
        results.append(cache_set_catalog(conn, row["set_code"]))
    return {"sets": results}


def card_summary(card, owned_quantity=0):
    prices = card.get("prices") or {}
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


def owned_quantities_for_cards(conn, card_ids):
    if not card_ids:
        return {}
    placeholders = ",".join("?" for _ in card_ids)
    rows = conn.execute(
        f"""
        SELECT card_id, COALESCE(SUM(quantity), 0) AS owned_quantity
        FROM collection
        WHERE card_id IN ({placeholders})
        GROUP BY card_id
        """,
        card_ids,
    ).fetchall()
    return {row["card_id"]: row["owned_quantity"] or 0 for row in rows}


def search_scryfall_cards(conn, query, language=None):
    text = (query or "").strip()
    if len(text) < 2:
        return {"cards": []}
    params = {
        "q": scryfall_query_with_language(f"{text} game:paper", language),
        "unique": "prints",
        "include_extras": "true",
        "include_variations": "true",
        "order": "released",
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
    owned_quantities = owned_quantities_for_cards(conn, [card.get("id") for card in scryfall_cards if card.get("id")])
    cards = [
        card_summary(card, owned_quantities.get(card.get("id"), 0))
        for card in scryfall_cards
    ]
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


def add_card_to_collection(conn, payload):
    card_id = payload.get("scryfall_id") or payload.get("card_id")
    if not card_id:
        raise ValueError("Choose a Scryfall card first.")
    quantity = max(1, int(money(payload.get("quantity"), fallback=1)))
    paid_price = money(payload.get("paid_price"), fallback=0.01)
    if paid_price <= 0:
        paid_price = 0.01
    acquired_date = payload.get("acquired_date") or today_iso()
    variant = payload.get("variant") or "Normal"

    url = SCRYFALL_ID_URL.format(card_id=urllib.parse.quote(card_id))
    synced_at = now_iso()
    scryfall_card = request_json(url)
    validate_selected_card(scryfall_card, payload)
    upsert_card(conn, scryfall_card, synced_at)
    cache_set_catalog(conn, scryfall_card.get("set"))

    existing = conn.execute(
        """
        SELECT quantity, paid_price, acquired_date, card_condition, notes, share_id
        FROM collection
        WHERE card_id = ? AND variant = ?
        """,
        (card_id, variant),
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
        card_condition = existing["card_condition"] or ""
        notes = existing["notes"] or ""
        share_id = existing["share_id"] or new_share_id(conn)
    else:
        new_quantity = quantity
        card_condition = ""
        notes = ""
        share_id = new_share_id(conn)

    conn.execute(
        """
        INSERT INTO collection (card_id, share_id, quantity, acquired_date, paid_price, variant, card_condition, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(card_id, variant) DO UPDATE SET
            share_id = COALESCE(collection.share_id, excluded.share_id),
            quantity = excluded.quantity,
            acquired_date = excluded.acquired_date,
            paid_price = excluded.paid_price,
            card_condition = excluded.card_condition,
            notes = excluded.notes,
            updated_at = excluded.updated_at
        """,
        (card_id, share_id, new_quantity, acquired_date, paid_price, variant, card_condition, notes, now_iso()),
    )
    card = conn.execute("SELECT * FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    conn.commit()
    return {
        "ok": True,
        "card": dict(card),
        "quantity": new_quantity,
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


def import_csv(conn, csv_path):
    init_db(conn)
    path = Path(csv_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    existing_share_ids = {
        (row["card_id"], row["variant"]): row["share_id"]
        for row in conn.execute(
            "SELECT card_id, variant, share_id FROM collection WHERE share_id IS NOT NULL AND share_id != ''"
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
                    "card_condition": source.get("Card Condition") or "",
                    "notes": [],
                }
            record = records[key]
            record["quantity"] += quantity
            record["paid_total"] += quantity * paid
            acquired_date = source.get("Date Added") or today_iso()
            if acquired_date and (not record["acquired_date"] or acquired_date < record["acquired_date"]):
                record["acquired_date"] = acquired_date
            if source.get("Card Condition"):
                record["card_condition"] = source.get("Card Condition")
            if source.get("Notes"):
                record["notes"].append(source.get("Notes"))
            imported += 1
    conn.execute("DELETE FROM collection")
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
            INSERT INTO collection (card_id, share_id, quantity, acquired_date, paid_price, variant, card_condition, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(card_id, variant) DO UPDATE SET
                share_id = COALESCE(collection.share_id, excluded.share_id),
                quantity = excluded.quantity,
                acquired_date = excluded.acquired_date,
                paid_price = excluded.paid_price,
                card_condition = excluded.card_condition,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                record["card_id"],
                share_id,
                record["quantity"],
                record["acquired_date"],
                paid_price,
                record["variant"],
                record["card_condition"],
                "; ".join(record["notes"]),
                updated_at,
            ),
        )
    conn.commit()
    return {"imported_rows": imported, "unmatched_rows": unmatched}


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


def collection_value_history(conn, months=24):
    price_expr = current_price_sql("c")
    first_acquired = conn.execute(
        "SELECT MIN(acquired_date) AS first_acquired FROM collection WHERE quantity > 0 AND acquired_date IS NOT NULL AND acquired_date != ''"
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
        WHERE col.quantity > 0
          AND col.acquired_date IS NOT NULL
          AND col.acquired_date != ''
        GROUP BY acquired_month
        ORDER BY acquired_month
        """
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
        WHERE col.quantity > 0
          AND col.acquired_date IS NOT NULL
          AND col.acquired_date != ''
          AND col.acquired_date < ?
        """,
        (start_month.isoformat(),),
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


def set_completion(conn, limit=10):
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
        LEFT JOIN collection col ON col.card_id = c.scryfall_id
        GROUP BY c.set_code
        HAVING owned_cards > 0 AND total_cards > 0
        ORDER BY (owned_cards * 1.0 / total_cards) DESC, owned_cards DESC, set_name
        LIMIT ?
        """,
        (limit,),
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


def set_detail(conn, set_code):
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
        LEFT JOIN collection col ON col.card_id = c.scryfall_id
        WHERE c.set_code = ?
        GROUP BY c.set_code
        """,
        (set_code,),
    ).fetchone()
    if not row:
        raise KeyError("Set not found")
    total = row["total_cards"] or 0
    owned = row["owned_cards"] or 0
    return {
        **dict(row),
        "completion_percent": round((owned / total * 100) if total else 0, 1),
    }


def dashboard(conn):
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
        LEFT JOIN collection col ON col.card_id = c.scryfall_id
        """
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
        LEFT JOIN card_meta meta ON meta.card_id = col.card_id AND meta.variant = col.variant
        WHERE col.quantity > 0
        ORDER BY owned_value DESC, c.name
        LIMIT 10
        """
    ).fetchall())
    history = collection_value_history(conn)
    set_breakdown = rows_to_dicts(conn.execute(
        f"""
        SELECT c.set_name, SUM(col.quantity) AS quantity,
               SUM(col.quantity * ({price_expr})) AS value
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        WHERE col.quantity > 0
        GROUP BY c.set_name
        ORDER BY value DESC
        """
    ).fetchall())
    result = dict(totals)
    result["gain_loss"] = result["current_total"] - result["paid_total"]
    result["gain_loss_percent"] = (result["gain_loss"] / result["paid_total"] * 100) if result["paid_total"] else 0
    result["top_cards"] = top
    result["history"] = history
    result["set_breakdown"] = set_breakdown
    result["set_completion"] = set_completion(conn)
    return result


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def list_decks(conn):
    rows = conn.execute(
        """
        SELECT d.id, d.share_id, d.name, d.created_at, d.updated_at,
               COUNT(dc.card_id) AS card_count
        FROM decks d
        LEFT JOIN deck_cards dc ON dc.deck_id = d.id
        GROUP BY d.id
        ORDER BY d.updated_at DESC, d.name COLLATE NOCASE
        """
    ).fetchall()
    return rows_to_dicts(rows)


def create_deck(conn, payload):
    name = re.sub(r"\s+", " ", (payload.get("name") or "").strip())
    if not name:
        raise ValueError("Deck name is required.")
    if len(name) > 20:
        raise ValueError("Deck name must be 20 characters or fewer.")
    timestamp = now_iso()
    share_id = new_deck_share_id(conn)
    cursor = conn.execute(
        """
        INSERT INTO decks (share_id, name, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (share_id, name, timestamp, timestamp),
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
        },
    }


def deck_cards(conn, deck_id):
    price_expr = current_price_sql("c")
    rows = conn.execute(
        f"""
        SELECT c.*, dc.variant, dc.added_at,
               COALESCE(col.quantity, 0) AS quantity,
               COALESCE(col.paid_price, 0.01) AS paid_price,
               col.acquired_date,
               col.share_id,
               ({price_expr}) AS display_price,
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value
        FROM deck_cards dc
        JOIN cards c ON c.scryfall_id = dc.card_id
        LEFT JOIN collection col ON col.card_id = dc.card_id AND col.variant = dc.variant
        WHERE dc.deck_id = ?
        ORDER BY c.name COLLATE NOCASE, dc.variant
        """,
        (deck_id,),
    ).fetchall()
    return rows_to_dicts(rows)


def deck_detail(conn, deck_id):
    deck = conn.execute(
        """
        SELECT d.id, d.share_id, d.name, d.created_at, d.updated_at,
               COUNT(dc.card_id) AS card_count
        FROM decks d
        LEFT JOIN deck_cards dc ON dc.deck_id = d.id
        WHERE d.id = ?
        GROUP BY d.id
        """,
        (deck_id,),
    ).fetchone()
    if not deck:
        raise KeyError("Deck not found")
    payload = dict(deck)
    payload["cards"] = deck_cards(conn, deck_id)
    return payload


def shared_deck(conn, share_id):
    deck = conn.execute("SELECT id FROM decks WHERE share_id = ?", (share_id,)).fetchone()
    if not deck:
        raise KeyError("Shared deck not found")
    payload = deck_detail(conn, deck["id"])
    payload["readonly"] = True
    return payload


def add_cards_to_deck(conn, deck_id, payload):
    deck = conn.execute("SELECT id FROM decks WHERE id = ?", (deck_id,)).fetchone()
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
        if not card_id:
            continue
        owned = conn.execute(
            """
            SELECT 1
            FROM collection
            WHERE card_id = ? AND variant = ? AND quantity > 0
            """,
            (card_id, variant),
        ).fetchone()
        if not owned:
            continue
        conn.execute(
            """
            INSERT INTO deck_cards (deck_id, card_id, variant, added_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(deck_id, card_id, variant) DO UPDATE SET
                added_at = deck_cards.added_at
            """,
            (deck_id, card_id, variant, timestamp),
        )
        added += 1
    conn.execute("UPDATE decks SET updated_at = ? WHERE id = ?", (timestamp, deck_id))
    conn.commit()
    return {"ok": True, "added": added, "deck_id": deck_id}


def remove_card_from_deck(conn, deck_id, payload):
    deck = conn.execute("SELECT id FROM decks WHERE id = ?", (deck_id,)).fetchone()
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


def delete_deck(conn, deck_id):
    cursor = conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
    if cursor.rowcount == 0:
        raise KeyError("Deck not found")
    conn.commit()
    return {"ok": True, "deleted": deck_id}


def list_cards(conn, query):
    params = urllib.parse.parse_qs(query)
    search = (params.get("search", [""])[0] or "").strip()
    owned = params.get("owned", ["all"])[0]
    sort = params.get("sort", ["value"])[0]
    set_code = (params.get("set", [""])[0] or "").strip().lower()
    limit = min(int(params.get("limit", ["250"])[0] or 250), 5000)
    where = []
    values = []
    if set_code:
        where.append("lower(c.set_code) = ?")
        values.append(set_code)
    if search:
        where.append("(c.name LIKE ? OR c.set_name LIKE ? OR c.collector_number LIKE ? OR c.type_line LIKE ?)")
        needle = f"%{search}%"
        values.extend([needle, needle, needle, needle])
    if owned == "owned":
        where.append("COALESCE(col.quantity, 0) > 0")
    elif owned == "missing":
        where.append("COALESCE(col.quantity, 0) = 0")
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    price_expr = current_price_sql("c")
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
               COALESCE(col.variant, 'Normal') AS variant, col.share_id, col.acquired_date, col.card_condition, col.notes,
               COALESCE(meta.favorite, 0) AS favorite,
               ({price_expr}) AS display_price,
               COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value,
               COALESCE(col.quantity, 0) * (({price_expr}) - COALESCE(col.paid_price, 0.01)) AS gain_loss
        FROM cards c
        LEFT JOIN collection col ON col.card_id = c.scryfall_id
        LEFT JOIN card_meta meta ON meta.card_id = c.scryfall_id AND meta.variant = COALESCE(col.variant, 'Normal')
        {where_sql}
        ORDER BY {order_sql}
        LIMIT ?
        """,
        values + [limit],
    ).fetchall()
    return rows_to_dicts(rows)


def shared_card(conn, share_id):
    price_expr = current_price_sql("c")
    row = conn.execute(
        f"""
        SELECT c.*, col.share_id, col.quantity, col.paid_price, col.variant, col.acquired_date,
               col.card_condition, col.notes, COALESCE(meta.favorite, 0) AS favorite,
               ({price_expr}) AS display_price,
               col.quantity * ({price_expr}) AS owned_value,
               col.quantity * (({price_expr}) - col.paid_price) AS gain_loss
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        LEFT JOIN card_meta meta ON meta.card_id = col.card_id AND meta.variant = col.variant
        WHERE col.share_id = ? AND col.quantity > 0
        """,
        (share_id,),
    ).fetchone()
    if not row:
        raise KeyError("Shared card not found")
    return dict(row)


def update_collection(conn, card_id, payload):
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
        "SELECT share_id FROM collection WHERE card_id = ? AND variant = ?",
        (card_id, original_variant),
    ).fetchone()
    existing_meta = conn.execute(
        "SELECT favorite FROM card_meta WHERE card_id = ? AND variant = ?",
        (card_id, original_variant),
    ).fetchone()
    if quantity == 0:
        conn.execute("DELETE FROM collection WHERE card_id = ? AND variant = ?", (card_id, original_variant))
    else:
        share_id = existing_collection["share_id"] if existing_collection and existing_collection["share_id"] else new_share_id(conn)
        if original_variant != variant:
            target_collection = conn.execute(
                "SELECT share_id FROM collection WHERE card_id = ? AND variant = ?",
                (card_id, variant),
            ).fetchone()
            if target_collection and target_collection["share_id"]:
                share_id = target_collection["share_id"]
            conn.execute("DELETE FROM collection WHERE card_id = ? AND variant = ?", (card_id, original_variant))
        conn.execute(
            """
            INSERT INTO collection (card_id, share_id, quantity, acquired_date, paid_price, variant, card_condition, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(card_id, variant) DO UPDATE SET
                share_id = COALESCE(collection.share_id, excluded.share_id),
                quantity = excluded.quantity,
                acquired_date = excluded.acquired_date,
                paid_price = excluded.paid_price,
                variant = excluded.variant,
                card_condition = excluded.card_condition,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                card_id,
                share_id,
                quantity,
                payload.get("acquired_date") or today_iso(),
                paid_price,
                variant,
                payload.get("card_condition") or "",
                payload.get("notes") or "",
                now_iso(),
            ),
        )
        if existing_meta and original_variant != variant:
            conn.execute(
                """
                INSERT INTO card_meta (card_id, variant, favorite, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(card_id, variant) DO UPDATE SET
                    favorite = excluded.favorite,
                    updated_at = excluded.updated_at
                """,
                (card_id, variant, existing_meta["favorite"], now_iso()),
            )
    conn.commit()
    return {"ok": True}


def delete_collection_entry(conn, card_id, payload):
    variant = payload.get("variant") or "Normal"
    cursor = conn.execute(
        "DELETE FROM collection WHERE card_id = ? AND variant = ?",
        (card_id, variant),
    )
    if cursor.rowcount == 0:
        raise KeyError("Collection entry not found")
    conn.commit()
    return {"ok": True, "deleted": {"card_id": card_id, "variant": variant}}


def update_favorite(conn, card_id, payload):
    card = conn.execute("SELECT 1 FROM cards WHERE scryfall_id = ?", (card_id,)).fetchone()
    if not card:
        raise KeyError("Card not found")
    variant = payload.get("variant") or "Normal"
    favorite = 1 if payload.get("favorite") else 0
    if not favorite:
        conn.execute("DELETE FROM card_meta WHERE card_id = ? AND variant = ?", (card_id, variant))
        conn.commit()
        return {"ok": True, "favorite": False}
    conn.execute(
        """
        INSERT INTO card_meta (card_id, variant, favorite, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(card_id, variant) DO UPDATE SET
            favorite = excluded.favorite,
            updated_at = excluded.updated_at
        """,
        (card_id, variant, favorite, now_iso()),
    )
    conn.commit()
    return {"ok": True, "favorite": bool(favorite)}


def export_rows(conn):
    price_expr = current_price_sql("c")
    return conn.execute(
        f"""
        SELECT c.name, c.set_name, c.collector_number, c.rarity, c.type_line,
               COALESCE(col.quantity, 0) AS quantity, COALESCE(col.acquired_date, '') AS acquired_date,
               COALESCE(col.paid_price, 0.01) AS paid_price, COALESCE(col.variant, 'Normal') AS variant,
               COALESCE(col.card_condition, '') AS card_condition, COALESCE(col.notes, '') AS notes,
               COALESCE(meta.favorite, 0) AS favorite,
               ({price_expr}) AS current_value, COALESCE(col.quantity, 0) * ({price_expr}) AS owned_value,
               c.scryfall_uri
        FROM collection col
        JOIN cards c ON c.scryfall_id = col.card_id
        LEFT JOIN card_meta meta ON meta.card_id = col.card_id AND meta.variant = col.variant
        WHERE col.quantity > 0
        ORDER BY owned_value DESC, c.name
        """
    ).fetchall()


def export_csv(conn):
    rows = export_rows(conn)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Set", "Card Number", "Rarity", "Type", "Quantity", "Date Acquired",
        "Price Paid", "Variant", "Condition", "Notes", "Favorite", "Current Value", "Owned Value", "Scryfall URL"
    ])
    for row in rows:
        writer.writerow([row[key] for key in row.keys()])
    return output.getvalue()


def export_json(conn):
    keys = [
        "name", "set_name", "collector_number", "rarity", "type_line", "quantity", "acquired_date",
        "paid_price", "variant", "card_condition", "notes", "favorite", "current_value", "owned_value", "scryfall_uri"
    ]
    return [
        {key: row[key] for key in keys}
        for row in export_rows(conn)
    ]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, payload, status=HTTPStatus.OK):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            with connect() as conn:
                init_db(conn)
                if parsed.path == "/api/dashboard":
                    return self.send_json(dashboard(conn))
                if parsed.path == "/api/cards":
                    return self.send_json({"cards": list_cards(conn, parsed.query)})
                if parsed.path == "/api/decks":
                    return self.send_json({"decks": list_decks(conn)})
                match = re.match(r"^/api/decks/([0-9]+)$", parsed.path)
                if match:
                    return self.send_json(deck_detail(conn, int(match.group(1))))
                match = re.match(r"^/api/sets/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(set_detail(conn, urllib.parse.unquote(match.group(1)).lower()))
                match = re.match(r"^/api/shared/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(shared_card(conn, urllib.parse.unquote(match.group(1))))
                match = re.match(r"^/api/shared-decks/([^/]+)$", parsed.path)
                if match:
                    return self.send_json(shared_deck(conn, urllib.parse.unquote(match.group(1))))
                if parsed.path == "/api/scryfall/search":
                    params = urllib.parse.parse_qs(parsed.query)
                    return self.send_json(search_scryfall_cards(
                        conn,
                        params.get("q", [""])[0],
                        params.get("lang", [None])[0],
                    ))
                if parsed.path == "/api/export.csv":
                    data = export_csv(conn).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=fiolfolio-collection.csv")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if parsed.path == "/api/export.json":
                    data = json.dumps(export_json(conn), indent=2).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=fiolfolio-collection.json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        if re.match(r"^/(cards|sets|decks)/[^/]+/?$", parsed.path):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            with connect() as conn:
                init_db(conn)
                if parsed.path == "/api/sync":
                    return self.send_json(sync_catalog(conn))
                if parsed.path == "/api/import":
                    payload = self.read_json()
                    return self.send_json(import_csv(conn, payload.get("path") or DEFAULT_IMPORT))
                if parsed.path == "/api/cards":
                    return self.send_json(add_card_to_collection(conn, self.read_json()), HTTPStatus.CREATED)
                if parsed.path == "/api/decks":
                    return self.send_json(create_deck(conn, self.read_json()), HTTPStatus.CREATED)
                match = re.match(r"^/api/decks/([0-9]+)/cards$", parsed.path)
                if match:
                    return self.send_json(add_cards_to_deck(conn, int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/collection$", parsed.path)
                if match:
                    return self.send_json(update_collection(conn, urllib.parse.unquote(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/favorite$", parsed.path)
                if match:
                    return self.send_json(update_favorite(conn, urllib.parse.unquote(match.group(1)), self.read_json()))
        except urllib.error.URLError as exc:
            return self.send_json({"error": f"Network error: {exc}"}, HTTPStatus.BAD_GATEWAY)
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        return self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            with connect() as conn:
                init_db(conn)
                match = re.match(r"^/api/decks/([0-9]+)$", parsed.path)
                if match:
                    return self.send_json(delete_deck(conn, int(match.group(1))))
                match = re.match(r"^/api/decks/([0-9]+)/cards$", parsed.path)
                if match:
                    return self.send_json(remove_card_from_deck(conn, int(match.group(1)), self.read_json()))
                match = re.match(r"^/api/cards/([^/]+)/collection$", parsed.path)
                if match:
                    return self.send_json(delete_collection_entry(conn, urllib.parse.unquote(match.group(1)), self.read_json()))
        except KeyError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        return self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)


def serve(host="127.0.0.1", port=8000):
    with connect() as conn:
        init_db(conn)
    server = ThreadingHTTPServer((host, port), Handler)
    display_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    print(f"Fiolfolio running at http://{display_host}:{port}")
    server.serve_forever()


def main(argv):
    command = argv[1] if len(argv) > 1 else "serve"
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
    if command == "serve":
        port = int(os.environ.get("PORT", argv[2] if len(argv) > 2 else 8000))
        host = os.environ.get("HOST", "127.0.0.1")
        serve(host, port)
        return 0
    print("Usage: python3 app.py [serve [port] | sync | import [csv_path] | seed [csv_path] | cache-owned-sets]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
