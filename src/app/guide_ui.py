from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell


router = APIRouter()


_ICONS = {
    "arrow": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
    "briefcase": '<rect width="20" height="14" x="2" y="6" rx="2"/><path d="M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><path d="M2 11h20"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h6"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
    "profile": '<path d="M19 21a7 7 0 0 0-14 0"/><circle cx="12" cy="7" r="4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "scan": '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/>',
    "sparkles": '<path d="m12 3-1.1 3.4a2 2 0 0 1-1.3 1.3L6.2 8.8l3.4 1.1a2 2 0 0 1 1.3 1.3l1.1 3.4 1.1-3.4a2 2 0 0 1 1.3-1.3l3.4-1.1-3.4-1.1a2 2 0 0 1-1.3-1.3Z"/><path d="m19 15-.6 1.8a1 1 0 0 1-.6.6L16 18l1.8.6a1 1 0 0 1 .6.6L19 21l.6-1.8a1 1 0 0 1 .6-.6L22 18l-1.8-.6a1 1 0 0 1-.6-.6Z"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 3v2"/><path d="M21 12h-2"/>',
}


def _icon(name: str) -> str:
    return (
        '<svg class="app-guide-icon" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true" focusable="false">{_ICONS[name]}</svg>'
    )


TERMS = {
    "Match score": ("ApplyLens’s estimate of how clearly the selected resume aligns with the job. It is not an employer ATS score or an interview guarantee.", "fit alignment ATS score", "match"),
    "Matched": ("A job requirement for which ApplyLens found relevant support in the selected resume.", "found evidence supported", "optimization"),
    "Missing": ("A requirement without enough visible support in the evaluated resume. It may still be part of your real experience.", "gap not found evidence", "optimization"),
    "Alternative requirement": ("A requirement that accepts one of several options. One recognized option may satisfy the requirement.", "either or Python R", "optimization"),
    "AI Suggestions": ("Evidence-grounded recommendations for you to review. They are not automatically accepted, saved, or submitted.", "rewrite recommendation tailoring", "suggestions"),
    "Ready": ("A contextual review state—not employer approval. It can describe a Planning row, a reviewable rewrite, or saved work ready to export.", "ready for review generated ready export", "planning"),
    "Safe / no rewrite": ("The job was reviewed successfully, but no worthwhile supported rewrite was recommended.", "safe no change guidance success", "bulk"),
    "No usable rewrite": ("ApplyLens did not find enough grounded evidence to produce a reviewable rewrite for this job and resume.", "no grounded rewrite evidence", "bulk"),
    "Failed / attention": ("That job did not finish successfully. Review it and rerun it if it remains eligible.", "error retry rerun", "bulk"),
    "Eligible": ("A Planning job that currently meets the displayed conditions for a bulk action or rerun.", "bulk available rerun", "bulk"),
    "Excluded": ("A reversible choice that removes an item from active Missing counts and optimization scoring without deleting it from the resume.", "exclude hidden missing scoring", "optimization"),
    "Re-include": ("Return an excluded item to active review so it can count as Missing and be considered again.", "restore undo exclusion reinclude", "optimization"),
    "Planning": ("The workspace where job fit, resume choice, readiness, and the next human action come together.", "worklist plan", "planning"),
    "Optimization Review": ("A job-by-job review of supported, missing, and potentially improvable resume evidence.", "scan report optimize", "optimization"),
    "Bulk Suggestions": ("One controlled request for suggestions across several eligible Planning jobs, with results reviewed together.", "bulk generate results center", "bulk"),
    "Compare": ("A read-only before-and-after view of the baseline and your current accepted decision set.", "original proposed before after", "finish"),
    "Export": ("Download an eligible reviewed draft as PDF or DOCX. Exporting does not submit an application.", "download PDF DOCX Word submit", "finish"),
}


