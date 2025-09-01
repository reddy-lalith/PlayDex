"""
Search Engine Module
Queries sports APIs and returns filtered clips with links
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from nba_api.stats.endpoints import playbyplayv2, leaguegamefinder
from nba_api.stats.static import players, teams
from app.models.search import (
    SearchResult, SearchResultMetadata, VideoLinks, 
    PlayData, Player, ExtractedEntities
)
from app.services.video_link_provider import VideoLinkProvider
import uuid as uuid_lib


class SearchEngine:
    """Queries sports APIs and returns filtered clips"""
    
    def __init__(self):
        self.video_provider = VideoLinkProvider()
        # Cache for player and team data
        self._players_cache = None
        self._teams_cache = None
    
    def search_clips(self, entities: ExtractedEntities) -> List[SearchResult]:
        """
        Search for clips based on extracted parameters
        """
        results = []
        
        # Get recent games based on search criteria
        games = self._get_relevant_games(entities)
        
        if not games:
            return results
        
        # For each game, get play-by-play data
        for game in games[:5]:  # Limit to 5 games for MVP
            game_id = game['GAME_ID']
            game_date = game.get('GAME_DATE', '')
            home_team = game.get('TEAM_NAME', '')
            visitor_team = game.get('MATCHUP', '').split(' @ ')[-1] if ' @ ' in game.get('MATCHUP', '') else ''
            
            # Get play-by-play data
            plays = self._get_game_plays(game_id, entities)
            
            # Convert plays to search results
            for play in plays:
                if play.get('EVENTNUM'):  # Only plays with video
                    # Get video links
                    video_data = self.video_provider.get_official_video_link(
                        game_id=game_id,
                        event_id=play['EVENTNUM']
                    )
                    
                    # Create search result
                    result = self._create_search_result(
                        play=play,
                        video_data=video_data,
                        game_date=game_date,
                        teams=[home_team, visitor_team]
                    )
                    
                    if result:
                        results.append(result)
        
        return results
    
    def _get_relevant_games(self, entities: ExtractedEntities) -> List[Dict]:
        """Get games based on search criteria"""
        try:
            # Set date range based on time_range or season
            if entities.time_range == "last week":
                date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                date_to = datetime.now().strftime('%Y-%m-%d')
            elif entities.time_range == "last month":
                date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                date_to = datetime.now().strftime('%Y-%m-%d')
            elif entities.season:
                # Handle season format (e.g., "2022-23")
                year = entities.season.split('-')[0]
                date_from = f"{year}-10-01"  # NBA season typically starts in October
                date_to = f"{int(year)+1}-06-30"  # Ends in June
            else:
                # Default to last 3 months for better results
                date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                date_to = datetime.now().strftime('%Y-%m-%d')
            
            # Find games
            if entities.player_id:
                # Get games for specific player
                gamefinder = leaguegamefinder.LeagueGameFinder(
                    player_id_nullable=entities.player_id,
                    date_from_nullable=date_from,
                    date_to_nullable=date_to,
                    league_id_nullable='00'  # NBA
                )
            else:
                # If no player specified, get recent games
                # This is less useful, so we'll return empty
                return []
            
            games_df = gamefinder.get_data_frames()[0]
            if games_df.empty:
                return []
                
            # Convert to records and limit to recent games
            games = games_df.head(10).to_dict('records')  # Limit to 10 most recent games
            return games
            
        except Exception as e:
            print(f"Error getting games: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_game_plays(self, game_id: str, entities: ExtractedEntities) -> List[Dict]:
        """Get play-by-play data for a game"""
        try:
            pbp = playbyplayv2.PlayByPlayV2(game_id=game_id)
            plays = pbp.get_data_frames()[0].to_dict('records')
            
            # Filter plays based on entities
            filtered_plays = []
            for play in plays:
                # Check if play matches search criteria
                if self._play_matches_criteria(play, entities):
                    filtered_plays.append(play)
            
            return filtered_plays
            
        except Exception as e:
            print(f"Error getting plays: {e}")
            return []
    
    def _play_matches_criteria(self, play: Dict, entities: ExtractedEntities) -> bool:
        """Check if a play matches the search criteria"""
        description = (play.get('HOMEDESCRIPTION', '') or '') + ' ' + (play.get('VISITORDESCRIPTION', '') or '')
        description_lower = description.lower()
        
        # Check player
        if entities.player and entities.player.lower() not in description_lower:
            return False
        
        # Check action
        if entities.action:
            action_keywords = {
                'dunk': ['dunk', 'slam'],
                'block': ['block'],
                'three': ['3pt', '3-pt', 'three'],
                'steal': ['steal'],
                'assist': ['assist']
            }
            
            if entities.action in action_keywords:
                if not any(keyword in description_lower for keyword in action_keywords[entities.action]):
                    return False
        
        return True
    
    def _create_search_result(self, play: Dict, video_data: Dict, game_date: str, teams: List[str]) -> Optional[SearchResult]:
        """Create a SearchResult from play data"""
        try:
            # Extract play description
            description = play.get('HOMEDESCRIPTION') or play.get('VISITORDESCRIPTION') or video_data.get('play_description', '')
            
            if not description:
                return None
            
            # Create play data
            play_data = PlayData(
                GAME_ID=play.get('GAME_ID', ''),
                EVENTNUM=play.get('EVENTNUM', 0),
                PERIOD=play.get('PERIOD', 0),
                PCTIMESTRING=play.get('PCTIMESTRING', ''),
                HOMEDESCRIPTION=play.get('HOMEDESCRIPTION'),
                VISITORDESCRIPTION=play.get('VISITORDESCRIPTION'),
                SCORE=play.get('SCORE'),
                SCOREMARGIN=play.get('SCOREMARGIN')
            )
            
            # Create video links
            video_links = VideoLinks(
                nba_stats=video_data['official_links']['nba_stats'],
                nba_game=video_data['official_links']['nba_game'],
                youtube_search=video_data['official_links']['youtube_search']
            )
            
            # Extract players from description (simplified)
            players = []
            # This would be more sophisticated in production
            
            # Create metadata
            metadata = SearchResultMetadata(
                date=datetime.strptime(game_date, '%Y-%m-%d') if game_date else datetime.now(),
                gameId=play.get('GAME_ID', ''),
                teams=teams,
                quarter=play.get('PERIOD', 0),
                timeRemaining=play.get('PCTIMESTRING', ''),
                players=players,
                action=self._extract_action_from_description(description)
            )
            
            # Create search result
            return SearchResult(
                id=str(uuid_lib.uuid4()),
                playData=play_data,
                previewThumbnail=video_data['thumbnails']['large'] or '/api/placeholder/320/180',
                watchLinks=video_links,
                description=description,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Error creating search result: {e}")
            return None
    
    def _extract_action_from_description(self, description: str) -> str:
        """Extract the primary action from play description"""
        description_lower = description.lower()
        
        if 'dunk' in description_lower or 'slam' in description_lower:
            return 'dunk'
        elif 'block' in description_lower:
            return 'block'
        elif '3pt' in description_lower or 'three' in description_lower:
            return 'three'
        elif 'steal' in description_lower:
            return 'steal'
        elif 'assist' in description_lower:
            return 'assist'
        else:
            return 'play'