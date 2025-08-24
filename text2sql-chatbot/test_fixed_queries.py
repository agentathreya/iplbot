#!/usr/bin/env python3
"""
Test the Fixed Chatbot with All 30 Queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_ipl_chatbot import FixedIPLAnalyzer, FixedQueryGenerator, get_database_connection, execute_query
from test_queries import TEST_QUERIES
import pandas as pd
import time

def test_all_queries():
    """Test all 30 queries with the fixed chatbot"""
    
    print("🏏 TESTING FIXED IPL CHATBOT - ALL 30 QUERIES")
    print("=" * 70)
    
    # Get database connection
    engine, _ = get_database_connection()
    if not engine:
        print("❌ Failed to connect to database")
        return
    
    # Initialize fixed analyzer
    analyzer = FixedIPLAnalyzer(engine)
    query_generator = FixedQueryGenerator(analyzer)
    
    print(f"✅ Connected to database")
    print(f"✅ Loaded {len(analyzer.all_players)} players, {len(analyzer.all_teams)} teams")
    print()
    
    # Test results storage
    results = []
    successful_queries = 0
    failed_queries = 0
    
    print("🧪 RUNNING ALL 30 TESTS...")
    print("=" * 70)
    
    for i, test_query in enumerate(TEST_QUERIES, 1):
        query_text = test_query['query']
        expected_type = test_query['expected_type']
        category = test_query['category']
        
        print(f"\n🔍 Test {i:2d}/30: {query_text}")
        print(f"    Category: {category} | Expected: {expected_type}")
        
        try:
            # Start timing
            start_time = time.time()
            
            # Step 1: Analyze query
            analysis = analyzer.analyze_complex_query(query_text)
            detected_type = analysis['query_type']
            
            # Step 2: Generate SQL
            sql_query = query_generator.generate_sql(analysis)
            
            # Step 3: Execute query
            result = execute_query(engine, sql_query)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Check results
            is_success = isinstance(result, pd.DataFrame)
            row_count = len(result) if is_success else 0
            
            # Determine if query type is correct
            type_correct = detected_type == expected_type
            
            # For basic_stats, allow statistical_analysis as correct too
            if expected_type == 'basic_stats' and detected_type == 'statistical_analysis':
                type_correct = True
            
            # Status
            if is_success and row_count > 0 and type_correct:
                status = "✅ SUCCESS"
                successful_queries += 1
            elif is_success and row_count > 0:
                status = "⚠️  PARTIAL" 
                successful_queries += 0.5
            else:
                status = "❌ FAILED"
                failed_queries += 1
            
            print(f"    Analysis: {detected_type} ({'✅' if type_correct else '❌'})")
            print(f"    Players: {analysis['entities']['players']}")
            print(f"    Teams: {analysis['entities']['teams']}")
            print(f"    Filters: {analysis['filters']}")
            print(f"    Execution: {execution_time:.2f}s | Rows: {row_count} | {status}")
            
            # Store results
            results.append({
                'test_id': i,
                'query': query_text,
                'category': category,
                'expected_type': expected_type,
                'detected_type': detected_type,
                'type_correct': type_correct,
                'success': is_success,
                'row_count': row_count,
                'execution_time': execution_time,
                'players_found': len(analysis['entities']['players']),
                'teams_found': len(analysis['entities']['teams']),
                'status': status.split()[1]  # Just the word part
            })
            
        except Exception as e:
            print(f"    ❌ ERROR: {str(e)}")
            failed_queries += 1
            results.append({
                'test_id': i,
                'query': query_text,
                'category': category,
                'expected_type': expected_type,
                'detected_type': 'ERROR',
                'type_correct': False,
                'success': False,
                'row_count': 0,
                'execution_time': 0,
                'players_found': 0,
                'teams_found': 0,
                'status': 'ERROR'
            })
    
    # Summary Report
    print("\n" + "=" * 70)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 70)
    
    total_tests = len(TEST_QUERIES)
    success_rate = (successful_queries / total_tests) * 100
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_queries:.0f}")
    print(f"Failed: {failed_queries}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Category breakdown
    print(f"\n📋 RESULTS BY CATEGORY:")
    print("-" * 40)
    
    categories = {}
    for result in results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'success': 0}
        categories[cat]['total'] += 1
        if result['status'] == 'SUCCESS':
            categories[cat]['success'] += 1
    
    for category, stats in categories.items():
        success_rate = (stats['success'] / stats['total']) * 100
        print(f"{category:20s}: {stats['success']}/{stats['total']} ({success_rate:.0f}%)")
    
    # Query type accuracy
    print(f"\n🎯 QUERY TYPE DETECTION ACCURACY:")
    print("-" * 40)
    
    type_correct_count = sum(1 for r in results if r['type_correct'])
    type_accuracy = (type_correct_count / total_tests) * 100
    print(f"Correct Type Detection: {type_correct_count}/{total_tests} ({type_accuracy:.1f}%)")
    
    # Performance stats
    print(f"\n⚡ PERFORMANCE METRICS:")
    print("-" * 40)
    
    successful_results = [r for r in results if r['success']]
    if successful_results:
        avg_time = sum(r['execution_time'] for r in successful_results) / len(successful_results)
        avg_rows = sum(r['row_count'] for r in successful_results) / len(successful_results)
        print(f"Average Execution Time: {avg_time:.2f}s")
        print(f"Average Result Rows: {avg_rows:.0f}")
    
    # Problem queries
    print(f"\n🚨 FAILED/PROBLEMATIC QUERIES:")
    print("-" * 40)
    
    problem_queries = [r for r in results if r['status'] != 'SUCCESS']
    if problem_queries:
        for result in problem_queries:
            print(f"{result['test_id']:2d}. {result['query'][:50]}...")
            print(f"    Expected: {result['expected_type']} | Got: {result['detected_type']}")
            print(f"    Status: {result['status']}")
            print()
    else:
        print("🎉 No failed queries! All tests passed!")
    
    # Examples of working queries
    print(f"\n✅ EXAMPLES OF WORKING QUERIES:")
    print("-" * 40)
    
    working_queries = [r for r in results if r['status'] == 'SUCCESS'][:5]
    for result in working_queries:
        print(f"✅ {result['query']}")
        print(f"   Type: {result['detected_type']} | Rows: {result['row_count']} | Time: {result['execution_time']:.2f}s")
    
    return results, success_rate

if __name__ == "__main__":
    results, success_rate = test_all_queries()
    
    print(f"\n🏆 CHATBOT TESTING COMPLETE!")
    print(f"Final Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 EXCELLENT! Chatbot is working very well!")
    elif success_rate >= 60:
        print("👍 GOOD! Most queries are working correctly!")
    else:
        print("⚠️  NEEDS IMPROVEMENT! Several queries need fixing!")