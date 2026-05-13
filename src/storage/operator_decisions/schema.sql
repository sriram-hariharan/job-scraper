CREATE TABLE IF NOT EXISTS operator_decisions (
    decision_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL DEFAULT '',
    decision_key TEXT NOT NULL,
    decision_timestamp TIMESTAMPTZ NOT NULL,
    queue_rank TEXT NOT NULL,
    job_doc_id TEXT NOT NULL,
    job_company TEXT NOT NULL,
    job_title TEXT NOT NULL,
    planning_action TEXT NOT NULL,
    winner_resume TEXT NOT NULL,
    winner_score TEXT NOT NULL,
    runner_up_resume TEXT NOT NULL,
    runner_up_score TEXT NOT NULL,
    selected_resume TEXT NOT NULL,
    decision TEXT NOT NULL,
    note TEXT NOT NULL
);

ALTER TABLE operator_decisions
ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_operator_decisions_key_timestamp
ON operator_decisions (decision_key, decision_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_operator_decisions_owner_key_timestamp
ON operator_decisions (owner_user_id, decision_key, decision_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_operator_decisions_queue_rank
ON operator_decisions (queue_rank);

CREATE INDEX IF NOT EXISTS idx_operator_decisions_selected_resume
ON operator_decisions (selected_resume);
