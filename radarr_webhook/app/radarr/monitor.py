"""
Radarr-specific implementation for monitoring downloads.
"""
from typing import Dict, Any

from app.core.config import logger
from app.core.monitor import DownloadMonitor
from app.radarr.models import RadarrEvent


class RadarrDownloadMonitor(DownloadMonitor):
    """
    Radarr-specific download monitor for handling movie events
    """
    
    @staticmethod
    def handle_event(event_data: Dict[str, Any]) -> bool:
        """
        Handle a webhook event from Radarr
        
        Args:
            event_data: Raw event data from Radarr webhook
            
        Returns:
            True if the event was handled successfully, False otherwise
        """
        # Create RadarrEvent from raw data
        event = RadarrEvent(event_data)
        logger.info(f"Processing Radarr {event.event_type} event for {event.get_media_title()}")
        
        # Handle based on event type
        if event.event_type == "Grab":
            return DownloadMonitor.handle_grab_event(event)
        elif event.event_type == "Download":
            return DownloadMonitor.handle_download_event(event)
        elif event.event_type in ["MovieDelete", "MovieFileDelete"]:
            return DownloadMonitor.handle_delete_event(event)
        else:
            logger.info(f"No monitoring needed for event type: {event.event_type}")
            return False 