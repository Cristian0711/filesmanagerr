FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for config and logs
RUN mkdir -p /app/config /app/logs \
    && chmod -R 777 /app/config /app/logs \
    && echo "Created config and logs directories with full permissions"

# Add debug scripts
COPY debug_volumes.sh /app/
RUN chmod +x /app/debug_volumes.sh

# Create an initial log file
RUN touch /app/logs/radarr-webhook.log && chmod 666 /app/logs/radarr-webhook.log

# Environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV LOG_LEVEL=INFO
ENV LOG_DIR=/app/logs
ENV CONFIG_DIR=/app/config
ENV PYTHONUNBUFFERED=1

# Expose the Flask port
EXPOSE 5000

# Run the application with monkey patch
CMD ["python", "monkey_patch.py"] 