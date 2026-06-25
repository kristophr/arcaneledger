# Changelog

## 0.4.5 beta

### Added
- Added a dedicated Container Allocation Import workflow on the Import page for bulk assigning already-owned cards into physical containers.
- Added CSV and JSON support for container allocation imports using `card_id`, `variant`, `condition`, `quantity`, and `container_id`.
- Added pre-commit validation for container allocation imports, including card existence, owned variant and condition quantity, uncontainered availability, container ownership, and remaining container capacity.
- Added cumulative capacity validation so multiple import rows targeting the same container cannot overfill it during one bulk import.
- Added row-level review controls so users can uncheck valid allocation rows and skip blocked rows before confirming.
- Added a Collector # field to the public catalog Search page for narrowing Scryfall searches to exact collector numbers.
- Added a partial-container state on card detail pages for cards where some copies are stored and some are still unassigned.

### Changed
- Bumped the app version and user agent to `0.4.5 beta`.
- Updated card detail container status icons to distinguish no storage, partial storage, and fully stored cards.
- Updated mixed container-status modals to show stored versus owned counts and provide an Add Unstored Copies action.
- Bumped frontend asset versions for the search, card detail container status, and container allocation import updates.

### Fixed
- Fixed card detail container UX where any stored copy made the card look fully stored, even when other owned copies were still uncontainered.
- Fixed exact-printing searches that needed collector numbers such as `205`, `001`, or `60s`.
- Added backend revalidation on container allocation commit so stale previews cannot write invalid storage assignments.

## 0.4.1 beta

### Added
- Added unified sharing to News article detail modals, including copyable `/news/:id` links and share-by-email support.
- Added direct `/news/:id` routing so shared News links open the correct public article.
- Added an admin-managed Pro Features section under Home Page Management for configuring Normal account limits.
- Added persistent site settings for Normal account limits covering containers, decks, and wishlists.

### Changed
- Bumped the app version and user agent to `0.4.1 beta`.
- Updated Normal account limit enforcement to read from admin-managed settings instead of fixed code values.
- Kept Pro, Contributor, and Admin accounts unlimited while letting admins increase Normal account limits over time.
- Bumped frontend asset versions for the News share and admin Pro Features updates.

### Fixed
- Prevented admins from reducing configured Normal account limits once saved.
- Preserved modal scroll locking when sharing a News article from inside the News detail modal.
- Routed News share-email success messages back to the News page status area.

## 0.4.0 beta

### Added
- Added a new `Contributor` role that sits below Admin and above Pro.
- Added a public News page available to guests and logged-in users.
- Added contributor-authored News articles displayed newest-first in large tiles.
- Added News body search that filters article text without broadening into unrelated metadata.
- Added a top-bar contributor studio `+` action for Admin and Contributor accounts.
- Added a large three-tab contributor studio with New Post, Drafts, and Published views.
- Added Markdown controls for contributor News posts.
- Added draft saving for incomplete News articles.
- Added immediate publishing for News articles.
- Added scheduled publishing so News posts remain hidden until their scheduled publish time has passed.
- Added contributor article management actions for loading drafts back into the editor, unpublishing published posts back to drafts, and deleting posts.
- Added database support for News post status, published timestamps, scheduled timestamps, and per-author article ownership.

### Changed
- Bumped the app version and user agent to `0.4.0 beta`.
- Treated Contributor as a Pro-level role for limits and public display styling while keeping Admin-only functionality restricted to Admins.
- Updated Admin user management so Admins can assign Contributor accounts.
- Updated public News article rendering to support the same lightweight Markdown syntax used elsewhere in Arcane Ledger.
- Bumped frontend asset versions for the News page and contributor studio updates.

### Fixed
- Fixed News authoring UX so contributors no longer need to publish immediately just to start writing.
- Fixed scheduled News visibility so scheduled posts do not appear in the public News feed until due.
- Fixed role migration safeguards so Contributor roles are preserved instead of normalized back to Normal.

## 0.3.0 beta

