"""Orbit - Personal AI Command Center - FastAPI application."""
import time
import uuid
import asyncio
import json
import os
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import httpx
from fastapi import FastAPI, Depends, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from cachetools import TTLCache
from asyncio import Lock
from collections import defaultdict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables from .env file
load_dotenv()


class ReauthRequired(Exception):
    """Raised when Open Banking re-authentication is required due to SCA expiry."""
    def __init__(self, connection_id: str | None = None, provider_id: str | None = None):
        self.connection_id = connection_id
        self.provider_id = provider_id
        super().__init__("Open banking re-authentication required")

from .deps import get_api_key, settings, get_current_user, get_supabase_client
from .models import (
    BudgetScanRequest, BudgetScanResponse,
    AddToGroceriesRequest, AddToGroceriesResponse,
    UpdateGroceryStatusRequest,
    CreateTaskRequest, CreateTaskResponse,
    UpdateTaskStatusRequest,
    CreateEventRequest, CreateEventResponse,
    UserLocationRequest, UserLocationResponse,
    ErrorResponse,
    # Open Banking models
    ListBankAccountsResponse,
    GetTransactionsRequest, GetTransactionsResponse,
    OpenBankingAuthStatusResponse,
    # Budget system models
    CreateBudgetCategoryRequest,
    CreateBudgetRuleRequest,
    BudgetSummaryResponse
)
from .services.budgets import budget_service
from .services.groceries import groceries_service
from .services.tasks import tasks_service
from .services.calendar import calendar_service
from .services.transaction_processor import transaction_processor
from .services.budget_engine import budget_engine
from .util.logging import logger
from .ai.router import router as ai_router
from .ai.tools import get_tool_names, tool_schemas
from .ai.tool_runtime import TOOL_DISPATCH
from .util.time import now, make_aware, to_aware_utc, utc_now
from .auth.google_oauth import oauth_manager
from .auth.open_banking import open_banking_oauth_manager
from .services.open_banking import open_banking_service
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="Personal AI Assistant",
    version="1.0.0",
    description="PAI - Centralized household operations API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ai_router)

# Thread-safe TTL cache for budget transactions
TRANSACTION_CACHE = TTLCache(
    maxsize=100,
    ttl=int(os.getenv("BUDGET_TRANSACTION_CACHE_TTL_SECONDS", "300"))
)
USER_LOCKS: Dict[str, Lock] = defaultdict(Lock)
_cache_lock = Lock()


