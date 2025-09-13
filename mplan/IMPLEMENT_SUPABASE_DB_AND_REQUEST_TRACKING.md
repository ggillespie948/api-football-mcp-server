# Implementation Plan: Supabase Database and Request Tracking for Soccer MCP Server

## Executive Summary

Transform the existing soccer MCP server from a direct API-calling service to a hybrid MCP/API server with intelligent data caching using Supabase. This implementation will optimize API usage within the 7,500 daily request limit while providing faster response times through cached data.

## Current State Analysis

### Existing Tools in soccer_server.py
1. **League Operations**: `get_league_fixtures`, `get_league_id_by_name`, `get_all_leagues_id`, `get_standings`, `get_league_info`, `get_league_schedule_by_date`
2. **Player Operations**: `get_player_id`, `get_player_profile`, `get_player_statistics`, `get_player_statistics_2`
3. **Team Operations**: `get_team_fixtures`, `get_team_info`, `get_team_fixtures_by_date_range`
4. **Match Operations**: `get_fixture_statistics`, `get_fixture_events`, `get_multiple_fixtures_stats`
5. **Live Operations**: `get_live_match_for_team`, `get_live_stats_for_team`, `get_live_match_timeline`

### Missing Critical Endpoints (TO BE IMPLEMENTED)
6. **Probable Scorers**: Player predictions/odds for scoring in upcoming matches
7. **Lineups**: Team lineups for fixtures (starting XI, substitutes, formation)
8. **Goal Scorers**: Detailed goal scorer information per fixture
9. **Current Gameweek**: Dynamic gameweek detection for Premier League

### API Endpoints Used (Current + Missing)
- `/leagues` - League information and search
- `/fixtures` - Match fixtures and schedules
- `/standings` - League standings
- `/players` - Player statistics and profiles
- `/players/profiles` - Player search
- `/teams` - Team information
- `/fixtures/statistics` - Match statistics
- `/fixtures/events` - Match events and timeline
- **`/predictions` - Probable scorers and match predictions** *(MISSING)*
- **`/fixtures/lineups` - Team lineups for matches** *(MISSING)*
- **`/fixtures/players` - Goal scorers per fixture** *(MISSING)*

## Implementation Strategy

### Phase 1: Database Schema Design and Setup

#### 1.1 Supabase Project Setup
```sql
-- Core Tables
CREATE TABLE leagues (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    logo VARCHAR(500),
    flag VARCHAR(500),
    season INTEGER,
    start_date DATE,
    end_date DATE,
    current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(10),
    country VARCHAR(100),
    founded INTEGER,
    logo VARCHAR(500),
    venue_id INTEGER,
    venue_name VARCHAR(255),
    venue_capacity INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE players (
    id INTEGER PRIMARY KEY,
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    age INTEGER,
    birth_date DATE,
    birth_place VARCHAR(255),
    birth_country VARCHAR(100),
    nationality VARCHAR(100),
    height VARCHAR(10),
    weight VARCHAR(10),
    photo VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fixtures (
    id INTEGER PRIMARY KEY,
    referee VARCHAR(255),
    timezone VARCHAR(50),
    date TIMESTAMP,
    timestamp BIGINT,
    league_id INTEGER REFERENCES leagues(id),
    season INTEGER,
    round VARCHAR(100),
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    home_score INTEGER,
    away_score INTEGER,
    status_long VARCHAR(50),
    status_short VARCHAR(10),
    status_elapsed INTEGER,
    venue_id INTEGER,
    venue_name VARCHAR(255),
    venue_city VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE standings (
    id SERIAL PRIMARY KEY,
    league_id INTEGER REFERENCES leagues(id),
    season INTEGER,
    team_id INTEGER REFERENCES teams(id),
    rank INTEGER,
    points INTEGER,
    goals_diff INTEGER,
    group_name VARCHAR(10),
    form VARCHAR(10),
    status VARCHAR(50),
    description VARCHAR(255),
    played INTEGER,
    win INTEGER,
    draw INTEGER,
    lose INTEGER,
    goals_for INTEGER,
    goals_against INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(league_id, season, team_id)
);

CREATE TABLE player_statistics (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id),
    team_id INTEGER REFERENCES teams(id),
    league_id INTEGER REFERENCES leagues(id),
    season INTEGER,
    appearances INTEGER,
    lineups INTEGER,
    minutes INTEGER,
    position VARCHAR(50),
    rating DECIMAL(3,2),
    goals_total INTEGER,
    goals_assists INTEGER,
    goals_saves INTEGER,
    shots_total INTEGER,
    shots_on INTEGER,
    passes_total INTEGER,
    passes_key INTEGER,
    passes_accuracy INTEGER,
    tackles_total INTEGER,
    blocks INTEGER,
    interceptions INTEGER,
    duels_total INTEGER,
    duels_won INTEGER,
    dribbles_attempts INTEGER,
    dribbles_success INTEGER,
    fouls_drawn INTEGER,
    fouls_committed INTEGER,
    cards_yellow INTEGER,
    cards_red INTEGER,
    penalty_won INTEGER,
    penalty_committed INTEGER,
    penalty_scored INTEGER,
    penalty_missed INTEGER,
    penalty_saved INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(player_id, team_id, league_id, season)
);

CREATE TABLE fixture_statistics (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER REFERENCES fixtures(id),
    team_id INTEGER REFERENCES teams(id),
    shots_on_goal INTEGER,
    shots_off_goal INTEGER,
    total_shots INTEGER,
    blocked_shots INTEGER,
    shots_inside_box INTEGER,
    shots_outside_box INTEGER,
    fouls INTEGER,
    corner_kicks INTEGER,
    offside INTEGER,
    ball_possession INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,
    goalkeeper_saves INTEGER,
    total_passes INTEGER,
    passes_accurate INTEGER,
    passes_percentage INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fixture_id, team_id)
);

CREATE TABLE fixture_events (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER REFERENCES fixtures(id),
    time_elapsed INTEGER,
    time_extra INTEGER,
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    assist_id INTEGER REFERENCES players(id),
    type VARCHAR(50),
    detail VARCHAR(100),
    comments TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- NEW TABLES FOR MISSING ENDPOINTS
CREATE TABLE fixture_lineups (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER REFERENCES fixtures(id),
    team_id INTEGER REFERENCES teams(id),
    formation VARCHAR(10),
    coach_id INTEGER,
    coach_name VARCHAR(255),
    coach_photo VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fixture_id, team_id)
);

CREATE TABLE lineup_players (
    id SERIAL PRIMARY KEY,
    lineup_id INTEGER REFERENCES fixture_lineups(id),
    player_id INTEGER REFERENCES players(id),
    player_name VARCHAR(255),
    player_number INTEGER,
    player_pos VARCHAR(10),
    grid VARCHAR(10),
    is_starter BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fixture_goalscorers (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER REFERENCES fixtures(id),
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    assist_player_id INTEGER REFERENCES players(id),
    time_elapsed INTEGER,
    time_extra INTEGER,
    goal_type VARCHAR(50), -- 'Normal Goal', 'Own Goal', 'Penalty', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE probable_scorers (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER REFERENCES fixtures(id),
    player_id INTEGER REFERENCES players(id),
    team_id INTEGER REFERENCES teams(id),
    probability DECIMAL(5,2), -- Percentage probability
    odds DECIMAL(10,2), -- Betting odds if available
    last_5_goals INTEGER, -- Goals in last 5 matches
    last_5_assists INTEGER, -- Assists in last 5 matches
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fixture_id, player_id)
);

CREATE TABLE premier_league_gameweeks (
    id SERIAL PRIMARY KEY,
    season INTEGER NOT NULL,
    gameweek INTEGER NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_current BOOLEAN DEFAULT false,
    is_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(season, gameweek)
);

-- Tracking and Metadata Tables
CREATE TABLE api_request_log (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255),
    params JSONB,
    response_size INTEGER,
    status_code INTEGER,
    error_message TEXT,
    request_timestamp TIMESTAMP DEFAULT NOW(),
    daily_count INTEGER DEFAULT 1 -- Track requests per day
);

-- Daily request counter for rate limiting
CREATE TABLE daily_request_counter (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE DEFAULT CURRENT_DATE,
    request_count INTEGER DEFAULT 0,
    last_reset TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Request mode configuration
CREATE TABLE request_mode_config (
    id SERIAL PRIMARY KEY,
    current_mode VARCHAR(20) DEFAULT 'standard',
    daily_budget INTEGER DEFAULT 3000,
    auto_adjust_enabled BOOLEAN DEFAULT true,
    last_mode_change TIMESTAMP DEFAULT NOW(),
    reason_for_change VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default configuration
INSERT INTO request_mode_config (current_mode, daily_budget, auto_adjust_enabled) 
VALUES ('standard', 3000, true);

CREATE TABLE data_sync_status (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(100), -- 'leagues', 'fixtures', 'standings', etc.
    league_id INTEGER,
    season INTEGER,
    last_sync TIMESTAMP,
    sync_frequency_hours INTEGER,
    next_sync TIMESTAMP,
    status VARCHAR(50), -- 'success', 'error', 'pending'
    error_details TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_fixtures_league_season ON fixtures(league_id, season);
CREATE INDEX idx_fixtures_date ON fixtures(date);
CREATE INDEX idx_fixtures_teams ON fixtures(home_team_id, away_team_id);
CREATE INDEX idx_standings_league_season ON standings(league_id, season);
CREATE INDEX idx_player_stats_player_season ON player_statistics(player_id, season);
CREATE INDEX idx_api_requests_created ON api_request_log(created_at);
CREATE INDEX idx_sync_status_next_sync ON data_sync_status(next_sync);
```

