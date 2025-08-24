#!/usr/bin/env python3
"""
Populate Essential Tables from Complete Data
Using existing IDs from the complete table
"""

import pandas as pd
from sqlalchemy import create_engine, text
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://neondb_owner:npg_xBSUw9Zu5HMy@ep-young-lake-a1usk5d6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def populate_essential_tables():
    """Populate key tables using existing IDs from complete data"""
    
    print("🏏 Populating Essential Tables with Proper IDs")
    print("=" * 60)
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Verify complete data exists
        logger.info("✅ Checking ipl_data_complete table...")
        total_count = pd.read_sql_query("SELECT COUNT(*) as count FROM ipl_data_complete", engine)
        total_records = total_count.iloc[0]['count']
        print(f"📊 Found {total_records:,} records in ipl_data_complete")
        
        # 1. Populate team_profiles using team names
        logger.info("🏅 Populating team_profiles...")
        
        # Create team mappings with proper short names
        team_mappings = {
            'Chennai Super Kings': 'CSK',
            'Royal Challengers Bangalore': 'RCB', 
            'Royal Challengers Bengaluru': 'RCB',
            'Mumbai Indians': 'MI',
            'Kolkata Knight Riders': 'KKR',
            'Delhi Daredevils': 'DD',
            'Delhi Capitals': 'DC',
            'Rajasthan Royals': 'RR',
            'Sunrisers Hyderabad': 'SRH',
            'Kings XI Punjab': 'KXIP',
            'Punjab Kings': 'PBKS',
            'Rising Pune Supergiants': 'RPS',
            'Rising Pune Supergiant': 'RPS',
            'Gujarat Lions': 'GL',
            'Kochi Tuskers Kerala': 'KTK',
            'Pune Warriors': 'PW',
            'Deccan Chargers': 'DCH',
            'Lucknow Super Giants': 'LSG',
            'Gujarat Titans': 'GT'
        }
        
        # Get unique teams from data
        teams_df = pd.read_sql_query("SELECT DISTINCT batting_team FROM ipl_data_complete WHERE batting_team IS NOT NULL", engine)
        
        # Insert teams manually with proper mappings
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM team_profiles"))
            conn.commit()
            
            for team_name in teams_df['batting_team']:
                short_name = team_mappings.get(team_name, team_name[:10])
                city = team_name.split()[-1] if len(team_name.split()) > 1 else team_name[:20]
                
                insert_query = """
                INSERT INTO team_profiles (team_name, team_short_name, team_city)
                VALUES (:team_name, :short_name, :city)
                """
                conn.execute(text(insert_query), {
                    'team_name': team_name,
                    'short_name': short_name,
                    'city': city
                })
            
            conn.commit()
            print(f"✅ Inserted {len(teams_df)} teams")
        
        # 2. Populate venue_details
        logger.info("🏟️ Populating venue_details...")
        venues_df = pd.read_sql_query("""
        SELECT DISTINCT venue as venue_name, country 
        FROM ipl_data_complete 
        WHERE venue IS NOT NULL
        """, engine)
        
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM venue_details"))
            conn.commit()
            
        venues_df.to_sql('venue_details', engine, if_exists='append', index=False)
        print(f"✅ Inserted {len(venues_df)} venues")
        
        # 3. Populate player_profiles using existing batter_id and bowler_id
        logger.info("👨‍💼 Populating player_profiles using existing IDs...")
        
        # Get unique batters with their IDs
        batters_df = pd.read_sql_query("""
        SELECT DISTINCT 
            batter_id as player_id,
            batter_full_name as player_name,
            batter_full_name as full_name,
            batting_style,
            bowling_style,
            'Batter' as player_role
        FROM ipl_data_complete 
        WHERE batter_full_name IS NOT NULL AND batter_id IS NOT NULL
        """, engine)
        
        # Get unique bowlers with their IDs
        bowlers_df = pd.read_sql_query("""
        SELECT DISTINCT 
            bowler_id as player_id,
            bowler_full_name as player_name,
            bowler_full_name as full_name,
            batting_style,
            bowling_style,
            'Bowler' as player_role
        FROM ipl_data_complete 
        WHERE bowler_full_name IS NOT NULL AND bowler_id IS NOT NULL
        """, engine)
        
        # Combine and handle duplicates (players who both bat and bowl)
        all_players = pd.concat([batters_df, bowlers_df], ignore_index=True)
        
        # For duplicate player_ids, keep the first one but update role to 'All-rounder'
        duplicate_ids = all_players[all_players.duplicated(['player_id'], keep=False)]['player_id'].unique()
        
        # Update role for all-rounders
        all_players.loc[all_players['player_id'].isin(duplicate_ids), 'player_role'] = 'All-rounder'
        
        # Remove duplicates based on player_id
        unique_players = all_players.drop_duplicates(subset=['player_id'], keep='first')
        
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM player_profiles"))
            conn.commit()
            
        unique_players.to_sql('player_profiles', engine, if_exists='append', index=False)
        print(f"✅ Inserted {len(unique_players)} player profiles")
        
        # 4. Populate season_summary
        logger.info("📊 Populating season_summary...")
        season_query = """
        INSERT INTO season_summary (season, year, total_matches, total_runs, total_wickets, total_fours, total_sixes)
        SELECT 
            season,
            year,
            COUNT(DISTINCT match_id) as total_matches,
            SUM(runs_batter) as total_runs,
            SUM(is_wicket) as total_wickets,
            SUM(is_four) as total_fours,
            SUM(is_six) as total_sixes
        FROM ipl_data_complete 
        WHERE season IS NOT NULL
        GROUP BY season, year
        """
        
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM season_summary"))
            result = conn.execute(text(season_query))
            conn.commit()
            print(f"✅ Inserted {result.rowcount} season summaries")
        
        # 5. Get ID mappings for further use
        logger.info("🔗 Creating ID mappings for reference...")
        
        # Team mappings
        team_mapping = pd.read_sql_query("SELECT team_id, team_name FROM team_profiles", engine)
        team_map = dict(zip(team_mapping['team_name'], team_mapping['team_id']))
        
        # Venue mappings
        venue_mapping = pd.read_sql_query("SELECT venue_id, venue_name FROM venue_details", engine)
        venue_map = dict(zip(venue_mapping['venue_name'], venue_mapping['venue_id']))
        
        # Player mappings (already have proper IDs)
        player_mapping = pd.read_sql_query("SELECT player_id, player_name FROM player_profiles", engine)
        player_map = dict(zip(player_mapping['player_name'], player_mapping['player_id']))
        
        # 6. Populate match_results with proper ID mapping
        logger.info("🏆 Populating match_results...")
        
        # Get match data and map IDs
        matches_df = pd.read_sql_query("""
        SELECT DISTINCT
            match_id,
            series_id,
            season,
            year,
            match_date,
            venue,
            batting_team,
            bowling_team,
            toss_winner,
            toss_decision,
            winner,
            result,
            player_of_match,
            is_super_over,
            day_game
        FROM ipl_data_complete 
        WHERE match_id IS NOT NULL AND innings = 1
        """, engine)
        
        # Map team and venue IDs
        matches_df['venue_id'] = matches_df['venue'].map(venue_map)
        matches_df['team1_id'] = matches_df['batting_team'].map(team_map)
        matches_df['team2_id'] = matches_df['bowling_team'].map(team_map)
        matches_df['toss_winner_id'] = matches_df['toss_winner'].map(team_map)
        matches_df['winner_id'] = matches_df['winner'].map(team_map)
        matches_df['player_of_match_id'] = matches_df['player_of_match'].map(player_map)
        
        # Prepare final match data
        match_insert_df = matches_df[[
            'match_id', 'series_id', 'season', 'year', 'match_date', 'venue_id', 
            'team1_id', 'team2_id', 'toss_winner_id', 'toss_decision', 'winner_id',
            'result', 'player_of_match_id', 'is_super_over', 'day_game'
        ]].rename(columns={
            'result': 'result_type', 
            'is_super_over': 'is_super_over', 
            'day_game': 'is_day_game'
        })
        
        # Clear and insert
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM match_results"))
            conn.commit()
            
        match_insert_df.to_sql('match_results', engine, if_exists='append', index=False)
        print(f"✅ Inserted {len(match_insert_df)} match results")
        
        # 7. Sample ball_by_ball data (first 50k records to demonstrate structure)
        logger.info("⚾ Populating sample ball_by_ball data...")
        
        sample_ball_df = pd.read_sql_query("""
        SELECT 
            match_id,
            innings,
            over_col as over_number,
            ball as ball_number,
            ball as ball_in_over,
            batter_id as striker_id,
            bowler_id,
            runs_batter as runs_scored,
            runs_batter,
            is_wicket,
            is_four,
            is_six,
            dismissal_type,
            shot_type,
            bowling_type,
            team_runs as team_score,
            team_wickets
        FROM ipl_data_complete 
        WHERE valid_ball = 1 
        LIMIT 50000
        """, engine)
        
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM ball_by_ball"))
            conn.commit()
            
        sample_ball_df.to_sql('ball_by_ball', engine, if_exists='append', index=False)
        print(f"✅ Inserted {len(sample_ball_df)} sample ball-by-ball records")
        
        # Verification
        print("\n🔍 Verifying all tables populated...")
        
        verification_queries = {
            "team_profiles": "SELECT COUNT(*) as count FROM team_profiles",
            "venue_details": "SELECT COUNT(*) as count FROM venue_details", 
            "player_profiles": "SELECT COUNT(*) as count FROM player_profiles",
            "match_results": "SELECT COUNT(*) as count FROM match_results",
            "season_summary": "SELECT COUNT(*) as count FROM season_summary",
            "ball_by_ball": "SELECT COUNT(*) as count FROM ball_by_ball"
        }
        
        print("\n📈 Final Database Summary:")
        print("=" * 40)
        
        for table_name, query in verification_queries.items():
            count_df = pd.read_sql_query(query, engine)
            count = count_df.iloc[0]['count']
            print(f"• {table_name:15}: {count:,} records")
        
        # Show complete data count for reference
        complete_count = pd.read_sql_query("SELECT COUNT(*) as count FROM ipl_data_complete", engine)
        complete_records = complete_count.iloc[0]['count'] 
        print(f"• {'ipl_data_complete':15}: {complete_records:,} records")
        
        print("\n🎉 SUCCESS! Essential normalized tables populated!")
        print("=" * 60)
        print("🚀 Your advanced IPL analytics database is ready!")
        print("🎯 Run: streamlit run advanced_ipl_chatbot.py")
        
        # Show sample queries you can now run
        print("\n💡 Example advanced queries you can now ask:")
        print("   • 'Show me Virat Kohli vs Jasprit Bumrah head to head'")
        print("   • 'MS Dhoni strike rate in death overs'") 
        print("   • 'Top performers in IPL 2023'")
        print("   • 'CSK vs MI historical record'")
        print("   • 'Best bowling figures at Wankhede Stadium'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Table population failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = populate_essential_tables()
    if success:
        print("\n✅ All essential tables created successfully!")
        print("Your multi-table IPL database is ready for advanced analytics!")
    else:
        print("\n💥 Table population failed. Check error details above.")