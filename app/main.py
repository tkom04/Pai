"""Personal AI Assistant - FastAPI application."""
import time
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .deps import get_api_key, settings
from .models import (
    BudgetScanRequest, BudgetScanResponse,
    AddToGroceriesRequest, AddToGroceriesResponse,
    UpdateGroceryStatusRequest,
    CreateTaskRequest, CreateTaskResponse,
    UpdateTaskStatusRequest,
    CreateEventRequest, CreateEventResponse,
    HAServiceCallRequest, HAServiceCallResponse,
    ErrorResponse
)
from .services.budgets import budget_service
from .services.groceries import groceries_service
from .services.tasks import tasks_service
from .services.calendar import calendar_service
from .services.ha import ha_service
from .util.logging import logger
from .ai.router import router as ai_router
from .ai.tools import get_tool_names, tool_schemas
from .ai.tool_runtime import TOOL_DISPATCH
from .util.time import now
from .auth.google_oauth import oauth_manager
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
        "time": now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/healthz")
async def healthz():
    """Health check endpoint without authentication (for Cloudflare Tunnel)."""
    return {"status": "ok", "time": now().isoformat()}


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
            "time": now().isoformat(),
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
                "time": now().isoformat()
            }
        )


@app.post("/budget_scan", response_model=BudgetScanResponse, dependencies=[Depends(get_api_key)])
async def budget_scan(request: BudgetScanRequest):
    """Scan budget for given period."""
    try:
        return await budget_service.scan_budget(request)
    except Exception as e:
        logger.error(f"Budget scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Budget scan failed: {str(e)}")


@app.post("/add_to_groceries", response_model=AddToGroceriesResponse, dependencies=[Depends(get_api_key)])
async def add_to_groceries(request: AddToGroceriesRequest):
    """Add item to groceries list."""
    try:
        return await groceries_service.add_item(request)
    except Exception as e:
        logger.error(f"Add to groceries failed: {e}")
        raise HTTPException(status_code=500, detail=f"Add to groceries failed: {str(e)}")


@app.get("/groceries", dependencies=[Depends(get_api_key)])
async def get_groceries():
    """List grocery items."""
    try:
        return {"items": await groceries_service.get_items()}
    except Exception as e:
        logger.error(f"Get groceries failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get groceries failed: {str(e)}")


@app.patch("/groceries/{item_id}", dependencies=[Depends(get_api_key)])
async def update_grocery_status(item_id: str = Path(..., description="Grocery item ID"), request: UpdateGroceryStatusRequest = ...):
    """Update grocery item status."""
    try:
        updated = await groceries_service.update_item_status(item_id, request.status)
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
        return await tasks_service.create_task(request)
    except Exception as e:
        logger.error(f"Create task failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create task failed: {str(e)}")


@app.get("/tasks", dependencies=[Depends(get_api_key)])
async def get_tasks():
    """List tasks."""
    try:
        return {"tasks": await tasks_service.get_tasks()}
    except Exception as e:
        logger.error(f"Get tasks failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get tasks failed: {str(e)}")


@app.patch("/tasks/{task_id}", dependencies=[Depends(get_api_key)])
async def update_task_status(task_id: str = Path(..., description="Task ID"), request: UpdateTaskStatusRequest = ...):
    """Update task status."""
    try:
        updated = await tasks_service.update_task_status(task_id, request.status)
        if not updated:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"ok": True, "id": task_id, "status": request.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update task status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update task status failed: {str(e)}")


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


@app.post("/ha_service_call", response_model=HAServiceCallResponse, dependencies=[Depends(get_api_key)])
async def ha_service_call(request: HAServiceCallRequest):
    """Call a Home Assistant service."""
    try:
        return await ha_service.call_service(request)
    except Exception as e:
        logger.error(f"HA service call failed: {e}")
        raise HTTPException(status_code=500, detail=f"HA service call failed: {str(e)}")


@app.get("/ha_entities", dependencies=[Depends(get_api_key)])
async def ha_entities(domain: Optional[str] = Query(None)):
    """List HA entities (optional filter by domain)."""
    try:
        entities = await ha_service.get_entities(domain=domain)  # type: ignore[attr-defined]
        return {"entities": entities}
    except Exception as e:
        logger.error(f"Get HA entities failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get HA entities failed: {str(e)}")


# ==================== Google OAuth Endpoints ====================

@app.get("/auth/google")
async def google_oauth_init():
    """Initiate Google OAuth flow."""
    try:
        authorization_url = oauth_manager.get_authorization_url()
        return {"authorization_url": authorization_url}
    except Exception as e:
        logger.error(f"Failed to initiate Google OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth initialization failed: {str(e)}")


@app.get("/auth/google/callback")
async def google_oauth_callback(code: str = Query(..., description="Authorization code from Google")):
    """Handle Google OAuth callback."""
    try:
        success = oauth_manager.exchange_code_for_token(code)
        if success:
            logger.info("Google OAuth completed successfully")
            return RedirectResponse(url="/?auth=success")
        else:
            logger.error("Failed to exchange OAuth code for token")
            raise HTTPException(status_code=400, detail="Failed to complete authentication")
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@app.get("/auth/google/status")
async def google_oauth_status():
    """Check Google OAuth authentication status."""
    try:
        is_authenticated = oauth_manager.is_authenticated()
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
        success = oauth_manager.revoke_token()
        if success:
            logger.info("Google OAuth token revoked")
            return {"ok": True, "message": "Authentication revoked"}
        else:
            raise HTTPException(status_code=400, detail="No active authentication to revoke")
    except Exception as e:
        logger.error(f"Failed to revoke OAuth token: {e}")
        raise HTTPException(status_code=500, detail=f"Token revocation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