#### 1.2 Row Level Security (RLS) Setup
```sql
-- Enable RLS
ALTER TABLE leagues ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixtures ENABLE ROW LEVEL SECURITY;
ALTER TABLE standings ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixture_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixture_events ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your authentication needs)
CREATE POLICY "Allow read access" ON leagues FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON teams FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON players FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON fixtures FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON standings FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON player_statistics FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON fixture_statistics FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON fixture_events FOR SELECT USING (true);
```

### Phase 2: Data Scraping Strategy

#### 2.1 API Rate Limit Management - PREMIER LEAGUE FOCUSED (1K DAILY LIMIT)
- **Daily Limit**: 1,000 requests (shared with other app)
- **Premier League Only Distribution**:
  - Static Data (Teams): 7 requests/week (1 per day)
  - Fixtures: 14 requests/day (twice daily updates)
  - Live Data: 200 requests/day (during match days only, 5-10 concurrent matches max)
  - Lineups: 100 requests/day (10 fixtures × 2 teams × 5 times per day)
  - Goal Scorers: 50 requests/day (post-match updates)
  - Probable Scorers: 50 requests/day (pre-match predictions)
  - Standings: 7 requests/week (once daily)
  - Current Gameweek: 7 requests/week (cached heavily)
  - Buffer/Error Recovery: 565 requests/day (56% buffer for retries)

**CRITICAL: Request Tracking Implementation**

Every API request MUST be tracked in real-time to ensure we never exceed 1,000 requests per day:

```python
class RequestTracker:
    def __init__(self, supabase_client):
        self.db = supabase_client
    
    def can_make_request(self) -> bool:
        """Check if we can make another request today"""
        today = datetime.now().date()
        
        # Get today's count
        result = self.db.table("daily_request_counter").select("request_count").eq("date", today).execute()
        
        if not result.data:
            # First request of the day
            self.db.table("daily_request_counter").insert({"date": today, "request_count": 0}).execute()
            return True
        
        current_count = result.data[0]["request_count"]
        return current_count < 1000  # Hard limit
    
    def record_request(self, endpoint: str, params: dict, status_code: int, error: str = None):
        """Record a request and increment daily counter"""
        today = datetime.now().date()
        
        # Log the request
        self.db.table("api_request_log").insert({
            "endpoint": endpoint,
            "params": params,
            "status_code": status_code,
            "error_message": error,
            "request_timestamp": datetime.now().isoformat()
        }).execute()
        
        # Increment daily counter
        self.db.table("daily_request_counter").update({
            "request_count": "request_count + 1"
        }).eq("date", today).execute()
    
    def get_remaining_requests(self) -> int:
        """Get remaining requests for today"""
        today = datetime.now().date()
        result = self.db.table("daily_request_counter").select("request_count").eq("date", today).execute()
        
        if not result.data:
            return 7500
        
        return 7500 - result.data[0]["request_count"]
```

#### 2.2 Configurable Request Mode System

