#!/usr/bin/env python3

import requests
import json
import time
import sys
from typing import List, Dict, Any

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def test_connection(self) -> bool:
        """Test if API is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.status_code == 200
        except:
            return False
    
    def send_chat_query(self, query: str) -> Dict[str, Any]:
        """Send a query to the chat endpoint"""
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/chat",
                json={"query": query},
                timeout=30
            )
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "execution_time": execution_time,
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "execution_time": execution_time,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "status_code": 0
            }
    
    def test_query_batch(self, queries: List[str], category: str):
        """Test a batch of queries"""
        print(f"\n🧪 Testing {category} ({len(queries)} queries)")
        print("-" * 50)
        
        batch_results = []
        successful = 0
        
        for i, query in enumerate(queries, 1):
            result = self.send_chat_query(query)
            
            if result["success"]:
                data_count = len(result["data"].get("data", []))
                successful += 1
                status = f"✅ [{data_count} records] ({result['execution_time']:.2f}s)"
            else:
                status = f"❌ {result['error']} ({result['execution_time']:.2f}s)"
            
            print(f"{i:2d}. {query[:60]:<60} {status}")
            
            batch_result = {
                "category": category,
                "query": query,
                "success": result["success"],
                "data_count": len(result["data"].get("data", [])) if result["success"] else 0,
                "execution_time": result["execution_time"],
                "error": result.get("error"),
                "sql_query": result["data"].get("sql_query") if result["success"] else None
            }
            
            batch_results.append(batch_result)
            self.results.append(batch_result)
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
        
        success_rate = (successful / len(queries)) * 100
        print(f"Category Success Rate: {successful}/{len(queries)} ({success_rate:.1f}%)")
        
        return batch_results
    
    def run_comprehensive_api_tests(self):
        """Run comprehensive API tests"""
        print("🏏 IPL CRICKET CHATBOT - COMPREHENSIVE API TESTING")
        print("=" * 60)
        
        # Check connection first
        if not self.test_connection():
            print("❌ Cannot connect to API at", self.base_url)
            print("Make sure the backend server is running!")
            return False
        
        print(f"✅ Connected to API at {self.base_url}")
        
        # Test categories with diverse queries
        
        # 1. Basic Player Stats
        basic_queries = [
            "Virat Kohli batting average",
            "Rohit Sharma total runs",
            "MS Dhoni strike rate",
            "Jasprit Bumrah wickets",
            "AB de Villiers boundaries",
            "David Warner career stats",
            "Chris Gayle sixes count"
        ]
        self.test_query_batch(basic_queries, "Basic Player Stats")
        
        # 2. Phase-wise Analysis
        phase_queries = [
            "Best batters in powerplay overs min 500 runs",
            "Death overs specialists with strike rate > 140",
            "Middle overs bowling economy leaders", 
            "Most runs in overs 16-20 minimum 800 runs",
            "Powerplay wicket takers top 10",
            "Best average in death overs min 300 runs"
        ]
        self.test_query_batch(phase_queries, "Phase-wise Analysis")
        
        # 3. Advanced Scenarios
        advanced_queries = [
            "Best batters vs pace bowling in death overs min 1000 runs",
            "Top bowlers against left-handed batsmen economy < 8",
            "Right hand batsmen vs spin bowling strike rate",
            "Left arm pace bowlers vs right hand batsmen",
            "Fast bowlers in powerplay minimum 200 balls",
            "Leg spinners vs left hand batsmen wickets"
        ]
        self.test_query_batch(advanced_queries, "Advanced Scenarios")
        
        # 4. Player Comparisons  
        comparison_queries = [
            "Kohli vs Rohit Sharma batting comparison",
            "Bumrah vs Malinga bowling stats",
            "MS Dhoni vs AB de Villiers as finishers",
            "Warner vs Gayle strike rate comparison",
            "Ashwin vs Harbhajan bowling economy"
        ]
        self.test_query_batch(comparison_queries, "Player Comparisons")
        
        # 5. Team & Venue Analysis
        team_venue_queries = [
            "Mumbai Indians batting performance",
            "Best bowling at Wankhede Stadium", 
            "Chennai Super Kings vs Royal Challengers",
            "Highest scores at Eden Gardens",
            "Team wise powerplay statistics"
        ]
        self.test_query_batch(team_venue_queries, "Team & Venue Analysis")
        
        # 6. Records & Milestones
        records_queries = [
            "Highest individual score in IPL",
            "Best bowling figures in a match",
            "Most expensive over in history",
            "Fastest fifty scored",
            "Most boundaries in an innings",
            "Best partnership records"
        ]
        self.test_query_batch(records_queries, "Records & Milestones")
        
        # 7. Situational Analysis
        situational_queries = [
            "Best performance while chasing targets > 180",
            "Defending team bowling when target < 150",
            "Performance in second innings vs first",
            "Super over specialists",
            "Toss winners batting first advantage"
        ]
        self.test_query_batch(situational_queries, "Situational Analysis")
        
        # 8. Fielding & Dismissals
        fielding_queries = [
            "Most catches by fielders",
            "Wicket keeper dismissals leaders",
            "Run out statistics by teams",
            "Most stumpings in IPL",
            "Direct hit run outs count"
        ]
        self.test_query_batch(fielding_queries, "Fielding & Dismissals")
        
        # 9. Edge Cases & Complex
        edge_cases = [
            "Players with exactly 50 sixes",
            "Bowlers with economy between 6.5 and 7.5",
            "Left arm spinners against left handers minimum 100 balls",
            "Night games vs day games batting average",
            "Player of match awards distribution"
        ]
        self.test_query_batch(edge_cases, "Edge Cases & Complex")
        
        # 10. Partial Name Matching
        partial_names = [
            "Kohli performance in finals",
            "Dhoni finishing ability stats",
            "Bumrah death bowling",
            "Gayle power hitting",
            "AB de Villiers 360 degree shots",
            "Warner opening partnership",
            "Malinga toe crushers"
        ]
        self.test_query_batch(partial_names, "Partial Name Matching")
        
        self.print_final_summary()
        
    def print_final_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests
        
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE API TEST RESULTS")
        print("=" * 60)
        
        print(f"Total Tests Executed: {total_tests}")
        print(f"Successful Queries: {successful_tests} ({(successful_tests/total_tests)*100:.1f}%)")
        print(f"Failed Queries: {failed_tests} ({(failed_tests/total_tests)*100:.1f}%)")
        
        if successful_tests > 0:
            avg_time = sum(r["execution_time"] for r in self.results if r["success"]) / successful_tests
            total_records = sum(r["data_count"] for r in self.results if r["success"])
            print(f"Average Response Time: {avg_time:.2f} seconds")
            print(f"Total Records Retrieved: {total_records:,}")
        
        # Category-wise breakdown
        print(f"\n📊 CATEGORY-WISE BREAKDOWN:")
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "success": 0}
            categories[cat]["total"] += 1
            if result["success"]:
                categories[cat]["success"] += 1
        
        for category, stats in categories.items():
            success_rate = (stats["success"] / stats["total"]) * 100
            print(f"  {category}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Show failed queries if any
        failed_queries = [r for r in self.results if not r["success"]]
        if failed_queries:
            print(f"\n❌ FAILED QUERIES ({len(failed_queries)}):")
            for i, failure in enumerate(failed_queries[:5], 1):  # Show first 5
                print(f"{i}. {failure['query']}")
                print(f"   Error: {failure['error']}")
            
            if len(failed_queries) > 5:
                print(f"   ... and {len(failed_queries) - 5} more failed queries")
        
        # Save detailed results
        timestamp = int(time.time())
        filename = f"api_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "failed_tests": failed_tests,
                    "success_rate": round((successful_tests/total_tests)*100, 2),
                    "timestamp": timestamp
                },
                "category_breakdown": categories,
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {filename}")
        
        # Final verdict
        if successful_tests >= total_tests * 0.85:  # 85% success rate
            print("🎉 TEST SUITE PASSED: Chatbot handles diverse queries successfully!")
            print("✅ The system is ready for production use!")
        elif successful_tests >= total_tests * 0.70:  # 70% success rate  
            print("⚠️ TEST SUITE PARTIALLY PASSED: Most queries work, some improvements needed")
        else:
            print("❌ TEST SUITE FAILED: Significant issues need to be addressed")
        
        return successful_tests >= total_tests * 0.85

def main():
    """Main function to run API tests"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"Testing API at: {base_url}")
    print("Make sure your backend server is running!")
    print()
    
    tester = APITester(base_url)
    success = tester.run_comprehensive_api_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()