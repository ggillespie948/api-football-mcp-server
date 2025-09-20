-- Phase 2: Extended Schema for Squads, H2H, and Team Statistics
-- Add these tables to your existing Supabase database

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
    form VARCHAR(10), -- "WWDLL" format for last 5
    last_5_results JSONB, -- Array of last 5 match results with details
    home_record JSONB, -- Home statistics
    away_record JSONB, -- Away statistics
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, league_id, season)
);

-- Enhanced player statistics for current season
CREATE TABLE enhanced_player_statistics (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id),
    team_id INTEGER REFERENCES teams(id),
    league_id INTEGER REFERENCES leagues(id),
    season INTEGER,
    -- Current season stats
    current_goals INTEGER DEFAULT 0,
    current_assists INTEGER DEFAULT 0,
    current_appearances INTEGER DEFAULT 0,
    current_minutes INTEGER DEFAULT 0,
    -- Form indicators
    last_5_goals INTEGER DEFAULT 0,
    last_5_assists INTEGER DEFAULT 0,
    last_5_appearances INTEGER DEFAULT 0,
    recent_form VARCHAR(10), -- "GAGA-" (G=Goal, A=Assist, -=No contribution)
    -- Performance metrics
    goals_per_game DECIMAL(3,2) DEFAULT 0,
    assists_per_game DECIMAL(3,2) DEFAULT 0,
    minutes_per_goal DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(player_id, team_id, league_id, season)
);

-- Indexes for performance
CREATE INDEX idx_team_squads_team_season ON team_squads(team_id, season);
CREATE INDEX idx_team_squads_player ON team_squads(player_id, season);
CREATE INDEX idx_h2h_teams ON head_to_head(team1_id, team2_id);
CREATE INDEX idx_h2h_reverse ON head_to_head(team2_id, team1_id);
CREATE INDEX idx_team_stats_team_season ON team_statistics(team_id, season);
CREATE INDEX idx_team_stats_league ON team_statistics(league_id, season);
CREATE INDEX idx_enhanced_player_stats ON enhanced_player_statistics(player_id, season);
CREATE INDEX idx_enhanced_player_team ON enhanced_player_statistics(team_id, season);

-- Row Level Security for new tables
ALTER TABLE team_squads ENABLE ROW LEVEL SECURITY;
ALTER TABLE head_to_head ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE enhanced_player_statistics ENABLE ROW LEVEL SECURITY;

-- Create policies for new tables
CREATE POLICY "Allow read access" ON team_squads FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON head_to_head FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON team_statistics FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON enhanced_player_statistics FOR SELECT USING (true);

-- Temporarily allow inserts for data loading (disable RLS or add insert policies)
ALTER TABLE team_squads DISABLE ROW LEVEL SECURITY;
ALTER TABLE head_to_head DISABLE ROW LEVEL SECURITY;
ALTER TABLE team_statistics DISABLE ROW LEVEL SECURITY;
ALTER TABLE enhanced_player_statistics DISABLE ROW LEVEL SECURITY;
