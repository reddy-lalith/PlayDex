"""
Player and team data cache - loaded at startup
"""
import json
from typing import Dict, List, Optional
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonallplayers
import time


class PlayerCache:
    """Cache player and team data to reduce API calls"""
    
    def __init__(self):
        self.players_by_name: Dict[str, Dict] = {}
        self.players_by_id: Dict[str, Dict] = {}
        self.teams_by_name: Dict[str, Dict] = {}
        self.teams_by_id: Dict[str, Dict] = {}
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Load all player and team data at startup"""
        print("Initializing player and team cache...")
        
        # Load static player data first (no API call)
        try:
            all_players = players.get_players()
            for player in all_players:
                name_lower = player['full_name'].lower()
                self.players_by_name[name_lower] = player
                self.players_by_id[str(player['id'])] = player
            print(f"Loaded {len(all_players)} players from static data")
        except Exception as e:
            print(f"Error loading static players: {e}")
        
        # Load team data (no API call)
        try:
            all_teams = teams.get_teams()
            for team in all_teams:
                self.teams_by_name[team['nickname'].lower()] = team
                self.teams_by_name[team['abbreviation'].lower()] = team
                self.teams_by_id[str(team['id'])] = team
            print(f"Loaded {len(all_teams)} teams from static data")
        except Exception as e:
            print(f"Error loading teams: {e}")
    
    def get_player_by_name(self, name: str) -> Optional[Dict]:
        """Get player data by name (case insensitive)"""
        return self.players_by_name.get(name.lower())
    
    def get_player_by_id(self, player_id: str) -> Optional[Dict]:
        """Get player data by ID"""
        return self.players_by_id.get(str(player_id))
    
    def search_players(self, query: str) -> List[Dict]:
        """Search for players by partial name match"""
        query_lower = query.lower()
        matches = []
        
        for name, player in self.players_by_name.items():
            if query_lower in name:
                matches.append(player)
        
        # Sort by relevance (exact matches first)
        matches.sort(key=lambda p: (
            not p['full_name'].lower().startswith(query_lower),
            p['full_name']
        ))
        
        return matches[:10]  # Return top 10 matches


# Global instance
player_cache = PlayerCache()