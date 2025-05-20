#!/usr/bin/env python3
"""
Monkey-patch script to force logging to work by creating the logger before the app starts
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

print("===== MONKEY PATCH STARTING =====")

# Ensure logs directory exists
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)
os.chmod(log_dir, 0o777)

# Create log file with direct file operations
log_file = os.path.join(log_dir, "radarr-webhook.log")
with open(log_file, "a") as f:
    f.write(f"\n\n===== NEW LOG SESSION STARTED AT {datetime.now().isoformat()} =====\n\n")

os.chmod(log_file, 0o666)

print(f"Log file created: {log_file}")
print(f"Log directory contents:")
for item in os.listdir(log_dir):
    print(f"  - {item}")

# Now force the Python logger to work
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove any existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Add console handler
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root_logger.addHandler(console)

# Add file handler
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root_logger.addHandler(file_handler)

print("===== MONKEY PATCH COMPLETE =====")

# Log a test message
root_logger.info("Logger monkey-patched successfully")

# Now proceed with importing the application
from app.core.logging import logger
logger.info("Application logger imported after monkey patch") 