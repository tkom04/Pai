"""Orbit - Personal AI Command Center - FastAPI application."""
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    OpenBankingAuthStatusResponse
)
from .services.budgets import budget_service
from .services.groceries import groceries_service
from .services.tasks import tasks_service
from .services.calendar import calendar_service
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
async def get_budgets():
    """Get current budget status with REAL Open Banking data."""
    logger.info("GET /budget_scan called")
    try:
        user_id = "default-user"

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
async def budget_scan(request: BudgetScanRequest):
    """Scan budget for given period. Auto-detects Open Banking if connected."""
    try:
        user_id = "default-user"

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
async def add_to_groceries(request: AddToGroceriesRequest):
    """Add item to groceries list."""
    try:
        return await groceries_service.add_item(request, "default-user")
    except Exception as e:
        logger.error(f"Add to groceries failed: {e}")
        raise HTTPException(status_code=500, detail=f"Add to groceries failed: {str(e)}")


@app.get("/groceries", dependencies=[Depends(get_api_key)])
async def get_groceries():
    """List grocery items."""
    try:
        return {"items": await groceries_service.get_items("default-user")}
    except Exception as e:
        logger.error(f"Get groceries failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get groceries failed: {str(e)}")


@app.patch("/groceries/{item_id}", dependencies=[Depends(get_api_key)])
async def update_grocery_status(item_id: str = Path(..., description="Grocery item ID"), request: UpdateGroceryStatusRequest = ...):
    """Update grocery item status."""
    try:
        # Convert status to boolean
        purchased = request.status.lower() in ['added', 'purchased', 'done']
        updated = await groceries_service.update_item_status(item_id, "default-user", purchased)
        if not updated:
            raise HTTPException(status_code=404, detail="Grocery item not found")
        return {"ok": True, "id": item_id, "status": request.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update grocery status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update grocery status failed: {str(e)}")


@app.post("/create_task", response_model=CreateTaskResponse, dependencies=[Depends(get_api_key)])
async def create_task(request: CreateTaskRequest):
    """Create a new task."""
    try:
        return await tasks_service.create_task(request, "default-user")
    except Exception as e:
        logger.error(f"Create task failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create task failed: {str(e)}")


@app.get("/tasks", dependencies=[Depends(get_api_key)])
async def get_tasks():
    """List tasks."""
    try:
        return {"tasks": await tasks_service.get_tasks("default-user")}
    except Exception as e:
        logger.error(f"Get tasks failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get tasks failed: {str(e)}")


@app.patch("/tasks/{task_id}", dependencies=[Depends(get_api_key)])
async def update_task_status(task_id: str = Path(..., description="Task ID"), request: UpdateTaskStatusRequest = ...):
    """Update task status."""
    try:
        updated = await tasks_service.update_task_status(task_id, "default-user", request.status)
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
async def create_event(request: CreateEventRequest):
    """Create a calendar event."""
    try:
        return await calendar_service.create_event(request)
    except Exception as e:
        logger.error(f"Create event failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create event failed: {str(e)}")


@app.get("/events", dependencies=[Depends(get_api_key)])
async def get_events(start: Optional[datetime] = Query(None), end: Optional[datetime] = Query(None)):
    """List events, optionally filtered by date range."""
    try:
        # CRITICAL FIX: Ensure timezone-aware dates using to_aware_utc
        start = to_aware_utc(start) if start else None
        end = to_aware_utc(end) if end else None
        return {"events": await calendar_service.get_events(start_date=start, end_date=end)}
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
async def google_oauth_init():
    """Initiate Google OAuth flow."""
    try:
        # Use default-user for dev mode
        user_id = "default-user"
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
            return RedirectResponse(url="http://localhost:3000/settings?auth=error&error=" + error)

        # Use default-user for dev mode
        user_id = "default-user"

        # Log the callback attempt
        logger.info(f"OAuth callback received - code: {code[:20]}..., state: {state}")

        success = await oauth_manager.exchange_code_for_token(code, user_id)
        if success:
            logger.info("Google OAuth completed successfully")
            return RedirectResponse(url="http://localhost:3000/settings?auth=success")
        else:
            logger.error("Failed to exchange OAuth code for token")
            return RedirectResponse(url="http://localhost:3000/settings?auth=error&error=token_exchange_failed")
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        return RedirectResponse(url=f"http://localhost:3000/settings?auth=error&error={str(e)}")


@app.get("/auth/google/status")
async def google_oauth_status():
    """Check Google OAuth authentication status."""
    try:
        # Use default-user for dev mode
        user_id = "default-user"
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
async def google_oauth_revoke():
    """Revoke Google OAuth token."""
    try:
        # Use default-user for dev mode
        user_id = "default-user"
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
async def open_banking_oauth_init():
    """Initiate Open Banking OAuth flow."""
    try:
        # Use default-user for dev mode
        user_id = "default-user"
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
async def open_banking_oauth_status():
    """Check Open Banking OAuth authentication status."""
    try:
        # Use default-user for dev mode
        user_id = "default-user"
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
async def open_banking_disconnect():
    """Disconnect Open Banking (revoke token)."""
    try:
        # Use default-user for dev mode
        user_id = "default-user"
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
async def list_bank_accounts():
    """List connected bank accounts (metadata only, no balances)."""
    try:
        # Use default-user for dev mode
        user_id = "default-user"

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
async def get_transactions(request: GetTransactionsRequest):
    """
    Fetch transactions in real-time from Open Banking API.

    CRITICAL: Transactions are NEVER stored - always fetched live.
    """
    try:
        # Use default-user for dev mode
        user_id = "default-user"

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
