"""
Search API Endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException
from app.models.search import SearchRequest, SearchResponse, AIResponse
from app.services.gemini_entity_extractor import GeminiEntityExtractor
from app.services.simple_search import SimpleSearch
from app.services.video_search import VideoSearch
from app.services.fast_search import FastSearch
from app.services.efficient_search import EfficientSearch
from app.services.playdex_search import PlayDexSearch

router = APIRouter()

# Initialize services
entity_extractor = GeminiEntityExtractor()
simple_search = SimpleSearch()
video_search = VideoSearch()
fast_search = FastSearch()
efficient_search = EfficientSearch()
playdex_search = PlayDexSearch()


@router.post("/search/direct")
async def search_direct(request: SearchRequest):
    """
    Direct search using PlayDex engine - returns raw video data format
    This is the most efficient endpoint for getting video results
    """
    try:
        # Use PlayDex's direct search
        result = playdex_search.search_direct(request.query)
        return result
        
    except Exception as e:
        print(f"PlayDex direct search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An error occurred during search")


@router.post("/search", response_model=SearchResponse)
async def search_clips(request: SearchRequest):
    """
    Search for sports clips using natural language
    """
    try:
        # Extract entities from query
        entities = entity_extractor.extract_entities_sync(request.query)
        
        print(f"Searching for: {request.query}")
        print(f"Extracted entities: {entities.model_dump()}")
        
        # Get pagination parameters
        limit = request.limit or 15
        offset = request.offset or 0
        
        # Search for clips - try video search first, fallback to simple search
        results = []
        total_results = 0
        
        # For buzzer beaters and game winners, we need play-by-play data
        # NBA API only has "Last 10 Seconds" but true buzzer beaters are 0:00-0:01
        if entities.action_detail in ["buzzer beater", "game winner"] and offset == 0:
            print(f"Using video search for {entities.action_detail} (requires precise time data)")
            try:
                results = video_search.search_clips(entities, limit=limit, offset=offset)
                has_more = len(results) == limit
            except Exception as e:
                print(f"Video search error: {e}")
                results = []
                has_more = False
        else:
            # Use PlayDex search for regular queries
            try:
                results = playdex_search.search_clips(entities, limit=limit, offset=offset)
                has_more = len(results) == limit
                
                if not results and offset == 0:
                    # Fallback to video search for empty results
                    print("PlayDex search returned no results, falling back to video search")
                    results = video_search.search_clips(entities, limit=limit, offset=offset)
                    has_more = len(results) == limit
            except Exception as e:
                print(f"Search engine error: {e}")
                # General fallback to video search
                try:
                    if offset == 0:
                        results = video_search.search_clips(entities, limit=limit, offset=offset)
                        has_more = len(results) == limit
                    else:
                        results = []
                        has_more = False
                except:
                    results = []
                    has_more = False
        
        # Generate AI response
        ai_response = AIResponse(
            summary=f"Found {len(results)} clips matching '{request.query}'" if results else f"Searching for '{request.query}' - try a simpler query like 'LeBron dunks' or 'Curry threes'",
            resultCount=len(results),
            insights=_generate_insights(results, entities)
        )
        
        # Return response with pagination info
        return SearchResponse(
            results=results,
            total=len(results),  # This is just current page count
            entities=entities.model_dump(),
            aiResponse=ai_response,
            hasMore=has_more,
            offset=offset,
            limit=limit
        )
        
    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An error occurred during search")


def _generate_insights(results: List, entities) -> List[str]:
    """Generate insights about search results"""
    insights = []
    
    if not results:
        insights.append("No clips found. Try broadening your search.")
        return insights
    
    # Basic insights
    if entities.player:
        insights.append(f"Showing clips featuring {entities.player}")
    
    if entities.action:
        action_names = {
            'dunk': 'dunks',
            'block': 'blocks',
            'three': '3-pointers',
            'steal': 'steals',
            'assist': 'assists',
            'layup': 'layups',
            'jumper': 'jump shots'
        }
        action_text = action_names.get(entities.action, entities.action)
        
        # Add action detail if present
        if entities.action_detail:
            action_text = f"{entities.action_detail} {action_text}"
        
        insights.append(f"Focused on {action_text}")
    
    if len(results) > 10:
        insights.append("Many clips available - showing most recent")
    
    return insights