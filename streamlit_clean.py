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
    page_title="IPL Cricket Analytics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to match your React UI design
st.markdown("""
<style>
/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main container styling */
.main > div {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Header styling similar to React app */
.header-container {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.header-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
}

.header-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(to right, #3b82f6, #8b5cf6);
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.5rem;
}

.header-text h1 {
    color: #111827;
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
}

.header-text p {
    color: #6b7280;
    font-size: 0.875rem;
    margin: 0;
}

/* Chat container styling */
.chat-container {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    height: calc(100vh - 200px);
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

/* Message styling */
.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 1rem 1rem 0.25rem 1rem;
    margin-left: 20%;
    word-wrap: break-word;
}

.bot-message {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    color: #1f2937;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 1rem 1rem 1rem 0.25rem;
    margin-right: 20%;
    word-wrap: break-word;
}

/* Input styling */
.stTextInput > div > div > input {
    border-radius: 0.5rem;
    border: 1px solid #d1d5db;
    padding: 0.75rem;
}

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 0.5rem;
    padding: 0.75rem 1.5rem;
    font-weight: 500;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    border: none;
}

/* Data table styling */
.stDataFrame {
    border-radius: 0.5rem;
    overflow: hidden;
    margin: 1rem 0;
}

/* Welcome message styling */
.welcome-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 1rem;
    margin: 1rem 0;
    text-align: center;
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
@st.cache_resource(show_spinner=False)
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
        
        # Initialize cricket agent
        cricket_agent = CricketQueryAgent(groq_api_key, db_manager)
        
        return db_manager, cricket_agent
        
    except Exception as e:
        st.error(f"Initialization error: {e}")
        st.stop()

# Main app
def main():
    # Header matching your React design
    st.markdown("""
    <div class="header-container">
        <div class="header-title">
            <div class="header-icon">🏏</div>
            <div class="header-text">
                <h1>IPL Cricket Analytics</h1>
                <p>AI-Powered Cricket Statistics Chatbot</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize connections
    try:
        db_manager, cricket_agent = initialize_connections()
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        st.stop()
    
    # Welcome message (only show if no messages yet)
    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome-message">
            <h2>🏏 Welcome to IPL Cricket Analytics Chatbot!</h2>
            <p>I'm your cricket analytics assistant powered by comprehensive IPL data. Ask me anything about player statistics, team performance, or match analytics!</p>
            <br>
            <p><strong>Try asking:</strong></p>
            <p>• "Top run scorers in IPL"</p>
            <p>• "Best bowlers in death overs"</p>
            <p>• "Kohli vs Rohit comparison"</p>
            <p>• "Mumbai Indians batting average"</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        # Display all messages
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                st.markdown(f'<div class="user-message"><strong>You:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message"><strong>🤖 Cricket AI:</strong><br>{message["content"]["response"]}</div>', unsafe_allow_html=True)
                
                # Show data table if available
                if message["content"].get("data"):
                    df = pd.DataFrame(message["content"]["data"])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"cricket_data_{int(time.time())}.csv",
                        mime="text/csv",
                        key=f"download_{i}"
                    )

    # Chat input at bottom
    st.markdown("---")
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask your cricket question:",
                placeholder="e.g., Who are the top run scorers in IPL?",
                key="chat_input"
            )
        
        with col2:
            send_button = st.button("Send", use_container_width=True)
    
    # Process user input
    if (send_button or user_input) and user_input.strip():
        # Add user message to session
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Show processing message
        with st.spinner("🤖 Analyzing your cricket query..."):
            result = cricket_agent.chat(user_input)
        
        # Add bot response
        st.session_state.messages.append({
            "role": "assistant",
            "content": result,
            "timestamp": datetime.now()
        })
        
        # Clear input and rerun
        st.session_state.chat_input = ""
        st.rerun()

if __name__ == "__main__":
    main()