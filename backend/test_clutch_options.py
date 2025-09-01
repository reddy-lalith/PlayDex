#!/usr/bin/env python3
"""
Test what clutch time options are available in NBA API
"""
import sys
sys.path.append('/Users/lalithreddy/PlayDex/backend')

try:
    from nba_api.stats.endpoints import videodetailsasset
    
    # Try different clutch time values
    test_values = [
        "Last 1 Second",
        "Last 2 Seconds", 
        "Last 3 Seconds",
        "Last 5 Seconds",
        "Last 10 Seconds",
        "Last 30 Seconds",
        "Last 1 Minute",
        "0:00",
        "0:01",
        "Buzzer",
        "Buzzer Beater"
    ]
    
    print("Testing NBA API clutch_time_nullable values...")
    print("-" * 50)
    
    for clutch_value in test_values:
        try:
            params = {
                'team_id': 1610612747,  # Lakers
                'player_id': 2544,      # LeBron
                'context_measure_detailed': 'PTS',
                'season': '2023-24',
                'season_type_all_star': 'Regular Season',
                'clutch_time_nullable': clutch_value,
                'last_n_games': 0,
                'month': 0,
                'opponent_team_id': 0,
                'period': 0
            }
            
            response = videodetailsasset.VideoDetailsAsset(**params)
            video_dict = response.get_dict()
            
            count = 0
            if video_dict and 'resultSets' in video_dict:
                videos = video_dict['resultSets']
                if isinstance(videos, dict) and 'playlist' in videos:
                    count = len(videos['playlist'])
            
            print(f"'{clutch_value}' -> {count} results (SUCCESS)")
            
        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg or "invalid" in error_msg.lower():
                print(f"'{clutch_value}' -> INVALID VALUE")
            else:
                print(f"'{clutch_value}' -> ERROR: {error_msg[:50]}...")
                
except Exception as e:
    print(f"Could not import NBA API: {e}")