#!/usr/bin/env python3
"""
High-Value Integration Test for Premier League MCP Server Setup
Tests core components without making external API calls
"""

import os
import sys
from datetime import datetime

# Add src to path (from tests directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that all core modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from src.config.settings import get_settings, validate_environment
        from src.database.connection import SupabaseManager
        from src.config.request_mode_manager import RequestModeManager, RequestMode
        from src.utils.adaptive_rate_limiter import AdaptiveRateLimiter
        from src.scrapers.base_scraper import BaseScraper
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_settings():
    """Test settings configuration"""
    print("\n🧪 Testing settings configuration...")
    
    try:
        from src.config.settings import get_settings, validate_environment
        
        settings = get_settings()
        print(f"✅ Settings loaded - Premier League ID: {settings.PREMIER_LEAGUE_ID}")
        print(f"✅ Default season: {settings.DEFAULT_SEASON}")
        print(f"✅ Max daily requests: {settings.MAX_DAILY_REQUESTS}")
        
        is_valid, missing = validate_environment()
        if missing:
            print(f"⚠️  Missing environment variables: {', '.join(missing)}")
            print("   This is expected if you haven't set up .env file yet")
        else:
            print("✅ All required environment variables are set")
            
        return True
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def test_request_modes():
    """Test request mode system"""
    print("\n🧪 Testing request mode system...")
    
    try:
        from src.config.request_mode_manager import RequestModeManager, RequestMode, ScalableScheduleManager
        
        # Test enum
        modes = [mode.value for mode in RequestMode]
        print(f"✅ Available modes: {', '.join(modes)}")
        
        # Test schedule manager
        schedule_manager = ScalableScheduleManager()
        comparison = schedule_manager.get_mode_comparison()
        
        print("✅ Mode comparison:")
        for mode, info in comparison.items():
            print(f"   {mode}: {info['daily_budget']} requests/day - {info['description']}")
        
        return True
    except Exception as e:
        print(f"❌ Request mode error: {e}")
        return False

def test_database_connection():
    """Test database connection (without requiring actual connection)"""
    print("\n🧪 Testing database connection setup...")
    
    try:
        from src.database.connection import SupabaseManager
        
        # Test manager creation (won't connect without credentials)
        manager = SupabaseManager()
        connection_info = manager.get_connection_info()
        
        print(f"✅ Database manager created")
        print(f"   Connected: {connection_info['connected']}")
        print(f"   URL configured: {connection_info['url'] != 'Not set'}")
        print(f"   Key configured: {connection_info['has_anon_key']}")
        
        if not connection_info['has_anon_key']:
            print("   ⚠️  No Supabase credentials - this is expected without .env setup")
        
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_rate_limiter():
    """Test rate limiter logic (without database)"""
    print("\n🧪 Testing rate limiter logic...")
    
    try:
        from src.utils.adaptive_rate_limiter import AdaptiveRateLimiter
        
        # Create rate limiter (will fail gracefully without DB)
        limiter = AdaptiveRateLimiter()
        
        print("✅ Rate limiter created")
        print(f"   Hard limit: {limiter.hard_limit}")
        print(f"   Emergency threshold: {limiter.emergency_threshold}")
        print(f"   Warning threshold: {limiter.warning_threshold}")
        
        return True
    except Exception as e:
        print(f"❌ Rate limiter error: {e}")
        return False

def print_setup_instructions():
    """Print setup instructions for the user"""
    print("\n" + "="*60)
    print("🚀 SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n1. Create Supabase Project:")
    print("   - Go to https://supabase.com")
    print("   - Create a new project")
    print("   - Copy your project URL and anon key")
    
    print("\n2. Get API Football Key:")
    print("   - Go to https://rapidapi.com/api-sports/api/api-football/")
    print("   - Subscribe to the API")
    print("   - Copy your RapidAPI key")
    
    print("\n3. Set up environment file:")
    print("   - Create a .env file in the project root")
    print("   - Add your credentials:")
    print("     SUPABASE_URL=https://your-project-id.supabase.co")
    print("     SUPABASE_ANON_KEY=your_anon_key_here")
    print("     RAPID_API_KEY_FOOTBALL=your_rapidapi_key_here")
    
    print("\n4. Set up database:")
    print("   - Run the SQL from src/database/schema.sql in your Supabase project")
    
    print("\n5. Test connection:")
    print("   - python test_setup.py --full")

def main():
    """Run all tests"""
    print("🏈 Premier League MCP Server - Setup Validation")
    print("="*60)
    
    tests = [
        test_imports,
        test_settings,
        test_request_modes,
        test_database_connection,
        test_rate_limiter
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "="*60)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Core setup is working.")
        if '--full' not in sys.argv:
            print_setup_instructions()
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
