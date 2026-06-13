# Full Agentic AI Schema/Store Contract Audit

## Purpose

This checkpoint audits the existing schema and store contracts that support the full-fledged ApplyLens AI agentic roadmap.

This is intentionally docs/tests only.

No runtime behavior is changed.

No API behavior is changed.

No storage schema is changed.

No migration is executed.

No scheduler behavior is changed.

No pipeline behavior is changed.

## Branch

`full-agentic-ai-schema-contract-audit-no-runtime-change`

## Scope

This audit covers existing storage contracts for:

- agent state
- agent trace
- agent feedback
- agentic approvals

The goal is to understand what already exists before adding any new persistent agent state, job-level trace, scan-level trace, LLMOps fields, feedback links, or RAG evaluation contracts.

## Contract inventory

### `src/storage/agent_state/schema.sql`

Status: `present`

Tables found:

- `agent_runs`
- `agent_steps`

Detected column-like identifiers:

- `ON`
- `REFERENCES`
- `agent_name`
- `agent_run_id`
- `agent_run_key`
- `agent_step_id`
- `agent_step_key`
- `approval_request_id`
- `candidate_key`
- `context_key`
- `input_summary_json`
- `job_id`
- `metadata_json`
- `observed_at_utc`
- `output_summary_json`
- `reason_codes_json`
- `run_status`
- `safety_flags_json`
- `step_index`
- `step_name`
- `step_status`

### `src/storage/agent_state/store.py`

Status: `present`

Top-level Python contracts:

- `safety_flags`
- `agent_state_schema_sql_text`
- `agent_state_table_specs`
- `_clean_text`
- `_snapshot`
- `_json_compact`
- `_require_text`
- `_returning_columns`
- `prepare_agent_run_upsert`
- `prepare_agent_step_upsert`
- `prepare_agent_run_select`
- `prepare_agent_steps_select_for_run`

### `src/storage/agent_state/migration_runner.py`

Status: `present`

Top-level Python contracts:

- `_normalize_schema_sql`
- `_without_line_comment`
- `_strip_sql_comments`
- `_split_sql_statements`
- `_validate_agent_state_schema_scope`
- `_metadata`
- `build_agent_state_migration_plan`
- `run_agent_state_migration`

### `src/storage/agent_trace/schema.sql`

Status: `present`

Tables found:

- `agent_runs`
- `agent_steps`

Detected column-like identifiers:

- `ON`
- `agent_name`
- `agent_run_id`
- `agent_step_id`
- `agent_version`
- `completed_at`
- `context_id`
- `cost_json`
- `error`
- `input_json`
- `latency_ms`
- `model_name`
- `model_provider`
- `output_json`
- `owner_user_id`
- `pipeline_run_id`
- `started_at`
- `status`
- `summary_json`
- `token_usage_json`
- `validation_json`

### `src/storage/agent_trace/store.py`

Status: `present`

Top-level Python contracts:

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

### `src/storage/agent_feedback/schema.sql`

Status: `present`

Tables found:

- `agent_feedback_events`

Detected column-like identifiers:

- `ON`
- `agent_run_id`
- `agent_step_id`
- `context_id`
- `created_at`
- `event_id`
- `event_type`
- `owner_user_id`
- `payload_json`
- `pipeline_run_id`
- `source`
- `target_id`
- `target_type`

### `src/storage/agent_feedback/store.py`

Status: `present`

Top-level Python contracts:

- `_clean_text`
- `_utc_now_iso`
- `_json_compact`
- `_sql_quote_text`
- `_sql_nullable_text`
- `_sql_jsonb`
- `_read_sql_artifact`
- `agent_feedback_schema_sql_text`
- `render_agent_feedback_schema_sql`
- `agent_feedback_schema_sql_generation_payload`
- `agent_feedback_table_specs`
- `agent_feedback_contract_health_payload`
- `_resolve_database_url`
- `_redact_database_url`
- `_feedback_query_payload_from_row`
- `_run_postgres_json_query`
- `_schema_prefix`
- `_require_owner_user_id`
- `_require_known_event_type`
- `_require_known_target_type`
- `_require_payload_json`
- `build_agent_feedback_event_id`
- `agent_feedback_event_db_row`
- `record_agent_feedback_event`
- `list_agent_feedback_events`
- `summarize_agent_feedback_events`
- `feedback_label_for_event_type`
- `feedback_value_for_label`
- `build_agent_feedback_evaluation_dataset`
- `_agent_feedback_counts`
- `export_agent_feedback_events`
- `render_agent_feedback_export_markdown`

