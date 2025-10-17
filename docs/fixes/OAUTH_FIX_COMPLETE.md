# 🔧 Complete OAuth Fix Guide

## Issues Found

### Issue 1: Wrong Data Type for user_id
**Error**: `invalid input syntax for type uuid: "default-user"`

**Root Cause**: The `google_oauth_tokens` table was created with `user_id UUID` instead of `user_id TEXT`, preventing the use of "default-user" string.

### Issue 2: Login Page vs Settings Page Confusion
There are **TWO separate Google OAuth flows**:
1. **Login Page** → Supabase Google OAuth (for authentication)
2. **Settings Page** → Google Calendar OAuth (for API access)

The login page authenticates you with the app, but doesn't connect to Google Calendar. You need to do that separately in Settings.

## Complete Fix

### Step 1: Fix the Database Table

Run this SQL in Supabase SQL Editor to recreate the table with the correct schema:

**Go to**: https://app.supabase.com/project/whlsxrfxsyqnoilyauji/editor

**Run**: Copy and paste the contents of `supabase_migrations/001a_fix_google_oauth_tokens.sql`

This will:
- Drop the existing table (if any)
- Recreate it with `user_id TEXT` (not UUID)
- Add all necessary indexes, policies, and triggers

### Step 2: Verify the Fix

Run this in Supabase SQL Editor to verify:

```sql
-- Check table structure
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'google_oauth_tokens';
```

You should see:
- `user_id` → `text` ✅ (not uuid)

### Step 3: Restart Your Backend

```powershell
# Press Ctrl+C to stop
# Then restart:
.\start_fixed.ps1
```

### Step 4: Test the Status Endpoint

```powershell
Invoke-WebRequest -Uri "http://localhost:8080/auth/google/status" -Headers @{"X-API-Key"="dev-api-key-12345"} -UseBasicParsing
```

Should return:
```json
{"authenticated":false,"service":"Google Calendar"}
```

(No "error" field!)

### Step 5: Connect Google Calendar in Settings

1. Go to: http://localhost:3000/settings
2. Click "Connect Calendar" button
3. Complete Google OAuth flow
4. You'll be redirected back to settings
5. Status should show "✓ Connected"

### Step 6: Test Calendar Creation

Try creating a calendar event from the Calendar page or via API:

```powershell
$body = @{
    title = "Test Event"
    start = "2025-10-10T10:00:00Z"
    end = "2025-10-10T11:00:00Z"
    description = "Testing calendar integration"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8080/create_event" `
  -Method POST `
  -Headers @{"X-API-Key"="dev-api-key-12345"; "Content-Type"="application/json"} `
  -Body $body `
  -UseBasicParsing
```

Should return:
```json
{"ok":true,"google_event_id":"some_event_id_here"}
```

## Understanding the Two OAuth Flows

### Flow 1: Supabase Authentication (Login Page)
- **Purpose**: Authenticate user with your app
- **Provider**: Supabase Auth with Google
- **Where**: Login page (`/login`)
- **What it does**: Logs you into the PAI dashboard
- **Calendar access**: ❌ No

### Flow 2: Google Calendar OAuth (Settings Page)
- **Purpose**: Access Google Calendar API
- **Provider**: Direct Google OAuth
- **Where**: Settings page (`/settings`)
- **What it does**: Gives the app permission to read/write your calendar
- **Calendar access**: ✅ Yes

**Important**: You need BOTH! First log in (Flow 1), then connect calendar (Flow 2).

## Verification Checklist

- [ ] Table `google_oauth_tokens` exists with `user_id TEXT`
- [ ] Backend starts without errors
- [ ] `/auth/google/status` returns 200 (no error field)
- [ ] Settings page "Connect Calendar" button works
- [ ] OAuth flow completes and redirects back
- [ ] Settings shows "✓ Connected"
- [ ] Calendar event creation returns 200 OK
- [ ] Event appears in Google Calendar

## Common Issues After Fix

### "Failed to initiate Google Calendar connection"
**Check**:
1. Backend is running on port 8080
2. Environment variables are set in `.env`
3. Google OAuth redirect URI is correct: `http://localhost:8080/auth/google/callback`

### "OAuth callback failed"
**Check**:
1. Google OAuth consent screen is configured
2. Redirect URI matches exactly in Google Cloud Console
3. Backend received the callback (check logs)

### Still getting 500 errors
**Check**:
1. Backend logs for detailed error messages
2. Supabase connection is working
3. Table has correct schema (TEXT not UUID)

## Files Created

1. `supabase_migrations/001_google_oauth_tokens.sql` - Original migration
2. `supabase_migrations/001a_fix_google_oauth_tokens.sql` - Fix for UUID issue
3. `test_oauth_init.py` - Test script (can be deleted after fix)
4. This file - Complete fix guide

## Clean Up After Fix

Once everything is working, you can delete:
- `test_oauth_init.py`
- `QUICK_FIX_CALENDAR.md` (replaced by this guide)

## Need More Help?

1. Check backend terminal logs for detailed errors
2. Check browser console for frontend errors
3. Verify all environment variables are set
4. Try the test commands in this guide

