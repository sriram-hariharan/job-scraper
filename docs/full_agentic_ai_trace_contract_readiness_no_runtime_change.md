# Full Agentic AI Trace Contract Readiness Audit

## Purpose

This checkpoint audits the existing trace contract for the full-fledged ApplyLens AI agentic roadmap.

This is intentionally docs/tests only.

No runtime behavior is changed.

No API behavior is changed.

No storage schema is changed.

No migration is executed.

No scheduler behavior is changed.

No pipeline behavior is changed.

## Branch

`full-agentic-ai-trace-contract-readiness-no-runtime-change`

## Scope

This audit maps the current trace-related surfaces across:

- trace storage schema
- trace store helpers
- agent trace helper module
- trace-producing agents
- app service payloads
- API read-only trace surfaces
- Agentic Review UI
- pipeline collector trace call sites

## Contract inventory

### `src/storage/agent_trace/schema.sql`

Status: `present`

SQL tables detected:

- `agent_runs`
- `agent_steps`

Trace-related line inventory:

- L1: `CREATE TABLE IF NOT EXISTS agent_runs (`
- L2: `agent_run_id TEXT PRIMARY KEY,`
- L3: `owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,`
- L4: `pipeline_run_id TEXT NOT NULL DEFAULT '',`
- L13: `CREATE INDEX IF NOT EXISTS idx_agent_runs_owner_started`
- L14: `ON agent_runs (owner_user_id, started_at DESC);`
- L16: `CREATE INDEX IF NOT EXISTS idx_agent_runs_pipeline_started`
- L17: `ON agent_runs (pipeline_run_id, started_at DESC);`
- L19: `CREATE INDEX IF NOT EXISTS idx_agent_runs_context_started`
- L20: `ON agent_runs (context_id, started_at DESC);`
- L22: `CREATE INDEX IF NOT EXISTS idx_agent_runs_status_started`
- L23: `ON agent_runs (status, started_at DESC);`
- L25: `CREATE TABLE IF NOT EXISTS agent_steps (`
- L27: `agent_run_id TEXT NOT NULL REFERENCES agent_runs(agent_run_id) ON DELETE CASCADE,`
- L28: `owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,`
- L29: `pipeline_run_id TEXT NOT NULL DEFAULT '',`
- L47: `CREATE INDEX IF NOT EXISTS idx_agent_steps_run_started`
- L48: `ON agent_steps (agent_run_id, started_at);`
- L50: `CREATE INDEX IF NOT EXISTS idx_agent_steps_owner_started`
- L51: `ON agent_steps (owner_user_id, started_at DESC);`
- L53: `CREATE INDEX IF NOT EXISTS idx_agent_steps_pipeline_started`
- L54: `ON agent_steps (pipeline_run_id, started_at DESC);`
- L56: `CREATE INDEX IF NOT EXISTS idx_agent_steps_context_started`
- L57: `ON agent_steps (context_id, started_at DESC);`
- L59: `CREATE INDEX IF NOT EXISTS idx_agent_steps_status_started`
- L60: `ON agent_steps (status, started_at DESC);`

### `src/storage/agent_trace/store.py`

Status: `present`

Top-level Python definitions detected:

- `_clean_text`
- `_utc_now_iso`
- `_json_compact`
- `_sql_quote_text`
- `_sql_jsonb`
- `_sql_nullable_timestamptz`
- `_sql_nullable_int`
- `_read_sql_artifact`
- `agent_trace_schema_sql_text`
- `render_agent_trace_schema_sql`
- `agent_trace_schema_sql_payload`
- `agent_trace_schema_sql_generation_payload`
- `agent_trace_table_specs`
- `agent_trace_contract_health_payload`
- `_resolve_database_url`
- `_redact_database_url`
- `_run_postgres_json_query`
- `_agent_trace_query_payload_from_row`
- `_schema_prefix`
- `_require_owner_user_id`
- `_require_agent_run_id`
- `_require_agent_step_id`
- `build_agent_run_id`
- `build_agent_step_id`
- `agent_run_db_row`
- `agent_step_db_row`
- `create_agent_run_postgres_payload`
- `complete_agent_run_postgres_payload`
- `fail_agent_run_postgres_payload`
- `_update_agent_run_status_postgres_payload`
- `record_agent_step_postgres_payload`
- `complete_agent_step_postgres_payload`
- `fail_agent_step_postgres_payload`
- `_update_agent_step_status_postgres_payload`
- `get_agent_run_postgres_payload`
- `list_agent_runs_postgres_payload`
- `list_agent_steps_postgres_payload`

Trace-related line inventory:

- L15: `DEFAULT_AGENT_TRACE_SCHEMA_SQL_PATH = Path("src/storage/agent_trace/schema.sql")`
- L64: `def agent_trace_schema_sql_text(`
- L65: `schema_path: Path = DEFAULT_AGENT_TRACE_SCHEMA_SQL_PATH,`
- L70: `def render_agent_trace_schema_sql() -> str:`
- L73: `"CREATE TABLE IF NOT EXISTS agent_runs (",`
- L74: `"    agent_run_id TEXT PRIMARY KEY,",`
- L75: `"    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",`
- L76: `"    pipeline_run_id TEXT NOT NULL DEFAULT '',",`
- L85: `"CREATE INDEX IF NOT EXISTS idx_agent_runs_owner_started",`
- L86: `"ON agent_runs (owner_user_id, started_at DESC);",`
- L88: `"CREATE INDEX IF NOT EXISTS idx_agent_runs_pipeline_started",`
- L89: `"ON agent_runs (pipeline_run_id, started_at DESC);",`
- L91: `"CREATE INDEX IF NOT EXISTS idx_agent_runs_context_started",`
- L92: `"ON agent_runs (context_id, started_at DESC);",`
- L94: `"CREATE INDEX IF NOT EXISTS idx_agent_runs_status_started",`
- L95: `"ON agent_runs (status, started_at DESC);",`
- L97: `"CREATE TABLE IF NOT EXISTS agent_steps (",`
- L99: `"    agent_run_id TEXT NOT NULL REFERENCES agent_runs(agent_run_id) ON DELETE CASCADE,",`
- L100: `"    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",`
- L101: `"    pipeline_run_id TEXT NOT NULL DEFAULT '',",`
- L119: `"CREATE INDEX IF NOT EXISTS idx_agent_steps_run_started",`
- L120: `"ON agent_steps (agent_run_id, started_at);",`
- L122: `"CREATE INDEX IF NOT EXISTS idx_agent_steps_owner_started",`
- L123: `"ON agent_steps (owner_user_id, started_at DESC);",`
- L125: `"CREATE INDEX IF NOT EXISTS idx_agent_steps_pipeline_started",`
- L126: `"ON agent_steps (pipeline_run_id, started_at DESC);",`
- L128: `"CREATE INDEX IF NOT EXISTS idx_agent_steps_context_started",`
- L129: `"ON agent_steps (context_id, started_at DESC);",`
- L131: `"CREATE INDEX IF NOT EXISTS idx_agent_steps_status_started",`
- L132: `"ON agent_steps (status, started_at DESC);",`
- L137: `def agent_trace_schema_sql_payload(`
- L138: `schema_path: Path = DEFAULT_AGENT_TRACE_SCHEMA_SQL_PATH,`
- L140: `return {"path": str(Path(schema_path)), "sql": agent_trace_schema_sql_text(schema_path)}`
- L143: `def agent_trace_schema_sql_generation_payload(`
- L144: `schema_path: Path = DEFAULT_AGENT_TRACE_SCHEMA_SQL_PATH,`
- L146: `generated_sql = render_agent_trace_schema_sql()`
- L147: `artifact_sql = agent_trace_schema_sql_text(schema_path)`
- L156: `def agent_trace_table_specs() -> Dict[str, Any]:`
- L158: `"agent_runs": {`
- L159: `"primary_key": ["agent_run_id"],`

