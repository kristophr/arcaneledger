const state = {
  cards: [],
  favoriteCards: [],
  missingCards: [],
  saleCards: [],
  wishlistCards: [],
  wishlists: [],
  catalogSearchResults: [],
  dashboard: null,
  searchTimer: null,
  favoriteSearchTimer: null,
  missingSearchTimer: null,
  saleSearchTimer: null,
  wishlistSearchTimer: null,
  catalogSearchTimer: null,
  editingCard: null,
  addResults: [],
  selectedAddCard: null,
  sharedCard: null,
  activeCardDetail: null,
  activeSet: null,
  setCards: [],
  decks: [],
  activeDeck: null,
  activeWishlist: null,
  pendingWishlistCard: null,
  pendingWishlistOptions: null,
  emailingWishlist: null,
  emailingEntity: null,
  containers: [],
  activeContainer: null,
  editingContainer: null,
  activeSaleCard: null,
  importRows: [],
  importIssues: [],
  selectedCards: new Map(),
  selectedSetMissingCards: new Map(),
  user: null,
  collectionView: localStorage.getItem("foilfolio.collectionView") || "tiles",
  favoritesView: localStorage.getItem("foilfolio.favoritesView") || "tiles",
  wishlistView: localStorage.getItem("foilfolio.wishlistView") || "tiles",
  settings: null,
};

const settingsKey = "foilfolio.settings";

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
const cardConditions = ["Near Mint", "Lightly Played", "Moderately Played", "Heavily Played", "Damaged"];
const pageRoutes = {
  dashboard: "/",
  favorites: "/favorites",
  collection: "/collection",
  decks: "/decks",
  containers: "/containers",
  "missing-list": "/missing-list",
  "for-sale": "/for-sale",
  wishlist: "/wishlist",
  search: "/search",
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
  historyCount: document.querySelector("#historyCount"),
  historyChart: document.querySelector("#historyChart"),
  topCount: document.querySelector("#topCount"),
  topCards: document.querySelector("#topCards"),
  setCompletionCount: document.querySelector("#setCompletionCount"),
  setCompletion: document.querySelector("#setCompletion"),
  cardsGrid: document.querySelector("#cardsGrid"),
  favoritesGrid: document.querySelector("#favoritesGrid"),
  missingGrid: document.querySelector("#missingGrid"),
  saleGrid: document.querySelector("#saleGrid"),
  wishlistGrid: document.querySelector("#wishlistGrid"),
  wishlistsGrid: document.querySelector("#wishlistsGrid"),
  catalogSearchGrid: document.querySelector("#catalogSearchGrid"),
  status: document.querySelector("#status"),
  favoritesStatus: document.querySelector("#favoritesStatus"),
  missingStatus: document.querySelector("#missingStatus"),
  saleStatus: document.querySelector("#saleStatus"),
  wishlistStatus: document.querySelector("#wishlistStatus"),
  catalogSearchStatus: document.querySelector("#catalogSearchStatus"),
  searchInput: document.querySelector("#searchInput"),
  favoriteSearchInput: document.querySelector("#favoriteSearchInput"),
  missingSearchInput: document.querySelector("#missingSearchInput"),
  saleSearchInput: document.querySelector("#saleSearchInput"),
  wishlistSearchInput: document.querySelector("#wishlistSearchInput"),
  catalogSearchForm: document.querySelector("#catalogSearchForm"),
  catalogSearchInput: document.querySelector("#catalogSearchInput"),
  catalogSearchButton: document.querySelector("#catalogSearchButton"),
  catalogOracleInput: document.querySelector("#catalogOracleInput"),
  catalogSetInput: document.querySelector("#catalogSetInput"),
  catalogColorSelect: document.querySelector("#catalogColorSelect"),
  catalogTypeSelect: document.querySelector("#catalogTypeSelect"),
  catalogRaritySelect: document.querySelector("#catalogRaritySelect"),
  catalogFormatSelect: document.querySelector("#catalogFormatSelect"),
  ownedFilter: document.querySelector("#ownedFilter"),
  sortSelect: document.querySelector("#sortSelect"),
  favoriteSortSelect: document.querySelector("#favoriteSortSelect"),
  missingSortSelect: document.querySelector("#missingSortSelect"),
  saleSortSelect: document.querySelector("#saleSortSelect"),
  wishlistSortSelect: document.querySelector("#wishlistSortSelect"),
  catalogSortSelect: document.querySelector("#catalogSortSelect"),
  tileViewButton: document.querySelector("#tileViewButton"),
  listViewButton: document.querySelector("#listViewButton"),
  favoriteTileViewButton: document.querySelector("#favoriteTileViewButton"),
  favoriteListViewButton: document.querySelector("#favoriteListViewButton"),
  wishlistTileViewButton: document.querySelector("#wishlistTileViewButton"),
  wishlistListViewButton: document.querySelector("#wishlistListViewButton"),
  shareFavoritesButton: document.querySelector("#shareFavoritesButton"),
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
  logoutButton: document.querySelector("#logoutButton"),
  importStatus: document.querySelector("#importStatus"),
  jsonImportFile: document.querySelector("#jsonImportFile"),
  csvImportFile: document.querySelector("#csvImportFile"),
  previewJsonImportButton: document.querySelector("#previewJsonImportButton"),
  previewCsvImportButton: document.querySelector("#previewCsvImportButton"),
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
  addSearchStatus: document.querySelector("#addSearchStatus"),
  addSearchResults: document.querySelector("#addSearchResults"),
  addCardForm: document.querySelector("#addCardForm"),
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
  settingsPageStatus: document.querySelector("#settingsPageStatus"),
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
  assignDeckOverlay: document.querySelector("#assignDeckOverlay"),
  assignDeckForm: document.querySelector("#assignDeckForm"),
  assignDeckCards: document.querySelector("#assignDeckCards"),
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
  containerDetailOverlay: document.querySelector("#containerDetailOverlay"),
  containerDetailTitle: document.querySelector("#containerDetailTitle"),
  containerDetailMeta: document.querySelector("#containerDetailMeta"),
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
  shareOverlay: document.querySelector("#shareOverlay"),
  shareTitle: document.querySelector("#shareTitle"),
  shareUrlInput: document.querySelector("#shareUrlInput"),
  copyShareButton: document.querySelector("#copyShareButton"),
  closeShareButton: document.querySelector("#closeShareButton"),
  sharedCardShell: document.querySelector("#sharedCardShell"),
  favoritesShareShell: document.querySelector("#favoritesShareShell"),
  wishlistShareShell: document.querySelector("#wishlistShareShell"),
  containerShareShell: document.querySelector("#containerShareShell"),
  cardDetailShell: document.querySelector("#cardDetailShell"),
  addPurchaseOverlay: document.querySelector("#addPurchaseOverlay"),
  addPurchaseForm: document.querySelector("#addPurchaseForm"),
  addPurchaseTitle: document.querySelector("#addPurchaseTitle"),
  closeAddPurchaseButton: document.querySelector("#closeAddPurchaseButton"),
  cancelAddPurchaseButton: document.querySelector("#cancelAddPurchaseButton"),
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
}

function setStatus(message, tone = "", target = els.status) {
  if (!target) return;
  target.textContent = message;
  target.dataset.tone = tone;
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
    const message = payload && payload.error ? payload.error : `Request failed: ${response.status}`;
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

function updateAuthUi() {
  const loggedIn = Boolean(state.user);
  document.body.classList.toggle("is-authenticated", loggedIn);
  if (els.accountButton) {
    els.accountButton.textContent = loggedIn ? state.user.email : "Log In";
    els.accountButton.title = loggedIn ? "Account settings" : "Log in";
  }
  if (els.logoutButton) {
    const icon = els.logoutButton.querySelector("[aria-hidden='true']");
    const label = els.logoutButton.querySelector(".auth-command-label");
    els.logoutButton.title = loggedIn ? "Log out" : "Log in";
    els.logoutButton.setAttribute("aria-label", loggedIn ? "Log out" : "Log in");
    if (icon) {
      icon.className = loggedIn ? "logout-icon" : "login-icon";
    }
    if (label) {
      label.textContent = loggedIn ? "Logout" : "Log In";
    }
  }
  if (els.settingsAccountEmail) {
    els.settingsAccountEmail.textContent = loggedIn ? state.user.email : "Not logged in";
  }
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
  }
  updateAuthUi();
  return state.user;
}

