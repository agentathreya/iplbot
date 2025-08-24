#!/usr/bin/env python3
"""
Test the correct cricket analytics without Streamlit
"""

import pandas as pd
from sqlalchemy import create_engine, text
import re
from fuzzywuzzy import fuzz, process
from typing import List, Dict, Optional, Tuple, Any

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
            
            print(f"Loaded {len(self.all_players)} players, {len(self.all_teams)} teams")
            
        except Exception as e:
            print(f"Error loading reference data: {e}")
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
            'metrics': []
        }
        
        # 1. DETECT QUERY TYPE with cricket understanding
        if any(word in query_lower for word in ['most', 'highest', 'best', 'top', 'leading', 'maximum', 'lowest']):
            analysis['query_type'] = 'top_performers'
        elif any(word in query_lower for word in ['vs', 'against', 'matchup', 'head to head', 'h2h', 'versus']):
            analysis['query_type'] = 'matchup'
        elif any(word in query_lower for word in ['powerplay', 'death over', 'middle over', 'overs 1-6', 'overs 7-15', 'overs 16-20']):
            analysis['query_type'] = 'phase_analysis'
        else:
            analysis['query_type'] = 'basic_stats'
        
        # 2. EXTRACT ENTITIES
        analysis['entities']['players'] = self.extract_players(query)
        analysis['entities']['teams'] = self.extract_teams(query)
        
        # 3. EXTRACT FILTERS with cricket logic
        analysis['filters'] = self.extract_cricket_filters(query_lower)
        
        # 4. EXTRACT METRICS
        analysis['metrics'] = self.extract_metrics(query_lower)
        
        return analysis
    
    def extract_players(self, query: str) -> List[str]:
        """Extract player names with improved matching"""
        found_players = []
        
        player_mappings = {
            'virat': 'Virat Kohli', 'kohli': 'Virat Kohli',
            'rohit': 'Rohit Sharma', 'sharma': 'Rohit Sharma',
            'dhoni': 'MS Dhoni', 'msd': 'MS Dhoni',
            'bumrah': 'Jasprit Bumrah',
            'abd': 'AB de Villiers', 'ab de villiers': 'AB de Villiers',
            'rashid': 'Rashid Khan', 'rashid khan': 'Rashid Khan'
        }
        
        query_lower = query.lower()
        
        for key, player in player_mappings.items():
            if key in query_lower and player not in found_players:
                found_players.append(player)
        
        return found_players
    
    def extract_teams(self, query: str) -> List[str]:
        """Extract team names from query"""
        team_mappings = {
            'csk': 'Chennai Super Kings', 'chennai': 'Chennai Super Kings',
            'mi': 'Mumbai Indians', 'mumbai': 'Mumbai Indians',
            'rcb': 'Royal Challengers Bangalore', 'bangalore': 'Royal Challengers Bangalore'
        }
        
        found_teams = []
        query_lower = query.lower()
        
        for key, team in team_mappings.items():
            if key in query_lower and team not in found_teams:
                found_teams.append(team)
        
        return found_teams
    
    def extract_cricket_filters(self, query_lower: str) -> Dict[str, Any]:
        """Extract cricket-specific filters"""
        filters = {}
        
        # Phase filters
        if any(word in query_lower for word in ['powerplay', 'power play', 'overs 1-6']):
            filters['phase'] = 'powerplay'
            filters['over_range'] = (1, 6)
        elif any(word in query_lower for word in ['middle over', 'overs 7-15']):
            filters['phase'] = 'middle'
            filters['over_range'] = (7, 15)
        elif any(word in query_lower for word in ['death over', 'death', 'overs 16-20']):
            filters['phase'] = 'death'
            filters['over_range'] = (16, 20)
        
        # Bowling type filters
        if any(word in query_lower for word in ['spin', 'spinner', 'spin bowling']):
            filters['bowling_type'] = 'spin'
        elif any(word in query_lower for word in ['pace', 'fast', 'seam', 'pace bowling', 'fast bowling']):
            filters['bowling_type'] = 'pace'
        
        # Batting style filters  
        if any(word in query_lower for word in ['lhb', 'left hand', 'left-hand', 'leftie']):
            filters['batting_style'] = 'LHB'
        
        # Minimum criteria filters
        min_runs_match = re.search(r'min(?:imum)?\s+(\d+)\s+runs?', query_lower)
        if min_runs_match:
            filters['min_runs'] = int(min_runs_match.group(1))
        
        return filters
    
    def extract_metrics(self, query_lower: str) -> List[str]:
        """Extract what metrics to calculate"""
        metrics = []
        
        if any(word in query_lower for word in ['economy', 'economy rate']):
            metrics.append('economy')
        elif any(word in query_lower for word in ['six', '6s']):
            metrics.append('sixes')
        elif any(word in query_lower for word in ['run', 'score']):
            metrics.append('runs')
        
        if not metrics:
            metrics.append('runs')
            
        return metrics

