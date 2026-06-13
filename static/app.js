const state = {
  cards: [],
  dashboard: null,
  searchTimer: null,
  editingCard: null,
  addResults: [],
  selectedAddCard: null,
  sharedCard: null,
  activeSet: null,
  setCards: [],
  decks: [],
  activeDeck: null,
  selectedCards: new Map(),
  collectionView: localStorage.getItem("fiolfolio.collectionView") || "tiles",
  settings: null,
};

const settingsKey = "fiolfolio.settings";

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

const els = {
  currentValue: document.querySelector("#currentValue"),
  paidTotal: document.querySelector("#paidTotal"),
  gainLoss: document.querySelector("#gainLoss"),
  ownedCards: document.querySelector("#ownedCards"),
  historyCount: document.querySelector("#historyCount"),
  historyChart: document.querySelector("#historyChart"),
  topCount: document.querySelector("#topCount"),
  topCards: document.querySelector("#topCards"),
  setCompletionCount: document.querySelector("#setCompletionCount"),
  setCompletion: document.querySelector("#setCompletion"),
  cardsGrid: document.querySelector("#cardsGrid"),
  status: document.querySelector("#status"),
  searchInput: document.querySelector("#searchInput"),
  ownedFilter: document.querySelector("#ownedFilter"),
  sortSelect: document.querySelector("#sortSelect"),
  tileViewButton: document.querySelector("#tileViewButton"),
  listViewButton: document.querySelector("#listViewButton"),
  collectionBulkBar: document.querySelector("#collectionBulkBar"),
  selectedCardsCount: document.querySelector("#selectedCardsCount"),
  addToDeckButton: document.querySelector("#addToDeckButton"),
  addCardButton: document.querySelector("#addCardButton"),
  importButton: document.querySelector("#importButton"),
  settingsButton: document.querySelector("#settingsButton"),
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
  confirmAddCardButton: document.querySelector("#confirmAddCardButton"),
  settingsOverlay: document.querySelector("#settingsOverlay"),
  settingsForm: document.querySelector("#settingsForm"),
  closeSettingsButton: document.querySelector("#closeSettingsButton"),
  cancelSettingsButton: document.querySelector("#cancelSettingsButton"),
  addDeckButton: document.querySelector("#addDeckButton"),
  addDeckOverlay: document.querySelector("#addDeckOverlay"),
  addDeckForm: document.querySelector("#addDeckForm"),
  closeAddDeckButton: document.querySelector("#closeAddDeckButton"),
  cancelAddDeckButton: document.querySelector("#cancelAddDeckButton"),
  decksGrid: document.querySelector("#decksGrid"),
  decksStatus: document.querySelector("#decksStatus"),
  assignDeckOverlay: document.querySelector("#assignDeckOverlay"),
  assignDeckForm: document.querySelector("#assignDeckForm"),
  closeAssignDeckButton: document.querySelector("#closeAssignDeckButton"),
  cancelAssignDeckButton: document.querySelector("#cancelAssignDeckButton"),
  deckDetailOverlay: document.querySelector("#deckDetailOverlay"),
  deckDetailTitle: document.querySelector("#deckDetailTitle"),
  deckDetailCards: document.querySelector("#deckDetailCards"),
  shareDeckButton: document.querySelector("#shareDeckButton"),
  deleteDeckButton: document.querySelector("#deleteDeckButton"),
  closeDeckDetailButton: document.querySelector("#closeDeckDetailButton"),
  deckShareShell: document.querySelector("#deckShareShell"),
  shareOverlay: document.querySelector("#shareOverlay"),
  shareTitle: document.querySelector("#shareTitle"),
  shareUrlInput: document.querySelector("#shareUrlInput"),
  copyShareButton: document.querySelector("#copyShareButton"),
  closeShareButton: document.querySelector("#closeShareButton"),
  sharedCardShell: document.querySelector("#sharedCardShell"),
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
}

function setStatus(message, tone = "") {
  els.status.textContent = message;
  els.status.dataset.tone = tone;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = payload && payload.error ? payload.error : `Request failed: ${response.status}`;
    throw new Error(message);
  }
  return payload;
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

function cardSelectionKey(card) {
  return `${card.scryfall_id}::${card.variant || "Normal"}`;
}

function updateBulkBar() {
  const count = state.selectedCards.size;
  els.collectionBulkBar.hidden = count === 0;
  els.selectedCardsCount.textContent = `${integer.format(count)} selected`;
}

