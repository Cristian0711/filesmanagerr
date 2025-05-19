#!/bin/bash

echo "=============== VOLUME DEBUG ==============="
echo "Running as user: $(id)"
echo "Working directory: $(pwd)"

# Check logs directory
echo "Checking logs directory:"
ls -la /app/logs
echo "Creating test file in logs directory"
echo "Test file created at $(date)" > /app/logs/test_container.log
chmod 777 /app/logs/test_container.log
ls -la /app/logs

# Check config directory
echo "Checking config directory:"
ls -la /app/config
echo "Creating test file in config directory"
echo "Test file created at $(date)" > /app/config/test_container.conf
chmod 777 /app/config/test_container.conf
ls -la /app/config

# Check volume mounts
echo "Mounted volumes:"
mount | grep app

echo "=============== END DEBUG ===============" 