from pathlib import Path


def test_source_yield_root_is_unique_and_precedes_pipeline_meta_and_queue():
    source = Path("src/app/ui.py").read_text(encoding="utf-8")
    assert source.count('id="sourceYieldRoot"') == 1
    assert source.index('id="executiveKpiRoot"') < source.index('id="sourceYieldRoot"')
    assert source.index('id="sourceYieldRoot"') < source.index('id="pipelineRunMeta"')
    assert source.index('id="sourceYieldRoot"') < source.index('id="executiveQueueRoot"')


def test_existing_status_bridge_publishes_all_source_yield_states():
    source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    assert '"applylens:source-yield-state"' in source
    status_block = source[source.index("async function loadStatus("):source.index("async function loadBrowse(")]
    assert 'publishSourceYieldState({ status: "loading" })' in status_block
    assert 'status: "ready", data: data.source_yield || null' in status_block
    assert 'status: "error"' in status_block


def test_status_endpoint_preserves_authenticated_owner_scope():
    source = Path("src/app/api.py").read_text(encoding="utf-8")
    status_block = source[source.index('@app.get("/status")'):source.index('@app.get("/pipeline/status")')]
    assert "owner_user_id=_auth_owner_user_id(http_request)" in status_block


def test_status_payload_includes_the_source_yield_read_model():
    source = Path("src/app/services.py").read_text(encoding="utf-8")
    status_block = source[source.index("def status_payload("):source.index("def _validated_browse_preference_ids(")]
    assert '"source_yield": source_yield' in status_block


def test_source_yield_styles_and_generated_mount_cover_theme_and_responsiveness():
    styles = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    component = Path("frontend/executive-kpi/src/SourceYield.tsx").read_text(encoding="utf-8")
    bundle = Path("src/app/static/build/executive-kpi/executive-kpi.js").read_text(encoding="utf-8")
    assert 'html[data-theme="dark"] #sourceYieldRoot' in styles
    assert "overflow: auto" in styles
    assert "@media (max-width: 760px)" in styles
    assert 'aria-expanded={expanded}' in component
    assert not any(name in component.lower() for name in ("greenhouse", "workday", "ashby", "workable", "recruitee"))
    assert "sourceYieldRoot" in bundle
    assert "Source Yield" in bundle


def test_source_button_uses_muted_token_surface_without_a_gradient():
    redesign = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    scoped = redesign[
        redesign.index("body .source-yield-source-button {"):
        redesign.index("\ninput,", redesign.index("body .source-yield-source-button {"))
    ]
    assert "linear-gradient" not in scoped
    assert "var(--app-surface-3)" in scoped
    assert "var(--app-border-2)" in scoped
    assert "var(--app-text)" in scoped
    assert 'html[data-theme="dark"] body .source-yield-source-button' in scoped