```python
from enum import Enum
from typing import Dict, Any

class RequestMode(Enum):
    MINIMAL = "minimal"        # ~500 requests/day - Basic data only
    LOW = "low"               # ~1,500 requests/day - Essential data
    STANDARD = "standard"     # ~3,000 requests/day - Full coverage
    HIGH = "high"             # ~5,000 requests/day - High frequency updates
    MAXIMUM = "maximum"       # ~7,000 requests/day - Real-time updates

class ScalableScheduleManager:
    """Manages different request cadence modes"""
    
    PREMIER_LEAGUE_ID = 39
    
    def __init__(self, mode: RequestMode = RequestMode.STANDARD):
        self.mode = mode
        self.schedules = self._build_mode_schedules()
    
    def _build_mode_schedules(self) -> Dict[RequestMode, Dict[str, Any]]:
        """Build different schedule configurations for each mode"""
        
        return {
            RequestMode.MINIMAL: {
                'daily_budget': 500,
                'description': 'Basic fixtures and standings only',
                'schedules': {
                    'teams': {
                        'frequency': 'monthly',  # Once per month
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': '/teams?league=39&season=2024'
                    },
                    'fixtures': {
                        'frequency': 'daily',  # Once per day
                        'priority': 'high',
                        'estimated_requests': 1,
                        'endpoint': '/fixtures?league=39&season=2024'
                    },
                    'standings': {
                        'frequency': 'daily',  # Once per day
                        'priority': 'medium',
                        'estimated_requests': 1,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'daily',  # Once per day
                        'priority': 'high',
                        'estimated_requests': 1,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    # NO lineups, goalscorers, probable_scorers, or live updates
                }
            },
            
            RequestMode.LOW: {
                'daily_budget': 1500,
                'description': 'Essential data with basic match updates',
                'schedules': {
                    'teams': {
                        'frequency': 'weekly',
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': '/teams?league=39&season=2024'
                    },
                    'fixtures': {
                        'frequency': 'twice_daily',  # Morning and evening
                        'priority': 'high',
                        'estimated_requests': 2,
                        'endpoint': '/fixtures?league=39&season=2024'
                    },
                    'standings': {
                        'frequency': 'daily',
                        'priority': 'medium',
                        'estimated_requests': 1,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'every_6_hours',  # 4 times per day
                        'priority': 'high',
                        'estimated_requests': 4,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    'goalscorers': {
                        'frequency': 'post_match_only',  # After matches end
                        'priority': 'medium',
                        'estimated_requests': 20,  # 10 matches × 2 checks
                        'endpoint': '/fixtures/players?fixture={fixture_id}'
                    },
                    # NO lineups, probable_scorers, or live updates
                }
            },
            
            RequestMode.STANDARD: {
                'daily_budget': 3000,
                'description': 'Full coverage with moderate update frequency',
                'schedules': {
                    'teams': {
                        'frequency': 'weekly',
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': '/teams?league=39&season=2024'
                    },
                    'fixtures': {
                        'frequency': 'twice_daily',
                        'priority': 'high',
                        'estimated_requests': 2,
                        'endpoint': '/fixtures?league=39&season=2024'
                    },
                    'standings': {
                        'frequency': 'daily',
                        'priority': 'medium',
                        'estimated_requests': 1,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'every_3_hours',  # 8 times per day
                        'priority': 'high',
                        'estimated_requests': 8,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    'lineups': {
                        'frequency': 'match_day_limited',  # 2 hours before + 2 updates
                        'priority': 'high',
                        'estimated_requests': 60,  # 10 fixtures × 2 teams × 3 checks
                        'endpoint': '/fixtures/lineups?fixture={fixture_id}'
                    },
                    'goalscorers': {
                        'frequency': 'post_match',
                        'priority': 'high',
                        'estimated_requests': 50,  # 10 matches × 5 checks
                        'endpoint': '/fixtures/players?fixture={fixture_id}'
                    },
                    'probable_scorers': {
                        'frequency': 'pre_match_daily',  # Once per day before match
                        'priority': 'medium',
                        'estimated_requests': 20,  # 10 fixtures × 2 updates
                        'endpoint': '/predictions?fixture={fixture_id}'
                    },
                    # NO live updates
                }
            },
            
            RequestMode.HIGH: {
                'daily_budget': 5000,
                'description': 'High frequency updates with live match tracking',
                'schedules': {
                    'teams': {
                        'frequency': 'weekly',
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': '/teams?league=39&season=2024'
                    },
                    'fixtures': {
                        'frequency': 'three_times_daily',
                        'priority': 'high',
                        'estimated_requests': 3,
                        'endpoint': '/fixtures?league=39&season=2024'
                    },
                    'standings': {
                        'frequency': 'twice_daily',
                        'priority': 'medium',
                        'estimated_requests': 2,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'hourly',
                        'priority': 'high',
                        'estimated_requests': 24,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    'lineups': {
                        'frequency': 'match_day_frequent',  # Multiple updates
                        'priority': 'highest',
                        'estimated_requests': 120,  # 10 fixtures × 2 teams × 6 checks
                        'endpoint': '/fixtures/lineups?fixture={fixture_id}'
                    },
                    'goalscorers': {
                        'frequency': 'during_and_post_match',
                        'priority': 'high',
                        'estimated_requests': 80,  # 10 matches × 8 checks
                        'endpoint': '/fixtures/players?fixture={fixture_id}'
                    },
                    'probable_scorers': {
                        'frequency': 'pre_match_frequent',
                        'priority': 'medium',
                        'estimated_requests': 40,  # 10 fixtures × 4 updates
                        'endpoint': '/predictions?fixture={fixture_id}'
                    },
                    'live_fixtures': {
                        'frequency': 'every_5_minutes',  # During match windows
                        'priority': 'highest',
                        'estimated_requests': 500,  # Match days only
                        'active_hours': '12:00-22:00',
                        'endpoint': '/fixtures?live=all&league=39'
                    }
                }
            },
            
            RequestMode.MAXIMUM: {
                'daily_budget': 7000,  # Leave 500 as safety buffer
                'description': 'Maximum frequency with real-time updates',
                'schedules': {
                    'teams': {
                        'frequency': 'weekly',
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': '/teams?league=39&season=2024'
                    },
                    'fixtures': {
                        'frequency': 'four_times_daily',
                        'priority': 'high',
                        'estimated_requests': 4,
                        'endpoint': '/fixtures?league=39&season=2024'
                    },
                    'standings': {
                        'frequency': 'three_times_daily',
                        'priority': 'medium',
                        'estimated_requests': 3,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'every_30_minutes',
                        'priority': 'high',
                        'estimated_requests': 48,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    'lineups': {
                        'frequency': 'match_day_maximum',
                        'priority': 'highest',
                        'estimated_requests': 200,  # 10 fixtures × 2 teams × 10 checks
                        'endpoint': '/fixtures/lineups?fixture={fixture_id}'
                    },
                    'goalscorers': {
                        'frequency': 'real_time',
                        'priority': 'highest',
                        'estimated_requests': 100,  # 10 matches × 10 checks
                        'endpoint': '/fixtures/players?fixture={fixture_id}'
                    },
                    'probable_scorers': {
                        'frequency': 'pre_match_maximum',
                        'priority': 'medium',
                        'estimated_requests': 60,  # 10 fixtures × 6 updates
                        'endpoint': '/predictions?fixture={fixture_id}'
                    },
                    'live_fixtures': {
                        'frequency': 'every_2_minutes',
                        'priority': 'highest',
                        'estimated_requests': 1000,
                        'active_hours': '12:00-22:00',
                        'endpoint': '/fixtures?live=all&league=39'
                    },
                    'live_events': {
                        'frequency': 'every_minute',  # Real-time events
                        'priority': 'highest',
                        'estimated_requests': 500,
                        'active_hours': '12:00-22:00',
                        'endpoint': '/fixtures/events?fixture={fixture_id}'
                    }
                }
            }
        }
    
    def get_current_schedule(self) -> Dict[str, Any]:
        """Get the schedule for current mode"""
        return self.schedules[self.mode]
    
    def switch_mode(self, new_mode: RequestMode) -> Dict[str, Any]:
        """Switch to a different request mode"""
        old_mode = self.mode
        self.mode = new_mode
        
        return {
            "previous_mode": old_mode.value,
            "new_mode": new_mode.value,
            "previous_budget": self.schedules[old_mode]['daily_budget'],
            "new_budget": self.schedules[new_mode]['daily_budget'],
            "description": self.schedules[new_mode]['description']
        }
    
    def get_mode_comparison(self) -> Dict[str, Any]:
        """Compare all available modes"""
        comparison = {}
        
        for mode in RequestMode:
            schedule = self.schedules[mode]
            comparison[mode.value] = {
                "daily_budget": schedule['daily_budget'],
                "description": schedule['description'],
                "endpoints_covered": len(schedule['schedules']),
                "live_updates": 'live_fixtures' in schedule['schedules']
            }
        
        return comparison

# Usage Configuration
class RequestModeConfig:
    """Configuration class for managing request modes"""
    
    def __init__(self):
        self.current_mode = RequestMode.STANDARD  # Default mode
        self.manager = ScalableScheduleManager(self.current_mode)
    
    def auto_adjust_mode(self, current_usage: int, time_remaining_hours: int) -> RequestMode:
        """Automatically adjust mode based on current usage and time remaining"""
        
        if time_remaining_hours <= 0:
            return RequestMode.MINIMAL  # Emergency mode
        
        projected_usage = current_usage + (current_usage / (24 - time_remaining_hours)) * time_remaining_hours
        
        if projected_usage > 6500:
            return RequestMode.MINIMAL
        elif projected_usage > 5000:
            return RequestMode.LOW
        elif projected_usage > 3500:
            return RequestMode.STANDARD
        elif projected_usage > 2000:
            return RequestMode.HIGH
        else:
            return RequestMode.MAXIMUM
    
    def get_emergency_mode_schedule(self) -> Dict[str, Any]:
        """Get emergency minimal schedule when approaching limits"""
        return {
            'daily_budget': 100,
            'description': 'Emergency mode - critical requests only',
            'schedules': {
                'live_fixtures': {
                    'frequency': 'every_10_minutes',  # Only during active matches
                    'priority': 'critical',
                    'estimated_requests': 50,
                    'endpoint': '/fixtures?live=all&league=39'
                },
                'current_gameweek': {
                    'frequency': 'every_12_hours',
                    'priority': 'critical',
                    'estimated_requests': 2,
                    'endpoint': '/fixtures?league=39&season=2024&next=10'
                }
            }
        }
```

