"""
Main entry point for the application.
Starts the Flask server with webhook endpoints.
"""
import os
import sys

# Add parent directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app.api import app
from app.core.config import Config, setup_logging, logger


def main():
    """
    Main entry point function
    """
    # Set up logging
    setup_logging()
    
    # Log startup details
    logger.info("Starting Radarr/Sonarr Webhook Server")
    logger.info(f"Server running on http://{Config.HOST}:{Config.PORT}")
    logger.info(f"Debug mode: {Config.DEBUG}")
    logger.info(f"Download monitoring: {'Enabled' if Config.DOWNLOAD_MONITOR_ENABLED else 'Disabled'}")
    logger.info(f"Radarr support: {'Enabled' if Config.RADARR_ENABLED else 'Disabled'}")
    logger.info(f"Sonarr support: {'Enabled' if Config.SONARR_ENABLED else 'Disabled'}")
    logger.info(f"qBittorrent integration: {'Enabled' if Config.QBITTORRENT_ENABLED else 'Disabled'}")
    
    # Start the Flask app
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=True  # Allow multiple concurrent requests
    )


# Alias for backwards compatibility with run.py
run_app = main


if __name__ == "__main__":
    main() 