### `src/agents/trace.py`

Status: `present`

Top-level Python definitions detected:

- `trace_recorder_safety_flags`
- `_snapshot`
- `_snapshots`
- `build_agent_run_record_payload`
- `build_agent_step_record_payload`
- `build_agent_trace_recording_payload`
- `build_fake_smoke_trace_payload`
- `execute_agent_trace_recording`
- `create_agent_run`
- `complete_agent_run`
- `fail_agent_run`
- `record_agent_step`
- `complete_agent_step`
- `fail_agent_step`
- `get_agent_run`
- `list_agent_runs`
- `list_agent_steps`

Trace-related line inventory:

- L8: `build_agent_run_snapshot,`
- L12: `from src.storage.agent_trace.store import (`
- L13: `complete_agent_run_postgres_payload,`
- L15: `create_agent_run_postgres_payload,`
- L16: `fail_agent_run_postgres_payload,`
- L18: `get_agent_run_postgres_payload,`
- L19: `list_agent_runs_postgres_payload,`
- L20: `list_agent_steps_postgres_payload,`
- L21: `record_agent_step_postgres_payload,`
- L25: `TRACE_RECORDER_SAFETY_FLAGS: dict[str, bool] = {`
- L41: `def trace_recorder_safety_flags() -> dict[str, bool]:`
- L42: `return dict(TRACE_RECORDER_SAFETY_FLAGS)`
- L55: `def build_agent_run_record_payload(run_snapshot: dict[str, Any]) -> dict[str, Any]:`
- L57: `prepared = agent_state_store.prepare_agent_run_upsert(snapshot)`
- L59: `"operation": "record_agent_run_snapshot",`
- L60: `"record_type": "agent_run",`
- L61: `"table": "agent_runs",`
- L64: `**trace_recorder_safety_flags(),`
- L68: `def build_agent_step_record_payload(step_snapshot: dict[str, Any]) -> dict[str, Any]:`
- L70: `prepared = agent_state_store.prepare_agent_step_upsert(snapshot)`
- L72: `"operation": "record_agent_step_snapshot",`
- L73: `"record_type": "agent_step",`
- L74: `"table": "agent_steps",`
- L77: `**trace_recorder_safety_flags(),`
- L81: `def build_agent_trace_recording_payload(`
- L86: `run_record = build_agent_run_record_payload(run_snapshot)`
- L87: `step_records = [`
- L88: `build_agent_step_record_payload(step_snapshot)`
- L91: `operations = [run_record, *step_records]`
- L93: `"operation": "build_agent_trace_recording_payload",`
- L95: `"step_count": len(step_records),`
- L96: `"record_count": len(operations),`
- L97: `"records": operations,`
- L98: `**trace_recorder_safety_flags(),`
- L102: `def build_fake_smoke_trace_payload() -> dict[str, Any]:`
- L110: `metadata={"source": "trace_recorder_smoke"},`
- L112: `run_snapshot = build_agent_run_snapshot(`
- L126: `agent_run_id=run_snapshot["agent_run_id"],`
- L132: `return build_agent_trace_recording_payload(`
- L138: `def execute_agent_trace_recording(`

### `src/agents/critic_agent.py`

Status: `present`

Top-level Python definitions detected:

- `_clean_text`
- `_utc_now_iso`
- `_normalize_term`
- `_normalize_text`
- `_as_list`
- `_joined_allowed_text`
- `_evidence_text`
- `_allowed_terms`
- `_proposed_terms`
- `_unsupported_terms`
- `_numeric_claims`
- `_unsupported_numeric_claims`
- `_evidence_spans`
- `build_critic_agent_input_payload`
- `evaluate_critic_suggestion`
- `build_critic_agent_validation_payload`
- `render_critic_decision`
- `build_critic_agent_summary_payload`
- `agent_trace_enabled`
- `agent_trace_strict`
- `trace_context_from_env`
- `record_critic_agent_trace`

Trace-related line inventory:

- L179: `pipeline_run_id: str = "",`
- L180: `owner_user_id: str = "",`
- L187: `"pipeline_run_id": _clean_text(pipeline_run_id),`
- L188: `"owner_user_id": _clean_text(owner_user_id),`
- L344: `"pipeline_run_id": _clean_text(input_payloads[0].get("pipeline_run_id")) if input_payloads else "",`
- L345: `"owner_user_id": _clean_text(input_payloads[0].get("owner_user_id")) if input_payloads else "",`
- L355: `def agent_trace_enabled(env: Dict[str, str] \| None = None) -> bool:`
- L360: `def agent_trace_strict(env: Dict[str, str] \| None = None) -> bool:`
- L367: `pipeline_run_id = (`
- L368: `_clean_text(env_map.get("JOB_APP_PIPELINE_RUN_ID"))`
- L369: `or _clean_text(env_map.get("JOB_STACK_USER_PIPELINE_RUN_ID"))`
- L371: `owner_user_id = _clean_text(env_map.get("JOB_STACK_OWNER_USER_ID"))`
- L373: `if not context_id and pipeline_run_id:`
- L374: `context_id = f"critic:{pipeline_run_id}"`
- L376: `"pipeline_run_id": pipeline_run_id,`
- L377: `"owner_user_id": owner_user_id,`
- L382: `def record_critic_agent_trace(`
- L389: `if not agent_trace_enabled(env_map):`
- L393: `if not context["owner_user_id"] or not context["pipeline_run_id"]:`
- L401: `"pipeline_run_id": payload.get("pipeline_run_id") or context["pipeline_run_id"],`
- L402: `"owner_user_id": payload.get("owner_user_id") or context["owner_user_id"],`
- L422: `run_payload = trace_module.create_agent_run(`
- L423: `record={`
- L424: `"owner_user_id": context["owner_user_id"],`
- L425: `"pipeline_run_id": context["pipeline_run_id"],`
- L432: `agent_run_id = _clean_text((run_payload.get("run") or {}).get("agent_run_id"))`
- L433: `if not agent_run_id:`
- L434: `raise RuntimeError("Agent trace run did not return agent_run_id.")`
- L443: `step_record = llmops.merge_llmops_into_agent_step_kwargs(`
- L445: `"agent_run_id": agent_run_id,`
- L446: `"owner_user_id": context["owner_user_id"],`
- L447: `"pipeline_run_id": context["pipeline_run_id"],`
- L457: `step_payload = trace_module.record_agent_step(`
- L458: `record=step_record`
- L467: `owner_user_id=context["owner_user_id"],`
- L472: `trace_module.complete_agent_run(`
- L473: `agent_run_id=agent_run_id,`
- L474: `owner_user_id=context["owner_user_id"],`
- L480: `"recorded": True,`
- L481: `"agent_run_id": agent_run_id,`

