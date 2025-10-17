# Google OAuth Setup Guide

This guide covers the setup for two separate Google OAuth flows in your application:

1. **Supabase Google OAuth** - For user authentication (Login page)
2. **Backend Google OAuth** - For Google Calendar API access (Settings page)

## 1. Supabase Google OAuth Setup (Login)

This allows users to sign in with their Google account instead of email/password.

### Steps:

1. **Create Google OAuth Credentials** (if you don't have them already)
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `https://[YOUR-SUPABASE-PROJECT-ID].supabase.co/auth/v1/callback`
     - For local testing: `http://localhost:54321/auth/v1/callback`
   - Copy the Client ID and Client Secret

2. **Configure Supabase**
   - Go to your Supabase Dashboard
   - Navigate to Authentication → Providers
   - Find "Google" and enable it
   - Paste your Google Client ID and Client Secret
   - Save the configuration

3. **Test Login**
   - Go to `http://localhost:3000/login`
   - Click "Continue with Google"
   - You should be redirected to Google's consent screen
   - After approval, you'll be redirected back to `/dashboard`

## 2. Backend Google OAuth Setup (Calendar API)

This allows users to connect their Google Calendar to your app for calendar management features.

### Steps:

1. **Enable Google Calendar API**
   - In the same Google Cloud project
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

2. **Configure OAuth Credentials** (if not already done)
   - You may use the same OAuth client or create a new one
   - Ensure the redirect URI includes:
     - `http://localhost:8080/auth/google/callback`
     - For production: `https://your-backend-domain.com/auth/google/callback`

3. **Update Environment Variables**

   Your `.env` file should already have:
   ```env
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback
   ```

4. **Create Supabase Table** (if not exists)

   You need a `google_oauth_tokens` table. Run this migration if you haven't:

   ```sql
   CREATE TABLE IF NOT EXISTS google_oauth_tokens (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     user_id TEXT UNIQUE NOT NULL,
     access_token TEXT NOT NULL,
     refresh_token TEXT,
     token_expiry TIMESTAMP,
     scopes TEXT[],
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

5. **Test Calendar Connection**
   - Login to your app
   - Go to Settings page
   - Click "Connect Calendar" under Integrations
   - You'll be redirected to Google's consent screen
   - After approval, you'll be redirected back to Settings
   - The status should show "✓ Connected"

## Features Implemented

### Login Page (`/login`)
- ✅ "Continue with Google" button with Google logo
- ✅ Uses Supabase's built-in OAuth provider
- ✅ Works alongside email/password authentication
- ✅ Redirects to dashboard after successful login

### Settings Page (`/settings`)
- ✅ Shows real-time calendar connection status
- ✅ "Connect Calendar" button when not connected
- ✅ "Disconnect" button when connected
- ✅ Success toast notification after connecting
- ✅ Confirmation dialog before disconnecting

### Backend Changes
- ✅ OAuth callback redirects to `/settings?auth=success`
- ✅ Existing OAuth endpoints remain unchanged

## Important Notes

1. **Two Separate OAuth Flows**:
   - Login with Google (Supabase) and Calendar API (Backend) use separate OAuth flows
   - Users can login with email/password and still connect Google Calendar
   - Users can login with Google and still need to separately connect Calendar

2. **Development Mode**:
   - Currently using `"default-user"` as user_id for calendar tokens
   - In production, you'll need to pass the actual authenticated user's ID

3. **Security**:
   - Supabase handles OAuth security for authentication
   - Backend stores calendar tokens securely in Supabase database
   - Tokens are automatically refreshed when expired

4. **Frontend Configuration**:
   - No additional environment variables needed for frontend
   - The app automatically uses `window.location.origin` for redirects

## Troubleshooting

### "Google sign-in failed"
- Check if Google provider is enabled in Supabase
- Verify redirect URIs match in Google Console
- Check browser console for detailed error messages

### "Failed to connect Google Calendar"
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in backend `.env`
- Check if Calendar API is enabled in Google Cloud Console
- Verify redirect URI matches: `http://localhost:8080/auth/google/callback`
- Check backend logs for detailed error messages

### Calendar shows "Not Connected" after redirect
- Check if `google_oauth_tokens` table exists in Supabase
- Verify backend can write to Supabase (check `SUPABASE_SERVICE_ROLE_KEY`)
- Look for errors in backend logs during OAuth callback

## Next Steps

1. Configure Supabase Google OAuth provider (Step 1)
2. Enable Google Calendar API (Step 2)
3. Test login with Google
4. Test calendar connection
5. For production: Update redirect URIs to use your production domain

