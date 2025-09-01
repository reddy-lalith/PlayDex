"""
Test script to verify search improvements
"""
import asyncio
from app.services.gemini_entity_extractor import GeminiEntityExtractor
from app.services.efficient_search import EfficientSearch
from app.services.video_search import VideoSearch
import time


async def test_search(query: str):
    """Test a search query with both search methods"""
    print(f"\n{'='*60}")
    print(f"Testing query: {query}")
    print('='*60)
    
    # Extract entities
    extractor = GeminiEntityExtractor()
    entities = await extractor.extract_entities(query)
    print(f"Extracted entities: {entities.model_dump()}")
    
    # Test efficient search (ballharbor-inspired)
    print("\n--- Efficient Search (ballharbor-inspired) ---")
    efficient = EfficientSearch()
    start_time = time.time()
    
    try:
        results = efficient.search_clips(entities, limit=15)
        elapsed = time.time() - start_time
        print(f"Found {len(results)} results in {elapsed:.2f} seconds")
        
        if results:
            print("\nFirst 3 results:")
            for i, result in enumerate(results[:3]):
                print(f"{i+1}. {result.description}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Compare with original video search (optional)
    """
    print("\n--- Original Video Search ---")
    video = VideoSearch()
    start_time = time.time()
    
    try:
        results = video.search_clips(entities, limit=15)
        elapsed = time.time() - start_time
        print(f"Found {len(results)} results in {elapsed:.2f} seconds")
    except Exception as e:
        print(f"Error: {e}")
    """


async def main():
    """Run test searches"""
    test_queries = [
        "LeBron James dunks",
        "Steph Curry three pointers",
        "Dame buzzer beaters 2017",
        "Giannis blocks last week"
    ]
    
    for query in test_queries:
        await test_search(query)
        await asyncio.sleep(2)  # Delay between searches


if __name__ == "__main__":
    asyncio.run(main())