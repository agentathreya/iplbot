from groq import Groq
import re
import json
import logging
from typing import Dict, List, Optional, Any
from player_matcher import PlayerNameMatcher

logger = logging.getLogger(__name__)

class CricketQueryGenerator:
    def __init__(self, groq_api_key: str, player_matcher: PlayerNameMatcher):
        self.client = Groq(api_key=groq_api_key)
        self.player_matcher = player_matcher
        
        # Cricket-specific context and schema
        self.cricket_schema = """
        Table: ipl_data
        Columns:
        - series_id (INTEGER): Series identifier
        - season (TEXT): IPL season (e.g., '2008', '2023/24')
        - series (TEXT): Tournament name
        - match_type (TEXT): Format (T20)
        - year (INTEGER): Year of match
        - date (DATE): Match date
        - venue (TEXT): Stadium/Ground name
        - country (TEXT): Host country
        - match_id (INTEGER): Unique match identifier
        - match_no (TEXT): Match number in series
        - batting_team (TEXT): Team batting
        - bowling_team (TEXT): Team bowling
        - innings (INTEGER): Innings number (1 or 2)
        - over_col (INTEGER): Over number
        - ball (INTEGER): Ball number in over
        - ball_no (TEXT): Ball number (e.g., '0.1', '0.2')
        - batter_id (INTEGER): Batter ID
        - bowler_id (INTEGER): Bowler ID
        - batter (TEXT): Batter short name
        - batter_full_name (TEXT): Batter full name
        - non_striker (TEXT): Non-striker short name
        - non_striker_full_name (TEXT): Non-striker full name
        - bowler (TEXT): Bowler short name
        - bowler_full_name (TEXT): Bowler full name
        - runs_total (INTEGER): Total runs in this ball
        - runs_batter (INTEGER): Runs scored by batter
        - balls_faced (INTEGER): Balls faced by batter so far
        - valid_ball (INTEGER): 1 if valid ball, 0 if not
        - is_four (BOOLEAN): True if boundary (4)
        - is_six (BOOLEAN): True if six
        - is_wicket (BOOLEAN): True if wicket
        - player_out (TEXT): Player dismissed
        - dismissal_type (TEXT): How player got out
        - fielder (TEXT): Fielder involved in dismissal
        - is_wk (BOOLEAN): Is wicket-keeper
        - is_sub (BOOLEAN): Is substitute
        - byes (INTEGER): Bye runs
        - legbyes (INTEGER): Leg bye runs
        - wides (INTEGER): Wide runs
        - noballs (INTEGER): No ball runs
        - penalties (INTEGER): Penalty runs
        - wagon_x (INTEGER): Ball position X coordinate
        - wagon_y (INTEGER): Ball position Y coordinate
        - wagon_zone (INTEGER): Wagon wheel zone
        - pitch_line (TEXT): Line of ball (off, middle, leg)
        - pitch_length (TEXT): Length of ball (full, short, good)
        - shot_type (TEXT): Type of shot played
        - shot_control (INTEGER): Shot control rating
        - bat_hand (TEXT): Batting hand (LHB/RHB)
        - bowling_type (TEXT): Bowling type (pace/spin)
        - predicted_score (TEXT): Predicted match score
        - win_probability (TEXT): Win probability
        - team_runs (INTEGER): Team total runs
        - team_balls (INTEGER): Team total balls
        - team_wickets (INTEGER): Team wickets lost
        - player_of_match (TEXT): Player of the match
        - player_of_series (TEXT): Player of the series
        - winner (TEXT): Match winner
        - toss_winner (TEXT): Toss winner
        - toss_decision (TEXT): Toss decision
        - is_super_over (BOOLEAN): Super over indicator
        - result (TEXT): Match result
        - batting_captain (TEXT): Batting team captain
        - bowling_captain (TEXT): Bowling team captain
        - home_team (TEXT): Home team
        - day_game (BOOLEAN): Day game indicator
        - bat_pos (INTEGER): Batting position
        - event_type (TEXT): Event type
        - event_fielder (TEXT): Event fielder
        - event_batter (TEXT): Event batter
        - runs_target (INTEGER): Runs target
        - target_balls (INTEGER): Target balls
        - bowler_runs (INTEGER): Bowler runs conceded
        - bowler_wicket (BOOLEAN): Bowler took wicket
        - curr_batter_runs (INTEGER): Current batter runs
        - curr_batter_balls (INTEGER): Current batter balls
        - curr_batter_fours (INTEGER): Current batter fours
        - curr_batter_sixes (INTEGER): Current batter sixes
        - bowling_type (TEXT): Bowling type
        - required_rr (TEXT): Required run rate
        - current_rr (TEXT): Current run rate
        - batting_partners (TEXT): Batting partnership
        - striker_out (BOOLEAN): Striker out indicator
        
        Important Notes:
        - Death overs: overs 16-20 in T20 (over_col BETWEEN 16 AND 20)
        - Powerplay: overs 1-6 (over_col BETWEEN 1 AND 6)
        - Middle overs: overs 7-15 (over_col BETWEEN 7 AND 15)
        - LHB = Left Hand Batsman (bat_hand = 'LHB')
        - RHB = Right Hand Batsman (bat_hand = 'RHB')
        - Pace bowlers: bowling_type ILIKE '%pace%' or bowling_type ILIKE '%fast%' or bowling_type ILIKE '%medium%'
        - Spin bowlers: bowling_type ILIKE '%spin%'
        - Batting Average: SUM(runs_batter) / NULLIF(COUNT(CASE WHEN is_wicket = true THEN 1 END), 0)
        - Bowling Average: SUM(runs_total) / NULLIF(COUNT(CASE WHEN is_wicket = true THEN 1 END), 0)
        - Strike Rate: (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
        - Economy Rate: (SUM(runs_total) * 6.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
        """
    
    def extract_minimum_threshold(self, user_query: str) -> Optional[int]:
        """Extract minimum threshold from user query"""
        patterns = [
            r'min(?:imum)?\s+(\d+)\s+runs?',
            r'at least\s+(\d+)\s+runs?',
            r'more than\s+(\d+)\s+runs?',
            r'minimum\s+of\s+(\d+)\s+runs?',
            r'min\s+(\d+)',
            r'minimum\s+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_query.lower())
            if match:
                return int(match.group(1))
        
        return None

    def generate_sql_query(self, user_query: str, matched_players: List[str] = None) -> Dict[str, Any]:
        """Generate SQL query using Groq API"""
        
        # Extract player names from query if not provided
        if not matched_players:
            matched_players = self.player_matcher.extract_player_names_from_query(user_query)
        
        # Extract minimum threshold if specified
        min_threshold = self.extract_minimum_threshold(user_query)
        
        # Create enhanced prompt with player and threshold context
        player_context = ""
        if matched_players:
            player_context = f"\nDetected Players: {', '.join(matched_players)}"
        
        threshold_context = ""
        if min_threshold:
            threshold_context = f"\nMinimum Threshold: Use {min_threshold} runs as the HAVING condition instead of default values"
        
        prompt = f"""
        You are an expert cricket analyst and SQL query generator. Generate a PostgreSQL query to answer the user's cricket question.

        {self.cricket_schema}
        {player_context}
        {threshold_context}
        
        User Question: "{user_query}"
        
        Instructions:
        1. Generate ONLY a valid PostgreSQL SELECT query
        2. Use exact player names from the detected players list when available
        3. Handle partial names by using ILIKE with wildcards
        4. For batting stats, focus on batter_full_name and batting-related columns
        5. For bowling stats, focus on bowler_full_name and bowling-related columns
        6. For advanced queries like "best batters vs pace in death overs":
           - Filter by over_col BETWEEN 16 AND 20 for death overs
           - Filter by bowling_style containing 'pace' for pace bowlers
           - Group by batter_full_name and calculate aggregations
        7. For "best bowlers vs LHB in middle overs":
           - Filter by over_col BETWEEN 7 AND 15 for middle overs
           - Filter by bat_hand = 'LHB' for left-hand batsmen
           - Group by bowler_full_name and calculate bowling stats
        8. Use appropriate aggregations (SUM, AVG, COUNT, MAX, MIN)
        9. Order results meaningfully (best performance first)
        10. Limit results to reasonable numbers (typically TOP 10-20)
        11. Handle NULL values appropriately
        12. For strike rates, use: (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
        13. For bowling average, use: (SUM(runs_total) * 1.0 / COUNT(CASE WHEN is_wicket = true THEN 1 END))
        14. For economy rate, use: (SUM(runs_total) * 6.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
        15. ALWAYS apply minimum thresholds to filter meaningful results:
            - For batting queries: HAVING SUM(runs_batter) >= 500 (or user-specified minimum)
            - For bowling queries: HAVING COUNT(CASE WHEN valid_ball = 1 THEN 1 END) >= 300 (minimum balls bowled)
            - For death overs specifically: HAVING SUM(runs_batter) >= 200 (death over runs)
            - For powerplay: HAVING SUM(runs_batter) >= 300 (powerplay runs)
            - If user specifies "minimum X runs" or "min X runs", use that exact value
        16. Extract minimum values from user query if specified (e.g., "min 1000 runs", "minimum 500 runs")
        17. IMPORTANT: For boolean columns (is_four, is_six, is_wicket), use COUNT() not SUM():
            - For fours: COUNT(CASE WHEN is_four = true THEN 1 END) AS fours
            - For sixes: COUNT(CASE WHEN is_six = true THEN 1 END) AS sixes
            - For wickets: COUNT(CASE WHEN is_wicket = true THEN 1 END) AS wickets
        18. Available seasons in database: 2008-2024 (no 2025 data available yet)
        
        Return ONLY the SQL query, no explanations or formatting.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean the query
            sql_query = self._clean_sql_query(sql_query)
            
            return {
                "sql_query": sql_query,
                "matched_players": matched_players,
                "original_query": user_query
            }
            
        except Exception as e:
            logger.error(f"Error generating query with Groq: {e}")
            # Fallback to rule-based query generation
            return self._fallback_query_generation(user_query, matched_players)
    
    def _clean_sql_query(self, query: str) -> str:
        """Clean and validate the SQL query"""
        # Remove code block formatting
        query = re.sub(r'```sql\n?', '', query)
        query = re.sub(r'```\n?', '', query)
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Ensure it starts with SELECT
        if not query.upper().startswith('SELECT'):
            # Try to find SELECT in the query
            select_match = re.search(r'SELECT\s', query, re.IGNORECASE)
            if select_match:
                query = query[select_match.start():]
        
        return query.strip()
    
    def _fallback_query_generation(self, user_query: str, matched_players: List[str]) -> Dict[str, Any]:
        """Fallback rule-based query generation"""
        logger.info("Using fallback query generation")
        
        query_lower = user_query.lower()
        
        # Basic batting stats
        if any(word in query_lower for word in ['runs', 'batting', 'average', 'strike rate']):
            player_filter = ""
            if matched_players:
                player_names = "', '".join(matched_players)
                player_filter = f"WHERE batter_full_name IN ('{player_names}')"
            
            sql_query = f"""
            SELECT 
                batter_full_name,
                COUNT(*) as balls_faced,
                SUM(runs_batter) as total_runs,
                ROUND(AVG(runs_batter::numeric), 2) as avg_runs_per_ball,
                ROUND((SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END)), 2) as strike_rate,
                SUM(CASE WHEN is_four = true THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN is_six = true THEN 1 ELSE 0 END) as sixes
            FROM ipl_data 
            {player_filter}
            GROUP BY batter_full_name 
            HAVING COUNT(*) > 50
            ORDER BY total_runs DESC 
            LIMIT 20
            """
        
        # Basic bowling stats
        elif any(word in query_lower for word in ['bowling', 'wickets', 'economy']):
            player_filter = ""
            if matched_players:
                player_names = "', '".join(matched_players)
                player_filter = f"WHERE bowler_full_name IN ('{player_names}')"
            
            sql_query = f"""
            SELECT 
                bowler_full_name,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_bowled,
                SUM(runs_total) as runs_conceded,
                COUNT(CASE WHEN is_wicket = true THEN 1 END) as wickets,
                ROUND((SUM(runs_total) * 6.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END)), 2) as economy_rate,
                ROUND((SUM(runs_total) * 1.0 / NULLIF(COUNT(CASE WHEN is_wicket = true THEN 1 END), 0)), 2) as bowling_average
            FROM ipl_data 
            {player_filter}
            GROUP BY bowler_full_name 
            HAVING COUNT(CASE WHEN valid_ball = 1 THEN 1 END) > 100
            ORDER BY wickets DESC 
            LIMIT 20
            """
        
        else:
            # Default query - top run scorers
            sql_query = """
            SELECT 
                batter_full_name,
                SUM(runs_batter) as total_runs,
                COUNT(*) as balls_faced,
                ROUND((SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END)), 2) as strike_rate
            FROM ipl_data 
            GROUP BY batter_full_name 
            HAVING COUNT(*) > 100
            ORDER BY total_runs DESC 
            LIMIT 15
            """
        
        return {
            "sql_query": sql_query,
            "matched_players": matched_players,
            "original_query": user_query
        }
    
    def enhance_query_with_context(self, base_query: str, context: Dict[str, Any]) -> str:
        """Enhance base query with additional context"""
        enhanced_query = base_query
        
        # Add time-based filters
        if context.get('season'):
            enhanced_query += f" AND season = '{context['season']}'"
        
        if context.get('venue'):
            enhanced_query += f" AND venue ILIKE '%{context['venue']}%'"
        
        if context.get('team'):
            enhanced_query += f" AND (batting_team = '{context['team']}' OR bowling_team = '{context['team']}')"
        
        return enhanced_query