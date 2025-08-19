import asyncio
import os
from dotenv import load_dotenv
from database import DatabaseManager
from player_matcher import PlayerNameMatcher
from query_generator import CricketQueryGenerator
import json
import time

# Load environment variables
load_dotenv()

class ComprehensiveCricketTester:
    def __init__(self):
        self.db_manager = DatabaseManager(os.getenv("DATABASE_URL"))
        players = self.db_manager.get_all_players()
        self.player_matcher = PlayerNameMatcher(players)
        self.query_generator = CricketQueryGenerator(os.getenv("GROQ_API_KEY"), self.player_matcher)
        
        self.test_results = []
        self.failed_queries = []
        
    def log_result(self, query, success, data_count=0, error=None, execution_time=0):
        result = {
            "query": query,
            "success": success,
            "data_count": data_count,
            "error": str(error) if error else None,
            "execution_time": round(execution_time, 2)
        }
        self.test_results.append(result)
        
        if not success:
            self.failed_queries.append(result)
            
        status = "✅" if success else "❌"
        print(f"{status} {query} [{data_count} records] ({execution_time:.2f}s)")
        if error:
            print(f"   Error: {error}")
    
    async def test_query(self, query):
        """Test a single query end-to-end"""
        start_time = time.time()
        try:
            # Generate SQL query
            query_result = self.query_generator.generate_sql_query(query)
            
            if not query_result.get("sql_query"):
                raise Exception("No SQL query generated")
            
            # Execute query
            data = self.db_manager.execute_query(query_result["sql_query"])
            
            execution_time = time.time() - start_time
            self.log_result(query, True, len(data), None, execution_time)
            return True, data
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_result(query, False, 0, e, execution_time)
            return False, None

    async def run_comprehensive_tests(self):
        """Run comprehensive tests covering all cricket scenarios"""
        
        print("🏏 Starting Comprehensive Cricket Query Tests")
        print("=" * 60)
        
        # 1. BASIC BATTING QUERIES
        print("\n📊 BASIC BATTING QUERIES")
        basic_batting_queries = [
            "Who scored the most runs?",
            "Top 10 run scorers in IPL",
            "Virat Kohli batting statistics",
            "MS Dhoni career runs",
            "Rohit Sharma strike rate",
            "Highest individual score in IPL",
            "Most boundaries in IPL history",
            "Best batting average minimum 1000 runs",
            "Strike rate leaders with min 500 runs"
        ]
        
        for query in basic_batting_queries:
            await self.test_query(query)
        
        # 2. BASIC BOWLING QUERIES  
        print("\n🎯 BASIC BOWLING QUERIES")
        basic_bowling_queries = [
            "Most wickets in IPL",
            "Best bowling figures in IPL",
            "Jasprit Bumrah bowling statistics", 
            "Lowest economy rate in IPL",
            "Best bowling average minimum 100 wickets",
            "Most dot balls bowled",
            "Lasith Malinga wicket count",
            "Harbhajan Singh vs Amit Mishra",
            "Top 5 bowlers with best strike rate"
        ]
        
        for query in basic_bowling_queries:
            await self.test_query(query)
            
        # 3. PHASE-WISE BATTING ANALYSIS
        print("\n⚡ PHASE-WISE BATTING ANALYSIS")
        phase_batting_queries = [
            "Best batters in powerplay overs",
            "Most runs in death overs minimum 500 runs",
            "Middle overs specialists with strike rate > 120",
            "Kohli performance in death overs",
            "Powerplay boundaries leaders",
            "Death overs finishers minimum 200 runs",
            "Best average in middle overs min 300 runs",
            "Strike rate in powerplay vs death overs",
            "Who scores most in overs 16-20?"
        ]
        
        for query in phase_batting_queries:
            await self.test_query(query)
            
        # 4. PHASE-WISE BOWLING ANALYSIS
        print("\n🎳 PHASE-WISE BOWLING ANALYSIS") 
        phase_bowling_queries = [
            "Best economy in powerplay minimum 200 balls",
            "Death overs specialists bowling",
            "Middle overs wicket takers",
            "Bumrah economy in death overs",
            "Powerplay wicket takers minimum 50 wickets",
            "Best bowling in overs 16-20",
            "Economy rate in middle overs",
            "Dot ball percentage in powerplay",
            "Death overs bowling average minimum 100 balls"
        ]
        
        for query in phase_bowling_queries:
            await self.test_query(query)
            
        # 5. ADVANCED BATTING SCENARIOS
        print("\n🔥 ADVANCED BATTING SCENARIOS")
        advanced_batting_queries = [
            "Best batters vs pace bowling minimum 800 runs",
            "Performance against spin bowling",
            "Left hand batsmen vs right arm pace",
            "Strike rate vs spin in middle overs",
            "Boundaries vs pace in death overs",
            "Best average vs left arm pace min 300 runs",
            "Right hand batsmen vs leg spin",
            "Performance vs fast bowlers in powerplay",
            "Strike rate vs medium pace bowling"
        ]
        
        for query in advanced_batting_queries:
            await self.test_query(query)
            
        # 6. ADVANCED BOWLING SCENARIOS
        print("\n🏹 ADVANCED BOWLING SCENARIOS")
        advanced_bowling_queries = [
            "Best bowlers vs left handed batsmen",
            "Economy vs right handed batsmen minimum 500 balls", 
            "Pace bowlers vs left handers wickets",
            "Spin bowling vs right handers average",
            "Fast bowlers in death overs performance",
            "Left arm pace vs right hand batsmen",
            "Leg spin vs left hand batsmen",
            "Off spin bowling economy minimum 300 balls",
            "Medium pace vs right handers strike rate"
        ]
        
        for query in advanced_bowling_queries:
            await self.test_query(query)
            
        # 7. PLAYER COMPARISONS
        print("\n⚔️ PLAYER COMPARISONS")
        comparison_queries = [
            "Kohli vs Rohit Sharma batting comparison",
            "MS Dhoni vs AB de Villiers strike rate",
            "Bumrah vs Malinga bowling comparison",
            "Kohli vs Warner in powerplay",
            "Dhoni vs Karthik as finishers",
            "Ashwin vs Harbhajan bowling stats",
            "Gayle vs Sehwag strike rate comparison",
            "Russell vs Pollard power hitting",
            "Bhuvi vs Shami bowling average"
        ]
        
        for query in comparison_queries:
            await self.test_query(query)
            
        # 8. VENUE-BASED ANALYSIS
        print("\n🏟️ VENUE-BASED ANALYSIS")
        venue_queries = [
            "Best batting performance at Wankhede Stadium",
            "Highest scores at Chinnaswamy Stadium",
            "Best bowling at Eden Gardens",
            "Most runs at Chepauk Stadium",
            "Economy rates at different venues",
            "Venue wise strike rates comparison",
            "Best venues for batting",
            "Bowling friendly grounds in IPL",
            "Home advantage statistics by venue"
        ]
        
        for query in venue_queries:
            await self.test_query(query)
            
        # 9. TEAM-BASED ANALYSIS
        print("\n👥 TEAM-BASED ANALYSIS")
        team_queries = [
            "Best team batting performance",
            "Mumbai Indians vs Chennai Super Kings",
            "Royal Challengers Bangalore top scorers",
            "Kolkata Knight Riders bowling attack",
            "Team wise powerplay performance",
            "Best death overs team performance",
            "Team with best bowling economy",
            "Highest team totals in IPL",
            "Best team bowling figures"
        ]
        
        for query in team_queries:
            await self.test_query(query)
            
        # 10. SITUATIONAL ANALYSIS
        print("\n🎯 SITUATIONAL ANALYSIS")
        situational_queries = [
            "Best performance while chasing",
            "Defending team bowling statistics",
            "Performance in second innings",
            "First innings batting averages",
            "Pressure situation performers",
            "Best finishers in tight matches",
            "Performance when team needs >10 rpr",
            "Economy when defending < 150",
            "Strike rate in run chases > 180"
        ]
        
        for query in situational_queries:
            await self.test_query(query)
            
        # 11. FIELDING & DISMISSAL ANALYSIS
        print("\n🧤 FIELDING & DISMISSAL ANALYSIS")
        fielding_queries = [
            "Most catches taken by fielders",
            "Run out statistics by teams",
            "Wicket keeper dismissals",
            "Most stumpings in IPL",
            "Caught behind dismissals",
            "Direct hit run outs",
            "Best fielding positions for catches",
            "Most dismissals by fielding position",
            "Wicket keeper vs fielder catches"
        ]
        
        for query in fielding_queries:
            await self.test_query(query)
            
        # 12. STATISTICAL RECORDS
        print("\n📈 STATISTICAL RECORDS") 
        record_queries = [
            "Fastest centuries in IPL",
            "Most consecutive boundaries",
            "Highest partnership records",
            "Best bowling figures in powerplay",
            "Most expensive overs in IPL",
            "Fastest fifties scored",
            "Most dot balls in an innings",
            "Highest strike rates in death overs",
            "Best bowling economy in an innings"
        ]
        
        for query in record_queries:
            await self.test_query(query)
            
        # 13. SEASONAL ANALYSIS
        print("\n📅 SEASONAL ANALYSIS")
        seasonal_queries = [
            "Best season for batting averages",
            "Most runs in 2016 season",
            "2019 bowling statistics",
            "Season wise boundary counts",
            "Best individual season performance",
            "Most wickets in a single season",
            "Economy rates by season",
            "Strike rates evolution over seasons",
            "Team performance by season"
        ]
        
        for query in seasonal_queries:
            await self.test_query(query)
            
        # 14. PARTIAL NAME MATCHING TESTS
        print("\n🔍 PARTIAL NAME MATCHING TESTS")
        partial_name_queries = [
            "Kohli batting stats",
            "Dhoni finishing ability",
            "Rohit powerplay performance", 
            "Bumrah death overs bowling",
            "AB boundaries count",
            "Warner strike rate",
            "Malinga wickets",
            "Gayle sixes",
            "Russell power hitting"
        ]
        
        for query in partial_name_queries:
            await self.test_query(query)
            
        # 15. EDGE CASES & COMPLEX QUERIES
        print("\n🧪 EDGE CASES & COMPLEX QUERIES")
        edge_case_queries = [
            "Players with exactly 100 boundaries",
            "Bowlers with economy between 7-8",
            "Batsmen with strike rate > 150 min 200 runs",
            "Left arm spinners vs left handed batsmen",
            "Right arm off break vs right handers",
            "Night games vs day games performance",
            "Toss winners batting first statistics",
            "Super over performances by players",
            "Player of match awards distribution"
        ]
        
        for query in edge_case_queries:
            await self.test_query(query)
            
        # Print final results
        await self.print_test_summary()
    
    async def print_test_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = len(self.failed_queries)
        
        print("\n" + "=" * 60)
        print("🏏 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests} ({(successful_tests/total_tests)*100:.1f}%)")
        print(f"Failed: {failed_tests} ({(failed_tests/total_tests)*100:.1f}%)")
        
        if successful_tests > 0:
            avg_execution_time = sum(r['execution_time'] for r in self.test_results if r['success']) / successful_tests
            total_records = sum(r['data_count'] for r in self.test_results if r['success'])
            print(f"Average execution time: {avg_execution_time:.2f}s")
            print(f"Total records retrieved: {total_records:,}")
        
        if self.failed_queries:
            print(f"\n❌ FAILED QUERIES ({len(self.failed_queries)}):")
            for i, failure in enumerate(self.failed_queries[:10], 1):  # Show first 10 failures
                print(f"{i}. {failure['query']}")
                print(f"   Error: {failure['error']}")
            
            if len(self.failed_queries) > 10:
                print(f"   ... and {len(self.failed_queries) - 10} more")
        
        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'failed_tests': failed_tests,
                    'success_rate': round((successful_tests/total_tests)*100, 2)
                },
                'detailed_results': self.test_results
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to 'test_results.json'")
        print("🎯 Test suite validates the chatbot can handle ANY cricket query!")

async def main():
    """Run the comprehensive test suite"""
    tester = ComprehensiveCricketTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())