### `src/storage/agentic_approvals/schema.sql`

Status: `present`

Tables found:

- `agentic_approval_audit_events`
- `agentic_approval_requests`

Detected column-like identifiers:

- `ON`
- `REFERENCES`
- `app_service_safety_gate_snapshot_json`
- `approval_request_id`
- `approval_status`
- `approved_at`
- `audit_event_id`
- `created_at`
- `denied_at`
- `dry_run_artifact_id`
- `event_actor_id`
- `event_payload_json`
- `event_type`
- `expires_at`
- `fixture_validation_snapshot_json`
- `idempotency_key`
- `owner_id`
- `proposed_action_summary`
- `proposed_action_type`
- `queue_safety_gate_snapshot_json`
- `review_decision`
- `review_reason`
- `reviewer_id`
- `revoked_at`
- `safety_gate_snapshot_json`
- `updated_at`

### `src/storage/agentic_approvals/store.py`

Status: `present`

Top-level Python contracts:

- `create_approval_request`
- `get_approval_request`
- `list_approval_requests`
- `record_approval_audit_event`
- `record_approval_decision`
- `expire_approval_requests`
- `_execute_fetch_one`
- `_execute_fetch_optional`
- `_execute_fetch_all`
- `ApprovalStorageError`
- `_row_to_dict`
- `_returning_columns`
- `_classify_exception`
- `_normalize_approval_status`
- `_normalize_decision_status`
- `_json_payload`
- `_reject_sensitive_payload`
- `_require_text`
- `_require_value`
- `_clean_text`
- `_utc_now`

## Roadmap interpretation

### Agent state

Current status: present.

The repository already has an agent state storage area. Before adding any new `JobApplicationContext` persistence, the existing schema and store functions must be treated as the starting point.

Do not create a parallel agent state system unless the existing contract is proven insufficient.

### Agent trace

Current status: present.

The repository already has an agent trace storage area. The next implementation phase should extend or reuse this contract for run-level, job-level, and scan-level trace only after confirming the existing table fields and helper functions.

Do not duplicate trace storage.

### Agent feedback

Current status: present.

The repository already has an agent feedback storage area. The next implementation phase should confirm whether feedback records link to user, run, job, scan, agent step, and suggestion IDs.

Do not add new feedback storage until the current feedback contract is mapped.

### Agentic approvals

Current status: present.

The repository already has approval storage. Any future human-in-the-loop approval work must preserve gated execution and must not bypass approval records.

Do not add execution, submission, or approval mutation in this audit phase.

## Immediate implementation gaps to verify later

1. Whether `agent_state` has enough fields for full `JobApplicationContext`.
2. Whether `agent_trace` supports owner user ID, pipeline run ID, job ID, scan ID, agent name, agent version, status, input summary, output summary, validation, safety metadata, latency, model metadata, token usage, and cost.
3. Whether `agent_feedback` links feedback to agent steps and suggestions.
4. Whether `agentic_approvals` cleanly separates approval request, approval decision, execution eligibility, and submission eligibility.
5. Whether all read/write helpers enforce owner isolation.
6. Whether migrations are manually applied, admin-applied, or application-applied.
7. Whether tests already protect no execution, no submission, no scoring mutation, and no approval mutation.
8. Whether job-level trace and scan-level trace require new optional fields or can reuse existing metadata JSON.
9. Whether LLMOps metadata belongs in trace metadata, dedicated LLMOps storage, or both.
10. Whether RAG evidence tracing should link to trace steps or remain in RAG-specific storage.

## Recommended next checkpoint

Next checkpoint should be:

`full-agentic-ai-trace-contract-readiness-no-runtime-change`

Purpose:

Audit the exact agent trace read/write path from storage to services to API to UI.

Expected files to inspect:

- `src/storage/agent_trace/schema.sql`
- `src/storage/agent_trace/store.py`
- `src/agents/trace.py`
- `src/app/services.py`
- `src/app/api.py`
- `src/app/profile_ui.py`
- `src/app/static/agentic_review.js`

Expected output:

- trace contract readiness doc
- trace read path map
- trace write path map
- run-level/job-level/scan-level gap map
- no runtime behavior change
- no API behavior change
- no storage schema change
- no pipeline behavior change

## Decision

Do not implement new persistent agent behavior yet.

The correct next move is a trace contract readiness audit, because trace is the backbone for the full-fledged agentic AI roadmap.
