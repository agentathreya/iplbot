import psycopg2
import os
from typing import List, Dict, Any
import logging
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                
                # Get column names
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    result = []
                    for row in rows:
                        result.append(dict(zip(columns, row)))
                    
                    return result
                else:
                    return []
                    
            except Exception as e:
                logger.error(f"Query execution error: {e}")
                logger.error(f"Query: {query}")
                raise
    
    def get_all_players(self) -> List[str]:
        """Get all unique player names from the database"""
        query = """
        SELECT DISTINCT batter_full_name FROM ipl_data WHERE batter_full_name IS NOT NULL
        UNION
        SELECT DISTINCT bowler_full_name FROM ipl_data WHERE bowler_full_name IS NOT NULL
        UNION
        SELECT DISTINCT non_striker_full_name FROM ipl_data WHERE non_striker_full_name IS NOT NULL
        ORDER BY 1
        """
        try:
            results = self.execute_query(query)
            return [row['batter_full_name'] for row in results if row['batter_full_name']]
        except Exception as e:
            logger.error(f"Error fetching players: {e}")
            return []
    
    def get_all_teams(self) -> List[str]:
        """Get all unique team names"""
        query = """
        SELECT DISTINCT batting_team FROM ipl_data WHERE batting_team IS NOT NULL
        UNION
        SELECT DISTINCT bowling_team FROM ipl_data WHERE bowling_team IS NOT NULL
        ORDER BY 1
        """
        try:
            results = self.execute_query(query)
            return [row['batting_team'] for row in results if row['batting_team']]
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            return []
    
    def get_all_venues(self) -> List[str]:
        """Get all unique venues"""
        query = "SELECT DISTINCT venue FROM ipl_data WHERE venue IS NOT NULL ORDER BY venue"
        try:
            results = self.execute_query(query)
            return [row['venue'] for row in results if row['venue']]
        except Exception as e:
            logger.error(f"Error fetching venues: {e}")
            return []
    
    def get_schema_info(self) -> Dict[str, str]:
        """Get database schema information"""
        query = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'ipl_data' 
        ORDER BY ordinal_position
        """
        try:
            results = self.execute_query(query)
            return {row['column_name']: row['data_type'] for row in results}
        except Exception as e:
            logger.error(f"Error fetching schema: {e}")
            return {}