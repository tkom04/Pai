"""Pydantic models for request/response schemas."""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


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

    @field_validator('due')
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware after Pydantic parses it."""
        if v is None:
            return v

        # If it's a datetime without timezone info, make it UTC
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)

        return v


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

    @field_validator('start', 'end')
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware after Pydantic parses it."""
        if v is None:
            return v

        # If it's a datetime without timezone info, make it UTC
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)

        return v

    class Config:
        # Ensure datetime fields are parsed as timezone-aware
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CreateEventResponse(BaseModel):
    """Response model for creating events."""
    ok: bool
    google_event_id: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    hint: Optional[str] = None


# ==================== User Preferences Models ====================

class UserLocationRequest(BaseModel):
    """Request model for setting user location preference."""
    location_lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    location_lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    location_name: Optional[str] = Field(None, max_length=255, description="Location name (e.g., 'San Francisco, CA')")
    use_browser_location: bool = Field(True, description="Whether to use browser geolocation")


class UserLocationResponse(BaseModel):
    """Response model for user location preference."""
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    location_name: Optional[str] = None
    use_browser_location: bool = True


# ==================== List/Read Operation Models ====================

class ListCalendarEventsRequest(BaseModel):
    """Request model for listing calendar events."""
    from_dt: Optional[datetime] = Field(None, description="Start datetime (defaults to now)")
    to_dt: Optional[datetime] = Field(None, description="End datetime (defaults to now + 7 days)")
    max_results: int = Field(50, ge=1, le=250, description="Maximum number of events to return")

    @field_validator('from_dt', 'to_dt')
    @classmethod
    def ensure_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware after Pydantic parses it."""
        if v is None:
            return v
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class CalendarEvent(BaseModel):
    """Calendar event item."""
    id: str
    summary: Optional[str] = None
    start: datetime
    end: datetime
    location: Optional[str] = None


class ListCalendarEventsResponse(BaseModel):
    """Response model for listing calendar events."""
    events: List[CalendarEvent]


class ListTasksRequest(BaseModel):
    """Request model for listing tasks."""
    status: Optional[str] = Field(None, description="Filter by status: todo, in_progress, done, archived")
    limit: int = Field(50, ge=1, le=250, description="Maximum number of tasks to return")


class TaskItem(BaseModel):
    """Task list item with index and UUID."""
    idx: int = Field(..., description="1-based index for easy reference")
    id: str = Field(..., description="UUID of the task")
    title: str
    status: str
    created_at: datetime


class ListTasksResponse(BaseModel):
    """Response model for listing tasks."""
    items: List[TaskItem]


class ListGroceriesRequest(BaseModel):
    """Request model for listing grocery items."""
    status: Optional[str] = Field(None, description="Filter by status: needed, in_cart, purchased")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of items to return")


class GroceryItem(BaseModel):
    """Grocery list item with index and UUID."""
    idx: int = Field(..., description="1-based index for easy reference")
    id: str = Field(..., description="UUID of the grocery item")
    name: str
    status: str
    created_at: datetime


class ListGroceriesResponse(BaseModel):
    """Response model for listing grocery items."""
    items: List[GroceryItem]


# ==================== Open Banking Models ====================

class BankAccount(BaseModel):
    """Bank account metadata (NO balances stored for compliance)."""
    id: str
    user_id: str
    provider_account_id: str
    provider: str
    account_type: Optional[str] = None
    display_name: Optional[str] = None
    bank_name: Optional[str] = None
    currency: str = "GBP"
    created_at: datetime


class Transaction(BaseModel):
    """Transaction data (fetched in real-time, NEVER stored)."""
    transaction_id: str
    timestamp: datetime
    description: str
    amount: float
    currency: str = "GBP"
    transaction_type: str  # "DEBIT" or "CREDIT"
    transaction_category: Optional[str] = None
    transaction_classification: Optional[List[str]] = None
    merchant_name: Optional[str] = None
    running_balance: Optional[Dict[str, float]] = None

    @field_validator('timestamp')
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware after Pydantic parses it."""
        if v is None:
            return v
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class ListBankAccountsResponse(BaseModel):
    """Response model for listing connected bank accounts."""
    ok: bool
    accounts: List[BankAccount]


class GetTransactionsRequest(BaseModel):
    """Request model for fetching transactions."""
    account_id: str
    from_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    to_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class GetTransactionsResponse(BaseModel):
    """Response model for fetching transactions."""
    ok: bool
    account_id: str
    transactions: List[Transaction]
    count: int


class OpenBankingAuthStatusResponse(BaseModel):
    """Response model for Open Banking authentication status."""
    ok: bool
    authenticated: bool
    provider: Optional[str] = None
    message: Optional[str] = None