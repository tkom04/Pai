-- Migration: 008_budget_v5_multibank.sql
-- Multi-bank budget enhancement with AI-powered detection and debt management

-- Remove UNIQUE constraint on open_banking_tokens.user_id to support multiple banks
ALTER TABLE open_banking_tokens DROP CONSTRAINT IF EXISTS open_banking_tokens_user_id_key;

-- Add new columns to open_banking_tokens for multi-bank support
ALTER TABLE open_banking_tokens 
ADD COLUMN IF NOT EXISTS institution_id TEXT,
ADD COLUMN IF NOT EXISTS institution_name TEXT,
ADD COLUMN IF NOT EXISTS consent_expires_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMPTZ;

-- Add provider columns to bank_accounts for multi-bank support
ALTER TABLE bank_accounts 
ADD COLUMN IF NOT EXISTS provider TEXT,
ADD COLUMN IF NOT EXISTS provider_account_id TEXT;

-- Create bank_connections table to track multiple bank connections per user
CREATE TABLE IF NOT EXISTS bank_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    token_id UUID NOT NULL REFERENCES open_banking_tokens(id) ON DELETE CASCADE,
    institution_id TEXT NOT NULL,
    institution_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'revoked')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_sync_at TIMESTAMPTZ,
    UNIQUE(user_id, institution_id)
);

-- Create account_mappings table for transfer detection
CREATE TABLE IF NOT EXISTS account_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    source_account_id TEXT NOT NULL,
    destination_account_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('transfer', 'credit_card', 'loan')),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    confirmed_by_user BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, source_account_id, destination_account_id)
);

-- Create debt_accounts table for credit cards and loans
CREATE TABLE IF NOT EXISTS debt_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    connection_id UUID NOT NULL REFERENCES bank_connections(id) ON DELETE CASCADE,
    account_name TEXT NOT NULL,
    debt_type TEXT NOT NULL CHECK (debt_type IN ('credit_card', 'loan', 'overdraft')),
    current_balance DECIMAL(15,2) DEFAULT 0,
    minimum_payment DECIMAL(15,2) DEFAULT 0,
    interest_rate DECIMAL(5,4) DEFAULT 0,
    due_date DATE,
    credit_limit DECIMAL(15,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create budget_templates table for smart categorization
CREATE TABLE IF NOT EXISTS budget_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_name TEXT NOT NULL,
    subcategory TEXT,
    merchant_patterns JSONB DEFAULT '[]',
    typical_range_min DECIMAL(15,2),
    typical_range_max DECIMAL(15,2),
    is_essential BOOLEAN DEFAULT FALSE,
    detection_confidence DECIMAL(3,2) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create duplicate_transactions table for duplicate detection
CREATE TABLE IF NOT EXISTS duplicate_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    tx1_hash TEXT NOT NULL,
    tx2_hash TEXT NOT NULL,
    similarity_score DECIMAL(3,2) NOT NULL,
    is_duplicate BOOLEAN DEFAULT FALSE,
    user_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, tx1_hash, tx2_hash)
);

-- Add new columns to recurring_payments for multi-bank detection
ALTER TABLE recurring_payments 
ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_transfer BOOLEAN DEFAULT FALSE;

-- Create transaction_cache table for temporary transaction storage
CREATE TABLE IF NOT EXISTS transaction_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    tx_hash TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    merchant TEXT NOT NULL,
    posted_at TIMESTAMPTZ NOT NULL,
    category TEXT,
    is_transfer BOOLEAN DEFAULT FALSE,
    is_duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, tx_hash)
);

-- Create budget_snapshots table for monthly budget summaries
CREATE TABLE IF NOT EXISTS budget_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    period TEXT NOT NULL,
    total_spent DECIMAL(15,2) DEFAULT 0,
    total_income DECIMAL(15,2) DEFAULT 0,
    categories JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, period)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_transaction_cache_user_amount_date 
ON transaction_cache(user_id, amount, posted_at);

CREATE INDEX IF NOT EXISTS idx_account_mappings_user_accounts 
ON account_mappings(user_id, source_account_id, destination_account_id);

CREATE INDEX IF NOT EXISTS idx_recurring_payments_user_merchant 
ON recurring_payments(user_id, merchant_name);

CREATE INDEX IF NOT EXISTS idx_bank_connections_user_status 
ON bank_connections(user_id, status);

CREATE INDEX IF NOT EXISTS idx_debt_accounts_user_type 
ON debt_accounts(user_id, debt_type);

-- Enable RLS on all new tables
ALTER TABLE bank_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE debt_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE duplicate_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_snapshots ENABLE ROW LEVEL SECURITY;

-- Create RLS policies with unique names
-- Bank connections policies
CREATE POLICY "bank_connections_select_own" ON bank_connections
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "bank_connections_insert_own" ON bank_connections
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "bank_connections_update_own" ON bank_connections
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "bank_connections_delete_own" ON bank_connections
    FOR DELETE USING (user_id = auth.uid()::text);

