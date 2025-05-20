#!/usr/bin/env python3
"""
Script to fix the logging issue in the application
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

print("=== LOGGER FIX SCRIPT ===")
print(f"Current directory: {os.getcwd()}")

# Ensure logs directory exists with correct permissions
log_dir = os.environ.get('LOG_DIR', '/app/logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir, mode=0o777, exist_ok=True)
    print(f"Created log directory: {log_dir}")
else:
    os.chmod(log_dir, 0o777)
    print(f"Ensured permissions on log directory: {log_dir}")

# Create a fixed logger
app_name = 'radarr-webhook'
log_file = os.path.join(log_dir, f"{app_name}.log")

print(f"Creating log file: {log_file}")
try:
    # Create the file if it doesn't exist
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write(f"Log file created by fix_logger.py\n")
        print(f"Created new log file")
    
    # Ensure permissions
    os.chmod(log_file, 0o666)
    print(f"Set permissions on log file: {oct(os.stat(log_file).st_mode)}")
    
    print(f"Log file ready at: {os.path.abspath(log_file)}")
    print(f"Size: {os.path.getsize(log_file)} bytes")
except Exception as e:
    print(f"Error creating log file: {e}")
    
print("\nLogs directory contents:")
for item in os.listdir(log_dir):
    item_path = os.path.join(log_dir, item)
    if os.path.isdir(item_path):
        print(f"  {item}/ (dir)")
    else:
        print(f"  {item} ({os.path.getsize(item_path)} bytes)")

print("\n=== FIX COMPLETE, RESTART THE CONTAINER ===") 