function authMode() {
  return els.authForm?.mode.value || "login";
}

function setAuthMode(mode) {
  const nextMode = ["register", "complete", "reset-request", "reset-complete"].includes(mode) ? mode : "login";
  els.authForm.mode.value = nextMode;
  const isLogin = nextMode === "login";
  const isRegister = nextMode === "register";
  const isComplete = nextMode === "complete";
  const isResetRequest = nextMode === "reset-request";
  const isResetComplete = nextMode === "reset-complete";
  els.authTitle.textContent = isComplete
    ? "Finish Account"
    : isRegister
      ? "Create Account"
      : isResetRequest
        ? "Reset Password"
        : isResetComplete
          ? "Choose New Password"
          : "Log In";
  els.submitAuthButton.textContent = isComplete
    ? "Create Account"
    : isRegister
      ? "Send Verification Email"
      : isResetRequest
        ? "Send Reset Email"
        : isResetComplete
          ? "Update Password"
          : "Log In";
  els.toggleAuthModeButton.textContent = isLogin ? "Create Account" : "Use Existing Account";
  els.toggleAuthModeButton.hidden = isComplete || isResetComplete;
  els.forgotPasswordButton.hidden = !isLogin;
  els.authNameField.hidden = !isComplete;
  els.authNameField.toggleAttribute("hidden", !isComplete);
  els.authNameField.style.display = isComplete ? "" : "none";
  els.authPasswordField.hidden = isRegister || isResetRequest;
  els.authPasswordField.toggleAttribute("hidden", isRegister || isResetRequest);
  els.authPasswordField.style.display = (isRegister || isResetRequest) ? "none" : "";
  els.authForm.email.readOnly = isComplete || isResetComplete;
  els.authForm.email.required = true;
  els.authForm.name.required = isComplete;
  els.authForm.name.disabled = !isComplete;
  if (!isComplete) {
    els.authForm.name.value = "";
  }
  els.authForm.password.required = !(isRegister || isResetRequest);
  els.authForm.password.disabled = isRegister || isResetRequest;
  els.authHint.textContent = isComplete
    ? "Email verified. Add your name and a strong password to finish creating your account."
    : isRegister
      ? "Enter your email and we will send a verification link before you create a password. Use this again to resend a verification email."
      : isResetRequest
        ? "Enter your account email and we will send a password reset link."
        : isResetComplete
          ? "Choose a new strong password for your FoilFolio account."
          : "Log in to manage your collection, decks, containers, favorites, and wishlist.";
  els.authForm.password.autocomplete = (isComplete || isResetComplete) ? "new-password" : "current-password";
  if (els.togglePasswordVisibilityButton) {
    els.togglePasswordVisibilityButton.textContent = "Show";
    els.authForm.password.type = "password";
  }
}

