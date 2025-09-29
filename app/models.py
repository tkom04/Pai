"""Pydantic models for request/response schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class Period(BaseModel):
    """Date period for budget scans."""
    from_date: str = Field(..., alias="from", description="Start date (YYYY-MM-DD)")
    to_date: str = Field(..., alias="to", description="End date (YYYY-MM-DD)")


class BudgetScanRequest(BaseModel):
    """Request model for budget scanning."""
    period: Period
    source: str = Field(default="csv", description="Data source: csv or notion")
    path: Optional[str] = Field(None, description="CSV file path when source=csv")


class CategorySummary(BaseModel):
    """Budget category summary."""
    name: str
    cap: float
    spent: float
    delta: float
    status: str


class BudgetScanResponse(BaseModel):
    """Response model for budget scanning."""
    period: Period
    categories: List[CategorySummary]
    buffer_remaining: float


class AddToGroceriesRequest(BaseModel):
    """Request model for adding items to groceries list."""
    item: str
    qty: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class AddToGroceriesResponse(BaseModel):
    """Response model for adding groceries."""
    ok: bool
    id: str
    item: Dict[str, Any]


# Status enums and update models
GroceryStatus = Literal["Needed", "Added", "Ordered"]


class UpdateGroceryStatusRequest(BaseModel):
    """Request model for updating grocery item status."""
    status: GroceryStatus


class CreateTaskRequest(BaseModel):
    """Request model for creating tasks."""
    title: str
    due: datetime
    context: str = Field(default="Home", description="Context: Home/Finance/Errand/Project")
    priority: str = Field(default="Med", description="Priority: Low/Med/High")


class CreateTaskResponse(BaseModel):
    """Response model for creating tasks."""
    ok: bool
    notion_page_id: str


TaskStatus = Literal["Not Started", "In Progress", "Done"]


class UpdateTaskStatusRequest(BaseModel):
    """Request model for updating task status."""
    status: TaskStatus


class CreateEventRequest(BaseModel):
    """Request model for creating calendar events."""
    title: str
    start: datetime
    end: datetime
    description: Optional[str] = None


class CreateEventResponse(BaseModel):
    """Response model for creating events."""
    ok: bool
    google_event_id: str


class HAServiceCallRequest(BaseModel):
    """Request model for Home Assistant service calls."""
    domain: str
    service: str
    entity_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class HAServiceCallResponse(BaseModel):
    """Response model for HA service calls."""
    ok: bool
    called: str
    entity_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    hint: Optional[str] = None