@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests with timing."""
    start_time = time.time()
    req_id = str(uuid.uuid4())

    # Add request ID to logger context
    logger.info(f"Request started", extra={"req_id": req_id, "route": request.url.path})

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    logger.info(f"Request completed", extra={
        "req_id": req_id,
        "route": request.url.path,
        "elapsed_ms": process_time,
        "status_code": response.status_code
    })

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            hint="Check logs for details"
        ).dict()
    )


@app.get("/ping", dependencies=[Depends(get_api_key)])
async def ping():
    """Health check endpoint."""
    return {
        "status": "ok",
        "time": utc_now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/healthz")
async def healthz():
    """Health check endpoint without authentication (for Cloudflare Tunnel)."""
    return {"status": "ok", "time": utc_now().isoformat()}


@app.get("/ai/tools/health", dependencies=[Depends(get_api_key)])
async def ai_tools_health():
    """
    Health check endpoint for AI tools system.
    Tests tool schema generation, dispatcher availability, and provides diagnostic info.
    """
    try:
        # Get tool schemas
        schemas = tool_schemas()
        schema_names = list(schemas.keys())

        # Get dispatcher tools
        dispatcher_names = list(TOOL_DISPATCH.keys())

        # Check for mismatches
        schema_only = set(schema_names) - set(dispatcher_names)
        dispatcher_only = set(dispatcher_names) - set(schema_names)

        # Test a simple tool (dry run)
        test_result = None
        try:
            # Try to validate that add_to_groceries exists and is callable
            if "add_to_groceries" in TOOL_DISPATCH:
                test_result = "add_to_groceries function is accessible"
        except Exception as e:
            test_result = f"Error accessing tool: {str(e)}"

        health_status = {
            "status": "healthy" if not (schema_only or dispatcher_only) else "warning",
            "time": utc_now().isoformat(),
            "tools": {
                "total_schemas": len(schema_names),
                "total_dispatchers": len(dispatcher_names),
                "schema_names": schema_names,
                "dispatcher_names": dispatcher_names,
                "schema_only": list(schema_only) if schema_only else [],
                "dispatcher_only": list(dispatcher_only) if dispatcher_only else [],
            },
            "test": test_result,
            "openai_model": settings.OPENAI_MODEL,
            "openai_api_key_configured": bool(settings.OPENAI_API_KEY)
        }

        if schema_only or dispatcher_only:
            health_status["warning"] = "Mismatch between schemas and dispatchers"

        return health_status

    except Exception as e:
        logger.error(f"Tools health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "time": utc_now().isoformat()
            }
        )


@app.get("/budget_scan", dependencies=[Depends(get_api_key)])
async def get_budgets(user_id: str = Depends(get_current_user)):
    """Get current budget status with REAL Open Banking data."""
    logger.info("GET /budget_scan called")
    try:

        # Check if Open Banking is connected
        is_authenticated = await open_banking_oauth_manager.is_authenticated(user_id)
        logger.info(f"Open Banking authenticated: {is_authenticated}")

        if is_authenticated:
            # Fetch last 30 days of transactions from Open Banking
            from datetime import date, timedelta
            to_date = date.today()
            from_date = to_date - timedelta(days=30)

            logger.info(f"Fetching transactions from {from_date} to {to_date}")

            # Create a budget scan request with timeout protection
            request = BudgetScanRequest(
                period={"from": from_date.isoformat(), "to": to_date.isoformat()},
                source="open_banking"
            )

            import asyncio
            try:
                # Add 10 second timeout to prevent hanging
                result = await asyncio.wait_for(
                    budget_service.scan_budget(request, user_id=user_id),
                    timeout=10.0
                )
                logger.info(f"Budget scan complete: {len(result.categories)} categories")
            except asyncio.TimeoutError:
                logger.error("Budget scan timed out after 10 seconds")
                # Fall back to empty data
                return {
                    "budgets": [],
                    "transactions": [],
                    "error": "Timeout fetching bank data"
                }

            # Convert to frontend format
            budgets = [
                {
                    "name": cat.name,
                    "amount": cat.cap,  # 'cap' is the budget limit
                    "spent": cat.spent,
                    "category": cat.name.lower()
                }
                for cat in result.categories
            ]
            logger.info(f"Returning {len(budgets)} budgets to frontend")

            return {
                "budgets": budgets,
                "transactions": []  # Frontend doesn't use this for display
            }
        else:
            # Return empty if not connected
            logger.warning("Open Banking not authenticated - returning empty")
            return {
                "budgets": [],
                "transactions": []
            }
    except Exception as e:
        logger.error(f"Get budgets failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Get budgets failed: {str(e)}")


@app.post("/budget_scan", response_model=BudgetScanResponse, dependencies=[Depends(get_api_key)])
async def budget_scan(request: BudgetScanRequest, user_id: str = Depends(get_current_user)):
    """Scan budget for given period. Auto-detects Open Banking if connected."""
    try:

        # Auto-detect Open Banking if authenticated
        if request.source == "csv" or request.source is None:
            is_authenticated = await open_banking_oauth_manager.is_authenticated(user_id)
            if is_authenticated:
                logger.info("Open Banking detected - using real bank data")
                request.source = "open_banking"

        return await budget_service.scan_budget(request, user_id=user_id)
    except Exception as e:
        logger.error(f"Budget scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Budget scan failed: {str(e)}")


@app.post("/add_to_groceries", response_model=AddToGroceriesResponse, dependencies=[Depends(get_api_key)])
async def add_to_groceries(request: AddToGroceriesRequest, user_id: str = Depends(get_current_user)):
    """Add item to groceries list."""
    try:
        return await groceries_service.add_item(request, user_id)
    except Exception as e:
        logger.error(f"Add to groceries failed: {e}")
        raise HTTPException(status_code=500, detail=f"Add to groceries failed: {str(e)}")


@app.get("/groceries", dependencies=[Depends(get_api_key)])
async def get_groceries(user_id: str = Depends(get_current_user)):
    """List grocery items."""
    try:
        return {"items": await groceries_service.get_items(user_id)}
    except Exception as e:
        logger.error(f"Get groceries failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get groceries failed: {str(e)}")


@app.patch("/groceries/{item_id}", dependencies=[Depends(get_api_key)])
async def update_grocery_status(item_id: str = Path(..., description="Grocery item ID"), request: UpdateGroceryStatusRequest = ..., user_id: str = Depends(get_current_user)):
    """Update grocery item status."""
    try:
        # Convert status to boolean
        purchased = request.status.lower() in ['added', 'purchased', 'done']
        updated = await groceries_service.update_item_status(item_id, user_id, purchased)
        if not updated:
            raise HTTPException(status_code=404, detail="Grocery item not found")
        return {"ok": True, "id": item_id, "status": request.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update grocery status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update grocery status failed: {str(e)}")


@app.post("/create_task", response_model=CreateTaskResponse, dependencies=[Depends(get_api_key)])
async def create_task(request: CreateTaskRequest, user_id: str = Depends(get_current_user)):
    """Create a new task."""
    try:
        return await tasks_service.create_task(request, user_id)
    except Exception as e:
        logger.error(f"Create task failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create task failed: {str(e)}")


@app.get("/tasks", dependencies=[Depends(get_api_key)])
async def get_tasks(user_id: str = Depends(get_current_user)):
    """List tasks."""
    try:
        return {"tasks": await tasks_service.get_tasks(user_id)}
    except Exception as e:
        logger.error(f"Get tasks failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get tasks failed: {str(e)}")


@app.patch("/tasks/{task_id}", dependencies=[Depends(get_api_key)])
async def update_task_status(task_id: str = Path(..., description="Task ID"), request: UpdateTaskStatusRequest = ..., user_id: str = Depends(get_current_user)):
    """Update task status."""
    try:
        updated = await tasks_service.update_task_status(task_id, user_id, request.status)
        if not updated:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"ok": True, "id": task_id, "status": request.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update task status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update task status failed: {str(e)}")


@app.post("/debug_event", dependencies=[Depends(get_api_key)])
async def debug_event(request: CreateEventRequest):
    """Debug endpoint to see what we're receiving."""
    return {
        "title": request.title,
        "start": str(request.start),
        "start_type": str(type(request.start)),
        "start_tzinfo": str(request.start.tzinfo) if hasattr(request.start, 'tzinfo') else "N/A",
        "end": str(request.end),
        "end_type": str(type(request.end)),
        "end_tzinfo": str(request.end.tzinfo) if hasattr(request.end, 'tzinfo') else "N/A",
        "description": request.description
    }

@app.post("/create_event", response_model=CreateEventResponse, dependencies=[Depends(get_api_key)])
async def create_event(request: CreateEventRequest, user_id: str = Depends(get_current_user)):
    """Create a calendar event."""
    try:
        # Create calendar service instance with proper user_id
        from .services.calendar import CalendarService
        user_calendar_service = CalendarService(user_id)

        return await user_calendar_service.create_event(request)
    except Exception as e:
        logger.error(f"Create event failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create event failed: {str(e)}")


