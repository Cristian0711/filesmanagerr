#!/usr/bin/env python3
"""
Debug script for diagnosing logger issues
"""
import os
import sys
import logging
import logging.handlers
import traceback

print("=== LOGGER DEBUG ===")
print(f"Current directory: {os.getcwd()}")
print(f"Python version: {sys.version}")
print(f"User: {os.getuid()}:{os.getgid()}")

# Check environment variables
print("\nEnvironment Variables:")
print(f"LOG_DIR: {os.environ.get('LOG_DIR', 'Not set')}")
print(f"CONFIG_DIR: {os.environ.get('CONFIG_DIR', 'Not set')}")

# Check log directory
log_dir = os.environ.get('LOG_DIR', '/app/logs')
print(f"\nChecking log directory: {log_dir}")
if os.path.exists(log_dir):
    print(f"Log directory exists")
    print(f"Permissions: {oct(os.stat(log_dir).st_mode)}")
    print(f"Is writable: {os.access(log_dir, os.W_OK)}")
    
    # List contents
    print("\nDirectory contents:")
    for item in os.listdir(log_dir):
        item_path = os.path.join(log_dir, item)
        if os.path.isdir(item_path):
            print(f"  {item}/ (dir)")
        else:
            print(f"  {item} ({os.path.getsize(item_path)} bytes)")
else:
    print(f"Log directory does not exist!")
    try:
        os.makedirs(log_dir, mode=0o777, exist_ok=True)
        print(f"Created log directory")
    except Exception as e:
        print(f"Error creating log directory: {e}")

# Try direct file writing
test_file = os.path.join(log_dir, "debug_test.log")
print(f"\nTrying to write directly to: {test_file}")
try:
    with open(test_file, 'w') as f:
        f.write("Test message written directly\n")
    print(f"Successfully wrote to file")
except Exception as e:
    print(f"Error writing to file: {e}")
    traceback.print_exc()

# Try rotating file handler
print("\nTrying RotatingFileHandler:")
try:
    logger = logging.getLogger("debug-test")
    logger.setLevel(logging.INFO)
    
    # Add rotating file handler
    rotation_file = os.path.join(log_dir, "rotation_test.log")
    handler = logging.handlers.RotatingFileHandler(
        rotation_file,
        maxBytes=1024*1024,
        backupCount=3
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Log test messages
    logger.info("This is a test message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print(f"Successfully created rotating file handler and logged messages")
    
    # Check file
    if os.path.exists(rotation_file):
        print(f"Rotation file created: {rotation_file}")
        print(f"File size: {os.path.getsize(rotation_file)} bytes")
    else:
        print(f"Failed to create rotation file!")
except Exception as e:
    print(f"Error setting up RotatingFileHandler: {e}")
    traceback.print_exc()

# Try to import and use the application's logger
print("\nTrying to use application logger:")
try:
    from app.core.logging import logger
    print(f"Logger imported: {logger}")
    print(f"Handler types: {[type(h).__name__ for h in logger.handlers]}")
    
    logger.info("Test message from debug.py")
    
    # Try to find the log file by checking handlers
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            log_path = handler.baseFilename
            print(f"Log file path: {log_path}")
            
            if os.path.exists(log_path):
                print(f"Log file exists, size: {os.path.getsize(log_path)} bytes")
                
                # Read the last few lines
                try:
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                        print(f"Last lines of log file:")
                        for line in lines[-5:]:
                            print(f"  {line.strip()}")
                except Exception as e:
                    print(f"Error reading log file: {e}")
            else:
                print(f"Log file does not exist!")
except Exception as e:
    print(f"Error using application logger: {e}")
    traceback.print_exc()

print("\n=== DEBUG COMPLETE ===") 