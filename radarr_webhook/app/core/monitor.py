"""
Monitor module for tracking downloads and creating hardlinks.
Base implementation for both Radarr and Sonarr.
"""
import os
import time
import threading
import traceback
from typing import Dict, Any, Set, Type, List

from app.core.config import Config, logger
from app.core.models import DownloadInfo, ArrEvent
from app.core.storage import FileOperations, DownloadLocator, TorrentStorage


# Global storage for active downloads
active_downloads: Dict[str, DownloadInfo] = {}

# Initialize torrent storage
TorrentStorage.initialize()


class DownloadMonitor:
    """
    Base class for download monitoring functionality.
    Works with both Radarr and Sonarr events.
    """
    
    @staticmethod
    def handle_grab_event(event: ArrEvent) -> bool:
        """
        Handle a Grab event by starting to monitor the download
        and creating hardlinks for files as they appear.
        Returns True if monitoring started successfully, False otherwise.
        """
        # Validate event data
        if not event.should_monitor_download():
            logger.warning(f"Event not suitable for download monitoring: {event}")
            return False
        
        # Get required data
        download_id = event.download_id
        media_title = event.get_media_title()
        media_folder = event.get_media_folder()
        download_client = event.download_client
        
        if not media_folder:
            logger.warning(f"No media folder found for {media_title}")
            return False
        
        # Ensure the media folder exists
        if not FileOperations.ensure_directory_exists(media_folder):
            return False
        
        # Create download info object
        download_info = DownloadInfo(
            media_title=media_title,
            media_folder=media_folder,
            download_id=download_id,
            download_client=download_client
        )
        
        # Set media type based on event
        download_info.media_type = event.media_type
        
        # Try to get media ID
        media_id = None
        if hasattr(event, 'movie') and event.movie and hasattr(event.movie, 'id'):
            media_id = event.movie.id
        elif hasattr(event, 'series') and event.series and hasattr(event.series, 'id'):
            media_id = event.series.id
        download_info.media_id = media_id
        
        # Find torrent path
        torrent_path = DownloadLocator.find_torrent_folder(download_id)
        if torrent_path:
            download_info.torrent_path = torrent_path
            
            # Store torrent information for later use
            TorrentStorage.save_torrent_info(
                download_id=download_id,
                media_id=media_id,
                media_title=media_title,
                media_path=media_folder,
                torrent_path=torrent_path,
                media_type=event.media_type
            )
            
            # If we're using qBittorrent API, immediately try to process files
            if Config.QBITTORRENT_ENABLED and Config.QBITTORRENT_USE_API:
                logger.info(f"Attempting immediate file processing for {media_title}")
                try:
                    from app.services.qbittorrent import QBittorrentClient
                    qbt = QBittorrentClient()
                    
                    # Check if torrent already exists and has some files
                    is_completed, _ = qbt.get_torrent_status(download_id)
                    files = qbt.get_torrent_files(download_id)
                    
                    if files:
                        # Process files that are already available
                        DownloadMonitor.process_download_folder(download_id)
                        
                        # If torrent is already completed, no need to monitor
                        if is_completed:
                            logger.info(f"Torrent already completed, no monitoring needed for {media_title}")
                            return True
                except Exception as e:
                    logger.error(f"Error during immediate file processing: {e}")
        
        # Add to active downloads dictionary
        active_downloads[download_id] = download_info
        
        # Start monitoring in a separate thread
        thread = threading.Thread(
            target=DownloadMonitor.monitor_download,
            args=(download_id,),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started monitoring download for {media_title} (ID: {download_id})")
        return True
    
    @staticmethod
    def handle_download_event(event: ArrEvent) -> bool:
        """
        Handle a Download event by stopping monitoring if it was active
        """
        download_id = event.download_id
        if not download_id:
            return False
            
        if download_id in active_downloads:
            # Mark download as inactive to stop monitoring
            active_downloads[download_id].deactivate()
            logger.info(f"Download completed for {event.get_media_title()}, stopping monitor")
            return True
        
        return False
    
    @staticmethod
    def handle_delete_event(event: ArrEvent) -> bool:
        """
        Handle a delete event by removing the torrent and/or files
        """
        # Try to get the media ID from the event
        media_id = None
        if hasattr(event, 'movie') and event.movie and hasattr(event.movie, 'id'):
            media_id = event.movie.id
        elif hasattr(event, 'series') and event.series and hasattr(event.series, 'id'):
            media_id = event.series.id
        
        if not media_id:
            logger.warning("Delete event missing required media ID")
            return False
            
        # Find all torrents associated with this media
        found_torrents = []
        for torrent_hash, info in TorrentStorage.get_all_torrents().items():
            if info.get('media_id') == media_id:
                found_torrents.append(torrent_hash)
                
        if not found_torrents:
            logger.warning(f"No torrents found for media ID {media_id}")
            return False
            
        success = True
        for torrent_hash in found_torrents:
            torrent_info = TorrentStorage.get_torrent_info(torrent_hash)
            if not torrent_info:
                continue
                
            # Delete from qBittorrent if enabled
            if Config.QBITTORRENT_ENABLED and Config.QBITTORRENT_USE_API:
                from app.services.qbittorrent import QBittorrentClient
                qbt = QBittorrentClient()
                if not qbt.delete_torrent(torrent_hash, with_files=True):
                    success = False
            
            # Delete the torrent path if it exists and not already deleted by qBittorrent
            torrent_path = torrent_info.get('torrent_path')
            if torrent_path and os.path.exists(torrent_path):
                if not FileOperations.delete_file_or_folder(torrent_path):
                    success = False
            
            # Remove from storage
            TorrentStorage.delete_torrent_info(torrent_hash)
            
        return success
    
    @staticmethod
    def monitor_download(download_id: str) -> None:
        """
        Monitor a download and create hardlinks for new files as they appear
        """
        if download_id not in active_downloads:
            logger.error(f"Download ID {download_id} not found in active downloads")
            return
            
        download_info = active_downloads[download_id]
        logger.info(f"Starting monitor for {download_info.media_title} with ID {download_id}")
        
        check_count = 0
        
        # Monitor until the download is marked inactive or max checks reached
        while (download_info.active and 
               check_count < Config.MAX_MONITOR_CHECKS):
            
            check_count += 1
            
            # Check if torrent is completed via qBittorrent API
            if Config.QBITTORRENT_ENABLED and Config.QBITTORRENT_USE_API:
                if DownloadLocator.is_torrent_completed(download_id):
                    logger.info(f"Torrent {download_id} is completed according to qBittorrent API")
                    # Process one last time to catch final files
                    torrent_folder = DownloadLocator.find_torrent_folder(download_id)
                    if torrent_folder:
                        DownloadMonitor.process_download_folder(download_id)
                    # Mark as inactive and stop monitoring
                    download_info.deactivate()
                    break
            
            # Get torrent folder
            torrent_folder = DownloadLocator.find_torrent_folder(download_id)
            
            if not torrent_folder:
                logger.warning(f"Could not locate torrent folder for {download_id}")
                time.sleep(30)  # Wait before next check
                continue
                
            logger.info(f"Check #{check_count}: Scanning {torrent_folder} for new files")
            
            try:
                DownloadMonitor.process_download_folder(download_id)
            except Exception as e:
                logger.error(f"Error processing download folder: {e}")
                
            # Update last check time
            download_info.update_check_time()
            
            # Sleep before next check
            time.sleep(Config.MONITOR_INTERVAL)
        
        # Log completion
        if check_count >= Config.MAX_MONITOR_CHECKS:
            logger.info(f"Reached maximum check count for {download_info.media_title}, stopping monitor")
        else:
            logger.info(f"Finished monitoring for {download_info.media_title}")
        
        # Remove from active downloads
        if download_id in active_downloads:
            active_downloads.pop(download_id)
    
    @staticmethod
    def process_download_folder(download_id: str) -> None:
        """
        Process a folder after download completion
        
        Args:
            download_id: The download ID
        """
        try:
            # Get download details from storage
            download_info = active_downloads.get(download_id)
            if not download_info:
                logger.warning(f"No download info found for download {download_id}, cannot process")
                return

            logger.info(f"Processing download folder for '{download_info.media_title}' ({download_id})")
            
            # Make sure the download path exists
            if not os.path.exists(download_info.download_path):
                logger.error(f"Download path does not exist: {download_info.download_path}")
                return
                
            # Get list of files to process
            all_files = DownloadLocator.get_download_files(download_id)
            total_files = len(all_files)
            processed_count = 0
            skipped_count = 0
            not_exists_count = 0
            
            logger.info(f"Found {total_files} files in torrent '{download_info.media_title}'")
            
            # Process each file
            for file_item in all_files:
                source_file = file_item["absolutePath"]
                relative_path = file_item["relativePath"]
                
                # Skip if not a media file
                if not DownloadMonitor._should_process_file(source_file, download_info.media_type):
                    skipped_count += 1
                    continue
                    
                # Skip if source file doesn't exist yet
                if not os.path.exists(source_file):
                    not_exists_count += 1
                    continue
                
                # Create hardlink to the library folder
                library_path = DownloadMonitor._get_library_path(download_info)
                success = DownloadMonitor._create_hardlink_with_structure(source_file, library_path, relative_path)
                if success:
                    processed_count += 1
            
            # Log summary
            logger.info(f"Torrent '{download_info.media_title}': Processed {processed_count}/{total_files} files")
            if skipped_count > 0:
                logger.info(f"Torrent '{download_info.media_title}': Skipped {skipped_count} non-media files")
            if not_exists_count > 0:
                logger.warning(f"Torrent '{download_info.media_title}': {not_exists_count} files do not exist yet, will retry later")
                
        except Exception as e:
            logger.error(f"Error processing download folder: {e}")
            traceback.print_exc()
    
    @staticmethod
    def _create_hardlink_with_structure(source_file: str, dest_base_dir: str, relative_path: str) -> bool:
        """
        Create a hardlink maintaining the directory structure from the torrent.
        
        Args:
            source_file: Full path to the source file
            dest_base_dir: Base destination directory
            relative_path: Relative path within the torrent
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create destination directory structure
            dest_file = os.path.join(dest_base_dir, relative_path)
            dest_dir = os.path.dirname(dest_file)
            
            # Ensure the directory exists
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
                
            # Skip if destination file already exists
            if os.path.exists(dest_file):
                return True
            
            # Try to create hardlink
            try:
                os.link(source_file, dest_file)
                return True
            except OSError as e:
                # If os.link fails (e.g., cross-filesystem), try using ln command
                import subprocess
                logger.debug(f"os.link failed for {os.path.basename(source_file)}, trying ln command: {e}")
                result = subprocess.run(['ln', source_file, dest_file], 
                                      capture_output=True, text=True)
                
                if result.returncode != 0:
                    # If hardlink fails, try copy as fallback
                    logger.warning(f"Error creating hardlink for {os.path.basename(source_file)}")
                    logger.debug(f"Trying copy instead for {os.path.basename(source_file)}")
                    subprocess.run(['cp', source_file, dest_file], check=True)
                
                return True
                
        except Exception as e:
            logger.error(f"Error creating hardlink for {os.path.basename(source_file)}: {e}")
            return False
    
    @staticmethod
    def get_active_downloads_status() -> Dict[str, Any]:
        """
        Return status information about all active downloads
        """
        status = {}
        for download_id, info in active_downloads.items():
            # Check if we have qBittorrent information for this download
            qbt_info = {}
            if Config.QBITTORRENT_ENABLED and Config.QBITTORRENT_USE_API:
                try:
                    from app.services.qbittorrent import QBittorrentClient
                    qbt = QBittorrentClient()
                    is_completed, torrent_info = qbt.get_torrent_status(download_id)
                    if torrent_info:
                        qbt_info = {
                            "progress": torrent_info.get("progress", 0) * 100,
                            "state": torrent_info.get("state", "unknown"),
                            "completed": is_completed,
                            "name": torrent_info.get("name", "Unknown")
                        }
                except Exception as e:
                    logger.error(f"Error getting qBittorrent status: {e}")
                    
            # Build the status object
            status[download_id] = {
                "media_title": info.media_title,
                "media_folder": info.media_folder,
                "media_type": info.media_type,
                "download_client": info.download_client,
                "first_seen": info.first_seen,
                "last_check": info.last_check,
                "processed_files_count": len(info.processed_files),
                "qbittorrent": qbt_info
            }
        return status
    
    @staticmethod
    def check_torrent(torrent_hash: str) -> Dict[str, Any]:
        """
        Check the status of a specific torrent
        
        Args:
            torrent_hash: The hash of the torrent to check
            
        Returns:
            Dictionary with information about the torrent
        """
        result = {
            "found": False,
            "completed": False,
            "progress": 0,
            "state": "unknown",
            "files": [],
            "being_monitored": torrent_hash in active_downloads
        }
        
        # Check if torrent is being monitored
        if torrent_hash in active_downloads:
            info = active_downloads[torrent_hash]
            result.update({
                "found": True,
                "media_title": info.media_title,
                "media_folder": info.media_folder,
                "media_type": info.media_type,
                "download_client": info.download_client,
                "first_seen": info.first_seen,
                "last_check": info.last_check,
                "processed_files_count": len(info.processed_files)
            })
        
        # Check stored information
        stored_info = TorrentStorage.get_torrent_info(torrent_hash)
        if stored_info:
            result.update({
                "found": True,
                "stored_info": {
                    "media_id": stored_info.get("media_id"),
                    "media_title": stored_info.get("media_title"),
                    "media_path": stored_info.get("media_path"),
                    "torrent_path": stored_info.get("torrent_path"),
                    "media_type": stored_info.get("media_type"),
                    "added_date": stored_info.get("added_date")
                }
            })
        
        # Check qBittorrent status if enabled
        if Config.QBITTORRENT_ENABLED and Config.QBITTORRENT_USE_API:
            try:
                from app.services.qbittorrent import QBittorrentClient
                qbt = QBittorrentClient()
                
                # Get torrent status
                is_completed, torrent_info = qbt.get_torrent_status(torrent_hash)
                if torrent_info:
                    result.update({
                        "found": True,
                        "completed": is_completed,
                        "progress": torrent_info.get("progress", 0) * 100,
                        "state": torrent_info.get("state", "unknown"),
                        "name": torrent_info.get("name", "Unknown"),
                        "size": torrent_info.get("size", 0),
                        "download_path": torrent_info.get("save_path", "Unknown"),
                    })
                    
                    # Get files in torrent
                    files = qbt.get_torrent_files(torrent_hash)
                    if files:
                        result["files"] = files
            except Exception as e:
                logger.error(f"Error checking torrent status: {e}")
        
        return result 