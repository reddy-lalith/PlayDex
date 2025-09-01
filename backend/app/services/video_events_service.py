"""
Service to fetch actual video URLs using the videoeventsasset endpoint
"""
import requests
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class VideoEventsService:
    """Service to fetch video URLs from NBA Stats API"""
    
    def __init__(self):
        self.headers = {
            'Host': 'stats.nba.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true',
            'Connection': 'keep-alive',
            'Referer': 'https://stats.nba.com/',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
    
    def get_video_url(self, game_id: str, event_id: int) -> Optional[Dict[str, str]]:
        """
        Get video URL for a specific game event
        
        Args:
            game_id: NBA game ID
            event_id: Event number within the game
            
        Returns:
            Dict with 'video' URL and 'desc' description, or None if not found
        """
        try:
            url = f'https://stats.nba.com/stats/videoeventsasset?GameEventID={event_id}&GameID={game_id}'
            
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            
            json_data = response.json()
            
            # Extract video URLs and playlist info
            result_sets = json_data.get('resultSets', {})
            video_urls = result_sets.get('Meta', {}).get('videoUrls', [])
            playlist = result_sets.get('playlist', [])
            
            if video_urls and playlist:
                # Get the highest quality video URL available
                video_url = None
                if video_urls[0].get('lurl'):  # Large resolution
                    video_url = video_urls[0]['lurl']
                elif video_urls[0].get('murl'):  # Medium resolution
                    video_url = video_urls[0]['murl']
                elif video_urls[0].get('surl'):  # Small resolution
                    video_url = video_urls[0]['surl']
                
                if video_url:
                    logger.info(f"Found video URL for game {game_id}, event {event_id}: {video_url}")
                    return {
                        'video': video_url,
                        'desc': playlist[0].get('dsc', 'No description available')
                    }
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching video URL for game {game_id}, event {event_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None