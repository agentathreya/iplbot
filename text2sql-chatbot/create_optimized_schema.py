#!/usr/bin/env python3
"""
IPL Database Schema Creator - Optimized for AI Chatbot
Creates multiple normalized tables for better query performance and AI understanding
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import logging
from typing import Dict, List, Optional
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IPLSchemaCreator:
    def __init__(self, database_url: str):
        """Initialize with database connection"""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
    def create_optimized_schema(self):
        """Create optimized multi-table schema for AI chatbot"""
        
        schema_sql = """
        -- =====================================================
        -- IPL DATABASE SCHEMA - OPTIMIZED FOR AI CHATBOT
        -- =====================================================
        
        -- Drop existing tables if they exist
        DROP TABLE IF EXISTS ball_by_ball CASCADE;
        DROP TABLE IF EXISTS batting_stats CASCADE;
        DROP TABLE IF EXISTS bowling_stats CASCADE;
        DROP TABLE IF EXISTS match_results CASCADE;
        DROP TABLE IF EXISTS player_profiles CASCADE;
        DROP TABLE IF EXISTS team_profiles CASCADE;
        DROP TABLE IF EXISTS venue_details CASCADE;
        DROP TABLE IF EXISTS season_summary CASCADE;
        DROP TABLE IF EXISTS ipl_data_complete CASCADE;
        
        -- =====================================================
        -- 1. TEAM PROFILES - Basic team information
        -- =====================================================
        CREATE TABLE team_profiles (
            team_id SERIAL PRIMARY KEY,
            team_name VARCHAR(100) UNIQUE NOT NULL,
            team_short_name VARCHAR(10),
            team_city VARCHAR(50),
            team_color VARCHAR(20),
            founded_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- =====================================================
        -- 2. VENUE DETAILS - Stadium information
        -- =====================================================
        CREATE TABLE venue_details (
            venue_id SERIAL PRIMARY KEY,
            venue_name VARCHAR(200) UNIQUE NOT NULL,
            city VARCHAR(100),
            country VARCHAR(50),
            capacity INTEGER,
            pitch_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- =====================================================
        -- 3. PLAYER PROFILES - Player information
        -- =====================================================
        CREATE TABLE player_profiles (
            player_id INTEGER PRIMARY KEY,
            player_name VARCHAR(100) NOT NULL,
            full_name VARCHAR(150),
            batting_style VARCHAR(20),
            bowling_style VARCHAR(50),
            player_role VARCHAR(30),
            nationality VARCHAR(50),
            debut_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- =====================================================
        -- 4. MATCH RESULTS - Match-level information
        -- =====================================================
        CREATE TABLE match_results (
            match_id INTEGER PRIMARY KEY,
            series_id INTEGER,
            season VARCHAR(10),
            year INTEGER,
            match_date DATE,
            venue_id INTEGER REFERENCES venue_details(venue_id),
            team1_id INTEGER REFERENCES team_profiles(team_id),
            team2_id INTEGER REFERENCES team_profiles(team_id),
            toss_winner_id INTEGER REFERENCES team_profiles(team_id),
            toss_decision VARCHAR(20),
            winner_id INTEGER REFERENCES team_profiles(team_id),
            result_type VARCHAR(20),
            margin_runs INTEGER,
            margin_wickets INTEGER,
            player_of_match_id INTEGER REFERENCES player_profiles(player_id),
            team1_score INTEGER,
            team1_wickets INTEGER,
            team1_overs DECIMAL(4,1),
            team2_score INTEGER,
            team2_wickets INTEGER,
            team2_overs DECIMAL(4,1),
            is_super_over INTEGER DEFAULT 0, -- 0=regular, 1=super over
            is_day_game INTEGER DEFAULT 0, -- 0=night game, 1=day game
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- =====================================================
        -- 5. BATTING STATS - Aggregated batting performance
        -- =====================================================
        CREATE TABLE batting_stats (
            id SERIAL PRIMARY KEY,
            player_id INTEGER REFERENCES player_profiles(player_id),
            match_id INTEGER REFERENCES match_results(match_id),
            season VARCHAR(10),
            year INTEGER,
            team_id INTEGER REFERENCES team_profiles(team_id),
            innings INTEGER,
            runs_scored INTEGER,
            balls_faced INTEGER,
            fours INTEGER,
            sixes INTEGER,
            strike_rate DECIMAL(6,2),
            is_out INTEGER, -- 0=not out, 1=out
            dismissal_type VARCHAR(30),
            position INTEGER,
            vs_pace_runs INTEGER DEFAULT 0,
            vs_pace_balls INTEGER DEFAULT 0,
            vs_spin_runs INTEGER DEFAULT 0,
            vs_spin_balls INTEGER DEFAULT 0,
            powerplay_runs INTEGER DEFAULT 0,
            powerplay_balls INTEGER DEFAULT 0,
            middle_overs_runs INTEGER DEFAULT 0,
            middle_overs_balls INTEGER DEFAULT 0,
            death_overs_runs INTEGER DEFAULT 0,
            death_overs_balls INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- =====================================================
        -- 6. BOWLING STATS - Aggregated bowling performance
        -- =====================================================
        CREATE TABLE bowling_stats (
            id SERIAL PRIMARY KEY,
            player_id INTEGER REFERENCES player_profiles(player_id),
            match_id INTEGER REFERENCES match_results(match_id),
            season VARCHAR(10),
            year INTEGER,
            team_id INTEGER REFERENCES team_profiles(team_id),
            innings INTEGER,
            overs_bowled DECIMAL(4,1),
            balls_bowled INTEGER,
            runs_conceded INTEGER,
            wickets_taken INTEGER,
            economy_rate DECIMAL(5,2),
            bowling_average DECIMAL(6,2),
            strike_rate DECIMAL(6,2),
            dots INTEGER,
            fours_conceded INTEGER,
            sixes_conceded INTEGER,
            wides INTEGER,
            no_balls INTEGER,
            powerplay_overs DECIMAL(4,1) DEFAULT 0,
            powerplay_runs INTEGER DEFAULT 0,
            powerplay_wickets INTEGER DEFAULT 0,
            middle_overs_overs DECIMAL(4,1) DEFAULT 0,
            middle_overs_runs INTEGER DEFAULT 0,
            middle_overs_wickets INTEGER DEFAULT 0,
            death_overs_overs DECIMAL(4,1) DEFAULT 0,
            death_overs_runs INTEGER DEFAULT 0,
            death_overs_wickets INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- =====================================================
        -- 7. SEASON SUMMARY - Season-level aggregations
        -- =====================================================
        CREATE TABLE season_summary (
            id SERIAL PRIMARY KEY,
            season VARCHAR(10),
            year INTEGER,
            total_matches INTEGER,
            total_runs INTEGER,
            total_wickets INTEGER,
            total_sixes INTEGER,
            total_fours INTEGER,
            highest_score INTEGER,
            highest_individual_score INTEGER,
            best_bowling_figures VARCHAR(10),
            orange_cap_winner_id INTEGER REFERENCES player_profiles(player_id),
            orange_cap_runs INTEGER,
            purple_cap_winner_id INTEGER REFERENCES player_profiles(player_id),
            purple_cap_wickets INTEGER,
            champion_team_id INTEGER REFERENCES team_profiles(team_id),
            runner_up_team_id INTEGER REFERENCES team_profiles(team_id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- =====================================================
        -- 8. BALL BY BALL - Detailed ball-by-ball data (condensed)
        -- =====================================================
        CREATE TABLE ball_by_ball (
            id SERIAL PRIMARY KEY,
            match_id INTEGER REFERENCES match_results(match_id),
            innings INTEGER,
            over_number INTEGER,
            ball_number INTEGER,
            ball_in_over INTEGER,
            striker_id INTEGER REFERENCES player_profiles(player_id),
            non_striker_id INTEGER REFERENCES player_profiles(player_id),
            bowler_id INTEGER REFERENCES player_profiles(player_id),
            batting_team_id INTEGER REFERENCES team_profiles(team_id),
            bowling_team_id INTEGER REFERENCES team_profiles(team_id),
            runs_scored INTEGER,
            runs_batter INTEGER,
            extras INTEGER,
            wide_runs INTEGER,
            bye_runs INTEGER,
            legbye_runs INTEGER,
            no_ball_runs INTEGER,
            is_wicket INTEGER, -- 0=no wicket, 1=wicket
            is_four INTEGER, -- 0=not four, 1=four
            is_six INTEGER, -- 0=not six, 1=six
            dismissal_type VARCHAR(30),
            fielder_id INTEGER REFERENCES player_profiles(player_id),
            shot_type VARCHAR(50),
            bowling_type VARCHAR(20),
            phase VARCHAR(20), -- powerplay, middle, death
            team_score INTEGER,
            team_wickets INTEGER,
            required_rate DECIMAL(5,2),
            current_rate DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- =====================================================
        -- 9. COMPLETE DATA TABLE - Full denormalized backup
        -- =====================================================
        CREATE TABLE ipl_data_complete (
            id SERIAL PRIMARY KEY,
            series_id INTEGER,
            season VARCHAR(20),
            series VARCHAR(100),
            match_type VARCHAR(20),
            year INTEGER,
            match_date DATE,
            venue TEXT,
            country VARCHAR(50),
            match_id INTEGER,
            match_no VARCHAR(50),
            batting_team VARCHAR(100),
            bowling_team VARCHAR(100),
            innings INTEGER,
            over_col INTEGER,
            ball INTEGER,
            ball_no DECIMAL(4,2),
            batter_id INTEGER,
            bowler_id INTEGER,
            batter VARCHAR(100),
            batter_full_name VARCHAR(150),
            non_striker VARCHAR(100),
            non_striker_full_name VARCHAR(150),
            bowler VARCHAR(100),
            bowler_full_name VARCHAR(150),
            runs_total INTEGER,
            runs_batter INTEGER,
            balls_faced INTEGER,
            valid_ball INTEGER,
            is_four INTEGER, -- 0=not four, 1=four  
            is_six INTEGER, -- 0=not six, 1=six
            is_wicket INTEGER, -- 0=no wicket, 1=wicket
            player_out VARCHAR(150),
            dismissal_type VARCHAR(50),
            fielder TEXT,
            is_wk INTEGER, -- 0=not wicket keeper, 1=wicket keeper
            is_sub INTEGER, -- 0=not substitute, 1=substitute
            byes INTEGER,
            legbyes INTEGER,
            wides INTEGER,
            noballs INTEGER,
            penalties INTEGER,
            wagon_x INTEGER,
            wagon_y INTEGER,
            wagon_zone INTEGER,
            pitch_line VARCHAR(50),
            pitch_length VARCHAR(50),
            shot_type VARCHAR(100),
            shot_control INTEGER,
            batting_style VARCHAR(20),
            long_batting_style VARCHAR(50),
            bowling_style VARCHAR(50),
            long_bowling_style VARCHAR(100),
            predicted_score DECIMAL(6,2),
            win_probability DECIMAL(6,2),
            team_runs INTEGER,
            team_balls INTEGER,
            team_wickets INTEGER,
            player_of_match VARCHAR(150),
            player_of_series VARCHAR(150),
            winner VARCHAR(100),
            toss_winner VARCHAR(100),
            toss_decision VARCHAR(20),
            is_super_over INTEGER, -- 0=regular, 1=super over
            result VARCHAR(20),
            batting_captain VARCHAR(150),
            bowling_captain VARCHAR(150),
            home_team VARCHAR(100),
            day_game INTEGER, -- 0=night game, 1=day game
            bat_pos INTEGER,
            event_type VARCHAR(50),
            event_fielder VARCHAR(150),
            event_batter VARCHAR(150),
            runs_target DECIMAL(6,2),
            target_balls DECIMAL(6,2),
            bowler_runs INTEGER,
            bowler_wicket INTEGER, -- 0=no wicket, 1=wicket
            curr_batter_runs INTEGER,
            curr_batter_balls INTEGER,
            curr_batter_fours INTEGER,
            curr_batter_sixes INTEGER,
            bowling_type VARCHAR(20),
            required_rr DECIMAL(6,2),
            current_rr DECIMAL(6,2),
            striker_out INTEGER, -- 0=not out, 1=out
            non_striker_pos DECIMAL(4,2),
            review_batter VARCHAR(150),
            team_reviewed VARCHAR(100),
            review_decision VARCHAR(50),
            umpire VARCHAR(150),
            umpires_call VARCHAR(50),
            stage VARCHAR(50),
            new_batter VARCHAR(150),
            batting_partners TEXT,
            next_batter VARCHAR(150),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- =====================================================
        -- CREATE ADDITIONAL INDEXES FOR PERFORMANCE
        -- =====================================================
        
        -- Batting stats indexes
        CREATE INDEX idx_batting_player_season ON batting_stats(player_id, season);
        CREATE INDEX idx_batting_team_season ON batting_stats(team_id, season);
        CREATE INDEX idx_batting_match ON batting_stats(match_id);
        
        -- Bowling stats indexes
        CREATE INDEX idx_bowling_player_season ON bowling_stats(player_id, season);
        CREATE INDEX idx_bowling_team_season ON bowling_stats(team_id, season);
        CREATE INDEX idx_bowling_match ON bowling_stats(match_id);
        
        -- Ball by ball indexes
        CREATE INDEX idx_ball_match_innings ON ball_by_ball(match_id, innings);
        CREATE INDEX idx_ball_striker ON ball_by_ball(striker_id);
        CREATE INDEX idx_ball_bowler ON ball_by_ball(bowler_id);
        CREATE INDEX idx_ball_phase ON ball_by_ball(phase);
        
        -- Complete data indexes
        CREATE INDEX idx_complete_match ON ipl_data_complete(match_id);
        CREATE INDEX idx_complete_batter ON ipl_data_complete(batter_full_name);
        CREATE INDEX idx_complete_bowler ON ipl_data_complete(bowler_full_name);
        CREATE INDEX idx_complete_season ON ipl_data_complete(season);
        CREATE INDEX idx_complete_team ON ipl_data_complete(batting_team, bowling_team);
        
        -- Match results indexes
        CREATE INDEX idx_match_season ON match_results(season, year);
        CREATE INDEX idx_match_venue ON match_results(venue_id);
        CREATE INDEX idx_match_teams ON match_results(team1_id, team2_id);
        CREATE INDEX idx_match_date ON match_results(match_date);
        
        -- Player profiles indexes
        CREATE INDEX idx_player_name ON player_profiles(player_name);
        CREATE INDEX idx_player_full_name ON player_profiles(full_name);
        CREATE INDEX idx_player_style ON player_profiles(batting_style, bowling_style);
        
        -- Team profiles indexes
        CREATE INDEX idx_team_name ON team_profiles(team_name);
        
        -- Venue details indexes  
        CREATE INDEX idx_venue_name ON venue_details(venue_name);
        CREATE INDEX idx_venue_city ON venue_details(city);
        
        COMMIT;
        """
        
        try:
            logger.info("🏗️ Creating optimized database schema...")
            
            with self.engine.connect() as conn:
                # Execute the schema creation
                conn.execute(text(schema_sql))
                conn.commit()
            
            logger.info("✅ Optimized schema created successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            return False
    
    def load_csv_data(self, csv_path: str):
        """Load CSV data into the complete table first, then populate normalized tables"""
        
        logger.info("📂 Loading CSV data...")
        
        try:
            # Read CSV with proper data types
            logger.info("Reading CSV file...")
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"Loaded {len(df):,} rows from CSV")
            
            # Clean column names for database compatibility
            df.columns = [col.replace(' ', '_').replace('-', '_').lower() for col in df.columns]
            
            # Handle data type conversions
            logger.info("Cleaning data types...")
            
            # Convert boolean columns to integers (0/1) for better compatibility
            bool_columns = ['isfour', 'issix', 'iswicket', 'issuperover', 'day_game', 'bowler_wicket', 'striker_out']
            for col in bool_columns:
                if col in df.columns:
                    # Convert boolean to integer (True->1, False->0)
                    df[col] = df[col].astype('boolean').astype('int')
            
            # Convert date columns
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df.rename(columns={'date': 'match_date'}, inplace=True)
            
            # Rename problematic columns
            column_mapping = {
                'over': 'over_col',
                'required_rr': 'required_rr', 
                'current_rr': 'current_rr',
                'non_striker.1': 'non_striker_alt'
            }
            
            df.rename(columns=column_mapping, inplace=True)
            
            # Load into complete table
            logger.info("Loading into ipl_data_complete table...")
            df.to_sql('ipl_data_complete', self.engine, if_exists='append', index=False, method='multi')
            logger.info(f"✅ Loaded {len(df):,} rows into ipl_data_complete")
            
            # Populate normalized tables
            self.populate_normalized_tables()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Data loading failed: {e}")
            return False
    
    def populate_normalized_tables(self):
        """Populate normalized tables from the complete data"""
        
        logger.info("🔄 Populating normalized tables...")
        
        try:
            # 1. Populate team_profiles
            logger.info("Populating team_profiles...")
            team_sql = """
            INSERT INTO team_profiles (team_name, team_short_name)
            SELECT DISTINCT 
                batting_team as team_name,
                CASE 
                    WHEN batting_team = 'Chennai Super Kings' THEN 'CSK'
                    WHEN batting_team = 'Mumbai Indians' THEN 'MI'
                    WHEN batting_team = 'Royal Challengers Bangalore' THEN 'RCB'
                    WHEN batting_team = 'Royal Challengers Bengaluru' THEN 'RCB'
                    WHEN batting_team = 'Kolkata Knight Riders' THEN 'KKR'
                    WHEN batting_team = 'Delhi Capitals' THEN 'DC'
                    WHEN batting_team = 'Delhi Daredevils' THEN 'DD'
                    WHEN batting_team = 'Rajasthan Royals' THEN 'RR'
                    WHEN batting_team = 'Punjab Kings' THEN 'PBKS'
                    WHEN batting_team = 'Kings XI Punjab' THEN 'KXIP'
                    WHEN batting_team = 'Sunrisers Hyderabad' THEN 'SRH'
                    WHEN batting_team = 'Gujarat Titans' THEN 'GT'
                    WHEN batting_team = 'Lucknow Super Giants' THEN 'LSG'
                    ELSE LEFT(batting_team, 3)
                END as team_short_name
            FROM ipl_data_complete 
            WHERE batting_team IS NOT NULL
            UNION
            SELECT DISTINCT 
                bowling_team as team_name,
                CASE 
                    WHEN bowling_team = 'Chennai Super Kings' THEN 'CSK'
                    WHEN bowling_team = 'Mumbai Indians' THEN 'MI'
                    WHEN bowling_team = 'Royal Challengers Bangalore' THEN 'RCB'
                    WHEN bowling_team = 'Royal Challengers Bengaluru' THEN 'RCB'
                    WHEN bowling_team = 'Kolkata Knight Riders' THEN 'KKR'
                    WHEN bowling_team = 'Delhi Capitals' THEN 'DC'
                    WHEN bowling_team = 'Delhi Daredevils' THEN 'DD'
                    WHEN bowling_team = 'Rajasthan Royals' THEN 'RR'
                    WHEN bowling_team = 'Punjab Kings' THEN 'PBKS'
                    WHEN bowling_team = 'Kings XI Punjab' THEN 'KXIP'
                    WHEN bowling_team = 'Sunrisers Hyderabad' THEN 'SRH'
                    WHEN bowling_team = 'Gujarat Titans' THEN 'GT'
                    WHEN bowling_team = 'Lucknow Super Giants' THEN 'LSG'
                    ELSE LEFT(bowling_team, 3)
                END as team_short_name
            FROM ipl_data_complete 
            WHERE bowling_team IS NOT NULL
            ON CONFLICT (team_name) DO NOTHING
            """
            
            with self.engine.connect() as conn:
                conn.execute(text(team_sql))
                conn.commit()
            
            # 2. Populate venue_details
            logger.info("Populating venue_details...")
            venue_sql = """
            INSERT INTO venue_details (venue_name, country)
            SELECT DISTINCT 
                venue as venue_name,
                country
            FROM ipl_data_complete 
            WHERE venue IS NOT NULL
            ON CONFLICT (venue_name) DO NOTHING
            """
            
            with self.engine.connect() as conn:
                conn.execute(text(venue_sql))
                conn.commit()
            
            # 3. Populate player_profiles
            logger.info("Populating player_profiles...")
            player_sql = """
            INSERT INTO player_profiles (player_id, player_name, full_name, batting_style, bowling_style)
            SELECT DISTINCT 
                batter_id as player_id,
                batter as player_name,
                batter_full_name as full_name,
                batting_style,
                NULL as bowling_style
            FROM ipl_data_complete 
            WHERE batter_id IS NOT NULL AND batter_full_name IS NOT NULL
            UNION
            SELECT DISTINCT 
                bowler_id as player_id,
                bowler as player_name,
                bowler_full_name as full_name,
                NULL as batting_style,
                bowling_style
            FROM ipl_data_complete 
            WHERE bowler_id IS NOT NULL AND bowler_full_name IS NOT NULL
            ON CONFLICT (player_id) DO UPDATE SET
                batting_style = COALESCE(player_profiles.batting_style, EXCLUDED.batting_style),
                bowling_style = COALESCE(player_profiles.bowling_style, EXCLUDED.bowling_style)
            """
            
            with self.engine.connect() as conn:
                conn.execute(text(player_sql))
                conn.commit()
            
            logger.info("✅ Normalized tables populated successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error populating normalized tables: {e}")
            raise

def main():
    """Main execution function"""
    
    DATABASE_URL = "postgresql://neondb_owner:npg_xBSUw9Zu5HMy@ep-young-lake-a1usk5d6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    CSV_PATH = "IPLdata final.csv"
    
    print("🏏 IPL Database Schema Creator")
    print("=" * 50)
    print("Creating optimized multi-table structure for AI chatbot")
    print()
    
    creator = IPLSchemaCreator(DATABASE_URL)
    
    # Step 1: Create schema
    print("Step 1: Creating optimized database schema...")
    if not creator.create_optimized_schema():
        print("❌ Schema creation failed!")
        return False
    
    # Step 2: Load data
    print("\nStep 2: Loading CSV data...")
    if not creator.load_csv_data(CSV_PATH):
        print("❌ Data loading failed!")
        return False
    
    print("\n🎉 IPL Database Setup Complete!")
    print("=" * 50)
    print("✅ 9 optimized tables created:")
    print("  📊 team_profiles      - Team information")
    print("  📊 venue_details      - Stadium information") 
    print("  📊 player_profiles    - Player information")
    print("  📊 match_results      - Match-level data")
    print("  📊 batting_stats      - Batting performance")
    print("  📊 bowling_stats      - Bowling performance")
    print("  📊 season_summary     - Season aggregations")
    print("  📊 ball_by_ball       - Ball-by-ball details")
    print("  📊 ipl_data_complete  - Complete backup table")
    print()
    print("🚀 Your chatbot is ready for optimal performance!")
    
    return True

if __name__ == "__main__":
    main()