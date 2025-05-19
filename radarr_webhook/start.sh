#!/bin/bash
# Setup script for radarr-webhook Docker environment

# Create host directories if they don't exist
mkdir -p ./logs ./config

# Set permissions to ensure Docker can write to them
chmod -R 777 ./logs ./config

# Print message
echo "Host directories prepared, starting containers..."

# Export current user's ID for docker-compose
export UID=$(id -u)
export GID=$(id -g)

# Start docker-compose
docker-compose up -d

# Display logs to verify it's working
echo "Containers started. Showing logs:"
docker-compose logs -f 