# Changelog

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
