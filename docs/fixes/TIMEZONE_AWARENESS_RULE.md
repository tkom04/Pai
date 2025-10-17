# Timezone Awareness Rule for PAI Project

## CRITICAL PROJECT RULE: Always Use Timezone-Aware Datetimes

### ⚠️ NEVER USE THESE - They Create Naive Datetimes:
- `datetime.utcnow()` ❌
- `datetime.now()` (without timezone) ❌
- `datetime.today()` ❌

### ✅ ALWAYS USE THESE - They Create Timezone-Aware Datetimes:
- `datetime.now(timezone.utc)` ✅
- `utc_now()` from `app.util.time` ✅
- `make_aware()` from `app.util.time` to convert naive → aware ✅

## Implementation

All datetime operations in this codebase MUST be timezone-aware to prevent "can't compare offset-naive and offset-aware datetimes" errors.

### Centralized Utilities
Use the shared utilities in `app/util/time.py`:
- `utc_now()` - Get current UTC time (timezone-aware)
- `make_aware(dt)` - Convert naive datetime to UTC-aware

### When Adding New Code
1. Import timezone utilities: `from ..util.time import utc_now, make_aware`
2. Use `utc_now()` instead of `datetime.utcnow()`
3. Apply `make_aware()` to any datetime from external sources (APIs, user input)
4. Test datetime operations to ensure no naive/aware comparison errors

### Files Updated (October 2025)
- `app/util/time.py` - Added centralized `make_aware()` function
- `app/services/calendar.py` - Removed duplicate helpers, import from util
- `app/main.py` - Updated GET /events endpoint to use `make_aware()`
- `app/services/tasks.py` - Replaced `datetime.utcnow()` with `utc_now()`
- `app/util/logging.py` - Fixed to use `datetime.now(timezone.utc)`
- `app/auth/google_oauth.py` - Removed duplicate helpers, import from util
- `frontend/components/CalendarView.tsx` - Added timezone-aware date handling

### Rule Enforcement
Any AI assistant working on this project MUST follow this rule. Always verify datetime operations are timezone-aware before submitting changes.

**This rule prevents critical timezone comparison errors that break calendar and task functionality.**