# slug, group, nav label, title, summary, when, what-you-see, guidance, terms, href, action, aliases, visual
TOPICS = (
    ("preferences", "Prepare", "Preferences", "Getting started & Preferences",
     "Give ApplyLens the resume context and job preferences it needs to personalize your workspace.",
     "Use this when you first join, change target roles, or want different job recommendations.",
     ("Role families and seniority", "Locations, skills, and exclusions", "A guided resume and preference review"),
     ("Preferences shape which opportunities are emphasized. You can revisit them later.", "Changing preferences does not rewrite a resume or apply to a job."),
     ("Ready",), "/profile/preferences", "Open Preferences", "onboarding setup roles seniority locations skills exclusions personalize profile", ""),
    ("resumes", "Prepare", "Resumes", "Resumes & versions",
     "Keep the factual source material ApplyLens uses to evaluate jobs and propose changes.",
     "Use this when you add a resume, maintain role-specific versions, or review which version is selected.",
     ("Your resume library", "Role-family assignments", "The selected or recommended resume for a job"),
     ("Multiple versions can help when you pursue different kinds of roles.", "ApplyLens may recommend the strongest-looking version, but suggestions should stay supported by experience already present in your resume."),
     ("Matched", "Missing"), "/profile", "Manage resumes", "CV upload version selected recommended facts evidence role mapping", ""),
    ("overview", "Discover", "Overview", "Overview & job queue",
     "Browse ranked jobs and decide which opportunities deserve your attention.",
     "Use this after jobs have been found or whenever you want a quick view of high-signal opportunities.",
     ("Snapshot counts and filters", "Job, company, recommendation, match, and selected resume", "Expandable details and Review actions"),
     ("Jobs come from configured discovery sources. Inspect why a job is prioritized and open the original posting before acting.", "Source Yield explains how recent discovery contributed to the list; it does not change ranking."),
     ("Match score", "Ready"), "/", "Open Overview", "dashboard jobs browse queue rank recommendation source yield filters posting", ""),
    ("pipeline", "Discover", "Pipeline", "Pipeline",
     "Start job discovery and watch a run move from setup to usable results.",
     "Use this to refresh the job set or check whether a run is idle, starting, running, complete, or needs attention.",
     ("Run controls and current status", "Progress stages and live counts", "Configuration summary and source health"),
     ("Review settings before launch. A completed run supplies jobs to Overview and Planning.", "A pipeline run never applies to a job. If setup is incomplete, the page identifies the user action needed."),
     ("Ready", "Planning"), "/pipeline", "Open Pipeline", "run live discovery status progress stages sources refresh configure", ""),
    ("planning", "Evaluate", "Planning", "Planning",
     "Turn promising jobs into a clear plan before changing a resume or applying.",
     "Use this when a job needs a resume choice, closer review, suggestions, or an application decision.",
     ("Review readiness and match score", "Recommended and selected resume", "AI Review details and the next available action"),
     ("A Planning row brings the job assessment, resume choice, and next step together.", "Ready for review means prepared for your judgment—not employer approval and not a submitted application."),
     ("Planning", "Ready", "Match score"), "/planning", "Open Planning", "worklist selected resume review readiness packet next step plan", "planning"),
    ("match", "Evaluate", "Match & readiness", "Match & readiness",
     "Estimate how clearly the selected resume supports the requirements visible in a job.",
     "Use this to compare opportunities or decide where stronger resume evidence may help.",
     ("A match value and recommendation", "Missing-requirement count and score gap", "Contextual readiness labels"),
     ("The match score is ApplyLens guidance for comparing apparent fit.", "It is not an employer ATS score and cannot predict an interview. Readiness labels describe the next review state, not a guarantee."),
     ("Match score", "Matched", "Missing", "Ready"), "/planning", "Review match information", "score fit alignment ATS rank readiness missing requirements gap", "match"),
    ("suggestions", "Improve", "AI Suggestions", "AI Suggestions & Tailoring",
     "Review proposed wording improvements while keeping your real experience as the boundary.",
     "Use this when Planning offers Generate Suggestions or an existing review can be reopened.",
     ("Suggested wording and its reason", "Supporting resume evidence and projected impact", "Manual edits and review choices"),
     ("Suggestions are recommendations—not silent resume edits. You decide what to accept, revise, or leave alone.", "Not every useful suggestion changes the score. Guidance may come without a rewrite when a stronger claim would not be safe or worthwhile."),
     ("AI Suggestions", "Safe / no rewrite", "No usable rewrite"), "/planning", "Find jobs needing suggestions", "generate optimize tailoring rewrite evidence edit accept reject guidance grounded", ""),
    ("bulk", "Improve", "Bulk Suggestions", "Bulk Suggestions",
     "Generate reviewable suggestions for several eligible Planning jobs in one controlled run.",
     "Use this when multiple Planning jobs need suggestion generation and you want to process them together.",
     ("Setup review and eligible-job count", "Running progress and Stop after current", "Results Center, filters, selection, and rerun actions"),
     ("Generated / Ready means reviewable suggestions were produced. Safe / no rewrite is a successful review with no worthwhile supported rewrite.", "No usable rewrite means grounded evidence was insufficient. Failed / attention needs review. Rerun selected and rerun all eligible act only on jobs currently shown as eligible."),
     ("Bulk Suggestions", "Eligible", "Safe / no rewrite", "No usable rewrite", "Failed / attention"), "/planning", "Open Bulk Suggestions", "bulk generate results center progress stop current generated rerun selected all failure", "bulk"),
    ("optimization", "Improve", "Optimization Review", "New Scan & Optimization Review",
     "Compare one saved resume with one target job and work through the most useful improvements.",
     "Use this for a specific job description, even when it did not come from the main queue.",
     ("Resume and job intake", "Matched, Missing, and AI Suggestions", "Resume/job views, personal details, and review controls"),
     ("Matched means support was found. Missing means enough evidence was not found; it does not prove you lack the skill. One option may satisfy an alternative such as “Python or R.”", "Exclude removes an item from active Missing counts and scoring without deleting it. It remains under Excluded, where Re-include reverses the choice."),
     ("Optimization Review", "Matched", "Missing", "Alternative requirement", "Excluded", "Re-include"), "/scan-workspace", "Start a New Scan", "scan report requirements alternative exclude excluded reinclude personal details", "optimization"),
    ("finish", "Finish", "Save, Compare & Export", "Save, Compare & Export",
     "Keep review choices, inspect the resulting draft, and download a file for your own application process.",
     "Use this after selecting suggestions, making supported edits, or recording review decisions.",
     ("Save state", "Before-and-after comparison", "Export readiness and PDF or DOCX choices"),
     ("Save preserves the current review state. It does not accept every suggestion and does not apply to a job. Compare is read-only.", "Export creates a file from eligible reviewed work. You still review and submit the document yourself."),
     ("Compare", "Export", "Ready"), "/profile/saved-scans", "Open Saved Scans", "save state compare original proposed export PDF DOCX Word download apply submit", "finish"),
    ("decisions", "Follow through", "Decisions", "Decisions",
     "Review the choices you recorded for jobs and the manual next steps that followed.",
     "Use this to revisit an Apply, Tailor, Skip, or Hold decision and its selected resume.",
     ("Decision history and filters", "Selected and alternate resumes", "Notes and an Open job action"),
     ("This is a history and follow-through surface.", "Recording a decision organizes your workflow; it never sends an application to an employer."),
     ("Planning", "Ready"), "/decisions-ui", "Open Decisions", "apply tailor skip hold history choice resume notes manual next step", ""),
    ("applications", "Follow through", "Applications", "Applications",
     "Track jobs you explicitly marked Applied or Saved for Later.",
     "Use this after updating a job’s manual status or when revisiting saved opportunities.",
     ("Applied Jobs and Saved for Later", "Company/title filters and dates", "Notes, status, and job-posting links"),
     ("ApplyLens records the status you choose.", "Marking Applied tells the app you applied; ApplyLens does not submit the employer application. Not applied and Dismiss keep tracking accurate."),
     ("Ready",), "/applications", "Open Applications", "tracking applied saved later not applied dismiss status employer submit notes", ""),
    ("saved", "Follow through", "Saved work", "Saved Scans & recent activity",
     "Return to saved optimization reports and review recent job-discovery activity.",
     "Use this to reopen, search, or manage earlier work instead of starting over.",
     ("Saved scan reports", "Resume and recent-activity areas", "Search, reopen, and management actions"),
     ("Reopening a saved scan restores the available report and review state for that job and resume.", "Deleting a saved scan removes that record; it is separate from deleting a resume or changing an application status."),
     ("Optimization Review", "Export"), "/profile/saved-scans", "Browse Saved Scans", "saved reopen search manage library recent activity history profile", ""),
    ("notifications", "Follow through", "Notifications", "Notifications",
     "See when job discovery or pipeline activity has something new to report.",
     "Use this when the bell shows unread activity or you want to review recent updates.",
     ("All and Unread views", "Pipeline and Discovery filters", "Read, refresh, mark-all-read, and delete actions"),
     ("Opening or marking a notification changes its read state.", "Deleting a notification removes its message; it does not undo the activity that produced it."),
     ("Ready",), "/pipeline", "Open Pipeline activity", "bell alerts unread read delete discovery activity refresh mark all", ""),
    ("assistant", "Follow through", "Job Assistant", "Job Assistant",
     "Ask grounded questions or search the available job collection from the floating assistant.",
     "Use this for a conversational way to find jobs or understand information available to ApplyLens.",
     ("A floating chat panel", "Conversation history and message box", "New chat and jump-to-latest controls"),
     ("The assistant decides whether a question needs job search or a direct answer.", "Its responses are guidance. Verify important details in the original posting before acting."),
     ("Match score", "Planning"), "/", "Return to Overview", "chat ask search jobs grounded questions conversation message assistant", ""),
)


