"""Tasks service for managing to-do items."""
from typing import List, Dict, Any
import uuid
from datetime import datetime

from ..models import CreateTaskRequest, CreateTaskResponse
from ..deps import notion_service
from ..util.logging import logger


class TasksService:
    """Service for task management."""

    def __init__(self):
        self.tasks = []  # Local cache for fallback

    async def create_task(self, request: CreateTaskRequest) -> CreateTaskResponse:
        """Create a new task."""
        try:
            # Try to create in Notion first
            notion_result = await notion_service.create_task_page(
                title=request.title,
                due=request.due.isoformat(),
                context=request.context,
                priority=request.priority
            )

            if "error" in notion_result:
                logger.warning(f"Notion task creation failed: {notion_result['error']}")
                # Fallback to local storage
                task_id = str(uuid.uuid4())
                task_data = {
                    "id": task_id,
                    "title": request.title,
                    "due": request.due.isoformat(),
                    "context": request.context,
                    "priority": request.priority,
                    "status": "Not Started",
                    "created_at": datetime.utcnow().isoformat(),
                    "notion_error": notion_result["error"]
                }
                self.tasks.append(task_data)

                return CreateTaskResponse(
                    ok=True,
                    notion_page_id=task_id
                )
            else:
                logger.info(f"Task created in Notion: {notion_result['id']}")
                return CreateTaskResponse(
                    ok=True,
                    notion_page_id=notion_result["id"]
                )

        except Exception as e:
            logger.error(f"Task creation failed: {e}")
            # Fallback to local storage
            task_id = str(uuid.uuid4())
            task_data = {
                "id": task_id,
                "title": request.title,
                "due": request.due.isoformat(),
                "context": request.context,
                "priority": request.priority,
                "status": "Not Started",
                "created_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            self.tasks.append(task_data)

            return CreateTaskResponse(
                ok=True,
                notion_page_id=task_id
            )

    async def get_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks."""
        return self.tasks

    async def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = status
                logger.info(f"Updated task {task_id} status to {status}")
                return True
        return False


# Global service instance
tasks_service = TasksService()
