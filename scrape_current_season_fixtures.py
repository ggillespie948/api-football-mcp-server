#!/usr/bin/env python3
"""
Scrape Current Season Fixtures using Global Settings
"""

import sys
sys.path.insert(0, 'src')

from config.settings import get_settings
from database.connection import get_db_client
import requests

def extract_gameweek_from_round(round_str):
    if not round_str:
        return None
    if "Regular Season" in round_str and " - " in round_str:
        parts = round_str.split(" - ")
        if len(parts) >= 2:
            try:
                return int(parts[-1])
            except ValueError:
                return None
    return None

def scrape_fixtures():
    settings = get_settings()
    db = get_db_client()
    
    print(f"Scraping Premier League fixtures for season {settings.DEFAULT_SEASON}...")
    
    response = requests.get(
        f'{settings.BASE_API_URL}/fixtures',
        headers=settings.get_api_headers(),
        params={'league': settings.PREMIER_LEAGUE_ID, 'season': settings.DEFAULT_SEASON},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        return False
    
    data = response.json()
    fixtures_data = []
    
    for fixture_info in data.get('response', []):
        fixture = fixture_info['fixture']
        league = fixture_info['league'] 
        teams = fixture_info['teams']
        goals = fixture_info['goals']
        
        round_str = league.get('round', '')
        gameweek = extract_gameweek_from_round(round_str)
        
        fixtures_data.append({
            'id': fixture['id'],
            'league_id': settings.PREMIER_LEAGUE_ID,
            'season': settings.DEFAULT_SEASON,
            'round': round_str,
            'gameweek': gameweek,
            'home_team_id': teams['home']['id'],
            'away_team_id': teams['away']['id'],
            'date': fixture.get('date'),
            'status_short': fixture['status']['short'],
            'status_long': fixture['status']['long'],
            'home_score': goals.get('home'),
            'away_score': goals.get('away')
        })
    
    print(f"Prepared {len(fixtures_data)} fixtures for season {settings.DEFAULT_SEASON}")
    
    # Count gameweeks
    gameweeks = {}
    for f in fixtures_data:
        gw = f['gameweek']
        if gw:
            gameweeks[gw] = gameweeks.get(gw, 0) + 1
    
    print(f"Gameweeks: {sorted(gameweeks.keys())}")
    
    try:
        result = db.table("fixtures").insert(fixtures_data).execute()
        print(f"SUCCESS: Stored {len(fixtures_data)} fixtures for season {settings.DEFAULT_SEASON}")
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    scrape_fixtures()
