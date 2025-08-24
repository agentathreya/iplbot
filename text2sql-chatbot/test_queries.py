#!/usr/bin/env python3
"""
Test Queries for IPL Chatbot - 30 queries from basic to advanced
"""

# 30 Test queries categorized by complexity and type
TEST_QUERIES = [
    
    # === BASIC BATTING QUERIES (1-8) ===
    {
        "id": 1,
        "query": "Virat Kohli total runs",
        "expected_type": "basic_stats",
        "category": "batting_basic",
        "description": "Basic player runs query"
    },
    {
        "id": 2,
        "query": "MS Dhoni career statistics",
        "expected_type": "basic_stats",
        "category": "batting_basic",
        "description": "Player career stats"
    },
    {
        "id": 3,
        "query": "Rohit Sharma sixes",
        "expected_type": "basic_stats",
        "category": "batting_basic",
        "description": "Player specific metric"
    },
    {
        "id": 4,
        "query": "ABD strike rate",
        "expected_type": "basic_stats",
        "category": "batting_basic",
        "description": "Player strike rate query"
    },
    {
        "id": 5,
        "query": "Gayle boundaries",
        "expected_type": "basic_stats",
        "category": "batting_basic",
        "description": "Player boundaries count"
    },
    {
        "id": 6,
        "query": "David Warner average",
        "expected_type": "basic_stats",
        "category": "batting_basic",
        "description": "Player batting average"
    },
    {
        "id": 7,
        "query": "Suresh Raina matches played",
        "expected_type": "basic_stats",
        "category": "batting_basic",
        "description": "Player matches count"
    },
    {
        "id": 8,
        "query": "KL Rahul runs in 2023",
        "expected_type": "basic_stats",
        "category": "batting_basic",
        "description": "Player runs in specific season"
    },
    
    # === BASIC BOWLING QUERIES (9-12) ===
    {
        "id": 9,
        "query": "Jasprit Bumrah wickets",
        "expected_type": "basic_stats",
        "category": "bowling_basic",
        "description": "Bowler wickets query"
    },
    {
        "id": 10,
        "query": "Rashid Khan economy rate",
        "expected_type": "basic_stats",
        "category": "bowling_basic",
        "description": "Bowler economy rate"
    },
    {
        "id": 11,
        "query": "Yuzvendra Chahal career stats",
        "expected_type": "basic_stats",
        "category": "bowling_basic",
        "description": "Bowler career statistics"
    },
    {
        "id": 12,
        "query": "Lasith Malinga total wickets",
        "expected_type": "basic_stats",
        "category": "bowling_basic",
        "description": "Bowler total wickets"
    },
    
    # === TEAM QUERIES (13-16) ===
    {
        "id": 13,
        "query": "CSK total wins",
        "expected_type": "basic_stats",
        "category": "team_basic",
        "description": "Team wins query"
    },
    {
        "id": 14,
        "query": "MI championship titles",
        "expected_type": "basic_stats",
        "category": "team_basic",
        "description": "Team titles count"
    },
    {
        "id": 15,
        "query": "RCB performance in 2023",
        "expected_type": "basic_stats",
        "category": "team_basic",
        "description": "Team season performance"
    },
    {
        "id": 16,
        "query": "KKR home record",
        "expected_type": "basic_stats",
        "category": "team_basic",
        "description": "Team home performance"
    },
    
    # === PHASE ANALYSIS QUERIES (17-20) ===
    {
        "id": 17,
        "query": "Rohit Sharma powerplay stats",
        "expected_type": "phase_analysis",
        "category": "batting_phase",
        "description": "Player powerplay performance"
    },
    {
        "id": 18,
        "query": "Kohli runs in death overs",
        "expected_type": "phase_analysis",
        "category": "batting_phase",
        "description": "Player death overs stats"
    },
    {
        "id": 19,
        "query": "MS Dhoni middle overs performance",
        "expected_type": "phase_analysis",
        "category": "batting_phase",
        "description": "Player middle overs stats"
    },
    {
        "id": 20,
        "query": "Bumrah death over bowling",
        "expected_type": "phase_analysis",
        "category": "bowling_phase",
        "description": "Bowler death overs performance"
    },
    
    # === MATCHUP QUERIES (21-24) ===
    {
        "id": 21,
        "query": "Virat Kohli vs Jasprit Bumrah",
        "expected_type": "matchup",
        "category": "matchup",
        "description": "Batter vs bowler matchup"
    },
    {
        "id": 22,
        "query": "Rohit Sharma against Rashid Khan",
        "expected_type": "matchup",
        "category": "matchup",
        "description": "Player vs player matchup"
    },
    {
        "id": 23,
        "query": "ABD vs Yuzvendra Chahal head to head",
        "expected_type": "matchup",
        "category": "matchup",
        "description": "Head to head analysis"
    },
    {
        "id": 24,
        "query": "Dhoni vs fast bowlers matchup",
        "expected_type": "matchup",
        "category": "matchup",
        "description": "Player vs bowling type"
    },
    
    # === ADVANCED QUERIES (25-30) ===
    {
        "id": 25,
        "query": "CSK vs MI head to head record",
        "expected_type": "matchup",
        "category": "team_matchup",
        "description": "Team vs team analysis"
    },
    {
        "id": 26,
        "query": "Top run scorers in 2023",
        "expected_type": "top_performers",
        "category": "advanced",
        "description": "Season top performers"
    },
    {
        "id": 27,
        "query": "Best economy rate in powerplay",
        "expected_type": "top_performers",
        "category": "advanced",
        "description": "Phase-wise top bowlers"
    },
    {
        "id": 28,
        "query": "Most sixes in death overs",
        "expected_type": "top_performers",
        "category": "advanced",
        "description": "Phase-wise hitting stats"
    },
    {
        "id": 29,
        "query": "Kohli and ABD partnership stats",
        "expected_type": "partnership",
        "category": "advanced",
        "description": "Partnership analysis"
    },
    {
        "id": 30,
        "query": "MS Dhoni entry point analysis when team in trouble",
        "expected_type": "entry_point_analysis",
        "category": "advanced",
        "description": "Complex situational analysis"
    }
]

def print_test_queries():
    """Print all test queries categorized"""
    
    print("🏏 IPL CHATBOT TEST QUERIES")
    print("=" * 60)
    
    categories = {}
    for query in TEST_QUERIES:
        cat = query['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(query)
    
    for category, queries in categories.items():
        print(f"\n📊 {category.upper().replace('_', ' ')}:")
        print("-" * 40)
        for q in queries:
            print(f"{q['id']:2d}. {q['query']}")
            print(f"    Expected: {q['expected_type']}")
            print(f"    Description: {q['description']}")
            print()

if __name__ == "__main__":
    print_test_queries()