### Added
- Added collection quick filters for owned sets, using full set names in a multi-select dropdown.
- Added collection container-status filtering so users can show only cards assigned to containers or only cards still needing storage.
- Added a unified share modal for cards, decks, sets, containers, wishlists, and favorites with both copy-link and email-share controls in one place.
- Added the unified share action back to the card detail view inside the Card Actions panel.

### Changed
- Bumped the app version and user agent to `0.3.0 beta`.
- Replaced separate share URL and email icons with one cleaner share icon across shareable screens.
- Reworked the share UI so logged-out users can still copy public links while email sharing remains available to logged-in users.
- Tightened the Add to Container modal layout and adjusted container allocation rows for better readability.
- Increased site wallpaper visibility slightly for richer background treatment.
- Bumped frontend asset versions for the collection filter, container modal, wallpaper, and unified sharing updates.

### Fixed
- Fixed card detail sharing after the share cleanup by restoring a visible Share Card action that opens the unified modal.
- Fixed stale share-email modal markup and handlers that were left behind after consolidating share flows.
- Fixed collection set filtering gaps where users could search card names but could not quickly filter by set names like Bloomburrow or Final Fantasy.

## 0.2.9 beta

### Added
- Added set drill-in financial totals for Total Paid, Market Value, and Delta so users can review spend versus current value inside each owned set.
- Added a wider card ledger modal with full transaction dates, purchase price, store name, and store location fields.
- Added variant-and-condition-aware container allocation controls for assigning cards into physical storage.
- Added bulk container allocation rows so selected collection cards can be split across different containers by variant and condition.

### Changed
- Bumped the app version and user agent to `0.2.9 beta`.
- Reworked the single-card Assign Containers modal to use a container dropdown plus variant/condition quantity columns instead of listing every container as a separate row.
- Reworked bulk Add to Container behavior so normal, foil, and other variant/condition quantities can be delegated to different containers in one save.
- Widened the assign-to-container modal and improved table spacing for clearer storage allocation.
- Bumped frontend asset versions for the set financial summary and container assignment updates.

### Fixed
- Fixed mass container assignment that previously flattened selected cards into one container workflow and made mixed normal/foil storage awkward.
- Fixed container allocation validation so the UI checks eligible owned quantities and container capacity before saving.

## 0.2.8 beta

### Added
- Added per-user default purchase price and default sell price preferences in Settings.
- Added default purchase/sell prices to the user profile payload so defaults persist across devices.
- Added CSV attachments to emailed collection reports for both SMTP and Mailgun delivery.
- Added a single batch-level Date Acquired field to the Add Card modal for multi-variant/multi-condition purchases.
- Added an Add Card modal option to update the user's default purchase price after a successful save.

### Changed
- Bumped the app version and user agent to `0.2.8 beta`.
- Updated Add Card purchase rows to remove repeated date fields and use one shared acquisition date.
- Updated Add Card and Add Purchase flows to use the user's default purchase price.
- Updated Mark for Sale flows to use the user's default sell price when configured, otherwise falling back to market price.
- Increased site wallpaper visibility so uploaded backgrounds appear richer while remaining subtle.
- Bumped frontend asset versions for the Settings, Add Card modal, and wallpaper updates.

### Fixed
- Fixed emailed reports so the recipient receives an attached CSV instead of only an HTML report preview.

## 0.2.7 beta

### Added
- Added a logged-in Reports page for building collection reports with selectable fields and spreadsheet-style previews.
- Added report filters for search text, set, variant, condition, quantity range, favorites-only, and for-sale-only views.
- Added CSV export, Excel-readable XLS export, and email delivery for collection reports.
- Added bulk removal controls inside wishlist detail views so users can select and remove multiple wishlist cards at once.
- Added consolidated variant inventory treatment on card detail pages so normal, foil, and etched copies are easier to review from one card view.
- Added a clearer Admin Wallpaper Management panel near the top of the Admin page.

### Changed
- Bumped the app version and user agent to `0.2.7 beta`.
- Updated report Card Name output to prefer printed/flavor names, while exposing the underlying Scryfall/oracle name as a separate Rules Name field.
- Updated short set-code report filters like `fin` to match the exact set code case-insensitively instead of broadly matching every set name containing similar text.
- Updated Admin wallpaper copy and placement so upload/delete controls are easier to find.
- Bumped frontend asset versions for Reports and report field label fixes.

