#!/usr/bin/env python3
"""
Simple test for buzzer beater and game winner logic
"""
import re

def test_score_specifier_extraction():
    """Test extraction of buzzer beater and game winner from queries"""
    print("=== Testing Score Specifier Extraction ===")
    
    SCORE_SPECIFIER_MAP = {
        'game-tying': 'GT', 'game tying': 'GT', 'tying': 'GT', 
        'lead-taking': 'LT', 'lead taking': 'LT', 'lead-taker': 'LT', 'lead taker': 'LT',
        'buzzer beater': 'BB', 'buzzer-beater': 'BB', 'buzzer beaters': 'BB', 'buzzer-beaters': 'BB',
        'game winner': 'GW', 'game-winner': 'GW', 'game winners': 'GW', 'game-winners': 'GW',
    }
    
    test_queries = [
        "damian lillard buzzer beaters",
        "lebron james game winners",
        "steph curry buzzer beater three pointers",
        "kawhi leonard game winner shot",
        "dame buzzer-beater against okc",
        "jordan game-winning shots"
    ]
    
    for query in test_queries:
        query_lower = query.lower()
        found_specifiers = []
        
        for spec in SCORE_SPECIFIER_MAP:
            if re.search(rf"\b{re.escape(spec)}\b", query_lower):
                found_specifiers.append((spec, SCORE_SPECIFIER_MAP[spec]))
        
        print(f"\nQuery: {query}")
        print(f"Found specifiers: {found_specifiers}")

def test_time_parsing():
    """Test time string parsing logic"""
    print("\n=== Testing Time Parsing ===")
    
    def time_to_seconds(time_str):
        """Convert time string (MM:SS or M:SS) to seconds"""
        if not time_str:
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
    
    test_times = [
        "0:00",     # Buzzer beater
        "0:01",     # 1 second left
        "0:0.3",    # 0.3 seconds
        "0:00.0",   # Exact buzzer
        "10:30",    # Normal time
        "2:45",     # Normal time
        "0:05",     # 5 seconds
    ]
    
    for time_str in test_times:
        seconds = time_to_seconds(time_str)
        is_buzzer = seconds is not None and seconds <= 1
        print(f"Time: {time_str:>8} -> {seconds:>6} seconds -> Buzzer beater: {is_buzzer}")

def test_description_parsing():
    """Test parsing buzzer beaters from descriptions"""
    print("\n=== Testing Description Parsing ===")
    
    test_descriptions = [
        "Lillard 26' 3PT Jump Shot (0:00)",
        "James Driving Layup (0:01)",
        "Curry 30' 3PT (10:23)",
        "Leonard Jump Shot (0:00) - Game Winner",
        "Butler Fadeaway (2:30)",
        "Irving Buzzer Beater 3PT",
        "Davis Dunk (0:0.3)"
    ]
    
    buzzer_pattern = r'\(0:0[0-1]?\)'
    keyword_pattern = r'buzzer|game.?winner'
    
    for desc in test_descriptions:
        has_time_buzzer = bool(re.search(buzzer_pattern, desc))
        has_keyword = bool(re.search(keyword_pattern, desc, re.IGNORECASE))
        is_buzzer = has_time_buzzer or has_keyword
        
        print(f"\nDescription: {desc}")
        print(f"  Has (0:0X): {has_time_buzzer}")
        print(f"  Has keyword: {has_keyword}")
        print(f"  Is buzzer beater: {is_buzzer}")

if __name__ == "__main__":
    test_score_specifier_extraction()
    print("\n" + "="*50)
    test_time_parsing()
    print("\n" + "="*50)
    test_description_parsing()