GROUPS = (
    ("Start", (("start", "Start here"),)),
    ("Discover", tuple((t[0], t[2]) for t in TOPICS if t[1] == "Discover")),
    ("Prepare", tuple((t[0], t[2]) for t in TOPICS if t[1] == "Prepare")),
    ("Evaluate", tuple((t[0], t[2]) for t in TOPICS if t[1] == "Evaluate")),
    ("Improve", tuple((t[0], t[2]) for t in TOPICS if t[1] == "Improve")),
    ("Finish", tuple((t[0], t[2]) for t in TOPICS if t[1] == "Finish")),
    ("Follow through", tuple((t[0], t[2]) for t in TOPICS if t[1] == "Follow through")),
    ("Reference", (("glossary", "Glossary"),)),
)


TOPIC_META = {
    "preferences": ("profile", "blue"), "resumes": ("file", "violet"),
    "overview": ("briefcase", "blue"), "pipeline": ("search", "violet"),
    "planning": ("target", "teal"), "match": ("target", "green"),
    "suggestions": ("sparkles", "amber"), "bulk": ("layers", "violet"),
    "optimization": ("scan", "violet"), "finish": ("file", "blue"),
    "decisions": ("check", "amber"), "applications": ("briefcase", "blue"),
    "saved": ("book", "teal"), "notifications": ("target", "amber"),
    "assistant": ("sparkles", "violet"), "start": ("book", "blue"),
    "glossary": ("book", "blue"),
}


