"""Tasks service for managing to-do items with Supabase."""
from typing import List, Dict, Any
import uuid
from datetime import datetime

from ..models import CreateTaskRequest, CreateTaskResponse
from ..deps import get_supabase_client
from ..util.logging import logger
from ..util.time import utc_now


class TasksService:
    """Service for task management using Supabase."""

    async def create_task(self, request: CreateTaskRequest, user_id: str) -> CreateTaskResponse:
        """Create a new task for specific user."""
        try:
            supabase = get_supabase_client()

            # Map priority values to match database schema
            priority_map = {'Low': 'low', 'Med': 'medium', 'High': 'high'}
            db_priority = priority_map.get(request.priority, 'medium')

            # Insert task into Supabase
            result = supabase.table('tasks').insert({
                'user_id': user_id if user_id != 'default-user' else None,
                'title': request.title,
                'description': request.context or '',
                'status': 'todo',
                'priority': db_priority,
                'due_date': request.due.isoformat() if request.due else None
            }).execute()

            if result.data and len(result.data) > 0:
                task = result.data[0]
                logger.info(f"Task created in Supabase: {task['id']} for user {user_id}")

                return CreateTaskResponse(
                    ok=True,
                    notion_page_id=task['id']  # Keep field name for compatibility
                )
            else:
                raise Exception("No data returned from Supabase")

        except Exception as e:
            logger.error(f"Task creation failed: {e}")
            return CreateTaskResponse(
                ok=False,
                notion_page_id=""
            )

    async def list_tasks(self, user_id: str, status: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List tasks with idx+id pattern for AI tool consumption."""
        try:
            supabase = get_supabase_client()

            # Handle default-user by querying NULL user_id
            if user_id == 'default-user':
                query = supabase.table('tasks').select('*').is_('user_id', 'null')
            else:
                query = supabase.table('tasks').select('*').eq('user_id', user_id)

            # Filter by status if specified (DB uses: todo, in_progress, done, archived)
            if status:
                query = query.eq('status', status)

            result = query.order('created_at', desc=False).limit(limit).execute()

            if result.data:
                # Return with idx (1-based) + id (UUID)
                return [{
                    "idx": i + 1,
                    "id": task['id'],
                    "title": task['title'],
                    "status": task['status'],
                    "created_at": task['created_at']
                } for i, task in enumerate(result.data)]

            return []

        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []

    async def get_tasks(self, user_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get tasks for specific user."""
        try:
            supabase = get_supabase_client()

            # Handle default-user by querying NULL user_id
            if user_id == 'default-user':
                query = supabase.table('tasks').select('*').is_('user_id', 'null')
            else:
                query = supabase.table('tasks').select('*').eq('user_id', user_id)

            # Filter by status if specified
            if status:
                query = query.eq('status', status)

            result = query.order('created_at', desc=True).execute()

            if result.data:
                return [{
                    "id": task['id'],
                    "title": task['title'],
                    "description": task['description'],
                    "status": task['status'],
                    "priority": task['priority'],
                    "due_date": task['due_date'],
                    "created_at": task['created_at'],
                    "updated_at": task['updated_at']
                } for task in result.data]

            return []

        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []

    async def update_task_status(self, task_id: str, user_id: str, status: str) -> bool:
        """Update task status (todo/in_progress/done/archived)."""
        try:
            supabase = get_supabase_client()

            # Validate status
            valid_statuses = ['todo', 'in_progress', 'done', 'archived']
            if status not in valid_statuses:
                logger.warning(f"Invalid status: {status}. Using 'todo'")
                status = 'todo'

            # Handle default-user by querying NULL user_id
            if user_id == 'default-user':
                result = supabase.table('tasks')\
                    .update({
                        'status': status,
                        'updated_at': utc_now().isoformat()
                    })\
                    .eq('id', task_id)\
                    .is_('user_id', 'null')\
                    .execute()
            else:
                result = supabase.table('tasks')\
                    .update({
                        'status': status,
                        'updated_at': utc_now().isoformat()
                    })\
                    .eq('id', task_id)\
                    .eq('user_id', user_id)\
                    .execute()

            if result.data:
                logger.info(f"Updated task {task_id} status to {status}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            return False

    async def update_task(self, task_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update task fields."""
        try:
            supabase = get_supabase_client()

            # Add updated_at timestamp
            updates['updated_at'] = utc_now().isoformat()

            result = supabase.table('tasks')\
                .update(updates)\
                .eq('id', task_id)\
                .eq('user_id', user_id)\
                .execute()

            if result.data:
                logger.info(f"Updated task {task_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            return False

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task."""
        try:
            supabase = get_supabase_client()

            result = supabase.table('tasks')\
                .delete()\
                .eq('id', task_id)\
                .eq('user_id', user_id)\
                .execute()

            logger.info(f"Deleted task {task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete task: {e}")
            return False


# Global service instance
tasks_service = TasksService()