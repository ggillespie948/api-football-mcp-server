#!/usr/bin/env python3
"""
Test Phase 2 Endpoints Locally
Test the new squad, H2H, and form endpoints
"""

import requests
import time
import sys

def test_server_status():
    """Test if server is running"""
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server running: {data.get('message', 'Unknown')}")
            print(f"   Season: {data.get('season', 'Unknown')}")
            print(f"   Protocols: {data.get('protocols', ['Unknown'])}")
            return True
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False

def test_existing_endpoints():
    """Test existing endpoints that should work"""
    print("\n📊 Testing Existing Endpoints:")
    
    endpoints = [
        "/api/current-gameweek",
        "/api/todays-fixtures", 
        "/api/gameweek/4/fixtures",
        "/health"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"   ⚠️  {endpoint}: {data['error']}")
                else:
                    print(f"   ✅ {endpoint}: Working")
            else:
                print(f"   ❌ {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: {e}")

def test_phase2_endpoints():
    """Test new Phase 2 endpoints"""
    print("\n🆕 Testing Phase 2 Endpoints:")
    
    # Test endpoints that should work with existing data
    endpoints = [
        ("/api/team/Arsenal/last5", "Arsenal's last 5 results"),
        ("/api/teams/Arsenal/vs/Chelsea/h2h", "Arsenal vs Chelsea H2H"),
        ("/api/standings/form", "League table with form")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"   ⚠️  {endpoint}: {data['error']}")
                else:
                    print(f"   ✅ {endpoint}: Working - {description}")
                    
                    # Show sample data
                    if "form" in data:
                        print(f"      Form: {data.get('form', 'N/A')}")
                    if "h2h_summary" in data:
                        summary = data["h2h_summary"]
                        print(f"      H2H: {summary.get('total_matches', 0)} matches")
                    if "standings_with_form" in data:
                        print(f"      Standings: {len(data['standings_with_form'])} teams")
            else:
                print(f"   ❌ {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: {e}")

def test_squad_endpoint():
    """Test squad endpoint (will likely need data)"""
    print("\n👥 Testing Squad Endpoint:")
    
    try:
        response = requests.get("http://localhost:5000/api/team/Arsenal/squad", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "squad" in data and data["squad"]:
                print(f"   ✅ Arsenal squad: {data.get('squad_size', 0)} players")
            else:
                print(f"   ⚠️  Arsenal squad: No squad data (needs scraping)")
        else:
            print(f"   ❌ Squad endpoint: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Squad endpoint: {e}")

def main():
    """Run all Phase 2 tests"""
    print("TESTING PHASE 2 ENDPOINTS LOCALLY")
    print("=" * 50)
    
    # Test server status
    if not test_server_status():
        print("\n❌ Server not running. Start with: python hybrid_server.py")
        return False
    
    # Test existing endpoints
    test_existing_endpoints()
    
    # Test Phase 2 endpoints
    test_phase2_endpoints()
    
    # Test squad endpoint
    test_squad_endpoint()
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS:")
    print("1. Run Phase 2 database schema: src/database/schema_phase2.sql")
    print("2. Scrape squad data for teams")
    print("3. Test MCP protocol (fix FastMCP import)")
    print("4. Deploy to production")
    print("=" * 50)

if __name__ == "__main__":
    main()
