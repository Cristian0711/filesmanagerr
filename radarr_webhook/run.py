#!/usr/bin/env python3
"""
Entry point for the Radarr Webhook Receiver application.
This script starts the Flask web server that handles Radarr webhook notifications.
"""

from app.main import run_app
from app.config import logger

if __name__ == "__main__":
    try:
        # Start the Flask application
        logger.info("Starting Radarr Webhook application")
        run_app()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True) 