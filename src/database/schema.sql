-- Premier League Football Data Schema for Supabase
-- This schema supports the MCP server with request tracking and mode management

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
    gameweek INTEGER, -- Extracted gameweek number for easy querying
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
CREATE INDEX idx_fixtures_gameweek ON fixtures(league_id, season, gameweek);
CREATE INDEX idx_fixtures_date ON fixtures(date);
CREATE INDEX idx_fixtures_teams ON fixtures(home_team_id, away_team_id);
CREATE INDEX idx_standings_league_season ON standings(league_id, season);
CREATE INDEX idx_player_stats_player_season ON player_statistics(player_id, season);
CREATE INDEX idx_api_requests_created ON api_request_log(request_timestamp);
CREATE INDEX idx_sync_status_next_sync ON data_sync_status(next_sync);
CREATE INDEX idx_daily_counter_date ON daily_request_counter(date);
CREATE INDEX idx_gameweeks_season ON premier_league_gameweeks(season);
CREATE INDEX idx_gameweeks_current ON premier_league_gameweeks(is_current);

-- Row Level Security (RLS) Setup
ALTER TABLE leagues ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixtures ENABLE ROW LEVEL SECURITY;
ALTER TABLE standings ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixture_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixture_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixture_lineups ENABLE ROW LEVEL SECURITY;
ALTER TABLE lineup_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixture_goalscorers ENABLE ROW LEVEL SECURITY;
ALTER TABLE probable_scorers ENABLE ROW LEVEL SECURITY;
ALTER TABLE premier_league_gameweeks ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your authentication needs)
CREATE POLICY "Allow read access" ON leagues FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON teams FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON players FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON fixtures FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON standings FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON player_statistics FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON fixture_statistics FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON fixture_events FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON fixture_lineups FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON lineup_players FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON fixture_goalscorers FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON probable_scorers FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON premier_league_gameweeks FOR SELECT USING (true);

-- Insert default configuration
INSERT INTO request_mode_config (current_mode, daily_budget, auto_adjust_enabled) 
VALUES ('low', 300, true);

-- Insert Premier League league record
INSERT INTO leagues (id, name, country, season, current) 
VALUES (39, 'Premier League', 'England', 2024, true);