#### 2.3 Premier League Historical Data Strategy

```python
PREMIER_LEAGUE_HISTORICAL_PLAN = {
    'league_id': 39,  # Premier League ONLY
    'seasons_to_fetch': [2021, 2022, 2023, 2024],
    'data_types': [
        'fixtures',
        'standings', 
        'player_statistics',
        'goalscorers',  # NEW
        'lineups'       # NEW (where available)
    ],
    'gameweek_logic': {
        'detect_current_gameweek': True,
        'backfill_previous_gameweeks': True,
        'total_gameweeks': 38,  # Premier League standard
        'current_gameweek_calculation': 'dynamic'  # Based on fixture dates
    },
    'request_budget': {
        'initial_backfill': 2000,  # One-time historical data fetch
        'maintenance': 100         # Daily maintenance requests
    }
}
```

### Phase 3: Server Architecture Redesign

#### 3.1 New Project Structure
```
api-football-mcp-server/
├── mplan/
│   └── IMPLEMENT_SUPABASE_DB_AND_REQUEST_TRACKING.md
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── supabase_config.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── connection.py
│   │   └── migrations/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── league_scraper.py
│   │   ├── fixture_scraper.py
│   │   ├── player_scraper.py
│   │   └── live_scraper.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── leagues.py
│   │   │   ├── fixtures.py
│   │   │   ├── players.py
│   │   │   └── teams.py
│   │   └── middleware/
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── tools.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_service.py
│   │   ├── cache_service.py
│   │   └── sync_service.py
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py
│       └── gameweek_calculator.py
├── scheduler/
│   ├── __init__.py
│   ├── cron_jobs.py
│   └── task_manager.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── soccer_server.py (legacy - to be refactored)
```

#### 3.2 Core Components

**3.2.1 Database Connection Manager**
```python
# src/database/connection.py
from supabase import create_client, Client
from typing import Optional
import os

class SupabaseManager:
    _instance: Optional['SupabaseManager'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        self._client = create_client(url, key)
        return self._client
    
    @property
    def client(self) -> Client:
        if self._client is None:
            self.initialize()
        return self._client
```

**3.2.2 Enhanced Base Scraper with Mode-Aware Rate Limiting**
```python
# src/scrapers/base_scraper.py
import requests
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.utils.adaptive_rate_limiter import AdaptiveRateLimiter
from src.database.connection import SupabaseManager
from src.config.request_mode_manager import RequestModeManager

class BaseScraper(ABC):
    def __init__(self):
        self.api_key = os.getenv("RAPID_API_KEY_FOOTBALL")
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.headers = {
            "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
            "x-rapidapi-key": self.api_key
        }
        self.rate_limiter = AdaptiveRateLimiter()
        self.mode_manager = RequestModeManager()
        self.db = SupabaseManager()
    
    @abstractmethod
    def scrape_and_store(self, **kwargs) -> Dict[str, Any]:
        pass
    
    def make_api_request(self, endpoint: str, params: Dict[str, Any], priority: str = 'medium') -> Dict[str, Any]:
        # Check if request is allowed based on current mode and usage
        if not self.rate_limiter.can_make_request(endpoint, priority):
            return {"error": "Rate limit exceeded or request not allowed in current mode"}
        
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            # Log the request
            self.log_api_request(endpoint, params, len(response.content), response.status_code)
            self.rate_limiter.record_request()
            
            return response.json()
        except Exception as e:
            self.log_api_request(endpoint, params, 0, 0, str(e))
            return {"error": str(e)}
    
    def log_api_request(self, endpoint: str, params: Dict, size: int, status: int, error: str = None):
        self.db.client.table("api_request_log").insert({
            "endpoint": endpoint,
            "params": params,
            "response_size": size,
            "status_code": status,
            "error_message": error
        }).execute()

# src/utils/adaptive_rate_limiter.py
from datetime import datetime, date
from typing import Dict, Any
from src.database.connection import SupabaseManager
from src.config.request_mode_manager import RequestModeManager

class AdaptiveRateLimiter:
    """Rate limiter that adapts based on current request mode"""
    
    def __init__(self):
        self.db = SupabaseManager()
        self.mode_manager = RequestModeManager()
        
    def can_make_request(self, endpoint: str, priority: str) -> bool:
        """Check if request is allowed based on mode and current usage"""
        
        # Get current usage
        current_usage = self._get_current_usage()
        current_mode = self.mode_manager.get_current_mode()
        daily_budget = self.mode_manager.get_daily_budget()
        
        # Hard limit check
        if current_usage >= 7500:
            return False
        
        # Mode-specific budget check
        if current_usage >= daily_budget:
            # Only allow critical requests when over mode budget
            return priority in ['highest', 'critical']
        
        # Check if endpoint is allowed in current mode
        if not self._is_endpoint_allowed_in_mode(endpoint, current_mode):
            return False
        
        # Auto-adjust mode if needed
        if self.mode_manager.auto_adjust_enabled:
            self._check_and_adjust_mode(current_usage)
        
        return True
    
    def record_request(self):
        """Record that a request was made"""
        today = date.today()
        
        # Increment daily counter
        result = self.db.client.table("daily_request_counter").select("*").eq("date", today).execute()
        
        if result.data:
            # Update existing record
            new_count = result.data[0]["request_count"] + 1
            self.db.client.table("daily_request_counter").update({
                "request_count": new_count
            }).eq("date", today).execute()
        else:
            # Create new record for today
            self.db.client.table("daily_request_counter").insert({
                "date": today.isoformat(),
                "request_count": 1
            }).execute()
    
    def _get_current_usage(self) -> int:
        """Get current daily usage"""
        today = date.today()
        result = self.db.client.table("daily_request_counter").select("request_count").eq("date", today).execute()
        return result.data[0]["request_count"] if result.data else 0
    
    def _is_endpoint_allowed_in_mode(self, endpoint: str, mode: str) -> bool:
        """Check if endpoint is allowed in current mode"""
        mode_schedule = self.mode_manager.get_mode_schedule(mode)
        
        # Check if any schedule item matches the endpoint
        for schedule_item in mode_schedule.get('schedules', {}).values():
            if endpoint in schedule_item.get('endpoint', ''):
                return True
        
        return False
    
    def _check_and_adjust_mode(self, current_usage: int):
        """Auto-adjust mode based on usage"""
        current_hour = datetime.now().hour
        time_remaining = 24 - current_hour
        
        if time_remaining <= 0:
            return
        
        # Calculate projected usage
        hourly_rate = current_usage / (24 - time_remaining) if (24 - time_remaining) > 0 else current_usage
        projected_daily = hourly_rate * 24
        
        # Determine appropriate mode
        if projected_daily > 6500:
            new_mode = 'minimal'
        elif projected_daily > 5000:
            new_mode = 'low'
        elif projected_daily > 3500:
            new_mode = 'standard'
        elif projected_daily > 2000:
            new_mode = 'high'
        else:
            new_mode = 'maximum'
        
        current_mode = self.mode_manager.get_current_mode()
        
        if new_mode != current_mode:
            self.mode_manager.switch_mode(new_mode, f"Auto-adjusted due to projected usage: {projected_daily:.0f}")

# src/config/request_mode_manager.py
class RequestModeManager:
    """Manages request mode configuration"""
    
    def __init__(self):
        self.db = SupabaseManager()
        self.mode_schedules = ScalableScheduleManager().schedules
    
    def get_current_mode(self) -> str:
        """Get current request mode from database"""
        result = self.db.client.table("request_mode_config").select("current_mode").limit(1).execute()
        return result.data[0]["current_mode"] if result.data else "standard"
    
    def get_daily_budget(self) -> int:
        """Get daily budget for current mode"""
        result = self.db.client.table("request_mode_config").select("daily_budget").limit(1).execute()
        return result.data[0]["daily_budget"] if result.data else 3000
    
    def get_auto_adjust_enabled(self) -> bool:
        """Check if auto-adjust is enabled"""
        result = self.db.client.table("request_mode_config").select("auto_adjust_enabled").limit(1).execute()
        return result.data[0]["auto_adjust_enabled"] if result.data else True
    
    @property
    def auto_adjust_enabled(self) -> bool:
        return self.get_auto_adjust_enabled()
    
    def switch_mode(self, new_mode: str, reason: str = "Manual change"):
        """Switch to a new request mode"""
        mode_info = self.mode_schedules.get(new_mode)
        if not mode_info:
            raise ValueError(f"Invalid mode: {new_mode}")
        
        self.db.client.table("request_mode_config").update({
            "current_mode": new_mode,
            "daily_budget": mode_info['daily_budget'],
            "last_mode_change": datetime.now().isoformat(),
            "reason_for_change": reason,
            "updated_at": datetime.now().isoformat()
        }).eq("id", 1).execute()
    
    def get_mode_schedule(self, mode: str) -> Dict[str, Any]:
        """Get schedule configuration for a specific mode"""
        return self.mode_schedules.get(mode, {})
    
    def enable_auto_adjust(self, enabled: bool = True):
        """Enable or disable auto-adjustment"""
        self.db.client.table("request_mode_config").update({
            "auto_adjust_enabled": enabled,
            "updated_at": datetime.now().isoformat()
        }).eq("id", 1).execute()
```

