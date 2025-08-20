import streamlit as st
import psycopg2
import pandas as pd
import os
from datetime import datetime
import time
import logging
from typing import List, Dict, Any, Optional
from fuzzywuzzy import fuzz, process
from groq import Groq
import re
from decimal import Decimal
from contextlib import contextmanager

# Set page config
st.set_page_config(
    page_title="IPL Cricket Chatbot 🏏",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.stApp > header {
    background-color: transparent;
}

.main-header {
    text-align: center;
    color: #2E8B57;
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: 1rem;
}

.chat-message-user {
    background: linear-gradient(90deg, #4CAF50, #45a049);
    color: white;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 15px 15px 5px 15px;
    margin-left: 20%;
    text-align: right;
}

.chat-message-bot {
    background: linear-gradient(90deg, #2196F3, #1976D2);
    color: white;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 15px 15px 15px 5px;
    margin-right: 20%;
}

.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    text-align: center;
    margin: 0.5rem 0;
}

.example-button {
    background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
    color: white;
    border: none;
    padding: 0.8rem;
    border-radius: 10px;
    font-weight: bold;
    transition: transform 0.2s;
}

.example-button:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# Database connection class
class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
        except Exception as e:
            st.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    result = []
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        # Round decimal values
                        for key, value in row_dict.items():
                            if isinstance(value, Decimal):
                                row_dict[key] = round(float(value), 2)
                            elif isinstance(value, float):
                                row_dict[key] = round(value, 2)
                        result.append(row_dict)
                    
                    return result
                else:
                    return []
                    
            except Exception as e:
                st.error(f"Query execution error: {e}")
                raise
    
    def get_all_players(self) -> List[str]:
        query = """
        SELECT DISTINCT batter_full_name FROM ipl_data WHERE batter_full_name IS NOT NULL
        UNION
        SELECT DISTINCT bowler_full_name FROM ipl_data WHERE bowler_full_name IS NOT NULL
        ORDER BY 1
        """
        try:
            results = self.execute_query(query)
            return [row['batter_full_name'] for row in results if row['batter_full_name']]
        except Exception as e:
            st.error(f"Error fetching players: {e}")
            return []

# Player name matcher class
class PlayerNameMatcher:
    def __init__(self, all_players: List[str]):
        self.all_players = all_players
        self.player_variations = self._create_player_variations()
    
    def _create_player_variations(self) -> Dict[str, str]:
        variations = {}
        
        for player in self.all_players:
            if not player:
                continue
                
            variations[player.lower()] = player
            
            parts = player.split()
            
            if len(parts) >= 2:
                first_last = f"{parts[0]} {parts[-1]}"
                variations[first_last.lower()] = player
                variations[parts[0].lower()] = player
                variations[parts[-1].lower()] = player
                
                if len(parts[0]) > 1:
                    initial_last = f"{parts[0][0]} {parts[-1]}"
                    variations[initial_last.lower()] = player
            
            clean_name = re.sub(r'^(Mr|Ms|Dr)\.?\s*', '', player, flags=re.IGNORECASE)
            if clean_name != player:
                variations[clean_name.lower()] = player
        
        return variations
    
    def find_best_match(self, query_name: str, threshold: int = 70) -> Optional[str]:
        if not query_name:
            return None
            
        query_name = query_name.strip()
        query_lower = query_name.lower()
        
        if query_lower in self.player_variations:
            return self.player_variations[query_lower]
        
        best_match = process.extractOne(
            query_name, 
            self.all_players, 
            scorer=fuzz.partial_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            return best_match[0]
        
        return None
    
    def extract_player_names_from_query(self, query: str) -> List[str]:
        patterns = [
            r'(?:stats|performance|record|average|runs|wickets)(?:\s+(?:of|for|by))?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)s+(?:vs|against|batting|bowling)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s+(?:in|during|at)'
        ]
        
        potential_names = []
        for pattern in patterns:
            matches = re.findall(pattern, query)
            potential_names.extend(matches)
        
        unique_names = list(set(potential_names))
        matched_names = []
        for name in unique_names:
            best_match = self.find_best_match(name)
            if best_match and best_match not in matched_names:
                matched_names.append(best_match)
        
        return matched_names

# Cricket query generator class
class CricketQueryGenerator:
    def __init__(self, groq_api_key: str, player_matcher: PlayerNameMatcher):
        self.client = Groq(api_key=groq_api_key)
        self.player_matcher = player_matcher
        
        self.cricket_schema = """
        Table: ipl_data
        Key Columns:
        - batter_full_name, bowler_full_name (TEXT): Player names
        - runs_batter, runs_total (INTEGER): Runs scored
        - over_col (INTEGER): Over number (1-20)
        - is_four, is_six, is_wicket (BOOLEAN): Boundary/wicket indicators
        - valid_ball (INTEGER): 1 if valid ball
        - bat_hand (TEXT): LHB/RHB for batting hand
        - bowling_style (TEXT): Pace/spin bowling style
        - season (TEXT): IPL season
        - venue (TEXT): Match venue
        
        Important Notes:
        - Death overs: over_col BETWEEN 16 AND 20
        - Powerplay: over_col BETWEEN 1 AND 6
        - Middle overs: over_col BETWEEN 7 AND 15
        - For boolean columns use COUNT(CASE WHEN column = true THEN 1 END)
        - Available data: 2008-2025 seasons
        """
    
    def extract_minimum_threshold(self, user_query: str) -> Optional[int]:
        patterns = [
            r'min(?:imum)?\s+(\d+)\s+runs?',
            r'at least\s+(\d+)\s+runs?',
            r'more than\s+(\d+)\s+runs?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_query.lower())
            if match:
                return int(match.group(1))
        
        return None

    def generate_sql_query(self, user_query: str) -> Dict[str, Any]:
        matched_players = self.player_matcher.extract_player_names_from_query(user_query)
        min_threshold = self.extract_minimum_threshold(user_query)
        
        player_context = ""
        if matched_players:
            player_context = f"\nDetected Players: {', '.join(matched_players)}"
        
        threshold_context = ""
        if min_threshold:
            threshold_context = f"\nMinimum Threshold: Use {min_threshold} runs"
        
        prompt = f"""
        You are an expert cricket analyst. Generate a PostgreSQL query for this question.

        {self.cricket_schema}
        {player_context}
        {threshold_context}
        
        User Question: "{user_query}"
        
        CRITICAL INSTRUCTIONS:
        1. Return ONLY a valid PostgreSQL SELECT query - NO explanations, comments, or additional text
        2. Start with SELECT and end with semicolon
        3. Use exact player names when available
        4. For batting queries, group by batter_full_name
        5. For bowling queries, group by bowler_full_name
        6. For boolean columns use COUNT(CASE WHEN column = true THEN 1 END)
        7. For strike rate: (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
        8. Apply minimum thresholds: HAVING SUM(runs_batter) >= 500 (or specified minimum)
        9. Order by most relevant metric DESC
        10. LIMIT to 10-20 results
        
        IMPORTANT: Return ONLY the SQL query with NO additional text, explanations, or comments.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800
            )
            
            sql_query = response.choices[0].message.content.strip()
            sql_query = self._clean_sql_query(sql_query)
            
            return {
                "sql_query": sql_query,
                "matched_players": matched_players,
                "original_query": user_query
            }
            
        except Exception as e:
            st.error(f"Error generating query: {e}")
            return self._fallback_query_generation(user_query, matched_players)
    
    def _clean_sql_query(self, query: str) -> str:
        # Remove code block formatting
        query = re.sub(r'```sql\n?', '', query)
        query = re.sub(r'```\n?', '', query)
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Find the SELECT statement
        if not query.upper().startswith('SELECT'):
            select_match = re.search(r'SELECT\s', query, re.IGNORECASE)
            if select_match:
                query = query[select_match.start():]
        
        # Remove any text after the SQL query ends
        # Look for common SQL ending patterns and cut off explanatory text
        sql_endings = [
            r';\s*This\s+query',
            r';\s*Note\s+that',
            r';\s*The\s+query',
            r';\s*This\s+will',
            r';\s*Explanation',
            r';\s*--',
            r';\s*\n\n',
            r';\s*[A-Z][a-z]+\s+[a-z]+',  # Sentences after semicolon
        ]
        
        for pattern in sql_endings:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                query = query[:match.start() + 1]  # Keep the semicolon
                break
        
        # Ensure query ends with semicolon if it doesn't
        query = query.strip()
        if not query.endswith(';'):
            query += ';'
        
        return query
    
    def _fallback_query_generation(self, user_query: str, matched_players: List[str]) -> Dict[str, Any]:
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ['runs', 'batting', 'average', 'strike rate']):
            player_filter = ""
            if matched_players:
                player_names = "', '".join(matched_players)
                player_filter = f"WHERE batter_full_name IN ('{player_names}')"
            
            sql_query = f"""
            SELECT 
                batter_full_name,
                COUNT(*) as balls_faced,
                SUM(runs_batter) as total_runs,
                ROUND((SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END)), 2) as strike_rate,
                COUNT(CASE WHEN is_four = true THEN 1 END) as fours,
                COUNT(CASE WHEN is_six = true THEN 1 END) as sixes
            FROM ipl_data 
            {player_filter}
            GROUP BY batter_full_name 
            HAVING SUM(runs_batter) >= 500
            ORDER BY total_runs DESC 
            LIMIT 10
            """
        else:
            sql_query = """
            SELECT 
                batter_full_name,
                SUM(runs_batter) as total_runs,
                COUNT(*) as balls_faced,
                ROUND((SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END)), 2) as strike_rate
            FROM ipl_data 
            GROUP BY batter_full_name 
            HAVING SUM(runs_batter) >= 1000
            ORDER BY total_runs DESC 
            LIMIT 10
            """
        
        return {
            "sql_query": sql_query,
            "matched_players": matched_players,
            "original_query": user_query
        }

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'db_manager' not in st.session_state:
    st.session_state.db_manager = None

if 'player_matcher' not in st.session_state:
    st.session_state.player_matcher = None

if 'query_generator' not in st.session_state:
    st.session_state.query_generator = None

# Initialize connections
@st.cache_resource(show_spinner="🔄 Connecting to database and initializing AI...")
def initialize_connections():
    # Debug: Show available secrets (without values)
    if hasattr(st, 'secrets'):
        available_secrets = list(st.secrets.keys()) if st.secrets else []
        st.sidebar.write(f"🔑 Available secrets: {available_secrets}")
    
    try:
        database_url = st.secrets["DATABASE_URL"]
        groq_api_key = st.secrets["GROQ_API_KEY"]
        st.sidebar.success("✅ Secrets loaded from Streamlit")
    except (KeyError, AttributeError) as e:
        # Fallback to environment variables
        database_url = os.getenv("DATABASE_URL")
        groq_api_key = os.getenv("GROQ_API_KEY")
        st.sidebar.warning("⚠️ Using environment variables")
        
        if not database_url or not groq_api_key:
            st.error(f"""
            🔑 **Missing Configuration**
            
            Please add these secrets in Streamlit Cloud:
            1. Go to your app settings
            2. Click on "Secrets" 
            3. Add:
            ```
            DATABASE_URL = "your_database_url"
            GROQ_API_KEY = "your_groq_key"
            ```
            
            Error: {e}
            """)
            st.stop()
    
    try:
        # Initialize database
        db_manager = DatabaseManager(database_url)
        
        # Test connection and get players
        players = db_manager.get_all_players()
        if not players:
            st.error("Could not load players from database")
            st.stop()
            
        # Initialize player matcher
        player_matcher = PlayerNameMatcher(players)
        
        # Initialize query generator
        query_generator = CricketQueryGenerator(groq_api_key, player_matcher)
        
        return db_manager, player_matcher, query_generator, len(players)
        
    except Exception as e:
        st.error(f"Initialization error: {e}")
        st.stop()

# Get database stats
def get_stats_summary(db_manager):
    try:
        query = """
        SELECT 
            COUNT(DISTINCT match_id) as total_matches,
            COUNT(DISTINCT batter_full_name) as total_batters,
            COUNT(DISTINCT bowler_full_name) as total_bowlers,
            COUNT(DISTINCT venue) as total_venues,
            COUNT(DISTINCT season) as total_seasons,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(*) as total_balls
        FROM ipl_data
        """
        result = db_manager.execute_query(query)
        return result[0] if result else {}
    except:
        return {}

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">🏏 IPL Cricket Chatbot</h1>', unsafe_allow_html=True)
    st.markdown("### Ask me anything about IPL cricket stats! Powered by AI & 277K+ records")
    
    # Initialize connections
    try:
        db_manager, player_matcher, query_generator, total_players = initialize_connections()
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ About")
        st.success("✅ **All systems connected!**")
        st.write(f"""
        🤖 **AI-Powered Cricket Analytics**
        - {total_players:,} players loaded
        - Dynamic SQL generation 
        - Fuzzy name matching
        - Real-time query processing
        """)
        
        # Database stats
        st.header("📊 Database Stats")
        stats = get_stats_summary(db_manager)
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Matches", f"{stats.get('total_matches', 0):,}")
                st.metric("Players", f"{stats.get('total_batters', 0):,}")
            with col2:
                st.metric("Records", f"{stats.get('total_balls', 0):,}")
                st.metric("Seasons", stats.get('total_seasons', 0))
            
            st.write(f"**Data Range:** {stats.get('earliest_date', '')} to {stats.get('latest_date', '')}")
        
        # Clear chat
        if st.session_state.messages:
            if st.button("🗑️ Clear Chat History", type="secondary"):
                st.session_state.messages = []
                st.rerun()
    
    # Example queries
    st.header("💡 Example Queries")
    col1, col2, col3, col4 = st.columns(4)
    
    examples = [
        ("🏆 Top IPL Scorers", "Who are the top 10 run scorers in IPL history?"),
        ("⚡ Death Overs Kings", "Who scored the most runs in death overs?"),
        ("👑 Virat Kohli Stats", "Virat Kohli career batting statistics"),
        ("🎯 Best vs Spin", "Best batsmen against spin bowlers in middle overs")
    ]
    
    for i, (title, query) in enumerate(examples):
        col = [col1, col2, col3, col4][i]
        with col:
            if st.button(title, use_container_width=True, key=f"example_{i}"):
                st.session_state.example_query = query
    
    # Query input
    query_input = st.text_input(
        "🤔 **Ask your cricket question:**",
        value=st.session_state.get('example_query', ''),
        placeholder="e.g., Best bowlers against left-handed batsmen in powerplay overs",
        key="main_query_input"
    )
    
    # Clear example query after setting
    if 'example_query' in st.session_state:
        del st.session_state.example_query
    
    # Process query
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ask_button = st.button("🔍 Ask Chatbot", type="primary", use_container_width=True)
    with col2:
        if st.button("🎲 Random Query", use_container_width=True):
            random_queries = [
                "MS Dhoni finishing stats in last 5 overs",
                "Most economical bowlers in powerplay",
                "Highest strike rates in IPL finals",
                "Best wicket keepers by dismissals"
            ]
            import random
            st.session_state.example_query = random.choice(random_queries)
            st.rerun()
    with col3:
        if st.button("📊 Quick Stats", use_container_width=True):
            st.session_state.example_query = "Overall IPL statistics summary"
            st.rerun()
    
    # Handle query processing
    if ask_button and query_input.strip():
        process_query(query_input.strip(), db_manager, query_generator)
    elif query_input.strip() and st.session_state.get('auto_submit', False):
        process_query(query_input.strip(), db_manager, query_generator)
        st.session_state.auto_submit = False

def process_query(query: str, db_manager, query_generator):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "timestamp": datetime.now()
    })
    
    # Process with AI
    with st.spinner("🤖 Analyzing your cricket query..."):
        try:
            query_result = query_generator.generate_sql_query(query)
            
            if not query_result.get("sql_query"):
                result = {"error": "Could not generate valid SQL query"}
            else:
                # Execute query
                data = db_manager.execute_query(query_result["sql_query"])
                
                # Generate response
                if not data:
                    response_text = "I couldn't find any data matching your query. Please try rephrasing your question."
                elif len(data) == 1:
                    player_name = data[0].get('batter_full_name') or data[0].get('bowler_full_name', 'the player')
                    response_text = f"Here are the statistics for {player_name}."
                else:
                    response_text = f"I found results for {len(data)} records. Here's what I discovered:"
                
                result = {
                    "response": response_text,
                    "data": data,
                    "sql_query": query_result["sql_query"],
                    "matched_players": query_result.get("matched_players", []),
                    "execution_time": 1.2  # Placeholder
                }
                
        except Exception as e:
            result = {"error": f"Query processing error: {str(e)}"}
    
    # Add bot response
    st.session_state.messages.append({
        "role": "assistant",
        "content": result,
        "timestamp": datetime.now()
    })
    
    st.rerun()

# Display chat history
if st.session_state.messages:
    st.header("💬 Chat History")
    
    for message in reversed(st.session_state.messages[-10:]):  # Show last 10
        timestamp_str = message['timestamp'].strftime("%H:%M:%S")
        
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message-user">
                <strong>You ({timestamp_str}):</strong><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
        
        else:
            result = message['content']
            
            if 'error' in result:
                st.error(f"❌ **Error ({timestamp_str}):** {result['error']}")
            else:
                # Bot response
                st.markdown(f"""
                <div class="chat-message-bot">
                    <strong>🤖 Cricket AI ({timestamp_str}):</strong><br>
                    {result.get('response', 'Here are your results:')}
                </div>
                """, unsafe_allow_html=True)
                
                # Data display
                if result.get('data'):
                    df = pd.DataFrame(result['data'])
                    
                    # Display table with custom styling
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                    )
                    
                    # Download and SQL query in columns
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"cricket_data_{int(time.time())}.csv",
                            mime="text/csv",
                            key=f"download_{message['timestamp']}"
                        )
                    
                    with col2:
                        # SQL Query toggle
                        if result.get('sql_query'):
                            if st.button(f"🔍 Show/Hide SQL", key=f"sql_{message['timestamp']}"):
                                st.session_state[f"show_sql_{message['timestamp']}"] = not st.session_state.get(f"show_sql_{message['timestamp']}", False)
                            
                            if st.session_state.get(f"show_sql_{message['timestamp']}", False):
                                st.code(result['sql_query'], language='sql')
        
        st.divider()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏏 <strong>IPL Cricket Chatbot</strong> - All-in-One Streamlit App</p>
    <p>✨ Powered by Groq AI • PostgreSQL • 277,935+ Ball-by-Ball Records • Dynamic Query Generation ✨</p>
    <p><em>Ask any cricket question - from simple stats to complex analytics!</em></p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()