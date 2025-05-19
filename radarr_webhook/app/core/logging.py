"""
Logging configuration module for the application.
Provides centralized logging setup with file rotation.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(log_dir='logs', log_level=logging.INFO, app_name='radarr-webhook'):
    """
    Set up application logging with rotation to keep files under 10MB.
    
    Args:
        log_dir: Directory where log files will be stored
        log_level: Logging level (default: INFO)
        app_name: Name of the application for the logger
        
    Returns:
        Logger instance configured with handlers
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure the root logger
    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers to prevent duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter with timestamp
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    
    # Create rotating file handler (10MB max size, 5 backup files)
    log_file = os.path.join(log_dir, f"{app_name}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log file: {os.path.abspath(log_file)}")
    
    return logger


# Default logger instance
logger = setup_logging() 