# 🚨 QUICK FIX: Calendar 500 Error

## TL;DR
Your calendar is failing because the **`google_oauth_tokens` table is missing** from your Supabase database.

## Quick Fix (5 minutes)

### 1. Run This SQL in Supabase
Go to https://app.supabase.com/project/whlsxrfxsyqnoilyauji/editor

Copy and paste the contents of `supabase_migrations/001_google_oauth_tokens.sql` into the SQL Editor and run it.

### 2. Restart Your Backend
```bash
# Stop the backend (Ctrl+C)
# Start it again
.\start_fixed.ps1
```

### 3. Complete OAuth
1. Go to http://localhost:3000/settings
2. Click "Connect Google Calendar"
3. Complete the OAuth flow

### 4. Test It
Try creating a calendar event again. It should work now!

## What Was Wrong?

The code was trying to:
1. Read OAuth tokens from `google_oauth_tokens` table
2. But that table didn't exist in your database
3. This caused a database error
4. Which resulted in a 500 Internal Server Error

## Files Created

I've created these files to help you:

1. **`supabase_migrations/001_google_oauth_tokens.sql`** - The missing database table
2. **`CALENDAR_FIX_GUIDE.md`** - Detailed troubleshooting guide
3. **`QUICK_FIX_CALENDAR.md`** - This file (quick reference)

## Still Not Working?

Check `CALENDAR_FIX_GUIDE.md` for detailed troubleshooting steps.

