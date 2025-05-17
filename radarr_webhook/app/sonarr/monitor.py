"""
Sonarr-specific implementation for monitoring TV series downloads.
"""
from typing import Dict, Any

from app.core.config import logger
from app.core.monitor import DownloadMonitor
from app.sonarr.models import SonarrEvent


class SonarrDownloadMonitor(DownloadMonitor):
    """
    Sonarr-specific download monitor for handling TV series events
    """
    
    @staticmethod
    def handle_event(event_data: Dict[str, Any]) -> bool:
        """
        Handle a webhook event from Sonarr
        
        Args:
            event_data: Raw event data from Sonarr webhook
            
        Returns:
            True if the event was handled successfully, False otherwise
        """
        # Create SonarrEvent from raw data
        event = SonarrEvent(event_data)
        logger.info(f"Processing Sonarr {event.event_type} event for {event.get_media_title()}")
        
        # Handle based on event type
        if event.event_type == "Grab":
            return DownloadMonitor.handle_grab_event(event)
        elif event.event_type == "Download":
            return DownloadMonitor.handle_download_event(event)
        elif event.event_type in ["SeriesDelete", "EpisodeFileDelete"]:
            return DownloadMonitor.handle_delete_event(event)
        else:
            logger.info(f"No monitoring needed for event type: {event.event_type}")
            return False 