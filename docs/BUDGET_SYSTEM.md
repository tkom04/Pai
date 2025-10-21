# Budget System Documentation

## Overview

The Orbit Budget System provides comprehensive budget management with real-time bank transaction processing, categorization rules, and privacy-first architecture.

## Architecture

### Core Components

1. **TransactionProcessor** - Normalizes, deduplicates, and categorizes bank transactions
2. **BudgetEngine** - Calculates summaries, handles rollovers, and manages budget logic
3. **REST API** - Provides secure endpoints for budget operations
4. **Frontend** - React components for budget visualization and management

### Security Features

- **SQL Injection Prevention** - All database queries use parameterized statements
- **Row Level Security (RLS)** - Database policies ensure users only access their own data
- **OAuth Token Refresh** - Automatic handling of expired bank connection tokens
- **Input Validation** - Pydantic models with strict validation and regex patterns
- **Audit Logging** - Non-PII event logging for compliance

### Performance Optimizations

- **O(n) Algorithms** - Efficient deduplication and transfer detection
- **Thread-Safe Caching** - TTLCache with per-user locks
- **Concurrent Refresh Prevention** - Prevents multiple simultaneous refreshes
- **Timeout Handling** - 30s limits with exponential backoff retry

## API Endpoints

### Budget Refresh
```
POST /api/budget/refresh?lookback_days=90
```
Fetches and processes bank transactions with full error handling.

### Budget Summary
```
GET /api/budget/summary?period=2024-01
```
Returns budget summary for specified period.

### Categories Management
```
GET /api/budget/categories
POST /api/budget/categories
DELETE /api/budget/categories/{key}
```

### Rules Management
```
GET /api/budget/rules
POST /api/budget/rules
DELETE /api/budget/rules/{id}
```

## Database Schema

### Tables

- `budget_categories` - User-defined budget categories with targets
- `budget_rules` - Categorization rules for transactions
- `budget_settings` - User preferences and configuration
- `audit_events` - Non-PII event logging

### RPC Functions

- `upsert_budget_category()` - Safe category creation/update
- `upsert_budget_rule()` - Safe rule creation

## Frontend Components

### BudgetView
- Period switcher with 12-month history
- Real-time refresh with loading states
- Category management with progress bars
- Bank connection status and setup

### Settings Page
- Budget category CRUD with optimistic updates
- Budget settings (currency, cycle, AI features)
- Rollback on failed operations

## Testing Guide

### Unit Tests

```python
# Test deduplication logic
def test_deduplication_allows_multiple_same_merchant():
    """Two coffees same day should NOT be duplicates"""
    pass

# Test transfer detection performance
def test_transfer_detection_on_performance():
    """1000 transactions should process in <1s"""
    pass

# Test SQL injection prevention
def test_sql_injection_prevention():
    """Malicious input should be safely handled"""
    malicious = "'; DROP TABLE budget_categories;--"
    with pytest.raises(ValidationError):
        await create_budget_category(key=malicious, ...)
```

### Integration Tests

1. **RLS Policies** - Verify cross-tenant access is blocked
2. **OAuth Flow** - Test token refresh and expiry handling
3. **Concurrent Refreshes** - Ensure only one refresh per user
4. **Error Handling** - Test partial failures and timeouts

### Performance Tests

1. **Transaction Processing** - 1000+ transactions in <1s
2. **Cache Efficiency** - Memory usage and TTL behavior
3. **Database Queries** - Index usage and query performance

## Environment Configuration

```bash
# Budget System Configuration
BUDGET_TRANSACTION_CACHE_TTL_SECONDS=300
BUDGET_ECB_RATES_CACHE_TTL_SECONDS=3600
BUDGET_DEFAULT_CURRENCY=GBP
```

## Deployment Checklist

- [ ] Database migration applied (`006_budget_system.sql`)
- [ ] RLS policies enabled and tested
- [ ] Environment variables configured
- [ ] Dependencies installed (`cachetools`, `tenacity`)
- [ ] Frontend components updated
- [ ] API endpoints tested
- [ ] Error handling verified
- [ ] Performance benchmarks met

## Security Considerations

1. **Input Sanitization** - All user inputs validated and sanitized
2. **SQL Injection** - Parameterized queries only, no string interpolation
3. **XSS Prevention** - React's built-in XSS protection
4. **CSRF Protection** - API key authentication
5. **Rate Limiting** - Implement per-user rate limits in production
6. **Audit Trail** - All operations logged for compliance

## Monitoring

- Transaction processing time
- Cache hit rates
- Error rates by endpoint
- OAuth token refresh frequency
- Database query performance
- Memory usage patterns

## Troubleshooting

### Common Issues

1. **"Refresh already in progress"** - Wait for current refresh to complete
2. **"No data available"** - Call `/api/budget/refresh` first
3. **"Session expired"** - Reconnect bank account
4. **Timeout errors** - Reduce `lookback_days` parameter

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in environment variables.

## Future Enhancements

- Multi-currency support with real-time rates
- Advanced categorization with machine learning
- Budget alerts and notifications
- Export functionality (CSV, PDF)
- Mobile app integration
- Third-party bank connections

