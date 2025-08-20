from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging
from decimal import Decimal

from database import DatabaseManager
from player_matcher import PlayerNameMatcher
from query_generator import CricketQueryGenerator

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IPL Cricket Chatbot API",
    description="Advanced cricket analytics chatbot with natural language query support",
    version="1.0.0"
)

# CORS middleware - Updated for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://ipl-cricket-frontend.herokuapp.com",  # Heroku frontend
        "https://*.herokuapp.com",  # All Heroku apps
        "https://*.vercel.app",     # Vercel deployment
        "https://*.netlify.app",    # Netlify deployment
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global variables
db_manager = None
player_matcher = None
query_generator = None

# Pydantic models
class ChatQuery(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    response: str
    data: Optional[List[Dict[str, Any]]] = []
    sql_query: Optional[str] = None
    matched_players: Optional[List[str]] = []
    execution_time: Optional[float] = None

class PlayerSuggestion(BaseModel):
    name: str
    confidence: int

# Initialize components
@app.on_event("startup")
async def startup_event():
    global db_manager, player_matcher, query_generator
    
    try:
        # Initialize database
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        db_manager = DatabaseManager(database_url)
        logger.info("Database connection initialized")
        
        # Initialize player matcher
        players = db_manager.get_all_players()
        player_matcher = PlayerNameMatcher(players)
        logger.info(f"Player matcher initialized with {len(players)} players")
        
        # Initialize query generator
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        query_generator = CricketQueryGenerator(groq_api_key, player_matcher)
        logger.info("Query generator initialized")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

# Dependency to get database manager
def get_db_manager() -> DatabaseManager:
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_manager

def get_query_generator() -> CricketQueryGenerator:
    if query_generator is None:
        raise HTTPException(status_code=500, detail="Query generator not initialized")
    return query_generator

def get_player_matcher() -> PlayerNameMatcher:
    if player_matcher is None:
        raise HTTPException(status_code=500, detail="Player matcher not initialized")
    return player_matcher

# API Routes
@app.get("/")
async def root():
    return {"message": "IPL Cricket Chatbot API is running!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(
    query: ChatQuery, 
    db: DatabaseManager = Depends(get_db_manager),
    qg: CricketQueryGenerator = Depends(get_query_generator)
):
    """Main chat endpoint to handle cricket queries"""
    import time
    start_time = time.time()
    
    try:
        # Generate SQL query using Groq
        query_result = qg.generate_sql_query(query.query)
        
        if not query_result.get("sql_query"):
            raise HTTPException(status_code=400, detail="Could not generate valid SQL query")
        
        # Execute the query
        data = db.execute_query(query_result["sql_query"])
        
        # Round decimal values to 2 decimal places
        data = round_decimal_values(data)
        
        # Generate natural language response
        response_text = generate_response_text(query.query, data, query_result.get("matched_players", []))
        
        execution_time = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            data=data,
            sql_query=query_result["sql_query"],
            matched_players=query_result.get("matched_players", []),
            execution_time=round(execution_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/players/search")
async def search_players(
    query: str, 
    limit: int = 10,
    pm: PlayerNameMatcher = Depends(get_player_matcher)
) -> List[PlayerSuggestion]:
    """Search for players with fuzzy matching"""
    try:
        matches = pm.find_multiple_matches(query, limit=limit)
        return [PlayerSuggestion(name=match[0], confidence=match[1]) for match in matches]
    except Exception as e:
        logger.error(f"Player search error: {e}")
        raise HTTPException(status_code=500, detail="Error searching players")

@app.get("/players")
async def get_all_players(db: DatabaseManager = Depends(get_db_manager)) -> List[str]:
    """Get all players in the database"""
    try:
        return db.get_all_players()
    except Exception as e:
        logger.error(f"Get players error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching players")

@app.get("/teams")
async def get_all_teams(db: DatabaseManager = Depends(get_db_manager)) -> List[str]:
    """Get all teams in the database"""
    try:
        return db.get_all_teams()
    except Exception as e:
        logger.error(f"Get teams error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching teams")

@app.get("/venues")
async def get_all_venues(db: DatabaseManager = Depends(get_db_manager)) -> List[str]:
    """Get all venues in the database"""
    try:
        return db.get_all_venues()
    except Exception as e:
        logger.error(f"Get venues error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching venues")

@app.get("/stats/summary")
async def get_summary_stats(db: DatabaseManager = Depends(get_db_manager)) -> Dict[str, Any]:
    """Get summary statistics of the database"""
    try:
        summary_query = """
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
        
        result = db.execute_query(summary_query)
        return result[0] if result else {}
        
    except Exception as e:
        logger.error(f"Summary stats error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching summary statistics")

@app.post("/query/validate")
async def validate_query(query: ChatQuery) -> Dict[str, Any]:
    """Validate and preview a query without execution"""
    try:
        qg = get_query_generator()
        query_result = qg.generate_sql_query(query.query)
        
        return {
            "valid": bool(query_result.get("sql_query")),
            "sql_query": query_result.get("sql_query"),
            "matched_players": query_result.get("matched_players", []),
            "query_type": classify_query_type(query.query)
        }
        
    except Exception as e:
        logger.error(f"Query validation error: {e}")
        raise HTTPException(status_code=500, detail="Error validating query")

# Helper functions
def round_decimal_values(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Round decimal values to 2 decimal places"""
    if not data:
        return data
    
    for row in data:
        for key, value in row.items():
            if isinstance(value, Decimal):
                row[key] = round(float(value), 2)
            elif isinstance(value, float):
                row[key] = round(value, 2)
    
    return data

def generate_response_text(original_query: str, data: List[Dict[str, Any]], matched_players: List[str]) -> str:
    """Generate natural language response based on query results"""
    if not data:
        return "I couldn't find any data matching your query. Please try rephrasing your question or check the player names."
    
    # Basic response generation based on query type
    if len(data) == 1:
        # Single result
        record = data[0]
        if 'batter_full_name' in record:
            return f"Here are the statistics for {record.get('batter_full_name', 'the player')}."
        elif 'bowler_full_name' in record:
            return f"Here are the bowling statistics for {record.get('bowler_full_name', 'the bowler')}."
    else:
        # Multiple results
        if 'batter_full_name' in data[0]:
            return f"I found batting statistics for {len(data)} players. Here are the results:"
        elif 'bowler_full_name' in data[0]:
            return f"I found bowling statistics for {len(data)} players. Here are the results:"
    
    return f"I found {len(data)} records matching your query:"

def classify_query_type(query: str) -> str:
    """Classify the type of cricket query"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['batting', 'runs', 'average', 'strike rate']):
        return 'batting'
    elif any(word in query_lower for word in ['bowling', 'wickets', 'economy']):
        return 'bowling'
    elif any(word in query_lower for word in ['match', 'team', 'vs']):
        return 'match'
    elif any(word in query_lower for word in ['best', 'worst', 'top', 'highest']):
        return 'ranking'
    else:
        return 'general'

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)