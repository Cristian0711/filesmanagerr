"""
Flask API for the webhook application.
Provides endpoints for Radarr and Sonarr webhooks and status information.
"""
import os
import json
from functools import wraps
from flask import Flask, request, jsonify, Response, g, render_template
from werkzeug.exceptions import BadRequest, Unauthorized, InternalServerError

from app.core.config import Config, setup_logging
from app.handlers import WebhookHandler
from app.core.monitor import active_downloads


# Set up logging
setup_logging()

# Create Flask application
app = Flask(__name__)


def auth_required(f):
    """Decorator to require authentication for endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        # Check token authentication
        if Config.AUTH_TOKEN and auth_header:
            token = auth_header.replace('Bearer ', '')
            if token == Config.AUTH_TOKEN:
                return f(*args, **kwargs)
        
        # Check basic auth
        auth = request.authorization
        if auth and auth.username == Config.WEBHOOK_USERNAME and auth.password == Config.WEBHOOK_PASSWORD:
            return f(*args, **kwargs)
            
        # No valid authentication provided
        return Response(
            'Authentication required', 
            401,
            {'WWW-Authenticate': 'Basic realm="Authentication Required"'}
        )
    return decorated


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Simple healthcheck endpoint that doesn't require auth"""
    return jsonify({'status': 'ok'})


@app.route('/webhook', methods=['POST'])
@auth_required
def webhook():
    """
    Main webhook endpoint that handles both Radarr and Sonarr webhooks
    """
    try:
        # Get JSON data from request
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        # Process webhook
        response_data, status_code = WebhookHandler.process_webhook(data)
        return jsonify(response_data), status_code
        
    except BadRequest:
        return jsonify({'error': 'Invalid JSON data'}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/webhook/radarr', methods=['POST'])
@auth_required
def radarr_webhook():
    """
    Radarr-specific webhook endpoint
    """
    try:
        # Get JSON data from request
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        # Process webhook as Radarr
        response_data, status_code = WebhookHandler.process_webhook(data, service_type='radarr')
        return jsonify(response_data), status_code
        
    except BadRequest:
        return jsonify({'error': 'Invalid JSON data'}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/webhook/sonarr', methods=['POST'])
@auth_required
def sonarr_webhook():
    """
    Sonarr-specific webhook endpoint
    """
    try:
        # Get JSON data from request
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        # Process webhook as Sonarr
        response_data, status_code = WebhookHandler.process_webhook(data, service_type='sonarr')
        return jsonify(response_data), status_code
        
    except BadRequest:
        return jsonify({'error': 'Invalid JSON data'}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/status', methods=['GET'])
@auth_required
def status():
    """
    Get status of all actively monitored downloads
    """
    from app.core.monitor import DownloadMonitor
    status_data = DownloadMonitor.get_active_downloads_status()
    
    return jsonify({
        'active_downloads_count': len(active_downloads),
        'download_monitoring_enabled': Config.DOWNLOAD_MONITOR_ENABLED,
        'downloads': status_data
    })


@app.route('/status/<torrent_hash>', methods=['GET'])
@auth_required
def check_torrent(torrent_hash):
    """
    Get detailed status about a specific torrent
    """
    from app.core.monitor import DownloadMonitor
    torrent_data = DownloadMonitor.check_torrent(torrent_hash)
    
    return jsonify(torrent_data)


@app.route('/last_webhook', methods=['GET'])
@auth_required
def last_webhook():
    """
    Get the last webhook that was received
    """
    try:
        webhook_file = os.path.join(os.path.dirname(Config.WEBHOOK_LOG_FILE), 'last_webhook_data.json')
        if os.path.exists(webhook_file):
            with open(webhook_file, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({'error': 'No webhook data available yet'}), 404
    except Exception as e:
        return jsonify({'error': f'Error reading webhook data: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Not Found'}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == "__main__":
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    ) 