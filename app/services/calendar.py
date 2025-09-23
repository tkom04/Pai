"""Calendar service for Google Calendar integration."""
from typing import List, Dict, Any
import uuid
from datetime import datetime

from ..models import CreateEventRequest, CreateEventResponse
from ..deps import google_calendar_client
from ..util.logging import logger


class CalendarService:
    """Service for calendar operations."""

    def __init__(self):
        self.events = []  # TODO: Replace with Google Calendar integration in Phase 3

    async def create_event(self, request: CreateEventRequest) -> CreateEventResponse:
        """Create a calendar event."""
        event_id = str(uuid.uuid4())

        event_data = {
            "id": event_id,
            "title": request.title,
            "start": request.start.isoformat(),
            "end": request.end.isoformat(),
            "description": request.description,
            "created_at": datetime.utcnow().isoformat()
        }

        self.events.append(event_data)

        logger.info(f"Created event: {request.title} ({request.start} - {request.end})")

        return CreateEventResponse(
            ok=True,
            google_event_id=event_id  # TODO: Replace with real Google Calendar event ID in Phase 3
        )

    async def get_events(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get events for date range."""
        if not start_date and not end_date:
            return self.events

        filtered_events = []
        for event in self.events:
            event_start = datetime.fromisoformat(event["start"])
            if start_date and event_start < start_date:
                continue
            if end_date and event_start > end_date:
                continue
            filtered_events.append(event)

        return filtered_events


# Global service instance
calendar_service = CalendarService()
