"""
Handlers for processing webhook events from Radarr.
"""
from typing import Dict, Any, Optional, Tuple

from app.config import logger
from app.models import RadarrEvent
from app.monitor import handle_grab_event, handle_download_event


def process_event(data: Dict[str, Any]) -> Tuple[str, bool]:
    """
    Process a webhook event from Radarr
    
    Args:
        data: The webhook payload as a dictionary
        
    Returns:
        A tuple containing (message, success_status)
    """
    # Create a RadarrEvent object from the data
    event = RadarrEvent(data)
    
    # Process based on event type
    event_type = event.event_type
    
    if event_type == 'Test':
        return handle_test_event(event)
        
    elif event_type == 'Grab':
        return handle_grab_webhook(event)
        
    elif event_type == 'Download':
        return handle_download_webhook(event)
        
    elif event_type == 'Rename':
        return handle_rename_webhook(event)
        
    else:
        logger.warning(f"Unknown event type: {event_type}")
        return f"Unknown event: {event_type}", False


def handle_test_event(event: RadarrEvent) -> Tuple[str, bool]:
    """Handle a test event from Radarr"""
    logger.info("Test webhook received from Radarr")
    return "Test webhook received successfully!", True


def handle_grab_webhook(event: RadarrEvent) -> Tuple[str, bool]:
    """Handle a Grab event from Radarr"""
    # Process the event using the monitor module
    success = handle_grab_event(event)
    
    # Get movie information for the response
    movie_title = event.remote_movie.title if event.remote_movie else "Unknown"
    quality = event.release.quality if event.release else "Unknown"
    
    if success:
        message = f"Movie '{movie_title}' scheduled for download (Quality: {quality}). Monitoring for hardlinking."
        logger.info(message)
    else:
        message = f"Movie '{movie_title}' scheduled for download, but monitoring could not be started."
        logger.warning(message)
    
    return message, success


def handle_download_webhook(event: RadarrEvent) -> Tuple[str, bool]:
    """Handle a Download event from Radarr"""
    # Stop monitoring if it was active
    handle_download_event(event)
    
    # Get movie information
    movie_title = event.movie.title if event.movie else "Unknown"
    quality = "Unknown"
    if event.movie and event.movie.quality:
        quality = event.movie.quality
    
    is_upgrade = "upgrade" if event.is_upgrade else "new download"
    
    message = f"Movie '{movie_title}' downloaded ({is_upgrade}), quality: {quality}"
    logger.info(message)
    
    return message, True


def handle_rename_webhook(event: RadarrEvent) -> Tuple[str, bool]:
    """Handle a Rename event from Radarr"""
    movie_title = event.movie.title if event.movie else "Unknown"
    message = f"Movie '{movie_title}' renamed"
    logger.info(message)
    
    return message, True 