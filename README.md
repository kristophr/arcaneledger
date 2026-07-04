# Arcane Ledger

**Version:** 0.5.0 beta

A Magic: The Gathering collection tracker. It uses Scryfall as the catalog and price source, stores data in SQLite, tracks collection value and purchase/sale history, manages decks, containers, wishlists, reports, store listings, profiles, public sharing, contributor news, and exports your data back to CSV, Moxfield CSV, or spreadsheet-friendly formats.

## Highlights

- Track owned cards by exact printing, variant, condition, quantity, purchase price, current market value, and ledger history.
- Capture daily Scryfall market price snapshots for owned cards so card value charts build real market history over time.
- Review purchase entry ledgers from a card page to see every card bought in the same store/date entry, including per-card and batch totals.
- Build decks from owned or wanted cards, share public deck pages, and browse public decks from other users.
- Organize physical storage with containers, capacity tracking, and per-card allocations by variant and condition.
- Import Arcane Ledger CSV/JSON data, Moxfield CSV exports, or Magic: The Gathering Arena CSV/deck lists with guided review before saving.
- Bulk import container allocations from the Containers page using CSV or JSON with validation for card ownership, variant, condition, available uncontainered quantity, and container capacity.
- Build wishlists, favorites, store listings, profile posts, and public comments around cards and decks.
- Profile blog and favorites subpages provide focused full-width feeds, with profile card clicks opening inline card preview modals.
- Share cards, decks, sets, containers, wishlists, and favorites from one clean modal with copy-link and email options.
- Publish and share contributor-written News articles with drafts, Markdown editing, image uploads, scheduled publishing, public reading/search, copy-link sharing, and email sharing.
- Filter collection views by set and container status to quickly find stored or unstored cards.
- Run collection reports with selectable fields, including `card_id` for storage imports, filters, CSV/XLS export, and email delivery with CSV attachments.
- Admin tools include user management, Contributor role assignment, Pro feature limits, moderation reports, email templates with membership triggers, announcements, logs, server details, and wallpaper management.
- Phone-sized layouts now use compact navigation, stacked cards, and wider mobile modals so the app is more usable on iPhone and other narrow screens.

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

Set the public URL used for email verification links:

```env
APP_BASE_URL=https://arcaneledger.example.com
```

Security defaults can also be adjusted in `.env`:

```env
SESSION_IDLE_MINUTES=30
EMAIL_VERIFICATION_MINUTES=30
PASSWORD_RESET_MINUTES=30
```

On a fresh server with no users, the home page shows `Claim Server`. The first account created through that flow becomes user `1` and gets the `admin` role. After the server is claimed, the normal login/create-account flow is used. If email is configured, new accounts verify by email; if not, accounts can be created directly with email and password.

Optional fallback admin emails can be configured with a comma-separated list:

```env
ADMIN_EMAILS=admin@example.com,friend@example.com
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
docker compose run --rm arcaneledger python app.py seed /imports/export.csv
docker compose up -d --build
```

To sync current Scryfall prices later:

```bash
docker compose exec arcaneledger python app.py sync
```

To replace the collection from a new CSV export:

```bash
cp "/path/to/new-export.csv" imports/export.csv
docker compose exec arcaneledger python app.py import /imports/export.csv
```

The web Import page supports Arcane Ledger JSON/CSV, Moxfield CSV, and Magic: The Gathering Arena CSV uploads. Moxfield and Arena CSV imports expect these headers:

```text
Count, Name, Edition, Condition, Language, Foil, Collector Number, Alter, Playtest Card, Purchase Price
```

`Alter` and `Playtest Card` are ignored during import. Arcane Ledger Moxfield-compatible exports include those columns as `false`.

Container allocation imports now live on the Containers page under `Import Allocations`. Use that workflow when cards already exist in your collection and you want to assign physical copies to containers by `card_id`, `variant`, `condition`, `quantity`, and `container_id`.

## Email

Arcane Ledger has email plumbing ready for future account confirmation and share-by-email features. SMTP is recommended for Mailgun if you already have working Mailgun SMTP credentials. Copy the example env file, then fill in your values:

```bash
cp .env.example .env
```

Recommended SMTP values for Mailgun:

```text
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@yourdomain.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=arcaneledger@yourdomain.com
SMTP_FROM_NAME=Arcane Ledger
SMTP_SECURE=false
SMTP_STARTTLS=true
```

