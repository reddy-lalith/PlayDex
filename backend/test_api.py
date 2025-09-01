"""
Simple test script for PlayDex API
"""
import asyncio
from app.services.entity_extractor import EntityExtractor
from app.services.search_engine import SearchEngine

async def test_entity_extractor():
    """Test entity extraction"""
    extractor = EntityExtractor()
    
    test_queries = [
        "lebron james dunks from last week",
        "steph curry 3-pointers",
        "giannis blocks in 2023",
        "durant assists this season"
    ]
    
    print("Testing Entity Extractor:")
    print("-" * 50)
    
    for query in test_queries:
        entities = extractor.extract_entities(query)
        print(f"\nQuery: '{query}'")
        print(f"Extracted: {entities.model_dump()}")

async def test_search_engine():
    """Test search engine (requires NBA API)"""
    extractor = EntityExtractor()
    engine = SearchEngine()
    
    print("\n\nTesting Search Engine:")
    print("-" * 50)
    
    # Test with LeBron search
    query = "lebron james dunks"
    entities = extractor.extract_entities(query)
    
    print(f"\nSearching for: '{query}'")
    print("This may take a moment...")
    
    try:
        results = engine.search_clips(entities)
        print(f"Found {len(results)} results")
        
        if results:
            print("\nFirst result:")
            print(f"- Description: {results[0].description}")
            print(f"- NBA Link: {results[0].watchLinks.nba_stats}")
            print(f"- YouTube Search: {results[0].watchLinks.youtube_search}")
    except Exception as e:
        print(f"Error during search: {e}")
        print("Note: NBA API may require specific game data to be available")

if __name__ == "__main__":
    asyncio.run(test_entity_extractor())
    # Uncomment to test search (requires NBA API access)
    # asyncio.run(test_search_engine())