### `src/agents/source_health_agent.py`

Status: `present`

Top-level Python definitions detected:

- `_clean_text`
- `_utc_now_iso`
- `_int_value`
- `_source_key`
- `_company_label`
- `_sum_by_source`
- `parse_source_health_report_csv`
- `build_source_health_agent_input_payload`
- `recommend_source_health_row`
- `build_source_health_agent_output_payload`
- `build_source_health_agent_validation_payload`
- `build_source_health_agent_summary_payload`
- `render_source_health_recommendations`
- `agent_trace_enabled`
- `agent_trace_strict`
- `trace_context_from_env`
- `record_source_health_agent_trace`

Trace-related line inventory:

- L76: `pipeline_run_id: str = "",`
- L84: `"pipeline_run_id": _clean_text(pipeline_run_id),`
- L229: `"pipeline_run_id": input_payload.get("pipeline_run_id", ""),`
- L240: `pipeline_run_id: str = "",`
- L246: `pipeline_run_id=pipeline_run_id,`
- L269: `def agent_trace_enabled(env: Dict[str, str] \| None = None) -> bool:`
- L274: `def agent_trace_strict(env: Dict[str, str] \| None = None) -> bool:`
- L281: `pipeline_run_id = (`
- L282: `_clean_text(env_map.get("JOB_APP_PIPELINE_RUN_ID"))`
- L283: `or _clean_text(env_map.get("JOB_STACK_USER_PIPELINE_RUN_ID"))`
- L285: `owner_user_id = _clean_text(env_map.get("JOB_STACK_OWNER_USER_ID"))`
- L287: `if not context_id and pipeline_run_id:`
- L288: `context_id = f"source_health:{pipeline_run_id}"`
- L290: `"pipeline_run_id": pipeline_run_id,`
- L291: `"owner_user_id": owner_user_id,`
- L296: `def record_source_health_agent_trace(`
- L305: `if not agent_trace_enabled(env_map):`
- L309: `if not context["owner_user_id"] or not context["pipeline_run_id"]:`
- L316: `pipeline_run_id=context["pipeline_run_id"],`
- L320: `run_payload = trace_module.create_agent_run(`
- L321: `record={`
- L322: `"owner_user_id": context["owner_user_id"],`
- L323: `"pipeline_run_id": context["pipeline_run_id"],`
- L330: `agent_run_id = _clean_text((run_payload.get("run") or {}).get("agent_run_id"))`
- L331: `if not agent_run_id:`
- L332: `raise RuntimeError("Agent trace run did not return agent_run_id.")`
- L341: `step_record = llmops.merge_llmops_into_agent_step_kwargs(`
- L343: `"agent_run_id": agent_run_id,`
- L344: `"owner_user_id": context["owner_user_id"],`
- L345: `"pipeline_run_id": context["pipeline_run_id"],`
- L355: `step_payload = trace_module.record_agent_step(`
- L356: `record=step_record`
- L365: `owner_user_id=context["owner_user_id"],`
- L370: `trace_module.complete_agent_run(`
- L371: `agent_run_id=agent_run_id,`
- L372: `owner_user_id=context["owner_user_id"],`
- L378: `"recorded": True,`
- L379: `"agent_run_id": agent_run_id,`
- L385: `if agent_trace_strict(env_map):`
- L387: `return {"attempted": True, "recorded": False, "warning": str(exc)}`

### `src/app/services.py`

Status: `present`

Top-level Python definitions detected:

