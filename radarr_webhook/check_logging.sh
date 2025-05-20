#!/bin/bash
# Script to check logging issues inside the container

echo "=== Checking Docker Logs ==="
docker logs radarr-webhook | grep "VOLUME DEBUG"

echo -e "\n=== Examining Container Logs Directory ==="
docker exec radarr-webhook ls -la /app/logs

echo -e "\n=== Running Direct Logger Test ==="
docker exec radarr-webhook python /app/test_logger.py

echo -e "\n=== Checking Logger Import ==="
docker exec radarr-webhook python -c "from app.core.logging import logger; print('Logger initialized:',logger); print('Handler types:', [type(h).__name__ for h in logger.handlers]); logger.info('Test message from check_logging.sh')"

echo -e "\n=== Post-Test Log Files ==="
docker exec radarr-webhook ls -la /app/logs

echo -e "\n=== Viewing Root Directory Permissions ==="
docker exec radarr-webhook ls -la /app 