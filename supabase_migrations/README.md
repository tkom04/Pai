# Supabase Migrations

This directory contains SQL migrations for the PAI (Personal AI Assistant) Supabase database.

## Running Migrations

1. **Go to your Supabase project**: https://app.supabase.com/project/whlsxrfxsyqnoilyauji
2. **Navigate to**: SQL Editor
3. **Run each migration file in order**

## Migration Files

### `001_google_oauth_tokens.sql` (DEPRECATED - Use 001a instead)
~~Original version - had correct schema~~

### `001a_fix_google_oauth_tokens.sql` (⚠️ REQUIRED - Run This!)
Creates/fixes the Google OAuth tokens table for storing authentication credentials:
- **google_oauth_tokens**: Stores Google OAuth2 access and refresh tokens

**Features:**
- Secure token storage for Google Calendar API
- Automatic token refresh support
- User-based token isolation (TEXT type, not UUID!)
- RLS policies for security
- Development-friendly: Works with "default-user"

**⚠️ CRITICAL**:
- This migration fixes the UUID/TEXT issue
- Run this even if you already ran 001
- It will drop and recreate the table with the correct schema

### `002_groceries_and_tasks.sql`
Creates the core tables for the multi-user PAI system:
- **groceries**: Shopping list items with user isolation
- **tasks**: Task management with user isolation

**Features:**
- Row Level Security (RLS) policies
- User data isolation via `user_id`
- Automatic `updated_at` triggers
- Proper indexing for performance
- Development-friendly: Allows NULL `user_id` for testing

### `003_user_preferences.sql`
Creates the user preferences table for storing user settings:
- **user_preferences**: User-specific settings like location preferences

**Features:**
- Location preferences for weather widget
- Browser geolocation toggle
- User data isolation

## Current RLS Status

**RLS is currently DISABLED** for testing purposes. To enable:

```sql
-- Enable RLS on groceries
ALTER TABLE groceries ENABLE ROW LEVEL SECURITY;

-- Enable RLS on tasks
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
```

## Development vs Production

### Development (Current)
- RLS disabled for easy testing
- `user_id` can be NULL
- Uses "default-user" for AI chat
- No authentication required

### Production (Future)
- RLS enabled for security
- `user_id` required (from Supabase auth)
- JWT token validation
- Proper user authentication

## Testing the Setup

```bash
# Test with PowerShell
curl https://whlsxrfxsyqnoilyauji.supabase.co/rest/v1/groceries `
  -Headers @{"apikey"="YOUR_ANON_KEY"} `
  -UseBasicParsing

# Should return: []
```

## Troubleshooting

### Calendar API returns 500 Internal Server Error

**Symptom**: POST to `/create_event` returns 500 error

**Cause 1**: The `google_oauth_tokens` table is missing from your database
**Cause 2**: The table has wrong schema (UUID instead of TEXT for user_id)

**Fix**:
1. Go to Supabase SQL Editor
2. Run the `001a_fix_google_oauth_tokens.sql` migration (this will drop and recreate)
3. Restart your backend
4. Complete Google OAuth authentication at `/settings` page
5. Try creating a calendar event again

### Error: "invalid input syntax for type uuid: 'default-user'"

**Symptom**: Settings page shows "Not Connected", backend logs show UUID error

**Cause**: The `user_id` column was created as UUID instead of TEXT

**Fix**: Run the `001a_fix_google_oauth_tokens.sql` migration to fix the schema

### How to verify the table exists

```sql
-- Run this in Supabase SQL Editor
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name = 'google_oauth_tokens';
```

Should return one row if the table exists.

## Next Steps

1. ⚠️ **URGENT**: Run `001_google_oauth_tokens.sql` migration
2. ✅ Tables created (groceries, tasks, preferences)
3. ✅ RLS disabled for testing
4. ✅ Frontend configured
5. ✅ Backend services updated
6. 🔜 Complete Google OAuth authentication
7. 🔜 Add proper authentication
8. 🔜 Enable RLS for production
9. 🔜 Migrate "default-user" data to real users

