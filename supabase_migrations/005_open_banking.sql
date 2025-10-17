-- Migration: Create Open Banking tables for TrueLayer integration
-- Description: Tables for OAuth tokens and bank account metadata (no transaction storage)

-- OAuth tokens table with RLS
CREATE TABLE open_banking_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL DEFAULT 'truelayer',
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    scope TEXT[] NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS policies
ALTER TABLE open_banking_tokens ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users can manage their tokens"
ON open_banking_tokens FOR ALL
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Bank accounts metadata (NO balances/transactions)
CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    display_name TEXT,
    bank_name TEXT,
    account_type TEXT,
    currency TEXT DEFAULT 'GBP',
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, account_id)
);

ALTER TABLE bank_accounts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users see their accounts"
ON bank_accounts FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "users upsert their accounts"
ON bank_accounts FOR INSERT WITH CHECK (user_id = auth.uid());

-- Indexes
CREATE INDEX idx_ob_tokens_user ON open_banking_tokens(user_id);
CREATE INDEX idx_bank_accounts_user ON bank_accounts(user_id);

-- Auto-update trigger
CREATE OR REPLACE FUNCTION update_ob_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ob_tokens_updated_at
    BEFORE UPDATE ON open_banking_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_ob_tokens_updated_at();

-- Add comments
COMMENT ON TABLE open_banking_tokens IS 'Stores TrueLayer OAuth2 credentials for Open Banking access';
COMMENT ON TABLE bank_accounts IS 'Minimal bank account metadata (no transaction data stored)';
COMMENT ON COLUMN open_banking_tokens.user_id IS 'User identifier (use "default-user" for development)';
COMMENT ON COLUMN open_banking_tokens.access_token IS 'TrueLayer OAuth2 access token';
COMMENT ON COLUMN open_banking_tokens.refresh_token IS 'TrueLayer OAuth2 refresh token for obtaining new access tokens';
COMMENT ON COLUMN open_banking_tokens.expires_at IS 'Expiry timestamp of the access token (with 5-min buffer)';
COMMENT ON COLUMN open_banking_tokens.scope IS 'Array of OAuth scopes granted to the token';
COMMENT ON COLUMN bank_accounts.account_id IS 'TrueLayer account identifier';
COMMENT ON COLUMN bank_accounts.display_name IS 'User-friendly account name from bank';
COMMENT ON COLUMN bank_accounts.bank_name IS 'Bank provider name (e.g., "Barclays", "HSBC")';