from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Player(BaseModel):
    id: str
    name: str
    team: Optional[str] = None


class PlayData(BaseModel):
    GAME_ID: str
    EVENTNUM: int
    PERIOD: int
    PCTIMESTRING: str
    HOMEDESCRIPTION: Optional[str] = None
    VISITORDESCRIPTION: Optional[str] = None
    SCORE: Optional[str] = None
    SCOREMARGIN: Optional[str] = None


class VideoLinks(BaseModel):
    nba_stats: Optional[str] = None
    nba_video: Optional[str] = None  # Direct video URL from VideoEvents endpoint
    nba_game: str
    youtube_search: str


class SearchResultMetadata(BaseModel):
    date: datetime
    gameId: str
    teams: List[str]
    quarter: int
    timeRemaining: str
    players: List[Player]
    action: str


class SearchResult(BaseModel):
    id: str
    playData: PlayData
    previewThumbnail: str
    watchLinks: VideoLinks
    description: str
    metadata: SearchResultMetadata


class AIResponse(BaseModel):
    summary: str
    resultCount: int
    insights: List[str]


class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    limit: Optional[int] = Field(default=15, description="Number of results per page")
    offset: Optional[int] = Field(default=0, description="Number of results to skip for pagination")


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    entities: Dict[str, Any]
    aiResponse: AIResponse
    hasMore: bool = Field(default=False, description="Whether more results are available")
    offset: int = Field(default=0, description="Current offset for pagination")
    limit: int = Field(default=15, description="Current limit per page")


class ExtractedEntities(BaseModel):
    player: Optional[str] = None
    player_id: Optional[str] = None
    action: Optional[str] = None
    action_detail: Optional[str] = None  # e.g., "step back", "fadeaway", "pull up"
    season: Optional[str] = None
    team: Optional[str] = None
    time_range: Optional[str] = None
    sport: str = "basketball"