`SMTP_SECURE=false` means Arcane Ledger uses a normal SMTP connection first; with `SMTP_STARTTLS=true` it upgrades to TLS on port `587`.

Arcane Ledger also accepts Laravel-style SMTP names if you already have those:

```text
MAIL_DRIVER=smtp
MAIL_HOST=smtp.mailgun.org
MAIL_PORT=587
MAIL_ENCRYPTION=tls
MAIL_USERNAME=postmaster@yourdomain.com
MAIL_PASSWORD=your-mailgun-smtp-password
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME=Arcane Ledger
```

If both `SMTP_*` and `MAIL_*` are present, `SMTP_*` values win.

The older Mailgun HTTP API settings are still supported as a fallback:

```text
MAILGUN_API_KEY=key-your-mailgun-api-key
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@yourdomain.com
MAILGUN_FROM_NAME=Arcane Ledger
```

For EU Mailgun API accounts, set `MAILGUN_API_BASE=https://api.eu.mailgun.net/v3`.

Do not commit `.env`; it is ignored by Git. Docker Compose reads `.env` for variable substitution, and `compose.yaml` explicitly passes only the app settings Arcane Ledger needs.

To check whether the app sees the email settings:

```bash
docker compose run --rm arcaneledger python app.py email-status
```

To test the SMTP connection without sending an email:

```bash
docker compose run --rm arcaneledger python app.py email-diagnose
```

For a detailed redacted SMTP trace:

```bash
docker compose run --rm arcaneledger python app.py email-trace
```

For a detailed redacted Mailgun API trace:

```bash
docker compose run --rm arcaneledger python app.py email-mailgun-trace
```

If a provider behaves badly with one SMTP auth mechanism, you can force one:

```text
SMTP_AUTH_METHOD=LOGIN
```

or, when using `MAIL_*` names:

```text
MAIL_AUTH_METHOD=LOGIN
```

Supported values are `LOGIN` and `PLAIN`. Leave it blank for Python's default SMTP negotiation.

To send a smoke-test email after credentials are ready:

```bash
docker compose run --rm arcaneledger python app.py email-test you@example.com
```

## Debug Logs

Arcane Ledger writes server startup messages, requests, network warnings, and unexpected server errors to a rotating log file:

```text
data/logs/arcaneledger.log
```

From Docker, check the configured log path and status:

```bash
docker compose run --rm arcaneledger python app.py log-status
```

To show the last 200 log lines:

```bash
docker compose run --rm arcaneledger python app.py logs
```

Or ask for a specific number of lines:

```bash
docker compose run --rm arcaneledger python app.py logs 500
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
python3 app.py email-trace
python3 app.py email-mailgun-trace
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

By default Arcane Ledger syncs all paper Magic prints from Scryfall with:

```text
SCRYFALL_QUERY=game:paper
```

You can narrow or broaden that in `compose.yaml` using any valid Scryfall search query.

Arcane Ledger also stores daily Scryfall market price snapshots for any card owned by at least one user. These snapshots power richer card and portfolio value charts from the day the feature is enabled forward. Configure the daily job with:

```text
APP_TIMEZONE=America/New_York
PRICE_SNAPSHOT_SCHEDULE_ENABLED=true
PRICE_SNAPSHOT_SCHEDULE_TIME=01:00
PRICE_SNAPSHOT_DAILY_LIMIT=0
PRICE_SNAPSHOT_REQUEST_DELAY=0.12
```

`PRICE_SNAPSHOT_DAILY_LIMIT=0` means every unique owned card is eligible. The scheduler skips cards that already have a snapshot for the current app-local date. You can also run a manual global snapshot from the command line:

```bash
docker compose exec arcaneledger python app.py refresh-price-snapshots 0
```

Main tables:

- `sets`: Scryfall set metadata.
- `cards`: Scryfall card catalog and current prices.
- `collection`: quantity owned, acquired date, paid price, variant, condition, and notes.
- `card_meta`: user metadata such as favorites.
- `decks`: deck names and share identifiers.
- `deck_cards`: card-to-deck metadata; assigning a card to a deck does not duplicate or delete collection data.
- `price_snapshots`: daily Scryfall market price snapshots by card and finish for value history.

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
