"""
Base models for the application.
These classes provide common structures used across both Radarr and Sonarr.
"""
from datetime import datetime
from typing import Dict, Any, Set, Optional, List


class MediaItem:
    """Base class for media items (movies, series, episodes)"""
    
    def __init__(self, data: Dict[str, Any] = None):
        data = data or {}
        self.id = data.get('id')
        self.title = data.get('title', 'Unknown')
        self.folder_path = data.get('folderPath')
        self.tags = data.get('tags', [])
    
    def __str__(self) -> str:
        return self.title


class RemoteMedia:
    """Base class for remote media information (not yet downloaded)"""
    
    def __init__(self, data: Dict[str, Any] = None):
        data = data or {}
        self.title = data.get('title', 'Unknown')
    
    def __str__(self) -> str:
        return self.title


class Release:
    """Model for media release information"""
    
    def __init__(self, data: Dict[str, Any] = None):
        data = data or {}
        self.quality = data.get('quality', 'Unknown')
        self.quality_version = data.get('qualityVersion')
        self.release_group = data.get('releaseGroup')
        self.release_title = data.get('releaseTitle')
        self.indexer = data.get('indexer')
        self.size = data.get('size')
        self.custom_format_score = data.get('customFormatScore')
        self.custom_formats = data.get('customFormats', [])
        self.indexer_flags = data.get('indexerFlags', [])
        self._languages = []
        self._extract_languages(data)
    
    def _extract_languages(self, data: Dict[str, Any]) -> None:
        """Extract language information from release data"""
        if 'languages' in data:
            for lang in data['languages']:
                if 'name' in lang:
                    self._languages.append(lang['name'])
    
    @property
    def languages(self) -> List[str]:
        return self._languages
    
    def __str__(self) -> str:
        return self.release_title or 'Unknown Release'


class ArrEvent:
    """Base class for all *Arr application events"""
    
    def __init__(self, data: Dict[str, Any] = None):
        data = data or {}
        self.event_type = data.get('eventType')
        self.instance_name = data.get('instanceName', 'Unknown')
        self.application_url = data.get('applicationUrl')
        
        # Download specific information
        self.is_upgrade = data.get('isUpgrade', False)
        self.download_client = data.get('downloadClient')
        self.download_id = data.get('downloadId')
        self.download_client_type = data.get('downloadClientType')
        self.import_mode = data.get('importMode')
        
        # Release information
        self.release = Release(data.get('release')) if data.get('release') else None
        
        # Set media type (to be overridden by subclasses)
        self.media_type = "unknown"
        
        # Raw data for access to uncovered fields
        self.raw_data = data
    
    def get_media_title(self) -> str:
        """
        Get the title of the media involved in this event.
        Must be implemented by subclasses.
        """
        return "Unknown Media"
    
    def get_media_folder(self) -> Optional[str]:
        """
        Get the folder path where the media should be stored.
        Must be implemented by subclasses.
        """
        return None
    
    def should_monitor_download(self) -> bool:
        """
        Determine if we should monitor this download for hardlinking.
        Base implementation checks for common requirements.
        """
        return (
            self.event_type == 'Grab' and 
            self.download_id is not None and 
            self.download_client is not None and 
            self.get_media_folder() is not None
        )
    
    def __str__(self) -> str:
        return f"{self.event_type} - {self.get_media_title()}"


class DownloadInfo:
    """Class for tracking download progress and hardlinking operations"""
    
    def __init__(self, media_title: str, media_folder: str, download_id: str, download_client: str):
        self.media_title = media_title
        self.media_folder = media_folder
        self.download_id = download_id
        self.download_client = download_client
        self.active = True
        self.first_seen = datetime.now().isoformat()
        self.last_check = datetime.now().isoformat()
        self.processed_files: Set[str] = set()
        self.media_type = "unknown"  # Will be set to "movie" or "series"
        
        # New fields for torrent management
        self.torrent_path = None
        self.media_id = None
        self.should_delete_files = False
        self.should_delete_torrent = False
    
    def update_check_time(self):
        """Update the last check timestamp"""
        self.last_check = datetime.now().isoformat()
    
    def add_processed_file(self, file_path: str):
        """Add a file to the processed files set"""
        self.processed_files.add(file_path)
    
    def is_file_processed(self, file_path: str) -> bool:
        """Check if a file has already been processed"""
        return file_path in self.processed_files
    
    def deactivate(self):
        """Mark this download as inactive"""
        self.active = False 