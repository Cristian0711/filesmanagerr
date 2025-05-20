#!/bin/bash
# Direct debugging of log issues

echo "===== STOPPING CONTAINER ====="
docker-compose down

echo "===== STARTING CONTAINER FOR DEBUGGING ====="
docker-compose up -d

echo "===== RUNNING DEBUG.PY ====="
docker exec radarr-webhook python /app/debug.py

echo "===== CREATING LOG FILE DIRECTLY ====="
docker exec radarr-webhook bash -c "mkdir -p /app/logs && echo 'Direct test log entry' > /app/logs/radarr-webhook.log && chmod 666 /app/logs/radarr-webhook.log && ls -la /app/logs"

echo "===== RUNNING FIX_LOGGER.PY ====="
docker exec radarr-webhook python /app/fix_logger.py

echo "===== RESTARTING CONTAINER ====="
docker-compose restart

echo "===== CHECKING FOR LOG FILES AFTER RESTART ====="
sleep 5
docker exec radarr-webhook ls -la /app/logs

echo "===== CHECKING LOG FILE CONTENTS ====="
docker exec radarr-webhook cat /app/logs/radarr-webhook.log || echo "Log file not found or empty"

echo "===== DONE =====" 