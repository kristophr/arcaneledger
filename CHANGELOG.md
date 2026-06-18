# Changelog

## 0.2.0 beta

### Added
- Added a read-only card ledger modal on owned card pages with date, transaction type, quantity, variant, condition, and amount.
- Added a compact ledger icon to the card detail icon row when the user owns the card.
- Added a card-page “Search the Web” panel with external card lookups for TCGplayer, Cardmarket, Cardhoarder, eBay, EDHREC, and MTGGoldfish.
- Added a card-page “Card Actions” panel for refreshing Scryfall metadata, opening Scryfall directly, and putting owned cards up for sale.

### Changed
- Reworked the card detail page to remove the vertical right-side action rail and move tools into the right-side information column.
- Removed card share and email actions from the card detail action area while that workflow is being redesigned.
- Widened the card ledger modal and adjusted its columns so the ledger avoids horizontal scrollbars.
- Shortened the web search panel title to “Search the Web” and matched its two-column layout to nearby card meta panels.
- Bumped frontend asset versions for the card detail page updates.

### Fixed
- Fixed the card detail action listeners so removed share/email buttons no longer require matching DOM elements.
- Fixed the card ledger modal mobile layout so ledger entries stack cleanly on narrow screens.

## 0.1.9 beta

### Added
- Added persistent Admin email templates so saved templates survive logout, reloads, and server restarts.
- Added Admin Home Page Management with draft and published announcements.
- Added date-ranged Home announcements that display only when published and active for the current date.
- Added read-only announcement detail modals on the Home page with safe Markdown rendering.
- Added a collapsible left navigation rail that can switch between icon-only and icon-with-text modes.
- Added a Home page “Today’s Card” spotlight selected daily from cataloged collection cards.

### Changed
- Reworked the Home page layout with announcements and Today’s Card in the main area.
- Grouped Home page metadata into a compact “Overall Server Stats” panel.
- Reduced the visual footprint of the Home page stat tiles.
- Cache-busted frontend assets for the navigation and Home page layout changes.

### Fixed
- Fixed Admin email templates previously saving only as in-browser session drafts.
- Fixed announcement drafts so canceling a new unsaved announcement removes the temporary row.

## 0.1.8 beta

### Added
- Added subject editing to admin email templates.
- Added reusable email template variables for app name, app version, base URL, domain name, sender/support email, user display name, account email, last login date, inactivity days, current date, and current year.
- Added last-login tracking on user accounts so future 30/60/90 day inactivity email triggers can be driven from real login activity.
- Added condition-aware container allocation so physical storage can now track exact card buckets by variant, condition, and container.

### Changed
- Updated container assignment from card pages to show every variant and condition combination across every container.
- Updated container assignment validation to enforce strict on-hand quantities for each exact variant and condition.
- Updated container detail removals to remove the exact stored condition row instead of only the card variant.
- Refreshed app metadata and documentation for the 0.1.8 beta release.

### Fixed
- Fixed deck detail loading when deck card quantities were queried through the wrong SQL alias.
- Fixed stored container assignments that previously blended all conditions for a variant together.
- Fixed purchase-journal deletion safety checks so container allocations are validated against the matching variant and condition.

## 0.1.7 beta

### Added
- Added a full import wizard with CSV header mapping, Scryfall match review, JSON paste/upload support, progress indicators, and final review before saving.
- Added profile pages with display names, profile details, social/contact fields, profile images, public posts, wall comments, friends, and “My Profile” navigation.
- Added card and profile social features including card comments, comment upvotes, blog posts about cards/decks, and reporting tools for public comments and posts.
- Added admin moderation reporting, server details, configurable admin emails, server claim flow, and release notes access from Settings.
- Added card purchase details for store name and purchase location.
- Added a unified Add New Card/Add to Collection/Add Purchase workflow with advanced Scryfall filters and variant/condition purchase rows.
- Added deck JSON export/import tools, full deck export/import, Browse Decks, public deck copying, and card preview modals from deck lists.
- Added container capacity tracking, full-container prevention, per-container allocation controls, fullness bars, stored card count, and container market value.
- Added Final Fantasy, Spider Man, and The Last Airbender theme options.

### Changed
- Rebranded the app and documentation to Arcane Ledger.
- Moved theme selection back into Settings and grouped Settings fields into Account Preferences and Store Contact sections.
- Moved guest users toward Home, Search, Browse Decks, and Store Front while keeping collection tools behind login.
- Improved card detail pages with responsive phone/tablet layouts, market history, user notes, public comments, anonymous metadata, and consistent share/Scryfall/store actions.
- Reworked deck behavior so decks can include any Scryfall card, then compare deck needs against the user’s collection instead of blocking deck building.
- Reworked container assignment so one card variant can be distributed across multiple physical containers.
- Improved collection/search card UX so clicking cards opens internal Arcane Ledger card pages, with Scryfall available through a dedicated icon.
- Improved wishlist and set workflows, including set sharing, missing-card wishlist creation, and list-style wishlist maintenance.

### Fixed
- Fixed stale hard-coded admin access by supporting environment-configured admins and first-user server claiming.
- Fixed version/changelog display plumbing so Settings can show the current release notes.
- Fixed Add Card flows that required duplicate repeated searches for normal/foil/condition variants.
- Fixed container over-allocation by validating capacity in both frontend controls and backend save paths.
- Fixed stored container value calculations so they use allocated quantities instead of total collection quantity.
- Fixed mobile card detail overflow and several icon/UX inconsistencies across card, deck, collection, and container views.

## 0.1.6 alpha

### Added
- Added self-hosted server claim flow so the first account on a fresh install becomes the server admin.
- Added admin email template testing and improved email configuration diagnostics.
- Added shared favorites links and email sharing support for favorites.
- Added exact Scryfall print lookup for add-to-collection flows.

### Changed
- Reworked Add New Card, Add to Collection, and Add Purchase flows to use the same variant/condition purchase table.
- Improved card detail page responsiveness for phone and tablet layouts.
- Updated Settings to show the current app version and open release notes from this changelog.

### Fixed
- Fixed favorites share URLs so they point to the correct user's favorites list.
- Removed quantity display from profile favorite cards.
- Improved mobile card detail layout to avoid horizontal overflow.
