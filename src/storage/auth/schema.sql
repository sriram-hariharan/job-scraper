CREATE TABLE IF NOT EXISTS auth_users (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    normalized_email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    last_login_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_auth_users_active
ON auth_users (is_active);

CREATE INDEX IF NOT EXISTS idx_auth_users_created_at
ON auth_users (created_at DESC);

CREATE TABLE IF NOT EXISTS auth_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    session_token_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    user_agent TEXT NOT NULL,
    ip_address TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id
ON auth_sessions (user_id);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash
ON auth_sessions (session_token_hash);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at
ON auth_sessions (expires_at);