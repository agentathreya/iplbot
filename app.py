import streamlit as st
import psycopg2
import pandas as pd
import os
from datetime import datetime
import time
import logging
from typing import List, Dict, Any, Optional
from groq import Groq
import re
from decimal import Decimal
from contextlib import contextmanager
import json

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
    
    def execute_query(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """Execute query and return result with metadata"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    result_data = []
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        # Round decimal values
                        for key, value in row_dict.items():
                            if isinstance(value, Decimal):
                                row_dict[key] = round(float(value), 2)
                            elif isinstance(value, float):
                                row_dict[key] = round(value, 2)
                        result_data.append(row_dict)
                    
                    return {
                        "success": True,
                        "data": result_data,
                        "row_count": len(result_data),
                        "columns": columns
                    }
                else:
                    return {
                        "success": True,
                        "data": [],
                        "row_count": 0,
                        "message": "Query executed successfully, no data returned"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "query": query
                }

# Simplified Cricket Query Agent (without complex tool calling)
class SimpleCricketAgent:
    def __init__(self, groq_api_key: str, db_manager: DatabaseManager):
        self.client = Groq(api_key=groq_api_key)
        self.db_manager = db_manager

    def chat(self, user_query: str) -> Dict[str, Any]:
        """Simple chat function that generates SQL and executes it"""
        
        try:
            # Generate SQL using Groq
            system_prompt = """You are an expert cricket analyst. Generate ONLY a valid PostgreSQL query for the IPL cricket database.

Database Schema:
- Table: ipl_data
- Key columns: batter_full_name, bowler_full_name, runs_batter, runs_total, over_col, ball, is_four, is_six, is_wicket, valid_ball, bat_hand, bowling_type, season, venue, batting_team, bowling_team, innings, match_id, date

Important Cricket Statistics:
- Batting Strike Rate: (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))
- Batting Average: SUM(runs_batter) / NULLIF(COUNT(CASE WHEN is_wicket = true THEN 1 END), 0)
- Bowling Average: SUM(runs_total) / NULLIF(COUNT(CASE WHEN is_wicket = true THEN 1 END), 0)
- Bowling Strike Rate: COUNT(CASE WHEN valid_ball = 1 THEN 1 END) / NULLIF(COUNT(CASE WHEN is_wicket = true THEN 1 END), 0)
- Bowling Economy Rate: (SUM(runs_total) * 6.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END))

Bowling Types:
- Use bowling_type column (not bowling_style)
- Spin bowling: bowling_type ILIKE '%spin%'
- Pace bowling: bowling_type ILIKE '%pace%' OR bowling_type ILIKE '%fast%' OR bowling_type ILIKE '%medium%'

Match Phases:
- Powerplay: over_col BETWEEN 1 AND 6
- Middle overs: over_col BETWEEN 7 AND 15
- Death overs: over_col BETWEEN 16 AND 20

Guidelines:
- Use ILIKE '%name%' for player name searches
- Add HAVING clauses for minimum thresholds (e.g., >= 500 runs or >= 100 balls)
- Use NULLIF to avoid division by zero
- Round decimal results to 2 places with ROUND()

