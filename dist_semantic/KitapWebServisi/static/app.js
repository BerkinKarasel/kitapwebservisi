const defaultTexts = {
  pageTitle: "Kitap Web Servisi",
  heroEyebrow: "Yerel Web Servisi",
  heroTitle: "Kitap bilgilerini daha zengin bir sonucla goruntuleyin.",
  heroLead: "ISBN, yazar, tur veya kitap adina gore sorgu yapin; sonuclari kapak gorseli, meta bilgiler ve kart duzeni ile ekranda inceleyin.",
  heroStatLabel: "Canli Sonuc",
  heroStatText: "Arayuz ve API ayni veritabanini kullanir.",
  semanticEyebrow: "Semantic Katman",
  semanticTitle: "Bu servis semantic web uyumlu calisir.",
  semanticLead: "Kitap verileri JSON-LD, Turtle, ontology ve mini SPARQL destekli semantic servislerle sunulur.",
  semanticFeatureOne: "JSON-LD Cikti",
  semanticFeatureTwo: "Turtle Destegi",
  semanticFeatureThree: "Mini SPARQL",
  semanticFeatureFour: "Ontology Endpoint",
  serviceModeEyebrow: "Servis Modu",
  serviceModeTitle: "Sonuclari hangi servis katmanindan getirelim?",
  classicModeButton: "Klasik Servis",
  semanticModeButton: "Semantic Servis",
  resultCountDefault: "0 kitap",
  apiTitle: "Hazir API Uclari",
  loadAllButton: "Tum Kitaplari Getir",
  formIsbnTitle: "Kitap Bul",
  formIsbnLabel: "ISBN",
  formIsbnPlaceholder: "9780060853983",
  formIsbnButton: "ISBN ile Sorgula",
  formAuthorTitle: "Yazara Gore Kitaplar",
  formAuthorLabel: "Yazar Adi Soyadi",
  formAuthorPlaceholder: "Yazar Adi Giriniz",
  formAuthorButton: "Yazari Ara",
  formGenreTitle: "Ture Gore Liste",
  formGenreLabel: "Tur",
  formGenrePlaceholder: "Tur Giriniz",
  formGenreButton: "Turu Listele",
  formPublisherTitle: "Kitabin Basimevi",
  formPublisherLabel: "Kitap Adi",
  formPublisherPlaceholder: "Tutunamayanlar",
  formPublisherButton: "Basimevini Bul",
  resultsTitle: "Sonuclar",
  resultsSubtitleDefault: "Bir sorgu calistirdiginizda kitaplar burada kart olarak gosterilecek.",
  clearButton: "Temizle",
  emptyBadge: "Hazir",
  emptyTitle: "Aramaya baslayin",
  emptyText: "Bir sorgu secin, sonuc ekraninda kitap kapaklari ve detaylarini gorelim.",
  summaryChip: "Ozet",
  summaryMany: "{count} kitap bulundu",
  summarySingle: "1 kitap bulundu",
  subtitleAuthor: "Yazar filtresi: {value}",
  subtitleGenre: "Tur filtresi: {value}",
  subtitleSelectedBook: "Secilen kitap: {value}",
  subtitleAllBooks: "Tum kitaplar listelendi.",
  subtitleNoResult: "Sonuc bulunamadi.",
  emptyResultBadge: "Bos Sonuc",
  emptyResultTitle: "Eslesen kitap bulunamadi",
  emptyResultText: "Farkli bir ISBN, yazar, tur veya kitap adi ile tekrar deneyin.",
  errorSubtitle: "Sorgu tamamlanamadi.",
  errorTitle: "Sonuc alinamadi",
  errorDefault: "Beklenmeyen bir hata olustu.",
  loadingSubtitle: "Servisten veri aliniyor...",
  loadingBadge: "Yukleniyor",
  loadingTitle: "Sorgu calisiyor",
  validationMessage: "Lutfen alani doldurun.",
  badgeError: "Hata {status}",
  isbnLabel: "ISBN",
  publisherLabel: "Basimevi",
  publishYearLabel: "Basim Yili"
};

let texts = { ...defaultTexts };
const GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes";
let lastListPayload = null;
let currentServiceMode = "classic";

