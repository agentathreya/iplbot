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

# Cricket schema for tool description
CRICKET_SCHEMA = """
IPL Cricket Database Schema:

Table: ipl_data
Key Columns:
- batter_full_name (TEXT): Full name of the batsman
- bowler_full_name (TEXT): Full name of the bowler
- runs_batter (INTEGER): Runs scored by the batsman on this ball
- runs_total (INTEGER): Total runs scored on this ball (including extras)
- over_col (INTEGER): Over number (1-20 for T20)
- ball (INTEGER): Ball number within the over (1-6)
- is_four (BOOLEAN): True if boundary (4 runs)
- is_six (BOOLEAN): True if six
- is_wicket (BOOLEAN): True if wicket taken
- valid_ball (INTEGER): 1 if valid ball, 0 for wides/no-balls
- bat_hand (TEXT): Batting hand - 'LHB' (Left) or 'RHB' (Right)
- bowling_style (TEXT): Bowling style (contains 'pace', 'spin', etc.)
- season (TEXT): IPL season (e.g., '2008', '2023/24')
- venue (TEXT): Stadium/Ground name
- batting_team (TEXT): Team batting
- bowling_team (TEXT): Team bowling
- innings (INTEGER): Innings number (1 or 2)
- match_id (INTEGER): Unique match identifier
- date (DATE): Match date

Important Cricket Context:
- Powerplay overs: 1-6 (over_col BETWEEN 1 AND 6)
- Middle overs: 7-15 (over_col BETWEEN 7 AND 15)  
- Death overs: 16-20 (over_col BETWEEN 16 AND 20)
- Strike rate = (runs_scored * 100.0) / balls_faced
- Economy rate = (runs_conceded * 6.0) / balls_bowled
- For boolean fields, use COUNT(CASE WHEN column = true THEN 1 END)
- Available seasons: 2008-2025 (277,935+ ball-by-ball records)

Example Queries:
- Top run scorers: SELECT batter_full_name, SUM(runs_batter) as total_runs FROM ipl_data GROUP BY batter_full_name ORDER BY total_runs DESC LIMIT 10;
- Best strike rate: SELECT batter_full_name, (SUM(runs_batter) * 100.0 / COUNT(CASE WHEN valid_ball = 1 THEN 1 END)) as strike_rate FROM ipl_data GROUP BY batter_full_name HAVING COUNT(*) >= 100 ORDER BY strike_rate DESC LIMIT 10;
"""