def _term_tone(term: str) -> str:
    if term in {"Matched", "Safe / no rewrite"}:
        return "green"
    if term in {"Missing", "Failed / attention"}:
        return "rose"
    if term in {"AI Suggestions", "Optimization Review", "Bulk Suggestions"}:
        return "violet"
    if term in {"Excluded", "Re-include", "Eligible"}:
        return "amber"
    return "blue"


def _flow(kind: str) -> str:
    flows = {
        "planning": (("Job", "Role needs", "briefcase"), ("Recommended resume", "Best evidence", "file"), ("Match estimate", "Alignment guidance", "target"), ("Next action", "Your decision", "arrow")),
        "match": (("Requirements", "Visible expectations", "briefcase"), ("Resume evidence", "Supported experience", "file"), ("Alignment", "ApplyLens guidance", "target")),
        "bulk": (("Eligible jobs", "Current Planning set", "layers"), ("Controlled run", "Progress job by job", "sparkles"), ("Results Center", "Review outcomes", "target"), ("Rerun", "Only eligible jobs", "arrow")),
        "optimization": (("Resume + job", "Focused comparison", "scan"), ("Matched / missing", "Evidence review", "target"), ("Suggestions", "Grounded improvements", "sparkles"), ("Accept / exclude", "Your reversible choices", "check"), ("Save", "Preserve the review", "file")),
        "finish": (("Save", "Preserve review", "check"), ("Compare", "Inspect changes", "layers"), ("Export", "PDF or DOCX", "file"), ("Apply yourself", "Employer site", "arrow")),
    }
    nodes = "".join(
        f'<div class="app-guide-diagram-node app-guide-tone-{("blue", "violet", "green", "amber")[index % 4]}"><span>{_icon(icon)}</span><strong>{escape(title)}</strong><small>{escape(copy)}</small></div>'
        for index, (title, copy, icon) in enumerate(flows[kind])
    )
    return f'<figure class="app-guide-diagram" aria-label="{escape(kind)} workflow">{nodes}</figure>'


def _term_chips(names: tuple[str, ...], *, rail: bool = False) -> str:
    extra = " app-guide-term-chip--rail" if rail else ""
    return "".join(
        f'<button type="button" class="app-guide-term-chip app-guide-tone-{_term_tone(name)}{extra}" '
        f'data-guide-term="{escape(name)}" data-guide-definition="{escape(TERMS[name][0])}">{escape(name)}</button>'
        for name in names
    )