Generate ONLY the SQL query, no explanations."""

            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the SQL query
            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0]
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1]
            
            sql_query = sql_query.strip()
            
            # Execute the query
            result = self.db_manager.execute_query(sql_query)
            
            if result["success"] and result["data"]:
                # Generate natural language response
                nl_response = self.client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are a cricket commentator. Interpret the query results in a friendly, engaging way."},
                        {"role": "user", "content": f"User asked: {user_query}\n\nResults: {result['data'][:5]}\n\nProvide a brief, engaging summary."}
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
                
                return {
                    "response": nl_response.choices[0].message.content,
                    "data": result["data"],
                    "sql_query": sql_query,
                    "success": True
                }
            else:
                return {
                    "response": f"Query executed but no data found. Error: {result.get('error', 'Unknown error')}",
                    "data": [],
                    "sql_query": sql_query,
                    "success": False,
                    "error": result.get('error', 'No data found')
                }
                
        except Exception as e:
            return {
                "response": f"I encountered an error while processing your question: {str(e)}",
                "data": [],
                "sql_query": None,
                "success": False,
                "error": str(e)
            }

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Initialize connections
@st.cache_resource(show_spinner="🔄 Connecting to database and AI...")
def initialize_connections():
    try:
        # Try Streamlit secrets first
        database_url = st.secrets["DATABASE_URL"]
        groq_api_key = st.secrets["GROQ_API_KEY"]
    except (KeyError, AttributeError):
        # Fallback to environment variables
        database_url = os.getenv("DATABASE_URL")
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not database_url or not groq_api_key:
            st.error("Please set DATABASE_URL and GROQ_API_KEY in Streamlit secrets or environment variables")
            st.stop()
    
    try:
        # Initialize database
        db_manager = DatabaseManager(database_url)
        
        # Test connection
        test_result = db_manager.execute_query("SELECT COUNT(*) as total_records FROM ipl_data LIMIT 1")
        if not test_result["success"]:
            st.error(f"Database connection failed: {test_result['error']}")
            st.stop()
            
        total_records = test_result["data"][0]["total_records"]
        
        # Initialize cricket agent
        cricket_agent = SimpleCricketAgent(groq_api_key, db_manager)
        
        return db_manager, cricket_agent, total_records
        
    except Exception as e:
        st.error(f"Initialization error: {e}")
        st.stop()

def process_query(query: str, cricket_agent):
    """Process user query and add to session state"""
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "timestamp": datetime.now()
    })
    
    # Process with AI agent
    with st.spinner("🤖 Analyzing your cricket query with AI..."):
        result = cricket_agent.chat(query)
    
    # Add bot response
    st.session_state.messages.append({
        "role": "assistant",
        "content": result,
        "timestamp": datetime.now()
    })

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">🏏 IPL Cricket Chatbot</h1>', unsafe_allow_html=True)
    st.markdown("### Ask me anything about IPL cricket stats! Powered by Advanced AI & 277K+ records")
    
    # Initialize connections
    try:
        db_manager, cricket_agent, total_records = initialize_connections()
        st.success(f"✅ Connected! {total_records:,} records available")
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ About")
        st.success("✅ **All systems connected!**")
        st.write(f"""
        🤖 **Advanced Cricket Analytics**
        - {total_records:,} ball-by-ball records
        - Simplified AI approach
        - Dynamic SQL generation 
        - Real-time query processing
        """)
        
        # Clear chat
        if st.session_state.messages:
            if st.button("🗑️ Clear Chat History", type="secondary"):
                st.session_state.messages = []
                st.rerun()
    
    # Example queries
    st.header("💡 Example Queries")
    col1, col2, col3, col4 = st.columns(4)
    
    examples = [
        ("🏆 Best Average", "Highest batting average vs spin bowling min 500 runs"),
        ("⚡ Strike Rate", "Best strike rate against pace bowling min 1000 balls"),
        ("🎯 Kohli vs Spin", "Virat Kohli average and strike rate vs spin"),
        ("🏹 Bowling Stats", "Best bowling average and strike rate vs left handed batsmen")
    ]
    
    for i, (title, query) in enumerate(examples):
        col = [col1, col2, col3, col4][i]
        with col:
            if st.button(title, use_container_width=True, key=f"example_{i}"):
                process_query(query, cricket_agent)
                st.rerun()
    
    # Query input
    query_input = st.text_input(
        "🤔 **Ask your cricket question:**",
        placeholder="e.g., Best batting average vs spin bowling min 500 runs",
        key="main_query_input"
    )
    
    # Process query
    if st.button("🔍 Ask Cricket AI", type="primary", use_container_width=True) and query_input.strip():
        process_query(query_input.strip(), cricket_agent)
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
                
                if not result.get('success', True):
                    st.error(f"❌ **Error ({timestamp_str}):** {result.get('error', 'Unknown error')}")
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
                        
                        # Display table
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
                                if st.button(f"🔍 Show SQL", key=f"sql_{message['timestamp']}"):
                                    st.code(result['sql_query'], language='sql')
            
            st.divider()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🏏 <strong>IPL Cricket Chatbot</strong> - Simplified AI Approach</p>
        <p>✨ Powered by Groq AI • PostgreSQL • Dynamic SQL Generation ✨</p>
        <p><em>Ask any cricket question - the AI will generate and execute queries!</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()