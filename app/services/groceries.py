"""Groceries service for managing shopping lists."""
from typing import List, Dict, Any
import uuid
from datetime import datetime

from ..models import AddToGroceriesRequest, AddToGroceriesResponse
from ..deps import notion_service
from ..util.logging import logger


class GroceriesService:
    """Service for groceries management."""

    def __init__(self):
        self.items = []  # Local cache for fallback

    async def add_item(self, request: AddToGroceriesRequest) -> AddToGroceriesResponse:
        """Add item to groceries list."""
        try:
            # Try to create in Notion first
            notion_result = await notion_service.create_grocery_page(
                item=request.item,
                qty=request.qty,
                notes=request.notes
            )

            if "error" in notion_result:
                logger.warning(f"Notion grocery creation failed: {notion_result['error']}")
                # Fallback to local storage
                item_id = str(uuid.uuid4())
                item_data = {
                    "id": item_id,
                    "name": request.item,
                    "qty": request.qty,
                    "notes": request.notes,
                    "status": "Needed",
                    "added_at": datetime.utcnow().isoformat(),
                    "notion_error": notion_result["error"]
                }
                self.items.append(item_data)

                return AddToGroceriesResponse(
                    ok=True,
                    id=item_id,
                    item=item_data
                )
            else:
                logger.info(f"Grocery item created in Notion: {notion_result['id']}")
                item_data = {
                    "id": notion_result["id"],
                    "name": request.item,
                    "qty": request.qty,
                    "notes": request.notes,
                    "status": "Needed",
                    "added_at": datetime.utcnow().isoformat(),
                    "notion_url": notion_result["url"]
                }
                self.items.append(item_data)

                return AddToGroceriesResponse(
                    ok=True,
                    id=notion_result["id"],
                    item=item_data
                )

        except Exception as e:
            logger.error(f"Grocery item creation failed: {e}")
            # Fallback to local storage
            item_id = str(uuid.uuid4())
            item_data = {
                "id": item_id,
                "name": request.item,
                "qty": request.qty,
                "notes": request.notes,
                "status": "Needed",
                "added_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            self.items.append(item_data)

            return AddToGroceriesResponse(
                ok=True,
                id=item_id,
                item=item_data
            )

    async def get_items(self) -> List[Dict[str, Any]]:
        """Get all grocery items."""
        return self.items

    async def update_item_status(self, item_id: str, status: str) -> bool:
        """Update item status (Needed/Added/Ordered)."""
        for item in self.items:
            if item["id"] == item_id:
                item["status"] = status
                logger.info(f"Updated grocery item {item_id} status to {status}")
                return True
        return False


# Global service instance
groceries_service = GroceriesService()
