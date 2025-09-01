import json
import spacy
from spacy.matcher import PhraseMatcher
from nba_api.stats.static import players

def load_team_id_dict(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def create_player_dictionaries():
    # Get both active and inactive players
    all_players_list = players.get_players()
    active_players_list = players.get_active_players()
    
    # Create dictionaries for all players (including retired)
    all_players = {player['full_name'].lower(): player['id'] for player in all_players_list}
    active_players = {player['full_name'].lower(): player['id'] for player in active_players_list}
    
    first_name_to_full_names = {}
    last_name_to_full_names = {}

    # Process all players for name matching
    for player in all_players_list:
        full_name = player['full_name'].lower()
        first_name = full_name.split()[0].lower()
        last_name = full_name.split()[-1].lower()

        if first_name in first_name_to_full_names:
            first_name_to_full_names[first_name].append(full_name)
        else:
            first_name_to_full_names[first_name] = [full_name]

        if last_name in last_name_to_full_names:
            last_name_to_full_names[last_name].append(full_name)
        else:
            last_name_to_full_names[last_name] = [full_name]
    
    # For now, return all_players as the main dictionary to support retired players
    return all_players, first_name_to_full_names, last_name_to_full_names

def create_matchers(nlp, team_id_dict, active_players, first_name_to_full_names, last_name_to_full_names):
    team_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    player_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

    team_patterns = [nlp.make_doc(name) for name in team_id_dict.keys()]
    team_matcher.add("TEAM_NAMES", team_patterns)

    full_name_patterns = [nlp.make_doc(name) for name in active_players.keys()]
    player_matcher.add("FULL_PLAYER_NAMES", full_name_patterns)

    # We'll handle first and last names separately in the entity extractor

    return team_matcher, player_matcher

def preprocess_query(query):
    stopwords = {"the", "a", "an"}
    query_tokens = query.split()
    filtered_tokens = [word for word in query_tokens if word.lower() not in stopwords]
    return " ".join(filtered_tokens)


def process_videos(df):
    """
    Reformat NBA video DataFrame rows into more readable columns and extract video URLs and thumbnails.

    Parameters:
        df (pd.DataFrame): Input DataFrame with NBA video data.

    Returns:
        pd.DataFrame: Reformatted DataFrame.
    """
    # Create a mapping of expected columns - only rename columns that exist
    column_mapping = {
        'gi': 'Game_ID',
        'ei': 'Event_Index',
        'y': 'Year',
        'm': 'Month',
        'd': 'Day',
        'gc': 'Game_Code',
        'p': 'Period',
        'cl': 'Clock',  # Clock/time remaining
        't': 'Time',    # Alternative time field
        'dsc': 'Description',
        'ha': 'Home_Team',
        'hid': 'Home_Team_ID',
        'va': 'Visitor_Team',
        'vid': 'Visitor_Team_ID',
        'hpb': 'Home_Points_Before',
        'hpa': 'Home_Points_After',
        'vpb': 'Visitor_Points_Before',
        'vpa': 'Visitor_Points_After',
        'pta': 'Points_This_Action',
        'video_url': 'Video_URL',
        'date': 'Game_Date'
    }
    
    # Only rename columns that actually exist in the DataFrame
    existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
    formatted_df = df.rename(columns=existing_columns)

    # Calculate derived columns only if required columns exist
    if all(col in formatted_df.columns for col in ['Home_Points_After', 'Home_Points_Before', 'Visitor_Points_After', 'Visitor_Points_Before']):
        formatted_df['Point_Change'] = (
            (formatted_df['Home_Points_After'] - formatted_df['Home_Points_Before']) + 
            (formatted_df['Visitor_Points_After'] - formatted_df['Visitor_Points_Before'])
        )
        
        formatted_df['Score_Diff'] = (formatted_df['Home_Points_Before'] - formatted_df['Visitor_Points_Before']).abs()
        formatted_df['Score_Diff_After'] = (formatted_df['Home_Points_After'] - formatted_df['Visitor_Points_After']).abs()
    else:
        # Add default values if score columns don't exist
        formatted_df['Point_Change'] = 0
        formatted_df['Score_Diff'] = 0
        formatted_df['Score_Diff_After'] = 0
    

    # Unpack the `video_url` dictionary to extract the video link and thumbnail link
    if 'Video_URL' in formatted_df.columns:
        formatted_df['Video_Link'] = formatted_df['Video_URL'].apply(lambda x: x.get('lurl') if isinstance(x, dict) else None)
        formatted_df['Thumbnail_Link'] = formatted_df['Video_URL'].apply(lambda x: x.get('lth') if isinstance(x, dict) else None)
    elif 'video_url' in formatted_df.columns:
        # Try lowercase version
        formatted_df['Video_Link'] = formatted_df['video_url'].apply(lambda x: x.get('lurl') if isinstance(x, dict) else None)
        formatted_df['Thumbnail_Link'] = formatted_df['video_url'].apply(lambda x: x.get('lth') if isinstance(x, dict) else None)
    else:
        # No video URL data available
        formatted_df['Video_Link'] = None
        formatted_df['Thumbnail_Link'] = None

    # Only reorder columns that actually exist
    desired_columns = [
        'Game_ID', 'Game_Date', 'Year', 'Month', 'Day', 'Game_Code', 'Period', 
        'Home_Team', 'Visitor_Team', 'Description', 'Home_Points_Before', 'Home_Points_After',
        'Visitor_Points_Before', 'Visitor_Points_After', 'Point_Change', 'Score_Diff', 'Score_Diff_After',
        'Home_Team_ID', 'Visitor_Team_ID', 'Video_Link', 'Thumbnail_Link', 
    ]
    
    # Only include columns that exist in the dataframe
    existing_desired_columns = [col for col in desired_columns if col in formatted_df.columns]
    
    # Include any other columns that weren't in our desired list
    other_columns = [col for col in formatted_df.columns if col not in existing_desired_columns]
    
    # Reorder with existing columns first, then any others
    formatted_df = formatted_df[existing_desired_columns + other_columns]

    return formatted_df