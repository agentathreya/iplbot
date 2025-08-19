import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import time

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

.query-input {
    font-size: 1.1rem;
    padding: 0.5rem;
}

.chat-message {
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 0.5rem;
    border-left: 4px solid #2E8B57;
    background-color: #f8f9fa;
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

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'backend_url' not in st.session_state:
    st.session_state.backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')

def call_chatbot_api(query):
    """Call the chatbot API"""
    try:
        response = requests.post(
            f"{st.session_state.backend_url}/chat",
            json={"query": query},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def get_stats_summary():
    """Get database statistics"""
    try:
        response = requests.get(
            f"{st.session_state.backend_url}/stats/summary",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

# Header
st.markdown('<h1 class="main-header">🏏 IPL Cricket Chatbot</h1>', unsafe_allow_html=True)
st.markdown("### Ask me anything about IPL cricket stats!")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.write("""
    This AI-powered chatbot can answer any IPL cricket query using:
    - 277,935+ ball-by-ball records (2008-2025)
    - Dynamic SQL generation 
    - Fuzzy player name matching
    - Advanced cricket analytics
    """)
    
    st.header("🔧 Settings")
    backend_url = st.text_input(
        "Backend URL", 
        value=st.session_state.backend_url,
        help="API endpoint URL"
    )
    if backend_url != st.session_state.backend_url:
        st.session_state.backend_url = backend_url
        st.rerun()
    
    # Database stats
    st.header("📊 Database Stats")
    stats = get_stats_summary()
    if stats:
        st.metric("Total Matches", f"{stats.get('total_matches', 0):,}")
        st.metric("Total Players", f"{stats.get('total_batters', 0):,}")
        st.metric("Total Records", f"{stats.get('total_balls', 0):,}")
        st.write(f"**Data Range:** {stats.get('earliest_date', '')} to {stats.get('latest_date', '')}")
    else:
        st.error("Cannot connect to backend")

# Example queries
st.header("💡 Example Queries")
example_cols = st.columns(3)

with example_cols[0]:
    if st.button("🏏 Top run scorers in IPL", use_container_width=True):
        st.session_state.current_query = "Who are the top 10 run scorers in IPL history?"

with example_cols[1]:
    if st.button("⚡ Death overs specialists", use_container_width=True):
        st.session_state.current_query = "Who scored the most runs in death overs?"

with example_cols[2]:
    if st.button("🎯 Virat Kohli stats", use_container_width=True):
        st.session_state.current_query = "Virat Kohli career batting statistics"

# Query input
query = st.text_input(
    "🤔 Ask your cricket question:",
    value=st.session_state.get('current_query', ''),
    placeholder="e.g., Best bowlers against left-handed batsmen in powerplay",
    key="query_input"
)

if st.session_state.get('current_query'):
    st.session_state.current_query = ''

# Process query
if st.button("🔍 Ask Chatbot", type="primary", use_container_width=True) or query:
    if query.strip():
        # Add user message
        st.session_state.messages.append({
            "role": "user", 
            "content": query,
            "timestamp": datetime.now()
        })
        
        # Call API
        with st.spinner("🤖 Analyzing your cricket query..."):
            result = call_chatbot_api(query)
        
        # Add bot response
        st.session_state.messages.append({
            "role": "assistant",
            "content": result,
            "timestamp": datetime.now()
        })
        
        # Clear input
        st.rerun()

# Display chat history
if st.session_state.messages:
    st.header("💬 Chat History")
    
    for i, message in enumerate(reversed(st.session_state.messages[-10:])):  # Show last 10 messages
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(f"**You:** {message['content']}")
                st.caption(message['timestamp'].strftime("%H:%M:%S"))
        
        else:
            with st.chat_message("assistant"):
                result = message['content']
                
                if 'error' in result:
                    st.error(f"❌ {result['error']}")
                else:
                    # Response text
                    st.success(f"🤖 **Response:** {result.get('response', 'Here are your results:')}")
                    
                    # Execution time
                    if 'execution_time' in result:
                        st.caption(f"⏱️ Query executed in {result['execution_time']}s")
                    
                    # Data table
                    if result.get('data'):
                        df = pd.DataFrame(result['data'])
                        st.dataframe(df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"cricket_data_{int(time.time())}.csv",
                            mime="text/csv"
                        )
                    
                    # SQL Query (expandable)
                    if result.get('sql_query'):
                        with st.expander("🔍 View SQL Query"):
                            st.code(result['sql_query'], language='sql')
                
                st.caption(message['timestamp'].strftime("%H:%M:%S"))
        
        st.divider()

# Clear chat button
if st.session_state.messages:
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏏 <strong>IPL Cricket Chatbot</strong> - Powered by AI & 277K+ cricket records</p>
    <p>Built with FastAPI, React, and Streamlit • Dynamic SQL Generation • Real-time Analytics</p>
</div>
""", unsafe_allow_html=True)