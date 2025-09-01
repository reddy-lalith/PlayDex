"""
Mock data generator for demonstration
Generates realistic looking results based on actual game data
"""
from typing import List, Dict
from datetime import datetime
from app.models.search import (
    SearchResult, SearchResultMetadata, VideoLinks, 
    PlayData, Player
)
import uuid as uuid_lib


def generate_mock_results_from_games(games: List[Dict], entities: Dict) -> List[SearchResult]:
    """
    Generate mock search results from real game data
    This is for demonstration purposes when real video events aren't available
    """
    results = []
    
    for game in games[:5]:  # Limit to 5 games
        # Extract game info
        game_id = game.get('Game_ID', game.get('GAME_ID', ''))
        game_date = game.get('GAME_DATE', '')
        team_name = game.get('TEAM_NAME', '')
        matchup = game.get('MATCHUP', '')
        
        # Parse teams from matchup
        teams = []
        if team_name:
            teams.append(team_name)
        if ' @ ' in matchup:
            opponent = matchup.split(' @ ')[-1]
            teams.append(opponent)
        elif ' vs. ' in matchup:
            opponent = matchup.split(' vs. ')[-1]
            teams.append(opponent)
            
        # Generate 1-2 mock plays per game based on action
        num_plays = 2 if entities.get('action') else 1
        
        for i in range(num_plays):
            # Create realistic play description
            period = 1 + (i % 4)  # Quarters 1-4
            time = f"{11 - (i * 3)}:30"  # Mock time
            
            description = _generate_description(entities, period, i)
            if not description:
                continue
                
            # Create play data
            play_data = PlayData(
                GAME_ID=game_id,
                EVENTNUM=100 + i,  # Mock event number
                PERIOD=period,
                PCTIMESTRING=time,
                HOMEDESCRIPTION=description if i % 2 == 0 else None,
                VISITORDESCRIPTION=description if i % 2 == 1 else None,
                SCORE=f"{70 + (i * 5)}-{65 + (i * 3)}",
                SCOREMARGIN=str(5 + (i * 2))
            )
            
            # Create video links (these will redirect to NBA.com)
            video_links = VideoLinks(
                nba_stats=f"https://www.nba.com/game/{game_id}",
                nba_game=f"https://www.nba.com/game/{game_id}",
                youtube_search=f"https://youtube.com/results?search_query=NBA+{entities.get('player', '').replace(' ', '+')}+{entities.get('action', 'highlights')}+{game_date}"
            )
            
            # Create metadata
            metadata = SearchResultMetadata(
                date=datetime.strptime(game_date, '%Y-%m-%d') if game_date else datetime.now(),
                gameId=game_id,
                teams=teams[:2] if len(teams) >= 2 else teams + ['Unknown'],
                quarter=period,
                timeRemaining=time,
                players=[Player(
                    id=entities.get('player_id', ''),
                    name=entities.get('player', '')
                )],
                action=entities.get('action', 'play')
            )
            
            # Create search result
            result = SearchResult(
                id=str(uuid_lib.uuid4()),
                playData=play_data,
                previewThumbnail=f"https://cdn.nba.com/teams/uploads/sites/1610612747/2023/generic-play.jpg",
                watchLinks=video_links,
                description=description,
                metadata=metadata
            )
            
            results.append(result)
    
    return results


def _generate_description(entities: Dict, period: int, index: int) -> str:
    """Generate a realistic play description"""
    player_name = entities.get('player', 'Player')
    action = entities.get('action', 'play')
    
    if action == 'dunk':
        descriptions = [
            f"{player_name} with the powerful slam dunk",
            f"{player_name} drives and throws it down",
            f"{player_name} with the one-handed jam",
            f"{player_name} finishes with authority"
        ]
    elif action == 'three':
        descriptions = [
            f"{player_name} hits the three-pointer",
            f"{player_name} drains it from beyond the arc",
            f"{player_name} connects from downtown",
            f"{player_name} with the long-range bomb"
        ]
    elif action == 'block':
        descriptions = [
            f"{player_name} with the rejection",
            f"{player_name} swats it away",
            f"{player_name} denies at the rim",
            f"{player_name} with the big block"
        ]
    elif action == 'steal':
        descriptions = [
            f"{player_name} picks the pocket",
            f"{player_name} with the steal",
            f"{player_name} forces the turnover",
            f"{player_name} intercepts the pass"
        ]
    elif action == 'assist':
        descriptions = [
            f"{player_name} with the beautiful pass",
            f"{player_name} finds the open man",
            f"{player_name} dishes for the score",
            f"{player_name} with the assist"
        ]
    else:
        descriptions = [
            f"{player_name} makes the play",
            f"{player_name} with the highlight",
            f"{player_name} shows off the skills",
            f"{player_name} in action"
        ]
    
    return descriptions[index % len(descriptions)]