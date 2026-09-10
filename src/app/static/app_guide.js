(() => {
  "use strict";

  const normalizeGuideSearch = (value) =>
    String(value || "").toLocaleLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

  const boot = () => {
    const search = document.getElementById("appGuideSearch");
    const navSearch = document.getElementById("appGuideNavSearch");
    const clearButton = document.getElementById("appGuideClearSearch");
    const searchPanel = document.getElementById("appGuideSearchPanel");
    const searchStatus = document.getElementById("appGuideSearchStatus");
    const searchEmpty = document.getElementById("appGuideSearchEmpty");
    const topicSelect = document.getElementById("appGuideTopicSelect");
    const railStart = document.getElementById("appGuideRailStart");
    const railHelp = document.getElementById("appGuideRailHelp");
    const railContext = document.getElementById("appGuideRailContext");
    const railTopicTitle = document.getElementById("appGuideRailTopicTitle");
    const railChips = document.getElementById("appGuideRailChips");
    const railTermTitle = document.getElementById("appGuideRailTermTitle");
    const railTermCopy = document.getElementById("appGuideRailTermCopy");
    const topics = Array.from(document.querySelectorAll("[data-guide-topic]"));
    const navLinks = Array.from(document.querySelectorAll(".app-guide-nav-link"));
    const topicTriggers = Array.from(document.querySelectorAll("[data-guide-nav-target]"));
    const popularTriggers = Array.from(document.querySelectorAll("[data-guide-popular-target]"));
    const results = Array.from(document.querySelectorAll("[data-guide-search-result]"));
    const resultGroups = Array.from(document.querySelectorAll("[data-guide-result-group]"));
    const validTopics = new Set(topics.map((topic) => topic.dataset.guideTopic));

    if (!search || !searchPanel || topics.length === 0) return;

    let activeTopic = "start";
    let activeResultIndex = -1;

    const setRailTerm = (termName, definition, article) => {
      if (!termName || !railTermTitle || !railTermCopy) return;
      railTermTitle.textContent = termName;
      railTermCopy.textContent = definition || "";
      document.querySelectorAll("[data-guide-term], [data-guide-glossary-select]").forEach((control) => {
        control.setAttribute("aria-pressed", String(control.dataset.guideTerm === termName || control.dataset.guideGlossarySelect === termName));
      });
      if (railChips) {
        railChips.querySelectorAll("[data-guide-rail-term]").forEach((control) => {
          control.setAttribute("aria-pressed", String(control.dataset.guideRailTerm === termName));
        });
      }
      document.querySelectorAll("[data-guide-glossary-term]").forEach((row) => {
        row.classList.toggle("is-highlighted", row.dataset.guideGlossaryTerm === termName && article?.dataset.guideTopic === "glossary");
      });
    };

    const termSourcesFor = (article) => {
      const topicTerms = Array.from(article.querySelectorAll("[data-guide-term]"));
      if (topicTerms.length) return topicTerms;
      return Array.from(article.querySelectorAll("[data-guide-glossary-select]"));
    };

    const syncRail = (article, requestedTerm = "") => {
      const isStart = article?.dataset.guideTopic === "start";
      const isGlossary = article?.dataset.guideTopic === "glossary";
      if (railStart) railStart.hidden = !isStart;
      if (railHelp) railHelp.hidden = isStart;
      if (railContext) railContext.hidden = isStart || isGlossary;
      if (isStart || isGlossary || !article || !railContext || !railChips) return;

      const heading = article.querySelector("h2");
      if (railTopicTitle) railTopicTitle.textContent = heading?.textContent || "Topic terms";
      const sources = termSourcesFor(article);
      railChips.replaceChildren();
      sources.forEach((source) => {
        const termName = source.dataset.guideTerm || source.dataset.guideGlossarySelect || "";
        const definition = source.dataset.guideDefinition || "";
        const toneOwner = source.closest("[class*='app-guide-tone-']") || source;
        const tone = Array.from(toneOwner.classList).find((name) => name.startsWith("app-guide-tone-")) || "app-guide-tone-blue";
        const button = document.createElement("button");
        button.type = "button";
        button.className = `app-guide-term-chip app-guide-term-chip--rail ${tone}`;
        button.dataset.guideRailTerm = termName;
        button.textContent = termName;
        button.addEventListener("click", () => setRailTerm(termName, definition, article));
        railChips.append(button);
      });
      const selected = sources.find((source) => (source.dataset.guideTerm || source.dataset.guideGlossarySelect) === requestedTerm) || sources[0];
      if (selected) {
        setRailTerm(
          selected.dataset.guideTerm || selected.dataset.guideGlossarySelect,
          selected.dataset.guideDefinition,
          article,
        );
      }
    };

    const selectTopic = (slug, options = {}) => {
      const resolved = validTopics.has(slug) ? slug : "start";
      activeTopic = resolved;
      let article = null;
      topics.forEach((topic) => {
        const selected = topic.dataset.guideTopic === resolved;
        topic.hidden = !selected;
        if (selected) article = topic;
      });
      navLinks.forEach((link) => {
        if (link.dataset.guideNavTarget === resolved) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
      });
      if (topicSelect) topicSelect.value = resolved;
      if (options.updateHash !== false && window.history?.replaceState) {
        window.history.replaceState(null, "", `#guide-topic-${resolved}`);
      }
      syncRail(article, options.term || "");
      if (options.focus && article) article.focus({ preventScroll: true });
      if (options.scroll && article) article.scrollIntoView({ behavior: "smooth", block: "start" });
      return resolved;
    };

    const visibleResults = () => results.filter((result) => !result.hidden && !result.closest("[data-guide-result-group]")?.hidden);

    const setActiveResult = (nextIndex) => {
      const visible = visibleResults();
      results.forEach((result) => {
        result.removeAttribute("data-active");
        result.setAttribute("aria-selected", "false");
      });
      if (!visible.length || nextIndex < 0) {
        activeResultIndex = -1;
        search.removeAttribute("aria-activedescendant");
        return;
      }
      activeResultIndex = (nextIndex + visible.length) % visible.length;
      const selected = visible[activeResultIndex];
      selected.dataset.active = "true";
      selected.setAttribute("aria-selected", "true");
      search.setAttribute("aria-activedescendant", selected.id);
      selected.scrollIntoView({ block: "nearest" });
    };

    const filterSearch = (rawQuery) => {
      const query = normalizeGuideSearch(rawQuery);
      const tokens = query.split(" ").filter(Boolean);
      let matched = 0;
      const groupCounts = new Map();
      results.forEach((result) => {
        const haystack = normalizeGuideSearch(result.dataset.guideSearchText);
        const visible = tokens.length > 0 && tokens.every((token) => haystack.includes(token));
        result.hidden = !visible;
        if (visible) {
          matched += 1;
          const group = result.closest("[data-guide-result-group]");
          if (group) groupCounts.set(group, (groupCounts.get(group) || 0) + 1);
        }
      });
      resultGroups.forEach((group) => { group.hidden = !groupCounts.get(group); });
      const hasQuery = tokens.length > 0;
      searchPanel.hidden = !hasQuery;
      search.setAttribute("aria-expanded", String(hasQuery));
      if (clearButton) clearButton.hidden = !hasQuery;
      if (searchEmpty) searchEmpty.hidden = !hasQuery || matched > 0;
      if (searchStatus) searchStatus.textContent = hasQuery
        ? `${matched} ${matched === 1 ? "result" : "results"} across features, terms, and actions`
        : "Type to search the guide";
      setActiveResult(hasQuery && matched ? 0 : -1);
      return matched;
    };

    const clearSearch = (options = {}) => {
      search.value = "";
      filterSearch("");
      if (options.focus !== false) search.focus();
    };

    const focusGuideSearch = () => {
      if (activeTopic !== "start") selectTopic("start", { scroll: true });
      search.focus();
      search.select();
    };

    const openResult = (result) => {
      if (!result) return;
      const target = result.dataset.guideTarget;
      const term = result.dataset.guideTermResult || "";
      clearSearch({ focus: false });
      selectTopic(target, { focus: true, scroll: true, term });
    };

    topicTriggers.forEach((trigger) => {
      trigger.addEventListener("click", (event) => {
        event.preventDefault();
        selectTopic(trigger.dataset.guideNavTarget, { focus: true, scroll: true });
      });
    });

    popularTriggers.forEach((trigger) => {
      trigger.addEventListener("click", () => selectTopic(trigger.dataset.guidePopularTarget, {
        focus: true,
        scroll: true,
        term: trigger.dataset.guidePopularTerm || "",
      }));
    });

    navLinks.forEach((link, index) => {
      link.addEventListener("keydown", (event) => {
        let nextIndex = null;
        if (event.key === "ArrowDown") nextIndex = (index + 1) % navLinks.length;
        if (event.key === "ArrowUp") nextIndex = (index - 1 + navLinks.length) % navLinks.length;
        if (event.key === "Home") nextIndex = 0;
        if (event.key === "End") nextIndex = navLinks.length - 1;
        if (nextIndex === null) return;
        event.preventDefault();
        navLinks[nextIndex].focus();
      });
    });

    if (topicSelect) topicSelect.addEventListener("change", () => selectTopic(topicSelect.value, { focus: true, scroll: true }));
    if (navSearch) navSearch.addEventListener("click", focusGuideSearch);
    document.querySelectorAll("[data-guide-term]").forEach((chip) => {
      chip.addEventListener("click", () => setRailTerm(chip.dataset.guideTerm, chip.dataset.guideDefinition, chip.closest("[data-guide-topic]")));
    });
    document.querySelectorAll("[data-guide-glossary-select]").forEach((term) => {
      term.addEventListener("click", () => setRailTerm(term.dataset.guideGlossarySelect, term.dataset.guideDefinition, term.closest("[data-guide-topic]")));
    });

    results.forEach((result) => {
      result.addEventListener("click", () => openResult(result));
      result.addEventListener("mouseenter", () => setActiveResult(visibleResults().indexOf(result)));
    });

    search.addEventListener("input", () => filterSearch(search.value));
    search.addEventListener("focus", () => {
      if (normalizeGuideSearch(search.value)) searchPanel.hidden = false;
    });
    search.addEventListener("keydown", (event) => {
      if (!normalizeGuideSearch(search.value)) return;
      if (event.key === "ArrowDown") { event.preventDefault(); setActiveResult(activeResultIndex + 1); }
      if (event.key === "ArrowUp") { event.preventDefault(); setActiveResult(activeResultIndex - 1); }
      if (event.key === "Enter" && activeResultIndex >= 0) {
        event.preventDefault();
        openResult(visibleResults()[activeResultIndex]);
      }
    });
    if (clearButton) clearButton.addEventListener("click", () => clearSearch());

    document.addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLocaleLowerCase() === "k") {
        event.preventDefault();
        focusGuideSearch();
        return;
      }
      if (event.key !== "Escape") return;
      if (!searchPanel.hidden || normalizeGuideSearch(search.value)) clearSearch();
      else if (document.activeElement === search) search.blur();
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest(".app-guide-search-shell")) {
        searchPanel.hidden = true;
        search.setAttribute("aria-expanded", "false");
      }
    });

    window.addEventListener("hashchange", () => {
      const slug = window.location.hash.replace("#guide-topic-", "");
      if (validTopics.has(slug) && slug !== activeTopic) selectTopic(slug, { updateHash: false });
    });

    const initial = window.location.hash.replace("#guide-topic-", "");
    selectTopic(validTopics.has(initial) ? initial : "start", { updateHash: false });
    window.ApplyLensGuide = { normalizeGuideSearch, filterSearch, clearSearch, selectTopic };
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();
