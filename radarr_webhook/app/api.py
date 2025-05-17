"""
API module for Radarr webhook application.
Contains Flask routes and authentication functionality.
"""
from functools import wraps
from typing import Dict, Any, Callable

from flask import Flask, request, jsonify, Response
from werkzeug.local import LocalProxy

from app.config import Config, logger
from app.handlers import process_event
from app.storage import WebhookStorage
from app.monitor import get_active_downloads_status, check_torrent


def create_app() -> Flask:
    """Create and configure the Flask application"""
    app = Flask(__name__)
    register_routes(app)
    return app


def require_auth(f: Callable) -> Callable:
    """
    Authentication decorator for Flask routes.
    Supports token-based and Basic authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs) -> Response:
        auth = request.authorization
        
        # Check token authentication provided as parameter
        token = request.args.get('token')
        if Config.AUTH_TOKEN and token == Config.AUTH_TOKEN:
            return f(*args, **kwargs)
        
        # Check Basic authentication
        if Config.WEBHOOK_USERNAME and Config.WEBHOOK_PASSWORD:
            if not auth or auth.username != Config.WEBHOOK_USERNAME or auth.password != Config.WEBHOOK_PASSWORD:
                logger.warning(f"Authentication failed from {request.remote_addr}")
                return jsonify({"error": "Invalid authentication"}), 401
        
        return f(*args, **kwargs)
    return decorated


def register_routes(app: Flask) -> None:
    """Register API routes with the Flask application"""
    
    @app.route('/', methods=['GET'])
    def index() -> Response:
        """Main index route - provides API status"""
        return jsonify({
            "status": "online",
            "info": "Radarr Webhook Receiver",
            "version": "1.0.0"
        })

    @app.route('/', methods=['POST'])
    @require_auth
    def root_webhook() -> Response:
        """
        Root webhook endpoint for Radarr
        """
        return handle_webhook_request()

    @app.route('/webhook', methods=['POST'])
    @require_auth
    def webhook() -> Response:
        """
        Main endpoint for Radarr webhooks
        """
        return handle_webhook_request()
    
    @app.route('/status', methods=['GET'])
    @require_auth
    def status() -> Response:
        """
        Status endpoint for checking active downloads
        """
        return jsonify({
            "active_downloads": get_active_downloads_status()
        })
    
    @app.route('/torrent/<torrent_hash>', methods=['GET'])
    @require_auth
    def torrent_status(torrent_hash: str) -> Response:
        """
        Get status of a specific torrent by hash
        """
        # Sanitize the hash (remove any non-hex characters)
        import re
        sanitized_hash = re.sub(r'[^0-9a-fA-F]', '', torrent_hash)
        
        if not sanitized_hash:
            return jsonify({"error": "Invalid torrent hash"}), 400
            
        # Check the torrent status
        result = check_torrent(sanitized_hash)
        
        return jsonify({
            "torrent_hash": sanitized_hash,
            "result": result
        })


def handle_webhook_request() -> Response:
    """
    Common function to handle webhook requests
    """
    # Check if JSON data exists
    if not request.is_json:
        logger.warning(f"Non-JSON request received from {request.remote_addr}")
        return jsonify({"error": "JSON content expected"}), 400
    
    data = request.get_json()
    logger.debug(f"Webhook received: {data.get('eventType', 'Unknown')}")
    
    # Save data with timestamp to the history file
    WebhookStorage.append_to_history(data)
    
    # Also save the latest event for quick reference
    WebhookStorage.save_latest_webhook(data)
    
    # Process the event
    message, success = process_event(data)
    
    return jsonify({
        "status": "success" if success else "warning",
        "message": message
    }) 