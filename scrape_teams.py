#!/usr/bin/env python3
"""
Simple Premier League Teams Scraper
"""

import requests
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_client

load_dotenv()

def scrape_and_store_teams():
    """Scrape Premier League teams and store in database"""
    
    api_key = os.getenv('RAPID_API_KEY_FOOTBALL')
    db = get_db_client()
    
    print("Scraping Premier League teams...")
    
    # Get settings
    sys.path.insert(0, 'src')
    from config.settings import get_settings
    settings = get_settings()
    
    # Get teams from API using global settings
    response = requests.get(
        settings.BASE_API_URL + '/teams',
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
    
    # Store in database
    try:
        result = db.table("teams").insert(teams_data).execute()
        print(f"SUCCESS: Stored {len(teams_data)} teams in database")
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    success = scrape_and_store_teams()
    if success:
        print("NEXT: Check database - SELECT * FROM teams LIMIT 5;")
    else:
        print("FAILED: Check API key and database permissions")
