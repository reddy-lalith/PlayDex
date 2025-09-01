#!/usr/bin/env python3
"""
Test if NBA API accepts "Last 1 Second" as clutch_time
"""
import requests
import json

# NBA Stats API endpoint
url = "https://stats.nba.com/stats/videodetailsasset"

# Headers required by NBA Stats
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin'
}

# Test different clutch time values
test_values = [
    "Last 1 Second",
    "Last 2 Seconds", 
    "Last 5 Seconds",
    "Last 10 Seconds",
    "1",
    "0:01",
    ""  # Empty to see default behavior
]

print("Testing NBA API clutch_time_nullable values...")
print("-" * 60)

for clutch_value in test_values:
    params = {
        'TeamID': '1610612747',  # Lakers
        'PlayerID': '2544',      # LeBron
        'ContextMeasure': 'PTS',
        'Season': '2023-24',
        'SeasonType': 'Regular Season',
        'ClutchTime': clutch_value,
        'LastNGames': '0',
        'Month': '0',
        'OpponentTeamID': '0',
        'Period': '0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'resultSets' in data:
                playlist = data['resultSets'].get('playlist', [])
                count = len(playlist) if playlist else 0
                print(f"'{clutch_value}' -> {count} results (SUCCESS)")
            else:
                print(f"'{clutch_value}' -> Unexpected response format")
        else:
            print(f"'{clutch_value}' -> HTTP {response.status_code} - INVALID")
            
    except Exception as e:
        print(f"'{clutch_value}' -> ERROR: {str(e)[:50]}...")

print("\nConclusion: The NBA API likely only accepts predefined clutch time values.")
print("Common valid values are: 'Last 5 Minutes', 'Last 1 Minute', 'Last 30 Seconds', 'Last 10 Seconds'")