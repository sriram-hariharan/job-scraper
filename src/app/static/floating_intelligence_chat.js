(function () {
  "use strict";

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

  function formatScore(value) {
    if (value === null || value === undefined || String(value).trim() === "") return "";
    const parsed = Number(String(value).replaceAll(",", "").trim());
    if (!Number.isFinite(parsed)) return String(value);
    const normalized = Math.abs(parsed) <= 1 ? parsed * 100 : parsed;
    return normalized.toFixed(1);
  }

  function buildRequestUrl(mode, request) {
    if (mode === "search") {
      const params = new URLSearchParams({
        request,
        top_k: "5",
      });
      return `/jobs/search-lite?${params.toString()}`;
    }

    const params = new URLSearchParams({
      request,
      top_k: "5",
      fetch_k: "15",
      include_diagnostics: "false",
    });
    return `/rag/answer?${params.toString()}`;
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
    const score = formatScore(fieldValue(row, ["score", "ai_fit_score"]));
    const postedAt = formatDateTime(fieldValue(row, ["posted_at", "posted_date", "date_posted"]));
    const jobUrl = fieldValue(row, ["job_url", "url", "doc_id"]);
    const sourceId = fieldValue(row, ["source_id"]);
    const titleHtml = jobUrl
      ? `<a href="${escapeHtml(jobUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title || "Job")}</a>`
      : escapeHtml(title || "Job");

    const meta = [
      company,
      options.includeScore && score ? `Score: ${score}` : "",
      location,
      options.includePosted && postedAt ? `Posted: ${postedAt}` : "",
      sourceId,
    ].filter(Boolean);

    return `
      <div class="floating-intelligence-chat-card">
        <div class="floating-intelligence-chat-card-title">#${idx + 1} ${titleHtml}</div>
        ${meta.length
          ? `<div class="floating-intelligence-chat-card-meta">${meta.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>`
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
        ${rows.map((row, idx) => buildJobCard(row, idx, { includeScore: true })).join("")}
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
          ${sources.map((row, idx) => buildJobCard(row, idx, { includePosted: true })).join("")}
        </div>
      `
      : "";

    return `
      <div class="floating-intelligence-chat-answer">${escapeHtml(answer)}</div>
      ${sourcesHtml}
    `;
  }

  function appendMessage(messages, role, html, options = {}) {
    const message = document.createElement("div");
    message.className = `floating-intelligence-chat-message floating-intelligence-chat-message--${role}`;
    if (options.error) {
      message.className += " floating-intelligence-chat-message--error";
    }
    message.innerHTML = html;
    messages.appendChild(message);
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

    if (!root || !openBtn || !panel || !closeBtn || !modeSelect || !input || !sendBtn || !messages || !status) {
      return;
    }

    function setStatus(value) {
      status.textContent = value;
    }

    function openPanel() {
      panel.classList.remove("hidden");
      openBtn.setAttribute("aria-expanded", "true");
      input.focus();
    }

    function closePanel() {
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

      const mode = modeSelect.value === "search" ? "search" : "answer";
      clearEmptyState(messages);
      appendMessage(messages, "user", escapeHtml(request));
      input.value = "";
      sendBtn.disabled = true;
      setStatus("Thinking...");

      try {
        const payload = await fetchJson(buildRequestUrl(mode, request));
        const html = mode === "search"
          ? buildSearchResponseHtml(payload)
          : buildAnswerResponseHtml(payload);
        appendMessage(messages, "assistant", html);
        setStatus("Idle");
      } catch (err) {
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