const resultElement = document.getElementById("result");
const resultCountElement = document.getElementById("resultCount");
const resultSubtitleElement = document.getElementById("resultSubtitle");
const clearButton = document.getElementById("clearButton");
const loadAllButton = document.getElementById("loadAllButton");
const classicModeButton = document.getElementById("classicModeButton");
const semanticModeButton = document.getElementById("semanticModeButton");
const forms = document.querySelectorAll("form[data-endpoint]");

function t(key, replacements = {}) {
  let value = texts[key] ?? defaultTexts[key] ?? key;
  Object.entries(replacements).forEach(([name, replacement]) => {
    value = value.replace(`{${name}}`, replacement);
  });
  return value;
}

function coverCacheKey(book) {
  return `book-cover:${book.isbn}`;
}

function normalizeCoverUrl(url) {
  if (!url) {
    return "";
  }
  return url.replace("http://", "https://");
}

function getCachedCover(book) {
  try {
    return localStorage.getItem(coverCacheKey(book)) || "";
  } catch {
    return "";
  }
}

function setCachedCover(book, url) {
  if (!url) {
    return;
  }

  try {
    localStorage.setItem(coverCacheKey(book), url);
  } catch {
    // Ignore storage failures and continue with runtime image loading.
  }
}

async function fetchGoogleBooksCover(book, query) {
  const response = await fetch(
    `${GOOGLE_BOOKS_API}?q=${encodeURIComponent(query)}&maxResults=1&printType=books`,
  );

  if (!response.ok) {
    return "";
  }

  const payload = await response.json();
  const volume = payload.items?.[0]?.volumeInfo;
  const imageLinks = volume?.imageLinks;
  const url =
    imageLinks?.extraLarge ||
    imageLinks?.large ||
    imageLinks?.medium ||
    imageLinks?.small ||
    imageLinks?.thumbnail ||
    imageLinks?.smallThumbnail ||
    "";

  const normalized = normalizeCoverUrl(url);
  if (normalized) {
    setCachedCover(book, normalized);
  }
  return normalized;
}

async function resolveCoverUrl(book) {
  if (book.cover_url && book.cover_url !== "/covers/default.svg") {
    return "";
  }

  const cached = getCachedCover(book);
  if (cached) {
    return cached;
  }

  try {
    const byIsbn = await fetchGoogleBooksCover(book, `isbn:${book.isbn}`);
    if (byIsbn) {
      return byIsbn;
    }

    const firstAuthor = book.authors?.[0] || "";
    const byTitle = await fetchGoogleBooksCover(
      book,
      `intitle:${book.title} inauthor:${firstAuthor}`,
    );
    if (byTitle) {
      return byTitle;
    }
  } catch {
    return "";
  }

  return "";
}

async function hydrateVisibleCovers(books) {
  await Promise.all(
    books.map(async (book) => {
      const image = resultElement.querySelector(`img[data-isbn="${book.isbn}"]`);
      if (!image) {
        return;
      }

      const realCover = await resolveCoverUrl(book);
      if (realCover) {
        image.src = realCover;
      }
    }),
  );
}

function applyStaticTexts() {
  document.querySelectorAll("[data-text]").forEach((element) => {
    element.textContent = t(element.dataset.text);
  });

  document.querySelectorAll("[data-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.placeholder);
  });

  document.title = t("pageTitle");
}

function normalizeSemanticBook(node) {
  if (!node) {
    return null;
  }

  const authors = Array.isArray(node.author)
    ? node.author.map((author) => author?.name || author).filter(Boolean)
    : [];

  const publisher =
    typeof node.publisher === "object" && node.publisher !== null
      ? node.publisher.name || ""
      : node.publisher || "";

  let coverUrl = node.image || "/covers/default.svg";
  if (typeof coverUrl === "string" && coverUrl.startsWith("http://127.0.0.1:8000")) {
    coverUrl = coverUrl.replace("http://127.0.0.1:8000", "");
  }

  return {
    title: node.name || "",
    isbn: node.isbn || "",
    genre: node.genre || "",
    publisher,
    publish_year: Number.parseInt(node.datePublished, 10) || "",
    cover_url: coverUrl,
    description: node.description || "",
    authors,
  };
}

