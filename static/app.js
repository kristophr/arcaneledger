const state = {
  cards: [],
  favoriteCards: [],
  favoriteDecks: [],
  favoriteStores: [],
  missingCards: [],
  saleCards: [],
  storeFrontCards: [],
  browseDecks: [],
  wishlistCards: [],
  wishlists: [],
  notifications: [],
  unreadNotificationCount: 0,
  adminUsers: [],
  adminLogs: null,
  adminServer: null,
  adminReports: [],
  adminEmailTemplates: [],
  adminAnnouncements: [],
  adminWallpapers: [],
  homeAnnouncements: [],
  editingAdminEmailTemplateId: null,
  editingAdminAnnouncementId: null,
  appConfig: {},
  userProfile: null,
  activeBlogCard: null,
  activeBlogDeck: null,
  activeBlogListCard: null,
  activeReportTarget: null,
  ownedSetCards: [],
  ownedSets: [],
  catalogSearchAllResults: [],
  catalogSearchResults: [],
  catalogHeroCards: [],
  catalogHeroLoaded: false,
  dashboard: null,
  searchTimer: null,
  favoriteSearchTimer: null,
  missingSearchTimer: null,
  saleSearchTimer: null,
  storeFrontSearchTimer: null,
  wishlistSearchTimer: null,
  catalogSearchTimer: null,
  editingCard: null,
  addResults: [],
  selectedAddCard: null,
  sharedCard: null,
  activeCardDetail: null,
  activeSet: null,
  setCards: [],
  activeOwnedSet: null,
  decks: [],
  activeDeck: null,
  deckEditorDirty: false,
  deckEditorSnapshot: "",
  activeWishlist: null,
  pendingWishlistCard: null,
  pendingWishlistOptions: null,
  emailingWishlist: null,
  emailingEntity: null,
  containers: [],
  activeContainer: null,
  editingContainer: null,
  activeSaleCard: null,
  assignContainerCard: null,
  importRows: [],
  importIssues: [],
  importWizard: {
    step: "source",
    format: "",
    text: "",
    headers: [],
    mapping: {},
    fields: [],
    jsonPreview: null,
    rows: [],
    issues: [],
    decks: [],
    wishlists: [],
    busy: false,
    progress: { visible: false, label: "", current: 0, total: 0 },
  },
  pendingDeckImport: null,
  selectedCards: new Map(),
  selectedSetMissingCards: new Map(),
  user: null,
  collectionView: localStorage.getItem("arcaneledger.collectionView") || "tiles",
  favoritesView: localStorage.getItem("arcaneledger.favoritesView") || "tiles",
  favoritesFilter: localStorage.getItem("arcaneledger.favoritesFilter") || "all",
  settings: null,
  navCollapsed: localStorage.getItem("arcaneledger.navCollapsed") === "1",
};

const settingsKey = "arcaneledger.settings";

const dollars = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

const compactDollars = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});

const integer = new Intl.NumberFormat("en-US");
function formatPercent(value) {
  const percent = Number(value || 0);
  return `${Number.isFinite(percent) ? percent.toFixed(1) : "0.0"}%`;
}
const cardConditions = ["Near Mint", "Lightly Played", "Moderately Played", "Heavily Played", "Damaged"];
const disallowedNameWords = new Set([
  "fuck", "shit", "bitch", "cunt", "asshole", "whore", "slut",
  "nigger", "nigga", "fag", "faggot", "retard", "kike", "spic",
  "chink", "gook", "tranny", "nazi", "hitler",
]);
const pageRoutes = {
  home: "/",
  dashboard: "/dashboard",
  search: "/search",
  favorites: "/favorites",
  collection: "/collection",
  sets: "/sets",
  decks: "/decks",
  "browse-decks": "/browse-decks",
  containers: "/containers",
  "missing-list": "/missing-list",
  "for-sale": "/for-sale",
  "store-front": "/store-front",
  wishlist: "/wishlist",
  notifications: "/notifications",
  admin: "/admin",
  settings: "/settings",
  import: "/import",
};
const routePages = Object.fromEntries(Object.entries(pageRoutes).map(([page, path]) => [path, page]));

const els = {
  currentValue: document.querySelector("#currentValue"),
  paidTotal: document.querySelector("#paidTotal"),
  gainLoss: document.querySelector("#gainLoss"),
  ownedCards: document.querySelector("#ownedCards"),
  favoriteCount: document.querySelector("#favoriteCount"),
  wishlistCount: document.querySelector("#wishlistCount"),
  saleCount: document.querySelector("#saleCount"),
  saleAskingTotal: document.querySelector("#saleAskingTotal"),
  deckCount: document.querySelector("#deckCount"),
  cardsInDecks: document.querySelector("#cardsInDecks"),
  containerCount: document.querySelector("#containerCount"),
  uncontainedCards: document.querySelector("#uncontainedCards"),
  homeTotalValue: document.querySelector("#homeTotalValue"),
  homeUserCount: document.querySelector("#homeUserCount"),
  homeCatalogedCards: document.querySelector("#homeCatalogedCards"),
  homeUniqueCards: document.querySelector("#homeUniqueCards"),
  homeDeckCount: document.querySelector("#homeDeckCount"),
  homeContainerCount: document.querySelector("#homeContainerCount"),
  homeWishlistCount: document.querySelector("#homeWishlistCount"),
  homeSaleQuantity: document.querySelector("#homeSaleQuantity"),
  homeSaleAskingTotal: document.querySelector("#homeSaleAskingTotal"),
  homeTodaysCardPanel: document.querySelector("#homeTodaysCardPanel"),
  homeTodaysCardLink: document.querySelector("#homeTodaysCardLink"),
  homeTodaysCardImage: document.querySelector("#homeTodaysCardImage"),
  homeTodaysCardName: document.querySelector("#homeTodaysCardName"),
  homeTodaysCardMeta: document.querySelector("#homeTodaysCardMeta"),
  homeTodaysCardText: document.querySelector("#homeTodaysCardText"),
  homeAnnouncementsPanel: document.querySelector("#homeAnnouncementsPanel"),
  homeAnnouncementsList: document.querySelector("#homeAnnouncementsList"),
  homeAnnouncementDetailOverlay: document.querySelector("#homeAnnouncementDetailOverlay"),
  homeAnnouncementDetailTitle: document.querySelector("#homeAnnouncementDetailTitle"),
  homeAnnouncementDetailMeta: document.querySelector("#homeAnnouncementDetailMeta"),
  homeAnnouncementDetailBody: document.querySelector("#homeAnnouncementDetailBody"),
  closeHomeAnnouncementDetailButton: document.querySelector("#closeHomeAnnouncementDetailButton"),
  historyCount: document.querySelector("#historyCount"),
  historyChart: document.querySelector("#historyChart"),
  refreshPriceSnapshotsButton: document.querySelector("#refreshPriceSnapshotsButton"),
  recentCount: document.querySelector("#recentCount"),
  recentCards: document.querySelector("#recentCards"),
  topCount: document.querySelector("#topCount"),
  topCards: document.querySelector("#topCards"),
  setCompletionCount: document.querySelector("#setCompletionCount"),
  setCompletion: document.querySelector("#setCompletion"),
  cardsGrid: document.querySelector("#cardsGrid"),
  favoritesGrid: document.querySelector("#favoritesGrid"),
  missingGrid: document.querySelector("#missingGrid"),
  saleGrid: document.querySelector("#saleGrid"),
  storeFrontGrid: document.querySelector("#storeFrontGrid"),
  browseDecksGrid: document.querySelector("#browseDecksGrid"),
  wishlistGrid: document.querySelector("#wishlistGrid"),
  wishlistsGrid: document.querySelector("#wishlistsGrid"),
  catalogSearchGrid: document.querySelector("#catalogSearchGrid"),
  status: document.querySelector("#status"),
  favoritesStatus: document.querySelector("#favoritesStatus"),
  missingStatus: document.querySelector("#missingStatus"),
  saleStatus: document.querySelector("#saleStatus"),
  storeFrontStatus: document.querySelector("#storeFrontStatus"),
  browseDecksStatus: document.querySelector("#browseDecksStatus"),
  saleModalStatus: document.querySelector("#saleModalStatus"),
  wishlistStatus: document.querySelector("#wishlistStatus"),
  notificationsStatus: document.querySelector("#notificationsStatus"),
  adminStatus: document.querySelector("#adminStatus"),
  adminEmailStatus: document.querySelector("#adminEmailStatus"),
  catalogSearchStatus: document.querySelector("#catalogSearchStatus"),
  notificationsList: document.querySelector("#notificationsList"),
  notificationsNavDot: document.querySelector("#notificationsNavDot"),
  navCollapseButton: document.querySelector("#navCollapseButton"),
  adminUsersList: document.querySelector("#adminUsersList"),
  adminUserCount: document.querySelector("#adminUserCount"),
  adminReportsList: document.querySelector("#adminReportsList"),
  adminReportCount: document.querySelector("#adminReportCount"),
  adminServerDetails: document.querySelector("#adminServerDetails"),
  adminServerVersion: document.querySelector("#adminServerVersion"),
  adminLogs: document.querySelector("#adminLogs"),
  adminLogMeta: document.querySelector("#adminLogMeta"),
  adminLogLineCount: document.querySelector("#adminLogLineCount"),
  adminEmailTemplateCount: document.querySelector("#adminEmailTemplateCount"),
  adminEmailTemplatesList: document.querySelector("#adminEmailTemplatesList"),
  addAdminEmailTemplateButton: document.querySelector("#addAdminEmailTemplateButton"),
  adminEmailTemplateOverlay: document.querySelector("#adminEmailTemplateOverlay"),
  adminEmailTemplateModalTitle: document.querySelector("#adminEmailTemplateModalTitle"),
  adminEmailTemplateTo: document.querySelector("#adminEmailTemplateTo"),
  adminEmailTemplateFrom: document.querySelector("#adminEmailTemplateFrom"),
  adminEmailTemplateSubject: document.querySelector("#adminEmailTemplateSubject"),
  adminEmailTemplateBody: document.querySelector("#adminEmailTemplateBody"),
  closeAdminEmailTemplateButton: document.querySelector("#closeAdminEmailTemplateButton"),
  cancelAdminEmailTemplateButton: document.querySelector("#cancelAdminEmailTemplateButton"),
  saveAdminEmailTemplateButton: document.querySelector("#saveAdminEmailTemplateButton"),
  adminAnnouncementCount: document.querySelector("#adminAnnouncementCount"),
  adminAnnouncementsList: document.querySelector("#adminAnnouncementsList"),
  adminAnnouncementStatus: document.querySelector("#adminAnnouncementStatus"),
  addAdminAnnouncementButton: document.querySelector("#addAdminAnnouncementButton"),
  adminAnnouncementOverlay: document.querySelector("#adminAnnouncementOverlay"),
  adminAnnouncementModalTitle: document.querySelector("#adminAnnouncementModalTitle"),
  adminAnnouncementSubject: document.querySelector("#adminAnnouncementSubject"),
  adminAnnouncementStartsOn: document.querySelector("#adminAnnouncementStartsOn"),
  adminAnnouncementEndsOn: document.querySelector("#adminAnnouncementEndsOn"),
  adminAnnouncementBody: document.querySelector("#adminAnnouncementBody"),
  closeAdminAnnouncementButton: document.querySelector("#closeAdminAnnouncementButton"),
  cancelAdminAnnouncementButton: document.querySelector("#cancelAdminAnnouncementButton"),
  draftAdminAnnouncementButton: document.querySelector("#draftAdminAnnouncementButton"),
  publishAdminAnnouncementButton: document.querySelector("#publishAdminAnnouncementButton"),
  adminWallpaperCount: document.querySelector("#adminWallpaperCount"),
  adminWallpaperInput: document.querySelector("#adminWallpaperInput"),
  uploadAdminWallpaperButton: document.querySelector("#uploadAdminWallpaperButton"),
  adminWallpaperStatus: document.querySelector("#adminWallpaperStatus"),
  adminWallpapersList: document.querySelector("#adminWallpapersList"),
  refreshAdminButton: document.querySelector("#refreshAdminButton"),
  refreshAdminLogsButton: document.querySelector("#refreshAdminLogsButton"),
  reportOverlay: document.querySelector("#reportOverlay"),
  reportForm: document.querySelector("#reportForm"),
  reportTargetLabel: document.querySelector("#reportTargetLabel"),
  reportStatus: document.querySelector("#reportStatus"),
  closeReportButton: document.querySelector("#closeReportButton"),
  cancelReportButton: document.querySelector("#cancelReportButton"),
  searchInput: document.querySelector("#searchInput"),
  favoriteSearchInput: document.querySelector("#favoriteSearchInput"),
  missingSearchInput: document.querySelector("#missingSearchInput"),
  saleSearchInput: document.querySelector("#saleSearchInput"),
  storeFrontSearchInput: document.querySelector("#storeFrontSearchInput"),
  wishlistSearchInput: document.querySelector("#wishlistSearchInput"),
  catalogSearchForm: document.querySelector("#catalogSearchForm"),
  catalogHeroCards: document.querySelector("#catalogHeroCards"),
  catalogSearchInput: document.querySelector("#catalogSearchInput"),
  catalogSearchButton: document.querySelector("#catalogSearchButton"),
  catalogOracleInput: document.querySelector("#catalogOracleInput"),
  catalogSetInput: document.querySelector("#catalogSetInput"),
  catalogColorSelect: document.querySelector("#catalogColorSelect"),
  catalogTypeSelect: document.querySelector("#catalogTypeSelect"),
  catalogRaritySelect: document.querySelector("#catalogRaritySelect"),
  catalogFormatSelect: document.querySelector("#catalogFormatSelect"),
  catalogHideOwnedFilter: document.querySelector("#catalogHideOwnedFilter"),
  ownedFilter: document.querySelector("#ownedFilter"),
  sortSelect: document.querySelector("#sortSelect"),
  favoriteSortSelect: document.querySelector("#favoriteSortSelect"),
  missingSortSelect: document.querySelector("#missingSortSelect"),
  saleSortSelect: document.querySelector("#saleSortSelect"),
  storeFrontSortSelect: document.querySelector("#storeFrontSortSelect"),
  wishlistSortSelect: document.querySelector("#wishlistSortSelect"),
  catalogSortSelect: document.querySelector("#catalogSortSelect"),
  tileViewButton: document.querySelector("#tileViewButton"),
  listViewButton: document.querySelector("#listViewButton"),
  favoriteTileViewButton: document.querySelector("#favoriteTileViewButton"),
  favoriteListViewButton: document.querySelector("#favoriteListViewButton"),
  favoriteFilterButtons: document.querySelectorAll("[data-favorites-filter]"),
  shareFavoritesButton: document.querySelector("#shareFavoritesButton"),
  emailFavoritesButton: document.querySelector("#emailFavoritesButton"),
  collectionBulkBar: document.querySelector("#collectionBulkBar"),
  favoritesBulkBar: document.querySelector("#favoritesBulkBar"),
  selectedCardsCount: document.querySelector("#selectedCardsCount"),
  favoriteSelectedCardsCount: document.querySelector("#favoriteSelectedCardsCount"),
  addToDeckButton: document.querySelector("#addToDeckButton"),
  addToContainerButton: document.querySelector("#addToContainerButton"),
  markForSaleButton: document.querySelector("#markForSaleButton"),
  favoriteAddToDeckButton: document.querySelector("#favoriteAddToDeckButton"),
  favoriteAddToContainerButton: document.querySelector("#favoriteAddToContainerButton"),
  addCardButton: document.querySelector("#addCardButton"),
  accountButton: document.querySelector("#accountButton"),
  myProfileButton: document.querySelector("#myProfileButton"),
  logoutButton: document.querySelector("#logoutButton"),
  importStatus: document.querySelector("#importStatus"),
  jsonImportFile: document.querySelector("#jsonImportFile"),
  csvImportFile: document.querySelector("#csvImportFile"),
  previewJsonImportButton: document.querySelector("#previewJsonImportButton"),
  previewCsvImportButton: document.querySelector("#previewCsvImportButton"),
  importWizardFile: document.querySelector("#importWizardFile"),
  importWizardJsonText: document.querySelector("#importWizardJsonText"),
  importWizardBackButton: document.querySelector("#importWizardBackButton"),
  importWizardResetButton: document.querySelector("#importWizardResetButton"),
  importWizardNextButton: document.querySelector("#importWizardNextButton"),
  importWizardSaveButton: document.querySelector("#importWizardSaveButton"),
  importMappingTable: document.querySelector("#importMappingTable"),
  importMapTitle: document.querySelector("#importMapTitle"),
  importMapSubtitle: document.querySelector("#importMapSubtitle"),
  importJsonPreview: document.querySelector("#importJsonPreview"),
  importWizardIssues: document.querySelector("#importWizardIssues"),
  importWizardRows: document.querySelector("#importWizardRows"),
  importReviewStepTitle: document.querySelector("#importReviewStepTitle"),
  importReviewStepSubtitle: document.querySelector("#importReviewStepSubtitle"),
  importRecapRows: document.querySelector("#importRecapRows"),
  importRecapSubtitle: document.querySelector("#importRecapSubtitle"),
  importWizardProgress: document.querySelector("#importWizardProgress"),
  importWizardProgressLabel: document.querySelector("#importWizardProgressLabel"),
  importWizardProgressCount: document.querySelector("#importWizardProgressCount"),
  importWizardProgressBar: document.querySelector("#importWizardProgressBar"),
  importReviewOverlay: document.querySelector("#importReviewOverlay"),
  importReviewTitle: document.querySelector("#importReviewTitle"),
  importReviewCount: document.querySelector("#importReviewCount"),
  importIssueCount: document.querySelector("#importIssueCount"),
  importIssues: document.querySelector("#importIssues"),
  importReviewRows: document.querySelector("#importReviewRows"),
  closeImportReviewButton: document.querySelector("#closeImportReviewButton"),
  cancelImportReviewButton: document.querySelector("#cancelImportReviewButton"),
  commitImportButton: document.querySelector("#commitImportButton"),
  template: document.querySelector("#cardTemplate"),
  listTemplate: document.querySelector("#cardListTemplate"),
  editOverlay: document.querySelector("#editOverlay"),
  editForm: document.querySelector("#editForm"),
  editTitle: document.querySelector("#editTitle"),
  closeEditButton: document.querySelector("#closeEditButton"),
  cancelEditButton: document.querySelector("#cancelEditButton"),
  addCardOverlay: document.querySelector("#addCardOverlay"),
  addSearchForm: document.querySelector("#addSearchForm"),
  addSearchInput: document.querySelector("#addSearchInput"),
  addSearchButton: document.querySelector("#addSearchButton"),
  addAdvancedToggle: document.querySelector("#addAdvancedToggle"),
  addAdvancedFilters: document.querySelector("#addAdvancedFilters"),
  addSetCodeInput: document.querySelector("#addSetCodeInput"),
  addColorInput: document.querySelector("#addColorInput"),
  addTypeInput: document.querySelector("#addTypeInput"),
  addSearchStatus: document.querySelector("#addSearchStatus"),
  addSearchResults: document.querySelector("#addSearchResults"),
  addCardForm: document.querySelector("#addCardForm"),
  addPurchaseMatrix: document.querySelector("#addPurchaseMatrix"),
  addPurchaseRows: document.querySelector("#addPurchaseRows"),
  selectedAddCard: document.querySelector("#selectedAddCard"),
  closeAddCardButton: document.querySelector("#closeAddCardButton"),
  cancelAddCardButton: document.querySelector("#cancelAddCardButton"),
  confirmAddNewCardButton: document.querySelector("#confirmAddNewCardButton"),
  confirmAddCardButton: document.querySelector("#confirmAddCardButton"),
  settingsOverlay: document.querySelector("#settingsOverlay"),
  settingsForm: document.querySelector("#settingsForm"),
  closeSettingsButton: document.querySelector("#closeSettingsButton"),
  cancelSettingsButton: document.querySelector("#cancelSettingsButton"),
  settingsPageForm: document.querySelector("#settingsPageForm"),
  settingsAccountEmail: document.querySelector("#settingsAccountEmail"),
  settingsAppVersion: document.querySelector("#settingsAppVersion"),
  openChangelogButton: document.querySelector("#openChangelogButton"),
  changelogOverlay: document.querySelector("#changelogOverlay"),
  changelogText: document.querySelector("#changelogText"),
  closeChangelogButton: document.querySelector("#closeChangelogButton"),
  dismissChangelogButton: document.querySelector("#dismissChangelogButton"),
  membershipBenefitsButton: document.querySelector("#membershipBenefitsButton"),
  membershipBenefitsOverlay: document.querySelector("#membershipBenefitsOverlay"),
  closeMembershipBenefitsButton: document.querySelector("#closeMembershipBenefitsButton"),
  dismissMembershipBenefitsButton: document.querySelector("#dismissMembershipBenefitsButton"),
  settingsPageStatus: document.querySelector("#settingsPageStatus"),
  billingPlanStatus: document.querySelector("#billingPlanStatus"),
  billingHelpText: document.querySelector("#billingHelpText"),
  billingMetaList: document.querySelector("#billingMetaList"),
  billingMonthlyButton: document.querySelector("#billingMonthlyButton"),
  billingYearlyButton: document.querySelector("#billingYearlyButton"),
  billingPortalButton: document.querySelector("#billingPortalButton"),
  notificationDetailOverlay: document.querySelector("#notificationDetailOverlay"),
  notificationSubjectInput: document.querySelector("#notificationSubjectInput"),
  notificationBodyInput: document.querySelector("#notificationBodyInput"),
  notificationStoreLink: document.querySelector("#notificationStoreLink"),
  closeNotificationDetailButton: document.querySelector("#closeNotificationDetailButton"),
  closeNotificationDetailFooterButton: document.querySelector("#closeNotificationDetailFooterButton"),
  clearDatabaseButton: document.querySelector("#clearDatabaseButton"),
  deleteProfileButton: document.querySelector("#deleteProfileButton"),
  authOverlay: document.querySelector("#authOverlay"),
  authForm: document.querySelector("#authForm"),
  authTitle: document.querySelector("#authTitle"),
  authHint: document.querySelector("#authHint"),
  authStatus: document.querySelector("#authStatus"),
  authNameField: document.querySelector("#authNameField"),
  authPasswordField: document.querySelector("#authPasswordField"),
  togglePasswordVisibilityButton: document.querySelector("#togglePasswordVisibilityButton"),
  forgotPasswordButton: document.querySelector("#forgotPasswordButton"),
  closeAuthButton: document.querySelector("#closeAuthButton"),
  toggleAuthModeButton: document.querySelector("#toggleAuthModeButton"),
  submitAuthButton: document.querySelector("#submitAuthButton"),
  addDeckButton: document.querySelector("#addDeckButton"),
  importDeckButton: document.querySelector("#importDeckButton"),
  exportDecksButton: document.querySelector("#exportDecksButton"),
  addDeckOverlay: document.querySelector("#addDeckOverlay"),
  addDeckForm: document.querySelector("#addDeckForm"),
  closeAddDeckButton: document.querySelector("#closeAddDeckButton"),
  cancelAddDeckButton: document.querySelector("#cancelAddDeckButton"),
  addWishlistButton: document.querySelector("#addWishlistButton"),
  addWishlistOverlay: document.querySelector("#addWishlistOverlay"),
  addWishlistForm: document.querySelector("#addWishlistForm"),
  closeAddWishlistButton: document.querySelector("#closeAddWishlistButton"),
  cancelAddWishlistButton: document.querySelector("#cancelAddWishlistButton"),
  assignWishlistOverlay: document.querySelector("#assignWishlistOverlay"),
  assignWishlistForm: document.querySelector("#assignWishlistForm"),
  assignWishlistPreview: document.querySelector("#assignWishlistPreview"),
  closeAssignWishlistButton: document.querySelector("#closeAssignWishlistButton"),
  cancelAssignWishlistButton: document.querySelector("#cancelAssignWishlistButton"),
  wishlistDetailOverlay: document.querySelector("#wishlistDetailOverlay"),
  wishlistDetailTitle: document.querySelector("#wishlistDetailTitle"),
  closeWishlistDetailButton: document.querySelector("#closeWishlistDetailButton"),
  closeWishlistDetailFooterButton: document.querySelector("#closeWishlistDetailFooterButton"),
  deleteWishlistButton: document.querySelector("#deleteWishlistButton"),
  emailWishlistOverlay: document.querySelector("#emailWishlistOverlay"),
  emailWishlistForm: document.querySelector("#emailWishlistForm"),
  emailWishlistTitle: document.querySelector("#emailWishlistTitle"),
  emailWishlistStatus: document.querySelector("#emailWishlistStatus"),
  closeEmailWishlistButton: document.querySelector("#closeEmailWishlistButton"),
  cancelEmailWishlistButton: document.querySelector("#cancelEmailWishlistButton"),
  decksGrid: document.querySelector("#decksGrid"),
  decksStatus: document.querySelector("#decksStatus"),
  setsGrid: document.querySelector("#setsGrid"),
  setsDetailShell: document.querySelector("#setsDetailShell"),
  setsOverviewShell: document.querySelector("#setsOverviewShell"),
  setsStatus: document.querySelector("#setsStatus"),
  assignDeckOverlay: document.querySelector("#assignDeckOverlay"),
  assignDeckForm: document.querySelector("#assignDeckForm"),
  assignDeckCards: document.querySelector("#assignDeckCards"),
  assignCreateDeckButton: document.querySelector("#assignCreateDeckButton"),
  closeAssignDeckButton: document.querySelector("#closeAssignDeckButton"),
  cancelAssignDeckButton: document.querySelector("#cancelAssignDeckButton"),
  deckDetailOverlay: document.querySelector("#deckDetailOverlay"),
  deckDetailTitle: document.querySelector("#deckDetailTitle"),
  deckDetailCards: document.querySelector("#deckDetailCards"),
  shareDeckButton: document.querySelector("#shareDeckButton"),
  emailDeckButton: document.querySelector("#emailDeckButton"),
  deleteDeckButton: document.querySelector("#deleteDeckButton"),
  closeDeckDetailButton: document.querySelector("#closeDeckDetailButton"),
  addDeckCardButton: document.querySelector("#addDeckCardButton"),
  deckCardPreviewOverlay: document.querySelector("#deckCardPreviewOverlay"),
  deckCardPreviewTitle: document.querySelector("#deckCardPreviewTitle"),
  deckCardPreviewShell: document.querySelector("#deckCardPreviewShell"),
  closeDeckCardPreviewButton: document.querySelector("#closeDeckCardPreviewButton"),
  scryfallJsonOverlay: document.querySelector("#scryfallJsonOverlay"),
  scryfallJsonTitle: document.querySelector("#scryfallJsonTitle"),
  scryfallJsonText: document.querySelector("#scryfallJsonText"),
  scryfallJsonStatus: document.querySelector("#scryfallJsonStatus"),
  closeScryfallJsonButton: document.querySelector("#closeScryfallJsonButton"),
  dismissScryfallJsonButton: document.querySelector("#dismissScryfallJsonButton"),
  deckCardSearchOverlay: document.querySelector("#deckCardSearchOverlay"),
  deckCardSearchTitle: document.querySelector("#deckCardSearchTitle"),
  deckCardSearchForm: document.querySelector("#deckCardSearchForm"),
  deckCardSearchInput: document.querySelector("#deckCardSearchInput"),
  deckCardSearchStatus: document.querySelector("#deckCardSearchStatus"),
  deckCardSearchResults: document.querySelector("#deckCardSearchResults"),
  closeDeckCardSearchButton: document.querySelector("#closeDeckCardSearchButton"),
  deckEditorShell: document.querySelector("#deckEditorShell"),
  deckShareShell: document.querySelector("#deckShareShell"),
  cardDecksOverlay: document.querySelector("#cardDecksOverlay"),
  cardDecksTitle: document.querySelector("#cardDecksTitle"),
  cardDecksList: document.querySelector("#cardDecksList"),
  closeCardDecksButton: document.querySelector("#closeCardDecksButton"),
  addContainerButton: document.querySelector("#addContainerButton"),
  addContainerOverlay: document.querySelector("#addContainerOverlay"),
  addContainerForm: document.querySelector("#addContainerForm"),
  addContainerEyebrow: document.querySelector("#addContainerEyebrow"),
  addContainerTitle: document.querySelector("#addContainerTitle"),
  saveContainerButton: document.querySelector("#saveContainerButton"),
  closeAddContainerButton: document.querySelector("#closeAddContainerButton"),
  cancelAddContainerButton: document.querySelector("#cancelAddContainerButton"),
  containersGrid: document.querySelector("#containersGrid"),
  containersStatus: document.querySelector("#containersStatus"),
  assignContainerOverlay: document.querySelector("#assignContainerOverlay"),
  assignContainerForm: document.querySelector("#assignContainerForm"),
  assignContainerCards: document.querySelector("#assignContainerCards"),
  assignCreateContainerButton: document.querySelector("#assignCreateContainerButton"),
  closeAssignContainerButton: document.querySelector("#closeAssignContainerButton"),
  cancelAssignContainerButton: document.querySelector("#cancelAssignContainerButton"),
  saleOverlay: document.querySelector("#saleOverlay"),
  saleForm: document.querySelector("#saleForm"),
  saleCards: document.querySelector("#saleCards"),
  closeSaleButton: document.querySelector("#closeSaleButton"),
  cancelSaleButton: document.querySelector("#cancelSaleButton"),
  soldOverlay: document.querySelector("#soldOverlay"),
  soldForm: document.querySelector("#soldForm"),
  soldTitle: document.querySelector("#soldTitle"),
  soldSubtitle: document.querySelector("#soldSubtitle"),
  closeSoldButton: document.querySelector("#closeSoldButton"),
  cancelSoldButton: document.querySelector("#cancelSoldButton"),
  storeFrontDetailOverlay: document.querySelector("#storeFrontDetailOverlay"),
  storeFrontDetailTitle: document.querySelector("#storeFrontDetailTitle"),
  storeFrontDetailBody: document.querySelector("#storeFrontDetailBody"),
  closeStoreFrontDetailButton: document.querySelector("#closeStoreFrontDetailButton"),
  containerDetailOverlay: document.querySelector("#containerDetailOverlay"),
  containerDetailTitle: document.querySelector("#containerDetailTitle"),
  containerDetailMeta: document.querySelector("#containerDetailMeta"),
  containerDetailStats: document.querySelector("#containerDetailStats"),
  containerDetailCards: document.querySelector("#containerDetailCards"),
  editContainerButton: document.querySelector("#editContainerButton"),
  shareContainerButton: document.querySelector("#shareContainerButton"),
  emailContainerButton: document.querySelector("#emailContainerButton"),
  deleteContainerButton: document.querySelector("#deleteContainerButton"),
  closeContainerDetailButton: document.querySelector("#closeContainerDetailButton"),
  cardContainersOverlay: document.querySelector("#cardContainersOverlay"),
  cardContainersTitle: document.querySelector("#cardContainersTitle"),
  cardContainersList: document.querySelector("#cardContainersList"),
  closeCardContainersButton: document.querySelector("#closeCardContainersButton"),
  cardMetaOverlay: document.querySelector("#cardMetaOverlay"),
  cardMetaEyebrow: document.querySelector("#cardMetaEyebrow"),
  cardMetaTitle: document.querySelector("#cardMetaTitle"),
  cardMetaList: document.querySelector("#cardMetaList"),
  closeCardMetaButton: document.querySelector("#closeCardMetaButton"),
  cardLedgerOverlay: document.querySelector("#cardLedgerOverlay"),
  cardLedgerEyebrow: document.querySelector("#cardLedgerEyebrow"),
  cardLedgerTitle: document.querySelector("#cardLedgerTitle"),
  cardLedgerList: document.querySelector("#cardLedgerList"),
  closeCardLedgerButton: document.querySelector("#closeCardLedgerButton"),
  shareOverlay: document.querySelector("#shareOverlay"),
  shareTitle: document.querySelector("#shareTitle"),
  shareUrlInput: document.querySelector("#shareUrlInput"),
  copyShareButton: document.querySelector("#copyShareButton"),
  closeShareButton: document.querySelector("#closeShareButton"),
  cardBlogOverlay: document.querySelector("#cardBlogOverlay"),
  cardBlogTitle: document.querySelector("#cardBlogTitle"),
  cardBlogForm: document.querySelector("#cardBlogForm"),
  cardBlogPreview: document.querySelector("#cardBlogPreview"),
  cardBlogStatus: document.querySelector("#cardBlogStatus"),
  closeCardBlogButton: document.querySelector("#closeCardBlogButton"),
  cancelCardBlogButton: document.querySelector("#cancelCardBlogButton"),
  cardBlogListOverlay: document.querySelector("#cardBlogListOverlay"),
  cardBlogListPreview: document.querySelector("#cardBlogListPreview"),
  cardBlogList: document.querySelector("#cardBlogList"),
  cardBlogListStatus: document.querySelector("#cardBlogListStatus"),
  closeCardBlogListButton: document.querySelector("#closeCardBlogListButton"),
  dismissCardBlogListButton: document.querySelector("#dismissCardBlogListButton"),
  writeCardBlogFromListButton: document.querySelector("#writeCardBlogFromListButton"),
  deckJsonOverlay: document.querySelector("#deckJsonOverlay"),
  deckJsonTitle: document.querySelector("#deckJsonTitle"),
  deckJsonText: document.querySelector("#deckJsonText"),
  deckJsonStatus: document.querySelector("#deckJsonStatus"),
  copyDeckJsonButton: document.querySelector("#copyDeckJsonButton"),
  closeDeckJsonButton: document.querySelector("#closeDeckJsonButton"),
  dismissDeckJsonButton: document.querySelector("#dismissDeckJsonButton"),
  exportDecksOverlay: document.querySelector("#exportDecksOverlay"),
  exportDecksStatus: document.querySelector("#exportDecksStatus"),
  closeExportDecksButton: document.querySelector("#closeExportDecksButton"),
  cancelExportDecksButton: document.querySelector("#cancelExportDecksButton"),
  downloadDecksJsonButton: document.querySelector("#downloadDecksJsonButton"),
  downloadDecksCsvButton: document.querySelector("#downloadDecksCsvButton"),
  importDeckOverlay: document.querySelector("#importDeckOverlay"),
  importDeckForm: document.querySelector("#importDeckForm"),
  importDeckJsonText: document.querySelector("#importDeckJsonText"),
  importDeckFileInput: document.querySelector("#importDeckFileInput"),
  importDeckPreview: document.querySelector("#importDeckPreview"),
  importDeckStatus: document.querySelector("#importDeckStatus"),
  closeImportDeckButton: document.querySelector("#closeImportDeckButton"),
  cancelImportDeckButton: document.querySelector("#cancelImportDeckButton"),
  reviewImportDeckButton: document.querySelector("#reviewImportDeckButton"),
  commitImportDeckButton: document.querySelector("#commitImportDeckButton"),
  sharedCardShell: document.querySelector("#sharedCardShell"),
  favoritesShareShell: document.querySelector("#favoritesShareShell"),
  wishlistShareShell: document.querySelector("#wishlistShareShell"),
  containerShareShell: document.querySelector("#containerShareShell"),
  storeShareShell: document.querySelector("#storeShareShell"),
  userProfileShell: document.querySelector("#userProfileShell"),
  cardDetailShell: document.querySelector("#cardDetailShell"),
  editProfileButton: document.querySelector("#editProfileButton"),
  profileOverlay: document.querySelector("#profileOverlay"),
  profileForm: document.querySelector("#profileForm"),
  profileImageInput: document.querySelector("#profileImageInput"),
  profileImagePreview: document.querySelector("#profileImagePreview"),
  profileStatus: document.querySelector("#profileStatus"),
  closeProfileButton: document.querySelector("#closeProfileButton"),
  cancelProfileButton: document.querySelector("#cancelProfileButton"),
  addPurchaseOverlay: document.querySelector("#addPurchaseOverlay"),
  addPurchaseForm: document.querySelector("#addPurchaseForm"),
  addPurchaseTitle: document.querySelector("#addPurchaseTitle"),
  closeAddPurchaseButton: document.querySelector("#closeAddPurchaseButton"),
  cancelAddPurchaseButton: document.querySelector("#cancelAddPurchaseButton"),
  inventoryAdjustOverlay: document.querySelector("#inventoryAdjustOverlay"),
  inventoryAdjustForm: document.querySelector("#inventoryAdjustForm"),
  inventoryAdjustTitle: document.querySelector("#inventoryAdjustTitle"),
  closeInventoryAdjustButton: document.querySelector("#closeInventoryAdjustButton"),
  cancelInventoryAdjustButton: document.querySelector("#cancelInventoryAdjustButton"),
  directSaleOverlay: document.querySelector("#directSaleOverlay"),
  directSaleForm: document.querySelector("#directSaleForm"),
  directSaleTitle: document.querySelector("#directSaleTitle"),
  closeDirectSaleButton: document.querySelector("#closeDirectSaleButton"),
  cancelDirectSaleButton: document.querySelector("#cancelDirectSaleButton"),
  setPageShell: document.querySelector("#setPageShell"),
  navCommands: document.querySelectorAll(".nav-command"),
  pages: document.querySelectorAll(".app-page"),
};

function defaultSettings() {
  const browserLanguage = (navigator.language || "en").slice(0, 2).toLowerCase();
  return {
    language: browserLanguage === "en" ? "en" : "en",
    theme: "light",
  };
}

function loadSettings() {
  try {
    return { ...defaultSettings(), ...JSON.parse(localStorage.getItem(settingsKey) || "{}") };
  } catch {
    return defaultSettings();
  }
}

function saveSettings(settings) {
  state.settings = { ...defaultSettings(), ...settings };
  localStorage.setItem(settingsKey, JSON.stringify(state.settings));
  applySettings();
}

function applySettings() {
  const settings = state.settings || defaultSettings();
  document.documentElement.lang = settings.language || "en";
  document.documentElement.dataset.theme = settings.theme || "light";
  if (els.settingsPageForm) {
    els.settingsPageForm.language.value = settings.language || "en";
    els.settingsPageForm.theme.value = settings.theme || "light";
  }
  if (els.settingsForm) {
    els.settingsForm.language.value = settings.language || "en";
    els.settingsForm.theme.value = settings.theme || "light";
  }
}

function setStatus(message, tone = "", target = els.status) {
  if (!target) return;
  target.textContent = message;
  target.dataset.tone = tone;
}

function isAdminUser() {
  return Boolean(state.user && state.user.is_admin);
}

async function api(path, options = {}) {
  const { promptLogin = false, ...fetchOptions } = options;
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(fetchOptions.headers || {}),
    },
    ...fetchOptions,
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    let message = payload && payload.error ? payload.error : `Request failed: ${response.status}`;
    if (response.status === 504) {
      message = "Request timed out. If this happened during import, the file may need too many Scryfall lookups at once. Try again after a minute, or reduce the batch size.";
    }
    if (response.status === 401) {
      state.user = null;
      updateAuthUi();
      if (promptLogin) {
        openAuthModal("login", message);
      }
    }
    throw new Error(message);
  }
  return payload;
}

async function loadAppConfig() {
  try {
    state.appConfig = await api("/api/config");
  } catch {
    state.appConfig = {};
  }
  applySiteWallpaper();
}

function applySiteWallpaper() {
  const wallpaper = state.appConfig?.wallpaper;
  const url = wallpaper?.url || "";
  if (url) {
    document.documentElement.style.setProperty("--site-wallpaper-image", `url("${String(url).replace(/"/g, "%22")}")`);
    document.body.classList.add("has-site-wallpaper");
  } else {
    document.documentElement.style.removeProperty("--site-wallpaper-image");
    document.body.classList.remove("has-site-wallpaper");
  }
}

function hostFromBaseUrl(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  try {
    return new URL(raw).hostname;
  } catch {
    return raw.replace(/^https?:\/\//i, "").replace(/\/.*$/, "");
  }
}

function defaultAdminFromEmail() {
  const host = hostFromBaseUrl(state.appConfig?.app_base_url) || window.location.hostname;
  return host ? `admin@${host}` : "";
}

function updateAuthUi() {
  const loggedIn = Boolean(state.user);
  if (!loggedIn) {
    state.unreadNotificationCount = 0;
  }
  document.body.classList.toggle("is-authenticated", loggedIn);
  for (const command of els.navCommands || []) {
    const target = command.dataset.pageTarget;
    if (!target) continue;
    command.hidden = (!loggedIn && protectedPage(target)) || (target === "admin" && !isAdminUser());
  }
  if (els.accountButton) {
    if (loggedIn) {
      els.accountButton.innerHTML = displayNameHtml(state.user.name || state.user.email, state.user);
    } else {
      els.accountButton.textContent = state.appConfig?.server_claimed === false ? "Claim Server" : "Login / Create Account";
    }
    els.accountButton.title = loggedIn
      ? `Account settings - ${state.user.email}`
      : state.appConfig?.server_claimed === false
        ? "Claim this Arcane Ledger server"
        : "Log in or create an account";
  }
  if (els.addCardButton) {
    els.addCardButton.hidden = !loggedIn;
  }
  if (els.myProfileButton) {
    els.myProfileButton.hidden = !loggedIn;
  }
  if (els.logoutButton) {
    const icon = els.logoutButton.querySelector("[aria-hidden='true']");
    const label = els.logoutButton.querySelector(".auth-command-label");
    els.logoutButton.hidden = !loggedIn;
    els.logoutButton.title = "Log out";
    els.logoutButton.setAttribute("aria-label", "Log out");
    if (icon) {
      icon.className = "logout-icon";
    }
    if (label) {
      label.textContent = "Logout";
    }
  }
  if (els.settingsAccountEmail) {
    els.settingsAccountEmail.textContent = loggedIn ? state.user.email : "Not logged in";
  }
  updateNotificationsDot();
  applyNavCollapsedState();
}

function openMyProfile() {
  if (!state.user) {
    openAuthModal("login", "Log in to view your profile.");
    return;
  }
  const slug = state.user.profile_slug || "";
  if (!slug) {
    activatePage("settings", { push: true });
    setStatus("Save a display name before opening your profile.", "error", els.settingsPageStatus);
    return;
  }
  window.history.pushState({}, "", `/user/${encodeURIComponent(slug)}`);
  loadUserProfile(slug);
}

function syncSettingsFromUser(user) {
  if (!user) return;
  state.settings = { ...defaultSettings(), language: user.language || "en", theme: user.theme || "light" };
  localStorage.setItem(settingsKey, JSON.stringify(state.settings));
  applySettings();
}

async function loadSession() {
  const payload = await api("/api/auth/session");
  state.user = payload.user || null;
  if (state.user) {
    syncSettingsFromUser(state.user);
    await loadNotificationSummary().catch(() => {});
  }
  updateAuthUi();
  return state.user;
}

function authMode() {
  return els.authForm?.mode.value || "login";
}

function setAuthMode(mode) {
  const nextMode = ["claim", "register", "register-direct", "complete", "reset-request", "reset-complete"].includes(mode) ? mode : "login";
  els.authForm.mode.value = nextMode;
  const isClaim = nextMode === "claim";
  const isLogin = nextMode === "login";
  const isRegister = nextMode === "register";
  const isRegisterDirect = nextMode === "register-direct";
  const isComplete = nextMode === "complete";
  const isResetRequest = nextMode === "reset-request";
  const isResetComplete = nextMode === "reset-complete";
  els.authTitle.textContent = isClaim
    ? "Claim Server"
    : isComplete
    ? "Finish Account"
    : (isRegister || isRegisterDirect)
      ? "Create Account"
      : isResetRequest
        ? "Reset Password"
        : isResetComplete
          ? "Choose New Password"
          : "Log In";
  els.submitAuthButton.textContent = isClaim
    ? "Claim Server"
    : isComplete
    ? "Create Account"
    : isRegister
      ? "Send Verification Email"
      : isRegisterDirect
        ? "Create Account"
      : isResetRequest
        ? "Send Reset Email"
        : isResetComplete
          ? "Update Password"
          : "Log In";
  els.toggleAuthModeButton.textContent = isLogin ? "Create Account" : "Use Existing Account";
  els.toggleAuthModeButton.hidden = isClaim || isComplete || isResetComplete;
  els.forgotPasswordButton.hidden = !isLogin || state.appConfig?.email_configured === false;
  const showName = isComplete;
  els.authNameField.hidden = !showName;
  els.authNameField.toggleAttribute("hidden", !showName);
  els.authNameField.style.display = showName ? "" : "none";
  const hidePassword = isRegister || isResetRequest;
  els.authPasswordField.hidden = hidePassword;
  els.authPasswordField.toggleAttribute("hidden", hidePassword);
  els.authPasswordField.style.display = hidePassword ? "none" : "";
  els.authForm.email.readOnly = isComplete || isResetComplete;
  els.authForm.email.required = true;
  els.authForm.name.required = showName;
  els.authForm.name.disabled = !showName;
  if (!showName) {
    els.authForm.name.value = "";
  }
  els.authForm.password.required = !hidePassword;
  els.authForm.password.disabled = hidePassword;
  els.authHint.textContent = isClaim
    ? "This is the one shot to claim this server and become the server admin."
    : isComplete
    ? "Email verified. Add a display name and a strong password to finish creating your account."
    : isRegister
      ? "Enter your email and we will send a verification link before you create a password. Use this again to resend a verification email."
      : isRegisterDirect
        ? "Email is not configured, so create your account with an email address and strong password."
      : isResetRequest
        ? "Enter your account email and we will send a password reset link."
        : isResetComplete
          ? "Choose a new strong password for your Arcane Ledger account."
          : "Log in to manage your collection, decks, containers, favorites, and wishlist.";
  els.authForm.password.autocomplete = (isComplete || isResetComplete) ? "new-password" : "current-password";
  if (els.togglePasswordVisibilityButton) {
    els.togglePasswordVisibilityButton.textContent = "Show";
    els.authForm.password.type = "password";
  }
}

function openAuthModal(mode = "login", message = "") {
  if (!els.authOverlay) return;
  if (mode === "login" && state.appConfig?.server_claimed === false && !state.user) {
    mode = "claim";
  }
  setAuthMode(mode);
  els.authStatus.textContent = message;
  els.authStatus.dataset.tone = message ? "error" : "";
  els.authOverlay.hidden = false;
  document.body.classList.add("modal-open");
  if (authMode() === "complete") {
    els.authForm.name.focus();
  } else if (authMode() === "reset-complete") {
    els.authForm.password.focus();
  } else {
    els.authForm.email.focus();
  }
}

function closeAuthModal() {
  if (!els.authOverlay) return;
  els.authOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.authStatus.textContent = "";
}

async function submitAuthForm() {
  const payload = Object.fromEntries(new FormData(els.authForm).entries());
  const mode = authMode();
  if (mode === "claim") {
    const result = await api("/api/auth/claim-server", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.user = result.user;
    state.appConfig = { ...(state.appConfig || {}), server_claimed: true };
    syncSettingsFromUser(state.user);
    updateAuthUi();
    await loadNotificationSummary().catch(() => {});
    closeAuthModal();
    await activatePage("dashboard", { replace: true });
    return;
  }
  if (mode === "register") {
    const result = await api("/api/auth/register-start", {
      method: "POST",
      body: JSON.stringify({ email: payload.email }),
    });
    els.authStatus.textContent = result.message || "Check your email for a verification link.";
    els.authStatus.dataset.tone = "";
    els.submitAuthButton.textContent = "Resend Verification Email";
    return;
  }
  if (mode === "register-direct") {
    const result = await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.user = result.user;
    syncSettingsFromUser(state.user);
    updateAuthUi();
    await loadNotificationSummary().catch(() => {});
    closeAuthModal();
    await activatePage("dashboard", { replace: true });
    return;
  }
  if (mode === "reset-request") {
    const result = await api("/api/auth/password-reset-start", {
      method: "POST",
      body: JSON.stringify({ email: payload.email }),
    });
    els.authStatus.textContent = result.message || "If that email has an Arcane Ledger account, a password reset link has been sent.";
    els.authStatus.dataset.tone = "";
    return;
  }
  if (mode === "reset-complete") {
    const result = await api("/api/auth/password-reset-complete", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.user = result.user;
    syncSettingsFromUser(state.user);
    updateAuthUi();
    await loadNotificationSummary().catch(() => {});
    closeAuthModal();
    await activatePage("dashboard", { replace: true });
    return;
  }
  const endpoint = mode === "complete" ? "/api/auth/register-complete" : "/api/auth/login";
  const result = await api(endpoint, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.user = result.user;
  syncSettingsFromUser(state.user);
  updateAuthUi();
  await loadNotificationSummary().catch(() => {});
  closeAuthModal();
  await activatePage("dashboard", { replace: true });
}

async function loadEmailVerification(token) {
  activatePage("home", { replace: true, promptLogin: false });
  try {
    const result = await api(`/api/auth/verification?token=${encodeURIComponent(token)}`);
    els.authForm.reset();
    els.authForm.token.value = token;
    els.authForm.email.value = result.email || "";
    openAuthModal("complete", "");
  } catch (error) {
    openAuthModal("login", error.message);
  }
}

async function loadPasswordReset(token) {
  activatePage("home", { replace: true, promptLogin: false });
  try {
    const result = await api(`/api/auth/password-reset?token=${encodeURIComponent(token)}`);
    els.authForm.reset();
    els.authForm.token.value = token;
    els.authForm.email.value = result.email || "";
    openAuthModal("reset-complete", "");
  } catch (error) {
    openAuthModal("reset-request", error.message);
  }
}

async function logout() {
  await api("/api/auth/logout", { method: "POST", body: JSON.stringify({}) });
  state.user = null;
  state.cards = [];
  state.favoriteCards = [];
  state.favoriteDecks = [];
  state.favoriteStores = [];
  state.missingCards = [];
  state.saleCards = [];
  state.wishlistCards = [];
  state.wishlists = [];
  state.notifications = [];
  state.unreadNotificationCount = 0;
  state.adminUsers = [];
  state.adminLogs = null;
  state.adminServer = null;
  state.adminReports = [];
  state.adminEmailTemplates = [];
  state.adminAnnouncements = [];
  state.adminWallpapers = [];
  state.editingAdminEmailTemplateId = null;
  state.editingAdminAnnouncementId = null;
  state.ownedSetCards = [];
  state.ownedSets = [];
  state.activeWishlist = null;
  state.activeOwnedSet = null;
  updateAuthUi();
  updateNotificationsDot();
  activatePage("home", { push: true });
}

function protectedPage(page) {
  return !["home", "search", "store-front", "browse-decks", "deck-share", "card-share", "favorites-share", "wishlist-share", "container-share", "store-share"].includes(page);
}

function valueClass(value) {
  if (value > 0.004) return "positive";
  if (value < -0.004) return "negative";
  return "";
}

function isSpecialVariant(variant) {
  return Boolean(variant && variant.toLowerCase() !== "normal");
}

function cardHasSpecialVariant(card) {
  if (Boolean(card.has_special_variant)) return true;
  if (isSpecialVariant(card.variant)) return true;
  return variantSummaries(card).some((summary) => isSpecialVariant(summary.variant));
}

function cardTitle(card) {
  return card.display_name || card.flavor_name || card.name || "";
}

function cardRulesName(card) {
  const title = cardTitle(card);
  return title && card.name && title !== card.name ? card.name : "";
}

function conditionText(card) {
  return cardConditions.includes(card.card_condition) ? card.card_condition : "Near Mint";
}

function parseListField(value) {
  if (Array.isArray(value)) return value;
  if (value === null || value === undefined || value === "") return null;
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : null;
  } catch (error) {
    return String(value).split(",").map((item) => item.trim()).filter(Boolean);
  }
}

function primaryCardType(typeLine) {
  const text = String(typeLine || "").toLowerCase();
  if (!text) return "Unknown";
  const checks = [
    ["token", "Token"],
    ["land", "Land"],
    ["creature", "Creature"],
    ["planeswalker", "Planeswalker"],
    ["battle", "Battle"],
    ["artifact", "Artifact"],
    ["enchantment", "Enchantment"],
    ["instant", "Instant"],
    ["sorcery", "Sorcery"],
  ];
  const match = checks.find(([needle]) => text.includes(needle));
  return match ? match[1] : String(typeLine).split("—", 1)[0].trim() || "Other";
}

function cardTypeLabel(card) {
  return card.type_category || primaryCardType(card.type_line);
}

function colorCodes(card) {
  const colors = parseListField(card.colors);
  if (colors && colors.length) return colors;
  const identity = parseListField(card.color_identity);
  if (identity && identity.length) return identity;
  if (colors || identity) return [];
  return null;
}

function cardColorLabel(card) {
  const colors = colorCodes(card);
  if (colors === null) return "Unknown";
  if (!colors.length) return "Colorless";
  return colors.join(" ");
}

function cardMetadataPillsHtml(card) {
  return `
    <span class="type-pill">${escapeHtml(cardTypeLabel(card))}</span>
    <span class="color-pill">${escapeHtml(cardColorLabel(card))}</span>
  `;
}

function variantSummaries(card) {
  const summaries = Array.isArray(card.variant_summaries) ? card.variant_summaries : [];
  if (summaries.length) {
    return summaries
      .map((summary) => ({
        variant: summary.variant || "Normal",
        quantity: Number(summary.quantity || 0),
        conditions: Array.isArray(summary.conditions) ? summary.conditions : [],
      }))
      .filter((summary) => summary.quantity > 0 || summary.conditions.length);
  }
  const buckets = Array.isArray(card.condition_inventory) ? card.condition_inventory : [];
  if (buckets.length) {
    const variants = new Map();
    for (const bucket of buckets) {
      const variant = bucket.variant || card.variant || "Normal";
      const entry = variants.get(variant) || { variant, quantity: 0, conditions: [] };
      const quantity = Number(bucket.quantity || 0);
      entry.quantity += quantity;
      entry.conditions.push({
        card_condition: bucket.card_condition || conditionText(card),
        quantity,
      });
      variants.set(variant, entry);
    }
    return Array.from(variants.values());
  }
  const quantity = Number(card.quantity ?? card.owned_quantity ?? 0);
  if (quantity <= 0) return [];
  return [{
    variant: card.variant || "Normal",
    quantity,
    conditions: [{
      card_condition: conditionText(card),
      quantity,
    }],
  }];
}

function totalVariantQuantity(card) {
  const summaries = variantSummaries(card);
  if (summaries.length) {
    return summaries.reduce((total, summary) => total + Number(summary.quantity || 0), 0);
  }
  return Number(card.quantity ?? card.owned_quantity ?? 0);
}

function totalVariantMarketValue(card) {
  const summaries = variantSummaries(card);
  if (!summaries.length) return Number(card.total_value ?? card.owned_value ?? 0);
  return summaries.reduce((total, summary) => total + (Number(summary.quantity || 0) * Number(priceForVariant(card, summary.variant || "Normal") || 0)), 0);
}

function conditionChipsHtml(conditions) {
  const validConditions = (conditions || []).filter((condition) => Number(condition.quantity || 0) > 0);
  if (!validConditions.length) return '<span class="variant-condition-chip">None</span>';
  return validConditions.map((condition) => `
    <span class="variant-condition-chip">
      ${escapeHtml(condition.card_condition || "Near Mint")}
      <small>${integer.format(condition.quantity || 0)}</small>
    </span>
  `).join("");
}

function variantSummaryHtml(card) {
  const summaries = variantSummaries(card);
  if (!summaries.length) return "";
  return `
    <div class="variant-summary-table" aria-label="Card variants">
      <div class="variant-summary-header">
        <span>Variant</span>
        <span>Conditions</span>
        <span>Qty</span>
      </div>
      ${summaries.map((summary) => `
        <div class="variant-summary-row ${isSpecialVariant(summary.variant) ? "is-special-variant" : ""}">
          <strong>${escapeHtml(summary.variant || "Normal")}</strong>
          <span class="variant-condition-list">${conditionChipsHtml(summary.conditions)}</span>
          <b>${integer.format(summary.quantity || 0)}</b>
        </div>
      `).join("")}
    </div>
  `;
}

function primaryVariantForGroup(cards) {
  const special = cards.find((card) => isSpecialVariant(card.variant));
  return special || cards[0];
}

function groupedCardsForDisplay(cards) {
  const groups = new Map();
  for (const card of cards || []) {
    const key = card.scryfall_id || card.card_id || `${card.name || ""}::${card.collector_number || ""}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(card);
  }
  const grouped = [];
  for (const group of groups.values()) {
    if (group.length === 1) {
      const card = { ...group[0] };
      card.quantity = totalVariantQuantity(card);
      card.owned_quantity = Number(card.owned_quantity ?? card.quantity ?? 0) || card.quantity;
      card.has_special_variant = cardHasSpecialVariant(card);
      grouped.push(card);
      continue;
    }
    const primary = primaryVariantForGroup(group);
    const summariesByVariant = new Map();
    const conditionInventory = [];
    let quantity = 0;
    let ownedValue = 0;
    let gainLoss = 0;
    let containerQuantity = 0;
    let deckQuantity = 0;
    let saleQuantity = 0;
    let unassignedQuantity = 0;
    const mergedDeckMemberships = [];
    const containerMembershipsList = [];
    const variantEntries = [];
    for (const card of group) {
      const variant = card.variant || "Normal";
      const cardSummaries = variantSummaries(card);
      const summary = cardSummaries.find((item) => (item.variant || "Normal") === variant) || {
        variant,
        quantity: Number(card.quantity || 0),
        conditions: [],
      };
      summariesByVariant.set(variant, summary);
      quantity += Number(card.quantity || 0);
      ownedValue += Number(card.owned_value || 0);
      gainLoss += Number(card.gain_loss || 0);
      containerQuantity += Number(card.container_quantity || 0);
      deckQuantity += Number(card.deck_quantity || 0);
      saleQuantity += Number(card.sale_quantity || 0);
      unassignedQuantity += Number(card.unassigned_quantity ?? card.quantity ?? 0);
      for (const bucket of card.condition_inventory || []) {
        conditionInventory.push({ ...bucket, variant: bucket.variant || variant });
      }
      variantEntries.push({
        ...card,
        variant,
        quantity: Number(card.quantity || 0),
        owned_quantity: Number(card.quantity || 0),
        condition_inventory: (card.condition_inventory || []).map((bucket) => ({ ...bucket, variant: bucket.variant || variant })),
      });
      mergedDeckMemberships.push(...deckMemberships(card));
      containerMembershipsList.push(...containerMemberships(card));
    }
    grouped.push({
      ...primary,
      quantity,
      owned_quantity: quantity,
      owned_value: ownedValue,
      total_value: ownedValue,
      gain_loss: gainLoss,
      container_quantity: containerQuantity,
      deck_quantity: deckQuantity,
      sale_quantity: saleQuantity,
      unassigned_quantity: unassignedQuantity,
      condition_inventory: conditionInventory,
      variant_entries: variantEntries,
      variant_summaries: Array.from(summariesByVariant.values()),
      deck_memberships: mergedDeckMemberships,
      container_memberships: containerMembershipsList,
      has_special_variant: group.some(cardHasSpecialVariant),
    });
  }
  return grouped;
}

function selectedCardEntries(card) {
  if (Array.isArray(card.variant_entries) && card.variant_entries.length) {
    return card.variant_entries;
  }
  const summaries = variantSummaries(card).filter((summary) => Number(summary.quantity || 0) > 0);
  if (!summaries.length || summaries.length === 1 && (summaries[0].variant || "Normal") === (card.variant || "Normal")) {
    return [card];
  }
  return summaries.map((summary) => ({
    ...card,
    variant: summary.variant || "Normal",
    quantity: Number(summary.quantity || 0),
    unassigned_quantity: Number(summary.quantity || 0),
    saleable_quantity: Number(summary.quantity || 0),
    deck_quantity: 0,
    sale_quantity: 0,
    sale_price: priceForVariant(card, summary.variant || "Normal"),
    display_price: priceForVariant(card, summary.variant || "Normal"),
    condition_inventory: (summary.conditions || []).map((condition) => ({
      variant: summary.variant || "Normal",
      card_condition: condition.card_condition || "Near Mint",
      quantity: Number(condition.quantity || 0),
      sale_available_quantity: Number(condition.quantity || 0),
      sale_quantity: 0,
      sale_price: priceForVariant(card, summary.variant || "Normal"),
    })),
  }));
}

function cardSelectionKey(card) {
  return `${card.scryfall_id}::${card.variant || "Normal"}`;
}

function updateBulkBar() {
  const count = state.selectedCards.size;
  for (const bar of [els.collectionBulkBar, els.favoritesBulkBar]) {
    if (bar) bar.hidden = count === 0;
  }
  for (const countEl of [els.selectedCardsCount, els.favoriteSelectedCardsCount]) {
    if (countEl) countEl.textContent = `${integer.format(count)} selected`;
  }
}

function clearSelectedCards() {
  state.selectedCards.clear();
  for (const checkbox of document.querySelectorAll(".select-card-checkbox")) {
    checkbox.checked = false;
  }
  updateBulkBar();
}

function updateSetMissingBar() {
  const bar = els.setPageShell?.querySelector("#setMissingBulkBar");
  const countEl = els.setPageShell?.querySelector("#setMissingSelectedCount");
  const count = state.selectedSetMissingCards.size;
  if (bar) bar.hidden = count === 0;
  if (countEl) countEl.textContent = `${integer.format(count)} selected`;
}

function clearSetMissingSelection() {
  state.selectedSetMissingCards.clear();
  for (const checkbox of els.setPageShell?.querySelectorAll(".select-card-checkbox") || []) {
    checkbox.checked = false;
  }
  updateSetMissingBar();
}

function wireCardSelection(selectWrap, selectCheckbox, card, options = {}) {
  const owned = Number(card.quantity || 0) > 0;
  const selectable = Boolean(options.selectable && owned);
  const entries = selectedCardEntries(card).filter((entry) => Number(entry.quantity || 0) > 0);
  selectWrap.hidden = !options.selectable;
  selectCheckbox.disabled = !selectable;
  selectCheckbox.checked = entries.length > 0 && entries.every((entry) => state.selectedCards.has(cardSelectionKey(entry)));
  selectCheckbox.addEventListener("change", () => {
    if (selectCheckbox.checked) {
      for (const entry of entries) {
        state.selectedCards.set(cardSelectionKey(entry), {
          card_id: entry.scryfall_id,
          variant: entry.variant || "Normal",
          name: cardTitle(entry),
          quantity: Number(entry.quantity || 0),
          unassigned_quantity: Number(entry.unassigned_quantity ?? entry.quantity ?? 0),
          saleable_quantity: Number(entry.saleable_quantity ?? entry.quantity ?? 0),
          deck_quantity: Number(entry.deck_quantity || 0),
          display_price: Number(entry.display_price || entry.market_price || 0),
          sale_quantity: Number(entry.sale_quantity || 0),
          sale_price: Number(entry.sale_price || entry.display_price || entry.market_price || 0),
          card_condition: conditionText(entry),
          condition_inventory: Array.isArray(entry.condition_inventory) ? entry.condition_inventory : [],
          image_small: entry.image_small || "",
          image_normal: entry.image_normal || "",
        });
      }
    } else {
      for (const entry of entries) {
        state.selectedCards.delete(cardSelectionKey(entry));
      }
    }
    updateBulkBar();
  });
}

function wireSetMissingSelection(selectWrap, selectCheckbox, card) {
  const owned = Number(card.quantity || 0) > 0;
  const alreadyMissing = Boolean(Number(card.missing_list || 0));
  const selectable = !owned && !alreadyMissing;
  selectWrap.hidden = owned;
  selectCheckbox.disabled = !selectable;
  selectWrap.title = alreadyMissing ? "Already on Missing List" : "Select missing card";
  selectCheckbox.setAttribute("aria-label", `Select ${cardTitle(card)} for Missing List`);
  selectCheckbox.checked = state.selectedSetMissingCards.has(cardSelectionKey(card));
  selectCheckbox.addEventListener("change", () => {
    const key = cardSelectionKey(card);
    if (selectCheckbox.checked) {
      state.selectedSetMissingCards.set(key, {
        card_id: card.scryfall_id,
        variant: card.variant || "Normal",
        name: cardTitle(card),
      });
    } else {
      state.selectedSetMissingCards.delete(key);
    }
    updateSetMissingBar();
  });
}

function wireShareButton(button, card) {
  button.disabled = !card.share_id;
  button.addEventListener("click", () => openShareModal(card));
}

function wireDeleteCardButton(button, card) {
  const owned = Number(card.quantity || 0) > 0;
  button.disabled = !owned;
  button.addEventListener("click", () => {
    deleteCollectionCard(card).catch((error) => setStatus(error.message, "error"));
  });
}

function wireRefreshCardButton(button, card) {
  if (!button) return;
  button.addEventListener("click", () => {
    refreshCardMetadata(button, card).catch((error) => setStatus(error.message, "error"));
  });
}

function wireWishlistButton(button, card, options = {}) {
  if (!button) return;
  const owned = Number(card.quantity || 0) > 0;
  button.hidden = owned;
  button.disabled = owned;
  if (owned) return;
  button.classList.toggle("is-wishlist", Boolean(card.wishlist));
  button.setAttribute("aria-pressed", card.wishlist ? "true" : "false");
  button.title = options.wishlistId ? "Remove from this Wishlist" : "Add to Wishlist";
  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    if (!state.user) {
      openAuthModal("register", "Create an account or log in before saving cards to your Wishlist.");
      return;
    }
    if (!options.wishlistId) {
      openAssignWishlistModal(card, options).catch((error) => setStatus(error.message, "error", options.statusTarget || els.status));
      return;
    }
    if (options.confirmUnwishlist) {
      const confirmed = window.confirm(`Remove ${cardTitle(card)} from this Wishlist? It will disappear from this list.`);
      if (!confirmed) return;
    }
    try {
      await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/wishlist`, {
        method: "POST",
        body: JSON.stringify({
          variant: card.variant || "Normal",
          wishlist_id: options.wishlistId,
          wishlist: false,
        }),
      });
      setStatus(`Removed ${cardTitle(card)} from Wishlist.`, "", options.statusTarget || els.status);
      if (options.afterWishlistChange) {
        await options.afterWishlistChange();
      } else {
        await reloadVisibleCardPages();
      }
    } catch (error) {
      setStatus(error.message, "error", options.statusTarget || els.status);
    }
  });
}

function openCardDetail(card) {
  if (!card || !card.scryfall_id) return;
  window.history.pushState({}, "", cardDetailUrl(card));
  loadCardDetail(card.scryfall_id, card.variant || "Normal").catch((error) => {
    setStatus(error.message, "error");
  });
}

function wireCardDetailNavigation(node, card) {
  node.addEventListener("click", (event) => {
    if (event.target.closest("button, a, input, label, select, textarea")) return;
    openCardDetail(card);
  });
}

function wireScryfallButton(button, card) {
  if (!button) return;
  button.href = card.scryfall_uri || "#";
  button.hidden = !card.scryfall_uri;
  button.addEventListener("click", (event) => {
    event.stopPropagation();
  });
}

async function refreshCardMetadata(button, card) {
  button.disabled = true;
  button.classList.add("is-spinning");
  setStatus(`Refreshing ${cardTitle(card)} from Scryfall...`);
  try {
    await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/refresh`, { method: "POST" });
    setStatus(`Refreshed ${cardTitle(card)} from Scryfall.`);
    await refresh();
  } finally {
    button.disabled = false;
    button.classList.remove("is-spinning");
  }
}

async function refreshCardDetailMetadata(button, card) {
  button.disabled = true;
  button.classList.add("is-spinning");
  setStatus(`Refreshing ${cardTitle(card)} from Scryfall...`);
  try {
    await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/refresh`, { method: "POST" });
    await Promise.all([
      loadCardDetail(card.scryfall_id, card.variant || "Normal"),
      refresh(),
    ]);
    setStatus(`Refreshed ${cardTitle(card)} from Scryfall.`);
  } finally {
    button.disabled = false;
    button.classList.remove("is-spinning");
  }
}

async function deleteCardFromDetail(card) {
  await deleteCollectionCard(card);
  window.history.pushState({}, "", "/");
  showPage("collection");
}

async function deleteCardMovement(button) {
  const card = state.activeCardDetail;
  if (!card) return;
  const movementType = button.dataset.movementType;
  const movementId = button.dataset.movementId;
  const isSale = movementType === "sell";
  const isAdjust = movementType === "adjust";
  const confirmed = window.confirm(
    isSale
      ? "Delete this sold entry? This will undo the sale, restore inventory, and put the card back on For Sale."
      : isAdjust
        ? "Delete this adjustment entry? This will reverse the inventory adjustment."
      : "Delete this purchase entry? This will reduce inventory. This is blocked if sold entries still depend on it."
  );
  if (!confirmed) return;
  const result = await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/movements`, {
    method: "DELETE",
    body: JSON.stringify({
      variant: card.variant || "Normal",
      movement_type: movementType,
      movement_id: movementId,
    }),
  });
  if (result.card) {
    renderCardDetail(result.card);
  } else {
    await loadCardDetail(card.scryfall_id, card.variant || "Normal");
  }
  await loadCards();
  await loadSaleCards();
  setStatus("Card history entry deleted.");
}

async function deleteCollectionCard(card) {
  const confirmed = window.confirm(`Remove ${cardTitle(card)} (${card.variant || "Normal"}) from your collection?`);
  if (!confirmed) return;
  await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/collection`, {
    method: "DELETE",
    body: JSON.stringify({ variant: card.variant || "Normal" }),
  });
  setStatus(`Removed ${cardTitle(card)} from your collection.`);
  state.selectedCards.delete(cardSelectionKey(card));
  await refresh();
}

function setCollectionView(view) {
  state.collectionView = view === "list" ? "list" : "tiles";
  localStorage.setItem("arcaneledger.collectionView", state.collectionView);
  els.tileViewButton.classList.toggle("is-active", state.collectionView === "tiles");
  els.listViewButton.classList.toggle("is-active", state.collectionView === "list");
  renderCollection();
}

function setFavoritesView(view) {
  state.favoritesView = view === "list" ? "list" : "tiles";
  localStorage.setItem("arcaneledger.favoritesView", state.favoritesView);
  els.favoriteTileViewButton.classList.toggle("is-active", state.favoritesView === "tiles");
  els.favoriteListViewButton.classList.toggle("is-active", state.favoritesView === "list");
  renderFavorites();
}

function setFavoritesFilter(filter) {
  state.favoritesFilter = ["all", "cards", "decks", "store"].includes(filter) ? filter : "all";
  localStorage.setItem("arcaneledger.favoritesFilter", state.favoritesFilter);
  renderFavorites();
}

function renderHome(data = {}) {
  state.homeAnnouncements = Array.isArray(data.announcements) ? data.announcements : [];
  renderHomeAnnouncements();
  renderTodaysCard(data.todays_card || null);
  if (els.homeTotalValue) els.homeTotalValue.textContent = dollars.format(data.total_value || 0);
  if (els.homeUserCount) els.homeUserCount.textContent = integer.format(data.user_count || 0);
  if (els.homeCatalogedCards) els.homeCatalogedCards.textContent = integer.format(data.cataloged_cards || 0);
  if (els.homeUniqueCards) els.homeUniqueCards.textContent = integer.format(data.unique_cards || 0);
  if (els.homeDeckCount) els.homeDeckCount.textContent = integer.format(data.deck_count || 0);
  if (els.homeContainerCount) els.homeContainerCount.textContent = integer.format(data.container_count || 0);
  if (els.homeWishlistCount) els.homeWishlistCount.textContent = integer.format(data.wishlist_count || 0);
  if (els.homeSaleQuantity) els.homeSaleQuantity.textContent = integer.format(data.sale_quantity || 0);
  if (els.homeSaleAskingTotal) els.homeSaleAskingTotal.textContent = dollars.format(data.sale_asking_total || 0);
}

function renderTodaysCard(card) {
  if (els.homeTodaysCardPanel) {
    els.homeTodaysCardPanel.hidden = !card;
  }
  if (!card) return;
  if (els.homeTodaysCardLink) {
    els.homeTodaysCardLink.href = cardDetailUrl(card);
  }
  if (els.homeTodaysCardImage) {
    els.homeTodaysCardImage.src = card.image_normal || card.image_small || "";
    els.homeTodaysCardImage.alt = cardTitle(card);
  }
  if (els.homeTodaysCardName) {
    els.homeTodaysCardName.textContent = cardTitle(card);
  }
  if (els.homeTodaysCardMeta) {
    els.homeTodaysCardMeta.textContent = `${card.set_name || ""} #${card.collector_number || ""} · ${card.variant || "Normal"} · ${dollars.format(card.display_price || card.market_price || 0)}`;
  }
  if (els.homeTodaysCardText) {
    const fallback = card.type_line ? `${card.type_line}${card.rarity ? ` · ${card.rarity}` : ""}` : "Click to view card details.";
    els.homeTodaysCardText.textContent = card.flavor_text || fallback;
  }
}

function renderHomeAnnouncements() {
  const announcements = state.homeAnnouncements || [];
  if (els.homeAnnouncementsPanel) {
    els.homeAnnouncementsPanel.hidden = !announcements.length;
  }
  if (!els.homeAnnouncementsList) return;
  if (!announcements.length) {
    els.homeAnnouncementsList.innerHTML = "";
    return;
  }
  els.homeAnnouncementsList.innerHTML = announcements.map((announcement) => `
    <button class="home-announcement-row" type="button" data-announcement-id="${escapeHtml(announcement.id)}">
      <span>${escapeHtml(announcement.subject || "Announcement")}</span>
      <small>${escapeHtml(formatAnnouncementRange(announcement))}</small>
    </button>
  `).join("");
  els.homeAnnouncementsList.querySelectorAll(".home-announcement-row").forEach((button) => {
    button.addEventListener("click", () => {
      const announcement = announcements.find((item) => String(item.id) === String(button.dataset.announcementId));
      openHomeAnnouncementDetail(announcement);
    });
  });
}

function openHomeAnnouncementDetail(announcement) {
  if (!announcement || !els.homeAnnouncementDetailOverlay) return;
  if (els.homeAnnouncementDetailTitle) {
    els.homeAnnouncementDetailTitle.textContent = announcement.subject || "Announcement";
  }
  if (els.homeAnnouncementDetailMeta) {
    els.homeAnnouncementDetailMeta.textContent = formatAnnouncementRange(announcement);
  }
  if (els.homeAnnouncementDetailBody) {
    els.homeAnnouncementDetailBody.innerHTML = markdownToHtml(announcement.body || "");
  }
  els.homeAnnouncementDetailOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeHomeAnnouncementDetail() {
  if (!els.homeAnnouncementDetailOverlay) return;
  els.homeAnnouncementDetailOverlay.hidden = true;
  document.body.classList.remove("modal-open");
}

async function loadHome() {
  const data = await api("/api/home");
  renderHome(data);
}

function renderDashboard(data) {
  state.dashboard = data;
  els.currentValue.textContent = dollars.format(data.current_total || 0);
  els.paidTotal.textContent = dollars.format(data.paid_total || 0);
  els.gainLoss.textContent = `${dollars.format(data.gain_loss || 0)} (${(data.gain_loss_percent || 0).toFixed(1)}%)`;
  els.gainLoss.className = valueClass(data.gain_loss || 0);
  els.ownedCards.textContent = `${integer.format(data.owned_cards || 0)} cards`;
  els.favoriteCount.textContent = integer.format(data.favorite_count || 0);
  els.wishlistCount.textContent = integer.format(data.wishlist_count || 0);
  els.saleCount.textContent = integer.format(data.sale_count || 0);
  els.saleAskingTotal.textContent = dollars.format(data.sale_asking_total || 0);
  els.deckCount.textContent = integer.format(data.deck_count || 0);
  els.cardsInDecks.textContent = integer.format(data.cards_in_decks || 0);
  els.containerCount.textContent = integer.format(data.container_count || 0);
  els.uncontainedCards.textContent = integer.format(data.uncontained_cards || 0);
  els.historyCount.textContent = `${(data.history || []).length} months`;
  els.recentCount.textContent = `${integer.format((data.recent_cards || []).length)} cards`;
  els.topCount.textContent = `${integer.format(data.owned_unique || 0)} owned prints`;
  renderRecentCards(data.recent_cards || []);
  renderTopCards(data.top_cards || []);
  renderSetCompletion(data.set_completion || []);
  renderChart(data.history || []);
}

function renderRecentCards(cards) {
  els.recentCards.innerHTML = "";
  if (!cards.length) {
    els.recentCards.innerHTML = '<div class="empty-state">No cards added yet.</div>';
    return;
  }
  for (const card of cards) {
    const item = document.createElement("a");
    item.className = "top-item";
    item.href = cardDetailUrl(card);
    item.innerHTML = `
      <img src="${card.image_small || ""}" alt="">
      <div>
        <strong title="${escapeHtml(cardTitle(card))}">${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)} - Added ${formatCompactDate(card.added_at || card.acquired_date)}</span>
      </div>
      <span class="value">Qty ${integer.format(card.quantity || 0)}</span>
    `;
    els.recentCards.appendChild(item);
  }
}

function renderTopCards(cards) {
  els.topCards.innerHTML = "";
  if (!cards.length) {
    els.topCards.innerHTML = '<div class="empty-state">No owned cards yet.</div>';
    return;
  }
  for (const card of cards) {
    const item = document.createElement("a");
    item.className = "top-item";
    item.href = cardDetailUrl(card);
    item.innerHTML = `
      <img src="${card.image_small || ""}" alt="">
      <div>
        <strong title="${escapeHtml(cardTitle(card))}">${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)} - Qty ${card.quantity}</span>
      </div>
      <span class="value">${dollars.format(card.owned_value || 0)}</span>
    `;
    els.topCards.appendChild(item);
  }
}

function renderSetCompletion(sets) {
  els.setCompletion.innerHTML = "";
  els.setCompletionCount.textContent = `${integer.format(sets.length)} tracked sets`;
  if (!sets.length) {
    els.setCompletion.innerHTML = '<div class="empty-state">No cached owned sets yet.</div>';
    return;
  }
  for (const set of sets) {
    const percent = Math.max(0, Math.min(100, Number(set.completion_percent || 0)));
    const item = document.createElement("button");
    item.className = "set-completion-item";
    item.type = "button";
    item.dataset.setCode = set.set_code || "";
    item.setAttribute("aria-label", `Open ${set.set_name}`);
    item.innerHTML = `
      <div>
        <strong>${escapeHtml(set.set_name)}</strong>
        <span>${integer.format(set.owned_cards || 0)} / ${integer.format(set.total_cards || 0)} unique prints</span>
      </div>
      <b>${percent.toFixed(1)}%</b>
      <div class="set-progress" aria-hidden="true">
        <span style="width: ${percent}%"></span>
      </div>
    `;
    item.addEventListener("click", () => openSetPage(set.set_code));
    els.setCompletion.appendChild(item);
  }
}

function showPage(pageName) {
  for (const page of els.pages) {
    page.hidden = page.dataset.page !== pageName;
  }
  const activePage = pageName === "deck-editor" ? "decks" : pageName;
  for (const command of els.navCommands) {
    command.classList.toggle("is-active", command.dataset.pageTarget === activePage);
  }
  els.myProfileButton?.classList.toggle("is-active", pageName === "user-profile");
}

function applyNavCollapsedState() {
  document.body.classList.toggle("nav-collapsed", state.navCollapsed);
  if (els.navCollapseButton) {
    const label = state.navCollapsed ? "Expand navigation" : "Collapse navigation";
    els.navCollapseButton.setAttribute("aria-label", label);
    els.navCollapseButton.setAttribute("aria-pressed", state.navCollapsed ? "true" : "false");
    els.navCollapseButton.title = label;
  }
  for (const command of els.navCommands || []) {
    const label = command.textContent.trim().replace(/\s+/g, " ");
    if (label) command.title = label;
  }
  if (els.myProfileButton) els.myProfileButton.title = "My Profile";
}

function toggleNavCollapsed() {
  state.navCollapsed = !state.navCollapsed;
  localStorage.setItem("arcaneledger.navCollapsed", state.navCollapsed ? "1" : "0");
  applyNavCollapsedState();
}

function pagePath(pageName) {
  return pageRoutes[pageName] || "/";
}

function pushPageRoute(pageName) {
  const nextPath = pagePath(pageName);
  if (window.location.pathname !== nextPath) {
    window.history.pushState({}, "", nextPath);
  }
}

function replacePageRoute(pageName) {
  const nextPath = pagePath(pageName);
  if (window.location.pathname !== nextPath) {
    window.history.replaceState({}, "", nextPath);
  }
}

function activatePage(pageName, options = {}) {
  const page = pageRoutes[pageName] ? pageName : "home";
  if (deckEditorIsVisible() && state.deckEditorDirty) {
    if (!confirmDiscardDeckEditorChanges()) {
      if (options.fromPop && state.activeDeck?.id) {
        window.history.pushState({}, "", `/decks/${encodeURIComponent(state.activeDeck.id)}`);
      }
      return;
    }
    discardDeckEditorChanges();
  }
  if (protectedPage(page) && !state.user) {
    if (options.replace) {
      replacePageRoute("home");
    } else if (options.push) {
      pushPageRoute("home");
    }
    showPage("home");
    loadHome().catch((error) => setStatus(error.message, "error"));
    if (options.promptLogin !== false) {
      openAuthModal("login", "Log in or create an account to use that feature.");
    }
    return;
  }
  if (page === "admin" && !isAdminUser()) {
    if (options.replace) {
      replacePageRoute(state.user ? "dashboard" : "home");
    } else if (options.push) {
      pushPageRoute(state.user ? "dashboard" : "home");
    }
    showPage(state.user ? "dashboard" : "home");
    setStatus("Admin access required.", "error", state.user ? els.status : undefined);
    if (!state.user && options.promptLogin !== false) {
      openAuthModal("login", "Log in with an admin account to use that feature.");
    }
    return;
  }
  if (options.replace) {
    replacePageRoute(page);
  } else if (options.push) {
    pushPageRoute(page);
  }
  showPage(page);
  if (page === "home") {
    loadHome().catch((error) => setStatus(error.message, "error"));
  }
  if (page === "settings") {
    renderSettingsPage();
  }
  if (page === "dashboard") {
    refresh().catch((error) => {
      setStatus(error.message, "error");
      renderCollection();
    });
  }
  if (page === "favorites") {
    clearSelectedCards();
    loadFavorites().catch((error) => {
      setStatus(error.message, "error", els.favoritesStatus);
    });
  }
  if (page === "collection") {
    loadCards().catch((error) => {
      setStatus(error.message, "error");
      renderCollection();
    });
  }
  if (page === "sets") {
    clearSelectedCards();
    loadOwnedSets().catch((error) => {
      setStatus(error.message, "error", els.setsStatus);
    });
  }
  if (page === "missing-list") {
    clearSelectedCards();
    loadMissingList().catch((error) => {
      setStatus(error.message, "error", els.missingStatus);
    });
  }
  if (page === "for-sale") {
    clearSelectedCards();
    loadSaleCards().catch((error) => {
      setStatus(error.message, "error", els.saleStatus);
    });
  }
  if (page === "store-front") {
    clearSelectedCards();
    loadStoreFront().catch((error) => {
      setStatus(error.message, "error", els.storeFrontStatus);
    });
  }
  if (page === "browse-decks") {
    loadBrowseDecks().catch((error) => {
      setStatus(error.message, "error", els.browseDecksStatus);
    });
  }
  if (page === "wishlist") {
    clearSelectedCards();
    loadWishlists().catch((error) => {
      setStatus(error.message, "error", els.wishlistStatus);
    });
  }
  if (page === "notifications") {
    loadNotifications().catch((error) => {
      setStatus(error.message, "error", els.notificationsStatus);
    });
  }
  if (page === "admin") {
    loadAdmin().catch((error) => {
      setStatus(error.message, "error", els.adminStatus);
    });
  }
  if (page === "search") {
    clearSelectedCards();
    loadCatalogHeroCards().catch(() => renderCatalogHeroCards([]));
    renderCatalogSearchResults();
  }
  if (page === "decks") {
    loadDecks().catch((error) => {
      els.decksStatus.textContent = error.message;
    });
  }
  if (page === "containers") {
    loadContainers().catch((error) => {
      els.containersStatus.textContent = error.message;
    });
  }
}

function activeStatusTarget() {
  const visiblePage = Array.from(els.pages).find((page) => !page.hidden)?.dataset.page || "";
  if (visiblePage === "favorites") return els.favoritesStatus;
  if (visiblePage === "sets") return els.setsStatus;
  if (visiblePage === "missing-list") return els.missingStatus;
  if (visiblePage === "for-sale") return els.saleStatus;
  if (visiblePage === "store-front") return els.storeFrontStatus;
  if (visiblePage === "wishlist") return els.wishlistStatus;
  if (visiblePage === "notifications") return els.notificationsStatus;
  if (visiblePage === "admin") return els.adminStatus;
  if (visiblePage === "search") return els.catalogSearchStatus;
  return els.status;
}

async function reloadVisibleCardPages() {
  const tasks = [loadCards()];
  const favoritesVisible = Array.from(els.pages).some((page) => page.dataset.page === "favorites" && !page.hidden);
  const missingVisible = Array.from(els.pages).some((page) => page.dataset.page === "missing-list" && !page.hidden);
  const saleVisible = Array.from(els.pages).some((page) => page.dataset.page === "for-sale" && !page.hidden);
  const storeFrontVisible = Array.from(els.pages).some((page) => page.dataset.page === "store-front" && !page.hidden);
  const wishlistVisible = Array.from(els.pages).some((page) => page.dataset.page === "wishlist" && !page.hidden);
  const notificationsVisible = Array.from(els.pages).some((page) => page.dataset.page === "notifications" && !page.hidden);
  if (favoritesVisible) {
    tasks.push(loadFavorites());
  }
  if (missingVisible) {
    tasks.push(loadMissingList());
  }
  if (saleVisible) {
    tasks.push(loadSaleCards());
  }
  if (storeFrontVisible) {
    tasks.push(loadStoreFront());
  }
  if (wishlistVisible) {
    tasks.push(loadWishlists());
    if (state.activeWishlist) {
      tasks.push(loadWishlist());
    }
  }
  if (notificationsVisible) {
    tasks.push(loadNotifications());
  } else {
    tasks.push(loadNotificationSummary());
  }
  const cardDetailVisible = Array.from(els.pages).some((page) => page.dataset.page === "card-detail" && !page.hidden);
  if (cardDetailVisible && state.activeCardDetail?.scryfall_id) {
    tasks.push(loadCardDetail(state.activeCardDetail.scryfall_id, state.activeCardDetail.variant || "Normal"));
  }
  await Promise.all(tasks);
}

function sharedRouteId() {
  const match = window.location.pathname.match(/^\/cards\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function setRouteCode() {
  if (window.location.pathname.startsWith("/sets/shared/")) return "";
  const match = window.location.pathname.match(/^\/sets\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]).toLowerCase() : "";
}

function sharedSetRoute() {
  const match = window.location.pathname.match(/^\/sets\/shared\/([^/]+)\/([^/]+)\/?$/);
  if (!match) return null;
  return {
    storeShareId: decodeURIComponent(match[1]),
    setCode: decodeURIComponent(match[2]).toLowerCase(),
  };
}

function deckRouteId() {
  const match = window.location.pathname.match(/^\/decks\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function isPrivateDeckRoute(routeId) {
  return /^[0-9]+$/.test(String(routeId || ""));
}

function wishlistRouteId() {
  const match = window.location.pathname.match(/^\/wishlists\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function containerRouteId() {
  const match = window.location.pathname.match(/^\/containers\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function storeRouteId() {
  const match = window.location.pathname.match(/^\/stores\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function userProfileRoute() {
  const match = window.location.pathname.match(/^\/user\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function favoritesShareRoute() {
  const match = window.location.pathname.match(/^\/favorites\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function cardDetailRoute() {
  const match = window.location.pathname.match(/^\/card\/([^/]+)\/([^/]+)\/?$/);
  if (!match) return null;
  return {
    cardId: decodeURIComponent(match[1]),
    variant: decodeURIComponent(match[2]),
  };
}

function verificationRouteToken() {
  const match = window.location.pathname.match(/^\/verify-email\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function passwordResetRouteToken() {
  const match = window.location.pathname.match(/^\/reset-password\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function appPageRoute() {
  const normalized = window.location.pathname.replace(/\/+$/, "") || "/";
  return routePages[normalized] || "";
}

function cardDetailUrl(card) {
  return `/card/${encodeURIComponent(card.scryfall_id || card.card_id || "")}/${encodeURIComponent(card.variant || "Normal")}`;
}

function renderChart(points) {
  const svg = els.historyChart;
  svg.innerHTML = "";
  svg.setAttribute("viewBox", "0 0 760 380");
  const width = 760;
  const height = 380;
  const padX = 54;
  const padTop = 32;
  const padBottom = 54;
  const values = points.map((point) => Number(point.value || 0));
  const addedValues = points.map((point) => Number(point.added_value || 0));
  const max = Math.max(1, ...values);
  const min = Math.min(0, ...values);
  const span = Math.max(1, max - min);
  const maxAdded = Math.max(1, ...addedValues);
  const plotWidth = width - padX * 2;
  const plotHeight = height - padTop - padBottom;

  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `
    <linearGradient id="historyArea" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="#216e61" stop-opacity="0.34"></stop>
      <stop offset="62%" stop-color="#6fa997" stop-opacity="0.16"></stop>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.02"></stop>
    </linearGradient>
    <linearGradient id="historyStroke" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0%" stop-color="#9f3f34"></stop>
      <stop offset="32%" stop-color="#c79a2f"></stop>
      <stop offset="68%" stop-color="#216e61"></stop>
      <stop offset="100%" stop-color="#276ca3"></stop>
    </linearGradient>
    <linearGradient id="historyBars" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="#c79a2f" stop-opacity="0.42"></stop>
      <stop offset="100%" stop-color="#216e61" stop-opacity="0.10"></stop>
    </linearGradient>
    <filter id="historyShadow" x="-8%" y="-18%" width="116%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="7" flood-color="#17332d" flood-opacity="0.18"></feDropShadow>
    </filter>
  `;
  svg.appendChild(defs);

  const grid = document.createElementNS("http://www.w3.org/2000/svg", "g");
  for (let i = 0; i < 5; i += 1) {
    const y = padTop + (plotHeight * i) / 4;
    const band = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    band.setAttribute("x", padX);
    band.setAttribute("y", y);
    band.setAttribute("width", plotWidth);
    band.setAttribute("height", plotHeight / 4);
    band.setAttribute("fill", i % 2 === 0 ? "rgba(33, 110, 97, 0.035)" : "rgba(199, 154, 47, 0.025)");
    grid.appendChild(band);

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", padX);
    line.setAttribute("x2", width - padX);
    line.setAttribute("y1", y);
    line.setAttribute("y2", y);
    line.setAttribute("stroke", "#dce5e1");
    grid.appendChild(line);

    const gridLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    gridLabel.setAttribute("x", padX - 10);
    gridLabel.setAttribute("y", y + 4);
    gridLabel.setAttribute("text-anchor", "end");
    gridLabel.setAttribute("fill", "#66706d");
    gridLabel.setAttribute("font-size", "11");
    gridLabel.textContent = compactDollars.format(max - (span * i) / 4);
    grid.appendChild(gridLabel);
  }
  svg.appendChild(grid);

  if (!points.length) {
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", width / 2);
    text.setAttribute("y", height / 2);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("fill", "#66706d");
    text.textContent = "No collection value history yet";
    svg.appendChild(text);
    return;
  }

  const coords = points.map((point, index) => {
    const x = points.length === 1 ? width / 2 : padX + (plotWidth * index) / (points.length - 1);
    const y = height - padBottom - ((Number(point.value || 0) - min) / span) * plotHeight;
    return { x, y, point };
  });

  const path = smoothPath(coords);

  const bars = document.createElementNS("http://www.w3.org/2000/svg", "g");
  bars.setAttribute("class", "history-added-bars");
  const barWidth = Math.max(12, Math.min(36, plotWidth / Math.max(points.length, 1) * 0.42));
  for (const coord of coords) {
    const added = Number(coord.point.added_value || 0);
    if (added <= 0) continue;
    const barHeight = Math.max(7, (added / maxAdded) * (plotHeight * 0.42));
    const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bar.setAttribute("class", "history-added-bar");
    bar.setAttribute("x", coord.x - barWidth / 2);
    bar.setAttribute("y", height - padBottom - barHeight);
    bar.setAttribute("width", barWidth);
    bar.setAttribute("height", barHeight);
    bar.setAttribute("rx", "6");
    bar.setAttribute("fill", "url(#historyBars)");
    bar.setAttribute("opacity", "0.92");
    bar.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "title")).textContent = `${coord.point.label}: +${dollars.format(added)}`;
    bars.appendChild(bar);
  }

  const areaPath = `${path} L ${width - padX} ${height - padBottom} L ${padX} ${height - padBottom} Z`;
  const area = document.createElementNS("http://www.w3.org/2000/svg", "path");
  area.setAttribute("d", areaPath);
  area.setAttribute("fill", "url(#historyArea)");
  area.setAttribute("filter", "url(#historyShadow)");
  svg.appendChild(area);
  svg.appendChild(bars);

  const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
  line.setAttribute("d", path);
  line.setAttribute("fill", "none");
  line.setAttribute("stroke", "url(#historyStroke)");
  line.setAttribute("stroke-width", "6");
  line.setAttribute("stroke-linecap", "round");
  line.setAttribute("stroke-linejoin", "round");
  svg.appendChild(line);

  for (const coord of coords) {
    const halo = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    halo.setAttribute("cx", coord.x);
    halo.setAttribute("cy", coord.y);
    halo.setAttribute("r", "8");
    halo.setAttribute("fill", "#ffffff");
    halo.setAttribute("opacity", "0.86");
    svg.appendChild(halo);

    const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    dot.setAttribute("cx", coord.x);
    dot.setAttribute("cy", coord.y);
    dot.setAttribute("r", "4.8");
    dot.setAttribute("fill", "#216e61");
    dot.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "title")).textContent = `${coord.point.label || coord.point.date}: ${dollars.format(coord.point.value || 0)} total`;
    svg.appendChild(dot);
  }

  const last = points[points.length - 1];
  const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
  label.setAttribute("x", width - padX);
  label.setAttribute("y", padTop - 12);
  label.setAttribute("text-anchor", "end");
  label.setAttribute("fill", "#17211f");
  label.setAttribute("font-weight", "700");
  label.textContent = `${last.label || last.date}: ${dollars.format(last.value || 0)}`;
  svg.appendChild(label);

  const first = points[0];
  const firstLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
  firstLabel.setAttribute("x", padX);
  firstLabel.setAttribute("y", height - 16);
  firstLabel.setAttribute("fill", "#66706d");
  firstLabel.setAttribute("font-size", "12");
  firstLabel.textContent = first.label || first.date;
  svg.appendChild(firstLabel);

  const lastLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
  lastLabel.setAttribute("x", width - padX);
  lastLabel.setAttribute("y", height - 16);
  lastLabel.setAttribute("text-anchor", "end");
  lastLabel.setAttribute("fill", "#66706d");
  lastLabel.setAttribute("font-size", "12");
  lastLabel.textContent = last.label || last.date;
  svg.appendChild(lastLabel);
}

function smoothPath(coords) {
  if (coords.length < 2) {
    const coord = coords[0];
    return coord ? `M ${coord.x.toFixed(2)} ${coord.y.toFixed(2)}` : "";
  }

  return coords.reduce((path, coord, index) => {
    if (index === 0) {
      return `M ${coord.x.toFixed(2)} ${coord.y.toFixed(2)}`;
    }
    const previous = coords[index - 1];
    const controlX = (previous.x + coord.x) / 2;
    return `${path} C ${controlX.toFixed(2)} ${previous.y.toFixed(2)}, ${controlX.toFixed(2)} ${coord.y.toFixed(2)}, ${coord.x.toFixed(2)} ${coord.y.toFixed(2)}`;
  }, "");
}

function cardQuery() {
  const params = new URLSearchParams({
    search: els.searchInput.value.trim(),
    owned: "owned",
    sort: els.sortSelect.value,
    limit: "250",
  });
  return params.toString();
}

function favoriteQuery() {
  const params = new URLSearchParams({
    search: els.favoriteSearchInput.value.trim(),
    owned: "owned",
    favorite: "1",
    sort: els.favoriteSortSelect.value,
    limit: "250",
  });
  return params.toString();
}

function missingQuery() {
  const params = new URLSearchParams({
    search: els.missingSearchInput.value.trim(),
    owned: "missing",
    missing_list: "1",
    sort: els.missingSortSelect.value,
    limit: "5000",
  });
  return params.toString();
}

function wishlistQuery() {
  const params = new URLSearchParams({
    search: els.wishlistSearchInput.value.trim(),
    owned: "missing",
    wishlist: "1",
    sort: els.wishlistSortSelect.value,
    limit: "5000",
  });
  return params.toString();
}

function saleQuery() {
  const params = new URLSearchParams({
    search: els.saleSearchInput.value.trim(),
    sort: els.saleSortSelect.value,
    limit: "5000",
  });
  return params.toString();
}

function storeFrontQuery() {
  const params = new URLSearchParams({
    search: els.storeFrontSearchInput.value.trim(),
    sort: els.storeFrontSortSelect.value,
    limit: "5000",
  });
  return params.toString();
}

async function loadCards() {
  const data = await api(`/api/cards?${cardQuery()}`);
  state.cards = data.cards || [];
  renderCollection();
}

async function loadOwnedSets() {
  const [cardData, setData] = await Promise.all([
    api(`/api/cards?${new URLSearchParams({
      owned: "owned",
      sort: "set",
      limit: "5000",
    }).toString()}`),
    api("/api/sets"),
  ]);
  state.ownedSetCards = cardData.cards || [];
  state.ownedSets = ownedSetGroups(state.ownedSetCards, setData.sets || []);
  renderOwnedSets();
}

async function loadFavorites() {
  const [cardData, deckData, storeData] = await Promise.all([
    api(`/api/cards?${favoriteQuery()}`),
    api("/api/favorite-decks"),
    api("/api/favorite-store-listings"),
  ]);
  state.favoriteCards = cardData.cards || [];
  state.favoriteDecks = deckData.decks || [];
  state.favoriteStores = storeData.listings || [];
  renderFavorites();
}

async function loadMissingList() {
  const data = await api(`/api/cards?${missingQuery()}`);
  state.missingCards = data.cards || [];
  renderMissingList();
}

async function loadWishlist() {
  if (!state.activeWishlist) {
    await loadWishlists();
    return;
  }
  const data = await api(`/api/wishlists/${encodeURIComponent(state.activeWishlist.id)}?${wishlistQuery()}`);
  state.activeWishlist = data;
  state.wishlistCards = data.cards || [];
  renderWishlist();
}

async function loadWishlists() {
  const data = await api("/api/wishlists");
  state.wishlists = data.wishlists || [];
  renderWishlists();
  return state.wishlists;
}

function updateNotificationsDot() {
  const unread = Number(state.unreadNotificationCount || 0);
  if (els.notificationsNavDot) {
    els.notificationsNavDot.hidden = unread <= 0;
    els.notificationsNavDot.title = unread > 0 ? `${integer.format(unread)} unread notification${unread === 1 ? "" : "s"}` : "";
  }
}

async function loadNotifications() {
  const data = await api("/api/notifications");
  state.notifications = data.notifications || [];
  state.unreadNotificationCount = Number(data.unread_count || 0);
  updateNotificationsDot();
  renderNotifications();
  return state.notifications;
}

async function loadNotificationSummary() {
  if (!state.user) {
    state.unreadNotificationCount = 0;
    updateNotificationsDot();
    return;
  }
  const data = await api("/api/notifications?limit=1", { promptLogin: false });
  state.unreadNotificationCount = Number(data.unread_count || 0);
  updateNotificationsDot();
}

function scryfallQuoted(value) {
  return `"${String(value || "").replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

function buildCatalogSearchQuery() {
  const parts = [];
  const text = els.catalogSearchInput.value.trim();
  const oracle = els.catalogOracleInput.value.trim();
  const setCode = els.catalogSetInput.value.trim().toLowerCase();
  const color = els.catalogColorSelect.value;
  const type = els.catalogTypeSelect.value;
  const rarity = els.catalogRaritySelect.value;
  const format = els.catalogFormatSelect.value;
  if (text) parts.push(text);
  if (oracle) parts.push(`o:${scryfallQuoted(oracle)}`);
  if (setCode) parts.push(`e:${setCode}`);
  if (color === "multi") parts.push("c>=2");
  else if (color === "colorless") parts.push("c:c");
  else if (color) parts.push(`c:${color}`);
  if (type) parts.push(`t:${type}`);
  if (rarity) parts.push(`r:${rarity}`);
  if (format) parts.push(`legal:${format}`);
  return parts.join(" ").trim();
}

function applyCatalogOwnedFilter() {
  const allResults = state.catalogSearchAllResults || [];
  const hideOwned = Boolean(els.catalogHideOwnedFilter?.checked);
  state.catalogSearchResults = hideOwned
    ? allResults.filter((card) => Number(card.owned_quantity || 0) <= 0)
    : [...allResults];
  return {
    total: allResults.length,
    visible: state.catalogSearchResults.length,
    hiddenOwned: allResults.length - state.catalogSearchResults.length,
    hideOwned,
  };
}

function catalogSearchStatusText(stats) {
  const resultText = `${integer.format(stats.visible)} result${stats.visible === 1 ? "" : "s"}`;
  if (stats.hideOwned && stats.hiddenOwned > 0) {
    return `${resultText} - ${integer.format(stats.hiddenOwned)} owned hidden`;
  }
  return resultText;
}

async function searchCatalog() {
  const query = buildCatalogSearchQuery();
  if (query.length < 2) {
    els.catalogSearchStatus.textContent = "Enter a card search or choose at least one filter.";
    return;
  }
  els.catalogSearchButton.disabled = true;
  els.catalogSearchStatus.textContent = "Searching Scryfall...";
  try {
    const language = (state.settings && state.settings.language) || "en";
    const order = els.catalogSortSelect.value || "released";
    const result = await api(`/api/scryfall/search?q=${encodeURIComponent(query)}&lang=${encodeURIComponent(language)}&order=${encodeURIComponent(order)}`);
    state.catalogSearchAllResults = result.cards || [];
    const stats = applyCatalogOwnedFilter();
    renderCatalogSearchResults();
    els.catalogSearchStatus.textContent = catalogSearchStatusText(stats);
  } catch (error) {
    els.catalogSearchStatus.textContent = error.message;
  } finally {
    els.catalogSearchButton.disabled = false;
  }
}

async function loadSaleCards() {
  const data = await api(`/api/cards/for-sale?${saleQuery()}`);
  state.saleCards = data.cards || [];
  renderSaleList();
}

async function loadStoreFront() {
  const data = await api(`/api/store-front?${storeFrontQuery()}`, { promptLogin: false });
  state.storeFrontCards = data.cards || [];
  renderStoreFront();
}

function renderCollection() {
  els.cardsGrid.className = state.collectionView === "list" ? "cards-list" : "cards-grid";
  els.tileViewButton.classList.toggle("is-active", state.collectionView === "tiles");
  els.listViewButton.classList.toggle("is-active", state.collectionView === "list");
  const options = { selectable: true, hideWishlist: true };
  if (state.collectionView === "list") {
    renderCardList(state.cards, els.cardsGrid, options);
  } else {
    renderCards(state.cards, els.cardsGrid, options);
  }
}

function setGroupKey(card) {
  return (card.set_code || card.set || card.set_name || "unknown").toString().trim().toLowerCase() || "unknown";
}

function ownedSetGroups(cards, completionSets = []) {
  const completionByCode = new Map((completionSets || []).map((set) => [String(set.set_code || "").toLowerCase(), set]));
  const groups = new Map();
  for (const card of groupedCardsForDisplay(cards || [])) {
    const quantity = Number(card.quantity || 0);
    if (quantity <= 0) continue;
    const key = setGroupKey(card);
    const group = groups.get(key) || {
      key,
      set_code: (card.set_code || card.set || key).toString().toLowerCase(),
      set_name: card.set_name || (card.set_code || key).toString().toUpperCase(),
      cards: [],
      unique_count: 0,
      quantity: 0,
      value: 0,
      preview_images: [],
    };
    group.cards.push(card);
    group.unique_count += 1;
    group.quantity += quantity;
    group.value += Number(card.owned_value || card.total_value || 0);
    if (card.image_normal || card.image_small) {
      group.preview_images.push(card.image_normal || card.image_small);
    }
    groups.set(key, group);
  }
  return Array.from(groups.values())
    .map((group) => {
      const completion = completionByCode.get(String(group.set_code || group.key).toLowerCase()) || {};
      const totalCards = Number(completion.total_cards || 0);
      const ownedUnique = Number(completion.owned_cards || group.unique_count || 0);
      const completionPercent = totalCards > 0 ? (ownedUnique / totalCards) * 100 : null;
      return {
        ...group,
        set_name: completion.set_name || group.set_name,
        total_cards: totalCards,
        owned_cards: ownedUnique,
        completion_percent: completionPercent,
        preview_images: Array.from(new Set(group.preview_images)).slice(0, 5),
        cards: group.cards.sort(compareCardsBySetOrder),
      };
    })
    .sort((a, b) => a.set_name.localeCompare(b.set_name));
}

function setCompletionLabel(set) {
  const percent = set.completion_percent;
  return percent !== null && percent !== undefined && Number.isFinite(Number(percent)) ? `${Number(percent).toFixed(1)}%` : "Unknown";
}

function setCompletionMetaText(set) {
  const uniqueText = Number(set.total_cards || 0) > 0
    ? `${integer.format(set.owned_cards || set.unique_count || 0)} / ${integer.format(set.total_cards || 0)} unique`
    : `${integer.format(set.unique_count || 0)} unique owned`;
  return `${uniqueText} - ${integer.format(set.quantity || 0)} cards - ${dollars.format(set.value || 0)}`;
}

function compareCardsBySetOrder(a, b) {
  const numberA = Number.parseFloat(a.collector_number);
  const numberB = Number.parseFloat(b.collector_number);
  if (Number.isFinite(numberA) && Number.isFinite(numberB) && numberA !== numberB) {
    return numberA - numberB;
  }
  return String(a.collector_number || "").localeCompare(String(b.collector_number || ""), undefined, { numeric: true })
    || cardTitle(a).localeCompare(cardTitle(b));
}

function renderOwnedSets() {
  if (!els.setsGrid || !els.setsOverviewShell || !els.setsDetailShell) return;
  state.activeOwnedSet = null;
  els.setsOverviewShell.hidden = false;
  els.setsDetailShell.hidden = true;
  els.setsDetailShell.innerHTML = "";
  els.setsGrid.innerHTML = "";
  const sets = state.ownedSets || [];
  if (els.setsStatus) {
    els.setsStatus.textContent = `${integer.format(sets.length)} owned set${sets.length === 1 ? "" : "s"}`;
  }
  if (!sets.length) {
    els.setsGrid.innerHTML = '<div class="empty-state">No owned sets yet.</div>';
    return;
  }
  for (const set of sets) {
    const item = document.createElement("button");
    const previewImages = Array.from(new Set(set.preview_images || [])).slice(0, 5);
    item.className = `deck-card set-card${previewImages.length ? " has-deck-preview" : ""}`;
    item.type = "button";
    item.dataset.setKey = set.key;
    item.setAttribute("aria-label", `Open ${set.set_name}`);
    item.innerHTML = `
      ${deckPreviewImagesHtml(previewImages)}
      <div>
        <p class="eyebrow">${escapeHtml((set.set_code || "").toUpperCase())}</p>
        <h3>${escapeHtml(set.set_name)}</h3>
      </div>
      <strong>${escapeHtml(setCompletionLabel(set))}</strong>
      <span>${escapeHtml(setCompletionMetaText(set))}</span>
      ${Number(set.total_cards || 0) > 0 ? `
        <div class="set-card-progress" aria-label="${escapeHtml(setCompletionLabel(set))} complete">
          <span style="width: ${Math.max(0, Math.min(100, Number(set.completion_percent || 0)))}%"></span>
        </div>
      ` : ""}
    `;
    item.addEventListener("click", () => openOwnedSet(set.key));
    els.setsGrid.appendChild(item);
  }
}

function openOwnedSet(setKey) {
  const set = (state.ownedSets || []).find((item) => item.key === setKey);
  if (!set || !els.setsOverviewShell || !els.setsDetailShell) return;
  state.activeOwnedSet = set;
  els.setsOverviewShell.hidden = true;
  els.setsDetailShell.hidden = false;
  renderOwnedSetDetail(set);
}

function closeOwnedSetDetail() {
  state.activeOwnedSet = null;
  if (els.setsOverviewShell) els.setsOverviewShell.hidden = false;
  if (els.setsDetailShell) {
    els.setsDetailShell.hidden = true;
    els.setsDetailShell.innerHTML = "";
  }
}

function renderOwnedSetDetail(set) {
  if (!els.setsDetailShell) return;
  els.setsDetailShell.innerHTML = `
    <div class="section-head set-detail-head">
      <div>
        <p class="eyebrow">${escapeHtml((set.set_code || "").toUpperCase())}</p>
        <h2>${escapeHtml(set.set_name)}</h2>
        <span>${escapeHtml(setCompletionLabel(set))} complete - ${escapeHtml(setCompletionMetaText(set))}</span>
      </div>
      <div class="set-detail-actions">
        <button id="emailSetButton" class="share-button" type="button" aria-label="Email set" title="Email set"><span class="send-icon" aria-hidden="true"></span></button>
        <button id="shareSetButton" class="share-button" type="button" aria-label="Share set" title="Share set">&#8599;</button>
        <button id="addMissingSetWishlistButton" class="share-button set-missing-wishlist-button" type="button" aria-label="Add missing cards to wishlist" title="Add Missing Cards to Wishlist"><span class="wishlist-icon" aria-hidden="true"></span></button>
        <button id="backToSetsButton" class="secondary-button" type="button">Back to Sets</button>
      </div>
    </div>
    <div id="ownedSetCardsGrid" class="cards-grid set-cards-grid"></div>
  `;
  els.setsDetailShell.querySelector("#backToSetsButton").addEventListener("click", closeOwnedSetDetail);
  els.setsDetailShell.querySelector("#shareSetButton").addEventListener("click", () => openSetShareModal(set));
  els.setsDetailShell.querySelector("#emailSetButton").addEventListener("click", () => openEmailSetModal(set));
  els.setsDetailShell.querySelector("#addMissingSetWishlistButton").addEventListener("click", (event) => {
    addOwnedSetMissingToWishlist(set, event.currentTarget).catch((error) => setStatus(error.message, "error", els.setsStatus));
  });
  renderCards(set.cards || [], els.setsDetailShell.querySelector("#ownedSetCardsGrid"), { hideWishlist: true });
}

async function addOwnedSetMissingToWishlist(set, button) {
  if (!set?.set_code) return;
  const confirmed = window.confirm(`Create "${set.set_name} Missing List" wishlist and add every missing card from this set?`);
  if (!confirmed) return;
  const originalTitle = button.title;
  button.disabled = true;
  button.title = "Creating wishlist...";
  try {
    const result = await api(`/api/sets/${encodeURIComponent(set.set_code)}/missing-wishlist`, {
      method: "POST",
      body: "{}",
    });
    const wishlist = result.wishlist || {};
    setStatus(`Created ${wishlist.name || "wishlist"} with ${integer.format(result.added || 0)} missing card${Number(result.added || 0) === 1 ? "" : "s"}.`, "success", els.setsStatus);
    await loadWishlists();
    await refresh();
  } finally {
    button.disabled = false;
    button.title = originalTitle;
  }
}

function renderFavorites() {
  els.favoritesGrid.className = state.favoritesView === "list" ? "cards-list" : "cards-grid";
  els.favoriteTileViewButton.classList.toggle("is-active", state.favoritesView === "tiles");
  els.favoriteListViewButton.classList.toggle("is-active", state.favoritesView === "list");
  for (const button of els.favoriteFilterButtons || []) {
    button.classList.toggle("is-active", button.dataset.favoritesFilter === state.favoritesFilter);
  }
  const options = {
    selectable: true,
    hideWishlist: true,
    confirmUnfavorite: true,
    statusTarget: els.favoritesStatus,
    afterFavoriteChange: async () => {
      await loadFavorites();
      await refresh();
    },
  };
  const container = document.createElement("div");
  container.className = "favorites-mixed-shell";
  const showCards = state.favoritesFilter === "all" || state.favoritesFilter === "cards";
  const showDecks = state.favoritesFilter === "all" || state.favoritesFilter === "decks";
  const showStore = state.favoritesFilter === "all" || state.favoritesFilter === "store";
  const cardsShell = document.createElement("div");
  cardsShell.className = state.favoritesView === "list" ? "cards-list favorites-card-list" : "cards-grid favorites-card-grid";
  if (state.favoritesView === "list") {
    renderCardList(state.favoriteCards, cardsShell, options);
  } else {
    renderCards(state.favoriteCards, cardsShell, options);
  }
  const decksShell = renderFavoriteDecks();
  const storeShell = renderFavoriteStoreListings();
  els.favoritesGrid.innerHTML = "";
  if (showDecks && state.favoriteDecks.length) container.appendChild(decksShell);
  if (showStore && state.favoriteStores.length) container.appendChild(storeShell);
  if (showCards && state.favoriteCards.length) container.appendChild(cardsShell);
  if (
    (!showDecks || !state.favoriteDecks.length)
    && (!showStore || !state.favoriteStores.length)
    && (!showCards || !state.favoriteCards.length)
  ) {
    container.innerHTML = '<div class="empty-state">No favorites yet.</div>';
  }
  els.favoritesGrid.appendChild(container);
}

function renderFavoriteDecks() {
  const section = document.createElement("section");
  section.className = "favorite-decks-section";
  section.innerHTML = `
    <div class="favorite-section-head">
      <span class="deck-icon" aria-hidden="true"></span>
      <strong>Decks</strong>
    </div>
    <div class="favorite-decks-grid"></div>
  `;
  const grid = section.querySelector(".favorite-decks-grid");
  for (const deck of state.favoriteDecks) {
    const item = document.createElement("article");
    item.className = "deck-card favorite-deck-card";
    item.innerHTML = `
      <button class="wishlist-open-button favorite-deck-open" type="button" aria-label="Open ${escapeHtml(deck.name || "deck")}">
        <p class="eyebrow">Favorited deck</p>
        <h3><span class="deck-icon" aria-hidden="true"></span><span>${escapeHtml(deck.name || "Deck")}</span></h3>
      </button>
      <strong>${integer.format(deck.card_count || 0)}</strong>
      <span>${displayNameHtml(deck.owner_name || "Arcane Ledger user", { is_pro: deck.owner_is_pro, role: deck.owner_role })}</span>
      <div class="wishlist-card-actions">
        <button class="share-button favorite-deck-unfavorite" type="button" aria-label="Remove favorite deck" title="Remove favorite">☆</button>
        <a class="share-button" href="${escapeHtml(deck.deck_url || `/decks/${encodeURIComponent(deck.share_id || "")}`)}" target="_blank" rel="noreferrer" aria-label="Open deck" title="Open deck">&#8599;</a>
      </div>
    `;
    item.querySelector(".favorite-deck-open").addEventListener("click", () => {
      const url = deck.deck_url || `/decks/${encodeURIComponent(deck.share_id || "")}`;
      window.open(url, "_blank", "noopener,noreferrer");
    });
    item.querySelector(".favorite-deck-unfavorite").addEventListener("click", async () => {
      try {
        await api(`/api/shared-decks/${encodeURIComponent(deck.share_id)}/favorite`, {
          method: "POST",
          body: JSON.stringify({ favorite: false }),
          promptLogin: true,
        });
        setStatus("Deck removed from favorites.", "success", els.favoritesStatus);
        await loadFavorites();
        await refresh();
      } catch (error) {
        setStatus(error.message, "error", els.favoritesStatus);
      }
    });
    grid.appendChild(item);
  }
  return section;
}

function renderFavoriteStoreListings() {
  const section = document.createElement("section");
  section.className = "favorite-decks-section favorite-store-section";
  section.innerHTML = `
    <div class="favorite-section-head">
      <span class="storefront-icon" aria-hidden="true"></span>
      <strong>Store</strong>
    </div>
    <div class="favorite-store-list"></div>
  `;
  const list = section.querySelector(".favorite-store-list");
  for (const listing of state.favoriteStores) {
    const row = document.createElement("article");
    row.className = "deck-card-row favorite-store-row";
    row.innerHTML = `
      <img src="${escapeHtml(listing.image_small || listing.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(listing))}</strong>
        <span>${displayNameHtml(listing.seller_name || "Seller", { is_pro: listing.seller_is_pro, role: listing.seller_role })} - ${escapeHtml(listing.variant || "Normal")} - ${escapeHtml(listing.card_condition || "Near Mint")}</span>
        <div class="deck-card-tags">
          <span>${integer.format(listing.sale_quantity || listing.quantity || 0)} for sale</span>
          <span>${dollars.format(listing.asking_price || 0)} ask</span>
          <span>${dollars.format(listing.display_price || 0)} market</span>
        </div>
      </div>
      <div class="wishlist-card-actions">
        <button class="share-button favorite-store-remove" type="button" aria-label="Remove store favorite" title="Remove favorite">☆</button>
        <a class="share-button" href="${escapeHtml(listing.store_url || "#")}" target="_blank" rel="noreferrer" aria-label="Open seller store" title="Open seller store">&#8599;</a>
      </div>
    `;
    row.addEventListener("click", (event) => {
      if (event.target.closest("button, a")) return;
      if (listing.store_url) window.open(listing.store_url, "_blank", "noopener,noreferrer");
    });
    row.querySelector(".favorite-store-remove").addEventListener("click", async () => {
      const confirmed = window.confirm(`Remove ${cardTitle(listing)} from Store favorites?`);
      if (!confirmed) return;
      await toggleStoreFavoriteListing(listing, false, { statusTarget: els.favoritesStatus });
      await loadFavorites();
      await refresh();
    });
    list.appendChild(row);
  }
  return section;
}

function renderWishlist() {
  els.wishlistGrid.className = "missing-list-grid wishlist-detail-grid";
  els.wishlistGrid.innerHTML = "";
  if (!state.wishlistCards.length) {
    els.wishlistGrid.innerHTML = '<div class="empty-state">No cards are on this Wishlist yet.</div>';
    return;
  }
  for (const card of state.wishlistCards) {
    const row = document.createElement("article");
    row.className = `missing-card-row wishlist-card-row ${card.fulfilled ? "is-fulfilled" : ""}`;
    row.innerHTML = `
      <a class="missing-card-art" href="${escapeHtml(cardDetailUrl(card))}">
        <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="${escapeHtml(cardTitle(card))}">
      </a>
      <div class="missing-card-main">
        <div class="missing-card-title-row">
          <div>
            <h3>${escapeHtml(cardTitle(card))}</h3>
            <p>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")}${cardRulesName(card) ? ` - Rules: ${escapeHtml(cardRulesName(card))}` : ""}</p>
          </div>
          <div class="missing-card-pills">
            <span>${escapeHtml(card.rarity || "unknown")}</span>
            <span>${escapeHtml(cardTypeLabel(card))}</span>
            <span>${escapeHtml(cardColorLabel(card))}</span>
            <span>Market ${dollars.format(card.display_price || 0)}</span>
            <span>Need ${integer.format(card.wishlist_quantity || 1)}</span>
            ${card.fulfilled ? "<span>Owned</span>" : ""}
          </div>
        </div>
        <div class="missing-market-links">
          ${marketplaceLinksHtml(card)}
        </div>
      </div>
      <div class="missing-row-actions">
        <button class="remove-missing-button" type="button" aria-label="Remove from Wishlist" title="Remove from Wishlist">
          <span class="remove-list-icon" aria-hidden="true"></span>
        </button>
      </div>
    `;
    row.querySelector(".remove-missing-button").addEventListener("click", () => {
      removeFromActiveWishlist(card).catch((error) => setStatus(error.message, "error", els.wishlistStatus));
    });
    els.wishlistGrid.appendChild(row);
  }
}

function renderWishlists() {
  els.wishlistsGrid.innerHTML = "";
  if (!state.wishlists.length) {
    els.wishlistsGrid.innerHTML = '<div class="empty-state">No wishlists yet.</div>';
    return;
  }
  for (const wishlist of state.wishlists) {
    const item = document.createElement("article");
    item.className = "deck-card wishlist-list-card";
    item.dataset.wishlistId = wishlist.id;
    item.innerHTML = `
      <button class="wishlist-open-button" type="button" aria-label="Open ${escapeHtml(wishlist.name)}">
        <p class="eyebrow">Wishlist</p>
        <h3><span class="wishlist-icon" aria-hidden="true"></span><span>${escapeHtml(wishlist.name)}</span></h3>
      </button>
      <strong>${integer.format(wishlist.item_count || 0)}</strong>
      <span>${integer.format(wishlist.unique_card_count || 0)} unique cards saved</span>
      <div class="wishlist-card-actions">
        <button class="share-button wishlist-share-button" type="button" aria-label="Share ${escapeHtml(wishlist.name)}" title="Share wishlist">&#8599;</button>
        <button class="share-button wishlist-email-button" type="button" aria-label="Email ${escapeHtml(wishlist.name)}" title="Email wishlist"><span class="send-icon" aria-hidden="true"></span></button>
      </div>
    `;
    item.querySelector(".wishlist-open-button").addEventListener("click", () => {
      openWishlistDetailModal(wishlist.id).catch((error) => {
        els.wishlistStatus.textContent = error.message;
      });
    });
    item.querySelector(".wishlist-share-button").addEventListener("click", () => openWishlistShareModal(wishlist));
    item.querySelector(".wishlist-email-button").addEventListener("click", () => openEmailWishlistModal(wishlist));
    els.wishlistsGrid.appendChild(item);
  }
}

async function openWishlistDetailModal(wishlistId) {
  const data = await api(`/api/wishlists/${encodeURIComponent(wishlistId)}?${wishlistQuery()}`);
  state.activeWishlist = data;
  state.wishlistCards = data.cards || [];
  els.wishlistDetailTitle.textContent = data.name || "Wishlist";
  renderWishlist();
  els.wishlistDetailOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeWishlistDetailModal() {
  els.wishlistDetailOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.activeWishlist = null;
  state.wishlistCards = [];
  els.wishlistGrid.innerHTML = "";
  els.wishlistSearchInput.value = "";
}

async function removeFromActiveWishlist(card) {
  if (!state.activeWishlist) return;
  const confirmed = window.confirm(`Remove ${cardTitle(card)} from "${state.activeWishlist.name || "Wishlist"}"?`);
  if (!confirmed) return;
  await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/wishlist`, {
    method: "POST",
    body: JSON.stringify({
      variant: card.variant || "Normal",
      wishlist_id: state.activeWishlist.id,
      wishlist: false,
    }),
  });
  setStatus(`Removed ${cardTitle(card)} from Wishlist.`, "success", els.wishlistStatus);
  await loadWishlist();
  await loadWishlists();
  await refresh();
}

function openAddWishlistModal() {
  els.addWishlistForm.reset();
  els.addWishlistOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.addWishlistForm.querySelector('[name="name"]').focus();
}

function closeAddWishlistModal() {
  els.addWishlistOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.addWishlistForm.reset();
}

async function openAssignWishlistModal(card, options = {}) {
  if (!state.user) {
    openAuthModal("register", "Create an account or log in before saving cards to your Wishlist.");
    return;
  }
  const wishlists = await loadWishlists();
  const select = els.assignWishlistForm.wishlist_id;
  select.innerHTML = "";
  if (!wishlists.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "Create a wishlist first";
    select.appendChild(option);
  } else {
    for (const wishlist of wishlists) {
      const option = document.createElement("option");
      option.value = wishlist.id;
      option.textContent = `${wishlist.name} (${integer.format(wishlist.item_count || 0)})`;
      select.appendChild(option);
    }
  }
  state.pendingWishlistCard = card;
  state.pendingWishlistOptions = options;
  els.assignWishlistPreview.innerHTML = `
    <article class="assign-wishlist-card">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")}</span>
      </div>
    </article>
  `;
  els.assignWishlistOverlay.hidden = false;
  document.body.classList.add("modal-open");
  select.focus();
}

function closeAssignWishlistModal() {
  els.assignWishlistOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.assignWishlistForm.reset();
  els.assignWishlistPreview.innerHTML = "";
  state.pendingWishlistCard = null;
  state.pendingWishlistOptions = null;
}

function shareUrlForEntity(type, entity) {
  if (type === "card") return shareUrlForCard(entity);
  if (type === "deck" || type === "shared-deck") return shareUrlForDeck(entity);
  if (type === "container") return shareUrlForContainer(entity);
  if (type === "set") return shareUrlForSet(entity);
  if (type === "favorites") return shareUrlForFavorites();
  return shareUrlForWishlist(entity);
}

function emailEntityLabel(type) {
  if (type === "card") return "Card";
  if (type === "deck" || type === "shared-deck") return "Deck";
  if (type === "container") return "Container";
  if (type === "set") return "Set";
  if (type === "favorites") return "Favorites";
  return "Wishlist";
}

function openEmailShareModal(type, entity) {
  state.emailingEntity = { type, entity };
  state.emailingWishlist = type === "wishlist" ? entity : null;
  els.emailWishlistForm.reset();
  els.emailWishlistForm.entity_type.value = type;
  els.emailWishlistForm.entity_id.value = type === "favorites"
    ? (entity.share_id || "")
    : type === "shared-deck"
    ? (entity.share_id || "")
    : (entity.id || entity.set_code || entity.scryfall_id || entity.card_id || "");
  const label = emailEntityLabel(type);
  els.emailWishlistTitle.textContent = `Email ${entity.name || label}`;
  els.emailWishlistStatus.textContent = shareUrlForEntity(type, entity);
  els.emailWishlistStatus.dataset.tone = "";
  els.emailWishlistOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.emailWishlistForm.email.focus();
}

function openEmailWishlistModal(wishlist) {
  openEmailShareModal("wishlist", wishlist);
}

function openEmailDeckModal(deck) {
  openEmailShareModal("deck", deck);
}

function openEmailContainerModal(container) {
  openEmailShareModal("container", container);
}

function openEmailCardModal(card) {
  openEmailShareModal("card", card);
}

function openEmailSetModal(set) {
  openEmailShareModal("set", set);
}

function openEmailFavoritesModal() {
  const shareId = state.user?.store_share_id || "";
  if (!shareId) {
    setStatus("Your account does not have a favorites share link yet. Refresh and try again.", "error", els.favoritesStatus);
    return;
  }
  openEmailShareModal("favorites", { name: "Favorites", share_id: shareId });
}

function closeEmailWishlistModal() {
  els.emailWishlistOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.emailWishlistForm.reset();
  els.emailWishlistStatus.textContent = "";
  els.emailWishlistStatus.dataset.tone = "";
  state.emailingWishlist = null;
  state.emailingEntity = null;
}

async function deleteActiveWishlist() {
  if (!state.activeWishlist) return;
  const confirmed = window.confirm(`Delete wishlist "${state.activeWishlist.name}"? This only removes the wishlist metadata.`);
  if (!confirmed) return;
  const wishlistName = state.activeWishlist.name;
  await api(`/api/wishlists/${encodeURIComponent(state.activeWishlist.id)}`, { method: "DELETE" });
  closeWishlistDetailModal();
  els.wishlistStatus.textContent = `Deleted ${wishlistName}.`;
  await loadWishlists();
  await refresh();
}

function renderCatalogHeroCards(cards = []) {
  if (!els.catalogHeroCards) return;
  els.catalogHeroCards.innerHTML = "";
  if (!cards.length) {
    els.catalogHeroCards.innerHTML = '<div class="catalog-hero-card-placeholder">Search. Collect. Track.</div>';
    return;
  }
  const tilts = [-8, 5, -3, 7, -5];
  for (const [index, card] of cards.slice(0, 5).entries()) {
    const link = document.createElement("a");
    link.className = "catalog-hero-card-link";
    link.href = cardDetailUrl(card);
    link.title = cardTitle(card);
    link.style.setProperty("--tilt", `${tilts[index % tilts.length]}deg`);
    link.innerHTML = `<img src="${escapeHtml(card.image_normal || card.image_small || "")}" alt="${escapeHtml(cardTitle(card))}">`;
    els.catalogHeroCards.appendChild(link);
  }
}

async function loadCatalogHeroCards() {
  if (state.catalogHeroLoaded) {
    renderCatalogHeroCards(state.catalogHeroCards);
    return;
  }
  state.catalogHeroLoaded = true;
  try {
    const result = await api("/api/search/hero-cards", { promptLogin: false });
    state.catalogHeroCards = result.cards || [];
  } catch {
    state.catalogHeroCards = [];
  }
  renderCatalogHeroCards(state.catalogHeroCards);
}

function renderCatalogSearchResults() {
  els.catalogSearchGrid.innerHTML = "";
  if (!state.catalogSearchResults.length) {
    const ownedHidden = Boolean(els.catalogHideOwnedFilter?.checked) && (state.catalogSearchAllResults || []).length > 0;
    els.catalogSearchGrid.innerHTML = ownedHidden
      ? '<div class="empty-state">All matching results are already in your collection.</div>'
      : '<div class="empty-state">Search Scryfall to add cards to Wishlist or Collection.</div>';
    return;
  }
  for (const card of state.catalogSearchResults) {
    const owned = Number(card.owned_quantity || 0) > 0;
    const item = document.createElement("article");
    item.className = "catalog-result-card";
    item.classList.toggle("is-owned", owned);
    item.classList.toggle("is-special", cardHasSpecialVariant(card));
    item.innerHTML = `
      <a class="catalog-result-art" href="${escapeHtml(cardDetailUrl(card))}" title="Open card details">
        <img src="${escapeHtml(card.image_normal || card.image_small || "")}" alt="${escapeHtml(cardTitle(card))}">
      </a>
      <div class="catalog-result-copy">
        <h3>${escapeHtml(cardTitle(card))}</h3>
        <p>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.rarity || "unknown")}</p>
        <p>${escapeHtml(card.type_line || "")}</p>
        ${owned ? variantSummaryHtml(card) : ""}
        <div class="catalog-result-pills">
          <span>${escapeHtml(cardTypeLabel(card))}</span>
          <span>${escapeHtml(cardColorLabel(card))}</span>
          <span>${dollars.format(priceForVariant(card, "Normal"))}</span>
          <span>Owned ${integer.format(card.owned_quantity || 0)}</span>
        </div>
      </div>
      <div class="catalog-result-actions">
        <a class="scryfall-button catalog-scryfall-button" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" aria-label="Open on Scryfall" title="Open on Scryfall">S</a>
        <button class="wishlist-button ${card.wishlist ? "is-wishlist" : ""}" type="button" aria-label="${card.wishlist ? "Remove from Wishlist" : "Add to Wishlist"}" title="${owned ? "Owned cards are not available for Wishlist" : card.wishlist ? "Remove from Wishlist" : "Add to Wishlist"}" ${owned ? "disabled" : ""}></button>
        <button class="primary-button catalog-add-button" type="button">Add to Collection</button>
      </div>
    `;
    item.addEventListener("click", (event) => {
      if (event.target.closest("a, button, input, select, textarea")) return;
      window.location.href = cardDetailUrl(card);
    });
    const wishlistButton = item.querySelector(".wishlist-button");
    wishlistButton.addEventListener("click", async () => {
      if (owned) return;
      if (!state.user) {
        openAuthModal("register", "Create an account or log in before saving cards to your Wishlist.");
        return;
      }
      try {
        await openAssignWishlistModal(card, {
          statusTarget: els.catalogSearchStatus,
          afterWishlistChange: async () => {
            card.wishlist = 1;
            renderCatalogSearchResults();
            await loadWishlists();
            await refresh();
          },
        });
      } catch (error) {
        setStatus(error.message, "error", els.catalogSearchStatus);
      }
    });
    item.querySelector(".catalog-add-button").addEventListener("click", () => {
      if (!state.user) {
        openAuthModal("register", "Create an account or log in before adding cards to your Collection.");
        return;
      }
      openAddCardModal(card);
    });
    els.catalogSearchGrid.appendChild(item);
  }
}

function renderMissingList() {
  els.missingGrid.className = "missing-list-grid";
  els.missingGrid.innerHTML = "";
  if (!state.missingCards.length) {
    els.missingGrid.innerHTML = '<div class="empty-state">No cards are on your Missing List yet.</div>';
    return;
  }
  for (const card of state.missingCards) {
    const row = document.createElement("article");
    row.className = "missing-card-row";
    row.innerHTML = `
      <a class="missing-card-art" href="${escapeHtml(cardDetailUrl(card))}">
        <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="${escapeHtml(cardTitle(card))}">
      </a>
      <div class="missing-card-main">
        <div class="missing-card-title-row">
          <div>
            <h3>${escapeHtml(cardTitle(card))}</h3>
            <p>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")}${cardRulesName(card) ? ` - Rules: ${escapeHtml(cardRulesName(card))}` : ""}</p>
          </div>
          <div class="missing-card-pills">
            <span>${escapeHtml(card.rarity || "unknown")}</span>
            <span>${escapeHtml(cardTypeLabel(card))}</span>
            <span>${escapeHtml(cardColorLabel(card))}</span>
          </div>
        </div>
        <div class="missing-market-links">
          ${marketplaceLinksHtml(card)}
        </div>
      </div>
      <div class="missing-row-actions">
        <button class="wishlist-button" type="button" aria-label="Wishlist card" title="Wishlist"></button>
        <button class="remove-missing-button" type="button" aria-label="Remove from Missing List" title="Remove from Missing List">
          <span class="remove-list-icon" aria-hidden="true"></span>
        </button>
      </div>
    `;
    wireWishlistButton(row.querySelector(".wishlist-button"), card, {
      statusTarget: els.missingStatus,
      afterWishlistChange: async () => {
        await loadMissingList();
        await loadWishlist();
      },
    });
    row.querySelector(".remove-missing-button").addEventListener("click", () => {
      removeFromMissingList(card).catch((error) => setStatus(error.message, "error", els.missingStatus));
    });
    els.missingGrid.appendChild(row);
  }
}

function marketplaceSearchQuery(card) {
  const parts = [
    cardTitle(card),
    cardRulesName(card),
    card.set_name,
    card.collector_number ? `#${card.collector_number}` : "",
  ].filter(Boolean);
  return parts.join(" ");
}

function marketplaceLinks(card) {
  const query = marketplaceSearchQuery(card);
  const encoded = encodeURIComponent(query);
  return [
    ["eBay", `https://www.ebay.com/sch/i.html?_nkw=${encoded}`],
    ["TCGplayer", `https://www.tcgplayer.com/search/magic/product?productLineName=magic&q=${encoded}&view=grid`],
    ["Cardmarket", `https://www.cardmarket.com/en/Magic/Products/Search?searchString=${encoded}`],
    ["Cardhoarder", `https://www.cardhoarder.com/cards?data%5Bsearch%5D=${encoded}`],
  ];
}

function marketplaceLinksHtml(card) {
  return marketplaceLinks(card).map(([label, url]) => `
    <a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>
  `).join("");
}

async function removeFromMissingList(card) {
  const confirmed = window.confirm(`Remove ${cardTitle(card)} from your Missing List?`);
  if (!confirmed) return;
  const result = await api("/api/cards/missing-list", {
    method: "POST",
    body: JSON.stringify({
      missing_list: false,
      cards: [{
        card_id: card.scryfall_id,
        variant: card.variant || "Normal",
      }],
    }),
  });
  setStatus(`Removed ${cardTitle(card)} from Missing List.`, "success", els.missingStatus);
  await loadMissingList();
  if (result.updated === 0) {
    await refresh();
  }
}

function renderSaleList() {
  els.saleGrid.className = "sale-list-grid";
  els.saleGrid.innerHTML = "";
  if (!state.saleCards.length) {
    els.saleGrid.innerHTML = '<div class="empty-state">No cards are marked for sale yet.</div>';
    return;
  }
  for (const card of state.saleCards) {
    const row = document.createElement("article");
    row.className = "sale-card-row";
    row.dataset.cardId = card.scryfall_id;
    row.dataset.variant = card.variant || "Normal";
    row.dataset.condition = conditionText(card);
    row.innerHTML = `
      <a class="sale-card-art" href="${escapeHtml(cardDetailUrl(card))}">
        <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="${escapeHtml(cardTitle(card))}">
      </a>
      <div class="sale-card-copy">
        <h3>${escapeHtml(cardTitle(card))}</h3>
        <p>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")} - ${escapeHtml(conditionText(card))}</p>
      </div>
      <span class="sale-available">Available ${integer.format(card.quantity || 0)}</span>
      <span class="sale-value-pill">${dollars.format(card.display_price || 0)} market</span>
      <label class="sale-inline-field">
        Qty
        <input name="quantity" type="number" min="1" max="${Number(card.quantity || 0)}" step="1" value="${Number(card.sale_quantity || 1)}">
      </label>
      <label class="sale-inline-field">
        Asking
        <input name="asking_price" type="number" min="0.01" step="0.01" value="${Number(card.sale_price || card.display_price || 0.01).toFixed(2)}">
      </label>
      <button class="mark-sold-button" type="button" aria-label="Mark sold" title="Mark sold">
        <span class="sold-icon" aria-hidden="true">$$</span>
      </button>
      <button class="remove-sale-button" type="button" aria-label="Remove from sale" title="Remove from sale">
        <span class="remove-list-icon" aria-hidden="true"></span>
      </button>
    `;
    row.querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", () => {
        saveSaleRow(row).catch((error) => setStatus(error.message, "error", els.saleStatus));
      });
    });
    row.querySelector(".remove-sale-button").addEventListener("click", () => {
      removeFromSale(card).catch((error) => setStatus(error.message, "error", els.saleStatus));
    });
    row.querySelector(".mark-sold-button").addEventListener("click", () => openSoldModal(card));
    els.saleGrid.appendChild(row);
  }
}

function saleAskingLabel(card) {
  const min = Number(card.min_asking_price || card.sale_price || 0);
  const max = Number(card.max_asking_price || card.sale_price || 0);
  if (min > 0 && max > 0 && Math.abs(min - max) > 0.004) return `${dollars.format(min)} - ${dollars.format(max)}`;
  return dollars.format(min || max || 0);
}

async function toggleStoreFavoriteListing(listing, favorite, options = {}) {
  if (!state.user) {
    openAuthModal("login", "Log in to favorite store listings.");
    return null;
  }
  if (Number(listing.seller_user_id || listing.user_id || 0) === Number(state.user.id || 0)) {
    setStatus("This is already your store listing.", "", options.statusTarget || els.storeFrontStatus);
    return null;
  }
  const result = await api("/api/store-front/favorite", {
    method: "POST",
    body: JSON.stringify({
      seller_user_id: listing.seller_user_id || listing.user_id,
      card_id: listing.card_id || listing.scryfall_id,
      variant: listing.variant || "Normal",
      card_condition: listing.card_condition || "Near Mint",
      favorite,
    }),
    promptLogin: true,
  });
  setStatus(
    favorite ? `Favorited ${cardTitle(listing)} store listing.` : `Removed ${cardTitle(listing)} store favorite.`,
    favorite ? "success" : "",
    options.statusTarget || els.storeFrontStatus,
  );
  return result;
}

function renderStoreFront() {
  if (!els.storeFrontGrid) return;
  if (els.storeFrontStatus) {
    const count = state.storeFrontCards.length;
    const quantity = state.storeFrontCards.reduce((total, card) => total + Number(card.sale_quantity || card.quantity || 0), 0);
    els.storeFrontStatus.textContent = `${integer.format(count)} card${count === 1 ? "" : "s"} listed - ${integer.format(quantity)} total for sale`;
  }
  const cards = (state.storeFrontCards || []).map((card) => ({
    ...card,
    readonly: true,
    quantity: Number(card.sale_quantity || card.quantity || 0),
    owned_value: Number(card.sale_asking_total || card.owned_value || 0),
    total_value: Number(card.sale_asking_total || card.owned_value || 0),
    gain_loss: Number(card.gain_loss || 0),
  }));
  renderCards(cards, els.storeFrontGrid, {
    readonly: true,
    hideFavorite: true,
    hideWishlist: true,
    onOpenCard: (card) => {
      openStoreFrontCardDetail(card.scryfall_id || card.card_id).catch((error) => setStatus(error.message, "error", els.storeFrontStatus));
    },
  });
  for (const tile of els.storeFrontGrid.querySelectorAll(".card-row")) {
    tile.classList.add("store-front-card-tile");
  }
  const renderedCards = groupedCardsForDisplay(cards);
  els.storeFrontGrid.querySelectorAll(".store-front-card-tile").forEach((tile, index) => {
    const card = renderedCards[index];
    if (!card) return;
    const stats = tile.querySelector(".card-stats");
    if (stats) {
      stats.insertAdjacentHTML("beforeend", `
        <span class="store-front-pill">${integer.format(card.seller_count || 0)} seller${Number(card.seller_count || 0) === 1 ? "" : "s"}</span>
        <span class="store-front-pill">${escapeHtml(saleAskingLabel(card))} asking</span>
      `);
    }
  });
}

async function openStoreFrontCardDetail(cardId) {
  if (!cardId) return;
  const data = await api(`/api/store-front/${encodeURIComponent(cardId)}`, { promptLogin: false });
  renderStoreFrontCardDetail(data.card || {}, data.sellers || []);
  els.storeFrontDetailOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeStoreFrontCardDetail() {
  if (els.storeFrontDetailOverlay) els.storeFrontDetailOverlay.hidden = true;
  if (els.storeFrontDetailBody) els.storeFrontDetailBody.innerHTML = "";
  document.body.classList.remove("modal-open");
}

function renderStoreFrontCardDetail(card, sellers) {
  els.storeFrontDetailTitle.textContent = cardTitle(card) || "Card for sale";
  const specialClass = cardHasSpecialVariant(card) ? " is-special" : "";
  const sellerRows = sellers.length ? sellers.map((seller) => `
    <article class="store-front-seller-row ${seller.is_current_user ? "is-current-user" : ""}" data-store-url="${escapeAttribute(seller.store_url || "")}" data-own-store="${seller.is_current_user ? "1" : "0"}" data-card-title="${escapeAttribute(cardTitle(card))}">
      <span>
        <strong>${displayNameHtml(seller.seller_name || "Seller", { is_pro: seller.seller_is_pro, role: seller.seller_role })}</strong>
        <small>${escapeHtml(seller.variant || "Normal")} - ${escapeHtml(seller.card_condition || "Near Mint")}</small>
      </span>
      <b>${integer.format(seller.sale_quantity || 0)}</b>
      <b>${dollars.format(seller.asking_price || 0)}</b>
      <button class="share-button store-front-favorite-button ${seller.favorite_store ? "is-favorite" : ""}" type="button" aria-label="${seller.favorite_store ? "Remove store favorite" : "Favorite store listing"}" title="${seller.is_current_user ? "This is your listing" : seller.favorite_store ? "Remove favorite" : "Favorite listing"}" ${seller.is_current_user ? "disabled" : ""}>☆</button>
    </article>
  `).join("") : '<div class="empty-state">No sellers currently have this card listed.</div>';
  els.storeFrontDetailBody.innerHTML = `
    <article class="store-front-card-detail${specialClass}" style="--card-detail-bg-image: url('${escapeAttribute(card.image_normal || card.image_small || "")}')">
      <a class="shared-card-art" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" title="Open on Scryfall">
        <img src="${escapeHtml(card.image_normal || card.image_small || "")}" alt="${escapeHtml(cardTitle(card))}">
      </a>
      <div class="shared-card-copy">
        <p class="eyebrow">${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")}</p>
        <h2>${escapeHtml(cardTitle(card))}</h2>
        <div class="card-divider"></div>
        <p>${escapeHtml(card.type_line || "")}</p>
        ${cardRulesName(card) ? `<p>Rules: ${escapeHtml(cardRulesName(card))}</p>` : ""}
        <div class="detail-pill-row">
          <span>${escapeHtml(cardTypeLabel(card))}</span>
          <span>${escapeHtml(cardColorLabel(card))}</span>
          <span>${integer.format(card.sale_quantity || card.quantity || 0)} for sale</span>
          <span>${integer.format(card.seller_count || sellers.length || 0)} seller${Number(card.seller_count || sellers.length || 0) === 1 ? "" : "s"}</span>
        </div>
        ${variantSummaryHtml(card)}
        <dl class="shared-card-details store-front-market-details">
          <div>
            <dt>Market Price</dt>
            <dd>${dollars.format(card.display_price || 0)}</dd>
          </div>
          <div>
            <dt>Market Total</dt>
            <dd>${dollars.format(card.market_total || 0)}</dd>
          </div>
          <div>
            <dt>Asking Range</dt>
            <dd>${escapeHtml(saleAskingLabel(card))}</dd>
          </div>
          <div>
            <dt>Asking Total</dt>
            <dd>${dollars.format(card.sale_asking_total || card.owned_value || 0)}</dd>
          </div>
        </dl>
        <a class="scryfall-button store-front-detail-scryfall" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" aria-label="Open on Scryfall" title="Open on Scryfall">S</a>
      </div>
    </article>
    <section class="store-front-sellers">
      <div class="store-front-sellers-head">
        <span>Seller</span>
        <span>Qty</span>
        <span>Ask each</span>
        <span>Save</span>
      </div>
      ${sellerRows}
    </section>
  `;
  els.storeFrontDetailBody.querySelectorAll(".store-front-seller-row").forEach((row) => {
    row.querySelector(".store-front-favorite-button")?.addEventListener("click", async (event) => {
      event.stopPropagation();
      const index = Array.from(els.storeFrontDetailBody.querySelectorAll(".store-front-seller-row")).indexOf(row);
      const selectedSeller = sellers[index];
      if (!selectedSeller) return;
      try {
        await toggleStoreFavoriteListing(
          { ...selectedSeller, card_id: card.scryfall_id || card.card_id, scryfall_id: card.scryfall_id || card.card_id, name: card.name, flavor_name: card.flavor_name },
          !selectedSeller.favorite_store,
          { statusTarget: els.storeFrontStatus },
        );
        selectedSeller.favorite_store = !selectedSeller.favorite_store;
        row.querySelector(".store-front-favorite-button")?.classList.toggle("is-favorite", selectedSeller.favorite_store);
        await loadStoreFront();
      } catch (error) {
        setStatus(error.message, "error", els.storeFrontStatus);
      }
    });
    row.addEventListener("click", () => {
      if (row.dataset.ownStore === "1") {
        closeStoreFrontCardDetail();
        if (els.saleSearchInput) els.saleSearchInput.value = row.dataset.cardTitle || "";
        activatePage("for-sale", { push: true });
        return;
      }
      const url = row.dataset.storeUrl;
      if (url) window.location.href = url;
    });
  });
}

function renderNotifications() {
  if (!els.notificationsList) return;
  els.notificationsList.innerHTML = "";
  if (!state.notifications.length) {
    els.notificationsList.innerHTML = '<div class="empty-state">No notifications yet.</div>';
    return;
  }
  for (const notification of state.notifications) {
    const row = document.createElement("article");
    row.className = `notification-row ${notification.is_read ? "" : "is-unread"}`;
    row.innerHTML = `
      <button class="notification-open-button" type="button">
        <span class="notification-read-dot" aria-hidden="true"></span>
        <span>
          <strong>${escapeHtml(notification.subject || "Notification")}</strong>
          <small>${escapeHtml(formatDate(notification.updated_at || notification.created_at || ""))}</small>
        </span>
      </button>
    `;
    row.querySelector(".notification-open-button").addEventListener("click", () => {
      openNotificationDetail(notification).catch((error) => setStatus(error.message, "error", els.notificationsStatus));
    });
    els.notificationsList.appendChild(row);
  }
}

async function openNotificationDetail(notification) {
  if (!notification) return;
  if (els.notificationSubjectInput) els.notificationSubjectInput.value = notification.subject || "";
  if (els.notificationBodyInput) els.notificationBodyInput.value = notification.body || "";
  if (els.notificationStoreLink) {
    els.notificationStoreLink.href = notification.link_url || "#";
    els.notificationStoreLink.hidden = !notification.link_url;
  }
  if (els.notificationDetailOverlay) {
    els.notificationDetailOverlay.hidden = false;
    document.body.classList.add("modal-open");
  }
  if (!notification.is_read) {
    const result = await api(`/api/notifications/${encodeURIComponent(notification.id)}/read`, {
      method: "POST",
      body: "{}",
    });
    state.notifications = result.notifications || state.notifications.map((item) => (
      item.id === notification.id ? { ...item, is_read: 1, read_at: new Date().toISOString() } : item
    ));
    state.unreadNotificationCount = Number(result.unread_count || 0);
    updateNotificationsDot();
    renderNotifications();
  }
}

function closeNotificationDetailModal() {
  if (!els.notificationDetailOverlay) return;
  els.notificationDetailOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  if (els.notificationSubjectInput) els.notificationSubjectInput.value = "";
  if (els.notificationBodyInput) els.notificationBodyInput.value = "";
  if (els.notificationStoreLink) els.notificationStoreLink.href = "#";
}

async function loadAdmin() {
  if (!isAdminUser()) {
    setStatus("Admin access required.", "error", els.adminStatus);
    return;
  }
  const [users, server, reports, templates, announcements, wallpapers, logs] = await Promise.all([
    api("/api/admin/users"),
    api("/api/admin/server"),
    api("/api/admin/reports"),
    api("/api/admin/email-templates"),
    api("/api/admin/announcements"),
    api("/api/admin/wallpapers"),
    loadAdminLogs(false),
  ]);
  state.adminUsers = users.users || [];
  state.adminServer = server;
  state.adminReports = reports.reports || [];
  state.adminEmailTemplates = templates.templates || [];
  state.adminAnnouncements = announcements.announcements || [];
  state.adminWallpapers = wallpapers.wallpapers || [];
  state.appConfig = { ...(state.appConfig || {}), wallpaper: wallpapers.current || null };
  applySiteWallpaper();
  renderAdminUsers();
  renderAdminServer();
  renderAdminReports();
  renderAdminLogs();
  renderAdminEmailTemplates();
  renderAdminAnnouncements();
  renderAdminWallpapers();
}

async function loadAdminLogs(render = true) {
  if (!isAdminUser()) return null;
  const lines = els.adminLogLineCount?.value || "200";
  const data = await api(`/api/admin/logs?lines=${encodeURIComponent(lines)}`);
  state.adminLogs = data;
  if (render) renderAdminLogs();
  return data;
}

function renderAdminUsers() {
  if (!els.adminUsersList) return;
  const users = state.adminUsers || [];
  if (els.adminUserCount) {
    els.adminUserCount.textContent = `${integer.format(users.length)} user${users.length === 1 ? "" : "s"}`;
  }
  els.adminUsersList.innerHTML = "";
  if (!users.length) {
    els.adminUsersList.innerHTML = '<div class="empty-state">No users found.</div>';
    return;
  }
  for (const user of users) {
    const row = document.createElement("article");
    row.className = `admin-user-row ${user.is_banned ? "is-banned" : ""}`;
    row.dataset.userId = user.id;
    const roleOptions = ["admin", "pro", "normal"].map((role) => (
      `<option value="${role}" ${user.role === role ? "selected" : ""}>${roleLabel(role)}</option>`
    )).join("");
    const protectedAdmin = Boolean(user.protected_admin);
    const selfUser = state.user && Number(state.user.id) === Number(user.id);
    row.innerHTML = `
      <div class="admin-user-main">
        <strong>${escapeHtml(user.name || user.email)}</strong>
        <span>${escapeHtml(user.email)}</span>
        <small>${integer.format(user.owned_quantity || 0)} cards · ${integer.format(user.deck_count || 0)} decks · ${integer.format(user.for_sale_quantity || 0)} for sale</small>
      </div>
      <label>
        <span>Role</span>
        <select class="admin-role-select" ${protectedAdmin || selfUser ? "disabled" : ""}>${roleOptions}</select>
      </label>
      <label class="admin-ban-toggle">
        <input class="admin-ban-input" type="checkbox" ${user.is_banned ? "checked" : ""} ${protectedAdmin || selfUser ? "disabled" : ""}>
        <span>Banned</span>
      </label>
      <button class="secondary-button compact-button admin-save-user-button" type="button" ${protectedAdmin || selfUser ? "disabled" : ""}>Save</button>
      <button class="danger-action-button compact-button admin-delete-user-button" type="button" ${protectedAdmin || selfUser ? "disabled" : ""}>
        <span class="trash-icon" aria-hidden="true"></span>Delete
      </button>
    `;
    row.querySelector(".admin-save-user-button")?.addEventListener("click", () => {
      saveAdminUser(row).catch((error) => setStatus(error.message, "error", els.adminStatus));
    });
    row.querySelector(".admin-delete-user-button")?.addEventListener("click", () => {
      deleteAdminUser(row, user).catch((error) => setStatus(error.message, "error", els.adminStatus));
    });
    els.adminUsersList.appendChild(row);
  }
}

function reportTypeLabel(type) {
  if (type === "card_comment") return "Card comment";
  if (type === "profile_post") return "Blog post";
  if (type === "profile_comment") return "Blog comment";
  return "Reported content";
}

function reportResolutionLabel(report) {
  if (report.status === "pending") return "Pending";
  if (report.resolution === "reviewed_removed") return "Reviewed - removed";
  if (report.resolution === "reviewed_ok") return "Reviewed - no action";
  return "Resolved";
}

function renderAdminReports() {
  if (!els.adminReportsList) return;
  const reports = state.adminReports || [];
  const pendingCount = reports.filter((report) => report.status === "pending").length;
  if (els.adminReportCount) {
    els.adminReportCount.textContent = `${integer.format(pendingCount)} pending`;
  }
  if (!reports.length) {
    els.adminReportsList.innerHTML = '<div class="empty-state">No content reports.</div>';
    return;
  }
  els.adminReportsList.innerHTML = reports.map((report) => {
    const target = report.target || {};
    const author = target.author || {};
    const reporter = report.reporter || {};
    const pending = report.status === "pending";
    return `
      <article class="admin-report-row ${pending ? "is-pending" : "is-resolved"}" data-report-id="${escapeHtml(report.id)}">
        <div class="admin-report-main">
          <div class="admin-report-title">
            <strong>${escapeHtml(reportTypeLabel(report.target_type))}</strong>
            <span>${escapeHtml(reportResolutionLabel(report))}</span>
          </div>
          <p>${escapeHtml(report.reason || "")}</p>
          <blockquote>${escapeHtml(target.body || "Content no longer exists.")}</blockquote>
          <small>
            Reported by ${reporter.profile_url ? `<a href="${escapeHtml(reporter.profile_url)}">${escapeHtml(reporter.name || reporter.email || "User")}</a>` : escapeHtml(reporter.name || reporter.email || "User")}
            ${author.name ? ` - Content by ${author.profile_url ? `<a href="${escapeHtml(author.profile_url)}">${escapeHtml(author.name)}</a>` : escapeHtml(author.name)}` : ""}
            ${target.context_name ? ` - ${escapeHtml(target.context_name)}` : ""}
          </small>
          ${report.resolved_at ? `<small>Resolved ${escapeHtml(formatActivityDate(report.resolved_at))}${report.admin?.name ? ` by ${escapeHtml(report.admin.name)}` : ""}</small>` : ""}
        </div>
        ${pending ? `
          <div class="admin-report-actions">
            <button class="secondary-button compact-button admin-report-keep-button" type="button">Reviewed, Fine</button>
            <button class="danger-action-button compact-button admin-report-remove-button" type="button"><span class="trash-icon" aria-hidden="true"></span>Reviewed, Delete</button>
          </div>
        ` : ""}
      </article>
    `;
  }).join("");
  els.adminReportsList.querySelectorAll(".admin-report-keep-button").forEach((button) => {
    button.addEventListener("click", () => resolveAdminReport(button, "keep").catch((error) => setStatus(error.message, "error", els.adminStatus)));
  });
  els.adminReportsList.querySelectorAll(".admin-report-remove-button").forEach((button) => {
    button.addEventListener("click", () => resolveAdminReport(button, "remove").catch((error) => setStatus(error.message, "error", els.adminStatus)));
  });
}

function adminEmailTriggerOptions(selectedValue = "user_created") {
  const triggers = [
    { value: "user_created", label: "User created" },
    { value: "inactive_30_days", label: "Inactive 30 days" },
    { value: "inactive_60_days", label: "Inactive 60 days" },
    { value: "inactive_90_days", label: "Inactive 90 days" },
  ];
  return triggers.map((trigger) => (
    `<option value="${escapeHtml(trigger.value)}" ${selectedValue === trigger.value ? "selected" : ""}>${escapeHtml(trigger.label)}</option>`
  )).join("");
}

function newAdminEmailTemplate() {
  const nextIndex = (state.adminEmailTemplates || []).length + 1;
  return {
    id: `draft-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    name: `Template ${nextIndex}`,
    trigger: "user_created",
    to_email: "%email%",
    from_email: defaultAdminFromEmail(),
    subject: "Welcome to %appname%, %displayname%",
    body: "Welcome %displayname%,\n\nThanks for creating your %appname% account on %date%.\n\nYou can access the site at %baseurl%.\n\n-%domainname%",
  };
}

function renderAdminEmailTemplates() {
  if (!els.adminEmailTemplatesList) return;
  const templates = state.adminEmailTemplates || [];
  if (els.adminEmailTemplateCount) {
    els.adminEmailTemplateCount.textContent = `${integer.format(templates.length)} template${templates.length === 1 ? "" : "s"}`;
  }
  if (!templates.length) {
    els.adminEmailTemplatesList.innerHTML = '<div class="empty-state">No email templates yet.</div>';
    return;
  }
  els.adminEmailTemplatesList.innerHTML = templates.map((template) => `
    <article class="admin-email-template-row" data-template-id="${escapeHtml(template.id)}">
      <label>
        <span>Name</span>
        <input class="admin-email-template-name" type="text" value="${escapeHtml(template.name || "")}" maxlength="80" placeholder="Template name">
      </label>
      <label>
        <span>Trigger</span>
        <select class="admin-email-template-trigger">${adminEmailTriggerOptions(template.trigger || "user_created")}</select>
      </label>
      <button class="secondary-button compact-button admin-test-email-template-button icon-only-button" type="button" aria-label="Send test email" title="Send test email">
        <span class="email-test-icon" aria-hidden="true"></span>
      </button>
      <button class="secondary-button compact-button admin-save-email-template-button" type="button">Save</button>
      <button class="secondary-button compact-button admin-edit-email-template-button" type="button">Edit Template</button>
    </article>
  `).join("");
  els.adminEmailTemplatesList.querySelectorAll(".admin-email-template-name").forEach((input) => {
    input.addEventListener("input", () => updateAdminEmailTemplateFromRow(input.closest(".admin-email-template-row")));
  });
  els.adminEmailTemplatesList.querySelectorAll(".admin-email-template-trigger").forEach((select) => {
    select.addEventListener("change", () => updateAdminEmailTemplateFromRow(select.closest(".admin-email-template-row")));
  });
  els.adminEmailTemplatesList.querySelectorAll(".admin-edit-email-template-button").forEach((button) => {
    button.addEventListener("click", () => openAdminEmailTemplateModal(button.closest(".admin-email-template-row")?.dataset.templateId));
  });
  els.adminEmailTemplatesList.querySelectorAll(".admin-save-email-template-button").forEach((button) => {
    button.addEventListener("click", () => saveAdminEmailTemplateFromRow(button).catch((error) => setStatus(`Template save failed: ${error.message}`, "error", els.adminEmailStatus || els.adminStatus)));
  });
  els.adminEmailTemplatesList.querySelectorAll(".admin-test-email-template-button").forEach((button) => {
    button.addEventListener("click", () => sendAdminEmailTemplateTest(button).catch((error) => setStatus(`Test failed: ${error.message}`, "error", els.adminEmailStatus || els.adminStatus)));
  });
}

function updateAdminEmailTemplateFromRow(row) {
  const templateId = row?.dataset.templateId;
  const template = (state.adminEmailTemplates || []).find((item) => item.id === templateId);
  if (!template) return;
  template.name = row.querySelector(".admin-email-template-name")?.value.trim() || "";
  template.trigger = row.querySelector(".admin-email-template-trigger")?.value || "user_created";
}

function addAdminEmailTemplate() {
  if (!isAdminUser()) return;
  const template = newAdminEmailTemplate();
  state.adminEmailTemplates = [...(state.adminEmailTemplates || []), template];
  renderAdminEmailTemplates();
  openAdminEmailTemplateModal(template.id);
}

function openAdminEmailTemplateModal(templateId) {
  if (!isAdminUser()) return;
  const template = (state.adminEmailTemplates || []).find((item) => item.id === templateId);
  if (!template || !els.adminEmailTemplateOverlay) return;
  state.editingAdminEmailTemplateId = template.id;
  if (els.adminEmailTemplateModalTitle) {
    els.adminEmailTemplateModalTitle.textContent = `Edit ${template.name || "Template"}`;
  }
  if (els.adminEmailTemplateTo) {
    els.adminEmailTemplateTo.value = template.to_email || "%email%";
  }
  if (els.adminEmailTemplateFrom) {
    els.adminEmailTemplateFrom.value = template.from_email || defaultAdminFromEmail();
  }
  if (els.adminEmailTemplateSubject) {
    els.adminEmailTemplateSubject.value = template.subject || "Welcome to %appname%";
  }
  if (els.adminEmailTemplateBody) {
    els.adminEmailTemplateBody.value = template.body || "";
  }
  els.adminEmailTemplateOverlay.hidden = false;
  els.adminEmailTemplateBody?.focus();
}

function closeAdminEmailTemplateModal() {
  if (!els.adminEmailTemplateOverlay) return;
  els.adminEmailTemplateOverlay.hidden = true;
  state.editingAdminEmailTemplateId = null;
}

async function saveAdminEmailTemplate(template) {
  const payload = adminEmailTemplatePayload(template);
  const result = await api("/api/admin/email-templates", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.adminEmailTemplates = result.templates || state.adminEmailTemplates.map((item) => (
    item.id === template.id ? result.template : item
  ));
  return result.template;
}

function adminEmailTemplatePayload(template) {
  const rawId = String(template?.id || "");
  const payload = {
    name: (template?.name || "").trim(),
    trigger: template?.trigger || "user_created",
    to_email: (template?.to_email || "%email%").trim(),
    from_email: (template?.from_email || defaultAdminFromEmail()).trim(),
    subject: (template?.subject || "Welcome to %appname%").trim(),
    body: template?.body || "",
  };
  if (/^\d+$/.test(rawId)) {
    payload.id = rawId;
  }
  return payload;
}

async function saveAdminEmailTemplateFromRow(button) {
  const row = button?.closest(".admin-email-template-row");
  updateAdminEmailTemplateFromRow(row);
  const templateId = row?.dataset.templateId;
  const template = (state.adminEmailTemplates || []).find((item) => item.id === templateId);
  if (!template) return;
  button.disabled = true;
  try {
    await saveAdminEmailTemplate(template);
    renderAdminEmailTemplates();
    setStatus("Template saved to database.", "success", els.adminEmailStatus || els.adminStatus);
  } finally {
    button.disabled = false;
  }
}

async function saveAdminEmailTemplateBody() {
  const template = (state.adminEmailTemplates || []).find((item) => item.id === state.editingAdminEmailTemplateId);
  if (!template) return;
  template.to_email = els.adminEmailTemplateTo?.value.trim() || "%email%";
  template.from_email = els.adminEmailTemplateFrom?.value.trim() || defaultAdminFromEmail();
  template.subject = els.adminEmailTemplateSubject?.value.trim() || "Welcome to %appname%";
  template.body = els.adminEmailTemplateBody?.value || "";
  const button = els.saveAdminEmailTemplateButton;
  if (button) button.disabled = true;
  try {
    await saveAdminEmailTemplate(template);
    closeAdminEmailTemplateModal();
    renderAdminEmailTemplates();
    setStatus("Template saved.", "success", els.adminEmailStatus || els.adminStatus);
  } finally {
    if (button) button.disabled = false;
  }
}

async function sendAdminEmailTemplateTest(button) {
  const row = button?.closest(".admin-email-template-row");
  updateAdminEmailTemplateFromRow(row);
  const templateId = row?.dataset.templateId;
  const template = (state.adminEmailTemplates || []).find((item) => item.id === templateId);
  if (!template) return;
  button.disabled = true;
  const target = els.adminEmailStatus || els.adminStatus;
  setStatus(`Sending test for ${template.name || "template"}...`, "", target);
  try {
    const result = await api("/api/admin/email-templates/test", {
      method: "POST",
      body: JSON.stringify(template),
    });
    setStatus(result.message || "Test successfully sent.", "success", target);
  } finally {
    button.disabled = false;
  }
}

function announcementStatusLabel(status) {
  return status === "published" ? "Published" : "Draft";
}

function newAdminAnnouncement() {
  const today = todayValue();
  return {
    id: `draft-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    subject: "",
    starts_on: today,
    ends_on: today,
    status: "draft",
    body: "",
  };
}

function renderAdminAnnouncements() {
  if (!els.adminAnnouncementsList) return;
  const announcements = state.adminAnnouncements || [];
  if (els.adminAnnouncementCount) {
    const published = announcements.filter((item) => item.status === "published").length;
    els.adminAnnouncementCount.textContent = `${integer.format(announcements.length)} announcement${announcements.length === 1 ? "" : "s"} · ${integer.format(published)} published`;
  }
  if (!announcements.length) {
    els.adminAnnouncementsList.innerHTML = '<div class="empty-state">No announcements yet.</div>';
    return;
  }
  els.adminAnnouncementsList.innerHTML = announcements.map((announcement) => `
    <article class="admin-announcement-row ${announcement.status === "published" ? "is-published" : "is-draft"}" data-announcement-id="${escapeHtml(announcement.id)}">
      <div class="admin-announcement-main">
        <strong>${escapeHtml(announcement.subject || "Untitled announcement")}</strong>
        <span>${escapeHtml(formatAnnouncementRange(announcement))}</span>
        <small>${escapeHtml(announcementStatusLabel(announcement.status))} · Updated ${escapeHtml(formatDate(announcement.updated_at || announcement.created_at || ""))}</small>
      </div>
      <button class="secondary-button compact-button admin-edit-announcement-button" type="button">Edit</button>
    </article>
  `).join("");
  els.adminAnnouncementsList.querySelectorAll(".admin-edit-announcement-button").forEach((button) => {
    button.addEventListener("click", () => openAdminAnnouncementModal(button.closest(".admin-announcement-row")?.dataset.announcementId));
  });
}

function addAdminAnnouncement() {
  if (!isAdminUser()) return;
  const announcement = newAdminAnnouncement();
  state.adminAnnouncements = [announcement, ...(state.adminAnnouncements || [])];
  renderAdminAnnouncements();
  openAdminAnnouncementModal(announcement.id);
}

function openAdminAnnouncementModal(announcementId) {
  if (!isAdminUser()) return;
  const announcement = (state.adminAnnouncements || []).find((item) => String(item.id) === String(announcementId));
  if (!announcement || !els.adminAnnouncementOverlay) return;
  state.editingAdminAnnouncementId = announcement.id;
  if (els.adminAnnouncementModalTitle) {
    els.adminAnnouncementModalTitle.textContent = announcement.id && String(announcement.id).startsWith("draft-") ? "Add Announcement" : "Edit Announcement";
  }
  if (els.adminAnnouncementSubject) els.adminAnnouncementSubject.value = announcement.subject || "";
  if (els.adminAnnouncementStartsOn) els.adminAnnouncementStartsOn.value = announcement.starts_on || todayValue();
  if (els.adminAnnouncementEndsOn) els.adminAnnouncementEndsOn.value = announcement.ends_on || announcement.starts_on || todayValue();
  if (els.adminAnnouncementBody) els.adminAnnouncementBody.value = announcement.body || "";
  els.adminAnnouncementOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.adminAnnouncementSubject?.focus();
}

function closeAdminAnnouncementModal() {
  if (!els.adminAnnouncementOverlay) return;
  const editingId = String(state.editingAdminAnnouncementId || "");
  els.adminAnnouncementOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  if (editingId.startsWith("draft-")) {
    state.adminAnnouncements = (state.adminAnnouncements || []).filter((item) => String(item.id) !== editingId);
    renderAdminAnnouncements();
  }
  state.editingAdminAnnouncementId = null;
}

function currentAdminAnnouncementFromModal(status) {
  const announcement = (state.adminAnnouncements || []).find((item) => String(item.id) === String(state.editingAdminAnnouncementId)) || {};
  return {
    id: announcement.id,
    subject: els.adminAnnouncementSubject?.value.trim() || "",
    starts_on: els.adminAnnouncementStartsOn?.value || todayValue(),
    ends_on: els.adminAnnouncementEndsOn?.value || els.adminAnnouncementStartsOn?.value || todayValue(),
    body: els.adminAnnouncementBody?.value || "",
    status,
  };
}

async function saveAdminAnnouncement(status) {
  const button = status === "published" ? els.publishAdminAnnouncementButton : els.draftAdminAnnouncementButton;
  if (button) button.disabled = true;
  try {
    const payload = currentAdminAnnouncementFromModal(status);
    const result = await api("/api/admin/announcements", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.adminAnnouncements = result.announcements || [];
    closeAdminAnnouncementModal();
    renderAdminAnnouncements();
    setStatus(status === "published" ? "Announcement published." : "Announcement saved as draft.", "success", els.adminAnnouncementStatus || els.adminStatus);
  } finally {
    if (button) button.disabled = false;
  }
}

function renderAdminWallpapers() {
  if (!els.adminWallpapersList) return;
  const wallpapers = state.adminWallpapers || [];
  const currentUrl = state.appConfig?.wallpaper?.url || "";
  if (els.adminWallpaperCount) {
    els.adminWallpaperCount.textContent = `${integer.format(wallpapers.length)} wallpaper${wallpapers.length === 1 ? "" : "s"}`;
  }
  if (!wallpapers.length) {
    els.adminWallpapersList.innerHTML = '<div class="empty-state">No wallpapers uploaded yet.</div>';
    return;
  }
  els.adminWallpapersList.innerHTML = wallpapers.map((wallpaper) => {
    const isCurrent = currentUrl && wallpaper.url === currentUrl;
    return `
      <article class="admin-wallpaper-row ${isCurrent ? "is-current" : ""}" data-wallpaper-id="${escapeHtml(wallpaper.id)}">
        <img src="${escapeHtml(wallpaper.url)}" alt="${escapeHtml(wallpaper.original_name || "Site wallpaper")}">
        <div class="admin-wallpaper-main">
          <strong>${escapeHtml(wallpaper.original_name || wallpaper.filename || "Wallpaper")}</strong>
          <span>${escapeHtml(formatBytes(wallpaper.size_bytes || 0))} · Uploaded ${escapeHtml(formatDate(wallpaper.created_at || ""))}${isCurrent ? " · Today's background" : ""}</span>
        </div>
        <button class="danger-action-button compact-button admin-delete-wallpaper-button" type="button">
          <span class="trash-icon" aria-hidden="true"></span>Delete
        </button>
      </article>
    `;
  }).join("");
  els.adminWallpapersList.querySelectorAll(".admin-delete-wallpaper-button").forEach((button) => {
    button.addEventListener("click", () => deleteAdminWallpaper(button).catch((error) => setStatus(`Wallpaper delete failed: ${error.message}`, "error", els.adminWallpaperStatus || els.adminStatus)));
  });
}

async function readAdminWallpaperFile(file) {
  if (!file) {
    throw new Error("Choose a wallpaper image first.");
  }
  if (!/^image\/(png|jpe?g|webp|gif)$/i.test(file.type || "")) {
    throw new Error("Choose a PNG, JPG, WebP, or GIF image.");
  }
  if (file.size > 5 * 1024 * 1024) {
    throw new Error("Choose an image under 5 MB.");
  }
  const image = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => resolve(String(reader.result || "")));
    reader.addEventListener("error", () => reject(new Error("Could not read that image.")));
    reader.readAsDataURL(file);
  });
  return { image, name: file.name || "Wallpaper" };
}

async function uploadAdminWallpaper() {
  if (!isAdminUser()) return;
  const file = els.adminWallpaperInput?.files?.[0];
  const button = els.uploadAdminWallpaperButton;
  if (button) button.disabled = true;
  setStatus("Uploading wallpaper...", "", els.adminWallpaperStatus || els.adminStatus);
  try {
    const payload = await readAdminWallpaperFile(file);
    const result = await api("/api/admin/wallpapers", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.adminWallpapers = result.wallpapers || [];
    state.appConfig = { ...(state.appConfig || {}), wallpaper: result.current || null };
    applySiteWallpaper();
    renderAdminWallpapers();
    if (els.adminWallpaperInput) els.adminWallpaperInput.value = "";
    setStatus("Wallpaper uploaded. It will join the daily rotation.", "success", els.adminWallpaperStatus || els.adminStatus);
  } finally {
    if (button) button.disabled = false;
  }
}

async function deleteAdminWallpaper(button) {
  if (!isAdminUser()) return;
  const row = button?.closest(".admin-wallpaper-row");
  const wallpaperId = row?.dataset.wallpaperId;
  if (!wallpaperId) return;
  const name = row.querySelector("strong")?.textContent || "this wallpaper";
  const confirmed = window.confirm(`Delete ${name}? It will be removed from the daily rotation.`);
  if (!confirmed) return;
  button.disabled = true;
  const result = await api(`/api/admin/wallpapers/${encodeURIComponent(wallpaperId)}`, {
    method: "DELETE",
    body: "{}",
  });
  state.adminWallpapers = result.wallpapers || [];
  state.appConfig = { ...(state.appConfig || {}), wallpaper: result.current || null };
  applySiteWallpaper();
  renderAdminWallpapers();
  setStatus("Wallpaper deleted.", "success", els.adminWallpaperStatus || els.adminStatus);
}

function insertAnnouncementMarkdown(action) {
  const textarea = els.adminAnnouncementBody;
  if (!textarea) return;
  const start = textarea.selectionStart || 0;
  const end = textarea.selectionEnd || 0;
  const selected = textarea.value.slice(start, end);
  const snippets = {
    bold: `**${selected || "bold text"}**`,
    italic: `*${selected || "italic text"}*`,
    heading: `## ${selected || "Heading"}`,
    list: `- ${selected || "List item"}`,
    link: `[${selected || "link text"}](https://example.com)`,
  };
  const insert = snippets[action] || selected;
  textarea.setRangeText(insert, start, end, "select");
  textarea.focus();
}

async function resolveAdminReport(button, action) {
  const row = button.closest(".admin-report-row");
  const reportId = row?.dataset.reportId;
  if (!reportId) return;
  if (action === "remove") {
    const confirmed = window.confirm("Replace this content with \"this was removed by a moderator\" and resolve all pending reports for it?");
    if (!confirmed) return;
  }
  button.disabled = true;
  const result = await api(`/api/admin/reports/${encodeURIComponent(reportId)}/resolve`, {
    method: "POST",
    body: JSON.stringify({ action }),
  });
  state.adminReports = result.reports || [];
  renderAdminReports();
  setStatus(action === "remove" ? "Report resolved and content removed." : "Report resolved with no action.", "success", els.adminStatus);
}

function roleLabel(role) {
  if (role === "admin") return "Admin";
  if (role === "pro" || role === "paid") return "Pro";
  return "Normal";
}

async function saveAdminUser(row) {
  const userId = row?.dataset.userId;
  if (!userId) return;
  const role = row.querySelector(".admin-role-select")?.value || "normal";
  const isBanned = Boolean(row.querySelector(".admin-ban-input")?.checked);
  const result = await api(`/api/admin/users/${encodeURIComponent(userId)}`, {
    method: "PUT",
    body: JSON.stringify({ role, is_banned: isBanned }),
  });
  state.adminUsers = result.users || state.adminUsers;
  renderAdminUsers();
  setStatus("User updated.", "success", els.adminStatus);
}

async function deleteAdminUser(row, user) {
  const userId = row?.dataset.userId;
  if (!userId) return;
  const confirmed = window.confirm(`Delete ${user?.email || "this user"} and all of their Arcane Ledger data? This cannot be undone.`);
  if (!confirmed) return;
  const result = await api(`/api/admin/users/${encodeURIComponent(userId)}`, {
    method: "DELETE",
    body: "{}",
  });
  state.adminUsers = result.users || [];
  renderAdminUsers();
  setStatus("User deleted.", "success", els.adminStatus);
}

function renderAdminLogs() {
  if (!els.adminLogs) return;
  const payload = state.adminLogs || {};
  els.adminLogs.textContent = (payload.lines || []).join("\n") || "No log lines yet.";
  if (els.adminLogMeta) {
    els.adminLogMeta.textContent = `${payload.path || "Log file"} · ${integer.format(payload.size || 0)} bytes · ${payload.exists ? "available" : "not created yet"}`;
  }
}

function renderAdminServer() {
  if (!els.adminServerDetails) return;
  const data = state.adminServer || {};
  const load = Array.isArray(data.load_average) && data.load_average.length
    ? data.load_average.map((value) => Number(value || 0).toFixed(2)).join(" / ")
    : "Unavailable";
  const memory = data.system_memory || {};
  const disk = data.disk || {};
  const rows = [
    ["App version", data.app_version || "Unknown"],
    ["Uptime", formatDuration(data.uptime_seconds || 0)],
    ["Host", data.host || "Unknown"],
    ["Platform", data.platform || "Unknown"],
    ["Python", data.python_version || "Unknown"],
    ["Process", `PID ${data.pid || "?"} · ${formatBytes(data.process_memory_bytes || 0)} memory`],
    ["CPU", `${integer.format(data.cpu_count || 0)} cores · load ${load}`],
    ["System memory", memory.total_bytes ? `${formatBytes(memory.used_bytes || 0)} used / ${formatBytes(memory.total_bytes || 0)} total${memory.available_bytes ? ` · ${formatBytes(memory.available_bytes)} available` : ""}` : "Unavailable"],
    ["Data disk", disk.total_bytes ? `${formatBytes(disk.used_bytes || 0)} used / ${formatBytes(disk.total_bytes || 0)} total · ${formatBytes(disk.free_bytes || 0)} free` : "Unavailable"],
    ["Database", `${formatBytes(data.database?.size_bytes || 0)} · ${data.database?.path || ""}`],
    ["Logs", `${formatBytes(data.logs?.size || 0)} · ${data.logs?.path || ""}`],
  ];
  if (els.adminServerVersion) {
    els.adminServerVersion.textContent = data.app_version || "";
  }
  els.adminServerDetails.innerHTML = rows.map(([label, value]) => `
    <div>
      <dt>${escapeHtml(label)}</dt>
      <dd>${escapeHtml(value)}</dd>
    </div>
  `).join("");
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = bytes;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  const decimals = size >= 10 || index === 0 ? 0 : 1;
  return `${size.toFixed(decimals)} ${units[index]}`;
}

function formatDuration(seconds) {
  let remaining = Math.max(0, Number(seconds || 0));
  const days = Math.floor(remaining / 86400);
  remaining %= 86400;
  const hours = Math.floor(remaining / 3600);
  remaining %= 3600;
  const minutes = Math.floor(remaining / 60);
  if (days) return `${days}d ${hours}h ${minutes}m`;
  if (hours) return `${hours}h ${minutes}m`;
  if (minutes) return `${minutes}m`;
  return `${Math.floor(remaining)}s`;
}

function salePayloadFromRow(row) {
  const quantityInput = row.querySelector('input[name="quantity"]');
  const priceInput = row.querySelector('input[name="asking_price"]');
  return {
    card_id: row.dataset.cardId,
    variant: row.dataset.variant || "Normal",
    card_condition: row.dataset.condition || "Near Mint",
    quantity: Number(quantityInput?.value || 0),
    asking_price: Number(priceInput?.value || 0),
  };
}

async function saveSaleRow(row) {
  const payload = salePayloadFromRow(row);
  const max = Number(row.querySelector('input[name="quantity"]')?.max || 0);
  if (payload.quantity < 1 || payload.quantity > max) {
    throw new Error(`Sale quantity must be between 1 and ${integer.format(max)}.`);
  }
  if (payload.asking_price <= 0) {
    throw new Error("Asking price must be greater than $0.00.");
  }
  await api("/api/cards/for-sale", {
    method: "POST",
    body: JSON.stringify({ cards: [payload], for_sale: true }),
  });
  setStatus("Sale listing updated.", "success", els.saleStatus);
  await loadNotificationSummary();
  await loadCards();
}

async function removeFromSale(card) {
  const confirmed = window.confirm(`Remove ${cardTitle(card)} from For Sale?`);
  if (!confirmed) return;
  await api("/api/cards/for-sale", {
    method: "POST",
    body: JSON.stringify({
      for_sale: false,
      cards: [{
        card_id: card.scryfall_id,
        variant: card.variant || "Normal",
        card_condition: conditionText(card),
      }],
    }),
  });
  setStatus(`Removed ${cardTitle(card)} from For Sale.`, "success", els.saleStatus);
  await loadSaleCards();
  await loadCards();
}

function isCardGridTarget(target) {
  return target === els.cardsGrid || target === els.favoritesGrid;
}

function renderCards(cards, target = els.cardsGrid, options = {}) {
  cards = groupedCardsForDisplay(cards);
  target.innerHTML = "";
  if (!cards.length) {
    target.innerHTML = '<div class="empty-state">No cards match the current filters.</div>';
    if (isCardGridTarget(target)) updateBulkBar();
    return;
  }
  for (const card of cards) {
    const owned = Number(card.quantity || 0) > 0;
    const catalogOnly = Boolean(card.catalog_only);
    const summaries = variantSummaries(card);
    const node = els.template.content.firstElementChild.cloneNode(true);
    const tileBackground = node.querySelector(".card-tile-art-bg");
    const selectWrap = node.querySelector(".select-card-wrap");
    const selectCheckbox = node.querySelector(".select-card-checkbox");
    const link = node.querySelector(".card-art");
    const img = node.querySelector("img");
    const title = node.querySelector("h3");
    const quantityWatermark = node.querySelector(".quantity-watermark");
    const meta = node.querySelector(".card-meta");
    const type = node.querySelector(".card-type");
    const ownedValue = node.querySelector(".owned-value");
    const price = node.querySelector(".price");
    const delta = node.querySelector(".delta");
    const variantPill = node.querySelector(".variant-pill");
    const conditionPill = node.querySelector(".condition-pill");
    const typePill = node.querySelector(".type-pill");
    const colorPill = node.querySelector(".color-pill");
    const favoriteButton = node.querySelector(".favorite-button");
    const wishlistButton = node.querySelector(".wishlist-button");
    const refreshButton = node.querySelector(".refresh-card-button");
    const editButton = node.querySelector(".edit-button");
    const deckButton = node.querySelector(".deck-membership-button");
    const containerButton = node.querySelector(".container-membership-button");
    const scryfallButton = node.querySelector(".scryfall-button");
    const shareButton = node.querySelector(".share-button");
    const blogButton = node.querySelector(".blog-card-button");
    const tileBackgroundImage = cssImageUrl(card.image_normal || card.image_small || "");
    node.style.setProperty("--card-tile-bg-image", tileBackgroundImage);
    if (tileBackground) tileBackground.style.backgroundImage = tileBackgroundImage;

    link.href = catalogOnly ? (card.scryfall_uri || "#") : cardDetailUrl(card);
    link.target = catalogOnly ? "_blank" : "_self";
    link.rel = catalogOnly ? "noreferrer" : "";
    if (options.onOpenCard) {
      link.target = "_self";
      link.rel = "";
      link.addEventListener("click", (event) => {
        event.preventDefault();
        options.onOpenCard(card);
      });
      node.addEventListener("click", (event) => {
        if (event.target.closest("button, input, select, textarea, .scryfall-button")) return;
        event.preventDefault();
        options.onOpenCard(card);
      });
    }
    img.src = card.image_normal || card.image_small || "";
    img.alt = cardTitle(card);
    title.textContent = cardTitle(card);
    meta.textContent = `${card.set_name} #${card.collector_number} - ${card.rarity || "unknown"}${cardRulesName(card) ? ` - Rules: ${cardRulesName(card)}` : ""}`;
    type.textContent = card.type_line || "";
    quantityWatermark.textContent = integer.format(card.quantity || 0);
    node.classList.toggle("is-special", cardHasSpecialVariant(card));
    node.classList.toggle("is-missing", !owned);
    ownedValue.textContent = dollars.format(card.owned_value || 0);
    if (price) price.textContent = `Now ${dollars.format(card.display_price || 0)}`;
    delta.textContent = `Delta ${dollars.format(card.gain_loss || 0)}`;
    delta.className = `delta ${valueClass(card.gain_loss || 0)}`;
    variantPill.textContent = summaries.length > 1 ? `${integer.format(summaries.length)} variants` : (card.variant || "Normal");
    conditionPill.textContent = summaries.length > 1 ? "Mixed conditions" : conditionText(card);
    typePill.textContent = cardTypeLabel(card);
    colorPill.textContent = cardColorLabel(card);
    type.insertAdjacentHTML("afterend", variantSummaryHtml(card));

    if (options.setMissingSelectable) {
      wireSetMissingSelection(selectWrap, selectCheckbox, card);
    } else {
      wireCardSelection(selectWrap, selectCheckbox, card, options);
    }

    if (options.hideFavorite || options.readonly) {
      favoriteButton.hidden = true;
    } else {
      favoriteButton.classList.toggle("is-favorite", Boolean(card.favorite));
      favoriteButton.setAttribute("aria-pressed", card.favorite ? "true" : "false");
      favoriteButton.title = card.favorite ? "Remove favorite" : "Favorite";
      favoriteButton.addEventListener("click", async () => {
        const nextFavorite = !Boolean(card.favorite);
        if (!nextFavorite && options.confirmUnfavorite) {
          const confirmed = window.confirm(`Remove ${cardTitle(card)} from Favorites? It will disappear from this page.`);
          if (!confirmed) return;
        }
        try {
          await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/favorite`, {
            method: "POST",
            body: JSON.stringify({
              variant: card.variant || "Normal",
              favorite: nextFavorite,
            }),
          });
          setStatus(nextFavorite ? `Favorited ${cardTitle(card)}.` : `Removed favorite from ${cardTitle(card)}.`, "", options.statusTarget || els.status);
          if (options.afterFavoriteChange) {
            await options.afterFavoriteChange();
          } else {
            await refresh();
          }
        } catch (error) {
          setStatus(error.message, "error", options.statusTarget || els.status);
        }
      });
    }
    if (options.hideWishlist || options.readonly) {
      wishlistButton.hidden = true;
    } else {
      wireWishlistButton(wishlistButton, card, options);
    }
    if (catalogOnly || options.readonly) {
      refreshButton.hidden = true;
      editButton.hidden = true;
      shareButton.hidden = true;
      blogButton.hidden = true;
      deckButton.hidden = true;
      containerButton.hidden = true;
    } else {
      wireRefreshCardButton(refreshButton, card);
      editButton.addEventListener("click", () => openCardDetail(card));
      blogButton.addEventListener("click", () => openCardBlogModal(card));
      wireDeckMembershipButton(deckButton, card, target === els.cardsGrid);
      wireContainerMembershipButton(containerButton, card, target === els.cardsGrid);
      wireCardDetailNavigation(node, card);
    }
    wireScryfallButton(scryfallButton, card);
    wireShareButton(shareButton, card);

    target.appendChild(node);
  }
  if (isCardGridTarget(target)) updateBulkBar();
}

function renderCardList(cards, target = els.cardsGrid, options = {}) {
  cards = groupedCardsForDisplay(cards);
  target.innerHTML = "";
  if (!cards.length) {
    target.innerHTML = '<div class="empty-state">No cards match the current filters.</div>';
    if (isCardGridTarget(target)) updateBulkBar();
    return;
  }
  for (const card of cards) {
    const owned = Number(card.quantity || 0) > 0;
    const catalogOnly = Boolean(card.catalog_only);
    const summaries = variantSummaries(card);
    const node = els.listTemplate.content.firstElementChild.cloneNode(true);
    const selectWrap = node.querySelector(".select-card-wrap");
    const selectCheckbox = node.querySelector(".select-card-checkbox");
    const link = node.querySelector(".list-card-art");
    const img = node.querySelector("img");
    const title = node.querySelector("h3");
    const meta = node.querySelector(".card-meta");
    const type = node.querySelector(".card-type");
    const price = node.querySelector(".price");
    const ownedValue = node.querySelector(".owned-value");
    const quantity = node.querySelector(".detail-quantity");
    const variant = node.querySelector(".detail-variant");
    const conditionPill = node.querySelector(".condition-pill");
    const typePill = node.querySelector(".type-pill");
    const colorPill = node.querySelector(".color-pill");
    const deckButton = node.querySelector(".deck-membership-button");
    const containerButton = node.querySelector(".container-membership-button");
    const scryfallButton = node.querySelector(".scryfall-button");
    const refreshButton = node.querySelector(".refresh-card-button");
    const editButton = node.querySelector(".edit-button");
    const shareButton = node.querySelector(".share-button");
    const blogButton = node.querySelector(".blog-card-button");
    const wishlistButton = node.querySelector(".wishlist-button");
    const deleteButton = node.querySelector(".delete-card-button");

    node.classList.toggle("is-special", cardHasSpecialVariant(card));
    node.classList.toggle("is-missing", !owned);
    link.href = catalogOnly ? (card.scryfall_uri || "#") : cardDetailUrl(card);
    link.target = catalogOnly ? "_blank" : "_self";
    link.rel = catalogOnly ? "noreferrer" : "";
    img.src = card.image_normal || card.image_small || "";
    img.alt = cardTitle(card);
    title.textContent = cardTitle(card);
    meta.textContent = `${card.set_name} #${card.collector_number} - ${card.rarity || "unknown"}${cardRulesName(card) ? ` - Rules: ${cardRulesName(card)}` : ""}`;
    type.textContent = card.type_line || "";
    price.textContent = `Now ${dollars.format(card.display_price || 0)}`;
    ownedValue.textContent = `Value ${dollars.format(card.owned_value || 0)}`;
    quantity.textContent = `Qty ${integer.format(card.quantity || 0)}`;
    variant.textContent = summaries.length > 1 ? `${integer.format(summaries.length)} variants` : (card.variant || "Normal");
    conditionPill.textContent = summaries.length > 1 ? "Mixed conditions" : conditionText(card);
    typePill.textContent = cardTypeLabel(card);
    colorPill.textContent = cardColorLabel(card);
    type.insertAdjacentHTML("afterend", variantSummaryHtml(card));

    wireCardSelection(selectWrap, selectCheckbox, card, options);
    wireDeckMembershipButton(deckButton, card, target === els.cardsGrid);
    wireContainerMembershipButton(containerButton, card, target === els.cardsGrid);
    wireScryfallButton(scryfallButton, card);
    if (catalogOnly || options.readonly) {
      deckButton.hidden = true;
      containerButton.hidden = true;
      refreshButton.hidden = true;
      editButton.hidden = true;
      shareButton.hidden = true;
      blogButton.hidden = true;
      deleteButton.hidden = true;
    } else {
      wireRefreshCardButton(refreshButton, card);
      editButton.addEventListener("click", () => openCardDetail(card));
      blogButton.addEventListener("click", () => openCardBlogModal(card));
      wireShareButton(shareButton, card);
      wireDeleteCardButton(deleteButton, card);
      wireCardDetailNavigation(node, card);
    }
    if (options.hideWishlist || options.readonly) {
      wishlistButton.hidden = true;
    } else {
      wireWishlistButton(wishlistButton, card, options);
    }

    target.appendChild(node);
  }
  if (isCardGridTarget(target)) updateBulkBar();
}

function formatDate(value) {
  if (!value) return "Not set";
  const [year, month] = value.split("-");
  const monthIndex = Number(month) - 1;
  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  if (!year || monthIndex < 0 || monthIndex > 11) return value;
  return `${year.slice(-2)} ${monthNames[monthIndex]}`;
}

function formatCompactDate(value) {
  if (!value) return "Not set";
  const [year, month, day] = String(value).slice(0, 10).split("-");
  const monthNumber = Number(month);
  const dayNumber = Number(day);
  if (!year || !monthNumber || !dayNumber) return value;
  return `${monthNumber}/${dayNumber}/${year.slice(-2)}`;
}

function formatAnnouncementDate(value) {
  return formatCompactDate(value);
}

function formatAnnouncementRange(announcement) {
  return `${formatAnnouncementDate(announcement?.starts_on || "")} - ${formatAnnouncementDate(announcement?.ends_on || "")}`;
}

function ensureSelectOption(select, value) {
  if (!value) return;
  const exists = Array.from(select.options).some((option) => option.value === value);
  if (!exists) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }
}

function openEditModal(card) {
  state.editingCard = card;
  els.editTitle.textContent = cardTitle(card);
  els.editForm.card_id.value = card.scryfall_id;
  els.editForm.original_variant.value = card.variant || "Normal";
  els.editForm.quantity.value = card.quantity || 0;
  els.editForm.paid_price.value = Number(card.paid_price || 0.01).toFixed(2);
  els.editForm.acquired_date.value = card.acquired_date || "";
  ensureSelectOption(els.editForm.variant, card.variant || "Normal");
  els.editForm.variant.value = card.variant || "Normal";
  els.editForm.card_condition.value = conditionText(card);
  els.editForm.graded.checked = Boolean(Number(card.graded || 0));
  els.editForm.notes.value = card.notes || "";
  els.editOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.editForm.quantity.focus();
}

function closeEditModal() {
  els.editOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.editingCard = null;
  els.editForm.reset();
}

function shareUrlForCard(card) {
  if (!card || !(card.scryfall_id || card.card_id)) return "";
  return new URL(cardDetailUrl(card), window.location.origin).toString();
}

function shareUrlForDeck(deck) {
  if (!deck || !deck.share_id) return "";
  return new URL(`/decks/${encodeURIComponent(deck.share_id)}`, window.location.origin).toString();
}

function shareUrlForWishlist(wishlist) {
  if (!wishlist || !wishlist.share_id) return "";
  return new URL(`/wishlists/${encodeURIComponent(wishlist.share_id)}`, window.location.origin).toString();
}

function shareUrlForContainer(container) {
  if (!container || !container.share_id) return "";
  return new URL(`/containers/${encodeURIComponent(container.share_id)}`, window.location.origin).toString();
}

function shareUrlForSet(set) {
  if (!set || !set.set_code) return "";
  const storeShareId = set.store_share_id || state.user?.store_share_id || "";
  if (!storeShareId) return "";
  return new URL(`/sets/shared/${encodeURIComponent(storeShareId)}/${encodeURIComponent(set.set_code)}`, window.location.origin).toString();
}

function shareUrlForFavorites() {
  const shareId = state.user?.store_share_id || "";
  return shareId ? new URL(`/favorites/${encodeURIComponent(shareId)}`, window.location.origin).toString() : "";
}

function openShareUrl(title, url) {
  els.shareTitle.textContent = title;
  els.shareUrlInput.value = url;
  els.shareOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.shareUrlInput.focus();
  els.shareUrlInput.select();
}

function openShareModal(card) {
  const url = shareUrlForCard(card);
  if (!url) {
    setStatus("This card does not have a share link yet.", "error");
    return;
  }
  openShareUrl(cardTitle(card), url);
}

function openDeckShareModal(deck) {
  const url = shareUrlForDeck(deck);
  if (!url) {
    els.decksStatus.textContent = "This deck does not have a share link yet.";
    return;
  }
  openShareUrl(deck.name || "Deck", url);
}

function openWishlistShareModal(wishlist) {
  const url = shareUrlForWishlist(wishlist);
  if (!url) {
    els.wishlistStatus.textContent = "This wishlist does not have a share link yet.";
    return;
  }
  openShareUrl(wishlist.name || "Wishlist", url);
}

function openContainerShareModal(container) {
  const url = shareUrlForContainer(container);
  if (!url) {
    els.containersStatus.textContent = "This container does not have a share link yet.";
    return;
  }
  openShareUrl(container.name || "Container", url);
}

function openSetShareModal(set) {
  const url = shareUrlForSet(set);
  if (!url) {
    setStatus("This set does not have a share link yet.", "error", els.setsStatus);
    return;
  }
  openShareUrl(set.set_name || "Set", url);
}

function openFavoritesShareModal() {
  const url = shareUrlForFavorites();
  if (!url) {
    setStatus("Your account does not have a favorites share link yet. Refresh and try again.", "error", els.favoritesStatus);
    return;
  }
  openShareUrl("Favorites", url);
}

function cardBlogPreviewHtml(card) {
  if (!card) return "";
  return `
    <a class="card-blog-card" href="${escapeHtml(cardDetailUrl(card))}">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="${escapeHtml(cardTitle(card))}">
      <span>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <small>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</small>
        <small>${escapeHtml(card.type_line || "")}</small>
      </span>
    </a>
  `;
}

function deckBlogPreviewHtml(deck) {
  if (!deck) return "";
  const images = uniqueDeckPreviewImages(deck);
  return `
    <a class="card-blog-card deck-blog-card" href="${escapeHtml(deck.deck_url || `/decks/${encodeURIComponent(deck.share_id || deck.id || "")}`)}">
      <span class="deck-blog-thumb">
        ${images.length ? images.slice(0, 3).map((src) => `<img src="${escapeHtml(src)}" alt="">`).join("") : '<span class="deck-icon" aria-hidden="true"></span>'}
      </span>
      <span>
        <strong>${escapeHtml(deck.name || "Deck")}</strong>
        <small>${integer.format(deck.card_count || 0)} cards - ${integer.format(deck.unique_card_count || 0)} unique</small>
        ${deck.description ? `<small>${escapeHtml(deck.description)}</small>` : ""}
      </span>
    </a>
  `;
}

function openCardBlogModal(card, presetText = "") {
  if (!state.user) {
    openAuthModal("login", "Log in to write a blog post.");
    return;
  }
  state.activeBlogCard = card;
  state.activeBlogDeck = null;
  if (els.cardBlogTitle) els.cardBlogTitle.textContent = "Write About This Card";
  if (els.cardBlogPreview) {
    els.cardBlogPreview.innerHTML = cardBlogPreviewHtml(card);
  }
  if (els.cardBlogForm) {
    els.cardBlogForm.body.value = presetText;
  }
  setStatus("", "", els.cardBlogStatus);
  els.cardBlogOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.cardBlogForm?.body?.focus();
}

function openDeckBlogModal(deck, presetText = "") {
  if (!state.user) {
    openAuthModal("login", "Log in to write a blog post.");
    return;
  }
  state.activeBlogCard = null;
  state.activeBlogDeck = deck;
  if (els.cardBlogTitle) els.cardBlogTitle.textContent = "Write About This Deck";
  if (els.cardBlogPreview) {
    els.cardBlogPreview.innerHTML = deckBlogPreviewHtml(deck);
  }
  if (els.cardBlogForm) {
    els.cardBlogForm.body.value = presetText;
  }
  setStatus("", "", els.cardBlogStatus);
  els.cardBlogOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.cardBlogForm?.body?.focus();
}

function closeCardBlogModal() {
  els.cardBlogOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.activeBlogCard = null;
  state.activeBlogDeck = null;
  els.cardBlogForm?.reset();
  if (els.cardBlogPreview) els.cardBlogPreview.innerHTML = "";
  setStatus("", "", els.cardBlogStatus);
}

function cardBlogPostRowHtml(post) {
  return `
    <article class="card-blog-row">
      <div class="profile-feed-author">
        ${profileAvatarHtml(post.author)}
        <div>
          <strong>${profileActorLink(post.author)}</strong>
          <span>${escapeHtml(formatActivityDate(post.created_at))}</span>
        </div>
      </div>
      <p>${escapeHtml(post.body || "")}</p>
      ${state.user ? `<button class="report-content-button" type="button" data-target-type="profile_post" data-target-id="${escapeHtml(post.id)}" data-target-label="blog post by ${escapeAttribute(post.author?.name || "Arcane Ledger user")}">Report</button>` : ""}
    </article>
  `;
}

async function openCardBlogListModal(card) {
  state.activeBlogListCard = card;
  els.cardBlogListPreview.innerHTML = cardBlogPreviewHtml(card);
  els.cardBlogList.innerHTML = '<div class="empty-state compact-empty">Loading blog posts...</div>';
  setStatus("", "", els.cardBlogListStatus);
  els.cardBlogListOverlay.hidden = false;
  document.body.classList.add("modal-open");
  try {
    const result = await api(`/api/cards/${encodeURIComponent(card.scryfall_id || card.card_id)}/posts?variant=${encodeURIComponent(card.variant || "Normal")}`, { promptLogin: false });
    const posts = result.posts || [];
    els.cardBlogList.innerHTML = posts.length
      ? posts.map(cardBlogPostRowHtml).join("")
      : '<div class="empty-state compact-empty">No blog posts have been written about this card yet.</div>';
  } catch (error) {
    els.cardBlogList.innerHTML = `<div class="empty-state compact-empty">${escapeHtml(error.message)}</div>`;
  }
}

function closeCardBlogListModal() {
  els.cardBlogListOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.activeBlogListCard = null;
  if (els.cardBlogListPreview) els.cardBlogListPreview.innerHTML = "";
  if (els.cardBlogList) els.cardBlogList.innerHTML = "";
  setStatus("", "", els.cardBlogListStatus);
}

function deckMemberships(card) {
  return Array.isArray(card.deck_memberships) ? card.deck_memberships : [];
}

function containerType(value) {
  return ["binder", "box", "other"].includes(value) ? value : "other";
}

function containerTypeLabel(value) {
  return {
    binder: "Binder",
    box: "Box",
    other: "Other",
  }[containerType(value)];
}

function containerIconHtml(value) {
  return `<span class="container-icon ${containerType(value)}-icon" aria-hidden="true"></span>`;
}

function containerMemberships(card) {
  return Array.isArray(card.container_memberships) ? card.container_memberships : [];
}

function openCardDecksModal(card) {
  const decks = deckMemberships(card);
  if (!decks.length) return;
  els.cardDecksTitle.textContent = cardTitle(card);
  els.cardDecksList.innerHTML = decks.map((deck) => `
    <button class="card-deck-link" type="button" data-share-id="${escapeHtml(deck.share_id || "")}">
      <span class="deck-icon" aria-hidden="true"></span>
      <span>${escapeHtml(deck.name || "Deck")}</span>
      <small>Qty ${integer.format(deck.deck_quantity || 1)}</small>
    </button>
  `).join("");
  for (const button of els.cardDecksList.querySelectorAll(".card-deck-link")) {
    button.addEventListener("click", () => {
      const shareId = button.dataset.shareId;
      if (!shareId) return;
      window.open(`/decks/${encodeURIComponent(shareId)}`, "_blank", "noopener");
    });
  }
  els.cardDecksOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function openCardContainersModal(card) {
  const containers = containerMemberships(card);
  if (!containers.length) return;
  if (containers.length === 1 && containers[0].id) {
    openContainerDetailModal(containers[0].id).catch((error) => {
      setStatus(error.message, "error");
    });
    return;
  }
  els.cardContainersTitle.textContent = cardTitle(card);
  els.cardContainersList.innerHTML = containers.map((container) => `
    <button class="card-deck-link card-container-link" type="button" data-container-id="${escapeHtml(container.id || "")}">
      ${containerIconHtml(container.storage_type)}
      <span>
        <strong>${escapeHtml(container.name || "Container")}</strong>
        <small>${escapeHtml(containerTypeLabel(container.storage_type))}${container.location ? ` - ${escapeHtml(container.location)}` : ""} - Stored ${integer.format(container.quantity || 0)}</small>
      </span>
    </button>
  `).join("");
  for (const button of els.cardContainersList.querySelectorAll(".card-container-link")) {
    button.addEventListener("click", () => {
      const containerId = button.dataset.containerId;
      if (!containerId) return;
      closeCardContainersModal();
      openContainerDetailModal(containerId).catch((error) => {
        setStatus(error.message, "error");
      });
    });
  }
  els.cardContainersOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeCardContainersModal() {
  els.cardContainersOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.cardContainersTitle.textContent = "Containers";
  els.cardContainersList.innerHTML = "";
}

function closeCardMetaModal() {
  els.cardMetaOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.cardMetaEyebrow.textContent = "Arcane Ledger meta";
  els.cardMetaTitle.textContent = "Card Meta";
  els.cardMetaList.innerHTML = "";
}

function closeCardDecksModal() {
  els.cardDecksOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.cardDecksTitle.textContent = "Decks";
  els.cardDecksList.innerHTML = "";
}

function wireDeckMembershipButton(button, card, showIndicator) {
  const decks = deckMemberships(card);
  if (!button || !showIndicator || !decks.length) {
    if (button) button.hidden = true;
    return;
  }
  button.hidden = false;
  button.title = `In ${decks.length} deck${decks.length === 1 ? "" : "s"}`;
  button.setAttribute("aria-label", `Show decks containing ${cardTitle(card)}`);
  button.addEventListener("click", () => openCardDecksModal(card));
}

function wireContainerMembershipButton(button, card, showIndicator) {
  const containers = containerMemberships(card);
  if (!button || !showIndicator || !containers.length) {
    if (button) button.hidden = true;
    return;
  }
  const firstType = containerType(containers[0].storage_type);
  const icon = button.querySelector(".container-icon");
  if (icon) {
    icon.className = `container-icon ${firstType}-icon`;
  }
  button.hidden = false;
  button.title = `Stored in ${containers.length} container${containers.length === 1 ? "" : "s"}`;
  button.setAttribute("aria-label", `Show containers storing ${cardTitle(card)}`);
  button.addEventListener("click", () => openCardContainersModal(card));
}

function closeShareModal() {
  els.shareOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.shareUrlInput.value = "";
}

async function copyShareUrl() {
  const url = els.shareUrlInput.value;
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
    setStatus("Share link copied.");
  } catch {
    els.shareUrlInput.focus();
    els.shareUrlInput.select();
    setStatus("Share link selected.");
  }
}

function deckJsonCard(card) {
  return {
    scryfall_id: card.scryfall_id || card.card_id || "",
    name: cardTitle(card),
    set_code: card.set_code || "",
    set_name: card.set_name || "",
    collector_number: card.collector_number || "",
    rarity: card.rarity || "",
    variant: card.variant || "Normal",
    quantity: deckQuantity(card),
    owned_quantity: Number(card.owned_quantity ?? card.quantity ?? 0),
    short_quantity: Math.max(0, Number(card.short_quantity ?? deckQuantity(card) - Number(card.owned_quantity ?? card.quantity ?? 0))),
    display_price: Number(card.display_price || 0),
    type_line: card.type_line || "",
    type_category: card.type_category || "",
    colors: card.colors || "",
    color_identity: card.color_identity || "",
    mana_cost: card.mana_cost || "",
    image_small: card.image_small || "",
    image_normal: card.image_normal || "",
    scryfall_uri: card.scryfall_uri || "",
  };
}

function deckJsonPayload(deck, includeNotes = false) {
  const payload = {
    format: includeNotes ? "arcaneledger.deck.full" : "arcaneledger.deck",
    version: 1,
    exported_at: new Date().toISOString(),
    name: deck.name || "Deck",
    is_private: Boolean(Number(deck.is_private || 0)),
    cards: (deck.cards || []).map(deckJsonCard),
  };
  if (includeNotes) {
    payload.description = deck.description || "";
    payload.internal_notes = deck.internal_notes || "";
    payload.external_notes = deck.external_notes || "";
  }
  return payload;
}

function openDeckJsonModal(deck, includeNotes = false) {
  if (!deck) return;
  els.deckJsonTitle.textContent = includeNotes ? "Export Full Deck" : "Export Deck List";
  els.deckJsonText.value = JSON.stringify(deckJsonPayload(deck, includeNotes), null, 2);
  setStatus("", "", els.deckJsonStatus);
  els.deckJsonOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.deckJsonText.focus();
  els.deckJsonText.select();
}

function closeDeckJsonModal() {
  els.deckJsonOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.deckJsonText.value = "";
  setStatus("", "", els.deckJsonStatus);
}

async function copyDeckJson() {
  const text = els.deckJsonText.value;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    setStatus("Deck JSON copied.", "success", els.deckJsonStatus);
  } catch {
    els.deckJsonText.focus();
    els.deckJsonText.select();
    setStatus("Deck JSON selected.", "", els.deckJsonStatus);
  }
}

function openImportDeckModal() {
  els.importDeckForm.reset();
  state.pendingDeckImport = null;
  renderDeckImportPreview([]);
  setStatus("", "", els.importDeckStatus);
  els.commitImportDeckButton.disabled = true;
  els.importDeckOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.importDeckJsonText.focus();
}

function closeImportDeckModal() {
  els.importDeckOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.importDeckForm.reset();
  state.pendingDeckImport = null;
  renderDeckImportPreview([]);
  els.commitImportDeckButton.disabled = true;
  setStatus("", "", els.importDeckStatus);
}

function openExportDecksModal() {
  setStatus("", "", els.exportDecksStatus);
  els.exportDecksOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeExportDecksModal() {
  els.exportDecksOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  setStatus("", "", els.exportDecksStatus);
}

function downloadDecks(format) {
  const endpoint = format === "csv" ? "/api/decks/export.csv" : "/api/decks/export.json";
  window.location.href = endpoint;
  setStatus(`Preparing ${format.toUpperCase()} download...`, "success", els.exportDecksStatus);
}

function deckImportFormat() {
  return els.importDeckForm.deck_import_format?.value || "json";
}

function deckImportPayloadFromText(text) {
  return {
    format: deckImportFormat(),
    content: text,
  };
}

function renderDeckImportPreview(decks = []) {
  if (!decks.length) {
    els.importDeckPreview.hidden = true;
    els.importDeckPreview.innerHTML = "";
    return;
  }
  els.importDeckPreview.hidden = false;
  els.importDeckPreview.innerHTML = `
    <div class="deck-import-preview-head">
      <strong>${integer.format(decks.length)} deck${decks.length === 1 ? "" : "s"} found</strong>
      <span>Rename any rows marked for review, then import.</span>
    </div>
    <div class="deck-import-list">
      ${decks.map((deck) => `
        <article class="deck-import-row ${deck.issues?.length ? "needs-review" : ""}" data-import-index="${escapeHtml(deck.index)}">
          <div>
            <label>
              Deck name
              <input type="text" maxlength="20" value="${escapeHtml(deck.name || "")}" data-import-name="${escapeHtml(deck.index)}">
            </label>
            ${deck.issues?.length ? `<p>${escapeHtml(deck.issues.join(" "))}</p>` : `<p>Ready to import.</p>`}
          </div>
          <span>${integer.format(deck.card_count || 0)} card${Number(deck.card_count || 0) === 1 ? "" : "s"}</span>
        </article>
      `).join("")}
    </div>
  `;
}

function deckImportNamesFromPreview() {
  const names = new Map();
  for (const input of els.importDeckPreview.querySelectorAll("[data-import-name]")) {
    names.set(Number(input.dataset.importName), input.value.trim().replace(/\s+/g, " "));
  }
  return names;
}

function containsDisallowedNameWord(value) {
  const normalized = String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const tokens = normalized.split(/\s+/).filter(Boolean);
  const compact = tokens.join("");
  return tokens.some((token) => disallowedNameWords.has(token))
    || Array.from(disallowedNameWords).some((word) => word.length >= 4 && compact.includes(word));
}

function deckImportClientNameIssues(decks) {
  const issues = new Map();
  const seen = new Map();
  const existingNames = new Set((state.decks || []).map((deck) => String(deck.name || "").trim().replace(/\s+/g, " ").toLowerCase()).filter(Boolean));
  for (const deck of decks) {
    const name = String(deck.name || "").trim().replace(/\s+/g, " ");
    const deckIssues = [];
    if (!name) deckIssues.push("Deck name is required.");
    if (name.length > 20) deckIssues.push("Deck name must be 20 characters or fewer.");
    if (containsDisallowedNameWord(name)) deckIssues.push("Deck name contains language that is not allowed.");
    const lowerName = name.toLowerCase();
    if (lowerName) {
      if (seen.has(lowerName)) {
        deckIssues.push("Deck name is duplicated in this import.");
        issues.set(seen.get(lowerName), [...(issues.get(seen.get(lowerName)) || []), "Deck name is duplicated in this import."]);
      } else {
        seen.set(lowerName, deck.index);
      }
      if (existingNames.has(lowerName)) {
        deckIssues.push("Deck name already exists in your account.");
      }
    }
    if (deckIssues.length) issues.set(deck.index, deckIssues);
  }
  return issues;
}

function applyDeckImportPreviewNames() {
  if (!state.pendingDeckImport) return [];
  const names = deckImportNamesFromPreview();
  return state.pendingDeckImport.normalized_decks.map((deck) => ({
    ...deck,
    name: names.get(Number(deck.index)) || deck.name,
  }));
}

async function previewDeckImport() {
  const text = els.importDeckJsonText.value.trim();
  if (!text) {
    setStatus("Paste or upload deck JSON/CSV first.", "error", els.importDeckStatus);
    return;
  }
  state.pendingDeckImport = null;
  els.commitImportDeckButton.disabled = true;
  setStatus("Reviewing import...", "", els.importDeckStatus);
  await loadDecks();
  const preview = await api("/api/decks/import/preview", {
    method: "POST",
    body: JSON.stringify(deckImportPayloadFromText(text)),
  });
  state.pendingDeckImport = preview;
  renderDeckImportPreview(preview.decks || []);
  const needsReview = (preview.decks || []).some((deck) => deck.needs_rename || deck.issues?.length);
  els.commitImportDeckButton.disabled = needsReview;
  setStatus(
    needsReview ? "Rename the highlighted decks before importing." : "Import looks good.",
    needsReview ? "error" : "success",
    els.importDeckStatus,
  );
}

function refreshDeckImportReviewState() {
  if (!state.pendingDeckImport) return;
  const decks = applyDeckImportPreviewNames();
  const issues = deckImportClientNameIssues(decks);
  const previewDecks = (state.pendingDeckImport.decks || []).map((deck) => {
    const renamed = decks.find((item) => Number(item.index) === Number(deck.index));
    return {
      ...deck,
      name: renamed?.name || "",
      issues: issues.get(Number(deck.index)) || [],
      needs_rename: issues.has(Number(deck.index)),
    };
  });
  renderDeckImportPreview(previewDecks);
  els.commitImportDeckButton.disabled = previewDecks.some((deck) => deck.needs_rename);
  if (els.commitImportDeckButton.disabled) {
    setStatus("Resolve highlighted deck names before importing.", "error", els.importDeckStatus);
  } else {
    setStatus("Names look good. Ready to import.", "success", els.importDeckStatus);
  }
}

async function commitDeckImport() {
  if (!state.pendingDeckImport) {
    await previewDeckImport();
    if (!state.pendingDeckImport || els.commitImportDeckButton.disabled) return;
  }
  const decks = applyDeckImportPreviewNames();
  const issues = deckImportClientNameIssues(decks);
  if (issues.size) {
    refreshDeckImportReviewState();
    return;
  }
  setStatus("Importing decks...", "", els.importDeckStatus);
  const result = await api("/api/decks/import/commit", {
    method: "POST",
    body: JSON.stringify({ decks }),
  });
  closeImportDeckModal();
  await loadDecks();
  if (result.decks?.length === 1) {
    await openDeckPage(result.decks[0].id);
  } else {
    setStatus(`Imported ${integer.format(result.imported || 0)} decks.`, "success", els.decksStatus);
  }
}

function todayValue() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function priceForVariant(card, variant) {
  const prices = card.prices || {};
  const variantText = String(variant || "").toLowerCase();
  const normal = Number(prices.usd ?? card.current_usd ?? 0);
  const foil = Number(prices.usd_foil ?? card.current_usd_foil ?? 0);
  const etched = Number(prices.usd_etched ?? card.current_usd_etched ?? 0);
  if (variantText.includes("etched") && etched > 0) return etched;
  if (variantText.includes("foil") && foil > 0) return foil;
  return normal || foil || etched || 0;
}

function variantsForCard(card) {
  const finishes = card.finishes || [];
  const variants = [];
  if (finishes.includes("nonfoil")) variants.push("Normal");
  if (finishes.includes("foil")) variants.push("Foil");
  if (finishes.includes("etched")) variants.push("Etched Foil");
  return variants.length ? variants : ["Normal"];
}

function resetAddPurchaseMatrix() {
  if (els.addPurchaseRows) els.addPurchaseRows.innerHTML = "";
  if (els.addPurchaseMatrix) els.addPurchaseMatrix.hidden = true;
}

function collapseAddAdvancedFilters() {
  if (els.addAdvancedFilters) els.addAdvancedFilters.hidden = true;
  if (els.addAdvancedToggle) {
    els.addAdvancedToggle.setAttribute("aria-expanded", "false");
    els.addAdvancedToggle.textContent = "Show advanced filters";
  }
}

function conditionOptionsHtml(selected = "Near Mint") {
  return cardConditions.map((condition) => (
    `<option value="${escapeHtml(condition)}" ${condition === selected ? "selected" : ""}>${escapeHtml(condition)}</option>`
  )).join("");
}

function addPurchaseRowHtml(row = {}) {
  const rowId = row.row_id || (window.crypto?.randomUUID ? window.crypto.randomUUID() : `row-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  const variant = row.variant || "Normal";
  const condition = cardConditions.includes(row.card_condition) ? row.card_condition : "Near Mint";
  const paidPrice = Number(row.paid_price || 0.01) > 0 ? Number(row.paid_price || 0.01).toFixed(2) : "0.01";
  const acquiredDate = row.acquired_date || todayValue();
  const quantity = Number.isFinite(Number(row.quantity)) ? Math.max(0, Number(row.quantity || 0)) : 0;
  return `
    <tr class="add-purchase-row" data-row-id="${escapeHtml(rowId)}" data-variant="${escapeHtml(variant)}">
      <td><span class="add-variant-name">${escapeHtml(variant)}</span></td>
      <td>
        <select data-add-field="card_condition" aria-label="${escapeAttribute(`${variant} condition`)}">
          ${conditionOptionsHtml(condition)}
        </select>
      </td>
      <td><input data-add-field="paid_price" type="number" min="0.01" step="0.01" value="${escapeHtml(paidPrice)}" aria-label="${escapeAttribute(`${variant} price paid per card`)}"></td>
      <td><input data-add-field="acquired_date" type="date" value="${escapeHtml(acquiredDate)}" aria-label="${escapeAttribute(`${variant} date acquired`)}"></td>
      <td><input data-add-field="graded" type="checkbox" value="1" ${row.graded ? "checked" : ""} aria-label="${escapeAttribute(`${variant} graded`)}"></td>
      <td><input data-add-field="quantity" type="number" min="0" step="1" value="${escapeHtml(String(quantity))}" aria-label="${escapeAttribute(`${variant} quantity`)}"></td>
      <td><button class="secondary-button add-row-button" type="button" data-add-row-copy title="Add another condition row for ${escapeAttribute(variant)}" aria-label="Add another condition row for ${escapeAttribute(variant)}">+</button></td>
    </tr>
  `;
}

function renderAddPurchaseRows(card) {
  if (!els.addPurchaseRows || !els.addPurchaseMatrix) return;
  els.addPurchaseRows.innerHTML = variantsForCard(card).map((variant) => addPurchaseRowHtml({ variant })).join("");
  els.addPurchaseMatrix.hidden = false;
}

function duplicateAddPurchaseRow(row) {
  if (!row) return;
  const duplicate = {
    variant: row.dataset.variant || "Normal",
    card_condition: row.querySelector('[data-add-field="card_condition"]')?.value || "Near Mint",
    paid_price: row.querySelector('[data-add-field="paid_price"]')?.value || "0.01",
    acquired_date: row.querySelector('[data-add-field="acquired_date"]')?.value || todayValue(),
    graded: Boolean(row.querySelector('[data-add-field="graded"]')?.checked),
    quantity: 0,
  };
  row.insertAdjacentHTML("afterend", addPurchaseRowHtml(duplicate));
}

function normalizeScryfallColorFilter(value) {
  const aliases = {
    white: "w",
    blue: "u",
    black: "b",
    red: "r",
    green: "g",
    colorless: "c",
    colourless: "c",
  };
  const tokens = String(value || "").toLowerCase().split(/[\s,;/]+/).filter(Boolean);
  if (!tokens.length) return "";
  const normalized = tokens.map((token) => aliases[token] || token).join("").replace(/[^wubrgc]/g, "");
  return Array.from(new Set(normalized.split(""))).join("");
}

function addSearchQuery() {
  const terms = [];
  const base = els.addSearchInput.value.trim();
  const setCode = (els.addSetCodeInput?.value || "").trim();
  const color = (els.addColorInput?.value || "").trim();
  const type = (els.addTypeInput?.value || "").trim();
  if (base) terms.push(base);
  if (setCode) terms.push(`e:${setCode.replace(/\s+/g, "")}`);
  if (color) {
    const normalized = normalizeScryfallColorFilter(color);
    if (normalized) terms.push(`c:${normalized}`);
  }
  if (type) terms.push(`t:${type}`);
  return terms.join(" ").trim();
}

function addPurchasePayloadRows() {
  const rows = [];
  for (const row of els.addPurchaseRows?.querySelectorAll(".add-purchase-row") || []) {
    const quantity = Number(row.querySelector('[data-add-field="quantity"]')?.value || 0);
    if (quantity <= 0) continue;
    rows.push({
      variant: row.dataset.variant || "Normal",
      card_condition: row.querySelector('[data-add-field="card_condition"]')?.value || "Near Mint",
      paid_price: Number(row.querySelector('[data-add-field="paid_price"]')?.value || 0),
      acquired_date: row.querySelector('[data-add-field="acquired_date"]')?.value || todayValue(),
      graded: row.querySelector('[data-add-field="graded"]')?.checked ? 1 : 0,
      quantity,
    });
  }
  return rows;
}

async function hydrateAddCardSelection(preselectedCard) {
  if (!preselectedCard?.scryfall_id) return null;
  const result = await api(`/api/scryfall/cards/${encodeURIComponent(preselectedCard.scryfall_id)}`, { promptLogin: true });
  return result.card || preselectedCard;
}

function openAddCardModal(preselectedCard = null) {
  if (!state.user) {
    openAuthModal("register", "Create an account or log in before adding cards to your Collection.");
    return;
  }
  state.addResults = [];
  state.selectedAddCard = null;
  els.addSearchForm.reset();
  collapseAddAdvancedFilters();
  els.addCardForm.reset();
  els.addCardForm.scryfall_id.value = "";
  resetAddPurchaseMatrix();
  els.addSearchStatus.textContent = "";
  els.addSearchStatus.dataset.tone = "";
  els.addSearchResults.innerHTML = "";
  els.addCardForm.hidden = true;
  els.selectedAddCard.hidden = true;
  els.selectedAddCard.innerHTML = "";
  els.confirmAddCardButton.disabled = true;
  els.confirmAddNewCardButton.disabled = true;
  els.addCardOverlay.hidden = false;
  document.body.classList.add("modal-open");
  if (preselectedCard && preselectedCard.scryfall_id) {
    els.addSearchInput.value = cardTitle(preselectedCard);
    els.addSearchStatus.textContent = "Loading exact Scryfall print...";
    hydrateAddCardSelection(preselectedCard)
      .then((card) => {
        state.addResults = [card];
        renderAddResults(state.addResults);
        selectAddCard(card);
        els.addSearchStatus.textContent = "Selected exact print from Search.";
        els.addSearchStatus.dataset.tone = "";
        els.addPurchaseRows?.querySelector('[data-add-field="quantity"]')?.focus();
      })
      .catch((error) => {
        els.addSearchStatus.textContent = error.message;
        els.addSearchStatus.dataset.tone = "error";
        state.addResults = [preselectedCard];
        renderAddResults(state.addResults);
      });
  } else {
    els.addSearchInput.focus();
  }
}

function resetAddCardModalForNew() {
  state.addResults = [];
  state.selectedAddCard = null;
  els.addSearchForm.reset();
  collapseAddAdvancedFilters();
  els.addCardForm.reset();
  els.addCardForm.scryfall_id.value = "";
  resetAddPurchaseMatrix();
  els.addSearchResults.innerHTML = "";
  els.addCardForm.hidden = true;
  els.selectedAddCard.hidden = true;
  els.selectedAddCard.innerHTML = "";
  els.confirmAddCardButton.disabled = true;
  els.confirmAddNewCardButton.disabled = true;
  els.addSearchInput.focus();
}

function closeAddCardModal() {
  els.addCardOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.addResults = [];
  state.selectedAddCard = null;
  els.addSearchResults.innerHTML = "";
  els.selectedAddCard.innerHTML = "";
  els.addCardForm.hidden = true;
  resetAddPurchaseMatrix();
  els.addCardForm.reset();
  els.confirmAddCardButton.disabled = true;
  els.confirmAddNewCardButton.disabled = true;
}

function renderAddResults(cards) {
  els.addSearchResults.innerHTML = "";
  if (!cards.length) {
    els.addSearchResults.innerHTML = '<div class="empty-state">No Scryfall prints found.</div>';
    return;
  }
  for (const card of cards) {
    const button = document.createElement("button");
    button.className = "add-result";
    button.type = "button";
    button.dataset.cardId = card.scryfall_id;
    button.innerHTML = `
      <img src="${card.image_small || card.image_normal || ""}" alt="">
      <span>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)}</span>
        ${cardRulesName(card) ? `<span>Rules: ${escapeHtml(cardRulesName(card))}</span>` : ""}
        <span>${escapeHtml(card.rarity || "unknown")} - ${dollars.format(priceForVariant(card, "Normal"))}</span>
        <span class="owned-count">Owned: ${integer.format(card.owned_quantity || 0)}</span>
      </span>
    `;
    button.addEventListener("click", () => selectAddCard(card));
    els.addSearchResults.appendChild(button);
  }
}

async function searchScryfallForAdd() {
  const query = addSearchQuery();
  if (query.length < 2) {
    els.addSearchStatus.textContent = "Type at least 2 characters or use an advanced filter.";
    return;
  }
  els.addSearchButton.disabled = true;
  els.addSearchStatus.textContent = "Searching Scryfall...";
  try {
    const language = (state.settings && state.settings.language) || "en";
    const result = await api(`/api/scryfall/search?q=${encodeURIComponent(query)}&lang=${encodeURIComponent(language)}`);
    state.addResults = result.cards || [];
    renderAddResults(state.addResults);
    els.addSearchStatus.textContent = `${integer.format(state.addResults.length)} results`;
  } catch (error) {
    els.addSearchStatus.textContent = error.message;
    els.addSearchStatus.dataset.tone = "error";
  } finally {
    els.addSearchButton.disabled = false;
  }
}

function selectAddCard(card) {
  state.selectedAddCard = card;
  els.addCardForm.scryfall_id.value = card.scryfall_id;
  els.addCardForm.hidden = false;
  renderAddPurchaseRows(card);
  els.confirmAddCardButton.disabled = false;
  els.confirmAddNewCardButton.disabled = false;
  for (const result of els.addSearchResults.querySelectorAll(".add-result")) {
    result.classList.toggle("is-selected", result.dataset.cardId === card.scryfall_id);
  }
  renderSelectedAddCard();
}

function renderSelectedAddCard() {
  const card = state.selectedAddCard;
  if (!card) return;
  const variants = variantsForCard(card);
  els.selectedAddCard.hidden = false;
  els.selectedAddCard.innerHTML = `
    <img src="${card.image_small || card.image_normal || ""}" alt="">
    <div>
      <strong>${escapeHtml(cardTitle(card))}</strong>
      <p>${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)} - ${escapeHtml(card.type_line || "")}</p>
      ${cardRulesName(card) ? `<span>Rules: ${escapeHtml(cardRulesName(card))}</span>` : ""}
      <span>${escapeHtml(variants.join(", "))} variants detected</span>
      <span class="owned-count">Owned: ${integer.format(card.owned_quantity || 0)}</span>
    </div>
  `;
}

function openSettingsModal() {
  els.settingsForm.language.value = (state.settings && state.settings.language) || "en";
  els.settingsForm.theme.value = (state.settings && state.settings.theme) || "light";
  els.settingsOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.settingsForm.language.focus();
}

function closeSettingsModal() {
  els.settingsOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.settingsForm.reset();
}

function renderSettingsPage() {
  if (!els.settingsPageForm) return;
  const settings = state.settings || defaultSettings();
  const user = state.user || {};
  els.settingsPageForm.name.value = user.name || "";
  els.settingsPageForm.public_email.value = user.public_email || "";
  els.settingsPageForm.contact_whatsapp.value = user.contact_whatsapp || "";
  els.settingsPageForm.contact_signal.value = user.contact_signal || "";
  els.settingsPageForm.contact_telegram.value = user.contact_telegram || "";
  els.settingsPageForm.contact_discord.value = user.contact_discord || "";
  els.settingsPageForm.contact_website.value = user.contact_website || "";
  els.settingsPageForm.language.value = settings.language || "en";
  els.settingsPageForm.theme.value = settings.theme || "light";
  if (els.settingsAccountEmail) {
    els.settingsAccountEmail.textContent = state.user ? state.user.email : "Not logged in";
  }
  if (els.settingsAppVersion) {
    els.settingsAppVersion.textContent = state.appConfig?.app_version || "Unknown";
  }
  renderBillingSettings();
}

function renderBillingSettings() {
  if (!els.billingPlanStatus) return;
  const user = state.user || {};
  const configured = Boolean(state.appConfig?.stripe_configured);
  const role = user.role || "normal";
  const isPro = role === "pro" || role === "admin" || Boolean(user.is_pro);
  const status = user.subscription_status || "";
  const planLabel = user.subscription_plan_label || (user.subscription_plan === "yearly" ? "Pro Yearly" : user.subscription_plan === "monthly" ? "Pro Monthly" : "Pro");
  const periodDate = user.subscription_current_period_end ? formatCompactDate(user.subscription_current_period_end) : "";
  const canceledDate = user.subscription_canceled_at ? formatCompactDate(user.subscription_canceled_at) : "";
  const endedDate = user.subscription_ended_at ? formatCompactDate(user.subscription_ended_at) : "";
  els.billingPlanStatus.textContent = role === "admin" ? "Admin" : isPro ? planLabel : "Normal";
  const hasSubscriptionHistory = Boolean(status || user.subscription_plan || user.stripe_price_id || periodDate || canceledDate || endedDate);
  if (els.billingMetaList) {
    if (hasSubscriptionHistory) {
      const periodLabel = user.subscription_cancel_at_period_end || endedDate || status === "canceled" ? "Ends" : "Renews";
      els.billingMetaList.hidden = false;
      els.billingMetaList.innerHTML = `
        <div><dt>Plan</dt><dd>${escapeHtml(planLabel)}</dd></div>
        <div><dt>Status</dt><dd>${escapeHtml(status || (isPro ? "active" : "normal"))}</dd></div>
        ${periodDate ? `<div><dt>${periodLabel}</dt><dd>${escapeHtml(periodDate)}</dd></div>` : ""}
        ${canceledDate ? `<div><dt>Canceled</dt><dd>${escapeHtml(canceledDate)}</dd></div>` : ""}
        ${endedDate ? `<div><dt>Ended</dt><dd>${escapeHtml(endedDate)}</dd></div>` : ""}
      `;
    } else {
      els.billingMetaList.hidden = true;
      els.billingMetaList.innerHTML = "";
    }
  }
  if (!configured) {
    els.billingHelpText.textContent = "Billing is not configured on this server.";
  } else if (role === "admin") {
    els.billingHelpText.textContent = "Admin accounts include Pro features.";
  } else if (isPro) {
    const schedule = user.subscription_cancel_at_period_end
      ? `${canceledDate ? ` Canceled ${canceledDate}.` : ""}${periodDate ? ` Access ends ${periodDate}.` : " Access ends at the end of the current billing period."}`
      : `${periodDate ? ` Renews ${periodDate}.` : ""}`;
    els.billingHelpText.textContent = `Your ${planLabel} subscription is ${status || "active"}.${schedule}`;
  } else if (status) {
    const ended = endedDate || periodDate;
    els.billingHelpText.textContent = `Your ${planLabel} subscription is ${status}.${ended ? ` Membership ended ${ended}.` : ""} Upgrade to restore Pro benefits.`;
  } else {
    els.billingHelpText.textContent = "Upgrade to Pro for unlimited decks, containers, and wishlists.";
  }
  const canCheckout = configured && role !== "admin";
  els.billingMonthlyButton.disabled = !canCheckout;
  els.billingYearlyButton.disabled = !canCheckout;
  els.billingPortalButton.disabled = !configured || !user.has_stripe_customer;
}

async function startBillingCheckout(plan) {
  const result = await api("/api/billing/checkout", {
    method: "POST",
    body: JSON.stringify({ plan }),
  });
  if (!result.url) throw new Error("Stripe did not return a checkout URL.");
  window.location.href = result.url;
}

async function openBillingPortal() {
  const result = await api("/api/billing/portal", {
    method: "POST",
    body: JSON.stringify({}),
  });
  if (!result.url) throw new Error("Stripe did not return a billing portal URL.");
  window.location.href = result.url;
}

async function openChangelogModal() {
  if (!els.changelogOverlay || !els.changelogText) return;
  els.changelogText.textContent = "Loading...";
  els.changelogOverlay.hidden = false;
  document.body.classList.add("modal-open");
  try {
    const result = await api("/api/changelog", { promptLogin: false });
    els.changelogText.textContent = result.changelog || "No release notes have been written yet.";
  } catch (error) {
    els.changelogText.textContent = error.message;
  }
}

function closeChangelogModal() {
  if (!els.changelogOverlay) return;
  els.changelogOverlay.hidden = true;
  document.body.classList.remove("modal-open");
}

function openMembershipBenefitsModal() {
  if (!els.membershipBenefitsOverlay) return;
  els.membershipBenefitsOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeMembershipBenefitsModal() {
  if (!els.membershipBenefitsOverlay) return;
  els.membershipBenefitsOverlay.hidden = true;
  document.body.classList.remove("modal-open");
}

function renderProfileImagePreview(dataUrl) {
  if (!els.profileImagePreview) return;
  if (!dataUrl) {
    els.profileImagePreview.innerHTML = '<span>No profile picture selected.</span>';
    return;
  }
  els.profileImagePreview.innerHTML = `<img src="${escapeHtml(dataUrl)}" alt="Profile picture preview"><button class="secondary-button compact-button" type="button">Remove</button>`;
  els.profileImagePreview.querySelector("button")?.addEventListener("click", () => {
    if (els.profileForm) els.profileForm.profile_image.value = "";
    if (els.profileImageInput) els.profileImageInput.value = "";
    renderProfileImagePreview("");
  });
}

function openProfileModal() {
  if (!els.profileOverlay || !els.profileForm) return;
  const user = state.user || {};
  els.profileForm.name.value = user.name || "";
  els.profileForm.about_me.value = user.about_me || "";
  els.profileForm.contact_discord.value = user.contact_discord || "";
  els.profileForm.contact_instagram.value = user.contact_instagram || "";
  els.profileForm.contact_bluesky.value = user.contact_bluesky || "";
  els.profileForm.contact_threads.value = user.contact_threads || "";
  els.profileForm.profile_image.value = user.profile_image || "";
  if (els.profileImageInput) els.profileImageInput.value = "";
  renderProfileImagePreview(user.profile_image || "");
  setStatus("", "", els.profileStatus);
  els.profileOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.profileForm.name.focus();
}

function closeProfileModal() {
  if (!els.profileOverlay) return;
  els.profileOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  if (els.profileForm) els.profileForm.reset();
  if (els.profileImageInput) els.profileImageInput.value = "";
  renderProfileImagePreview("");
}

function profilePayloadFromForm() {
  const formValues = Object.fromEntries(new FormData(els.profileForm).entries());
  return userSettingsPayload({
    name: formValues.name || "",
    about_me: formValues.about_me || "",
    profile_image: formValues.profile_image || "",
    contact_discord: formValues.contact_discord || "",
    contact_instagram: formValues.contact_instagram || "",
    contact_bluesky: formValues.contact_bluesky || "",
    contact_threads: formValues.contact_threads || "",
  });
}

async function readProfileImageFile(file) {
  if (!file) return "";
  if (!/^image\/(png|jpe?g|webp|gif)$/i.test(file.type || "")) {
    throw new Error("Choose a PNG, JPG, WebP, or GIF image.");
  }
  if (file.size > 650 * 1024) {
    throw new Error("Choose an image under 650 KB.");
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => resolve(String(reader.result || "")));
    reader.addEventListener("error", () => reject(new Error("Could not read that image.")));
    reader.readAsDataURL(file);
  });
}

function userSettingsPayload(overrides = {}) {
  const settings = state.settings || defaultSettings();
  const user = state.user || {};
  return {
    name: user.name || "",
    public_email: user.public_email || "",
    contact_whatsapp: user.contact_whatsapp || "",
    contact_signal: user.contact_signal || "",
    contact_telegram: user.contact_telegram || "",
    contact_discord: user.contact_discord || "",
    contact_website: user.contact_website || "",
    contact_instagram: user.contact_instagram || "",
    contact_bluesky: user.contact_bluesky || "",
    contact_threads: user.contact_threads || "",
    about_me: user.about_me || "",
    profile_image: user.profile_image || "",
    language: settings.language || "en",
    theme: settings.theme || "light",
    ...overrides,
  };
}

async function saveUserSettings(payload) {
  if (!state.user) {
    saveSettings(payload);
    return;
  }
  const result = await api("/api/user/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  state.user = result.user;
  syncSettingsFromUser(state.user);
  updateAuthUi();
}

function renderDecks(decks) {
  els.decksGrid.innerHTML = "";
  if (!decks.length) {
    els.decksGrid.innerHTML = '<div class="empty-state">No decks yet.</div>';
    return;
  }
  for (const deck of decks) {
    const item = document.createElement("article");
    const previewImages = uniqueDeckPreviewImages(deck);
    item.className = `deck-card${previewImages.length ? " has-deck-preview" : ""}`;
    item.tabIndex = 0;
    item.setAttribute("role", "button");
    item.dataset.deckId = deck.id;
    item.setAttribute("aria-label", `Open ${deck.name}`);
    item.innerHTML = `
      ${deckPreviewImagesHtml(previewImages)}
      <div>
        <p class="eyebrow">Deck${Number(deck.is_private || 0) ? " - Private" : ""}</p>
        <h3>${escapeHtml(deck.name)}</h3>
      </div>
      <strong>${integer.format(deck.card_count || 0)}</strong>
      <span>${integer.format(deck.unique_card_count || 0)} unique cards assigned</span>
      <button class="deck-blog-button" type="button" aria-label="Write blog post about ${escapeAttribute(deck.name || "deck")}" title="Write blog post"><span class="blog-post-icon" aria-hidden="true"></span></button>
    `;
    const openDeck = () => {
      openDeckPage(deck.id).catch((error) => {
        els.decksStatus.textContent = error.message;
      });
    };
    item.addEventListener("click", (event) => {
      if (event.target.closest("button")) return;
      openDeck();
    });
    item.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      if (event.target.closest("button")) return;
      event.preventDefault();
      openDeck();
    });
    item.querySelector(".deck-blog-button")?.addEventListener("click", (event) => {
      event.stopPropagation();
      openDeckBlogModal(deck);
    });
    els.decksGrid.appendChild(item);
  }
}

function browseDeckCardTableHtml(deck) {
  const cards = deck.cards || [];
  if (!cards.length) {
    return '<div class="browse-deck-empty">No cards listed yet.</div>';
  }
  const visible = cards.slice(0, 8);
  const hiddenCount = Math.max(0, Number(deck.unique_card_count || cards.length) - visible.length);
  return `
    <table class="browse-deck-card-table">
      <thead>
        <tr>
          <th>Card</th>
          <th>Variant</th>
          <th>Qty</th>
        </tr>
      </thead>
      <tbody>
        ${visible.map((card) => `
          <tr class="deck-card-preview-trigger browse-deck-card-row" role="button" tabindex="0" data-card-id="${escapeHtml(card.scryfall_id || card.card_id || "")}" data-variant="${escapeHtml(card.variant || "Normal")}">
            <td>${escapeHtml(cardTitle(card))}</td>
            <td>${escapeHtml(card.variant || "Normal")}</td>
            <td>${integer.format(deckQuantity(card))}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
    ${hiddenCount > 0 ? `<p class="browse-deck-more">+ ${integer.format(hiddenCount)} more unique card${hiddenCount === 1 ? "" : "s"}</p>` : ""}
  `;
}

function renderBrowseDecks(decks) {
  els.browseDecksGrid.innerHTML = "";
  if (!decks.length) {
    els.browseDecksGrid.innerHTML = '<div class="empty-state">No public decks are available yet.</div>';
    return;
  }
  for (const deck of decks) {
    const item = document.createElement("article");
    const previewImages = uniqueDeckPreviewImages(deck);
    item.className = `deck-card browse-deck-card${previewImages.length ? " has-deck-preview" : ""}`;
    item.innerHTML = `
      ${deckPreviewImagesHtml(previewImages)}
      <div class="browse-deck-head">
        <div>
          <p class="eyebrow">Public deck${deck.owner_name ? ` - ${displayNameHtml(deck.owner_name, { is_pro: deck.owner_is_pro, role: deck.owner_role })}` : ""}</p>
          <h3>${escapeHtml(deck.name || "Deck")}</h3>
        </div>
        <div class="browse-deck-actions" aria-label="Deck actions">
          <button class="share-button browse-deck-favorite ${deck.favorite_deck ? "is-favorite" : ""}" type="button" aria-label="${deck.favorite_deck ? "Remove favorite" : "Favorite deck"}" title="${deck.viewer_is_owner ? "This is your deck" : deck.favorite_deck ? "Remove favorite" : "Favorite deck"}">☆</button>
          <button class="share-button browse-deck-import" type="button" aria-label="Save to my Decks" title="${deck.viewer_is_owner ? "This is already your deck" : "Save to my Decks"}"><span class="copy-deck-icon" aria-hidden="true"></span></button>
          <button class="share-button browse-deck-share" type="button" aria-label="Share URL" title="Share URL">&#8599;</button>
          <button class="share-button browse-deck-email" type="button" aria-label="Email deck" title="Email deck"><span class="send-icon" aria-hidden="true"></span></button>
        </div>
      </div>
      <div class="browse-deck-meta">
        <strong>${integer.format(deck.card_count || 0)} cards</strong>
        <span>${integer.format(deck.unique_card_count || 0)} unique</span>
      </div>
      ${deck.description ? `<p class="browse-deck-description">${escapeHtml(deck.description)}</p>` : ""}
      ${browseDeckCardTableHtml(deck)}
    `;
    item.querySelector(".browse-deck-favorite").addEventListener("click", () => {
      if (deck.viewer_is_owner) {
        setStatus("This is already your deck.", "", els.browseDecksStatus);
        return;
      }
      toggleSharedDeckFavorite(deck, item.querySelector(".browse-deck-favorite")).then(loadBrowseDecks).catch((error) => setStatus(error.message, "error", els.browseDecksStatus));
    });
    item.querySelector(".browse-deck-import").addEventListener("click", () => {
      if (deck.viewer_is_owner) {
        setStatus("This is already in your deck list.", "", els.browseDecksStatus);
        return;
      }
      importSharedDeck(deck, item.querySelector(".browse-deck-import")).catch((error) => setStatus(error.message, "error", els.browseDecksStatus));
    });
    item.querySelector(".browse-deck-share").addEventListener("click", () => openDeckShareModal(deck));
    item.querySelector(".browse-deck-email").addEventListener("click", () => {
      if (!state.user) {
        openAuthModal("login", "Log in to email a deck.");
        return;
      }
      openEmailShareModal("shared-deck", deck);
    });
    wireDeckCardPreviewRows(item, deck.cards || []);
    item.addEventListener("dblclick", () => {
      window.open(shareUrlForDeck(deck), "_blank", "noopener");
    });
    els.browseDecksGrid.appendChild(item);
  }
}

function deckEditorFormSnapshot(form) {
  if (!form) return "";
  return JSON.stringify({
    name: form.elements.name?.value || "",
    description: form.elements.description?.value || "",
    internal_notes: form.elements.internal_notes?.value || "",
    external_notes: form.elements.external_notes?.value || "",
    is_private: Boolean(form.elements.is_private?.checked),
  });
}

function setDeckEditorDirty(isDirty, message = true) {
  state.deckEditorDirty = Boolean(isDirty);
  const status = els.deckEditorShell?.querySelector("#deckEditorStatus");
  if (status && message) {
    status.textContent = state.deckEditorDirty ? "Unsaved changes." : "";
    status.dataset.tone = state.deckEditorDirty ? "warning" : "";
  }
}

function updateDeckEditorDirtyState(form) {
  setDeckEditorDirty(deckEditorFormSnapshot(form) !== state.deckEditorSnapshot);
}

function confirmDiscardDeckEditorChanges() {
  if (!state.deckEditorDirty) return true;
  return window.confirm("You have unsaved deck changes. Leave without saving?");
}

function deckIsPrivateNow(deck) {
  const form = els.deckEditorShell?.querySelector("#deckEditorForm");
  if (form && state.activeDeck && String(state.activeDeck.id) === String(deck?.id || "")) {
    return Boolean(form.elements.is_private?.checked);
  }
  return Boolean(Number(deck?.is_private || 0));
}

function discardDeckEditorChanges() {
  resetDeckEditorDirtyState();
}

function resetDeckEditorDirtyState() {
  state.deckEditorDirty = false;
  state.deckEditorSnapshot = "";
}

function uniqueDeckPreviewImages(deck) {
  return Array.from(new Set((deck.preview_images || []).filter(Boolean))).slice(0, 5);
}

function deckPreviewImagesHtml(images) {
  if (!images.length) return "";
  return `
    <div class="deck-card-art-stack" aria-hidden="true">
      ${images.map((src, index) => `<img src="${escapeHtml(src)}" alt="" style="--slot:${index};">`).join("")}
    </div>
  `;
}

function renderDeckCardsEditable(deck) {
  const cards = deck.cards || [];
  if (!cards.length) {
    return '<div class="empty-state">No cards in this deck yet.</div>';
  }
  return cards.map((card) => `
    <article class="deck-card-row deck-card-preview-trigger ${Number(card.short_quantity || 0) > 0 ? "is-short" : ""}" role="button" tabindex="0" data-card-id="${escapeHtml(card.scryfall_id || card.card_id || "")}" data-variant="${escapeHtml(card.variant || "Normal")}">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
        ${deckInventoryStatusHtml(card)}
      </div>
      <b>Qty ${integer.format(deckQuantity(card))}</b>
      <button class="remove-deck-card-button" type="button" data-card-id="${escapeHtml(card.scryfall_id || card.card_id || "")}" data-variant="${escapeHtml(card.variant || "Normal")}" aria-label="Remove card from deck" title="Remove card"><span class="trash-icon" aria-hidden="true"></span></button>
    </article>
  `).join("");
}

function deckPreviewCardByRow(row, cards) {
  return (cards || []).find((candidate) => (
    (candidate.scryfall_id || candidate.card_id) === row.dataset.cardId
    && (candidate.variant || "Normal") === (row.dataset.variant || "Normal")
  ));
}

function wireDeckCardPreviewRows(container, cards) {
  if (!container) return;
  for (const row of container.querySelectorAll(".deck-card-preview-trigger")) {
    const open = () => {
      const card = deckPreviewCardByRow(row, cards);
      if (card) {
        openDeckCardPreviewModal(card).catch((error) => setStatus(error.message, "error"));
      }
    };
    row.addEventListener("click", open);
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open();
      }
    });
  }
}

function closeDeckCardPreviewModal() {
  els.deckCardPreviewOverlay.hidden = true;
  if (!document.querySelector(".modal-overlay:not([hidden])")) {
    document.body.classList.remove("modal-open");
  }
  els.deckCardPreviewShell.innerHTML = "";
}

function closeScryfallJsonModal() {
  els.scryfallJsonOverlay.hidden = true;
  els.scryfallJsonText.value = "";
  setStatus("", "", els.scryfallJsonStatus);
  if (!document.querySelector(".modal-overlay:not([hidden])")) {
    document.body.classList.remove("modal-open");
  }
}

async function openScryfallJsonModal(card) {
  const cardId = card.scryfall_id || card.card_id;
  if (!cardId) return;
  els.scryfallJsonTitle.textContent = `${cardTitle(card)} JSON`;
  els.scryfallJsonText.value = "Loading Scryfall JSON...";
  setStatus("", "", els.scryfallJsonStatus);
  els.scryfallJsonOverlay.hidden = false;
  document.body.classList.add("modal-open");
  try {
    const payload = await api(`/api/cards/${encodeURIComponent(cardId)}/scryfall-json`);
    els.scryfallJsonText.value = JSON.stringify(payload, null, 2);
    els.scryfallJsonText.focus();
    els.scryfallJsonText.select();
  } catch (error) {
    els.scryfallJsonText.value = "";
    setStatus(error.message, "error", els.scryfallJsonStatus);
  }
}

function renderDeckCardPreviewModal(card, sourceCard) {
  const specialClass = isSpecialVariant(card.variant) ? " is-special" : "";
  const deckQty = deckQuantity(sourceCard || card);
  els.deckCardPreviewTitle.textContent = cardTitle(card);
  els.deckCardPreviewShell.innerHTML = `
    <article class="shared-card deck-card-preview-card${specialClass}">
      <div class="card-detail-media">
        <a class="shared-card-art" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" title="Open on Scryfall">
          <img src="${escapeHtml(card.image_normal || card.image_small || "")}" alt="${escapeHtml(cardTitle(card))}">
        </a>
      </div>
      <div class="shared-card-copy">
        <p class="eyebrow">Deck card</p>
        <h2>${escapeHtml(cardTitle(card))}</h2>
        <div class="card-divider"></div>
        <p>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.rarity || "unknown")}</p>
        ${cardRulesName(card) ? `<p>Rules: ${escapeHtml(cardRulesName(card))}</p>` : ""}
        <p>${escapeHtml(card.type_line || "")}</p>
        <div class="detail-pill-row">
          <span>${escapeHtml(card.variant || "Normal")}</span>
          <span>${escapeHtml(cardTypeLabel(card))}</span>
          <span>${escapeHtml(cardColorLabel(card))}</span>
        </div>
        <dl class="shared-card-details">
          <div>
            <dt>Deck Qty</dt>
            <dd>${integer.format(deckQty)}</dd>
          </div>
          <div>
            <dt>Owned</dt>
            <dd>${integer.format(card.owned_quantity ?? card.quantity ?? 0)}</dd>
          </div>
          <div>
            <dt>Market Price</dt>
            <dd>${dollars.format(card.market_price ?? card.display_price ?? 0)}</dd>
          </div>
          <div>
            <dt>Set</dt>
            <dd>${escapeHtml(card.set_name || "")}</dd>
          </div>
        </dl>
      </div>
      <aside class="card-detail-toolbar" aria-label="Card actions">
        <a class="detail-action-button detail-card-page-button" href="${escapeHtml(cardDetailUrl(card))}" aria-label="Open full card page" title="Open full card page"><span class="open-card-page-icon" aria-hidden="true"></span></a>
        <a class="detail-action-button detail-scryfall-button" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" aria-label="View on Scryfall" title="View on Scryfall">S</a>
        <button class="detail-action-button detail-scryfall-json-button" type="button" aria-label="View Scryfall JSON" title="View Scryfall JSON">{}</button>
      </aside>
    </article>
  `;
  els.deckCardPreviewShell.querySelector(".detail-scryfall-json-button")?.addEventListener("click", () => {
    openScryfallJsonModal(card).catch((error) => setStatus(error.message, "error"));
  });
  els.deckCardPreviewOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

async function openDeckCardPreviewModal(sourceCard) {
  const cardId = sourceCard.scryfall_id || sourceCard.card_id;
  if (!cardId) return;
  els.deckCardPreviewTitle.textContent = cardTitle(sourceCard);
  els.deckCardPreviewShell.innerHTML = '<div class="empty-state">Loading card...</div>';
  els.deckCardPreviewOverlay.hidden = false;
  document.body.classList.add("modal-open");
  try {
    const variant = sourceCard.variant || "Normal";
    const endpoint = state.user
      ? `/api/cards/${encodeURIComponent(cardId)}/detail?variant=${encodeURIComponent(variant)}`
      : `/api/cards/${encodeURIComponent(cardId)}/public?variant=${encodeURIComponent(variant)}`;
    const detail = await api(endpoint);
    renderDeckCardPreviewModal({ ...sourceCard, ...detail, variant }, sourceCard);
  } catch (error) {
    els.deckCardPreviewShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderDeckEditor(deck) {
  const cards = deck.cards || [];
  state.activeDeck = deck;
  showPage("deck-editor");
  els.deckEditorShell.innerHTML = `
    <section class="deck-editor-layout">
      <div class="deck-editor-main">
        <div class="deck-editor-head">
          <div>
            <p class="eyebrow">Deck editor</p>
            <h1>${escapeHtml(deck.name || "Deck")}</h1>
            <span>${integer.format(deck.card_count || cards.reduce((total, card) => total + deckQuantity(card), 0))} cards - ${integer.format(deck.unique_card_count || cards.length)} unique</span>
          </div>
          <button class="primary-button" type="button" data-deck-action="add-card">+ Add Card</button>
        </div>
        <div class="deck-detail-list deck-editor-card-list">
          ${renderDeckCardsEditable(deck)}
        </div>
      </div>
      <aside class="deck-editor-side">
        <form id="deckEditorForm" class="deck-editor-form">
          <label>
            Deck Name
            <input name="name" type="text" maxlength="20" value="${escapeAttribute(deck.name || "")}" required>
          </label>
          <label>
            Description
            <textarea name="description" maxlength="500" rows="5" placeholder="Public summary for this deck">${escapeHtml(deck.description || "")}</textarea>
          </label>
          <label>
            Internal Notes
            <textarea name="internal_notes" maxlength="2000" rows="7" placeholder="Private notes only you can see">${escapeHtml(deck.internal_notes || "")}</textarea>
          </label>
          <label>
            External Notes
            <textarea name="external_notes" maxlength="2000" rows="7" placeholder="Public notes shown on shared deck pages">${escapeHtml(deck.external_notes || "")}</textarea>
          </label>
          <label class="deck-private-toggle">
            <input name="is_private" type="checkbox" value="1" ${Number(deck.is_private || 0) ? "checked" : ""}>
            <span>
              <strong>Private</strong>
              <small>Hide this deck from Browse Decks.</small>
            </span>
          </label>
          <div class="deck-editor-actions">
            <button class="primary-button" type="submit">Save</button>
            <button class="share-button" type="button" data-deck-action="email" aria-label="Email deck" title="Email deck"><span class="send-icon" aria-hidden="true"></span></button>
            <button class="share-button" type="button" data-deck-action="share" aria-label="Share deck" title="Share deck">&#8599;</button>
            <button class="share-button" type="button" data-deck-action="blog" aria-label="Write blog post about deck" title="Write blog post"><span class="blog-post-icon" aria-hidden="true"></span></button>
            <button class="share-button deck-json-button" type="button" data-deck-action="json" aria-label="Copy deck JSON" title="Copy deck JSON">{}</button>
            <button class="share-button" type="button" data-deck-action="full-json" aria-label="Export full deck JSON" title="Export full deck JSON"><span class="extract-json-icon" aria-hidden="true"></span></button>
          </div>
          <button class="danger-action-button deck-editor-delete" type="button" data-deck-action="delete">
            <span class="trash-icon" aria-hidden="true"></span>
            <span>Delete Deck</span>
          </button>
          <div id="deckEditorStatus" class="status" aria-live="polite"></div>
        </form>
      </aside>
    </section>
  `;
  wireDeckCardPreviewRows(els.deckEditorShell.querySelector(".deck-editor-card-list"), cards);
  const status = els.deckEditorShell.querySelector("#deckEditorStatus");
  const deckEditorForm = els.deckEditorShell.querySelector("#deckEditorForm");
  state.deckEditorSnapshot = deckEditorFormSnapshot(deckEditorForm);
  setDeckEditorDirty(false, false);
  deckEditorForm.addEventListener("input", () => updateDeckEditorDirtyState(deckEditorForm));
  deckEditorForm.addEventListener("change", () => updateDeckEditorDirtyState(deckEditorForm));
  deckEditorForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "Saving deck...";
    status.dataset.tone = "";
    const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
    payload.is_private = event.currentTarget.elements.is_private.checked ? "1" : "0";
    try {
      const result = await api(`/api/decks/${encodeURIComponent(deck.id)}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      resetDeckEditorDirtyState();
      renderDeckEditor(result.deck);
      await loadDecks();
      const nextStatus = els.deckEditorShell.querySelector("#deckEditorStatus");
      nextStatus.textContent = "Deck saved.";
      nextStatus.dataset.tone = "";
    } catch (error) {
      status.textContent = error.message;
      status.dataset.tone = "error";
    }
  });
  els.deckEditorShell.querySelector('[data-deck-action="add-card"]').addEventListener("click", openDeckCardSearchModal);
  els.deckEditorShell.querySelector('[data-deck-action="email"]').addEventListener("click", () => openEmailDeckModal(state.activeDeck));
  els.deckEditorShell.querySelector('[data-deck-action="share"]').addEventListener("click", () => openDeckShareModal(state.activeDeck));
  els.deckEditorShell.querySelector('[data-deck-action="blog"]').addEventListener("click", () => openDeckBlogModal(state.activeDeck));
  els.deckEditorShell.querySelector('[data-deck-action="json"]').addEventListener("click", () => openDeckJsonModal(state.activeDeck, false));
  els.deckEditorShell.querySelector('[data-deck-action="full-json"]').addEventListener("click", () => openDeckJsonModal(state.activeDeck, true));
  els.deckEditorShell.querySelector('[data-deck-action="delete"]').addEventListener("click", () => {
    deleteActiveDeck().catch((error) => {
      status.textContent = error.message;
      status.dataset.tone = "error";
    });
  });
  for (const button of els.deckEditorShell.querySelectorAll(".remove-deck-card-button")) {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const card = cards.find((candidate) => (
        (candidate.scryfall_id || candidate.card_id) === button.dataset.cardId
        && (candidate.variant || "Normal") === (button.dataset.variant || "Normal")
      ));
      if (!card) return;
      removeCardFromActiveDeck(card).catch((error) => {
        status.textContent = error.message;
        status.dataset.tone = "error";
      });
    });
  }
}

async function loadDeckEditor(deckId) {
  showPage("deck-editor");
  els.deckEditorShell.innerHTML = '<div class="empty-state">Loading deck...</div>';
  try {
    const deck = await api(`/api/decks/${encodeURIComponent(deckId)}`);
    renderDeckEditor(deck);
  } catch (error) {
    els.deckEditorShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function openDeckPage(deckId) {
  if (!deckId) return;
  if (deckEditorIsVisible() && state.deckEditorDirty) {
    if (!confirmDiscardDeckEditorChanges()) return;
    discardDeckEditorChanges();
  }
  window.history.pushState({}, "", `/decks/${encodeURIComponent(deckId)}`);
  await loadDeckEditor(deckId);
}

function deckEditorIsVisible() {
  return !document.querySelector('[data-page="deck-editor"]')?.hidden;
}

function renderActiveDeck(deck) {
  if (deckEditorIsVisible()) {
    renderDeckEditor(deck);
  } else {
    renderDeckDetail(deck);
  }
}

function renderDeckDetail(deck, readonly = false) {
  const cards = deck.cards || [];
  state.activeDeck = deck;
  els.deckDetailTitle.textContent = deck.name || "Deck";
  els.deckDetailCards.innerHTML = "";
  if (!cards.length) {
    els.deckDetailCards.innerHTML = '<div class="empty-state">No cards in this deck yet.</div>';
    return;
  }
  for (const card of cards) {
    const row = document.createElement("article");
    row.className = `deck-card-row deck-card-preview-trigger ${Number(card.short_quantity || 0) > 0 ? "is-short" : ""}`;
    row.setAttribute("role", "button");
    row.tabIndex = 0;
    row.dataset.cardId = card.scryfall_id || card.card_id || "";
    row.dataset.variant = card.variant || "Normal";
    row.innerHTML = `
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
        ${deckInventoryStatusHtml(card)}
      </div>
      <b>Qty ${integer.format(deckQuantity(card))}</b>
      ${readonly ? "" : '<button class="remove-deck-card-button" type="button" aria-label="Remove card from deck" title="Remove card"><span class="trash-icon" aria-hidden="true"></span></button>'}
    `;
    if (!readonly) {
      const removeButton = row.querySelector(".remove-deck-card-button");
      removeButton.addEventListener("click", (event) => {
        event.stopPropagation();
        removeCardFromActiveDeck(card).catch((error) => {
          els.decksStatus.textContent = error.message;
        });
      });
    }
    els.deckDetailCards.appendChild(row);
  }
  wireDeckCardPreviewRows(els.deckDetailCards, cards);
}

async function openDeckDetailModal(deckId) {
  const deck = await api(`/api/decks/${encodeURIComponent(deckId)}`);
  renderDeckDetail(deck);
  els.deckDetailOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeDeckDetailModal() {
  closeDeckCardSearchModal({ keepDeckOpen: false });
  els.deckDetailOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.activeDeck = null;
  els.deckDetailCards.innerHTML = "";
}

function deckCardKey(card) {
  return `${card.scryfall_id || card.card_id || ""}::${card.variant || "Normal"}`;
}

function activeDeckQuantities() {
  const quantities = new Map();
  for (const card of state.activeDeck?.cards || []) {
    quantities.set(deckCardKey(card), Number(card.deck_quantity ?? card.quantity ?? 0));
  }
  return quantities;
}

function deckQuantity(card) {
  return Number(card.deck_quantity ?? card.quantity ?? 0);
}

function deckInventoryStatusHtml(card) {
  const needed = deckQuantity(card);
  const owned = Number(card.owned_quantity ?? card.quantity ?? 0);
  const short = Math.max(0, Number(card.short_quantity ?? needed - owned));
  const className = short > 0 ? "deck-inventory-status is-short" : "deck-inventory-status";
  const text = short > 0
    ? `Need ${integer.format(short)} more - Owned ${integer.format(owned)} / Deck ${integer.format(needed)}`
    : `Owned ${integer.format(owned)} / Deck ${integer.format(needed)}`;
  return `<span class="${className}">${escapeHtml(text)}</span>`;
}

function openDeckCardSearchModal() {
  if (!state.activeDeck) return;
  els.deckCardSearchForm.reset();
  els.deckCardSearchResults.innerHTML = "";
  els.deckCardSearchStatus.textContent = "Search Scryfall for any card to add to this deck.";
  els.deckCardSearchTitle.textContent = `Add to ${state.activeDeck.name || "Deck"}`;
  els.deckCardSearchOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.deckCardSearchInput.focus();
}

function closeDeckCardSearchModal(options = {}) {
  els.deckCardSearchOverlay.hidden = true;
  els.deckCardSearchResults.innerHTML = "";
  els.deckCardSearchStatus.textContent = "";
  els.deckCardSearchForm.reset();
  if (!options.keepDeckOpen || els.deckDetailOverlay.hidden) {
    document.body.classList.remove("modal-open");
  }
}

function renderDeckCardSearchResults(cards) {
  els.deckCardSearchResults.innerHTML = "";
  if (!cards.length) {
    els.deckCardSearchResults.innerHTML = '<div class="empty-state">No matching Scryfall cards found.</div>';
    return;
  }
  for (const card of cards) {
    const current = Number(card.active_deck_quantity || 0);
    const owned = Number(card.owned_quantity || 0);
    const deckText = [
      current ? `${integer.format(current)} already in this deck` : "",
      `Owned ${integer.format(owned)}`,
    ].filter(Boolean).join(" - ");
    const row = document.createElement("article");
    row.className = "deck-card-search-result";
    row.innerHTML = `
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <span>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <small>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</small>
        <small>${escapeHtml(deckText)}</small>
        <span class="deck-card-tags">${cardMetadataPillsHtml(card)}</span>
      </span>
      <label class="deck-quantity-field">
        Qty
        <input type="number" min="1" max="99" step="1" value="1" aria-label="Quantity to add">
      </label>
      <button class="primary-button deck-add-card-button" type="button">Add</button>
    `;
    const input = row.querySelector("input");
    row.querySelector(".deck-add-card-button").addEventListener("click", () => {
      addCardToActiveDeck(card, Number(input.value || 1)).catch((error) => {
        els.deckCardSearchStatus.textContent = error.message;
      });
    });
    els.deckCardSearchResults.appendChild(row);
  }
}

async function searchCardsForDeck() {
  if (!state.activeDeck) return;
  const query = els.deckCardSearchInput.value.trim();
  if (query.length < 2) {
    els.deckCardSearchStatus.textContent = "Type at least 2 characters.";
    els.deckCardSearchResults.innerHTML = "";
    return;
  }
  els.deckCardSearchStatus.textContent = "Searching Scryfall...";
  const language = (state.settings && state.settings.language) || "en";
  const data = await api(`/api/scryfall/search?q=${encodeURIComponent(query)}&lang=${encodeURIComponent(language)}&order=name`);
  const deckQuantities = activeDeckQuantities();
  const cards = (data.cards || []).map((card) => {
    const activeDeckQuantity = deckQuantities.get(deckCardKey(card)) || 0;
    card.active_deck_quantity = activeDeckQuantity;
    card.variant = card.variant || "Normal";
    return card;
  });
  els.deckCardSearchStatus.textContent = `${integer.format(cards.length)} match${cards.length === 1 ? "" : "es"}.`;
  renderDeckCardSearchResults(cards);
}

async function addCardToActiveDeck(card, quantity = 1) {
  if (!state.activeDeck) return;
  if (state.deckEditorDirty && !confirmDiscardDeckEditorChanges()) return;
  discardDeckEditorChanges();
  const deckId = state.activeDeck.id;
  const max = 99;
  const selectedQuantity = Math.min(Math.max(1, Number(quantity || 1)), max);
  await api(`/api/decks/${encodeURIComponent(deckId)}/cards`, {
    method: "POST",
    body: JSON.stringify({
      cards: [{
        card_id: card.scryfall_id || card.card_id,
        variant: card.variant || "Normal",
        quantity: selectedQuantity,
      }],
    }),
  });
  const deck = await api(`/api/decks/${encodeURIComponent(deckId)}`);
  renderActiveDeck(deck);
  await loadDecks();
  els.deckCardSearchStatus.textContent = `Added ${integer.format(selectedQuantity)} ${cardTitle(card)}.`;
  await searchCardsForDeck();
}

async function removeCardFromActiveDeck(card) {
  if (!state.activeDeck) return;
  const confirmed = window.confirm(`Remove ${cardTitle(card)} from ${state.activeDeck.name}?`);
  if (!confirmed) return;
  if (state.deckEditorDirty && !confirmDiscardDeckEditorChanges()) return;
  discardDeckEditorChanges();
  await api(`/api/decks/${encodeURIComponent(state.activeDeck.id)}/cards`, {
    method: "DELETE",
    body: JSON.stringify({
      card_id: card.scryfall_id,
      variant: card.variant || "Normal",
      card_condition: card.card_condition || "Near Mint",
    }),
  });
  const deck = await api(`/api/decks/${encodeURIComponent(state.activeDeck.id)}`);
  renderActiveDeck(deck);
  await loadDecks();
}

async function deleteActiveDeck() {
  if (!state.activeDeck) return;
  const confirmed = window.confirm(`Delete deck "${state.activeDeck.name}"? This only removes the deck metadata.`);
  if (!confirmed) return;
  const deckName = state.activeDeck.name;
  await api(`/api/decks/${encodeURIComponent(state.activeDeck.id)}`, { method: "DELETE" });
  discardDeckEditorChanges();
  if (deckEditorIsVisible()) {
    state.activeDeck = null;
    window.history.pushState({}, "", "/decks");
    showPage("decks");
  } else {
    closeDeckDetailModal();
  }
  await loadDecks();
  els.decksStatus.textContent = `Deleted ${deckName}.`;
}

async function loadDecks() {
  const data = await api("/api/decks");
  state.decks = data.decks || [];
  renderDecks(state.decks);
  return state.decks;
}

async function loadBrowseDecks() {
  const data = await api("/api/browse-decks");
  state.browseDecks = data.decks || [];
  renderBrowseDecks(state.browseDecks);
  return state.browseDecks;
}

function openAddDeckModal() {
  els.addDeckForm.reset();
  if (!els.assignDeckOverlay.hidden) {
    els.addDeckOverlay.classList.add("modal-overlay-stacked");
    state.returnToAssignDeck = true;
  } else {
    els.addDeckOverlay.classList.remove("modal-overlay-stacked");
    state.returnToAssignDeck = false;
  }
  els.addDeckOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.addDeckForm.querySelector('[name="name"]').focus();
}

function closeAddDeckModal() {
  els.addDeckOverlay.hidden = true;
  els.addDeckOverlay.classList.remove("modal-overlay-stacked");
  if (els.assignDeckOverlay.hidden) {
    document.body.classList.remove("modal-open");
  }
  state.returnToAssignDeck = false;
  els.addDeckForm.reset();
}

function renderAssignDeckCards(deck = null) {
  const deckQuantities = new Map((deck?.cards || []).map((card) => [deckCardKey(card), deckQuantity(card)]));
  const cards = Array.from(state.selectedCards.values());
  els.assignDeckCards.innerHTML = cards.map((card) => {
    const inDeck = deckQuantities.get(deckCardKey(card)) || 0;
    const available = Math.max(0, Number(card.quantity || 0) - inDeck);
    return `
      <article class="assign-deck-card" data-card-id="${escapeHtml(card.card_id)}" data-variant="${escapeHtml(card.variant || "Normal")}">
        <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
        <div>
          <strong>${escapeHtml(card.name || "Card")}</strong>
          <span>${escapeHtml(card.variant || "Normal")} - ${integer.format(available)} available${inDeck ? `, ${integer.format(inDeck)} already in deck` : ""}</span>
        </div>
        <label class="deck-quantity-field">
          Qty
          <input type="number" min="0" max="${available}" step="1" value="${available > 0 ? 1 : 0}" ${available > 0 ? "" : "disabled"} aria-label="Quantity to add">
        </label>
      </article>
    `;
  }).join("");
}

function selectCardForDetailAssignment(card) {
  clearSelectedCards();
  const containerQuantity = containerMemberships(card).reduce((total, container) => total + Number(container.quantity || 0), 0);
  state.selectedCards.set(cardSelectionKey(card), {
    card_id: card.scryfall_id,
    variant: card.variant || "Normal",
    name: cardTitle(card),
    quantity: Number(card.quantity || 0),
    unassigned_quantity: Number(card.unassigned_quantity ?? Math.max(0, Number(card.quantity || 0) - containerQuantity)),
    saleable_quantity: Number(card.saleable_quantity ?? card.quantity ?? 0),
    deck_quantity: deckMemberships(card).reduce((total, deck) => total + Number(deck.deck_quantity || 0), 0),
    display_price: Number(card.display_price || card.market_price || 0),
    sale_quantity: Number(card.sale_quantity || 0),
    sale_price: Number(card.sale_price || card.display_price || card.market_price || 0),
    card_condition: conditionText(card),
    condition_inventory: Array.isArray(card.condition_inventory) ? card.condition_inventory : [],
    image_small: card.image_small || "",
    image_normal: card.image_normal || "",
  });
  updateBulkBar();
}

async function openDetailAddToDeckModal(card) {
  if (!state.user) {
    openAuthModal("login", "Log in to add this card to a deck.");
    return;
  }
  selectCardForDetailAssignment(card);
  await openAssignDeckModal();
}

async function openDetailAddToContainerModal(card) {
  if (!state.user) {
    openAuthModal("login", "Log in to store this card in a container.");
    return;
  }
  selectCardForDetailAssignment(card);
  await openAssignContainerModal({ card });
}

function openSaleManagementForCard(card) {
  if (!state.user) {
    openAuthModal("login", "Log in to manage sale listings.");
    return;
  }
  els.saleSearchInput.value = cardTitle(card);
  activatePage("for-sale", { push: true });
  setStatus(`Showing sale listings for ${cardTitle(card)}.`, "success", els.saleStatus);
}

async function refreshAssignDeckCardsForSelectedDeck() {
  const deckId = els.assignDeckForm.deck_id.value;
  if (!deckId) {
    renderAssignDeckCards();
    return;
  }
  const deck = await api(`/api/decks/${encodeURIComponent(deckId)}`);
  renderAssignDeckCards(deck);
}

function populateAssignDeckSelect(decks) {
  const select = els.assignDeckForm.deck_id;
  select.innerHTML = "";
  if (!decks.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "Create a deck first";
    select.appendChild(option);
    return;
  }
  for (const deck of decks) {
    const option = document.createElement("option");
    option.value = deck.id;
    option.textContent = `${deck.name} (${integer.format(deck.card_count || 0)})`;
    select.appendChild(option);
  }
}

async function openAssignDeckModal() {
  if (!state.selectedCards.size) return;
  const decks = await loadDecks();
  const select = els.assignDeckForm.deck_id;
  populateAssignDeckSelect(decks);
  if (decks.length) {
    await refreshAssignDeckCardsForSelectedDeck();
  } else {
    renderAssignDeckCards();
  }
  els.assignDeckOverlay.hidden = false;
  document.body.classList.add("modal-open");
  select.focus();
}

function closeAssignDeckModal() {
  els.assignDeckOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.assignDeckForm.reset();
  els.assignDeckCards.innerHTML = "";
}

function renderContainers(containers) {
  els.containersGrid.innerHTML = "";
  if (!containers.length) {
    els.containersGrid.innerHTML = '<div class="empty-state">No containers yet.</div>';
    return;
  }
  for (const container of containers) {
    const item = document.createElement("button");
    item.className = "deck-card container-card";
    item.type = "button";
    item.dataset.containerId = container.id;
    item.setAttribute("aria-label", `Open ${container.name}`);
    item.innerHTML = `
      <div>
        <p class="eyebrow">${escapeHtml(containerTypeLabel(container.storage_type))}</p>
        <h3>${containerIconHtml(container.storage_type)}<span>${escapeHtml(container.name)}</span></h3>
        ${container.location ? `<span class="container-location">${escapeHtml(container.location)}</span>` : ""}
      </div>
      <strong>${integer.format(container.stored_quantity || 0)}${Number(container.capacity || 0) > 0 ? ` / ${integer.format(container.capacity || 0)}` : ""}</strong>
      <span>${Number(container.capacity || 0) > 0 ? `${formatPercent(container.fill_percent || 0)} full` : `${integer.format(container.card_count || 0)} unique cards stored`}</span>
    `;
    item.addEventListener("click", () => {
      openContainerDetailModal(container.id).catch((error) => {
        els.containersStatus.textContent = error.message;
      });
    });
    els.containersGrid.appendChild(item);
  }
}

function renderContainerDetail(container) {
  const cards = container.cards || [];
  const capacity = Number(container.capacity || 0);
  const stored = Number(container.stored_quantity || 0);
  const fill = capacity > 0 ? Math.min(100, Number(container.fill_percent || ((stored / capacity) * 100))) : 0;
  state.activeContainer = container;
  els.containerDetailTitle.textContent = container.name || "Container";
  els.containerDetailMeta.textContent = [containerTypeLabel(container.storage_type), container.location, container.notes].filter(Boolean).join(" - ");
  els.containerDetailStats.innerHTML = `
    <section class="container-fill-card">
      <div class="container-fill-head">
        <span>Container fullness</span>
        <strong>${integer.format(stored)}${capacity > 0 ? ` / ${integer.format(capacity)}` : ""}</strong>
      </div>
      <div class="container-fill-track" aria-label="${capacity > 0 ? `${formatPercent(fill)} full` : "No capacity set"}">
        <span style="width: ${escapeHtml(String(fill))}%"></span>
      </div>
      <div class="container-stat-grid">
        <article>
          <span>Current card count</span>
          <strong>${integer.format(stored)}</strong>
        </article>
        <article>
          <span>Capacity</span>
          <strong>${capacity > 0 ? integer.format(capacity) : "Not set"}</strong>
        </article>
        <article>
          <span>Market value</span>
          <strong>${dollars.format(Number(container.container_value || 0))}</strong>
        </article>
      </div>
    </section>
  `;
  els.containerDetailCards.innerHTML = "";
  if (!cards.length) {
    els.containerDetailCards.innerHTML = '<div class="empty-state">No cards stored in this container yet.</div>';
    return;
  }
  for (const card of cards) {
    const row = document.createElement("article");
    row.className = "deck-card-row container-card-row";
    row.innerHTML = `
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
      </div>
      <b>Stored ${integer.format(card.stored_quantity || 0)}</b>
      <button class="remove-deck-card-button" type="button" aria-label="Remove card from container" title="Remove card"><span class="trash-icon" aria-hidden="true"></span></button>
    `;
    row.querySelector(".remove-deck-card-button").addEventListener("click", () => {
      removeCardFromActiveContainer(card).catch((error) => {
        els.containersStatus.textContent = error.message;
      });
    });
    els.containerDetailCards.appendChild(row);
  }
}

async function openContainerDetailModal(containerId) {
  const container = await api(`/api/containers/${encodeURIComponent(containerId)}`);
  renderContainerDetail(container);
  els.containerDetailOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeContainerDetailModal() {
  els.containerDetailOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.activeContainer = null;
  els.containerDetailCards.innerHTML = "";
  els.containerDetailStats.innerHTML = "";
  els.containerDetailMeta.textContent = "";
}

async function removeCardFromActiveContainer(card) {
  if (!state.activeContainer) return;
  const confirmed = window.confirm(`Remove ${cardTitle(card)} from ${state.activeContainer.name}? This only removes the storage assignment.`);
  if (!confirmed) return;
  await api(`/api/containers/${encodeURIComponent(state.activeContainer.id)}/cards`, {
    method: "DELETE",
    body: JSON.stringify({
      card_id: card.scryfall_id,
      variant: card.variant || "Normal",
    }),
  });
  const container = await api(`/api/containers/${encodeURIComponent(state.activeContainer.id)}`);
  renderContainerDetail(container);
  await loadContainers();
  await loadCards();
}

async function deleteActiveContainer() {
  if (!state.activeContainer) return;
  const confirmed = window.confirm(`Delete container "${state.activeContainer.name}"? This only removes storage metadata.`);
  if (!confirmed) return;
  const containerName = state.activeContainer.name;
  await api(`/api/containers/${encodeURIComponent(state.activeContainer.id)}`, { method: "DELETE" });
  closeContainerDetailModal();
  els.containersStatus.textContent = `Deleted ${containerName}.`;
  await loadContainers();
  await loadCards();
}

async function readImportFile(input, label) {
  const file = input.files && input.files[0];
  if (!file) {
    throw new Error(`Choose a ${label} file first.`);
  }
  return file.text();
}

function resetImportWizard() {
  state.importWizard = {
    step: "source",
    format: "",
    text: "",
    headers: [],
    mapping: {},
    fields: [],
    jsonPreview: null,
    rows: [],
    issues: [],
    decks: [],
    wishlists: [],
    busy: false,
    progress: { visible: false, label: "", current: 0, total: 0 },
  };
  if (els.importWizardFile) els.importWizardFile.value = "";
  if (els.importWizardJsonText) els.importWizardJsonText.value = "";
  setStatus("", "", els.importStatus);
  renderImportWizard();
}

function importStepIndex(step) {
  return ["source", "map", "review", "recap"].indexOf(step);
}

function setImportWizardStep(step) {
  state.importWizard.step = step;
  renderImportWizard();
}

function setImportProgress(label, current, total) {
  const safeTotal = Math.max(0, Number(total) || 0);
  const safeCurrent = Math.min(Math.max(0, Number(current) || 0), safeTotal || Number(current) || 0);
  state.importWizard.progress = { visible: true, label, current: safeCurrent, total: safeTotal };
  renderImportProgress();
}

function clearImportProgress() {
  state.importWizard.progress = { visible: false, label: "", current: 0, total: 0 };
  renderImportProgress();
}

function renderImportProgress() {
  const progress = state.importWizard.progress || {};
  if (!els.importWizardProgress) return;
  els.importWizardProgress.hidden = !progress.visible;
  const total = Math.max(0, Number(progress.total) || 0);
  const current = Math.min(Math.max(0, Number(progress.current) || 0), total || Number(progress.current) || 0);
  const percent = total ? Math.round((current / total) * 100) : 0;
  if (els.importWizardProgressLabel) els.importWizardProgressLabel.textContent = progress.label || "Working";
  if (els.importWizardProgressCount) {
    els.importWizardProgressCount.textContent = total
      ? `${integer.format(current)} / ${integer.format(total)} (${percent}%)`
      : "Working...";
  }
  if (els.importWizardProgressBar) els.importWizardProgressBar.style.width = `${total ? percent : 12}%`;
}

function renderImportWizard() {
  const wizard = state.importWizard;
  document.querySelectorAll("[data-import-step]").forEach((panel) => {
    panel.hidden = panel.dataset.importStep !== wizard.step;
  });
  document.querySelectorAll("[data-import-step-indicator]").forEach((item) => {
    item.classList.toggle("is-active", item.dataset.importStepIndicator === wizard.step);
    item.classList.toggle("is-complete", importStepIndex(item.dataset.importStepIndicator) < importStepIndex(wizard.step));
  });
  if (els.importWizardBackButton) els.importWizardBackButton.disabled = wizard.busy || wizard.step === "source";
  if (els.importWizardResetButton) els.importWizardResetButton.disabled = Boolean(wizard.busy);
  if (els.importWizardNextButton) {
    els.importWizardNextButton.hidden = wizard.step === "recap";
    els.importWizardNextButton.disabled = Boolean(wizard.busy);
  }
  if (els.importWizardSaveButton) {
    els.importWizardSaveButton.hidden = wizard.step !== "recap";
    els.importWizardSaveButton.disabled = Boolean(wizard.busy);
  }
  renderImportProgress();
  if (wizard.step === "map") {
    if (wizard.format === "csv") renderImportMappingStep();
    else renderImportJsonPreviewStep();
  }
  if (wizard.step === "review") renderImportWizardReview();
  if (wizard.step === "recap") renderImportWizardRecap();
}

async function importWizardSourceNext() {
  const file = els.importWizardFile?.files?.[0];
  const pastedJson = (els.importWizardJsonText?.value || "").trim();
  if (!file && !pastedJson) {
    setStatus("Upload a CSV/JSON file or paste JSON first.", "error", els.importStatus);
    return;
  }
  setStatus("Reading import source...", "", els.importStatus);
  let text = pastedJson;
  let format = "json";
  if (file) {
    text = await file.text();
    const name = file.name.toLowerCase();
    format = name.endsWith(".csv") || file.type.includes("csv") ? "csv" : "json";
  }
  state.importWizard.text = text;
  state.importWizard.format = format;
  if (format === "csv") {
    const result = await api("/api/import/csv/headers", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    state.importWizard.headers = result.headers || [];
    state.importWizard.mapping = result.mapping || {};
    state.importWizard.fields = result.fields || [];
    state.importWizard.rowCount = result.row_count || 0;
    setStatus(`Loaded CSV with ${integer.format(state.importWizard.rowCount)} row${Number(state.importWizard.rowCount) === 1 ? "" : "s"}.`, "success", els.importStatus);
  } else {
    const result = await api("/api/import/json/preview", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    state.importWizard.jsonPreview = result;
    state.importWizard.rows = result.cards?.rows || [];
    state.importWizard.issues = [...(result.cards?.issues || []), ...(result.issues || [])];
    state.importWizard.decks = result.decks?.normalized_decks || [];
    state.importWizard.wishlists = result.wishlists?.normalized_wishlists || [];
    setStatus(result.label || "JSON loaded.", result.can_commit === false ? "error" : "success", els.importStatus);
  }
  setImportWizardStep("map");
}

function renderImportMappingStep() {
  const wizard = state.importWizard;
  if (els.importMapTitle) els.importMapTitle.textContent = "Map CSV Columns";
  if (els.importMapSubtitle) els.importMapSubtitle.textContent = `${integer.format(wizard.headers.length)} headers · ${integer.format(wizard.rowCount || 0)} rows`;
  if (els.importJsonPreview) els.importJsonPreview.innerHTML = "";
  const headers = ["", ...wizard.headers];
  els.importMappingTable.innerHTML = `
    <div class="import-mapping-head">
      <span>CSV column</span>
      <span>Arcane Ledger field</span>
      <span>Required</span>
    </div>
    ${(wizard.fields || []).map((field) => `
      <label class="import-mapping-row">
        <select data-import-field="${escapeHtml(field.key)}">
          ${headers.map((header) => `<option value="${escapeHtml(header)}" ${wizard.mapping[field.key] === header ? "selected" : ""}>${escapeHtml(header || "Do not import")}</option>`).join("")}
        </select>
        <strong>${escapeHtml(field.label)}</strong>
        <span>${field.required ? "Required" : "Optional"}</span>
      </label>
    `).join("")}
  `;
  els.importMappingTable.querySelectorAll("select[data-import-field]").forEach((select) => {
    select.addEventListener("change", () => {
      state.importWizard.mapping[select.dataset.importField] = select.value;
    });
  });
}

function renderImportJsonPreviewStep() {
  const preview = state.importWizard.jsonPreview || {};
  if (els.importMapTitle) els.importMapTitle.textContent = "JSON Detection";
  if (els.importMapSubtitle) els.importMapSubtitle.textContent = preview.label || "";
  if (els.importMappingTable) els.importMappingTable.innerHTML = "";
  const decks = preview.decks?.decks || [];
  const wishlists = preview.wishlists?.wishlists || [];
  const cards = preview.cards?.rows || [];
  const issues = [...(preview.issues || []), ...(preview.cards?.issues || [])];
  els.importJsonPreview.innerHTML = `
    <div class="import-json-card ${preview.can_commit === false ? "needs-review" : ""}">
      <strong>${escapeHtml(preview.label || "JSON import")}</strong>
      <span>${escapeHtml(preview.kind || "unknown")}</span>
      ${issues.length ? `<p>${escapeHtml(issues.join(" "))}</p>` : ""}
    </div>
    ${decks.length ? `
      <div class="deck-import-list">
        ${decks.map((deck) => `
          <article class="deck-import-row ${deck.issues?.length ? "needs-review" : ""}" data-import-index="${escapeHtml(deck.index)}">
            <div>
              <label>
                Deck name
                <input type="text" maxlength="20" value="${escapeHtml(deck.name || "")}" data-json-deck-name="${escapeHtml(deck.index)}">
              </label>
              ${deck.issues?.length ? `<p>${escapeHtml(deck.issues.join(" "))}</p>` : `<p>Ready to import.</p>`}
            </div>
            <span>${integer.format(deck.card_count || 0)} cards</span>
          </article>
        `).join("")}
      </div>
    ` : ""}
    ${wishlists.length ? `
      <div class="deck-import-list">
        ${wishlists.map((wishlist) => `
          <article class="deck-import-row ${wishlist.issues?.length ? "needs-review" : ""}" data-import-index="${escapeHtml(wishlist.index)}">
            <div>
              <label>
                Wishlist name
                <input type="text" maxlength="30" value="${escapeHtml(wishlist.name || "")}" data-json-wishlist-name="${escapeHtml(wishlist.index)}">
              </label>
              ${wishlist.issues?.length ? `<p>${escapeHtml(wishlist.issues.join(" "))}</p>` : `<p>Ready to import.</p>`}
            </div>
            <span>${integer.format(wishlist.card_count || 0)} cards</span>
          </article>
        `).join("")}
      </div>
    ` : ""}
    ${cards.length ? `<div class="empty-state compact-empty">${integer.format(cards.length)} collection card group${cards.length === 1 ? "" : "s"} will be reviewed next.</div>` : ""}
  `;
  els.importJsonPreview.querySelectorAll("[data-json-deck-name]").forEach((input) => {
    input.addEventListener("input", () => {
      const index = Number(input.dataset.jsonDeckName);
      const deck = state.importWizard.decks.find((item) => Number(item.index) === index);
      if (deck) deck.name = input.value.trim().replace(/\s+/g, " ");
    });
  });
  els.importJsonPreview.querySelectorAll("[data-json-wishlist-name]").forEach((input) => {
    input.addEventListener("input", () => {
      const index = Number(input.dataset.jsonWishlistName);
      const wishlist = state.importWizard.wishlists.find((item) => Number(item.index) === index);
      if (wishlist) wishlist.name = input.value.trim().replace(/\s+/g, " ");
    });
  });
}

const IMPORT_MATCH_BATCH_SIZE = 12;
const IMPORT_SAVE_BATCH_SIZE = 20;

function importWizardAggregateRows(rows) {
  const grouped = new Map();
  const output = [];
  for (const row of rows || []) {
    const cardId = row.match?.card?.scryfall_id;
    if (!cardId) {
      output.push(row);
      continue;
    }
    const entry = row.entry || {};
    const variant = entry.variant || "Normal";
    const condition = entry.card_condition || "Near Mint";
    const key = `${cardId}::${variant}::${condition}`;
    const quantity = Number(entry.quantity || 0);
    const paidPrice = Number(entry.paid_price || 0.01) || 0.01;
    if (!grouped.has(key)) {
      const clone = JSON.parse(JSON.stringify(row));
      clone.source_rows = [entry];
      clone.entry.quantity = quantity;
      clone.entry.paid_total = paidPrice * quantity;
      clone.entry.line = String(entry.line || "");
      grouped.set(key, clone);
      output.push(clone);
    } else {
      const target = grouped.get(key);
      target.source_rows.push(entry);
      target.entry.quantity = Number(target.entry.quantity || 0) + quantity;
      target.entry.paid_total = Number(target.entry.paid_total || 0) + (paidPrice * quantity);
      if (target.entry.quantity > 0) {
        target.entry.paid_price = Math.round((target.entry.paid_total / target.entry.quantity) * 10000) / 10000;
      }
      target.entry.line = target.source_rows.map((item) => item.line).filter(Boolean).join(", ");
    }
  }
  return output.map((row, index) => ({ ...row, id: `group-${index + 1}` }));
}

function importWizardEntryCacheKey(entry) {
  if (entry?.scryfall_id) return `id::${entry.scryfall_id}`;
  return [
    "query",
    (entry?.name || "").trim().toLowerCase(),
    (entry?.set_code || entry?.set_name || "").trim().toLowerCase(),
    (entry?.collector_number || "").trim().toLowerCase(),
  ].join("::");
}

function importWizardCachedRow(entry, match) {
  const rowId = `row-${entry.line || Math.random().toString(36).slice(2)}`;
  return {
    id: rowId,
    checked: Boolean(match),
    entry,
    match,
    status: match ? "matched" : "unmatched",
  };
}

async function importWizardMatchCsvRows(wizard) {
  setStatus("Preparing CSV rows...", "", els.importStatus);
  const prepared = await api("/api/import/csv/entries", {
    method: "POST",
    body: JSON.stringify({ text: wizard.text, mapping: wizard.mapping }),
  });
  const entries = prepared.entries || [];
  const total = entries.length;
  const matchedRows = [];
  const issues = [...(prepared.issues || [])];
  const matchCache = new Map();
  setImportProgress("Matching cards with Scryfall", 0, total);
  for (let offset = 0; offset < total; offset += IMPORT_MATCH_BATCH_SIZE) {
    const batch = entries.slice(offset, offset + IMPORT_MATCH_BATCH_SIZE);
    const uncached = [];
    for (const entry of batch) {
      const cacheKey = importWizardEntryCacheKey(entry);
      if (matchCache.has(cacheKey)) {
        matchedRows.push(importWizardCachedRow(entry, matchCache.get(cacheKey)));
      } else {
        uncached.push(entry);
      }
    }
    setImportProgress("Matching cards with Scryfall", offset, total);
    if (uncached.length) {
      const result = await api("/api/import/entries/match", {
        method: "POST",
        body: JSON.stringify({ entries: uncached }),
      });
      for (const row of result.rows || []) {
        matchCache.set(importWizardEntryCacheKey(row.entry || {}), row.match || null);
        matchedRows.push(row);
      }
      issues.push(...(result.issues || []));
    }
    setImportProgress("Matching cards with Scryfall", Math.min(offset + batch.length, total), total);
  }
  wizard.rows = importWizardAggregateRows(matchedRows);
  wizard.issues = issues;
  setStatus(`Matched ${integer.format(wizard.rows.filter((row) => row.match?.card).length)} card group${wizard.rows.length === 1 ? "" : "s"}.`, "success", els.importStatus);
}

async function importWizardMapNext() {
  const wizard = state.importWizard;
  if (wizard.format === "csv") {
    if (!wizard.mapping.name && !wizard.mapping.scryfall_id) {
      setStatus("Map at least Card title or Scryfall ID before continuing.", "error", els.importStatus);
      return;
    }
    await importWizardMatchCsvRows(wizard);
  } else if (wizard.jsonPreview?.kind === "unknown") {
    setStatus("This JSON type cannot be saved yet.", "error", els.importStatus);
    return;
  } else if (["decks", "wishlists"].includes(wizard.jsonPreview?.kind)) {
    setImportWizardStep("recap");
    return;
  } else if (wizard.jsonPreview?.kind === "full") {
    wizard.rows = wizard.jsonPreview.cards?.rows || [];
    wizard.issues = wizard.jsonPreview.cards?.issues || [];
    if (!wizard.rows.length) {
      clearImportProgress();
      setImportWizardStep("recap");
      return;
    }
  }
  clearImportProgress();
  setImportWizardStep("review");
}

function renderImportWizardReview() {
  const rows = state.importWizard.rows || [];
  const issues = state.importWizard.issues || [];
  if (els.importReviewStepTitle) els.importReviewStepTitle.textContent = "Review Matches";
  if (els.importReviewStepSubtitle) {
    const selected = rows.filter((row) => row.checked).length;
    els.importReviewStepSubtitle.textContent = `${integer.format(selected)} of ${integer.format(rows.length)} selected`;
  }
  els.importWizardIssues.innerHTML = issues.length
    ? issues.map((issue) => `<div>Line ${escapeHtml(issue.line || "?")}: ${escapeHtml(issue.error || issue)}</div>`).join("")
    : "";
  els.importWizardRows.innerHTML = rows.length ? rows.map((row) => importWizardRowHtml(row)).join("") : '<div class="empty-state">No card rows to review.</div>';
  els.importWizardRows.querySelectorAll("[data-import-delete-row]").forEach((button) => {
    button.addEventListener("click", () => {
      state.importWizard.rows = state.importWizard.rows.filter((row) => row.id !== button.dataset.importDeleteRow);
      renderImportWizardReview();
    });
  });
  els.importWizardRows.querySelectorAll("[data-import-row-check]").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const row = state.importWizard.rows.find((item) => item.id === checkbox.dataset.importRowCheck);
      if (row) row.checked = checkbox.checked;
      renderImportWizardReview();
    });
  });
  els.importWizardRows.querySelectorAll(".import-match-button").forEach((button) => {
    button.addEventListener("click", () => {
      const rowId = button.dataset.rowId;
      const rowEl = button.closest(".import-wizard-row");
      const row = state.importWizard.rows.find((item) => item.id === rowId);
      const input = rowEl.querySelector(".import-match-search");
      const select = rowEl.querySelector(".import-match-results");
      searchImportWizardRow(row, input, select, rowEl).catch((error) => setStatus(error.message, "error", els.importStatus));
    });
  });
  els.importWizardRows.querySelectorAll(".import-match-search").forEach((input) => {
    input.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      input.closest(".import-wizard-row")?.querySelector(".import-match-button")?.click();
    });
  });
  els.importWizardRows.querySelectorAll(".import-match-results").forEach((select) => {
    select.addEventListener("change", () => {
      const row = state.importWizard.rows.find((item) => item.id === select.dataset.rowId);
      const selected = select._cards?.find((card) => card.scryfall_id === select.value);
      if (!row || !selected) return;
      row.match = { source: "scryfall", confidence: "user selected", card: selected };
      row.status = "matched";
      row.checked = true;
      renderImportWizardReview();
    });
  });
}

function importWizardRowHtml(row) {
  const entry = row.entry || {};
  const matchCard = row.match?.card;
  return `
    <article class="import-wizard-row ${!matchCard ? "needs-review" : ""}" data-row-id="${escapeHtml(row.id)}">
      <label class="import-row-check">
        <input type="checkbox" data-import-row-check="${escapeHtml(row.id)}" ${row.checked ? "checked" : ""} ${matchCard ? "" : "disabled"}>
      </label>
      <div class="import-row-source">
        <strong>${escapeHtml(entry.name || "Unnamed row")}</strong>
        <span>Line ${escapeHtml(entry.line || "?")} · ${escapeHtml(entry.set_name || entry.set_code || "Unknown set")} #${escapeHtml(entry.collector_number || "?")} · ${escapeHtml(entry.variant || "Normal")} · ${escapeHtml(entry.card_condition || "Near Mint")}</span>
      </div>
      <div class="import-row-match">${renderImportCard(matchCard)}</div>
      <b>${integer.format(entry.quantity || 0)}</b>
      <div class="import-row-tools">
        <div class="search-control">
          <input class="import-match-search" type="search" value="${escapeAttribute(entry.name || "")}" placeholder="Search Scryfall">
          <button class="search-button import-match-button" type="button" data-row-id="${escapeHtml(row.id)}" aria-label="Search Scryfall">&#8981;</button>
        </div>
        <select class="import-match-results" data-row-id="${escapeHtml(row.id)}" hidden></select>
      </div>
      <button class="delete-movement-button" type="button" data-import-delete-row="${escapeHtml(row.id)}" aria-label="Delete import row" title="Delete row"><span class="trash-icon" aria-hidden="true"></span></button>
    </article>
  `;
}

async function searchImportWizardRow(row, input, select, item) {
  const query = input.value.trim();
  if (query.length < 2) return;
  item.classList.add("is-searching");
  try {
    const result = await api(`/api/scryfall/search?q=${encodeURIComponent(query)}`);
    const cards = result.cards || [];
    select._cards = cards;
    select.innerHTML = cards.length
      ? '<option value="">Choose a Scryfall match</option>' + cards.map((card) => `<option value="${escapeHtml(card.scryfall_id)}">${escapeHtml(card.display_name || card.name)} - ${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)}</option>`).join("")
      : '<option value="">No matches</option>';
    select.hidden = false;
  } finally {
    item.classList.remove("is-searching");
  }
}

function importWizardReviewNext() {
  if (!state.importWizard.rows.length) {
    setStatus("No rows remain to import.", "error", els.importStatus);
    return;
  }
  setImportWizardStep("recap");
}

function renderImportWizardRecap() {
  const wizard = state.importWizard;
  const rows = (wizard.rows || []).filter((row) => row.checked && row.match?.card);
  const decks = wizard.decks || [];
  const wishlists = wizard.wishlists || [];
  const parts = [];
  if (rows.length) parts.push(`${integer.format(rows.length)} card group${rows.length === 1 ? "" : "s"}`);
  if (decks.length && ["decks", "full"].includes(wizard.jsonPreview?.kind)) parts.push(`${integer.format(decks.length)} deck${decks.length === 1 ? "" : "s"}`);
  if (wishlists.length && ["wishlists", "full"].includes(wizard.jsonPreview?.kind)) parts.push(`${integer.format(wishlists.length)} wishlist${wishlists.length === 1 ? "" : "s"}`);
  if (els.importRecapSubtitle) els.importRecapSubtitle.textContent = parts.join(" · ") || "Nothing selected";
  const cardRows = rows.length ? `
    <h4>Cards</h4>
    <div class="import-recap-list">
      ${rows.map((row) => `
        <article>
          <strong>${escapeHtml(cardTitle(row.match.card))}</strong>
          <span>${escapeHtml(row.match.card.set_name || "")} #${escapeHtml(row.match.card.collector_number || "")} · ${escapeHtml(row.entry?.variant || "Normal")} · ${escapeHtml(row.entry?.card_condition || "Near Mint")}</span>
          <b>Qty ${integer.format(row.entry?.quantity || 0)}</b>
        </article>
      `).join("")}
    </div>
  ` : "";
  const deckRows = decks.length && ["decks", "full"].includes(wizard.jsonPreview?.kind) ? `
    <h4>Decks</h4>
    <div class="import-recap-list">
      ${decks.map((deck) => `
        <article>
          <strong>${escapeHtml(deck.name || "Deck")}</strong>
          <span>${integer.format((deck.cards || []).length)} unique card row${Number((deck.cards || []).length) === 1 ? "" : "s"}</span>
          <b>${deck.is_private ? "Private" : "Public"}</b>
        </article>
      `).join("")}
    </div>
  ` : "";
  const wishlistRows = wishlists.length && ["wishlists", "full"].includes(wizard.jsonPreview?.kind) ? `
    <h4>Wishlists</h4>
    <div class="import-recap-list">
      ${wishlists.map((wishlist) => `
        <article>
          <strong>${escapeHtml(wishlist.name || "Wishlist")}</strong>
          <span>${integer.format((wishlist.cards || []).length)} unique card row${Number((wishlist.cards || []).length) === 1 ? "" : "s"}</span>
          <b>Wishlist</b>
        </article>
      `).join("")}
    </div>
  ` : "";
  els.importRecapRows.innerHTML = cardRows + deckRows + wishlistRows || '<div class="empty-state">Nothing is selected to save.</div>';
}

async function saveImportWizard() {
  if (state.importWizard.busy) return;
  const wizard = state.importWizard;
  const rows = (wizard.rows || [])
    .filter((row) => row.checked && row.match?.card)
    .map((row) => ({
    checked: row.checked,
    entry: row.entry,
    card_id: row.match?.card?.scryfall_id || "",
    match: row.match,
  }));
  const decks = wizard.format === "json" && ["decks", "full"].includes(wizard.jsonPreview?.kind) ? (wizard.decks || []) : [];
  const wishlists = wizard.format === "json" && ["wishlists", "full"].includes(wizard.jsonPreview?.kind) ? (wizard.wishlists || []) : [];
  const totalSteps = rows.length + (decks.length ? 1 : 0) + (wishlists.length ? 1 : 0);
  let completedSteps = 0;
  let importedCards = 0;
  let importedDecks = 0;
  let importedWishlists = 0;
  if (!totalSteps) {
    setStatus("Nothing is selected to save.", "error", els.importStatus);
    return;
  }
  wizard.busy = true;
  renderImportWizard();
  setImportProgress("Saving import", 0, totalSteps);
  setStatus("Saving import...", "", els.importStatus);
  try {
    for (let offset = 0; offset < rows.length; offset += IMPORT_SAVE_BATCH_SIZE) {
      const batch = rows.slice(offset, offset + IMPORT_SAVE_BATCH_SIZE);
      setImportProgress("Saving cards to collection", completedSteps, totalSteps);
      const result = await api("/api/import/commit", {
        method: "POST",
        body: JSON.stringify({ rows: batch }),
      });
      importedCards += result.imported_rows ?? 0;
      completedSteps += batch.length;
      setImportProgress("Saving cards to collection", completedSteps, totalSteps);
    }
    if (decks.length || wishlists.length) {
      setImportProgress(decks.length ? "Saving decks" : "Saving wishlists", completedSteps, totalSteps);
      const result = await api("/api/import/json/commit", {
        method: "POST",
        body: JSON.stringify({ kind: "full", rows: [], decks, wishlists }),
      });
      importedDecks += result.imported?.decks ?? 0;
      importedWishlists += result.imported?.wishlists ?? 0;
      completedSteps += (decks.length ? 1 : 0) + (wishlists.length ? 1 : 0);
      setImportProgress("Saving import", completedSteps, totalSteps);
    }
    const savedParts = [`${integer.format(importedCards)} card group${Number(importedCards) === 1 ? "" : "s"}`];
    if (importedDecks) savedParts.push(`${integer.format(importedDecks)} deck${Number(importedDecks) === 1 ? "" : "s"}`);
    if (importedWishlists) savedParts.push(`${integer.format(importedWishlists)} wishlist${Number(importedWishlists) === 1 ? "" : "s"}`);
    const message = `Saved ${savedParts.join(", ")}.`;
    resetImportWizard();
    setStatus(message, "success", els.importStatus);
    await refresh();
    await loadDecks().catch(() => {});
    await loadWishlists().catch(() => {});
  } finally {
    wizard.busy = false;
    clearImportProgress();
    renderImportWizard();
  }
}

async function importWizardNext() {
  if (state.importWizard.busy) return;
  state.importWizard.busy = true;
  renderImportWizard();
  const step = state.importWizard.step;
  try {
    if (step === "source") return await importWizardSourceNext();
    if (step === "map") return await importWizardMapNext();
    if (step === "review") return importWizardReviewNext();
  } finally {
    state.importWizard.busy = false;
    renderImportWizard();
  }
}

function importWizardBack() {
  const step = state.importWizard.step;
  if (step === "map") setImportWizardStep("source");
  if (step === "review") setImportWizardStep("map");
  if (step === "recap") {
    const wizard = state.importWizard;
    const hasCardRows = (wizard.rows || []).length > 0;
    setImportWizardStep(wizard.format === "json" && !hasCardRows ? "map" : "review");
  }
}

async function previewImport(format) {
  const isJson = format === "json";
  const input = isJson ? els.jsonImportFile : els.csvImportFile;
  const button = isJson ? els.previewJsonImportButton : els.previewCsvImportButton;
  button.disabled = true;
  els.importStatus.textContent = `Reading ${format.toUpperCase()} file...`;
  try {
    const text = await readImportFile(input, format.toUpperCase());
    els.importStatus.textContent = "Matching cards with Scryfall...";
    const result = await api("/api/import/preview", {
      method: "POST",
      body: JSON.stringify({ format, text }),
    });
    state.importRows = result.rows || [];
    state.importIssues = result.issues || [];
    renderImportReview();
    els.importReviewOverlay.hidden = false;
    document.body.classList.add("modal-open");
    els.importStatus.textContent = "Review matches before importing.";
  } finally {
    button.disabled = false;
  }
}

function closeImportReviewModal() {
  els.importReviewOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.importRows = [];
  state.importIssues = [];
  els.importReviewRows.innerHTML = "";
  els.importIssues.innerHTML = "";
}

function renderImportCard(card) {
  if (!card) return '<strong>No match</strong><span>Search and choose a Scryfall card before importing this row.</span>';
  return `
    <strong>${escapeHtml(card.display_name || card.name || "Card")}</strong>
    <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(cardTypeLabel(card))} - ${escapeHtml(cardColorLabel(card))}</span>
  `;
}

function renderImportReview() {
  const checkedCount = state.importRows.filter((row) => row.checked).length;
  els.importReviewCount.textContent = `${integer.format(checkedCount)} of ${integer.format(state.importRows.length)} selected`;
  els.importIssueCount.textContent = `${integer.format(state.importIssues.length)} issue${state.importIssues.length === 1 ? "" : "s"}`;
  els.importIssues.innerHTML = state.importIssues.length
    ? state.importIssues.map((issue) => `<div>Line ${escapeHtml(issue.line || "?")}: ${escapeHtml(issue.error || "Unable to process row.")}</div>`).join("")
    : "";
  els.importReviewRows.innerHTML = "";
  for (const row of state.importRows) {
    const entry = row.entry || {};
    const matchCard = row.match && row.match.card;
    const item = document.createElement("article");
    item.className = `import-review-row ${row.status === "bad" || !matchCard ? "needs-review" : ""}`;
    item.dataset.rowId = row.id;
    item.innerHTML = `
      <label class="import-row-check">
        <input type="checkbox" ${row.checked ? "checked" : ""} ${matchCard ? "" : "disabled"}>
      </label>
      <div class="import-row-source">
        <strong>${escapeHtml(entry.name || "Unnamed row")}</strong>
        <span>Line ${escapeHtml(entry.line || "?")} - ${escapeHtml(entry.set_name || entry.set_code || "Unknown set")} #${escapeHtml(entry.collector_number || "?")} - Qty ${integer.format(entry.quantity || 0)}</span>
      </div>
      <div class="import-row-match">${renderImportCard(matchCard)}</div>
      <div class="import-row-tools">
        <div class="search-control">
          <input class="import-match-search" type="search" placeholder="Search Scryfall">
          <button class="search-button import-match-button" type="button" aria-label="Search Scryfall">&#8981;</button>
        </div>
        <select class="import-match-results" hidden></select>
      </div>
    `;
    const checkbox = item.querySelector('input[type="checkbox"]');
    checkbox.addEventListener("change", () => {
      row.checked = checkbox.checked;
      renderImportReview();
    });
    const input = item.querySelector(".import-match-search");
    const button = item.querySelector(".import-match-button");
    const select = item.querySelector(".import-match-results");
    input.value = entry.name || "";
    button.addEventListener("click", () => searchImportRow(row, input, select, item));
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        searchImportRow(row, input, select, item);
      }
    });
    select.addEventListener("change", () => {
      const selected = select._cards?.find((card) => card.scryfall_id === select.value);
      if (!selected) return;
      row.match = { source: "scryfall", confidence: "user selected", card: selected };
      row.status = "matched";
      row.checked = true;
      renderImportReview();
    });
    els.importReviewRows.appendChild(item);
  }
}

async function searchImportRow(row, input, select, item) {
  const query = input.value.trim();
  if (query.length < 2) return;
  item.classList.add("is-searching");
  try {
    const result = await api(`/api/scryfall/search?q=${encodeURIComponent(query)}`);
    const cards = result.cards || [];
    select._cards = cards;
    select.innerHTML = cards.length
      ? '<option value="">Choose a Scryfall match</option>' + cards.map((card) => `<option value="${escapeHtml(card.scryfall_id)}">${escapeHtml(card.display_name || card.name)} - ${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)}</option>`).join("")
      : '<option value="">No matches</option>';
    select.hidden = false;
  } finally {
    item.classList.remove("is-searching");
  }
}

async function commitImportReview() {
  const rows = state.importRows.map((row) => ({
    checked: row.checked,
    entry: row.entry,
    card_id: row.match?.card?.scryfall_id || "",
    match: row.match,
  }));
  els.commitImportButton.disabled = true;
  els.importStatus.textContent = "Importing checked rows...";
  try {
    const result = await api("/api/import/commit", {
      method: "POST",
      body: JSON.stringify({ rows }),
    });
    closeImportReviewModal();
    els.importStatus.textContent = `Imported ${integer.format(result.imported_rows || 0)} row${result.imported_rows === 1 ? "" : "s"}. ${integer.format((result.skipped_rows || []).length)} skipped.`;
    await refresh();
  } finally {
    els.commitImportButton.disabled = false;
  }
}

async function loadContainers() {
  const data = await api("/api/containers");
  state.containers = data.containers || [];
  renderContainers(state.containers);
  return state.containers;
}

function openAddContainerModal() {
  state.editingContainer = null;
  if (!els.containerDetailOverlay.hidden || !els.assignContainerOverlay.hidden) {
    els.addContainerOverlay.classList.add("modal-overlay-stacked");
  } else {
    els.addContainerOverlay.classList.remove("modal-overlay-stacked");
  }
  state.returnToAssignContainer = !els.assignContainerOverlay.hidden;
  els.addContainerForm.reset();
  els.addContainerForm.id.value = "";
  els.addContainerForm.storage_type.value = "other";
  els.addContainerForm.capacity.value = "";
  els.addContainerEyebrow.textContent = "New container";
  els.addContainerTitle.textContent = "Add Container";
  els.saveContainerButton.textContent = "Add";
  els.addContainerOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.addContainerForm.querySelector('[name="name"]').focus();
}

function openEditContainerModal(container) {
  state.editingContainer = container;
  if (!els.containerDetailOverlay.hidden) {
    els.addContainerOverlay.classList.add("modal-overlay-stacked");
  } else {
    els.addContainerOverlay.classList.remove("modal-overlay-stacked");
  }
  els.addContainerForm.reset();
  els.addContainerForm.id.value = container.id || "";
  els.addContainerForm.name.value = container.name || "";
  els.addContainerForm.storage_type.value = containerType(container.storage_type);
  els.addContainerForm.capacity.value = container.capacity || "";
  els.addContainerForm.location.value = container.location || "";
  els.addContainerForm.notes.value = container.notes || "";
  els.addContainerEyebrow.textContent = "Edit container";
  els.addContainerTitle.textContent = "Edit Container";
  els.saveContainerButton.textContent = "Save";
  els.addContainerOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.addContainerForm.querySelector('[name="name"]').focus();
}

function closeAddContainerModal() {
  els.addContainerOverlay.hidden = true;
  els.addContainerOverlay.classList.remove("modal-overlay-stacked");
  if (els.containerDetailOverlay.hidden && els.assignContainerOverlay.hidden) {
    document.body.classList.remove("modal-open");
  }
  state.returnToAssignContainer = false;
  state.editingContainer = null;
  els.addContainerForm.reset();
}

function normalizeConditionName(value) {
  return value || "Near Mint";
}

function containerAllocationBuckets(card) {
  return variantSummaries(card).flatMap((summary) => {
    const variant = summary.variant || "Normal";
    const conditions = Array.isArray(summary.conditions) ? summary.conditions : [];
    if (!conditions.length && Number(summary.quantity || 0) > 0) {
      return [{
        variant,
        card_condition: normalizeConditionName(conditionText(card)),
        quantity: Number(summary.quantity || 0),
      }];
    }
    return conditions
      .map((condition) => ({
        variant,
        card_condition: normalizeConditionName(condition.card_condition || conditionText(card)),
        quantity: Number(condition.quantity || 0),
      }))
      .filter((condition) => condition.quantity > 0);
  });
}

function containerAllocationQuantity(card, containerId, variant = null, condition = null) {
  let memberships = containerMemberships(card) || [];
  if (containerId !== null && containerId !== undefined) {
    memberships = memberships.filter((container) => Number(container.id) === Number(containerId));
  }
  return memberships
    .filter((container) => !variant || (container.variant || "Normal") === variant)
    .filter((container) => !condition || normalizeConditionName(container.card_condition) === normalizeConditionName(condition))
    .reduce((total, container) => total + Number(container.quantity || 0), 0);
}

function renderAssignContainerCards(containers = state.containers || []) {
  if (state.assignContainerCard) {
    renderContainerAllocationRows(containers);
    return;
  }
  const cards = Array.from(state.selectedCards.values());
  els.assignContainerCards.innerHTML = "";
  if (!cards.length) {
    els.assignContainerCards.innerHTML = '<div class="empty-state">Select owned cards first.</div>';
    return;
  }
  for (const card of cards) {
    const available = Math.max(0, Number(card.unassigned_quantity || 0));
    const row = document.createElement("article");
    row.className = "assign-container-row";
    row.dataset.cardKey = `${card.card_id}::${card.variant}`;
    row.innerHTML = `
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(card.name || "Card")}</strong>
        <span>${escapeHtml(card.variant || "Normal")} - ${integer.format(available)} unassigned of ${integer.format(card.quantity || 0)} owned</span>
      </div>
      <label>
        Qty
        <input type="number" min="1" max="${available}" step="1" value="${available > 0 ? 1 : 0}" ${available <= 0 ? "disabled" : ""}>
      </label>
    `;
    els.assignContainerCards.appendChild(row);
  }
}

function renderContainerAllocationRows(containers = []) {
  const card = state.assignContainerCard;
  els.assignContainerCards.innerHTML = "";
  if (!card) return;
  const buckets = containerAllocationBuckets(card);
  const owned = buckets.reduce((total, bucket) => total + Number(bucket.quantity || 0), 0);
  const stored = (containerMemberships(card) || []).reduce((total, container) => total + Number(container.quantity || 0), 0);
  const unassigned = Math.max(0, owned - stored);
  const preview = document.createElement("section");
  preview.className = "assign-container-card-preview";
  preview.innerHTML = `
    <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
    <div>
      <strong>${escapeHtml(cardTitle(card))}</strong>
      <span>${integer.format(owned)} owned, ${integer.format(stored)} stored, ${integer.format(unassigned)} unassigned</span>
    </div>
  `;
  els.assignContainerCards.appendChild(preview);
  if (!buckets.length) {
    els.assignContainerCards.insertAdjacentHTML("beforeend", '<div class="empty-state">Add this card to your collection first.</div>');
    return;
  }
  if (!containers.length) {
    els.assignContainerCards.insertAdjacentHTML("beforeend", '<div class="empty-state">Create a container first.</div>');
    return;
  }
  const table = document.createElement("div");
  table.className = "container-allocation-table";
  const rows = [];
  for (const bucket of buckets) {
    const bucketOwned = Number(bucket.quantity || 0);
    const bucketStored = containerAllocationQuantity(card, null, bucket.variant, bucket.card_condition);
    for (const container of containers) {
      const current = containerAllocationQuantity(card, container.id, bucket.variant, bucket.card_condition);
      const capacity = Number(container.capacity || 0);
      const remaining = Number(container.remaining_capacity ?? 0);
      const maxForContainer = capacity > 0 ? Math.min(bucketOwned, current + remaining) : bucketOwned;
      const isFull = capacity > 0 && remaining <= 0 && current <= 0;
      const location = container.location ? ` - ${escapeHtml(container.location)}` : "";
      const capacityText = capacity > 0
        ? `${isFull ? "No more space" : `${integer.format(Math.max(0, remaining))} open`} - ${integer.format(current)} stored here`
        : `${integer.format(current)} stored here`;
      rows.push(`
        <article class="container-allocation-row${isFull ? " is-full" : ""}"
          data-container-id="${escapeHtml(container.id)}"
          data-variant="${escapeHtml(bucket.variant)}"
          data-condition="${escapeHtml(bucket.card_condition)}"
          data-owned="${escapeHtml(String(bucketOwned))}">
          <strong>${escapeHtml(bucket.variant)}</strong>
          <span>${escapeHtml(bucket.card_condition)}<small class="container-space-label">${integer.format(bucketStored)} of ${integer.format(bucketOwned)} stored</small></span>
          <span>${escapeHtml(container.name || "Container")}<small class="container-space-label">${escapeHtml(containerTypeLabel(container.storage_type))}${location}</small></span>
          <span>${escapeHtml(capacityText)}</span>
          <label>
            <span class="sr-only">Quantity in ${escapeHtml(container.name || "container")}</span>
            <input type="number" min="0" max="${escapeHtml(String(maxForContainer))}" step="1" value="${escapeHtml(String(Math.min(current, maxForContainer)))}" ${isFull ? "disabled" : ""}>
          </label>
        </article>
      `);
    }
  }
  table.innerHTML = `
    <div class="container-allocation-header">
      <span>Variant</span>
      <span>Condition</span>
      <span>Container</span>
      <span>Space</span>
      <span>Quantity</span>
    </div>
    ${rows.join("")}
  `;
  els.assignContainerCards.appendChild(table);
}

function updateAssignContainerMode() {
  const isCardAllocation = Boolean(state.assignContainerCard);
  const selectLabel = els.assignContainerForm.container_id.closest("label");
  if (selectLabel) selectLabel.hidden = isCardAllocation;
  els.assignContainerForm.container_id.required = !isCardAllocation;
  if (els.assignCreateContainerButton) {
    els.assignCreateContainerButton.textContent = isCardAllocation ? "Create Container" : "Add New Container";
  }
  const title = document.querySelector("#assignContainerTitle");
  if (title) title.textContent = isCardAllocation ? "Assign Containers" : "Add to Container";
  const eyebrow = els.assignContainerOverlay.querySelector(".eyebrow");
  if (eyebrow) eyebrow.textContent = isCardAllocation ? "Store this card" : "Store selected cards";
  const submit = els.assignContainerForm.querySelector('button[type="submit"]');
  if (submit) submit.textContent = isCardAllocation ? "Save Containers" : "Add to Container";
}

async function openAssignContainerModal(options = {}) {
  state.assignContainerCard = options.card || null;
  if (!state.selectedCards.size) return;
  const containers = await loadContainers();
  const select = els.assignContainerForm.container_id;
  populateAssignContainerSelect(containers);
  updateAssignContainerMode();
  renderAssignContainerCards(containers);
  els.assignContainerOverlay.hidden = false;
  document.body.classList.add("modal-open");
  if (state.assignContainerCard) {
    els.assignContainerCards.querySelector('input[type="number"]')?.focus();
  } else {
    select.focus();
  }
}

function populateAssignContainerSelect(containers) {
  const select = els.assignContainerForm.container_id;
  select.innerHTML = "";
  if (!containers.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "Create a container first";
    select.appendChild(option);
  } else {
    for (const container of containers) {
      const option = document.createElement("option");
      const capacity = Number(container.capacity || 0);
      const remaining = Number(container.remaining_capacity ?? 0);
      const isFull = capacity > 0 && remaining <= 0;
      option.value = container.id;
      option.disabled = isFull;
      option.textContent = `${containerTypeLabel(container.storage_type)} - ${container.name}${container.location ? ` - ${container.location}` : ""}${isFull ? " - no more space" : ""}`;
      select.appendChild(option);
    }
  }
}

function closeAssignContainerModal() {
  els.assignContainerOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.assignContainerCard = null;
  els.assignContainerForm.reset();
  els.assignContainerCards.innerHTML = "";
  updateAssignContainerMode();
}

function renderSaleCards() {
  const cards = Array.from(state.selectedCards.values());
  els.saleCards.innerHTML = "";
  const stats = {
    rows: 0,
    availableRows: 0,
    blockedRows: 0,
    totalAvailable: 0,
    totalDeckQuantity: 0,
    totalOwned: 0,
  };
  if (!cards.length) {
    els.saleCards.innerHTML = '<div class="empty-state">Select owned cards first.</div>';
    return stats;
  }
  for (const card of cards) {
    const market = Number(card.display_price || 0);
    const buckets = Array.isArray(card.condition_inventory) ? card.condition_inventory : [];
    const cardDeckQuantity = Number(card.deck_quantity || 0);
    stats.totalOwned += Number(card.quantity || 0);
    stats.totalDeckQuantity += cardDeckQuantity;
    const saleBuckets = buckets
      .map((bucket) => ({
        card_condition: bucket.card_condition || card.card_condition || "Near Mint",
        quantity: Number(bucket.quantity || 0),
        sale_available_quantity: Number(bucket.sale_available_quantity ?? bucket.quantity ?? 0),
        sale_quantity: Number(bucket.sale_quantity || 0),
        sale_price: Number(bucket.sale_price || card.sale_price || market || 0.01),
        deck_reserved_quantity: Number(bucket.deck_reserved_quantity || 0),
      }))
      .filter((bucket) => bucket.quantity > 0);
    if (!saleBuckets.length && Number(card.quantity || 0) > 0) {
      saleBuckets.push({
        card_condition: card.card_condition || "Near Mint",
        quantity: Number(card.quantity || 0),
        sale_available_quantity: Number(card.saleable_quantity ?? card.quantity ?? 0),
        sale_quantity: Number(card.sale_quantity || 0),
        sale_price: Number(card.sale_price || market || 0.01),
        deck_reserved_quantity: cardDeckQuantity,
      });
    }
    for (const bucket of saleBuckets) {
      const condition = bucket.card_condition || "Near Mint";
      const maxQuantity = Number(bucket.sale_available_quantity ?? bucket.quantity ?? 0);
      const existingQuantity = Number(bucket.sale_quantity || 0);
      const disabled = maxQuantity <= 0;
      const deckReservedQuantity = Number(bucket.deck_reserved_quantity || 0);
      stats.rows += 1;
      stats.totalAvailable += Math.max(0, maxQuantity);
      if (disabled) {
        stats.blockedRows += 1;
      } else {
        stats.availableRows += 1;
      }
      const row = document.createElement("article");
      row.className = "sale-modal-row";
      row.dataset.cardId = card.card_id;
      row.dataset.variant = card.variant || "Normal";
      row.dataset.condition = condition;
      row.innerHTML = `
        <label class="sale-modal-check" title="Include in sale">
          <input type="checkbox" ${disabled ? "disabled" : "checked"} aria-label="Include ${escapeHtml(card.name || "card")} ${escapeHtml(condition)}">
        </label>
        <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
        <div class="sale-modal-card-copy">
          <strong>${escapeHtml(card.name || "Card")}</strong>
          <span>${escapeHtml(card.variant || "Normal")} - ${escapeHtml(condition)}${disabled ? " - 0 available" : cardDeckQuantity > 0 ? ` - FYI: ${integer.format(cardDeckQuantity)} listed in decks` : ""}</span>
        </div>
        <label class="sale-readonly-field">
          Available Qty
          <output>${integer.format(maxQuantity)}</output>
        </label>
        <span class="sale-value-pill">${dollars.format(market)} market</span>
        <label class="sale-inline-field">
          Quantity
          <input name="quantity" type="number" min="1" max="${maxQuantity}" step="1" value="${disabled ? 0 : existingQuantity > 0 ? existingQuantity : 1}" ${disabled ? "disabled" : ""}>
        </label>
        <label class="sale-inline-field">
          Asking Price
          <input name="asking_price" type="number" min="0.01" step="0.01" value="${Number(bucket.sale_price || market || 0.01).toFixed(2)}">
        </label>
      `;
      els.saleCards.appendChild(row);
    }
  }
  return stats;
}

function saleAvailabilityMessage(stats) {
  if (!stats || !stats.rows) return "";
  if (stats.totalAvailable <= 0) {
    return "0 copies are available to sell for the selected card.";
  }
  if (stats.totalDeckQuantity > 0) {
    return `FYI: ${integer.format(stats.totalDeckQuantity)} ${stats.totalDeckQuantity === 1 ? "copy is" : "copies are"} listed in decks. This listing will still use your actual collection inventory.`;
  }
  return "";
}

function openSaleModal() {
  if (!state.selectedCards.size) return;
  const stats = renderSaleCards();
  const message = saleAvailabilityMessage(stats);
  const tone = stats.totalAvailable <= 0 ? "error" : "";
  setStatus(message, message ? tone : "", els.saleModalStatus);
  const submitButton = els.saleForm.querySelector('button[type="submit"]');
  if (submitButton) {
    submitButton.disabled = stats.availableRows <= 0;
  }
  els.saleOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function selectedSaleCardFromDetail(card) {
  const variant = card.variant || "Normal";
  const buckets = Array.isArray(card.condition_inventory)
    ? card.condition_inventory.filter((bucket) => (bucket.variant || variant) === variant)
    : [];
  const saleableQuantity = buckets.length
    ? buckets.reduce((total, bucket) => total + Number(bucket.sale_available_quantity ?? bucket.quantity ?? 0), 0)
    : Number(card.saleable_quantity ?? card.quantity ?? 0);
  const deckQuantity = buckets.length
    ? buckets.reduce((total, bucket) => total + Number(bucket.deck_reserved_quantity || 0), 0)
    : Number(card.deck_quantity || 0);
  return {
    card_id: card.scryfall_id,
    variant,
    name: cardTitle(card),
    quantity: Number(card.quantity || 0),
    unassigned_quantity: Number(card.unassigned_quantity ?? card.quantity ?? 0),
    saleable_quantity: saleableQuantity,
    deck_quantity: deckQuantity,
    display_price: Number(card.display_price || card.market_price || 0),
    sale_quantity: Number(card.sale_quantity || 0),
    sale_price: Number(card.sale_price || card.display_price || card.market_price || 0),
    card_condition: conditionText(card),
    condition_inventory: buckets,
    image_small: card.image_small || "",
    image_normal: card.image_normal || "",
  };
}

function openSaleModalForCardDetail(card) {
  if (!card || Number(card.quantity || 0) <= 0) {
    setStatus("Add this card to your collection before marking it for sale.", "error");
    return;
  }
  const saleCard = selectedSaleCardFromDetail(card);
  const confirmed = window.confirm(`Mark ${cardTitle(card)} for sale?`);
  if (!confirmed) return;
  clearSelectedCards();
  state.selectedCards.set(cardSelectionKey(card), saleCard);
  updateBulkBar();
  openSaleModal();
}

function closeSaleModal() {
  els.saleOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.saleForm.reset();
  els.saleCards.innerHTML = "";
  setStatus("", "", els.saleModalStatus);
  const submitButton = els.saleForm.querySelector('button[type="submit"]');
  if (submitButton) {
    submitButton.disabled = false;
  }
}

function openSoldModal(card) {
  state.activeSaleCard = card;
  const quantity = Math.max(1, Number(card.sale_quantity || 1));
  els.soldTitle.textContent = cardTitle(card);
  els.soldSubtitle.textContent = `${integer.format(quantity)} listed - ${card.variant || "Normal"} - ${conditionText(card)}`;
  els.soldForm.card_id.value = card.scryfall_id;
  els.soldForm.variant.value = card.variant || "Normal";
  els.soldForm.card_condition.value = conditionText(card);
  els.soldForm.quantity.max = quantity;
  els.soldForm.quantity.value = 1;
  els.soldForm.sold_date.value = todayValue();
  els.soldForm.sold_price_each.value = Number(card.sale_price || card.display_price || 0.01).toFixed(2);
  els.soldOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.soldForm.sold_date.focus();
}

function closeSoldModal() {
  els.soldOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.activeSaleCard = null;
  els.soldForm.reset();
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}

function identityIsPro(identity) {
  return Boolean(identity?.is_pro || identity?.owner_is_pro || identity?.seller_is_pro || identity?.role === "pro" || identity?.role === "admin" || identity?.owner_role === "pro" || identity?.owner_role === "admin");
}

function proBadgeHtml(identity) {
  return identityIsPro(identity) ? '<span class="pro-badge" title="Pro member" aria-label="Pro member">PRO</span>' : "";
}

function displayNameHtml(name, identity = {}) {
  const safeName = escapeHtml(name || "Arcane Ledger user");
  const nameClass = identityIsPro(identity) ? "display-name pro-display-name" : "display-name";
  return `<span class="display-name-wrap"><span class="${nameClass}">${safeName}</span>${proBadgeHtml(identity)}</span>`;
}

function profileActorLink(actor) {
  const name = actor?.name || "Collector";
  const href = actor?.profile_url || (actor?.profile_slug ? `/user/${encodeURIComponent(actor.profile_slug)}` : "");
  const content = displayNameHtml(name, actor);
  return href ? `<a href="${escapeHtml(href)}" class="profile-actor-link">${content}</a>` : `<span class="profile-actor-link">${content}</span>`;
}

function inlineMarkdownToHtml(value) {
  let text = escapeHtml(value);
  text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return text;
}

function markdownToHtml(value) {
  const lines = String(value || "").replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let inList = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      if (inList) {
        html.push("</ul>");
        inList = false;
      }
      continue;
    }
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${inlineMarkdownToHtml(trimmed.slice(2))}</li>`);
      continue;
    }
    if (inList) {
      html.push("</ul>");
      inList = false;
    }
    if (trimmed.startsWith("### ")) {
      html.push(`<h4>${inlineMarkdownToHtml(trimmed.slice(4))}</h4>`);
    } else if (trimmed.startsWith("## ")) {
      html.push(`<h3>${inlineMarkdownToHtml(trimmed.slice(3))}</h3>`);
    } else if (trimmed.startsWith("# ")) {
      html.push(`<h2>${inlineMarkdownToHtml(trimmed.slice(2))}</h2>`);
    } else {
      html.push(`<p>${inlineMarkdownToHtml(trimmed)}</p>`);
    }
  }
  if (inList) html.push("</ul>");
  return html.join("");
}

function cssImageUrl(value) {
  return `url("${String(value || "").replaceAll("\\", "\\\\").replaceAll('"', "%22")}")`;
}

function renderSharedCard(card) {
  state.sharedCard = card;
  const specialClass = isSpecialVariant(card.variant) ? " is-special" : "";
  els.sharedCardShell.innerHTML = `
    <article class="shared-card${specialClass}">
      <div class="card-detail-media">
        <a class="shared-card-art" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer">
          <img src="${escapeHtml(card.image_normal || card.image_small || "")}" alt="${escapeHtml(cardTitle(card))}">
        </a>
        <div class="detail-storage-actions shared-card-blog-actions">
          <button class="detail-storage-button detail-blog-posts-button" type="button" aria-label="View blog posts about this card" title="View blog posts"><span class="blog-post-icon" aria-hidden="true"></span></button>
        </div>
      </div>
      <div class="shared-card-copy">
        <p class="eyebrow">Shared from Arcane Ledger</p>
        <h2>${escapeHtml(cardTitle(card))}</h2>
        <div class="card-divider"></div>
        <p>${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)} - ${escapeHtml(card.rarity || "unknown")}</p>
        ${cardRulesName(card) ? `<p>Rules: ${escapeHtml(cardRulesName(card))}</p>` : ""}
        <p>${escapeHtml(card.type_line || "")}</p>
        <dl class="shared-card-details">
          <div>
            <dt>Variant</dt>
            <dd>${escapeHtml(card.variant || "Normal")}</dd>
          </div>
          <div>
            <dt>Market Price</dt>
            <dd>${dollars.format(card.market_price ?? card.display_price ?? 0)}</dd>
          </div>
          <div>
            <dt>Type</dt>
            <dd>${escapeHtml(cardTypeLabel(card))}</dd>
          </div>
          <div>
            <dt>Colors</dt>
            <dd>${escapeHtml(cardColorLabel(card))}</dd>
          </div>
        </dl>
      </div>
      <aside class="card-detail-toolbar" aria-label="Card actions">
        <a class="detail-action-button detail-scryfall-button" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" aria-label="View on Scryfall" title="View on Scryfall">S</a>
      </aside>
    </article>
  `;
  els.sharedCardShell.querySelector(".detail-blog-posts-button")?.addEventListener("click", () => {
    openCardBlogListModal(card).catch((error) => setStatus(error.message, "error"));
  });
}

function renderMovementHistory(movements) {
  if (!movements || !movements.length) {
    return '<div class="empty-state">No card movement yet.</div>';
  }
  return `
    <div class="purchase-history-list">
      ${movements.map((movement) => {
        const isSale = movement.movement_type === "sell";
        const isAdjust = movement.movement_type === "adjust";
        const adjustedIn = isAdjust && movement.adjustment_type === "increase";
        const verb = isAdjust ? (adjustedIn ? "adjusted in" : "adjusted out") : isSale ? "sold" : "bought";
        const amountLabel = isSale ? "received" : "total";
        const deleteLabel = isAdjust ? "Delete adjustment entry" : isSale ? "Delete sold entry" : "Delete purchase entry";
        const purchaseSource = [movement.store_name, movement.store_location].filter(Boolean).join(" - ");
        return `
        <article class="purchase-history-row ${isAdjust ? "is-adjustment" : isSale ? "is-sale" : "is-purchase"}">
          <div>
            <strong>${escapeHtml(formatDate(movement.movement_date || movement.purchase_date))}</strong>
            <span>${escapeHtml(movement.card_condition || "Near Mint")}</span>
          </div>
          <div>
            <b>${integer.format(movement.quantity || 0)} ${verb}</b>
            <span>${isAdjust ? escapeHtml(movement.note || "Manual inventory adjustment") : `${dollars.format(movement.total_amount ?? movement.total_price ?? 0)} ${amountLabel} - ${dollars.format(movement.price_each || 0)} each`}</span>
            ${!isSale && !isAdjust && purchaseSource ? `<small>${escapeHtml(purchaseSource)}</small>` : ""}
            ${!isSale && !isAdjust && movement.notes ? `<small>${escapeHtml(movement.notes)}</small>` : ""}
          </div>
          ${movement.movement_id ? `
            <button class="delete-movement-button" type="button" aria-label="${deleteLabel}" title="${deleteLabel}" data-movement-type="${escapeHtml(movement.movement_type)}" data-movement-id="${escapeHtml(movement.movement_id)}">
              <span class="trash-icon" aria-hidden="true"></span>
            </button>
          ` : ""}
        </article>
      `;
      }).join("")}
    </div>
  `;
}

function movementTypeLabel(movement) {
  if (movement?.movement_type === "sell") return "Sell";
  if (movement?.movement_type === "adjust") {
    return movement.adjustment_type === "increase" ? "Adjust In" : "Adjust Out";
  }
  return "Buy";
}

function renderLedgerEntries(movements) {
  if (!movements || !movements.length) {
    return '<div class="empty-state">No ledger entries yet.</div>';
  }
  return `
    <div class="card-ledger-table">
      <div class="card-ledger-head">
        <span>Date</span>
        <span>Type</span>
        <span>Qty</span>
        <span>Variant</span>
        <span>Condition</span>
        <span>Amount</span>
      </div>
      ${movements.map((movement) => {
        const amount = movement.movement_type === "adjust"
          ? ""
          : dollars.format(movement.total_amount ?? movement.total_price ?? 0);
        return `
          <div class="card-ledger-row">
            <span>${escapeHtml(formatDate(movement.movement_date || movement.purchase_date))}</span>
            <strong>${escapeHtml(movementTypeLabel(movement))}</strong>
            <b>${integer.format(movement.quantity || 0)}</b>
            <span>${escapeHtml(movement.variant || "Normal")}</span>
            <span>${escapeHtml(movement.card_condition || "Near Mint")}</span>
            <span>${escapeHtml(amount || "-")}</span>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function openCardLedgerModal(card) {
  if (!els.cardLedgerOverlay) return;
  if (els.cardLedgerEyebrow) els.cardLedgerEyebrow.textContent = "Card ledger";
  if (els.cardLedgerTitle) els.cardLedgerTitle.textContent = cardTitle(card) || "Ledger";
  if (els.cardLedgerList) els.cardLedgerList.innerHTML = renderLedgerEntries(card.movements || card.purchases || []);
  els.cardLedgerOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeCardLedgerModal() {
  if (!els.cardLedgerOverlay) return;
  els.cardLedgerOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  if (els.cardLedgerList) els.cardLedgerList.innerHTML = "";
}

function renderCardComments(card) {
  const comments = Array.isArray(card.comments) ? card.comments : [];
  return `
    <form class="card-comment-form">
      <textarea name="body" maxlength="1000" placeholder="Add a public comment about this card..."></textarea>
      <button class="secondary-button" type="submit">Add Comment</button>
    </form>
    <div class="card-comment-list">
      ${comments.length ? comments.map((comment) => `
        <article class="card-comment-row">
          <div class="card-comment-meta">
            <a href="${escapeHtml(comment.author?.profile_url || "#")}" class="card-comment-author">${displayNameHtml(comment.author?.name || "Arcane Ledger user", comment.author)}</a>
            <span>${escapeHtml(formatDate(comment.created_at))}</span>
          </div>
          <p>${escapeHtml(comment.body || "")}</p>
          ${state.user ? `<button class="report-content-button" type="button" data-target-type="card_comment" data-target-id="${escapeHtml(comment.id)}" data-target-label="card comment by ${escapeAttribute(comment.author?.name || "Arcane Ledger user")}">Report</button>` : ""}
          <button class="comment-upvote-button ${comment.user_upvoted ? "is-active" : ""}" type="button" data-comment-id="${escapeHtml(comment.id)}" ${comment.can_upvote ? "" : "disabled"} title="${comment.can_upvote ? "Upvote this comment" : "You cannot upvote your own comment"}" aria-label="Upvote comment">
            <span aria-hidden="true">▲</span>
            <b>${integer.format(comment.upvote_count || 0)}</b>
          </button>
        </article>
      `).join("") : '<div class="empty-state">No public comments yet.</div>'}
    </div>
  `;
}

function wireCardComments(card) {
  const form = els.cardDetailShell.querySelector(".card-comment-form");
  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    addCardComment(card, form).catch((error) => setStatus(error.message, "error"));
  });
  els.cardDetailShell.querySelectorAll(".comment-upvote-button").forEach((button) => {
    button.addEventListener("click", () => {
      toggleCardCommentUpvote(card, button).catch((error) => setStatus(error.message, "error"));
    });
  });
}

function refreshCardCommentsPanel(card) {
  const panel = els.cardDetailShell.querySelector(".card-comments-panel");
  if (!panel) return;
  panel.innerHTML = `
    <div class="panel-head">
      <h2>Public Comments</h2>
      <span>${integer.format((card.comments || []).length)} comments</span>
    </div>
    ${renderCardComments(card)}
  `;
  wireCardComments(card);
}

function openReportModal(target) {
  if (!state.user) {
    openAuthModal("login", "Log in to report content.");
    return;
  }
  state.activeReportTarget = target;
  if (els.reportTargetLabel) {
    els.reportTargetLabel.textContent = target.label || "Report this content for moderator review.";
  }
  els.reportForm?.reset();
  setStatus("", "", els.reportStatus);
  if (els.reportOverlay) {
    els.reportOverlay.hidden = false;
    document.body.classList.add("modal-open");
    els.reportForm?.reason?.focus();
  }
}

function closeReportModal() {
  if (!els.reportOverlay) return;
  els.reportOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.activeReportTarget = null;
  els.reportForm?.reset();
  setStatus("", "", els.reportStatus);
}

async function submitContentReport(form) {
  const target = state.activeReportTarget;
  if (!target) return;
  const reason = form.reason.value.trim();
  if (!reason) {
    setStatus("Report reason is required.", "error", els.reportStatus);
    form.reason.focus();
    return;
  }
  const button = form.querySelector('button[type="submit"]');
  const originalText = button ? button.textContent : "";
  if (button) {
    button.disabled = true;
    button.textContent = "Submitting...";
  }
  try {
    await api("/api/reports", {
      method: "POST",
      body: JSON.stringify({
        target_type: target.type,
        target_id: target.id,
        reason,
      }),
      promptLogin: true,
    });
    closeReportModal();
    setStatus("Report submitted for moderator review.", "success", activeStatusTarget());
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalText || "Submit Report";
    }
  }
}

async function addCardComment(card, form) {
  const textarea = form.elements.body;
  const button = form.querySelector("button[type='submit']");
  const body = textarea.value.trim();
  if (!body) {
    setStatus("Write a comment first.", "error");
    textarea.focus();
    return;
  }
  const originalText = button ? button.textContent : "";
  if (button) {
    button.disabled = true;
    button.textContent = "Adding...";
  }
  try {
    const result = await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/comments`, {
      method: "POST",
      body: JSON.stringify({ body }),
      promptLogin: true,
    });
    card.comments = result.comments || [];
    refreshCardCommentsPanel(card);
    setStatus("Comment added.");
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalText || "Add Comment";
    }
  }
}

async function toggleCardCommentUpvote(card, button) {
  const commentId = button.dataset.commentId;
  if (!commentId) return;
  button.disabled = true;
  try {
    const result = await api(`/api/card-comments/${encodeURIComponent(commentId)}/upvote`, {
      method: "POST",
      promptLogin: true,
    });
    card.comments = result.comments || [];
    refreshCardCommentsPanel(card);
  } finally {
    button.disabled = false;
  }
}

function normalizedPriceSeries(card) {
  const source = Array.isArray(card.price_histories) && card.price_histories.length
    ? card.price_histories
    : [{ variant: card.variant || "Normal", points: card.price_history || [] }];
  return source
    .map((series) => ({
      variant: series.variant || "Normal",
      points: (series.points || [])
        .map((point) => ({ date: point.date, value: Number(point.value || 0) }))
        .filter((point) => point.date && point.value > 0),
    }))
    .filter((series) => series.points.length);
}

function renderCardPriceChart(card) {
  const seriesList = normalizedPriceSeries(card);
  if (!seriesList.length) {
    return `
      <div class="card-price-empty">
        <span>No price snapshots yet.</span>
      </div>
    `;
  }
  const width = 340;
  const height = 170;
  const pad = 18;
  const allDates = Array.from(new Set(seriesList.flatMap((series) => series.points.map((point) => point.date)))).sort();
  const values = seriesList.flatMap((series) => series.points.map((point) => point.value));
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = Math.max(0.01, maxValue - minValue);
  const midValue = minValue + range / 2;
  const yTicks = [
    { value: maxValue, y: pad, anchor: "start" },
    { value: midValue, y: height / 2, anchor: "start" },
    { value: minValue, y: height - pad, anchor: "start" },
  ];
  const firstDate = allDates[0] || "";
  const lastDate = allDates[allDates.length - 1] || "";
  const xForDate = (dateValue) => {
    const index = allDates.indexOf(dateValue);
    if (allDates.length <= 1 || index < 0) return width / 2;
    return pad + (index / (allDates.length - 1)) * (width - pad * 2);
  };
  const yFor = (value) => height - pad - ((value - minValue) / range) * (height - pad * 2);
  const pathFor = (points) => points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xForDate(point.date).toFixed(1)} ${yFor(point.value).toFixed(1)}`)
    .join(" ");
  const normalSeries = seriesList.find((series) => !isSpecialVariant(series.variant)) || seriesList[0];
  const latest = normalSeries.points[normalSeries.points.length - 1];
  const first = normalSeries.points[0];
  const delta = latest.value - first.value;
  const normalSeriesMarkup = [];
  const specialSeriesMarkup = [];
  for (const series of seriesList) {
    const path = pathFor(series.points);
    const special = isSpecialVariant(series.variant);
    const area = series.points.length
      ? `${path} L ${xForDate(series.points[series.points.length - 1].date).toFixed(1)} ${height - pad} L ${xForDate(series.points[0].date).toFixed(1)} ${height - pad} Z`
      : "";
    const markup = `
      <path d="${area}" class="card-price-area ${special ? "is-special" : "is-normal"}"></path>
      <path d="${path}" class="card-price-line ${special ? "is-special" : "is-normal"}"></path>
      ${series.points.map((point, index) => `
        <circle class="${special ? "is-special" : "is-normal"}" cx="${xForDate(point.date).toFixed(1)}" cy="${yFor(point.value).toFixed(1)}" r="${index === series.points.length - 1 ? "4" : "2.5"}">
          <title>${escapeHtml(series.variant)} ${escapeHtml(formatDate(point.date))}: ${dollars.format(point.value)}</title>
        </circle>
      `).join("")}
    `;
    if (special) specialSeriesMarkup.push(markup);
    else normalSeriesMarkup.push(markup);
  }
  return `
    <div class="card-price-chart-wrap">
      <svg class="card-price-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Market value for the past 3 months">
        <defs>
          <linearGradient id="cardPriceAreaNormal" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="var(--chart-normal)" stop-opacity="0.26"></stop>
            <stop offset="100%" stop-color="var(--chart-normal)" stop-opacity="0.04"></stop>
          </linearGradient>
          <linearGradient id="cardPriceAreaSpecial" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="var(--chart-special-back)" stop-opacity="0.30"></stop>
            <stop offset="100%" stop-color="var(--chart-special-back)" stop-opacity="0.05"></stop>
          </linearGradient>
        </defs>
        <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" class="card-price-axis"></line>
        <line x1="${pad}" y1="${pad}" x2="${width - pad}" y2="${pad}" class="card-price-grid"></line>
        <line x1="${pad}" y1="${height / 2}" x2="${width - pad}" y2="${height / 2}" class="card-price-grid"></line>
        ${yTicks.map((tick) => `
          <text x="${pad + 3}" y="${tick.y - 4}" class="card-price-scale-label" text-anchor="${tick.anchor}">${escapeHtml(dollars.format(tick.value))}</text>
        `).join("")}
        ${firstDate ? `<text x="${pad}" y="${height - 2}" class="card-price-date-label" text-anchor="start">${escapeHtml(formatDate(firstDate))}</text>` : ""}
        ${lastDate && lastDate !== firstDate ? `<text x="${width - pad}" y="${height - 2}" class="card-price-date-label" text-anchor="end">${escapeHtml(formatDate(lastDate))}</text>` : ""}
        ${specialSeriesMarkup.join("")}
        ${normalSeriesMarkup.join("")}
      </svg>
      <div class="card-price-chart-meta">
        <strong>${dollars.format(latest.value)}</strong>
        <span class="${valueClass(delta)}">${escapeHtml(normalSeries.variant)} ${delta >= 0 ? "+" : ""}${dollars.format(delta)}</span>
      </div>
      <div class="card-price-legend">
        ${seriesList.map((series) => {
          const latestPoint = series.points[series.points.length - 1];
          return `<span class="${isSpecialVariant(series.variant) ? "is-special" : "is-normal"}"><i></i>${escapeHtml(series.variant)} ${dollars.format(latestPoint.value)}</span>`;
        }).join("")}
      </div>
    </div>
  `;
}

function renderCardAggregateStats(stats = {}) {
  const userCount = Number(stats.user_count || 0);
  const totalQuantity = Number(stats.total_quantity || 0);
  const deckCount = Number(stats.deck_count || 0);
  const favoriteCount = Number(stats.favorite_count || 0);
  const wishlistCount = Number(stats.wishlist_count || 0);
  const saleUserCount = Number(stats.sale_user_count || 0);
  const rows = [
    { value: integer.format(userCount), label: userCount === 1 ? "user owns" : "users own" },
    { value: integer.format(totalQuantity), label: totalQuantity === 1 ? "copy owned" : "copies owned" },
    { value: integer.format(deckCount), label: deckCount === 1 ? "deck" : "decks", action: "decks", disabled: deckCount <= 0 },
    { value: integer.format(favoriteCount), label: favoriteCount === 1 ? "favorite" : "favorites" },
    { value: integer.format(wishlistCount), label: wishlistCount === 1 ? "wishlist" : "wishlists" },
    { value: integer.format(saleUserCount), label: "for sale", action: "sales", disabled: saleUserCount <= 0 },
  ];
  return `
    <div class="card-meta-grid">
      ${rows.map((row) => row.action ? `
        <button class="card-meta-action" type="button" data-meta-action="${row.action}" ${row.disabled ? "disabled" : ""}>
          <strong>${row.value}</strong>
          <span>${row.label}</span>
        </button>
      ` : `
        <div>
          <strong>${row.value}</strong>
          <span>${row.label}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function cardWebSearchLinks(card) {
  const title = cardTitle(card);
  const rulesName = cardRulesName(card) || card.name || title;
  const setName = card.set_name || "";
  const setCode = card.set || card.set_code || "";
  const collector = card.collector_number || "";
  const marketQuery = [title, setCode, collector].filter(Boolean).join(" ");
  const broadQuery = [title, setName || setCode, "MTG"].filter(Boolean).join(" ");
  const tcgQuery = title || rulesName;
  return [
    {
      label: "TCGplayer",
      href: `https://www.tcgplayer.com/search/magic/product?productLineName=magic&q=${encodeURIComponent(tcgQuery)}`,
    },
    {
      label: "Cardmarket",
      href: `https://www.cardmarket.com/en/Magic/Products/Search?searchString=${encodeURIComponent(tcgQuery)}`,
    },
    {
      label: "Cardhoarder",
      href: `https://www.cardhoarder.com/cards?data%5Bsearch%5D=${encodeURIComponent(tcgQuery)}`,
    },
    {
      label: "eBay",
      href: `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(marketQuery || broadQuery)}`,
    },
    {
      label: "EDHREC",
      href: `https://edhrec.com/route/?cc=${encodeURIComponent(rulesName || title)}`,
    },
    {
      label: "MTGGoldfish",
      href: `https://www.mtggoldfish.com/q?utf8=%E2%9C%93&query_string=${encodeURIComponent(rulesName || title)}`,
    },
  ].filter((link) => link.href && title);
}

function renderCardDetailActionPanel(card, { owned = false, canManageCollection = false } = {}) {
  const showRefresh = Boolean(canManageCollection);
  const showSale = Boolean(canManageCollection && owned);
  if (!showRefresh && !card.scryfall_uri && !showSale) return "";
  return `
    <section class="card-insight-panel card-detail-action-panel">
      <div class="panel-head compact-panel-head">
        <h2>Card Actions</h2>
        <span>Tools</span>
      </div>
      <div class="card-action-grid">
        ${showRefresh ? `
          <button class="card-action-tile detail-refresh-button" type="button">
            <strong>&#8635;</strong>
            <span>Refresh Scryfall</span>
          </button>
        ` : ""}
        ${card.scryfall_uri ? `
          <a class="card-action-tile detail-scryfall-button" href="${escapeHtml(card.scryfall_uri)}" target="_blank" rel="noreferrer">
            <strong>S</strong>
            <span>View on Scryfall</span>
          </a>
        ` : ""}
        ${showSale ? `
          <button class="card-action-tile detail-for-sale-button" type="button">
            <strong><span class="sale-icon" aria-hidden="true"></span></strong>
            <span>Put Up For Sale</span>
          </button>
        ` : ""}
      </div>
    </section>
  `;
}

function renderCardWebSearchPanel(card) {
  const links = cardWebSearchLinks(card);
  if (!links.length) return "";
  return `
    <section class="card-insight-panel card-web-search-panel">
      <div class="panel-head compact-panel-head">
        <h2>Search the Web</h2>
        <span>External sites</span>
      </div>
      <div class="card-web-link-grid">
        ${links.map((link) => `
          <a href="${escapeHtml(link.href)}" target="_blank" rel="noreferrer">
            <span>${escapeHtml(link.label)}</span>
            <b>&#8599;</b>
          </a>
        `).join("")}
      </div>
    </section>
  `;
}

function openCardMetaOverlay(title, eyebrow = "Arcane Ledger meta") {
  els.cardMetaEyebrow.textContent = eyebrow;
  els.cardMetaTitle.textContent = title;
  els.cardMetaOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

async function openCardDeckReferencesModal(card) {
  openCardMetaOverlay("Decks Using This Card", cardTitle(card));
  els.cardMetaList.innerHTML = '<div class="empty-state">Loading decks...</div>';
  try {
    const result = await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/deck-references`, { promptLogin: true });
    const decks = result.decks || [];
    if (!decks.length) {
      els.cardMetaList.innerHTML = '<div class="empty-state">No decks include this card yet.</div>';
      return;
    }
    els.cardMetaList.innerHTML = decks.map((deck) => `
      <a class="card-meta-drilldown-row" href="${escapeHtml(deck.deck_url || `/decks/${encodeURIComponent(deck.share_id || "")}`)}" target="_blank" rel="noreferrer">
        <span>
          <strong>${escapeHtml(deck.name || "Deck")}</strong>
          <span>${displayNameHtml(deck.owner_name || "Arcane Ledger user", { is_pro: deck.owner_is_pro, role: deck.owner_role })} - ${integer.format(deck.deck_quantity || 0)} in deck</span>
        </span>
        <b>&#8599;</b>
      </a>
    `).join("");
  } catch (error) {
    els.cardMetaList.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function openCardSaleSellersModal(card) {
  openCardMetaOverlay("For Sale", cardTitle(card));
  els.cardMetaList.innerHTML = '<div class="empty-state">Loading sellers...</div>';
  try {
    const result = await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/sale-sellers`, { promptLogin: true });
    const sellers = result.sellers || [];
    if (!sellers.length) {
      els.cardMetaList.innerHTML = '<div class="empty-state">No users have this card for sale yet.</div>';
      return;
    }
    els.cardMetaList.innerHTML = sellers.map((seller) => {
      const minPrice = Number(seller.min_asking_price || 0);
      const maxPrice = Number(seller.max_asking_price || 0);
      const priceLabel = minPrice && maxPrice && minPrice !== maxPrice
        ? `${dollars.format(minPrice)}-${dollars.format(maxPrice)}`
        : dollars.format(minPrice || maxPrice || 0);
      return `
        <a class="card-meta-drilldown-row" href="${escapeHtml(seller.store_url || `/stores/${encodeURIComponent(seller.store_share_id || "")}`)}" target="_blank" rel="noreferrer">
          <span>
            <strong>${displayNameHtml(seller.seller_name || "Seller", { is_pro: seller.seller_is_pro, role: seller.seller_role })}</strong>
            <span>${integer.format(seller.sale_quantity || 0)} for sale - ${priceLabel}</span>
          </span>
          <b>&#8599;</b>
        </a>
      `;
    }).join("");
  } catch (error) {
    els.cardMetaList.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderCardDetail(card) {
  state.activeCardDetail = card;
  const specialClass = cardHasSpecialVariant(card) ? " is-special" : "";
  const ownedQuantity = totalVariantQuantity(card);
  const owned = ownedQuantity > 0;
  const canManageCollection = Boolean(state.user && !card.readonly);
  const summaries = variantSummaries(card);
  const hasDecks = deckMemberships(card).length > 0;
  const hasContainers = containerMemberships(card).length > 0;
  const listedForSale = Number(card.sale_quantity || 0) > 0;
  const totalValue = Number(card.total_value ?? card.owned_value ?? totalVariantMarketValue(card) ?? 0);
  const totalPaid = Number(card.total_paid ?? (Number(card.paid_price || 0) * ownedQuantity) ?? 0);
  const averagePaid = Number(card.average_paid ?? card.paid_price ?? 0);
  const totalDelta = totalValue - totalPaid;
  const detailsHtml = owned ? `
          <div>
            <dt>Owned</dt>
            <dd>${integer.format(ownedQuantity)}</dd>
          </div>
          <div>
            <dt>First Obtained</dt>
            <dd>${escapeHtml(formatDate(card.first_obtained || card.acquired_date || ""))}</dd>
          </div>
          <div>
            <dt>Market Price</dt>
            <dd>${dollars.format(card.market_price ?? card.display_price ?? 0)}</dd>
          </div>
          <div>
            <dt>Average Paid</dt>
            <dd>${dollars.format(averagePaid)}</dd>
          </div>
          <div>
            <dt>Total Paid</dt>
            <dd>${dollars.format(totalPaid)}</dd>
          </div>
          <div>
            <dt>Total Value</dt>
            <dd>${dollars.format(totalValue)}</dd>
          </div>
          <div class="detail-wide">
            <dt>Delta</dt>
            <dd class="${valueClass(totalDelta)}">${dollars.format(totalDelta)}</dd>
          </div>
  ` : `
          <div>
            <dt>Status</dt>
            <dd>Not in your collection</dd>
          </div>
          <div>
            <dt>Market Price</dt>
            <dd>${dollars.format(card.market_price ?? card.display_price ?? 0)}</dd>
          </div>
          <div>
            <dt>Set</dt>
            <dd>${escapeHtml(card.set_name || "")}</dd>
          </div>
  `;
  els.cardDetailShell.innerHTML = `
    <div class="card-detail-layout">
      <article class="shared-card editable-card-detail${specialClass}" style="--card-detail-bg-image: url('${escapeAttribute(card.image_normal || card.image_small || "")}')">
        <div class="card-detail-media">
          <a class="shared-card-art" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" title="Open on Scryfall">
            <img src="${escapeHtml(card.image_normal || card.image_small || "")}" alt="${escapeHtml(cardTitle(card))}">
          </a>
          <div class="detail-storage-actions">
            ${owned ? `<button class="detail-storage-button detail-decks-button ${hasDecks ? "is-linked" : "is-add"}" type="button" aria-label="${hasDecks ? "View decks" : "Add to deck"}" title="${hasDecks ? "View decks" : "Add to deck"}">
              ${hasDecks ? '<span class="deck-icon" aria-hidden="true"></span>' : '<span class="add-to-deck-icon" aria-hidden="true"></span>'}
            </button>
            <button class="detail-storage-button detail-containers-button ${hasContainers ? "is-stored" : "is-missing-storage"}" type="button" aria-label="${hasContainers ? "View container" : "Not in a container"}" title="${hasContainers ? "View container" : "Not in a container - add to container"}">
              ${hasContainers ? '<span class="storage-check-icon" aria-hidden="true"></span>' : '<span class="storage-x-icon" aria-hidden="true"></span>'}
            </button>
            ${listedForSale ? '<button class="detail-storage-button detail-store-button" type="button" aria-label="Manage sale listing" title="Manage sale listing"><span class="sale-icon" aria-hidden="true"></span></button>' : ""}` : ""}
            ${owned ? '<button class="detail-storage-button detail-ledger-button" type="button" aria-label="View ledger" title="View ledger"><span class="ledger-icon" aria-hidden="true"></span></button>' : ""}
            <button class="detail-storage-button detail-blog-posts-button" type="button" aria-label="View blog posts about this card" title="View blog posts"><span class="blog-post-icon" aria-hidden="true"></span></button>
          </div>
        </div>
        <div class="shared-card-copy">
          <p class="eyebrow">${owned ? "Collection card" : "Catalog card"}</p>
          <h2>${escapeHtml(cardTitle(card))}</h2>
          <div class="card-divider"></div>
          <p>${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)} - ${escapeHtml(card.rarity || "unknown")}</p>
          ${cardRulesName(card) ? `<p>Rules: ${escapeHtml(cardRulesName(card))}</p>` : ""}
          <p>${escapeHtml(card.type_line || "")}</p>
          <div class="detail-pill-row">
            <span>${escapeHtml(summaries.length > 1 ? `${integer.format(summaries.length)} variants` : (card.variant || "Normal"))}</span>
            ${owned ? `<span>${escapeHtml(summaries.length > 1 ? "Mixed conditions" : conditionText(card))}</span>` : ""}
            <span>${escapeHtml(cardTypeLabel(card))}</span>
            <span>${escapeHtml(cardColorLabel(card))}</span>
          </div>
          ${owned ? variantSummaryHtml(card) : ""}
          <dl class="shared-card-details">
            ${detailsHtml}
          </dl>
          <div class="detail-actions">
            ${canManageCollection ? '<button id="addPurchaseButton" class="primary-button" type="button">Add Purchase</button>' : ""}
            ${canManageCollection && owned ? '<button id="adjustInventoryButton" class="secondary-button" type="button">Adjust Inventory</button><button id="addDirectSaleButton" class="secondary-button" type="button">Add Sale</button>' : ""}
            ${!owned ? '<button class="wishlist-button detail-wishlist-button" type="button" aria-label="Add to Wishlist" title="Add to Wishlist"></button>' : ""}
          </div>
        </div>
      </article>
      <aside class="card-detail-insights">
        <section class="card-insight-panel">
          <div class="panel-head compact-panel-head">
            <h2>Market</h2>
            <span>Past 3 months</span>
          </div>
          ${renderCardPriceChart(card)}
        </section>
        ${renderCardDetailActionPanel(card, { owned, canManageCollection })}
        ${renderCardWebSearchPanel(card)}
        ${canManageCollection ? `<section class="card-insight-panel card-meta-panel">
          <div class="panel-head compact-panel-head">
            <h2>Arcane Ledger Meta</h2>
            <span>All users</span>
          </div>
          ${renderCardAggregateStats(card.aggregate_stats || {})}
        </section>
        <section class="card-insight-panel card-notes-panel">
          <div class="panel-head compact-panel-head">
            <h2>Private Notes</h2>
            <span>Only you</span>
          </div>
          <form class="card-notes-form">
            <textarea name="notes" maxlength="5000" placeholder="Add personal notes for this card...">${escapeHtml(card.private_notes || "")}</textarea>
            <button class="secondary-button" type="submit">Save Notes</button>
          </form>
        </section>
        ` : ""}
      </aside>
    </div>
    <div class="card-detail-lower-grid ${owned ? "" : "is-comments-only"}">
      ${owned ? `<section class="purchase-history-panel">
        <div class="panel-head">
          <h2>Card History</h2>
          <span>${integer.format((card.movements || card.purchases || []).length)} entries</span>
        </div>
        ${renderMovementHistory(card.movements || card.purchases || [])}
      </section>` : ""}
      <section class="purchase-history-panel card-comments-panel">
        <div class="panel-head">
          <h2>Public Comments</h2>
          <span>${integer.format((card.comments || []).length)} comments</span>
        </div>
        ${renderCardComments(card)}
      </section>
    </div>
  `;
  els.cardDetailShell.querySelector("#addPurchaseButton")?.addEventListener("click", () => openAddCardModal(card));
  els.cardDetailShell.querySelector("#adjustInventoryButton")?.addEventListener("click", () => openInventoryAdjustModal(card));
  els.cardDetailShell.querySelector("#addDirectSaleButton")?.addEventListener("click", () => openDirectSaleModal(card));
  els.cardDetailShell.querySelector(".card-notes-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    saveCardPrivateNotes(card, event.currentTarget).catch((error) => setStatus(error.message, "error"));
  });
  els.cardDetailShell.querySelectorAll(".card-meta-action").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.metaAction === "decks") {
        openCardDeckReferencesModal(card).catch((error) => setStatus(error.message, "error"));
      }
      if (button.dataset.metaAction === "sales") {
        openCardSaleSellersModal(card).catch((error) => setStatus(error.message, "error"));
      }
    });
  });
  els.cardDetailShell.querySelector(".detail-wishlist-button") && wireWishlistButton(els.cardDetailShell.querySelector(".detail-wishlist-button"), card, {
    statusTarget: els.status,
    afterWishlistChange: async () => {
      await loadCardDetail(card.scryfall_id, card.variant || "Normal");
      await loadWishlists();
    },
  });
  els.cardDetailShell.querySelector(".detail-refresh-button")?.addEventListener("click", (event) => {
    refreshCardDetailMetadata(event.currentTarget, card).catch((error) => setStatus(error.message, "error"));
  });
  els.cardDetailShell.querySelector(".detail-for-sale-button")?.addEventListener("click", () => openSaleModalForCardDetail(card));
  els.cardDetailShell.querySelector(".detail-blog-posts-button")?.addEventListener("click", () => {
    openCardBlogListModal(card).catch((error) => setStatus(error.message, "error"));
  });
  els.cardDetailShell.querySelector(".detail-share-button")?.addEventListener("click", () => openShareModal(card));
  els.cardDetailShell.querySelector(".detail-email-button")?.addEventListener("click", () => openEmailCardModal(card));
  els.cardDetailShell.querySelector(".detail-delete-button")?.addEventListener("click", () => {
    deleteCardFromDetail(card).catch((error) => setStatus(error.message, "error"));
  });
  els.cardDetailShell.querySelector(".detail-decks-button")?.addEventListener("click", () => {
    if (hasDecks) {
      openCardDecksModal(card);
    } else {
      openDetailAddToDeckModal(card).catch((error) => setStatus(error.message, "error"));
    }
  });
  els.cardDetailShell.querySelector(".detail-containers-button")?.addEventListener("click", () => {
    if (hasContainers) {
      openCardContainersModal(card);
    } else {
      openDetailAddToContainerModal(card).catch((error) => setStatus(error.message, "error"));
    }
  });
  els.cardDetailShell.querySelector(".detail-store-button")?.addEventListener("click", () => openSaleManagementForCard(card));
  els.cardDetailShell.querySelector(".detail-ledger-button")?.addEventListener("click", () => openCardLedgerModal(card));
  els.cardDetailShell.querySelectorAll(".delete-movement-button").forEach((button) => {
    button.addEventListener("click", () => {
      deleteCardMovement(button).catch((error) => setStatus(error.message, "error"));
    });
  });
  wireCardComments(card);
}

async function saveCardPrivateNotes(card, form) {
  const button = form.querySelector("button[type='submit']");
  const textarea = form.elements.notes;
  const originalText = button ? button.textContent : "";
  if (button) {
    button.disabled = true;
    button.textContent = "Saving...";
  }
  try {
    const result = await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/notes`, {
      method: "PUT",
      body: JSON.stringify({
        variant: card.variant || "Normal",
        notes: textarea.value,
      }),
      promptLogin: true,
    });
    card.private_notes = result.notes || "";
    setStatus("Private notes saved.");
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalText || "Save Notes";
    }
  }
}

async function loadCardDetail(cardId, variant = "Normal") {
  showPage("card-detail");
  els.cardDetailShell.innerHTML = '<div class="empty-state">Loading card...</div>';
  try {
    const card = await api(`/api/cards/${encodeURIComponent(cardId)}/detail?variant=${encodeURIComponent(variant)}`);
    renderCardDetail(card);
  } catch (error) {
    els.cardDetailShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadPublicCardDetail(cardId, variant = "Normal") {
  showPage("shared");
  els.sharedCardShell.innerHTML = '<div class="empty-state">Loading card...</div>';
  try {
    const card = await api(`/api/cards/${encodeURIComponent(cardId)}/public?variant=${encodeURIComponent(variant)}`);
    renderSharedCard(card);
  } catch (error) {
    els.sharedCardShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function uniqueVariantsForCard(card) {
  const variants = new Set(variantsForCard(card));
  if (card.variant) variants.add(card.variant);
  for (const bucket of card.condition_inventory || []) {
    if (bucket.variant) variants.add(bucket.variant);
  }
  return Array.from(variants);
}

function fillVariantSelect(select, card, selected = "Normal", onlyOwned = false) {
  const variants = onlyOwned
    ? Array.from(new Set((card.condition_inventory || []).filter((bucket) => Number(bucket.available_quantity ?? bucket.quantity ?? 0) > 0).map((bucket) => bucket.variant || "Normal")))
    : uniqueVariantsForCard(card);
  select.innerHTML = "";
  for (const variant of variants.length ? variants : ["Normal"]) {
    const option = document.createElement("option");
    option.value = variant;
    option.textContent = variant;
    option.selected = variant === selected;
    select.appendChild(option);
  }
}

function fillConditionSelect(select, card, variant, selected = "Near Mint", mode = "all") {
  const buckets = (card.condition_inventory || []).filter((bucket) => (bucket.variant || "Normal") === (variant || "Normal"));
  let conditions = cardConditions;
  if (mode === "owned") {
    conditions = buckets
      .filter((bucket) => Number(bucket.quantity || 0) > 0)
      .map((bucket) => bucket.card_condition || "Near Mint");
  } else if (mode === "available") {
    conditions = buckets
      .filter((bucket) => Number(bucket.available_quantity ?? bucket.quantity ?? 0) > 0)
      .map((bucket) => bucket.card_condition || "Near Mint");
  }
  const uniqueConditions = Array.from(new Set(conditions.length ? conditions : cardConditions));
  select.innerHTML = "";
  for (const condition of uniqueConditions) {
    const option = document.createElement("option");
    option.value = condition;
    option.textContent = condition;
    option.selected = condition === selected;
    select.appendChild(option);
  }
}

function inventoryBucket(card, variant, condition) {
  return (card.condition_inventory || []).find((bucket) =>
    (bucket.variant || "Normal") === (variant || "Normal") &&
    (bucket.card_condition || "Near Mint") === (condition || "Near Mint")
  );
}

function openAddPurchaseModal(card) {
  state.activeCardDetail = card;
  els.addPurchaseTitle.textContent = cardTitle(card);
  els.addPurchaseForm.card_id.value = card.scryfall_id;
  fillVariantSelect(els.addPurchaseForm.variant, card, card.variant || "Normal");
  els.addPurchaseForm.quantity.value = 1;
  els.addPurchaseForm.card_condition.value = conditionText(card);
  els.addPurchaseForm.purchase_date.value = todayValue();
  els.addPurchaseForm.total_price.value = "0.01";
  els.addPurchaseOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.addPurchaseForm.quantity.focus();
}

function closeAddPurchaseModal() {
  els.addPurchaseOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.addPurchaseForm.reset();
}

function updateInventoryAdjustLimits() {
  const card = state.activeCardDetail;
  if (!card) return;
  const form = els.inventoryAdjustForm;
  const isDecrease = form.adjustment_type.value === "decrease";
  fillConditionSelect(form.card_condition, card, form.variant.value, form.card_condition.value, isDecrease ? "available" : "all");
  const bucket = inventoryBucket(card, form.variant.value, form.card_condition.value);
  const maxQuantity = isDecrease ? Number(bucket?.available_quantity || 0) : 9999;
  form.quantity.max = isDecrease ? String(maxQuantity) : "";
  if (isDecrease && Number(form.quantity.value || 1) > maxQuantity) {
    form.quantity.value = Math.max(1, maxQuantity);
  }
}

function openInventoryAdjustModal(card) {
  state.activeCardDetail = card;
  els.inventoryAdjustTitle.textContent = cardTitle(card);
  els.inventoryAdjustForm.card_id.value = card.scryfall_id;
  els.inventoryAdjustForm.adjustment_type.value = "increase";
  fillVariantSelect(els.inventoryAdjustForm.variant, card, card.variant || "Normal");
  fillConditionSelect(els.inventoryAdjustForm.card_condition, card, els.inventoryAdjustForm.variant.value, conditionText(card), "all");
  els.inventoryAdjustForm.quantity.value = 1;
  els.inventoryAdjustForm.adjustment_date.value = todayValue();
  els.inventoryAdjustForm.note.value = "";
  updateInventoryAdjustLimits();
  els.inventoryAdjustOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.inventoryAdjustForm.quantity.focus();
}

function closeInventoryAdjustModal() {
  els.inventoryAdjustOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.inventoryAdjustForm.reset();
}

function updateDirectSaleLimits() {
  const card = state.activeCardDetail;
  if (!card) return;
  const form = els.directSaleForm;
  fillConditionSelect(form.card_condition, card, form.variant.value, form.card_condition.value, "available");
  const bucket = inventoryBucket(card, form.variant.value, form.card_condition.value);
  const maxQuantity = Number(bucket?.available_quantity || 0);
  form.quantity.max = String(maxQuantity);
  if (Number(form.quantity.value || 1) > maxQuantity) {
    form.quantity.value = Math.max(1, maxQuantity);
  }
}

function openDirectSaleModal(card) {
  const availableBuckets = (card.condition_inventory || []).filter((bucket) => Number(bucket.available_quantity || 0) > 0);
  if (!availableBuckets.length) {
    setStatus("No sellable copies are available for this card. Remove deck assignments or sale listings first.", "error");
    return;
  }
  state.activeCardDetail = card;
  const first = availableBuckets.find((bucket) => (bucket.variant || "Normal") === (card.variant || "Normal")) || availableBuckets[0];
  els.directSaleTitle.textContent = cardTitle(card);
  els.directSaleForm.card_id.value = card.scryfall_id;
  fillVariantSelect(els.directSaleForm.variant, card, first.variant || card.variant || "Normal", true);
  fillConditionSelect(els.directSaleForm.card_condition, card, els.directSaleForm.variant.value, first.card_condition || "Near Mint", "available");
  els.directSaleForm.quantity.value = 1;
  els.directSaleForm.sold_date.value = todayValue();
  els.directSaleForm.sold_price_each.value = Number(card.display_price || card.market_price || 0.01).toFixed(2);
  updateDirectSaleLimits();
  els.directSaleOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.directSaleForm.quantity.focus();
}

function closeDirectSaleModal() {
  els.directSaleOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.directSaleForm.reset();
}

async function loadSharedCard(shareId) {
  try {
    const card = await api(`/api/shared/${encodeURIComponent(shareId)}`);
    if (state.user && card.personalized) {
      showPage("card-detail");
      renderCardDetail(card);
      return;
    }
    showPage("shared");
    els.sharedCardShell.innerHTML = '<div class="empty-state">Loading shared card...</div>';
    renderSharedCard(card);
  } catch (error) {
    showPage("shared");
    els.sharedCardShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderSetPage(setDetail, cards, options = {}) {
  state.activeSet = setDetail;
  state.setCards = cards;
  state.selectedSetMissingCards.clear();
  const percent = Math.max(0, Math.min(100, Number(setDetail.completion_percent || 0)));
  const readonly = Boolean(options.readonly || setDetail.readonly);
  els.setPageShell.innerHTML = `
    <section class="set-hero">
      <div>
        <p class="eyebrow">${readonly ? "Shared set" : "Set completion"}</p>
        <h2>${escapeHtml(setDetail.set_name || setDetail.set_code)}</h2>
        <span>${readonly && setDetail.owner_name ? `${escapeHtml(setDetail.owner_name)} - ` : ""}${integer.format(setDetail.owned_cards || 0)} / ${integer.format(setDetail.total_cards || 0)} unique prints</span>
      </div>
      <div class="set-hero-actions">
        <b>${percent.toFixed(1)}%</b>
        ${readonly ? "" : '<button id="addMissingSetButton" class="primary-button" type="button">Add Missing to Missing List</button>'}
      </div>
      <div class="set-progress set-progress-large" aria-label="${percent.toFixed(1)} percent complete">
        <span style="width: ${percent}%"></span>
      </div>
    </section>
    <div id="setPageStatus" class="status" aria-live="polite"></div>
    <div id="setMissingBulkBar" class="bulk-bar" ${readonly ? "hidden" : "hidden"}>
      <span id="setMissingSelectedCount">0 selected</span>
      <button id="addSelectedMissingButton" class="primary-button" type="button">Add to Missing List</button>
    </div>
    <div id="setCardsGrid" class="cards-grid set-cards-grid"></div>
  `;
  const addMissingButton = els.setPageShell.querySelector("#addMissingSetButton");
  if (addMissingButton) addMissingButton.addEventListener("click", () => {
    addSetMissingToMissingList(setDetail.set_code, addMissingButton).catch((error) => {
      const status = els.setPageShell.querySelector("#setPageStatus");
      setStatus(error.message, "error", status);
    });
  });
  const addSelectedButton = els.setPageShell.querySelector("#addSelectedMissingButton");
  if (addSelectedButton) addSelectedButton.addEventListener("click", () => {
    addSelectedSetMissingToMissingList(addSelectedButton).catch((error) => {
      const status = els.setPageShell.querySelector("#setPageStatus");
      setStatus(error.message, "error", status);
    });
  });
  renderCards(cards, els.setPageShell.querySelector("#setCardsGrid"), readonly ? { readonly: true, hideWishlist: true } : { setMissingSelectable: true });
  if (!readonly) updateSetMissingBar();
}

async function addSetMissingToMissingList(setCode, button) {
  const status = els.setPageShell.querySelector("#setPageStatus");
  button.disabled = true;
  const original = button.textContent;
  button.textContent = "Adding...";
  try {
    const result = await api(`/api/sets/${encodeURIComponent(setCode)}/missing-list`, {
      method: "POST",
      body: "{}",
    });
    const added = Number(result.added || 0);
    const tagged = Number(result.tagged || 0);
    setStatus(`${integer.format(added)} newly added. ${integer.format(tagged)} missing cards are now on the Missing List.`, "success", status);
    await loadMissingList();
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

async function addSelectedSetMissingToMissingList(button) {
  const cards = Array.from(state.selectedSetMissingCards.values());
  if (!cards.length) return;
  const status = els.setPageShell.querySelector("#setPageStatus");
  button.disabled = true;
  const original = button.textContent;
  button.textContent = "Adding...";
  try {
    const result = await api("/api/cards/missing-list", {
      method: "POST",
      body: JSON.stringify({ cards, missing_list: true }),
    });
    setStatus(`${integer.format(result.updated || 0)} card${Number(result.updated || 0) === 1 ? "" : "s"} added to Missing List.`, "success", status);
    clearSetMissingSelection();
    if (state.activeSet?.set_code) {
      await loadSetPage(state.activeSet.set_code);
    }
    await loadMissingList();
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

function deckRowsHtml(cards, emptyMessage = "No cards in this deck yet.") {
  if (!cards.length) {
    return `<div class="empty-state">${escapeHtml(emptyMessage)}</div>`;
  }
  return cards.map((card) => `
    <article class="deck-card-row deck-card-preview-trigger ${Number(card.short_quantity || 0) > 0 ? "is-short" : ""}" role="button" tabindex="0" data-card-id="${escapeHtml(card.scryfall_id || card.card_id || "")}" data-variant="${escapeHtml(card.variant || "Normal")}">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
        ${deckInventoryStatusHtml(card)}
      </div>
      <b>Qty ${integer.format(deckQuantity(card))}</b>
    </article>
  `).join("");
}

function profileFavoriteRowsHtml(cards) {
  if (!cards.length) {
    return '<div class="empty-state">No public favorite cards yet.</div>';
  }
  return cards.map((card) => `
    <article class="deck-card-row deck-card-preview-trigger" role="button" tabindex="0" data-card-id="${escapeHtml(card.scryfall_id || card.card_id || "")}" data-variant="${escapeHtml(card.variant || "Normal")}">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
      </div>
    </article>
  `).join("");
}

function containerRowsHtml(cards) {
  if (!cards.length) {
    return '<div class="empty-state">No cards in this container yet.</div>';
  }
  return cards.map((card) => `
    <article class="deck-card-row container-shared-row">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
      </div>
      <b>Stored ${integer.format(card.stored_quantity || 0)}</b>
    </article>
  `).join("");
}

function wishlistRowsHtml(cards) {
  if (!cards.length) {
    return '<div class="empty-state">No cards in this wishlist yet.</div>';
  }
  return cards.map((card) => `
    <article class="deck-card-row wishlist-shared-row ${card.fulfilled ? "is-fulfilled" : ""}">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
        <div class="missing-market-links shared-wishlist-market-links">${marketplaceLinksHtml(card)}</div>
      </div>
      <b>${card.wishlist_quantity ? `Need ${integer.format(card.wishlist_quantity)}` : dollars.format(card.display_price || 0)}${card.fulfilled ? " ✓" : ""}</b>
    </article>
  `).join("");
}

async function toggleSharedDeckFavorite(deck, button) {
  if (!state.user) {
    openAuthModal("login", "Log in to favorite another user's deck.");
    return;
  }
  const nextFavorite = !deck.favorite_deck;
  button.disabled = true;
  try {
    const result = await api(`/api/shared-decks/${encodeURIComponent(deck.share_id)}/favorite`, {
      method: "POST",
      body: JSON.stringify({ favorite: nextFavorite }),
      promptLogin: true,
    });
    renderSharedDeck(result.deck || { ...deck, favorite_deck: nextFavorite });
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

async function importSharedDeck(deck, button) {
  if (!state.user) {
    openAuthModal("login", "Log in to save another user's deck.");
    return;
  }
  const defaultName = sharedDeckCopyName(deck);
  const name = window.prompt("Save this shared deck to your Decks as:", defaultName);
  if (name === null) {
    return;
  }
  const cleanName = name.trim();
  if (!cleanName) {
    setStatus("Deck name is required.", "error");
    return;
  }
  if (cleanName.length > 20) {
    setStatus("Deck name must be 20 characters or fewer.", "error");
    return;
  }
  if (containsDisallowedNameWord(cleanName)) {
    setStatus("Deck name contains language that is not allowed.", "error");
    return;
  }
  const decks = await loadDecks();
  let replace = false;
  const duplicate = decks.find((existing) => String(existing.name || "").toLowerCase() === cleanName.toLowerCase());
  if (duplicate) {
    replace = window.confirm(`You already have a deck named "${cleanName}". Replace it with this shared deck?`);
    if (!replace) return;
  }
  button.disabled = true;
  const original = button.innerHTML;
  button.textContent = "Saving...";
  try {
    let result = await api(`/api/shared-decks/${encodeURIComponent(deck.share_id)}/import`, {
      method: "POST",
      body: JSON.stringify({ name: cleanName, replace }),
      promptLogin: true,
    });
    if (result.duplicate) {
      const confirmed = window.confirm(`You already have a deck named "${result.name}". Replace it with this shared deck?`);
      if (confirmed) {
        result = await api(`/api/shared-decks/${encodeURIComponent(deck.share_id)}/import`, {
          method: "POST",
          body: JSON.stringify({ name: result.name, replace: true }),
          promptLogin: true,
        });
      } else {
        return;
      }
    }
    const copiedDeck = result.deck || {};
    const message = `${result.replaced ? "Replaced" : "Saved"} deck "${copiedDeck.name || cleanName}" with ${integer.format(result.imported || 0)} card${Number(result.imported || 0) === 1 ? "" : "s"}.`;
    const status = els.deckShareShell.querySelector(".shared-deck-action-status");
    if (status) {
      status.textContent = message;
      status.dataset.tone = "success";
    }
    await loadDecks();
    await refresh();
    if (copiedDeck.id) {
      await openDeckPage(copiedDeck.id);
    }
  } catch (error) {
    const status = els.deckShareShell.querySelector(".shared-deck-action-status");
    if (status) {
      status.textContent = error.message;
      status.dataset.tone = "error";
    } else {
      setStatus(error.message, "error");
    }
  } finally {
    button.disabled = false;
    button.innerHTML = original;
  }
}

function titleCaseDeckPrefix(value) {
  return String(value || "")
    .replace(/@.*$/, "")
    .replace(/[^a-z0-9 ]+/gi, " ")
    .replace(/\s+/g, " ")
    .trim()
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function sharedDeckCopyName(deck) {
  if (deck?._forcedName) return deck._forcedName;
  const owner = titleCaseDeckPrefix(deck.owner_name || "User") || "User";
  const deckName = String(deck.name || "Deck").replace(/\s+/g, " ").trim() || "Deck";
  const combined = `${owner} ${deckName}`.trim();
  if (combined.length <= 20) return combined;
  if (owner.length >= 18) return owner.slice(0, 20).trim();
  const prefix = `${owner} `;
  const remaining = Math.max(1, 20 - prefix.length);
  return `${prefix}${deckName.slice(0, remaining)}`.trim();
}

function renderSharedDeck(deck) {
  const cards = deck.cards || [];
  const cardCount = Number(deck.card_count || cards.reduce((total, card) => total + deckQuantity(card), 0));
  const actionHtml = deck.can_favorite || deck.can_import ? `
    <div class="shared-deck-actions" aria-label="Deck actions">
      ${deck.can_favorite ? `<button class="share-button shared-deck-favorite-button ${deck.favorite_deck ? "is-favorite" : ""}" type="button" aria-label="${deck.favorite_deck ? "Remove deck from favorites" : "Favorite this deck"}" title="${deck.favorite_deck ? "Remove from favorites" : "Favorite this deck"}">☆</button>` : ""}
      ${deck.can_import ? `<button class="share-button shared-deck-import-button" type="button" aria-label="Save to my Decks" title="Save to my Decks"><span class="copy-deck-icon" aria-hidden="true"></span></button>` : ""}
    </div>
    <div class="shared-deck-action-status status" aria-live="polite"></div>
  ` : "";
  els.deckShareShell.innerHTML = `
    <section class="shared-deck-card">
      <div class="shared-deck-head">
        <div>
          <p class="eyebrow">Shared deck</p>
          <h2>${escapeHtml(deck.name || "Deck")}</h2>
          <span>${integer.format(cardCount)} cards${deck.owner_name ? ` - ${displayNameHtml(deck.owner_name, { is_pro: deck.owner_is_pro, role: deck.owner_role })}` : ""}</span>
        </div>
        ${actionHtml}
      </div>
      <div class="shared-deck-content">
        <div class="deck-detail-list shared-deck-list">
          ${deckRowsHtml(cards, "No cards in this deck yet.")}
        </div>
        <aside class="shared-deck-notes" aria-label="Deck notes">
          <section class="shared-note-box">
            <p class="eyebrow">Description</p>
            <p>${escapeHtml(deck.description || "No description shared.")}</p>
          </section>
          <section class="shared-note-box shared-note-box-large">
            <p class="eyebrow">External Notes</p>
            <p>${escapeHtml(deck.external_notes || "No external notes shared.")}</p>
          </section>
        </aside>
      </div>
    </section>
  `;
  const favoriteButton = els.deckShareShell.querySelector(".shared-deck-favorite-button");
  if (favoriteButton) {
    favoriteButton.addEventListener("click", () => toggleSharedDeckFavorite(deck, favoriteButton));
  }
  const importButton = els.deckShareShell.querySelector(".shared-deck-import-button");
  if (importButton) {
    importButton.addEventListener("click", () => importSharedDeck(deck, importButton));
  }
  wireDeckCardPreviewRows(els.deckShareShell.querySelector(".shared-deck-list"), cards);
}

function renderSharedWishlist(wishlist) {
  const cards = wishlist.cards || [];
  els.wishlistShareShell.innerHTML = `
    <section class="shared-deck-card">
      <div class="shared-deck-head">
        <div>
          <p class="eyebrow">Shared wishlist</p>
          <h2>${escapeHtml(wishlist.name || "Wishlist")}</h2>
          <span>${integer.format(cards.length)} card${cards.length === 1 ? "" : "s"}</span>
        </div>
      </div>
      <div class="deck-detail-list">
        ${wishlistRowsHtml(cards)}
      </div>
    </section>
  `;
}

function renderSharedContainer(container) {
  const cards = container.cards || [];
  const storedCount = Number(container.stored_quantity || cards.reduce((total, card) => total + Number(card.stored_quantity || 0), 0));
  const meta = [containerTypeLabel(container.storage_type), container.location].filter(Boolean).join(" - ");
  els.containerShareShell.innerHTML = `
    <section class="shared-deck-card">
      <div class="shared-deck-head">
        <div>
          <p class="eyebrow">Shared container</p>
          <h2>${escapeHtml(container.name || "Container")}</h2>
          <span>${integer.format(storedCount)} stored cards${meta ? ` - ${escapeHtml(meta)}` : ""}</span>
        </div>
      </div>
      ${container.notes ? `<p class="shared-card-note">${escapeHtml(container.notes)}</p>` : ""}
      <div class="deck-detail-list">
        ${containerRowsHtml(cards)}
      </div>
    </section>
  `;
}

function renderSharedStore(store) {
  const cards = store.cards || [];
  const contacts = store.contacts || [];
  const contactHtml = contacts.length ? `
    <div class="store-contact-list" aria-label="Seller contact methods">
      ${contacts.map((contact) => {
        const value = escapeHtml(contact.value || "");
        const label = escapeHtml(contact.label || "Contact");
        return contact.href
          ? `<a href="${escapeHtml(contact.href)}" target="${String(contact.href).startsWith("mailto:") ? "_self" : "_blank"}" rel="noreferrer"><strong>${label}</strong><span>${value}</span></a>`
          : `<span><strong>${label}</strong><span>${value}</span></span>`;
      }).join("")}
    </div>
  ` : "";
  const rows = cards.length ? cards.map((card) => `
    <article class="deck-card-row favorite-deck-share-row">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.variant || "Normal")} - ${escapeHtml(conditionText(card))}</span>
        <small>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")}</small>
      </div>
      <b>${integer.format(card.sale_quantity || 0)} @ ${dollars.format(card.sale_price || 0)}</b>
    </article>
  `).join("") : '<div class="empty-state">No active sale listings.</div>';
  els.storeShareShell.innerHTML = `
    <section class="shared-deck-card">
      <div class="shared-deck-head">
        <div>
          <p class="eyebrow">Arcane Ledger store</p>
          <h2>${displayNameHtml(store.seller_name || "Seller", { is_pro: store.seller_is_pro, role: store.seller_role })}</h2>
          <span>${integer.format(store.card_count || cards.length)} listing${Number(store.card_count || cards.length) === 1 ? "" : "s"} - ${integer.format(store.sale_quantity || 0)} card${Number(store.sale_quantity || 0) === 1 ? "" : "s"} for sale</span>
          ${contactHtml}
        </div>
      </div>
      <div class="deck-detail-list">
        ${rows}
      </div>
    </section>
  `;
}

function profileAvatarHtml(actor, className = "profile-mini-avatar") {
  const name = actor?.name || "User";
  if (actor?.profile_image) {
    return `<span class="${className}"><img src="${escapeHtml(actor.profile_image)}" alt="${escapeHtml(name)} profile picture"></span>`;
  }
  return `<span class="${className}">${escapeHtml(name.slice(0, 1).toUpperCase())}</span>`;
}

function formatActivityDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return formatDate(value);
  return date.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function profileCommentRows(comments, parentId = null) {
  const rows = (comments || []).filter((comment) => (comment.parent_comment_id || null) === parentId);
  if (!rows.length) return "";
  return rows.map((comment) => `
    <article class="profile-comment ${parentId ? "is-reply" : ""}">
      <div class="profile-feed-author">
        ${profileAvatarHtml(comment.author)}
        <div>
          <strong>${profileActorLink(comment.author)}</strong>
          <span>${escapeHtml(formatActivityDate(comment.created_at))}</span>
        </div>
      </div>
      <p>${escapeHtml(comment.body || "")}</p>
      ${state.user ? `<button class="report-content-button" type="button" data-target-type="profile_comment" data-target-id="${escapeHtml(comment.id)}" data-target-label="blog comment by ${escapeAttribute(comment.author?.name || "Arcane Ledger user")}">Report</button>` : ""}
      ${state.user ? `
        <form class="profile-reply-form" data-post-id="${escapeHtml(comment.post_id)}" data-parent-id="${escapeHtml(comment.id)}">
          <input name="body" type="text" maxlength="1000" placeholder="Reply">
          <button class="secondary-button compact-button" type="submit">Reply</button>
        </form>
      ` : ""}
      ${profileCommentRows(comments, comment.id)}
    </article>
  `).join("");
}

function profileFeedItemHtml(item) {
  return `
    <article class="profile-feed-item">
      <div class="profile-feed-author">
        ${profileAvatarHtml(item.author)}
        <div>
          <strong>${profileActorLink(item.author)}</strong>
          <span>${escapeHtml(formatActivityDate(item.created_at))}</span>
        </div>
      </div>
      <p>${escapeHtml(item.body || "")}</p>
    </article>
  `;
}

function renderUserProfile(profile) {
  state.userProfile = profile;
  const stats = profile.stats || {};
  const contacts = profile.contacts || [];
  const favorites = profile.favorites || [];
  const decks = profile.public_decks || [];
  const friends = profile.friends || [];
  const wallMessages = profile.wall_messages || [];
  const posts = profile.posts || [];
  const contactHtml = contacts.length ? `
    <div class="store-contact-list profile-contact-list" aria-label="Profile contact methods">
      ${contacts.map((contact) => {
        const value = escapeHtml(contact.value || "");
        const label = escapeHtml(contact.label || "Contact");
        return contact.href
          ? `<a href="${escapeHtml(contact.href)}" target="${String(contact.href).startsWith("mailto:") ? "_self" : "_blank"}" rel="noreferrer"><strong>${label}</strong><span>${value}</span></a>`
          : `<span><strong>${label}</strong><span>${value}</span></span>`;
      }).join("")}
    </div>
  ` : "";
  const profileImage = profile.profile_image
    ? `<img src="${escapeHtml(profile.profile_image)}" alt="${escapeHtml(profile.name || "User")} profile picture">`
    : `<span>${escapeHtml((profile.name || "U").slice(0, 1).toUpperCase())}</span>`;
  const favoriteRows = profileFavoriteRowsHtml(favorites);
  const deckRows = decks.length ? `
    <div class="profile-deck-list">
      ${decks.map((deck) => `
        <a class="profile-deck-card" href="${escapeHtml(deck.deck_url || `/decks/${encodeURIComponent(deck.share_id || "")}`)}">
          ${deckPreviewImagesHtml(deck.preview_images || [])}
          <strong>${escapeHtml(deck.name || "Deck")}</strong>
          <span>${integer.format(deck.card_count || 0)} cards · ${integer.format(deck.unique_card_count || 0)} unique</span>
        </a>
      `).join("")}
    </div>
  ` : '<div class="empty-state">No public decks yet.</div>';
  const friendRows = friends.length ? `
    <div class="profile-friend-list">
      ${friends.map((friend) => `
        <a class="profile-friend-row" href="${escapeHtml(friend.profile_url || `/user/${encodeURIComponent(friend.profile_slug || "")}`)}">
          ${profileAvatarHtml(friend)}
          <span>${displayNameHtml(friend.name || "Collector", friend)}</span>
        </a>
      `).join("")}
    </div>
  ` : '<div class="empty-state compact-empty">No friends added yet.</div>';
  const wallForm = profile.can_post_wall ? `
    <form id="profileWallForm" class="profile-compose-form">
      <textarea name="body" maxlength="800" rows="3" placeholder="Leave a message on ${escapeHtml(profile.name || "this profile")}'s wall."></textarea>
      <button class="primary-button" type="submit">Post Message</button>
    </form>
  ` : '<div class="empty-state compact-empty">Log in to leave a wall message.</div>';
  const wallRows = wallMessages.length ? wallMessages.map(profileFeedItemHtml).join("") : '<div class="empty-state compact-empty">No wall messages yet.</div>';
  const postForm = profile.can_post_blog ? `
    <form id="profilePostForm" class="profile-compose-form">
      <textarea name="body" maxlength="2400" rows="4" placeholder="Post an update for your followers."></textarea>
      <button class="primary-button" type="submit">Post Update</button>
    </form>
  ` : "";
  const postRows = posts.length ? posts.map((post) => `
    <article class="profile-post">
      <div class="profile-feed-author">
        ${profileAvatarHtml(profile)}
        <div>
          <strong>${displayNameHtml(profile.name || "Collector", profile)}</strong>
          <span>${escapeHtml(formatActivityDate(post.created_at))}</span>
        </div>
      </div>
      <p>${escapeHtml(post.body || "")}</p>
      ${state.user ? `<button class="report-content-button" type="button" data-target-type="profile_post" data-target-id="${escapeHtml(post.id)}" data-target-label="blog post by ${escapeAttribute(profile.name || "Collector")}">Report</button>` : ""}
      ${post.card ? `<div class="profile-post-card-link">${cardBlogPreviewHtml(post.card)}</div>` : ""}
      ${post.deck ? `<div class="profile-post-card-link">${deckBlogPreviewHtml(post.deck)}</div>` : ""}
      ${profile.can_comment ? `
        <form class="profile-comment-form" data-post-id="${escapeHtml(post.id)}">
          <input name="body" type="text" maxlength="1000" placeholder="Write a comment">
          <button class="secondary-button compact-button" type="submit">Comment</button>
        </form>
      ` : ""}
      <div class="profile-comments">
        ${profileCommentRows(post.comments || []) || '<div class="empty-state compact-empty">No comments yet.</div>'}
      </div>
    </article>
  `).join("") : '<div class="empty-state compact-empty">No blog posts yet.</div>';
  const addFriendButton = profile.can_add_friend ? '<button id="profileAddFriendButton" class="secondary-button" type="button">Add Friend</button>' : "";
  const alreadyFriend = profile.is_friend ? '<span class="profile-status-pill">Friend Added</span>' : "";
  els.userProfileShell.innerHTML = `
    <section class="user-profile-card">
      <div class="user-profile-hero">
        <div class="user-profile-avatar">${profileImage}</div>
        <div>
          <p class="eyebrow">Arcane Ledger profile</p>
          <h2>${displayNameHtml(profile.name || "Collector", profile)}</h2>
          <span>Member since ${escapeHtml(formatDate(profile.member_since || ""))}</span>
          ${profile.about_me ? `<p>${escapeHtml(profile.about_me)}</p>` : ""}
          ${contactHtml}
        </div>
      </div>
      <div class="user-profile-stats">
        <article><span>Cards</span><strong>${integer.format(stats.owned_quantity || 0)}</strong></article>
        <article><span>Unique</span><strong>${integer.format(stats.unique_cards || 0)}</strong></article>
        <article><span>Collection value</span><strong>${dollars.format(stats.collection_value || 0)}</strong></article>
        <article><span>Public decks</span><strong>${integer.format(stats.public_deck_count || decks.length || 0)}</strong></article>
      </div>
      <div class="user-profile-actions">
        ${profile.store_url ? `<a class="primary-button" href="${escapeHtml(profile.store_url)}">View Store</a>` : ""}
        ${decks.length ? `<a class="secondary-button" href="#profileDecks">Public Decks</a>` : ""}
        ${addFriendButton}
        ${alreadyFriend}
      </div>
      <div id="profilePageStatus" class="status" aria-live="polite"></div>
      <div class="user-profile-layout">
        <div class="user-profile-left">
          <section class="profile-panel">
            <div class="panel-head">
              <h3>Favorite Cards</h3>
              <span>${integer.format(favorites.length)} shown</span>
            </div>
            <div class="deck-detail-list">${favoriteRows}</div>
          </section>
          <section id="profileDecks" class="profile-panel">
            <div class="panel-head">
              <h3>Public Decks</h3>
              <span>${integer.format(decks.length)} shown</span>
            </div>
            ${deckRows}
          </section>
        </div>
        <div class="user-profile-right">
          ${profile.is_self ? `
            <section class="profile-panel">
              <div class="panel-head">
                <h3>Friends</h3>
                <span>${integer.format(friends.length)}</span>
              </div>
              ${friendRows}
            </section>
          ` : ""}
          <section class="profile-panel profile-wall-panel">
            <div class="panel-head">
              <h3>Wall</h3>
              <span>${integer.format(wallMessages.length)} messages</span>
            </div>
            ${wallForm}
            <div class="profile-feed-list">${wallRows}</div>
          </section>
          <section class="profile-panel profile-post-panel">
            <div class="panel-head">
              <h3>Blog Posts</h3>
              <span>${integer.format(posts.length)} posts</span>
            </div>
            ${postForm}
            <div class="profile-post-list">${postRows}</div>
          </section>
        </div>
      </div>
    </section>
  `;
  wireUserProfileInteractions(profile);
}

function profileStatusTarget() {
  return document.querySelector("#profilePageStatus");
}

async function refreshRenderedUserProfile(result) {
  if (result?.profile) {
    renderUserProfile(result.profile);
    return;
  }
  if (state.userProfile?.profile_slug) {
    await loadUserProfile(state.userProfile.profile_slug);
  }
}

function wireUserProfileInteractions(profile) {
  const slug = profile.profile_slug || "";
  document.querySelector("#profileAddFriendButton")?.addEventListener("click", async () => {
    try {
      const result = await api(`/api/users/profile/${encodeURIComponent(slug)}/friend`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      await refreshRenderedUserProfile(result);
      setStatus("Friend added.", "success", profileStatusTarget());
    } catch (error) {
      setStatus(error.message, "error", profileStatusTarget());
    }
  });
  document.querySelector("#profileWallForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      const result = await api(`/api/users/profile/${encodeURIComponent(slug)}/wall`, {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(new FormData(form).entries())),
      });
      await refreshRenderedUserProfile(result);
      setStatus("Wall message posted.", "success", profileStatusTarget());
    } catch (error) {
      setStatus(error.message, "error", profileStatusTarget());
    }
  });
  document.querySelector("#profilePostForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      const result = await api(`/api/users/profile/${encodeURIComponent(slug)}/posts`, {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(new FormData(form).entries())),
      });
      await refreshRenderedUserProfile(result);
      setStatus("Blog post published.", "success", profileStatusTarget());
    } catch (error) {
      setStatus(error.message, "error", profileStatusTarget());
    }
  });
  for (const form of document.querySelectorAll(".profile-comment-form, .profile-reply-form")) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const postId = form.dataset.postId;
      const payload = Object.fromEntries(new FormData(form).entries());
      if (form.dataset.parentId) {
        payload.parent_comment_id = form.dataset.parentId;
      }
      try {
        const result = await api(`/api/profile/posts/${encodeURIComponent(postId)}/comments`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        await refreshRenderedUserProfile(result);
        setStatus("Reply posted.", "success", profileStatusTarget());
      } catch (error) {
        setStatus(error.message, "error", profileStatusTarget());
      }
    });
  }
}

function renderSharedFavorites(payload) {
  const cards = payload.cards || [];
  const decks = payload.decks || [];
  const store = payload.store || [];
  const ownerName = payload.owner_name || "Collector";
  const deckRows = decks.length ? `
    <div class="favorite-decks-share-list">
      ${decks.map((deck) => `
        <article class="deck-card-row favorite-deck-share-row">
          <span class="deck-icon" aria-hidden="true"></span>
          <div>
            <strong>${escapeHtml(deck.name || "Deck")}</strong>
          <span>${displayNameHtml(deck.owner_name || "Arcane Ledger user", { is_pro: deck.owner_is_pro, role: deck.owner_role })} - ${integer.format(deck.card_count || 0)} cards</span>
          </div>
          <a class="share-button" href="${escapeHtml(deck.deck_url || `/decks/${encodeURIComponent(deck.share_id || "")}`)}" target="_blank" rel="noreferrer" aria-label="Open deck" title="Open deck">&#8599;</a>
        </article>
      `).join("")}
    </div>
  ` : "";
  const storeRows = store.length ? `
    <div class="favorite-decks-share-list">
      ${store.map((listing) => `
        <article class="deck-card-row favorite-deck-share-row">
          <img src="${escapeHtml(listing.image_small || listing.image_normal || "")}" alt="">
          <div>
            <strong>${escapeHtml(cardTitle(listing))}</strong>
            <span>${displayNameHtml(listing.seller_name || "Seller", { is_pro: listing.seller_is_pro, role: listing.seller_role })} - ${escapeHtml(listing.variant || "Normal")} - ${escapeHtml(listing.card_condition || "Near Mint")}</span>
          </div>
          <a class="share-button" href="${escapeHtml(listing.store_url || "#")}" target="_blank" rel="noreferrer" aria-label="Open store" title="Open store">&#8599;</a>
        </article>
      `).join("")}
    </div>
  ` : "";
  els.favoritesShareShell.innerHTML = `
    <section class="shared-deck-card">
      <div class="shared-deck-head">
        <div>
          <p class="eyebrow">Shared favorites</p>
          <h2>${escapeHtml(ownerName)}'s Favorites</h2>
          <span>${integer.format(cards.length)} favorite cards - ${integer.format(decks.length)} favorite decks - ${integer.format(store.length)} store listings</span>
        </div>
      </div>
      ${deckRows}
      ${storeRows}
      <div class="deck-detail-list">
        ${deckRowsHtml(cards)}
      </div>
    </section>
  `;
}

async function loadSharedWishlist(shareId) {
  showPage("wishlist-share");
  els.wishlistShareShell.innerHTML = '<div class="empty-state">Loading shared wishlist...</div>';
  try {
    const wishlist = await api(`/api/shared-wishlists/${encodeURIComponent(shareId)}`);
    renderSharedWishlist(wishlist);
  } catch (error) {
    els.wishlistShareShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadSharedDeck(shareId) {
  showPage("deck-share");
  els.deckShareShell.innerHTML = '<div class="empty-state">Loading shared deck...</div>';
  try {
    const deck = await api(`/api/shared-decks/${encodeURIComponent(shareId)}`);
    renderSharedDeck(deck);
  } catch (error) {
    els.deckShareShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadSharedContainer(shareId) {
  showPage("container-share");
  els.containerShareShell.innerHTML = '<div class="empty-state">Loading shared container...</div>';
  try {
    const container = await api(`/api/shared-containers/${encodeURIComponent(shareId)}`);
    renderSharedContainer(container);
  } catch (error) {
    els.containerShareShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadSharedStore(shareId) {
  showPage("store-share");
  els.storeShareShell.innerHTML = '<div class="empty-state">Loading store...</div>';
  try {
    const store = await api(`/api/stores/${encodeURIComponent(shareId)}`);
    renderSharedStore(store);
  } catch (error) {
    els.storeShareShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadUserProfile(slug) {
  showPage("user-profile");
  els.userProfileShell.innerHTML = '<div class="empty-state">Loading profile...</div>';
  try {
    const profile = await api(`/api/users/profile/${encodeURIComponent(slug)}`);
    renderUserProfile(profile);
  } catch (error) {
    els.userProfileShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadSharedFavorites(shareId) {
  showPage("favorites-share");
  els.favoritesShareShell.innerHTML = '<div class="empty-state">Loading shared favorites...</div>';
  try {
    const payload = await api(`/api/shared-favorites/${encodeURIComponent(shareId || "")}`);
    renderSharedFavorites(payload);
  } catch (error) {
    els.favoritesShareShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadSetPage(setCode) {
  if (!setCode) return;
  showPage("set");
  els.setPageShell.innerHTML = '<div class="empty-state">Loading set...</div>';
  try {
    const [setDetail, cardData] = await Promise.all([
      api(`/api/sets/${encodeURIComponent(setCode)}`),
      api(`/api/cards?${new URLSearchParams({
        set: setCode,
        owned: "all",
        sort: "set-owned",
        limit: "5000",
      }).toString()}`),
    ]);
    renderSetPage(setDetail, cardData.cards || []);
  } catch (error) {
    els.setPageShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadSharedSet(route) {
  if (!route?.storeShareId || !route?.setCode) return;
  showPage("set");
  els.setPageShell.innerHTML = '<div class="empty-state">Loading shared set...</div>';
  try {
    const payload = await api(`/api/shared-sets/${encodeURIComponent(route.storeShareId)}/${encodeURIComponent(route.setCode)}`);
    renderSetPage(payload, payload.cards || [], { readonly: true });
  } catch (error) {
    els.setPageShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function openSetPage(setCode) {
  if (!setCode) return;
  const normalized = String(setCode).toLowerCase();
  window.history.pushState({}, "", `/sets/${encodeURIComponent(normalized)}`);
  loadSetPage(normalized);
}

async function refresh() {
  const [dashboard] = await Promise.all([
    api("/api/dashboard"),
    loadCards(),
  ]);
  renderDashboard(dashboard);
}

async function refreshPriceSnapshots() {
  const button = els.refreshPriceSnapshotsButton;
  if (!button) return;
  const original = button.textContent;
  button.disabled = true;
  button.textContent = "Snapshotting...";
  try {
    const result = await api("/api/prices/snapshots/refresh", {
      method: "POST",
      body: JSON.stringify({ limit: 250 }),
      promptLogin: true,
    });
    await refresh();
    setStatus(`Saved ${integer.format(result.refreshed || 0)} price snapshot${Number(result.refreshed || 0) === 1 ? "" : "s"} for ${result.snapshot_date}.`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

function wireEvents() {
  window.addEventListener("beforeunload", (event) => {
    if (!state.deckEditorDirty) return;
    event.preventDefault();
    event.returnValue = "";
  });
  document.addEventListener("click", (event) => {
    const button = event.target.closest?.(".report-content-button");
    if (!button) return;
    event.preventDefault();
    openReportModal({
      type: button.dataset.targetType,
      id: button.dataset.targetId,
      label: button.dataset.targetLabel,
    });
  });
  for (const command of els.navCommands) {
    if (command.id === "myProfileButton") continue;
    command.addEventListener("click", () => {
      const page = command.dataset.pageTarget || "dashboard";
      activatePage(page, { push: true });
    });
  }
  els.myProfileButton?.addEventListener("click", openMyProfile);
  window.addEventListener("popstate", () => {
    const routePage = appPageRoute();
    if (routePage) {
      activatePage(routePage, { fromPop: true });
      return;
    }
    if (deckEditorIsVisible() && state.deckEditorDirty && !confirmDiscardDeckEditorChanges()) {
      if (state.activeDeck?.id) {
        window.history.pushState({}, "", `/decks/${encodeURIComponent(state.activeDeck.id)}`);
      }
      return;
    }
    discardDeckEditorChanges();
    const detail = cardDetailRoute();
    if (detail) {
      loadCardDetail(detail.cardId, detail.variant);
      return;
    }
    const setCode = setRouteCode();
    if (setCode) {
      loadSetPage(setCode);
      return;
    }
    const profileSlug = userProfileRoute();
    if (profileSlug) {
      loadUserProfile(profileSlug);
      return;
    }
    const deckId = deckRouteId();
    if (deckId) {
      if (isPrivateDeckRoute(deckId) && state.user) {
        loadDeckEditor(deckId);
      } else if (isPrivateDeckRoute(deckId)) {
        activatePage("home", { replace: true, promptLogin: false });
        openAuthModal("login", "Log in to edit this deck.");
      } else {
        document.body.classList.toggle("share-only", !isPrivateDeckRoute(deckId));
        loadSharedDeck(deckId);
      }
    }
  });

  els.searchInput.addEventListener("input", () => {
    window.clearTimeout(state.searchTimer);
    state.searchTimer = window.setTimeout(() => {
      clearSelectedCards();
      loadCards().catch((error) => setStatus(error.message, "error"));
    }, 180);
  });
  els.ownedFilter.addEventListener("change", () => {
    clearSelectedCards();
    loadCards().catch((error) => setStatus(error.message, "error"));
  });
  els.sortSelect.addEventListener("change", () => {
    clearSelectedCards();
    loadCards().catch((error) => setStatus(error.message, "error"));
  });
  els.favoriteSearchInput.addEventListener("input", () => {
    window.clearTimeout(state.favoriteSearchTimer);
    state.favoriteSearchTimer = window.setTimeout(() => {
      clearSelectedCards();
      loadFavorites().catch((error) => setStatus(error.message, "error", els.favoritesStatus));
    }, 180);
  });
  els.favoriteSortSelect.addEventListener("change", () => {
    clearSelectedCards();
    loadFavorites().catch((error) => setStatus(error.message, "error", els.favoritesStatus));
  });
  els.missingSearchInput.addEventListener("input", () => {
    window.clearTimeout(state.missingSearchTimer);
    state.missingSearchTimer = window.setTimeout(() => {
      clearSelectedCards();
      loadMissingList().catch((error) => setStatus(error.message, "error", els.missingStatus));
    }, 180);
  });
  els.missingSortSelect.addEventListener("change", () => {
    clearSelectedCards();
    loadMissingList().catch((error) => setStatus(error.message, "error", els.missingStatus));
  });
  els.saleSearchInput.addEventListener("input", () => {
    window.clearTimeout(state.saleSearchTimer);
    state.saleSearchTimer = window.setTimeout(() => {
      loadSaleCards().catch((error) => setStatus(error.message, "error", els.saleStatus));
    }, 180);
  });
  els.saleSortSelect.addEventListener("change", () => {
    loadSaleCards().catch((error) => setStatus(error.message, "error", els.saleStatus));
  });
  els.storeFrontSearchInput.addEventListener("input", () => {
    window.clearTimeout(state.storeFrontSearchTimer);
    state.storeFrontSearchTimer = window.setTimeout(() => {
      loadStoreFront().catch((error) => setStatus(error.message, "error", els.storeFrontStatus));
    }, 180);
  });
  els.storeFrontSortSelect.addEventListener("change", () => {
    loadStoreFront().catch((error) => setStatus(error.message, "error", els.storeFrontStatus));
  });
  els.wishlistSearchInput.addEventListener("input", () => {
    window.clearTimeout(state.wishlistSearchTimer);
    state.wishlistSearchTimer = window.setTimeout(() => {
      loadWishlist().catch((error) => setStatus(error.message, "error", els.wishlistStatus));
    }, 180);
  });
  els.wishlistSortSelect.addEventListener("change", () => {
    loadWishlist().catch((error) => setStatus(error.message, "error", els.wishlistStatus));
  });
  els.catalogSearchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    searchCatalog().catch((error) => setStatus(error.message, "error", els.catalogSearchStatus));
  });
  els.catalogSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      searchCatalog().catch((error) => setStatus(error.message, "error", els.catalogSearchStatus));
    }
  });
  els.catalogHideOwnedFilter.addEventListener("change", () => {
    if (!state.catalogSearchAllResults.length) return;
    const stats = applyCatalogOwnedFilter();
    renderCatalogSearchResults();
    els.catalogSearchStatus.textContent = catalogSearchStatusText(stats);
  });

  els.addCardButton.addEventListener("click", () => {
    if (!state.user) {
      openAuthModal("login", "Create an account or log in before adding cards.");
      return;
    }
    openAddCardModal();
  });
  els.navCollapseButton?.addEventListener("click", toggleNavCollapsed);
  els.accountButton.addEventListener("click", () => {
    if (state.user) {
      activatePage("settings", { push: true });
    } else {
      openAuthModal("login");
    }
  });
  els.logoutButton.addEventListener("click", () => {
    if (state.user) {
      logout().catch((error) => setStatus(error.message, "error"));
    } else {
      openAuthModal("login");
    }
  });
  els.addDeckButton.addEventListener("click", openAddDeckModal);
  els.importDeckButton.addEventListener("click", openImportDeckModal);
  els.exportDecksButton.addEventListener("click", openExportDecksModal);
  els.addWishlistButton.addEventListener("click", openAddWishlistModal);
  els.addContainerButton.addEventListener("click", openAddContainerModal);
  els.refreshPriceSnapshotsButton?.addEventListener("click", () => {
    refreshPriceSnapshots().catch((error) => setStatus(error.message, "error"));
  });
  els.refreshAdminButton?.addEventListener("click", () => {
    loadAdmin().catch((error) => setStatus(error.message, "error", els.adminStatus));
  });
  els.refreshAdminLogsButton?.addEventListener("click", () => {
    loadAdminLogs().catch((error) => setStatus(error.message, "error", els.adminStatus));
  });
  els.adminLogLineCount?.addEventListener("change", () => {
    loadAdminLogs().catch((error) => setStatus(error.message, "error", els.adminStatus));
  });
  els.addAdminEmailTemplateButton?.addEventListener("click", addAdminEmailTemplate);
  els.closeAdminEmailTemplateButton?.addEventListener("click", closeAdminEmailTemplateModal);
  els.cancelAdminEmailTemplateButton?.addEventListener("click", closeAdminEmailTemplateModal);
  els.saveAdminEmailTemplateButton?.addEventListener("click", () => {
    saveAdminEmailTemplateBody().catch((error) => setStatus(`Template save failed: ${error.message}`, "error", els.adminEmailStatus || els.adminStatus));
  });
  els.adminEmailTemplateOverlay?.addEventListener("click", (event) => {
    if (event.target === els.adminEmailTemplateOverlay) {
      closeAdminEmailTemplateModal();
    }
  });
  els.addAdminAnnouncementButton?.addEventListener("click", addAdminAnnouncement);
  els.closeAdminAnnouncementButton?.addEventListener("click", closeAdminAnnouncementModal);
  els.cancelAdminAnnouncementButton?.addEventListener("click", closeAdminAnnouncementModal);
  els.draftAdminAnnouncementButton?.addEventListener("click", () => {
    saveAdminAnnouncement("draft").catch((error) => setStatus(`Announcement save failed: ${error.message}`, "error", els.adminAnnouncementStatus || els.adminStatus));
  });
  els.publishAdminAnnouncementButton?.addEventListener("click", () => {
    saveAdminAnnouncement("published").catch((error) => setStatus(`Announcement publish failed: ${error.message}`, "error", els.adminAnnouncementStatus || els.adminStatus));
  });
  els.adminAnnouncementOverlay?.addEventListener("click", (event) => {
    if (event.target === els.adminAnnouncementOverlay) {
      closeAdminAnnouncementModal();
    }
  });
  els.adminAnnouncementOverlay?.querySelectorAll("[data-markdown-action]")?.forEach((button) => {
    button.addEventListener("click", () => insertAnnouncementMarkdown(button.dataset.markdownAction));
  });
  els.uploadAdminWallpaperButton?.addEventListener("click", () => {
    uploadAdminWallpaper().catch((error) => setStatus(`Wallpaper upload failed: ${error.message}`, "error", els.adminWallpaperStatus || els.adminStatus));
  });
  els.closeHomeAnnouncementDetailButton?.addEventListener("click", closeHomeAnnouncementDetail);
  els.homeAnnouncementDetailOverlay?.addEventListener("click", (event) => {
    if (event.target === els.homeAnnouncementDetailOverlay) {
      closeHomeAnnouncementDetail();
    }
  });
  els.openChangelogButton?.addEventListener("click", () => {
    openChangelogModal().catch((error) => setStatus(error.message, "error", els.settingsPageStatus));
  });
  els.membershipBenefitsButton?.addEventListener("click", openMembershipBenefitsModal);
  els.closeMembershipBenefitsButton?.addEventListener("click", closeMembershipBenefitsModal);
  els.dismissMembershipBenefitsButton?.addEventListener("click", closeMembershipBenefitsModal);
  els.membershipBenefitsOverlay?.addEventListener("click", (event) => {
    if (event.target === els.membershipBenefitsOverlay) {
      closeMembershipBenefitsModal();
    }
  });
  els.billingMonthlyButton?.addEventListener("click", () => {
    startBillingCheckout("monthly").catch((error) => setStatus(error.message, "error", els.settingsPageStatus));
  });
  els.billingYearlyButton?.addEventListener("click", () => {
    startBillingCheckout("yearly").catch((error) => setStatus(error.message, "error", els.settingsPageStatus));
  });
  els.billingPortalButton?.addEventListener("click", () => {
    openBillingPortal().catch((error) => setStatus(error.message, "error", els.settingsPageStatus));
  });
  els.closeChangelogButton?.addEventListener("click", closeChangelogModal);
  els.dismissChangelogButton?.addEventListener("click", closeChangelogModal);
  els.changelogOverlay?.addEventListener("click", (event) => {
    if (event.target === els.changelogOverlay) {
      closeChangelogModal();
    }
  });
  els.closeAddPurchaseButton.addEventListener("click", closeAddPurchaseModal);
  els.cancelAddPurchaseButton.addEventListener("click", closeAddPurchaseModal);
  els.addPurchaseOverlay.addEventListener("click", (event) => {
    if (event.target === els.addPurchaseOverlay) {
      closeAddPurchaseModal();
    }
  });
  els.closeInventoryAdjustButton.addEventListener("click", closeInventoryAdjustModal);
  els.cancelInventoryAdjustButton.addEventListener("click", closeInventoryAdjustModal);
  els.inventoryAdjustOverlay.addEventListener("click", (event) => {
    if (event.target === els.inventoryAdjustOverlay) {
      closeInventoryAdjustModal();
    }
  });
  els.inventoryAdjustForm.adjustment_type.addEventListener("change", updateInventoryAdjustLimits);
  els.inventoryAdjustForm.variant.addEventListener("change", updateInventoryAdjustLimits);
  els.inventoryAdjustForm.card_condition.addEventListener("change", updateInventoryAdjustLimits);
  els.closeDirectSaleButton.addEventListener("click", closeDirectSaleModal);
  els.cancelDirectSaleButton.addEventListener("click", closeDirectSaleModal);
  els.directSaleOverlay.addEventListener("click", (event) => {
    if (event.target === els.directSaleOverlay) {
      closeDirectSaleModal();
    }
  });
  els.directSaleForm.variant.addEventListener("change", updateDirectSaleLimits);
  els.directSaleForm.card_condition.addEventListener("change", updateDirectSaleLimits);
  els.tileViewButton.addEventListener("click", () => setCollectionView("tiles"));
  els.listViewButton.addEventListener("click", () => setCollectionView("list"));
  els.favoriteTileViewButton.addEventListener("click", () => setFavoritesView("tiles"));
  els.favoriteListViewButton.addEventListener("click", () => setFavoritesView("list"));
  for (const button of els.favoriteFilterButtons || []) {
    button.addEventListener("click", () => setFavoritesFilter(button.dataset.favoritesFilter));
  }
  els.shareFavoritesButton.addEventListener("click", openFavoritesShareModal);
  els.emailFavoritesButton?.addEventListener("click", openEmailFavoritesModal);
  els.addToDeckButton.addEventListener("click", () => {
    openAssignDeckModal().catch((error) => setStatus(error.message, "error"));
  });
  els.addToContainerButton.addEventListener("click", () => {
    openAssignContainerModal().catch((error) => setStatus(error.message, "error"));
  });
  els.markForSaleButton.addEventListener("click", openSaleModal);
  els.favoriteAddToDeckButton.addEventListener("click", () => {
    openAssignDeckModal().catch((error) => setStatus(error.message, "error", els.favoritesStatus));
  });
  els.favoriteAddToContainerButton.addEventListener("click", () => {
    openAssignContainerModal().catch((error) => setStatus(error.message, "error", els.favoritesStatus));
  });
  els.importWizardNextButton?.addEventListener("click", () => {
    importWizardNext().catch((error) => {
      clearImportProgress();
      setStatus(error.message, "error", els.importStatus);
    });
  });
  els.importWizardBackButton?.addEventListener("click", importWizardBack);
  els.importWizardResetButton?.addEventListener("click", resetImportWizard);
  els.importWizardSaveButton?.addEventListener("click", () => {
    saveImportWizard().catch((error) => {
      clearImportProgress();
      setStatus(error.message, "error", els.importStatus);
    });
  });
  els.importWizardFile?.addEventListener("change", () => {
    if (els.importWizardFile.files?.length && els.importWizardJsonText) {
      els.importWizardJsonText.value = "";
    }
    state.importWizard.format = "";
    state.importWizard.text = "";
    setStatus("", "", els.importStatus);
  });
  els.importWizardJsonText?.addEventListener("input", () => {
    if (els.importWizardJsonText.value.trim() && els.importWizardFile) {
      els.importWizardFile.value = "";
    }
    state.importWizard.format = "";
    state.importWizard.text = "";
    setStatus("", "", els.importStatus);
  });
  els.previewJsonImportButton?.addEventListener("click", () => {
    previewImport("json").catch((error) => {
      els.importStatus.textContent = error.message;
    });
  });
  els.previewCsvImportButton?.addEventListener("click", () => {
    previewImport("csv").catch((error) => {
      els.importStatus.textContent = error.message;
    });
  });

  els.closeEditButton.addEventListener("click", closeEditModal);
  els.cancelEditButton.addEventListener("click", closeEditModal);
  els.editOverlay.addEventListener("click", (event) => {
    if (event.target === els.editOverlay) {
      closeEditModal();
    }
  });
  els.closeAddCardButton.addEventListener("click", closeAddCardModal);
  els.cancelAddCardButton.addEventListener("click", closeAddCardModal);
  els.addCardOverlay.addEventListener("click", (event) => {
    if (event.target === els.addCardOverlay) {
      closeAddCardModal();
    }
  });
  els.closeSettingsButton.addEventListener("click", closeSettingsModal);
  els.cancelSettingsButton.addEventListener("click", closeSettingsModal);
  els.settingsOverlay.addEventListener("click", (event) => {
    if (event.target === els.settingsOverlay) {
      closeSettingsModal();
    }
  });
  els.closeNotificationDetailButton?.addEventListener("click", closeNotificationDetailModal);
  els.closeNotificationDetailFooterButton?.addEventListener("click", closeNotificationDetailModal);
  els.notificationDetailOverlay?.addEventListener("click", (event) => {
    if (event.target === els.notificationDetailOverlay) {
      closeNotificationDetailModal();
    }
  });
  els.closeAuthButton.addEventListener("click", closeAuthModal);
  els.toggleAuthModeButton.addEventListener("click", () => {
    const createMode = state.appConfig?.email_configured === false ? "register-direct" : "register";
    setAuthMode(authMode() === "login" ? createMode : "login");
    els.authStatus.textContent = "";
  });
  els.forgotPasswordButton.addEventListener("click", () => {
    setAuthMode("reset-request");
    els.authStatus.textContent = "";
    els.authStatus.dataset.tone = "";
    els.authForm.email.focus();
  });
  els.togglePasswordVisibilityButton.addEventListener("click", () => {
    const showing = els.authForm.password.type === "text";
    els.authForm.password.type = showing ? "password" : "text";
    els.togglePasswordVisibilityButton.textContent = showing ? "Show" : "Hide";
  });
  els.authOverlay.addEventListener("click", (event) => {
    if (event.target === els.authOverlay) {
      closeAuthModal();
    }
  });
  els.authForm.addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuthForm().catch((error) => {
      els.authStatus.textContent = error.message;
      els.authStatus.dataset.tone = "error";
    });
  });
  els.closeAddDeckButton.addEventListener("click", closeAddDeckModal);
  els.cancelAddDeckButton.addEventListener("click", closeAddDeckModal);
  els.addDeckOverlay.addEventListener("click", (event) => {
    if (event.target === els.addDeckOverlay) {
      closeAddDeckModal();
    }
  });
  els.closeImportDeckButton.addEventListener("click", closeImportDeckModal);
  els.cancelImportDeckButton.addEventListener("click", closeImportDeckModal);
  els.closeExportDecksButton.addEventListener("click", closeExportDecksModal);
  els.cancelExportDecksButton.addEventListener("click", closeExportDecksModal);
  els.downloadDecksJsonButton.addEventListener("click", () => downloadDecks("json"));
  els.downloadDecksCsvButton.addEventListener("click", () => downloadDecks("csv"));
  els.exportDecksOverlay.addEventListener("click", (event) => {
    if (event.target === els.exportDecksOverlay) {
      closeExportDecksModal();
    }
  });
  els.importDeckOverlay.addEventListener("click", (event) => {
    if (event.target === els.importDeckOverlay) {
      closeImportDeckModal();
    }
  });
  els.importDeckFileInput.addEventListener("change", async () => {
    const file = els.importDeckFileInput.files?.[0];
    if (!file) return;
    const text = await file.text();
    els.importDeckJsonText.value = text;
    const extension = file.name.toLowerCase().split(".").pop();
    if (extension === "csv" || file.type.includes("csv")) {
      els.importDeckForm.deck_import_format.value = "csv";
    } else {
      els.importDeckForm.deck_import_format.value = "json";
    }
    state.pendingDeckImport = null;
    renderDeckImportPreview([]);
    els.commitImportDeckButton.disabled = true;
    setStatus("File loaded. Review it before importing.", "", els.importDeckStatus);
  });
  els.importDeckJsonText.addEventListener("input", () => {
    state.pendingDeckImport = null;
    renderDeckImportPreview([]);
    els.commitImportDeckButton.disabled = true;
    setStatus("", "", els.importDeckStatus);
  });
  els.importDeckPreview.addEventListener("change", (event) => {
    if (event.target.matches("[data-import-name]")) {
      refreshDeckImportReviewState();
    }
  });
  els.reviewImportDeckButton.addEventListener("click", () => {
    previewDeckImport().catch((error) => setStatus(error.message, "error", els.importDeckStatus));
  });
  els.importDeckForm.addEventListener("submit", (event) => {
    event.preventDefault();
    commitDeckImport().catch((error) => setStatus(error.message, "error", els.importDeckStatus));
  });
  els.closeAddWishlistButton.addEventListener("click", closeAddWishlistModal);
  els.cancelAddWishlistButton.addEventListener("click", closeAddWishlistModal);
  els.addWishlistOverlay.addEventListener("click", (event) => {
    if (event.target === els.addWishlistOverlay) {
      closeAddWishlistModal();
    }
  });
  els.closeAssignWishlistButton.addEventListener("click", closeAssignWishlistModal);
  els.cancelAssignWishlistButton.addEventListener("click", closeAssignWishlistModal);
  els.assignWishlistOverlay.addEventListener("click", (event) => {
    if (event.target === els.assignWishlistOverlay) {
      closeAssignWishlistModal();
    }
  });
  els.closeWishlistDetailButton.addEventListener("click", closeWishlistDetailModal);
  els.closeWishlistDetailFooterButton.addEventListener("click", closeWishlistDetailModal);
  els.deleteWishlistButton.addEventListener("click", () => {
    deleteActiveWishlist().catch((error) => {
      els.wishlistStatus.textContent = error.message;
    });
  });
  els.wishlistDetailOverlay.addEventListener("click", (event) => {
    if (event.target === els.wishlistDetailOverlay) {
      closeWishlistDetailModal();
    }
  });
  els.closeEmailWishlistButton.addEventListener("click", closeEmailWishlistModal);
  els.cancelEmailWishlistButton.addEventListener("click", closeEmailWishlistModal);
  els.emailWishlistOverlay.addEventListener("click", (event) => {
    if (event.target === els.emailWishlistOverlay) {
      closeEmailWishlistModal();
    }
  });
  els.closeAssignDeckButton.addEventListener("click", closeAssignDeckModal);
  els.cancelAssignDeckButton.addEventListener("click", closeAssignDeckModal);
  els.assignCreateDeckButton.addEventListener("click", openAddDeckModal);
  els.assignDeckForm.deck_id.addEventListener("change", () => {
    refreshAssignDeckCardsForSelectedDeck().catch((error) => {
      setStatus(error.message, "error", activeStatusTarget());
    });
  });
  els.assignDeckOverlay.addEventListener("click", (event) => {
    if (event.target === els.assignDeckOverlay) {
      closeAssignDeckModal();
    }
  });
  els.closeDeckDetailButton.addEventListener("click", closeDeckDetailModal);
  els.closeDeckCardPreviewButton.addEventListener("click", closeDeckCardPreviewModal);
  els.deckCardPreviewOverlay.addEventListener("click", (event) => {
    if (event.target === els.deckCardPreviewOverlay) {
      closeDeckCardPreviewModal();
    }
  });
  els.closeScryfallJsonButton.addEventListener("click", closeScryfallJsonModal);
  els.dismissScryfallJsonButton.addEventListener("click", closeScryfallJsonModal);
  els.scryfallJsonOverlay.addEventListener("click", (event) => {
    if (event.target === els.scryfallJsonOverlay) {
      closeScryfallJsonModal();
    }
  });
  els.addDeckCardButton.addEventListener("click", openDeckCardSearchModal);
  els.emailDeckButton.addEventListener("click", () => {
    if (state.activeDeck) {
      openEmailDeckModal(state.activeDeck);
    }
  });
  els.shareDeckButton.addEventListener("click", () => {
    if (state.activeDeck) {
      openDeckShareModal(state.activeDeck);
    }
  });
  els.deleteDeckButton.addEventListener("click", () => {
    deleteActiveDeck().catch((error) => {
      els.decksStatus.textContent = error.message;
    });
  });
  els.deckDetailOverlay.addEventListener("click", (event) => {
    if (event.target === els.deckDetailOverlay) {
      closeDeckDetailModal();
    }
  });
  els.deckCardSearchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    searchCardsForDeck().catch((error) => {
      els.deckCardSearchStatus.textContent = error.message;
    });
  });
  els.closeDeckCardSearchButton.addEventListener("click", () => {
    closeDeckCardSearchModal({ keepDeckOpen: true });
  });
  els.deckCardSearchOverlay.addEventListener("click", (event) => {
    if (event.target === els.deckCardSearchOverlay) {
      closeDeckCardSearchModal({ keepDeckOpen: true });
    }
  });
  els.closeCardDecksButton.addEventListener("click", closeCardDecksModal);
  els.cardDecksOverlay.addEventListener("click", (event) => {
    if (event.target === els.cardDecksOverlay) {
      closeCardDecksModal();
    }
  });
  els.closeAddContainerButton.addEventListener("click", closeAddContainerModal);
  els.cancelAddContainerButton.addEventListener("click", closeAddContainerModal);
  els.addContainerOverlay.addEventListener("click", (event) => {
    if (event.target === els.addContainerOverlay) {
      closeAddContainerModal();
    }
  });
  els.closeAssignContainerButton.addEventListener("click", closeAssignContainerModal);
  els.cancelAssignContainerButton.addEventListener("click", closeAssignContainerModal);
  els.assignCreateContainerButton.addEventListener("click", openAddContainerModal);
  els.assignContainerOverlay.addEventListener("click", (event) => {
    if (event.target === els.assignContainerOverlay) {
      closeAssignContainerModal();
    }
  });
  els.closeSaleButton.addEventListener("click", closeSaleModal);
  els.cancelSaleButton.addEventListener("click", closeSaleModal);
  els.saleOverlay.addEventListener("click", (event) => {
    if (event.target === els.saleOverlay) {
      closeSaleModal();
    }
  });
  els.closeSoldButton.addEventListener("click", closeSoldModal);
  els.cancelSoldButton.addEventListener("click", closeSoldModal);
  els.soldOverlay.addEventListener("click", (event) => {
    if (event.target === els.soldOverlay) {
      closeSoldModal();
    }
  });
  els.closeStoreFrontDetailButton.addEventListener("click", closeStoreFrontCardDetail);
  els.storeFrontDetailOverlay.addEventListener("click", (event) => {
    if (event.target === els.storeFrontDetailOverlay) {
      closeStoreFrontCardDetail();
    }
  });
  els.soldForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.soldForm).entries());
    payload.quantity = Number(payload.quantity || 0);
    payload.sold_price_each = Number(payload.sold_price_each || 0);
    const maxQuantity = Number(els.soldForm.quantity.max || 0);
    if (payload.quantity < 1 || payload.quantity > maxQuantity) {
      setStatus(`Sold quantity must be between 1 and ${integer.format(maxQuantity)}.`, "error", els.saleStatus);
      return;
    }
    if (!payload.sold_date) {
      setStatus("Choose the date sold.", "error", els.saleStatus);
      return;
    }
    if (payload.sold_price_each <= 0) {
      setStatus("Sold price must be greater than $0.00.", "error", els.saleStatus);
      return;
    }
    try {
      const result = await api("/api/cards/sold", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const sold = result.sold || {};
      setStatus(`Marked ${integer.format(sold.quantity || payload.quantity)} card${Number(sold.quantity || payload.quantity) === 1 ? "" : "s"} sold.`, "success", els.saleStatus);
      closeSoldModal();
      await loadSaleCards();
      await loadCards();
      if (!Array.from(els.pages).find((page) => page.dataset.page === "dashboard")?.hidden) {
        await refresh();
      }
    } catch (error) {
      setStatus(error.message, "error", els.saleStatus);
    }
  });
  els.closeContainerDetailButton.addEventListener("click", closeContainerDetailModal);
  els.editContainerButton.addEventListener("click", () => {
    if (state.activeContainer) {
      openEditContainerModal(state.activeContainer);
    }
  });
  els.emailContainerButton.addEventListener("click", () => {
    if (state.activeContainer) {
      openEmailContainerModal(state.activeContainer);
    }
  });
  els.shareContainerButton.addEventListener("click", () => {
    if (state.activeContainer) {
      openContainerShareModal(state.activeContainer);
    }
  });
  els.deleteContainerButton.addEventListener("click", () => {
    deleteActiveContainer().catch((error) => {
      els.containersStatus.textContent = error.message;
    });
  });
  els.containerDetailOverlay.addEventListener("click", (event) => {
    if (event.target === els.containerDetailOverlay) {
      closeContainerDetailModal();
    }
  });
  els.closeCardContainersButton.addEventListener("click", closeCardContainersModal);
  els.cardContainersOverlay.addEventListener("click", (event) => {
    if (event.target === els.cardContainersOverlay) {
      closeCardContainersModal();
    }
  });
  els.closeCardMetaButton.addEventListener("click", closeCardMetaModal);
  els.cardMetaOverlay.addEventListener("click", (event) => {
    if (event.target === els.cardMetaOverlay) {
      closeCardMetaModal();
    }
  });
  els.closeCardLedgerButton?.addEventListener("click", closeCardLedgerModal);
  els.cardLedgerOverlay?.addEventListener("click", (event) => {
    if (event.target === els.cardLedgerOverlay) {
      closeCardLedgerModal();
    }
  });
  els.closeShareButton.addEventListener("click", closeShareModal);
  els.copyShareButton.addEventListener("click", copyShareUrl);
  els.shareOverlay.addEventListener("click", (event) => {
    if (event.target === els.shareOverlay) {
      closeShareModal();
    }
  });
  els.closeCardBlogButton?.addEventListener("click", closeCardBlogModal);
  els.cancelCardBlogButton?.addEventListener("click", closeCardBlogModal);
  els.cardBlogOverlay?.addEventListener("click", (event) => {
    if (event.target === els.cardBlogOverlay) {
      closeCardBlogModal();
    }
  });
  els.cardBlogForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const card = state.activeBlogCard;
    const deck = state.activeBlogDeck;
    if ((!card && !deck) || !state.user?.profile_slug) return;
    try {
      const payload = Object.fromEntries(new FormData(els.cardBlogForm).entries());
      if (card) {
        payload.card_id = card.scryfall_id || card.card_id;
        payload.variant = card.variant || "Normal";
      }
      if (deck) {
        payload.deck_id = deck.id;
      }
      const result = await api(`/api/users/profile/${encodeURIComponent(state.user.profile_slug)}/posts`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      closeCardBlogModal();
      setStatus(`Blog post saved for ${card ? cardTitle(card) : deck.name || "deck"}.`, "success");
      if (state.userProfile?.profile_slug === state.user.profile_slug && result.profile) {
        renderUserProfile(result.profile);
      }
    } catch (error) {
      setStatus(error.message, "error", els.cardBlogStatus);
    }
  });
  els.closeCardBlogListButton?.addEventListener("click", closeCardBlogListModal);
  els.dismissCardBlogListButton?.addEventListener("click", closeCardBlogListModal);
  els.cardBlogListOverlay?.addEventListener("click", (event) => {
    if (event.target === els.cardBlogListOverlay) {
      closeCardBlogListModal();
    }
  });
  els.closeReportButton?.addEventListener("click", closeReportModal);
  els.cancelReportButton?.addEventListener("click", closeReportModal);
  els.reportOverlay?.addEventListener("click", (event) => {
    if (event.target === els.reportOverlay) {
      closeReportModal();
    }
  });
  els.reportForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    submitContentReport(event.currentTarget).catch((error) => setStatus(error.message, "error", els.reportStatus));
  });
  els.writeCardBlogFromListButton?.addEventListener("click", () => {
    const card = state.activeBlogListCard;
    closeCardBlogListModal();
    if (card) openCardBlogModal(card);
  });
  els.closeDeckJsonButton.addEventListener("click", closeDeckJsonModal);
  els.dismissDeckJsonButton.addEventListener("click", closeDeckJsonModal);
  els.copyDeckJsonButton.addEventListener("click", copyDeckJson);
  els.deckJsonOverlay.addEventListener("click", (event) => {
    if (event.target === els.deckJsonOverlay) {
      closeDeckJsonModal();
    }
  });
  els.closeImportReviewButton.addEventListener("click", closeImportReviewModal);
  els.cancelImportReviewButton.addEventListener("click", closeImportReviewModal);
  els.importReviewOverlay.addEventListener("click", (event) => {
    if (event.target === els.importReviewOverlay) {
      closeImportReviewModal();
    }
  });
  els.commitImportButton.addEventListener("click", () => {
    commitImportReview().catch((error) => {
      els.importStatus.textContent = error.message;
      els.commitImportButton.disabled = false;
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !els.editOverlay.hidden) {
      closeEditModal();
    }
    if (event.key === "Escape" && !els.addCardOverlay.hidden) {
      closeAddCardModal();
    }
    if (event.key === "Escape" && !els.addPurchaseOverlay.hidden) {
      closeAddPurchaseModal();
    }
    if (event.key === "Escape" && !els.inventoryAdjustOverlay.hidden) {
      closeInventoryAdjustModal();
    }
    if (event.key === "Escape" && !els.directSaleOverlay.hidden) {
      closeDirectSaleModal();
    }
    if (event.key === "Escape" && !els.settingsOverlay.hidden) {
      closeSettingsModal();
    }
    if (event.key === "Escape" && els.profileOverlay && !els.profileOverlay.hidden) {
      closeProfileModal();
    }
    if (event.key === "Escape" && els.notificationDetailOverlay && !els.notificationDetailOverlay.hidden) {
      closeNotificationDetailModal();
    }
    if (event.key === "Escape" && els.changelogOverlay && !els.changelogOverlay.hidden) {
      closeChangelogModal();
    }
    if (event.key === "Escape" && els.membershipBenefitsOverlay && !els.membershipBenefitsOverlay.hidden) {
      closeMembershipBenefitsModal();
    }
    if (event.key === "Escape" && !els.authOverlay.hidden) {
      closeAuthModal();
    }
    if (event.key === "Escape" && !els.shareOverlay.hidden) {
      closeShareModal();
    }
    if (event.key === "Escape" && els.cardBlogOverlay && !els.cardBlogOverlay.hidden) {
      closeCardBlogModal();
    }
    if (event.key === "Escape" && els.cardBlogListOverlay && !els.cardBlogListOverlay.hidden) {
      closeCardBlogListModal();
    }
    if (event.key === "Escape" && !els.deckJsonOverlay.hidden) {
      closeDeckJsonModal();
    }
    if (event.key === "Escape" && !els.exportDecksOverlay.hidden) {
      closeExportDecksModal();
    }
    if (event.key === "Escape" && !els.importDeckOverlay.hidden) {
      closeImportDeckModal();
    }
    if (event.key === "Escape" && !els.addDeckOverlay.hidden) {
      closeAddDeckModal();
    }
    if (event.key === "Escape" && !els.addWishlistOverlay.hidden) {
      closeAddWishlistModal();
    }
    if (event.key === "Escape" && !els.assignWishlistOverlay.hidden) {
      closeAssignWishlistModal();
    }
    if (event.key === "Escape" && !els.wishlistDetailOverlay.hidden) {
      closeWishlistDetailModal();
    }
    if (event.key === "Escape" && !els.emailWishlistOverlay.hidden) {
      closeEmailWishlistModal();
    }
    if (event.key === "Escape" && !els.assignDeckOverlay.hidden) {
      closeAssignDeckModal();
    }
    if (event.key === "Escape" && !els.deckCardSearchOverlay.hidden) {
      closeDeckCardSearchModal({ keepDeckOpen: true });
      return;
    }
    if (event.key === "Escape" && !els.scryfallJsonOverlay.hidden) {
      closeScryfallJsonModal();
      return;
    }
    if (event.key === "Escape" && !els.deckCardPreviewOverlay.hidden) {
      closeDeckCardPreviewModal();
      return;
    }
    if (event.key === "Escape" && !els.deckDetailOverlay.hidden) {
      closeDeckDetailModal();
    }
    if (event.key === "Escape" && !els.cardDecksOverlay.hidden) {
      closeCardDecksModal();
    }
    if (event.key === "Escape" && !els.addContainerOverlay.hidden) {
      closeAddContainerModal();
    }
    if (event.key === "Escape" && !els.assignContainerOverlay.hidden) {
      closeAssignContainerModal();
    }
    if (event.key === "Escape" && !els.saleOverlay.hidden) {
      closeSaleModal();
    }
    if (event.key === "Escape" && !els.soldOverlay.hidden) {
      closeSoldModal();
    }
    if (event.key === "Escape" && !els.containerDetailOverlay.hidden) {
      closeContainerDetailModal();
    }
    if (event.key === "Escape" && !els.cardContainersOverlay.hidden) {
      closeCardContainersModal();
    }
    if (event.key === "Escape" && !els.cardMetaOverlay.hidden) {
      closeCardMetaModal();
    }
    if (event.key === "Escape" && els.cardLedgerOverlay && !els.cardLedgerOverlay.hidden) {
      closeCardLedgerModal();
    }
    if (event.key === "Escape" && !els.importReviewOverlay.hidden) {
      closeImportReviewModal();
    }
  });
  els.addSearchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    els.addSearchStatus.dataset.tone = "";
    searchScryfallForAdd();
  });
  els.addAdvancedToggle?.addEventListener("click", () => {
    const isHidden = Boolean(els.addAdvancedFilters?.hidden);
    if (els.addAdvancedFilters) els.addAdvancedFilters.hidden = !isHidden;
    els.addAdvancedToggle.setAttribute("aria-expanded", String(isHidden));
    els.addAdvancedToggle.textContent = isHidden ? "Hide advanced filters" : "Show advanced filters";
  });
  els.addSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      els.addSearchStatus.dataset.tone = "";
      searchScryfallForAdd();
    }
  });
  els.addPurchaseRows?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-add-row-copy]");
    if (!button) return;
    duplicateAddPurchaseRow(button.closest(".add-purchase-row"));
  });
  els.addCardForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.selectedAddCard) {
      els.addSearchStatus.textContent = "Choose a card first.";
      return;
    }
    const purchases = addPurchasePayloadRows();
    if (!purchases.length) {
      els.addSearchStatus.textContent = "No quantity detected.";
      els.addSearchStatus.dataset.tone = "error";
      els.addPurchaseRows?.querySelector('[data-add-field="quantity"]')?.focus();
      return;
    }
    for (const purchase of purchases) {
      if (purchase.quantity < 1) {
        els.addSearchStatus.textContent = "Quantity must be at least 1.";
        els.addSearchStatus.dataset.tone = "error";
        return;
      }
      if (!purchase.acquired_date) {
        els.addSearchStatus.textContent = "Choose a date acquired for every row with quantity.";
        els.addSearchStatus.dataset.tone = "error";
        return;
      }
      if (purchase.paid_price <= 0) {
        els.addSearchStatus.textContent = "Price paid per card must be greater than $0.00.";
        els.addSearchStatus.dataset.tone = "error";
        return;
      }
    }
    const formValues = Object.fromEntries(new FormData(els.addCardForm).entries());
    const payload = {
      scryfall_id: formValues.scryfall_id,
      store_name: formValues.store_name || "",
      store_location: formValues.store_location || "",
      notes: formValues.notes || "",
      purchases,
    };
    payload.expected_name = state.selectedAddCard.name || "";
    payload.expected_set_code = state.selectedAddCard.set_code || "";
    payload.expected_collector_number = state.selectedAddCard.collector_number || "";
    payload.expected_image_normal = state.selectedAddCard.image_normal || "";
    const addAndNew = event.submitter === els.confirmAddNewCardButton;
    const addedCardTitle = cardTitle(state.selectedAddCard);
    els.confirmAddCardButton.disabled = true;
    els.confirmAddNewCardButton.disabled = true;
    try {
      const result = await api("/api/cards", {
        method: "POST",
        body: JSON.stringify(payload),
        promptLogin: true,
      });
      const quantity = Number(result.quantity_added || 0);
      const variantLabel = (result.variants || []).join(", ") || result.variant || "selected variants";
      setStatus(`Added ${integer.format(quantity)} ${addedCardTitle} card${quantity === 1 ? "" : "s"} (${variantLabel}).`);
      if (addAndNew) {
        resetAddCardModalForNew();
      } else {
        closeAddCardModal();
      }
      await refresh();
      const searchVisible = Array.from(els.pages).some((page) => page.dataset.page === "search" && !page.hidden);
      if (searchVisible && state.catalogSearchResults.length) {
        await searchCatalog();
      }
      const detailVisible = Array.from(els.pages).some((page) => page.dataset.page === "card-detail" && !page.hidden);
      if (detailVisible) {
        await loadCardDetail(payload.scryfall_id, purchases[0]?.variant || "Normal");
      }
    } catch (error) {
      els.addSearchStatus.textContent = error.message;
      els.addSearchStatus.dataset.tone = "error";
      els.confirmAddCardButton.disabled = false;
      els.confirmAddNewCardButton.disabled = false;
    }
  });
  els.settingsForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.settingsForm).entries());
    saveSettings({ ...(state.settings || defaultSettings()), ...payload });
    setStatus("Settings saved.");
    closeSettingsModal();
  });
  els.editProfileButton?.addEventListener("click", openProfileModal);
  els.closeProfileButton?.addEventListener("click", closeProfileModal);
  els.cancelProfileButton?.addEventListener("click", closeProfileModal);
  els.profileOverlay?.addEventListener("click", (event) => {
    if (event.target === els.profileOverlay) {
      closeProfileModal();
    }
  });
  els.profileImageInput?.addEventListener("change", async () => {
    try {
      const dataUrl = await readProfileImageFile(els.profileImageInput.files?.[0]);
      els.profileForm.profile_image.value = dataUrl;
      renderProfileImagePreview(dataUrl);
      setStatus("", "", els.profileStatus);
    } catch (error) {
      els.profileImageInput.value = "";
      setStatus(error.message, "error", els.profileStatus);
    }
  });
  els.profileForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await saveUserSettings(profilePayloadFromForm());
      renderSettingsPage();
      setStatus("Profile saved.", "success", els.settingsPageStatus);
      closeProfileModal();
    } catch (error) {
      setStatus(error.message, "error", els.profileStatus);
    }
  });
  els.settingsPageForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = userSettingsPayload(Object.fromEntries(new FormData(els.settingsPageForm).entries()));
    try {
      await saveUserSettings(payload);
      setStatus("Settings saved.", "success", els.settingsPageStatus);
    } catch (error) {
      setStatus(error.message, "error", els.settingsPageStatus);
    }
  });
  els.clearDatabaseButton.addEventListener("click", async () => {
    const confirmed = window.confirm("Clear your Arcane Ledger database? This removes your collection, decks, containers, lists, sale listings, and card history, but keeps your account.");
    if (!confirmed) return;
    try {
      await api("/api/user/clear-data", { method: "POST", body: JSON.stringify({}) });
      setStatus("Your database has been cleared.", "success", els.settingsPageStatus);
      state.cards = [];
      state.favoriteCards = [];
      state.missingCards = [];
      state.saleCards = [];
      state.wishlistCards = [];
      state.wishlists = [];
      state.activeWishlist = null;
      await refresh();
    } catch (error) {
      setStatus(error.message, "error", els.settingsPageStatus);
    }
  });
  els.deleteProfileButton.addEventListener("click", async () => {
    const confirmed = window.confirm("Delete your Arcane Ledger profile and all of your data? This cannot be undone.");
    if (!confirmed) return;
    const typed = window.prompt('Type "delete" to confirm profile deletion.');
    if ((typed || "").toLowerCase() !== "delete") return;
    try {
      await api("/api/user/profile", { method: "DELETE", body: JSON.stringify({}) });
      state.user = null;
      updateAuthUi();
      setStatus("Profile deleted.", "success");
      activatePage("home", { push: true });
    } catch (error) {
      setStatus(error.message, "error", els.settingsPageStatus);
    }
  });
  els.addDeckForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.addDeckForm).entries());
    try {
      const result = await api("/api/decks", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      els.decksStatus.textContent = `Added ${result.deck.name}.`;
      const returnToAssignDeck = Boolean(state.returnToAssignDeck);
      closeAddDeckModal();
      const decks = await loadDecks();
      if (returnToAssignDeck && !els.assignDeckOverlay.hidden) {
        populateAssignDeckSelect(decks);
        els.assignDeckForm.deck_id.value = String(result.deck.id);
        await refreshAssignDeckCardsForSelectedDeck();
        els.assignDeckForm.deck_id.focus();
      }
    } catch (error) {
      els.decksStatus.textContent = error.message;
    }
  });
  els.addWishlistForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.addWishlistForm).entries());
    try {
      const result = await api("/api/wishlists", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      els.wishlistStatus.textContent = `Added ${result.wishlist.name}.`;
      closeAddWishlistModal();
      await loadWishlists();
    } catch (error) {
      els.wishlistStatus.textContent = error.message;
    }
  });
  els.assignWishlistForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const wishlistId = els.assignWishlistForm.wishlist_id.value;
    const card = state.pendingWishlistCard;
    const options = state.pendingWishlistOptions || {};
    if (!wishlistId) {
      setStatus("Create a wishlist first.", "error", options.statusTarget || els.wishlistStatus);
      return;
    }
    if (!card) {
      setStatus("Choose a card first.", "error", options.statusTarget || els.wishlistStatus);
      return;
    }
    try {
      await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/wishlist`, {
        method: "POST",
        body: JSON.stringify({
          variant: card.variant || "Normal",
          wishlist_id: wishlistId,
          wishlist: true,
          card,
        }),
        promptLogin: true,
      });
      card.wishlist = 1;
      setStatus(`Added ${cardTitle(card)} to Wishlist.`, "success", options.statusTarget || els.wishlistStatus);
      closeAssignWishlistModal();
      if (options.afterWishlistChange) {
        await options.afterWishlistChange();
      } else {
        await loadWishlists();
        await refresh();
      }
    } catch (error) {
      setStatus(error.message, "error", options.statusTarget || els.wishlistStatus);
    }
  });
  els.emailWishlistForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.emailWishlistForm).entries());
    const type = payload.entity_type || state.emailingEntity?.type || "wishlist";
    const entityId = payload.entity_id || state.emailingEntity?.entity?.id || state.emailingWishlist?.id;
    const endpoints = {
      card: "cards",
      deck: "decks",
      "shared-deck": "shared-decks",
      container: "containers",
      wishlist: "wishlists",
      set: "sets",
      favorites: "favorites",
    };
    const endpoint = endpoints[type];
    const label = emailEntityLabel(type);
    if (!endpoint || !entityId) {
      els.emailWishlistStatus.textContent = `Choose a ${label.toLowerCase()} first.`;
      els.emailWishlistStatus.dataset.tone = "error";
      return;
    }
    const submitButton = els.emailWishlistForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    els.emailWishlistStatus.textContent = `Sending ${label.toLowerCase()}...`;
    els.emailWishlistStatus.dataset.tone = "";
    try {
      await api(`/api/${endpoint}/${encodeURIComponent(entityId)}/email`, {
        method: "POST",
        body: JSON.stringify({
          email: payload.email,
          variant: state.emailingEntity?.entity?.variant || "Normal",
          share_id: state.emailingEntity?.entity?.share_id || "",
        }),
      });
      const recipient = payload.email;
      closeEmailWishlistModal();
      const statusTarget = type === "deck" ? els.decksStatus : type === "shared-deck" ? els.browseDecksStatus : type === "container" ? els.containersStatus : type === "wishlist" ? els.wishlistStatus : type === "set" ? els.setsStatus : type === "favorites" ? els.favoritesStatus : els.status;
      setStatus(`${label} emailed to ${recipient}.`, "success", statusTarget);
    } catch (error) {
      els.emailWishlistStatus.textContent = error.message;
      els.emailWishlistStatus.dataset.tone = "error";
    } finally {
      submitButton.disabled = false;
    }
  });
  els.addContainerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.addContainerForm).entries());
    const containerId = payload.id;
    delete payload.id;
    try {
      const result = await api(containerId ? `/api/containers/${encodeURIComponent(containerId)}` : "/api/containers", {
        method: containerId ? "PUT" : "POST",
        body: JSON.stringify(payload),
      });
      els.containersStatus.textContent = `${containerId ? "Updated" : "Added"} ${result.container.name}.`;
      const returnToAssignContainer = Boolean(state.returnToAssignContainer);
      closeAddContainerModal();
      const containers = await loadContainers();
      if (returnToAssignContainer && !els.assignContainerOverlay.hidden) {
        populateAssignContainerSelect(containers);
        renderAssignContainerCards(containers);
        if (state.assignContainerCard) {
          const newRowInput = els.assignContainerCards.querySelector(`[data-container-id="${CSS.escape(String(result.container.id))}"] input`);
          newRowInput?.focus();
        } else {
          els.assignContainerForm.container_id.value = String(result.container.id);
          els.assignContainerForm.container_id.focus();
        }
      }
      if (state.activeContainer && Number(state.activeContainer.id) === Number(result.container.id)) {
        renderContainerDetail(result.container);
      }
      await reloadVisibleCardPages();
    } catch (error) {
      els.containersStatus.textContent = error.message;
    }
  });
  els.assignDeckForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const deckId = els.assignDeckForm.deck_id.value;
    const statusTarget = activeStatusTarget();
    if (!deckId) {
      setStatus("Create a deck first.", "error", statusTarget);
      return;
    }
    const cards = Array.from(els.assignDeckCards.querySelectorAll(".assign-deck-card")).map((row) => {
      const input = row.querySelector("input");
      return {
        card_id: row.dataset.cardId,
        variant: row.dataset.variant || "Normal",
        quantity: Number(input.value || 0),
      };
    }).filter((card) => card.card_id && card.quantity > 0);
    if (!cards.length) {
      setStatus("Choose at least one available card quantity.", "error", statusTarget);
      return;
    }
    try {
      const result = await api(`/api/decks/${encodeURIComponent(deckId)}/cards`, {
        method: "POST",
        body: JSON.stringify({ cards }),
      });
      setStatus(`Added ${integer.format(result.added || 0)} card${result.added === 1 ? "" : "s"} to deck.`, "", statusTarget);
      closeAssignDeckModal();
      clearSelectedCards();
      await loadDecks();
      await reloadVisibleCardPages();
    } catch (error) {
      setStatus(error.message, "error", statusTarget);
    }
  });
  els.assignContainerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const containerId = els.assignContainerForm.container_id.value;
    const statusTarget = activeStatusTarget();
    if (state.assignContainerCard) {
      const card = state.assignContainerCard;
      const ownedByBucket = new Map();
      for (const bucket of containerAllocationBuckets(card)) {
        ownedByBucket.set(`${bucket.variant}||${bucket.card_condition}`, Number(bucket.quantity || 0));
      }
      const allocations = Array.from(els.assignContainerCards.querySelectorAll(".container-allocation-row")).map((row) => ({
        container_id: Number(row.dataset.containerId || 0),
        variant: row.dataset.variant || "Normal",
        card_condition: row.dataset.condition || "Near Mint",
        quantity: Number(row.querySelector('input[type="number"]')?.value || 0),
        max: Number(row.querySelector('input[type="number"]')?.max || 0),
      })).filter((allocation) => allocation.container_id);
      if (!allocations.length) {
        setStatus("Create a container first.", "error", statusTarget);
        return;
      }
      const overCapacity = allocations.find((allocation) => allocation.quantity > allocation.max);
      if (overCapacity) {
        setStatus("One of those containers does not have enough space.", "error", statusTarget);
        return;
      }
      const totalsByBucket = new Map();
      for (const allocation of allocations) {
        const key = `${allocation.variant}||${allocation.card_condition}`;
        totalsByBucket.set(key, (totalsByBucket.get(key) || 0) + Math.max(0, Number(allocation.quantity || 0)));
      }
      for (const [key, total] of totalsByBucket.entries()) {
        const owned = ownedByBucket.get(key) || 0;
        if (total > owned) {
          const [variant, condition] = key.split("||");
          setStatus(`Only ${integer.format(owned)} ${variant} / ${condition} copy/copies are owned.`, "error", statusTarget);
          return;
        }
      }
      try {
        const result = await api(`/api/cards/${encodeURIComponent(card.scryfall_id || card.card_id)}/containers`, {
          method: "POST",
          body: JSON.stringify({
            allocations,
          }),
        });
        setStatus(`Stored ${integer.format(result.stored || 0)} card${Number(result.stored || 0) === 1 ? "" : "s"} across containers.`, "success", statusTarget);
        closeAssignContainerModal();
        clearSelectedCards();
        await loadContainers();
        await reloadVisibleCardPages();
      } catch (error) {
        setStatus(error.message, "error", statusTarget);
      }
      return;
    }
    if (!containerId) {
      setStatus("Create a container first.", "error", statusTarget);
      return;
    }
    if (els.assignContainerForm.container_id.selectedOptions[0]?.disabled) {
      setStatus("That container has no more space.", "error", statusTarget);
      return;
    }
    const cardsByKey = new Map(Array.from(state.selectedCards.values()).map((card) => [`${card.card_id}::${card.variant}`, card]));
    const cards = Array.from(els.assignContainerCards.querySelectorAll(".assign-container-row")).map((row) => {
      const card = cardsByKey.get(row.dataset.cardKey);
      const input = row.querySelector('input[type="number"]');
      if (!card || !input) return null;
      return {
        card_id: card.card_id,
        variant: card.variant,
        quantity: Number(input.value || 0),
      };
    }).filter((card) => card && card.quantity > 0);
    if (!cards.length) {
      setStatus("No unassigned copies are available for those cards.", "error", statusTarget);
      return;
    }
    try {
      const result = await api(`/api/containers/${encodeURIComponent(containerId)}/cards`, {
        method: "POST",
        body: JSON.stringify({ cards }),
      });
      setStatus(`Stored ${integer.format(result.added || 0)} card${result.added === 1 ? "" : "s"} in container.`, "", statusTarget);
      closeAssignContainerModal();
      clearSelectedCards();
      await loadContainers();
      await reloadVisibleCardPages();
    } catch (error) {
      setStatus(error.message, "error", statusTarget);
    }
  });
  els.saleForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const rows = Array.from(els.saleCards.querySelectorAll(".sale-modal-row"));
    const cards = [];
    for (const row of rows) {
      const checked = row.querySelector('input[type="checkbox"]')?.checked;
      if (!checked) continue;
      const quantityInput = row.querySelector('input[name="quantity"]');
      const priceInput = row.querySelector('input[name="asking_price"]');
      const quantity = Number(quantityInput?.value || 0);
      const max = Number(quantityInput?.max || 0);
      const askingPrice = Number(priceInput?.value || 0);
      if (quantity < 1 || quantity > max) {
        setStatus(`Sale quantity must be between 1 and ${integer.format(max)}.`, "error", els.saleModalStatus);
        return;
      }
      if (askingPrice <= 0) {
        setStatus("Asking price must be greater than $0.00.", "error", els.saleModalStatus);
        return;
      }
      cards.push({
        card_id: row.dataset.cardId,
        variant: row.dataset.variant || "Normal",
        card_condition: row.dataset.condition || "Near Mint",
        quantity,
        asking_price: askingPrice,
      });
    }
    if (!cards.length) {
      const hasZeroAvailableRows = rows.some((row) => Number(row.querySelector('input[name="quantity"]')?.max || 0) <= 0);
      setStatus(
        hasZeroAvailableRows
          ? "0 copies are available to sell for the selected card."
          : "Keep at least one checked card to mark for sale.",
        "error",
        els.saleModalStatus,
      );
      return;
    }
    try {
      const result = await api("/api/cards/for-sale", {
        method: "POST",
        body: JSON.stringify({ cards, for_sale: true }),
      });
      setStatus(`Marked ${integer.format(result.updated || 0)} card${result.updated === 1 ? "" : "s"} for sale.`, "success");
      closeSaleModal();
      clearSelectedCards();
      await loadNotificationSummary();
      await reloadVisibleCardPages();
    } catch (error) {
      setStatus(error.message, "error", els.saleModalStatus);
    }
  });
  els.editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const cardId = els.editForm.card_id.value;
    const payload = Object.fromEntries(new FormData(els.editForm).entries());
    try {
      await api(`/api/cards/${encodeURIComponent(cardId)}/collection`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setStatus(`Saved ${state.editingCard ? state.editingCard.name : "card"}.`);
      const editedVariant = payload.variant || state.editingCard?.variant || "Normal";
      const isDetailVisible = !document.querySelector('[data-page="card-detail"]')?.hidden;
      closeEditModal();
      await refresh();
      if (isDetailVisible) {
        await loadCardDetail(cardId, editedVariant);
      }
    } catch (error) {
      setStatus(error.message, "error");
    }
  });
  els.addPurchaseForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.addPurchaseForm).entries());
    const cardId = payload.card_id;
    try {
      const result = await api(`/api/cards/${encodeURIComponent(cardId)}/purchases`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      closeAddPurchaseModal();
      renderCardDetail(result.card);
      await refresh();
      setStatus(`Added purchase for ${cardTitle(result.card)}.`);
    } catch (error) {
      setStatus(error.message, "error");
    }
  });
  els.inventoryAdjustForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.inventoryAdjustForm).entries());
    const cardId = payload.card_id;
    const maxQuantity = Number(els.inventoryAdjustForm.quantity.max || 0);
    payload.quantity = Number(payload.quantity || 0);
    if (payload.quantity < 1) {
      setStatus("Adjustment quantity must be at least 1.", "error");
      return;
    }
    if (payload.adjustment_type === "decrease" && maxQuantity && payload.quantity > maxQuantity) {
      setStatus(`Only ${integer.format(maxQuantity)} copy/copies are available to remove.`, "error");
      return;
    }
    try {
      const result = await api(`/api/cards/${encodeURIComponent(cardId)}/inventory`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      closeInventoryAdjustModal();
      renderCardDetail(result.card);
      await refresh();
      setStatus(`Inventory adjusted for ${cardTitle(result.card)}.`);
    } catch (error) {
      setStatus(error.message, "error");
    }
  });
  els.directSaleForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.directSaleForm).entries());
    const cardId = payload.card_id;
    const maxQuantity = Number(els.directSaleForm.quantity.max || 0);
    payload.quantity = Number(payload.quantity || 0);
    payload.sold_price_each = Number(payload.sold_price_each || 0);
    if (payload.quantity < 1 || (maxQuantity && payload.quantity > maxQuantity)) {
      setStatus(`Sold quantity must be between 1 and ${integer.format(maxQuantity || 1)}.`, "error");
      return;
    }
    if (payload.sold_price_each <= 0) {
      setStatus("Sold price must be greater than $0.00.", "error");
      return;
    }
    try {
      const result = await api(`/api/cards/${encodeURIComponent(cardId)}/direct-sale`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      closeDirectSaleModal();
      renderCardDetail(result.card);
      await refresh();
      setStatus(`Added sale for ${cardTitle(result.card)}.`);
    } catch (error) {
      setStatus(error.message, "error");
    }
  });
}

async function boot() {
  await loadAppConfig();
  state.settings = loadSettings();
  applySettings();
  const initialSharedId = sharedRouteId();
  const initialSetCode = setRouteCode();
  const initialSharedSet = sharedSetRoute();
  const initialDeckRouteId = deckRouteId();
  const initialDeckEditorId = isPrivateDeckRoute(initialDeckRouteId) ? initialDeckRouteId : "";
  const initialDeckShareId = initialDeckRouteId && !initialDeckEditorId ? initialDeckRouteId : "";
  const initialWishlistShareId = wishlistRouteId();
  const initialContainerShareId = containerRouteId();
  const initialStoreShareId = storeRouteId();
  const initialUserProfileSlug = userProfileRoute();
  const initialFavoritesShare = favoritesShareRoute();
  const initialCardDetail = cardDetailRoute();
  const initialVerificationToken = verificationRouteToken();
  const initialPasswordResetToken = passwordResetRouteToken();
  const initialAppPage = appPageRoute();
  const initialPath = window.location.pathname.replace(/\/+$/, "") || "/";
  const isRootRoute = initialPath === "/";
  const isAlwaysShareOnlyRoute = Boolean(initialSharedSet || initialDeckShareId || initialWishlistShareId || initialContainerShareId || initialStoreShareId || initialFavoritesShare);
  await loadSession().catch(() => {
    state.user = null;
    updateAuthUi();
  });
  applyNavCollapsedState();
  const isShareOnlyRoute = isAlwaysShareOnlyRoute || Boolean((initialSharedId || initialCardDetail) && !state.user);
  if (!isShareOnlyRoute) {
    wireEvents();
  }
  if (initialSharedId) {
    document.body.classList.toggle("share-only", !state.user);
    loadSharedCard(initialSharedId);
  } else if (initialDeckShareId) {
    document.body.classList.add("share-only");
    loadSharedDeck(initialDeckShareId);
  } else if (initialDeckEditorId) {
    if (state.user) {
      loadDeckEditor(initialDeckEditorId);
      refresh().catch((error) => {
        setStatus(error.message, "error");
        renderCollection();
      });
    } else {
      activatePage("home", { replace: true, promptLogin: false });
      openAuthModal("login", "Log in to edit this deck.");
    }
  } else if (initialWishlistShareId) {
    document.body.classList.add("share-only");
    loadSharedWishlist(initialWishlistShareId);
  } else if (initialContainerShareId) {
    document.body.classList.add("share-only");
    loadSharedContainer(initialContainerShareId);
  } else if (initialStoreShareId) {
    document.body.classList.add("share-only");
    loadSharedStore(initialStoreShareId);
  } else if (initialFavoritesShare) {
    document.body.classList.add("share-only");
    loadSharedFavorites(initialFavoritesShare);
  } else if (initialSharedSet) {
    document.body.classList.add("share-only");
    loadSharedSet(initialSharedSet);
  } else if (initialVerificationToken) {
    loadEmailVerification(initialVerificationToken);
  } else if (initialPasswordResetToken) {
    loadPasswordReset(initialPasswordResetToken);
  } else if (initialUserProfileSlug) {
    loadUserProfile(initialUserProfileSlug);
  } else if (isRootRoute) {
    activatePage(state.user ? "dashboard" : "home", { replace: true, promptLogin: false });
  } else if (initialCardDetail) {
    if (state.user) {
      loadCardDetail(initialCardDetail.cardId, initialCardDetail.variant);
      refresh().catch((error) => {
        setStatus(error.message, "error");
        renderCollection();
      });
    } else {
      document.body.classList.add("share-only");
      loadPublicCardDetail(initialCardDetail.cardId, initialCardDetail.variant);
    }
  } else if (initialSetCode) {
    if (state.user) {
      loadSetPage(initialSetCode);
      refresh().catch((error) => {
        setStatus(error.message, "error");
        renderCollection();
      });
    } else {
      activatePage("home");
      openAuthModal("login", "Log in to view set progress.");
    }
  } else if (initialAppPage) {
    if (!state.user && protectedPage(initialAppPage)) {
      activatePage("home", { replace: true, promptLogin: false });
    } else if (initialAppPage === "admin" && !isAdminUser()) {
      activatePage(state.user ? "dashboard" : "home", { replace: true, promptLogin: false });
    } else {
      activatePage(initialAppPage);
    }
  } else {
    activatePage("home", { replace: true, promptLogin: false });
  }
}

boot().catch((error) => {
  setStatus(error.message, "error");
});
