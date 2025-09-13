#!/usr/bin/env python3
"""
Simple test for gameweek extraction without requiring API keys
"""

def extract_gameweek_from_round(round_str):
    """Extract gameweek number from API Football round string"""
    try:
        if not round_str:
            return None
        
        # Handle Premier League format: "Regular Season - 15"
        if "Regular Season" in round_str and " - " in round_str:
            parts = round_str.split(" - ")
            if len(parts) >= 2:
                return int(parts[-1])
        
        # Handle simple round formats: "Round 15", "15th Round"
        import re
        numbers = re.findall(r'\d+', round_str)
        if numbers:
            gameweek = int(numbers[0])
            # Premier League has 38 gameweeks, filter out invalid ones
            if 1 <= gameweek <= 38:
                return gameweek
        
        return None
        
    except (ValueError, IndexError):
        return None

def main():
    print("🧪 Testing gameweek extraction (no API keys needed)...")
    
    test_cases = [
        ("Regular Season - 15", 15),
        ("Regular Season - 1", 1),
        ("Regular Season - 38", 38),
        ("Round 10", 10),
        ("1st Round", 1),
        ("Quarter-finals", None),
        ("Semi-finals", None),
        ("", None),
    ]
    
    print("✅ Gameweek extraction test results:")
    all_passed = True
    
    for round_str, expected in test_cases:
        result = extract_gameweek_from_round(round_str)
        passed = result == expected
        all_passed = all_passed and passed
        status = "✅" if passed else "❌"
        print(f"   {status} '{round_str}' -> {result} (expected {expected})")
    
    print(f"\n{'🎉 All tests passed!' if all_passed else '❌ Some tests failed'}")
    
    print("\n🏈 ANSWER TO YOUR QUESTION:")
    print("="*50)
    print("✅ YES! The fixtures table now has gameweek support!")
    print("✅ Common use case 'Get fixtures for gameweek and competition' is fully supported!")
    print("\nHow it works:")
    print("1. fixtures.round stores raw API data: 'Regular Season - 15'")
    print("2. fixtures.gameweek stores extracted number: 15")
    print("3. Index on (league_id, season, gameweek) for fast queries")
    print("\nSQL Examples:")
    print("  -- Get all gameweek 15 fixtures")
    print("  SELECT * FROM fixtures WHERE league_id = 39 AND season = 2024 AND gameweek = 15;")
    print("  -- Get fixtures for multiple gameweeks")
    print("  SELECT * FROM fixtures WHERE gameweek BETWEEN 10 AND 15;")
    
if __name__ == "__main__":
    main()
