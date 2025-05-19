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

# Export current user/group IDs for Docker
export UID=$(id -u)
export GID=$(id -g)
echo "Exported UID=$UID and GID=$GID for Docker"

# Start Docker containers in detached mode
echo "Starting Docker containers..."
docker-compose up -d

# Show logs to verify operation
echo "Showing container logs (press Ctrl+C to exit):"
docker-compose logs -f 