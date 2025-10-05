"""Calendar service for Google Calendar integration with OAuth."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from googleapiclient.errors import HttpError

from ..models import CreateEventRequest, CreateEventResponse
from ..auth.google_oauth import oauth_manager
from ..util.logging import logger


class CalendarService:
    """Service for Google Calendar operations with OAuth authentication."""

    def __init__(self):
        self.calendar_id = "primary"  # Use primary calendar by default
        self._service = None

    def _get_service(self):
        """Get or create authenticated Google Calendar service."""
        if not oauth_manager.is_authenticated():
            raise ValueError("Not authenticated with Google Calendar. Please complete OAuth flow.")

        try:
            return oauth_manager.get_calendar_service()
        except Exception as e:
            logger.error(f"Failed to get calendar service: {e}")
            raise ValueError(f"Failed to access Google Calendar: {str(e)}")

    async def create_event(self, request: CreateEventRequest) -> CreateEventResponse:
        """Create a calendar event in Google Calendar."""
        try:
            service = self._get_service()

            # Convert datetime to RFC3339 format with timezone
            event_body = {
                'summary': request.title,
                'description': request.description or '',
                'start': {
                    'dateTime': request.start.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': request.end.isoformat(),
                    'timeZone': 'UTC',
                }
            }

            event = service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()

            logger.info(f"Created Google Calendar event: {request.title} ({request.start} - {request.end})")

            return CreateEventResponse(
                ok=True,
                google_event_id=event['id']
            )

        except ValueError as e:
            # Authentication error
            logger.error(f"Calendar authentication error: {e}")
            raise
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise ValueError(f"Failed to create calendar event: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating calendar event: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")

    async def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Get events from Google Calendar for date range."""
        try:
            service = self._get_service()

            # Build query parameters
            query_params = {
                'calendarId': self.calendar_id,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }

            if start_date:
                query_params['timeMin'] = start_date.isoformat() + 'Z'
            if end_date:
                query_params['timeMax'] = end_date.isoformat() + 'Z'

            events_result = service.events().list(**query_params).execute()
            events = events_result.get('items', [])

            # Transform to simpler format
            formatted_events = []
            for event in events:
                formatted_event = {
                    'id': event['id'],
                    'title': event.get('summary', 'No title'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'description': event.get('description', ''),
                    'created_at': event.get('created'),
                    'html_link': event.get('htmlLink')
                }
                formatted_events.append(formatted_event)

            logger.info(f"Retrieved {len(formatted_events)} events from Google Calendar")
            return formatted_events

        except ValueError as e:
            # Authentication error
            logger.error(f"Calendar authentication error: {e}")
            raise
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise ValueError(f"Failed to retrieve calendar events: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving calendar events: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")

    async def update_event(self, event_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Google Calendar event."""
        try:
            service = self._get_service()

            # Get existing event
            event = service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()

            # Apply updates
            if 'title' in updates:
                event['summary'] = updates['title']
            if 'description' in updates:
                event['description'] = updates['description']
            if 'start' in updates:
                event['start'] = {
                    'dateTime': updates['start'].isoformat() if isinstance(updates['start'], datetime) else updates['start'],
                    'timeZone': 'UTC'
                }
            if 'end' in updates:
                event['end'] = {
                    'dateTime': updates['end'].isoformat() if isinstance(updates['end'], datetime) else updates['end'],
                    'timeZone': 'UTC'
                }

            # Update the event
            updated_event = service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            logger.info(f"Updated Google Calendar event: {event_id}")
            return {'id': updated_event['id'], 'updated': True}

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise ValueError(f"Failed to update calendar event: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error updating calendar event: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")

    async def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a Google Calendar event."""
        try:
            service = self._get_service()

            service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()

            logger.info(f"Deleted Google Calendar event: {event_id}")
            return {'id': event_id, 'deleted': True}

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise ValueError(f"Failed to delete calendar event: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error deleting calendar event: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")


# Global service instance
calendar_service = CalendarService()
