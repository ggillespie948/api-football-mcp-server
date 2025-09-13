#!/usr/bin/env python3
"""
Minimal API Contract Test - Simple and High Value
Tests core functionality without emojis or complex setup
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_gameweek_in_fixtures():
    """Test that fixtures table has gameweek field"""
    print("Testing fixtures schema has gameweek field...")
    
    try:
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'database', 'schema.sql')
        
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        if "gameweek INTEGER" in schema:
            print("  PASS: fixtures table has gameweek field")
            return True
        else:
            print("  FAIL: fixtures table missing gameweek field")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_request_modes():
    """Test request mode system"""
    print("Testing request modes...")
    
    try:
        from config.request_mode_manager import RequestMode
        
        modes = [mode.value for mode in RequestMode]
        expected = ['minimal', 'low', 'standard', 'high', 'maximum']
        
        if set(modes) == set(expected):
            print(f"  PASS: All 5 modes available")
            return True
        else:
            print(f"  FAIL: Mode mismatch")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_enhanced_tools_import():
    """Test enhanced tools can be imported"""
    print("Testing enhanced tools import...")
    
    try:
        # This will fail without API key, but import should work
        from mcp.enhanced_tools import EnhancedMCPTools
        
        print("  PASS: Enhanced tools imported successfully")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_original_soccer_server():
    """Test original soccer_server.py tools"""
    print("Testing original soccer_server.py...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        import soccer_server
        
        # Check key functions exist
        key_functions = [
            'get_league_fixtures',
            'get_standings', 
            'get_player_statistics',
            'get_team_fixtures'
        ]
        
        missing = []
        for func_name in key_functions:
            if not hasattr(soccer_server, func_name):
                missing.append(func_name)
        
        if missing:
            print(f"  FAIL: Missing functions: {missing}")
            return False
        else:
            print(f"  PASS: All {len(key_functions)} key functions found")
            return True
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    """Run minimal tests"""
    print("PREMIER LEAGUE MCP SERVER - MINIMAL CONTRACT TESTS")
    print("=" * 60)
    
    tests = [
        test_gameweek_in_fixtures,
        test_request_modes,
        test_original_soccer_server,
        test_enhanced_tools_import
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("SUCCESS: Core system is ready")
        print("READY FOR: Database setup and credential configuration")
    else:
        print("WARNING: Some core components need attention")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
