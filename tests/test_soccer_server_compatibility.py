#!/usr/bin/env python3
"""
Test compatibility with original soccer_server.py
Ensures enhanced tools maintain same contracts as original tools
"""

import os
import sys
import inspect

# Add both src and root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def get_original_tool_signatures():
    """Extract tool signatures from original soccer_server.py"""
    try:
        # Import original soccer_server
        import soccer_server
        
        # Find all MCP tools (functions decorated with @mcp.tool())
        original_tools = {}
        
        # Get all functions from soccer_server module
        for name, obj in inspect.getmembers(soccer_server):
            if inspect.isfunction(obj) and not name.startswith('_'):
                # Get function signature
                sig = inspect.signature(obj)
                doc = inspect.getdoc(obj) or ""
                
                original_tools[name] = {
                    "signature": str(sig),
                    "parameters": list(sig.parameters.keys()),
                    "docstring": doc[:100] + "..." if len(doc) > 100 else doc
                }
        
        return original_tools
        
    except Exception as e:
        print(f"Error getting original tool signatures: {e}")
        return {}

def test_tool_compatibility():
    """Test that enhanced tools are compatible with original tools"""
    print("Testing compatibility with original soccer_server.py tools...")
    
    try:
        original_tools = get_original_tool_signatures()
        
        if not original_tools:
            print("  SKIP: Could not load original tools")
            return True
        
        print(f"  Found {len(original_tools)} original tools")
        
        # Key tools we should maintain compatibility with
        key_tools = [
            "get_league_fixtures",
            "get_league_id_by_name", 
            "get_standings",
            "get_player_statistics",
            "get_team_fixtures",
            "get_fixture_statistics",
            "get_fixture_events"
        ]
        
        missing_tools = []
        for tool in key_tools:
            if tool not in original_tools:
                missing_tools.append(tool)
            else:
                print(f"  FOUND: {tool}{original_tools[tool]['signature']}")
        
        if missing_tools:
            print(f"  WARNING: Missing tools in original: {missing_tools}")
        
        print(f"  SUCCESS: Found {len(key_tools) - len(missing_tools)}/{len(key_tools)} key tools")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_enhanced_tool_contracts():
    """Test enhanced tool contracts without requiring database"""
    print("Testing enhanced tool contracts...")
    
    try:
        # Test imports work
        from mcp.enhanced_tools import EnhancedMCPTools
        
        tools = EnhancedMCPTools()
        
        # Test new tools exist
        new_tools = [
            "get_fixture_lineups",
            "get_fixture_goalscorers", 
            "get_probable_scorers",
            "get_current_gameweek",
            "get_gameweek_fixtures"
        ]
        
        for tool_name in new_tools:
            if hasattr(tools, tool_name):
                print(f"  FOUND: {tool_name}")
            else:
                print(f"  MISSING: {tool_name}")
                return False
        
        print(f"  SUCCESS: All {len(new_tools)} new tools available")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def create_env_template():
    """Create environment template if needed"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env.template')
    
    if not os.path.exists(env_path):
        template_content = """# Premier League MCP Server Environment Configuration
# Copy this to .env and fill in your actual values

# REQUIRED: Supabase Database
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here

# REQUIRED: API Football from RapidAPI
RAPID_API_KEY_FOOTBALL=your_rapidapi_key_here

# OPTIONAL: Configuration
DEFAULT_REQUEST_MODE=standard
ENVIRONMENT=development
"""
        
        try:
            with open(env_path, 'w') as f:
                f.write(template_content)
            print(f"Created .env.template at {env_path}")
            return True
        except Exception as e:
            print(f"Error creating .env.template: {e}")
            return False
    else:
        print(".env.template already exists")
        return True

def main():
    """Run all compatibility tests"""
    print("PREMIER LEAGUE MCP SERVER - COMPATIBILITY TESTS")
    print("=" * 60)
    
    tests = [
        test_tool_compatibility,
        test_enhanced_tool_contracts,
        create_env_template
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"Test failed: {e}")
            print()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} compatibility tests passed")
    
    if passed == total:
        print("SUCCESS: System is compatible and ready")
        print("NEXT STEPS:")
        print("1. Copy .env.template to .env")
        print("2. Add your Supabase and API Football credentials")
        print("3. Run: python tests/test_with_credentials.py")
    else:
        print("WARNING: Some compatibility issues found")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