-- Account mappings policies
CREATE POLICY "account_mappings_select_own" ON account_mappings
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "account_mappings_insert_own" ON account_mappings
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "account_mappings_update_own" ON account_mappings
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "account_mappings_delete_own" ON account_mappings
    FOR DELETE USING (user_id = auth.uid()::text);

-- Debt accounts policies
CREATE POLICY "debt_accounts_select_own" ON debt_accounts
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "debt_accounts_insert_own" ON debt_accounts
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "debt_accounts_update_own" ON debt_accounts
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "debt_accounts_delete_own" ON debt_accounts
    FOR DELETE USING (user_id = auth.uid()::text);

-- Budget templates policies (read-only for users)
CREATE POLICY "budget_templates_select_all" ON budget_templates
    FOR SELECT USING (true);

-- Duplicate transactions policies
CREATE POLICY "duplicate_transactions_select_own" ON duplicate_transactions
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "duplicate_transactions_insert_own" ON duplicate_transactions
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "duplicate_transactions_update_own" ON duplicate_transactions
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "duplicate_transactions_delete_own" ON duplicate_transactions
    FOR DELETE USING (user_id = auth.uid()::text);

-- Transaction cache policies
CREATE POLICY "transaction_cache_select_own" ON transaction_cache
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "transaction_cache_insert_own" ON transaction_cache
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "transaction_cache_update_own" ON transaction_cache
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "transaction_cache_delete_own" ON transaction_cache
    FOR DELETE USING (user_id = auth.uid()::text);

-- Budget snapshots policies
CREATE POLICY "budget_snapshots_select_own" ON budget_snapshots
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "budget_snapshots_insert_own" ON budget_snapshots
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "budget_snapshots_update_own" ON budget_snapshots
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "budget_snapshots_delete_own" ON budget_snapshots
    FOR DELETE USING (user_id = auth.uid()::text);

-- Update existing RLS policies to have unique names
-- Drop old policies and recreate with unique names
DROP POLICY IF EXISTS "select_own" ON open_banking_tokens;
DROP POLICY IF EXISTS "insert_own" ON open_banking_tokens;
DROP POLICY IF EXISTS "update_own" ON open_banking_tokens;
DROP POLICY IF EXISTS "delete_own" ON open_banking_tokens;

CREATE POLICY "open_banking_tokens_select_own" ON open_banking_tokens
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "open_banking_tokens_insert_own" ON open_banking_tokens
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "open_banking_tokens_update_own" ON open_banking_tokens
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "open_banking_tokens_delete_own" ON open_banking_tokens
    FOR DELETE USING (user_id = auth.uid()::text);

-- Update bank_accounts policies
DROP POLICY IF EXISTS "select_own" ON bank_accounts;
DROP POLICY IF EXISTS "insert_own" ON bank_accounts;
DROP POLICY IF EXISTS "update_own" ON bank_accounts;
DROP POLICY IF EXISTS "delete_own" ON bank_accounts;

CREATE POLICY "bank_accounts_select_own" ON bank_accounts
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "bank_accounts_insert_own" ON bank_accounts
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "bank_accounts_update_own" ON bank_accounts
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "bank_accounts_delete_own" ON bank_accounts
    FOR DELETE USING (user_id = auth.uid()::text);

-- Update recurring_payments policies
DROP POLICY IF EXISTS "select_own" ON recurring_payments;
DROP POLICY IF EXISTS "insert_own" ON recurring_payments;
DROP POLICY IF EXISTS "update_own" ON recurring_payments;
DROP POLICY IF EXISTS "delete_own" ON recurring_payments;

CREATE POLICY "recurring_payments_select_own" ON recurring_payments
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY "recurring_payments_insert_own" ON recurring_payments
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "recurring_payments_update_own" ON recurring_payments
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY "recurring_payments_delete_own" ON recurring_payments
    FOR DELETE USING (user_id = auth.uid()::text);

-- Add comments for documentation
COMMENT ON TABLE bank_connections IS 'Tracks multiple bank connections per user with institution metadata';
COMMENT ON TABLE account_mappings IS 'Maps relationships between user accounts for transfer detection';
COMMENT ON TABLE debt_accounts IS 'Manages credit cards and loans for debt paydown strategies';
COMMENT ON TABLE budget_templates IS 'Smart categorization patterns for AI-powered budget generation';
COMMENT ON TABLE duplicate_transactions IS 'Tracks potential duplicate transactions for user review';
COMMENT ON TABLE transaction_cache IS 'Temporary storage for transaction processing and analysis';
COMMENT ON TABLE budget_snapshots IS 'Monthly budget summaries with category breakdowns';