@app.get("/events", dependencies=[Depends(get_api_key)])
async def get_events(start: Optional[datetime] = Query(None), end: Optional[datetime] = Query(None), user_id: str = Depends(get_current_user)):
    """List events, optionally filtered by date range."""
    try:
        # CRITICAL FIX: Ensure timezone-aware dates using to_aware_utc
        start = to_aware_utc(start) if start else None
        end = to_aware_utc(end) if end else None

        # Create calendar service instance with proper user_id
        from .services.calendar import CalendarService
        user_calendar_service = CalendarService(user_id)

        return {"events": await user_calendar_service.get_events(start_date=start, end_date=end)}
    except ValueError as e:
        # Authentication or calendar access error - return empty list with message
        logger.warning(f"Calendar not accessible: {e}")
        return {
            "events": [],
            "message": "Google Calendar not connected. Please authenticate to see events.",
            "authenticated": False
        }
    except Exception as e:
        logger.error(f"Get events failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get events failed: {str(e)}")


# ==================== Google OAuth Endpoints ====================

@app.get("/auth/google")
async def google_oauth_init(user_id: str = Depends(get_current_user)):
    """Initiate Google OAuth flow."""
    try:
        authorization_url = oauth_manager.get_authorization_url(user_id)
        return {"authorization_url": authorization_url}
    except Exception as e:
        logger.error(f"Failed to initiate Google OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth initialization failed: {str(e)}")


@app.get("/auth/google/callback")
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter from Google"),
    error: Optional[str] = Query(None, description="Error parameter from Google")
):
    """Handle Google OAuth callback."""
    try:
        # Check for OAuth error first
        if error:
            logger.error(f"OAuth error from Google: {error}")
            return RedirectResponse(url="http://localhost:3000/calendar?auth=error&error=" + error)

        # Extract user_id from state parameter (set during OAuth initiation)
        user_id = state or "default-user"

        # Log the callback attempt
        logger.info(f"OAuth callback received - code: {code[:20]}..., state: {state}, user_id: {user_id}")

        success = await oauth_manager.exchange_code_for_token(code, user_id)
        if success:
            logger.info("Google OAuth completed successfully")
            return RedirectResponse(url="http://localhost:3000/calendar?auth=success")
        else:
            logger.error("Failed to exchange OAuth code for token")
            return RedirectResponse(url="http://localhost:3000/calendar?auth=error&error=token_exchange_failed")
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        return RedirectResponse(url=f"http://localhost:3000/calendar?auth=error&error={str(e)}")


@app.get("/auth/google/status")
async def google_oauth_status(user_id: str = Depends(get_current_user)):
    """Check Google OAuth authentication status."""
    try:
        is_authenticated = await oauth_manager.is_authenticated(user_id)
        return {
            "authenticated": is_authenticated,
            "service": "Google Calendar"
        }
    except Exception as e:
        logger.error(f"Failed to check OAuth status: {e}")
        return {
            "authenticated": False,
            "error": str(e)
        }


@app.post("/auth/google/revoke")
async def google_oauth_revoke(user_id: str = Depends(get_current_user)):
    """Revoke Google OAuth token."""
    try:
        success = await oauth_manager.revoke_token(user_id)
        if success:
            logger.info("Google OAuth token revoked")
            return {"ok": True, "message": "Authentication revoked"}
        else:
            raise HTTPException(status_code=400, detail="No active authentication to revoke")
    except Exception as e:
        logger.error(f"Failed to revoke OAuth token: {e}")
        raise HTTPException(status_code=500, detail=f"Token revocation failed: {str(e)}")


# ==================== Open Banking Endpoints ====================

@app.get("/auth/open-banking")
async def open_banking_oauth_init(user_id: str = Depends(get_current_user)):
    """Initiate Open Banking OAuth flow."""
    try:
        authorization_url = open_banking_oauth_manager.get_authorization_url(user_id)
        return {"authorization_url": authorization_url}
    except Exception as e:
        logger.error(f"Failed to initiate Open Banking OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth initialization failed: {str(e)}")


@app.get("/auth/open-banking/callback")
async def open_banking_oauth_callback(
    code: str = Query(..., description="Authorization code from TrueLayer"),
    state: Optional[str] = Query(None, description="State parameter from TrueLayer"),
    error: Optional[str] = Query(None, description="Error parameter from TrueLayer")
):
    """Handle Open Banking OAuth callback."""
    try:
        # Check for OAuth error first
        if error:
            logger.error(f"OAuth error from TrueLayer: {error}")
            return RedirectResponse(url=f"http://localhost:3000/budget?auth=error&error={error}")

        # Extract user_id from state (or use default)
        user_id = state or "default-user"

        # Exchange code for token
        success = await open_banking_oauth_manager.exchange_code_for_token(code, user_id)

        if success:
            # Sync bank accounts to database
            try:
                accounts_count = await open_banking_service.sync_bank_accounts(user_id)
                logger.info(f"Open Banking OAuth completed successfully, synced {accounts_count} accounts")
            except Exception as e:
                logger.warning(f"OAuth succeeded but account sync failed: {e}")
                # Continue anyway - accounts can be synced later

            return RedirectResponse(url="http://localhost:3000/budget?auth=success")
        else:
            logger.error("Failed to exchange OAuth code for token")
            return RedirectResponse(url="http://localhost:3000/budget?auth=error&error=token_exchange_failed")
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        return RedirectResponse(url=f"http://localhost:3000/budget?auth=error&error={str(e)}")


