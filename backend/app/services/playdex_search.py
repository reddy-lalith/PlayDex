"""
PlayDex Search Service
High-performance search engine with advanced NLP and video retrieval
"""
from typing import List, Dict, Optional
import pandas as pd
from app.models.search import (
    SearchResult, SearchResultMetadata, VideoLinks, 
    PlayData, ExtractedEntities
)
from app.services.playdex_engine.search_engine import SearchEngine as PlayDexEngine
import uuid as uuid_lib
from datetime import datetime


class PlayDexSearch:
    """Search service using the PlayDex engine for NBA video search"""
    
    def __init__(self):
        # Initialize PlayDex engine with current season
        self.engine = PlayDexEngine(season="2024-25")
        
    def search_direct(self, query: str) -> Dict:
        """
        Direct search using PlayDex engine - returns raw video data
        This is the most efficient way to get results
        """
        try:
            # Execute search using PlayDex engine
            df = self.engine.query(query)
            
            if df is None or df.empty:
                return {"query": query, "data": []}
            
            # Convert DataFrame to list of dictionaries (raw video format)
            data = df.to_dict(orient='records')
            return {"query": query, "data": data}
            
        except Exception as e:
            print(f"PlayDex search error: {e}")
            import traceback
            traceback.print_exc()
            return {"query": query, "data": [], "error": str(e)}
    
    def search_clips(self, entities: ExtractedEntities, limit: int = 15, offset: int = 0) -> List[SearchResult]:
        """
        Search for clips using PlayDex engine with format conversion
        """
        try:
            # Build query string from entities
            query = self._build_query_from_entities(entities)
            
            if not query:
                return []
            
            print(f"PlayDex search query: {query}")
            
            # Execute search using PlayDex engine
            df = self.engine.query(query)
            
            if df is None or df.empty:
                print("No results from PlayDex engine")
                return []
            
            # Convert DataFrame to SearchResult objects
            results = self._convert_to_search_results(df)
            
            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            paginated_results = results[start_idx:end_idx]
            
            return paginated_results
            
        except Exception as e:
            print(f"PlayDex search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _build_query_from_entities(self, entities: ExtractedEntities) -> str:
        """Build a query string from extracted entities"""
        query_parts = []
        
        # Add player name
        if entities.player:
            query_parts.append(entities.player)
        
        # Add action
        if entities.action:
            # Map action terms for search
            action_mapping = {
                'dunk': 'dunks',
                'block': 'blocks',
                'three': '3-pointers',
                'steal': 'steals',
                'assist': 'assists',
                'layup': 'layups',
                'jumper': 'jump shots'
            }
            action_text = action_mapping.get(entities.action, entities.action)
            
            # Add action detail if present
            if entities.action_detail:
                # Handle specific action details
                if entities.action_detail == "buzzer beater":
                    query_parts.append("buzzer beater")  # Keep as is, engine now handles it
                elif entities.action_detail == "game winner":
                    query_parts.append("game winner")  # Keep as is, engine now handles it
                else:
                    query_parts.append(f"{entities.action_detail} {action_text}")
            else:
                query_parts.append(action_text)
        elif entities.action_detail:
            # If we only have action detail (like "buzzer beater"), add it
            query_parts.append(entities.action_detail)
        
        # Add time range
        if entities.time_range:
            # Map time ranges for search engine
            if entities.time_range == "last week":
                query_parts.append("last 7 days")
            elif entities.time_range == "last month":
                query_parts.append("last 30 days")
            else:
                query_parts.append(entities.time_range)
        
        # Add season
        if entities.season:
            query_parts.append(entities.season)
        
        # Add team context
        if entities.team:
            query_parts.append(f"against {entities.team}")
        
        # Add shot details if present
        if hasattr(entities, 'shot_details') and entities.shot_details:
            if entities.shot_details.get('distance'):
                query_parts.append(f"from {entities.shot_details['distance']} feet")
        
        # If no specific query parts, just search for the player
        if not query_parts and entities.player:
            query_parts = [entities.player, "points"]  # Default to points
        
        return ' '.join(query_parts)
    
    def _convert_to_search_results(self, df: pd.DataFrame) -> List[SearchResult]:
        """Convert PlayDex DataFrame results to SearchResult objects"""
        results = []
        
        for _, row in df.iterrows():
            try:
                # Extract game and event IDs
                game_id = str(row.get('Game_ID', ''))
                event_id = int(row.get('Event_Index', 0))
                
                # Create PlayData
                play_data = PlayData(
                    GAME_ID=game_id,
                    EVENTNUM=event_id,
                    PERIOD=int(row.get('Period', 0)),
                    PCTIMESTRING='',  # Not in current format
                    HOMEDESCRIPTION=None,  # Will be in Description
                    VISITORDESCRIPTION=None,  # Will be in Description
                    SCORE=None,  # Not available in current format
                    SCOREMARGIN=None  # Not available in current format
                )
                
                # Extract description
                description = row.get('Description', '')
                
                # Create video links using the actual video and thumbnail URLs
                video_url = row.get('Video_Link', '')
                thumbnail_url = row.get('Thumbnail_Link', '/api/placeholder/320/180')
                
                # Include the actual video URL
                video_links = VideoLinks(
                    nba_stats=f"https://www.nba.com/stats/events/?flag=1&GameID={game_id}&GameEventID={event_id}",
                    nba_game=f"https://www.nba.com/game/{game_id}",
                    youtube_search=f"https://youtube.com/results?search_query=NBA+{description.replace(' ', '+')}",
                    nba_video=video_url if video_url else None  # Add the actual video URL
                )
                
                # Parse date
                try:
                    game_date = pd.to_datetime(row.get('Game_Date'))
                except:
                    game_date = datetime.now()
                
                # Extract teams
                home_team = row.get('Home_Team', '')
                visitor_team = row.get('Visitor_Team', '')
                teams = [team for team in [home_team, visitor_team] if team]
                
                # Create metadata
                metadata = SearchResultMetadata(
                    date=game_date,
                    gameId=game_id,
                    teams=teams,
                    quarter=int(row.get('Period', 0)),
                    timeRemaining='',  # Not in current format
                    players=[],  # Could extract from description
                    action=self._extract_action_from_description(description)
                )
                
                # Create search result with the actual thumbnail
                result = SearchResult(
                    id=str(uuid_lib.uuid4()),
                    playData=play_data,
                    previewThumbnail=thumbnail_url,  # Using actual NBA thumbnail
                    watchLinks=video_links,
                    description=description,
                    metadata=metadata
                )
                
                results.append(result)
                
            except Exception as e:
                print(f"Error converting row to SearchResult: {e}")
                continue
        
        return results
    
    def _extract_action_from_description(self, description: str) -> str:
        """Extract the primary action from play description"""
        description_lower = description.lower()
        
        if 'dunk' in description_lower or 'slam' in description_lower:
            return 'dunk'
        elif 'block' in description_lower:
            return 'block'
        elif '3pt' in description_lower or 'three' in description_lower or '3-pt' in description_lower:
            return 'three'
        elif 'steal' in description_lower:
            return 'steal'
        elif 'assist' in description_lower:
            return 'assist'
        elif 'layup' in description_lower:
            return 'layup'
        elif 'jump shot' in description_lower or 'jumper' in description_lower:
            return 'jumper'
        elif 'free throw' in description_lower:
            return 'free throw'
        else:
            return 'play'