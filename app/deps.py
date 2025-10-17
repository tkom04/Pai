"""Dependencies and client configurations for PAI."""
import os
import jwt
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Header
from pydantic_settings import BaseSettings
from openai import OpenAI
import httpx
from notion_client import Client as NotionClient
from supabase import create_client, Client as SupabaseClient


def get_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Validate API key from request headers."""
    expected_key = os.getenv("APP_API_KEY", "test-key")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured")

    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return x_api_key


class NotionService:
    """Enhanced Notion API service with full CRUD operations."""
    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY")

        # Only initialize client if API key is present
        if self.api_key:
            self.client = NotionClient(auth=self.api_key)
        else:
            self.client = None
            print("WARNING: NOTION_API_KEY not configured. Notion features will not work.")

        self.budgets_db_id = os.getenv("NOTION_DB_BUDGETS")
        self.tasks_db_id = os.getenv("NOTION_DB_TASKS")
        self.groceries_db_id = os.getenv("NOTION_DB_GROCERIES")

        # Cache for database schemas
        self._db_schema_cache: Dict[str, Any] = {}

    async def get_database_schema(self, database_id: str) -> dict:
        """Retrieve and cache database schema."""
        if not self.client:
            raise HTTPException(status_code=503, detail="Notion API not configured. Set NOTION_API_KEY in .env file.")

        if database_id in self._db_schema_cache:
            return self._db_schema_cache[database_id]

        try:
            database = self.client.databases.retrieve(database_id=database_id)
            self._db_schema_cache[database_id] = database
            return database
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve database schema: {str(e)}")

    async def query_database(
        self,
        database_id: str,
        filter_conditions: Optional[dict] = None,
        sorts: Optional[List[dict]] = None,
        page_size: int = 100
    ) -> List[dict]:
        """Query a Notion database with filters and sorting."""
        if not self.client:
            raise HTTPException(status_code=503, detail="Notion API not configured. Set NOTION_API_KEY in .env file.")

        try:
            query_params = {"database_id": database_id, "page_size": page_size}

            if filter_conditions:
                query_params["filter"] = filter_conditions
            if sorts:
                query_params["sorts"] = sorts

            results = []
            response = self.client.databases.query(**query_params)
            results.extend(response.get("results", []))

            # Handle pagination
            while response.get("has_more"):
                query_params["start_cursor"] = response["next_cursor"]
                response = self.client.databases.query(**query_params)
                results.extend(response.get("results", []))

            return results
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to query database: {str(e)}")

    async def create_page(self, database_id: str, properties: dict, content: Optional[List[dict]] = None) -> dict:
        """Create a page in any Notion database with validation."""
        if not self.client:
            raise HTTPException(status_code=503, detail="Notion API not configured. Set NOTION_API_KEY in .env file.")

        try:
            page_data = {
                "parent": {"database_id": database_id},
                "properties": properties
            }

            if content:
                page_data["children"] = content

            response = self.client.pages.create(**page_data)
            return {"id": response["id"], "url": response["url"], "properties": response.get("properties", {})}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create page: {str(e)}")

    async def update_page(self, page_id: str, properties: dict) -> dict:
        """Update a Notion page's properties."""
        if not self.client:
            raise HTTPException(status_code=503, detail="Notion API not configured. Set NOTION_API_KEY in .env file.")

        try:
            response = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            return {"id": response["id"], "url": response["url"], "properties": response.get("properties", {})}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update page: {str(e)}")

    async def get_page(self, page_id: str) -> dict:
        """Retrieve a Notion page by ID."""
        if not self.client:
            raise HTTPException(status_code=503, detail="Notion API not configured. Set NOTION_API_KEY in .env file.")

        try:
            response = self.client.pages.retrieve(page_id=page_id)
            return response
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Page not found: {str(e)}")

    async def delete_page(self, page_id: str) -> dict:
        """Archive (delete) a Notion page."""
        if not self.client:
            raise HTTPException(status_code=503, detail="Notion API not configured. Set NOTION_API_KEY in .env file.")

        try:
            response = self.client.pages.update(
                page_id=page_id,
                archived=True
            )
            return {"id": response["id"], "archived": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to archive page: {str(e)}")

    # Legacy methods for backward compatibility
    async def create_task_page(self, title: str, due: str, context: str = "Home", priority: str = "Med") -> dict:
        """Create a task page in Notion Tasks database."""
        if not self.tasks_db_id:
            return {"id": f"mock-task-{title}", "url": "https://notion.so/mock", "error": "NOTION_DB_TASKS not configured"}

        try:
            properties = {
                "Title": {"title": [{"text": {"content": title}}]},
                "Due": {"date": {"start": due}},
                "Context": {"select": {"name": context}},
                "Priority": {"select": {"name": priority}},
                "Status": {"select": {"name": "Not Started"}}
            }
            return await self.create_page(self.tasks_db_id, properties)
        except Exception as e:
            return {"id": f"mock-task-{title}", "url": "https://notion.so/mock", "error": str(e)}

    async def create_grocery_page(self, item: str, qty: int = 1, notes: str = None) -> dict:
        """Create a grocery item page in Notion Groceries database."""
        if not self.groceries_db_id:
            return {"id": f"mock-grocery-{item}", "url": "https://notion.so/mock", "error": "NOTION_DB_GROCERIES not configured"}

        try:
            properties = {
                "Item": {"title": [{"text": {"content": item}}]},
                "Qty": {"number": qty},
                "Notes": {"rich_text": [{"text": {"content": notes or ""}}]},
                "Status": {"select": {"name": "Needed"}}
            }
            return await self.create_page(self.groceries_db_id, properties)
        except Exception as e:
            return {"id": f"mock-grocery-{item}", "url": "https://notion.so/mock", "error": str(e)}

    async def create_budget_page(self, category: str, cap: float, spent: float, month: str) -> dict:
        """Create a budget entry page in Notion Budgets database."""
        if not self.budgets_db_id:
            return {"id": f"mock-budget-{category}", "url": "https://notion.so/mock", "error": "NOTION_DB_BUDGETS not configured"}

        try:
            delta = cap - spent
            status = "WARN" if spent / cap > 0.8 else "OK"

            properties = {
                "Category": {"select": {"name": category}},
                "Cap": {"number": cap},
                "Spent": {"number": spent},
                "Delta": {"number": delta},
                "Status": {"select": {"name": status}},
                "Month": {"date": {"start": month}}
            }
            return await self.create_page(self.budgets_db_id, properties)
        except Exception as e:
            return {"id": f"mock-budget-{category}", "url": "https://notion.so/mock", "error": str(e)}


class GoogleCalendarClient:
    """Google Calendar API client (placeholder for Phase 3)."""
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_JSON_PATH")
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID")

    async def create_event(self, event_data: dict) -> dict:
        """Create an event in Google Calendar."""
        # TODO: Implement in Phase 3
        return {"id": "placeholder", "event": event_data}


# Import Open Banking services
from .services.open_banking import open_banking_service
from .auth.open_banking import open_banking_oauth_manager

# Global client instances
notion_service = NotionService()
google_calendar_client = GoogleCalendarClient()


class Settings(BaseSettings):
    """Application settings (loaded from env)."""
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # Valid as of Oct 2025
    OPENAI_REQUEST_TIMEOUT_S: int = 60
    AI_STREAMING_ENABLED: bool = True


settings = Settings()  # loaded once


def get_openai_client() -> OpenAI:
    """Provide configured OpenAI client."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    return OpenAI(api_key=api_key)


# ==================== Supabase Authentication ====================

def get_supabase_client() -> SupabaseClient:
    """Get Supabase client for database operations."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    return create_client(supabase_url, supabase_key)


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user_id from Supabase JWT token.
    Expects Authorization header: "Bearer <token>"
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "")

    try:
        # Get Supabase JWT secret
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not jwt_secret:
            # Fallback: verify with Supabase client
            supabase = get_supabase_client()
            user = supabase.auth.get_user(token)
            if user and user.user:
                return user.user.id
            raise HTTPException(status_code=401, detail="Invalid token")

        # Decode JWT token
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
