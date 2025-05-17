"""
Models for data received from Sonarr webhooks.

These classes are used to structure data received from Sonarr
and facilitate access to information in notifications.
"""
from typing import Dict, Any, Optional, List

from app.core.models import MediaItem, RemoteMedia, ArrEvent, Release


class Series(MediaItem):
    """Model for a series from Sonarr"""
    
    def __init__(self, data: Dict[str, Any] = None):
        super().__init__(data)
        data = data or {}
        self.title_slug = data.get('titleSlug')
        self.tvdb_id = data.get('tvdbId')
        self.imdb_id = data.get('imdbId')
        self.overview = data.get('overview')
        self.series_type = data.get('seriesType', 'standard')
        self.year = data.get('year')
        self.path = data.get('path')  # synonym for folder_path
        
        # Extract poster URL from images
        self.poster = None
        images = data.get('images', [])
        for image in images:
            if image.get('coverType') == 'poster':
                self.poster = image.get('url')
                break
    
    def __str__(self) -> str:
        return f"{self.title} ({self.year or 'Unknown Year'})"


class Episode(MediaItem):
    """Model for an episode from Sonarr"""
    
    def __init__(self, data: Dict[str, Any] = None):
        super().__init__(data)
        data = data or {}
        self.episode_number = data.get('episodeNumber')
        self.season_number = data.get('seasonNumber')
        self.air_date = data.get('airDate')
        self.air_date_utc = data.get('airDateUtc')
        self.quality = data.get('quality')
        self.quality_version = data.get('qualityVersion')
        self.scene_episode_number = data.get('sceneEpisodeNumber')
        self.scene_season_number = data.get('sceneSeasonNumber')
        self.absolute_episode_number = data.get('absoluteEpisodeNumber')
        self.series_id = data.get('seriesId')
        
        # File information
        if data.get('episodeFile'):
            self.file_path = data.get('episodeFile', {}).get('path')
            self.quality = data.get('episodeFile', {}).get('quality', {}).get('quality', {}).get('name')
        else:
            self.file_path = None
            self.quality = None
    
    def __str__(self) -> str:
        return f"S{self.season_number:02d}E{self.episode_number:02d} - {self.title}"


class RemoteEpisode(RemoteMedia):
    """Model for remote episode information"""
    
    def __init__(self, data: Dict[str, Any] = None):
        super().__init__(data)
        data = data or {}
        
        # Store episodes information
        self.episodes: List[Episode] = []
        if 'episodes' in data:
            for episode_data in data['episodes']:
                self.episodes.append(Episode(episode_data))
        
        # Extract series title
        if 'series' in data:
            self.series_title = data['series'].get('title', 'Unknown Series')
        else:
            self.series_title = 'Unknown Series'
    
    def __str__(self) -> str:
        if self.episodes:
            return f"{self.series_title} - {len(self.episodes)} episode(s)"
        return self.series_title


class SonarrEvent(ArrEvent):
    """Model for Sonarr-specific events"""
    
    def __init__(self, data: Dict[str, Any] = None):
        super().__init__(data)
        
        # Create objects for series, episode and remote episode
        self.series = Series(data.get('series')) if data.get('series') else None
        self.episodes = []
        if data.get('episodes'):
            for episode_data in data.get('episodes', []):
                self.episodes.append(Episode(episode_data))
        
        self.remote_episode = RemoteEpisode(data.get('remoteEpisode')) if data.get('remoteEpisode') else None
        
        # Set media type
        self.media_type = "series"
    
    def get_media_title(self) -> str:
        """Get the title of the series involved in this event"""
        if self.series:
            if self.episodes:
                episode_info = f"S{self.episodes[0].season_number:02d}E{self.episodes[0].episode_number:02d}"
                if len(self.episodes) > 1:
                    return f"{self.series.title} - {episode_info} (+{len(self.episodes)-1})"
                return f"{self.series.title} - {episode_info}"
            return self.series.title
        elif self.remote_episode:
            return self.remote_episode.series_title
        return "Unknown Series"
    
    def get_media_folder(self) -> Optional[str]:
        """Get the folder path where the series should be stored"""
        if self.series:
            return self.series.folder_path or self.series.path
        return None
    
    def get_event_description(self) -> str:
        """Returns a description for the event"""
        if self.event_type == 'Test':
            return "Test webhook received from Sonarr"
            
        elif self.event_type == 'Grab':
            title = self.get_media_title()
            return f"Episode(s) scheduled for download: {title}"
            
        elif self.event_type == 'Download':
            title = self.get_media_title()
            is_upgrade = "upgrade" if self.is_upgrade else "new download"
            return f"Episode(s) downloaded: {title} ({is_upgrade})"
            
        elif self.event_type == 'EpisodeFileDelete':
            title = self.get_media_title()
            return f"Episode file deleted: {title}"
            
        elif self.event_type == 'SeriesDelete':
            title = self.series.title if self.series else "Unknown"
            return f"Series deleted: {title}"
            
        elif self.event_type == 'Rename':
            title = self.series.title if self.series else "Unknown"
            return f"Series renamed: {title}"
            
        else:
            return f"Unknown event: {self.event_type}" 