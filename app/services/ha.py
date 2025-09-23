"""Home Assistant service for automation control."""
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models import HAServiceCallRequest, HAServiceCallResponse
from ..deps import ha_client
from ..util.logging import logger


class HomeAssistantService:
    """Service for Home Assistant operations."""

    def __init__(self):
        self.last_calls = []  # TODO: Replace with real HA integration in Phase 3

    async def call_service(self, request: HAServiceCallRequest) -> HAServiceCallResponse:
        """Call a Home Assistant service."""
        service_call = f"{request.domain}.{request.service}"

        call_data = {
            "domain": request.domain,
            "service": request.service,
            "entity_id": request.entity_id,
            "data": request.data,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.last_calls.append(call_data)

        logger.info(f"HA service call: {service_call} on {request.entity_id}")

        return HAServiceCallResponse(
            ok=True,
            called=service_call,
            entity_id=request.entity_id
        )

    async def get_entities(self, domain: str = None) -> List[Dict[str, Any]]:
        """Get available HA entities."""
        # TODO: Implement real HA entity listing in Phase 3
        sample_entities = [
            {"entity_id": "light.kitchen", "name": "Kitchen Light", "domain": "light"},
            {"entity_id": "light.living_room", "name": "Living Room Light", "domain": "light"},
            {"entity_id": "switch.coffee_maker", "name": "Coffee Maker", "domain": "switch"},
        ]

        if domain:
            return [e for e in sample_entities if e["domain"] == domain]
        return sample_entities


# Global service instance
ha_service = HomeAssistantService()
