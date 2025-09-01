#!/usr/bin/env python3
"""
Test script for buzzer beaters and game winners
"""
import sys
sys.path.append('/Users/lalithreddy/PlayDex/backend')

from app.services.playdex_engine.search_engine import SearchEngine
from app.services.gemini_entity_extractor import GeminiEntityExtractor
from app.services.playdex_search import PlayDexSearch

def test_playdex_engine():
    """Test PlayDex engine directly"""
    print("=== Testing PlayDex Engine Directly ===")
    
    engine = SearchEngine(season="2023-24")
    
    # Test 1: Damian Lillard buzzer beaters
    print("\n1. Testing: Damian Lillard buzzer beaters")
    query1 = "damian lillard buzzer beaters"
    try:
        results1 = engine.query(query1)
        if results1 is not None and not results1.empty:
            print(f"Found {len(results1)} results")
            print("Sample descriptions:")
            for i, desc in enumerate(results1['Description'].head(3)):
                print(f"  {i+1}. {desc}")
        else:
            print("No results found")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: LeBron James game winners
    print("\n2. Testing: LeBron James game winners")
    query2 = "lebron james game winners"
    try:
        results2 = engine.query(query2)
        if results2 is not None and not results2.empty:
            print(f"Found {len(results2)} results")
            print("Sample descriptions:")
            for i, desc in enumerate(results2['Description'].head(3)):
                print(f"  {i+1}. {desc}")
        else:
            print("No results found")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Steph Curry buzzer beater three pointers
    print("\n3. Testing: Steph Curry buzzer beater three pointers")
    query3 = "steph curry buzzer beater three pointers"
    try:
        results3 = engine.query(query3)
        if results3 is not None and not results3.empty:
            print(f"Found {len(results3)} results")
            print("Sample descriptions:")
            for i, desc in enumerate(results3['Description'].head(3)):
                print(f"  {i+1}. {desc}")
        else:
            print("No results found")
    except Exception as e:
        print(f"Error: {e}")

def test_entity_extraction():
    """Test entity extraction"""
    print("\n=== Testing Entity Extraction ===")
    
    extractor = GeminiEntityExtractor()
    
    test_queries = [
        "damian lillard buzzer beaters",
        "lebron james game winners",
        "steph curry buzzer beater three pointers",
        "kawhi leonard game winner playoffs"
    ]
    
    for query in test_queries:
        entities = extractor._simple_extract(query)
        print(f"\nQuery: {query}")
        print(f"  Player: {entities.player}")
        print(f"  Action: {entities.action}")
        print(f"  Action Detail: {entities.action_detail}")

def test_playdex_search():
    """Test PlayDex search service"""
    print("\n=== Testing PlayDex Search Service ===")
    
    search = PlayDexSearch()
    extractor = GeminiEntityExtractor()
    
    # Test buzzer beater search
    print("\n1. Testing buzzer beater search via service")
    query = "damian lillard buzzer beaters"
    entities = extractor._simple_extract(query)
    
    try:
        results = search.search_clips(entities, limit=5)
        print(f"Found {len(results)} results")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result.description}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing Buzzer Beaters and Game Winners\n")
    
    test_entity_extraction()
    print("\n" + "="*50 + "\n")
    
    test_playdex_engine()
    print("\n" + "="*50 + "\n")
    
    test_playdex_search()