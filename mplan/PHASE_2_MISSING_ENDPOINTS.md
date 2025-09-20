# Phase 2: Missing Endpoints Implementation Plan

## 🎯 **CURRENT STATUS RECAP**

### ✅ **COMPLETED (90% of system):**
- **HTTP API**: `https://api.stats.scorers.app` (live)
- **MCP Server**: Enhanced `soccer_server.py` with @mcp.tool() decorators
- **Database**: Supabase with 2025 Premier League data
- **Caching**: 90%+ faster responses, zero API calls
- **Core Endpoints**: Fixtures, current gameweek, today's matches
- **Missing Endpoints**: Lineups, goalscorers, probable scorers (implemented but need data)

### ❌ **MISSING FOR SPORTS APP:**
- **Squads/Rosters**: Team player lists
- **H2H (Head-to-Head)**: Historical matchups between teams
- **Last 5**: Recent team form/results
- **Enhanced Standings**: With form, recent results
- **Player Statistics**: Individual player stats

## 📊 **API FOOTBALL ENDPOINTS TO IMPLEMENT**

Based on API Football v3 documentation ([api-football.com](https://www.api-football.com/documentation-v3)):

### **1. Team Squads/Players**
```
Endpoint: /players
Parameters: team={team_id}, season={season}
Purpose: Get all players in a team's squad
Usage: "Show me Arsenal's current squad"
```

### **2. Head-to-Head Records**
```
Endpoint: /fixtures/headtohead
Parameters: h2h={team1_id}-{team2_id}
Purpose: Historical matchups between two teams
Usage: "Arsenal vs Chelsea head-to-head record"
```

### **3. Team Statistics/Form**
```
Endpoint: /teams/statistics
Parameters: league={league_id}, season={season}, team={team_id}
Purpose: Team performance stats, form, home/away records
Usage: "Liverpool's last 5 results and form"
```

### **4. Enhanced Player Statistics**
```
Endpoint: /players
Parameters: league={league_id}, season={season}, team={team_id}
Purpose: Detailed player stats for season
Usage: "Top scorers, assists, cards, etc."
```

### **5. Enhanced Standings with Form**
```
Endpoint: /standings
Enhancement: Add recent form analysis
Purpose: League table with recent form indicators
Usage: "Premier League table with last 5 games form"
```

## 🏗️ **IMPLEMENTATION PLAN**

### **Phase 2A: Database Schema Extensions**

#### **New Tables:**
```sql
-- Team squads/rosters
CREATE TABLE team_squads (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    season INTEGER,
    position VARCHAR(50),
    jersey_number INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, player_id, season)
);

-- Head-to-head records
CREATE TABLE head_to_head (
    id SERIAL PRIMARY KEY,
    team1_id INTEGER REFERENCES teams(id),
    team2_id INTEGER REFERENCES teams(id),
    total_matches INTEGER,
    team1_wins INTEGER,
    team2_wins INTEGER,
    draws INTEGER,
    last_match_id INTEGER REFERENCES fixtures(id),
    last_match_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team1_id, team2_id)
);

-- Team form/statistics
CREATE TABLE team_statistics (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    league_id INTEGER REFERENCES leagues(id),
    season INTEGER,
    matches_played INTEGER,
    wins INTEGER,
    draws INTEGER,
    losses INTEGER,
    goals_for INTEGER,
    goals_against INTEGER,
    clean_sheets INTEGER,
    form VARCHAR(10), -- "WWDLL" format
    last_5_results JSONB, -- Array of last 5 match results
    home_record JSONB, -- Home statistics
    away_record JSONB, -- Away statistics
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, league_id, season)
);

-- Enhanced player statistics
CREATE TABLE enhanced_player_statistics (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id),
    team_id INTEGER REFERENCES teams(id),
    league_id INTEGER REFERENCES leagues(id),
    season INTEGER,
    -- Current season stats
    current_goals INTEGER,
    current_assists INTEGER,
    current_appearances INTEGER,
    current_minutes INTEGER,
    -- Form indicators
    last_5_goals INTEGER,
    last_5_assists INTEGER,
    last_5_appearances INTEGER,
    recent_form VARCHAR(10), -- "GAGA-" (G=Goal, A=Assist, -=No contribution)
    -- Performance metrics
    goals_per_game DECIMAL(3,2),
    assists_per_game DECIMAL(3,2),
    minutes_per_goal DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(player_id, team_id, league_id, season)
);

-- Indexes
CREATE INDEX idx_team_squads_team_season ON team_squads(team_id, season);
CREATE INDEX idx_h2h_teams ON head_to_head(team1_id, team2_id);
CREATE INDEX idx_team_stats_team_season ON team_statistics(team_id, season);
CREATE INDEX idx_enhanced_player_stats ON enhanced_player_statistics(player_id, season);
```

### **Phase 2B: Enhanced Scrapers**

#### **1. Squad Scraper**
```python
# src/scrapers/squad_scraper.py
class SquadScraper(BaseScraper):
    def scrape_team_squad(self, team_id: int, season: int = None):
        """Scrape team squad/roster"""
        season = season or self.current_season
        
        response = self.make_api_request(
            "players",
            {"team": team_id, "season": season},
            priority="medium"
        )
        
        # Process and store squad data
        return self._process_and_store_squad(team_id, season, response)
    
    def get_squad_for_all_teams(self, season: int = None):
        """Get squads for all Premier League teams"""
        teams = self.get_premier_league_teams()
        
        for team in teams:
            self.scrape_team_squad(team["id"], season)
```

#### **2. Head-to-Head Scraper**
```python
# src/scrapers/h2h_scraper.py
class HeadToHeadScraper(BaseScraper):
    def scrape_h2h_record(self, team1_id: int, team2_id: int):
        """Scrape head-to-head record between two teams"""
        
        response = self.make_api_request(
            "fixtures/headtohead",
            {"h2h": f"{team1_id}-{team2_id}"},
            priority="low"
        )
        
        return self._process_and_store_h2h(team1_id, team2_id, response)
    
    def generate_all_h2h_records(self):
        """Generate H2H records for all Premier League team combinations"""
        teams = self.get_premier_league_teams()
        
        for i, team1 in enumerate(teams):
            for team2 in teams[i+1:]:  # Avoid duplicates
                self.scrape_h2h_record(team1["id"], team2["id"])
```

#### **3. Team Statistics Scraper**
```python
# src/scrapers/team_stats_scraper.py
class TeamStatisticsScraper(BaseScraper):
    def scrape_team_statistics(self, team_id: int, season: int = None):
        """Scrape comprehensive team statistics"""
        season = season or self.current_season
        
        response = self.make_api_request(
            "teams/statistics",
            {"league": self.premier_league_id, "season": season, "team": team_id},
            priority="medium"
        )
        
        return self._process_and_store_team_stats(team_id, season, response)
    
    def calculate_last_5_form(self, team_id: int, season: int):
        """Calculate last 5 matches form from fixtures"""
        # Get last 5 completed fixtures for team
        fixtures = db.table("fixtures").select("*").eq("league_id", self.premier_league_id).eq("season", season).or_(f"home_team_id.eq.{team_id},away_team_id.eq.{team_id}").eq("status_short", "FT").order("date", desc=True).limit(5).execute()
        
        form = ""
        for fixture in fixtures.data:
            if fixture["home_team_id"] == team_id:
                # Home team
                home_score = fixture["home_score"]
                away_score = fixture["away_score"]
                if home_score > away_score:
                    form += "W"
                elif home_score < away_score:
                    form += "L"
                else:
                    form += "D"
            else:
                # Away team
                home_score = fixture["home_score"]
                away_score = fixture["away_score"]
                if away_score > home_score:
                    form += "W"
                elif away_score < home_score:
                    form += "L"
                else:
                    form += "D"
        
        return form
```

### **Phase 2C: New MCP Tools**

#### **Squad/Roster Tools:**
```python
@mcp.tool()
def get_team_squad(team_name: str, season: int = None) -> Dict[str, Any]:
    """Get team's current squad/roster"""

@mcp.tool()
def get_player_info_detailed(player_name: str) -> Dict[str, Any]:
    """Get detailed player information and current team"""
```

#### **Head-to-Head Tools:**
```python
@mcp.tool()
def get_head_to_head(team1_name: str, team2_name: str) -> Dict[str, Any]:
    """Get head-to-head record between two teams"""

@mcp.tool()
def get_recent_h2h_fixtures(team1_name: str, team2_name: str, limit: int = 5) -> Dict[str, Any]:
    """Get recent fixtures between two teams"""
```

#### **Form/Statistics Tools:**
```python
@mcp.tool()
def get_team_last_5_results(team_name: str) -> Dict[str, Any]:
    """Get team's last 5 match results and form"""

@mcp.tool()
def get_team_statistics_detailed(team_name: str, season: int = None) -> Dict[str, Any]:
    """Get comprehensive team statistics"""

@mcp.tool()
def get_premier_league_form_table() -> Dict[str, Any]:
    """Get Premier League table with last 5 games form"""
```

### **Phase 2D: Enhanced HTTP API Endpoints**

```python
# Add to standalone_server.py or hybrid_server.py

@app.get("/api/team/{team_name}/squad")
async def get_team_squad_api(team_name: str, season: int = None):
    """HTTP endpoint for team squad"""

@app.get("/api/teams/{team1_name}/vs/{team2_name}/h2h")
async def get_h2h_api(team1_name: str, team2_name: str):
    """HTTP endpoint for head-to-head"""

@app.get("/api/team/{team_name}/last5")
async def get_team_last5_api(team_name: str):
    """HTTP endpoint for team's last 5 results"""

@app.get("/api/team/{team_name}/statistics")
async def get_team_stats_api(team_name: str, season: int = None):
    """HTTP endpoint for team statistics"""

@app.get("/api/standings/form")
async def get_standings_with_form_api():
    """HTTP endpoint for standings with form"""
```

### **Phase 2E: Scheduled Data Collection**

#### **Daily/Weekly Scraping Schedule:**
```python
# Update scraper_manager.py

PHASE_2_SCHEDULE = {
    'squads': {
        'frequency': 'weekly',  # Squad changes are rare
        'priority': 'low',
        'estimated_requests': 20,  # 20 teams
        'endpoint': 'players?team={team_id}&season={season}'
    },
    'team_statistics': {
        'frequency': 'daily',  # Updated after matches
        'priority': 'medium', 
        'estimated_requests': 20,  # 20 teams
        'endpoint': 'teams/statistics?league=39&season={season}&team={team_id}'
    },
    'h2h_records': {
        'frequency': 'monthly',  # Historical data, changes slowly
        'priority': 'low',
        'estimated_requests': 190,  # 20*19/2 = 190 combinations
        'endpoint': 'fixtures/headtohead?h2h={team1_id}-{team2_id}'
    }
}
```

### **Phase 2F: Request Budget Allocation**

#### **Updated 1,000 Request/Day Budget:**
```
Current Usage:
- Fixtures: 50 requests/day
- Live data: 200 requests/day
- Lineups: 100 requests/day

New Additions:
- Squads: 20 requests/week (3/day)
- Team stats: 20 requests/day  
- H2H: 190 requests/month (6/day)

Total: 379 requests/day
Buffer: 621 requests/day (62% safety margin)
```

## 🚀 **IMPLEMENTATION TIMELINE**

### **Week 1: Database & Core Scrapers**
- [ ] Extend database schema with new tables
- [ ] Implement SquadScraper class
- [ ] Implement TeamStatisticsScraper class
- [ ] Implement HeadToHeadScraper class

### **Week 2: MCP Tools Integration**
- [ ] Add squad-related MCP tools
- [ ] Add H2H MCP tools  
- [ ] Add team statistics MCP tools
- [ ] Add form analysis MCP tools

### **Week 3: HTTP API Extensions**
- [ ] Add squad HTTP endpoints
- [ ] Add H2H HTTP endpoints
- [ ] Add team statistics HTTP endpoints
- [ ] Add enhanced standings endpoint

### **Week 4: Data Population & Testing**
- [ ] Scrape all Premier League squads
- [ ] Generate all H2H records
- [ ] Calculate team statistics and form
- [ ] Test all new endpoints

## 🎯 **EXPECTED ENDPOINTS AFTER PHASE 2**

### **For Sports App:**
```bash
# Squads
GET /api/team/Arsenal/squad
GET /api/team/Arsenal/players

# Head-to-Head
GET /api/teams/Arsenal/vs/Chelsea/h2h
GET /api/teams/Arsenal/vs/Chelsea/recent

# Team Form
GET /api/team/Arsenal/last5
GET /api/team/Arsenal/statistics
GET /api/standings/form

# Enhanced existing
GET /api/team/Arsenal/fixtures/upcoming
GET /api/gameweek/4/fixtures
```

### **For Social Media Agent (MCP):**
```python
get_team_squad("Arsenal")                    # Squad info
get_head_to_head("Arsenal", "Chelsea")       # H2H record
get_team_last_5_results("Arsenal")           # Recent form
get_team_statistics_detailed("Arsenal")      # Full stats
get_premier_league_form_table()              # Table with form
```

## 📋 **IMMEDIATE NEXT STEPS**

### **Option 1: Quick Implementation (1-2 days)**
Focus on most valuable endpoints:
1. **Team squads** (for lineup context)
2. **Last 5 results** (for form analysis)
3. **Enhanced standings** (with form)

### **Option 2: Complete Implementation (1 week)**
Full implementation of all missing endpoints with comprehensive data.

### **Option 3: Incremental (As needed)**
Add endpoints based on sports app requirements.

## 🎯 **RECOMMENDATION**

**Start with Option 1** - Quick implementation of high-value endpoints:
- Team squads (20 requests for all teams)
- Last 5 form calculation (from existing fixture data)
- Enhanced standings with form

**This gives you 80% of sports app functionality with minimal API usage.**

**Ready to implement Phase 2?**
