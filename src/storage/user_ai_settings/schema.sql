CREATE TABLE IF NOT EXISTS user_ai_settings (
    owner_user_id TEXT PRIMARY KEY REFERENCES auth_users(user_id) ON DELETE CASCADE,
    preferred_provider TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_ai_settings_preferred_provider_check
        CHECK (preferred_provider IS NULL OR preferred_provider IN ('groq', 'openai'))
);

CREATE TABLE IF NOT EXISTS user_ai_provider_credentials (
    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    credential_ciphertext TEXT NOT NULL,
    credential_hint TEXT NOT NULL,
    encryption_scheme TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (owner_user_id, provider),
    CONSTRAINT user_ai_provider_credentials_provider_check
        CHECK (provider IN ('groq', 'openai')),
    CONSTRAINT user_ai_provider_credentials_encryption_scheme_check
        CHECK (encryption_scheme = 'fernet-v1')
);

CREATE INDEX IF NOT EXISTS idx_user_ai_provider_credentials_updated
ON user_ai_provider_credentials (owner_user_id, updated_at DESC);