- `_app_service_safety_gate_int`
- `_app_service_safety_gate_result`
- `app_service_agentic_workflow_safety_gate_payload`
- `app_service_persist_agentic_approval_request`
- `_invalidate_patch_selection_overlay_cache`
- `_patch_selection_overlay_cache_version`
- `_job_metadata_overlay_cache_key`
- `_tailoring_workspace_button_state_cache_key`
- `_safe_owner_dir_name`
- `_safe_run_dir_name`
- `_pipeline_scratch_output_dir`
- `_sanitize_resume_filename`
- `_sanitize_scan_upload_filename`
- `profile_resumes_payload`
- `_role_family_options_payload`
- `profile_resume_role_mappings_payload`
- `save_profile_resume_role_mapping_payload`
- `delete_profile_resume_role_mapping_service_payload`
- `_onboarding_requirement_status`
- `onboarding_preferences_payload`
- `save_onboarding_preferences_payload`
- `onboarding_status_payload`
- `_preferences_for_pipeline`
- `_selected_role_families_for_pipeline`
- `_public_admin_user_row`
- `admin_profile_users_payload`
- `admin_profile_update_user_access_payload`
- `admin_profile_delete_user_payload`
- `_pipeline_run_public_row`
- `profile_pipeline_runs_payload`
- `_user_pipeline_run_and_artifacts`
- `profile_pipeline_run_detail_payload`
- `profile_pipeline_run_agentic_review_payload`
- `_agent_trace_empty_payload`
- `_agent_trace_json`
- `_agent_trace_int`
- `_agent_trace_public_step`
- `_agent_trace_public_run`
- `_agent_trace_step_is_warning`
- `_agent_trace_rows_for_owner_pipeline`
- `agent_trace_payload`
- `record_agent_feedback_payload`
- `_safe_feedback_limit`
- `_empty_agent_feedback_summary_payload`
- `list_agent_feedback_payload`
- `agent_feedback_summary_payload`
- `agent_feedback_export_payload`
- `_rerun_config_from_pipeline_record`
- `profile_pipeline_rerun_payload`
- `user_pipeline_gate_payload`
- `profile_upload_resume_payload`
- `profile_delete_resume_payload`
- `profile_resume_file_payload`
- `_materialize_profile_resume_temp_path`
- `_scan_upload_mime_type`
- `_dual_write_saved_scan_postgres`
- `_new_scan_resume_document`
- `_build_new_scan_document_preview`
- `_new_scan_job_record`
- `_new_scan_tailoring_summary`
- `_unique_scan_terms`
- `_enrich_new_scan_resume_evidence_for_scoring`
- `_relaxed_new_scan_prefilter`
- `_build_new_scan_review_payload`
- `create_saved_scan_payload`
- `_scan_job_description_text_for_display`
- `_scan_job_context_from_record`
- `scan_workspace_job_context_payload`
- `profile_saved_scans_payload`
- `saved_scan_report_payload`
- `delete_saved_scan_payload`
- `save_saved_scan_state_payload`
- `_extract_scan_upload_text_from_pdf`
- `_extract_scan_upload_text_from_docx`
- `extract_scan_resume_upload_text_payload`
- `_utc_now`
- `_derive_pipeline_log_path`
- `_derive_pipeline_status_path`
- `_new_run_id`
- `_load_runtime_status_file`
- `_job_app`
- `_make_args`
- `_normalize_pipeline_llm_actions`
- `_normalize_delete_seen_data`
- `_new_pipeline_run_state`
- `_max_concurrent_user_pipeline_runs`
- `_active_pipeline_reservation_ttl_seconds`
- `_active_pipeline_worker_id`
- `_user_pipeline_redis_admission_lock_enabled`
- `_user_pipeline_redis_admission_lock_payload`
- `_release_user_pipeline_redis_admission_lock_payload`
- `_active_run_redis_admission_lock_payload`
- `_release_user_pipeline_active_run`
- `_clear_owner_active_pipeline_state`
- `_active_user_pipeline_run_count`
- `_owner_active_pipeline_state`
- `_set_owner_active_pipeline_state`
- `_pipeline_status_snapshot`
- `_write_runtime_status_file`
- `_pid_exists`
- `_heal_stale_running_runtime_status`
- `stop_live_pipeline_for_server_shutdown`
- `_runtime_status_is_stale_startup`
- `_is_pipeline_process_running`
- `_pipeline_terminal_statuses`
- `_status_payload_completed_finalization`
- `_status_payload_return_code`
- `_reconciled_terminal_status_payload`
- `_run_status_json_heal_payload`
- `_persist_user_pipeline_terminal_reconciliation`
- `_reconciled_user_pipeline_run_record`
- `_latest_owner_pipeline_status_payload`
- `_persist_user_pipeline_status_snapshot`
- `_pipeline_artifact_ingestion_key`
- `_pipeline_artifact_candidate_paths`
- `_pipeline_artifact_name`
- `_pipeline_artifact_kind`
- `_pipeline_artifact_content_type`
- `_read_pipeline_artifact_record`
- `_ingest_pipeline_run_artifacts_to_postgres`
- `_truthy_env_value`
- `_finalize_seen_jobs_staging_payload`
- `_pipeline_scratch_cleanup_payload`
- `_owner_db_active_pipeline_status_payload`
- `owner_pipeline_status_payload`
- `pipeline_status_payload`
- `scheduler_jobs_payload`
- `scheduler_job_command_payload`
- `_augment_launchd_config_exists`
- `scheduler_launchd_config_payload`
- `scheduler_launchd_agent_status_payload`
- `scheduler_postgres_status_payload`
- `scheduler_operator_summary_payload`
- `_normalize_scheduler_filter_text`
- `_load_scheduler_history_rows`
- `scheduler_history_payload`
- `_load_notification_rows`
- `_normalize_notification_read_flag`
- `_normalize_optional_notification_read_filter`
- `_load_latest_notification_state_overlay`
- `_apply_notification_state_overlay`
- `notifications_payload`
- `notifications_summary_payload`
- `notifications_unread_count_payload`
- `_dual_write_notification_state_postgres`
- `record_notification_read_state_payload`
- `scheduler_storage_contract_payload`
- `_pipeline_child_env_max_value_bytes`
- `_pipeline_child_env`
- `_pipeline_child_env_summary`
- `run_live_pipeline_payload`
- `_clean_text`
- `_env_flag_enabled`
- `_scan_issue_display_label`
- `_scan_issue_normalized_key`
- `_scan_issue_is_dimension_key`
- `_scan_issue_text_blob`
- `_scan_issue_text_contains_term`
- `_scan_issue_text_signal_terms`
- `_scan_issue_display_terms`
- `_scan_issue_dimension_labels`
- `_scan_issue_group_label`
- `_scan_issue_candidate_id`
- `_scan_issue_supported_signals`
- `_scan_issue_is_deterministic_only_replacement`
- `_scan_issue_title`
- `_scan_issue_group_id_for_row`
- `_scan_issue_unique_display_labels`
- `_scan_issue_canonical_term`
- `_scan_issue_term_family`
- `_scan_issue_skill_type`
- `_scan_summary_has_advanced_degree_requirement`
- `_scan_issue_score_priority`
- `_scan_issue_score_priority_weight`
- `_scan_issue_extract_summary_terms`
- `_scan_jd_text_from_record`
- `_scan_jd_context_chunk_is_metadata`
- `_scan_jd_context_anchors_for_term`
- `_scan_predicted_skill_role_key`
- `_build_predicted_skill_scan_rows`
- `_build_other_keyword_scan_rows`
- `_scan_resume_visible_term_keys`
- `_scan_resume_term_match_count`
- `_scan_resume_evidence_anchors_for_term`
- `_scan_issue_best_candidate`
- `_scan_keyword_issue_from_term`
- `_scan_keyword_rows_from_replacement_issues`
- `_scan_keyword_rows_from_non_skill_replacement_issues`
- `_scan_keyword_rows_from_generic_issues`
- `_scan_score_delta_points`
- `_scan_resume_document_text`
- `_normalize_workspace_profile_url`
- `_normalize_workspace_personal_details`
- `_extract_resume_personal_details`
- `_workspace_personal_details_contact_text`
- `_workspace_personal_details_link_items`
- `_scan_resume_bullet_texts`
- `_scan_resume_visible_search_terms`
- `_scan_searchability_issue`
- `_scan_recruiter_tip_issue`
- `_scan_formatting_issue`
- `_scan_searchability_target_title`
- `_scan_searchability_title_tokens`
- `_build_searchability_scan_issues`
- `_build_recruiter_tip_scan_issues`
- `_build_formatting_scan_issues`
- `_build_scan_match_report_summary`
- `_scan_issue_from_replacement_row`
- `_scan_issue_critic_jd_skills`
- `_scan_issue_to_critic_input`
- `_attach_critic_advisory_to_scan_issues`
- `_build_tailoring_scan_issue_contract`
- `_coerce_scan_score_value`
- `_build_tailoring_scan_score_snapshot`
- `_build_tailoring_scan_session_snapshot`
- `_build_workspace_score_preview_contract`
- `_build_workspace_draft_fragments_contract`
- `_normalize_selected_patch_candidate_ids`
- `_serialize_selected_patch_candidate_ids`
- `_load_tailoring_json_artifact`
- `_infer_packet_json_path_from_tailoring_artifact`
- `_artifact_needs_operator_rehydration`
- `_rehydrate_legacy_tailoring_operator_payload`
- `_tailoring_artifact_candidate_ids`
- `_default_selected_candidate_ids_from_replacement_plan`
- `_tailoring_artifact_signature`
- `_load_latest_patch_selection_overlay`
- `_ensure_tailoring_preview_fields`
- `_derive_workspace_button_state_from_raw_payload`
- `_tailoring_workspace_button_state`
- `_normalize_tailoring_state_filter_values`
- `_row_matches_tailoring_state_filter`
- `_apply_saved_patch_selection_overlay`
- `_sanitize_optional_resume_filename`
- `_normalize_operator_decision`
- `_operator_decision_key`
- `_validate_operator_decision_identity`
- `_resolve_resume_preview_path`
- `planning_resume_preview_path`
- `_slugify_text`
- `_load_job_doc_id_to_index`
- `_job_corpus_identity_values`
- `_job_corpus_company_title`
- `_resolve_job_index_for_regeneration`
- `_load_csv_rows_with_fieldnames`
- `_write_csv_rows`
- `_run_checked_cmd`
- `_read_regenerated_llm_status`
- `_find_planning_row_for_regeneration`
- `regenerate_selected_resume_tailoring_payload`
- `_normalize_application_status`
- `_application_action_key`
- `_validate_application_identity`
- `_dual_write_application_action_postgres`
- `_application_action_latest_sort_key`
- `_load_latest_application_actions`
- `_application_row_key_candidates`
- `_application_overlay_from_row`
- `_load_latest_application_action_overlay`
- `_overlay_application_actions`
- `_exclude_applied_rows`
- `_load_job_metadata_overlay_from_corpus`
- `_overlay_job_metadata`
- `_csv_rows_from_text`
- `_jsonl_row_count_from_text`
- `_artifact_row_by_name`
- `_artifact_text_by_name`
- `_artifact_json_by_name`
- `_agentic_workflow_summary_from_artifacts`
- `_agentic_workflow_summary_from_dir`
- `_agentic_workflow_verification_from_artifacts`
- `_agentic_workflow_manifest_from_artifacts`
- `_agentic_workflow_execution_plan_from_artifacts`
- `_agentic_workflow_dry_run_from_artifacts`
- `_read_only_adapter_preflight_from_artifacts`
- `_manual_read_only_adapter_chain_from_artifacts`
- `_explicit_read_only_chain_artifact_generation_from_artifacts`
- `_dry_run_execution_simulation_from_artifacts`
- `_proposal_only_mutation_plan_from_artifacts`
- `_operator_approval_mock_from_simulation`
- `_rag_evaluation_from_artifacts`
- `_agentic_workflow_verification_from_dir`
- `_agentic_workflow_manifest_from_dir`
- `_job_prioritization_overlay_from_rows`
- `_tailoring_decision_overlay_from_rows`
- `_operator_review_overlay_from_rows`
- `_overlay_job_prioritization`
- `_overlay_tailoring_decisions`
- `_overlay_operator_review`
- `_build_job_index_from_planning_rows`
- `_job_metadata_overlay_from_jsonl_text`
- `_overlay_job_metadata_from_map`
- `_latest_user_pipeline_artifact_context`
- `health_payload`
- `user_workspace_state_payload`
- `status_payload`
- `browse_payload`
- `review_payload`
- `workflow_payload`
- `planner_payload`
- `_resolve_planning_artifact_path`
- `planning_artifact_payload`
- `tailoring_scan_preload_payload`
- `_operator_decision_latest_sort_key`
- `_load_latest_operator_decision_rows`
- `decisions_payload`
- `_dual_write_operator_decision_postgres`
- `record_operator_resume_selection_payload`
- `preview_planning_patch_selection_payload`
- `_dual_write_patch_selection_postgres`
- `record_planning_patch_selection_payload`
- `_tailoring_workspace_draft_artifact_path`
- `_normalize_workspace_rewrite_review_decisions`
- `_normalize_workspace_manual_bullet_edits`
- `_normalize_workspace_excluded_scan_issue_ids`
- `_build_tailoring_workspace_default_draft_payload`
- `load_tailoring_workspace_draft_payload`
- `save_tailoring_workspace_draft_payload`
- `_normalize_tailoring_workspace_compare_text`
- `_normalize_tailoring_workspace_text_key`
- `_tailoring_workspace_candidate_id`
- `_tailoring_workspace_bullet_key`
- `_tailoring_workspace_surfaced_items`
- `_derive_workspace_rewrite_review_decisions`
- `_build_workspace_rewrite_review_telemetry`
- `_build_tailoring_workspace_effective_patch_specs`
- `_load_job_record_for_workspace_preview`
- `_workspace_job_record_has_substantive_context`
- `_resolve_workspace_preview_job_record`
- `_load_resume_evidence_for_workspace_preview`
- `_workspace_preview_dimension_deltas`
- `_build_workspace_counterfactual_preview`
- `preview_tailoring_workspace_draft_payload`
- `_scan_phrase_signal_terms`
- `_scan_phrase_insert_after_lead_verb`
- `_scan_phrase_append_context`
- `_scan_phrase_structured_output_contract`
- `_scan_phrase_default_provider`
- `_scan_phrase_default_model`
- `_scan_phrase_extract_first_json_value`
- `_scan_phrase_parse_options_payload`
- `_scan_phrase_deterministic_options`
- `_scan_phrase_llm_prompt`
- `_scan_phrase_validate_llm_options`
- `_generate_scan_phrase_options_with_llm`
- `generate_tailoring_scan_phrase_payload`
- `_normalize_workspace_export_format`
- `_workspace_export_output_path`
- `_workspace_export_line_is_heading`
- `_workspace_export_span_style`
- `_workspace_export_style_key`
- `_workspace_export_runs_from_spans`
- `_workspace_export_dominant_style`
- `_workspace_export_docx_font_name`
- `_workspace_export_pdf_font_name`
- `_workspace_export_finalize_paragraph`
- `_workspace_export_same_row`
- `_workspace_export_line_is_date_range`
- `_workspace_export_should_promote_to_paired_row`
- `_workspace_export_line_is_date_range`
- `_workspace_export_should_promote_to_paired_row`
- `_workspace_export_is_centered_paragraph`
- `_workspace_export_annotate_page_layout`
- `_workspace_export_line_starts_bullet`
- `_workspace_export_line_starts_strong_label`
- `_workspace_export_line_is_contact`
- `_workspace_export_line_is_centered`
- `_workspace_export_should_start_new_paragraph`
- `_extract_resume_pdf_paragraph_pages_for_export`
- `_workspace_export_has_leading_bullet`
- `_workspace_export_preserve_bullet_prefix`
- `_workspace_export_docx_has_merged_bullet_paragraphs`
- `_workspace_export_match_score`
- `_apply_workspace_export_patch_specs`
- `_workspace_export_apply_personal_details`
- `_workspace_export_is_section_heading_text`
- `_workspace_export_apply_docx_section_rule`
- `_workspace_export_pdf_contact_segments`
- `_workspace_export_draw_centered_pdf_contact_line`
- `_build_workspace_export_pdf`
- `_workspace_export_clean_docx_text`
- `_workspace_export_docx_safe_font_name`
- `_workspace_export_docx_effective_font_size`
- `_workspace_export_configure_docx_section`
- `_workspace_export_configure_docx_document_defaults`
- `_build_workspace_export_docx`
- `_workspace_export_is_likely_name_line`
- `_workspace_export_is_likely_contact_line`
- `_workspace_export_split_merged_header_contact_text`
- `_workspace_export_is_bullet_paragraph_text`
- `_workspace_export_extract_pdf_header_link_items`
- `_workspace_export_append_plain_docx_run`
- `_workspace_export_add_docx_hyperlink`
- `_workspace_export_rebuild_docx_contact_paragraph`
- `_workspace_export_normalize_docx_first_bullet_indent`
- `_workspace_export_normalize_docx_bootstrap_header`
- `_workspace_export_docx_first_run_style`
- `_workspace_export_clear_docx_paragraph_content`
- `_workspace_export_is_bullet_only_run_text`
- `_workspace_export_strip_leading_bullet_text`
- `_workspace_export_wrap_inline_label_value_text`
- `_workspace_export_restore_original_lead_word`
- `_workspace_export_run_style_payload`
- `_workspace_export_apply_docx_run_style`
- `_workspace_export_build_patched_runs`
- `_workspace_export_replace_docx_paragraph_text`
- `_apply_workspace_export_patch_specs_to_docx`
- `_build_workspace_export_docx_with_pdf2docx_bootstrap`
- `_workspace_export_header_link_items_from_pages`
- `_workspace_export_has_personal_details_patch`
- `_workspace_export_find_soffice_binary`
- `_build_workspace_export_finalized_docx`
- `_convert_workspace_docx_to_pdf_with_soffice`
- `_build_tailoring_workspace_export_context`
- `_workspace_export_preview_row_from_paragraph`
- `_workspace_export_split_skills_preview_rows`
- `_workspace_export_split_header_like_preview_row`
- `_workspace_export_section_supports_header_row_split`
- `_workspace_export_line_is_date_range`
- `_workspace_export_should_render_paired_row_inline`
- `_workspace_export_preview_pages_payload`
- `render_tailoring_workspace_draft_preview_payload`
- `export_tailoring_workspace_draft_payload`
- `record_application_action_payload`
- `application_actions_payload`
- `applied_jobs_payload`
- `jobs_search_lite_payload`
- `route_assistant_intent`
- `_is_assistant_internal_retrieval_error`
- `assistant_query_payload`
- `rag_search_payload`
- `rag_answer_payload`

