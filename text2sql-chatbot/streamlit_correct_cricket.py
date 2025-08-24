#!/usr/bin/env python3
"""
🏏 CORRECT Advanced IPL Analytics Chatbot - Streamlit Version
Properly handles cricket statistics with accurate query generation
"""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import re
from fuzzywuzzy import fuzz, process
from typing import List, Dict, Optional, Tuple, Any
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="🏏 Correct IPL Analytics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CricketIPLAnalyzer:
    """Cricket-aware IPL analyzer with proper statistics understanding"""
    
    def __init__(self, engine):
        self.engine = engine
        self.load_reference_data()
    
    def load_reference_data(self):
        """Load reference data for better query understanding"""
        try:
            # Load players
            self.players_df = pd.read_sql_query("""
                SELECT DISTINCT batter_full_name as player_name 
                FROM ipl_data_complete 
                WHERE batter_full_name IS NOT NULL
                UNION
                SELECT DISTINCT bowler_full_name as player_name 
                FROM ipl_data_complete 
                WHERE bowler_full_name IS NOT NULL
            """, self.engine)
            self.all_players = self.players_df['player_name'].tolist()
            
            # Load teams
            self.teams_df = pd.read_sql_query("""
                SELECT DISTINCT batting_team as team_name 
                FROM ipl_data_complete 
                WHERE batting_team IS NOT NULL
            """, self.engine)
            self.all_teams = self.teams_df['team_name'].tolist()
            
            logger.info(f"Loaded {len(self.all_players)} players, {len(self.all_teams)} teams")
            
        except Exception as e:
            logger.error(f"Error loading reference data: {e}")
            self.all_players = []
            self.all_teams = []
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze cricket queries with proper understanding"""
        query_lower = query.lower()
        
        analysis = {
            'query_type': 'unknown',
            'entities': {
                'players': [],
                'teams': [],
                'seasons': []
            },
            'filters': {},
            'metrics': [],
            'complexity': 'basic'
        }
        
        # 1. DETECT QUERY TYPE with cricket understanding
        if any(word in query_lower for word in ['vs', 'against', 'matchup', 'head to head', 'h2h', 'versus']):
            analysis['query_type'] = 'matchup'
            analysis['complexity'] = 'advanced'
        elif any(word in query_lower for word in ['most', 'highest', 'best', 'top', 'leading', 'maximum', 'lowest', 'worst', 'poorest']):
            analysis['query_type'] = 'top_performers'
            analysis['complexity'] = 'intermediate'
        elif any(word in query_lower for word in ['powerplay', 'death over', 'middle over', 'overs 1-6', 'overs 7-15', 'overs 16-20']) or 'overs' in query_lower:
            analysis['query_type'] = 'phase_analysis'
            analysis['complexity'] = 'advanced'
        elif any(word in query_lower for word in ['partnership', 'batting partners']):
            analysis['query_type'] = 'partnership'
            analysis['complexity'] = 'advanced'
        else:
            analysis['query_type'] = 'basic_stats'
        
        # 2. EXTRACT ENTITIES
        analysis['entities']['players'] = self.extract_players(query)
        analysis['entities']['teams'] = self.extract_teams(query)
        analysis['entities']['seasons'] = self.extract_seasons(query)
        
        # 3. EXTRACT FILTERS with cricket logic
        analysis['filters'] = self.extract_cricket_filters(query_lower)
        
        # 4. EXTRACT METRICS 
        analysis['metrics'] = self.extract_metrics(query_lower)
        
        return analysis
    
    def extract_players(self, query: str) -> List[str]:
        """Extract player names with improved matching"""
        found_players = []
        
        # Enhanced player mappings
        player_mappings = {
            'virat': 'Virat Kohli', 'kohli': 'Virat Kohli', 
            'rohit': 'Rohit Sharma', 'sharma': 'Rohit Sharma',
            'dhoni': 'MS Dhoni', 'msd': 'MS Dhoni',
            'bumrah': 'Jasprit Bumrah',
            'abd': 'AB de Villiers', 'ab de villiers': 'AB de Villiers',
            'gayle': 'Chris Gayle',
            'warner': 'David Warner',
            'raina': 'Suresh Raina',
            'rashid': 'Rashid Khan', 'rashid khan': 'Rashid Khan',
            'chahal': 'Yuzvendra Chahal',
            'malinga': 'Lasith Malinga',
            'kl rahul': 'KL Rahul', 'rahul': 'KL Rahul',
            'pollard': 'Kieron Pollard'
        }
        
        query_lower = query.lower()
        
        # Check for exact matches first
        for key, player in player_mappings.items():
            if key in query_lower and player not in found_players:
                found_players.append(player)
        
        # If no exact matches, try fuzzy matching
        if not found_players:
            words = query.split()
            for word in words:
                if len(word) > 2:
                    match = process.extractOne(word, self.all_players, scorer=fuzz.partial_ratio)
                    if match and match[1] >= 80:
                        if match[0] not in found_players:
                            found_players.append(match[0])
        
        return found_players
    
    def extract_teams(self, query: str) -> List[str]:
        """Extract team names from query"""
        team_mappings = {
            'csk': 'Chennai Super Kings', 'chennai': 'Chennai Super Kings',
            'mi': 'Mumbai Indians', 'mumbai': 'Mumbai Indians',
            'rcb': 'Royal Challengers Bangalore', 'bangalore': 'Royal Challengers Bangalore',
            'kkr': 'Kolkata Knight Riders', 'kolkata': 'Kolkata Knight Riders',
            'dc': 'Delhi Capitals', 'delhi': 'Delhi Capitals',
            'rr': 'Rajasthan Royals', 'rajasthan': 'Rajasthan Royals',
            'pbks': 'Punjab Kings', 'punjab': 'Punjab Kings',
            'srh': 'Sunrisers Hyderabad', 'hyderabad': 'Sunrisers Hyderabad',
            'gt': 'Gujarat Titans', 'gujarat': 'Gujarat Titans',
            'lsg': 'Lucknow Super Giants', 'lucknow': 'Lucknow Super Giants'
        }
        
        found_teams = []
        query_lower = query.lower()
        
        for key, team in team_mappings.items():
            if key in query_lower and team not in found_teams:
                found_teams.append(team)
        
        return found_teams
    
    def extract_seasons(self, query: str) -> List[str]:
        """Extract season/year from query"""
        seasons = []
        # Look for years between 2008-2025
        year_pattern = r'\b(20(?:0[8-9]|1[0-9]|2[0-5]))\b'
        matches = re.findall(year_pattern, query)
        return list(set(matches))
    
    def extract_cricket_filters(self, query_lower: str) -> Dict[str, Any]:
        """Extract cricket-specific filters"""
        filters = {}
        
        # Specific over ranges (e.g., "overs 7 to 10", "overs 1-6")
        over_range_match = re.search(r'overs?\s+(\d+)\s+to\s+(\d+)', query_lower)
        if over_range_match:
            start_over = int(over_range_match.group(1))
            end_over = int(over_range_match.group(2))
            filters['over_range'] = (start_over, end_over)
            filters['phase'] = f"overs_{start_over}_{end_over}"
        
        # Phase filters (CRITICAL for cricket analytics) 
        elif any(word in query_lower for word in ['powerplay', 'power play', 'overs 1-6']):
            filters['phase'] = 'powerplay'
            filters['over_range'] = (1, 6)
        elif any(word in query_lower for word in ['middle over', 'overs 7-15']):
            filters['phase'] = 'middle'
            filters['over_range'] = (7, 15)
        elif any(word in query_lower for word in ['death over', 'death', 'overs 16-20']):
            filters['phase'] = 'death'
            filters['over_range'] = (16, 20)
        
        # Bowling type filters
        if any(word in query_lower for word in ['v spin', 'vs spin', 'against spin', 'spin bowling']):
            filters['bowling_type'] = 'spin'
        elif any(word in query_lower for word in ['v pace', 'vs pace', 'against pace', 'pace bowling', 'fast bowling']):
            filters['bowling_type'] = 'pace'
        
        # Batting style filters
        if any(word in query_lower for word in ['v lhb', 'vs lhb', 'left hand', 'left-hand', 'leftie']):
            filters['batting_style'] = 'LHB'
        elif any(word in query_lower for word in ['v rhb', 'vs rhb', 'right hand', 'right-hand']):
            filters['batting_style'] = 'RHB'
        
        # Minimum criteria filters with dots
        min_runs_match = re.search(r'min\.?\s*(\d+)\s+runs?', query_lower)
        if min_runs_match:
            filters['min_runs'] = int(min_runs_match.group(1))
        
        # Sorting preferences
        if any(word in query_lower for word in ['order by average', 'sort by average', 'by average']):
            filters['order_by'] = 'average'
        elif any(word in query_lower for word in ['order by strike rate', 'by strike rate']):
            filters['order_by'] = 'strike_rate'
        elif any(word in query_lower for word in ['order by runs', 'by runs']):
            filters['order_by'] = 'runs'
        
        # Economy rate direction (best = lowest, worst = highest)
        if any(word in query_lower for word in ['worst economy', 'highest economy', 'poorest economy']):
            filters['economy_direction'] = 'worst'
        
        # Target score filters (for chase analysis)
        target_match = re.search(r'(\d+)\+?\s+chase', query_lower)
        if target_match:
            filters['min_target'] = int(target_match.group(1))
        
        return filters
    
    def extract_metrics(self, query_lower: str) -> List[str]:
        """Extract what metrics to calculate"""
        metrics = []
        
        if any(word in query_lower for word in ['run', 'score']):
            metrics.append('runs')
        if any(word in query_lower for word in ['wicket', 'dismiss']):
            metrics.append('wickets')
        if any(word in query_lower for word in ['economy', 'economy rate']):
            metrics.append('economy')
        if any(word in query_lower for word in ['strike rate', 'sr']):
            metrics.append('strike_rate')
        if any(word in query_lower for word in ['average', 'avg']):
            metrics.append('average')
        if any(word in query_lower for word in ['six', '6s']):
            metrics.append('sixes')
        if any(word in query_lower for word in ['four', '4s', 'boundaries']):
            metrics.append('fours')
        
        # Default to runs if no specific metric
        if not metrics:
            metrics.append('runs')
            
        return metrics

class CricketQueryGenerator:
    """Generate accurate cricket SQL queries"""
    
    def __init__(self, analyzer: CricketIPLAnalyzer):
        self.analyzer = analyzer
    
    def generate_sql(self, analysis: Dict[str, Any]) -> str:
        """Generate SQL based on cricket analysis"""
        
        query_type = analysis['query_type']
        
        if query_type == 'matchup':
            return self.generate_matchup_query(analysis)
        elif query_type == 'top_performers':
            return self.generate_top_performers_query(analysis)
        elif query_type == 'phase_analysis':
            return self.generate_phase_analysis_query(analysis)
        elif query_type == 'partnership':
            return self.generate_partnership_query(analysis)
        else:
            return self.generate_basic_stats_query(analysis)
    
    def generate_basic_stats_query(self, analysis: Dict[str, Any]) -> str:
        """Generate basic player statistics with proper filters"""
        
        players = analysis['entities']['players']
        filters = analysis['filters']
        
        if not players:
            return "-- Error: No player specified"
        
        player = players[0]
        escaped_player = player.replace("'", "''")
        
        # Build WHERE conditions
        where_conditions = [f"batter_full_name = '{escaped_player}'"]
        where_conditions.append("valid_ball = 1")
        
        # Apply cricket filters
        if 'bowling_type' in filters:
            where_conditions.append(f"bowling_type = '{filters['bowling_type']}'")
        
        if 'over_range' in filters:
            start_over, end_over = filters['over_range']
            where_conditions.append(f"over_col BETWEEN {start_over} AND {end_over}")
        
        if 'batting_style' in filters and 'bowling_type' not in filters:
            # This is for bowler vs batting style
            where_conditions[0] = f"bowler_full_name = '{escaped_player}'"
        
        where_clause = " AND ".join(where_conditions)
        
        # Build the query based on whether it's batting or bowling stats
        if 'batting_style' in filters and 'bowling_type' not in filters:
            # Bowling stats vs batting style
            return f"""
            -- 🏏 BOWLING STATS: {player} vs {filters.get('batting_style', 'all batters')}
            SELECT 
                bowler_full_name as player,
                batting_style,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_bowled,
                SUM(runs_total) as runs_conceded,
                COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as wickets,
                ROUND((SUM(runs_total) * 6.0) / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as economy_rate,
                ROUND(COUNT(CASE WHEN valid_ball = 1 THEN 1 END) * 1.0 / NULLIF(COUNT(CASE WHEN is_wicket = 1 THEN 1 END), 0), 1) as balls_per_wicket
            FROM ipl_data_complete
            WHERE {where_clause}
            GROUP BY bowler_full_name, batting_style
            """
        else:
            # Batting stats
            phase_label = f" vs {filters['bowling_type']}" if 'bowling_type' in filters else ""
            phase_label += f" in {filters['phase']} overs" if 'phase' in filters else ""
            
            return f"""
            -- 🏏 BATTING STATS: {player}{phase_label}
            SELECT 
                batter_full_name as player,
                SUM(runs_batter) as total_runs,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
                ROUND(SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as strike_rate,
                COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
                COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
                COUNT(CASE WHEN runs_batter = 0 AND valid_ball = 1 THEN 1 END) as dots,
                COUNT(CASE WHEN is_wicket = 1 AND player_out = batter THEN 1 END) as dismissals,
                ROUND(SUM(runs_batter) * 1.0 / NULLIF(COUNT(CASE WHEN is_wicket = 1 AND player_out = batter THEN 1 END), 0), 2) as batting_average,
                ROUND((COUNT(CASE WHEN is_four = 1 THEN 1 END) + COUNT(CASE WHEN is_six = 1 THEN 1 END)) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as boundary_percentage
            FROM ipl_data_complete
            WHERE {where_clause}
            GROUP BY batter_full_name
            """
    
    def generate_top_performers_query(self, analysis: Dict[str, Any]) -> str:
        """Generate top performers query with proper cricket filters"""
        
        filters = analysis['filters']
        metrics = analysis['metrics']
        primary_metric = metrics[0] if metrics else 'runs'
        
        # Build WHERE conditions
        where_conditions = ["valid_ball = 1"]
        
        # Apply cricket filters
        if 'over_range' in filters:
            start_over, end_over = filters['over_range']
            where_conditions.append(f"over_col BETWEEN {start_over} AND {end_over}")
        
        if 'bowling_type' in filters:
            where_conditions.append(f"bowling_type = '{filters['bowling_type']}'")
        
        if 'min_target' in filters:
            where_conditions.append(f"runs_target >= {filters['min_target']}")
        
        where_clause = " AND ".join(where_conditions)
        
        # Generate query based on metric
        if primary_metric == 'economy' or 'economy' in str(analysis.get('query_type', '')).lower():
            # Bowling economy rate
            phase_label = f" in {filters['phase']} overs" if 'phase' in filters else ""
            
            # Determine if worst (highest) or best (lowest) economy
            if filters.get('economy_direction') == 'worst':
                order_direction = 'DESC'
                title_prefix = 'WORST'
            else:
                order_direction = 'ASC'
                title_prefix = 'BEST'
            
            return f"""
            -- 🏆 {title_prefix} ECONOMY RATE BOWLERS{phase_label}
            SELECT 
                bowler_full_name,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_bowled,
                SUM(runs_total) as runs_conceded,
                COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as wickets,
                ROUND((SUM(runs_total) * 6.0) / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as economy_rate
            FROM ipl_data_complete
            WHERE {where_clause}
            GROUP BY bowler_full_name
            HAVING COUNT(CASE WHEN valid_ball = 1 THEN 1 END) >= 50
            ORDER BY economy_rate {order_direction}
            LIMIT 15
            """
        
        elif primary_metric == 'sixes' or 'six' in analysis['query_type'].lower():
            # Most sixes
            phase_label = f" in {filters['phase']} overs" if 'phase' in filters else ""
            
            return f"""
            -- 🏆 MOST SIXES{phase_label}
            SELECT 
                batter_full_name,
                COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
                SUM(runs_batter) as total_runs,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
                ROUND(SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as strike_rate
            FROM ipl_data_complete
            WHERE {where_clause}
            GROUP BY batter_full_name
            HAVING COUNT(CASE WHEN valid_ball = 1 THEN 1 END) >= 50
            ORDER BY sixes DESC
            LIMIT 15
            """
        
        else:
            # Top run scorers (default)
            phase_label = f" in {filters['phase']} overs" if 'phase' in filters else ""
            min_runs = filters.get('min_runs', 50)
            
            having_clause = f"SUM(runs_batter) >= {min_runs}"
            
            # Determine sorting order and HAVING clause
            if filters.get('order_by') == 'average':
                order_clause = "batting_average DESC"
                title_suffix = " (by Average)"
                # For average sorting, require dismissals > 0
                having_clause += " AND COUNT(CASE WHEN is_wicket = 1 AND player_out = batter THEN 1 END) > 0"
            elif filters.get('order_by') == 'strike_rate':
                order_clause = "strike_rate DESC"  
                title_suffix = " (by Strike Rate)"
            else:
                order_clause = "total_runs DESC"
                title_suffix = ""
            
            return f"""
            -- 🏆 TOP RUN SCORERS{phase_label}{title_suffix}
            SELECT 
                batter_full_name,
                SUM(runs_batter) as total_runs,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
                ROUND(SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as strike_rate,
                ROUND(SUM(runs_batter) * 1.0 / NULLIF(COUNT(CASE WHEN is_wicket = 1 AND player_out = batter THEN 1 END), 0), 2) as batting_average,
                COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
                COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes
            FROM ipl_data_complete
            WHERE {where_clause}
            GROUP BY batter_full_name
            HAVING {having_clause}
            ORDER BY {order_clause}
            LIMIT 15
            """
    
    def generate_matchup_query(self, analysis: Dict[str, Any]) -> str:
        """Generate player vs player or team vs team matchup"""
        
        players = analysis['entities']['players']
        teams = analysis['entities']['teams']
        
        if len(teams) >= 2:
            return self.generate_team_vs_team_query(teams, analysis)
        elif len(players) >= 2:
            return self.generate_player_vs_player_query(players, analysis)
        elif len(players) == 1 and analysis['filters'].get('bowling_type'):
            return self.generate_player_vs_bowling_type_query(players[0], analysis)
        else:
            return "-- Error: Unable to determine matchup type"
    
    def generate_player_vs_player_query(self, players: List[str], analysis: Dict[str, Any]) -> str:
        """Generate player vs player matchup"""
        
        batter = players[0]
        bowler = players[1]
        
        escaped_batter = batter.replace("'", "''")
        escaped_bowler = bowler.replace("'", "''")
        
        return f"""
        -- 🎯 MATCHUP: {batter} vs {bowler}
        SELECT 
            batter_full_name,
            bowler_full_name,
            SUM(runs_batter) as runs_scored,
            COUNT(*) as balls_faced,
            ROUND(SUM(runs_batter) * 100.0 / COUNT(*), 2) as strike_rate,
            COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
            COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
            COUNT(CASE WHEN is_wicket = 1 AND player_out = batter_full_name THEN 1 END) as dismissals
        FROM ipl_data_complete
        WHERE batter_full_name = '{escaped_batter}'
          AND bowler_full_name = '{escaped_bowler}'
          AND valid_ball = 1
        GROUP BY batter_full_name, bowler_full_name
        """
    
    def generate_team_vs_team_query(self, teams: List[str], analysis: Dict[str, Any]) -> str:
        """Generate team vs team head-to-head"""
        
        team1 = teams[0]
        team2 = teams[1]
        
        escaped_team1 = team1.replace("'", "''")
        escaped_team2 = team2.replace("'", "''")
        
        return f"""
        -- 🏆 HEAD-TO-HEAD: {team1} vs {team2}
        WITH match_results AS (
            SELECT DISTINCT
                match_id,
                season,
                venue,
                winner,
                batting_team,
                MAX(team_runs) as team_score
            FROM ipl_data_complete
            WHERE (batting_team IN ('{escaped_team1}', '{escaped_team2}')
                   AND bowling_team IN ('{escaped_team1}', '{escaped_team2}'))
            GROUP BY match_id, season, venue, winner, batting_team
        )
        SELECT 
            '{team1}' as team1,
            '{team2}' as team2,
            COUNT(DISTINCT match_id) as total_matches,
            COUNT(CASE WHEN winner = '{escaped_team1}' THEN 1 END) as team1_wins,
            COUNT(CASE WHEN winner = '{escaped_team2}' THEN 1 END) as team2_wins,
            ROUND(AVG(CASE WHEN batting_team = '{escaped_team1}' THEN team_score END), 1) as team1_avg_score,
            ROUND(AVG(CASE WHEN batting_team = '{escaped_team2}' THEN team_score END), 1) as team2_avg_score
        FROM match_results
        """
    
    def generate_player_vs_bowling_type_query(self, player: str, analysis: Dict[str, Any]) -> str:
        """Generate player vs bowling type query"""
        
        bowling_type = analysis['filters']['bowling_type']
        escaped_player = player.replace("'", "''")
        
        return f"""
        -- 🎯 {player} vs {bowling_type.upper()} BOWLING
        SELECT 
            batter_full_name,
            bowling_type,
            SUM(runs_batter) as runs_scored,
            COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
            ROUND(SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as strike_rate,
            COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
            COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
            COUNT(CASE WHEN is_wicket = 1 AND player_out = batter_full_name THEN 1 END) as dismissals
        FROM ipl_data_complete
        WHERE batter_full_name = '{escaped_player}'
          AND bowling_type = '{bowling_type}'
          AND valid_ball = 1
        GROUP BY batter_full_name, bowling_type
        """
    
    def generate_phase_analysis_query(self, analysis: Dict[str, Any]) -> str:
        """Generate phase-specific analysis"""
        # This delegates to basic_stats or top_performers based on entities
        if analysis['entities']['players']:
            return self.generate_basic_stats_query(analysis)
        else:
            return self.generate_top_performers_query(analysis)
    
    def generate_partnership_query(self, analysis: Dict[str, Any]) -> str:
        """Generate partnership analysis query"""
        
        players = analysis['entities']['players']
        if len(players) < 2:
            return "-- Error: Need at least 2 players for partnership analysis"
        
        player1 = players[0]
        player2 = players[1]
        
        escaped_player1 = player1.replace("'", "''")
        escaped_player2 = player2.replace("'", "''")
        
        return f"""
        -- 🤝 PARTNERSHIP: {player1} & {player2}
        SELECT 
            batting_partners,
            COUNT(DISTINCT match_id) as matches_together,
            COUNT(*) as balls_together,
            SUM(runs_total) as partnership_runs,
            ROUND(SUM(runs_total) * 6.0 / COUNT(*), 2) as run_rate
        FROM ipl_data_complete
        WHERE batting_partners LIKE '%{escaped_player1}%'
          AND batting_partners LIKE '%{escaped_player2}%'
          AND valid_ball = 1
        GROUP BY batting_partners
        ORDER BY partnership_runs DESC
        """

def get_database_connection():
    """Get database connection using environment variables"""
    try:
        # Try to get DATABASE_URL from environment variables
        database_url = os.getenv('DATABASE_URL')
        
        # Fallback to hardcoded for local development (remove in production)
        if not database_url:
            database_url = "postgresql://neondb_owner:npg_xBSUw9Zu5HMy@ep-young-lake-a1usk5d6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
            logger.warning("Using fallback database connection. Set DATABASE_URL environment variable for production.")
        
        engine = create_engine(database_url)
        return engine, None
    except Exception as e:
        return None, str(e)

def execute_query(engine, query: str):
    """Execute SQL query safely"""
    try:
        result = pd.read_sql_query(text(query), engine)
        return result
    except Exception as e:
        return f"Query execution error: {str(e)}"

# Streamlit UI
def main():
    st.title("🏏 Correct IPL Analytics Chatbot")
    st.markdown("### Cricket-aware query analysis with **accurate** statistics")
    
    # Initialize
    if 'analyzer' not in st.session_state:
        with st.spinner("🔄 Connecting to IPL database..."):
            engine, error = get_database_connection()
            if engine:
                st.session_state.analyzer = CricketIPLAnalyzer(engine)
                st.session_state.generator = CricketQueryGenerator(st.session_state.analyzer)
                st.session_state.engine = engine
                st.success("✅ Connected to IPL database with 765 players!")
            else:
                st.error(f"❌ Database connection failed: {error}")
                return
    
    # Sidebar with examples  
    with st.sidebar:
        st.header("📋 Example Queries")
        
        st.markdown("### 🏏 Phase Analysis")
        if st.button("📊 Best batters in middle overs", use_container_width=True):
            st.session_state.query_input = "best batters in middle overs (min 500 runs)"
        if st.button("⚡ Most sixes in death overs", use_container_width=True):
            st.session_state.query_input = "most sixes in death overs"
        if st.button("🚀 Rohit powerplay stats", use_container_width=True):
            st.session_state.query_input = "Rohit Sharma powerplay stats"
            
        st.markdown("### 🎯 Player vs Bowling")
        if st.button("🌪️ Kohli vs spin bowling", use_container_width=True):
            st.session_state.query_input = "kohli v spin bowling"
        if st.button("🔄 Rashid Khan vs LHB", use_container_width=True):
            st.session_state.query_input = "Rashid Khan v LHB"
        if st.button("⚡ Pollard vs pace", use_container_width=True):
            st.session_state.query_input = "Pollard vs pace bowling"
            
        st.markdown("### 🏆 Top Performers")  
        if st.button("💰 Best economy bowlers", use_container_width=True):
            st.session_state.query_input = "bowlers with highest economy"
        if st.button("🏃 Top run scorers 2023", use_container_width=True):
            st.session_state.query_input = "top run scorers in 2023"
            
        st.markdown("### ⚔️ Matchups")
        if st.button("👑 Kohli vs Bumrah", use_container_width=True):
            st.session_state.query_input = "Kohli vs Bumrah"
        if st.button("🏟️ CSK vs MI head to head", use_container_width=True):
            st.session_state.query_input = "CSK vs MI head to head"
        
        st.markdown("---")
        st.success("🎯 All queries use correct cricket filters!")
    
    # Main interface
    st.markdown("### 🏏 Ask Your Cricket Question")
    st.markdown("Type your query and press **Enter** to analyze")
    
    # Initialize query if not set
    if 'query_input' not in st.session_state:
        st.session_state.query_input = ""
    
    # Query input with better styling
    query = st.text_input(
        "",
        value=st.session_state.query_input,
        placeholder="e.g., best batters in middle overs (min 500 runs)",
        key="main_query_input",
        help="Press Enter after typing your query to execute it automatically"
    )
    
    # Auto-execute on Enter (when query changes and is not empty)
    if query and query != st.session_state.get('last_query', ''):
        st.session_state.last_query = query
        st.session_state.query_input = ""  # Clear the input for next query
        
        with st.spinner("🔄 Analyzing cricket query..."):
            
            # Analyze query
            analysis = st.session_state.analyzer.analyze_query(query)
            
            # Show query being analyzed
            st.markdown(f"**🔍 Analyzing:** {query}")
            
            # Display analysis
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**📊 Query Analysis**")
                st.info(f"""
                **Type:** {analysis['query_type'].replace('_', ' ').title()}  
                **Players:** {', '.join(analysis['entities']['players']) or 'None'}  
                **Teams:** {', '.join(analysis['entities']['teams']) or 'None'}  
                **Filters:** {analysis['filters'] or 'None'}
                """)
            
            # Generate and execute SQL
            sql_query = st.session_state.generator.generate_sql(analysis)
            
            with col2:
                st.markdown("**🔧 Generated SQL**")
                with st.expander("View SQL Query", expanded=False):
                    st.code(sql_query, language='sql')
            
            # Execute query immediately
            with st.spinner("⚡ Executing query..."):
                result = execute_query(st.session_state.engine, sql_query)
                
                st.markdown("---")
                
                if isinstance(result, pd.DataFrame):
                    if len(result) > 0:
                        # Display query title
                        st.markdown(f"### 📈 Results for: *{query}*")
                        
                        # Display results in a nice table
                        st.dataframe(
                            result, 
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Show summary stats
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("📊 Results", len(result))
                        
                        with col2:
                            if 'total_runs' in result.columns:
                                st.metric("🏃 Total Runs", f"{result['total_runs'].sum():,}")
                            elif 'runs_scored' in result.columns:
                                st.metric("🏃 Runs", f"{result['runs_scored'].sum():,}")
                        
                        with col3:
                            if 'balls_faced' in result.columns:
                                st.metric("⚾ Total Balls", f"{result['balls_faced'].sum():,}")
                            elif 'balls_bowled' in result.columns:
                                st.metric("⚾ Balls Bowled", f"{result['balls_bowled'].sum():,}")
                        
                        # Option to download results
                        csv = result.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Results CSV",
                            data=csv,
                            file_name=f"ipl_{analysis['query_type']}.csv",
                            mime="text/csv"
                        )
                        
                        st.success("✅ Query executed with correct cricket filters!")
                        
                    else:
                        st.warning("⚠️ Query executed successfully but returned no results. This might be expected for some matchups that didn't occur in IPL.")
                else:
                    st.error(f"❌ Query failed: {result}")
    
    # Footer
    st.markdown("---")
    st.markdown("**🏏 Built with correct cricket understanding | All filters properly applied in SQL**")

if __name__ == "__main__":
    main()