**3.2.3 Premier League Gameweek Calculator**
```python
# src/utils/gameweek_calculator.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from src.database.connection import SupabaseManager

class PremierLeagueGameweekCalculator:
    PREMIER_LEAGUE_ID = 39
    
    def __init__(self):
        self.db = SupabaseManager()
    
    def get_current_gameweek(self, season: int) -> Optional[int]:
        """
        Calculate current gameweek based on fixture dates for Premier League
        """
        now = datetime.now()
        
        # Check cached gameweek first
        cached = self.db.client.table("premier_league_gameweeks").select("*").eq("season", season).eq("is_current", True).execute()
        
        if cached.data and len(cached.data) > 0:
            gw = cached.data[0]
            if gw['start_date'] <= now.isoformat() <= gw['end_date']:
                return gw['gameweek']
        
        # Calculate dynamically from fixtures
        fixtures = self.db.client.table("fixtures").select("*").eq("league_id", self.PREMIER_LEAGUE_ID).eq("season", season).order("date").execute()
        
        if not fixtures.data:
            return None
        
        # Group fixtures by round and find current gameweek
        for fixture in fixtures.data:
            fixture_date = datetime.fromisoformat(fixture['date'].replace('Z', '+00:00'))
            if fixture_date > now:
                # Extract gameweek number from round (e.g., "Regular Season - 15")
                round_str = fixture['round']
                if 'Regular Season' in round_str:
                    try:
                        gameweek = int(round_str.split(' - ')[-1])
                        self._update_current_gameweek(season, gameweek)
                        return gameweek
                    except (ValueError, IndexError):
                        continue
        
        return None
    
    def _update_current_gameweek(self, season: int, gameweek: int):
        """Update the current gameweek in database"""
        # Reset all current flags
        self.db.client.table("premier_league_gameweeks").update({"is_current": False}).eq("season", season).execute()
        
        # Set new current gameweek
        self.db.client.table("premier_league_gameweeks").update({"is_current": True}).eq("season", season).eq("gameweek", gameweek).execute()
    
    def get_gameweek_fixtures(self, season: int, gameweek: int) -> List[Dict]:
        """Get all fixtures for a specific gameweek"""
        return self.db.client.table("fixtures").select("*").eq("league_id", self.PREMIER_LEAGUE_ID).eq("season", season).eq("round", f"Regular Season - {gameweek}").execute().data
```

