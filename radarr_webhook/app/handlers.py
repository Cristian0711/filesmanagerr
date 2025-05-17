"""
Webhook handlers for Radarr and Sonarr
"""
import json
from typing import Dict, Any, Union, Tuple

from app.core.config import Config, logger
from app.radarr.models import RadarrEvent
from app.sonarr.models import SonarrEvent
from app.radarr.monitor import RadarrDownloadMonitor
from app.sonarr.monitor import SonarrDownloadMonitor
from app.core.storage import WebhookStorage


class WebhookHandler:
    """Main webhook handler that delegates to appropriate service handler"""
    
    @staticmethod
    def process_webhook(data: Dict[str, Any], service_type: str = None) -> Tuple[Dict[str, Any], int]:
        """
        Process an incoming webhook and route to correct handler
        
        Args:
            data: The webhook payload data
            service_type: Optional service type override ('radarr' or 'sonarr')
            
        Returns:
            Tuple of (response_data, status_code)
        """
        # Save webhook data for debugging
        WebhookStorage.save_latest_webhook(data)
        WebhookStorage.append_to_history(data)
        
        # Determine service type if not provided
        if not service_type:
            service_type = WebhookHandler._detect_service_type(data)
            
        # Log the webhook event
        event_type = data.get('eventType', 'Unknown')
        logger.info(f"Received {service_type} webhook: {event_type}")
        
        # Process based on service type
        if service_type == 'radarr' and Config.RADARR_ENABLED:
            return WebhookHandler._handle_radarr(data)
        elif service_type == 'sonarr' and Config.SONARR_ENABLED:
            return WebhookHandler._handle_sonarr(data)
        else:
            logger.warning(f"Service type '{service_type}' not enabled or unsupported")
            return {"error": f"Service type '{service_type}' not enabled or unsupported"}, 400
    
    @staticmethod
    def _detect_service_type(data: Dict[str, Any]) -> str:
        """
        Detect which service (Radarr or Sonarr) sent the webhook
        
        Args:
            data: The webhook payload data
            
        Returns:
            'radarr' or 'sonarr' based on webhook content
        """
        # Look for specific keys that are unique to each service
        if 'movie' in data:
            return 'radarr'
        elif 'series' in data or 'episodes' in data:
            return 'sonarr'
        
        # If we can't determine, default to radarr
        logger.warning("Couldn't determine service type from webhook data")
        return 'radarr'
    
    @staticmethod
    def _handle_radarr(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Handle Radarr webhook
        
        Args:
            data: The webhook payload data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Create event object from data
            event = RadarrEvent(data)
            
            # Log event details
            logger.info(f"Processing Radarr {event.event_type} event for {event.get_media_title()}")
            
            # Process based on event type
            if not Config.DOWNLOAD_MONITOR_ENABLED:
                return {"message": "Download monitoring disabled, event logged only"}, 200
                
            # Send to download monitor
            handled = RadarrDownloadMonitor.handle_event(data)
            
            if handled:
                return {"message": f"Successfully processed {event.event_type} event"}, 200
            else:
                return {"message": f"Event {event.event_type} did not require monitoring"}, 200
                
        except Exception as e:
            logger.exception(f"Error processing Radarr webhook: {e}")
            return {"error": f"Error processing webhook: {str(e)}"}, 500
    
    @staticmethod
    def _handle_sonarr(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Handle Sonarr webhook
        
        Args:
            data: The webhook payload data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Create event object from data
            event = SonarrEvent(data)
            
            # Log event details
            logger.info(f"Processing Sonarr {event.event_type} event for {event.get_media_title()}")
            
            # Process based on event type
            if not Config.DOWNLOAD_MONITOR_ENABLED:
                return {"message": "Download monitoring disabled, event logged only"}, 200
                
            # Send to download monitor
            handled = SonarrDownloadMonitor.handle_event(data)
            
            if handled:
                return {"message": f"Successfully processed {event.event_type} event"}, 200
            else:
                return {"message": f"Event {event.event_type} did not require monitoring"}, 200
                
        except Exception as e:
            logger.exception(f"Error processing Sonarr webhook: {e}")
            return {"error": f"Error processing webhook: {str(e)}"}, 500 