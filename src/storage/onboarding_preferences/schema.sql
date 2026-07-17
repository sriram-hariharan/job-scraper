CREATE TABLE IF NOT EXISTS user_onboarding_preferences (
    owner_user_id TEXT PRIMARY KEY REFERENCES auth_users(user_id) ON DELETE CASCADE,
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    selected_role_families JSONB NOT NULL DEFAULT '[]'::jsonb,
    target_seniority JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferred_locations JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferred_location_specs JSONB NOT NULL DEFAULT '[]'::jsonb,
    location_strict_match BOOLEAN NOT NULL DEFAULT FALSE,
    location_show_others_if_unmatched BOOLEAN NOT NULL DEFAULT FALSE,
    work_modes JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferred_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    excluded_keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE user_onboarding_preferences
ADD COLUMN IF NOT EXISTS preferred_location_specs JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE user_onboarding_preferences
ADD COLUMN IF NOT EXISTS location_strict_match BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE user_onboarding_preferences
ADD COLUMN IF NOT EXISTS location_show_others_if_unmatched BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_user_onboarding_preferences_updated
ON user_onboarding_preferences (updated_at DESC);
