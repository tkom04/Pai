# 🏦 Open Banking Integration - Handoff Document

## 📋 Context for New AI Session

This document provides everything needed to implement **UK Open Banking** integration into the Orbit personal AI platform.

---

## 🏗️ Project Overview

**Orbit** is a FastAPI-based personal AI command center that integrates:
- ✅ Google Calendar (OAuth implemented - see `app/auth/google_oauth.py`)
- ✅ Supabase (tasks, groceries, user data)
- ✅ OpenAI GPT-4o-mini (streaming + tool calling)
- ⏳ **Open Banking** (NOT YET IMPLEMENTED - this is what we're adding)

### Current Structure:
```
app/
├── main.py              # FastAPI app + endpoints
├── deps.py              # Dependency injection + service clients
├── models.py            # Pydantic request/response models
├── auth/
│   └── google_oauth.py  # Google OAuth2 (USE AS REFERENCE!)
├── services/
│   ├── budgets.py       # Budget service (currently CSV-based)
│   ├── calendar.py      # Google Calendar service
│   ├── groceries.py     # Grocery management
│   └── tasks.py         # Task management
└── util/
    ├── time.py          # Timezone utilities (CRITICAL!)
    └── logging.py       # Structured logging
```

---

## 🎯 Goal: Add Open Banking Integration

### What We Need:

1. **UK Open Banking OAuth Flow** (similar to Google OAuth pattern)
   - Use TrueLayer, Plaid, or Yapily
   - Multi-tenant token storage in Supabase
   - Token refresh mechanism

2. **Real-Time Transaction Fetching** ⚡
   - Replace CSV-based budget service
   - Fetch real bank transactions on-demand
   - **NO STORAGE** - data lives only in memory (compliance-friendly!)

3. **Budget Analysis Enhancement**
   - Real-time spending data
   - Category auto-classification
   - AI tool integration

---

## 🔑 CRITICAL PATTERNS TO FOLLOW

### 1. OAuth Pattern (Copy from `app/auth/google_oauth.py`)

The Google OAuth implementation is **THE BLUEPRINT**:
- Multi-tenant (user_id-based)
- Token storage in Supabase
- Automatic token refresh
- Clean error handling

### 2. Timezone Awareness (MUST FOLLOW!)

See `TIMEZONE_AWARENESS_RULE.md`

**NEVER:**
- `datetime.utcnow()` ❌
- `datetime.now()` without timezone ❌

**ALWAYS:**
```python
from app.util.time import utc_now, to_aware_utc

now = utc_now()  # Current UTC time
aware = to_aware_utc(some_datetime)  # Convert to aware
```

### 3. Error Handling Pattern

```python
try:
    result = await do_something()
    return {"ok": True, "data": result}
except ValueError as e:
    # Auth errors - return helpful message
    logger.warning(f"Auth error: {e}")
    return {"ok": False, "message": str(e), "authenticated": False}
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

---

## 📦 Recommended Provider: TrueLayer

**Why TrueLayer:**
- Best UK bank coverage
- Good documentation
- Free sandbox
- Similar OAuth flow to Google

**Environment Variables:**
```bash
OPEN_BANKING_PROVIDER=truelayer
TRUELAYER_CLIENT_ID=your-client-id
TRUELAYER_CLIENT_SECRET=your-secret
TRUELAYER_REDIRECT_URI=http://localhost:8080/auth/open-banking/callback
TRUELAYER_ENVIRONMENT=sandbox
```

---

## 🗂️ Supabase Migrations Needed

Create `supabase_migrations/005_open_banking.sql`:

**⚠️ COMPLIANCE-FRIENDLY: We do NOT store transaction data!**

```sql
-- OAuth tokens table (encrypted, necessary for auth)
CREATE TABLE public.open_banking_tokens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    access_token TEXT NOT NULL,  -- Consider encrypting at rest
    refresh_token TEXT,
    token_expiry TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Minimal bank account metadata (NO balances, NO transactions)
CREATE TABLE public.bank_accounts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider_account_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    account_type TEXT,          -- e.g., "current", "savings"
    display_name TEXT,          -- User-friendly name
    bank_name TEXT,             -- e.g., "Barclays"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, provider_account_id)
);

-- Indexes
CREATE INDEX idx_bank_accounts_user ON public.bank_accounts(user_id);

-- RLS
ALTER TABLE public.open_banking_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bank_accounts ENABLE ROW LEVEL SECURITY;

-- Note: Transactions are fetched in real-time and NEVER stored
-- This avoids PCI-DSS, financial regulations, and data breach liability
```

---

## 📝 Implementation Steps

1. **Study Google OAuth** (`app/auth/google_oauth.py`) - 30 mins
2. **Create `app/auth/open_banking.py`** - Copy OAuth pattern
3. **Apply Supabase migrations** - Create tables (tokens + minimal account metadata only)
4. **Add endpoints to `app/main.py`** - OAuth + real-time transaction fetching
5. **Update `app/services/budgets.py`** - Fetch from Open Banking on-demand
6. **Test in TrueLayer sandbox** - Use test credentials
7. **Add frontend UI** - Connect bank button + loading state in `pwa/components/BudgetView.tsx`
8. **Add friendly header** - "Loading fresh data from your bank..." message

---

## 🔗 Key Files to Read

**MUST READ:**
1. `app/auth/google_oauth.py` - Your OAuth blueprint
2. `TIMEZONE_AWARENESS_RULE.md` - Critical datetime rules
3. `app/services/budgets.py` - Current budget implementation

**Reference:**
- `app/services/calendar.py` - How to use OAuth in a service
- `app/main.py` lines 309-350 - OAuth endpoints
- `supabase_migrations/001_google_oauth_tokens.sql` - Token table pattern

---

## ⚡ Current System Status

- ✅ Backend: FastAPI on port 8000
- ✅ PWA: Next.js on port 3000 (user dashboard)
- ✅ Website: Next.js on port 3001 (marketing site with solar system!)
- ✅ Supabase: 4 migrations applied (oauth, groceries/tasks, preferences, waitlist)
- ✅ Google Calendar OAuth: WORKING PERFECTLY
- ✅ Event filtering: Fixed today (was showing 100 events, now accurate)
- ⏳ Open Banking: Not started

---

## 🎯 Success Criteria

Open Banking is complete when:

1. ✅ User can click "Connect Bank" and complete OAuth flow
2. ✅ Tokens stored securely in Supabase with auto-refresh
3. ✅ Transactions fetched in real-time (NO storage, compliance-friendly!)
4. ✅ `/budget_scan` returns real spending data from live API
5. ✅ AI can answer "How much did I spend on food this week?" using live data
6. ✅ Frontend shows bank connection status + friendly loading message
7. ✅ Budget page displays: "🔄 Loading fresh data from your bank..." during fetch

---

## 🚀 Real-Time Architecture (No Data Storage)

**Flow:**
```
User opens /budget page
  ↓
Frontend calls /api/transactions
  ↓
Backend checks OAuth token
  ↓
Backend calls TrueLayer API (live)
  ↓
Transform & return data
  ↓
Data lives only in browser/memory
  ↓
User closes page → data gone
```

**Benefits:**
- 🔒 No PCI-DSS compliance needed
- 📜 No financial data regulations
- 🛡️ Zero data breach risk
- ⚡ Always fresh data (no stale cache)

**Trade-off:**
- ⏱️ 1-2 second load time (acceptable with friendly UX)

---

**Pro Tip:** The Google OAuth implementation took ~2 hours and works flawlessly. Copy that exact pattern and you'll have Open Banking working quickly! 🚀