def _topic_article(topic: tuple, next_slug: str, next_label: str) -> str:
    slug, group, _nav, title, summary, when, sees, guidance, terms, href, action, _aliases, visual = topic
    icon, tone = TOPIC_META[slug]
    seen = "".join(f'<li><span aria-hidden="true">{_icon("check")}</span>{escape(item)}</li>' for item in sees)
    prose = "".join(f"<p>{escape(paragraph)}</p>" for paragraph in guidance)
    diagram = _flow(visual) if visual else ""
    return f"""
      <article class="app-guide-topic" id="guide-topic-{escape(slug)}" data-guide-topic="{escape(slug)}" hidden tabindex="-1">
        <header class="app-guide-topic-header">
          <span class="app-guide-topic-symbol app-guide-tone-{tone}">{_icon(icon)}</span>
          <span class="app-guide-topic-kicker">{escape(group)}</span>
          <h2>{escape(title)}</h2><p>{escape(summary)}</p>
        </header>
        <section class="app-guide-article-section" aria-labelledby="guide-{escape(slug)}-helps">
          <span class="app-guide-section-kicker">What it helps you do</span>
          <h3 id="guide-{escape(slug)}-helps">Know when this part of ApplyLens belongs in your workflow.</h3>
          <p>{escape(when)}</p>
        </section>
        <section class="app-guide-article-section app-guide-article-section--split">
          <div><span class="app-guide-section-kicker">What you’ll see</span><ul class="app-guide-see-list">{seen}</ul></div>
          <div><span class="app-guide-section-kicker">How to think about it</span>{prose}</div>
        </section>
        {diagram}
        <section class="app-guide-article-terms" aria-label="Common terms"><span class="app-guide-section-kicker">Common terms</span><div>{_term_chips(terms)}</div></section>
        <a class="app-guide-product-link" href="{escape(href)}">{escape(action)}{_icon('arrow')}</a>
        <a class="app-guide-next" href="#guide-topic-{escape(next_slug)}" data-guide-nav-target="{escape(next_slug)}"><span>Next</span><strong>{escape(next_label)}</strong>{_icon('arrow')}</a>
      </article>
    """.strip()


def _start_article() -> str:
    steps = (
        ("01", "profile", "blue", "Set up your profile", "Add a resume and set your preferences.", "preferences"),
        ("02", "search", "violet", "Find relevant jobs", "Run Pipeline and browse Overview.", "pipeline"),
        ("03", "target", "green", "Review your fit", "Compare the job, resume, and match.", "planning"),
        ("04", "sparkles", "amber", "Generate suggestions", "Request grounded improvements.", "suggestions"),
        ("05", "scan", "violet", "Optimize and decide", "Review evidence and reversible choices.", "optimization"),
        ("06", "briefcase", "blue", "Export, apply, and track", "Submit yourself, then record it.", "finish"),
    )
    workflow = "".join(
        f'<li class="app-guide-workflow-step app-guide-tone-{tone}"><a href="#guide-topic-{slug}" data-guide-nav-target="{slug}"><span class="app-guide-step-badge" aria-hidden="true">{number}</span><span class="app-guide-step-icon">{_icon(icon)}</span><strong>{escape(title)}</strong><small>{escape(copy)}</small></a></li>'
        for number, icon, tone, title, copy, slug in steps
    )
    popular = (
        ("Match score", "match", "Match score"), ("Missing", "optimization", "Missing"),
        ("Exclude", "optimization", "Excluded"), ("Bulk Suggestions", "bulk", "Bulk Suggestions"),
        ("Export", "finish", "Export"), ("Applications", "applications", ""),
    )
    chips = "".join(
        f'<button type="button" class="app-guide-popular-chip" data-guide-popular-target="{slug}" data-guide-popular-term="{escape(term)}">{escape(label)}</button>'
        for label, slug, term in popular
    )
    return f"""
      <article class="app-guide-topic app-guide-topic--start" id="guide-topic-start" data-guide-topic="start" tabindex="-1">
        <section class="app-guide-intro">
          <div class="app-guide-intro-copy"><span class="app-guide-eyebrow">ApplyLens Guide</span><h1>Get the most out of ApplyLens</h1><p>A step-by-step guide to finding, evaluating, and applying to the right opportunities—with AI by your side.</p></div>
          <div class="app-guide-hero-art" aria-label="Find jobs, optimize your resume, and apply successfully">
            <span class="app-guide-orbit app-guide-orbit--one"></span><span class="app-guide-orbit app-guide-orbit--two"></span>
            <div class="app-guide-float-card app-guide-float-card--jobs"><span>{_icon('search')}</span><small>DISCOVER</small><strong>Find jobs</strong><em>Matched to your goals</em></div>
            <div class="app-guide-float-card app-guide-float-card--resume"><span>{_icon('sparkles')}</span><small>IMPROVE</small><strong>Optimize resume</strong><em>Grounded suggestions</em></div>
            <div class="app-guide-float-card app-guide-float-card--apply"><span>{_icon('check')}</span><small>FOLLOW THROUGH</small><strong>Apply successfully</strong><em>You stay in control</em></div>
          </div>
        </section>
        {_search_surface()}
        <div class="app-guide-popular" id="appGuidePopular"><span>Popular</span>{chips}</div>
        <section class="app-guide-workflow" aria-labelledby="appGuideWorkflowTitle"><div class="app-guide-section-heading"><span>Start here</span><h2 id="appGuideWorkflowTitle">From first resume to a tracked application</h2><p>Follow these six connected stages to see how everything fits together.</p></div><ol>{workflow}</ol></section>
        <section class="app-guide-featured">
          <div class="app-guide-featured-copy"><span class="app-guide-section-kicker">Featured topic</span><span class="app-guide-featured-icon">{_icon('file')}</span><h2>Resumes &amp; versions</h2><p>Keep the factual source material ApplyLens uses to evaluate jobs and propose changes.</p><div><a class="app-guide-product-link" href="/profile">Go to Resumes{_icon('arrow')}</a><a class="app-guide-learn-link" href="#guide-topic-resumes" data-guide-nav-target="resumes">Learn more{_icon('arrow')}</a></div></div>
          <div class="app-guide-resume-art" aria-label="Layered resume versions"><span class="app-guide-resume-sheet app-guide-resume-sheet--back">General</span><span class="app-guide-resume-sheet app-guide-resume-sheet--mid">Product Analytics</span><span class="app-guide-resume-sheet app-guide-resume-sheet--front"><small>MY RESUME</small><strong>Data Science</strong><em>Active</em><i></i><i></i><i></i></span></div>
        </section>
      </article>
    """.strip()


