# Production Scheduler Observability Reporting Job, No Scheduler, No Export, No Migration

Step 177A adds an explicitly invoked deterministic production scheduler observability reporting job surface. The implementation exposes a POST JSON endpoint and a minimal Agentic Review UI action. It does not persist reporting results, create reporting job records, create files, stream files, enqueue work, schedule work, start background work, emit metrics/logs/audit records, run migrations, trigger scheduler execution, trigger application execution, or trigger application submission.

## Safety contract summary

This reporting job implementation is explicitly deterministic and has no persistence, no application execution, and no application submission.

## Scope

- Runtime route file: `src/app/api.py`
- UI asset path: `src/app/static/agentic_review.js`
- Endpoint path: `/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job`
- Endpoint method: `POST`
- Response format: structured JSON only

The reporting job surface is explicitly invoked only. It reuses the existing production scheduler observability reporting gate and remains blocked when that reporting decision is missing or unsupported. The response contains deterministic job fields, a deterministic reporting job key derived from `approval_request_id`, status, reason codes, and a structured result summary.

## Verification contract phrases

- Production scheduler observability reporting job no scheduler no export no migration: PASS
- Production scheduler observability reporting job implementation: EXPLICIT_POST_JSON_ONLY
- Production scheduler observability reporting job safety: NO_SCHEDULER_NO_EXPORT_NO_MIGRATION_NO_PERSISTENCE
- Reporting job endpoint path: /api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job
- Reporting job endpoint method: POST_ONLY
- Runtime route file: src/app/api.py
- UI asset path: src/app/static/agentic_review.js
- Reporting job decision: EXPLICIT_INVOCATION_ONLY
- Read-only report endpoint method remains GET_ONLY
- Dashboard endpoint method remains GET_ONLY
- Export preview endpoint method remains GET_ONLY
- Writer status endpoint method remains GET_ONLY
- Migration execution: NO_GO
- Persistence: NO_GO
- Persistent storage writer: NO_GO
- File export creation: NO_GO
- Scheduler/background work: NO_GO
- Application execution: NO_GO
- Application submission: NO_GO
- Production scheduler wiring changes: NO_GO
- Metrics writer: NO_GO
- Logging writer: NO_GO
- Audit writer: NO_GO
- did_persist_reporting_result: false
- did_schedule_background_work: false
- did_create_reporting_job_record: false
- did_export_files: false
- did_execute_scheduler: false
- did_execute_application: false
- did_submit_application: false
- migration_required: false
- persistence_enabled: false
- reporting_job_invoked: true
- reporting_job_status
- reporting_job_key
- approval_request_id
- surface
- reason_codes
- result_summary
- no storage module modified in this phase
- no SQL file modified in this phase
- no migration file added
- no migration runner added
- no migration execution enabled
- no uncontrolled scheduler loop added
- no background worker added
- no automatic submission loop added
- no metrics emitter added
- no metrics writer added
- no logging emitter added
- no logging writer added
- no audit writer added
- no file export writer added
- no persistent storage writer added
- no reporting job record added
- no FileResponse added
- no StreamingResponse added
- no file write helpers added
- no subprocess added
- no background task added
- no Thread or Process added
- reporting job is deterministic
- reporting job is explicitly invoked
- reporting job API endpoint is POST only
- reporting job UI action calls explicit POST endpoint only
- reporting job returns structured JSON only
- reporting job key is derived deterministically from approval_request_id
- reporting job requires production scheduler observability reporting allowed/read-only decision
- reporting job blocks missing production scheduler observability reporting decision
- reporting job blocks unsupported production scheduler observability reporting decision
- reporting job does not trigger execution
- reporting job does not trigger submission
- reporting job does not trigger production scheduler wiring
- reporting job does not trigger scheduler work
- reporting job does not trigger migration execution
- reporting job does not persist reporting results
- reporting job does not create reporting job records
- reporting job does not write audit events
- reporting job does not write metrics
- reporting job does not write logs
- reporting job does not schedule background work
- reporting job does not create files
- reporting job does not stream files
- reporting job does not export files
- reporting job preserves existing queue safety gates
- reporting job preserves existing execution safety gates
- reporting job preserves submission safety gates
- reporting job preserves scheduler decision safety gates
- reporting job preserves live scheduler decision safety gates
- reporting job preserves production wiring safety gates
- reporting job preserves production observability safety gates
- reporting job preserves reporting safety gates
- reporting job preserves cache behavior
- reporting job preserves retry behavior
- reporting job preserves deduplication
- reporting job preserves ranking
- reporting job preserves metrics behavior
- reporting job preserves ATS health behavior
- reporting job preserves deterministic behavior
- persistence implementation must be separate future phase
- file export implementation must be separate future phase
- scheduler/background implementation must be separate future phase
- migration execution must be separate future phase

## Non-goals

- No persistence.
- No database writes.
- No migration.
- No scheduler or background work.
- No file export.
- No active emitter.
- No application execution.
- No application submission.
- No scoring changes.
- No prefilter relevance changes.
- No LLM evaluation changes.
- No execution changes.
- No submission changes.
- No scheduler behavior changes.
- No cache changes.
- No retry changes.
- No deduplication changes.
- No ranking changes.
- No metrics behavior changes.
- No ATS health behavior changes.