@app.get("/auth/open-banking/status", response_model=OpenBankingAuthStatusResponse)
async def open_banking_oauth_status(user_id: str = Depends(get_current_user)):
    """Check Open Banking OAuth authentication status."""
    try:
        is_authenticated = await open_banking_oauth_manager.is_authenticated(user_id)
        return OpenBankingAuthStatusResponse(
            ok=True,
            authenticated=is_authenticated,
            provider="truelayer",
            message="Connected to Open Banking" if is_authenticated else "Not connected"
        )
    except Exception as e:
        logger.error(f"Failed to check OAuth status: {e}")
        return OpenBankingAuthStatusResponse(
            ok=False,
            authenticated=False,
            message=f"Error checking status: {str(e)}"
        )


@app.post("/auth/open-banking/disconnect")
async def open_banking_disconnect(user_id: str = Depends(get_current_user)):
    """Disconnect Open Banking (revoke token)."""
    try:
        success = await open_banking_oauth_manager.revoke_token(user_id)
        if success:
            logger.info("Open Banking OAuth token revoked")
            return {"ok": True, "message": "Bank connection disconnected"}
        else:
            raise HTTPException(status_code=400, detail="No active bank connection to disconnect")
    except Exception as e:
        logger.error(f"Failed to disconnect Open Banking: {e}")
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {str(e)}")


@app.get("/api/bank-accounts", response_model=ListBankAccountsResponse, dependencies=[Depends(get_api_key)])
async def list_bank_accounts(user_id: str = Depends(get_current_user)):
    """List connected bank accounts (metadata only, no balances)."""
    try:
        # Check if authenticated
        is_authenticated = await open_banking_oauth_manager.is_authenticated(user_id)
        if not is_authenticated:
            return ListBankAccountsResponse(
                ok=False,
                accounts=[]
            )

        # Get accounts from TrueLayer API (real-time)
        accounts = await open_banking_service.get_bank_accounts(user_id)
        logger.info(f"Endpoint returning {len(accounts)} accounts: {[acc.display_name for acc in accounts]}")

        return ListBankAccountsResponse(
            ok=True,
            accounts=accounts
        )
    except Exception as e:
        logger.error(f"Failed to list bank accounts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list bank accounts: {str(e)}")


@app.post("/api/transactions", response_model=GetTransactionsResponse, dependencies=[Depends(get_api_key)])
async def get_transactions(request: GetTransactionsRequest, user_id: str = Depends(get_current_user)):
    """
    Fetch transactions in real-time from Open Banking API.

    CRITICAL: Transactions are NEVER stored - always fetched live.
    """
    try:
        # Check if authenticated
        is_authenticated = await open_banking_oauth_manager.is_authenticated(user_id)
        if not is_authenticated:
            raise HTTPException(
                status_code=401,
                detail="Not connected to Open Banking. Please connect your bank first."
            )

        # Fetch transactions in real-time
        transactions = await open_banking_service.get_transactions(
            user_id=user_id,
            account_id=request.account_id,
            from_date=request.from_date,
            to_date=request.to_date
        )

        return GetTransactionsResponse(
            ok=True,
            account_id=request.account_id,
            transactions=transactions,
            count=len(transactions)
        )
    except ValueError as e:
        # Auth errors - return helpful message
        logger.warning(f"Auth error fetching transactions: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch transactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")


# ==================== User Preferences Endpoints ====================

@app.get("/user/location", response_model=UserLocationResponse, dependencies=[Depends(get_api_key)])
async def get_user_location():
    """Get saved user location preference."""
    try:
        # For dev mode without auth, use NULL user_id (which RLS policies allow)
        user_id = None

        supabase = get_supabase_client()

        # Query with IS NULL for dev mode
        if user_id is None:
            result = supabase.table("user_preferences").select("*").is_("user_id", "null").execute()
        else:
            result = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()

        if result.data and len(result.data) > 0:
            pref = result.data[0]
            return UserLocationResponse(
                location_lat=pref.get("location_lat"),
                location_lon=pref.get("location_lon"),
                location_name=pref.get("location_name"),
                use_browser_location=pref.get("use_browser_location", True)
            )

        # Return default if no preference saved
        return UserLocationResponse()
    except Exception as e:
        logger.error(f"Failed to get user location: {e}", exc_info=True)
        # Return default on error instead of failing
        return UserLocationResponse()


@app.post("/user/location", response_model=UserLocationResponse, dependencies=[Depends(get_api_key)])
async def save_user_location(request: UserLocationRequest):
    """Save or update user location preference."""
    try:
        # For dev mode without auth, use NULL user_id (which RLS policies allow)
        user_id = None

        supabase = get_supabase_client()

        # First, delete any existing null user_id entries
        if user_id is None:
            supabase.table("user_preferences").delete().is_("user_id", "null").execute()

        # Prepare data
        data = {
            "user_id": user_id,
            "location_lat": request.location_lat,
            "location_lon": request.location_lon,
            "location_name": request.location_name,
            "use_browser_location": request.use_browser_location,
            "updated_at": utc_now().isoformat()
        }

        # Insert new record
        result = supabase.table("user_preferences").insert(data).execute()

        if result.data and len(result.data) > 0:
            pref = result.data[0]
            return UserLocationResponse(
                location_lat=pref.get("location_lat"),
                location_lon=pref.get("location_lon"),
                location_name=pref.get("location_name"),
                use_browser_location=pref.get("use_browser_location", True)
            )

        return UserLocationResponse(
            location_lat=request.location_lat,
            location_lon=request.location_lon,
            location_name=request.location_name,
            use_browser_location=request.use_browser_location
        )
    except Exception as e:
        logger.error(f"Failed to save user location: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save location: {str(e)}")


