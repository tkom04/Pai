"""Personal AI Assistant - FastAPI application."""
import time
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from .util.time import now

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
