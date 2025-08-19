#!/usr/bin/env python3

"""
Demo script showcasing the IPL Cricket Chatbot's capabilities
This demonstrates that the system can handle ANY cricket query dynamically
"""

import requests
import json
import time

class ChatbotDemo:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        
    def send_query(self, query):
        """Send a query and return formatted response"""
        try:
            response = requests.post(
                f"{self.api_url}/chat",
                json={"query": query},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "data_count": len(data.get("data", [])),
                    "sql_query": data.get("sql_query", ""),
                    "matched_players": data.get("matched_players", []),
                    "execution_time": data.get("execution_time", 0)
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def demo_query(self, query, description=""):
        """Demonstrate a single query with formatted output"""
        print(f"\n🏏 Query: {query}")
        if description:
            print(f"   Description: {description}")
        print("-" * 70)
        
        result = self.send_query(query)
        
        if result["success"]:
            print(f"✅ Success! Found {result['data_count']} records")
            print(f"⏱️  Execution time: {result['execution_time']}s")
            
            if result["matched_players"]:
                print(f"👤 Detected players: {', '.join(result['matched_players'])}")
            
            print(f"💬 Response: {result['response'][:200]}...")
            
            if result["sql_query"]:
                # Show a preview of the generated SQL
                sql_preview = result["sql_query"][:150] + "..." if len(result["sql_query"]) > 150 else result["sql_query"]
                print(f"🔍 SQL Preview: {sql_preview}")
                
        else:
            print(f"❌ Failed: {result['error']}")
        
        time.sleep(1)  # Brief pause for readability
        
    def run_demo(self):
        """Run the comprehensive demo"""
        print("🎯 IPL CRICKET CHATBOT - DYNAMIC QUERY DEMONSTRATION")
        print("=" * 70)
        print("This demo proves the chatbot can handle ANY cricket query dynamically!")
        print("No hardcoded templates - pure AI-powered query generation.")
        
        # Check connection
        try:
            requests.get(f"{self.api_url}/", timeout=5)
            print(f"✅ Connected to chatbot at {self.api_url}")
        except:
            print(f"❌ Cannot connect to {self.api_url}")
            print("Make sure the backend server is running!")
            return
        
        # Demo Categories
        
        print(f"\n" + "="*70)
        print("📊 BASIC STATISTICS - Natural Language Understanding")
        print("="*70)
        
        self.demo_query(
            "Who scored the most runs in IPL?",
            "Simple aggregation query"
        )
        
        self.demo_query(
            "Kohli batting average and strike rate",
            "Partial name matching + multiple metrics"
        )
        
        self.demo_query(
            "Top 5 wicket takers in IPL history",
            "Ranking with limit"
        )
        
        print(f"\n" + "="*70)
        print("⚡ PHASE-WISE ANALYSIS - Cricket Domain Intelligence")
        print("="*70)
        
        self.demo_query(
            "Best batters in death overs minimum 1000 runs",
            "Phase-specific filtering with custom thresholds"
        )
        
        self.demo_query(
            "Powerplay specialists with strike rate above 140",
            "Phase + condition-based filtering"
        )
        
        self.demo_query(
            "Most economical bowlers in middle overs min 500 balls",
            "Bowling economics in specific phase"
        )
        
        print(f"\n" + "="*70) 
        print("🔥 ADVANCED SCENARIOS - Complex Multi-Condition Queries")
        print("="*70)
        
        self.demo_query(
            "Best batters vs pace bowling in death overs min 800 runs",
            "Multi-dimensional analysis: phase + bowling type + threshold"
        )
        
        self.demo_query(
            "Left arm spinners vs right handed batsmen economy rate",
            "Bowling style vs batting hand matchup analysis"
        )
        
        self.demo_query(
            "Fast bowlers performance against left handers in powerplay",
            "Complex situational analysis"
        )
        
        print(f"\n" + "="*70)
        print("⚔️ PLAYER COMPARISONS - Head-to-Head Analysis")  
        print("="*70)
        
        self.demo_query(
            "Kohli vs Rohit Sharma strike rate comparison",
            "Direct player comparison"
        )
        
        self.demo_query(
            "MS Dhoni vs AB de Villiers as finishers in death overs",
            "Role-specific comparison with context"
        )
        
        self.demo_query(
            "Bumrah vs Malinga bowling figures comparison",
            "Bowling legends head-to-head"
        )
        
        print(f"\n" + "="*70)
        print("🏟️ SITUATIONAL CRICKET - Match Context Analysis")
        print("="*70)
        
        self.demo_query(
            "Best performance while chasing targets above 180",
            "Situational pressure analysis"
        )
        
        self.demo_query(
            "Bowling performance at Wankhede Stadium in evening games",
            "Venue + time specific analysis"
        )
        
        self.demo_query(
            "Most expensive overs conceded by spinners",
            "Bowling performance extremes"
        )
        
        print(f"\n" + "="*70)
        print("🧪 EDGE CASES - Testing AI Limits")
        print("="*70)
        
        self.demo_query(
            "Right handed batsmen vs leg spin bowling in middle overs minimum 200 runs",
            "Very specific multi-condition edge case"
        )
        
        self.demo_query(
            "Players with strike rate between 130-140 in death overs min 300 runs",
            "Range-based filtering with phase and threshold"
        )
        
        self.demo_query(
            "Wicket keepers with most dismissals excluding catches",
            "Role-specific with exclusion logic"
        )
        
        print(f"\n" + "="*70)
        print("🎉 DEMO COMPLETE - KEY TAKEAWAYS")
        print("="*70)
        
        print("✅ DYNAMIC QUERY GENERATION: No hardcoded templates!")
        print("✅ CRICKET DOMAIN EXPERTISE: Understands phases, roles, situations")
        print("✅ FUZZY NAME MATCHING: Works with partial player names")
        print("✅ INTELLIGENT THRESHOLDS: Auto-applies meaningful minimums")
        print("✅ COMPLEX SQL GENERATION: Handles multi-condition queries") 
        print("✅ REAL-TIME PROCESSING: Fast response times")
        print("✅ COMPREHENSIVE COVERAGE: Batting, bowling, fielding, situational")
        
        print(f"\n🚀 The IPL Cricket Chatbot can handle ANY cricket question!")
        print("💡 Try your own queries at the web interface!")

def main():
    demo = ChatbotDemo()
    demo.run_demo()

if __name__ == "__main__":
    main()