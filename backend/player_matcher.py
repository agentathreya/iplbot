from fuzzywuzzy import fuzz, process
from typing import List, Dict, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)

class PlayerNameMatcher:
    def __init__(self, all_players: List[str]):
        self.all_players = all_players
        self.player_variations = self._create_player_variations()
    
    def _create_player_variations(self) -> Dict[str, str]:
        """Create variations of player names for better matching"""
        variations = {}
        
        for player in self.all_players:
            if not player:
                continue
                
            # Store full name
            variations[player.lower()] = player
            
            # Create variations
            parts = player.split()
            
            # First name + Last name
            if len(parts) >= 2:
                first_last = f"{parts[0]} {parts[-1]}"
                variations[first_last.lower()] = player
                
                # Just first name
                variations[parts[0].lower()] = player
                
                # Just last name  
                variations[parts[-1].lower()] = player
                
                # Initials + Last name (like V Kohli for Virat Kohli)
                if len(parts[0]) > 1:
                    initial_last = f"{parts[0][0]} {parts[-1]}"
                    variations[initial_last.lower()] = player
            
            # Remove common prefixes/suffixes
            clean_name = re.sub(r'^(Mr|Ms|Dr)\.?\s*', '', player, flags=re.IGNORECASE)
            if clean_name != player:
                variations[clean_name.lower()] = player
        
        return variations
    
    def find_best_match(self, query_name: str, threshold: int = 70) -> Optional[str]:
        """Find the best matching player name"""
        if not query_name:
            return None
            
        query_name = query_name.strip()
        query_lower = query_name.lower()
        
        # Direct match in variations
        if query_lower in self.player_variations:
            return self.player_variations[query_lower]
        
        # Fuzzy match on full names
        best_match = process.extractOne(
            query_name, 
            self.all_players, 
            scorer=fuzz.partial_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            return best_match[0]
        
        # Fuzzy match on variations
        variation_keys = list(self.player_variations.keys())
        best_variation = process.extractOne(
            query_lower,
            variation_keys,
            scorer=fuzz.ratio
        )
        
        if best_variation and best_variation[1] >= threshold:
            return self.player_variations[best_variation[0]]
        
        return None
    
    def find_multiple_matches(self, query_name: str, limit: int = 5, threshold: int = 60) -> List[Tuple[str, int]]:
        """Find multiple possible matches for a query"""
        if not query_name:
            return []
            
        # Get fuzzy matches
        matches = process.extract(
            query_name,
            self.all_players,
            scorer=fuzz.partial_ratio,
            limit=limit
        )
        
        # Filter by threshold
        return [(match[0], match[1]) for match in matches if match[1] >= threshold]
    
    def extract_player_names_from_query(self, query: str) -> List[str]:
        """Extract potential player names from a natural language query"""
        # Common cricket query patterns
        patterns = [
            r'(?:stats|performance|record|average|runs|wickets)(?:\s+(?:of|for|by))?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s+(?:vs|against|batting|bowling)',
            r'(?:best|worst|top|highest|lowest)\s+(?:batting|bowling)?\s*(?:by|from)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s+(?:in|during|at)'
        ]
        
        potential_names = []
        
        for pattern in patterns:
            matches = re.findall(pattern, query)
            potential_names.extend(matches)
        
        # Remove duplicates and clean
        unique_names = list(set(potential_names))
        
        # Match against our player database
        matched_names = []
        for name in unique_names:
            best_match = self.find_best_match(name)
            if best_match and best_match not in matched_names:
                matched_names.append(best_match)
        
        return matched_names