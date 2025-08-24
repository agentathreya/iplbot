#!/usr/bin/env python3
"""
🏏 Advanced IPL Analytics Chatbot
Handles complex cricket statistics queries using optimized multi-table database
"""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import re
from fuzzywuzzy import fuzz, process
from typing import List, Dict, Optional, Tuple, Any
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="🏏 Advanced IPL Analytics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AdvancedIPLAnalyzer:
    """Advanced analyzer for complex IPL queries"""
    
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
            
            # Load venues
            self.venues_df = pd.read_sql_query("""
                SELECT DISTINCT venue as venue_name 
                FROM ipl_data_complete 
                WHERE venue IS NOT NULL
            """, self.engine)
            self.all_venues = self.venues_df['venue_name'].tolist()
            
            logger.info(f"Loaded {len(self.all_players)} players, {len(self.all_teams)} teams, {len(self.all_venues)} venues")
            
        except Exception as e:
            logger.error(f"Error loading reference data: {e}")
            self.all_players = []
            self.all_teams = []
            self.all_venues = []
    
    def analyze_complex_query(self, query: str) -> Dict[str, Any]:
        """Analyze complex IPL queries and determine intent"""
        query_lower = query.lower()
        
        analysis = {
            'query_type': 'unknown',
            'entities': {
                'players': [],
                'teams': [],
                'venues': [],
                'seasons': []
            },
            'metrics': [],
            'filters': {},
            'aggregation': 'sum',
            'complexity': 'basic',
            'special_analysis': None
        }
        
        # 1. DETECT QUERY TYPE
        if any(word in query_lower for word in ['vs', 'against', 'matchup', 'head to head', 'h2h']):
            analysis['query_type'] = 'matchup'
            analysis['complexity'] = 'advanced'
        elif any(phrase in query_lower for phrase in ['entry point', 'next batter', 'batting position', 'batting order']):
            analysis['query_type'] = 'entry_point_analysis'
            analysis['complexity'] = 'advanced' 
            analysis['special_analysis'] = 'next_batter'
        elif any(word in query_lower for word in ['phase', 'powerplay', 'death over', 'middle over']):
            analysis['query_type'] = 'phase_analysis'
            analysis['complexity'] = 'advanced'
        elif any(word in query_lower for word in ['partnership', 'batting partners', 'combination']):
            analysis['query_type'] = 'partnership'
            analysis['complexity'] = 'advanced'
        elif any(word in query_lower for word in ['most', 'highest', 'best', 'top', 'leading']):
            analysis['query_type'] = 'top_performers'
        elif any(word in query_lower for word in ['average', 'strike rate', 'economy']):
            analysis['query_type'] = 'statistical_analysis'
        else:
            analysis['query_type'] = 'basic_stats'
        
        # 2. EXTRACT ENTITIES
        analysis['entities']['players'] = self.extract_players(query)
        analysis['entities']['teams'] = self.extract_teams(query)
        analysis['entities']['venues'] = self.extract_venues(query)
        analysis['entities']['seasons'] = self.extract_seasons(query)
        
        # 3. DETECT METRICS
        analysis['metrics'] = self.extract_metrics(query_lower)
        
        # 4. EXTRACT FILTERS
        analysis['filters'] = self.extract_filters(query_lower)
        
        # 5. DETERMINE COMPLEXITY
        complexity_factors = [
            len(analysis['entities']['players']) > 1,
            len(analysis['filters']) > 2,
            analysis['query_type'] in ['matchup', 'entry_point_analysis', 'partnership'],
            'vs' in query_lower,
            'phase' in query_lower
        ]
        
        if sum(complexity_factors) >= 2:
            analysis['complexity'] = 'advanced'
        elif sum(complexity_factors) == 1:
            analysis['complexity'] = 'intermediate'
        
        return analysis
    
    def extract_players(self, query: str) -> List[str]:
        """Extract player names from query using fuzzy matching"""
        found_players = []
        
        # Famous player mappings
        player_mappings = {
            'virat': 'Virat Kohli', 'kohli': 'Virat Kohli', 'vk': 'Virat Kohli',
            'rohit': 'Rohit Sharma', 'hitman': 'Rohit Sharma',
            'dhoni': 'MS Dhoni', 'msd': 'MS Dhoni', 'captain cool': 'MS Dhoni',
            'bumrah': 'Jasprit Bumrah', 'boom boom': 'Jasprit Bumrah',
            'ab': 'AB de Villiers', 'abd': 'AB de Villiers', 'mr 360': 'AB de Villiers',
            'gayle': 'Chris Gayle', 'universe boss': 'Chris Gayle',
            'warner': 'David Warner', 'raina': 'Suresh Raina',
            'jadeja': 'Ravindra Jadeja', 'sir jadeja': 'Ravindra Jadeja'
        }
        
        query_lower = query.lower()
        
        # Check for famous players
        for key, player in player_mappings.items():
            if key in query_lower:
                found_players.append(player)
        
        # Use fuzzy matching for other players
        words = query.split()
        for i, word in enumerate(words):
            if word.istitle():  # Capitalized words might be names
                # Try single word match
                match = process.extractOne(word, self.all_players, scorer=fuzz.partial_ratio)
                if match and match[1] >= 70:
                    found_players.append(match[0])
                
                # Try two-word combinations
                if i < len(words) - 1:
                    two_word = f"{word} {words[i+1]}"
                    match = process.extractOne(two_word, self.all_players, scorer=fuzz.ratio)
                    if match and match[1] >= 80:
                        found_players.append(match[0])
        
        return list(set(found_players))  # Remove duplicates
    
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
            if key in query_lower:
                found_teams.append(team)
        
        return found_teams
    
    def extract_venues(self, query: str) -> List[str]:
        """Extract venue names from query"""
        found_venues = []
        
        # Use fuzzy matching for venues
        words = query.split()
        for word in words:
            if word.istitle():
                match = process.extractOne(word, self.all_venues, scorer=fuzz.partial_ratio)
                if match and match[1] >= 70:
                    found_venues.append(match[0])
        
        return list(set(found_venues))
    
    def extract_seasons(self, query: str) -> List[str]:
        """Extract season/year information from query"""
        seasons = []
        
        # Look for years
        year_pattern = r'20\d{2}'
        years = re.findall(year_pattern, query)
        seasons.extend(years)
        
        # Look for season keywords
        if 'this season' in query.lower():
            seasons.append('2024')  # Current season
        elif 'last season' in query.lower():
            seasons.append('2023')
        
        return seasons
    
    def extract_metrics(self, query_lower: str) -> List[str]:
        """Extract metrics from query"""
        metrics = []
        
        metric_keywords = {
            'runs': ['runs', 'scored', 'score'],
            'wickets': ['wickets', 'wicket', 'dismissed', 'out'],
            'sixes': ['sixes', 'six', '6s'],
            'fours': ['fours', 'four', 'boundaries', '4s'],
            'strike_rate': ['strike rate', 'strike', 'sr'],
            'average': ['average', 'avg'],
            'economy': ['economy', 'economy rate'],
            'dot_balls': ['dot balls', 'dots'],
            'centuries': ['centuries', 'century', '100s'],
            'fifties': ['fifties', 'fifty', '50s']
        }
        
        for metric, keywords in metric_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                metrics.append(metric)
        
        return metrics or ['runs']  # Default to runs
    
    def extract_filters(self, query_lower: str) -> Dict[str, Any]:
        """Extract filters from query"""
        filters = {}
        
        # Phase filters
        if any(phrase in query_lower for phrase in ['powerplay', 'power play']):
            filters['phase'] = 'powerplay'
        elif any(phrase in query_lower for phrase in ['death over', 'death overs', 'final over']):
            filters['phase'] = 'death'
        elif any(phrase in query_lower for phrase in ['middle over', 'middle overs']):
            filters['phase'] = 'middle'
        
        # Bowling type filters
        if any(phrase in query_lower for phrase in ['vs spin', 'against spin', 'spin bowling']):
            filters['bowling_type'] = 'spin'
        elif any(phrase in query_lower for phrase in ['vs pace', 'against pace', 'fast bowling']):
            filters['bowling_type'] = 'pace'
        
        # Innings filter
        if 'first innings' in query_lower:
            filters['innings'] = 1
        elif 'second innings' in query_lower:
            filters['innings'] = 2
        
        return filters

