CREATE TABLE IF NOT EXISTS notification_state_events (
    state_id TEXT PRIMARY KEY,
    state_timestamp TIMESTAMPTZ NOT NULL,
    owner_user_id TEXT NOT NULL DEFAULT '',
    notification_id TEXT NOT NULL,
    is_read BOOLEAN NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

ALTER TABLE notification_state_events
ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT '';

ALTER TABLE notification_state_events
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_notification_state_owner_notification_timestamp
ON notification_state_events (owner_user_id, notification_id, state_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_notification_state_owner_deleted_timestamp
ON notification_state_events (owner_user_id, is_deleted, state_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_notification_state_notification_timestamp
ON notification_state_events (notification_id, state_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_notification_state_is_read_timestamp
ON notification_state_events (is_read, state_timestamp DESC);
