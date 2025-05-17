"""
Models for data received from Radarr webhooks.

These classes are used to structure data received from Radarr
and facilitate access to information in notifications.
"""
from typing import Dict, Any, Optional

from app.core.models import ArrEvent, MediaItem, RemoteMedia


class Movie(MediaItem):
    """Model for a movie from Radarr"""
    
    def __init__(self, data: Dict[str, Any] = None):
        super().__init__(data)
        data = data or {}
        self.year = data.get('year')
        self.release_date = data.get('physicalRelease')
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
    
    def _extract_quality(self, data: Dict[str, Any]) -> str:
        """Extract quality information from movie data"""
        if 'quality' in data and 'quality' in data['quality']:
            return data['quality']['quality'].get('name', 'Unknown')
        return 'Unknown'
    
    def __str__(self) -> str:
        return f"{self.title} ({self.year or 'Unknown Year'})"


class RemoteMovie(RemoteMedia):
    """Model for remote movie information"""
    
    def __init__(self, data: Dict[str, Any] = None):
        super().__init__(data)
        data = data or {}
        self.year = data.get('year')
        self.tmdb_id = data.get('tmdbId')
        self.imdb_id = data.get('imdbId')
        
        # Extract quality if available
        self.quality = 'Unknown'
        if 'quality' in data and 'quality' in data['quality']:
            self.quality = data['quality']['quality'].get('name', 'Unknown')
    
    def __str__(self) -> str:
        return f"{self.title} ({self.year or 'Unknown Year'})"


class RadarrEvent(ArrEvent):
    """Model for Radarr-specific events"""
    
    def __init__(self, data: Dict[str, Any] = None):
        super().__init__(data)
        
        # Create objects for movie and remote movie
        self.movie = Movie(data.get('movie')) if data.get('movie') else None
        self.remote_movie = RemoteMovie(data.get('remoteMovie')) if data.get('remoteMovie') else None
        
        # Set media type
        self.media_type = "movie"
    
    def get_media_title(self) -> str:
        """Get the title of the movie involved in this event"""
        if self.event_type == "Grab" and self.remote_movie:
            return self.remote_movie.title
        elif self.movie:
            return self.movie.title
        return "Unknown Movie"
    
    def get_media_folder(self) -> Optional[str]:
        """Get the folder path where the movie should be stored"""
        if self.movie and self.movie.folder_path:
            return self.movie.folder_path
        return None
    
    def get_event_description(self) -> str:
        """Returns a description for the event"""
        if self.event_type == 'Test':
            return "Test webhook received from Radarr"
            
        elif self.event_type == 'Grab':
            title = self.get_media_title()
            return f"Movie scheduled for download: {title}"
            
        elif self.event_type == 'Download':
            title = self.get_media_title()
            is_upgrade = "upgrade" if self.is_upgrade else "new download"
            return f"Movie downloaded: {title} ({is_upgrade})"
            
        elif self.event_type == 'MovieFileDelete':
            title = self.get_media_title()
            return f"Movie file deleted: {title}"
            
        elif self.event_type == 'Rename':
            title = self.get_media_title()
            return f"Movie renamed: {title}"
            
        else:
            return f"Unknown event: {self.event_type}" 