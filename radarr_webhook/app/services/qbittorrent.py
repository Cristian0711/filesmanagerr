"""
qBittorrent client module for interfacing with qBittorrent.
"""
import qbittorrentapi
from typing import Dict, Any, Optional, List, Tuple
import os

from app.core.config import Config, logger


class QBittorrentClient:
    """
    Client for interacting with qBittorrent WebUI API
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QBittorrentClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the qBittorrent client connection"""
        self.client = qbittorrentapi.Client(
            host=Config.QBITTORRENT_HOST,
            port=Config.QBITTORRENT_PORT,
            username=Config.QBITTORRENT_USERNAME,
            password=Config.QBITTORRENT_PASSWORD,
            VERIFY_WEBUI_CERTIFICATE=False
        )
        
        # Test connection
        try:
            self.client.auth_log_in()
            qbt_version = self.client.app.version
            logger.info(f"Connected to qBittorrent {qbt_version}")
            self.connected = True
        except Exception as e:
            logger.error(f"Failed to connect to qBittorrent: {e}")
            self.connected = False
    
    def get_torrent_status(self, torrent_hash: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get the status of a torrent by hash
        
        Args:
            torrent_hash: The hash of the torrent to check
            
        Returns:
            Tuple of (is_finished, torrent_info)
            is_finished is True if the torrent has completed, otherwise False
            torrent_info is a dictionary with details about the torrent
        """
        if not self.connected:
            logger.warning("qBittorrent client not connected")
            return False, {}
        
        try:
            # Normalize the hash (qBittorrent expects lowercase)
            torrent_hash = torrent_hash.lower()
            
            # Get torrent info
            torrent = self.client.torrents_info(hashes=torrent_hash)
            
            if not torrent:
                logger.warning(f"Torrent {torrent_hash} not found in qBittorrent")
                return False, {}
            
            # Get the first (and only) torrent in the list
            torrent_info = torrent[0]
            
            # Check if torrent is completed
            is_completed = torrent_info.progress == 1.0 and torrent_info.state in [
                "uploading", "pausedUP", "queuedUP", "stalledUP", "forcedUP", "checkingUP"
            ]
            
            # Create a dictionary with torrent information
            info = {
                "hash": torrent_info.hash,
                "name": torrent_info.name,
                "progress": torrent_info.progress,
                "state": torrent_info.state,
                "size": torrent_info.size,
                "content_path": torrent_info.content_path,
                "download_path": torrent_info.download_path,
                "save_path": torrent_info.save_path,
                "completed": is_completed
            }
            
            logger.info(f"Torrent {torrent_hash} status: {info['state']} ({info['progress']*100:.1f}%)")
            return is_completed, info
            
        except Exception as e:
            logger.error(f"Error checking torrent status: {e}")
            return False, {}
    
    def get_torrent_files(self, torrent_hash: str) -> List[Dict[str, Any]]:
        """
        Get the list of files in a torrent
        
        Args:
            torrent_hash: The hash of the torrent to check
            
        Returns:
            List of files in the torrent, each as a dictionary with file details
        """
        if not self.connected:
            logger.warning("qBittorrent client not connected")
            return []
        
        try:
            # Normalize the hash (qBittorrent expects lowercase)
            torrent_hash = torrent_hash.lower()
            
            # Get files in torrent
            files = self.client.torrents_files(torrent_hash=torrent_hash)
            
            if not files:
                logger.warning(f"No files found for torrent {torrent_hash}")
                return []
            
            # Create a simplified file list
            file_list = []
            for f in files:
                file_list.append({
                    "name": f.name,
                    "size": f.size,
                    "progress": f.progress,
                    "priority": f.priority,
                    "is_seed": f.is_seed,
                    "piece_range": f.piece_range,
                    "availability": f.availability
                })
            
            return file_list
            
        except Exception as e:
            logger.error(f"Error getting torrent files: {e}")
            return []
    
    def get_torrent_download_path(self, torrent_hash: str) -> Optional[str]:
        """
        Get the download path of a torrent
        
        Args:
            torrent_hash: The hash of the torrent to check
            
        Returns:
            Path where the torrent is being downloaded, or None if not found
        """
        _, info = self.get_torrent_status(torrent_hash)
        
        if not info:
            return None
        
        # Try different path attributes, as they can vary by qBittorrent version
        for path_attr in ['content_path', 'save_path']:
            if path_attr in info and info[path_attr]:
                path = info[path_attr]
                # If it's just save_path, we need to append the torrent name
                if path_attr == 'save_path' and 'name' in info:
                    path = os.path.join(path, info['name'])
                return path
        
        return None
    
    def delete_torrent(self, torrent_hash: str, with_files: bool = False) -> bool:
        """
        Delete a torrent from qBittorrent
        
        Args:
            torrent_hash: The hash of the torrent to delete
            with_files: If True, also delete downloaded files
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.warning("qBittorrent client not connected")
            return False
        
        try:
            # Normalize the hash
            torrent_hash = torrent_hash.lower()
            
            # Get torrent info first to log what we're deleting
            _, info = self.get_torrent_status(torrent_hash)
            if not info:
                logger.warning(f"Torrent {torrent_hash} not found for deletion")
                return False
                
            torrent_name = info.get('name', 'Unknown')
            
            # Delete the torrent
            self.client.torrents_delete(delete_files=with_files, hashes=torrent_hash)
            
            action = "and files " if with_files else ""
            logger.info(f"Deleted torrent {action}for {torrent_name} (ID: {torrent_hash})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting torrent {torrent_hash}: {e}")
            return False 