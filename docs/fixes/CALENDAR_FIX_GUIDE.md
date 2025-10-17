# Calendar 500 Error Fix Guide

## Problem
The `/create_event` endpoint is returning a **500 Internal Server Error** because the required `google_oauth_tokens` table is missing from your Supabase database.

## Root Cause
The Google OAuth manager tries to fetch OAuth tokens from the `google_oauth_tokens` table, but this table was never created. This causes the calendar service to fail when trying to authenticate with Google Calendar API.

## Solution

### Step 1: Run the Database Migration

1. **Open Supabase Dashboard**
   - Go to: https://app.supabase.com/project/whlsxrfxsyqnoilyauji
   - Navigate to: **SQL Editor**

2. **Run the Migration**
   - Open the file: `supabase_migrations/001_google_oauth_tokens.sql`
   - Copy the entire SQL content
   - Paste it into the Supabase SQL Editor
   - Click **Run**

3. **Verify the Table Was Created**
   ```sql
   SELECT * FROM google_oauth_tokens;
   ```
   Should return an empty result set (no error).

### Step 2: Complete Google OAuth Setup

1. **Check Environment Variables**
   Make sure these are set in your `.env` file:
   ```env
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback
   ```

2. **Authenticate with Google**
   - Go to: http://localhost:3000/settings (or your frontend URL)
   - Look for the Google Calendar authentication section
   - Click "Connect Google Calendar"
   - Complete the OAuth flow
   - You should see "Connected" status

### Step 3: Test Calendar Creation

1. **Try Creating a Calendar Event**
   ```bash
   curl -X POST http://localhost:8080/create_event \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: dev-api-key-12345" \
     -d '{
       "title": "Test Event",
       "start": "2025-10-10T10:00:00Z",
       "end": "2025-10-10T11:00:00Z",
       "description": "This is a test event"
     }'
   ```

2. **Expected Response**
   ```json
   {
     "ok": true,
     "google_event_id": "some_event_id_here"
   }
   ```

## Verification Checklist

- [ ] `google_oauth_tokens` table created in Supabase
- [ ] Google OAuth credentials configured in `.env`
- [ ] Google Calendar authentication completed via `/settings` page
- [ ] Calendar event creation returns 200 OK (not 500)
- [ ] Event appears in Google Calendar

## Common Issues

### Issue: "Not authenticated with Google Calendar"
**Solution**: Complete the OAuth flow at `/settings` page first

### Issue: "GOOGLE_CLIENT_ID must be set"
**Solution**: Add Google OAuth credentials to your `.env` file

### Issue: Still getting 500 errors
**Solution**:
1. Check backend logs for detailed error messages
2. Verify Supabase connection is working
3. Ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set correctly

## Additional Resources

- Google OAuth Setup Guide: `GOOGLE_OAUTH_SETUP.md`
- Supabase Migrations: `supabase_migrations/README.md`
- API Reference: `API_REFERENCE.md`

## Need Help?

If you're still experiencing issues:
1. Check the backend terminal logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure the Supabase database is accessible
4. Check that Google OAuth app is properly configured in Google Cloud Console