class AdvancedQueryGenerator:
    """Generate complex SQL queries for IPL analytics"""
    
    def __init__(self, analyzer: AdvancedIPLAnalyzer):
        self.analyzer = analyzer
    
    def generate_sql(self, analysis: Dict[str, Any]) -> str:
        """Generate SQL query based on analysis"""
        
        query_type = analysis['query_type']
        
        if query_type == 'matchup':
            return self.generate_matchup_query(analysis)
        elif query_type == 'entry_point_analysis':
            return self.generate_entry_point_query(analysis)
        elif query_type == 'partnership':
            return self.generate_partnership_query(analysis)
        elif query_type == 'phase_analysis':
            return self.generate_phase_analysis_query(analysis)
        elif query_type == 'top_performers':
            return self.generate_top_performers_query(analysis)
        else:
            return self.generate_basic_stats_query(analysis)
    
    def generate_matchup_query(self, analysis: Dict[str, Any]) -> str:
        """Generate matchup analysis query (bowler vs batter)"""
        
        players = analysis['entities']['players']
        if len(players) < 2:
            return "-- Error: Need at least 2 players for matchup analysis"
        
        batter = players[0]  # Assume first is batter
        bowler = players[1]   # Assume second is bowler
        
        # Build conditions
        conditions = ["1=1"]
        
        if analysis['entities']['seasons']:
            seasons = "', '".join(analysis['entities']['seasons'])
            conditions.append(f"season IN ('{seasons}')")
        
        where_clause = " AND ".join(conditions)
        
        return f"""
        -- 🎯 MATCHUP ANALYSIS: {batter} vs {bowler}
        SELECT 
            batter_full_name as batter,
            bowler_full_name as bowler,
            COUNT(*) as balls_faced,
            SUM(runs_batter) as runs_scored,
            COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
            COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
            COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as dismissals,
            ROUND(
                CASE 
                    WHEN COUNT(CASE WHEN valid_ball = 1 THEN 1 END) > 0 
                    THEN (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
                    ELSE 0 
                END, 2
            ) as strike_rate,
            ROUND(
                CASE 
                    WHEN COUNT(CASE WHEN is_wicket = 1 THEN 1 END) > 0 
                    THEN (SUM(runs_batter) * 1.0 / COUNT(CASE WHEN is_wicket = 1 THEN 1 END))
                    ELSE SUM(runs_batter) * 1.0
                END, 2
            ) as avg_runs_per_dismissal,
            STRING_AGG(DISTINCT season, ', ') as seasons_played,
            STRING_AGG(DISTINCT dismissal_type, ', ') as dismissal_types
        FROM ipl_data_complete
        WHERE batter_full_name = '{batter.replace("'", "''")}'
          AND bowler_full_name = '{bowler.replace("'", "''")}'
          AND {where_clause}
        GROUP BY batter_full_name, bowler_full_name
        ORDER BY balls_faced DESC
        """
    
    def generate_entry_point_query(self, analysis: Dict[str, Any]) -> str:
        """Generate entry point analysis query using next_batter column"""
        
        players = analysis['entities']['players']
        if not players:
            return """
            -- 📊 ENTRY POINT ANALYSIS - Overall Statistics
            SELECT 
                next_batter,
                COUNT(DISTINCT match_id) as matches,
                COUNT(*) as entry_opportunities,
                AVG(team_runs) as avg_team_score_at_entry,
                AVG(team_wickets) as avg_wickets_at_entry,
                ROUND(AVG(over_col + (ball * 1.0 / 6)), 2) as avg_entry_over,
                ROUND(AVG(required_rr), 2) as avg_required_rate_at_entry
            FROM ipl_data_complete 
            WHERE next_batter IS NOT NULL 
              AND next_batter != ''
            GROUP BY next_batter
            HAVING COUNT(*) >= 10
            ORDER BY entry_opportunities DESC
            LIMIT 20
            """
        
        player = players[0]
        
        return f"""
        -- 🎯 ENTRY POINT ANALYSIS: {player}
        SELECT 
            '{player}' as player,
            season,
            batting_team,
            COUNT(DISTINCT match_id) as matches_as_next_batter,
            COUNT(*) as total_entry_situations,
            ROUND(AVG(team_runs), 1) as avg_team_score_at_entry,
            ROUND(AVG(team_wickets), 1) as avg_wickets_at_entry,
            ROUND(AVG(over_col + (ball * 1.0 / 6)), 2) as avg_entry_over,
            ROUND(AVG(CASE WHEN required_rr IS NOT NULL THEN required_rr END), 2) as avg_required_rate,
            ROUND(AVG(current_rr), 2) as avg_current_rate_at_entry,
            COUNT(CASE WHEN team_wickets >= 5 THEN 1 END) as crisis_entries,
            COUNT(CASE WHEN over_col >= 16 THEN 1 END) as death_over_entries,
            STRING_AGG(DISTINCT 
                CASE 
                    WHEN team_wickets <= 2 THEN 'Early Entry'
                    WHEN team_wickets BETWEEN 3 AND 5 THEN 'Middle Entry' 
                    ELSE 'Crisis Entry'
                END, ', '
            ) as entry_scenarios
        FROM ipl_data_complete 
        WHERE next_batter = '{player.replace("'", "''")}'
        GROUP BY season, batting_team
        ORDER BY season DESC, matches_as_next_batter DESC
        """
    
    def generate_partnership_query(self, analysis: Dict[str, Any]) -> str:
        """Generate partnership analysis query"""
        
        players = analysis['entities']['players']
        if len(players) >= 2:
            player1, player2 = players[0], players[1]
            return f"""
            -- 🤝 PARTNERSHIP ANALYSIS: {player1} & {player2}
            SELECT 
                batting_partners,
                season,
                COUNT(DISTINCT match_id) as matches_together,
                COUNT(*) as balls_together,
                SUM(runs_total) as partnership_runs,
                ROUND(AVG(runs_total), 2) as avg_runs_per_ball,
                MAX(team_runs) - MIN(team_runs) as max_partnership_in_match,
                COUNT(CASE WHEN is_four = 1 OR is_six = 1 THEN 1 END) as boundaries,
                STRING_AGG(DISTINCT batting_team, ', ') as teams
            FROM ipl_data_complete 
            WHERE batting_partners LIKE '%{player1.replace("'", "''")}%'
              AND batting_partners LIKE '%{player2.replace("'", "''")}%'
            GROUP BY batting_partners, season
            ORDER BY partnership_runs DESC
            """
        
        return """
        -- 🤝 TOP PARTNERSHIPS - Overall Analysis
        SELECT 
            batting_partners,
            COUNT(DISTINCT match_id) as matches,
            SUM(runs_total) as total_runs,
            COUNT(CASE WHEN is_four = 1 OR is_six = 1 THEN 1 END) as boundaries,
            ROUND(AVG(runs_total), 2) as avg_runs_per_ball
        FROM ipl_data_complete 
        WHERE batting_partners IS NOT NULL 
          AND batting_partners != ''
          AND batting_partners NOT LIKE '%Unknown%'
        GROUP BY batting_partners
        HAVING COUNT(*) >= 100
        ORDER BY total_runs DESC
        LIMIT 20
        """
    
    def generate_phase_analysis_query(self, analysis: Dict[str, Any]) -> str:
        """Generate phase-wise analysis query"""
        
        phase = analysis['filters'].get('phase', 'all')
        players = analysis['entities']['players']
        
        # Build phase condition
        if phase == 'powerplay':
            phase_condition = "over_col BETWEEN 1 AND 6"
        elif phase == 'middle':
            phase_condition = "over_col BETWEEN 7 AND 15"
        elif phase == 'death':
            phase_condition = "over_col BETWEEN 16 AND 20"
        else:
            phase_condition = "1=1"
        
        if players:
            player = players[0]
            return f"""
            -- 📊 PHASE ANALYSIS: {player} ({phase.upper()} OVERS)
            SELECT 
                batter_full_name,
                season,
                CASE 
                    WHEN over_col BETWEEN 1 AND 6 THEN 'Powerplay'
                    WHEN over_col BETWEEN 7 AND 15 THEN 'Middle Overs'
                    WHEN over_col BETWEEN 16 AND 20 THEN 'Death Overs'
                END as phase,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
                SUM(runs_batter) as runs_scored,
                COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
                COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
                COUNT(CASE WHEN runs_batter = 0 AND valid_ball = 1 THEN 1 END) as dots,
                ROUND(
                    CASE 
                        WHEN COUNT(CASE WHEN valid_ball = 1 THEN 1 END) > 0 
                        THEN (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
                        ELSE 0 
                    END, 2
                ) as strike_rate
            FROM ipl_data_complete
            WHERE batter_full_name = '{player.replace("'", "''")}'
              AND {phase_condition}
            GROUP BY batter_full_name, season, 
                CASE 
                    WHEN over_col BETWEEN 1 AND 6 THEN 'Powerplay'
                    WHEN over_col BETWEEN 7 AND 15 THEN 'Middle Overs'
                    WHEN over_col BETWEEN 16 AND 20 THEN 'Death Overs'
                END
            ORDER BY season DESC, runs_scored DESC
            """
        
        return f"""
        -- 📊 PHASE ANALYSIS: TOP PERFORMERS ({phase.upper()} OVERS)
        SELECT 
            batter_full_name,
            COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
            SUM(runs_batter) as runs_scored,
            COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
            COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
            ROUND(
                CASE 
                    WHEN COUNT(CASE WHEN valid_ball = 1 THEN 1 END) > 0 
                    THEN (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
                    ELSE 0 
                END, 2
            ) as strike_rate
        FROM ipl_data_complete
        WHERE {phase_condition}
        GROUP BY batter_full_name
        HAVING COUNT(CASE WHEN valid_ball = 1 THEN 1 END) >= 50
        ORDER BY runs_scored DESC
        LIMIT 20
        """
    
    def generate_top_performers_query(self, analysis: Dict[str, Any]) -> str:
        """Generate top performers query"""
        
        metrics = analysis['metrics'][0] if analysis['metrics'] else 'runs'
        
        if metrics == 'runs':
            return """
            -- 🏆 TOP RUN SCORERS
            SELECT 
                batter_full_name,
                COUNT(DISTINCT season) as seasons_played,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
                SUM(runs_batter) as total_runs,
                COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
                COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
                ROUND(
                    CASE 
                        WHEN COUNT(CASE WHEN valid_ball = 1 THEN 1 END) > 0 
                        THEN (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
                        ELSE 0 
                    END, 2
                ) as strike_rate,
                STRING_AGG(DISTINCT batting_team, ', ') as teams_played_for
            FROM ipl_data_complete
            WHERE batter_full_name IS NOT NULL
            GROUP BY batter_full_name
            HAVING COUNT(CASE WHEN valid_ball = 1 THEN 1 END) >= 100
            ORDER BY total_runs DESC
            LIMIT 20
            """
        elif metrics == 'wickets':
            return """
            -- 🏆 TOP WICKET TAKERS
            SELECT 
                bowler_full_name,
                COUNT(DISTINCT season) as seasons_played,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_bowled,
                SUM(runs_total) as runs_conceded,
                COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as wickets_taken,
                ROUND(
                    CASE 
                        WHEN COUNT(CASE WHEN valid_ball = 1 THEN 1 END) > 0 
                        THEN (SUM(runs_total) * 6.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
                        ELSE 0 
                    END, 2
                ) as economy_rate,
                ROUND(
                    CASE 
                        WHEN COUNT(CASE WHEN is_wicket = 1 THEN 1 END) > 0 
                        THEN (SUM(runs_total) * 1.0 / COUNT(CASE WHEN is_wicket = 1 THEN 1 END))
                        ELSE 0 
                    END, 2
                ) as bowling_average,
                STRING_AGG(DISTINCT bowling_team, ', ') as teams_played_for
            FROM ipl_data_complete
            WHERE bowler_full_name IS NOT NULL
            GROUP BY bowler_full_name
            HAVING COUNT(CASE WHEN valid_ball = 1 THEN 1 END) >= 100
            ORDER BY wickets_taken DESC
            LIMIT 20
            """
        
        return "-- Error: Unsupported metric for top performers"
    
    def generate_basic_stats_query(self, analysis: Dict[str, Any]) -> str:
        """Generate basic statistics query"""
        
        players = analysis['entities']['players']
        if not players:
            return """
            SELECT 'Please specify a player name for basic stats' as message
            """
        
        player = players[0]
        
        return f"""
        -- 📊 BASIC STATS: {player}
        SELECT 
            batter_full_name,
            COUNT(DISTINCT season) as seasons_played,
            COUNT(DISTINCT match_id) as matches_played,
            COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
            SUM(runs_batter) as total_runs,
            COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
            COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
            COUNT(CASE WHEN runs_batter = 0 AND valid_ball = 1 THEN 1 END) as dots,
            COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as dismissals,
            ROUND(
                CASE 
                    WHEN COUNT(CASE WHEN valid_ball = 1 THEN 1 END) > 0 
                    THEN (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
                    ELSE 0 
                END, 2
            ) as strike_rate,
            ROUND(
                CASE 
                    WHEN COUNT(CASE WHEN is_wicket = 1 THEN 1 END) > 0 
                    THEN (SUM(runs_batter) * 1.0 / COUNT(CASE WHEN is_wicket = 1 THEN 1 END))
                    ELSE SUM(runs_batter) * 1.0
                END, 2
            ) as batting_average,
            STRING_AGG(DISTINCT batting_team, ', ') as teams_played_for,
            STRING_AGG(DISTINCT season, ', ' ORDER BY season) as seasons
        FROM ipl_data_complete
        WHERE batter_full_name = '{player.replace("'", "''")}'
        GROUP BY batter_full_name
        """

