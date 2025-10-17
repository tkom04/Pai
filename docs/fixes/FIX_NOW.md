# 🚨 URGENT FIX REQUIRED

## The Problem
Your Google Calendar OAuth is failing because the `google_oauth_tokens` table has the **wrong data type** for the `user_id` column.

**Error**: `invalid input syntax for type uuid: "default-user"`
**Cause**: Table was created with `user_id UUID` but needs `user_id TEXT`

## The Solution (5 minutes)

### 1. Run This SQL in Supabase NOW ⚡

Go to: https://app.supabase.com/project/whlsxrfxsyqnoilyauji/editor

Copy the entire contents of this file:
```
supabase_migrations/001a_fix_google_oauth_tokens.sql
```

Paste into Supabase SQL Editor and click **RUN**.

This will:
- Drop the old table (if it exists)
- Create a new table with the correct schema (`user_id TEXT`)
- Add all necessary indexes and policies

### 2. Restart Your Backend

```powershell
# Press Ctrl+C in the backend terminal
# Then run:
.\start_fixed.ps1
```

### 3. Connect Google Calendar

1. Open: http://localhost:3000/settings
2. Click **"Connect Calendar"** button
3. Authorize with Google
4. You'll be redirected back to settings
5. Should show **"✓ Connected"**

### 4. Test It Works

Go to the Calendar page and try creating an event. It should work now!

## What Was Wrong?

### Issue 1: Wrong Data Type ❌
- **Expected**: `user_id TEXT` (to store "default-user")
- **Actual**: `user_id UUID` (expecting a UUID format)
- **Result**: Database rejected "default-user" string

### Issue 2: Two Different OAuth Flows 🤔
You have TWO separate Google OAuth systems:

1. **Login Page** (`/login`)
   - Supabase OAuth
   - Logs you into the PAI app
   - Does NOT connect to Google Calendar

2. **Settings Page** (`/settings`)
   - Google Calendar OAuth
   - Gives app permission to access your calendar
   - This is what you need for calendar features

**You need BOTH**: First login, then connect calendar in settings.

## After the Fix

Once you run the SQL migration:

✅ Settings page "Connect Calendar" button will work
✅ OAuth flow will complete successfully
✅ Calendar event creation will return 200 OK (not 500)
✅ Events will appear in your Google Calendar

## Still Not Working?

See `OAUTH_FIX_COMPLETE.md` for detailed troubleshooting.

## Quick Test

After running the fix, test with:

```powershell
# Check auth status (should not have "error" field)
Invoke-WebRequest -Uri "http://localhost:8080/auth/google/status" -Headers @{"X-API-Key"="dev-api-key-12345"} -UseBasicParsing
```

Should return:
```json
{"authenticated":false,"service":"Google Calendar"}
```

(The `false` is normal before you connect in Settings)