Trace-related line inventory:

- L19: `from src.pipeline.post_run_notification import DEFAULT_NOTIFICATION_RECORDS_DIR`
- L130: `from src.storage.agent_trace.store import (`
- L131: `get_agent_run_postgres_payload,`
- L132: `list_agent_runs_postgres_payload,`
- L133: `list_agent_steps_postgres_payload,`
- L137: `list_agent_feedback_events,`
- L138: `record_agent_feedback_event,`
- L201: `DEFAULT_NOTIFICATION_RECORDS_DIR = Path(DEFAULT_NOTIFICATION_RECORDS_DIR)`
- L218: `"owner_user_id": "",`
- L431: `"did_record_approval_audit_event": False,`
- L539: `approval_audit_event = storage_module.record_approval_audit_event(`
- L554: `result["did_record_approval_audit_event"] = True`
- L560: `result["did_record_approval_audit_event"] = False`
- L614: `def _safe_owner_dir_name(owner_user_id: str = "") -> str:`
- L615: `safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", _clean_text(owner_user_id)).strip("._-")`
- L626: `owner_user_id: str,`
- L629: `owner_dir = _safe_owner_dir_name(owner_user_id) or "anonymous"`
- L676: `owner_user_id: str = "",`
- L679: `owner_user_id=_clean_text(owner_user_id),`
- L707: `owner_user_id: str = "",`
- L709: `owner = _clean_text(owner_user_id)`
- L732: `owner_user_id: str = "",`
- L737: `owner = _clean_text(owner_user_id)`
- L742: `owner_user_id=owner,`
- L760: `owner_user_id: str = "",`
- L764: `owner = _clean_text(owner_user_id)`
- L769: `owner_user_id=owner,`
- L788: `owner_user_id: str,`
- L791: `owner = _clean_text(owner_user_id)`
- L796: `resumes_payload = profile_resumes_payload(owner_user_id=owner)`
- L813: `owner_user_id: str = "",`
- L815: `owner = _clean_text(owner_user_id)`
- L832: `owner_user_id=owner,`
- L838: `"owner_user_id": owner,`
- L847: `owner_user_id: str = "",`
- L849: `owner = _clean_text(owner_user_id)`
- L855: `owner_user_id=owner,`
- L877: `"owner_user_id": owner,`
- L880: `owner_user_id=owner,`
- L888: `owner_user_id: str = "",`