**3.2.4 Missing Endpoint Scrapers**
```python
# src/scrapers/lineup_scraper.py
class LineupScraper(BaseScraper):
    def scrape_lineups(self, fixture_id: int) -> Dict[str, Any]:
        """Scrape team lineups for a fixture"""
        if not self.rate_limiter.can_make_request():
            return {"error": "Rate limit exceeded"}
        
        data = self.make_api_request(f"fixtures/lineups", {"fixture": fixture_id})
        
        if "error" not in data:
            self._store_lineups(fixture_id, data)
        
        return data
    
    def _store_lineups(self, fixture_id: int, api_data: Dict):
        """Store lineup data in Supabase"""
        for team_data in api_data.get("response", []):
            team_info = team_data.get("team", {})
            coach_info = team_data.get("coach", {})
            
            # Insert lineup record
            lineup_result = self.db.client.table("fixture_lineups").insert({
                "fixture_id": fixture_id,
                "team_id": team_info.get("id"),
                "formation": team_data.get("formation"),
                "coach_id": coach_info.get("id"),
                "coach_name": coach_info.get("name"),
                "coach_photo": coach_info.get("photo")
            }).execute()
            
            lineup_id = lineup_result.data[0]["id"]
            
            # Insert starting XI
            for player in team_data.get("startXI", []):
                player_info = player.get("player", {})
                self.db.client.table("lineup_players").insert({
                    "lineup_id": lineup_id,
                    "player_id": player_info.get("id"),
                    "player_name": player_info.get("name"),
                    "player_number": player_info.get("number"),
                    "player_pos": player_info.get("pos"),
                    "grid": player_info.get("grid"),
                    "is_starter": True
                }).execute()
            
            # Insert substitutes
            for player in team_data.get("substitutes", []):
                player_info = player.get("player", {})
                self.db.client.table("lineup_players").insert({
                    "lineup_id": lineup_id,
                    "player_id": player_info.get("id"),
                    "player_name": player_info.get("name"),
                    "player_number": player_info.get("number"),
                    "player_pos": player_info.get("pos"),
                    "grid": player_info.get("grid"),
                    "is_starter": False
                }).execute()

# src/scrapers/goalscorer_scraper.py
class GoalscorerScraper(BaseScraper):
    def scrape_goalscorers(self, fixture_id: int) -> Dict[str, Any]:
        """Scrape goal scorers for a fixture"""
        if not self.rate_limiter.can_make_request():
            return {"error": "Rate limit exceeded"}
        
        data = self.make_api_request(f"fixtures/players", {"fixture": fixture_id})
        
        if "error" not in data:
            self._store_goalscorers(fixture_id, data)
        
        return data
    
    def _store_goalscorers(self, fixture_id: int, api_data: Dict):
        """Store goalscorer data in Supabase"""
        for team_data in api_data.get("response", []):
            team_id = team_data.get("team", {}).get("id")
            
            for player_data in team_data.get("players", []):
                player_info = player_data.get("player", {})
                
                for goal in player_data.get("statistics", [{}])[0].get("goals", {}).get("total") or []:
                    if goal and goal > 0:
                        # Extract goal details from events if available
                        self.db.client.table("fixture_goalscorers").insert({
                            "fixture_id": fixture_id,
                            "team_id": team_id,
                            "player_id": player_info.get("id"),
                            "time_elapsed": None,  # Would need to cross-reference with events
                            "goal_type": "Normal Goal"  # Default, would need event details
                        }).execute()

# src/scrapers/probable_scorer_scraper.py
class ProbableScorerScraper(BaseScraper):
    def scrape_probable_scorers(self, fixture_id: int) -> Dict[str, Any]:
        """Scrape probable scorers predictions for a fixture"""
        if not self.rate_limiter.can_make_request():
            return {"error": "Rate limit exceeded"}
        
        data = self.make_api_request(f"predictions", {"fixture": fixture_id})
        
        if "error" not in data:
            self._store_probable_scorers(fixture_id, data)
        
        return data
    
    def _store_probable_scorers(self, fixture_id: int, api_data: Dict):
        """Store probable scorer predictions in Supabase"""
        for prediction in api_data.get("response", []):
            # Extract probable scorer data from predictions
            # This would need to be adapted based on actual API response structure
            pass
```

### Phase 4: Implementation Timeline

#### Week 1: Foundation Setup ✅ COMPLETED
- [x] Set up Supabase project and database schema ✅
- [x] Create new project structure ✅
- [x] Implement database connection and basic models ✅
- [x] Set up configurable request mode system ✅
- [x] Install all required dependencies ✅

#### Week 2: Core Components ✅ COMPLETED
- [x] Implement adaptive rate limiter with mode awareness ✅
- [x] Create enhanced base scraper class ✅
- [x] Implement Premier League gameweek calculator ✅
- [x] Create missing endpoint scrapers (lineups, goalscorers, probable scorers) ✅
- [x] Update for 1,000 daily request limit ✅
- [x] Database schema deployed to Supabase ✅
- [x] Environment configuration working ✅

#### Week 3: Data Collection & Testing (IN PROGRESS)
- [x] Database connection established ✅
- [ ] **NEXT: Scrape initial Premier League data** 
- [ ] Test all missing endpoints with real data
- [ ] Validate gameweek extraction with real fixtures
- [ ] Test request mode switching

#### Week 4: MCP Integration
- [ ] Refactor existing MCP tools to use cached data
- [ ] Add new MCP tools for missing endpoints
- [ ] Add MCP tools for request mode management
- [ ] Implement data synchronization service

#### Week 5: API & Scheduling
- [ ] Implement FastAPI endpoints
- [ ] Create scheduled scraping jobs
- [ ] Set up monitoring and alerting
- [ ] Implement error handling and recovery

#### Week 6: Testing and Optimization
- [ ] Performance testing with real data
- [ ] API rate limit validation
- [ ] Data accuracy verification
- [ ] Final deployment preparation

### Implementation Progress Summary

#### ✅ **COMPLETED COMPONENTS:**
1. **Project Structure** - Complete directory structure with proper Python packages
2. **Dependencies** - All required packages installed (Supabase, FastAPI, etc.)
3. **Database Schema** - Complete SQL schema with all tables and indexes
4. **Connection Manager** - Singleton Supabase connection with error handling
5. **Configuration System** - Environment-based settings with validation
6. **Request Mode System** - 5-mode scalable system with database persistence

#### ✅ **COMPLETED CORE COMPONENTS:**
1. **Project Structure** ✅ - Complete directory structure with proper Python packages
2. **Dependencies** ✅ - All required packages installed (Supabase, FastAPI, etc.)
3. **Database Schema** ✅ - Complete SQL schema with gameweek support and indexes
4. **Connection Manager** ✅ - Singleton Supabase connection with error handling
5. **Configuration System** ✅ - Environment-based settings with validation
6. **Request Mode System** ✅ - 5-mode scalable system with database persistence
7. **Adaptive Rate Limiter** ✅ - Smart rate limiting with auto-adjustment and mode awareness
8. **Enhanced Base Scraper** ✅ - Full-featured scraper with caching, retry logic, and gameweek support
9. **Integration Tests** ✅ - High-value tests validating all core components (moved to tests/)
10. **Gameweek Support** ✅ - fixtures.gameweek field with extraction logic for fast queries
11. **Missing Endpoint Scrapers** ✅ - LineupScraper, GoalscorerScraper, ProbableScorerScraper
12. **Premier League Gameweek Calculator** ✅ - Dynamic gameweek detection and management
13. **Scraper Manager** ✅ - Coordinates all scrapers with intelligent data collection
14. **Enhanced MCP Tools** ✅ - New tools for missing endpoints + enhanced existing tools

#### 🔄 **IN PROGRESS:**
- Integration with existing soccer_server.py

#### 📋 **REMAINING CORE COMPONENTS:**
- Scheduling System (automated data collection)
- FastAPI Endpoints (REST API alongside MCP)
- Final Integration Testing

### Phase 5: Monitoring and Maintenance

#### 5.1 Key Metrics to Track
- API requests per day/hour
- Data freshness by entity type
- Cache hit rates
- Response times
- Error rates
- Database performance

#### 5.2 Alerting Rules
```python
ALERTING_RULES = {
    'api_rate_limit': {
        'threshold': 6000,  # 80% of daily limit
        'action': 'reduce_scraping_frequency'
    },
    'data_staleness': {
        'fixtures': 6,  # hours
        'live_data': 10,  # minutes
        'standings': 24  # hours
    },
    'error_rate': {
        'threshold': 5,  # percent
        'window': 60  # minutes
    }
}
```

### Phase 6: API Endpoints Design

#### 6.1 RESTful API Structure (Premier League Focused)
```python
# FastAPI endpoints to replace MCP tools
GET /api/v1/premier-league/fixtures?season=2024&gameweek=15
GET /api/v1/premier-league/standings?season=2024
GET /api/v1/premier-league/current-gameweek?season=2024
GET /api/v1/players/{player_id}/statistics?season=2024
GET /api/v1/teams/{team_id}/fixtures?type=upcoming&limit=5
GET /api/v1/fixtures/{fixture_id}/statistics
GET /api/v1/fixtures/{fixture_id}/events
GET /api/v1/fixtures/{fixture_id}/lineups          # NEW
GET /api/v1/fixtures/{fixture_id}/goalscorers      # NEW
GET /api/v1/fixtures/{fixture_id}/probable-scorers # NEW
GET /api/v1/live/matches?league_id=39
```

