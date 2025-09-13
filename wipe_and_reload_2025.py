#!/usr/bin/env python3
"""
Wipe old data and reload 2025 season
"""

import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, 'src')
from config.settings import get_settings
from database.connection import get_db_client

load_dotenv()

def wipe_and_reload():
    settings = get_settings()
    db = get_db_client()
    
    print("WIPING OLD DATA AND LOADING 2025 SEASON")
    print("=" * 50)
    
    # Step 1: Wipe fixtures first (foreign key constraint)
    print("1. Wiping fixtures...")
    try:
        db.table("fixtures").delete().neq("id", 0).execute()
        print("   SUCCESS: Fixtures wiped")
    except Exception as e:
        print(f"   Error wiping fixtures: {e}")
    
    # Step 2: Wipe teams
    print("2. Wiping teams...")
    try:
        db.table("teams").delete().neq("id", 0).execute()
        print("   SUCCESS: Teams wiped")
    except Exception as e:
        print(f"   Error wiping teams: {e}")
    
    # Step 3: Get 2025 teams
    print("3. Getting 2025 teams...")
    response = requests.get(
        f'{settings.BASE_API_URL}/teams',
        headers=settings.get_api_headers(),
        params={'league': settings.PREMIER_LEAGUE_ID, 'season': settings.DEFAULT_SEASON},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"   API Error: {response.status_code}")
        return False
    
    data = response.json()
    teams_data = []
    
    for team_info in data.get('response', []):
        team = team_info['team']
        venue = team_info.get('venue', {})
        
        teams_data.append({
            'id': team['id'],
            'name': team['name'],
            'code': team.get('code'),
            'country': team.get('country'),
            'founded': team.get('founded'),
            'logo': team.get('logo'),
            'venue_id': venue.get('id'),
            'venue_name': venue.get('name'),
            'venue_capacity': venue.get('capacity')
        })
    
    print(f"   Got {len(teams_data)} teams for season {settings.DEFAULT_SEASON}")
    
    # Step 4: Store teams
    print("4. Storing 2025 teams...")
    try:
        result = db.table("teams").insert(teams_data).execute()
        print(f"   SUCCESS: Stored {len(teams_data)} teams")
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    # Step 5: Get 2025 fixtures
    print("5. Getting 2025 fixtures...")
    response = requests.get(
        f'{settings.BASE_API_URL}/fixtures',
        headers=settings.get_api_headers(),
        params={'league': settings.PREMIER_LEAGUE_ID, 'season': settings.DEFAULT_SEASON},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"   API Error: {response.status_code}")
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
        gameweek = None
        if "Regular Season" in round_str and " - " in round_str:
            try:
                gameweek = int(round_str.split(" - ")[-1])
            except ValueError:
                pass
        
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
    
    print(f"   Got {len(fixtures_data)} fixtures")
    
    # Count gameweeks
    gameweeks = {}
    for f in fixtures_data:
        gw = f['gameweek']
        if gw:
            gameweeks[gw] = gameweeks.get(gw, 0) + 1
    
    print(f"   Gameweeks: {sorted(gameweeks.keys())}")
    
    # Step 6: Store fixtures
    print("6. Storing 2025 fixtures...")
    try:
        result = db.table("fixtures").insert(fixtures_data).execute()
        print(f"   SUCCESS: Stored {len(fixtures_data)} fixtures")
        print("=" * 50)
        print("2025 SEASON DATA LOADED!")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    wipe_and_reload()
