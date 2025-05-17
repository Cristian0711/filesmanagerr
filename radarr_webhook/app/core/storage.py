"""
Storage module for handling persistence of webhook data,
file operations, and other storage-related functionality.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.config import Config, logger


class WebhookStorage:
    """Class for managing webhook data persistence"""
    
    @staticmethod
    def save_latest_webhook(data: Dict[str, Any]) -> None:
        """Save the most recent webhook data to a file"""
        try:
            with open('last_webhook_data.json', 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving latest webhook data: {e}")
    
    @staticmethod
    def append_to_history(data: Dict[str, Any]) -> None:
        """
        Append webhook data to history file with timestamp
        """
        history_file = Config.WEBHOOK_LOG_FILE
        
        # Create a new entry with timestamp
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "data": data
        }
        
        # Read existing history if file exists
        history = []
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                # If file is corrupted, start fresh
                logger.warning(f"Corrupted history file {history_file}, starting fresh")
                history = []
        
        # Append new entry
        history.append(entry)
        
        # Write back to file
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            logger.error(f"Error appending to webhook history: {e}")


class FileOperations:
    """Class for handling file operations"""
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """
        Ensure the specified directory exists
        Returns True if successful, False otherwise
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")
            return False
    
    @staticmethod
    def is_valid_media_file(file_path: str) -> bool:
        """
        Check if the file is a valid media file based on extension and size
        """
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size < Config.MIN_FILE_SIZE:
                return False
                
            # Check extension
            _, ext = os.path.splitext(file_path.lower())
            return ext in Config.get_supported_extensions()
        except Exception as e:
            logger.error(f"Error checking file {file_path}: {e}")
            return False
    
    @staticmethod
    def create_hardlink(source_file: str, destination_dir: str) -> bool:
        """
        Create a hardlink from source file to destination directory
        Returns True if successful, False otherwise
        """
        try:
            # Get basename of the source file
            file_name = os.path.basename(source_file)
            dest_file = os.path.join(destination_dir, file_name)
            
            # Skip if destination file already exists
            if os.path.exists(dest_file):
                return False
                
            # Try to create hardlink using os.link
            try:
                os.link(source_file, dest_file)
                logger.info(f"Created hardlink for {file_name}")
                return True
            except OSError as e:
                # If os.link fails (e.g., cross-filesystem), try using ln command
                import subprocess
                logger.warning(f"os.link failed, trying ln command: {e}")
                result = subprocess.run(['ln', source_file, dest_file], 
                                      capture_output=True, text=True)
                
                if result.returncode != 0:
                    # If hardlink fails, try copy as fallback
                    logger.error(f"Error creating hardlink: {result.stderr}")
                    logger.info(f"Trying copy instead for {source_file}")
                    subprocess.run(['cp', source_file, dest_file], check=True)
                
                return True
                
        except Exception as e:
            logger.error(f"Error creating hardlink for {source_file}: {e}")
            return False


class DownloadLocator:
    """Class for locating download folders and files"""
    
    @staticmethod
    def find_torrent_folder(download_id: str) -> Optional[str]:
        """
        Locate the folder where the torrent is being downloaded
        Returns the path if found, or None if not found
        
        This method will use qBittorrent API if enabled, otherwise
        it will use the traditional filesystem search.
        """
        # Try to use qBittorrent API first if enabled
        if Config.QBITTORRENT_ENABLED and Config.QBITTORRENT_USE_API:
            from app.services.qbittorrent import QBittorrentClient
            
            try:
                qbt = QBittorrentClient()
                path = qbt.get_torrent_download_path(download_id)
                
                if path:
                    logger.info(f"Found download path via qBittorrent API: {path}")
                    return path
                    
                # If API didn't find the path but torrent exists, get the default download path
                is_completed, info = qbt.get_torrent_status(download_id)
                if info:  # Torrent found but no specific path
                    logger.info(f"Using default download folder from qBittorrent API")
                    return Config.DOWNLOAD_PATH
            except Exception as e:
                logger.error(f"Error using qBittorrent API: {e}")
        
        # Fall back to filesystem search if API is disabled or failed
        logger.info("Using filesystem search to locate download folder")
        return DownloadLocator._find_torrent_folder_by_filesystem(download_id)
    
    @staticmethod
    def _find_torrent_folder_by_filesystem(download_id: str) -> Optional[str]:
        """
        Traditional filesystem search to locate torrent folder.
        This is used as a fallback when qBittorrent API is not available.
        """
        # Search for folder with the torrent hash as name or containing a .torrent file with that hash
        search_paths = [
            os.path.join(Config.DOWNLOAD_PATH, download_id),       # Direct folder match
            os.path.join(Config.DOWNLOAD_PATH, download_id.lower()) # Lowercase hash
        ]
        
        # Try to find an exact match first
        for path in search_paths:
            if os.path.exists(path) and os.path.isdir(path):
                logger.info(f"Found download folder by direct match: {path}")
                return path
                
        # Otherwise scan the downloads directory for matching folders
        try:
            logger.info(f"Searching for download {download_id} in {Config.DOWNLOAD_PATH}")
            for root, dirs, files in os.walk(Config.DOWNLOAD_PATH):
                for dir_name in dirs:
                    full_path = os.path.join(root, dir_name)
                    # Check if this might be our download (implementation depends on your naming scheme)
                    if download_id.lower() in dir_name.lower():
                        logger.info(f"Found download folder by partial match: {full_path}")
                        return full_path
                        
            # If still not found, return the base downloads path as a fallback
            logger.warning(f"Could not find specific folder for {download_id}, using base path")
            return Config.DOWNLOAD_PATH
        except Exception as e:
            logger.error(f"Error searching for download folder: {e}")
            return None
    
    @staticmethod
    def is_torrent_completed(download_id: str) -> bool:
        """
        Check if a torrent is completed using qBittorrent API
        
        Returns True if the torrent is completed, False otherwise.
        If qBittorrent API is disabled or fails, returns False.
        """
        if not Config.QBITTORRENT_ENABLED or not Config.QBITTORRENT_USE_API:
            logger.info("qBittorrent API disabled, cannot check torrent completion")
            return False
            
        try:
            from app.services.qbittorrent import QBittorrentClient
            qbt = QBittorrentClient()
            is_completed, _ = qbt.get_torrent_status(download_id)
            return is_completed
        except Exception as e:
            logger.error(f"Error checking torrent completion: {e}")
            return False 