# Implementation Notes & Important Information

## 🔴 Critical Requirements

### OpenAI Tool Schema Format

The OpenAI API requires tools to be in this specific format:

```python
{
    "type": "function",
    "name": "tool_name",
    "description": "Clear description for the AI",
    "parameters": {
        "type": "object",
        "properties": {
            "field_name": {
                "type": "string",
                "description": "Field description"
            }
        },
        "required": ["field_name"],
        "additionalProperties": False
    }
}
```

**Important:**
- Each tool MUST have `"type": "function"`
- Parameters MUST follow JSON Schema format
- Use clear descriptions for better AI understanding
- Mark fields as required appropriately

### OpenAI Streaming Implementation

The streaming implementation uses:
- `client.chat.completions.create()` with `stream=True`
- NOT the deprecated `client.responses.stream()` API
- Tool calls are accumulated via delta chunks
- Maximum 5 iterations to prevent infinite loops

### Notion Database Property Names

Property names in Notion are **case-sensitive**. The implementation expects:

**Tasks Database:**
- Title (title)
- Due (date)
- Context (select)
- Priority (select)
- Status (select)

**Groceries Database:**
- Item (title)
- Qty (number)
- Notes (rich_text)
- Status (select)

**Budgets Database:**
- Category (select)
- Cap (number)
- Spent (number)
- Delta (number)
- Status (select)
- Month (date)

If your database has different property names, update them in `app/deps.py` → `NotionService`.

---

## 🔧 Configuration Notes

### Environment Variables Loading

The application uses `pydantic-settings` for configuration:
- Environment variables are loaded automatically
- `.env` file is read by the application
- Settings are validated on startup
- Missing required settings will cause startup failure

### Google OAuth Token Storage

OAuth tokens are stored in `google_token.json`:
- File is created after first successful OAuth flow
- Token is automatically refreshed when expired
- File is in `.gitignore` (never commit)
- Delete file to force re-authentication

### Notion Integration Permissions

The Notion integration MUST have:
- Read content capability
- Update content capability
- Insert content capability

Databases MUST be shared with the integration:
1. Open database in Notion
2. Click "..." → "Add connections"
3. Select your integration
4. Click "Confirm"

---

## 🚨 Common Pitfalls

### 1. OpenAI Model Name
❌ Wrong: `gpt-4.1-mini`, `gpt-5-mini`
✅ Correct: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`

### 2. Notion Database IDs
- Must be 32 characters (without hyphens) or UUID format
- Get from database URL: `https://notion.so/{workspace}/{DB_ID}?v=...`
- Use the ID between workspace and `?v=`

### 3. Google OAuth Redirect URI
- MUST match exactly in Google Cloud Console
- Include protocol: `http://localhost:8080/auth/google/callback`
- For production, update to HTTPS domain

### 4. API Key Authentication
- Header name is `x-api-key` (lowercase, with hyphen)
- NOT `X-API-Key` or `api-key`
- Required for all endpoints except `/healthz` and OAuth

### 5. DateTime Format
- All datetimes should be ISO8601 format
- Include timezone: `2025-10-05T14:00:00Z` or `2025-10-05T14:00:00+01:00`
- Python: `datetime.isoformat()`

---

## 🔐 Security Considerations

### API Key Security
- Use strong random keys (min 32 characters)
- Rotate regularly (every 90 days recommended)
- Never log API keys
- Use different keys for dev/staging/prod

### OAuth Security
- Tokens are stored locally (not in database)
- Refresh tokens allow re-authentication without user
- Revoke tokens when no longer needed
- Monitor OAuth activity in Google Cloud Console

### Rate Limiting (Not Implemented Yet)
When implementing rate limiting:
- Per-API-key limits
- Per-IP limits for OAuth endpoints
- Separate limits for AI endpoints (more expensive)
- Use Redis for distributed rate limiting

---

## 🎯 Testing Strategy

### Unit Tests
Located in `tests/` directory:
- `test_ai_router.py` - AI streaming and tool calling
- `test_tools_runtime.py` - Tool execution

Run tests:
```bash
pytest tests/
```

### Integration Tests
Test complete workflows:

1. **AI → Notion → Calendar**
   ```json
   {
     "prompt": "Schedule dentist for Friday at 2pm and create a task"
   }
   ```

2. **Budget Analysis**
   ```json
   {
     "prompt": "How much did I spend on food this month?"
   }
   ```

3. **Grocery List**
   ```json
   {
     "prompt": "Add milk, eggs, and bread to groceries"
   }
   ```

### Manual Testing
1. Start server: `uvicorn app.main:app --reload --port 8080`
2. Visit: http://localhost:8080/docs
3. Authorize with API key
4. Test each endpoint
5. Check Notion and Google Calendar for results

---

## 📊 Monitoring & Logging

### Log Levels
- **INFO**: Normal operations, API calls
- **WARNING**: Non-critical issues
- **ERROR**: Failed operations, exceptions

