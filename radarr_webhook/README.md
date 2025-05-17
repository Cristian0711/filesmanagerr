# Radarr Webhook Receiver

A Python application that receives webhook notifications from Radarr and creates hardlinks for downloaded media files.

## Features

- Receives webhook notifications from Radarr
- Automatically creates hardlinks from torrent files to movie folders
- Monitors in-progress downloads and links files as they appear
- Integrates with qBittorrent API to check download status
- Supports all Radarr event types (Grab, Download, Rename, etc.)
- Provides authentication options (token-based or username/password)
- Maintains a history of webhook events
- Well-organized modular code structure for easy customization

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/radarr-webhook.git
cd radarr-webhook
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file based on the example:
```bash
cp .env.example .env
```

4. Edit the `.env` file to configure your settings:
```ini
# Flask server configuration
FLASK_APP=app.main
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000
HOST=0.0.0.0  # Change to your IP if needed

# Authentication credentials for webhook (if needed)
WEBHOOK_USERNAME=your_username
WEBHOOK_PASSWORD=your_password

# Secret token for authentication (optional)
AUTH_TOKEN=your_secret_token_here

# File paths
WEBHOOK_LOG_FILE=webhook_history.json
QBITTORRENT_PATH=/path/to/downloads  # Change to your actual download path

# qBittorrent connection settings
QBITTORRENT_ENABLED=true
QBITTORRENT_HOST=localhost
QBITTORRENT_PORT=8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin
QBITTORRENT_USE_API=true

# Download monitor settings
MONITOR_INTERVAL=60
MAX_MONITOR_CHECKS=100
MIN_FILE_SIZE=10485760  # 10MB in bytes
```

## Usage

### Running the application

Start the server:
```bash
python run.py
```

For production use, you might want to use Gunicorn:
```bash
gunicorn -b 0.0.0.0:5000 app.main:app
```

### Configuring Radarr

1. In Radarr, go to Settings > Connect > + (Add)
2. Select "Webhook" as the notification type
3. Enter a name (e.g., "Hardlink Webhook")
4. Configure the webhook:
   - URL: `http://your-server-ip:5000/webhook`
   - Method: POST
   - Username/Password: Enter if you configured them in your .env file
   - Select which events should trigger the webhook (at least "On Grab" is required)

5. Test the connection and save the settings

### Authentication Options

This application supports multiple authentication methods:

1. **Token-based authentication**:
   - Set `AUTH_TOKEN` in your `.env` file
   - Add the token to your webhook URL: `http://your-server-ip:5000/webhook?token=your_secret_token`

2. **Basic HTTP authentication**:
   - Set `WEBHOOK_USERNAME` and `WEBHOOK_PASSWORD` in your `.env` file
   - Configure these credentials in Radarr's webhook settings

### qBittorrent Integration

For qBittorrent integration to work:

1. Enable the qBittorrent WebUI in Tools > Options > Web UI
2. Set up the port, username, and password
3. Configure these settings in the `.env` file
4. The application will use the qBittorrent API to:
   - Find exact download paths
   - Check if downloads are completed
   - Get detailed torrent information

## API Endpoints

- `GET /` - Status information
- `POST /webhook` or `POST /` - Webhook receiver endpoint
- `GET /status` - Shows currently monitored downloads
- `GET /torrent/<hash>` - Get status of a specific torrent by hash

## Project Structure

```
radarr_webhook/
├── app/
│   ├── __init__.py
│   ├── api.py         # Flask API and routing
│   ├── config.py      # Configuration and environment variables
│   ├── handlers.py    # Event handling logic
│   ├── main.py        # Application entry point 
│   ├── models.py      # Data models for Radarr events
│   ├── monitor.py     # Download monitoring and hardlinking
│   ├── qbt_client.py  # qBittorrent API client
│   └── storage.py     # File operations and data persistence
├── .env               # Environment variables (create from .env.example)
├── .env.example       # Example environment variables
├── requirements.txt   # Python dependencies
├── README.md          # This documentation
└── run.py            # Startup script
```

## Customizing Behavior

To customize how different events are processed:

1. For event processing logic, check `app/handlers.py`
2. For download monitoring and hardlinking, check `app/monitor.py`
3. For file operations, check `app/storage.py`
4. For qBittorrent integration, check `app/qbt_client.py`

## Logging

The application logs to both console and a file named `webhook.log`. Check this file for detailed information about the application's operation.

## License

MIT 