@st.cache_resource
def get_database_connection():
    """Get optimized database connection"""
    try:
        DATABASE_URL = "postgresql://neondb_owner:npg_xBSUw9Zu5HMy@ep-young-lake-a1usk5d6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        test_df = pd.read_sql_query("SELECT COUNT(*) as count FROM ipl_data_complete LIMIT 1", engine)
        row_count = test_df.iloc[0]['count']
        
        return engine, row_count
        
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None, 0

def execute_query(engine, query: str):
    """Execute SQL query safely"""
    try:
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        return f"Query Error: {str(e)}"

def main():
    """Main Streamlit application"""
    
    st.title("🏏 Advanced IPL Analytics Chatbot")
    st.markdown("### 🎯 Handles Complex Cricket Queries with Multi-Table Optimization")
    
    # Load database connection
    with st.spinner("Connecting to optimized IPL database..."):
        engine, row_count = get_database_connection()
        if not engine:
            st.error("Failed to connect to database")
            return
        
        analyzer = AdvancedIPLAnalyzer(engine)
        query_generator = AdvancedQueryGenerator(analyzer)
    
    st.success(f"✅ Connected to database with {row_count:,} records")
    
    # Sidebar with advanced features
    with st.sidebar:
        st.header("🚀 Advanced Features")
        
        st.subheader("🎯 Query Types Supported:")
        st.write("• **Basic Stats**: Runs, wickets, averages")
        st.write("• **Matchups**: Player vs Player analysis") 
        st.write("• **Entry Point**: Next batter analysis")
        st.write("• **Phase Analysis**: Powerplay, middle, death")
        st.write("• **Partnerships**: Batting combinations")
        st.write("• **Complex Filters**: Season, team, venue")
        
        st.subheader("📊 Example Queries:")
        example_queries = [
            "Virat Kohli vs Jasprit Bumrah matchup",
            "MS Dhoni entry point analysis", 
            "Rohit Sharma powerplay stats",
            "CSK vs MI head to head",
            "Death over specialists",
            "Kohli and ABD partnership",
            "Most sixes in 2023",
            "Best economy rate bowlers"
        ]
        
        for i, query in enumerate(example_queries):
            if st.button(f"🔍 {query}", key=f"example_{i}"):
                st.session_state.current_query = query
    
    # Main query interface
    st.header("💬 Ask Your Complex IPL Question")
    
    # Initialize session state
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    # Query input
    user_query = st.text_area(
        "Enter your IPL analytics question:",
        value=st.session_state.current_query,
        height=100,
        placeholder="E.g., 'Virat Kohli vs Rashid Khan matchup in IPL 2023' or 'MS Dhoni entry point analysis when team is in trouble'"
    )
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        analyze_btn = st.button("🔍 Analyze", type="primary")
    
    with col2:
        clear_btn = st.button("🗑️ Clear")
    
    if clear_btn:
        st.session_state.query_history = []
        st.session_state.current_query = ""
        st.rerun()
    
    if analyze_btn and user_query.strip():
        
        # Step 1: Analyze the query
        with st.expander("🧠 Query Analysis", expanded=True):
            analysis = analyzer.analyze_complex_query(user_query)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Query Type:**", analysis['query_type'])
                st.write("**Complexity:**", analysis['complexity'])
                if analysis['special_analysis']:
                    st.write("**Special Analysis:**", analysis['special_analysis'])
            
            with col2:
                st.write("**Players:**", ', '.join(analysis['entities']['players']) or 'None')
                st.write("**Teams:**", ', '.join(analysis['entities']['teams']) or 'None')
                st.write("**Seasons:**", ', '.join(analysis['entities']['seasons']) or 'All')
            
            with col3:
                st.write("**Metrics:**", ', '.join(analysis['metrics']))
                st.write("**Filters:**", str(analysis['filters']) if analysis['filters'] else 'None')
        
        # Step 2: Generate and execute SQL
        with st.spinner("Generating optimized SQL query..."):
            sql_query = query_generator.generate_sql(analysis)
        
        st.subheader("🔧 Generated SQL Query")
        st.code(sql_query, language="sql")
        
        # Step 3: Execute query
        with st.spinner("Executing advanced analytics query..."):
            result = execute_query(engine, sql_query)
        
        # Step 4: Display results
        if isinstance(result, pd.DataFrame):
            st.subheader("📊 Analysis Results")
            
            if len(result) == 0:
                st.warning("No results found for your query.")
            else:
                st.dataframe(result, use_container_width=True)
                
                # Download option
                csv = result.to_csv(index=False)
                st.download_button(
                    "📥 Download Results",
                    csv,
                    f"ipl_analysis_{analysis['query_type']}.csv",
                    "text/csv"
                )
                
                # Add insights for complex queries
                if analysis['complexity'] == 'advanced':
                    st.subheader("💡 Key Insights")
                    if analysis['query_type'] == 'matchup' and len(result) > 0:
                        row = result.iloc[0]
                        st.write(f"• **Balls Faced**: {row['balls_faced']} balls")
                        st.write(f"• **Strike Rate**: {row['strike_rate']}%")
                        if row['dismissals'] > 0:
                            st.write(f"• **Dismissals**: {row['dismissals']} times")
                        st.write(f"• **Boundary %**: {((row['fours'] + row['sixes']) / row['balls_faced'] * 100):.1f}%")
        
        else:
            st.error(f"Query execution failed: {result}")
        
        # Add to history
        st.session_state.query_history.append({
            'query': user_query,
            'analysis': analysis,
            'sql': sql_query,
            'success': isinstance(result, pd.DataFrame),
            'result_count': len(result) if isinstance(result, pd.DataFrame) else 0
        })
    
    # Query history
    if st.session_state.query_history:
        st.header("📝 Recent Advanced Queries")
        for i, item in enumerate(reversed(st.session_state.query_history[-3:])):
            with st.expander(f"Q{len(st.session_state.query_history)-i}: {item['query'][:60]}..."):
                st.write(f"**Type**: {item['analysis']['query_type']} | **Complexity**: {item['analysis']['complexity']}")
                st.code(item['sql'][:200] + "..." if len(item['sql']) > 200 else item['sql'], language="sql")
                status = f"✅ {item['result_count']} rows" if item['success'] else "❌ Failed"
                st.write(f"**Result**: {status}")

if __name__ == "__main__":
    main()