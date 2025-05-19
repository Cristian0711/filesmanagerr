FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create volumes for data persistence
VOLUME ["/app/config", "/app/logs"]

# Set environment variables
ENV PORT=5000
ENV HOST=0.0.0.0
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV DOWNLOAD_MONITOR_ENABLED=true
ENV RADARR_ENABLED=true
ENV SONARR_ENABLED=true

# Expose the port
EXPOSE 5000

# Run the application
CMD ["python", "run.py"] 