function clearSelectedCards() {
  state.selectedCards.clear();
  for (const checkbox of els.cardsGrid.querySelectorAll(".select-card-checkbox")) {
    checkbox.checked = false;
  }
  updateBulkBar();
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
      });
    } else {
      state.selectedCards.delete(key);
    }
    updateBulkBar();
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
  localStorage.setItem("fiolfolio.collectionView", state.collectionView);
  els.tileViewButton.classList.toggle("is-active", state.collectionView === "tiles");
  els.listViewButton.classList.toggle("is-active", state.collectionView === "list");
  renderCollection();
}

function renderDashboard(data) {
  state.dashboard = data;
  els.currentValue.textContent = dollars.format(data.current_total || 0);
  els.paidTotal.textContent = dollars.format(data.paid_total || 0);
  els.gainLoss.textContent = `${dollars.format(data.gain_loss || 0)} (${(data.gain_loss_percent || 0).toFixed(1)}%)`;
  els.gainLoss.className = valueClass(data.gain_loss || 0);
  els.ownedCards.textContent = `${integer.format(data.owned_cards || 0)} cards`;
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
    item.href = card.scryfall_uri || "#";
    item.target = "_blank";
    item.rel = "noreferrer";
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
  for (const command of els.navCommands) {
    command.classList.toggle("is-active", command.dataset.pageTarget === pageName);
  }
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
    owned: els.ownedFilter.value,
    sort: els.sortSelect.value,
    limit: "250",
  });
  return params.toString();
}