@app.delete("/user/location", dependencies=[Depends(get_api_key)])
async def delete_user_location():
    """Clear user location preference."""
    try:
        # For dev mode without auth, use NULL user_id
        user_id = None

        supabase = get_supabase_client()

        if user_id is None:
            supabase.table("user_preferences").delete().is_("user_id", "null").execute()
        else:
            supabase.table("user_preferences").delete().eq("user_id", user_id).execute()

        return {"ok": True, "message": "Location preference cleared"}
    except Exception as e:
        logger.error(f"Failed to delete user location: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear location: {str(e)}")


# ==================== Budget System Endpoints ====================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError)
)
async def fetch_transactions_with_retry(account_id, user_id, from_date, to_date):
    """Retry with exponential backoff, but not for SCA errors"""
    try:
        return await open_banking_service.get_transactions(
            user_id=user_id,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date
        )
    except httpx.HTTPStatusError as e:
        # Don't retry SCA errors (403 sca_exceeded)
        if e.response.status_code == 403:
            try:
                payload = e.response.json()
                if payload.get("error") == "sca_exceeded":
                    raise ReauthRequired(connection_id=account_id, provider_id="truelayer")
            except:
                pass
        raise


async def _fetch_all_accounts(accounts, user_id: str, from_date: str, to_date: str, failed_accounts: list):
    """Fetch transactions from all accounts with SCA error handling."""
    all_transactions = []

    for account in accounts:
        try:
            transactions = await open_banking_service.get_transactions(
                user_id, account.id, from_date, to_date
            )
            all_transactions.extend(transactions)
        except ReauthRequired as e:
            logger.warning(f"SCA required for account {account.display_name}: {e}")
            failed_accounts.append(account.display_name)
        except Exception as e:
            logger.error(f"Failed to fetch transactions for account {account.display_name}: {e}")
            failed_accounts.append(account.display_name)

    return all_transactions


