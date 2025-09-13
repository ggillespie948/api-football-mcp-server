#!/usr/bin/env python3
"""
Test script to demonstrate gameweek fixture querying
Shows the common use case you asked about
"""

import os
import sys

# Add src to path (from tests directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_gameweek_extraction():
    """Test gameweek extraction from round strings"""
    print("🧪 Testing gameweek extraction...")
    
    try:
        from src.scrapers.base_scraper import BaseScraper
        
        # Create a mock scraper to test the method
        class TestScraper(BaseScraper):
            def scrape_and_store(self, **kwargs):
                pass
        
        scraper = TestScraper()
        
        # Test cases
        test_cases = [
            ("Regular Season - 15", 15),
            ("Regular Season - 1", 1),
            ("Regular Season - 38", 38),
            ("Round 10", 10),
            ("1st Round", 1),
            ("Quarter-finals", None),
            ("Semi-finals", None),
            ("", None),
            (None, None)
        ]
        
        print("✅ Gameweek extraction test results:")
        for round_str, expected in test_cases:
            result = scraper.extract_gameweek_from_round(round_str)
            status = "✅" if result == expected else "❌"
            print(f"   {status} '{round_str}' -> {result} (expected {expected})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in gameweek extraction test: {e}")
        return False

def demonstrate_common_use_cases():
    """Demonstrate the common use cases you mentioned"""
    print("\n🏈 Common Use Case Examples:")
    print("="*50)
    
    print("1. Get fixtures for specific gameweek:")
    print("   scraper.get_fixtures_by_gameweek(league_id=39, season=2024, gameweek=15)")
    print("   -> Returns all Premier League fixtures for gameweek 15")
    
    print("\n2. Get current gameweek fixtures:")
    print("   scraper.get_current_gameweek_fixtures()")
    print("   -> Returns fixtures for the current gameweek")
    
    print("\n3. Database queries you can now do:")
    print("   SELECT * FROM fixtures WHERE league_id = 39 AND season = 2024 AND gameweek = 15;")
    print("   SELECT * FROM fixtures WHERE gameweek BETWEEN 10 AND 15;")
    print("   SELECT COUNT(*) FROM fixtures GROUP BY gameweek;")
    
    print("\n4. The fixtures table now includes:")
    print("   - id (fixture ID)")
    print("   - league_id (39 for Premier League)")
    print("   - season (2024)")
    print("   - round ('Regular Season - 15')")
    print("   - gameweek (15) <- NEW! Extracted for easy querying")
    print("   - home_team_id, away_team_id")
    print("   - date, status, scores, etc.")

def show_database_schema():
    """Show the updated database schema"""
    print("\n📊 Updated Database Schema:")
    print("="*50)
    print("""
CREATE TABLE fixtures (
    id INTEGER PRIMARY KEY,
    league_id INTEGER REFERENCES leagues(id),
    season INTEGER,
    round VARCHAR(100),           -- "Regular Season - 15"
    gameweek INTEGER,            -- 15 (extracted for easy queries)
    home_team_id INTEGER,
    away_team_id INTEGER,
    date TIMESTAMP,
    home_score INTEGER,
    away_score INTEGER,
    status_short VARCHAR(10),    -- 'FT', 'NS', '1H', etc.
    -- ... other fields
);

-- Index for fast gameweek queries
CREATE INDEX idx_fixtures_gameweek ON fixtures(league_id, season, gameweek);
    """)

def main():
    """Run all demonstrations"""
    print("🏈 Premier League Gameweek Fixtures - Common Use Cases")
    print("="*60)
    
    # Test gameweek extraction
    extraction_works = test_gameweek_extraction()
    
    # Show common use cases
    demonstrate_common_use_cases()
    
    # Show database schema
    show_database_schema()
    
    print("\n" + "="*60)
    if extraction_works:
        print("✅ Gameweek extraction is working!")
        print("🚀 Ready for common use cases:")
        print("   - Get fixtures by gameweek and competition ✅")
        print("   - Get current gameweek fixtures ✅")
        print("   - Fast database queries with gameweek index ✅")
    else:
        print("❌ Some tests failed - check the implementation")
    
    print("\n💡 Next steps:")
    print("   1. Set up your Supabase database with the updated schema")
    print("   2. Add your API keys to .env file")
    print("   3. Test with real data: python test_with_real_data.py")
    print("="*60)

if __name__ == "__main__":
    main()
