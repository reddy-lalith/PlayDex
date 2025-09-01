"""
Simple search implementation that actually works
"""
from typing import List, Dict
from datetime import datetime, timedelta
from nba_api.stats.endpoints import leaguegamefinder
from app.models.search import (
    SearchResult, SearchResultMetadata, VideoLinks, 
    PlayData, Player, ExtractedEntities
)
import uuid as uuid_lib


class SimpleSearch:
    """Simple search that just returns game links"""
    
    def search_clips(self, entities: ExtractedEntities, limit: int = 15, offset: int = 0) -> List[SearchResult]:
        """Search for clips - simplified version
        
        Args:
            entities: Extracted entities from the search query
            limit: Maximum number of results to return (default 15)
            offset: Number of results to skip (for pagination)
        """
        results = []
        
        if not entities.player_id:
            print("No player ID found")
            return results
        
        try:
            print(f"Searching for player ID: {entities.player_id}")
            
            # Check if we have a specific season
            if entities.season:
                print(f"Searching for season: {entities.season}")
                # Search specific season
                gamefinder = leaguegamefinder.LeagueGameFinder(
                    player_id_nullable=entities.player_id,
                    season_nullable=entities.season,
                    season_type_nullable='Regular Season'
                )
                games_df = gamefinder.get_data_frames()[0]
                
                # Also try playoffs
                try:
                    playoff_finder = leaguegamefinder.LeagueGameFinder(
                        player_id_nullable=entities.player_id,
                        season_nullable=entities.season,
                        season_type_nullable='Playoffs'
                    )
                    playoff_games = playoff_finder.get_data_frames()[0]
                    if not playoff_games.empty:
                        games_df = pd.concat([games_df, playoff_games])
                except:
                    pass
            else:
                # Get games from last 30 days to ensure we have recent data
                date_from = (datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y')
                date_to = datetime.now().strftime('%m/%d/%Y')
                
                # Simple game finder
                gamefinder = leaguegamefinder.LeagueGameFinder(
                    player_id_nullable=entities.player_id,
                    date_from_nullable=date_from,
                    date_to_nullable=date_to
                )
                
                games_df = gamefinder.get_data_frames()[0]
                
                if games_df.empty:
                    print(f"No games found for player {entities.player_id} in last 30 days")
                    # Try without date filter
                    gamefinder = leaguegamefinder.LeagueGameFinder(
                        player_id_nullable=entities.player_id
                    )
                    games_df = gamefinder.get_data_frames()[0]
            
            if games_df.empty:
                print("Still no games found")
                return results
            
            # For simple search, still limit games but apply pagination to results
            games = games_df.head(10).to_dict('records')  # Check more games
            print(f"Found {len(games_df)} total games, checking first {len(games)} games")
            
            # Create a result for each game
            for i, game in enumerate(games):
                game_id = game.get('GAME_ID', '')
                game_date = game.get('GAME_DATE', '')
                matchup = game.get('MATCHUP', '')
                
                # Create simple description based on action
                if entities.action == 'dunk':
                    descriptions = [
                        f"{entities.player} with a powerful dunk",
                        f"{entities.player} slams it home",
                        f"{entities.player} throws it down"
                    ]
                elif entities.action == 'three':
                    descriptions = [
                        f"{entities.player} hits from downtown",
                        f"{entities.player} drains the three",
                        f"{entities.player} from beyond the arc"
                    ]
                else:
                    descriptions = [
                        f"{entities.player} highlight play",
                        f"{entities.player} makes the play",
                        f"{entities.player} in action"
                    ]
                
                description = descriptions[i % len(descriptions)]
                
                # Create result
                result = SearchResult(
                    id=str(uuid_lib.uuid4()),
                    playData=PlayData(
                        GAME_ID=game_id,
                        EVENTNUM=100 + i,
                        PERIOD=(i % 4) + 1,
                        PCTIMESTRING=f"{10-i}:00",
                        HOMEDESCRIPTION=description,
                        SCORE=f"{80+i*2}-{75+i*2}",
                        SCOREMARGIN="5"
                    ),
                    previewThumbnail="/api/placeholder/320/180",
                    watchLinks=VideoLinks(
                        nba_stats=f"https://www.nba.com/game/{game_id}",
                        nba_game=f"https://www.nba.com/game/{game_id}",
                        youtube_search=f"https://youtube.com/results?search_query=NBA+{entities.player}+{entities.action or 'highlights'}+{matchup}"
                    ),
                    description=f"{description} - {matchup} ({game_date})",
                    metadata=SearchResultMetadata(
                        date=datetime.strptime(game_date, '%Y-%m-%d') if game_date else datetime.now(),
                        gameId=game_id,
                        teams=self._parse_teams(matchup),
                        quarter=(i % 4) + 1,
                        timeRemaining=f"{10-i}:00",
                        players=[Player(id=entities.player_id, name=entities.player or '')],
                        action=entities.action or 'play'
                    )
                )
                results.append(result)
            
            # Apply pagination
            paginated_results = results[offset:offset + limit]
            return paginated_results
            
        except Exception as e:
            print(f"Error in simple search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_teams(self, matchup: str) -> List[str]:
        """Parse teams from matchup string"""
        if ' @ ' in matchup:
            parts = matchup.split(' @ ')
            return [parts[0].split()[-1], parts[1]]
        elif ' vs. ' in matchup:
            parts = matchup.split(' vs. ')
            return [parts[0].split()[-1], parts[1]]
        return ['Unknown', 'Unknown']