#!/usr/bin/env python3
"""
Fix Teams for 2025 Season
"""

import sys
import requests
from dotenv import load_dotenv
import os

sys.path.insert(0, 'src')
from config.settings import get_settings
from database.connection import get_db_client

load_dotenv()

def get_2025_teams():
    settings = get_settings()
    
    print(f"Getting 2025 season teams...")
    
    response = requests.get(
        f'{settings.BASE_API_URL}/teams',
        headers=settings.get_api_headers(),
        params={'league': settings.PREMIER_LEAGUE_ID, 'season': settings.DEFAULT_SEASON},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        teams = data.get('response', [])
        print(f'2025 season: {len(teams)} teams')
        
        team_ids = []
        for team_info in teams:
            team = team_info['team']
            team_ids.append(team['id'])
            print(f'  {team["id"]}: {team["name"]}')
        
        return team_ids
    else:
        print(f'Error: {response.status_code}')
        return []

def check_existing_teams():
    db = get_db_client()
    
    result = db.table("teams").select("id, name").execute()
    existing_ids = [team['id'] for team in result.data]
    
    print(f"Existing teams in database: {len(existing_ids)}")
    print(f"IDs: {sorted(existing_ids)}")
    
    return existing_ids

if __name__ == "__main__":
    print("CHECKING 2025 TEAMS")
    print("=" * 40)
    
    api_team_ids = get_2025_teams()
    print()
    
    db_team_ids = check_existing_teams()
    print()
    
    missing = set(api_team_ids) - set(db_team_ids)
    extra = set(db_team_ids) - set(api_team_ids)
    
    if missing:
        print(f"Missing team IDs: {missing}")
    if extra:
        print(f"Extra team IDs: {extra}")
    
    if not missing and not extra:
        print("Teams match! Ready for fixtures.")
    else:
        print("Teams don't match - need to update database")
    
    print("=" * 40)