@app.post("/api/budget/refresh")
async def budget_refresh(
    lookback_days: int = Query(90, ge=1, le=365),
    user_id: str = Depends(get_current_user)
):
    """FIXED: OAuth refresh + timeout + concurrency lock"""
    lock = USER_LOCKS[user_id]

    if lock.locked():
        raise HTTPException(409, {
            "error": "refresh_in_progress",
            "message": "Budget refresh already running. Please wait."
        })

    async with lock:
        try:
            # Check OAuth (with automatic refresh on expiry)
            try:
                is_auth = await open_banking_oauth_manager.is_authenticated(user_id)
                if not is_auth:
                    raise HTTPException(401, "Connect your bank first")
            except Exception as e:
                # Attempt automatic refresh
                try:
                    await open_banking_oauth_manager.refresh_access_token(user_id)
                except Exception as refresh_error:
                    logger.warning(f"Token refresh failed: {refresh_error}")
                    raise HTTPException(401, {
                        "error": "session_expired",
                        "message": "Please reconnect your bank",
                        "action": "/connect-bank"
                    })

            # Fetch accounts
            accounts = await open_banking_service.get_bank_accounts(user_id)
            if not accounts:
                raise HTTPException(404, "No bank accounts found")

            # Fetch transactions with 30s timeout
            from_date = (utc_now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
            to_date = utc_now().strftime("%Y-%m-%d")

            all_transactions = []
            failed_accounts = []

            try:
                # Wrap in timeout
                fetch_task = asyncio.create_task(
                    _fetch_all_accounts(accounts, user_id, from_date, to_date, failed_accounts)
                )
                all_transactions = await asyncio.wait_for(fetch_task, timeout=30.0)
            except asyncio.TimeoutError:
                raise HTTPException(504, {
                    "error": "timeout",
                    "message": "Your bank is taking too long. Try reducing lookback_days.",
                    "current_lookback": lookback_days
                })

            # Process transactions
            normalized = await transaction_processor.normalize_batch(all_transactions)
            categorized = await transaction_processor.apply_rules(normalized, user_id)

            # Cache with lock
            summary_id = str(uuid.uuid4())
            async with _cache_lock:
                TRANSACTION_CACHE[user_id] = {
                    "transactions": categorized,
                    "summary_id": summary_id,
                    "timestamp": utc_now()
                }

            # Log audit event
            await log_audit_event(user_id, "budget_refresh_success", {
                "transaction_count": len(categorized),
                "account_count": len(accounts),
                "failed_accounts": len(failed_accounts),
                "lookback_days": lookback_days
            })

            coverage = sum(1 for tx in categorized if tx.category) / len(categorized) if categorized else 0

            response = {
                "ok": True,
                "summary_id": summary_id,
                "transactions_count": len(categorized),
                "coverage": coverage,
                "last_updated": utc_now().isoformat()
            }

            if failed_accounts:
                response["warnings"] = [{
                    "type": "partial_failure",
                    "message": f"{len(failed_accounts)} account(s) failed to fetch",
                    "failed_accounts": failed_accounts
                }]

                # Check if any failures were due to SCA requirements
                if len(failed_accounts) == len(accounts):
                    # All accounts failed - likely SCA issue
                    response["status"] = "reauth_required"
                    response["message"] = "Bank re-authentication required. Please reconnect your bank account."

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Budget refresh error: {e}", exc_info=True)
            raise HTTPException(500, f"Failed to refresh: {str(e)}")


async def _fetch_all_accounts(accounts, user_id, from_date, to_date, failed_accounts):
    """Fetch from all accounts, continue on partial failure"""
    all_txs = []
    for account in accounts:
        try:
            txs = await fetch_transactions_with_retry(
                account.provider_account_id,
                user_id,
                from_date,
                to_date
            )
            all_txs.extend(txs)
        except ReauthRequired as e:
            logger.warning(f"SCA required for account {account.display_name}: {e}")
            failed_accounts.append(account.display_name)
            continue
        except Exception as e:
            logger.warning(f"Failed to fetch account {account.display_name}: {e}")
            failed_accounts.append(account.display_name)
            continue
    return all_txs


async def log_audit_event(user_id: str, event_type: str, metadata: dict):
    """Log non-PII audit event"""
    supabase = get_supabase_client()

    supabase.table("audit_events").insert({
        "user_id": user_id,
        "event_type": event_type,
        "metadata": metadata
    }).execute()


@app.get("/api/budget/summary")
async def get_budget_summary(
    period: str = Query(..., regex=r"^\d{4}-(0[1-9]|1[0-2])$"),
    user_id: str = Depends(get_current_user)
):
    """Get budget summary for period"""
    try:
        async with _cache_lock:
            cache = TRANSACTION_CACHE.get(user_id)

        if not cache:
            # No cached data available, try to refresh automatically
            logger.info(f"No cached data for user {user_id}, attempting automatic refresh")
            try:
                # Trigger a background refresh with shorter lookback to avoid timeout
                await budget_refresh(lookback_days=30, user_id=user_id)

                # Check cache again after refresh
                async with _cache_lock:
                    cache = TRANSACTION_CACHE.get(user_id)

                if not cache:
                    raise HTTPException(422, "No data available. Please refresh your budget data.")

            except HTTPException as e:
                if e.status_code == 409:  # Refresh already in progress
                    raise HTTPException(422, "Budget refresh in progress. Please wait a moment and try again.")
                elif e.status_code == 401:  # Not authenticated
                    raise HTTPException(401, "Please connect your bank first.")
                else:
                    raise HTTPException(422, "No data available. Please refresh your budget data.")

        transactions = cache["transactions"]
        summary = await budget_engine.calculate_summary(
            transactions,
            user_id,
            period
        )

        return summary.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get summary error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get summary: {str(e)}")


@app.post("/api/budget/categories")
async def create_budget_category(
    request: CreateBudgetCategoryRequest,
    user_id: str = Depends(get_current_user)
):
    """Create/update category via Supabase client"""
    supabase = get_supabase_client()

    category_data = {
        "user_id": user_id,
        "key": request.key,
        "label": request.label,
        "target": float(request.target),
        "rollover": request.rollover,
        "order": request.order
    }

    result = supabase.table("budget_categories").upsert(category_data).execute()
    return {"ok": True, "category": result.data[0]}


@app.get("/api/budget/categories")
async def list_budget_categories(user_id: str = Depends(get_current_user)):
    """List all categories"""
    supabase = get_supabase_client()

    result = supabase.table("budget_categories").select("*").eq("user_id", user_id).order("order").execute()
    return {"categories": result.data}


@app.delete("/api/budget/categories/{category_key}")
async def delete_budget_category(
    category_key: str = Path(..., regex=r'^[a-z_]+$'),  # Whitelist pattern
    user_id: str = Depends(get_current_user)
):
    """Delete category"""
    supabase = get_supabase_client()

    result = supabase.table("budget_categories").delete().eq("user_id", user_id).eq("key", category_key).execute()

    if not result.data:
        raise HTTPException(404, "Category not found")
    return {"ok": True}


@app.post("/api/budget/rules")
async def create_budget_rule(
    request: CreateBudgetRuleRequest,
    user_id: str = Depends(get_current_user)
):
    """Create rule via Supabase client"""
    supabase = get_supabase_client()

    rule_data = {
        "user_id": user_id,
        "priority": request.priority,
        "matchers": request.matchers,
        "category_key": request.category_key,
        "created_by": "user"
    }

    result = supabase.table("budget_rules").insert(rule_data).execute()
    return {"ok": True, "rule": result.data[0]}


@app.get("/api/budget/rules")
async def list_budget_rules(user_id: str = Depends(get_current_user)):
    """List rules"""
    supabase = get_supabase_client()

    result = supabase.table("budget_rules").select("*").eq("user_id", user_id).order("priority").execute()
    return {"rules": result.data}


@app.delete("/api/budget/rules/{rule_id}")
async def delete_budget_rule(
    rule_id: str = Path(...),
    user_id: str = Depends(get_current_user)
):
    """Delete rule"""
    supabase = get_supabase_client()

    # Validate UUID format
    try:
        uuid.UUID(rule_id)
    except ValueError:
        raise HTTPException(400, "Invalid rule ID format")

    result = supabase.table("budget_rules").delete().eq("id", rule_id).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(404, "Rule not found")
    return {"ok": True}


@app.get("/api/budget/settings")
async def get_budget_settings(user_id: str = Depends(get_current_user)):
    """Get user budget settings"""
    supabase = get_supabase_client()

    result = supabase.table("budget_settings").select("*").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]
    else:
        # Return default settings
        return {
            "currency": "GBP",
            "cycle_start_day": 1,
            "show_ai_overview": False
        }


@app.post("/api/budget/settings")
async def update_budget_settings(
    settings: dict,
    user_id: str = Depends(get_current_user)
):
    """Update user budget settings"""
    supabase = get_supabase_client()

    result = supabase.table("budget_settings").upsert({
        "user_id": user_id,
        **settings
    }).execute()

    return {"ok": True, "settings": result.data[0]}


# ==================== Multi-Bank Budget Enhancement Endpoints ====================

@app.delete("/api/banking/revoke/{connection_id}")
async def revoke_bank_connection(
    connection_id: str = Path(..., description="Bank connection ID to revoke"),
    user_id: str = Depends(get_current_user)
):
    """Revoke bank connection with privacy-first data deletion."""
    try:
        success = await open_banking_oauth_manager.revoke_token(user_id, connection_id)
        if success:
            logger.info(f"Bank connection {connection_id} revoked for user {user_id}")
            return {"ok": True, "message": "Bank connection revoked and all data deleted"}
        else:
            raise HTTPException(status_code=400, detail="Failed to revoke bank connection")
    except Exception as e:
        logger.error(f"Failed to revoke bank connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to revoke connection: {str(e)}")


