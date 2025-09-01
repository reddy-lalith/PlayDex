"""
Efficient search implementation inspired by ballharbor
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2
from nba_api.stats.endpoints import videoeventsasset
from app.models.search import (
    SearchResult, SearchResultMetadata, VideoLinks, 
    PlayData, Player, ExtractedEntities
)
import uuid as uuid_lib
import requests


class EfficientSearch:
    """Efficient search using ballharbor's approach - simpler and more reliable"""
    
    def __init__(self):
        self.timeout = 10
        self.max_games_per_search = 10  # Much lower limit
    
    def search_clips(self, entities: ExtractedEntities, limit: int = 15, offset: int = 0) -> List[SearchResult]:
        """Search for clips with a focus on reliability over completeness"""
        results = []
        
        if not entities.player_id:
            print("No player ID found")
            return results
        
        try:
            # Get games - but limit the scope significantly
            if entities.season:
                # For specific season, get a sample of games
                games = self._get_season_sample(entities.player_id, entities.season)
            else:
                # For recent games, get last 5-10 games
                games = self._get_recent_games(entities.player_id)
            
            if not games:
                print("No games found")
                return results
            
            print(f"Searching {len(games)} games for clips...")
            
            # Process games sequentially with delays
            for idx, game in enumerate(games):
                if len(results) >= limit * 3:  # Get 3x results then paginate
                    break
                
                # Add delay between games
                if idx > 0:
                    time.sleep(1)
                
                game_results = self._process_game(game, entities)
                results.extend(game_results)
            
            # Sort by date and paginate
            results.sort(key=lambda x: x.metadata.date, reverse=True)
            return results[offset:offset + limit]
            
        except Exception as e:
            print(f"Error in efficient search: {e}")
            return []
    
    def _get_recent_games(self, player_id: str) -> List[Dict]:
        """Get player's most recent games"""
        try:
            # Get games from last 30 days
            date_from = (datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y')
            
            gamefinder = leaguegamefinder.LeagueGameFinder(
                player_id_nullable=player_id,
                date_from_nullable=date_from,
                timeout=self.timeout
            )
            
            games_df = gamefinder.get_data_frames()[0]
            
            if games_df.empty:
                # Try current season without date filter
                gamefinder = leaguegamefinder.LeagueGameFinder(
                    player_id_nullable=player_id,
                    season_nullable='2024-25',
                    timeout=self.timeout
                )
                games_df = gamefinder.get_data_frames()[0]
            
            # Return at most 10 games
            return games_df.head(self.max_games_per_search).to_dict('records')
            
        except Exception as e:
            print(f"Error getting games: {e}")
            return []
    
    def _get_season_sample(self, player_id: str, season: str) -> List[Dict]:
        """Get a sample of games from a specific season"""
        try:
            gamefinder = leaguegamefinder.LeagueGameFinder(
                player_id_nullable=player_id,
                season_nullable=season,
                timeout=self.timeout
            )
            
            games_df = gamefinder.get_data_frames()[0]
            
            if games_df.empty:
                return []
            
            # For buzzer beaters, try to get more games but still limit
            if hasattr(self, 'current_search_type') and self.current_search_type == 'buzzer_beater':
                # Get games spread throughout the season
                total_games = len(games_df)
                if total_games > 20:
                    # Sample every Nth game
                    step = total_games // 20
                    games_df = games_df.iloc[::step].head(20)
                else:
                    games_df = games_df.head(20)
            else:
                # For regular searches, just get recent games
                games_df = games_df.head(self.max_games_per_search)
            
            return games_df.to_dict('records')
            
        except Exception as e:
            print(f"Error getting season games: {e}")
            return []
    
    def _process_game(self, game: Dict, entities: ExtractedEntities) -> List[SearchResult]:
        """Process a single game for relevant plays"""
        results = []
        game_id = game.get('GAME_ID', '')
        
        try:
            # Get play-by-play data
            pbp = playbyplayv2.PlayByPlayV2(game_id=game_id, timeout=self.timeout)
            plays_df = pbp.get_data_frames()[0]
            
            # Filter for player
            player_plays = plays_df[
                plays_df['PLAYER1_ID'] == int(entities.player_id)
            ]
            
            if player_plays.empty:
                return results
            
            # Apply filters based on action
            if entities.action_detail == "buzzer beater":
                # Buzzer beater filter
                time_mask = (
                    player_plays['PCTIMESTRING'].str.match(r'^0:0[0-1]$', na=False) |
                    player_plays['PCTIMESTRING'].str.match(r'^0:[0-1]\.\d+$', na=False)
                )
                player_plays = player_plays[time_mask]
                
                # Filter out misses
                player_plays = player_plays[
                    ~player_plays['HOMEDESCRIPTION'].str.contains('MISS', case=False, na=False) &
                    ~player_plays['VISITORDESCRIPTION'].str.contains('MISS', case=False, na=False)
                ]
            
            elif entities.action:
                # Action-based filtering
                action_keywords = {
                    'dunk': 'DUNK',
                    'three': '3PT',
                    'block': 'BLOCK',
                    'steal': 'STEAL'
                }
                
                if entities.action in action_keywords:
                    keyword = action_keywords[entities.action]
                    player_plays = player_plays[
                        player_plays['HOMEDESCRIPTION'].str.contains(keyword, case=False, na=False) |
                        player_plays['VISITORDESCRIPTION'].str.contains(keyword, case=False, na=False)
                    ]
                    
                    # Filter out misses for shots
                    if entities.action in ['dunk', 'three']:
                        player_plays = player_plays[
                            ~player_plays['HOMEDESCRIPTION'].str.contains('MISS', case=False, na=False) &
                            ~player_plays['VISITORDESCRIPTION'].str.contains('MISS', case=False, na=False)
                        ]
            
            # Create results for matching plays (limit per game)
            for _, play in player_plays.head(3).iterrows():
                result = self._create_result(play, game, entities)
                if result:
                    results.append(result)
            
        except Exception as e:
            print(f"Error processing game {game_id}: {e}")
        
        return results
    
    def _create_result(self, play: Dict, game: Dict, entities: ExtractedEntities) -> Optional[SearchResult]:
        """Create a search result from play data"""
        try:
            game_id = game.get('GAME_ID', '')
            event_num = play['EVENTNUM']
            
            # Try to get video URL using videoeventsasset
            video_url = None
            try:
                video_asset = videoeventsasset.VideoEventsAsset(
                    game_id=game_id,
                    game_event_id=event_num,
                    timeout=5
                )
                video_data = video_asset.get_dict()
                
                # Extract video URL from response
                if 'resultSets' in video_data and 'Meta' in video_data['resultSets']:
                    meta = video_data['resultSets']['Meta']
                    if 'videoUrls' in meta and len(meta['videoUrls']) > 0:
                        video_url = meta['videoUrls'][0].get('lurl')  # Low quality URL
            except:
                # Video URL fetch failed, continue without it
                pass
            
            # Create result
            description = play['HOMEDESCRIPTION'] or play['VISITORDESCRIPTION'] or ''
            
            return SearchResult(
                id=str(uuid_lib.uuid4()),
                playData=PlayData(
                    GAME_ID=game_id,
                    EVENTNUM=event_num,
                    PERIOD=play['PERIOD'],
                    PCTIMESTRING=play['PCTIMESTRING'],
                    HOMEDESCRIPTION=play['HOMEDESCRIPTION'] or '',
                    VISITORDESCRIPTION=play['VISITORDESCRIPTION'] or '',
                    SCORE=play.get('SCORE', ''),
                    SCOREMARGIN=play.get('SCOREMARGIN', '')
                ),
                previewThumbnail="/api/placeholder/320/180",
                watchLinks=VideoLinks(
                    nba_stats=f"https://www.nba.com/stats/events/?GameID={game_id}&GameEventID={event_num}",
                    nba_video=video_url,
                    nba_game=f"https://www.nba.com/game/{game_id}",
                    youtube_search=f"https://youtube.com/results?search_query=NBA+{entities.player}+{entities.action or 'highlights'}"
                ),
                description=f"{description} - {game.get('MATCHUP', '')} ({game.get('GAME_DATE', '')})",
                metadata=SearchResultMetadata(
                    date=datetime.strptime(game.get('GAME_DATE', ''), '%Y-%m-%d') if game.get('GAME_DATE') else datetime.now(),
                    gameId=game_id,
                    teams=self._parse_teams(game.get('MATCHUP', '')),
                    quarter=play['PERIOD'],
                    timeRemaining=play['PCTIMESTRING'],
                    players=[Player(id=entities.player_id, name=entities.player or '')],
                    action=entities.action or 'play'
                )
            )
            
        except Exception as e:
            print(f"Error creating result: {e}")
            return None
    
    def _parse_teams(self, matchup: str) -> List[str]:
        """Parse teams from matchup string"""
        if ' @ ' in matchup:
            parts = matchup.split(' @ ')
            return [parts[0].split()[-1], parts[1]]
        elif ' vs. ' in matchup:
            parts = matchup.split(' vs. ')
            return [parts[0].split()[-1], parts[1]]
        return ['UNK', 'UNK']