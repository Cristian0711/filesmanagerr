"""
Storage module for handling persistence of webhook data,
file operations, and other storage-related functionality.
"""
import os
import json
import pickle
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
import sys

from app.core.config import Config, logger


class TorrentStorage:
    """
    Class to manage persistent storage of torrent information
    """
    _storage_file = None  # Will be set in initialize
    _torrents = {}  # hash -> {metadata}
    
    @classmethod
    def initialize(cls):
        """Initialize the torrent storage system"""
        # Use the config directory for storage
        config_dir = os.getenv('CONFIG_DIR', 'config')
        
        # Make sure the config directory exists
        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, mode=0o777, exist_ok=True)
            else:
                # Ensure it's writable
                os.chmod(config_dir, 0o777)
        except Exception as e:
            print(f"Error configuring config directory {config_dir}: {e}", file=sys.stderr)
            # Fall back to current directory
            config_dir = '.'
            print(f"Falling back to current directory for config", file=sys.stderr)
        
        # Set the storage file path
        cls._storage_file = os.path.join(config_dir, "torrents.pickle")
        print(f"Torrent storage file location: {os.path.abspath(cls._storage_file)}", file=sys.stderr)
        
        # Try to load existing data
        if os.path.exists(cls._storage_file):
            try:
                with open(cls._storage_file, 'rb') as f:
                    cls._torrents = pickle.load(f)
                logger.info(f"Loaded {len(cls._torrents)} torrents from storage")
                print(f"Loaded {len(cls._torrents)} torrents from storage", file=sys.stderr)
            except Exception as e:
                logger.error(f"Error loading torrent storage: {e}")
                print(f"Error loading torrent storage: {e}", file=sys.stderr)
                cls._torrents = {}
        else:
            print(f"No existing torrent storage file found at {cls._storage_file}", file=sys.stderr)
    
    @classmethod
    def save_torrent_info(cls, download_id: str, media_id: int, media_title: str, 
                         media_path: str, torrent_path: str, media_type: str):
        """
        Save torrent information for later use
        
        Args:
            download_id: Torrent hash
            media_id: Radarr/Sonarr media ID
            media_title: Title of the media
            media_path: Path where media is stored
            torrent_path: Path where torrent files are downloaded
            media_type: Type of media ("movie" or "series")
        """
        cls._torrents[download_id] = {
            'media_id': media_id,
            'media_title': media_title,
            'media_path': media_path,
            'torrent_path': torrent_path,
            'media_type': media_type,
            'added_date': datetime.now().isoformat()
        }
        cls._save_to_disk()
        logger.info(f"Stored torrent info for {media_title} (ID: {download_id})")
    
    @classmethod
    def get_torrent_info(cls, download_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stored information about a torrent
        
        Args:
            download_id: Torrent hash
            
        Returns:
            Dictionary with torrent information or None if not found
        """
        return cls._torrents.get(download_id)
    
    @classmethod
    def delete_torrent_info(cls, download_id: str) -> bool:
        """
        Remove a torrent from storage
        
        Args:
            download_id: Torrent hash
            
        Returns:
            True if torrent was found and removed, False otherwise
        """
        if download_id in cls._torrents:
            media_title = cls._torrents[download_id].get('media_title', 'Unknown')
            del cls._torrents[download_id]
            cls._save_to_disk()
            logger.info(f"Removed torrent info for {media_title} (ID: {download_id})")
            return True
        return False
    
    @classmethod
    def get_all_torrents(cls) -> Dict[str, Dict[str, Any]]:
        """Get all stored torrents"""
        return cls._torrents
    
    @classmethod
    def _save_to_disk(cls):
        """Save the torrent dictionary to disk"""
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(cls._storage_file), exist_ok=True)
            
            # Use atomic writing pattern to prevent corruption
            temp_file = cls._storage_file + '.tmp'
            with open(temp_file, 'wb') as f:
                pickle.dump(cls._torrents, f)
            
            # Replace the old file with the new one
            if os.path.exists(cls._storage_file):
                os.remove(cls._storage_file)
            os.rename(temp_file, cls._storage_file)
            
            # Report success
            print(f"Successfully saved {len(cls._torrents)} torrents to {cls._storage_file}", file=sys.stderr)
        except Exception as e:
            logger.error(f"Error saving torrent storage: {e}")
            print(f"Error saving torrent storage to {cls._storage_file}: {e}", file=sys.stderr)


class WebhookStorage:
    """Class for managing webhook data persistence"""
    
    @staticmethod
    def save_latest_webhook(data: Dict[str, Any]) -> None:
        """Save the most recent webhook data to a file"""
        try:
            # Use the config directory
            config_dir = os.getenv('CONFIG_DIR', 'config')
            os.makedirs(config_dir, exist_ok=True)
            
            file_path = os.path.join(config_dir, 'last_webhook_data.json')
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Saved latest webhook data to {file_path}", file=sys.stderr)
        except Exception as e:
            logger.error(f"Error saving latest webhook data: {e}")
            print(f"Error saving latest webhook data: {e}", file=sys.stderr)
    
    @staticmethod
    def append_to_history(data: Dict[str, Any]) -> None:
        """
        Append webhook data to history file with timestamp
        """
        # Use the config directory
        config_dir = os.getenv('CONFIG_DIR', 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        # Override the history file location to use config dir
        history_file = os.path.join(config_dir, os.path.basename(Config.WEBHOOK_LOG_FILE))
        
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
                print(f"Corrupted history file {history_file}, starting fresh", file=sys.stderr)
                history = []
        
        # Append new entry
        history.append(entry)
        
        # Write back to file
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=4)
            print(f"Updated webhook history at {history_file}", file=sys.stderr)
        except Exception as e:
            logger.error(f"Error appending to webhook history: {e}")
            print(f"Error appending to webhook history: {e}", file=sys.stderr)


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
    def ensure_parent_directory_exists(file_path: str) -> bool:
        """
        Ensure the parent directory of a file exists
        Returns True if successful, False otherwise
        """
        try:
            parent_dir = os.path.dirname(file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating parent directory for {file_path}: {e}")
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
                
            # Ensure the destination directory exists
            FileOperations.ensure_directory_exists(destination_dir)
                
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
    
    @staticmethod
    def delete_file_or_folder(path: str) -> bool:
        """
        Delete a file or folder
        Returns True if successful, False otherwise
        """
        try:
            if os.path.isfile(path):
                os.remove(path)
                logger.info(f"Deleted file: {path}")
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
                logger.info(f"Deleted directory: {path}")
            else:
                logger.warning(f"Path not found for deletion: {path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error deleting path {path}: {e}")
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
        Traditional filesystem search to locate torrent folder or file.
        This is used as a fallback when qBittorrent API is not available.
        """
        # Search for folder with the torrent hash as name or containing a .torrent file with that hash
        search_paths = [
            os.path.join(Config.DOWNLOAD_PATH, download_id),       # Direct folder match
            os.path.join(Config.DOWNLOAD_PATH, download_id.lower()) # Lowercase hash
        ]
        
        # Try to find an exact match first
        for path in search_paths:
            if os.path.exists(path):
                if os.path.isdir(path):
                    logger.info(f"Found download folder by direct match: {path}")
                    return path
                elif os.path.isfile(path):
                    logger.info(f"Found download file by direct match: {path}")
                    return path
                
        # Otherwise scan the downloads directory for matching folders and files
        try:
            logger.info(f"Searching for download {download_id} in {Config.DOWNLOAD_PATH}")
            
            # Search for files first
            for root, _, files in os.walk(Config.DOWNLOAD_PATH):
                for file_name in files:
                    # Check if filename contains the hash
                    if download_id.lower() in file_name.lower():
                        file_path = os.path.join(root, file_name)
                        logger.info(f"Found download file by partial match: {file_path}")
                        return file_path
            
            # Then search for folders
            for root, dirs, _ in os.walk(Config.DOWNLOAD_PATH):
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