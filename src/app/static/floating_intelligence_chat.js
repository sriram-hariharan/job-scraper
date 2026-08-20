(function () {
  "use strict";


  const FLOATING_CHAT_CLASS_NAMES = {
    message: "floating-intelligence-chat-message",
    userMessage: "floating-intelligence-chat-message--user",
    assistantMessage: "floating-intelligence-chat-message--assistant",
    errorMessage: "floating-intelligence-chat-message--error",
    bubble: "floating-intelligence-chat-bubble",
    card: "floating-intelligence-chat-card",
    cardMeta: "floating-intelligence-chat-card-meta",
  };

  const OPENING_ASSISTANT_GREETING = (
    "I can help you search the current job corpus, compare roles, inspect requirements, "
    + "and identify useful skills — with grounded answers from available job postings."
  );

  const SUGGESTED_PROMPT_ICONS = {
    search: '<path d="M10.5 4.5a6 6 0 1 1 0 12 6 6 0 0 1 0-12zM14.8 14.8 19.5 19.5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>',
    compare: '<path d="M6 5v14M18 5v14M6 9h12M6 15h12" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>',
    skills: '<path d="M5 18l4-7 3.5 4L19 6" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>',
    postings: '<path d="M6 4.5h9l3.5 3.5v11.5H6z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/><path d="M9 12h6M9 15.5h4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>',
  };

  const SUGGESTED_PROMPTS = [
    {
      icon: "search",
      accent: "blue",
      title: "Backend engineering roles",
      hint: "Search the current corpus",
      request: "Show backend engineering roles",
    },
    {
      icon: "postings",
      accent: "violet",
      title: "Data engineering roles",
      hint: "Search the current corpus",
      request: "Show data engineering roles",
    },
    {
      icon: "skills",
      accent: "amber",
      title: "Postings mentioning AWS",
      hint: "Search by technology",
      request: "Show postings that mention AWS",
    },
    {
      icon: "compare",
      accent: "teal",
      title: "Compare Java and Python",
      hint: "Grounded answer with sources",
      request: "Compare Java and Python requirements in available postings",
    },
  ];

  // The backend returns HTTP 200 with insufficient_evidence=true for genuine
  // "no matching jobs" answers AND for provider/runtime failures. These markers
  // come from src/rag/rag_answerer.py answer strings and let the UI tell them
  // apart without changing any backend behavior.
  const ANSWER_FAILURE_MARKERS = [
    { marker: "grounded answer generation failed", kind: "provider" },
    { marker: "the LLM timed out", kind: "runtime" },
    { marker: "retrieval failed", kind: "runtime" },
  ];

  const ANSWER_FAILURE_COPY = {
    provider: {
      title: "AI answer temporarily unavailable",
      body: "The configured AI provider or model could not complete this request. "
        + "Try again or check your AI settings.",
    },
    runtime: {
      title: "Answer could not be generated",
      body: "Something went wrong while generating this answer. Try again in a moment.",
    },
  };

  const SCROLL_PIN_THRESHOLD_PX = 80;
  const COMPOSER_MAX_HEIGHT_PX = 132;

  function qs(id) {
    return document.getElementById(id);
  }

  function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function extractErrorMessage(err) {
    let message = err?.message || String(err || "Unknown error");

    const httpMatch = message.match(/^HTTP \d+:\s*(.*)$/s);
    if (httpMatch) {
      message = httpMatch[1];
    }

    try {
      const parsed = JSON.parse(message);
      if (Array.isArray(parsed.detail)) {
        message = parsed.detail
          .map((item) => {
            if (item && item.msg && item.input !== undefined) {
              return `${item.msg} (input: ${item.input})`;
            }
            if (item && item.msg) {
              return item.msg;
            }
            return JSON.stringify(item);
          })
          .join("\n");
      } else if (parsed.detail) {
        message = typeof parsed.detail === "string"
          ? parsed.detail
          : JSON.stringify(parsed.detail);
      }
    } catch {
      // Keep the original message.
    }

    return message;
  }

  async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    if (response.status === 401) {
      throw new Error("Your session has expired. Reload the page and sign in again.");
    }
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }
    return response.json();
  }

  function formatDateTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function metaItem(label, value) {
    if (value === null || value === undefined || String(value).trim() === "") return "";
    return `
      <span class="floating-intelligence-chat-card-meta-item">
        <span class="floating-intelligence-chat-card-meta-label">${escapeHtml(label)}</span>
        <span>${escapeHtml(value)}</span>
      </span>
    `;
  }

  function buildRequestUrl(request) {
    const params = new URLSearchParams({
      request,
      top_k: "5",
      fetch_k: "10",
      include_diagnostics: "false",
    });
    return `/assistant/query?${params.toString()}`;
  }

  function fieldValue(row, keys) {
    for (const key of keys) {
      const value = row && row[key];
      if (value !== null && value !== undefined && String(value).trim() !== "") {
        return value;
      }
    }
    return "";
  }

  function buildJobCard(row, idx, options = {}) {
    const company = fieldValue(row, ["company", "job_company"]);
    const title = fieldValue(row, ["title", "job_title"]);
    const location = fieldValue(row, ["location", "job_location"]);
    const postedAt = formatDateTime(fieldValue(row, ["posted_at", "posted_date", "date_posted"]));
    const jobUrl = fieldValue(row, ["job_url", "url", "doc_id"]);
    const sourceId = fieldValue(row, ["source_id"]);
    const titleHtml = jobUrl
      ? `<a href="${escapeHtml(jobUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title || "Job")}</a>`
      : escapeHtml(title || "Job");

    const meta = [
      metaItem("Company", company),
      metaItem("Location", location),
      options.includePosted ? metaItem("Posted", postedAt) : "",
      sourceId ? metaItem("Source", sourceId) : "",
    ].filter(Boolean);

    const kicker = options.useSourceIdKicker && sourceId
      ? escapeHtml(sourceId)
      : `${options.sourceLabel || "Result"} ${idx + 1}`;

    return `
      <div class="${FLOATING_CHAT_CLASS_NAMES.card}">
        <div class="floating-intelligence-chat-card-kicker">${kicker}</div>
        <div class="floating-intelligence-chat-card-title">${titleHtml}</div>
        ${meta.length
          ? `<div class="${FLOATING_CHAT_CLASS_NAMES.cardMeta}">${meta.join("")}</div>`
          : ""}
      </div>
    `;
  }

  function buildIntentChip(label) {
    return `<div class="floating-intelligence-chat-intent-chip">${escapeHtml(label)}</div>`;
  }

  function buildEmptySearchResponseHtml() {
    return `
      ${buildIntentChip("Searched jobs")}
      <p class="floating-intelligence-chat-answer">
        I did not find direct matches in the current job corpus. The corpus may not contain that exact role or skill wording, so try broader or related terms.
      </p>
    `;
  }

  function buildSearchResponseHtml(payload) {
    const rows = Array.isArray(payload?.results) ? payload.results : [];
    if (!rows.length) {
      return buildEmptySearchResponseHtml();
    }

    return `
      ${buildIntentChip("Searched jobs")}
      <div class="floating-intelligence-chat-results">
        ${rows.map((row, idx) => buildJobCard(row, idx, {
          includePosted: true,
          sourceLabel: "Result",
        })).join("")}
      </div>
    `;
  }

  function buildProviderMetaHtml(response) {
    const provider = fieldValue(response, ["llm_provider"]);
    const model = fieldValue(response, ["llm_model"]);
    if (!provider && !model) {
      return "";
    }

    const label = [provider, model].filter(Boolean).map((part) => escapeHtml(part)).join(" &middot; ");
    const fallbackHtml = response && response.llm_fallback_used
      ? '<span class="floating-intelligence-chat-provider-fallback">fallback</span>'
      : "";

    return `
      <div class="floating-intelligence-chat-provider-meta">
        <span>${label}</span>
        ${fallbackHtml}
      </div>
    `;
  }

  function answerResponseOf(payload) {
    return payload?.response && typeof payload.response === "object"
      ? payload.response
      : payload || {};
  }

  // Returns "provider", "runtime", or "" — never exposes the raw internal detail.
  function classifyAnswerFailure(response) {
    const answer = String((response && response.answer) || "");
    for (const entry of ANSWER_FAILURE_MARKERS) {
      if (answer.indexOf(entry.marker) !== -1) {
        return entry.kind;
      }
    }
    return "";
  }

  function isRetryableFailure(payload) {
    if (payload?.intent === "search_jobs") {
      return false;
    }
    return Boolean(classifyAnswerFailure(answerResponseOf(payload)));
  }

  function buildAnswerFailureHtml(kind) {
    const copy = ANSWER_FAILURE_COPY[kind] || ANSWER_FAILURE_COPY.runtime;
    return `
      <div class="floating-intelligence-chat-failure">
        <div class="floating-intelligence-chat-failure-title">${escapeHtml(copy.title)}</div>
        <p class="floating-intelligence-chat-failure-copy">${escapeHtml(copy.body)}</p>
      </div>
    `;
  }

  function buildAnswerResponseHtml(payload) {
    const response = answerResponseOf(payload);
    const answer = response.answer || payload?.answer || "No answer text returned.";

    const failureKind = classifyAnswerFailure(response);
    if (failureKind) {
      return `
        ${buildIntentChip("Answered from corpus")}
        ${buildAnswerFailureHtml(failureKind)}
      `;
    }

    const insufficient = response.insufficient_evidence === true;
    const sources = Array.isArray(response.sources)
      ? response.sources
      : Array.isArray(payload?.sources)
        ? payload.sources
        : [];

    const sourcesHtml = sources.length
      ? `
        <div class="floating-intelligence-chat-sources">
          <div class="floating-intelligence-chat-section-label">Sources</div>
          ${sources.map((row, idx) => buildJobCard(row, idx, {
            includePosted: true,
            sourceLabel: "Source",
            useSourceIdKicker: true,
          })).join("")}
        </div>
      `
      : "";

    const answerHtml = insufficient
      ? `
        <div class="floating-intelligence-chat-insufficient">
          <div class="floating-intelligence-chat-insufficient-label">Insufficient evidence</div>
          <p class="floating-intelligence-chat-answer">${escapeHtml(answer)}</p>
        </div>
      `
      : `<p class="floating-intelligence-chat-answer">${escapeHtml(answer)}</p>`;

    return `
      ${buildIntentChip("Answered from corpus")}
      ${answerHtml}
      ${sourcesHtml}
      ${buildProviderMetaHtml(response)}
    `;
  }

  function isNearBottom(messages) {
    const distance = messages.scrollHeight - messages.scrollTop - messages.clientHeight;
    return distance <= SCROLL_PIN_THRESHOLD_PX;
  }

  function scrollToLatest(messages) {
    messages.scrollTop = messages.scrollHeight;
  }

  function appendMessage(messages, role, html, options = {}) {
    const pinned = options.forceScroll === true || isNearBottom(messages);
    const message = document.createElement("div");
    const roleClass = role === "user"
      ? FLOATING_CHAT_CLASS_NAMES.userMessage
      : FLOATING_CHAT_CLASS_NAMES.assistantMessage;
    message.className = `${FLOATING_CHAT_CLASS_NAMES.message} ${roleClass}`;
    if (options.error) {
      message.className += ` ${FLOATING_CHAT_CLASS_NAMES.errorMessage}`;
    }
    if (options.thinking) {
      message.dataset.floatingChatThinking = "true";
    }
    message.innerHTML = `<div class="${FLOATING_CHAT_CLASS_NAMES.bubble}">${html}</div>`;
    messages.appendChild(message);
    if (pinned) {
      scrollToLatest(messages);
    }
    return message;
  }

  function buildThinkingHtml() {
    return `
      <div class="floating-intelligence-chat-thinking" role="status" aria-label="Generating answer">
        <span class="floating-intelligence-chat-thinking-dot" aria-hidden="true"></span>
        <span class="floating-intelligence-chat-thinking-dot" aria-hidden="true"></span>
        <span class="floating-intelligence-chat-thinking-dot" aria-hidden="true"></span>
      </div>
    `;
  }

  function removeThinkingMessage(messages) {
    const thinking = messages.querySelector("[data-floating-chat-thinking='true']");
    if (thinking) {
      thinking.remove();
    }
  }

  function buildSuggestedPromptsHtml() {
    return SUGGESTED_PROMPTS.map((prompt) => `
      <button
        type="button"
        class="floating-intelligence-chat-suggested-prompt"
        data-accent="${escapeHtml(prompt.accent || "blue")}"
        data-floating-chat-prompt="${escapeHtml(prompt.request)}"
      >
        <span class="floating-intelligence-chat-suggested-prompt-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">${SUGGESTED_PROMPT_ICONS[prompt.icon] || ""}</svg>
        </span>
        <span class="floating-intelligence-chat-suggested-prompt-copy">
          <span class="floating-intelligence-chat-suggested-prompt-title">${escapeHtml(prompt.title)}</span>
          <span class="floating-intelligence-chat-suggested-prompt-hint">${escapeHtml(prompt.hint)}</span>
        </span>
      </button>
    `).join("");
  }

  function buildEmptyStateHtml() {
    return `
      <div class="floating-intelligence-chat-empty">
        <span class="floating-intelligence-chat-empty-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <circle cx="11" cy="11" r="6.2" fill="none" stroke="currentColor" stroke-width="1.9" />
            <path d="M15.6 15.6 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            <path d="M11 7.6l.85 2.05 2.05.85-2.05.85L11 13.4l-.85-2.05-2.05-.85 2.05-.85z" fill="currentColor" />
          </svg>
        </span>
        <h3 class="floating-intelligence-chat-empty-title">What would you like to explore?</h3>
        <p class="floating-intelligence-chat-empty-copy">${escapeHtml(OPENING_ASSISTANT_GREETING)}</p>
        <div class="floating-intelligence-chat-suggested-prompts">
          ${buildSuggestedPromptsHtml()}
        </div>
      </div>
    `;
  }

  function clearEmptyState(messages) {
    if (!messages.dataset.floatingChatTouched) {
      messages.innerHTML = "";
      messages.dataset.floatingChatTouched = "true";
    }
  }

  function ensureOpeningAssistantGreeting(messages) {
    if (
      messages.dataset.floatingChatGreetingShown
      || messages.querySelector(`.${FLOATING_CHAT_CLASS_NAMES.message}`)
    ) {
      return;
    }

    messages.innerHTML = buildEmptyStateHtml();
    messages.dataset.floatingChatGreetingShown = "true";
  }

  function resetToEmptyState(messages) {
    messages.innerHTML = buildEmptyStateHtml();
    messages.dataset.floatingChatGreetingShown = "true";
    delete messages.dataset.floatingChatTouched;
    messages.scrollTop = 0;
  }

  const FOCUSABLE_SELECTOR = [
    "a[href]",
    "button:not([disabled])",
    "textarea:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    '[tabindex]:not([tabindex="-1"])',
  ].join(",");

  function isVisible(el) {
    if (!el || el.hidden) return false;
    if (el.getAttribute && el.getAttribute("aria-hidden") === "true") return false;
    if (el.closest && el.closest("[hidden]")) return false;
    // offsetParent is null for display:none subtrees in real browsers.
    if ("offsetParent" in el && el.offsetParent === null) {
      const style = typeof window !== "undefined" && window.getComputedStyle
        ? window.getComputedStyle(el)
        : null;
      if (style && (style.display === "none" || style.visibility === "hidden")) return false;
    }
    return true;
  }

  // Discovered fresh on every call so controls that appear later (Retry,
  // source links, jump-to-latest) participate without a static list.
  function focusableElements(container) {
    if (!container || !container.querySelectorAll) return [];
    return Array.from(container.querySelectorAll(FOCUSABLE_SELECTOR)).filter(isVisible);
  }

  function bindFloatingChat() {
    const root = qs("floatingIntelligenceChat");
    const openBtn = qs("floatingIntelligenceChatButton");
    const panel = qs("floatingIntelligenceChatPanel");
    const closeBtn = qs("floatingIntelligenceChatCloseBtn");
    const modeSelect = qs("floatingIntelligenceModeSelect");
    const input = qs("floatingIntelligenceInput");
    const sendBtn = qs("floatingIntelligenceSendBtn");
    const messages = qs("floatingIntelligenceMessages");
    const status = qs("floatingIntelligenceStatus");
    const newChatBtn = qs("floatingIntelligenceNewChatBtn");
    const jumpBtn = qs("floatingIntelligenceJumpBtn");

    if (!root || !openBtn || !panel || !closeBtn || !input || !sendBtn || !messages || !status) {
      return;
    }

    let activeController = null;
    let activeRequestId = 0;
    let lastUserRequest = "";
    let isBusy = false;

    if (modeSelect) {
      modeSelect.hidden = true;
      modeSelect.setAttribute("aria-hidden", "true");
      modeSelect.tabIndex = -1;
    }

    ensureOpeningAssistantGreeting(messages);

    function setStatus(value) {
      status.textContent = value;
    }

    function openPanel() {
      root.classList.add("is-open");
      panel.classList.remove("hidden");
      openBtn.setAttribute("aria-expanded", "true");
      // preventScroll keeps the page from jumping to the composer on open.
      try {
        input.focus({ preventScroll: true });
      } catch {
        input.focus();
      }
    }

    function restoreLauncherFocus() {
      if (openBtn && typeof openBtn.focus === "function" && openBtn.isConnected !== false) {
        try {
          openBtn.focus({ preventScroll: true });
        } catch {
          openBtn.focus();
        }
      }
    }

    function closePanel() {
      root.classList.remove("is-open");
      panel.classList.add("hidden");
      openBtn.setAttribute("aria-expanded", "false");
      restoreLauncherFocus();
    }

    function isPanelOpen() {
      return !panel.classList.contains("hidden");
    }

    function trapFocus(event) {
      if (event.key !== "Tab" || !isPanelOpen()) {
        return;
      }

      const focusables = focusableElements(panel);
      if (!focusables.length) {
        return;
      }

      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;

      if (event.shiftKey) {
        if (active === first || !panel.contains(active)) {
          event.preventDefault();
          last.focus();
        }
        return;
      }

      if (active === last || !panel.contains(active)) {
        event.preventDefault();
        first.focus();
      }
    }

    function autoGrowComposer() {
      input.style.height = "auto";
      input.style.height = `${Math.min(input.scrollHeight, COMPOSER_MAX_HEIGHT_PX)}px`;
    }

    function setBusy(busy) {
      isBusy = busy;
      sendBtn.dataset.state = busy ? "busy" : "idle";
      sendBtn.setAttribute("aria-label", busy ? "Stop generating" : "Send message");
      sendBtn.setAttribute("title", busy ? "Stop generating" : "Send message");
      sendBtn.disabled = false;
      panel.dataset.busy = busy ? "true" : "false";
      panel.setAttribute("aria-busy", busy ? "true" : "false");
    }

    function updateJumpButton() {
      if (!jumpBtn) {
        return;
      }
      const hasMessages = Boolean(messages.querySelector(`.${FLOATING_CHAT_CLASS_NAMES.message}`));
      jumpBtn.hidden = !hasMessages || isNearBottom(messages);
    }

    function abortActiveRequest() {
      if (activeController) {
        activeController.abort();
        activeController = null;
      }
    }

    function appendRetryAction(messageEl) {
      const bubble = messageEl.querySelector(`.${FLOATING_CHAT_CLASS_NAMES.bubble}`);
      if (!bubble) {
        return;
      }
      const actions = document.createElement("div");
      actions.className = "floating-intelligence-chat-actions";
      actions.innerHTML = `
        <button type="button" class="floating-intelligence-chat-retry-btn" data-floating-chat-retry="true">
          Retry
        </button>
      `;
      bubble.appendChild(actions);
    }

    async function runRequest(request, options = {}) {
      if (isBusy) {
        return;
      }

      const cleaned = String(request || "").trim();
      if (!cleaned) {
        setStatus("Enter a question first.");
        input.focus();
        return;
      }

      lastUserRequest = cleaned;
      clearEmptyState(messages);
      if (options.skipUserEcho !== true) {
        appendMessage(messages, "user", escapeHtml(cleaned), { forceScroll: true });
      }
      appendMessage(messages, "assistant", buildThinkingHtml(), {
        thinking: true,
        forceScroll: true,
      });

      const controller = new AbortController();
      activeController = controller;
      const requestId = ++activeRequestId;
      setBusy(true);
      setStatus("Thinking...");
      updateJumpButton();

      try {
        const payload = await fetchJson(buildRequestUrl(cleaned), { signal: controller.signal });
        if (requestId !== activeRequestId) {
          return;
        }
        const html = payload?.intent === "search_jobs"
          ? buildSearchResponseHtml(payload)
          : buildAnswerResponseHtml(payload);
        removeThinkingMessage(messages);
        const answerEl = appendMessage(messages, "assistant", html);
        if (isRetryableFailure(payload)) {
          appendRetryAction(answerEl);
          setStatus("Error");
        } else {
          setStatus("Idle");
        }
      } catch (err) {
        if (requestId !== activeRequestId) {
          return;
        }
        removeThinkingMessage(messages);
        if (err && err.name === "AbortError") {
          setStatus("Stopped");
        } else {
          const errorEl = appendMessage(
            messages,
            "assistant",
            escapeHtml(extractErrorMessage(err)),
            { error: true },
          );
          appendRetryAction(errorEl);
          setStatus("Error");
        }
      } finally {
        if (requestId === activeRequestId) {
          activeController = null;
          setBusy(false);
          updateJumpButton();
        }
      }
    }

    function stopRequest() {
      if (!isBusy) {
        return;
      }
      abortActiveRequest();
      removeThinkingMessage(messages);
      setBusy(false);
      setStatus("Stopped");
      updateJumpButton();
      input.focus();
    }

    function startNewChat() {
      abortActiveRequest();
      activeRequestId += 1;
      lastUserRequest = "";
      setBusy(false);
      resetToEmptyState(messages);
      input.value = "";
      autoGrowComposer();
      setStatus("Idle");
      updateJumpButton();
      input.focus();
    }

    function submitComposer() {
      if (isBusy) {
        stopRequest();
        return;
      }
      const request = input.value;
      if (!String(request || "").trim()) {
        return;
      }
      input.value = "";
      autoGrowComposer();
      runRequest(request);
    }

    openBtn.addEventListener("click", () => {
      if (panel.classList.contains("hidden")) {
        openPanel();
      } else {
        closePanel();
      }
    });

    closeBtn.addEventListener("click", closePanel);

    panel.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && isPanelOpen()) {
        event.preventDefault();
        closePanel();
        return;
      }
      trapFocus(event);
    });
    sendBtn.addEventListener("click", submitComposer);

    if (newChatBtn) {
      newChatBtn.addEventListener("click", startNewChat);
    }

    if (jumpBtn) {
      jumpBtn.addEventListener("click", () => {
        scrollToLatest(messages);
        updateJumpButton();
      });
    }

    messages.addEventListener("scroll", updateJumpButton);

    messages.addEventListener("click", (event) => {
      const promptEl = event.target.closest("[data-floating-chat-prompt]");
      if (promptEl) {
        runRequest(promptEl.getAttribute("data-floating-chat-prompt"));
        return;
      }

      const retryEl = event.target.closest("[data-floating-chat-retry]");
      if (retryEl && lastUserRequest && !isBusy) {
        const messageEl = retryEl.closest(`.${FLOATING_CHAT_CLASS_NAMES.message}`);
        if (messageEl) {
          messageEl.remove();
        }
        runRequest(lastUserRequest, { skipUserEcho: true });
      }
    });

    input.addEventListener("input", autoGrowComposer);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitComposer();
      }
    });

    setBusy(false);
    autoGrowComposer();
    updateJumpButton();
  }

  window.addEventListener("DOMContentLoaded", bindFloatingChat);
})();
