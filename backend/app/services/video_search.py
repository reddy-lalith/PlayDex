"""
Video search implementation using NBA API VideoEvents endpoint
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2
from app.services.video_events_service import VideoEventsService
from app.models.search import (
    SearchResult, SearchResultMetadata, VideoLinks, 
    PlayData, Player, ExtractedEntities
)
import uuid as uuid_lib
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class VideoSearch:
    """Search that uses VideoEvents endpoint to get actual video URLs"""
    
    def __init__(self):
        self.video_service = VideoEventsService()
    
    def search_clips(self, entities: ExtractedEntities, limit: int = 15, offset: int = 0) -> List[SearchResult]:
        """Search for clips with video URLs
        
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
            
            # Get games based on season or recent games
            if entities.season:
                # Search for specific season
                print(f"Searching for season: {entities.season}")
                
                # Try up to 3 times with exponential backoff
                for attempt in range(3):
                    try:
                        # Add delay before API call
                        if attempt > 0:
                            time.sleep(2 * attempt)
                        
                        gamefinder = leaguegamefinder.LeagueGameFinder(
                            player_id_nullable=entities.player_id,
                            season_nullable=entities.season,
                            season_type_nullable='Regular Season',
                            timeout=20  # Longer timeout
                        )
                        games_df = gamefinder.get_data_frames()[0]
                        break  # Success, exit retry loop
                    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                        if attempt < 2:
                            wait_time = 3 * (attempt + 1)
                            print(f"NBA API timeout, waiting {wait_time} seconds before retry...")
                            time.sleep(wait_time)
                        else:
                            print(f"NBA API failed after 3 attempts")
                            raise
                
                # Also try playoffs for that season
                try:
                    time.sleep(2)  # Delay before second API call
                    playoff_finder = leaguegamefinder.LeagueGameFinder(
                        player_id_nullable=entities.player_id,
                        season_nullable=entities.season,
                        season_type_nullable='Playoffs',
                        timeout=20
                    )
                    playoff_games = playoff_finder.get_data_frames()[0]
                except Exception as e:
                    print(f"Could not fetch playoff games: {e}")
                    playoff_games = pd.DataFrame()
                if not playoff_games.empty:
                    # Combine regular season and playoff games
                    if games_df.empty:
                        games_df = playoff_games
                    else:
                        games_df = pd.concat([games_df, playoff_games]).drop_duplicates().sort_values('GAME_DATE', ascending=False)
            else:
                # For buzzer beaters without specific season, search known seasons
                if entities.action_detail == "buzzer beater":
                    # Search known seasons where players had famous buzzer beaters
                    buzzer_beater_seasons = []
                    
                    # Add player-specific seasons
                    if entities.player and 'lillard' in entities.player.lower():
                        buzzer_beater_seasons = ['2018-19', '2013-14', '2016-17', '2022-23']  # Dame's famous buzzer beaters
                    elif entities.player and 'lebron' in entities.player.lower():
                        buzzer_beater_seasons = ['2017-18', '2012-13', '2008-09', '2005-06']
                    elif entities.player and 'curry' in entities.player.lower():
                        # Steph has had many buzzer beaters throughout his career
                        buzzer_beater_seasons = ['2023-24', '2021-22', '2020-21', '2018-19', '2015-16', '2013-14', '2012-13']
                    else:
                        # General recent seasons for other players
                        buzzer_beater_seasons = ['2023-24', '2022-23', '2021-22', '2020-21', '2019-20', '2018-19']
                    
                    games_df = pd.DataFrame()
                    
                    for season in buzzer_beater_seasons[:4]:  # Check more seasons for buzzer beaters
                        try:
                            # Try playoffs first (buzzer beaters more common in playoffs)
                            playoff_finder = leaguegamefinder.LeagueGameFinder(
                                player_id_nullable=entities.player_id,
                                season_nullable=season,
                                season_type_nullable='Playoffs'
                            )
                            playoff_games = playoff_finder.get_data_frames()[0]
                            if not playoff_games.empty:
                                games_df = pd.concat([games_df, playoff_games])
                                
                            # Try regular season
                            gamefinder = leaguegamefinder.LeagueGameFinder(
                                player_id_nullable=entities.player_id,
                                season_nullable=season,
                                season_type_nullable='Regular Season'
                            )
                            season_games = gamefinder.get_data_frames()[0]
                            if not season_games.empty:
                                games_df = pd.concat([games_df, season_games.head(10)])  # Include more regular season games
                        except Exception as e:
                            print(f"Error searching season {season}: {e}")
                            continue
                    
                    if not games_df.empty:
                        games_df = games_df.drop_duplicates().sort_values('GAME_DATE', ascending=False)
                else:
                    # Get recent games (last 30 days)
                    date_from = (datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y')
                    date_to = datetime.now().strftime('%m/%d/%Y')
                    
                    gamefinder = leaguegamefinder.LeagueGameFinder(
                        player_id_nullable=entities.player_id,
                        date_from_nullable=date_from,
                        date_to_nullable=date_to
                    )
                    
                    games_df = gamefinder.get_data_frames()[0]
                    
                    if games_df.empty:
                        # Try without date filter for last season
                        gamefinder = leaguegamefinder.LeagueGameFinder(
                            player_id_nullable=entities.player_id,
                            season_nullable='2024-25'
                        )
                        games_df = gamefinder.get_data_frames()[0]
            
            if games_df.empty:
                print("No games found")
                return results
            
            # Process all games for comprehensive results
            total_games = len(games_df)
            print(f"Found {total_games} games to search")
            
            # For rare events like buzzer beaters, search more games but still have a reasonable limit
            # For common events like dunks/threes, we can limit if needed
            if entities.action_detail in ["buzzer beater", "game winner"]:
                if total_games > 40:
                    games_df = games_df.head(40)  # Limit to 40 games for buzzer beaters
                    print(f"Searching 40 most recent games (of {total_games}) for {entities.action_detail}")
                else:
                    print(f"Searching ALL {total_games} games for {entities.action_detail}")
            elif total_games > 30 and entities.action in ["dunk", "three", "layup"]:
                # For common plays in large datasets, limit to avoid extreme processing
                games_df = games_df.head(30)
                print(f"Limiting to 30 games for common action: {entities.action}")
            else:
                if total_games > 40:
                    games_df = games_df.head(40)
                    print(f"Processing 40 most recent games (of {total_games})")
                else:
                    print(f"Processing all {total_games} games")
            
            # Convert games to dict for processing
            games = games_df.to_dict('records')
            
            # Track total results found across all games
            all_results = []
            results_lock = threading.Lock()
            
            # For buzzer beaters and rare events, use parallel processing
            # But only if we have a reasonable number of games
            if entities.action_detail in ["buzzer beater", "game winner"] and 10 < len(games) <= 40:
                print(f"Using parallel processing for {len(games)} games...")
                
                def process_game(game_data):
                    game_id = game_data.get('GAME_ID', '')
                    game_date = game_data.get('GAME_DATE', '')
                    matchup = game_data.get('MATCHUP', '')
                    local_results = []
                    
                    try:
                        # Add delay to avoid rate limiting
                        time.sleep(1.5)  # 1.5 second delay between requests
                        
                        # Get play-by-play data with retries
                        for attempt in range(3):
                            try:
                                pbp = playbyplayv2.PlayByPlayV2(game_id=game_id, timeout=15)
                                plays_df = pbp.get_data_frames()[0]
                                break
                            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                                if attempt < 2:
                                    print(f"Attempt {attempt + 1} failed for game {game_id}, retrying...")
                                    time.sleep(2 * (attempt + 1))  # Exponential backoff
                                else:
                                    print(f"Failed to get data for game {game_id} after 3 attempts")
                                    return local_results
                        
                        # Quick check for buzzer beater times
                        time_mask = (
                            plays_df['PCTIMESTRING'].str.match(r'^0:0[0-1]$', na=False) |
                            plays_df['PCTIMESTRING'].str.match(r'^0:[0-1]\.\d+$', na=False)
                        )
                        
                        # First check if player was in this game at all
                        player_in_game = plays_df[
                            (plays_df['PLAYER1_ID'] == int(entities.player_id)) |
                            (plays_df['PLAYER2_ID'] == int(entities.player_id)) |
                            (plays_df['PLAYER3_ID'] == int(entities.player_id))
                        ]
                        
                        if player_in_game.empty:
                            return local_results  # Player didn't play in this game
                        
                        # Filter by player and time
                        player_plays = plays_df[
                            (plays_df['PLAYER1_ID'] == int(entities.player_id)) & time_mask
                        ]
                        
                        # Filter out misses
                        if not player_plays.empty:
                            player_plays = player_plays[
                                ~player_plays['HOMEDESCRIPTION'].str.contains('MISS', case=False, na=False) &
                                ~player_plays['VISITORDESCRIPTION'].str.contains('MISS', case=False, na=False)
                            ]
                        
                        if len(player_plays) > 0:
                            print(f"Found {len(player_plays)} buzzer beaters in game {game_id}")
                            
                        # Process plays
                        for _, play in player_plays.iterrows():
                            result = self._create_result(play, game_id, game_date, matchup, entities)
                            local_results.append(result)
                            
                    except Exception as e:
                        print(f"Error processing game {game_id}: {e}")
                    
                    return local_results
                
                # Process games in parallel with fewer workers to avoid rate limiting
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future_to_game = {executor.submit(process_game, game): game for game in games}
                    
                    completed = 0
                    for future in as_completed(future_to_game):
                        completed += 1
                        if completed % 10 == 0:
                            print(f"Processed {completed}/{len(games)} games...")
                        
                        try:
                            game_results = future.result()
                            if game_results:
                                print(f"Adding {len(game_results)} results from parallel processing")
                            with results_lock:
                                all_results.extend(game_results)
                        except Exception as e:
                            print(f"Game processing failed: {e}")
            else:
                # Sequential processing for regular searches
                for game_idx, game in enumerate(games):
                    # Log progress for large searches
                    if game_idx > 0 and game_idx % 10 == 0:
                        print(f"Processed {game_idx}/{len(games)} games, found {len(all_results)} clips so far...")
                    
                    # For common actions, stop early if we have plenty of results
                    if entities.action in ["dunk", "three", "layup"] and len(all_results) >= 100:
                        print(f"Found {len(all_results)} clips, stopping search")
                        break
                    game_id = game.get('GAME_ID', '')
                    game_date = game.get('GAME_DATE', '')
                    matchup = game.get('MATCHUP', '')
                    
                    try:
                        # Add delay between games to avoid rate limiting
                        if game_idx > 0:
                            time.sleep(1.5)  # 1.5 second delay between games
                        
                        # Get play-by-play data with timeout and retry
                        for attempt in range(3):
                            try:
                                pbp = playbyplayv2.PlayByPlayV2(game_id=game_id, timeout=15)
                                plays_df = pbp.get_data_frames()[0]
                                break
                            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                                if attempt < 2:
                                    wait_time = 2 * (attempt + 1)
                                    print(f"Timeout for game {game_id}, waiting {wait_time}s before retry...")
                                    time.sleep(wait_time)
                                else:
                                    print(f"Skipping game {game_id} after 3 attempts")
                                    raise
                        
                        # Filter plays by player - PLAYER1_ID is typically the primary actor (shooter)
                        # For shots, we want PLAYER1_ID to ensure they're the shooter, not assister
                        if entities.action in ['dunk', 'three', 'layup', 'jumper'] or entities.action_detail in ['buzzer beater', 'game winner']:
                            # For shooting actions, only get plays where player is the shooter (PLAYER1_ID)
                            player_plays = plays_df[
                                plays_df['PLAYER1_ID'] == int(entities.player_id)
                            ]
                        else:
                            # For other actions (blocks, steals, assists), check all player columns
                            player_plays = plays_df[
                                (plays_df['PLAYER1_ID'] == int(entities.player_id)) |
                                (plays_df['PLAYER2_ID'] == int(entities.player_id)) |
                                (plays_df['PLAYER3_ID'] == int(entities.player_id))
                            ]
                        
                        # Filter by action type and action detail if specified
                        if entities.action or entities.action_detail:
                            # Special handling for certain action details
                            if entities.action_detail == "buzzer beater":
                                # Buzzer beaters: shots at the last second (0:00 or 0:01 with decimals)
                                time_mask = (
                                    player_plays['PCTIMESTRING'].str.match(r'^0:00$', na=False) |     # 0:00 exactly
                                    player_plays['PCTIMESTRING'].str.match(r'^0:0\.\d+$', na=False) | # 0:0.X (like 0:0.3)
                                    player_plays['PCTIMESTRING'].str.match(r'^0:01$', na=False) |     # 0:01
                                    player_plays['PCTIMESTRING'].str.match(r'^0:1\.\d+$', na=False)   # 0:1.X (like 0:1.2)
                                )
                                player_plays = player_plays[time_mask]
                                
                                # Filter out MISSES for buzzer beaters - we only want made shots
                                player_plays = player_plays[
                                    ~player_plays['HOMEDESCRIPTION'].str.contains('MISS', case=False, na=False) &
                                    ~player_plays['VISITORDESCRIPTION'].str.contains('MISS', case=False, na=False)
                                ]
                                
                                if len(player_plays) > 0:
                                    print(f"Found {len(player_plays)} made buzzer beaters in game {game_id}")
                                
                                # If we found buzzer beaters, we can return early
                                if len(player_plays) > 0:
                                    # Process these plays and return early if we have enough results
                                    for _, play in player_plays.iterrows():
                                        event_num = play['EVENTNUM']
                                        
                                        # Get play description
                                        description = play['HOMEDESCRIPTION'] or play['VISITORDESCRIPTION'] or ''
                                        
                                        # Skip fetching video URL for now to avoid timeouts
                                        direct_video_url = None
                                        
                                        # Also construct the NBA stats event page URL as fallback
                                        season_year = self._get_season_from_game_id(game_id)
                                        import urllib.parse
                                        title_encoded = urllib.parse.quote(description)
                                        nba_stats_url = f"https://www.nba.com/stats/events?CFID=&CFPARAMS=&GameEventID={event_num}&GameID={game_id}&Season={season_year}&flag=1&title={title_encoded}"
                                        
                                        # Create result
                                        result = SearchResult(
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
                                                nba_stats=nba_stats_url,  # NBA stats page (as fallback)
                                                nba_video=direct_video_url,  # Direct MP4 video URL (primary)
                                                nba_game=f"https://www.nba.com/game/{game_id}",
                                                youtube_search=f"https://youtube.com/results?search_query=NBA+{entities.player}+buzzer+beater+{matchup}"
                                            ),
                                            description=f"{description} - {matchup} ({game_date})",
                                            metadata=SearchResultMetadata(
                                                date=datetime.strptime(game_date, '%Y-%m-%d') if game_date else datetime.now(),
                                                gameId=game_id,
                                                teams=self._parse_teams(matchup),
                                                quarter=play['PERIOD'],
                                                timeRemaining=play['PCTIMESTRING'],
                                                players=[Player(id=entities.player_id, name=entities.player or '')],
                                                action=entities.action or 'shot'
                                            )
                                        )
                                        all_results.append(result)
                                    # Skip normal play processing since we already handled it
                                    continue
                                
                            elif entities.action_detail == "game winner":
                                # Game winners: buzzer beaters (0:00) in 4th quarter or OT that result in team winning
                                # First filter for 4th quarter or overtime
                                fourth_or_ot = player_plays['PERIOD'] >= 4
                                
                                # Then filter for buzzer beater time (0:00)
                                time_mask = (
                                    player_plays['PCTIMESTRING'].str.match(r'^0:00$', na=False) |     # 0:00 exactly
                                    player_plays['PCTIMESTRING'].str.match(r'^0:0\.\d+$', na=False)  # 0:0.X
                                )
                                
                                # Combine conditions
                                player_plays = player_plays[fourth_or_ot & time_mask]
                                
                                # Filter out misses - we only want made shots
                                player_plays = player_plays[
                                    ~player_plays['HOMEDESCRIPTION'].str.contains('MISS', case=False, na=False) &
                                    ~player_plays['VISITORDESCRIPTION'].str.contains('MISS', case=False, na=False)
                                ]
                                
                                # Additional filter: Check if the shot resulted in team winning
                                # This requires checking the score margin after the shot
                                if len(player_plays) > 0 and 'SCOREMARGIN' in player_plays.columns:
                                    # Filter for shots where team was tied or down before the shot
                                    # and the shot puts them ahead (game winner)
                                    winning_plays = []
                                    for _, play in player_plays.iterrows():
                                        scoremargin = play.get('SCOREMARGIN', '')
                                        if scoremargin:
                                            try:
                                                margin = int(scoremargin)
                                                # If margin is positive and small (1-3), likely a game winner
                                                # We'll keep all buzzer beaters in 4th/OT for now as they're likely game winners
                                                winning_plays.append(play)
                                            except:
                                                # If we can't parse, include it
                                                winning_plays.append(play)
                                        else:
                                            winning_plays.append(play)
                                    
                                    if winning_plays:
                                        player_plays = pd.DataFrame(winning_plays)
                                    else:
                                        player_plays = pd.DataFrame()
                                
                                print(f"Game winner search: Found {len(player_plays)} game-winning buzzer beaters in 4th/OT")
                                
                                # Filter by shot type if specified
                                if entities.action and len(player_plays) > 0:
                                    action_filter = self._get_action_filter(entities.action)
                                    if action_filter:
                                        player_plays = player_plays[
                                            player_plays['HOMEDESCRIPTION'].str.contains(action_filter, case=False, na=False) |
                                            player_plays['VISITORDESCRIPTION'].str.contains(action_filter, case=False, na=False)
                                        ]
                                
                            elif entities.action_detail == "crossover" and entities.action:
                                # For crossover + shot combos, just look for the shot type
                                # The crossover happens before and isn't recorded in play-by-play
                                if entities.action:
                                    action_filter = self._get_action_filter(entities.action)
                                    if action_filter:
                                        player_plays = player_plays[
                                            player_plays['HOMEDESCRIPTION'].str.contains(action_filter, case=False, na=False) |
                                            player_plays['VISITORDESCRIPTION'].str.contains(action_filter, case=False, na=False)
                                        ]
                            else:
                                # Standard filtering
                                conditions = []
                                
                                # Add action filter
                                if entities.action:
                                    action_filter = self._get_action_filter(entities.action)
                                    if action_filter:
                                        conditions.append(action_filter)
                                
                                # Add action detail filter (but be less strict)
                                if entities.action_detail and entities.action_detail not in ["crossover", "buzzer beater"]:
                                    detail_filter = self._get_detail_filter(entities.action_detail)
                                    if detail_filter:
                                        conditions.append(detail_filter)
                                
                                # Apply filters if we have any
                                if conditions:
                                    # For single condition or relaxed filtering
                                    filter_pattern = '|'.join(conditions)  # OR instead of AND
                                    player_plays = player_plays[
                                        player_plays['HOMEDESCRIPTION'].str.contains(filter_pattern, case=False, na=False) |
                                        player_plays['VISITORDESCRIPTION'].str.contains(filter_pattern, case=False, na=False)
                                    ]
                                
                                # For shooting actions, filter out misses
                                if entities.action in ['dunk', 'three', 'layup', 'jumper']:
                                    player_plays = player_plays[
                                        ~player_plays['HOMEDESCRIPTION'].str.contains('MISS', case=False, na=False) &
                                        ~player_plays['VISITORDESCRIPTION'].str.contains('MISS', case=False, na=False)
                                    ]
                        
                        # Log filtering results
                        if len(player_plays) > 0:
                            print(f"Game {game_id}: Found {len(player_plays)} valid plays after filtering")
                        
                        # Process all matching plays from this game
                        for _, play in player_plays.iterrows():
                            event_num = play['EVENTNUM']
                            
                            # Create result using helper method
                            result = self._create_result(play, game_id, game_date, matchup, entities)
                            all_results.append(result)
                            
                    except Exception as e:
                        print(f"Error processing game {game_id}: {e}")
                        continue
            
            # Apply pagination to the complete results
            print(f"Total clips found: {len(all_results)}")
            
            # Debug: Show sample of results if any found
            if all_results and entities.action_detail in ["buzzer beater", "game winner"]:
                print(f"Sample buzzer beater results:")
                for i, result in enumerate(all_results[:3]):
                    print(f"  {i+1}. {result.description}")
            
            # Sort results by date (most recent first)
            all_results.sort(key=lambda x: x.metadata.date, reverse=True)
            
            # Apply offset and limit for pagination
            start_idx = offset
            end_idx = offset + limit
            paginated_results = all_results[start_idx:end_idx]
            
            # Now fetch video URLs only for the paginated results
            print(f"Fetching video URLs for {len(paginated_results)} results...")
            for idx, result in enumerate(paginated_results):
                try:
                    # Add small delay between video requests to avoid rate limiting
                    if idx > 0:
                        time.sleep(0.5)
                    
                    video_data = self.video_service.get_video_url(
                        result.playData.GAME_ID, 
                        result.playData.EVENTNUM
                    )
                    if video_data:
                        result.watchLinks.nba_video = video_data.get('video')
                        # Update description if available
                        if video_data.get('desc'):
                            result.description = f"{video_data['desc']} - {result.description.split(' - ', 1)[1]}"
                except Exception as e:
                    print(f"Error fetching video for result: {e}")
                    # Continue without video URL
            
            print(f"Returning {len(paginated_results)} results (offset: {offset}, limit: {limit})")
            return paginated_results
            
        except Exception as e:
            print(f"Error in video search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _create_result(self, play, game_id: str, game_date: str, matchup: str, entities: ExtractedEntities) -> SearchResult:
        """Create a SearchResult from play data"""
        event_num = play['EVENTNUM']
        description = play['HOMEDESCRIPTION'] or play['VISITORDESCRIPTION'] or ''
        
        # Construct the NBA stats event page URL
        season_year = self._get_season_from_game_id(game_id)
        import urllib.parse
        title_encoded = urllib.parse.quote(description)
        nba_stats_url = f"https://www.nba.com/stats/events?CFID=&CFPARAMS=&GameEventID={event_num}&GameID={game_id}&Season={season_year}&flag=1&title={title_encoded}"
        
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
                nba_stats=nba_stats_url,
                nba_video=None,  # Will be fetched later for paginated results
                nba_game=f"https://www.nba.com/game/{game_id}",
                youtube_search=f"https://youtube.com/results?search_query=NBA+{entities.player}+{entities.action_detail or ''}+{entities.action or 'highlights'}+{matchup}"
            ),
            description=f"{description} - {matchup} ({game_date})",
            metadata=SearchResultMetadata(
                date=datetime.strptime(game_date, '%Y-%m-%d') if game_date else datetime.now(),
                gameId=game_id,
                teams=self._parse_teams(matchup),
                quarter=play['PERIOD'],
                timeRemaining=play['PCTIMESTRING'],
                players=[Player(id=entities.player_id, name=entities.player or '')],
                action=entities.action or 'play'
            )
        )
    
    def _get_action_filter(self, action: str) -> Optional[str]:
        """Get filter string for action type"""
        action_filters = {
            'dunk': 'DUNK',
            'three': '3PT',
            'block': 'BLOCK',
            'steal': 'STEAL',
            'assist': 'AST',
            'layup': 'Layup',
            'jumper': 'Jump Shot'
        }
        return action_filters.get(action)
    
    def _get_detail_filter(self, detail: str) -> Optional[str]:
        """Get filter string for action detail/modifier"""
        detail_filters = {
            'step back': 'Step Back',
            'fadeaway': 'Fade Away',
            'pull up': 'Pull Up',
            'buzzer beater': 'Buzzer',
            'game winner': 'Game',
            'clutch': '3PT',  # Often clutch shots are 3s
            'alley oop': 'Alley Oop',
            'and one': 'PTS)',  # Often appears in descriptions with points
            'putback': 'Putback',
            'fast break': 'Fast Break',
            'euro step': 'Euro',
            'spin move': 'Spin',
            'crossover': 'Crossover',
            'behind the back': 'Behind',
            'no look': 'No Look',
            'reverse': 'Reverse',
            'windmill': 'Windmill',
            '360': '360'
        }
        return detail_filters.get(detail)
    
    def _parse_teams(self, matchup: str) -> List[str]:
        """Parse teams from matchup string"""
        if ' @ ' in matchup:
            parts = matchup.split(' @ ')
            return [parts[0].split()[-1], parts[1]]
        elif ' vs. ' in matchup:
            parts = matchup.split(' vs. ')
            return [parts[0].split()[-1], parts[1]]
        return ['Unknown', 'Unknown']
    
    def _get_season_from_game_id(self, game_id: str) -> str:
        """Determine season from game ID
        Game ID format: 00XYYYYY where:
        - 00 is league ID (00 for NBA)
        - X is season indicator (2 for regular season/playoffs)
        - YY is the year (last 2 digits)
        
        Examples:
        - 0021301192 = 2013-14 season
        - 0022301234 = 2023-24 season
        """
        if len(game_id) >= 5:
            # Extract year indicator (positions 3-4)
            year_code = game_id[3:5]
            try:
                year_num = int(year_code)
                # Convert to full year (00-50 = 2000-2050, 51-99 = 1951-1999)
                if year_num <= 50:
                    start_year = 2000 + year_num
                else:
                    start_year = 1900 + year_num
                    
                return f"{start_year}-{str(start_year + 1)[-2:]}"
            except:
                pass
        
        # Fallback for specific patterns
        if game_id.startswith('00424'):
            return '2024-25'
        elif game_id.startswith('00223') or game_id.startswith('00224'):
            return '2023-24'
        elif game_id.startswith('00222'):
            return '2022-23'
        elif game_id.startswith('00221'):
            return '2021-22'
        elif game_id.startswith('00220'):
            return '2020-21'
        elif game_id.startswith('00213'):
            return '2013-14'
        else:
            # Default to current season
            return '2024-25'