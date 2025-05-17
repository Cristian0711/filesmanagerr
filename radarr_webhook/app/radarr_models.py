"""
Models for data received from Radarr webhooks.

These classes are used to structure data received from Radarr
and facilitate access to information in notifications.
"""

class Movie:
    """Model for a movie from Radarr"""
    
    def __init__(self, data=None):
        data = data or {}
        self.id = data.get('id')
        self.title = data.get('title')
        self.year = data.get('year')
        self.release_date = data.get('physicalRelease')
        self.folder_path = data.get('folderPath')
        self.tmdb_id = data.get('tmdbId')
        self.imdb_id = data.get('imdbId')
        self.overview = data.get('overview')
        self.poster = data.get('images', [{}])[0].get('url') if data.get('images') else None
        self.quality = data.get('quality', {}).get('quality', {}).get('name')
        self.tags = data.get('tags', [])
        
    def __str__(self):
        return f"{self.title} ({self.year})"


class RemoteMovie:
    """Model for remote movie information"""
    
    def __init__(self, data=None):
        data = data or {}
        self.title = data.get('title')
        self.year = data.get('year')
        self.tmdb_id = data.get('tmdbId')
        self.imdb_id = data.get('imdbId')
        self.quality = data.get('quality', {}).get('quality', {}).get('name')
        
    def __str__(self):
        return f"{self.title} ({self.year})"


class RadarrEvent:
    """Main model for Radarr events"""
    
    def __init__(self, data=None):
        data = data or {}
        self.event_type = data.get('eventType')
        self.instance_name = data.get('instanceName', 'Radarr')
        self.application_url = data.get('applicationUrl')
        
        # Create objects for movie
        self.movie = Movie(data.get('movie')) if data.get('movie') else None
        self.remote_movie = RemoteMovie(data.get('remoteMovie')) if data.get('remoteMovie') else None
        
        # Download specific information
        self.is_upgrade = data.get('isUpgrade', False)
        self.download_client = data.get('downloadClient')
        self.download_id = data.get('downloadId')
        self.import_mode = data.get('importMode')
        
        # Raw data for access to uncovered fields
        self.raw_data = data
        
    def __str__(self):
        movie_title = self.movie.title if self.movie else "Unknown"
        return f"{self.event_type} - {movie_title}"
        
    def get_event_description(self):
        """Returns a description for the event"""
        if self.event_type == 'Test':
            return "Test webhook received from Radarr"
            
        elif self.event_type == 'Grab':
            title = self.remote_movie.title if self.remote_movie else "Unknown"
            return f"Movie scheduled for download: {title}"
            
        elif self.event_type == 'Download':
            title = self.movie.title if self.movie else "Unknown"
            is_upgrade = "upgrade" if self.is_upgrade else "new download"
            return f"Movie downloaded: {title} ({is_upgrade})"
            
        elif self.event_type == 'Rename':
            title = self.movie.title if self.movie else "Unknown"
            return f"Movie renamed: {title}"
            
        else:
            return f"Unknown event: {self.event_type}" 