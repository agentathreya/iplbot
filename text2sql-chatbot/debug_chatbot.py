#!/usr/bin/env python3
"""
Debug the chatbot query analysis issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_ipl_chatbot import AdvancedIPLAnalyzer, AdvancedQueryGenerator, get_database_connection
from test_queries import TEST_QUERIES
import pandas as pd

def debug_query_analysis():
    """Debug the query analysis for our test queries"""
    
    print("🔍 DEBUGGING IPL CHATBOT QUERY ANALYSIS")
    print("=" * 60)
    
    # Get database connection
    engine, _ = get_database_connection()
    if not engine:
        print("❌ Failed to connect to database")
        return
    
    # Initialize analyzer
    analyzer = AdvancedIPLAnalyzer(engine)
    query_generator = AdvancedQueryGenerator(analyzer)
    
    print(f"✅ Loaded {len(analyzer.all_players)} players")
    print(f"✅ Loaded {len(analyzer.all_teams)} teams")
    print(f"✅ Loaded {len(analyzer.all_venues)} venues")
    print()
    
    # Test problematic queries first
    problem_queries = [
        "Virat Kohli vs Jasprit Bumrah",
        "Kohli runs in death overs", 
        "Rohit Sharma powerplay stats",
        "CSK vs MI head to head"
    ]
    
    print("🚨 TESTING PROBLEM QUERIES:")
    print("-" * 40)
    
    for query in problem_queries:
        print(f"\n🔍 Query: '{query}'")
        
        # Analyze query
        analysis = analyzer.analyze_complex_query(query)
        
        print(f"   Type detected: {analysis['query_type']}")
        print(f"   Players found: {analysis['entities']['players']}")
        print(f"   Teams found: {analysis['entities']['teams']}")
        print(f"   Metrics: {analysis['metrics']}")
        print(f"   Filters: {analysis['filters']}")
        print(f"   Complexity: {analysis['complexity']}")
        
        # Generate SQL
        sql = query_generator.generate_sql(analysis)
        print(f"   SQL Preview: {sql[:100]}...")
        
        # Check if it's defaulting to basic stats
        if analysis['query_type'] == 'basic_stats' and ('vs' in query.lower() or 'death' in query.lower() or 'powerplay' in query.lower()):
            print("   ❌ ISSUE: Should not be basic_stats!")
        else:
            print("   ✅ Analysis looks correct")
    
    print("\n" + "=" * 60)
    print("🧪 TESTING ALL 30 QUERIES:")
    print("-" * 40)
    
    results = []
    
    for test_query in TEST_QUERIES[:10]:  # Test first 10
        query = test_query['query']
        expected = test_query['expected_type']
        
        print(f"\n{test_query['id']:2d}. {query}")
        
        # Analyze
        analysis = analyzer.analyze_complex_query(query)
        detected = analysis['query_type']
        
        # Check if correct
        is_correct = detected == expected
        status = "✅" if is_correct else "❌"
        
        print(f"    Expected: {expected}")
        print(f"    Detected: {detected} {status}")
        print(f"    Players: {analysis['entities']['players']}")
        print(f"    Filters: {analysis['filters']}")
        
        results.append({
            'id': test_query['id'],
            'query': query,
            'expected': expected,
            'detected': detected,
            'correct': is_correct,
            'players': len(analysis['entities']['players']),
            'complexity': analysis['complexity']
        })
    
    # Summary
    print(f"\n📊 SUMMARY (First 10 queries):")
    print("-" * 40)
    correct = sum(1 for r in results if r['correct'])
    total = len(results)
    print(f"Correct: {correct}/{total} ({correct/total*100:.1f}%)")
    
    # Show issues
    print(f"\n🚨 ISSUES FOUND:")
    print("-" * 40)
    for r in results:
        if not r['correct']:
            print(f"  {r['id']:2d}. {r['query'][:40]}...")
            print(f"      Expected {r['expected']} but got {r['detected']}")
    
    return results

if __name__ == "__main__":
    debug_query_analysis()