def _glossary_article() -> str:
    rows = "".join(
        f'<div class="app-guide-glossary-row app-guide-tone-{_term_tone(term)}" data-guide-glossary-term="{escape(term)}"><dt><button type="button" class="app-guide-glossary-term" data-guide-glossary-select="{escape(term)}" data-guide-definition="{escape(data[0])}"><span aria-hidden="true"></span>{escape(term)}</button><small>{"Status" if _term_tone(term) in {"green", "rose"} else "Concept"}</small></dt><dd>{escape(data[0])}</dd></div>'
        for term, data in TERMS.items()
    )
    return f'<article class="app-guide-topic" id="guide-topic-glossary" data-guide-topic="glossary" hidden tabindex="-1"><header class="app-guide-topic-header"><span class="app-guide-topic-symbol app-guide-tone-blue">{_icon("book")}</span><span class="app-guide-topic-kicker">Reference</span><h2>Glossary</h2><p>A searchable reference for the terms that carry the most meaning in ApplyLens.</p></header><div class="app-guide-glossary-head" aria-hidden="true"><span>Term</span><span>Definition</span></div><dl class="app-guide-glossary-list">{rows}</dl></article>'


def _navigation() -> tuple[str, str]:
    desktop, mobile = [], []
    for group, items in GROUPS:
        links = []
        for slug, label in items:
            current = ' aria-current="page"' if slug == "start" else ""
            icon, _tone = TOPIC_META[slug]
            links.append(f'<a class="app-guide-nav-link" href="#guide-topic-{escape(slug)}" data-guide-nav-target="{escape(slug)}"{current}><span>{_icon(icon)}</span>{escape(label)}</a>')
            mobile.append(f'<option value="{escape(slug)}">{escape(group)} — {escape(label)}</option>')
        desktop.append(f'<div class="app-guide-nav-group"><span>{escape(group)}</span>{"".join(links)}</div>')
    return "".join(desktop), "".join(mobile)


def _search_result(result_id: str, kind: str, title: str, description: str, target: str, search_text: str, *, term: str = "") -> str:
    icon = "arrow" if kind == "action" else TOPIC_META.get(target, ("book", "blue"))[0]
    term_attr = f' data-guide-term-result="{escape(term)}"' if term else ""
    marker = '<span class="app-guide-search-result-dot" aria-hidden="true"></span>' if kind == "term" else f'<span class="app-guide-search-result-icon" aria-hidden="true">{_icon(icon)}</span>'
    return f'<button id="{result_id}" type="button" role="option" aria-selected="false" class="app-guide-search-result app-guide-search-result--{kind}" data-guide-search-result data-guide-target="{escape(target)}"{term_attr} data-guide-search-text="{escape(search_text)}">{marker}<span class="app-guide-search-result-copy"><strong class="app-guide-search-result-title">{escape(title)}</strong><span class="app-guide-search-result-description">{escape(description)}</span></span></button>'


