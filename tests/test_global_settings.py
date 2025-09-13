#!/usr/bin/env python3
"""
Test Global Settings Working Everywhere
"""

import sys
sys.path.insert(0, 'src')

def test_global_settings():
    from config.settings import get_settings
    
    settings = get_settings()
    
    print("GLOBAL SETTINGS:")
    print(f"Premier League ID: {settings.PREMIER_LEAGUE_ID}")
    print(f"Default Season: {settings.DEFAULT_SEASON}")
    print(f"API URL: {settings.BASE_API_URL}")
    print(f"Max Daily Requests: {settings.MAX_DAILY_REQUESTS}")
    
    return settings

def test_base_scraper_uses_settings():
    try:
        from scrapers.base_scraper import BaseScraper
        scraper = BaseScraper()
        
        print(f"Base Scraper Season: {scraper.current_season}")
        print(f"Base Scraper League: {scraper.premier_league_id}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def show_current_data():
    from database.connection import get_db_client
    db = get_db_client()
    
    # Show what data we have
    result = db.table("fixtures").select("season, COUNT(*) as count").execute()
    
    print("CURRENT DATABASE:")
    for row in result.data:
        print(f"  Season {row.get('season', 'unknown')}: {row.get('count', 0)} fixtures")

if __name__ == "__main__":
    print("TESTING GLOBAL SETTINGS")
    print("=" * 40)
    
    settings = test_global_settings()
    print()
    
    scraper_test = test_base_scraper_uses_settings() 
    print()
    
    show_current_data()
    print()
    
    print("NEXT: Integrate with soccer_server.py MCP tools")
    print("=" * 40)