### What Gets Logged
- All HTTP requests with timing
- Tool executions (with masked secrets)
- OAuth flows
- API errors with stack traces

### What NOT to Log
- API keys
- OAuth tokens
- User passwords
- Sensitive user data

### Structured Logging
Uses `structlog` for structured JSON logs:
```python
logger.info("Task created", extra={
    "task_id": task_id,
    "user": user_id,
    "duration_ms": elapsed
})
```

---

## 🚀 Performance Considerations

### OpenAI Streaming
- Streaming reduces perceived latency
- Client sees response immediately
- Total time is similar to non-streaming
- Better UX for long responses

### Notion API
- Rate limit: 3 requests per second
- Implement caching for frequent reads
- Use batch operations when possible
- Cache database schemas (already implemented)

### Google Calendar API
- Rate limit: 500 queries per 100 seconds per user
- Use batch requests for multiple operations
- Cache calendar events locally if needed

### Memory Usage
- OpenAI streaming: Low (chunks processed individually)
- Notion queries: Medium (paginated results)
- Calendar events: Low (max 100 results by default)

---

## 🔄 Future Improvements

### Scheduled Jobs (Phase 4)
Using APScheduler:
- Morning briefing (8 AM daily)
- Budget summary (weekly)
- Task reminders (daily)
- Calendar sync (hourly)

### Webhooks
- Notion database changes
- Google Calendar updates
- Real-time synchronization

### Caching
- Redis for session storage
- Cache Notion database schemas
- Cache calendar events (5-minute TTL)

### Error Recovery
- Retry logic for API failures
- Circuit breaker pattern
- Graceful degradation

---

## 📝 Code Style & Standards

### Python
- PEP 8 compliant
- Type hints for all functions
- Docstrings for public APIs
- Max line length: 120 characters

### Async/Await
- All service methods are async
- Use `await` for I/O operations
- Don't block the event loop

### Error Handling
```python
try:
    result = await external_service.call()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail="User-friendly message")
```

### Testing
- Test files in `tests/` directory
- Use pytest with asyncio
- Mock external services
- Aim for >80% coverage

---

## 🐛 Known Issues & Limitations

### Current Limitations
1. No pagination for large result sets (>100 items)
2. No rate limiting implemented
3. No user authentication (single API key)
4. No database migrations (manual schema updates)
5. No offline mode (requires internet)

### Known Issues
1. OAuth token refresh may fail after 6 months (Google limit)
2. Notion API rate limits not enforced client-side
3. No retry logic for transient failures
4. Large calendar queries may timeout

### Workarounds
1. Re-authenticate OAuth every few months
2. Implement client-side rate limiting
3. Add exponential backoff retry logic
4. Add pagination for calendar queries

---

## 📚 Additional Resources

- **OpenAI API Docs**: https://platform.openai.com/docs/api-reference
- **Notion API Docs**: https://developers.notion.com/reference
- **Google Calendar API**: https://developers.google.com/calendar/api/guides/overview
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pydantic Docs**: https://docs.pydantic.dev/

---

## 🆘 Getting Help

### Debugging Checklist
1. ✅ Check `.env` file has all required variables
2. ✅ Verify API keys are valid and active
3. ✅ Confirm Notion databases are shared with integration
4. ✅ Check OAuth token exists (`google_token.json`)
5. ✅ Review application logs for errors
6. ✅ Test with Swagger UI at `/docs`
7. ✅ Verify network connectivity to external services

### Log Analysis
```bash
# Filter for errors
grep "ERROR" logs/app.log

# Filter for specific request
grep "req_id=abc123" logs/app.log

# Watch logs in real-time
tail -f logs/app.log
```

### Common Error Messages

**"OPENAI_API_KEY not configured"**
→ Add key to `.env` and restart server

**"Not authenticated with Google Calendar"**
→ Complete OAuth flow at `/auth/google`

**"Failed to create page: object_not_found"**
→ Database not shared with Notion integration

**"Invalid redirect_uri"**
→ Update redirect URI in Google Cloud Console

---

## 💡 Pro Tips

1. **Development Workflow**
   - Use `--reload` flag during development
   - Keep Swagger UI open for quick testing
   - Monitor logs in separate terminal

2. **Debugging AI Responses**
   - Check tool schemas in `app/ai/tools.py`
   - Verify tool execution in logs
   - Test tools directly via REST API first

3. **OAuth Token Management**
   - Keep backup of `google_token.json`
   - Document when tokens were created
   - Set calendar reminders for token refresh

4. **Notion Database Management**
   - Create test databases for development
   - Keep production data separate
   - Document database schema changes

5. **Cost Optimization**
   - Monitor OpenAI usage dashboard
   - Use `gpt-4o-mini` for cost savings
   - Cache responses when possible
   - Set max token limits

---

*Last Updated: October 4, 2025*
*Implementation Version: 1.0.0*