### Fixed
- Fixed Reports set filtering that returned all Final Fantasy-related sets when a user entered a specific short code like `fin`.
- Fixed Reports card naming for reskinned cards such as `Stay with Me`, which previously appeared as the base rules card `Rhystic Study`.
- Fixed card detail movement history so all variant ledger entries can be viewed together while still preserving selected-variant context.

## 0.2.6 beta

### Added
- Added Admin wallpaper management so site admins can upload and delete background images from the Admin area.
- Added a daily wallpaper rotation that selects one uploaded image each day and applies it as a faint site-wide background.
- Added local wallpaper storage under the app data directory with guarded media serving for uploaded wallpaper files.
- Added detailed Stripe subscription tracking for purchased plan, Stripe price, subscription status, current period end, scheduled cancellation, canceled date, and ended date.
- Added a Billing Details grid in Settings showing plan, status, renewal/end date, canceled date, and ended date when subscription history exists.
- Added transactional subscription receipt emails after successful Stripe checkout, sent to the user's main account email address.
- Added receipt duplicate protection so Stripe webhook retries do not send duplicate membership receipt emails.

### Changed
- Updated the Admin page with a dedicated Wallpapers panel and thumbnail management controls.
- Updated the public app configuration payload to include the currently selected daily wallpaper.
- Updated billing copy to distinguish active renewals from subscriptions that are canceled but still active until the end of the billing period.
- Updated Pro access checks so canceled subscriptions stop granting Pro after the current paid period has ended.
- Preserved the last known Stripe price and plan when subscription events omit item pricing.
- Bumped frontend asset versions for the billing details update.

### Fixed
- Fixed billing visibility so monthly and yearly Pro subscriptions display as `Pro Monthly` or `Pro Yearly` instead of a generic Pro label.
- Fixed subscription status handling so ended/canceled memberships clearly show when access ended and prompt the user to restore Pro benefits.

## 0.2.5 beta

### Added
- Added Stripe Billing configuration and checkout/portal support for Pro subscriptions.
- Added Pro account support, including active/trialing Stripe subscriptions granting Pro features.
- Added Normal account creation limits for decks, containers, and wishlists, with Admin and Pro accounts remaining unlimited.
- Added a Billing section in Settings with monthly/yearly upgrade buttons, billing portal access, and Whispering Yak billing disclosure.
- Added a Membership Benefits modal comparing Normal and Pro limits.
- Added optional purchase notes to the unified Add Card/Add Purchase workflow and surfaced purchase notes in card ledger history.
- Added compact collection-card imagery to the Search page header using cards already cataloged in Arcane Ledger.
- Added Pro visual identity treatment: Pro/Admin display names now render in rainbow text with a compact PRO badge across profiles, comments, decks, favorites, stores, and account chrome.
- Added Stripe environment variables to the example configuration.

### Changed
- Renamed the former Paid role to Pro throughout account role handling.
- Improved the Search page header to use less vertical space while keeping a more welcoming catalog entry point.
- Updated public/profile/deck/store identity payloads so Pro status can render consistently across social and marketplace views.
- Updated Settings with a direct support/request link to the Arcane Ledger help site.
- Bumped frontend asset versions for the billing, search, notes, and Pro identity updates.

### Fixed
- Fixed role migration so legacy `paid` users are normalized to `pro`.
- Fixed role-based feature checks to use effective account role, including subscription-backed Pro access.
- Fixed public profile, comment, deck, favorite, and store seller displays that previously lacked enough role metadata to show Pro status.
- Fixed purchase journal display so optional purchase notes are visible on card history rows.
- Fixed card detail Total Value so mixed variants sum each owned variant quantity against that variant's current market value.

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
- Fixed Admin announcement modal close-button placement.
- Fixed announcement date-range display so Home and Admin announcement lists show clear local dates like `6/18/26 - 6/22/26`.
- Verified announcement subject, body, beginning date, and display-until date persist to the database and active Home announcements filter inclusively through the end date.

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
