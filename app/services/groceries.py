"""Groceries service for managing shopping lists with Supabase."""
from typing import List, Dict, Any
import uuid
from datetime import datetime

from ..models import AddToGroceriesRequest, AddToGroceriesResponse
from ..deps import get_supabase_client
from ..util.logging import logger


class GroceriesService:
    """Service for groceries management using Supabase."""

    async def add_item(self, request: AddToGroceriesRequest, user_id: str) -> AddToGroceriesResponse:
        """Add item to groceries list for specific user."""
        try:
            supabase = get_supabase_client()

            # Insert grocery item into Supabase
            result = supabase.table('groceries').insert({
                'user_id': user_id if user_id != 'default-user' else None,
                'item': request.item,
                'quantity': request.qty or 1,
                'category': request.notes or 'General',  # Using notes as category
                'purchased': False
            }).execute()

            if result.data and len(result.data) > 0:
                grocery = result.data[0]
                logger.info(f"Grocery item created in Supabase: {grocery['id']} for user {user_id}")

                return AddToGroceriesResponse(
                    ok=True,
                    id=grocery['id'],
                    item={
                        "id": grocery['id'],
                        "name": grocery['item'],
                        "qty": grocery['quantity'],
                        "category": grocery['category'],
                        "purchased": grocery['purchased'],
                        "added_at": grocery['created_at']
                    }
                )
            else:
                raise Exception("No data returned from Supabase")

        except Exception as e:
            logger.error(f"Grocery item creation failed: {e}")
            # Return error response instead of falling back
            return AddToGroceriesResponse(
                ok=False,
                id="",
                item={"error": str(e)}
            )

    async def list_items(self, user_id: str, status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List grocery items with idx+id pattern for AI tool consumption."""
        try:
            supabase = get_supabase_client()

            # Handle default-user by querying NULL user_id
            if user_id == 'default-user':
                query = supabase.table('groceries').select('*').is_('user_id', 'null')
            else:
                query = supabase.table('groceries').select('*').eq('user_id', user_id)

            # Map status enum to purchased boolean for DB query
            if status:
                if status == 'purchased':
                    query = query.eq('purchased', True)
                elif status in ['needed', 'in_cart']:
                    query = query.eq('purchased', False)

            result = query.order('created_at', desc=False).limit(limit).execute()

            if result.data:
                # Return with idx (1-based) + id (UUID)
                items = []
                for i, item in enumerate(result.data):
                    # Map purchased boolean back to status string
                    item_status = 'purchased' if item['purchased'] else 'needed'

                    items.append({
                        "idx": i + 1,
                        "id": item['id'],
                        "name": item['item'],
                        "status": item_status,
                        "created_at": item['created_at']
                    })
                return items

            return []

        except Exception as e:
            logger.error(f"Failed to list grocery items: {e}")
            return []

    async def get_items(self, user_id: str, purchased: bool = None) -> List[Dict[str, Any]]:
        """Get grocery items for specific user."""
        try:
            supabase = get_supabase_client()

            # Handle default-user by querying NULL user_id
            if user_id == 'default-user':
                query = supabase.table('groceries').select('*').is_('user_id', 'null')
            else:
                query = supabase.table('groceries').select('*').eq('user_id', user_id)

            # Filter by purchased status if specified
            if purchased is not None:
                query = query.eq('purchased', purchased)

            result = query.order('created_at', desc=True).execute()

            if result.data:
                return [{
                    "id": item['id'],
                    "name": item['item'],
                    "qty": item['quantity'],
                    "category": item['category'],
                    "purchased": item['purchased'],
                    "added_at": item['created_at']
                } for item in result.data]

            return []

        except Exception as e:
            logger.error(f"Failed to get grocery items: {e}")
            return []

    async def update_item_status(self, item_id: str, user_id: str, purchased: bool) -> bool:
        """Update item purchased status."""
        try:
            supabase = get_supabase_client()

            # Handle default-user by querying NULL user_id
            if user_id == 'default-user':
                result = supabase.table('groceries')\
                    .update({'purchased': purchased})\
                    .eq('id', item_id)\
                    .is_('user_id', 'null')\
                    .execute()
            else:
                result = supabase.table('groceries')\
                    .update({'purchased': purchased})\
                    .eq('id', item_id)\
                    .eq('user_id', user_id)\
                    .execute()

            if result.data:
                logger.info(f"Updated grocery item {item_id} purchased status to {purchased}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update grocery item: {e}")
            return False

    async def delete_item(self, item_id: str, user_id: str) -> bool:
        """Delete a grocery item."""
        try:
            supabase = get_supabase_client()

            # Handle default-user by querying NULL user_id
            if user_id == 'default-user':
                result = supabase.table('groceries')\
                    .delete()\
                    .eq('id', item_id)\
                    .is_('user_id', 'null')\
                    .execute()
            else:
                result = supabase.table('groceries')\
                    .delete()\
                    .eq('id', item_id)\
                    .eq('user_id', user_id)\
                    .execute()

            logger.info(f"Deleted grocery item {item_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete grocery item: {e}")
            return False


# Global service instance
groceries_service = GroceriesService()