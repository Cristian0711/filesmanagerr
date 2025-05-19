#!/bin/bash
# Test volume mounts by creating files in the host and checking if they appear in the container

# Create test files in host directories
echo "Creating test files on host..."
echo "Host test file created at $(date)" > ./logs/host_test.log
echo "Host test file created at $(date)" > ./config/host_test.conf
chmod 777 ./logs/host_test.log ./config/host_test.conf

# List files in host directories
echo "Files in host logs directory:"
ls -la ./logs
echo "Files in host config directory:"
ls -la ./config

# Run a command in the container to check if files are visible
echo -e "\nChecking if files are visible in container..."
docker exec radarr-webhook ls -la /app/logs
docker exec radarr-webhook ls -la /app/config

# Create a file in the container and check if it appears on the host
echo -e "\nCreating files from container..."
docker exec radarr-webhook bash -c "echo Container file created at \$(date) > /app/logs/container_test.log"
docker exec radarr-webhook bash -c "echo Container file created at \$(date) > /app/config/container_test.conf"
docker exec radarr-webhook chmod 777 /app/logs/container_test.log /app/config/container_test.conf

# Check if container files appeared on host
echo -e "\nChecking for container files on host..."
ls -la ./logs
ls -la ./config 