# Minimal Fixture Validator Module Implementation

Doc path: `docs/minimal_fixture_validator_module_implementation.md`

Phase 75A is minimal fixture validator module implementation only. Fixture validator module added: `src/agents/fixture_validator.py`. Fixture validator tests added: `tests/test_fixture_validator.py`. No fixture validator CLI is added. No runtime integration is added. No fixture execution is added. No workflow_runner integration is added. No live planning integration is added. No additional fixture payload files are added. The existing fixture remains synthetic and inert. The validator is read-only. The validator uses explicit file paths only. The validator does not discover fixtures at runtime. The validator does not call generator, simulator, planner, workflow_runner, app services, queue, DB, or application submission. No DB writes are added. No mutation is enabled. No approval API/storage is added. No queue updates are added. No application submission is added.

`workflow_runner.py` remains dry-run only. The read-only adapter preflight must continue to report `executable_adapter_count=0`.

## Current Implementation Scope

- Minimal fixture validator module implementation: `PASS`
- Fixture validator module: `PASS`
- Fixture validator tests: `PASS`
- Fixture validator CLI: `NOT_YET`
- Runtime integration: `NO_GO`
- Runtime failure-mode tests: `NO_GO`
- Storage integration tests: `NO_GO`
- DB migrations: `NO_GO`
- Runtime DB writes: `NO_GO`
- Mutation execution: `NO_GO`
- Live execution: `NO_GO`

## Validator Boundary

- read-only local validation only
- explicit file path input only
- no runtime discovery
- no fixture execution
- no DB writes
- no queue mutation
- no application submission
- no generator/simulator/planner/workflow_runner/app-service invocation
- no CLI

## Validated Fixture Contract

Required fields and safety flags:

- `fixture_schema_version`
- `fixture_id`
- `fixture_family`
- `synthetic`
- `contains_private_data`
- `contains_secret`
- `contains_production_path`
- `contains_live_queue_path`
- `contains_application_submission_target`
- `request.execution_mode`
- `request.allow_agent_execution`
- `request.allow_live_execution`
- `request.allow_mutation`
- `request.allow_db_write`
- `request.allow_queue_update`
- `request.allow_application_submission`
- `expected_validation.did_execute_fixture`
- `expected_validation.did_mutate_production`
- `expected_validation.did_write_db`

## Stable Reason Codes

- `invalid_json`
- `missing_required_field`
- `invalid_schema_version`
- `invalid_fixture_family`
- `private_data_not_allowed`
- `secret_not_allowed`
- `production_path_not_allowed`
- `live_queue_path_not_allowed`
- `application_submission_target_not_allowed`
- `agent_execution_not_allowed`
- `live_execution_not_allowed`
- `mutation_not_allowed`
- `db_write_not_allowed`
- `queue_update_not_allowed`
- `application_submission_not_allowed`
- `execution_flag_not_false`

## Test Coverage

- valid `safe_execution_request_minimal.json` passes
- validation result confirms `did_execute_fixture=false`
- validation result confirms `did_mutate_production=false`
- validation result confirms `did_write_db=false`
- invalid tmp copy with `request.allow_db_write=true` fails with `db_write_not_allowed`
- invalid tmp copy with `contains_secret=true` fails with `secret_not_allowed`
- invalid tmp copy with `request.allow_application_submission=true` fails with `application_submission_not_allowed`
- invalid tmp copy missing a required field fails with `missing_required_field`
- validator module requires no runtime imports or side effects
- fixture directory still contains only `.gitkeep` and `safe_execution_request_minimal.json`

## Forbidden Next-Step Shortcuts

- do not add CLI next without explicit approval
- do not wire validator into runtime next without explicit approval
- do not add runtime failure-mode tests next
- do not add DB writes next
- do not add storage integration next
- do not add approval APIs next
- do not add mutation APIs next
- do not add live queue updates next
- do not start application submission automation next
- do not enable workflow_runner live execution next

## Recommended Next Phase

Recommended next phase: 75B minimal fixture validator module implementation final audit and merge gate.

After 75B: 76A minimal fixture validator module implementation release safety checkpoint, docs/tests only.

The 76A release safety checkpoint is tracked in `docs/minimal_fixture_validator_module_implementation_release_safety_checkpoint.md`.

The minimal fixture validator CLI implementation is tracked in `docs/minimal_fixture_validator_cli_implementation.md`.