#### 6.2 New MCP Tools for Missing Endpoints
```python
# Additional MCP tools to be added to soccer_server.py

@mcp.tool()
def get_fixture_lineups(fixture_id: int) -> Dict[str, Any]:
    """Retrieve team lineups for a specific fixture.
    
    Args:
        fixture_id (int): The ID of the fixture.
        
    Returns:
        Dict[str, Any]: Lineup data from cache or API.
    """
    # Check cache first, fallback to API if needed
    pass

@mcp.tool()
def get_fixture_goalscorers(fixture_id: int) -> Dict[str, Any]:
    """Retrieve goal scorers for a specific fixture.
    
    Args:
        fixture_id (int): The ID of the fixture.
        
    Returns:
        Dict[str, Any]: Goal scorer data from cache or API.
    """
    pass

@mcp.tool()
def get_probable_scorers(fixture_id: int) -> Dict[str, Any]:
    """Retrieve probable scorer predictions for a fixture.
    
    Args:
        fixture_id (int): The ID of the fixture.
        
    Returns:
        Dict[str, Any]: Probable scorer predictions.
    """
    pass

@mcp.tool()
def get_current_gameweek(season: int = 2024) -> Dict[str, Any]:
    """Get the current Premier League gameweek.
    
    Args:
        season (int): The season year.
        
    Returns:
        Dict[str, Any]: Current gameweek information.
    """
    calculator = PremierLeagueGameweekCalculator()
    current_gw = calculator.get_current_gameweek(season)
    
    if current_gw:
        fixtures = calculator.get_gameweek_fixtures(season, current_gw)
        return {
            "current_gameweek": current_gw,
            "season": season,
            "fixtures": fixtures,
            "total_gameweeks": 38
        }
    else:
        return {"error": "Could not determine current gameweek"}

@mcp.tool()
def get_gameweek_fixtures(season: int, gameweek: int) -> Dict[str, Any]:
    """Get all fixtures for a specific Premier League gameweek.
    
    Args:
        season (int): The season year.
        gameweek (int): The gameweek number (1-38).
        
    Returns:
        Dict[str, Any]: Fixtures for the specified gameweek.
    """
    if not (1 <= gameweek <= 38):
        return {"error": "Gameweek must be between 1 and 38"}
    
    calculator = PremierLeagueGameweekCalculator()
    fixtures = calculator.get_gameweek_fixtures(season, gameweek)
    
    return {
        "gameweek": gameweek,
        "season": season,
        "fixtures": fixtures,
        "fixture_count": len(fixtures)
    }

# NEW MCP TOOLS FOR REQUEST MODE MANAGEMENT

@mcp.tool()
def get_request_mode_status() -> Dict[str, Any]:
    """Get current request mode and usage statistics.
    
    Returns:
        Dict[str, Any]: Current mode, usage, and available modes.
    """
    mode_manager = RequestModeManager()
    rate_limiter = AdaptiveRateLimiter()
    
    current_usage = rate_limiter._get_current_usage()
    current_mode = mode_manager.get_current_mode()
    daily_budget = mode_manager.get_daily_budget()
    
    # Get mode comparison
    schedule_manager = ScalableScheduleManager()
    mode_comparison = schedule_manager.get_mode_comparison()
    
    return {
        "current_mode": current_mode,
        "daily_budget": daily_budget,
        "current_usage": current_usage,
        "remaining_requests": 7500 - current_usage,
        "mode_budget_remaining": daily_budget - current_usage,
        "usage_percentage": (current_usage / 7500) * 100,
        "mode_usage_percentage": (current_usage / daily_budget) * 100 if daily_budget > 0 else 0,
        "auto_adjust_enabled": mode_manager.auto_adjust_enabled,
        "available_modes": mode_comparison
    }

@mcp.tool()
def switch_request_mode(mode: str, reason: str = "Manual change") -> Dict[str, Any]:
    """Switch to a different request mode.
    
    Args:
        mode (str): New mode ('minimal', 'low', 'standard', 'high', 'maximum').
        reason (str): Reason for the change.
        
    Returns:
        Dict[str, Any]: Mode change confirmation and details.
    """
    valid_modes = ['minimal', 'low', 'standard', 'high', 'maximum']
    
    if mode not in valid_modes:
        return {
            "error": f"Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}"
        }
    
    try:
        mode_manager = RequestModeManager()
        old_mode = mode_manager.get_current_mode()
        old_budget = mode_manager.get_daily_budget()
        
        mode_manager.switch_mode(mode, reason)
        
        new_budget = mode_manager.get_daily_budget()
        
        return {
            "success": True,
            "previous_mode": old_mode,
            "new_mode": mode,
            "previous_budget": old_budget,
            "new_budget": new_budget,
            "reason": reason,
            "message": f"Successfully switched from {old_mode} mode ({old_budget} requests/day) to {mode} mode ({new_budget} requests/day)"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def toggle_auto_adjust(enabled: bool) -> Dict[str, Any]:
    """Enable or disable automatic mode adjustment.
    
    Args:
        enabled (bool): True to enable auto-adjustment, False to disable.
        
    Returns:
        Dict[str, Any]: Confirmation of the change.
    """
    try:
        mode_manager = RequestModeManager()
        mode_manager.enable_auto_adjust(enabled)
        
        return {
            "success": True,
            "auto_adjust_enabled": enabled,
            "message": f"Auto-adjustment {'enabled' if enabled else 'disabled'}"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_usage_prediction() -> Dict[str, Any]:
    """Get prediction of daily usage based on current rate.
    
    Returns:
        Dict[str, Any]: Usage prediction and recommendations.
    """
    try:
        rate_limiter = AdaptiveRateLimiter()
        current_usage = rate_limiter._get_current_usage()
        
        now = datetime.now()
        current_hour = now.hour
        
        if current_hour == 0:
            return {"message": "Cannot predict usage at midnight"}
        
        # Calculate hourly rate and projection
        hours_elapsed = current_hour
        hourly_rate = current_usage / hours_elapsed if hours_elapsed > 0 else 0
        projected_daily = hourly_rate * 24
        
        # Determine recommended action
        if projected_daily > 7000:
            recommendation = "EMERGENCY: Switch to minimal mode immediately"
            recommended_mode = "minimal"
        elif projected_daily > 5500:
            recommendation = "WARNING: Consider switching to low mode"
            recommended_mode = "low"
        elif projected_daily > 3500:
            recommendation = "CAUTION: Monitor usage closely"
            recommended_mode = "standard"
        else:
            recommendation = "NORMAL: Usage is within safe limits"
            recommended_mode = "high" if projected_daily < 2000 else "standard"
        
        return {
            "current_usage": current_usage,
            "hours_elapsed": hours_elapsed,
            "hourly_rate": round(hourly_rate, 2),
            "projected_daily_total": round(projected_daily),
            "will_exceed_limit": projected_daily > 7500,
            "recommendation": recommendation,
            "recommended_mode": recommended_mode,
            "safety_margin": 7500 - projected_daily
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_mode_schedule(mode: str = None) -> Dict[str, Any]:
    """Get the scraping schedule for a specific mode or current mode.
    
    Args:
        mode (str): Mode to get schedule for. If None, uses current mode.
        
    Returns:
        Dict[str, Any]: Detailed schedule configuration.
    """
    try:
        if mode is None:
            mode_manager = RequestModeManager()
            mode = mode_manager.get_current_mode()
        
        schedule_manager = ScalableScheduleManager(RequestMode(mode))
        schedule = schedule_manager.get_current_schedule()
        
        return {
            "mode": mode,
            "daily_budget": schedule['daily_budget'],
            "description": schedule['description'],
            "schedules": schedule['schedules'],
            "total_endpoints": len(schedule['schedules']),
            "estimated_daily_requests": sum(
                item.get('estimated_requests', 0) 
                for item in schedule['schedules'].values()
            )
        }
    except Exception as e:
        return {"error": str(e)}
```