@app.post("/api/budget/detect-transfers")
async def detect_transfers(user_id: str = Depends(get_current_user)):
    """Detect transfers between user's accounts."""
    try:
        from .services.multibank_detector import multibank_detector

        # Get recent transactions from cache
        supabase = get_supabase_client()
        cache_result = supabase.table("transaction_cache").select("*").eq(
            "user_id", user_id
        ).gte("posted_at", (utc_now() - timedelta(days=30)).isoformat()).execute()

        if not cache_result.data:
            return {"ok": False, "message": "No transaction data available. Please refresh your budget first."}

        # Convert to NormalizedTransaction objects
        from .models import NormalizedTransaction
        transactions = []
        for tx_data in cache_result.data:
            tx = NormalizedTransaction(
                id=tx_data['tx_hash'],
                posted_at=datetime.fromisoformat(tx_data['posted_at']),
                amount=Decimal(str(tx_data['amount'])),
                currency='GBP',
                description='',
                merchant=tx_data.get('merchant'),
                account_id=tx_data['account_id'],
                category=tx_data.get('category'),
                is_transfer=tx_data.get('is_transfer', False),
                is_duplicate=tx_data.get('is_duplicate', False)
            )
            transactions.append(tx)

        # Detect transfers
        transfers = await multibank_detector.detect_transfers(user_id, transactions)

        return {
            "ok": True,
            "transfers_detected": len(transfers),
            "transfers": transfers
        }
    except Exception as e:
        logger.error(f"Failed to detect transfers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to detect transfers: {str(e)}")


