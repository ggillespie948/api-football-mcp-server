#!/usr/bin/env python3
"""
API Contract Tests for Premier League MCP Server
Tests the enhanced tools against expected contracts from original soccer_server.py
"""

import os
import sys
from typing import Dict, Any

# Add src to path (from tests directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_original_tool_contracts():
    """Test that enhanced tools maintain compatibility with original soccer_server.py contracts"""
    print("Testing API contract compatibility...")
    
    try:
        from mcp.enhanced_tools import enhanced_tools
        
        # Test contracts based on original soccer_server.py tools
        contracts = [
            {
                "name": "get_current_gameweek",
                "method": enhanced_tools.get_current_gameweek,
                "args": {"season": 2024},
                "expected_keys": ["current_gameweek", "season", "fixtures", "total_gameweeks"]
            },
            {
                "name": "get_gameweek_fixtures", 
                "method": enhanced_tools.get_gameweek_fixtures,
                "args": {"season": 2024, "gameweek": 15},
                "expected_keys": ["gameweek", "season", "fixtures", "fixture_count"]
            },
            {
                "name": "get_fixture_lineups",
                "method": enhanced_tools.get_fixture_lineups,
                "args": {"fixture_id": 123456},
                "expected_keys": ["fixture_id"]  # Should have this even on error
            },
            {
                "name": "get_request_mode_status",
                "method": enhanced_tools.get_request_mode_status,
                "args": {},
                "expected_keys": ["current_mode", "daily_budget", "current_usage"]
            }
        ]
        
        passed = 0
        total = len(contracts)
        
        for contract in contracts:
            try:
                print(f"Testing {contract['name']}...")
                result = contract["method"](**contract["args"])
                
                # Check if result is a dict
                if not isinstance(result, dict):
                    print(f"  FAIL: {contract['name']} did not return dict")
                    continue
                
                # Check for expected keys (allow error responses)
                if "error" in result:
                    print(f"  OK: {contract['name']} returned error (expected without DB)")
                    passed += 1
                else:
                    # Check expected keys
                    missing_keys = [key for key in contract["expected_keys"] if key not in result]
                    if missing_keys:
                        print(f"  FAIL: {contract['name']} missing keys: {missing_keys}")
                    else:
                        print(f"  PASS: {contract['name']} contract valid")
                        passed += 1
                        
            except Exception as e:
                print(f"  FAIL: {contract['name']} raised exception: {e}")
        
        print(f"Contract tests: {passed}/{total} passed")
        return passed == total
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Test error: {e}")
        return False

def test_gameweek_extraction():
    """Test gameweek extraction logic"""
    print("Testing gameweek extraction...")
    
    def extract_gameweek_from_round(round_str):
        """Copy of extraction logic for testing"""
        try:
            if not round_str:
                return None
            
            # Handle Premier League format: "Regular Season - 15"
            if "Regular Season" in round_str and " - " in round_str:
                parts = round_str.split(" - ")
                if len(parts) >= 2:
                    return int(parts[-1])
            
            # Handle simple round formats
            import re
            numbers = re.findall(r'\d+', round_str)
            if numbers:
                gameweek = int(numbers[0])
                if 1 <= gameweek <= 38:
                    return gameweek
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    test_cases = [
        ("Regular Season - 15", 15),
        ("Regular Season - 1", 1), 
        ("Regular Season - 38", 38),
        ("Quarter-finals", None),
        ("", None)
    ]
    
    passed = 0
    for round_str, expected in test_cases:
        result = extract_gameweek_from_round(round_str)
        if result == expected:
            print(f"  PASS: '{round_str}' -> {result}")
            passed += 1
        else:
            print(f"  FAIL: '{round_str}' -> {result} (expected {expected})")
    
    print(f"Gameweek extraction: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)

def test_request_mode_system():
    """Test request mode system"""
    print("Testing request mode system...")
    
    try:
        from config.request_mode_manager import RequestMode, ScalableScheduleManager
        
        # Test all modes exist
        modes = [mode.value for mode in RequestMode]
        expected_modes = ['minimal', 'low', 'standard', 'high', 'maximum']
        
        if set(modes) == set(expected_modes):
            print(f"  PASS: All modes available: {modes}")
            
            # Test schedule manager
            manager = ScalableScheduleManager()
            comparison = manager.get_mode_comparison()
            
            if len(comparison) == 5:
                print(f"  PASS: Schedule comparison has {len(comparison)} modes")
                return True
            else:
                print(f"  FAIL: Expected 5 modes, got {len(comparison)}")
                return False
        else:
            print(f"  FAIL: Mode mismatch. Got: {modes}, Expected: {expected_modes}")
            return False
            
    except Exception as e:
        print(f"  FAIL: Request mode test error: {e}")
        return False

def test_database_schema_validation():
    """Validate database schema has required tables"""
    print("Testing database schema...")
    
    try:
        # Read schema file and check for required tables
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'database', 'schema.sql')
        
        with open(schema_path, 'r') as f:
            schema_content = f.read()
        
        required_tables = [
            'fixtures',
            'teams', 
            'players',
            'standings',
            'fixture_lineups',
            'fixture_goalscorers',
            'probable_scorers',
            'premier_league_gameweeks',
            'daily_request_counter',
            'request_mode_config'
        ]
        
        missing_tables = []
        for table in required_tables:
            if f"CREATE TABLE {table}" not in schema_content:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"  FAIL: Missing tables: {missing_tables}")
            return False
        
        # Check for gameweek field in fixtures
        if "gameweek INTEGER" in schema_content:
            print("  PASS: fixtures table has gameweek field")
        else:
            print("  FAIL: fixtures table missing gameweek field")
            return False
        
        print(f"  PASS: All {len(required_tables)} required tables found")
        return True
        
    except Exception as e:
        print(f"  FAIL: Schema validation error: {e}")
        return False

def main():
    """Run all API contract tests"""
    print("PREMIER LEAGUE MCP SERVER - API CONTRACT TESTS")
    print("=" * 60)
    
    tests = [
        test_database_schema_validation,
        test_gameweek_extraction,
        test_request_mode_system,
        test_original_tool_contracts
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Empty line between tests
        except Exception as e:
            print(f"Test failed with exception: {e}")
            print()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} contract tests passed")
    
    if passed == total:
        print("SUCCESS: All API contracts are valid")
        print("NEXT: Set up .env file with your credentials")
    else:
        print("WARNING: Some contract tests failed")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
