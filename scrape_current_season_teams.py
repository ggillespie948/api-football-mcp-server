#!/usr/bin/env python3
"""
Scrape Current Season Teams using Global Settings
"""

import sys
sys.path.insert(0, 'src')

from config.settings import get_settings
from database.connection import get_db_client
import requests

def scrape_teams():
    settings = get_settings()
    db = get_db_client()
    
    print(f"Scraping Premier League teams for season {settings.DEFAULT_SEASON}...")
    
    response = requests.get(
        f'{settings.BASE_API_URL}/teams',
        headers=settings.get_api_headers(),
        params={'league': settings.PREMIER_LEAGUE_ID, 'season': settings.DEFAULT_SEASON},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
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
    
    print(f"Prepared {len(teams_data)} teams for season {settings.DEFAULT_SEASON}")
    
    try:
        result = db.table("teams").insert(teams_data).execute()
        print(f"SUCCESS: Stored {len(teams_data)} teams")
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    scrape_teams()
