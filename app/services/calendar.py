"""Calendar service for Google Calendar integration with OAuth."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, date, time as dt_time, timedelta
from googleapiclient.errors import HttpError

from ..models import CreateEventRequest, CreateEventResponse
from ..auth.google_oauth import oauth_manager
from ..util.logging import logger
from ..util.time import make_aware, to_aware_utc, utc_now


class CalendarService:
    """Service for Google Calendar operations with OAuth authentication."""

    def __init__(self):
        self.calendar_id = "primary"  # Use primary calendar by default
        self._service = None
        self.user_id = "default-user"  # Use default-user for dev mode

    async def _get_service(self):
        """Get or create authenticated Google Calendar service."""
        try:
            # Check authentication status
            is_auth = await oauth_manager.is_authenticated(self.user_id)
            logger.info(f"Authentication status for {self.user_id}: {is_auth}")

            if not is_auth:
                raise ValueError("Not authenticated with Google Calendar. Please complete OAuth flow.")

            # Get the calendar service
            service = await oauth_manager.get_calendar_service(self.user_id)
            logger.info("Successfully obtained calendar service")
            return service
        except Exception as e:
            logger.error(f"Failed to get calendar service: {e}")
            raise ValueError(f"Failed to access Google Calendar: {str(e)}")

    async def create_event(self, request: CreateEventRequest) -> CreateEventResponse:
        """Create a calendar event in Google Calendar."""
        try:
            logger.info(f"Creating event: {request.title}")

            service = await self._get_service()
            logger.info("Got service successfully")

            # CRITICAL FIX: Use to_aware_utc to ensure all datetimes are timezone-aware UTC
            start_dt = to_aware_utc(request.start)
            end_dt = to_aware_utc(request.end)
            now_utc = utc_now()

            logger.info(f"Converted datetimes: start={start_dt} (tz={start_dt.tzinfo}), end={end_dt} (tz={end_dt.tzinfo}), now={now_utc} (tz={now_utc.tzinfo})")

            # Validate: end must be after start
            if end_dt <= start_dt:
                raise ValueError("Event end time must be after start time")

            event_body = {
                'summary': request.title,
                'description': request.description or '',
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'UTC',
                }
            }
            logger.info(f"Event body created: {event_body}")

            logger.info("About to call Google Calendar API...")
            try:
                event = service.events().insert(
                    calendarId=self.calendar_id,
                    body=event_body
                ).execute()
                logger.info("Google Calendar API call completed successfully")
            except TypeError as e:
                import traceback, sys
                logger.error(f"TypeError in Google Calendar API call: {e}")
                logger.error("Full traceback:")
                traceback.print_exc(file=sys.stderr)
                # Log all datetime objects and their timezone info
                logger.error(f"event_body start datetime: {event_body['start']['dateTime']} (type: {type(event_body['start']['dateTime'])})")
                logger.error(f"event_body end datetime: {event_body['end']['dateTime']} (type: {type(event_body['end']['dateTime'])})")
                logger.error(f"start_dt: {start_dt} (tz: {start_dt.tzinfo})")
                logger.error(f"end_dt: {end_dt} (tz: {end_dt.tzinfo})")
                raise ValueError(f"Timezone comparison error in Google API: {str(e)}")
            except Exception as e:
                logger.error(f"Other error in Google Calendar API call: {e}")
                raise

            logger.info(f"Created Google Calendar event: {request.title} ({start_dt} - {end_dt})")

            return CreateEventResponse(
                ok=True,
                google_event_id=event['id']
            )

        except ValueError as e:
            # Authentication error or validation error
            logger.error(f"Calendar error: {e}")
            raise
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise ValueError(f"Failed to create calendar event: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating calendar event: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")

    async def list_events(
        self,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """List calendar events for AI tool consumption with default 7-day window."""
        try:
            service = await self._get_service()

            # Default time window: now to now + 7 days
            now = utc_now()
            start = to_aware_utc(from_dt) if from_dt else now
            end = to_aware_utc(to_dt) if to_dt else (now + timedelta(days=7))

            logger.info(f"Listing calendar events from {start} to {end}")

            # Query Google Calendar API
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy='startTime',
                maxResults=max_results
            ).execute()

            items = []
            for ev in events_result.get('items', []):
                # Handle all-day (date) vs timed (dateTime) events
                raw_start = ev.get('start', {})
                raw_end = ev.get('end', {})

                # For all-day events, Google returns just 'date' field
                if 'dateTime' in raw_start:
                    start_str = raw_start['dateTime']
                else:
                    # All-day event: append time to make it a datetime
                    start_str = raw_start.get('date', '') + 'T00:00:00+00:00'

                if 'dateTime' in raw_end:
                    end_str = raw_end['dateTime']
                else:
                    # All-day event: append time to make it a datetime
                    end_str = raw_end.get('date', '') + 'T23:59:59+00:00'

                # Parse and ensure timezone-aware
                start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))

                items.append({
                    'id': ev.get('id'),
                    'summary': ev.get('summary'),
                    'start': start_dt,
                    'end': end_dt,
                    'location': ev.get('location'),
                })

            logger.info(f"Retrieved {len(items)} calendar events")
            return items

        except ValueError as e:
            # Authentication error
            logger.error(f"Calendar authentication error: {e}")
            raise
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise ValueError(f"Failed to list calendar events: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error listing calendar events: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")

    async def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Get events from Google Calendar for date range."""
        try:
            service = await self._get_service()

            # Build query parameters
            query_params = {
                'calendarId': self.calendar_id,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }

            if start_date:
                # CRITICAL FIX: Use to_aware_utc to ensure timezone-aware datetime
                start_date = to_aware_utc(start_date)
                query_params['timeMin'] = start_date.isoformat()
            if end_date:
                # CRITICAL FIX: Use to_aware_utc to ensure timezone-aware datetime
                end_date = to_aware_utc(end_date)
                query_params['timeMax'] = end_date.isoformat()

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
            service = await self._get_service()

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
                # CRITICAL FIX: Use to_aware_utc to ensure timezone-aware datetime
                start_dt = to_aware_utc(updates['start']) if isinstance(updates['start'], (datetime, str)) else updates['start']
                event['start'] = {
                    'dateTime': start_dt.isoformat() if isinstance(start_dt, datetime) else start_dt,
                    'timeZone': 'UTC'
                }
            if 'end' in updates:
                # CRITICAL FIX: Use to_aware_utc to ensure timezone-aware datetime
                end_dt = to_aware_utc(updates['end']) if isinstance(updates['end'], (datetime, str)) else updates['end']
                event['end'] = {
                    'dateTime': end_dt.isoformat() if isinstance(end_dt, datetime) else end_dt,
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
            service = await self._get_service()

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