function normalizePayload(payload) {
  if (payload?.["@type"] === "Collection" && Array.isArray(payload.hasPart)) {
    const books = payload.hasPart.map(normalizeSemanticBook).filter(Boolean);
    return {
      books,
      summary: t("summaryMany", { count: String(books.length) }),
      subtitle: payload.description || t("subtitleAllBooks"),
    };
  }

  if (payload?.["@type"] === "Book" || (payload?.isbn && payload?.name)) {
    const book = normalizeSemanticBook(payload);
    return {
      books: book ? [book] : [],
      summary: t("summarySingle"),
      subtitle: t("subtitleSelectedBook", { value: book?.title || payload.name || "" }),
    };
  }

  if (payload?.books) {
    return {
      books: payload.books,
      summary: t("summaryMany", { count: String(payload.count) }),
      subtitle: payload.author
        ? t("subtitleAuthor", { value: payload.author })
        : payload.genre
          ? t("subtitleGenre", { value: payload.genre })
          : t("subtitleAllBooks"),
    };
  }

  if (payload?.title && payload?.isbn) {
    return {
      books: [payload],
      summary: t("summarySingle"),
      subtitle: t("subtitleSelectedBook", { value: payload.title }),
    };
  }

  return {
    books: [],
    summary: t("resultCountDefault"),
    subtitle: t("subtitleNoResult"),
  };
}

function getServiceMode() {
  return currentServiceMode;
}

function updateServiceModeButtons() {
  classicModeButton?.classList.toggle("is-active", getServiceMode() === "classic");
  semanticModeButton?.classList.toggle("is-active", getServiceMode() === "semantic");
}

function setServiceMode(mode) {
  currentServiceMode = mode === "semantic" ? "semantic" : "classic";
  updateServiceModeButtons();
}

function buildRequestUrl(field, value) {
  const mode = getServiceMode();
  const encodedValue = encodeURIComponent(value);

  if (mode === "semantic") {
    if (field === "isbn") {
      return `/semantic/books/by-isbn?isbn=${encodedValue}`;
    }
    if (field === "author") {
      return `/semantic/books/by-author?author=${encodedValue}`;
    }
    if (field === "genre") {
      return `/semantic/books/by-genre?genre=${encodedValue}`;
    }
    return `/semantic/books`;
  }

  if (field === "isbn") {
    return `/api/books/by-isbn?isbn=${encodedValue}`;
  }
  if (field === "author") {
    return `/api/books/by-author?author=${encodedValue}`;
  }
  if (field === "genre") {
    return `/api/books/by-genre?genre=${encodedValue}`;
  }
  return "/api/books";
}

function bookCard(book) {
  return `
    <article class="book-card" data-book-isbn="${book.isbn}" tabindex="0" role="button">
      <img
        class="book-cover"
        src="${book.cover_url}"
        alt="${book.title} kapak gorseli"
        loading="lazy"
        referrerpolicy="no-referrer"
        data-isbn="${book.isbn}"
        onerror="this.src='/covers/default.svg'">
      <div class="book-body">
        <span class="book-badge">${book.genre}</span>
        <h3>${book.title}</h3>
        <p class="book-authors">${book.authors.join(", ")}</p>
        <div class="book-meta">
          <span>${t("isbnLabel")}: ${book.isbn}</span>
          <span>${t("publisherLabel")}: ${book.publisher}</span>
          <span>${t("publishYearLabel")}: ${book.publish_year}</span>
        </div>
      </div>
    </article>
  `;
}

function renderInitialState() {
  resultCountElement.textContent = t("resultCountDefault");
  resultSubtitleElement.textContent = t("resultsSubtitleDefault");
  resultElement.className = "result-grid empty-state";
  resultElement.innerHTML = `
    <article class="empty-card">
      <span class="empty-badge">${t("emptyBadge")}</span>
      <h3>${t("emptyTitle")}</h3>
      <p>${t("emptyText")}</p>
    </article>
  `;
}

