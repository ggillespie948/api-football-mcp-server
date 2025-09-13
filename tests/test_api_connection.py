#!/usr/bin/env python3
"""
Test API Football Connection
Simple test to verify API connectivity and get some real data
"""

import requests
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_api_football_connection():
    """Test connection to API Football"""
    print("Testing API Football connection...")
    
    api_key = os.getenv('RAPID_API_KEY_FOOTBALL')
    if not api_key:
        print("  SKIP: No API key found")
        return False
    
    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    
    try:
        # Test with Premier League teams
        response = requests.get(
            'https://api-football-v1.p.rapidapi.com/v3/teams',
            headers=headers,
            params={'league': 39, 'season': 2024},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            teams = data.get('response', [])
            print(f"  SUCCESS: Got {len(teams)} Premier League teams")
            
            if teams:
                print(f"  Example team: {teams[0]['team']['name']}")
                print(f"  API requests remaining: {response.headers.get('x-ratelimit-requests-remaining', 'Unknown')}")
            
            return True
        else:
            print(f"  FAIL: API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_current_gameweek_api():
    """Test getting current gameweek from API"""
    print("Testing current gameweek API...")
    
    api_key = os.getenv('RAPID_API_KEY_FOOTBALL')
    if not api_key:
        print("  SKIP: No API key found")
        return False
    
    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    
    try:
        # Get next few fixtures to determine current gameweek
        response = requests.get(
            'https://api-football-v1.p.rapidapi.com/v3/fixtures',
            headers=headers,
            params={'league': 39, 'season': 2024, 'next': 5},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get('response', [])
            
            if fixtures:
                # Extract gameweek from first fixture
                round_str = fixtures[0]['league']['round']
                print(f"  SUCCESS: Next fixture round: {round_str}")
                
                # Extract gameweek
                if "Regular Season" in round_str and " - " in round_str:
                    gameweek = int(round_str.split(" - ")[-1])
                    print(f"  Current/Next gameweek: {gameweek}")
                    return True
                else:
                    print(f"  WARNING: Unexpected round format: {round_str}")
                    return True  # Still success, just different format
            else:
                print("  WARNING: No upcoming fixtures found")
                return True
        else:
            print(f"  FAIL: API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    """Run API tests"""
    print("PREMIER LEAGUE MCP SERVER - API CONNECTION TESTS")
    print("=" * 60)
    
    tests = [
        test_api_football_connection,
        test_current_gameweek_api
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} API tests passed")
    
    if passed == len(tests):
        print("SUCCESS: API connection working")
        print("READY: System can fetch real Premier League data")
        print("NEXT: Test full system integration")
    else:
        print("WARNING: API connection issues")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
