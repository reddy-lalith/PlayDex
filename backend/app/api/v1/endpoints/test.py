"""
Test endpoints with mock data
"""
from typing import List
from fastapi import APIRouter
from app.models.search import SearchRequest, SearchResponse, SearchResult, AIResponse
from app.models.search import PlayData, VideoLinks, SearchResultMetadata, Player
from datetime import datetime
import uuid

router = APIRouter()


@router.get("/health")
async def health_check():
    """Quick health check endpoint"""
    return {"status": "ok", "message": "Test endpoint is working"}


@router.post("/mock-search", response_model=SearchResponse)
async def mock_search(request: SearchRequest):
    """
    Mock search endpoint for testing frontend integration
    """
    # Mock results based on query
    mock_results = []
    
    if "lebron" in request.query.lower():
        mock_results.append(
            SearchResult(
                id=str(uuid.uuid4()),
                playData=PlayData(
                    GAME_ID="0022300145",
                    EVENTNUM=123,
                    PERIOD=3,
                    PCTIMESTRING="8:45",
                    HOMEDESCRIPTION="James DUNK (15 PTS)",
                    SCORE="78-72",
                    SCOREMARGIN="6"
                ),
                previewThumbnail="https://cdn.nba.com/teams/uploads/sites/1610612747/2023/05/lebron-dunk.jpg",
                watchLinks=VideoLinks(
                    nba_stats="https://www.nba.com/stats/events/?flag=1&GameID=0022300145&GameEventID=123",
                    nba_game="https://www.nba.com/game/0022300145",
                    youtube_search="https://youtube.com/results?search_query=NBA+LeBron+James+dunk+playoffs+2023"
                ),
                description="LeBron James powerful dunk in transition",
                metadata=SearchResultMetadata(
                    date=datetime.now(),
                    gameId="0022300145",
                    teams=["Lakers", "Warriors"],
                    quarter=3,
                    timeRemaining="8:45",
                    players=[Player(id="2544", name="LeBron James")],
                    action="dunk"
                )
            )
        )
        
        mock_results.append(
            SearchResult(
                id=str(uuid.uuid4()),
                playData=PlayData(
                    GAME_ID="0022300146",
                    EVENTNUM=245,
                    PERIOD=4,
                    PCTIMESTRING="2:30",
                    HOMEDESCRIPTION="James DUNK (28 PTS)",
                    SCORE="102-98",
                    SCOREMARGIN="4"
                ),
                previewThumbnail="https://cdn.nba.com/teams/uploads/sites/1610612747/2023/05/lebron-slam.jpg",
                watchLinks=VideoLinks(
                    nba_stats="https://www.nba.com/stats/events/?flag=1&GameID=0022300146&GameEventID=245",
                    nba_game="https://www.nba.com/game/0022300146",
                    youtube_search="https://youtube.com/results?search_query=NBA+LeBron+James+slam+dunk"
                ),
                description="LeBron James tomahawk slam in the 4th quarter",
                metadata=SearchResultMetadata(
                    date=datetime.now(),
                    gameId="0022300146",
                    teams=["Lakers", "Nuggets"],
                    quarter=4,
                    timeRemaining="2:30",
                    players=[Player(id="2544", name="LeBron James")],
                    action="dunk"
                )
            )
        )
    
    if "curry" in request.query.lower() or "steph" in request.query.lower():
        mock_results.append(
            SearchResult(
                id=str(uuid.uuid4()),
                playData=PlayData(
                    GAME_ID="0022300200",
                    EVENTNUM=89,
                    PERIOD=2,
                    PCTIMESTRING="5:12",
                    HOMEDESCRIPTION="Curry 3PT (18 PTS)",
                    SCORE="45-40",
                    SCOREMARGIN="5"
                ),
                previewThumbnail="https://cdn.nba.com/teams/uploads/sites/1610612744/2023/05/curry-three.jpg",
                watchLinks=VideoLinks(
                    nba_stats="https://www.nba.com/stats/events/?flag=1&GameID=0022300200&GameEventID=89",
                    nba_game="https://www.nba.com/game/0022300200",
                    youtube_search="https://youtube.com/results?search_query=Steph+Curry+deep+three+pointer"
                ),
                description="Stephen Curry hits a deep three from 35 feet",
                metadata=SearchResultMetadata(
                    date=datetime.now(),
                    gameId="0022300200",
                    teams=["Warriors", "Celtics"],
                    quarter=2,
                    timeRemaining="5:12",
                    players=[Player(id="201939", name="Stephen Curry")],
                    action="three"
                )
            )
        )
    
    # Generate AI response
    ai_response = AIResponse(
        summary=f"Found {len(mock_results)} clips matching '{request.query}'",
        resultCount=len(mock_results),
        insights=[
            f"Showing {len(mock_results)} highlight{'s' if len(mock_results) != 1 else ''}",
            "All clips link to official NBA sources",
            "Click on any clip to watch on NBA.com or search on YouTube"
        ] if mock_results else ["No clips found. Try searching for 'LeBron James' or 'Steph Curry'"]
    )
    
    return SearchResponse(
        results=mock_results,
        total=len(mock_results),
        entities={
            "query": request.query,
            "mock_data": True
        },
        aiResponse=ai_response
    )