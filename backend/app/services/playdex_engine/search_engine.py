import spacy
from nba_api.stats.endpoints import commonplayerinfo, videodetailsasset, playercareerstats
import pandas as pd
from app.services.playdex_engine.utils import load_team_id_dict, create_player_dictionaries, create_matchers, process_videos
from app.services.playdex_engine.entity_extractor import EntityExtractor
import re
class SearchEngine:
    def __init__(self, season='2024-25', season_type='Regular Season', last_n_games=200):
        self.nlp = spacy.load("en_core_web_sm")
        self.team_id_dict = load_team_id_dict("app/services/playdex_engine/team_id_dict.json")
        self.active_players, first_name_to_full_name, last_name_to_full_name = create_player_dictionaries()
        team_matcher, player_matcher = create_matchers(self.nlp, self.team_id_dict, self.active_players, first_name_to_full_name, last_name_to_full_name)


        self.entity_extractor = EntityExtractor(self.nlp, team_matcher, player_matcher, self.active_players, first_name_to_full_name, last_name_to_full_name)

        self.params = {
            "context_measure_detailed": [],
            "season": season,
            "season_type_all_star": season_type,
            "last_n_games": last_n_games,
            "period": 0,
            "month": 0,
        }

    def set_parameter(self, param_name, value):
        self.params[param_name] = value

    def build_params(self):
        required_params = ["context_measure_detailed", "season", "season_type_all_star", "team_id", "player_id"]
        missing_params = [param for param in required_params if self.params.get(param) is None]
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
        return self.params
    
    def filter_play_descriptions(self, df, keywords):
        """
        Filter plays based on shot type keywords using SHOT_SPECIFIER_MAP.

        Parameters:
            df (pd.DataFrame): DataFrame with play descriptions.
            keywords (list): List of keywords to search for.

        Returns:
            pd.DataFrame: Filtered DataFrame with only the desired plays.
        """
        if not keywords:
            return df  

        from app.services.playdex_engine.keywords_constants import SHOT_SPECIFIER_MAP
        
        # Map user keywords to NBA description terms
        nba_terms = []
        for keyword in keywords:
            if keyword.lower() in SHOT_SPECIFIER_MAP:
                nba_terms.append(SHOT_SPECIFIER_MAP[keyword.lower()])
            else:
                nba_terms.append(keyword)
        
        # Check for distance modifiers in original keywords
        has_long_range = any(word in ' '.join(keywords).lower() for word in ['long', 'deep', 'logo', 'halfcourt', 'half-court'])
        
        # Handle 3-pointers specifically
        if "3PT" in nba_terms:
            # For 3-pointers, look for 3PT in the description
            three_pt_patterns = [r'\b3PT\b', r'\b3-PT\b', r'\bThree Point\b']
            filtered_df = df[df['Description'].str.contains('|'.join(three_pt_patterns), case=False, na=False, regex=True)]
        # For jump shots, we need to be more specific
        elif "Jump Shot" in nba_terms:
            # Include regular jump shots and 3PT shots (which are also jump shots)
            # Exclude layups, dunks, tips, etc.
            jump_shot_patterns = [
                r'\b(Jump Shot|Jumper|Pull-Up|Pullup|Step Back|Turnaround|Fadeaway)\b',
                r'\b3PT\b',  # 3-pointers are typically jump shots
                r'\b(Running|Floating)\s+(Jump Shot|Jumper)\b'
            ]
            
            # Create a filter for jump shot types
            jump_filter = df['Description'].str.contains('|'.join(jump_shot_patterns), case=False, na=False, regex=True)
            
            # Exclude non-jump shot types
            exclude_patterns = [
                r'\b(Layup|Dunk|Tip|Hook|Alley Oop)\b',
                r'\b(Cutting|Putback)\s+(Layup|Dunk)\b'
            ]
            exclude_filter = ~df['Description'].str.contains('|'.join(exclude_patterns), case=False, na=False, regex=True)
            
            filtered_df = df[jump_filter & exclude_filter]
            
            # If looking for long range, prioritize 3PT and shots with distance info
            if has_long_range and 'Distance' in df.columns:
                # Filter for shots 20+ feet (long range)
                filtered_df = filtered_df[filtered_df['Distance'] >= 20]
        else:
            # For other shot types, use standard filtering
            filtered_df = df
            for term in nba_terms:
                pattern = rf'\b{re.escape(term)}\b'
                filtered_df = filtered_df[filtered_df['Description'].str.contains(pattern, case=False, na=False, regex=True)]

        return filtered_df
    
    def build_interpretation_message(self, params, play_type_keywords):
        message_parts = []

        if params.get('player_id'):
            player_name = next((name for name, id in self.active_players.items() if id == params['player_id']), None)
            if player_name:
                message_parts.append(player_name.title())  # Capitalize the name

        context_measure = params.get('context_measure_detailed')
        
        if play_type_keywords:
            play_type_str = ' '.join(play_type_keywords).lower()
        else:
            play_type_str = ""

        if context_measure:
            action = self.get_action(context_measure)
            if play_type_str:
                message_parts.append(f"{play_type_str} {action}")
            else:
                message_parts.append(action)
        elif play_type_str:
            message_parts.append(play_type_str)

        season_type = params.get('season_type_all_star')
        if season_type and season_type != "Regular Season":
            message_parts.append(f"in the {season_type}")

        month = params.get('month')
        if month and month != "0":
            months = ["", "October", "November", "December", "January", "February", "March", "April", "May", "June", "July", "August", "September"]
            message_parts.append(f"in {months[int(month)]}")

        season = params.get('season')
        if season:
            message_parts.append(f"during the {season} season")


        opponent_team_id = params.get('opponent_team_id')
        if opponent_team_id:
            team_name = next((name for name, id in self.team_id_dict.items() if id == opponent_team_id), None)
            if team_name:
                message_parts.append(f"against the {team_name.title()}")

        clutch_time = params.get('clutch_time_nullable')
        if clutch_time:
            message_parts.append(f"in {clutch_time}")

        # Combine all parts
        if message_parts:
            return "Interpreted as: " + " ".join(message_parts)
        else:
            return "No specific interpretation available"

    def get_action(self, context_measure):
        """ Helper function to determine the action based on context_measure """
        if context_measure == 'PTS':
            return 'field goals made'
        elif context_measure == 'AST':
            return 'assists'
        elif context_measure == 'REB':
            return 'rebounds'
        elif context_measure == 'STL':
            return 'steals'
        elif context_measure == 'BLK':
            return 'blocks'
        elif context_measure == 'TOV':
            return 'turnovers'
        elif context_measure == 'FGA':
            return 'shot attempts'
        elif context_measure == 'MISS':
            return 'misses'
        else:
            return context_measure.lower()
        
    def filter_with_score_specifiers(self, df, score_specifiers):
        # First check if we have the necessary columns
        time_column = None
        if 'Clock' in df.columns:
            time_column = 'Clock'
        elif 'Time' in df.columns:
            time_column = 'Time'
        
        if time_column:
            # Convert time to seconds for easier filtering
            df['TimeInSeconds'] = df[time_column].apply(lambda x: self._time_to_seconds(x) if pd.notna(x) else None)
        elif 'Description' in df.columns:
            # Try to extract time from description for buzzer beaters
            # Buzzer beaters often have "(0:00)" or similar in description
            # Pattern matches: (0:00), (0:01), (0:0.X), (0:1.X)
            df['HasBuzzerBeater'] = df['Description'].str.contains(r'\(0:[0-1](?:\.\d+)?\)', regex=True, na=False)
        
        if 'Period' in df.columns:
            df['IsLastPeriod'] = df['Period'] >= 4  # 4th quarter or OT
        
        # Handle buzzer beater (BB) - This shouldn't happen anymore since we use clutch_time
        if score_specifiers == 'BB':
            print("Note: Buzzer beaters should now be handled via clutch_time parameter")
            return df
        
        # Handle game winner (GW)
        elif score_specifiers == 'GW':
            # Game winners: buzzer beaters (0:00) in 4th quarter or OT
            if 'IsLastPeriod' in df.columns:
                # First filter for 4th/OT
                df = df[df['IsLastPeriod'] == True]
                
                # Then filter for buzzer beaters
                if 'TimeInSeconds' in df.columns:
                    df = df[df['TimeInSeconds'] <= 1]
                elif 'HasBuzzerBeater' in df.columns:
                    df = df[df['HasBuzzerBeater'] == True]
                elif 'Description' in df.columns:
                    df = df[df['Description'].str.contains('buzzer|game.?winner|0:0', case=False, na=False)]
            return df
        
        # Original score specifiers (GT, LT)
        if 'Home_Points_Before' in df.columns and 'Visitor_Points_Before' in df.columns:
            df['Score_Diff_Before'] = df['Home_Points_Before'] - df['Visitor_Points_Before']
            df['Score_Diff_After'] = df['Home_Points_After'] - df['Visitor_Points_After']
            
            # GT: Check if the shot tied the game
            if score_specifiers == 'GT':
                df = df[df['Score_Diff_After'] == 0]
            
            # LT: Check if the shot was a lead-taking shot
            elif score_specifiers == 'LT':
                df = df[((df['Score_Diff_Before'] <= 0) & (df['Score_Diff_After'] > 0)) |
                        ((df['Score_Diff_Before'] >= 0) & (df['Score_Diff_After'] < 0))]

        return df
    
    def _time_to_seconds(self, time_str):
        """Convert time string (MM:SS or M:SS) to seconds"""
        if pd.isna(time_str) or not time_str:
            return None
        try:
            parts = str(time_str).split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            return None
        except:
            return None
    def fetch_videos(self, context_measure, shot_specifiers=None, score_specifiers=None):
        try:
            self.set_parameter("context_measure_detailed", context_measure)
            params = self.build_params()
            intepretation = self.build_interpretation_message(params, shot_specifiers)
            print(intepretation)
            if params['context_measure_detailed'] == 'MISS':
                params['context_measure_detailed'] = 'FGA'
            
            print(f"Fetching videos with params: {params}")
            response = videodetailsasset.VideoDetailsAsset(**params)
            video_dict = response.get_dict()
            
            # Debug: Print response structure
            print(f"Response keys: {video_dict.keys() if video_dict else 'None'}")
            
            videos = video_dict['resultSets']
            
            # Debug the response structure
            print(f"ResultSets type: {type(videos)}")
            if isinstance(videos, dict):
                print(f"ResultSets keys: {list(videos.keys())}")
            elif isinstance(videos, list):
                print(f"ResultSets is a list with {len(videos)} items")
                if videos:
                    print(f"First item type: {type(videos[0])}")
            
            # Check if we have valid video data
            if not videos:
                print(f"No video data found for season {params.get('season')} and measure {context_measure}")
                return pd.DataFrame()
            
            # Handle different response structures
            if isinstance(videos, dict):
                video_urls = videos.get('Meta', {}).get('videoUrls', [])
                plays = videos.get('playlist', [])
            elif isinstance(videos, list) and len(videos) > 0:
                # Sometimes the API returns a list of result sets
                for result_set in videos:
                    if isinstance(result_set, dict) and result_set.get('name') == 'Playlist':
                        plays = result_set.get('rowSet', [])
                        # Get column headers
                        headers = result_set.get('headers', [])
                        if plays and headers:
                            # Convert to list of dicts
                            plays = [dict(zip(headers, play)) for play in plays]
                        break
                else:
                    plays = []
                
                # Look for video URLs in another result set
                video_urls = []
                for result_set in videos:
                    if isinstance(result_set, dict) and result_set.get('name') == 'Meta':
                        meta_data = result_set.get('rowSet', [[]])[0] if result_set.get('rowSet') else []
                        if meta_data:
                            video_urls = meta_data  # This might need adjustment based on structure
                        break
            else:
                print(f"Unexpected videos structure: {type(videos)}")
                return pd.DataFrame()
            
            if not plays:
                print(f"No plays found in playlist for {context_measure}")
                if len(str(video_dict)) < 500:  # Only print if response is reasonably sized
                    print(f"Full response structure: {video_dict}")
                else:
                    print("Response too large to print")
                    
                # Provide helpful context about data availability
                season = params.get('season', '')
                if season and season < '2019-20':
                    print(f"\nNote: NBA video data is limited for the {season} season.")
                    print("Try searching for:")
                    print("- More recent seasons (2019-20 or later)")
                    print("- Offensive plays (dunks, threes) which have better coverage")
                    print("- Playoff games which have more video coverage")
                
                return pd.DataFrame()
                
            df = pd.DataFrame(plays)
            df['video_url'] = video_urls
            
            # Debug: Print column names to see what we're working with
            print(f"DataFrame columns: {df.columns.tolist()}")
            print(f"First row sample: {df.iloc[0].to_dict() if len(df) > 0 else 'No data'}")

            # Try to create date column - handle different API response formats
            if 'y' in df.columns and 'm' in df.columns and 'd' in df.columns:
                df['date'] = pd.to_datetime(df['y'].astype(str) + '-' + 
                                            df['m'].astype(str).str.zfill(2) + '-' + 
                                            df['d'].astype(str).str.zfill(2))
            elif 'date' in df.columns:
                # Use existing date column if available
                df['date'] = pd.to_datetime(df['date'])
            elif 'gi' in df.columns:
                # Try to extract date from game ID if available
                df['date'] = pd.to_datetime('2017-01-01')  # Default date for older seasons
            else:
                # Fallback - use a default date
                df['date'] = pd.to_datetime('2017-01-01')

            df = df.sort_values(by='date', ascending=False)

            df = process_videos(df)  # Processing layer

            if shot_specifiers:
                df = self.filter_play_descriptions(df, shot_specifiers)
            
            if score_specifiers:
                df = self.filter_with_score_specifiers(df, score_specifiers)
            
            if params['clutch_time_nullable']:
                # Clutch is defined as the last 5 minutes of a game with a score differential of 5 or fewer points
                df = df[df['Score_Diff'] <= 5]
            
            if context_measure == 'MISS':
                df = df[df['Point_Change'] == 0]

            return df
        except Exception as e:
            print("Query returned no results")
            print(e)
            
            # Check if it's an older season that might not have video data
            season = self.params.get("season", "")
            if season and season < "2019-20":
                print(f"Note: Video data may not be available for the {season} season. NBA video archives are limited for older seasons.")
            
            # If it's a JSON decode error (500 response) in 2024-25, try workaround
            if "Expecting value" in str(e) and self.params.get("season") == "2024-25":
                # For PTS/FGM/FGA failures, try alternative approach
                if context_measure in ['PTS', 'FGM', 'FGA', 'MISS']:
                    print("Trying workaround for 2024-25 season...")
                    
                    # Get player name for filtering
                    player_name = next((name for name, id in self.active_players.items() if id == self.params['player_id']), "")
                    if not player_name:
                        print("Could not find player name")
                        return pd.DataFrame()
                    
                    # Try different context measures that work in 2024-25
                    working_measures = ['REB', 'STL', 'BLK']  # These work for 2024-25
                    
                    all_videos = pd.DataFrame()
                    for measure in working_measures:
                        try:
                            print(f"Trying {measure} endpoint...")
                            self.set_parameter("context_measure_detailed", measure)
                            response = videodetailsasset.VideoDetailsAsset(**self.params)
                            video_dict = response.get_dict()
                            videos = video_dict['resultSets']
                            video_urls = videos['Meta']['videoUrls']
                            plays = videos['playlist']
                            df = pd.DataFrame(plays)
                            if len(df) > 0:
                                df['video_url'] = video_urls
                                all_videos = pd.concat([all_videos, df])
                        except:
                            continue
                    
                    if len(all_videos) > 0:
                        # Process and filter for player's scoring plays
                        all_videos['date'] = pd.to_datetime(all_videos['y'].astype(str) + '-' + 
                                                           all_videos['m'].astype(str).str.zfill(2) + '-' + 
                                                           all_videos['d'].astype(str).str.zfill(2))
                        all_videos = all_videos.sort_values(by='date', ascending=False)
                        all_videos = process_videos(all_videos)
                        
                        # Filter for plays where this player scored
                        last_name = player_name.split()[-1]
                        # Pattern: Player's last name at start of description followed by shot type
                        scoring_pattern = f"^{last_name}\\s+.*(?:Layup|Dunk|Jump Shot|Hook Shot|Fadeaway|Bank Shot|Tip Shot|3PT)"
                        all_videos = all_videos[all_videos['Description'].str.contains(scoring_pattern, case=False, na=False, regex=True)]
                        
                        # Apply shot specifiers if provided
                        if shot_specifiers:
                            all_videos = self.filter_play_descriptions(all_videos, shot_specifiers)
                        
                        if score_specifiers:
                            all_videos = self.filter_with_score_specifiers(all_videos, score_specifiers)
                        
                        # Remove duplicates
                        all_videos = all_videos.drop_duplicates(subset=['gi', 'ei'])
                        
                        if len(all_videos) > 0:
                            print(f"Found {len(all_videos)} videos using workaround")
                            return all_videos
                
                # If workaround didn't work or not applicable, try previous season
                print("Falling back to 2023-24 season...")
                self.set_parameter("season", "2023-24")
                try:
                    return self.fetch_videos(context_measure, shot_specifiers, score_specifiers)
                except:
                    return pd.DataFrame()
                finally:
                    self.set_parameter("season", "2024-25")  # Reset to original
                    
            return pd.DataFrame()

    def map_player_team_ids(self, player_name, team_name=None):
        try:
            player_id = self.active_players.get(player_name.lower())
            if not player_id:
                raise ValueError(f"No player found for the name: {player_name}")

            # Get the requested season from params
            requested_season = self.params.get('season', '2024-25')
            
            # First try to get player career stats which includes historical team data
            team_id = None
            try:
                career_stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_dict()
                
                # Look for the SeasonTotalsRegularSeason result set
                for result_set in career_stats['resultSets']:
                    if result_set['name'] == 'SeasonTotalsRegularSeason':
                        headers = result_set['headers']
                        rows = result_set['rowSet']
                        
                        # Find the column indices
                        season_idx = headers.index('SEASON_ID') if 'SEASON_ID' in headers else None
                        team_idx = headers.index('TEAM_ID') if 'TEAM_ID' in headers else None
                        
                        if season_idx is not None and team_idx is not None:
                            # Find the team for the requested season
                            for row in rows:
                                if row[season_idx] == requested_season:
                                    team_id = row[team_idx]
                                    print(f"Found team ID {team_id} for {player_name} in season {requested_season}")
                                    break
                        break
            except Exception as e:
                print(f"Error getting career stats: {e}")
            
            # If we couldn't find the team from career stats, try other methods
            if team_id is None:
                # Use hardcoded knowledge for known cases
                if player_name.lower() == 'lebron james':
                    season_year = int(requested_season.split('-')[0])
                    if 2003 <= season_year <= 2009:
                        team_id = 1610612739  # Cleveland Cavaliers
                    elif 2010 <= season_year <= 2013:
                        team_id = 1610612748  # Miami Heat
                    elif 2014 <= season_year <= 2017:
                        team_id = 1610612739  # Cleveland Cavaliers (return)
                    else:  # 2018 onwards
                        team_id = 1610612747  # Los Angeles Lakers
                    print(f"Using hardcoded team ID {team_id} for LeBron James in {requested_season}")
                else:
                    # Fallback to current team from player info
                    try:
                        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()
                        team_id = player_info['resultSets'][0]['rowSet'][0][18]
                        print(f"Using current team ID {team_id} for {player_name} (fallback)")
                    except:
                        print(f"Could not get any team ID for {player_name}")
                        return None, None, None
            
            print(f"Final result - Player: {player_name}, Season: {requested_season}, Team ID: {team_id}")

            opponent_team_id = None
            if team_name:
                opponent_team_id = self.team_id_dict.get(team_name.upper(), None)
                if opponent_team_id is None:
                    raise ValueError(f"Could not find opponent team with name: {team_name}")

            return player_id, team_id, opponent_team_id

        except Exception as e:
            print(f"Error mapping player and team IDs: {e}")
            return None, None, None

    def query(self, query):
        player_name, team_name, season_type, context_measures, month, clutch_time, shot_specifiers, score_specifiers, season = self.entity_extractor.extract_entities(query)
        print(f"EXTRACTED: Player Name={player_name}, Team Name={team_name}, Season Type={season_type}, Context Measures={context_measures}, Month={month}, Clutch Time={clutch_time}, Shot Specifiers={shot_specifiers}, Score Specifier={score_specifiers}, Season={season}") 
        
        if "MISS" in context_measures and "PTS" in context_measures:
            context_measures.remove("PTS")

        # Set season if extracted from query, otherwise use default
        if season:
            self.set_parameter("season", season)
        elif season_type == "All Star":
            # For All-Star games without a specific year, default to 2023-24 (most recent completed All-Star game)
            self.set_parameter("season", "2023-24")
            print("No season specified for All-Star game, defaulting to 2023-24")
            
        self.set_parameter("season_type_all_star", season_type)
        self.set_parameter("month", month)
        self.set_parameter("clutch_time_nullable", clutch_time)

        player_id, team_id, opponent_team_id = self.map_player_team_ids(player_name, team_name)
        if player_id is None or team_id is None:
            print(f"Could not retrieve valid player or team ID for query: {query}")
            return pd.DataFrame()

        self.set_parameter("player_id", player_id)
        self.set_parameter("team_id", team_id)
        if opponent_team_id:
            self.set_parameter("opponent_team_id", opponent_team_id)

        videos = pd.DataFrame()
        
        # If no specific context measures are extracted, default to PTS
        if not context_measures:
            context_measures = ["PTS"]
            
        print(context_measures)

        for measure in context_measures:
            vids = None
            if measure == "PTS" or measure == "FGA" or measure == "MISS":
                vids = self.fetch_videos(measure, shot_specifiers, score_specifiers)
            else: 
                vids = self.fetch_videos(measure)
            videos = pd.concat([videos, vids])

        return videos