"""
Monitor module for tracking downloads and creating hardlinks.
"""
import os
import time
import threading
from typing import Dict, Any, Set

from app.config import Config, logger
from app.models import DownloadInfo, RadarrEvent
from app.storage import FileOperations, DownloadLocator


# Global storage for active downloads
active_downloads: Dict[str, DownloadInfo] = {}


def handle_grab_event(event: RadarrEvent) -> bool:
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
    movie_title = event.movie.title
    movie_folder = event.movie.folder_path
    download_client = event.download_client
    
    # Ensure the movie folder exists
    if not FileOperations.ensure_directory_exists(movie_folder):
        return False
    
    # Create download info object
    download_info = DownloadInfo(
        movie_title=movie_title,
        movie_folder=movie_folder,
        download_id=download_id,
        download_client=download_client
    )
    
    # Add to active downloads dictionary
    active_downloads[download_id] = download_info
    
    # Start monitoring in a separate thread
    thread = threading.Thread(
        target=monitor_download,
        args=(download_id,),
        daemon=True
    )
    thread.start()
    
    logger.info(f"Started monitoring download for {movie_title} (ID: {download_id})")
    return True


def handle_download_event(event: RadarrEvent) -> bool:
    """
    Handle a Download event by stopping monitoring if it was active
    """
    download_id = event.download_id
    if not download_id:
        return False
        
    if download_id in active_downloads:
        # Mark download as inactive to stop monitoring
        active_downloads[download_id].deactivate()
        logger.info(f"Download completed for {event.movie.title if event.movie else 'Unknown'}, stopping monitor")
        return True
    
    return False


def monitor_download(download_id: str) -> None:
    """
    Monitor a download and create hardlinks for new files as they appear
    """
    if download_id not in active_downloads:
        logger.error(f"Download ID {download_id} not found in active downloads")
        return
        
    download_info = active_downloads[download_id]
    logger.info(f"Starting monitor for {download_info.movie_title} with ID {download_id}")
    
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
                    process_download_folder(torrent_folder, download_info)
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
            process_download_folder(torrent_folder, download_info)
        except Exception as e:
            logger.error(f"Error processing download folder: {e}")
            
        # Update last check time
        download_info.update_check_time()
        
        # Sleep before next check
        time.sleep(Config.MONITOR_INTERVAL)
    
    # Log completion
    if check_count >= Config.MAX_MONITOR_CHECKS:
        logger.info(f"Reached maximum check count for {download_info.movie_title}, stopping monitor")
    else:
        logger.info(f"Finished monitoring for {download_info.movie_title}")
    
    # Remove from active downloads
    if download_id in active_downloads:
        active_downloads.pop(download_id)


def process_download_folder(folder_path: str, download_info: DownloadInfo) -> None:
    """
    Process all files in the download folder and create hardlinks for new files
    """
    # Get all files in the folder and its subfolders
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            source_file = os.path.join(root, file_name)
            
            # Skip already processed files
            if download_info.is_file_processed(source_file):
                continue
                
            # Check if this is a file we should process
            if FileOperations.is_valid_media_file(source_file):
                # Create hardlink
                if FileOperations.create_hardlink(source_file, download_info.movie_folder):
                    # Mark as processed
                    download_info.add_processed_file(source_file)
                    logger.info(f"Processed {file_name} for {download_info.movie_title}")


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
                from app.qbt_client import QBittorrentClient
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
            "movie_title": info.movie_title,
            "movie_folder": info.movie_folder,
            "download_client": info.download_client,
            "first_seen": info.first_seen,
            "last_check": info.last_check,
            "processed_files_count": len(info.processed_files),
            "qbittorrent": qbt_info
        }
    return status


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
            "movie_title": info.movie_title,
            "movie_folder": info.movie_folder,
            "download_client": info.download_client,
            "first_seen": info.first_seen,
            "last_check": info.last_check,
            "processed_files_count": len(info.processed_files)
        })
    
    # Check qBittorrent status if enabled
    if Config.QBITTORRENT_ENABLED and Config.QBITTORRENT_USE_API:
        try:
            from app.qbt_client import QBittorrentClient
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