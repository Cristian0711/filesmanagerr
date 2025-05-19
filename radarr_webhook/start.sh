#!/bin/bash
# Setup script for radarr-webhook Docker environment

# Create required directories if they don't exist
mkdir -p ./logs
mkdir -p ./config

# Set permissions to ensure Docker can write to them
chmod -R 777 ./logs
chmod -R 777 ./config

# Report directory settings
echo "Directory setup:"
echo "- Logs directory: $(pwd)/logs"
echo "- Config directory: $(pwd)/config"
echo "- Current user: $(id)"

# We're already running as root, so we don't need to export UID/GID
# Just print who we're running as
echo "Running Docker as root user"

# Clean up container if it already exists
echo "Stopping any existing containers..."
docker-compose down

# Start Docker containers in detached mode
echo "Starting Docker containers..."
docker-compose up -d

# Show logs to verify operation
echo "Showing container logs (press Ctrl+C to exit):"
docker-compose logs -f 