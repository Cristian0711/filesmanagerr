"""
Configuration module for *arr webhook applications.
Handles environment variables, settings, and shared configurations.
"""
import os
from dotenv import load_dotenv

# Import the new centralized logging system
from app.core.logging import logger

# Load environment variables
load_dotenv()

# Application settings
class Config:
    """Main configuration class for the application"""
    # Server settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # Authentication
    AUTH_TOKEN = os.getenv('AUTH_TOKEN')
    WEBHOOK_USERNAME = os.getenv('WEBHOOK_USERNAME')
    WEBHOOK_PASSWORD = os.getenv('WEBHOOK_PASSWORD')
    
    # File paths
    WEBHOOK_LOG_FILE = os.getenv('WEBHOOK_LOG_FILE', 'webhook_history.json')
    DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', '/mnt/downloads')
    
    # qBittorrent connection settings
    QBITTORRENT_ENABLED = os.getenv('QBITTORRENT_ENABLED', 'true').lower() == 'true'
    QBITTORRENT_HOST = os.getenv('QBITTORRENT_HOST', 'localhost')
    QBITTORRENT_PORT = int(os.getenv('QBITTORRENT_PORT', 8080))
    QBITTORRENT_USERNAME = os.getenv('QBITTORRENT_USERNAME', 'admin')
    QBITTORRENT_PASSWORD = os.getenv('QBITTORRENT_PASSWORD', 'adminadmin')
    QBITTORRENT_USE_API = os.getenv('QBITTORRENT_USE_API', 'true').lower() == 'true'
    QBITTORRENT_PATH = os.getenv('QBITTORRENT_PATH', DOWNLOAD_PATH)
    
    # Download monitor settings
    DOWNLOAD_MONITOR_ENABLED = os.getenv('DOWNLOAD_MONITOR_ENABLED', 'true').lower() == 'true'
    MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', 60))  # Seconds between checks
    MAX_MONITOR_CHECKS = int(os.getenv('MAX_MONITOR_CHECKS', 100))
    MIN_FILE_SIZE = int(os.getenv('MIN_FILE_SIZE', 10*1024*1024))  # 10MB default
    
    # Supported media extensions
    MEDIA_EXTENSIONS = ['.mkv', '.mp4', '.avi', '.mov', '.m4v']
    SUBTITLE_EXTENSIONS = ['.srt', '.sub', '.idx', '.ass']
    
    # Service type
    RADARR_ENABLED = os.getenv('RADARR_ENABLED', 'true').lower() == 'true'
    SONARR_ENABLED = os.getenv('SONARR_ENABLED', 'true').lower() == 'true'
    
    @classmethod
    def get_supported_extensions(cls):
        """Return all supported file extensions"""
        return cls.MEDIA_EXTENSIONS + cls.SUBTITLE_EXTENSIONS 