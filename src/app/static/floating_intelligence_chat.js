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

    return `
      <div class="${FLOATING_CHAT_CLASS_NAMES.card}">
        <div class="floating-intelligence-chat-card-kicker">${options.sourceLabel || "Result"} ${idx + 1}</div>
        <div class="floating-intelligence-chat-card-title">${titleHtml}</div>
        ${meta.length
          ? `<div class="${FLOATING_CHAT_CLASS_NAMES.cardMeta}">${meta.join("")}</div>`
          : ""}
      </div>
    `;
  }

  function buildSearchResponseHtml(payload) {
    const rows = Array.isArray(payload?.results) ? payload.results : [];
    if (!rows.length) {
      return "No search results returned.";
    }

    return `
      <div class="floating-intelligence-chat-results">
        ${rows.map((row, idx) => buildJobCard(row, idx, {
          includePosted: true,
          sourceLabel: "Result",
        })).join("")}
      </div>
    `;
  }

  function buildAnswerResponseHtml(payload) {
    const response = payload?.response && typeof payload.response === "object"
      ? payload.response
      : payload || {};
    const answer = response.answer || payload?.answer || "No answer text returned.";
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
          })).join("")}
        </div>
      `
      : "";

    return `
      <p class="floating-intelligence-chat-answer">${escapeHtml(answer)}</p>
      ${sourcesHtml}
    `;
  }

  function appendMessage(messages, role, html, options = {}) {
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
    messages.scrollTop = messages.scrollHeight;
    return message;
  }

  function removeThinkingMessage(messages) {
    const thinking = messages.querySelector("[data-floating-chat-thinking='true']");
    if (thinking) {
      thinking.remove();
    }
    messages.scrollTop = messages.scrollHeight;
  }

  function clearEmptyState(messages) {
    if (!messages.dataset.floatingChatTouched) {
      messages.innerHTML = "";
      messages.dataset.floatingChatTouched = "true";
    }
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

    if (!root || !openBtn || !panel || !closeBtn || !input || !sendBtn || !messages || !status) {
      return;
    }

    if (modeSelect) {
      modeSelect.hidden = true;
      modeSelect.setAttribute("aria-hidden", "true");
      modeSelect.tabIndex = -1;
    }

    function setStatus(value) {
      status.textContent = value;
    }

    function openPanel() {
      root.classList.add("is-open");
      panel.classList.remove("hidden");
      openBtn.setAttribute("aria-expanded", "true");
      input.focus();
    }

    function closePanel() {
      root.classList.remove("is-open");
      panel.classList.add("hidden");
      openBtn.setAttribute("aria-expanded", "false");
    }

    async function sendRequest() {
      if (sendBtn.disabled) {
        return;
      }

      const request = input.value.trim();
      if (!request) {
        setStatus("Enter a question first.");
        return;
      }

      clearEmptyState(messages);
      appendMessage(messages, "user", escapeHtml(request));
      appendMessage(messages, "assistant", "Thinking...", { thinking: true });
      input.value = "";
      sendBtn.disabled = true;
      setStatus("Thinking...");

      try {
        const payload = await fetchJson(buildRequestUrl(request));
        const html = payload?.intent === "search_jobs"
          ? buildSearchResponseHtml(payload)
          : buildAnswerResponseHtml(payload);
        removeThinkingMessage(messages);
        appendMessage(messages, "assistant", html);
        setStatus("Idle");
      } catch (err) {
        removeThinkingMessage(messages);
        appendMessage(messages, "assistant", escapeHtml(extractErrorMessage(err)), { error: true });
        setStatus("Error");
      } finally {
        sendBtn.disabled = false;
      }
    }

    openBtn.addEventListener("click", () => {
      if (panel.classList.contains("hidden")) {
        openPanel();
      } else {
        closePanel();
      }
    });

    closeBtn.addEventListener("click", closePanel);
    sendBtn.addEventListener("click", sendRequest);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        sendRequest();
      }
    });
  }

  window.addEventListener("DOMContentLoaded", bindFloatingChat);
})();