function renderBooks(payload) {
  const normalized = normalizePayload(payload);
  resultCountElement.textContent = `${normalized.books.length} kitap`;
  resultSubtitleElement.textContent = normalized.subtitle;

  if (normalized.books.length !== 1) {
    lastListPayload = payload;
  }

  if (!normalized.books.length) {
    resultElement.className = "result-grid empty-state";
    resultElement.innerHTML = `
      <article class="empty-card">
        <span class="empty-badge">${t("emptyResultBadge")}</span>
        <h3>${t("emptyResultTitle")}</h3>
        <p>${t("emptyResultText")}</p>
      </article>
    `;
    return;
  }

  resultElement.className = "result-grid";
  const featuredBook = normalized.books[0];
  const backButton =
    normalized.books.length === 1 && lastListPayload
      ? `
        <button type="button" class="ghost back-button" data-action="go-back">
          ${t("backButton")}
        </button>
      `
      : "";
  const descriptionBlock =
    normalized.books.length === 1 && featuredBook?.description
      ? `
        <div class="summary-description">
          <span class="meta-chip">${t("descriptionChip")}</span>
          <p>${featuredBook.description}</p>
        </div>
      `
      : "";

  resultElement.innerHTML = `
    <section class="result-highlight">
      <article class="meta-card">
        <span class="meta-chip">${t("summaryChip")}</span>
        ${backButton}
        <strong>${normalized.summary}</strong>
        <p>${normalized.subtitle}</p>
        ${descriptionBlock}
      </article>
    </section>
    ${normalized.books.map(bookCard).join("")}
  `;

  void hydrateVisibleCovers(normalized.books);
}

function renderError(payload, status) {
  resultCountElement.textContent = t("resultCountDefault");
  resultSubtitleElement.textContent = t("errorSubtitle");
  resultElement.className = "result-grid empty-state";
  resultElement.innerHTML = `
    <article class="error-card">
      <span class="empty-badge">${t("badgeError", { status: String(status) })}</span>
      <h3>${t("errorTitle")}</h3>
      <p>${payload.error || t("errorDefault")}</p>
    </article>
  `;
}

function renderLoading(url) {
  resultSubtitleElement.textContent = t("loadingSubtitle");
  resultElement.className = "result-grid empty-state";
  resultElement.innerHTML = `
    <article class="loading-card">
      <span class="empty-badge">${t("loadingBadge")}</span>
      <h3>${t("loadingTitle")}</h3>
      <p>${url}</p>
    </article>
  `;
}

async function requestJson(url) {
  renderLoading(url);
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    renderError(data, response.status);
    return;
  }
  renderBooks(data);
}

async function loadTexts() {
  try {
    const response = await fetch("/texts.json", { cache: "no-store" });
    if (!response.ok) {
      return;
    }
    const customTexts = await response.json();
    texts = { ...defaultTexts, ...customTexts };
  } catch {
    texts = { ...defaultTexts };
  }
}

forms.forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const field = form.dataset.field;
    const value = new FormData(form).get(field)?.toString().trim();
    if (!value) {
      renderError({ error: t("validationMessage") }, 400);
      return;
    }
    const url = buildRequestUrl(field, value);
    await requestJson(url);
  });
});

loadAllButton.addEventListener("click", async () => {
  await requestJson(getServiceMode() === "semantic" ? "/semantic/books" : "/api/books");
});

classicModeButton?.addEventListener("click", () => {
  setServiceMode("classic");
});

semanticModeButton?.addEventListener("click", () => {
  setServiceMode("semantic");
});

resultElement.addEventListener("click", async (event) => {
  const backButton = event.target.closest('[data-action="go-back"]');
  if (backButton) {
    if (lastListPayload) {
      renderBooks(lastListPayload);
    }
    return;
  }

  const bookCardElement = event.target.closest(".book-card[data-book-isbn]");
  if (!bookCardElement) {
    return;
  }

  const isbn = bookCardElement.dataset.bookIsbn;
  await requestJson(buildRequestUrl("isbn", isbn));
});

resultElement.addEventListener("keydown", async (event) => {
  if (event.key !== "Enter" && event.key !== " ") {
    return;
  }

  const bookCardElement = event.target.closest(".book-card[data-book-isbn]");
  if (!bookCardElement) {
    return;
  }

  event.preventDefault();
  const isbn = bookCardElement.dataset.bookIsbn;
  await requestJson(buildRequestUrl("isbn", isbn));
});

clearButton.addEventListener("click", () => {
  renderInitialState();
});

async function initializePage() {
  await loadTexts();
  applyStaticTexts();
  updateServiceModeButtons();
  renderInitialState();
}

initializePage();
