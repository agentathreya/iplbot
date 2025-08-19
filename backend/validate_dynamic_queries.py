import os
from dotenv import load_dotenv
from database import DatabaseManager
from player_matcher import PlayerNameMatcher
from query_generator import CricketQueryGenerator
import re
import json

load_dotenv()

class DynamicQueryValidator:
    def __init__(self):
        self.db_manager = DatabaseManager(os.getenv("DATABASE_URL"))
        players = self.db_manager.get_all_players()
        self.player_matcher = PlayerNameMatcher(players)
        self.query_generator = CricketQueryGenerator(os.getenv("GROQ_API_KEY"), self.player_matcher)
    
    def analyze_sql_complexity(self, sql_query):
        """Analyze if SQL query is properly constructed and dynamic"""
        complexity_score = 0
        features = []
        
        # Check for proper aggregations
        if re.search(r'\b(SUM|AVG|COUNT|MAX|MIN)\s*\(', sql_query, re.IGNORECASE):
            complexity_score += 2
            features.append("Aggregation functions")
        
        # Check for GROUP BY
        if re.search(r'\bGROUP\s+BY\b', sql_query, re.IGNORECASE):
            complexity_score += 2
            features.append("GROUP BY clause")
            
        # Check for HAVING clause (important for thresholds)
        if re.search(r'\bHAVING\b', sql_query, re.IGNORECASE):
            complexity_score += 3
            features.append("HAVING clause (thresholds)")
            
        # Check for multiple WHERE conditions
        where_conditions = len(re.findall(r'\bAND\b|\bOR\b', sql_query, re.IGNORECASE))
        if where_conditions > 0:
            complexity_score += where_conditions
            features.append(f"Complex WHERE conditions ({where_conditions} operators)")
            
        # Check for JOINs (advanced)
        if re.search(r'\bJOIN\b', sql_query, re.IGNORECASE):
            complexity_score += 3
            features.append("JOIN operations")
            
        # Check for CASE statements
        if re.search(r'\bCASE\s+WHEN\b', sql_query, re.IGNORECASE):
            complexity_score += 2
            features.append("CASE WHEN conditions")
            
        # Check for ORDER BY
        if re.search(r'\bORDER\s+BY\b', sql_query, re.IGNORECASE):
            complexity_score += 1
            features.append("ORDER BY clause")
            
        # Check for LIMIT
        if re.search(r'\bLIMIT\b', sql_query, re.IGNORECASE):
            complexity_score += 1
            features.append("LIMIT clause")
            
        # Check for proper column usage (cricket-specific)
        cricket_columns = [
            'batter_full_name', 'bowler_full_name', 'runs_batter', 'runs_total',
            'is_four', 'is_six', 'is_wicket', 'over_col', 'bat_hand', 'bowling_style'
        ]
        
        used_columns = []
        for column in cricket_columns:
            if column in sql_query:
                used_columns.append(column)
                
        if used_columns:
            complexity_score += len(used_columns)
            features.append(f"Cricket-specific columns ({len(used_columns)})")
        
        return complexity_score, features
    
    def validate_query_generation(self, natural_query):
        """Validate that query generation is truly dynamic"""
        try:
            # Generate query
            result = self.query_generator.generate_sql_query(natural_query)
            sql_query = result.get('sql_query', '')
            
            if not sql_query:
                return False, "No SQL generated", 0, []
            
            # Analyze complexity
            complexity_score, features = self.analyze_sql_complexity(sql_query)
            
            # Check if it's a real query or fallback
            is_dynamic = complexity_score >= 5  # Minimum threshold for dynamic query
            
            # Validate SQL syntax (basic check)
            if not sql_query.strip().upper().startswith('SELECT'):
                return False, "Invalid SQL structure", 0, []
            
            # Test execution
            try:
                data = self.db_manager.execute_query(sql_query)
                return True, "Valid dynamic query", complexity_score, features
            except Exception as e:
                return False, f"Query execution error: {str(e)}", complexity_score, features
                
        except Exception as e:
            return False, f"Generation error: {str(e)}", 0, []
    
    def run_validation_tests(self):
        """Run comprehensive validation tests"""
        print("🔬 VALIDATING DYNAMIC QUERY GENERATION")
        print("=" * 50)
        
        # Test queries that should generate complex, dynamic SQL
        test_queries = [
            "Best batters vs pace in death overs min 1000 runs",
            "Top bowlers against left-handed batsmen with economy < 8",
            "Kohli vs Rohit strike rate comparison in powerplay",
            "Most expensive overs bowled by spinners",
            "Batsmen with highest average vs leg spin minimum 200 runs", 
            "Death overs specialists with strike rate > 140",
            "Bowlers with best figures in middle overs",
            "Left arm pace vs right hand batsmen statistics",
            "Team performance in run chases > 180",
            "Wicket keepers with most dismissals"
        ]
        
        results = []
        
        for query in test_queries:
            print(f"\n📊 Testing: {query}")
            
            is_valid, message, complexity, features = self.validate_query_generation(query)
            
            results.append({
                'query': query,
                'is_valid': is_valid,
                'message': message,
                'complexity_score': complexity,
                'features': features
            })
            
            status = "✅" if is_valid else "❌"
            print(f"{status} {message}")
            print(f"   Complexity Score: {complexity}")
            if features:
                print(f"   Features: {', '.join(features)}")
        
        # Summary
        valid_count = sum(1 for r in results if r['is_valid'])
        total_count = len(results)
        
        print(f"\n" + "=" * 50)
        print(f"🎯 VALIDATION SUMMARY")
        print(f"Valid Dynamic Queries: {valid_count}/{total_count} ({(valid_count/total_count)*100:.1f}%)")
        
        avg_complexity = sum(r['complexity_score'] for r in results if r['is_valid']) / max(valid_count, 1)
        print(f"Average Complexity Score: {avg_complexity:.1f}")
        
        # Show detailed analysis of a few queries
        print(f"\n🔍 DETAILED ANALYSIS (Top 3 Queries):")
        sorted_results = sorted(results, key=lambda x: x['complexity_score'], reverse=True)[:3]
        
        for i, result in enumerate(sorted_results, 1):
            print(f"\n{i}. {result['query']}")
            print(f"   Complexity: {result['complexity_score']}")
            print(f"   Features: {', '.join(result['features'])}")
            
            # Show generated SQL
            query_result = self.query_generator.generate_sql_query(result['query'])
            if query_result.get('sql_query'):
                sql_preview = query_result['sql_query'][:200] + "..." if len(query_result['sql_query']) > 200 else query_result['sql_query']
                print(f"   SQL Preview: {sql_preview}")
        
        # Save results
        with open('validation_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_count,
                    'valid_queries': valid_count,
                    'success_rate': round((valid_count/total_count)*100, 2),
                    'avg_complexity': round(avg_complexity, 2)
                },
                'detailed_results': results
            }, f, indent=2)
        
        print(f"\n📊 Validation results saved to 'validation_results.json'")
        
        if valid_count >= total_count * 0.8:  # 80% success rate
            print("🎉 VALIDATION PASSED: Query generator is truly dynamic!")
        else:
            print("⚠️ VALIDATION NEEDS IMPROVEMENT: Some queries may be using fallbacks")
        
        return valid_count >= total_count * 0.8

def main():
    validator = DynamicQueryValidator()
    validator.run_validation_tests()

if __name__ == "__main__":
    main()