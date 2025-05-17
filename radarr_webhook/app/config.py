"""
Configuration module for Radarr webhook application.
Handles environment variables, settings, and shared configurations.
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging():
    """Configure and setup logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("webhook.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("radarr-webhook")

# Create logger instance
logger = setup_logging()

# Application settings
class Config:
    """Main configuration class for the application"""
    # Server settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Authentication
    AUTH_TOKEN = os.getenv('AUTH_TOKEN')
    WEBHOOK_USERNAME = os.getenv('WEBHOOK_USERNAME')
    WEBHOOK_PASSWORD = os.getenv('WEBHOOK_PASSWORD')
    
    # File paths
    WEBHOOK_LOG_FILE = os.getenv('WEBHOOK_LOG_FILE', 'webhook_history.json')
    QBITTORRENT_PATH = os.getenv('QBITTORRENT_PATH', '/mnt/downloads')
    
    # qBittorrent connection settings
    QBITTORRENT_ENABLED = os.getenv('QBITTORRENT_ENABLED', 'true').lower() == 'true'
    QBITTORRENT_HOST = os.getenv('QBITTORRENT_HOST', 'localhost')
    QBITTORRENT_PORT = int(os.getenv('QBITTORRENT_PORT', 8080))
    QBITTORRENT_USERNAME = os.getenv('QBITTORRENT_USERNAME', 'admin')
    QBITTORRENT_PASSWORD = os.getenv('QBITTORRENT_PASSWORD', 'adminadmin')
    QBITTORRENT_USE_API = os.getenv('QBITTORRENT_USE_API', 'true').lower() == 'true'
    
    # Download monitor settings
    MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', 60))  # Seconds between checks
    MAX_MONITOR_CHECKS = int(os.getenv('MAX_MONITOR_CHECKS', 100))
    MIN_FILE_SIZE = int(os.getenv('MIN_FILE_SIZE', 10*1024*1024))  # 10MB default
    
    # Supported media extensions
    MEDIA_EXTENSIONS = ['.mkv', '.mp4', '.avi', '.mov', '.m4v']
    SUBTITLE_EXTENSIONS = ['.srt', '.sub', '.idx', '.ass']
    
    @classmethod
    def get_supported_extensions(cls):
        """Return all supported file extensions"""
        return cls.MEDIA_EXTENSIONS + cls.SUBTITLE_EXTENSIONS 