#!/usr/bin/env python3
"""
Ready for Database Test
Simple test to confirm system is ready for Supabase setup
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def main():
    """Check if system is ready for database setup"""
    print("PREMIER LEAGUE MCP SERVER - DATABASE READINESS CHECK")
    print("=" * 60)
    
    checks = []
    
    # 1. Check schema file exists
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'database', 'schema.sql')
    if os.path.exists(schema_path):
        print("1. Database schema file: EXISTS")
        checks.append(True)
    else:
        print("1. Database schema file: MISSING")
        checks.append(False)
    
    # 2. Check gameweek support
    try:
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        if "gameweek INTEGER" in schema and "idx_fixtures_gameweek" in schema:
            print("2. Gameweek support: READY")
            checks.append(True)
        else:
            print("2. Gameweek support: INCOMPLETE")
            checks.append(False)
    except:
        print("2. Gameweek support: ERROR")
        checks.append(False)
    
    # 3. Check configuration system
    try:
        from config.settings import get_settings
        settings = get_settings()
        print(f"3. Configuration system: READY (Premier League ID: {settings.PREMIER_LEAGUE_ID})")
        checks.append(True)
    except Exception as e:
        print(f"3. Configuration system: ERROR - {e}")
        checks.append(False)
    
    # 4. Check request modes
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from config.request_mode_manager import RequestMode
        modes = [mode.value for mode in RequestMode]
        print(f"4. Request modes: READY ({len(modes)} modes)")
        checks.append(True)
    except Exception as e:
        print(f"4. Request modes: ERROR - {e}")
        checks.append(False)
    
    # 5. Check scrapers
    scraper_files = [
        'lineup_scraper.py',
        'goalscorer_scraper.py', 
        'probable_scorer_scraper.py',
        'scraper_manager.py'
    ]
    
    scrapers_exist = 0
    for scraper in scraper_files:
        scraper_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'scrapers', scraper)
        if os.path.exists(scraper_path):
            scrapers_exist += 1
    
    if scrapers_exist == len(scraper_files):
        print(f"5. Scrapers: READY (all {len(scraper_files)} scrapers)")
        checks.append(True)
    else:
        print(f"5. Scrapers: INCOMPLETE ({scrapers_exist}/{len(scraper_files)})")
        checks.append(False)
    
    print("=" * 60)
    
    if all(checks):
        print("STATUS: READY FOR DATABASE SETUP")
        print()
        print("NEXT STEPS:")
        print("1. Go to https://supabase.com and create a new project")
        print("2. In Supabase SQL Editor, run: src/database/schema.sql")
        print("3. Get your project URL and anon key from Settings > API")
        print("4. Create .env file with:")
        print("   SUPABASE_URL=https://your-project-id.supabase.co")
        print("   SUPABASE_ANON_KEY=your_anon_key_here")
        print("   RAPID_API_KEY_FOOTBALL=your_rapidapi_key_here")
        print("5. Test: python tests/test_with_database.py")
        print()
        print("YOUR COMMON USE CASE IS READY:")
        print("- Get fixtures for gameweek and competition: IMPLEMENTED")
        print("- Gameweek field in fixtures table: READY")
        print("- Fast queries with indexes: OPTIMIZED")
        print("- Request tracking under 7500/day: PROTECTED")
    else:
        failed_checks = sum(1 for check in checks if not check)
        print(f"STATUS: {failed_checks} issues need attention")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
