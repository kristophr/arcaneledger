# FoilFolio

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

To expose the app on a different host port, set `HOST_PORT` in `.env`:

```env
HOST_PORT=8088
```

Then restart with:

```bash
docker compose down
docker compose up -d --build
```

The app still listens on `8000` inside the container; `HOST_PORT` only changes the port you use from your browser.

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
docker compose run --rm foilfolio python app.py seed /imports/export.csv
docker compose up -d --build
```

To sync current Scryfall prices later:

```bash
docker compose exec foilfolio python app.py sync
```

To replace the collection from a new CSV export:

```bash
cp "/path/to/new-export.csv" imports/export.csv
docker compose exec foilfolio python app.py import /imports/export.csv
```

## Email

FoilFolio has email plumbing ready for future account confirmation and share-by-email features. SMTP is recommended for Mailgun if you already have working Mailgun SMTP credentials. Copy the example env file, then fill in your values:

```bash
cp .env.example .env
```

Recommended SMTP values for Mailgun:

```text
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@yourdomain.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=foilfolio@yourdomain.com
SMTP_FROM_NAME=FoilFolio
SMTP_SECURE=false
SMTP_STARTTLS=true
```

`SMTP_SECURE=false` means FoilFolio uses a normal SMTP connection first; with `SMTP_STARTTLS=true` it upgrades to TLS on port `587`.

The older Mailgun HTTP API settings are still supported as a fallback:

```text
MAILGUN_API_KEY=key-your-mailgun-api-key
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@yourdomain.com
MAILGUN_FROM_NAME=FoilFolio
```

For EU Mailgun API accounts, set `MAILGUN_API_BASE=https://api.eu.mailgun.net/v3`.

Do not commit `.env`; it is ignored by Git. Docker Compose reads `.env` for variable substitution, and `compose.yaml` explicitly passes only the app settings FoilFolio needs.

To check whether the app sees the email settings:

```bash
docker compose run --rm foilfolio python app.py email-status
```

To test the SMTP connection without sending an email:

```bash
docker compose run --rm foilfolio python app.py email-diagnose
```

To send a smoke-test email after credentials are ready:

```bash
docker compose run --rm foilfolio python app.py email-test you@example.com
```

## Debug Logs

FoilFolio writes server startup messages, requests, network warnings, and unexpected server errors to a rotating log file:

```text
data/logs/foilfolio.log
```

From Docker, check the configured log path and status:

```bash
docker compose run --rm foilfolio python app.py log-status
```

To show the last 200 log lines:

```bash
docker compose run --rm foilfolio python app.py logs
```

Or ask for a specific number of lines:

```bash
docker compose run --rm foilfolio python app.py logs 500
```

The same log tail is also available to a logged-in user at:

```text
/api/debug/logs?lines=200
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
python3 app.py email-status
python3 app.py email-diagnose
python3 app.py email-test you@example.com
python3 app.py log-status
python3 app.py logs 200
```

## Data

The SQLite database lives at:

```text
data/mtg_collection.sqlite
```

Docker Compose mounts that same folder to `/app/data`, so the database persists across image rebuilds and container restarts.

The app initializes and migrates its SQLite schema on startup, so new tables and columns are created automatically when you update the code and restart the container.

By default FoilFolio syncs all paper Magic prints from Scryfall with:

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