@app.post("/api/budget/auto-generate")
async def auto_generate_budget(
    lookback_days: int = Query(90, ge=30, le=365),
    user_id: str = Depends(get_current_user)
):
    """Generate budget from spending patterns using AI."""
    try:
        from .services.budget_ai import budget_ai

        result = await budget_ai.generate_budget_from_patterns(user_id, lookback_days)

        if 'error' in result:
            raise HTTPException(status_code=422, detail=result['error'])

        return {
            "ok": True,
            "suggested_categories": result['suggested_categories'],
            "debt_recommendations": result['debt_recommendations'],
            "spending_insights": result['spending_insights'],
            "total_analyzed": result['total_analyzed']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to auto-generate budget: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate budget: {str(e)}")


@app.get("/api/budget/debt-accounts")
async def get_debt_accounts(user_id: str = Depends(get_current_user)):
    """Get debt accounts with paydown strategy suggestions."""
    try:
        from .services.budget_ai import budget_ai

        supabase = get_supabase_client()
        debt_result = supabase.table("debt_accounts").select("*").eq("user_id", user_id).execute()
        debt_accounts = debt_result.data if debt_result.data else []

        if not debt_accounts:
            return {
                "ok": True,
                "debt_accounts": [],
                "strategy": "none",
                "message": "No debt accounts found"
            }

        # Generate strategy recommendations
        strategy_result = await budget_ai.suggest_debt_paydown_strategy(user_id, debt_accounts)

        return {
            "ok": True,
            "debt_accounts": debt_accounts,
            "strategy": strategy_result['strategy'],
            "recommendation": strategy_result['recommendation'],
            "reasoning": strategy_result['reasoning'],
            "avalanche": strategy_result['avalanche'],
            "snowball": strategy_result['snowball']
        }
    except Exception as e:
        logger.error(f"Failed to get debt accounts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get debt accounts: {str(e)}")


@app.put("/api/budget/confirm-duplicate/{tx_hash}")
async def confirm_duplicate_transaction(
    tx_hash: str = Path(..., description="Transaction hash to mark as duplicate"),
    is_duplicate: bool = Query(..., description="Whether this is a duplicate"),
    user_id: str = Depends(get_current_user)
):
    """Mark transaction as duplicate for exclusion from budget calculations."""
    try:
        supabase = get_supabase_client()

        # Update transaction cache
        result = supabase.table("transaction_cache").update({
            "is_duplicate": is_duplicate
        }).eq("user_id", user_id).eq("tx_hash", tx_hash).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Update duplicate_transactions table
        supabase.table("duplicate_transactions").update({
            "user_confirmed": True,
            "is_duplicate": is_duplicate
        }).eq("user_id", user_id).or_(f"tx1_hash.eq.{tx_hash},tx2_hash.eq.{tx_hash}").execute()

        return {
            "ok": True,
            "message": f"Transaction marked as {'duplicate' if is_duplicate else 'not duplicate'}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to confirm duplicate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update transaction: {str(e)}")


@app.get("/api/banking/connections")
async def get_bank_connections(user_id: str = Depends(get_current_user)):
    """List all bank connections for user with real-time institution metadata."""
    try:
        supabase = get_supabase_client()

        # Get bank connections
        connections_result = supabase.table("bank_connections").select("*").eq("user_id", user_id).execute()
        connections = connections_result.data if connections_result.data else []

        # Get tokens for each connection
        tokens_result = supabase.table("open_banking_tokens").select("*").eq("user_id", user_id).execute()
        tokens = {token['id']: token for token in tokens_result.data} if tokens_result.data else {}

        # Enrich with real-time institution metadata
        enriched_connections = []
        for connection in connections:
            token_id = connection['token_id']
            token = tokens.get(token_id, {})

            # Get institution metadata
            institution_metadata = await open_banking_oauth_manager.get_institution_metadata(
                connection.get('institution_id', '')
            )

            # Calculate consent expiry
            consent_expires_at = token.get('consent_expires_at')
            days_until_expiry = None
            if consent_expires_at:
                try:
                    expiry_date = datetime.fromisoformat(consent_expires_at.replace('Z', '+00:00'))
                    days_until_expiry = (expiry_date - utc_now()).days
                except Exception:
                    pass

            # Test token validity to detect SCA expiry (only if needed)
            token_test = None
            if connection.get('status') == 'active' or days_until_expiry is None or days_until_expiry > 0:
                # Only test token validity for potentially active connections
                try:
                    token_test = await open_banking_oauth_manager.test_token_validity(user_id, token_id)
                except Exception as e:
                    logger.warning(f"Token validity test failed for connection {connection['id']}: {e}")
                    token_test = {"valid": False, "reason": "test_failed", "sca_expired": False}
            else:
                # Skip testing for clearly expired connections
                token_test = {"valid": False, "reason": "expired", "sca_expired": False}

            # Determine status based on token test and expiry
            if token_test and token_test.get("sca_expired"):
                status = "reauth_required"
            elif days_until_expiry is not None and days_until_expiry <= 0:
                status = "expired"
            elif days_until_expiry is not None and days_until_expiry <= 7:
                status = "expiring_soon"
            elif token_test and token_test.get("valid"):
                status = "active"
            else:
                status = "error"

            enriched_connection = {
                **connection,
                'institution_logo': institution_metadata.get('logo', 'bank') if institution_metadata else 'bank',
                'institution_display_name': institution_metadata.get('name', connection.get('institution_name', 'Unknown Bank')) if institution_metadata else connection.get('institution_name', 'Unknown Bank'),
                'days_until_expiry': days_until_expiry,
                'status': status,
                'token_valid': token_test.get('valid', False),
                'sca_expired': token_test.get('sca_expired', False),
                'last_sync': token.get('last_sync_at')
            }
            enriched_connections.append(enriched_connection)

        return {
            "ok": True,
            "connections": enriched_connections,
            "total_connections": len(enriched_connections)
        }
    except Exception as e:
        logger.error(f"Failed to get bank connections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get connections: {str(e)}")

@app.post("/api/banking/test-token")
async def test_bank_token(user_id: str = Depends(get_current_user)):
    """Test if bank token is valid and not affected by SCA expiry."""
    try:
        token_test = await open_banking_oauth_manager.test_token_validity(user_id)

        if token_test.get("sca_expired"):
            return {
                "valid": False,
                "sca_expired": True,
                "message": "Bank re-authentication required. Please reconnect your bank account.",
                "action": "reauth_required"
            }
        elif token_test.get("valid"):
            return {
                "valid": True,
                "sca_expired": False,
                "message": "Bank connection is working properly.",
                "action": "none"
            }
        else:
            return {
                "valid": False,
                "sca_expired": False,
                "message": f"Bank connection issue: {token_test.get('reason', 'unknown')}",
                "action": "check_connection"
            }
    except Exception as e:
        logger.error(f"Error testing bank token: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to test token: {str(e)}")

@app.post("/api/banking/extend-connection/{connection_id}")
async def extend_bank_connection(connection_id: str, user_id: str = Depends(get_current_user)):
    """Extend a TrueLayer bank connection using the /connections/extend endpoint."""
    try:
        result = await open_banking_oauth_manager.extend_connection(user_id, connection_id)

        if result["success"]:
            return {
                "ok": True,
                "message": result["message"],
                "expires_in": result.get("expires_in"),
                "consent_expires_at": result.get("consent_expires_at")
            }
        else:
            error_code = result.get("error", "unknown")
            if error_code == "validation_error":
                # TrueLayer validation error - return as 400 to preserve details
                raise HTTPException(400, {
                    "error": "validation_error",
                    "message": result["message"],
                    "details": result.get("details", {})
                })
            elif error_code == "reauth_required":
                raise HTTPException(401, {
                    "error": "reauth_required",
                    "message": result["message"]
                })
            elif error_code == "consent_required":
                raise HTTPException(403, {
                    "error": "consent_required",
                    "message": result["message"]
                })
            else:
                raise HTTPException(500, {
                    "error": error_code,
                    "message": result["message"]
                })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extending bank connection: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to extend connection: {str(e)}")

@app.post("/api/budget/process-multibank")
async def process_multibank_detection(user_id: str = Depends(get_current_user)):
    """Process transactions with multi-bank detection (transfers, duplicates, UK utilities)."""
    try:
        from .services.multibank_detector import multibank_detector

        # Get recent transactions from cache
        supabase = get_supabase_client()
        cache_result = supabase.table("transaction_cache").select("*").eq(
            "user_id", user_id
        ).gte("posted_at", (utc_now() - timedelta(days=90)).isoformat()).execute()

        if not cache_result.data:
            return {"ok": False, "message": "No transaction data available. Please refresh your budget first."}

        # Convert to NormalizedTransaction objects
        from .models import NormalizedTransaction
        transactions = []
        for tx_data in cache_result.data:
            tx = NormalizedTransaction(
                id=tx_data['tx_hash'],
                posted_at=datetime.fromisoformat(tx_data['posted_at']),
                amount=Decimal(str(tx_data['amount'])),
                currency='GBP',
                description='',
                merchant=tx_data.get('merchant'),
                account_id=tx_data['account_id'],
                category=tx_data.get('category'),
                is_transfer=tx_data.get('is_transfer', False),
                is_duplicate=tx_data.get('is_duplicate', False)
            )
            transactions.append(tx)

        # Process with multi-bank detection
        result = await multibank_detector.process_transactions(user_id, transactions)

        return {
            "ok": True,
            "summary": result,
            "message": f"Processed {result['total_processed']} transactions"
        }
    except Exception as e:
        logger.error(f"Failed to process multi-bank detection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process transactions: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