### `src/app/api.py`

Status: `present`

Top-level Python definitions detected:

- `_warm_semantic_retrieval_background`
- `_start_semantic_warmup_thread`
- `PlanningWorkspaceDraftLoadRequest`
- `PlanningWorkspaceDraftSaveRequest`
- `PlanningWorkspaceDraftPreviewRequest`
- `PlanningWorkspaceDraftRenderRequest`
- `PlanningScanPhraseRequest`
- `PlanningWorkspaceDraftExportRequest`
- `PlanningScanPreloadRequest`
- `PlanningStartScanRequest`
- `PlanningExtractResumeUploadRequest`
- `PlanningSavedScanStateRequest`
- `AgentFeedbackRequest`
- `AgenticApprovalDecisionRequest`
- `CriticEvaluatorReadonlyRequest`
- `lifespan`
- `require_dashboard_auth`
- `_auth_user_from_request`
- `_auth_owner_user_id`
- `_require_auth_owner_user_id`
- `_auth_owner_email`
- `_require_admin_user`
- `_agentic_approval_storage_connection`
- `_agent_trace_readonly_storage_connection`
- `_agent_trace_readonly_safety_metadata`
- `_agent_trace_readonly_json_value`
- `_agent_trace_readonly_row_dict`
- `_agent_trace_readonly_run_payload`
- `_agent_trace_readonly_step_payload`
- `_agent_trace_readonly_step_order`
- `_agent_trace_readonly_cursor`
- `_agent_trace_readonly_fetchone`
- `_agent_trace_readonly_fetchall`
- `_read_agent_trace_for_approval`
- `_agent_trace_readonly_payload`
- `_agentic_approval_decision_safety_payload`
- `_production_scheduler_observability_reporting_decision_for_approval`
- `_agentic_production_scheduler_observability_report_payload`
- `_agentic_production_scheduler_observability_dashboard_and_export_base_payload`
- `_agentic_production_scheduler_observability_dashboard_payload`
- `_agentic_production_scheduler_observability_export_preview_payload`
- `_agentic_production_scheduler_observability_writer_status_payload`
- `_agentic_production_scheduler_observability_reporting_job_payload`
- `health`
- `record_agent_feedback`
- `record_agentic_approval_decision`
- `get_production_scheduler_observability_report`
- `get_production_scheduler_observability_dashboard`
- `get_production_scheduler_observability_export_preview`
- `get_production_scheduler_observability_writer_status`
- `get_agentic_approval_agent_trace`
- `_critic_evaluator_readonly_safety_flags`
- `invoke_critic_evaluator_readonly_api_action`
- `invoke_production_scheduler_observability_reporting_job_endpoint`
- `agent_feedback_summary`
- `agent_feedback_export`
- `list_agent_feedback`
- `user_workspace_state`
- `status`
- `pipeline_status`
- `scheduler_jobs`
- `scheduler_command`
- `scheduler_launchd_config`
- `scheduler_launchd_agent_status`
- `scheduler_history`
- `scheduler_storage_contract`
- `scheduler_postgres_status`
- `scheduler_summary`
- `notifications`
- `notifications_summary`
- `notifications_unread_count`
- `notifications_read_state`
- `run_live_pipeline`
- `browse`
- `review`
- `workflow`
- `planner`
- `planning_artifact`
- `planning_scan_preload`
- `planning_start_scan`
- `planning_saved_scan`
- `planning_save_saved_scan_state`
- `profile_delete_saved_scan`
- `planning_extract_resume_upload`
- `planning_resume_preview`
- `decisions`
- `planning_select_resume`
- `planning_regenerate_selected_resume`
- `planning_preview_selected_patches`
- `planning_select_patches`
- `load_workspace_draft`
- `save_workspace_draft`
- `preview_workspace_draft`
- `render_workspace_draft_preview`
- `generate_scan_phrases`
- `export_workspace_draft`
- `record_application_action`
- `applied_jobs`
- `rag_search`
- `jobs_search_lite`
- `assistant_query`
- `rag_answer`
- `profile_resumes`
- `profile_resume_role_mappings`
- `save_profile_resume_role_mapping`
- `delete_profile_resume_role_mapping`
- `onboarding_preferences`
- `save_onboarding_preferences`
- `onboarding_status`
- `profile_admin_users`
- `profile_admin_update_user_access`
- `profile_admin_delete_user`
- `profile_pipeline_runs`
- `profile_pipeline_run_detail`
- `profile_pipeline_run_agent_trace`
- `profile_pipeline_run_agentic_review_data`
- `profile_pipeline_run_rerun`
- `profile_saved_scans`
- `profile_upload_resume`
- `profile_delete_resume`

