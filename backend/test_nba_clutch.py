#!/usr/bin/env python3
"""
Test NBA API clutch time functionality
"""
import sys
sys.path.append('/Users/lalithreddy/PlayDex/backend')

def test_clutch_extraction():
    """Test that buzzer beaters are extracted as clutch time"""
    from app.services.playdex_engine.entity_extractor import EntityExtractor
    from app.services.playdex_engine.utils import create_player_dictionaries, create_matchers
    import spacy
    
    # Initialize
    nlp = spacy.blank("en")
    active_players, first_name_to_full_names, last_name_to_full_names = create_player_dictionaries()
    team_matcher = None  # Not needed for this test
    player_matcher = None  # Not needed for this test
    
    extractor = EntityExtractor(nlp, team_matcher, player_matcher, active_players, first_name_to_full_names, last_name_to_full_names)
    
    # Test queries
    test_queries = [
        "damian lillard buzzer beaters",
        "lebron james last second shots",
        "steph curry clutch threes",
        "kawhi leonard game winner"
    ]
    
    print("=== Testing Clutch Time Extraction ===")
    for query in test_queries:
        # Extract entities
        player_name, team_name, season_type, context_measures, month, clutch_time, shot_specifiers, score_specifiers, season = extractor.extract_entities(query)
        
        print(f"\nQuery: {query}")
        print(f"  Player: {player_name}")
        print(f"  Clutch Time: {clutch_time}")
        print(f"  Score Specifier: {score_specifiers}")
        print(f"  Context Measures: {context_measures}")

def test_nba_api_directly():
    """Test NBA API with clutch_time parameter"""
    print("\n=== Testing NBA API Directly ===")
    
    try:
        from nba_api.stats.endpoints import videodetailsasset
        
        # Test parameters
        params = {
            'team_id': 1610612757,  # Portland Trail Blazers
            'player_id': 203081,    # Damian Lillard
            'context_measure_detailed': 'PTS',
            'season': '2023-24',
            'season_type_all_star': 'Regular Season',
            'clutch_time_nullable': 'Last 10 Seconds',  # This should get buzzer beaters!
            'last_n_games': 0,
            'month': 0,
            'opponent_team_id': 0,
            'period': 0
        }
        
        print(f"\nSearching for Damian Lillard shots in Last 10 Seconds...")
        print(f"Parameters: clutch_time_nullable = '{params['clutch_time_nullable']}'")
        
        response = videodetailsasset.VideoDetailsAsset(**params)
        video_dict = response.get_dict()
        
        if video_dict and 'resultSets' in video_dict:
            videos = video_dict['resultSets']
            if isinstance(videos, dict) and 'playlist' in videos:
                plays = videos['playlist']
                print(f"\nFound {len(plays)} plays in the last 10 seconds!")
                
                # Show first few
                for i, play in enumerate(plays[:5]):
                    desc = play.get('dsc', 'No description')
                    print(f"  {i+1}. {desc}")
            else:
                print("No plays found or unexpected format")
        else:
            print("No response from API")
            
    except Exception as e:
        print(f"Error testing NBA API: {e}")

if __name__ == "__main__":
    test_clutch_extraction()
    test_nba_api_directly()