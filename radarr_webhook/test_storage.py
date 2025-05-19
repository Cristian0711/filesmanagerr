#!/usr/bin/env python
"""
Test script to verify that storage and logging are working correctly.
"""
import os
import sys
import json
import pickle
from datetime import datetime

# Set environment variables for testing
os.environ['CONFIG_DIR'] = 'config'
os.environ['LOG_DIR'] = 'logs'

# Import after setting environment variables
from app.core.logging import logger
from app.core.storage import TorrentStorage, WebhookStorage

def test_directories():
    """Test that directories exist and are writable"""
    print("Testing directories:")
    
    # Test config directory
    config_dir = os.environ['CONFIG_DIR']
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, mode=0o777, exist_ok=True)
        print(f"Created config directory: {config_dir}")
    
    if os.access(config_dir, os.W_OK):
        print(f"✅ Config directory {config_dir} is writable")
    else:
        print(f"❌ Config directory {config_dir} is NOT writable")
        stat_info = os.stat(config_dir)
        print(f"  Mode: {oct(stat_info.st_mode)}")
        print(f"  Owner: {stat_info.st_uid}:{stat_info.st_gid}")
    
    # Test logs directory
    log_dir = os.environ['LOG_DIR']
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, mode=0o777, exist_ok=True)
        print(f"Created logs directory: {log_dir}")
    
    if os.access(log_dir, os.W_OK):
        print(f"✅ Logs directory {log_dir} is writable")
    else:
        print(f"❌ Logs directory {log_dir} is NOT writable")
        stat_info = os.stat(log_dir)
        print(f"  Mode: {oct(stat_info.st_mode)}")
        print(f"  Owner: {stat_info.st_uid}:{stat_info.st_gid}")

def test_torrent_storage():
    """Test TorrentStorage functionality"""
    print("\nTesting TorrentStorage:")
    
    # Initialize storage
    TorrentStorage.initialize()
    
    # Generate test data
    test_id = f"test_torrent_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Save test data
    TorrentStorage.save_torrent_info(
        download_id=test_id,
        media_id=12345,
        media_title="Test Movie",
        media_path="/movies/Test Movie",
        torrent_path="/downloads/Test Movie",
        media_type="movie"
    )
    
    # Check if storage file exists
    storage_file = os.path.join(os.environ['CONFIG_DIR'], "torrents.pickle")
    if os.path.exists(storage_file):
        print(f"✅ Storage file created at {storage_file}")
        print(f"  File size: {os.path.getsize(storage_file)} bytes")
        print(f"  File permissions: {oct(os.stat(storage_file).st_mode)}")
    else:
        print(f"❌ Storage file NOT created at {storage_file}")
    
    # Retrieve and verify data
    retrieved = TorrentStorage.get_torrent_info(test_id)
    if retrieved and retrieved.get('media_title') == "Test Movie":
        print(f"✅ Successfully retrieved test data")
    else:
        print(f"❌ Failed to retrieve test data")
    
    # Try to load the file directly
    try:
        with open(storage_file, 'rb') as f:
            data = pickle.load(f)
            if test_id in data:
                print(f"✅ Direct file read successful")
            else:
                print(f"❌ File does not contain test data")
    except Exception as e:
        print(f"❌ Failed to read storage file directly: {e}")

def test_webhook_storage():
    """Test WebhookStorage functionality"""
    print("\nTesting WebhookStorage:")
    
    # Save test data
    test_data = {
        "test": True,
        "timestamp": datetime.now().isoformat(),
        "name": "Test Webhook"
    }
    
    WebhookStorage.save_latest_webhook(test_data)
    
    # Check if file exists
    webhook_file = os.path.join(os.environ['CONFIG_DIR'], "last_webhook_data.json")
    if os.path.exists(webhook_file):
        print(f"✅ Webhook file created at {webhook_file}")
        print(f"  File size: {os.path.getsize(webhook_file)} bytes")
        print(f"  File permissions: {oct(os.stat(webhook_file).st_mode)}")
        
        # Try to read the file
        try:
            with open(webhook_file, 'r') as f:
                data = json.load(f)
                if data.get('test') == True:
                    print(f"✅ Webhook file contents verified")
                else:
                    print(f"❌ Webhook file contents incorrect")
        except Exception as e:
            print(f"❌ Failed to read webhook file: {e}")
    else:
        print(f"❌ Webhook file NOT created at {webhook_file}")

def test_logging():
    """Test logging functionality"""
    print("\nTesting Logging:")
    
    # Log some test messages
    logger.info("This is a test INFO message")
    logger.warning("This is a test WARNING message")
    logger.error("This is a test ERROR message")
    
    # Check if log file exists
    log_file = os.path.join(os.environ['LOG_DIR'], "radarr-webhook.log")
    if os.path.exists(log_file):
        print(f"✅ Log file created at {log_file}")
        print(f"  File size: {os.path.getsize(log_file)} bytes")
        print(f"  File permissions: {oct(os.stat(log_file).st_mode)}")
        
        # Check file contents
        try:
            with open(log_file, 'r') as f:
                last_lines = f.readlines()[-3:]  # Get last 3 lines
                if any("test INFO message" in line for line in last_lines):
                    print(f"✅ Log file contains test messages")
                else:
                    print(f"❌ Log file does not contain expected messages")
        except Exception as e:
            print(f"❌ Failed to read log file: {e}")
    else:
        print(f"❌ Log file NOT created at {log_file}")

if __name__ == "__main__":
    print("=== Storage and Logging Test ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Running as user: {os.getuid()}:{os.getgid()}")
    
    test_directories()
    test_torrent_storage()
    test_webhook_storage()
    test_logging()
    
    print("\nTest completed.") 