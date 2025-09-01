"""
Gemini-based Entity Extractor for natural language sports queries
"""
import json
import google.generativeai as genai
from typing import Dict, Optional
from app.models.search import ExtractedEntities
from app.core.config import settings


class GeminiEntityExtractor:
    """Extract sports entities using Google's Gemini AI"""
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            print("Warning: Gemini API key not configured")
        
        # Fallback player database for when Gemini is not available
        self.player_db = {
            "lebron james": {"id": "2544", "full_name": "LeBron James"},
            "lebron": {"id": "2544", "full_name": "LeBron James"},
            "stephen curry": {"id": "201939", "full_name": "Stephen Curry"},
            "steph curry": {"id": "201939", "full_name": "Stephen Curry"},
            "curry": {"id": "201939", "full_name": "Stephen Curry"},
            "giannis antetokounmpo": {"id": "203507", "full_name": "Giannis Antetokounmpo"},
            "giannis": {"id": "203507", "full_name": "Giannis Antetokounmpo"},
            "greek freak": {"id": "203507", "full_name": "Giannis Antetokounmpo"},
            "kevin durant": {"id": "201142", "full_name": "Kevin Durant"},
            "kd": {"id": "201142", "full_name": "Kevin Durant"},
            "durant": {"id": "201142", "full_name": "Kevin Durant"},
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
            
            # More current players
            "kyrie irving": {"id": "202681", "full_name": "Kyrie Irving"},
            "kyrie": {"id": "202681", "full_name": "Kyrie Irving"},
            "kawhi leonard": {"id": "202695", "full_name": "Kawhi Leonard"},
            "kawhi": {"id": "202695", "full_name": "Kawhi Leonard"},
            "anthony davis": {"id": "203076", "full_name": "Anthony Davis"},
            "ad": {"id": "203076", "full_name": "Anthony Davis"},
            "paul george": {"id": "202331", "full_name": "Paul George"},
            "pg": {"id": "202331", "full_name": "Paul George"},
            "jimmy butler": {"id": "202710", "full_name": "Jimmy Butler"},
            "butler": {"id": "202710", "full_name": "Jimmy Butler"},
            "devin booker": {"id": "1626164", "full_name": "Devin Booker"},
            "booker": {"id": "1626164", "full_name": "Devin Booker"},
            "ja morant": {"id": "1629630", "full_name": "Ja Morant"},
            "ja": {"id": "1629630", "full_name": "Ja Morant"},
            
            # Legends
            "kobe bryant": {"id": "977", "full_name": "Kobe Bryant"},
            "kobe": {"id": "977", "full_name": "Kobe Bryant"},
            "michael jordan": {"id": "893", "full_name": "Michael Jordan"},
            "mj": {"id": "893", "full_name": "Michael Jordan"},
            "jordan": {"id": "893", "full_name": "Michael Jordan"},
            "shaquille o'neal": {"id": "406", "full_name": "Shaquille O'Neal"},
            "shaq": {"id": "406", "full_name": "Shaquille O'Neal"},
            "tim duncan": {"id": "1495", "full_name": "Tim Duncan"},
            "duncan": {"id": "1495", "full_name": "Tim Duncan"},
            "magic johnson": {"id": "77142", "full_name": "Magic Johnson"},
            "magic": {"id": "77142", "full_name": "Magic Johnson"},
            "larry bird": {"id": "1449", "full_name": "Larry Bird"},
            "bird": {"id": "1449", "full_name": "Larry Bird"},
        }
    
    async def extract_entities(self, query: str) -> ExtractedEntities:
        """Extract entities using Gemini AI with fallback to rule-based extraction"""
        
        if self.model:
            try:
                # Use Gemini for extraction
                prompt = f"""
                You are a basketball expert. Extract entities from this search query: "{query}"
                
                Return ONLY a valid JSON object with these fields:
                - player: full player name (e.g., "LeBron James", "Stephen Curry")
                - action: main basketball action - use ONLY one of these: "dunk", "three", "block", "steal", "assist", "layup", "jumper", or null
                - action_detail: specific move type like "step back", "fadeaway", "pull up", "buzzer beater", "alley oop", "fast break", "euro step", "spin move", "crossover", "behind the back", "no look", "reverse", "windmill", "360", or null
                - season: NBA season format like "2023-24" or null (convert year to season, e.g., "2010" becomes "2009-10")
                - team: team name or null
                - game_context: context like "playoffs", "finals", "clutch", "overtime", or null
                
                Examples:
                - "steph curry step back three" -> {{"player": "Stephen Curry", "action": "three", "action_detail": "step back", "season": null, "team": null, "game_context": null}}
                - "lebron james poster dunk in the finals" -> {{"player": "LeBron James", "action": "dunk", "action_detail": null, "season": null, "team": null, "game_context": "finals"}}
                - "giannis spin move layup" -> {{"player": "Giannis Antetokounmpo", "action": "layup", "action_detail": "spin move", "season": null, "team": null, "game_context": null}}
                
                Important: Return ONLY the JSON object, no other text.
                """
                
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                print(f"Gemini response: {response_text}")
                
                # Try to extract JSON from the response
                # Sometimes Gemini adds markdown code blocks
                if response_text.startswith("```json"):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.startswith("```"):
                    response_text = response_text[3:]  # Remove ```
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Remove ```
                
                result = json.loads(response_text)
                
                # Look up player ID from our database
                player_id = None
                if result.get('player'):
                    player_lower = result['player'].lower()
                    for key, value in self.player_db.items():
                        if key in player_lower or player_lower in key:
                            player_id = value['id']
                            result['player'] = value['full_name']
                            break
                
                return ExtractedEntities(
                    player=result.get('player'),
                    player_id=player_id,
                    action=result.get('action'),
                    action_detail=result.get('action_detail'),
                    season=result.get('season'),
                    team=result.get('team'),
                    time_range=result.get('game_context'),
                    sport="basketball"
                )
                
            except Exception as e:
                print(f"Gemini extraction error: {e}")
                # Fall back to simple extraction
        
        # Fallback to simple extraction
        return self._simple_extract(query)
    
    def extract_entities_sync(self, query: str) -> ExtractedEntities:
        """Synchronous version for compatibility"""
        
        if self.model:
            try:
                # Use Gemini for extraction
                prompt = f"""
                You are a basketball expert. Extract entities from this search query: "{query}"
                
                Return ONLY a valid JSON object with these fields:
                - player: full player name (e.g., "LeBron James", "Stephen Curry")
                - action: main basketball action - use ONLY one of these: "dunk", "three", "block", "steal", "assist", "layup", "jumper", or null
                - action_detail: specific move type like "step back", "fadeaway", "pull up", "buzzer beater", "alley oop", "fast break", "euro step", "spin move", "crossover", "behind the back", "no look", "reverse", "windmill", "360", or null
                - season: NBA season format like "2023-24" or null (convert year to season, e.g., "2010" becomes "2009-10")
                - team: team name or null
                - game_context: context like "playoffs", "finals", "clutch", "overtime", or null
                
                Examples:
                - "steph curry step back three" -> {{"player": "Stephen Curry", "action": "three", "action_detail": "step back", "season": null, "team": null, "game_context": null}}
                - "lebron james poster dunk in the finals" -> {{"player": "LeBron James", "action": "dunk", "action_detail": null, "season": null, "team": null, "game_context": "finals"}}
                - "giannis spin move layup" -> {{"player": "Giannis Antetokounmpo", "action": "layup", "action_detail": "spin move", "season": null, "team": null, "game_context": null}}
                
                Important: Return ONLY the JSON object, no other text.
                """
                
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                print(f"Gemini response: {response_text}")
                
                # Try to extract JSON from the response
                # Sometimes Gemini adds markdown code blocks
                if response_text.startswith("```json"):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.startswith("```"):
                    response_text = response_text[3:]  # Remove ```
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Remove ```
                
                result = json.loads(response_text)
                
                # Look up player ID from our database
                player_id = None
                if result.get('player'):
                    player_lower = result['player'].lower()
                    for key, value in self.player_db.items():
                        if key in player_lower or player_lower in key:
                            player_id = value['id']
                            result['player'] = value['full_name']
                            break
                
                return ExtractedEntities(
                    player=result.get('player'),
                    player_id=player_id,
                    action=result.get('action'),
                    action_detail=result.get('action_detail'),
                    season=result.get('season'),
                    team=result.get('team'),
                    time_range=result.get('game_context'),
                    sport="basketball"
                )
                
            except Exception as e:
                print(f"Gemini extraction error: {e}")
                # Fall back to simple extraction
        
        # Fallback to simple extraction
        return self._simple_extract(query)
    
    def _simple_extract(self, query: str) -> ExtractedEntities:
        """Simple fallback extraction when Gemini is not available"""
        query_lower = query.lower()
        
        # Extract player
        player = None
        player_id = None
        for player_key, player_info in self.player_db.items():
            if player_key in query_lower:
                player = player_info["full_name"]
                player_id = player_info["id"]
                break
        
        # Extract basic action
        action = None
        if "dunk" in query_lower or "slam" in query_lower:
            action = "dunk"
        elif "three" in query_lower or "3" in query_lower:
            action = "three"
        elif "block" in query_lower:
            action = "block"
        elif "steal" in query_lower:
            action = "steal"
        elif "assist" in query_lower or "pass" in query_lower:
            action = "assist"
        elif "layup" in query_lower:
            action = "layup"
        elif "jumper" in query_lower or "jump shot" in query_lower:
            action = "jumper"
        
        # Extract action detail
        action_detail = None
        if "buzzer beater" in query_lower or "buzzer-beater" in query_lower:
            action_detail = "buzzer beater"
        elif "game winner" in query_lower or "game-winner" in query_lower:
            action_detail = "game winner"
        elif "step back" in query_lower or "stepback" in query_lower:
            action_detail = "step back"
        elif "fadeaway" in query_lower or "fade away" in query_lower:
            action_detail = "fadeaway"
        elif "pull up" in query_lower or "pullup" in query_lower:
            action_detail = "pull up"
        elif "alley oop" in query_lower or "alley-oop" in query_lower:
            action_detail = "alley oop"
        elif "fast break" in query_lower or "fastbreak" in query_lower:
            action_detail = "fast break"
        
        return ExtractedEntities(
            player=player,
            player_id=player_id,
            action=action,
            action_detail=action_detail,
            sport="basketball"
        )