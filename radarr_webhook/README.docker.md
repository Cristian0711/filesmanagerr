# Radarr & Sonarr Webhook Server Docker Setup

This document explains how to run the Radarr & Sonarr Webhook Server using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)

## Quick Start with Docker Compose

1. Clone this repository and navigate to the project directory:

```bash
git clone <repository-url>
cd radarr_webhook
```

2. Edit the `docker-compose.yml` file to set your specific paths and credentials:

```yaml
volumes:
  - /path/to/downloads:/mnt/downloads:ro  # Change to your actual downloads path
  - /path/to/media:/mnt/plexmedia        # Change to your actual media path
```

3. Start the container:

```bash
docker-compose up -d
```

4. The webhook server will be accessible at `http://your-server-ip:5000`

## Configure Radarr & Sonarr

In Radarr and Sonarr, add a webhook notification with the following URL:

- Radarr: `http://your-server-ip:5000/webhook/radarr`
- Sonarr: `http://your-server-ip:5000/webhook/sonarr`

If you've set up authentication, include the username and password:

```
http://webhookuser:webhookpass@your-server-ip:5000/webhook/radarr
```

## Manual Docker Setup

If you're not using Docker Compose, you can run the container directly:

```bash
# Build the image
docker build -t radarr-webhook .

# Run the container
docker run -d \
  --name radarr-webhook \
  -p 5000:5000 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  -v /path/to/downloads:/mnt/downloads:ro \
  -v /path/to/media:/mnt/plexmedia \
  -e QBITTORRENT_HOST=your-qbittorrent-host \
  -e QBITTORRENT_PORT=8080 \
  -e QBITTORRENT_USERNAME=admin \
  -e QBITTORRENT_PASSWORD=adminadmin \
  radarr-webhook
```

## Environment Variables

The Docker container can be configured using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Port for the webhook server | 5000 |
| HOST | Host to bind to | 0.0.0.0 |
| DOWNLOAD_MONITOR_ENABLED | Enable download monitoring | true |
| RADARR_ENABLED | Enable Radarr support | true |
| SONARR_ENABLED | Enable Sonarr support | true |
| QBITTORRENT_ENABLED | Enable qBittorrent integration | true |
| QBITTORRENT_HOST | qBittorrent WebUI host | localhost |
| QBITTORRENT_PORT | qBittorrent WebUI port | 8080 |
| QBITTORRENT_USERNAME | qBittorrent WebUI username | admin |
| QBITTORRENT_PASSWORD | qBittorrent WebUI password | adminadmin |
| QBITTORRENT_PATH | Path to qBittorrent downloads | /mnt/downloads |
| WEBHOOK_USERNAME | Username for webhook authentication | |
| WEBHOOK_PASSWORD | Password for webhook authentication | |

## Volumes

The container uses the following volumes:

- `/app/config`: Configuration files
- `/app/logs`: Log files
- `/mnt/downloads`: Download directory (read-only)
- `/mnt/plexmedia`: Media library directory

## Check Logs

To view the logs:

```bash
docker logs -f radarr-webhook
``` 