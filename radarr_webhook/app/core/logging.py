"""
Logging configuration module for the application.
Provides centralized logging setup with file rotation.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(log_dir=None, log_level=None, app_name='radarr-webhook'):
    """
    Set up application logging with rotation to keep files under 10MB.
    
    Args:
        log_dir: Directory where log files will be stored
        log_level: Logging level (default: INFO)
        app_name: Name of the application for the logger
        
    Returns:
        Logger instance configured with handlers
    """
    # Use environment variables if parameters not specified
    if log_dir is None:
        log_dir = os.getenv('LOG_DIR', 'logs')
    
    if log_level is None:
        log_level_str = os.getenv('LOG_LEVEL', 'INFO')
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Create logs directory with full permissions if it doesn't exist
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=0o777, exist_ok=True)
            print(f"Created log directory: {log_dir}", file=sys.stderr)
        else:
            # Ensure it's writable
            os.chmod(log_dir, 0o777)
            print(f"Ensured write permissions on log directory: {log_dir}", file=sys.stderr)
    except Exception as e:
        print(f"Error configuring log directory {log_dir}: {e}", file=sys.stderr)
        # Fall back to current directory
        log_dir = '.'
        print(f"Falling back to current directory for logs", file=sys.stderr)
    
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
    
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Print success message to stderr (will show in Docker logs)
        print(f"Logging to file: {log_file}", file=sys.stderr)
    except Exception as e:
        print(f"Error setting up log file {log_file}: {e}", file=sys.stderr)
        print("Log messages will only appear in console output", file=sys.stderr)
    
    # Always add console handler for Docker visibility
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Log initial messages
    logger.info(f"Logging initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    
    if len(logger.handlers) > 1:  # Both file and console handlers
        logger.info(f"Log file: {os.path.abspath(log_file)}")
    
    return logger


# Default logger instance
logger = setup_logging() 