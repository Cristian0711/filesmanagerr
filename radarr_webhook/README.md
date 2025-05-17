# Radarr & Sonarr Webhook Server

A Python application that receives webhooks from Radarr and Sonarr and monitors downloads to create hardlinks for media files as they download.

## Features

- Receives and processes webhook events from both Radarr and Sonarr
- Monitors downloads in real-time
- Creates hardlinks for media files as they download
- Supports multiple download clients via qBittorrent API
- Provides status monitoring API
- Secure authentication options

## Requirements

- Python 3.8+
- qBittorrent (optional, for download monitoring)
- Radarr and/or Sonarr with webhook notifications enabled

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/radarr-sonarr-webhook.git
cd radarr-sonarr-webhook
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your configuration:

```
# Server settings
FLASK_ENV=production
DEBUG=False
PORT=9090
HOST=0.0.0.0

# Authentication
AUTH_TOKEN=your_secure_token_here
WEBHOOK_USERNAME=username
WEBHOOK_PASSWORD=password

# File paths
WEBHOOK_LOG_FILE=./logs/webhooks.log
DOWNLOAD_PATH=/path/to/downloads

# qBittorrent settings
QBITTORRENT_ENABLED=True
QBITTORRENT_HOST=localhost
QBITTORRENT_PORT=8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin
QBITTORRENT_USE_API=True

# Features
DOWNLOAD_MONITOR_ENABLED=True
RADARR_ENABLED=True
SONARR_ENABLED=True
```

## Usage

### Running the application

```bash
# Development mode
python -m app.main

# Production mode
gunicorn -w 4 -b 0.0.0.0:9090 "app.main:app"
```

### Configuring Radarr/Sonarr

1. In Radarr/Sonarr, go to Settings > Connect > + > Webhook
2. Enter the URL to your webhook server:
   - For generic endpoint: `http://your-server:9090/webhook`
   - For Radarr specific: `http://your-server:9090/webhook/radarr`
   - For Sonarr specific: `http://your-server:9090/webhook/sonarr`
3. If using Basic Auth, configure your username and password

### API Endpoints

- `POST /webhook`: Generic webhook endpoint (auto-detects service)
- `POST /webhook/radarr`: Radarr-specific webhook endpoint
- `POST /webhook/sonarr`: Sonarr-specific webhook endpoint
- `GET /status`: Status of active downloads
- `GET /status/<torrent_hash>`: Status of a specific torrent
- `GET /last_webhook`: View the last received webhook
- `GET /healthcheck`: Simple health check endpoint

## Development

### Project Structure

```
radarr_webhook/
├── app/
│   ├── core/           # Shared core functionality
│   │   ├── config.py   # Configuration settings
│   │   ├── models.py   # Base models
│   │   ├── monitor.py  # Download monitoring
│   │   └── storage.py  # File operations
│   ├── radarr/         # Radarr-specific code
│   │   ├── models.py   # Radarr models
│   │   └── monitor.py  # Radarr monitor
│   ├── sonarr/         # Sonarr-specific code
│   │   ├── models.py   # Sonarr models
│   │   └── monitor.py  # Sonarr monitor
│   ├── services/       # External services
│   │   └── qbittorrent.py  # qBittorrent client
│   ├── api.py          # Flask API endpoints
│   ├── handlers.py     # Webhook handling logic
│   └── main.py         # Application entry point
├── logs/               # Log files
├── .env                # Environment configuration
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. 