Trace-related line inventory:

- L12: `from src.agents.critic_evaluator import evaluate_agent_trace`
- L123: `pipeline_run_id: str = ""`
- L125: `agent_run_id: str = ""`
- L141: `class CriticEvaluatorReadonlyRequest(BaseModel):`
- L142: `trace_payload: dict[str, Any] \| list[dict[str, Any]] = Field(default_factory=dict)`
- L143: `trace_payload_source: str = "request_body"`
- L179: `def _auth_owner_user_id(request: Request) -> str:`
- L183: `def _require_auth_owner_user_id(request: Request) -> str:`
- L184: `owner_user_id = _auth_owner_user_id(request)`
- L185: `if not owner_user_id:`
- L187: `return owner_user_id`
- L208: `def _agent_trace_readonly_storage_connection() -> Any:`
- L212: `AGENT_TRACE_READONLY_API_SAFETY_METADATA: dict[str, bool] = {`
- L214: `"did_create_agent_run": False,`
- L233: `AGENT_TRACE_RUN_COLUMNS: tuple[str, ...] = (`
- L234: `"agent_run_id",`
- L235: `"agent_run_key",`
- L248: `AGENT_TRACE_STEP_COLUMNS: tuple[str, ...] = (`
- L251: `"agent_run_id",`
- L269: `def _agent_trace_readonly_safety_metadata() -> dict[str, bool]:`
- L270: `return dict(AGENT_TRACE_READONLY_API_SAFETY_METADATA)`
- L273: `def _agent_trace_readonly_json_value(value: Any, default: Any) -> Any:`
- L285: `def _agent_trace_readonly_row_dict(`
- L296: `def _agent_trace_readonly_run_payload(row: Any) -> dict[str, Any]:`
- L297: `payload = _agent_trace_readonly_row_dict(row, AGENT_TRACE_RUN_COLUMNS)`
- L301: `"agent_run_id": str(payload.get("agent_run_id") or "").strip(),`
- L302: `"agent_run_key": str(payload.get("agent_run_key") or "").strip(),`
- L310: `"metadata": _agent_trace_readonly_json_value(`
- L314: `"safety_metadata": _agent_trace_readonly_json_value(`
- L315: `payload.get("safety_flags_json") or payload.get("safety_metadata"),`
- L321: `def _agent_trace_readonly_step_payload(row: Any) -> dict[str, Any]:`
- L322: `payload = _agent_trace_readonly_row_dict(row, AGENT_TRACE_STEP_COLUMNS)`
- L328: `"agent_run_id": str(payload.get("agent_run_id") or "").strip(),`
- L338: `"input_summary": _agent_trace_readonly_json_value(`
- L342: `"output_summary": _agent_trace_readonly_json_value(`
- L346: `"reason_codes": _agent_trace_readonly_json_value(`
- L350: `"metadata": _agent_trace_readonly_json_value(`
- L354: `"safety_metadata": _agent_trace_readonly_json_value(`
- L355: `payload.get("safety_flags_json") or payload.get("safety_metadata"),`
- L361: `def _agent_trace_readonly_step_order(step: dict[str, Any]) -> tuple[Any, ...]:`

### `src/app/profile_ui.py`

Status: `present`

Top-level Python definitions detected:

- `_preferences_section_html`
- `_profile_navigation_icon_preloads_html`
- `profile_page`
- `pipeline_run_agentic_review_page`
- `profile_preferences_page`
- `saved_scans_page`

### `src/app/static/agentic_review.js`

Status: `present`

Trace-related line inventory:

