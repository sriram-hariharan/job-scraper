CREATE TABLE IF NOT EXISTS notification_state_events (
    state_id TEXT PRIMARY KEY,
    state_timestamp TIMESTAMPTZ NOT NULL,
    notification_id TEXT NOT NULL,
    is_read BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_state_notification_timestamp
ON notification_state_events (notification_id, state_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_notification_state_is_read_timestamp
ON notification_state_events (is_read, state_timestamp DESC);