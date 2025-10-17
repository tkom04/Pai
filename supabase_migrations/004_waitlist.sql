-- Create waitlist table for Orbit landing page signups
CREATE TABLE IF NOT EXISTS public.waitlist (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    first_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    invited BOOLEAN DEFAULT FALSE,
    invited_at TIMESTAMP WITH TIME ZONE,
    notes TEXT
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_waitlist_email ON public.waitlist(email);
CREATE INDEX IF NOT EXISTS idx_waitlist_created_at ON public.waitlist(created_at DESC);

-- Enable RLS
ALTER TABLE public.waitlist ENABLE ROW LEVEL SECURITY;

-- Allow public inserts (for waitlist signups)
CREATE POLICY "Allow public waitlist signups"
    ON public.waitlist
    FOR INSERT
    TO PUBLIC
    WITH CHECK (true);

-- Only allow authenticated users to view waitlist
CREATE POLICY "Only authenticated users can view waitlist"
    ON public.waitlist
    FOR SELECT
    TO authenticated
    USING (true);

-- Only authenticated users can update waitlist
CREATE POLICY "Only authenticated users can update waitlist"
    ON public.waitlist
    FOR UPDATE
    TO authenticated
    USING (true);

COMMENT ON TABLE public.waitlist IS 'Stores waitlist signups from the Orbit landing page';

