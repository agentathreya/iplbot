# 🏏 Cricket Analytics Research & Query Patterns

## Key Issues Found in Current Implementation:
1. **Filters are detected but NOT applied in SQL WHERE clause**
2. **Phase analysis ignores over_col filtering**  
3. **Bowling type matchups ignore bowling_type column**
4. **Top performers don't respect minimum criteria**
5. **Player vs bowling style queries ignore bowling_type**

## Correct Cricket Analytics Patterns:

### 1. Phase Analysis (Powerplay/Middle/Death Overs)
```sql
-- Powerplay: overs 1-6 (over_col BETWEEN 1 AND 6)
-- Middle overs: overs 7-15 (over_col BETWEEN 7 AND 15) 
-- Death overs: overs 16-20 (over_col BETWEEN 16 AND 20)

-- Example: Best batters in middle overs (min 500 runs)
SELECT 
    batter_full_name,
    COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
    SUM(runs_batter) as total_runs,
    COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
    COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
    ROUND(SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as strike_rate
FROM ipl_data_complete 
WHERE over_col BETWEEN 7 AND 15  -- MIDDLE OVERS FILTER
  AND valid_ball = 1
GROUP BY batter_full_name
HAVING SUM(runs_batter) >= 500  -- MIN 500 RUNS FILTER
ORDER BY total_runs DESC
```

### 2. Player vs Bowling Type
```sql
-- Example: Kohli vs spin bowling  
SELECT 
    batter_full_name,
    bowling_type,
    COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_faced,
    SUM(runs_batter) as runs,
    COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
    COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
    COUNT(CASE WHEN is_wicket = 1 AND player_out = batter_full_name THEN 1 END) as dismissals,
    ROUND(SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as strike_rate
FROM ipl_data_complete
WHERE batter_full_name = 'Virat Kohli'  -- PLAYER FILTER
  AND bowling_type = 'spin'              -- BOWLING TYPE FILTER  
  AND valid_ball = 1
GROUP BY batter_full_name, bowling_type
```

### 3. Top Performers with Filters
```sql  
-- Example: Best economy rate bowlers in powerplay
SELECT 
    bowler_full_name,
    COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_bowled,
    SUM(runs_total) as runs_conceded,
    COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as wickets,
    ROUND((SUM(runs_total) * 6.0) / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as economy_rate
FROM ipl_data_complete
WHERE over_col BETWEEN 1 AND 6  -- POWERPLAY FILTER
  AND valid_ball = 1
GROUP BY bowler_full_name  
HAVING COUNT(CASE WHEN valid_ball = 1 THEN 1 END) >= 50  -- MIN BALLS FILTER
ORDER BY economy_rate ASC  -- BEST (LOWEST) ECONOMY
LIMIT 15
```

### 4. Player vs Player Matchups
```sql
-- Example: Virat Kohli vs Jasprit Bumrah
SELECT 
    batter_full_name,
    bowler_full_name, 
    COUNT(*) as balls_faced,
    SUM(runs_batter) as runs_scored,
    COUNT(CASE WHEN is_four = 1 THEN 1 END) as fours,
    COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
    COUNT(CASE WHEN is_wicket = 1 AND player_out = batter_full_name THEN 1 END) as dismissals,
    ROUND(SUM(runs_batter) * 100.0 / COUNT(*), 2) as strike_rate
FROM ipl_data_complete
WHERE batter_full_name = 'Virat Kohli'
  AND bowler_full_name = 'Jasprit Bumrah' 
  AND valid_ball = 1
GROUP BY batter_full_name, bowler_full_name
```

### 5. Player vs Batting Style (LHB/RHB)
```sql
-- Example: Rashid Khan vs Left-handed batters
SELECT 
    bowler_full_name,
    batting_style,
    COUNT(CASE WHEN valid_ball = 1 THEN 1 END) as balls_bowled,
    SUM(runs_total) as runs_conceded,
    COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as wickets,
    ROUND((SUM(runs_total) * 6.0) / COUNT(CASE WHEN valid_ball = 1 THEN 1 END), 2) as economy_rate,
    ROUND(COUNT(CASE WHEN valid_ball = 1 THEN 1 END) * 1.0 / COUNT(CASE WHEN is_wicket = 1 THEN 1 END), 2) as balls_per_wicket
FROM ipl_data_complete
WHERE bowler_full_name = 'Rashid Khan'
  AND batting_style = 'LHB'  -- LEFT-HANDED BATTERS
  AND valid_ball = 1
GROUP BY bowler_full_name, batting_style
```

### 6. Team vs Team Head-to-Head
```sql
-- Example: CSK vs MI head to head 
WITH team_scores AS (
    SELECT 
        match_id,
        season,
        venue,
        winner,
        batting_team,
        SUM(runs_total) as team_total
    FROM ipl_data_complete
    WHERE (batting_team IN ('Chennai Super Kings', 'Mumbai Indians') 
           AND bowling_team IN ('Chennai Super Kings', 'Mumbai Indians'))
    GROUP BY match_id, season, venue, winner, batting_team
)
SELECT 
    COUNT(DISTINCT match_id) as total_matches,
    COUNT(CASE WHEN winner = 'Chennai Super Kings' THEN 1 END) as csk_wins,
    COUNT(CASE WHEN winner = 'Mumbai Indians' THEN 1 END) as mi_wins,
    ROUND(AVG(CASE WHEN batting_team = 'Chennai Super Kings' THEN team_total END), 1) as csk_avg_score,
    ROUND(AVG(CASE WHEN batting_team = 'Mumbai Indians' THEN team_total END), 1) as mi_avg_score
FROM team_scores
```

## Key Columns to Understand:
- `over_col`: Over number (1-20)
- `valid_ball`: 1 for valid deliveries (excludes wides/no-balls)
- `bowling_type`: 'pace' or 'spin'  
- `batting_style`: 'LHB' (left-handed) or 'RHB' (right-handed)
- `runs_batter`: Runs scored by batter off that ball
- `runs_total`: Total runs off that ball (including extras)
- `is_wicket`: 1 if wicket fell on that ball
- `player_out`: Name of player who got out