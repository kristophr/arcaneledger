# Fiolfolio

A self-hosted Magic: The Gathering collection tracker. It uses Scryfall as the catalog and price source, stores data in SQLite, imports portfolio CSV exports, tracks decks, supports read-only share links, and exports your owned cards back to CSV.

## Run With Docker Compose

Start the app with the existing local SQLite data in `./data`:

```bash
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8000
```

To run it in the background:

```bash
docker compose up -d --build
```

To stop it:

```bash
docker compose down
```

## Import Or Seed In Docker

Put exports in `./imports`. The default import path inside the container is:

```text
/imports/export.csv
```

For a one-time catalog sync plus CSV import:

```bash
mkdir -p imports
cp "/Users/kristophr/Downloads/export(1).csv" imports/export.csv
docker compose run --rm fiolfolio python app.py seed /imports/export.csv
docker compose up -d --build
```

To sync current Scryfall prices later:

```bash
docker compose exec fiolfolio python app.py sync
```

To replace the collection from a new CSV export:

```bash
cp "/path/to/new-export.csv" imports/export.csv
docker compose exec fiolfolio python app.py import /imports/export.csv
```

## Local Python Run

```bash
python3 app.py seed
python3 app.py serve 8000
```

Then open:

```text
http://127.0.0.1:8000
```

## Commands

```bash
python3 app.py sync
python3 app.py import "/Users/kristophr/Downloads/export(1).csv"
python3 app.py seed "/Users/kristophr/Downloads/export(1).csv"
python3 app.py serve 8000
```

## Data

The SQLite database lives at:

```text
data/mtg_collection.sqlite
```

Docker Compose mounts that same folder to `/app/data`, so the database persists across image rebuilds and container restarts.

The app initializes and migrates its SQLite schema on startup, so new tables and columns are created automatically when you update the code and restart the container.

By default Fiolfolio syncs all paper Magic prints from Scryfall with:

```text
SCRYFALL_QUERY=game:paper
```

You can narrow or broaden that in `compose.yaml` using any valid Scryfall search query.

Main tables:

- `sets`: Scryfall set metadata.
- `cards`: Scryfall card catalog and current prices.
- `collection`: quantity owned, acquired date, paid price, variant, condition, and notes.
- `card_meta`: user metadata such as favorites.
- `decks`: deck names and share identifiers.
- `deck_cards`: card-to-deck metadata; assigning a card to a deck does not duplicate or delete collection data.
- `price_snapshots`: daily Scryfall price snapshots for value history.

If a CSV row has a missing or zero paid price, the importer stores `$0.01`.

## Sharing

Collection cards and decks can be shared with generated URLs:

```text
/cards/<share_id>
/decks/<share_id>
```

Shared URLs use a read-only interface with no app navigation or editing controls.

## Git Notes

The repository is intended to include source and configuration only:

- Commit: `app.py`, `static/`, `Dockerfile`, `compose.yaml`, `.dockerignore`, `.gitignore`, and `README.md`.
- Do not commit: `data/` or `imports/`.

The included `.gitignore` keeps local SQLite databases and import files out of Git.
