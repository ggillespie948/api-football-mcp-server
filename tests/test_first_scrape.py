#!/usr/bin/env python3
"""
First Data Scrape Test
Test scraping real Premier League data into our database
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_api_status():
    """Quick test of API status"""
    print("Checking API Football status...")
    
    import requests
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('RAPID_API_KEY_FOOTBALL')
    if not api_key:
        print("  ERROR: No API key found")
        return False
    
    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    
    try:
        # Test API status endpoint (should be free)
        response = requests.get(
            'https://api-football-v1.p.rapidapi.com/v3/status',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            requests_made = data.get('response', {}).get('requests', {})
            print(f"  SUCCESS: API accessible")
            print(f"  Requests today: {requests_made.get('current', 'unknown')}")
            print(f"  Limit per day: {requests_made.get('limit_day', 'unknown')}")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_premier_league_teams_scrape():
    """Test scraping Premier League teams"""
    print("Testing Premier League teams scrape...")
    
    try:
        from scrapers.base_scraper import BaseScraper
        
        # Create scraper
        scraper = BaseScraper()
        
        # Get Premier League teams
        teams = scraper.get_premier_league_teams()
        
        if teams and len(teams) > 0:
            print(f"  SUCCESS: Scraped {len(teams)} Premier League teams")
            print(f"  Example: {teams[0].get('name', 'Unknown')}")
            return True
        else:
            print("  FAIL: No teams data returned")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_current_gameweek():
    """Test current gameweek detection"""
    print("Testing current gameweek detection...")
    
    try:
        from utils.gameweek_calculator import PremierLeagueGameweekCalculator
        
        calculator = PremierLeagueGameweekCalculator()
        current_gw = calculator.get_current_gameweek(2024)
        
        if current_gw:
            print(f"  SUCCESS: Current gameweek is {current_gw}")
            return True
        else:
            print("  INFO: Could not determine current gameweek (needs fixture data)")
            return True  # This is OK if no fixtures are scraped yet
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def check_database_status():
    """Check current database status"""
    print("Checking database status...")
    
    try:
        from database.connection import get_db_client
        db = get_db_client()
        
        # Check table counts
        tables_to_check = ['teams', 'fixtures', 'leagues', 'request_mode_config']
        
        for table in tables_to_check:
            try:
                result = db.table(table).select("*", count="exact").execute()
                count = result.count if hasattr(result, 'count') else len(result.data or [])
                print(f"  {table}: {count} records")
            except Exception as e:
                print(f"  {table}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    """Run first scrape tests"""
    print("PREMIER LEAGUE MCP SERVER - FIRST DATA SCRAPE TEST")
    print("=" * 60)
    
    # Check current status
    check_database_status()
    print()
    
    # Test API
    api_working = test_api_status()
    print()
    
    if api_working:
        # Try scraping
        teams_scraped = test_premier_league_teams_scrape()
        print()
        
        gameweek_test = test_current_gameweek()
        print()
        
        if teams_scraped:
            print("SUCCESS: Ready to scrape more data!")
            print("NEXT STEPS:")
            print("1. Scrape fixtures: python -c \"from src.scrapers.base_scraper import BaseScraper; s=BaseScraper(); s.get_fixtures_by_gameweek(39, 2024, 15)\"")
            print("2. Check data: SELECT * FROM teams LIMIT 5;")
        else:
            print("WARNING: API issues - check rate limits")
    else:
        print("WARNING: API not accessible - check credentials or wait for rate limit reset")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