#### 6.2 MCP Tool Migration Strategy
Each existing MCP tool will be updated to:
1. Check cache first (Supabase)
2. Return cached data if fresh
3. Fall back to API only if cache is stale and within rate limits
4. Queue data refresh for next scraping cycle

### Phase 7: Deployment Strategy

#### 7.1 Environment Configuration
```python
# src/config/settings.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # API Football
    RAPID_API_KEY_FOOTBALL: str = os.getenv("RAPID_API_KEY_FOOTBALL")
    
    # Rate Limiting
    MAX_DAILY_REQUESTS: int = 7500
    RATE_LIMIT_WINDOW_HOURS: int = 24
    
    # Scraping Configuration
    ENABLE_LIVE_SCRAPING: bool = True
    SCRAPING_TIMEZONE: str = "UTC"
    
    # Cache Configuration
    DEFAULT_CACHE_TTL_HOURS: int = 24
    LIVE_DATA_TTL_MINUTES: int = 5
    
    class Config:
        env_file = ".env"
```

#### 7.2 Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run both MCP server and scheduler
CMD ["python", "-m", "src.main"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  soccer-server:
    build: .
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - RAPID_API_KEY_FOOTBALL=${RAPID_API_KEY_FOOTBALL}
    ports:
      - "8000:8000"  # FastAPI
      - "5000:5000"  # MCP
    restart: unless-stopped
    
  scheduler:
    build: .
    command: ["python", "-m", "scheduler.cron_jobs"]
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - RAPID_API_KEY_FOOTBALL=${RAPID_API_KEY_FOOTBALL}
    restart: unless-stopped
```

## Request Tracking & Monitoring System

### Daily Request Monitoring Dashboard
```python
# src/monitoring/request_monitor.py
class RequestMonitor:
    def __init__(self):
        self.db = SupabaseManager()
    
    def get_daily_usage_report(self) -> Dict[str, Any]:
        """Generate daily API usage report"""
        today = datetime.now().date()
        
        # Get total requests today
        total_result = self.db.client.table("daily_request_counter").select("request_count").eq("date", today).execute()
        total_requests = total_result.data[0]["request_count"] if total_result.data else 0
        
        # Get requests by endpoint
        endpoint_stats = self.db.client.table("api_request_log").select("endpoint").eq("request_timestamp::date", today).execute()
        
        # Calculate usage by category
        endpoint_breakdown = {}
        for record in endpoint_stats.data:
            endpoint = record["endpoint"]
            endpoint_breakdown[endpoint] = endpoint_breakdown.get(endpoint, 0) + 1
        
        return {
            "date": today.isoformat(),
            "total_requests": total_requests,
            "remaining_requests": 7500 - total_requests,
            "usage_percentage": (total_requests / 7500) * 100,
            "endpoint_breakdown": endpoint_breakdown,
            "status": "OK" if total_requests < 7000 else "WARNING" if total_requests < 7500 else "CRITICAL"
        }
    
    def predict_daily_usage(self) -> Dict[str, Any]:
        """Predict if we'll exceed daily limit based on current usage"""
        now = datetime.now()
        current_hour = now.hour
        
        if current_hour == 0:
            return {"prediction": "Unable to predict at midnight"}
        
        today = now.date()
        total_result = self.db.client.table("daily_request_counter").select("request_count").eq("date", today).execute()
        current_requests = total_result.data[0]["request_count"] if total_result.data else 0
        
        # Simple linear projection
        hourly_rate = current_requests / current_hour
        projected_daily = hourly_rate * 24
        
        return {
            "current_requests": current_requests,
            "current_hour": current_hour,
            "hourly_rate": round(hourly_rate, 2),
            "projected_daily_total": round(projected_daily),
            "will_exceed_limit": projected_daily > 7500,
            "recommended_action": "REDUCE_FREQUENCY" if projected_daily > 7000 else "CONTINUE_NORMAL"
        }

# Automated alerting
def check_and_alert():
    monitor = RequestMonitor()
    report = monitor.get_daily_usage_report()
    prediction = monitor.predict_daily_usage()
    
    if report["status"] == "CRITICAL":
        # Send alert - API limit reached
        send_alert("API limit reached!", report)
    elif prediction["will_exceed_limit"]:
        # Send warning - likely to exceed limit
        send_alert("API limit will be exceeded!", prediction)
```

### Emergency Rate Limiting
```python
class EmergencyRateLimiter:
    """Emergency system to prevent exceeding daily API limits"""
    
    def __init__(self):
        self.db = SupabaseManager()
        self.critical_threshold = 7000  # Start emergency mode at 7000 requests
        self.max_threshold = 7500       # Hard stop at 7500
    
    def should_allow_request(self, endpoint: str, priority: str) -> bool:
        """Determine if a request should be allowed based on current usage"""
        current_usage = self._get_current_usage()
        
        if current_usage >= self.max_threshold:
            return False  # Hard stop
        
        if current_usage >= self.critical_threshold:
            # Emergency mode - only allow critical requests
            critical_endpoints = [
                'fixtures/lineups',    # Match day lineups
                'fixtures?live=all',   # Live scores
                'fixtures/events'      # Live events
            ]
            
            return any(critical in endpoint for critical in critical_endpoints) and priority == 'highest'
        
        return True  # Normal operation
    
    def _get_current_usage(self) -> int:
        today = datetime.now().date()
        result = self.db.client.table("daily_request_counter").select("request_count").eq("date", today).execute()
        return result.data[0]["request_count"] if result.data else 0
```

## Success Criteria

1. **Performance**: 95% of requests served from cache with <100ms response time
2. **Reliability**: 99.9% uptime for both MCP and API endpoints
3. **Rate Limit Compliance**: NEVER exceed 7,500 daily API requests (hard constraint)
4. **Data Freshness**: Premier League data updated within acceptable timeframes
5. **Data Quality**: <1% data discrepancy compared to direct API calls
6. **Request Tracking**: 100% of API requests logged and counted in real-time

## Risk Mitigation

1. **API Rate Limiting**: Implement circuit breaker pattern and request queuing
2. **Data Staleness**: Implement intelligent cache invalidation and fallback strategies
3. **Database Performance**: Use connection pooling and query optimization
4. **Error Handling**: Comprehensive logging, monitoring, and automatic recovery
5. **Dependency Management**: Version pinning and regular security updates

## Future Enhancements

1. **Machine Learning**: Predictive caching based on usage patterns
2. **Multi-Region**: Deploy across multiple regions for better performance
3. **Real-time Updates**: WebSocket support for live match updates
4. **Advanced Analytics**: Data warehouse integration for historical analysis
5. **Third-party Integrations**: Support for additional football data providers

---

*This implementation plan provides a comprehensive roadmap for transforming the soccer MCP server into a robust, scalable, and efficient system that maximizes the value of the API-Football service while staying within rate limits.*
