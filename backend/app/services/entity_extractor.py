"""
Entity Extractor Module
Handles natural language processing for sports queries
"""
from typing import Dict, List, Optional
import re
from app.models.search import ExtractedEntities


class EntityExtractor:
    """Extract and normalize sports entities from natural language queries"""
    
    def __init__(self):
        # Common NBA player names and their IDs
        self.player_db = {
            # LeBron
            "lebron james": {"id": "2544", "full_name": "LeBron James"},
            "lebron": {"id": "2544", "full_name": "LeBron James"},
            "king james": {"id": "2544", "full_name": "LeBron James"},
            
            # Curry
            "stephen curry": {"id": "201939", "full_name": "Stephen Curry"},
            "steph curry": {"id": "201939", "full_name": "Stephen Curry"},
            "curry": {"id": "201939", "full_name": "Stephen Curry"},
            
            # Giannis
            "giannis antetokounmpo": {"id": "203507", "full_name": "Giannis Antetokounmpo"},
            "giannis": {"id": "203507", "full_name": "Giannis Antetokounmpo"},
            
            # Durant
            "kevin durant": {"id": "201142", "full_name": "Kevin Durant"},
            "kd": {"id": "201142", "full_name": "Kevin Durant"},
            "durant": {"id": "201142", "full_name": "Kevin Durant"},
            
            # Other stars
            "luka doncic": {"id": "1629029", "full_name": "Luka Dončić"},
            "luka": {"id": "1629029", "full_name": "Luka Dončić"},
            "nikola jokic": {"id": "203999", "full_name": "Nikola Jokić"},
            "jokic": {"id": "203999", "full_name": "Nikola Jokić"},
            "joel embiid": {"id": "203954", "full_name": "Joel Embiid"},
            "embiid": {"id": "203954", "full_name": "Joel Embiid"},
            "jayson tatum": {"id": "1628369", "full_name": "Jayson Tatum"},
            "tatum": {"id": "1628369", "full_name": "Jayson Tatum"},
            "damian lillard": {"id": "203081", "full_name": "Damian Lillard"},
            "dame": {"id": "203081", "full_name": "Damian Lillard"},
            "lillard": {"id": "203081", "full_name": "Damian Lillard"},
        }
        
        # Common basketball actions
        self.actions = {
            "dunk": ["dunk", "dunks", "dunked", "slam", "jam", "poster"],
            "block": ["block", "blocks", "blocked", "rejection", "swat"],
            "three": ["three", "3-pointer", "3pt", "3-point", "three-pointer", "triple"],
            "steal": ["steal", "steals", "stole", "pickpocket"],
            "assist": ["assist", "assists", "pass", "dime"],
            "layup": ["layup", "lay-up", "finger roll"],
            "jumper": ["jumper", "jump shot", "mid-range"],
        }
        
        # Shot modifiers and play details
        self.action_details = {
            "step back": ["step back", "stepback", "step-back"],
            "fadeaway": ["fadeaway", "fade away", "fade-away", "turnaround"],
            "pull up": ["pull up", "pullup", "pull-up"],
            "buzzer beater": ["buzzer beater", "buzzer", "game winner", "clutch"],
            "alley oop": ["alley oop", "alley-oop", "lob"],
            "and one": ["and one", "and-one", "and 1"],
            "putback": ["putback", "put back", "tip in"],
            "fast break": ["fast break", "fastbreak", "transition"],
            "euro step": ["euro step", "eurostep", "euro-step"],
            "spin move": ["spin move", "spin"],
            "crossover": ["crossover", "cross over", "ankle breaker"],
            "behind the back": ["behind the back", "behind-the-back"],
            "no look": ["no look", "no-look"],
            "reverse": ["reverse"],
            "windmill": ["windmill"],
            "360": ["360"],
        }
        
        # Time-related keywords
        self.time_keywords = {
            "last week": 7,
            "last month": 30,
            "this season": "current_season",
            "playoffs": "playoffs",
            "finals": "finals",
        }
    
    def extract_entities(self, query: str) -> ExtractedEntities:
        """
        Extract and normalize sports entities from user query
        
        Example:
        Input: "lebron james blocks in 2012"
        Output: ExtractedEntities(
            player="LeBron James",
            player_id="2544",
            action="block",
            season="2012-13",
            sport="basketball"
        )
        """
        query_lower = query.lower()
        
        # Extract player
        player = None
        player_id = None
        for player_key, player_info in self.player_db.items():
            if player_key in query_lower:
                player = player_info["full_name"]
                player_id = player_info["id"]
                break
        
        # Extract action details first (they might include action words)
        action_detail = None
        for detail_key, detail_variants in self.action_details.items():
            for variant in detail_variants:
                if variant in query_lower:
                    action_detail = detail_key
                    break
            if action_detail:
                break
        
        # Extract action
        action = None
        for action_key, action_variants in self.actions.items():
            for variant in action_variants:
                if variant in query_lower:
                    action = action_key
                    break
            if action:
                break
        
        # Extract season/year
        season = None
        year_match = re.search(r'\b(19|20)\d{2}\b', query)
        if year_match:
            year = int(year_match.group())
            # Convert year to NBA season format
            season = f"{year}-{str(year + 1)[-2:]}"
        
        # Extract time range
        time_range = None
        for time_key in self.time_keywords:
            if time_key in query_lower:
                time_range = time_key
                break
        
        return ExtractedEntities(
            player=player,
            player_id=player_id,
            action=action,
            action_detail=action_detail,
            season=season,
            time_range=time_range,
            sport="basketball"
        )
    
    def spell_check(self, text: str) -> str:
        """Correct common misspellings in sports queries"""
        # Simple spell correction for common mistakes
        corrections = {
            "lebrom": "lebron",
            "currey": "curry",
            "gianis": "giannis",
            "durant": "durant",
            "tree pointer": "three pointer",
        }
        
        text_lower = text.lower()
        for wrong, correct in corrections.items():
            text_lower = text_lower.replace(wrong, correct)
        
        return text_lower
    
    def link_entities(self, entities: Dict) -> Dict:
        """Link entities to database IDs"""
        # This would connect to a real database in production
        # For now, it's already handled in extract_entities
        return entities