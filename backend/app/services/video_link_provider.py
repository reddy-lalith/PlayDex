"""
Video Link Provider Module
Provides links to official NBA videos without storing content
"""
from typing import Dict, Optional
from urllib.parse import quote
from nba_api.stats.endpoints import videoevents


class VideoLinkProvider:
    """Provides links to official NBA videos without storing content"""
    
    def get_official_video_link(self, game_id: str, event_id: int) -> Dict:
        """
        Get official NBA video information without storing
        """
        try:
            # Get video metadata from nba_api
            video_event = videoevents.VideoEvents(
                game_id=game_id, 
                game_event_id=event_id
            )
            video_data = video_event.get_dict()
            
            # Extract thumbnails and metadata
            if video_data['resultSets']['Meta']['videoUrls']:
                video_meta = video_data['resultSets']['Meta']['videoUrls'][0]
                uuid = video_meta.get('uuid', '')
                thumbnails = {
                    'small': video_meta.get('stp', ''),   # 320x180
                    'medium': video_meta.get('mtp', ''),  # 576x324
                    'large': video_meta.get('ltp', '')    # 1280x720
                }
            else:
                uuid = ''
                thumbnails = {'small': '', 'medium': '', 'large': ''}
            
            # Get play description
            play_description = ''
            if video_data['resultSets']['playlist']:
                play_description = video_data['resultSets']['playlist'][0].get('dsc', '')
            
            # Generate official NBA links (no direct video URLs)
            return {
                'uuid': uuid,
                'thumbnails': thumbnails,
                'official_links': {
                    'nba_stats': f"https://www.nba.com/stats/events/?flag=1&GameID={game_id}&GameEventID={event_id}",
                    'nba_game': f"https://www.nba.com/game/{game_id}",
                    'youtube_search': self.generate_youtube_search_url(play_description)
                },
                'play_description': play_description
            }
        
        except Exception as e:
            print(f"Error getting video links: {e}")
            # Return fallback links
            return {
                'uuid': '',
                'thumbnails': {'small': '', 'medium': '', 'large': ''},
                'official_links': {
                    'nba_stats': f"https://www.nba.com/stats/events/?flag=1&GameID={game_id}&GameEventID={event_id}",
                    'nba_game': f"https://www.nba.com/game/{game_id}",
                    'youtube_search': "https://youtube.com/c/NBA"
                },
                'play_description': 'Play information unavailable'
            }
    
    def generate_youtube_search_url(self, description: str) -> str:
        """
        Generate YouTube search URL for official NBA channel
        """
        if not description:
            return "https://youtube.com/c/NBA"
        
        # Clean up description and add NBA official context
        search_query = f"NBA {description} official"
        encoded_query = quote(search_query)
        
        return f"https://youtube.com/results?search_query={encoded_query}"