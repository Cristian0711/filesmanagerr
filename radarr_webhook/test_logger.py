#!/usr/bin/env python3
"""
Direct test of logging functionality
"""
import os
import sys
import logging

# Print system information
print("=== LOGGER TEST ===")
print(f"Current directory: {os.getcwd()}")
print(f"User: {os.getuid()}:{os.getgid()}")
print(f"LOG_DIR environment variable: {os.environ.get('LOG_DIR', 'Not set')}")
print(f"CONFIG_DIR environment variable: {os.environ.get('CONFIG_DIR', 'Not set')}")

# Create a very basic logger that writes directly to a file
log_dir = os.environ.get('LOG_DIR', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir, mode=0o777)
    print(f"Created log directory: {log_dir}")

log_file = os.path.join(log_dir, "direct_test.log")
print(f"Attempting to write to log file: {log_file}")

try:
    # Create a test file to check write access
    with open(log_file, 'w') as f:
        f.write("Direct file write test at startup\n")
    print(f"Successfully wrote to log file directly")
    
    # Setup basic logger
    logger = logging.getLogger("direct-test")
    logger.setLevel(logging.INFO)
    
    # Add file handler
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    # Test logging
    logger.info("This is a direct test message")
    logger.warning("This is a direct warning message")
    logger.error("This is a direct error message")
    
    print(f"Logging complete. Check {log_file} for output.")
    
    # Read back the log file
    with open(log_file, 'r') as f:
        content = f.read()
        print("\nLog file contents:")
        print(content)
        
except Exception as e:
    print(f"ERROR in direct logging test: {e}")
    
print("=== TEST COMPLETE ===") 