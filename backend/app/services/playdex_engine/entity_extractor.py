import re
import spacy
from datetime import datetime
from app.services.playdex_engine.keywords_constants import SHOT_SPECIFIER_MAP, SCORE_SPECIFIER_MAP, CONTEXT_MEASURE_MAP, MONTH_MAP, CLUTCH_KEYWORDS, SEASON_KEYWORDS, CLUTCH_TIME_MAP
from rapidfuzz import process, fuzz


class EntityExtractor:
    def __init__(self, nlp, team_matcher, player_matcher, active_players, first_name_to_full_names, last_name_to_full_names):
        self.nlp = nlp
        self.team_matcher = team_matcher
        self.player_matcher = player_matcher
        self.active_players = active_players
        self.first_name_to_full_names = first_name_to_full_names
        self.last_name_to_full_names = last_name_to_full_names
        
    def reformulate_query(self, user_query):
        """
        Reformulates the user query by matching it to the nearest player names, context keywords, or month names.
        
        Parameters:
        - user_query: The original user input string.
        
        Returns:
        - A reformulated query string with corrected player names and keywords.
        """
        # Step 1: Separate the keyword categories
        player_names = list(self.active_players.keys())
        context_keywords = [word for measure in CONTEXT_MEASURE_MAP for word in CONTEXT_MEASURE_MAP[measure]]
        month_keywords = list(MONTH_MAP.keys())
        specifier_keywords = list(SHOT_SPECIFIER_MAP.keys())
        score_keywords = list(SCORE_SPECIFIER_MAP.keys())
        non_player_keywords = context_keywords + month_keywords + specifier_keywords + CLUTCH_KEYWORDS + SEASON_KEYWORDS + score_keywords

        # Step 2: Perform fuzzy matching on the entire query using player names
        matched_fragment, score, _ = process.extractOne(user_query.lower(), [p.lower() for p in player_names], scorer=fuzz.partial_ratio)

        # Step 3: Remove the matched fragment (typo version) from the query if the score is high enough
        if score > 70:
            matched_player_name = player_names[[p.lower() for p in player_names].index(matched_fragment)]
            remaining_query = self.remove_fragment(user_query, matched_player_name)
        else:
            matched_player_name = None
            remaining_query = user_query

        # Step 4: Apply word-level fuzzy matching on the remaining query
        reformulated_words = []
        query_words = remaining_query.split()
        for word in query_words:
            # Perform word-level matching using non-player keywords
            match, score, _ = process.extractOne(word.lower(), [kw.lower() for kw in non_player_keywords], scorer=fuzz.ratio)

            # Replace the word if a close match is found in context or month keywords
            if score > 85:
                matched_keyword = non_player_keywords[[kw.lower() for kw in non_player_keywords].index(match)]
                reformulated_words.append(matched_keyword)
            else:
                reformulated_words.append(word)

        # Step 5: Reconstruct the query with the correctly matched player name
        if matched_player_name:
            reformulated_query = f"{matched_player_name} " + " ".join(reformulated_words)
        else:
            reformulated_query = " ".join(reformulated_words)
        return reformulated_query

    def remove_fragment(self, query, fragment):
        """
        Removes a fragment from the query, allowing for misspellings and partial matches.
        
        Parameters:
        - query: The original user query.
        - fragment: The correctly spelled fragment to be removed.
        
        Returns:
        - The query string with the fragment removed.
        """
        query_words = query.lower().split()
        fragment_words = fragment.lower().split()
        
        # Find the best matching sequence in the query
        best_start = 0
        best_length = 0
        best_score = 0
        
        for i in range(len(query_words)):
            for j in range(i + 1, min(len(query_words) + 1, i + len(fragment_words) + 2)):  # Allow for +1 word
                sequence = ' '.join(query_words[i:j])
                score = fuzz.ratio(sequence, fragment.lower())
                if score > best_score:
                    best_score = score
                    best_start = i
                    best_length = j - i
        
        # Remove the best matching sequence if the score is high enough
        if best_score > 70:  # Adjust this threshold as needed
            del query_words[best_start:best_start + best_length]
        
        return ' '.join(query_words)
        
        
    def extract_entities(self, query):
        from app.services.playdex_engine.utils import preprocess_query  # Import here to avoid circular dependency
        cleaned_query = preprocess_query(query)
        cleaned_query = self.reformulate_query(cleaned_query)
        doc = self.nlp(cleaned_query)

        player_name = self._extract_player_name(doc)
        team_name = self._extract_team_name(doc)
        season_type = self._extract_season_type(cleaned_query)
        context_measures, shot_specifiers = self.get_context_measures(cleaned_query)
        score_specifers = self._extract_score_specifiers(cleaned_query)
        month = self._extract_month(cleaned_query)
        clutch_time = self._extract_clutch_time(cleaned_query)
        season = self._extract_season(query)  # Use original query to preserve year format

        return player_name, team_name, season_type, context_measures, month, clutch_time, shot_specifiers, score_specifers, season

    def get_context_measures(self, user_input):
        """
        Determine all relevant Context_Measures and specific shot specifiers based on the keywords in the user input.
        
        :param user_input: String input from the user.
        :return: A tuple (list of context measures, list of specific play type keywords).
        """
        doc = self.nlp(user_input.lower())
        found_measures = set()
        shot_specifiers = []

        # Convert the user input to a set of canonical shot specifiers
        canonical_specifiers = set()
        canonical_score_specifiers = []
        
        # First check for multi-word patterns in SHOT_SPECIFIER_MAP
        lower_input = user_input.lower()
        for phrase, canonical in SHOT_SPECIFIER_MAP.items():
            # Use word boundaries to avoid false matches (e.g., "step" in "misstep")
            if re.search(r'\b' + re.escape(phrase) + r'\b', lower_input):
                canonical_specifiers.add(canonical)
                if canonical == '3PT':
                    found_measures.add("PTS")
                    shot_specifiers.append(phrase)

        # Check for individual keywords against context measure map and shot specifier map
        for token in doc:

            normalized_text = token.text
            
            # Check if the token matches a context measure keyword
            for measure, keywords in CONTEXT_MEASURE_MAP.items():
                if normalized_text in keywords:
                    found_measures.add(measure)
                    if measure == "PTS" and normalized_text not in shot_specifiers:
                        shot_specifiers.append(normalized_text)
            
            # Check if the token matches a shot specifier and capture its canonical form
            if normalized_text in SHOT_SPECIFIER_MAP:
                canonical_form = SHOT_SPECIFIER_MAP[normalized_text]
                if canonical_form not in canonical_specifiers:
                    canonical_specifiers.add(canonical_form)
        
        # If no context measures are found, default to PTS
        if not found_measures:
            found_measures.add("PTS")

        # Add the canonical shot specifiers to the shot_specifiers list
        shot_specifiers = list(canonical_specifiers)
        return list(found_measures), shot_specifiers 

    def _extract_score_specifiers(self, query):
        score_specifiers = []
        for spec in SCORE_SPECIFIER_MAP:
            if re.search(rf"\b{re.escape(spec)}\b", query):
                score_specifiers.append(SCORE_SPECIFIER_MAP[spec])
        if not score_specifiers:
            return None
        
        return score_specifiers[0]
    
    def _extract_clutch_time(self, query):
        
        # Define priority order (from most specific to least specific)
        priority_order = ["Last 10 Seconds", "Last 1 Minute", "Last 5 Minutes"]
        
        lower_query = query.lower()
        matches = []
        
        for phrase, clutch_value in CLUTCH_TIME_MAP.items():
            if re.search(rf"\b{re.escape(phrase)}\b", lower_query):
                matches.append(clutch_value)
        
        if not matches:
            return None
        
        # Sort matches based on priority
        sorted_matches = sorted(set(matches), key=lambda x: priority_order.index(x) if x in priority_order else 999)
        
        # Return the highest priority match
        return sorted_matches[0]
    
    def _extract_player_name(self, doc):
        player_matches = self.player_matcher(doc)
        if player_matches:
            match_id, start, end = player_matches[0]
            matched_text = doc[start:end].text.lower()

            if matched_text in self.active_players:
                return matched_text
            
        # If no full name match, try to match first and last names
        tokens = [token.text.lower() for token in doc]
        for i, token in enumerate(tokens):
            if token in self.first_name_to_full_names:
                if i + 1 < len(tokens) and ' '.join([token, tokens[i+1]]) in self.active_players:
                    return ' '.join([token, tokens[i+1]])
            if token in self.last_name_to_full_names:
                if len(self.last_name_to_full_names[token]) == 1:
                    return self.last_name_to_full_names[token][0]
                elif i > 0 and ' '.join([tokens[i-1], token]) in self.active_players:
                    return ' '.join([tokens[i-1], token])
        
        return None

    def _extract_team_name(self, doc):
        team_matches = self.team_matcher(doc)
        if team_matches:
            match_id, start, end = team_matches[0]
            return doc[start:end].text.lower()
        return None

    def _extract_season_type(self, query):
        season_type_patterns = {
            "Playoffs": r"\b(play[-\s]?offs?|postseason)\b",
            "Regular Season": r"\bregular season\b",
            "Pre Season": r"\b(pre[-\s]?season)\b",
            "All Star": r"\ball[-\s]?star\b"
        }

        for season, pattern in season_type_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return season
        return "Regular Season"

    def _extract_month(self, query):
        """
        Extract the month mentioned in the user query.
        
        :param query: User input query as a string.
        :return: The month as a string if found, else "0".
        """
        doc = self.nlp(query.lower())

        for token in doc:
            if token.text in MONTH_MAP:
                return MONTH_MAP[token.text]

        return "0"  # Default to "0" if no month is found
    
    def _extract_season(self, query):
        """
        Extract the season year from the user query.
        Looks for patterns like:
        - 2024-25
        - 2024-2025
        - 2024
        - 2015
        
        :param query: User input query as a string.
        :return: The season in format "YYYY-YY" or None if not found.
        """
        # Pattern for YYYY-YY or YYYY-YYYY format
        pattern1 = r'\b(20\d{2})[-\s]?(20)?(\d{2})\b'
        match1 = re.search(pattern1, query)
        
        if match1:
            year1 = match1.group(1)
            year2_digits = match1.group(3)
            # Convert to YYYY-YY format
            return f"{year1}-{year2_digits}"
        
        # Pattern for single year (e.g., 2024)
        pattern2 = r'\b(20\d{2})\b'
        match2 = re.search(pattern2, query)
        
        if match2:
            year = int(match2.group(1))
            
            # Special handling for All-Star games
            # All-Star games happen in February, so 2022 All-Star = 2021-22 season
            if "all star" in query.lower() or "all-star" in query.lower():
                prev_year = year - 1
                return f"{prev_year}-{str(year)[-2:]}"
            else:
                # For historical queries, when someone says "player in YYYY", 
                # they usually mean the season ending in that year
                # e.g., "LeBron in 2015" means 2014-15 season
                # But for current/future years, they mean the season starting that year
                current_year = datetime.now().year
                
                if year <= current_year:
                    # Historical query: use season ending in that year
                    prev_year = year - 1
                    return f"{prev_year}-{str(year)[-2:]}"
                else:
                    # Future query: use season starting in that year
                    next_year = str(year + 1)[-2:]
                    return f"{year}-{next_year}"
        
        return None  # Return None if no season is found