- L159: `return `<div class="pipeline-runs-empty-cell">No advisory rows recorded for this run.</div>`;`
- L205: `readOnlyAdapterPreflight = {},`
- L206: `manualReadOnlyAdapterChain = {},`
- L207: `explicitReadOnlyChainArtifactGeneration = {},`
- L216: `const preflightSection = renderReadOnlyAdapterPreflightSection(readOnlyAdapterPreflight);`
- L217: `const adapterChainSection = renderManualReadOnlyAdapterChainSection(manualReadOnlyAdapterChain);`
- L218: `const chainGeneratorSection = renderExplicitReadOnlyChainGeneratorSection(explicitReadOnlyChainArtifactGeneration);`
- L250: `const preflightAvailable = Boolean(readOnlyAdapterPreflight?.available);`
- L251: `const preflightPlan = readOnlyAdapterPreflight?.plan_json && typeof readOnlyAdapterPreflight.plan_json === "object"`
- L252: `? readOnlyAdapterPreflight.plan_json`
- L254: `const chainAvailable = Boolean(manualReadOnlyAdapterChain?.present \|\| manualReadOnlyAdapterChain?.available);`
- L256: `explicitReadOnlyChainArtifactGeneration?.present`
- L257: `\|\| explicitReadOnlyChainArtifactGeneration?.available`
- L287: `<div class="pipeline-runs-empty-cell">No agentic workflow manifest, execution plan, dry run, or verification recorded for this run.</div>`
- L290: `<span>Optional diagnostics not recorded</span>`
- L349: `<span>Optional diagnostics not recorded</span>`
- L403: `` : `<div class="pipeline-runs-empty-cell">No RAG evaluation data recorded for this run yet.</div>`}`
- L439: `return `<div class="pipeline-runs-empty-cell">No feedback events recorded for this run yet.</div>`;`
- L473: `const runId = escapeHtml(agentFeedback?.pipeline_run_id \|\| getAgenticReviewRunId());`
- L511: `function renderAgentTraceReadOnlyDetails(label, value, options = {}) {`
- L528: `function agentTraceReadOnlyStepStatus(step = {}) {`
- L532: `function renderAgentTraceReadOnlyStep(step = {}) {`
- L533: `const status = agentTraceReadOnlyStepStatus(step);`
- L536: `const safety = step.safety_metadata \|\| step.metadata?.safety_metadata \|\| {};`
- L556: `${renderAgentTraceReadOnlyDetails("Input summary", step.input_summary \|\| step.input_json, { helper: "Read-only input summary." })}`
- L557: `${renderAgentTraceReadOnlyDetails("Output summary", step.output_summary \|\| step.output_json, { helper: "Read-only output summary." })}`
- L558: `${renderAgentTraceReadOnlyDetails("validation_json", validation, { helper: "Readable validation_json display." })}`
- L559: `${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable safety metadata display." })}`
- L565: `function renderAgentTraceReadOnlyState(message, tone = "info", label = "Agent trace state") {`
- L573: `function renderAgentTraceReadOnlyPanel(tracePayload = {}) {`
- L576: `const steps = Array.isArray(tracePayload?.agent_steps) ? tracePayload.agent_steps : [];`
- L579: `const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"`
- L580: `? tracePayload.agent_run`
- L582: `const safety = tracePayload?.safety_metadata && typeof tracePayload.safety_metadata === "object"`
- L583: `? tracePayload.safety_metadata`
- L596: `? "No persisted trace found for this run. The trace panel is read-only and will show ordered agent steps when trace records are available."`
- L611: `${loadingState ? renderAgentTraceReadOnlyState("Loading state: fetching read-only agent trace details with GET only.", "info", "Agent trace loading state") : ""}`
- L612: `${safeError ? renderAgentTraceReadOnlyState(`Fetch failure: ${safeError} Read-only display preserved.`, "error", "Agent trace fetch failure") : ""}`
- L617: `${notFoundMessage && !loadingState ? renderAgentTraceReadOnlyState(notFoundMessage, "info", "Agent trace not found trace") : ""}`
- L618: `${emptyMessage && !loadingState ? renderAgentTraceReadOnlyState(emptyMessage, "info", "Agent trace empty trace") : ""}`

### `src/pipeline/collector.py`

Status: `present`

Top-level Python definitions detected:

- `_is_user_pipeline_mode`
- `_selected_role_families_from_env`
- `_json_list_from_env`
- `_pipeline_preferences_from_env`
- `_truthy_env_value`
- `_record_source_health_agent_trace`
- `_agent_trace_status_counts`
- `log_market_insights`
- `log_company_hiring`
- `collect_all_jobs_async`

Trace-related line inventory:

- L67: `def _record_source_health_agent_trace(`
- L73: `from src.agents.source_health_agent import record_source_health_agent_trace`
- L75: `return record_source_health_agent_trace(`
- L81: `if _truthy_env_value(os.environ.get("APPLYLENS_AGENT_TRACE_STRICT")):`
- L83: `return {"attempted": True, "recorded": False, "warning": str(exc)}`
- L86: `def _agent_trace_status_counts(trace_result: Dict[str, Any]) -> Dict[str, int]:`
- L88: `return {"agent_trace_enabled": 0}`
- L89: `if trace_result.get("recorded"):`
- L91: `"agent_trace_enabled": 1,`
- L92: `"agent_trace_steps_recorded": 1,`
- L93: `"agent_trace_write_failed": 0,`
- L96: `"agent_trace_enabled": 1,`
- L97: `"agent_trace_steps_recorded": 0,`
- L98: `"agent_trace_write_failed": 1,`
- L198: `record_ats_counts,`
- L199: `record_company_hiring,`
- L200: `record_pipeline_run,`
- L579: `trace_result = _record_source_health_agent_trace(`
- L583: `if trace_result.get("recorded"):`
- L585: `"Source Health Agent trace recorded: %s %s",`
- L586: `trace_result.get("agent_run_id", ""),`
- L591: `update_counts(**_agent_trace_status_counts(trace_result))`
- L649: `run_id = record_pipeline_run(`
- L660: `record_company_hiring(run_id, deduped_jobs)`
- L662: `record_ats_counts(run_id, "SCRAPED", scraped_counts)`
- L663: `record_ats_counts(run_id, "FILTERED", filtered_counts)`
- L664: `record_ats_counts(run_id, "DEDUPED", deduped_counts)`
- L665: `record_ats_counts(run_id, "RANKED", log_stage_metrics("RANKED", ranked_jobs))`
- L666: `record_ats_counts(run_id, "DETAILS", details_counts)`

## Current readiness interpretation

### Trace storage

Current status: present.

The repository already has trace storage. Any future persistent full agent state work must reuse or intentionally extend the existing trace storage contract.

Do not create a second trace store.

### Trace write path

Current status: partially present.

The audit targets existing trace helper modules and agent call sites. Before adding any new trace-producing behavior, the next implementation must confirm the exact write contract, required fields, optional fields, owner isolation, failure handling, and strict/non-strict behavior.

Trace writes must remain explicit and must not silently trigger application execution, submission, scoring mutation, or approval mutation.

### Trace read path

Current status: partially present.

The audit targets service/API/UI surfaces that expose trace information. Before adding job-level or scan-level trace, the next implementation must confirm whether current read paths are run-level only or already support more granular context.

Read-only trace routes must remain read-only.

### Agentic Review UI

Current status: present.

The Agentic Review UI already exists. Future UI work should extend the existing panel/tabs/read-only payload model instead of creating a parallel UI.

### Pipeline collector trace call site

Current status: present.

The pipeline collector has trace-related call-site references. Any future stage wrapper work must preserve current metrics/count handling and must not break existing pipeline behavior.

## Run-level, job-level, and scan-level gap map

| Trace level | Current audit result | Next verification |
|---|---|---|
| Run-level trace | Existing trace storage/API/UI surfaces appear present | Confirm exact run lookup and owner isolation |
| Job-level trace | Not confirmed by this audit | Inspect whether job identifiers exist in trace metadata or schema |
| Scan-level trace | Not confirmed by this audit | Inspect scan workspace/service contracts and trace linkage |
| Agent step trace | Existing agent step terminology appears present | Confirm fields, ordering, validation, safety metadata |
| LLMOps trace | Not fully confirmed by this audit | Inspect `src/agents/llmops.py` and model metadata usage |
| RAG evidence trace | Not confirmed by this audit | Inspect RAG store/retrieval contracts separately |

## Safety requirements for future implementation

Future trace work must preserve:

1. No application execution.
2. No application submission.
3. No approval mutation.
4. No scoring mutation.
5. No ranking mutation.
6. No scraper behavior change.
7. No scheduler behavior change.
8. No hidden LLM call.
9. No cross-user trace access.
10. No raw private data exposure in public trace payloads.

## Recommended next checkpoint

Next checkpoint should be:

`full-agentic-ai-stage-wrapper-gap-audit-no-runtime-change`

Purpose:

Map which existing pipeline and agent modules already behave like trace-recording stage wrappers and which full roadmap agents still need safe wrappers.

Expected areas to inspect:

- discovery/source health
- relevance prefilter
- deduplication
- JD intelligence
- resume match
- tailoring decision
- final application scoring
- critic/evaluator
- strategy/operator review
- app service scan workspace
- pipeline collector

Expected output:

- stage wrapper inventory
- current trace-producing modules
- missing wrapper map
- no runtime behavior change
- no API behavior change
- no storage schema change
- no pipeline behavior change

## Decision

Do not implement trace behavior yet.

The correct next step is a stage wrapper gap audit so future implementation extends existing modules instead of inventing duplicate agent stages.