class CricketQueryGenerator:
    """Generate accurate cricket SQL queries"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
    
    def generate_sql(self, analysis: Dict[str, Any]) -> str:
        """Generate SQL based on cricket analysis"""
        
        query_type = analysis['query_type']
        
        if query_type == 'top_performers':
            return self.generate_top_performers_query(analysis)
        elif query_type == 'basic_stats':
            return self.generate_basic_stats_query(analysis)
        else:
            return "-- Query type not implemented yet"
    
    def generate_basic_stats_query(self, analysis: Dict[str, Any]) -> str:
        """Generate basic player statistics with proper filters"""
        
        players = analysis['entities']['players']
        filters = analysis['filters']
        
        if not players:
            return "-- Error: No player specified"
        
        player = players[0]
        escaped_player = player.replace("'", "''")
        
        # Build WHERE conditions
        where_conditions = [f"batter_full_name = '{escaped_player}'", "valid_ball = 1"]
        
        # Apply cricket filters
        if 'bowling_type' in filters:
            where_conditions.append(f"bowling_type = '{filters['bowling_type']}'")
        
        if 'over_range' in filters:
            start_over, end_over = filters['over_range']
            where_conditions.append(f"over_col BETWEEN {start_over} AND {end_over}")
        
        # Special case for bowler vs batting style
        if 'batting_style' in filters and 'bowling_type' not in filters:
            where_conditions[0] = f"bowler_full_name = '{escaped_player}'"
        
        where_clause = " AND ".join(where_conditions)
        
        # Build appropriate query
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
                ROUND((SUM(runs_total) * 6.0) / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as economy_rate
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
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
                SUM(runs_batter) as total_runs,
                COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
                COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
                COUNT(CASE WHEN is_wicket = 1 AND player_out = batter_full_name THEN 1 END) as dismissals,
                ROUND(SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as strike_rate
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
        
        where_clause = " AND ".join(where_conditions)
        
        # Generate query based on metric
        if primary_metric == 'economy':
            # Bowling economy rate
            phase_label = f" in {filters['phase']} overs" if 'phase' in filters else ""
            
            return f"""
            -- 🏆 BEST ECONOMY RATE BOWLERS{phase_label}
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
            ORDER BY economy_rate ASC
            LIMIT 15
            """
        
        elif primary_metric == 'sixes':
            # Most sixes
            phase_label = f" in {filters['phase']} overs" if 'phase' in filters else ""
            
            return f"""
            -- 🏆 MOST SIXES{phase_label}
            SELECT 
                batter_full_name,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
                SUM(runs_batter) as total_runs,
                COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
                ROUND(SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as strike_rate
            FROM ipl_data_complete
            WHERE {where_clause}
            GROUP BY batter_full_name
            HAVING COUNT(CASE WHEN valid_ball = 1 THEN 1 END) >= 50
            ORDER BY sixes DESC
            LIMIT 15
            """
        
        else:
            # Top run scorers
            phase_label = f" in {filters['phase']} overs" if 'phase' in filters else ""
            min_runs = filters.get('min_runs', 50)
            
            return f"""
            -- 🏆 TOP RUN SCORERS{phase_label}
            SELECT 
                batter_full_name,
                COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
                SUM(runs_batter) as total_runs,
                COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
                COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
                ROUND(SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as strike_rate
            FROM ipl_data_complete
            WHERE {where_clause}
            GROUP BY batter_full_name
            HAVING SUM(runs_batter) >= {min_runs}
            ORDER BY total_runs DESC
            LIMIT 15
            """

def get_database_connection():
    """Get database connection"""
    try:
        connection_string = "postgresql://neondb_owner:npg_xBSUw9Zu5HMy@ep-young-lake-a1usk5d6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        engine = create_engine(connection_string)
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

if __name__ == "__main__":
    print('🏏 TESTING CORRECT CRICKET ANALYTICS')
    print('=' * 60)
    
    # Get database connection
    engine, error = get_database_connection()
    if not engine:
        print(f"Database connection failed: {error}")
        exit(1)
    
    analyzer = CricketIPLAnalyzer(engine)
    generator = CricketQueryGenerator(analyzer)
    
    # Test the user's specific queries
    test_queries = [
        'best batters in middle overs (min 500 runs)',
        'bowlers with the highest economy',
        'kohli v spin bowling',
        'Rashid Khan v LHB',
        'most sixes in death overs'
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f'\n🔍 Test {i}: {query}')
        print('-' * 50)
        
        # Analyze
        analysis = analyzer.analyze_query(query)
        print(f'Type: {analysis["query_type"]}')
        print(f'Filters: {analysis["filters"]}')
        
        # Generate SQL
        sql = generator.generate_sql(analysis)
        print(f'SQL Preview: {sql.strip()[:150]}...')
        
        # Execute
        try:
            result = execute_query(engine, sql)
            if isinstance(result, pd.DataFrame):
                print(f'✅ SUCCESS: {len(result)} rows returned')
                if len(result) > 0:
                    print('Sample results:')
                    print(result.head(3).to_string(index=False)[:300])
            else:
                print(f'❌ ERROR: {result}')
        except Exception as e:
            print(f'❌ EXCEPTION: {e}')