async function loadCards() {
  const data = await api(`/api/cards?${cardQuery()}`);
  state.cards = data.cards || [];
  renderCollection();
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

function renderCards(cards, target = els.cardsGrid, options = {}) {
  target.innerHTML = "";
  if (!cards.length) {
    target.innerHTML = '<div class="empty-state">No cards match the current filters.</div>';
    if (target === els.cardsGrid) updateBulkBar();
    return;
  }
  for (const card of cards) {
    const owned = Number(card.quantity || 0) > 0;
    const node = els.template.content.firstElementChild.cloneNode(true);
    const selectWrap = node.querySelector(".select-card-wrap");
    const selectCheckbox = node.querySelector(".select-card-checkbox");
    const link = node.querySelector(".card-art");
    const img = node.querySelector("img");
    const title = node.querySelector("h3");
    const variantBadge = node.querySelector(".variant-badge");
    const meta = node.querySelector(".card-meta");
    const type = node.querySelector(".card-type");
    const ownedValue = node.querySelector(".owned-value");
    const price = node.querySelector(".price");
    const delta = node.querySelector(".delta");
    const favoriteButton = node.querySelector(".favorite-button");
    const editButton = node.querySelector(".edit-button");
    const shareButton = node.querySelector(".share-button");
    const detailQuantity = node.querySelector(".detail-quantity");
    const detailPaid = node.querySelector(".detail-paid");
    const detailDate = node.querySelector(".detail-date");
    const detailVariant = node.querySelector(".detail-variant");

    link.href = card.scryfall_uri || "#";
    img.src = card.image_normal || card.image_small || "";
    img.alt = cardTitle(card);
    title.textContent = cardTitle(card);
    meta.textContent = `${card.set_name} #${card.collector_number} - ${card.rarity || "unknown"}${cardRulesName(card) ? ` - Rules: ${cardRulesName(card)}` : ""}`;
    type.textContent = card.type_line || "";
    variantBadge.textContent = card.variant || "Normal";
    node.classList.toggle("is-special", isSpecialVariant(card.variant));
    node.classList.toggle("is-missing", !owned);
    ownedValue.textContent = dollars.format(card.owned_value || 0);
    price.textContent = `Now ${dollars.format(card.display_price || 0)}`;
    delta.textContent = `Delta ${dollars.format(card.gain_loss || 0)}`;
    delta.className = `delta ${valueClass(card.gain_loss || 0)}`;
    detailQuantity.textContent = integer.format(card.quantity || 0);
    detailPaid.textContent = dollars.format(card.paid_price || 0.01);
    detailDate.textContent = formatDate(card.acquired_date);
    detailVariant.textContent = card.variant || "Normal";

    wireCardSelection(selectWrap, selectCheckbox, card, options);

    favoriteButton.classList.toggle("is-favorite", Boolean(card.favorite));
    favoriteButton.setAttribute("aria-pressed", card.favorite ? "true" : "false");
    favoriteButton.title = card.favorite ? "Remove favorite" : "Favorite";
    favoriteButton.addEventListener("click", async () => {
      const nextFavorite = !Boolean(card.favorite);
      try {
        await api(`/api/cards/${encodeURIComponent(card.scryfall_id)}/favorite`, {
          method: "POST",
          body: JSON.stringify({
            variant: card.variant || "Normal",
            favorite: nextFavorite,
          }),
        });
        setStatus(nextFavorite ? `Favorited ${cardTitle(card)}.` : `Removed favorite from ${cardTitle(card)}.`);
        await refresh();
      } catch (error) {
        setStatus(error.message, "error");
      }
    });
    editButton.addEventListener("click", () => openEditModal(card));
    wireShareButton(shareButton, card);

    target.appendChild(node);
  }
  if (target === els.cardsGrid) updateBulkBar();
}

function renderCardList(cards, target = els.cardsGrid, options = {}) {
  target.innerHTML = "";
  if (!cards.length) {
    target.innerHTML = '<div class="empty-state">No cards match the current filters.</div>';
    if (target === els.cardsGrid) updateBulkBar();
    return;
  }
  for (const card of cards) {
    const owned = Number(card.quantity || 0) > 0;
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
    const shareButton = node.querySelector(".share-button");
    const deleteButton = node.querySelector(".delete-card-button");

    node.classList.toggle("is-special", isSpecialVariant(card.variant));
    node.classList.toggle("is-missing", !owned);
    link.href = card.scryfall_uri || "#";
    img.src = card.image_normal || card.image_small || "";
    img.alt = cardTitle(card);
    title.textContent = cardTitle(card);
    meta.textContent = `${card.set_name} #${card.collector_number} - ${card.rarity || "unknown"}${cardRulesName(card) ? ` - Rules: ${cardRulesName(card)}` : ""}`;
    type.textContent = card.type_line || "";
    price.textContent = `Now ${dollars.format(card.display_price || 0)}`;
    ownedValue.textContent = `Value ${dollars.format(card.owned_value || 0)}`;
    quantity.textContent = `Qty ${integer.format(card.quantity || 0)}`;
    variant.textContent = card.variant || "Normal";

    wireCardSelection(selectWrap, selectCheckbox, card, options);
    wireShareButton(shareButton, card);
    wireDeleteCardButton(deleteButton, card);

    target.appendChild(node);
  }
  if (target === els.cardsGrid) updateBulkBar();
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
  els.editForm.card_condition.value = card.card_condition || "";
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
  if (!card || !card.share_id) return "";
  return new URL(`/cards/${encodeURIComponent(card.share_id)}`, window.location.origin).toString();
}

function shareUrlForDeck(deck) {
  if (!deck || !deck.share_id) return "";
  return new URL(`/decks/${encodeURIComponent(deck.share_id)}`, window.location.origin).toString();
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
    setStatus("This collection entry does not have a share link yet.", "error");
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

function openAddCardModal() {
  state.addResults = [];
  state.selectedAddCard = null;
  els.addSearchForm.reset();
  els.addCardForm.reset();
  els.addCardForm.scryfall_id.value = "";
  els.addCardForm.quantity.value = "1";
  els.addCardForm.paid_price.value = "0.01";
  els.addCardForm.acquired_date.value = todayValue();
  els.addCardForm.variant.innerHTML = "<option>Normal</option>";
  els.addSearchStatus.textContent = "";
  els.addSearchResults.innerHTML = "";
  els.selectedAddCard.hidden = true;
  els.selectedAddCard.innerHTML = "";
  els.confirmAddCardButton.disabled = true;
  els.addCardOverlay.hidden = false;
  document.body.classList.add("modal-open");
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
      <span>cards assigned</span>
    `;
    item.addEventListener("click", () => {
      openDeckDetailModal(deck.id).catch((error) => {
        els.decksStatus.textContent = error.message;
      });
    });
    els.decksGrid.appendChild(item);
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
      </div>
      <b>Qty ${integer.format(card.quantity || 0)}</b>
      ${readonly ? "" : '<button class="remove-deck-card-button" type="button" aria-label="Remove card from deck" title="Remove card">x</button>'}
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
  els.deckDetailOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  state.activeDeck = null;
  els.deckDetailCards.innerHTML = "";
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
  renderDeckDetail(deck);
  await loadDecks();
}

async function deleteActiveDeck() {
  if (!state.activeDeck) return;
  const confirmed = window.confirm(`Delete deck "${state.activeDeck.name}"? This only removes the deck metadata.`);
  if (!confirmed) return;
  const deckName = state.activeDeck.name;
  await api(`/api/decks/${encodeURIComponent(state.activeDeck.id)}`, { method: "DELETE" });
  closeDeckDetailModal();
  els.decksStatus.textContent = `Deleted ${deckName}.`;
  await loadDecks();
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
  els.assignDeckOverlay.hidden = false;
  document.body.classList.add("modal-open");
  select.focus();
}

function closeAssignDeckModal() {
  els.assignDeckOverlay.hidden = true;
  document.body.classList.remove("modal-open");
  els.assignDeckForm.reset();
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
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
        <p class="eyebrow">Shared from Fiolfolio</p>
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
            <dt>Owned</dt>
            <dd>${integer.format(card.quantity || 0)}</dd>
          </div>
          <div>
            <dt>Date Added</dt>
            <dd>${escapeHtml(formatDate(card.acquired_date))}</dd>
          </div>
          <div>
            <dt>Current Value</dt>
            <dd>${dollars.format(card.display_price || 0)}</dd>
          </div>
        </dl>
      </div>
    </article>
  `;
}

async function loadSharedCard(shareId) {
  showPage("shared");
  els.sharedCardShell.innerHTML = '<div class="empty-state">Loading shared card...</div>';
  try {
    const card = await api(`/api/shared/${encodeURIComponent(shareId)}`);
    renderSharedCard(card);
  } catch (error) {
    els.sharedCardShell.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function renderSetPage(setDetail, cards) {
  state.activeSet = setDetail;
  state.setCards = cards;
  const percent = Math.max(0, Math.min(100, Number(setDetail.completion_percent || 0)));
  els.setPageShell.innerHTML = `
    <section class="set-hero">
      <div>
        <p class="eyebrow">Set completion</p>
        <h2>${escapeHtml(setDetail.set_name || setDetail.set_code)}</h2>
        <span>${integer.format(setDetail.owned_cards || 0)} / ${integer.format(setDetail.total_cards || 0)} unique prints</span>
      </div>
      <b>${percent.toFixed(1)}%</b>
      <div class="set-progress set-progress-large" aria-label="${percent.toFixed(1)} percent complete">
        <span style="width: ${percent}%"></span>
      </div>
    </section>
    <div id="setCardsGrid" class="cards-grid set-cards-grid"></div>
  `;
  renderCards(cards, els.setPageShell.querySelector("#setCardsGrid"));
}

function deckRowsHtml(cards) {
  if (!cards.length) {
    return '<div class="empty-state">No cards in this deck yet.</div>';
  }
  return cards.map((card) => `
    <article class="deck-card-row">
      <img src="${escapeHtml(card.image_small || card.image_normal || "")}" alt="">
      <div>
        <strong>${escapeHtml(cardTitle(card))}</strong>
        <span>${escapeHtml(card.set_name || "")} #${escapeHtml(card.collector_number || "")} - ${escapeHtml(card.variant || "Normal")}</span>
      </div>
      <b>Qty ${integer.format(card.quantity || 0)}</b>
    </article>
  `).join("");
}

function renderSharedDeck(deck) {
  const cards = deck.cards || [];
  els.deckShareShell.innerHTML = `
    <section class="shared-deck-card">
      <div class="shared-deck-head">
        <div>
          <p class="eyebrow">Shared deck</p>
          <h2>${escapeHtml(deck.name || "Deck")}</h2>
          <span>${integer.format(cards.length)} cards</span>
        </div>
      </div>
      <div class="deck-detail-list">
        ${deckRowsHtml(cards)}
      </div>
    </section>
  `;
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
      if (sharedRouteId() || setRouteCode() || deckRouteId()) {
        window.history.pushState({}, "", "/");
      }
      const page = command.dataset.pageTarget || "dashboard";
      showPage(page);
      if (page === "decks") {
        loadDecks().catch((error) => {
          els.decksStatus.textContent = error.message;
        });
      }
    });
  }

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

  els.addCardButton.addEventListener("click", openAddCardModal);
  els.settingsButton.addEventListener("click", openSettingsModal);
  els.addDeckButton.addEventListener("click", openAddDeckModal);
  els.tileViewButton.addEventListener("click", () => setCollectionView("tiles"));
  els.listViewButton.addEventListener("click", () => setCollectionView("list"));
  els.addToDeckButton.addEventListener("click", () => {
    openAssignDeckModal().catch((error) => setStatus(error.message, "error"));
  });

  els.importButton.addEventListener("click", async () => {
    setStatus("Importing collection CSV...");
    els.importButton.disabled = true;
    try {
      const result = await api("/api/import", { method: "POST", body: "{}" });
      const missed = (result.unmatched_rows || []).length;
      setStatus(`Imported ${integer.format(result.imported_rows || 0)} rows. ${integer.format(missed)} unmatched.`);
      await refresh();
    } catch (error) {
      setStatus(error.message, "error");
    } finally {
      els.importButton.disabled = false;
    }
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
  els.closeAddDeckButton.addEventListener("click", closeAddDeckModal);
  els.cancelAddDeckButton.addEventListener("click", closeAddDeckModal);
  els.addDeckOverlay.addEventListener("click", (event) => {
    if (event.target === els.addDeckOverlay) {
      closeAddDeckModal();
    }
  });
  els.closeAssignDeckButton.addEventListener("click", closeAssignDeckModal);
  els.cancelAssignDeckButton.addEventListener("click", closeAssignDeckModal);
  els.assignDeckOverlay.addEventListener("click", (event) => {
    if (event.target === els.assignDeckOverlay) {
      closeAssignDeckModal();
    }
  });
  els.closeDeckDetailButton.addEventListener("click", closeDeckDetailModal);
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
  els.closeShareButton.addEventListener("click", closeShareModal);
  els.copyShareButton.addEventListener("click", copyShareUrl);
  els.shareOverlay.addEventListener("click", (event) => {
    if (event.target === els.shareOverlay) {
      closeShareModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !els.editOverlay.hidden) {
      closeEditModal();
    }
    if (event.key === "Escape" && !els.addCardOverlay.hidden) {
      closeAddCardModal();
    }
    if (event.key === "Escape" && !els.settingsOverlay.hidden) {
      closeSettingsModal();
    }
    if (event.key === "Escape" && !els.shareOverlay.hidden) {
      closeShareModal();
    }
    if (event.key === "Escape" && !els.addDeckOverlay.hidden) {
      closeAddDeckModal();
    }
    if (event.key === "Escape" && !els.assignDeckOverlay.hidden) {
      closeAssignDeckModal();
    }
    if (event.key === "Escape" && !els.deckDetailOverlay.hidden) {
      closeDeckDetailModal();
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
    els.confirmAddCardButton.disabled = true;
    try {
      const result = await api("/api/cards", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setStatus(`Added ${cardTitle(state.selectedAddCard)} (${result.variant}).`);
      closeAddCardModal();
      await refresh();
    } catch (error) {
      els.addSearchStatus.textContent = error.message;
      els.confirmAddCardButton.disabled = false;
    }
  });
  els.settingsForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(els.settingsForm).entries());
    saveSettings(payload);
    setStatus("Settings saved.");
    closeSettingsModal();
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
  els.assignDeckForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const deckId = els.assignDeckForm.deck_id.value;
    if (!deckId) {
      setStatus("Create a deck first.", "error");
      return;
    }
    const cards = Array.from(state.selectedCards.values()).map((card) => ({
      card_id: card.card_id,
      variant: card.variant,
    }));
    try {
      const result = await api(`/api/decks/${encodeURIComponent(deckId)}/cards`, {
        method: "POST",
        body: JSON.stringify({ cards }),
      });
      setStatus(`Added ${integer.format(result.added || 0)} card${result.added === 1 ? "" : "s"} to deck.`);
      closeAssignDeckModal();
      clearSelectedCards();
      await loadDecks();
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
      closeEditModal();
      await refresh();
    } catch (error) {
      setStatus(error.message, "error");
    }
  });
}

state.settings = loadSettings();
applySettings();
const initialSharedId = sharedRouteId();
const initialSetCode = setRouteCode();
const initialDeckShareId = deckRouteId();
const isShareOnlyRoute = Boolean(initialSharedId || initialDeckShareId);
if (!isShareOnlyRoute) {
  wireEvents();
}
if (initialSharedId) {
  document.body.classList.add("share-only");
  loadSharedCard(initialSharedId);
} else if (initialDeckShareId) {
  document.body.classList.add("share-only");
  loadSharedDeck(initialDeckShareId);
} else if (initialSetCode) {
  loadSetPage(initialSetCode);
  refresh().catch((error) => {
    setStatus(error.message, "error");
    renderCollection();
  });
} else {
  refresh().catch((error) => {
    setStatus(error.message, "error");
    renderCollection();
  });
}
