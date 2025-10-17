-- Migration: Create google_oauth_tokens table for storing Google OAuth credentials
-- Description: This table stores Google OAuth2 tokens for users to access Google Calendar and other services

-- Create google_oauth_tokens table
CREATE TABLE IF NOT EXISTS google_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL UNIQUE,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expiry TIMESTAMPTZ,
    scopes TEXT[] NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create index on user_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_google_oauth_tokens_user_id ON google_oauth_tokens(user_id);

-- Add RLS policies (disabled for development)
ALTER TABLE google_oauth_tokens ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for development (with NULL user_id or any user_id)
-- NOTE: In production, you should restrict this to authenticated users only
CREATE POLICY "Allow all for development" ON google_oauth_tokens
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_google_oauth_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on row update
CREATE TRIGGER google_oauth_tokens_updated_at
    BEFORE UPDATE ON google_oauth_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_google_oauth_tokens_updated_at();

-- Add comment to table
COMMENT ON TABLE google_oauth_tokens IS 'Stores Google OAuth2 credentials for accessing Google Calendar and other Google services';
COMMENT ON COLUMN google_oauth_tokens.user_id IS 'User identifier (use "default-user" for development)';
COMMENT ON COLUMN google_oauth_tokens.access_token IS 'Google OAuth2 access token';
COMMENT ON COLUMN google_oauth_tokens.refresh_token IS 'Google OAuth2 refresh token for obtaining new access tokens';
COMMENT ON COLUMN google_oauth_tokens.token_expiry IS 'Expiry timestamp of the access token';
COMMENT ON COLUMN google_oauth_tokens.scopes IS 'Array of OAuth scopes granted to the token';

