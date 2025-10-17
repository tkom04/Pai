-- Migration: Groceries and Tasks tables for multi-user PAI system
-- Created: 2025-10-08
-- Description: Core tables for shopping lists and task management

-- ============================================================================
-- GROCERIES TABLE
-- ============================================================================

-- Create groceries table (if not exists)
CREATE TABLE IF NOT EXISTS groceries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    item TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    category TEXT DEFAULT 'groceries',
    budget_category TEXT DEFAULT 'groceries',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'purchased')),
    purchased BOOLEAN DEFAULT FALSE,
    added_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for groceries
CREATE INDEX IF NOT EXISTS idx_groceries_user_id ON groceries(user_id);
CREATE INDEX IF NOT EXISTS idx_groceries_status ON groceries(user_id, status);
CREATE INDEX IF NOT EXISTS idx_groceries_created_at ON groceries(created_at DESC);

-- RLS Policies for groceries (currently disabled for testing)
ALTER TABLE groceries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own groceries" ON groceries;
CREATE POLICY "Users can view own groceries"
    ON groceries FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

DROP POLICY IF EXISTS "Users can insert own groceries" ON groceries;
CREATE POLICY "Users can insert own groceries"
    ON groceries FOR INSERT
    WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

DROP POLICY IF EXISTS "Users can update own groceries" ON groceries;
CREATE POLICY "Users can update own groceries"
    ON groceries FOR UPDATE
    USING (auth.uid() = user_id OR user_id IS NULL);

DROP POLICY IF EXISTS "Users can delete own groceries" ON groceries;
CREATE POLICY "Users can delete own groceries"
    ON groceries FOR DELETE
    USING (auth.uid() = user_id OR user_id IS NULL);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_groceries_updated_at ON groceries;
CREATE TRIGGER update_groceries_updated_at
    BEFORE UPDATE ON groceries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TASKS TABLE
-- ============================================================================

-- Create tasks table (if not exists)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for tasks
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(user_id, due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- RLS Policies for tasks
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own tasks" ON tasks;
CREATE POLICY "Users can view own tasks"
    ON tasks FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

DROP POLICY IF EXISTS "Users can insert own tasks" ON tasks;
CREATE POLICY "Users can insert own tasks"
    ON tasks FOR INSERT
    WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

DROP POLICY IF EXISTS "Users can update own tasks" ON tasks;
CREATE POLICY "Users can update own tasks"
    ON tasks FOR UPDATE
    USING (auth.uid() = user_id OR user_id IS NULL);

DROP POLICY IF EXISTS "Users can delete own tasks" ON tasks;
CREATE POLICY "Users can delete own tasks"
    ON tasks FOR DELETE
    USING (auth.uid() = user_id OR user_id IS NULL);

-- Trigger to update updated_at for tasks
DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- Grant permissions on tables
GRANT ALL ON groceries TO anon, authenticated;
GRANT ALL ON tasks TO anon, authenticated;

-- Grant permissions on sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Success message
SELECT 'Migration 002: Groceries and Tasks tables created successfully!' as message;

