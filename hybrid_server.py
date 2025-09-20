#!/usr/bin/env python3
"""
Hybrid MCP + HTTP Server
Exposes the same functions via BOTH MCP protocol AND HTTP API
"""

import time
import signal
import sys
import os
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import get_settings
from database.connection import get_db_client

print(f"Current working directory: {os.getcwd()}", file=sys.stderr)

# Initialize components
settings = get_settings()
db = get_db_client()

# Handle SIGINT (Ctrl+C) gracefully
def signal_handler(sig, frame):
    print("Shutting down hybrid server gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ================================
# SHARED FUNCTIONS (Used by both MCP and HTTP)
# ================================

def _get_current_gameweek(season: int = None) -> Dict[str, Any]:
    """Shared function for current gameweek"""
    try:
        season = season or settings.DEFAULT_SEASON
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
        return {"error": f"get_current_gameweek error: {str(e)}"}

def _get_gameweek_fixtures(season: int, gameweek: int) -> Dict[str, Any]:
    """Shared function for gameweek fixtures"""
    try:
        if not (1 <= gameweek <= 38):
            return {"error": "Gameweek must be between 1 and 38"}
        
        fixtures = db.table("fixtures").select("*").eq("league_id", settings.PREMIER_LEAGUE_ID).eq("season", season).eq("gameweek", gameweek).execute()
        
        return {
            "gameweek": gameweek,
            "season": season,
            "fixtures": fixtures.data,
            "fixture_count": len(fixtures.data),
            "source": "supabase_cache"
        }
        
    except Exception as e:
        return {"error": f"get_gameweek_fixtures error: {str(e)}"}

def _get_todays_fixtures() -> Dict[str, Any]:
    """Shared function for today's fixtures"""
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
        return {"error": f"get_todays_fixtures error: {str(e)}"}

def _get_league_fixtures(league_id: int, season: int) -> Dict[str, Any]:
    """Shared function for league fixtures"""
    try:
        # Use global settings for Premier League
        if league_id == settings.PREMIER_LEAGUE_ID:
            season = season or settings.DEFAULT_SEASON
        
        # Get from cache
        cached_fixtures = db.table("fixtures").select("*").eq("league_id", league_id).eq("season", season).execute()
        
        if cached_fixtures.data:
            print(f"Using cached fixtures: {len(cached_fixtures.data)} fixtures", file=sys.stderr)
            
            # Format to match original API response
            fixtures_list = []
            for fixture in cached_fixtures.data:
                fixtures_list.append({
                    "fixture": {
                        "id": fixture["id"],
                        "referee": fixture.get("referee"),
                        "timezone": fixture.get("timezone"),
                        "date": fixture.get("date"),
                        "timestamp": fixture.get("timestamp"),
                        "status": {
                            "long": fixture.get("status_long"),
                            "short": fixture.get("status_short"),
                            "elapsed": fixture.get("status_elapsed")
                        }
                    },
                    "league": {
                        "id": fixture["league_id"],
                        "season": fixture["season"],
                        "round": fixture.get("round")
                    },
                    "teams": {
                        "home": {"id": fixture["home_team_id"]},
                        "away": {"id": fixture["away_team_id"]}
                    },
                    "goals": {
                        "home": fixture.get("home_score"),
                        "away": fixture.get("away_score")
                    }
                })
            
            return {
                "response": fixtures_list,
                "source": "supabase_cache",
                "cached_fixtures": len(fixtures_list)
            }
        else:
            return {"error": "No cached fixtures found"}
            
    except Exception as e:
        return {"error": f"Enhanced get_league_fixtures error: {str(e)}"}

# ================================
# HTTP API SERVER
# ================================

app = FastAPI(title="Premier League Hybrid MCP+HTTP Server", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Premier League Hybrid MCP+HTTP Server", "status": "running", "season": settings.DEFAULT_SEASON, "protocols": ["MCP", "HTTP"]}

@app.get("/health")
async def health():
    try:
        result = db.table("request_mode_config").select("current_mode").limit(1).execute()
        return {"status": "healthy", "database": "connected", "mode": result.data[0]["current_mode"] if result.data else "unknown"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "unhealthy", "error": str(e)})

# HTTP API endpoints that call the same functions as MCP tools
@app.get("/api/current-gameweek")
async def http_get_current_gameweek(season: int = None):
    return _get_current_gameweek(season)

@app.get("/api/gameweek/{gameweek}/fixtures")
async def http_get_gameweek_fixtures(gameweek: int, season: int = None):
    season = season or settings.DEFAULT_SEASON
    return _get_gameweek_fixtures(season, gameweek)

@app.get("/api/todays-fixtures")
async def http_get_todays_fixtures():
    return _get_todays_fixtures()

@app.get("/api/league/{league_id}/fixtures")
async def http_get_league_fixtures(league_id: int, season: int = None):
    season = season or settings.DEFAULT_SEASON
    return _get_league_fixtures(league_id, season)

# ================================
# PHASE 2: NEW HTTP ENDPOINTS
# ================================

@app.get("/api/team/{team_name}/squad")
async def http_get_team_squad(team_name: str, season: int = None):
    """HTTP endpoint for team squad"""
    season = season or settings.DEFAULT_SEASON
    
    # Find team
    teams = db.table("teams").select("*").ilike("name", f"%{team_name}%").execute()
    if not teams.data:
        return JSONResponse(status_code=404, content={"error": f"No team found matching '{team_name}'"})
    
    team = teams.data[0]
    team_id = team["id"]
    
    # Get squad
    squad_data = db.table("team_squads").select("*, players(*)").eq("team_id", team_id).eq("season", season).eq("is_active", True).execute()
    
    return {
        "team": team,
        "season": season,
        "squad": squad_data.data,
        "squad_size": len(squad_data.data),
        "source": "supabase_cache"
    }

@app.get("/api/team/{team_name}/last5")
async def http_get_team_last5(team_name: str):
    """HTTP endpoint for team's last 5 results"""
    
    # Find team
    teams = db.table("teams").select("*").ilike("name", f"%{team_name}%").execute()
    if not teams.data:
        return JSONResponse(status_code=404, content={"error": f"No team found matching '{team_name}'"})
    
    team = teams.data[0]
    team_id = team["id"]
    
    # Get last 5 fixtures
    fixtures = db.table("fixtures").select("*").eq("league_id", settings.PREMIER_LEAGUE_ID).eq("season", settings.DEFAULT_SEASON).eq("status_short", "FT").or_(f"home_team_id.eq.{team_id},away_team_id.eq.{team_id}").order("date", desc=True).limit(5).execute()
    
    form = ""
    last_5_results = []
    
    for fixture in fixtures.data:
        is_home = fixture["home_team_id"] == team_id
        
        if is_home:
            team_score = fixture["home_score"]
            opponent_score = fixture["away_score"]
            opponent_id = fixture["away_team_id"]
        else:
            team_score = fixture["away_score"]
            opponent_score = fixture["home_score"]
            opponent_id = fixture["home_team_id"]
        
        if team_score is not None and opponent_score is not None:
            # Get opponent name
            opponent = db.table("teams").select("name").eq("id", opponent_id).execute()
            opponent_name = opponent.data[0]["name"] if opponent.data else "Unknown"
            
            # Determine result
            if team_score > opponent_score:
                result_char = "W"
                result_text = "Win"
            elif team_score < opponent_score:
                result_char = "L"
                result_text = "Loss"
            else:
                result_char = "D"
                result_text = "Draw"
            
            form += result_char
            
            last_5_results.append({
                "fixture_id": fixture["id"],
                "date": fixture["date"],
                "gameweek": fixture.get("gameweek"),
                "opponent": opponent_name,
                "is_home": is_home,
                "score": f"{team_score}-{opponent_score}",
                "result": result_text
            })
    
    return {
        "team": team,
        "form": form,
        "last_5_results": last_5_results,
        "source": "supabase_cache"
    }

@app.get("/api/teams/{team1_name}/vs/{team2_name}/h2h")
async def http_get_h2h(team1_name: str, team2_name: str, limit: int = 10):
    """HTTP endpoint for head-to-head record"""
    
    # Find both teams
    team1_result = db.table("teams").select("*").ilike("name", f"%{team1_name}%").execute()
    team2_result = db.table("teams").select("*").ilike("name", f"%{team2_name}%").execute()
    
    if not team1_result.data:
        return JSONResponse(status_code=404, content={"error": f"No team found matching '{team1_name}'"})
    if not team2_result.data:
        return JSONResponse(status_code=404, content={"error": f"No team found matching '{team2_name}'"})
    
    team1 = team1_result.data[0]
    team2 = team2_result.data[0]
    team1_id = team1["id"]
    team2_id = team2["id"]
    
    # Get fixtures between these teams
    fixtures = db.table("fixtures").select("*").eq("league_id", settings.PREMIER_LEAGUE_ID).or_(
        f"and(home_team_id.eq.{team1_id},away_team_id.eq.{team2_id}),and(home_team_id.eq.{team2_id},away_team_id.eq.{team1_id})"
    ).order("date", desc=True).limit(limit).execute()
    
    # Calculate H2H stats
    total_matches = 0
    team1_wins = 0
    team2_wins = 0
    draws = 0
    recent_fixtures = []
    
    for fixture in fixtures.data:
        if fixture["home_score"] is not None and fixture["away_score"] is not None:
            total_matches += 1
            home_score = fixture["home_score"]
            away_score = fixture["away_score"]
            
            if fixture["home_team_id"] == team1_id:
                if home_score > away_score:
                    team1_wins += 1
                elif home_score < away_score:
                    team2_wins += 1
                else:
                    draws += 1
            else:
                if home_score > away_score:
                    team2_wins += 1
                elif home_score < away_score:
                    team1_wins += 1
                else:
                    draws += 1
        
        recent_fixtures.append({
            "fixture_id": fixture["id"],
            "date": fixture["date"],
            "gameweek": fixture.get("gameweek"),
            "home_team": team1["name"] if fixture["home_team_id"] == team1_id else team2["name"],
            "away_team": team2["name"] if fixture["away_team_id"] == team2_id else team1["name"],
            "home_score": fixture["home_score"],
            "away_score": fixture["away_score"],
            "status": fixture["status_short"]
        })
    
    return {
        "team1": team1,
        "team2": team2,
        "h2h_summary": {
            "total_matches": total_matches,
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "draws": draws
        },
        "recent_fixtures": recent_fixtures,
        "source": "supabase_cache"
    }

@app.get("/api/standings/form")
async def http_get_standings_with_form(season: int = None):
    """HTTP endpoint for standings with form"""
    season = season or settings.DEFAULT_SEASON
    
    # Get standings
    standings = db.table("standings").select("*").eq("league_id", settings.PREMIER_LEAGUE_ID).eq("season", season).order("rank").execute()
    
    enhanced_standings = []
    
    for standing in standings.data:
        team_id = standing["team_id"]
        
        # Get team name
        team_info = db.table("teams").select("name").eq("id", team_id).execute()
        team_name = team_info.data[0]["name"] if team_info.data else "Unknown"
        
        # Calculate form
        last_5_fixtures = db.table("fixtures").select("*").eq("league_id", settings.PREMIER_LEAGUE_ID).eq("season", season).eq("status_short", "FT").or_(f"home_team_id.eq.{team_id},away_team_id.eq.{team_id}").order("date", desc=True).limit(5).execute()
        
        form = ""
        for fixture in last_5_fixtures.data:
            is_home = fixture["home_team_id"] == team_id
            team_score = fixture["home_score"] if is_home else fixture["away_score"]
            opponent_score = fixture["away_score"] if is_home else fixture["home_score"]
            
            if team_score is not None and opponent_score is not None:
                if team_score > opponent_score:
                    form += "W"
                elif team_score < opponent_score:
                    form += "L"
                else:
                    form += "D"
        
        enhanced_standing = standing.copy()
        enhanced_standing["team_name"] = team_name
        enhanced_standing["form"] = form
        enhanced_standings.append(enhanced_standing)
    
    return {
        "season": season,
        "league_name": "Premier League",
        "standings_with_form": enhanced_standings,
        "source": "supabase_cache"
    }

# ================================
# MCP TOOLS (Same functions, MCP protocol)
# ================================

# We'll need to add the MCP decorators when we have the right package
# For now, let's create the functions that will be MCP tools

def mcp_get_current_gameweek(season: int = None) -> Dict[str, Any]:
    """MCP tool for current gameweek"""
    return _get_current_gameweek(season)

def mcp_get_gameweek_fixtures(season: int, gameweek: int) -> Dict[str, Any]:
    """MCP tool for gameweek fixtures"""
    return _get_gameweek_fixtures(season, gameweek)

def mcp_get_todays_fixtures() -> Dict[str, Any]:
    """MCP tool for today's fixtures"""
    return _get_todays_fixtures()

def mcp_get_league_fixtures(league_id: int, season: int) -> Dict[str, Any]:
    """MCP tool for league fixtures"""
    return _get_league_fixtures(league_id, season)

# ================================
# SERVER STARTUP
# ================================

def start_http_server():
    """Start the HTTP API server"""
    print(f"Starting HTTP API server on port 5000")
    uvicorn.run(app, host="0.0.0.0", port=5000)

def start_mcp_server():
    """Start the MCP server (when we have the right package)"""
    # This will be enabled when we have FastMCP working
    print("MCP server would start here (needs FastMCP package)")
    pass

if __name__ == "__main__":
    try:
        print("Starting Hybrid MCP+HTTP Server...")
        print(f"Premier League ID: {settings.PREMIER_LEAGUE_ID}")
        print(f"Current Season: {settings.DEFAULT_SEASON}")
        print()
        
        # For now, just start HTTP server
        # When MCP package is fixed, we'll run both in threads
        start_http_server()
        
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
