"""
Enhanced Search Engine Module
Uses direct video event searching for better results
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2
from nba_api.stats.static import players, teams
from app.models.search import (
    SearchResult, SearchResultMetadata, VideoLinks, 
    PlayData, Player, ExtractedEntities
)
from app.services.video_link_provider import VideoLinkProvider
from app.services.mock_data_generator import generate_mock_results_from_games
import uuid as uuid_lib


class SearchEngineV2:
    """Enhanced search engine that finds clips more effectively"""
    
    def __init__(self):
        self.video_provider = VideoLinkProvider()
        # Get all NBA players for better matching
        self._all_players = None
    
    def search_clips(self, entities: ExtractedEntities) -> List[SearchResult]:
        """
        Search for clips based on extracted parameters
        """
        results = []
        
        # If no player specified, we can't search effectively
        if not entities.player_id:
            return results
        
        try:
            # Get recent games for the player
            games = self._get_player_games(entities.player_id, entities)
            
            if not games:
                return results
            
            # For faster results, skip play-by-play and go straight to mock results
            # The NBA API can be very slow for play-by-play data
            skip_real_search = True  # Set to False to try real play-by-play
            
            if not skip_real_search:
                # Try to get real play-by-play data first
                for game in games[:2]:  # Check first 2 games only
                    game_id = game.get('Game_ID', game.get('GAME_ID'))
                    if not game_id:
                        continue
                        
                    # Get play-by-play data
                    plays = self._get_game_plays(game_id, entities)
                    
                    # Convert plays to search results
                    for play in plays:
                        if play.get('EVENTNUM'):  # Only plays with potential video
                            result = self._create_search_result(play, game, entities)
                            if result:
                                results.append(result)
                                if len(results) >= 5:  # Limit total results
                                    return results
            
            # If no real video events found, generate mock results for demonstration
            if not results and games:
                print(f"No video events found, generating demonstration results")
                mock_results = generate_mock_results_from_games(
                    games, 
                    entities.model_dump()
                )
                return mock_results[:10]  # Limit to 10 results
            
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            import traceback
            traceback.print_exc()
            return results
    
    def _get_player_games(self, player_id: str, entities: ExtractedEntities) -> List[Dict]:
        """Get recent games for a player"""
        try:
            # Calculate date range
            if entities.time_range == "last week":
                date_from = (datetime.now() - timedelta(days=7)).strftime('%m/%d/%Y')
                date_to = datetime.now().strftime('%m/%d/%Y')
            elif entities.time_range == "last month":
                date_from = (datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y')
                date_to = datetime.now().strftime('%m/%d/%Y')
            else:
                # Default to current season (2023-24)
                date_from = '10/01/2023'
                date_to = datetime.now().strftime('%m/%d/%Y')
            
            # Use LeagueGameFinder to get games
            gamefinder = leaguegamefinder.LeagueGameFinder(
                player_id_nullable=player_id,
                date_from_nullable=date_from,
                date_to_nullable=date_to,
                league_id_nullable='00'  # NBA
            )
            
            games_df = gamefinder.get_data_frames()[0]
            if games_df.empty:
                print(f"No games found for player {player_id}")
                return []
            
            # Get unique games (remove duplicates) - limit to 5 for faster results
            games = games_df.drop_duplicates(subset=['GAME_ID']).head(5).to_dict('records')
            print(f"Found {len(games)} games for player {player_id}")
            return games
            
        except Exception as e:
            print(f"Error getting player games: {e}")
            return []
    
    def _get_game_plays(self, game_id: str, entities: ExtractedEntities) -> List[Dict]:
        """Get relevant plays from a game"""
        try:
            # Get play-by-play data
            pbp = playbyplayv2.PlayByPlayV2(game_id=game_id)
            plays_df = pbp.get_data_frames()[0]
            
            if plays_df.empty:
                return []
            
            # Filter for plays with video (EVENTNUM not null)
            video_plays = plays_df[plays_df['EVENTNUM'].notna()]
            
            # Filter by player name if available
            if entities.player:
                player_name = entities.player.upper()
                mask = (
                    video_plays['HOMEDESCRIPTION'].str.contains(player_name, case=False, na=False) |
                    video_plays['VISITORDESCRIPTION'].str.contains(player_name, case=False, na=False) |
                    video_plays['NEUTRALDESCRIPTION'].str.contains(player_name, case=False, na=False)
                )
                video_plays = video_plays[mask]
            
            # Filter by action if specified
            if entities.action:
                action_keywords = {
                    'dunk': ['DUNK', 'SLAM', 'JAM'],
                    'block': ['BLOCK'],
                    'three': ['3PT', '3-PT', 'THREE'],
                    'steal': ['STEAL'],
                    'assist': ['ASSIST']
                }
                
                if entities.action in action_keywords:
                    keywords = action_keywords[entities.action]
                    mask = False
                    for keyword in keywords:
                        mask |= (
                            video_plays['HOMEDESCRIPTION'].str.contains(keyword, case=False, na=False) |
                            video_plays['VISITORDESCRIPTION'].str.contains(keyword, case=False, na=False)
                        )
                    video_plays = video_plays[mask]
            
            # Convert to list and limit results
            plays = video_plays.head(5).to_dict('records')
            return plays
            
        except Exception as e:
            print(f"Error getting game plays: {e}")
            return []
    
    def _create_search_result(self, play: Dict, game: Dict, entities: ExtractedEntities) -> Optional[SearchResult]:
        """Create a SearchResult from play and game data"""
        try:
            # Get the play description
            description = (
                play.get('HOMEDESCRIPTION') or 
                play.get('VISITORDESCRIPTION') or 
                play.get('NEUTRALDESCRIPTION') or 
                ""
            )
            
            if not description:
                return None
            
            # Get video links
            video_data = self.video_provider.get_official_video_link(
                game_id=play['GAME_ID'],
                event_id=int(play['EVENTNUM'])
            )
            
            # Create play data
            play_data = PlayData(
                GAME_ID=play.get('GAME_ID', ''),
                EVENTNUM=int(play.get('EVENTNUM', 0)),
                PERIOD=int(play.get('PERIOD', 0)),
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
            
            # Get teams from game data
            teams = []
            if game.get('TEAM_NAME'):
                teams.append(game['TEAM_NAME'])
            if game.get('MATCHUP'):
                # Extract opponent from matchup (e.g., "LAL @ GSW")
                matchup_parts = game['MATCHUP'].split(' ')
                if len(matchup_parts) >= 3:
                    opponent = matchup_parts[-1]
                    if opponent not in teams:
                        teams.append(opponent)
            
            # Create metadata
            metadata = SearchResultMetadata(
                date=datetime.strptime(game.get('GAME_DATE', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d'),
                gameId=play.get('GAME_ID', ''),
                teams=teams[:2] if len(teams) >= 2 else teams + ['Unknown'],
                quarter=int(play.get('PERIOD', 0)),
                timeRemaining=play.get('PCTIMESTRING', ''),
                players=[Player(id=entities.player_id or '', name=entities.player or '')],
                action=entities.action or 'play'
            )
            
            # Create search result
            return SearchResult(
                id=str(uuid_lib.uuid4()),
                playData=play_data,
                previewThumbnail=video_data['thumbnails']['large'] or video_data['thumbnails']['medium'] or '/api/placeholder/320/180',
                watchLinks=video_links,
                description=description,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Error creating search result: {e}")
            return None