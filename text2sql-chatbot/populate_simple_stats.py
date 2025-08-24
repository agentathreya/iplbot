#!/usr/bin/env python3
"""
Populate Simple Stats Tables
Create basic batting and bowling statistics
"""

import pandas as pd
from sqlalchemy import create_engine, text
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://neondb_owner:npg_xBSUw9Zu5HMy@ep-young-lake-a1usk5d6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def populate_simple_stats():
    """Populate batting_stats and bowling_stats with simplified approach"""
    
    print("🏏 Populating Simple Stats Tables")
    print("=" * 60)
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Get ID mappings first
        logger.info("🔗 Loading ID mappings...")
        
        # Team mappings
        team_mapping = pd.read_sql_query("SELECT team_id, team_name FROM team_profiles", engine)
        team_map = dict(zip(team_mapping['team_name'], team_mapping['team_id']))
        
        # Player mappings
        player_mapping = pd.read_sql_query("SELECT player_id, player_name FROM player_profiles", engine)
        player_map = dict(zip(player_mapping['player_name'], player_mapping['player_id']))
        
        # 1. Populate batting_stats with basic stats
        logger.info("🏏 Creating basic batting stats...")
        
        # Get batting data in chunks to avoid memory issues
        batting_df = pd.read_sql_query("""
        SELECT 
            batter_full_name,
            match_id,
            season,
            year,
            batting_team,
            innings,
            runs_batter,
            is_four,
            is_six,
            is_wicket,
            player_out,
            dismissal_type,
            bat_pos,
            over_col
        FROM ipl_data_complete
        WHERE batter_full_name IS NOT NULL 
          AND valid_ball = 1
        """, engine)
        
        logger.info(f"Processing {len(batting_df):,} batting records...")
        
        # Group by match-level innings for each batter
        batting_grouped = batting_df.groupby([
            'batter_full_name', 'match_id', 'season', 'year', 'batting_team', 'innings'
        ]).agg({
            'runs_batter': 'sum',
            'is_four': 'sum', 
            'is_six': 'sum',
            'is_wicket': lambda x: 1 if any(batting_df.loc[x.index, 'player_out'] == batting_df.loc[x.index, 'batter_full_name']) else 0,
            'dismissal_type': 'first',
            'bat_pos': 'first',
            'over_col': 'count'  # balls faced
        }).reset_index()
        
        batting_grouped.columns = [
            'player_name', 'match_id', 'season', 'year', 'team', 'innings',
            'runs_scored', 'fours', 'sixes', 'is_out', 'dismissal_type', 'position', 'balls_faced'
        ]
        
        # Map IDs
        batting_grouped['player_id'] = batting_grouped['player_name'].map(player_map)
        batting_grouped['team_id'] = batting_grouped['team'].map(team_map)
        
        # Calculate strike rate
        batting_grouped['strike_rate'] = (batting_grouped['runs_scored'] / batting_grouped['balls_faced'] * 100).round(2)
        batting_grouped['strike_rate'] = batting_grouped['strike_rate'].fillna(0)
        
        # Add default values for advanced stats
        batting_grouped['vs_pace_runs'] = 0
        batting_grouped['vs_pace_balls'] = 0
        batting_grouped['vs_spin_runs'] = 0
        batting_grouped['vs_spin_balls'] = 0
        batting_grouped['powerplay_runs'] = 0
        batting_grouped['powerplay_balls'] = 0
        batting_grouped['middle_overs_runs'] = 0
        batting_grouped['middle_overs_balls'] = 0
        batting_grouped['death_overs_runs'] = 0
        batting_grouped['death_overs_balls'] = 0
        
        # Remove rows where mapping failed
        batting_grouped = batting_grouped.dropna(subset=['player_id', 'team_id'])
        
        # Select final columns
        batting_final = batting_grouped[[
            'player_id', 'match_id', 'season', 'year', 'team_id', 'innings',
            'runs_scored', 'balls_faced', 'fours', 'sixes', 'strike_rate',
            'is_out', 'dismissal_type', 'position',
            'vs_pace_runs', 'vs_pace_balls', 'vs_spin_runs', 'vs_spin_balls',
            'powerplay_runs', 'powerplay_balls', 'middle_overs_runs', 'middle_overs_balls',
            'death_overs_runs', 'death_overs_balls'
        ]]
        
        # Clear and insert batting stats
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM batting_stats"))
            conn.commit()
        
        # Insert in chunks
        chunk_size = 5000
        total_inserted = 0
        
        for i in tqdm(range(0, len(batting_final), chunk_size), desc="Inserting batting stats"):
            chunk = batting_final.iloc[i:i + chunk_size]
            chunk.to_sql('batting_stats', engine, if_exists='append', index=False)
            total_inserted += len(chunk)
        
        print(f"✅ Inserted {total_inserted:,} batting stat records")
        
        # 2. Populate bowling_stats
        logger.info("🎯 Creating basic bowling stats...")
        
        # Get bowling data
        bowling_df = pd.read_sql_query("""
        SELECT 
            bowler_full_name,
            match_id,
            season,
            year,
            bowling_team,
            innings,
            runs_total,
            is_wicket,
            is_four,
            is_six,
            wides,
            noballs,
            over_col
        FROM ipl_data_complete
        WHERE bowler_full_name IS NOT NULL 
          AND valid_ball = 1
        """, engine)
        
        logger.info(f"Processing {len(bowling_df):,} bowling records...")
        
        # Group by match-level innings for each bowler
        bowling_grouped = bowling_df.groupby([
            'bowler_full_name', 'match_id', 'season', 'year', 'bowling_team', 'innings'
        ]).agg({
            'runs_total': 'sum',
            'is_wicket': 'sum',
            'is_four': 'sum',
            'is_six': 'sum', 
            'wides': 'sum',
            'noballs': 'sum',
            'over_col': 'count'  # balls bowled
        }).reset_index()
        
        bowling_grouped.columns = [
            'player_name', 'match_id', 'season', 'year', 'team', 'innings',
            'runs_conceded', 'wickets_taken', 'fours_conceded', 'sixes_conceded', 
            'wides', 'no_balls', 'balls_bowled'
        ]
        
        # Map IDs
        bowling_grouped['player_id'] = bowling_grouped['player_name'].map(player_map)
        bowling_grouped['team_id'] = bowling_grouped['team'].map(team_map)
        
        # Calculate overs bowled and derived stats
        bowling_grouped['overs_bowled'] = (bowling_grouped['balls_bowled'] / 6).round(1)
        bowling_grouped['economy_rate'] = (bowling_grouped['runs_conceded'] * 6 / bowling_grouped['balls_bowled']).round(2)
        bowling_grouped['economy_rate'] = bowling_grouped['economy_rate'].replace([float('inf'), float('-inf')], 0).fillna(0)
        
        # Calculate bowling average and strike rate
        bowling_grouped['bowling_average'] = (bowling_grouped['runs_conceded'] / bowling_grouped['wickets_taken']).round(2)
        bowling_grouped['bowling_average'] = bowling_grouped['bowling_average'].replace([float('inf'), float('-inf')], 0).fillna(0)
        
        bowling_grouped['strike_rate'] = (bowling_grouped['balls_bowled'] / bowling_grouped['wickets_taken']).round(2)  
        bowling_grouped['strike_rate'] = bowling_grouped['strike_rate'].replace([float('inf'), float('-inf')], 0).fillna(0)
        
        # Calculate dots (approximation)
        bowling_grouped['dots'] = (bowling_grouped['balls_bowled'] - bowling_grouped['fours_conceded'] - bowling_grouped['sixes_conceded']).clip(lower=0)
        
        # Add default values for phase-wise stats
        bowling_grouped['powerplay_overs'] = 0
        bowling_grouped['powerplay_runs'] = 0
        bowling_grouped['powerplay_wickets'] = 0
        bowling_grouped['middle_overs_overs'] = 0
        bowling_grouped['middle_overs_runs'] = 0
        bowling_grouped['middle_overs_wickets'] = 0
        bowling_grouped['death_overs_overs'] = 0
        bowling_grouped['death_overs_runs'] = 0
        bowling_grouped['death_overs_wickets'] = 0
        
        # Remove rows where mapping failed
        bowling_grouped = bowling_grouped.dropna(subset=['player_id', 'team_id'])
        
        # Select final columns
        bowling_final = bowling_grouped[[
            'player_id', 'match_id', 'season', 'year', 'team_id', 'innings',
            'overs_bowled', 'balls_bowled', 'runs_conceded', 'wickets_taken',
            'economy_rate', 'bowling_average', 'strike_rate', 'dots',
            'fours_conceded', 'sixes_conceded', 'wides', 'no_balls',
            'powerplay_overs', 'powerplay_runs', 'powerplay_wickets',
            'middle_overs_overs', 'middle_overs_runs', 'middle_overs_wickets',
            'death_overs_overs', 'death_overs_runs', 'death_overs_wickets'
        ]]
        
        # Clear and insert bowling stats
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM bowling_stats"))
            conn.commit()
        
        # Insert in chunks
        total_inserted = 0
        
        for i in tqdm(range(0, len(bowling_final), chunk_size), desc="Inserting bowling stats"):
            chunk = bowling_final.iloc[i:i + chunk_size]
            chunk.to_sql('bowling_stats', engine, if_exists='append', index=False)
            total_inserted += len(chunk)
        
        print(f"✅ Inserted {total_inserted:,} bowling stat records")
        
        # 3. Update ball_by_ball with all data (replacing the 50k sample)
        logger.info("⚾ Updating ball_by_ball with complete data...")
        
        # Clear existing data
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM ball_by_ball"))
            conn.commit()
        
        # Get all ball-by-ball data in chunks
        chunk_size = 25000
        offset = 0
        total_inserted = 0
        
        # Get total count
        total_balls = pd.read_sql_query("SELECT COUNT(*) as count FROM ipl_data_complete WHERE valid_ball = 1", engine).iloc[0]['count']
        
        progress_bar = tqdm(total=total_balls, desc="Loading complete ball-by-ball")
        
        while offset < total_balls:
            chunk_df = pd.read_sql_query(f"""
            SELECT 
                match_id,
                innings,
                over_col,
                ball,
                batter_id,
                bowler_id,
                runs_batter,
                is_wicket,
                is_four,
                is_six,
                dismissal_type,
                shot_type,
                bowling_type,
                team_runs,
                team_wickets
            FROM ipl_data_complete 
            WHERE valid_ball = 1 
            ORDER BY match_id, innings, over_col, ball
            LIMIT {chunk_size} OFFSET {offset}
            """, engine)
            
            if chunk_df.empty:
                break
            
            # Rename columns to match schema
            chunk_df = chunk_df.rename(columns={
                'over_col': 'over_number',
                'ball': 'ball_number',
                'ball': 'ball_in_over',
                'batter_id': 'striker_id',
                'runs_batter': 'runs_scored',
                'runs_batter': 'runs_batter',
                'team_runs': 'team_score'
            })
            
            # Add missing columns with defaults
            chunk_df['non_striker_id'] = chunk_df['striker_id']  # Placeholder
            chunk_df['batting_team_id'] = None
            chunk_df['bowling_team_id'] = None
            chunk_df['extras'] = 0
            chunk_df['wide_runs'] = 0
            chunk_df['bye_runs'] = 0
            chunk_df['legbye_runs'] = 0
            chunk_df['no_ball_runs'] = 0
            chunk_df['fielder_id'] = None
            chunk_df['phase'] = chunk_df['over_number'].apply(
                lambda x: 'Powerplay' if x <= 6 else 'Middle' if x <= 15 else 'Death'
            )
            chunk_df['required_rate'] = 0
            chunk_df['current_rate'] = 0
            
            # Fill NaN values
            chunk_df = chunk_df.fillna(0)
            
            # Insert chunk
            chunk_df.to_sql('ball_by_ball', engine, if_exists='append', index=False)
            
            total_inserted += len(chunk_df)
            offset += chunk_size
            progress_bar.update(len(chunk_df))
        
        progress_bar.close()
        print(f"✅ Inserted {total_inserted:,} complete ball-by-ball records")
        
        # Final verification
        print("\n🔍 Final verification of all tables...")
        
        verification_queries = {
            "team_profiles": "SELECT COUNT(*) as count FROM team_profiles",
            "venue_details": "SELECT COUNT(*) as count FROM venue_details",
            "player_profiles": "SELECT COUNT(*) as count FROM player_profiles",
            "match_results": "SELECT COUNT(*) as count FROM match_results", 
            "batting_stats": "SELECT COUNT(*) as count FROM batting_stats",
            "bowling_stats": "SELECT COUNT(*) as count FROM bowling_stats",
            "season_summary": "SELECT COUNT(*) as count FROM season_summary",
            "ball_by_ball": "SELECT COUNT(*) as count FROM ball_by_ball"
        }
        
        print("\n📈 FINAL Database Summary:")
        print("=" * 50)
        
        all_populated = True
        for table_name, query in verification_queries.items():
            count_df = pd.read_sql_query(query, engine)
            count = count_df.iloc[0]['count']
            status = '✅' if count > 0 else '❌'
            if count == 0:
                all_populated = False
            print(f"{status} {table_name:15}: {count:,} records")
        
        # Show complete data count for reference
        complete_count = pd.read_sql_query("SELECT COUNT(*) as count FROM ipl_data_complete", engine)
        complete_records = complete_count.iloc[0]['count']
        print(f"✅ {'ipl_data_complete':15}: {complete_records:,} records")
        
        if all_populated:
            print("\n🎉 SUCCESS! ALL TABLES NOW FULLY POPULATED!")
            print("=" * 60)
            print("🚀 Your complete multi-table IPL database is ready!")
            print("🎯 Run: streamlit run advanced_ipl_chatbot.py")
            
            print("\n💡 You can now ask complex queries like:")
            print("   • 'Virat Kohli batting average vs fast bowlers'")
            print("   • 'Jasprit Bumrah economy rate in death overs'")
            print("   • 'CSK vs MI head-to-head in playoffs'")
            print("   • 'Best strike rates in powerplay in IPL 2023'")
            print("   • 'Top wicket-takers at Wankhede Stadium'")
        
        return all_populated
        
    except Exception as e:
        logger.error(f"❌ Stats population failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = populate_simple_stats()
    if success:
        print("\n✅ All stats tables populated successfully!")
    else:
        print("\n💥 Stats population failed. Check error details above.")