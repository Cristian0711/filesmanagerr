"""
Models for data received from Radarr webhooks.

These classes are used to structure data received from Radarr
and facilitate access to information in notifications.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Set


class Movie:
    """Model for a movie from Radarr"""
    
    def __init__(self, data: Dict[str, Any] = None):
        data = data or {}
        self.id = data.get('id')
        self.title = data.get('title', 'Unknown')
        self.year = data.get('year')
        self.release_date = data.get('physicalRelease')
        self.folder_path = data.get('folderPath')
        self.tmdb_id = data.get('tmdbId')
        self.imdb_id = data.get('imdbId')
        self.overview = data.get('overview')
        self.genres = data.get('genres', [])
        
        # Extract poster URL from images
        self.poster = None
        images = data.get('images', [])
        for image in images:
            if image.get('coverType') == 'poster':
                self.poster = image.get('url')
                break
        
        # Additional properties
        self.quality = self._extract_quality(data)
        self.tags = data.get('tags', [])
        self.original_language = self._extract_language(data)
    
    def _extract_quality(self, data: Dict[str, Any]) -> str:
        """Extract quality information from movie data"""
        if 'quality' in data and 'quality' in data['quality']:
            return data['quality']['quality'].get('name', 'Unknown')
        return 'Unknown'
    
    def _extract_language(self, data: Dict[str, Any]) -> str:
        """Extract language information from movie data"""
        if 'originalLanguage' in data and 'name' in data['originalLanguage']:
            return data['originalLanguage']['name']
        return 'Unknown'
    
    def __str__(self) -> str:
        return f"{self.title} ({self.year})"


class RemoteMovie:
    """Model for remote movie information"""
    
    def __init__(self, data: Dict[str, Any] = None):
        data = data or {}
        self.title = data.get('title', 'Unknown')
        self.year = data.get('year')
        self.tmdb_id = data.get('tmdbId')
        self.imdb_id = data.get('imdbId')
        
        # Extract quality if available
        self.quality = 'Unknown'
        if 'quality' in data and 'quality' in data['quality']:
            self.quality = data['quality']['quality'].get('name', 'Unknown')
    
    def __str__(self) -> str:
        return f"{self.title} ({self.year})"


class Release:
    """Model for release information"""
    
    def __init__(self, data: Dict[str, Any] = None):
        data = data or {}
        self.quality = data.get('quality', 'Unknown')
        self.quality_version = data.get('qualityVersion')
        self.release_group = data.get('releaseGroup')
        self.release_title = data.get('releaseTitle')
        self.indexer = data.get('indexer')
        self.size = data.get('size')
        self.languages = self._extract_languages(data)
        self.custom_format_score = data.get('customFormatScore')
        self.custom_formats = data.get('customFormats', [])
        self.indexer_flags = data.get('indexerFlags', [])
    
    def _extract_languages(self, data: Dict[str, Any]) -> List[str]:
        """Extract language information from release data"""
        languages = []
        if 'languages' in data:
            for lang in data['languages']:
                if 'name' in lang:
                    languages.append(lang['name'])
        return languages
    
    def __str__(self) -> str:
        return self.release_title or 'Unknown Release'


class DownloadInfo:
    """Class for tracking download progress and hardlinking operations"""
    
    def __init__(self, movie_title: str, movie_folder: str, download_id: str, download_client: str):
        self.movie_title = movie_title
        self.movie_folder = movie_folder
        self.download_id = download_id
        self.download_client = download_client
        self.active = True
        self.first_seen = datetime.now().isoformat()
        self.last_check = datetime.now().isoformat()
        self.processed_files: Set[str] = set()
    
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


class RadarrEvent:
    """Main model for Radarr events"""
    
    def __init__(self, data: Dict[str, Any] = None):
        data = data or {}
        self.event_type = data.get('eventType')
        self.instance_name = data.get('instanceName', 'Radarr')
        self.application_url = data.get('applicationUrl')
        
        # Create objects for movie, remote movie, and release
        self.movie = Movie(data.get('movie')) if data.get('movie') else None
        self.remote_movie = RemoteMovie(data.get('remoteMovie')) if data.get('remoteMovie') else None
        self.release = Release(data.get('release')) if data.get('release') else None
        
        # Download specific information
        self.is_upgrade = data.get('isUpgrade', False)
        self.download_client = data.get('downloadClient')
        self.download_id = data.get('downloadId')
        self.download_client_type = data.get('downloadClientType')
        self.import_mode = data.get('importMode')
        
        # Raw data for access to uncovered fields
        self.raw_data = data
    
    def __str__(self) -> str:
        movie_title = self.movie.title if self.movie else "Unknown"
        return f"{self.event_type} - {movie_title}"
    
    def get_event_description(self) -> str:
        """Returns a description for the event"""
        if self.event_type == 'Test':
            return "Test webhook received from Radarr"
            
        elif self.event_type == 'Grab':
            title = self.remote_movie.title if self.remote_movie else "Unknown"
            quality = self.release.quality if self.release else "Unknown"
            return f"Movie scheduled for download: {title} (Quality: {quality})"
            
        elif self.event_type == 'Download':
            title = self.movie.title if self.movie else "Unknown"
            is_upgrade = "upgrade" if self.is_upgrade else "new download"
            return f"Movie downloaded: {title} ({is_upgrade})"
            
        elif self.event_type == 'Rename':
            title = self.movie.title if self.movie else "Unknown"
            return f"Movie renamed: {title}"
            
        else:
            return f"Unknown event: {self.event_type}"
    
    def should_monitor_download(self) -> bool:
        """Determine if we should monitor this download for hardlinking"""
        return (
            self.event_type == 'Grab' and 
            self.download_id is not None and 
            self.download_client is not None and 
            self.movie is not None and 
            self.movie.folder_path is not None
        ) 