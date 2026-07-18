import re
from pathlib import Path

from src.app.ui import executive_dashboard


ROOT = Path(__file__).resolve().parents[1]
UI_PATH = ROOT / "src/app/ui.py"
APP_JS_PATH = ROOT / "src/app/static/app.js"
COMPONENT_PATH = ROOT / "frontend/executive-kpi/src/AnalyticsDashboard.tsx"
MAIN_PATH = ROOT / "frontend/executive-kpi/src/main.tsx"
PACKAGE_PATH = ROOT / "frontend/executive-kpi/package.json"
LOCK_PATH = ROOT / "frontend/executive-kpi/package-lock.json"
BUNDLE_DIR = ROOT / "src/app/static/build/executive-kpi"


def test_executive_route_keeps_kpi_mount_and_uses_one_react_queue_mount():
    markup = executive_dashboard()

    assert markup.count('id="executiveKpiRoot"') == 1
    assert "/static/build/executive-kpi/executive-kpi.css?v=phase133a" in markup
    assert (
        '<script type="module" '
        'src="/static/build/executive-kpi/executive-kpi.js?v=phase133a_fix1"></script>'
        in markup
    )

    for legacy_id in (
        "statQueueRows",
        "statDecisionRows",
        "statUndecidedApplyReview",
        "statUndecidedMaybeTailor",
    ):
        assert legacy_id not in markup

    for preserved_marker in (
        "Executive Queue",
        "Refresh Status",
        "Run Live Pipeline",
        'id="executiveQueueRoot"',
    ):
        assert preserved_marker in markup

    assert markup.count('id="executiveQueueRoot"') == 1
    for retired_legacy_id in (
        'id="actionFilter"',
        'id="preferenceFilter"',
        'name="executiveViewMode"',
        'id="queueTable"',
        'id="queuePaginationActions"',
    ):
        assert retired_legacy_id not in markup


def test_react_component_preserves_four_metric_meanings_and_real_snapshot_only():
    component = COMPONENT_PATH.read_text(encoding="utf-8")

    for label in (
        "Queue Rows",
        "Next Steps",
        "Undecided Job Reviews",
        "Undecided Maybe Tailor",
    ):
        assert label in component

    assert "Current snapshot" in component
    assert "queueRows" in component
    assert "Math.random" not in component
    assert "sparkline" not in component.lower()
    assert "up 12%" not in component.lower()
    assert "https://21st.dev/@dhileepkumargm/components/analytics-dashboard" in component
    assert 'from "recharts"' in component
    assert 'from "lucide-react"' in component


def test_existing_status_owner_publishes_loading_success_error_and_refreshes():
    source = APP_JS_PATH.read_text(encoding="utf-8")

    assert 'fetchJson("/status")' in source
    assert 'const EXECUTIVE_KPI_EVENT_NAME = "applylens:executive-kpi-state"' in source
    assert "new CustomEvent(EXECUTIVE_KPI_EVENT_NAME, { detail })" in source
    assert 'publishExecutiveKpiState({ status: "loading" })' in source
    assert 'status: "ready"' in source
    assert 'status: "error"' in source
    assert "await loadStatus();" in source
    assert 'refreshStatusBtn.addEventListener("click"' in source

    for source_field in (
        "summary.execution_queue_rows",
        "summary.operator_decisions_rows",
        "undecided.APPLY_REVIEW_VARIANTS",
        "undecided.MAYBE_TAILOR",
    ):
        assert source_field in source


def test_react_island_has_no_independent_network_owner_and_handles_event_updates():
    source = MAIN_PATH.read_text(encoding="utf-8")

    assert "applylens:executive-kpi-state" in source
    assert "addEventListener(KPI_EVENT_NAME" in source
    assert "removeEventListener(KPI_EVENT_NAME" in source
    assert "fetch(" not in source
    assert "setInterval(" not in source
    assert "createRoot(mount)" in source


def test_frontend_build_is_locked_scoped_and_available_to_fastapi():
    package = PACKAGE_PATH.read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert LOCK_PATH.is_file()
    assert '"react"' in package
    assert '"recharts"' in package
    assert '"lucide-react"' in package
    assert '"@tanstack/react-table"' in package
    assert '"tailwindcss"' in package
    assert '"vite"' in package
    assert "https://" not in package
    assert (BUNDLE_DIR / "executive-kpi.js").is_file()
    assert (BUNDLE_DIR / "executive-kpi.css").is_file()
    assert "FROM node:22-alpine AS executive-kpi-builder" in dockerfile
    assert "FROM python:3.12-slim" in dockerfile
    assert "npm ci" in dockerfile
    assert "npm run build" in dockerfile
    assert "frontend/executive-kpi" in readme
    assert "npm ci" in readme
    assert "npm run build" in readme


def test_rendered_asset_urls_resolve_to_complete_production_bundle():
    markup = executive_dashboard()
    bundle = (BUNDLE_DIR / "executive-kpi.js").read_text(encoding="utf-8")
    generated_names = sorted(path.name for path in BUNDLE_DIR.iterdir())

    static_urls = re.findall(
        r'(?:href|src)="(/static/build/executive-kpi/[^"?]+)(?:\?[^\"]+)?"',
        markup,
    )
    assert static_urls == [
        "/static/build/executive-kpi/executive-kpi.css",
        "/static/build/executive-kpi/executive-kpi.js",
    ]
    for static_url in static_urls:
        assert (ROOT / "src/app/static" / static_url.removeprefix("/static/")).is_file()

    assert set(generated_names) == {
        "executive-kpi.css",
        "executive-kpi.js",
    }
    assert len([name for name in generated_names if name.endswith(".js")]) == 1
    assert len([name for name in generated_names if name.endswith(".css")]) == 1
    assert not any(re.search(r" \d+\.(?:css|js)$", name) for name in generated_names)
    assert "\nimport " not in bundle

    assert "executiveKpiRoot" in bundle
    assert "applylens:executive-kpi-state" in bundle
    assert "executiveQueueRoot" in bundle
    assert "applylens:executive-queue-state" in bundle
    assert "applylens:executive-queue-action" in bundle
    assert "process.env" not in bundle
    assert "localhost" not in bundle
    assert "/assets/" not in bundle


def test_tailwind_is_scoped_and_does_not_reset_the_server_rendered_page():
    config = (ROOT / "frontend/executive-kpi/tailwind.config.cjs").read_text(encoding="utf-8")
    styles = (ROOT / "frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")

    assert 'prefix: "kpi-"' in config
    assert "preflight: false" in config
    assert "@tailwind base" not in styles
    assert "#executiveKpiRoot" in styles
    assert "#executiveQueueRoot" in styles
    assert "html[data-theme=\"dark\"] #executiveKpiRoot" in styles
    assert "html[data-theme=\"dark\"] #executiveQueueRoot" in styles


def test_kpi_tooltip_escapes_vertically_without_global_overflow_or_fake_history():
    component = COMPONENT_PATH.read_text(encoding="utf-8")
    styles = (ROOT / "frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")

    assert "allowEscapeViewBox={{ x: false, y: true }}" in component
    assert 'wrapperStyle={{ zIndex: 30, pointerEvents: "none" }}' in component
    assert "export function SnapshotTooltip" in component
    assert ".executive-kpi-card:hover" in styles
    assert ".executive-kpi-chart .recharts-tooltip-wrapper" in styles
    assert "pointer-events: none" in styles
    assert "fake history" not in component.lower()