def _search_catalog() -> str:
    features = "".join(_search_result(f"guideFeatureResult{index}", "feature", t[3], t[4], t[0], " ".join((t[3], t[4], t[11]))) for index, t in enumerate(TOPICS))
    terms = "".join(_search_result(f"guideTermResult{index}", "term", term, data[0], data[2], " ".join((term, data[0], data[1])), term=term) for index, (term, data) in enumerate(TERMS.items()))
    actions = (
        ("Add or change a resume", "resumes", "Upload or select a resume version.", "upload CV profile"), ("Run job discovery", "pipeline", "Start or refresh the job pipeline.", "start jobs"),
        ("Generate AI Suggestions", "suggestions", "Review grounded tailoring ideas.", "tailor rewrite"), ("Generate suggestions in bulk", "bulk", "Open the eligible multi-job workflow.", "Results Center"),
        ("Start a New Scan", "optimization", "Compare a resume with one job.", "job description"), ("Exclude or Re-include", "optimization", "Make a reversible requirement choice.", "missing scoring"),
        ("Save review choices", "finish", "Preserve the current review state.", "save"), ("Compare and export", "finish", "Inspect and download PDF or DOCX.", "before after"),
        ("Record a job decision", "decisions", "Track Apply, Tailor, Skip, or Hold.", "choice"), ("Track a manual application", "applications", "Record Applied or Saved for Later.", "status"),
        ("Reopen a saved scan", "saved", "Return to an earlier report.", "recent activity"), ("Review notifications", "notifications", "Open recent pipeline activity.", "bell unread"),
        ("Ask the Job Assistant", "assistant", "Search jobs with grounded chat.", "conversation"),
    )
    action_html = "".join(_search_result(f"guideActionResult{index}", "action", label, description, slug, f"{label} {aliases}") for index, (label, slug, description, aliases) in enumerate(actions))
    return f'<section class="app-guide-search-group" data-guide-result-group="features"><h2>Features</h2><div>{features}</div></section><section class="app-guide-search-group" data-guide-result-group="terms"><h2>Terms</h2><div>{terms}</div></section><section class="app-guide-search-group" data-guide-result-group="actions"><h2>Actions</h2><div>{action_html}</div></section>'


def _search_surface() -> str:
    return f'''<div class="app-guide-search-shell"><label class="app-guide-search" for="appGuideSearch">{_icon('search')}<span class="visually-hidden">Search the App Guide</span><input class="app-guide-search-input" id="appGuideSearch" type="search" autocomplete="off" placeholder="Search features, actions, or terms…" aria-controls="appGuideSearchPanel" aria-describedby="appGuideSearchStatus" aria-expanded="false" aria-autocomplete="list" /><kbd aria-hidden="true">⌘ K</kbd></label><button class="app-guide-clear-search" id="appGuideClearSearch" type="button" hidden>Clear</button><div class="app-guide-search-panel" id="appGuideSearchPanel" role="listbox" aria-label="Guide search results" hidden><div class="app-guide-search-status" id="appGuideSearchStatus" role="status" aria-live="polite">Type to search the guide</div>{_search_catalog()}<div class="app-guide-search-empty" id="appGuideSearchEmpty" hidden>No features, terms, or actions match that search.</div></div></div>'''


