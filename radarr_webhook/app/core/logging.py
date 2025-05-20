"""
Logging configuration module for the application.
Provides centralized logging setup with file rotation.
"""
import os
import sys
import logging
import stat
import platform
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
    
    # Print system information
    print(f"System: {platform.system()} {platform.release()}", file=sys.stderr)
    print(f"Python: {platform.python_version()}", file=sys.stderr)
    print(f"Current working directory: {os.getcwd()}", file=sys.stderr)
    print(f"User running process: {os.getuid()}:{os.getgid()}", file=sys.stderr)
    
    # Create logs directory with full permissions if it doesn't exist
    log_file = None
    try:
        # Convert to absolute path for clarity in logs
        log_dir = os.path.abspath(log_dir)
        print(f"Log directory (absolute): {log_dir}", file=sys.stderr)
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=0o777, exist_ok=True)
            print(f"Created log directory: {log_dir}", file=sys.stderr)
        
        # Ensure it's writable by setting permissions
        os.chmod(log_dir, 0o777)
        print(f"Set permissions on log directory: {oct(os.stat(log_dir).st_mode)}", file=sys.stderr)
        
        # Check if directory is writable
        if not os.access(log_dir, os.W_OK):
            print(f"WARNING: Log directory {log_dir} is not writable!", file=sys.stderr)
            # Try to find what's wrong
            dir_stat = os.stat(log_dir)
            print(f"Directory owner: {dir_stat.st_uid}:{dir_stat.st_gid}", file=sys.stderr)
            print(f"Directory permissions: {oct(dir_stat.st_mode)}", file=sys.stderr)
        else:
            print(f"Log directory {log_dir} is writable", file=sys.stderr)
            
        # Create a test file to verify write permissions
        test_file = os.path.join(log_dir, "test_write.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("Test write access")
            print(f"Successfully created test file at {test_file}", file=sys.stderr)
            os.remove(test_file)
            print(f"Successfully removed test file at {test_file}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Could not write test file to {log_dir}: {e}", file=sys.stderr)
            
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
    
    # Create a console handler first - ensure messages are visible in Docker
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    print("Added console handler to logger", file=sys.stderr)
    
    # Create rotating file handler (10MB max size, 5 backup files)
    log_file = os.path.join(log_dir, f"{app_name}.log")
    
    try:
        print(f"Attempting to create log file at: {log_file}", file=sys.stderr)
        
        # First try to create an empty file to test permissions
        # Create the parent directory
        if not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create the file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write(f"Log file created at {datetime.now().isoformat()}\n")
            print(f"Created empty log file at {log_file}", file=sys.stderr)
        
        # Set permissions on the log file
        os.chmod(log_file, 0o666)
        print(f"Set permissions on log file: {oct(os.stat(log_file).st_mode)}", file=sys.stderr)
        
        # Create the rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Print success message to stderr (will show in Docker logs)
        print(f"Successfully added file handler for: {log_file}", file=sys.stderr)
    except Exception as e:
        print(f"Error setting up log file {log_file}: {e}", file=sys.stderr)
        print("Log messages will only appear in console output", file=sys.stderr)
    
    # Log initial messages
    logger.info(f"Logging initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    
    if len(logger.handlers) > 1:  # Both file and console handlers
        logger.info(f"Log file: {os.path.abspath(log_file)}")
    
    return logger


# Create the default logger instance
logger = setup_logging() 