"""
Main application entry point for Radarr Webhook application.
"""
from app.config import Config, logger
from app.api import create_app

# Create the Flask application
app = create_app()

def run_app():
    """Run the Flask application with configured settings"""
    port = Config.PORT
    host = Config.HOST
    debug = Config.DEBUG
    
    logger.info(f"Starting Radarr Webhook Receiver on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_app() 