def _context_rail() -> str:
    rows = (
        ("green", "Matched", "Relevant evidence was found."),
        ("rose", "Missing", "Enough visible evidence was not found."),
        ("blue", "Ready", "A reviewable state, not approval."),
        ("teal", "Safe / no rewrite", "Reviewed successfully; no rewrite needed."),
    )
    term_rows = "".join(
        f'<div class="app-guide-rail-term-row"><span class="app-guide-term-dot app-guide-term-dot--{tone}" aria-hidden="true"><i></i></span>'
        f'<span><strong>{escape(term)}</strong><small>{escape(description)}</small></span></div>'
        for tone, term, description in rows
    )
    return f'''
      <aside class="app-guide-rail" aria-label="Guide context">
        <section class="app-guide-rail-card app-guide-rail-card--trust">
          <div class="app-guide-rail-header"><span class="app-guide-rail-icon">{_icon('shield')}</span><h2>What you can trust</h2></div>
          <ul><li><span class="app-guide-trust-check" aria-hidden="true">{_icon('check')}</span><span><strong>AI suggests. You decide.</strong></span></li><li><span class="app-guide-trust-check" aria-hidden="true">{_icon('check')}</span><span>Your evidence is the boundary.</span></li><li><span class="app-guide-trust-check" aria-hidden="true">{_icon('check')}</span><span>A score is guidance, not an ATS score or interview guarantee.</span></li><li><span class="app-guide-trust-check" aria-hidden="true">{_icon('check')}</span><span>Exclude is reversible and does not delete a skill.</span></li><li><span class="app-guide-trust-check" aria-hidden="true">{_icon('check')}</span><span>Save is not Apply.</span></li><li><span class="app-guide-trust-check" aria-hidden="true">{_icon('check')}</span><span>Export is still yours; it does not submit.</span></li></ul>
        </section>
        <div id="appGuideRailStart">
          <section class="app-guide-rail-card app-guide-rail-card--terms">
            <div class="app-guide-rail-header"><span class="app-guide-rail-icon app-guide-rail-icon--terms">{_icon('book')}</span><h2>Common terms</h2></div>
            <div class="app-guide-rail-term-list">{term_rows}</div>
            <a href="#guide-topic-glossary" data-guide-nav-target="glossary">See all terms{_icon('arrow')}</a>
          </section>
        </div>
        <section class="app-guide-rail-card app-guide-rail-card--help" id="appGuideRailHelp" hidden><div class="app-guide-rail-header"><span class="app-guide-rail-icon">{_icon('layers')}</span><h2>Need more help?</h2></div><p>Explore the Guide from the beginning or search for a specific feature.</p><a href="#guide-topic-start" id="appGuideBackToStart" data-guide-nav-target="start">Back to Start here{_icon('arrow')}</a></section>
        <section class="app-guide-rail-card app-guide-rail-card--context" id="appGuideRailContext" hidden><span class="app-guide-section-kicker">In this section</span><h2 id="appGuideRailTopicTitle">Topic terms</h2><div class="app-guide-rail-chips" id="appGuideRailChips"></div><div class="app-guide-rail-definition" aria-live="polite"><strong id="appGuideRailTermTitle"></strong><p id="appGuideRailTermCopy"></p></div></section>
      </aside>
    '''


@router.get("/guide", response_class=HTMLResponse)
def app_guide_page() -> str:
    desktop_nav, mobile_options = _navigation()
    articles = [_start_article()]
    for index, topic in enumerate(TOPICS):
        next_slug, next_label = (TOPICS[index + 1][0], TOPICS[index + 1][3]) if index + 1 < len(TOPICS) else ("glossary", "Glossary")
        articles.append(_topic_article(topic, next_slug, next_label))
    articles.append(_glossary_article())
    return f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>ApplyLens AI Guide</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" /><link rel="stylesheet" href="/static/styles.css?v=eucalyptus_action_cascade_r2" /><link rel="stylesheet" href="/static/app_redesign.css?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1" /><link rel="stylesheet" href="/static/app_guide.css?v=applylens_guide_r7" />
</head><body class="app-guide-body">{render_top_shell('/guide')}<main class="page app-guide-page" id="mainContent">
  <div class="app-guide-global-header" aria-hidden="true"></div>
  <div class="app-guide-workspace">
    <aside class="app-guide-nav" aria-label="App Guide topics"><div class="app-guide-nav-heading"><span>{_icon('book')}</span><div><strong>App Guide</strong><small>Product manual</small></div></div><button type="button" class="app-guide-nav-search" id="appGuideNavSearch">{_icon('search')}<span>Search guide…</span><kbd aria-hidden="true">⌘K</kbd></button><nav>{desktop_nav}</nav></aside>
    <div class="app-guide-content-scroll" id="appGuideContentScroll">
      <div class="app-guide-mobile-nav"><label for="appGuideTopicSelect">Guide topic</label><select id="appGuideTopicSelect">{mobile_options}</select></div>
      <div class="app-guide-content-grid">
        <section class="app-guide-content" id="appGuideContent" aria-label="Guide content">{''.join(articles)}</section>
        {_context_rail()}
      </div>
    </div>
  </div>
</main><script src="/static/vendor/tabler/tabler.min.js"></script><script src="/static/shell.js?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1"></script><script src="/static/app_guide.js?v=applylens_guide_r7"></script></body></html>
    """.strip()
