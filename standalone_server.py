#!/usr/bin/env python3
"""
Standalone Premier League Server (No MCP dependency)
Provides all the enhanced functions via HTTP API
"""

import sys
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import get_settings
from database.connection import get_db_client
from datetime import datetime

# Initialize
app = FastAPI(title="Premier League MCP Server", version="1.0.0")
settings = get_settings()
db = get_db_client()

@app.get("/")
async def root():
    return {"message": "Premier League MCP Server", "status": "running", "season": settings.DEFAULT_SEASON}

@app.get("/health")
async def health():
    try:
        # Test database connection
        result = db.table("request_mode_config").select("current_mode").limit(1).execute()
        return {"status": "healthy", "database": "connected", "mode": result.data[0]["current_mode"] if result.data else "unknown"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "unhealthy", "error": str(e)})

@app.get("/api/current-gameweek")
async def get_current_gameweek(season: int = None):
    try:
        season = season or settings.DEFAULT_SEASON
        
        # Calculate current gameweek from fixtures
        now = datetime.now()
        
        # Find next fixture to determine current gameweek
        next_fixtures = db.table("fixtures").select("*").eq("league_id", settings.PREMIER_LEAGUE_ID).eq("season", season).gte("date", now.isoformat()).order("date").limit(1).execute()
        
        if next_fixtures.data:
            current_gw = next_fixtures.data[0]["gameweek"]
            
            if current_gw:
                # Get all fixtures for current gameweek
                fixtures_result = db.table("fixtures").select("*").eq("league_id", settings.PREMIER_LEAGUE_ID).eq("season", season).eq("gameweek", current_gw).execute()
                
                return {
                    "current_gameweek": current_gw,
                    "season": season,
                    "fixtures": fixtures_result.data,
                    "total_gameweeks": 38,
                    "source": "supabase_cache"
                }
        
        return {"error": "Could not determine current gameweek"}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"get_current_gameweek error: {str(e)}"})

@app.get("/api/gameweek/{gameweek}/fixtures")
async def get_gameweek_fixtures(gameweek: int, season: int = None):
    try:
        season = season or settings.DEFAULT_SEASON
        
        if not (1 <= gameweek <= 38):
            return JSONResponse(status_code=400, content={"error": "Gameweek must be between 1 and 38"})
        
        fixtures = db.table("fixtures").select("*").eq("league_id", settings.PREMIER_LEAGUE_ID).eq("season", season).eq("gameweek", gameweek).execute()
        
        return {
            "gameweek": gameweek,
            "season": season,
            "fixtures": fixtures.data,
            "fixture_count": len(fixtures.data),
            "source": "supabase_cache"
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"get_gameweek_fixtures error: {str(e)}"})

@app.get("/api/todays-fixtures")
async def get_todays_fixtures():
    try:
        today = datetime.now().date().isoformat()
        
        # Get today's fixtures
        fixtures_result = db.table("fixtures").select("*").eq("league_id", settings.PREMIER_LEAGUE_ID).eq("season", settings.DEFAULT_SEASON).gte("date", today).lt("date", f"{today}T23:59:59").execute()
        
        return {
            "date": today,
            "fixtures": fixtures_result.data,
            "fixture_count": len(fixtures_result.data),
            "source": "supabase_cache"
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"get_todays_fixtures error: {str(e)}"})

if __name__ == "__main__":
    print(f"Starting Premier League Server on port 5000")
    print(f"Premier League ID: {settings.PREMIER_LEAGUE_ID}")
    print(f"Current Season: {settings.DEFAULT_SEASON}")
    
    uvicorn.run(app, host="0.0.0.0", port=5000)
