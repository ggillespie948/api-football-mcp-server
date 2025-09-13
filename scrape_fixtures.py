#!/usr/bin/env python3
"""
Simple Premier League Fixtures Scraper
"""

import requests
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_client

load_dotenv()

def extract_gameweek_from_round(round_str):
    """Extract gameweek from round string"""
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

def scrape_and_store_fixtures():
    """Scrape Premier League fixtures and store in database"""
    
    api_key = os.getenv('RAPID_API_KEY_FOOTBALL')
    db = get_db_client()
    
    print("Scraping Premier League fixtures...")
    
    # Get fixtures from API
    response = requests.get(
        'https://v3.football.api-sports.io/fixtures',
        headers={'x-apisports-key': api_key},
        params={'league': 39, 'season': 2025},
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
        
        # Extract gameweek
        round_str = league.get('round', '')
        gameweek = extract_gameweek_from_round(round_str)
        
        fixtures_data.append({
            'id': fixture['id'],
            'referee': fixture.get('referee'),
            'timezone': fixture.get('timezone'),
            'date': fixture.get('date'),
            'timestamp': fixture.get('timestamp'),
            'league_id': league['id'],
            'season': league['season'],
            'round': round_str,
            'gameweek': gameweek,
            'home_team_id': teams['home']['id'],
            'away_team_id': teams['away']['id'],
            'home_score': goals.get('home'),
            'away_score': goals.get('away'),
            'status_long': fixture['status']['long'],
            'status_short': fixture['status']['short'],
            'status_elapsed': fixture['status'].get('elapsed'),
            'venue_id': fixture.get('venue', {}).get('id'),
            'venue_name': fixture.get('venue', {}).get('name'),
            'venue_city': fixture.get('venue', {}).get('city')
        })
    
    print(f"Prepared {len(fixtures_data)} fixtures")
    
    # Count gameweeks
    gameweeks = {}
    for fixture in fixtures_data:
        gw = fixture['gameweek']
        if gw:
            gameweeks[gw] = gameweeks.get(gw, 0) + 1
    
    print(f"Gameweeks found: {sorted(gameweeks.keys())}")
    print(f"Example: Gameweek 1 has {gameweeks.get(1, 0)} fixtures")
    
    # Store in database
    try:
        result = db.table("fixtures").insert(fixtures_data).execute()
        print(f"SUCCESS: Stored {len(fixtures_data)} fixtures")
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    success = scrape_and_store_fixtures()
    if success:
        print("NEXT: Test your common use case!")
        print("SELECT * FROM fixtures WHERE league_id = 39 AND season = 2024 AND gameweek = 15;")
    else:
        print("FAILED: Check errors above")