function openAuthModal(mode = "login", message = "") {
  if (!els.authOverlay) return;
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
  if (mode === "reset-request") {
    const result = await api("/api/auth/password-reset-start", {
      method: "POST",
      body: JSON.stringify({ email: payload.email }),
    });
    els.authStatus.textContent = result.message || "If that email has a FoilFolio account, a password reset link has been sent.";
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
  closeAuthModal();
  await activatePage(appPageRoute() || "dashboard", { replace: true });
}

async function loadEmailVerification(token) {
  activatePage("search", { replace: true, promptLogin: false });
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
  activatePage("search", { replace: true, promptLogin: false });
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
  state.missingCards = [];
  state.saleCards = [];
  state.wishlistCards = [];
  state.wishlists = [];
  state.activeWishlist = null;
  updateAuthUi();
  activatePage("search", { push: true });
}

function protectedPage(page) {
  return !["search", "deck-share", "card-share", "favorites-share", "wishlist-share", "container-share"].includes(page);
}

function valueClass(value) {
  if (value > 0.004) return "positive";
  if (value < -0.004) return "negative";
  return "";
}

function isSpecialVariant(variant) {
  return Boolean(variant && variant.toLowerCase() !== "normal");
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
  selectWrap.hidden = !options.selectable;
  selectCheckbox.disabled = !selectable;
  selectCheckbox.checked = state.selectedCards.has(cardSelectionKey(card));
  selectCheckbox.addEventListener("change", () => {
    const key = cardSelectionKey(card);
    if (selectCheckbox.checked) {
      state.selectedCards.set(key, {
        card_id: card.scryfall_id,
        variant: card.variant || "Normal",
        name: cardTitle(card),
        quantity: Number(card.quantity || 0),
        unassigned_quantity: Number(card.unassigned_quantity ?? card.quantity ?? 0),
        saleable_quantity: Number(card.saleable_quantity ?? card.quantity ?? 0),
        deck_quantity: Number(card.deck_quantity || 0),
        display_price: Number(card.display_price || card.market_price || 0),
        sale_quantity: Number(card.sale_quantity || 0),
        sale_price: Number(card.sale_price || card.display_price || card.market_price || 0),
        card_condition: conditionText(card),
        condition_inventory: Array.isArray(card.condition_inventory) ? card.condition_inventory : [],
        image_small: card.image_small || "",
        image_normal: card.image_normal || "",
      });
    } else {
      state.selectedCards.delete(key);
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
  const confirmed = window.confirm(
    isSale
      ? "Delete this sold entry? This will undo the sale, restore inventory, and put the card back on For Sale."
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
  localStorage.setItem("foilfolio.collectionView", state.collectionView);
  els.tileViewButton.classList.toggle("is-active", state.collectionView === "tiles");
  els.listViewButton.classList.toggle("is-active", state.collectionView === "list");
  renderCollection();
}

function setFavoritesView(view) {
  state.favoritesView = view === "list" ? "list" : "tiles";
  localStorage.setItem("foilfolio.favoritesView", state.favoritesView);
  els.favoriteTileViewButton.classList.toggle("is-active", state.favoritesView === "tiles");
  els.favoriteListViewButton.classList.toggle("is-active", state.favoritesView === "list");
  renderFavorites();
}

function setWishlistView(view) {
  state.wishlistView = view === "list" ? "list" : "tiles";
  localStorage.setItem("foilfolio.wishlistView", state.wishlistView);
  els.wishlistTileViewButton.classList.toggle("is-active", state.wishlistView === "tiles");
  els.wishlistListViewButton.classList.toggle("is-active", state.wishlistView === "list");
  renderWishlist();
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
  els.topCount.textContent = `${integer.format(data.owned_unique || 0)} owned prints`;
  renderTopCards(data.top_cards || []);
  renderSetCompletion(data.set_completion || []);
  renderChart(data.history || []);
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
  const page = pageRoutes[pageName] ? pageName : "dashboard";
  if (protectedPage(page) && !state.user) {
    if (options.replace) {
      replacePageRoute("search");
    } else if (options.push) {
      pushPageRoute("search");
    }
    showPage("search");
    if (options.promptLogin !== false) {
      openAuthModal("login", "Log in or create an account to use that feature.");
    }
    return;
  }
  if (options.replace) {
    replacePageRoute(page);
  } else if (options.push) {
    pushPageRoute(page);
  }
  showPage(page);
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
  if (page === "wishlist") {
    clearSelectedCards();
    loadWishlists().catch((error) => {
      setStatus(error.message, "error", els.wishlistStatus);
    });
  }
  if (page === "search") {
    clearSelectedCards();
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
  if (visiblePage === "missing-list") return els.missingStatus;
  if (visiblePage === "for-sale") return els.saleStatus;
  if (visiblePage === "wishlist") return els.wishlistStatus;
  if (visiblePage === "search") return els.catalogSearchStatus;
  return els.status;
}

async function reloadVisibleCardPages() {
  const tasks = [loadCards()];
  const favoritesVisible = Array.from(els.pages).some((page) => page.dataset.page === "favorites" && !page.hidden);
  const missingVisible = Array.from(els.pages).some((page) => page.dataset.page === "missing-list" && !page.hidden);
  const saleVisible = Array.from(els.pages).some((page) => page.dataset.page === "for-sale" && !page.hidden);
  const wishlistVisible = Array.from(els.pages).some((page) => page.dataset.page === "wishlist" && !page.hidden);
  if (favoritesVisible) {
    tasks.push(loadFavorites());
  }
  if (missingVisible) {
    tasks.push(loadMissingList());
  }
  if (saleVisible) {
    tasks.push(loadSaleCards());
  }
  if (wishlistVisible) {
    tasks.push(loadWishlists());
    if (state.activeWishlist) {
      tasks.push(loadWishlist());
    }
  }
  await Promise.all(tasks);
}

function sharedRouteId() {
  const match = window.location.pathname.match(/^\/cards\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function setRouteCode() {
  const match = window.location.pathname.match(/^\/sets\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]).toLowerCase() : "";
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

function favoritesShareRoute() {
  return /^\/favorites\/shared\/?$/.test(window.location.pathname);
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

async function loadCards() {
  const data = await api(`/api/cards?${cardQuery()}`);
  state.cards = data.cards || [];
  renderCollection();
}

async function loadFavorites() {
  const data = await api(`/api/cards?${favoriteQuery()}`);
  state.favoriteCards = data.cards || [];
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
    state.catalogSearchResults = result.cards || [];
    renderCatalogSearchResults();
    els.catalogSearchStatus.textContent = `${integer.format(state.catalogSearchResults.length)} result${state.catalogSearchResults.length === 1 ? "" : "s"}`;
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

function renderCollection() {
  els.cardsGrid.className = state.collectionView === "list" ? "cards-list" : "cards-grid";
  els.tileViewButton.classList.toggle("is-active", state.collectionView === "tiles");
  els.listViewButton.classList.toggle("is-active", state.collectionView === "list");
  if (state.collectionView === "list") {
    renderCardList(state.cards, els.cardsGrid, { selectable: true });
  } else {
    renderCards(state.cards, els.cardsGrid, { selectable: true });
  }
}

function renderFavorites() {
  els.favoritesGrid.className = state.favoritesView === "list" ? "cards-list" : "cards-grid";
  els.favoriteTileViewButton.classList.toggle("is-active", state.favoritesView === "tiles");
  els.favoriteListViewButton.classList.toggle("is-active", state.favoritesView === "list");
  const options = {
    selectable: true,
    confirmUnfavorite: true,
    statusTarget: els.favoritesStatus,
    afterFavoriteChange: async () => {
      await loadFavorites();
      await refresh();
    },
  };
  if (state.favoritesView === "list") {
    renderCardList(state.favoriteCards, els.favoritesGrid, options);
  } else {
    renderCards(state.favoriteCards, els.favoritesGrid, options);
  }
}

function renderWishlist() {
  els.wishlistGrid.className = state.wishlistView === "list" ? "cards-list wishlist-detail-grid" : "cards-grid wishlist-detail-grid";
  els.wishlistTileViewButton.classList.toggle("is-active", state.wishlistView === "tiles");
  els.wishlistListViewButton.classList.toggle("is-active", state.wishlistView === "list");
  const options = {
    wishlistId: state.activeWishlist?.id,
    confirmUnwishlist: true,
    statusTarget: els.wishlistStatus,
    afterWishlistChange: async () => {
      await loadWishlist();
      await loadWishlists();
      await refresh();
    },
  };
  if (state.wishlistView === "list") {
    renderCardList(state.wishlistCards, els.wishlistGrid, options);
  } else {
    renderCards(state.wishlistCards, els.wishlistGrid, options);
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
  if (type === "deck") return shareUrlForDeck(entity);
  if (type === "container") return shareUrlForContainer(entity);
  return shareUrlForWishlist(entity);
}

function emailEntityLabel(type) {
  if (type === "card") return "Card";
  if (type === "deck") return "Deck";
  if (type === "container") return "Container";
  return "Wishlist";
}

function openEmailShareModal(type, entity) {
  state.emailingEntity = { type, entity };
  state.emailingWishlist = type === "wishlist" ? entity : null;
  els.emailWishlistForm.reset();
  els.emailWishlistForm.entity_type.value = type;
  els.emailWishlistForm.entity_id.value = entity.id || entity.scryfall_id || entity.card_id || "";
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

function renderCatalogSearchResults() {
  els.catalogSearchGrid.innerHTML = "";
  if (!state.catalogSearchResults.length) {
    els.catalogSearchGrid.innerHTML = '<div class="empty-state">Search Scryfall to add cards to Wishlist or Collection.</div>';
    return;
  }
  for (const card of state.catalogSearchResults) {
    const owned = Number(card.owned_quantity || 0) > 0;
    const item = document.createElement("article");
    item.className = "catalog-result-card";
    item.classList.toggle("is-owned", owned);
    item.innerHTML = `
      <a class="catalog-result-art" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" title="Open on Scryfall">
        <img src="${escapeHtml(card.image_normal || card.image_small || "")}" alt="${escapeHtml(cardTitle(card))}">
      </a>
      <div class="catalog-result-copy">
        <h3>${escapeHtml(cardTitle(card))}</h3>
        <p>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.rarity || "unknown")}</p>
        <p>${escapeHtml(card.type_line || "")}</p>
        <div class="catalog-result-pills">
          <span>${escapeHtml(cardTypeLabel(card))}</span>
          <span>${escapeHtml(cardColorLabel(card))}</span>
          <span>${dollars.format(priceForVariant(card, "Normal"))}</span>
          <span>Owned ${integer.format(card.owned_quantity || 0)}</span>
        </div>
      </div>
      <div class="catalog-result-actions">
        <button class="wishlist-button ${card.wishlist ? "is-wishlist" : ""}" type="button" aria-label="${card.wishlist ? "Remove from Wishlist" : "Add to Wishlist"}" title="${owned ? "Owned cards are not available for Wishlist" : card.wishlist ? "Remove from Wishlist" : "Add to Wishlist"}" ${owned ? "disabled" : ""}></button>
        <button class="primary-button catalog-add-button" type="button">Add to Collection</button>
      </div>
    `;
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
  target.innerHTML = "";
  if (!cards.length) {
    target.innerHTML = '<div class="empty-state">No cards match the current filters.</div>';
    if (isCardGridTarget(target)) updateBulkBar();
    return;
  }
  for (const card of cards) {
    const owned = Number(card.quantity || 0) > 0;
    const catalogOnly = Boolean(card.catalog_only);
    const node = els.template.content.firstElementChild.cloneNode(true);
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

    link.href = catalogOnly ? (card.scryfall_uri || "#") : cardDetailUrl(card);
    link.target = catalogOnly ? "_blank" : "_self";
    link.rel = catalogOnly ? "noreferrer" : "";
    img.src = card.image_normal || card.image_small || "";
    img.alt = cardTitle(card);
    title.textContent = cardTitle(card);
    meta.textContent = `${card.set_name} #${card.collector_number} - ${card.rarity || "unknown"}${cardRulesName(card) ? ` - Rules: ${cardRulesName(card)}` : ""}`;
    type.textContent = card.type_line || "";
    quantityWatermark.textContent = integer.format(card.quantity || 0);
    node.classList.toggle("is-special", isSpecialVariant(card.variant));
    node.classList.toggle("is-missing", !owned);
    ownedValue.textContent = dollars.format(card.owned_value || 0);
    if (price) price.textContent = `Now ${dollars.format(card.display_price || 0)}`;
    delta.textContent = `Delta ${dollars.format(card.gain_loss || 0)}`;
    delta.className = `delta ${valueClass(card.gain_loss || 0)}`;
    variantPill.textContent = card.variant || "Normal";
    conditionPill.textContent = conditionText(card);
    typePill.textContent = cardTypeLabel(card);
    colorPill.textContent = cardColorLabel(card);

    if (options.setMissingSelectable) {
      wireSetMissingSelection(selectWrap, selectCheckbox, card);
    } else {
      wireCardSelection(selectWrap, selectCheckbox, card, options);
    }

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
    wireWishlistButton(wishlistButton, card, options);
    if (catalogOnly) {
      refreshButton.hidden = true;
      editButton.hidden = true;
      shareButton.hidden = true;
      deckButton.hidden = true;
      containerButton.hidden = true;
    } else {
      wireRefreshCardButton(refreshButton, card);
      editButton.addEventListener("click", () => openCardDetail(card));
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
  target.innerHTML = "";
  if (!cards.length) {
    target.innerHTML = '<div class="empty-state">No cards match the current filters.</div>';
    if (isCardGridTarget(target)) updateBulkBar();
    return;
  }
  for (const card of cards) {
    const owned = Number(card.quantity || 0) > 0;
    const catalogOnly = Boolean(card.catalog_only);
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
    const wishlistButton = node.querySelector(".wishlist-button");
    const deleteButton = node.querySelector(".delete-card-button");

    node.classList.toggle("is-special", isSpecialVariant(card.variant));
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
    variant.textContent = card.variant || "Normal";
    conditionPill.textContent = conditionText(card);
    typePill.textContent = cardTypeLabel(card);
    colorPill.textContent = cardColorLabel(card);

    wireCardSelection(selectWrap, selectCheckbox, card, options);
    wireDeckMembershipButton(deckButton, card, target === els.cardsGrid);
    wireContainerMembershipButton(containerButton, card, target === els.cardsGrid);
    wireScryfallButton(scryfallButton, card);
    if (catalogOnly) {
      deckButton.hidden = true;
      containerButton.hidden = true;
      refreshButton.hidden = true;
      editButton.hidden = true;
      shareButton.hidden = true;
      deleteButton.hidden = true;
    } else {
      wireRefreshCardButton(refreshButton, card);
      editButton.addEventListener("click", () => openCardDetail(card));
      wireShareButton(shareButton, card);
      wireDeleteCardButton(deleteButton, card);
      wireCardDetailNavigation(node, card);
    }
    wireWishlistButton(wishlistButton, card, options);

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

function shareUrlForFavorites() {
  return new URL("/favorites/shared", window.location.origin).toString();
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

function openFavoritesShareModal() {
  openShareUrl("Favorites", shareUrlForFavorites());
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

function todayValue() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function priceForVariant(card, variant) {
  const prices = card.prices || {};
  const variantText = String(variant || "").toLowerCase();
  if (variantText.includes("etched") && prices.usd_etched) return prices.usd_etched;
  if (variantText.includes("foil") && prices.usd_foil) return prices.usd_foil;
  return prices.usd || prices.usd_foil || prices.usd_etched || 0;
}

function variantsForCard(card) {
  const finishes = card.finishes || [];
  const variants = [];
  if (finishes.includes("nonfoil")) variants.push("Normal");
  if (finishes.includes("foil")) variants.push("Foil");
  if (finishes.includes("etched")) variants.push("Etched Foil");
  return variants.length ? variants : ["Normal"];
}

function openAddCardModal(preselectedCard = null) {
  if (!state.user) {
    openAuthModal("register", "Create an account or log in before adding cards to your Collection.");
    return;
  }
  state.addResults = [];
  state.selectedAddCard = null;
  els.addSearchForm.reset();
  els.addCardForm.reset();
  els.addCardForm.scryfall_id.value = "";
  els.addCardForm.quantity.value = "1";
  els.addCardForm.paid_price.value = "0.01";
  els.addCardForm.acquired_date.value = todayValue();
  els.addCardForm.variant.innerHTML = "<option>Normal</option>";
  els.addCardForm.card_condition.value = "Near Mint";
  els.addCardForm.graded.checked = false;
  els.addSearchStatus.textContent = "";
  els.addSearchResults.innerHTML = "";
  els.selectedAddCard.hidden = true;
  els.selectedAddCard.innerHTML = "";
  els.confirmAddCardButton.disabled = true;
  els.confirmAddNewCardButton.disabled = true;
  els.addCardOverlay.hidden = false;
  document.body.classList.add("modal-open");
  if (preselectedCard && preselectedCard.scryfall_id) {
    state.addResults = [preselectedCard];
    els.addSearchInput.value = cardTitle(preselectedCard);
    renderAddResults(state.addResults);
    selectAddCard(preselectedCard);
    els.addSearchStatus.textContent = "Selected from Search.";
    els.addCardForm.quantity.focus();
  } else {
    els.addSearchInput.focus();
  }
}

function resetAddCardModalForNew() {
  state.addResults = [];
  state.selectedAddCard = null;
  els.addSearchForm.reset();
  els.addCardForm.reset();
  els.addCardForm.scryfall_id.value = "";
  els.addCardForm.quantity.value = "1";
  els.addCardForm.paid_price.value = "0.01";
  els.addCardForm.acquired_date.value = todayValue();
  els.addCardForm.variant.innerHTML = "<option>Normal</option>";
  els.addCardForm.card_condition.value = "Near Mint";
  els.addCardForm.graded.checked = false;
  els.addSearchResults.innerHTML = "";
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
  const query = els.addSearchInput.value.trim();
  if (query.length < 2) {
    els.addSearchStatus.textContent = "Type at least 2 characters.";
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
  els.addCardForm.variant.innerHTML = "";
  for (const variant of variantsForCard(card)) {
    const option = document.createElement("option");
    option.value = variant;
    option.textContent = variant;
    els.addCardForm.variant.appendChild(option);
  }
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
  const variant = els.addCardForm.variant.value || "Normal";
  els.selectedAddCard.hidden = false;
  els.selectedAddCard.innerHTML = `
    <img src="${card.image_small || card.image_normal || ""}" alt="">
    <div>
      <strong>${escapeHtml(cardTitle(card))}</strong>
      <p>${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)} - ${escapeHtml(card.type_line || "")}</p>
      ${cardRulesName(card) ? `<span>Rules: ${escapeHtml(cardRulesName(card))}</span>` : ""}
      <span>${escapeHtml(variant)} market: ${dollars.format(priceForVariant(card, variant))}</span>
      <span class="owned-count">Owned: ${integer.format(card.owned_quantity || 0)}</span>
    </div>
  `;
}

function openSettingsModal() {
  els.settingsForm.language.value = (state.settings && state.settings.language) || "en";
  els.settingsForm.theme.value = (state.settings && state.settings.theme) || "light";
  els.settingsOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.settingsForm.theme.focus();
}

function closeSettingsModal() {
  els.settingsOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.settingsForm.reset();
}

function renderSettingsPage() {
  if (!els.settingsPageForm) return;
  const settings = state.settings || defaultSettings();
  els.settingsPageForm.language.value = settings.language || "en";
  els.settingsPageForm.theme.value = settings.theme || "light";
  if (els.settingsAccountEmail) {
    els.settingsAccountEmail.textContent = state.user ? state.user.email : "Not logged in";
  }
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
    const item = document.createElement("button");
    item.className = "deck-card";
    item.type = "button";
    item.dataset.deckId = deck.id;
    item.setAttribute("aria-label", `Open ${deck.name}`);
    item.innerHTML = `
      <div>
        <p class="eyebrow">Deck</p>
        <h3>${escapeHtml(deck.name)}</h3>
      </div>
      <strong>${integer.format(deck.card_count || 0)}</strong>
      <span>${integer.format(deck.unique_card_count || 0)} unique cards assigned</span>
    `;
    item.addEventListener("click", () => {
      openDeckPage(deck.id).catch((error) => {
        els.decksStatus.textContent = error.message;
      });
    });
    els.decksGrid.appendChild(item);
  }
}

function renderDeckCardsEditable(deck) {
  const cards = deck.cards || [];
  if (!cards.length) {
    return '<div class="empty-state">No cards in this deck yet.</div>';
  }
  return cards.map((card) => `
    <article class="deck-card-row">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
      </div>
      <b>Qty ${integer.format(deckQuantity(card))}</b>
      <button class="remove-deck-card-button" type="button" data-card-id="${escapeHtml(card.scryfall_id || card.card_id || "")}" data-variant="${escapeHtml(card.variant || "Normal")}" aria-label="Remove card from deck" title="Remove card"><span class="trash-icon" aria-hidden="true"></span></button>
    </article>
  `).join("");
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
          <div class="deck-editor-actions">
            <button class="primary-button" type="submit">Save</button>
            <button class="share-button" type="button" data-deck-action="email" aria-label="Email deck" title="Email deck"><span class="send-icon" aria-hidden="true"></span></button>
            <button class="share-button" type="button" data-deck-action="share" aria-label="Share deck" title="Share deck">&#8599;</button>
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
  const status = els.deckEditorShell.querySelector("#deckEditorStatus");
  els.deckEditorShell.querySelector("#deckEditorForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "Saving deck...";
    status.dataset.tone = "";
    const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const result = await api(`/api/decks/${encodeURIComponent(deck.id)}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
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
  els.deckEditorShell.querySelector('[data-deck-action="delete"]').addEventListener("click", () => {
    deleteActiveDeck().catch((error) => {
      status.textContent = error.message;
      status.dataset.tone = "error";
    });
  });
  for (const button of els.deckEditorShell.querySelectorAll(".remove-deck-card-button")) {
    button.addEventListener("click", () => {
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
    row.className = "deck-card-row";
    row.innerHTML = `
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
      </div>
      <b>Qty ${integer.format(deckQuantity(card))}</b>
      ${readonly ? "" : '<button class="remove-deck-card-button" type="button" aria-label="Remove card from deck" title="Remove card"><span class="trash-icon" aria-hidden="true"></span></button>'}
    `;
    if (!readonly) {
      const removeButton = row.querySelector(".remove-deck-card-button");
      removeButton.addEventListener("click", () => {
        removeCardFromActiveDeck(card).catch((error) => {
          els.decksStatus.textContent = error.message;
        });
      });
    }
    els.deckDetailCards.appendChild(row);
  }
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

function openDeckCardSearchModal() {
  if (!state.activeDeck) return;
  els.deckCardSearchForm.reset();
  els.deckCardSearchResults.innerHTML = "";
  els.deckCardSearchStatus.textContent = "Search owned cards not already in this deck.";
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
    els.deckCardSearchResults.innerHTML = '<div class="empty-state">No matching owned cards are available for this deck.</div>';
    return;
  }
  for (const card of cards) {
    const available = Math.max(1, Number(card.available_deck_quantity ?? card.quantity ?? 1));
    const current = Number(card.deck_quantity || 0);
    const row = document.createElement("article");
    row.className = "deck-card-search-result";
    row.innerHTML = `
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <span>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <small>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</small>
        <small>${current ? `${integer.format(current)} already in deck - ` : ""}${integer.format(available)} available to add</small>
        <span class="deck-card-tags">${cardMetadataPillsHtml(card)}</span>
      </span>
      <label class="deck-quantity-field">
        Qty
        <input type="number" min="1" max="${available}" step="1" value="1" aria-label="Quantity to add">
      </label>
      <button class="primary-button deck-add-card-button" type="button">Add</button>
    `;
    const input = row.querySelector("input");
    row.querySelector(".deck-add-card-button").addEventListener("click", () => {
      addOwnedCardToActiveDeck(card, Number(input.value || 1)).catch((error) => {
        els.deckCardSearchStatus.textContent = error.message;
      });
    });
    els.deckCardSearchResults.appendChild(row);
  }
}

async function searchOwnedCardsForDeck() {
  if (!state.activeDeck) return;
  const query = els.deckCardSearchInput.value.trim();
  if (query.length < 2) {
    els.deckCardSearchStatus.textContent = "Type at least 2 characters.";
    els.deckCardSearchResults.innerHTML = "";
    return;
  }
  els.deckCardSearchStatus.textContent = "Searching your collection...";
  const params = new URLSearchParams({
    search: query,
    owned: "owned",
    sort: "name",
    limit: "250",
  });
  const data = await api(`/api/cards?${params.toString()}`);
  const deckQuantities = activeDeckQuantities();
  const cards = (data.cards || []).filter((card) => {
    const inDeck = deckQuantities.get(deckCardKey(card)) || 0;
    const available = Number(card.quantity || 0) - inDeck;
    card.deck_quantity = inDeck;
    card.available_deck_quantity = available;
    return available > 0;
  });
  els.deckCardSearchStatus.textContent = `${integer.format(cards.length)} available match${cards.length === 1 ? "" : "es"}.`;
  renderDeckCardSearchResults(cards);
}

async function addOwnedCardToActiveDeck(card, quantity = 1) {
  if (!state.activeDeck) return;
  const deckId = state.activeDeck.id;
  const max = Math.max(1, Number(card.available_deck_quantity ?? card.quantity ?? 1));
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
  await searchOwnedCardsForDeck();
}

async function removeCardFromActiveDeck(card) {
  if (!state.activeDeck) return;
  const confirmed = window.confirm(`Remove ${cardTitle(card)} from ${state.activeDeck.name}?`);
  if (!confirmed) return;
  await api(`/api/decks/${encodeURIComponent(state.activeDeck.id)}/cards`, {
    method: "DELETE",
    body: JSON.stringify({
      card_id: card.scryfall_id,
      variant: card.variant || "Normal",
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

function openAddDeckModal() {
  els.addDeckForm.reset();
  els.addDeckOverlay.hidden = false;
  document.body.classList.add("modal-open");
  els.addDeckForm.querySelector('[name="name"]').focus();
}

function closeAddDeckModal() {
  els.addDeckOverlay.hidden = true;
  document.body.classList.remove("modal-open");
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

async function refreshAssignDeckCardsForSelectedDeck() {
  const deckId = els.assignDeckForm.deck_id.value;
  if (!deckId) {
    renderAssignDeckCards();
    return;
  }
  const deck = await api(`/api/decks/${encodeURIComponent(deckId)}`);
  renderAssignDeckCards(deck);
}

async function openAssignDeckModal() {
  if (!state.selectedCards.size) return;
  const decks = await loadDecks();
  const select = els.assignDeckForm.deck_id;
  select.innerHTML = "";
  if (!decks.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "Create a deck first";
    select.appendChild(option);
  } else {
    for (const deck of decks) {
      const option = document.createElement("option");
      option.value = deck.id;
      option.textContent = `${deck.name} (${integer.format(deck.card_count || 0)})`;
      select.appendChild(option);
    }
  }
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
      <strong>${integer.format(container.stored_quantity || 0)}</strong>
      <span>${integer.format(container.card_count || 0)} unique cards stored</span>
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
  state.activeContainer = container;
  els.containerDetailTitle.textContent = container.name || "Container";
  els.containerDetailMeta.textContent = [containerTypeLabel(container.storage_type), container.location, container.notes].filter(Boolean).join(" - ");
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
  els.addContainerOverlay.classList.remove("modal-overlay-stacked");
  els.addContainerForm.reset();
  els.addContainerForm.id.value = "";
  els.addContainerForm.storage_type.value = "other";
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
  if (els.containerDetailOverlay.hidden) {
    document.body.classList.remove("modal-open");
  }
  state.editingContainer = null;
  els.addContainerForm.reset();
}

function renderAssignContainerCards() {
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

async function openAssignContainerModal() {
  if (!state.selectedCards.size) return;
  const containers = await loadContainers();
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
      option.value = container.id;
      option.textContent = `${containerTypeLabel(container.storage_type)} - ${container.name}${container.location ? ` - ${container.location}` : ""}`;
      select.appendChild(option);
    }
  }
  renderAssignContainerCards();
  els.assignContainerOverlay.hidden = false;
  document.body.classList.add("modal-open");
  select.focus();
}

function closeAssignContainerModal() {
  els.assignContainerOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.assignContainerForm.reset();
  els.assignContainerCards.innerHTML = "";
}

function renderSaleCards() {
  const cards = Array.from(state.selectedCards.values());
  els.saleCards.innerHTML = "";
  if (!cards.length) {
    els.saleCards.innerHTML = '<div class="empty-state">Select owned cards first.</div>';
    return;
  }
  for (const card of cards) {
    const market = Number(card.display_price || 0);
    const buckets = Array.isArray(card.condition_inventory) ? card.condition_inventory : [];
    const saleBuckets = buckets
      .map((bucket) => ({
        card_condition: bucket.card_condition || card.card_condition || "Near Mint",
        quantity: Number(bucket.quantity || 0),
        sale_available_quantity: Number(bucket.sale_available_quantity ?? bucket.quantity ?? 0),
        sale_quantity: Number(bucket.sale_quantity || 0),
        sale_price: Number(bucket.sale_price || card.sale_price || market || 0.01),
      }))
      .filter((bucket) => bucket.quantity > 0);
    if (!saleBuckets.length && Number(card.quantity || 0) > 0) {
      saleBuckets.push({
        card_condition: card.card_condition || "Near Mint",
        quantity: Number(card.quantity || 0),
        sale_available_quantity: Number(card.saleable_quantity ?? card.quantity ?? 0),
        sale_quantity: Number(card.sale_quantity || 0),
        sale_price: Number(card.sale_price || market || 0.01),
      });
    }
    for (const bucket of saleBuckets) {
      const condition = bucket.card_condition || "Near Mint";
      const maxQuantity = Number(bucket.sale_available_quantity ?? bucket.quantity ?? 0);
      const existingQuantity = Number(bucket.sale_quantity || 0);
      const disabled = maxQuantity <= 0;
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
          <span>${escapeHtml(card.variant || "Normal")} - ${escapeHtml(condition)}${disabled ? " - remove from decks before selling" : Number(card.deck_quantity || 0) > 0 ? ` - ${integer.format(card.deck_quantity)} in decks` : ""}</span>
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
}

function openSaleModal() {
  if (!state.selectedCards.size) return;
  renderSaleCards();
  els.saleOverlay.hidden = false;
  document.body.classList.add("modal-open");
}

function closeSaleModal() {
  els.saleOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.saleForm.reset();
  els.saleCards.innerHTML = "";
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

function renderSharedCard(card) {
  state.sharedCard = card;
  const specialClass = isSpecialVariant(card.variant) ? " is-special" : "";
  els.sharedCardShell.innerHTML = `
    <article class="shared-card${specialClass}">
      <a class="shared-card-art" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer">
        <img src="${escapeHtml(card.image_normal || card.image_small || "")}" alt="${escapeHtml(cardTitle(card))}">
      </a>
      <div class="shared-card-copy">
        <p class="eyebrow">Shared from FoilFolio</p>
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
}

function renderMovementHistory(movements) {
  if (!movements || !movements.length) {
    return '<div class="empty-state">No card movement yet.</div>';
  }
  return `
    <div class="purchase-history-list">
      ${movements.map((movement) => {
        const isSale = movement.movement_type === "sell";
        const verb = isSale ? "sold" : "bought";
        const amountLabel = isSale ? "received" : "total";
        const deleteLabel = isSale ? "Delete sold entry" : "Delete purchase entry";
        return `
        <article class="purchase-history-row ${isSale ? "is-sale" : "is-purchase"}">
          <div>
            <strong>${escapeHtml(formatDate(movement.movement_date || movement.purchase_date))}</strong>
            <span>${escapeHtml(movement.card_condition || "Near Mint")}</span>
          </div>
          <div>
            <b>${integer.format(movement.quantity || 0)} ${verb}</b>
            <span>${dollars.format(movement.total_amount ?? movement.total_price ?? 0)} ${amountLabel} - ${dollars.format(movement.price_each || 0)} each</span>
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

function renderCardDetail(card) {
  state.activeCardDetail = card;
  const specialClass = isSpecialVariant(card.variant) ? " is-special" : "";
  const owned = Number(card.quantity || 0) > 0;
  const hasDecks = deckMemberships(card).length > 0;
  const hasContainers = containerMemberships(card).length > 0;
  const detailsHtml = owned ? `
          <div>
            <dt>Owned</dt>
            <dd>${integer.format(card.quantity || 0)}</dd>
          </div>
          <div>
            <dt>Average Paid</dt>
            <dd>${dollars.format(card.paid_price || 0)}</dd>
          </div>
          <div>
            <dt>Market Price</dt>
            <dd>${dollars.format(card.market_price ?? card.display_price ?? 0)}</dd>
          </div>
          <div>
            <dt>Total Value</dt>
            <dd>${dollars.format(card.total_value ?? card.owned_value ?? 0)}</dd>
          </div>
          <div>
            <dt>Total Delta</dt>
            <dd class="${valueClass(card.gain_loss || 0)}">${dollars.format(card.gain_loss || 0)}</dd>
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
    <article class="shared-card editable-card-detail${specialClass}">
      <div class="card-detail-media">
        <a class="shared-card-art" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" title="Open on Scryfall">
          <img src="${escapeHtml(card.image_normal || card.image_small || "")}" alt="${escapeHtml(cardTitle(card))}">
        </a>
        ${owned ? `<div class="detail-storage-actions">
          <button class="detail-storage-button detail-decks-button" type="button" aria-label="View decks" title="${hasDecks ? "View decks" : "Not in any decks"}" ${hasDecks ? "" : "disabled"}>
            <span class="deck-icon" aria-hidden="true"></span>
          </button>
          <button class="detail-storage-button detail-containers-button" type="button" aria-label="View containers" title="${hasContainers ? "View containers" : "Not stored in a container"}" ${hasContainers ? "" : "disabled"}>
            ${containerIconHtml((containerMemberships(card)[0] || {}).storage_type)}
          </button>
        </div>` : ""}
      </div>
      <div class="shared-card-copy">
        <p class="eyebrow">${owned ? "Collection card" : "Catalog card"}</p>
        <h2>${escapeHtml(cardTitle(card))}</h2>
        <div class="card-divider"></div>
        <p>${escapeHtml(card.set_name)} #${escapeHtml(card.collector_number)} - ${escapeHtml(card.rarity || "unknown")}</p>
        ${cardRulesName(card) ? `<p>Rules: ${escapeHtml(cardRulesName(card))}</p>` : ""}
        <p>${escapeHtml(card.type_line || "")}</p>
        <div class="detail-pill-row">
          <span>${escapeHtml(card.variant || "Normal")}</span>
          ${owned ? `<span>${escapeHtml(conditionText(card))}</span>` : ""}
          <span>${escapeHtml(cardTypeLabel(card))}</span>
          <span>${escapeHtml(cardColorLabel(card))}</span>
        </div>
        <dl class="shared-card-details">
          ${detailsHtml}
        </dl>
        <div class="detail-actions">
          ${owned
            ? '<button id="addPurchaseButton" class="primary-button" type="button">Add Purchase</button>'
            : '<button class="wishlist-button detail-wishlist-button" type="button" aria-label="Add to Wishlist" title="Add to Wishlist"></button>'}
        </div>
      </div>
      <aside class="card-detail-toolbar" aria-label="Card actions">
        ${owned ? '<button class="detail-action-button detail-edit-button" type="button" aria-label="Edit card" title="Edit card"><span class="edit-icon" aria-hidden="true"></span></button>' : ""}
        <button class="detail-action-button detail-refresh-button" type="button" aria-label="Refresh from Scryfall" title="Refresh from Scryfall">&#8635;</button>
        <a class="detail-action-button detail-scryfall-button" href="${escapeHtml(card.scryfall_uri || "#")}" target="_blank" rel="noreferrer" aria-label="View on Scryfall" title="View on Scryfall">S</a>
        <button class="detail-action-button detail-share-button" type="button" aria-label="Share card" title="Share card">&#8599;</button>
        <button class="detail-action-button detail-email-button" type="button" aria-label="Email card" title="Email card"><span class="send-icon" aria-hidden="true"></span></button>
        ${owned ? '<button class="detail-action-button detail-delete-button" type="button" aria-label="Delete card" title="Delete card"><span class="trash-icon" aria-hidden="true"></span></button>' : ""}
      </aside>
    </article>
    ${owned ? `<section class="purchase-history-panel">
      <div class="panel-head">
        <h2>Card History</h2>
        <span>${integer.format((card.movements || card.purchases || []).length)} entries</span>
      </div>
      ${renderMovementHistory(card.movements || card.purchases || [])}
    </section>` : ""}
  `;
  els.cardDetailShell.querySelector("#addPurchaseButton")?.addEventListener("click", () => openAddPurchaseModal(card));
  els.cardDetailShell.querySelector(".detail-wishlist-button") && wireWishlistButton(els.cardDetailShell.querySelector(".detail-wishlist-button"), card, {
    statusTarget: els.status,
    afterWishlistChange: async () => {
      await loadCardDetail(card.scryfall_id, card.variant || "Normal");
      await loadWishlists();
    },
  });
  els.cardDetailShell.querySelector(".detail-edit-button")?.addEventListener("click", () => openEditModal(card));
  els.cardDetailShell.querySelector(".detail-refresh-button").addEventListener("click", (event) => {
    refreshCardDetailMetadata(event.currentTarget, card).catch((error) => setStatus(error.message, "error"));
  });
  els.cardDetailShell.querySelector(".detail-share-button").addEventListener("click", () => openShareModal(card));
  els.cardDetailShell.querySelector(".detail-email-button").addEventListener("click", () => openEmailCardModal(card));
  els.cardDetailShell.querySelector(".detail-delete-button")?.addEventListener("click", () => {
    deleteCardFromDetail(card).catch((error) => setStatus(error.message, "error"));
  });
  els.cardDetailShell.querySelector(".detail-decks-button")?.addEventListener("click", () => openCardDecksModal(card));
  els.cardDetailShell.querySelector(".detail-containers-button")?.addEventListener("click", () => openCardContainersModal(card));
  els.cardDetailShell.querySelectorAll(".delete-movement-button").forEach((button) => {
    button.addEventListener("click", () => {
      deleteCardMovement(button).catch((error) => setStatus(error.message, "error"));
    });
  });
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

function openAddPurchaseModal(card) {
  state.activeCardDetail = card;
  els.addPurchaseTitle.textContent = cardTitle(card);
  els.addPurchaseForm.card_id.value = card.scryfall_id;
  els.addPurchaseForm.variant.value = card.variant || "Normal";
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

function renderSetPage(setDetail, cards) {
  state.activeSet = setDetail;
  state.setCards = cards;
  state.selectedSetMissingCards.clear();
  const percent = Math.max(0, Math.min(100, Number(setDetail.completion_percent || 0)));
  els.setPageShell.innerHTML = `
    <section class="set-hero">
      <div>
        <p class="eyebrow">Set completion</p>
        <h2>${escapeHtml(setDetail.set_name || setDetail.set_code)}</h2>
        <span>${integer.format(setDetail.owned_cards || 0)} / ${integer.format(setDetail.total_cards || 0)} unique prints</span>
      </div>
      <div class="set-hero-actions">
        <b>${percent.toFixed(1)}%</b>
        <button id="addMissingSetButton" class="primary-button" type="button">Add Missing to Missing List</button>
      </div>
      <div class="set-progress set-progress-large" aria-label="${percent.toFixed(1)} percent complete">
        <span style="width: ${percent}%"></span>
      </div>
    </section>
    <div id="setPageStatus" class="status" aria-live="polite"></div>
    <div id="setMissingBulkBar" class="bulk-bar" hidden>
      <span id="setMissingSelectedCount">0 selected</span>
      <button id="addSelectedMissingButton" class="primary-button" type="button">Add to Missing List</button>
    </div>
    <div id="setCardsGrid" class="cards-grid set-cards-grid"></div>
  `;
  const addMissingButton = els.setPageShell.querySelector("#addMissingSetButton");
  addMissingButton.addEventListener("click", () => {
    addSetMissingToMissingList(setDetail.set_code, addMissingButton).catch((error) => {
      const status = els.setPageShell.querySelector("#setPageStatus");
      setStatus(error.message, "error", status);
    });
  });
  const addSelectedButton = els.setPageShell.querySelector("#addSelectedMissingButton");
  addSelectedButton.addEventListener("click", () => {
    addSelectedSetMissingToMissingList(addSelectedButton).catch((error) => {
      const status = els.setPageShell.querySelector("#setPageStatus");
      setStatus(error.message, "error", status);
    });
  });
  renderCards(cards, els.setPageShell.querySelector("#setCardsGrid"), { setMissingSelectable: true });
  updateSetMissingBar();
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
    <article class="deck-card-row">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
      </div>
      <b>Qty ${integer.format(deckQuantity(card))}</b>
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
    <article class="deck-card-row wishlist-shared-row">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
        <div class="deck-card-tags">${cardMetadataPillsHtml(card)}</div>
      </div>
      <b>${dollars.format(card.display_price || 0)}</b>
    </article>
  `).join("");
}

function renderSharedDeck(deck) {
  const cards = deck.cards || [];
  const cardCount = Number(deck.card_count || cards.reduce((total, card) => total + deckQuantity(card), 0));
  els.deckShareShell.innerHTML = `
    <section class="shared-deck-card">
      <div class="shared-deck-head">
        <div>
          <p class="eyebrow">Shared deck</p>
          <h2>${escapeHtml(deck.name || "Deck")}</h2>
          <span>${integer.format(cardCount)} cards</span>
        </div>
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

function renderSharedFavorites(payload) {
  const cards = payload.cards || [];
  els.favoritesShareShell.innerHTML = `
    <section class="shared-deck-card">
      <div class="shared-deck-head">
        <div>
          <p class="eyebrow">Shared favorites</p>
          <h2>Favorites</h2>
          <span>${integer.format(cards.length)} favorite cards</span>
        </div>
      </div>
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

async function loadSharedFavorites() {
  showPage("favorites-share");
  els.favoritesShareShell.innerHTML = '<div class="empty-state">Loading shared favorites...</div>';
  try {
    const payload = await api("/api/shared-favorites");
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

function wireEvents() {
  for (const command of els.navCommands) {
    command.addEventListener("click", () => {
      const page = command.dataset.pageTarget || "dashboard";
      activatePage(page, { push: true });
    });
  }
  window.addEventListener("popstate", () => {
    const routePage = appPageRoute();
    if (routePage) {
      activatePage(routePage);
      return;
    }
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
    const deckId = deckRouteId();
    if (deckId) {
      if (isPrivateDeckRoute(deckId) && state.user) {
        loadDeckEditor(deckId);
      } else if (isPrivateDeckRoute(deckId)) {
        activatePage("search", { replace: true, promptLogin: false });
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

  els.addCardButton.addEventListener("click", () => {
    if (!state.user) {
      openAuthModal("login", "Create an account or log in before adding cards.");
      return;
    }
    openAddCardModal();
  });
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
  els.addWishlistButton.addEventListener("click", openAddWishlistModal);
  els.addContainerButton.addEventListener("click", openAddContainerModal);
  els.closeAddPurchaseButton.addEventListener("click", closeAddPurchaseModal);
  els.cancelAddPurchaseButton.addEventListener("click", closeAddPurchaseModal);
  els.addPurchaseOverlay.addEventListener("click", (event) => {
    if (event.target === els.addPurchaseOverlay) {
      closeAddPurchaseModal();
    }
  });
  els.tileViewButton.addEventListener("click", () => setCollectionView("tiles"));
  els.listViewButton.addEventListener("click", () => setCollectionView("list"));
  els.favoriteTileViewButton.addEventListener("click", () => setFavoritesView("tiles"));
  els.favoriteListViewButton.addEventListener("click", () => setFavoritesView("list"));
  els.wishlistTileViewButton.addEventListener("click", () => setWishlistView("tiles"));
  els.wishlistListViewButton.addEventListener("click", () => setWishlistView("list"));
  els.shareFavoritesButton.addEventListener("click", openFavoritesShareModal);
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
  els.previewJsonImportButton.addEventListener("click", () => {
    previewImport("json").catch((error) => {
      els.importStatus.textContent = error.message;
    });
  });
  els.previewCsvImportButton.addEventListener("click", () => {
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
  els.closeAuthButton.addEventListener("click", closeAuthModal);
  els.toggleAuthModeButton.addEventListener("click", () => {
    setAuthMode(authMode() === "login" ? "register" : "login");
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
    searchOwnedCardsForDeck().catch((error) => {
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
  els.closeShareButton.addEventListener("click", closeShareModal);
  els.copyShareButton.addEventListener("click", copyShareUrl);
  els.shareOverlay.addEventListener("click", (event) => {
    if (event.target === els.shareOverlay) {
      closeShareModal();
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
    if (event.key === "Escape" && !els.settingsOverlay.hidden) {
      closeSettingsModal();
    }
    if (event.key === "Escape" && !els.authOverlay.hidden) {
      closeAuthModal();
    }
    if (event.key === "Escape" && !els.shareOverlay.hidden) {
      closeShareModal();
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
    if (event.key === "Escape" && !els.importReviewOverlay.hidden) {
      closeImportReviewModal();
    }
  });
  els.addSearchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    els.addSearchStatus.dataset.tone = "";
    searchScryfallForAdd();
  });
  els.addSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      els.addSearchStatus.dataset.tone = "";
      searchScryfallForAdd();
    }
  });
  els.addCardForm.variant.addEventListener("change", renderSelectedAddCard);
  els.addCardForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.selectedAddCard) {
      els.addSearchStatus.textContent = "Choose a card first.";
      return;
    }
    const payload = Object.fromEntries(new FormData(els.addCardForm).entries());
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
      setStatus(`Added ${addedCardTitle} (${result.variant}).`);
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
    } catch (error) {
      els.addSearchStatus.textContent = error.message;
      els.confirmAddCardButton.disabled = false;
      els.confirmAddNewCardButton.disabled = false;
    }
  });
  els.settingsForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.settingsForm).entries());
    saveSettings(payload);
    setStatus("Settings saved.");
    closeSettingsModal();
  });
  els.settingsPageForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.settingsPageForm).entries());
    try {
      await saveUserSettings(payload);
      setStatus("Settings saved.", "success", els.settingsPageStatus);
    } catch (error) {
      setStatus(error.message, "error", els.settingsPageStatus);
    }
  });
  els.clearDatabaseButton.addEventListener("click", async () => {
    const confirmed = window.confirm("Clear your FoilFolio database? This removes your collection, decks, containers, lists, sale listings, and card history, but keeps your account.");
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
    const confirmed = window.confirm("Delete your FoilFolio profile and all of your data? This cannot be undone.");
    if (!confirmed) return;
    const typed = window.prompt('Type "delete" to confirm profile deletion.');
    if ((typed || "").toLowerCase() !== "delete") return;
    try {
      await api("/api/user/profile", { method: "DELETE", body: JSON.stringify({}) });
      state.user = null;
      updateAuthUi();
      setStatus("Profile deleted.", "success");
      activatePage("search", { push: true });
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
      closeAddDeckModal();
      await loadDecks();
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
      container: "containers",
      wishlist: "wishlists",
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
      const statusTarget = type === "deck" ? els.decksStatus : type === "container" ? els.containersStatus : type === "wishlist" ? els.wishlistStatus : els.status;
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
      closeAddContainerModal();
      await loadContainers();
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
    if (!containerId) {
      setStatus("Create a container first.", "error", statusTarget);
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
        setStatus(`Sale quantity must be between 1 and ${integer.format(max)}.`, "error");
        return;
      }
      if (askingPrice <= 0) {
        setStatus("Asking price must be greater than $0.00.", "error");
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
      setStatus("Keep at least one checked card to mark for sale.", "error");
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
      await loadCards();
      await loadSaleCards();
    } catch (error) {
      setStatus(error.message, "error");
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
}

async function boot() {
  state.settings = loadSettings();
  applySettings();
  const initialSharedId = sharedRouteId();
  const initialSetCode = setRouteCode();
  const initialDeckRouteId = deckRouteId();
  const initialDeckEditorId = isPrivateDeckRoute(initialDeckRouteId) ? initialDeckRouteId : "";
  const initialDeckShareId = initialDeckRouteId && !initialDeckEditorId ? initialDeckRouteId : "";
  const initialWishlistShareId = wishlistRouteId();
  const initialContainerShareId = containerRouteId();
  const initialFavoritesShare = favoritesShareRoute();
  const initialCardDetail = cardDetailRoute();
  const initialVerificationToken = verificationRouteToken();
  const initialPasswordResetToken = passwordResetRouteToken();
  const initialAppPage = appPageRoute();
  const isAlwaysShareOnlyRoute = Boolean(initialDeckShareId || initialWishlistShareId || initialContainerShareId || initialFavoritesShare);
  await loadSession().catch(() => {
    state.user = null;
    updateAuthUi();
  });
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
      activatePage("search", { replace: true, promptLogin: false });
      openAuthModal("login", "Log in to edit this deck.");
    }
  } else if (initialWishlistShareId) {
    document.body.classList.add("share-only");
    loadSharedWishlist(initialWishlistShareId);
  } else if (initialContainerShareId) {
    document.body.classList.add("share-only");
    loadSharedContainer(initialContainerShareId);
  } else if (initialFavoritesShare) {
    document.body.classList.add("share-only");
    loadSharedFavorites();
  } else if (initialVerificationToken) {
    loadEmailVerification(initialVerificationToken);
  } else if (initialPasswordResetToken) {
    loadPasswordReset(initialPasswordResetToken);
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
      activatePage("search");
      openAuthModal("login", "Log in to view set progress.");
    }
  } else if (initialAppPage) {
    if (!state.user && protectedPage(initialAppPage)) {
      activatePage("search", { replace: true, promptLogin: false });
    } else {
      activatePage(initialAppPage);
    }
  } else {
    activatePage(state.user ? "dashboard" : "search", { replace: !state.user, promptLogin: false });
  }
}

boot().catch((error) => {
  setStatus(error.message, "error");
});