# Improved Cricket Query Agent
class CricketQueryAgent:
    def __init__(self, groq_api_key: str, db_manager: DatabaseManager):
        self.client = Groq(api_key=groq_api_key)
        self.db_manager = db_manager

    def execute_cricket_query(self, sql_query: str) -> str:
        """Tool function to execute cricket database queries"""
        try:
            result = self.db_manager.execute_query(sql_query)
            
            if result["success"]:
                if result["data"]:
                    return json.dumps({
                        "status": "success",
                        "row_count": result["row_count"],
                        "data": result["data"][:20]  # Limit to 20 rows for display
                    })
                else:
                    return json.dumps({
                        "status": "success",
                        "message": "Query executed successfully but returned no data"
                    })
            else:
                return json.dumps({
                    "status": "error",
                    "error": result["error"],
                    "suggestion": "Please check the SQL syntax and table/column names"
                })
                
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            })

    def chat(self, user_query: str) -> Dict[str, Any]:
        """Main chat function using tool-based approach"""
        
        # System prompt for cricket analysis
        system_prompt = f"""You are an expert IPL cricket analyst and SQL query generator.

Your task is to help users analyze cricket data by:
1. Understanding their natural language cricket questions
2. Generating appropriate SQL queries using the execute_cricket_query tool
3. Interpreting the results and providing meaningful cricket insights

Database Schema:
{CRICKET_SCHEMA}

Important Guidelines:
- ALWAYS use the execute_cricket_query tool for data queries
- Generate clean, efficient SQL queries
- Apply appropriate filters and thresholds (e.g., minimum 500 runs for meaningful batting stats)
- Explain cricket insights in an engaging, fan-friendly way
- If a query fails, analyze the error and try a corrected version
- For player names, use ILIKE '%player%' for partial matching

Available Functions:
- execute_cricket_query(sql_query): Execute SQL query on cricket database

User Question: {user_query}"""

        # Conversation with function calling
        messages = [
            {
                "role": "system", 
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_query
            }
        ]

        # Available tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_cricket_query",
                    "description": "Execute SQL query on IPL cricket database to get player statistics, match data, and cricket analytics",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {
                                "type": "string",
                                "description": "SQL query to execute on the cricket database. Must be valid PostgreSQL syntax."
                            }
                        },
                        "required": ["sql_query"]
                    }
                }
            }
        ]

        try:
            # Make API call with tools
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1,
                max_tokens=1500
            )

            # Process the response
            assistant_message = response.choices[0].message
            
            # Check if the model wants to use tools
            if assistant_message.tool_calls:
                # Execute the tool call
                tool_call = assistant_message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "execute_cricket_query":
                    # Execute the SQL query
                    sql_query = function_args["sql_query"]
                    tool_result = self.execute_cricket_query(sql_query)
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call.dict()]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                    
                    # Get final response with data interpretation
                    final_response = self.client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages,
                        temperature=0.2,
                        max_tokens=1000
                    )
                    
                    # Parse the tool result for display
                    try:
                        tool_data = json.loads(tool_result)
                        if tool_data["status"] == "success" and "data" in tool_data:
                            return {
                                "response": final_response.choices[0].message.content,
                                "data": tool_data["data"],
                                "sql_query": sql_query,
                                "success": True
                            }
                        else:
                            return {
                                "response": final_response.choices[0].message.content,
                                "data": [],
                                "sql_query": sql_query,
                                "success": False,
                                "error": tool_data.get("error", "Unknown error")
                            }
                    except:
                        return {
                            "response": final_response.choices[0].message.content,
                            "data": [],
                            "sql_query": sql_query,
                            "success": True
                        }
            else:
                # Direct response without tools
                return {
                    "response": assistant_message.content,
                    "data": [],
                    "sql_query": None,
                    "success": True
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
@st.cache_resource(show_spinner="🔄 Connecting to database and initializing AI...")
def initialize_connections():
    try:
        database_url = st.secrets["DATABASE_URL"]
        groq_api_key = st.secrets["GROQ_API_KEY"]
    except (KeyError, AttributeError):
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
        cricket_agent = CricketQueryAgent(groq_api_key, db_manager)
        
        return db_manager, cricket_agent, total_records
        
    except Exception as e:
        st.error(f"Initialization error: {e}")
        st.stop()

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">🏏 IPL Cricket Chatbot</h1>', unsafe_allow_html=True)
    st.markdown("### Ask me anything about IPL cricket stats! Powered by Advanced AI & 277K+ records")
    
    # Initialize connections
    try:
        db_manager, cricket_agent, total_records = initialize_connections()
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
        - Tool-based AI agent approach
        - Dynamic SQL generation 
        - Real-time query processing
        
        🔧 **Powered by:**
        - Groq LLM with function calling
        - PostgreSQL database
        - Advanced error handling
        """)
        
        st.header("📊 Features")
        st.write("""
        - **Natural Language Queries**
        - **Automatic Error Recovery**  
        - **Cricket Context Awareness**
        - **Optimized SQL Generation**
        - **Real-time Data Processing**
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
        ("🏆 Top Scorers", "Who are the top 10 run scorers in IPL?"),
        ("⚡ Death Overs", "Best batsmen in death overs"),
        ("🎯 vs Spin", "Best batters against spin bowling"),
        ("👑 Kohli Stats", "Virat Kohli career statistics")
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
        placeholder="e.g., Which bowler has the best economy rate in powerplay overs?",
        key="main_query_input"
    )
    
    # Clear example query after setting
    if 'example_query' in st.session_state:
        del st.session_state.example_query
    
    # Process query
    if st.button("🔍 Ask Cricket AI", type="primary", use_container_width=True) and query_input.strip():
        process_query(query_input.strip(), cricket_agent)

def process_query(query: str, cricket_agent):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "timestamp": datetime.now()
    })
    
    # Process with AI agent
    with st.spinner("🤖 Analyzing your cricket query with AI tools..."):
        result = cricket_agent.chat(query)
    
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
    <p>🏏 <strong>Advanced IPL Cricket Chatbot</strong> - Tool-Based AI Agent</p>
    <p>✨ Powered by Groq Function Calling • PostgreSQL • LangChain-Inspired Architecture ✨</p>
    <p><em>Ask any cricket question - the AI will automatically generate and execute the right queries!</em></p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()