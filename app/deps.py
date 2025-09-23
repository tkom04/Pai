"""Dependencies and client configurations for PAI."""
import os
from typing import Optional
from fastapi import HTTPException, Header
import httpx
from notion_client import Client as NotionClient


def get_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Validate API key from request headers."""
    expected_key = os.getenv("APP_API_KEY", "test-key")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured")

    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return x_api_key


class NotionService:
    """Notion API service."""
    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY")
        self.client = NotionClient(auth=self.api_key)
        self.budgets_db_id = os.getenv("NOTION_DB_BUDGETS", "276d1d46-0bbb-81a5-8b20-ca7f1aed6c0f")  # All Expenses
        self.tasks_db_id = os.getenv("NOTION_DB_TASKS", "276d1d46-0bbb-800b-a1c1-d7a0aba4426f")  # Habit Tracker (repurpose)
        self.groceries_db_id = os.getenv("NOTION_DB_GROCERIES", "276d1d46-0bbb-800b-a1c1-d7a0aba4426f")  # Habit Tracker (repurpose)

    async def create_task_page(self, title: str, due: str, context: str = "Home", priority: str = "Med") -> dict:
        """Create a task page in Notion Tasks database."""
        try:
            properties = {
                "Title": {"title": [{"text": {"content": title}}]},
                "Due": {"date": {"start": due}},
                "Context": {"select": {"name": context}},
                "Priority": {"select": {"name": priority}},
                "Status": {"select": {"name": "Not Started"}}
            }

            response = self.client.pages.create(
                parent={"database_id": self.tasks_db_id},
                properties=properties
            )
            return {"id": response["id"], "url": response["url"]}
        except Exception as e:
            # Fallback to mock response if Notion fails
            return {"id": f"mock-task-{title}", "url": "https://notion.so/mock", "error": str(e)}

    async def create_grocery_page(self, item: str, qty: int = 1, notes: str = None) -> dict:
        """Create a grocery item page in Notion Groceries database."""
        try:
            properties = {
                "Item": {"title": [{"text": {"content": item}}]},
                "Qty": {"number": qty},
                "Notes": {"rich_text": [{"text": {"content": notes or ""}}]},
                "Status": {"select": {"name": "Needed"}}
            }

            response = self.client.pages.create(
                parent={"database_id": self.groceries_db_id},
                properties=properties
            )
            return {"id": response["id"], "url": response["url"]}
        except Exception as e:
            # Fallback to mock response if Notion fails
            return {"id": f"mock-grocery-{item}", "url": "https://notion.so/mock", "error": str(e)}

    async def create_budget_page(self, category: str, cap: float, spent: float, month: str) -> dict:
        """Create a budget entry page in Notion Budgets database."""
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

            response = self.client.pages.create(
                parent={"database_id": self.budgets_db_id},
                properties=properties
            )
            return {"id": response["id"], "url": response["url"]}
        except Exception as e:
            # Fallback to mock response if Notion fails
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


class HomeAssistantClient:
    """Home Assistant REST API client (placeholder for Phase 3)."""
    def __init__(self):
        self.base_url = os.getenv("HA_BASE_URL")
        self.token = os.getenv("HA_TOKEN")

    async def call_service(self, domain: str, service: str, entity_id: Optional[str] = None, data: Optional[dict] = None) -> dict:
        """Call a Home Assistant service."""
        # TODO: Implement in Phase 3
        return {"domain": domain, "service": service, "entity_id": entity_id, "data": data}


# Global client instances
notion_service = NotionService()
google_calendar_client = GoogleCalendarClient()
ha_client = HomeAssistantClient()
