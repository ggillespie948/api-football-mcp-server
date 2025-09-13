"""
Premier League Gameweek Calculator
Handles dynamic gameweek detection and management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from src.database.connection import SupabaseManager
from src.scrapers.base_scraper import BaseScraper


class PremierLeagueGameweekCalculator(BaseScraper):
    """Calculator for Premier League gameweek detection and management"""
    
    def __init__(self):
        super().__init__()
        self.total_gameweeks = 38
    
    def scrape_and_store(self, **kwargs) -> Dict[str, Any]:
        """Implementation of abstract method - updates current gameweek"""
        season = kwargs.get("season", self.current_season)
        return self.update_current_gameweek(season)
    
    def get_current_gameweek(self, season: int = None) -> Optional[int]:
        """
        Get the current Premier League gameweek
        
        Args:
            season: The season year (defaults to current season)
            
        Returns:
            Current gameweek number or None if not found
        """
        season = season or self.current_season
        
        try:
            # Check cached gameweek first
            cached = self.db.client.table("premier_league_gameweeks").select("*").eq("season", season).eq("is_current", True).execute()
            
            if cached.data and len(cached.data) > 0:
                gw_data = cached.data[0]
                gw_start = datetime.fromisoformat(gw_data['start_date'].replace('Z', '+00:00'))
                gw_end = datetime.fromisoformat(gw_data['end_date'].replace('Z', '+00:00'))
                now = datetime.now().replace(tzinfo=gw_start.tzinfo)
                
                # Check if we're still in this gameweek
                if gw_start <= now <= gw_end:
                    print(f"✅ Current gameweek from cache: {gw_data['gameweek']}")
                    return gw_data['gameweek']
                else:
                    print("⚠️ Cached gameweek is outdated, recalculating...")
            
            # Calculate dynamically from fixtures
            return self._calculate_current_gameweek_from_fixtures(season)
            
        except Exception as e:
            print(f"❌ Error getting current gameweek: {e}")
            return None
    
    def _calculate_current_gameweek_from_fixtures(self, season: int) -> Optional[int]:
        """
        Calculate current gameweek based on fixture dates
        
        Args:
            season: The season year
            
        Returns:
            Current gameweek number or None
        """
        try:
            # Get all Premier League fixtures for the season
            fixtures = self.get_cached_data(
                "fixtures",
                {"league_id": self.premier_league_id, "season": season},
                max_age_hours=6
            )
            
            if not fixtures:
                print("🔄 No cached fixtures, fetching from API...")
                # Fetch fixtures from API
                response = self.make_api_request(
                    "fixtures",
                    {"league": self.premier_league_id, "season": season},
                    priority="high"
                )
                
                if "error" in response:
                    print(f"❌ Error fetching fixtures: {response['error']}")
                    return None
                
                # Process fixtures and extract gameweeks
                fixtures = []
                for fixture_data in response.get("response", []):
                    fixture = fixture_data.get("fixture", {})
                    league = fixture_data.get("league", {})
                    
                    round_str = league.get("round", "")
                    gameweek = self.extract_gameweek_from_round(round_str)
                    
                    if gameweek:
                        fixtures.append({
                            "id": fixture.get("id"),
                            "date": fixture.get("date"),
                            "gameweek": gameweek,
                            "round": round_str,
                            "status_short": fixture.get("status", {}).get("short")
                        })
                
                # Store fixtures (simplified version)
                if fixtures:
                    print(f"✅ Processed {len(fixtures)} fixtures")
            
            # Find current gameweek based on dates
            now = datetime.now()
            
            # Group fixtures by gameweek
            gameweeks = {}
            for fixture in fixtures:
                gw = fixture["gameweek"]
                if gw and gw not in gameweeks:
                    gameweeks[gw] = []
                gameweeks[gw].append(fixture)
            
            # Find current gameweek
            for gameweek in sorted(gameweeks.keys()):
                gw_fixtures = gameweeks[gameweek]
                
                # Get date range for this gameweek
                fixture_dates = [datetime.fromisoformat(f["date"].replace('Z', '+00:00')) for f in gw_fixtures if f["date"]]
                
                if not fixture_dates:
                    continue
                
                gw_start = min(fixture_dates)
                gw_end = max(fixture_dates) + timedelta(days=2)  # Give 2 days after last match
                
                # Check if we're in this gameweek
                if gw_start <= now <= gw_end:
                    print(f"✅ Calculated current gameweek: {gameweek}")
                    self._update_current_gameweek_in_db(season, gameweek, gw_start, gw_end)
                    return gameweek
                
                # Check if this gameweek is upcoming (within next 7 days)
                if gw_start > now and (gw_start - now).days <= 7:
                    print(f"✅ Next gameweek starting soon: {gameweek}")
                    self._update_current_gameweek_in_db(season, gameweek, gw_start, gw_end)
                    return gameweek
            
            # If no current gameweek found, find the next upcoming one
            for gameweek in sorted(gameweeks.keys()):
                gw_fixtures = gameweeks[gameweek]
                fixture_dates = [datetime.fromisoformat(f["date"].replace('Z', '+00:00')) for f in gw_fixtures if f["date"]]
                
                if fixture_dates and min(fixture_dates) > now:
                    print(f"✅ Next upcoming gameweek: {gameweek}")
                    gw_start = min(fixture_dates)
                    gw_end = max(fixture_dates) + timedelta(days=2)
                    self._update_current_gameweek_in_db(season, gameweek, gw_start, gw_end)
                    return gameweek
            
            print("⚠️ Could not determine current gameweek")
            return None
            
        except Exception as e:
            print(f"❌ Error calculating current gameweek: {e}")
            return None
    
    def _update_current_gameweek_in_db(self, season: int, gameweek: int, start_date: datetime, end_date: datetime):
        """
        Update the current gameweek in database
        
        Args:
            season: The season year
            gameweek: The gameweek number
            start_date: Gameweek start date
            end_date: Gameweek end date
        """
        try:
            # Reset all current flags for this season
            self.db.client.table("premier_league_gameweeks").update({
                "is_current": False
            }).eq("season", season).execute()
            
            # Insert or update the current gameweek
            gameweek_record = {
                "season": season,
                "gameweek": gameweek,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "is_current": True,
                "is_completed": False
            }
            
            # Try to update existing record first
            existing = self.db.client.table("premier_league_gameweeks").select("id").eq("season", season).eq("gameweek", gameweek).execute()
            
            if existing.data:
                # Update existing
                self.db.client.table("premier_league_gameweeks").update({
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "is_current": True,
                    "updated_at": datetime.now().isoformat()
                }).eq("season", season).eq("gameweek", gameweek).execute()
            else:
                # Insert new
                self.db.client.table("premier_league_gameweeks").insert(gameweek_record).execute()
            
            print(f"✅ Updated current gameweek to {gameweek} for season {season}")
            
        except Exception as e:
            print(f"❌ Error updating current gameweek in database: {e}")
    
    def get_gameweek_fixtures(self, season: int, gameweek: int) -> List[Dict[str, Any]]:
        """
        Get all fixtures for a specific gameweek
        
        Args:
            season: The season year
            gameweek: The gameweek number
            
        Returns:
            List of fixtures for the gameweek
        """
        return self.get_fixtures_by_gameweek(self.premier_league_id, season, gameweek)
    
    def get_next_gameweek(self, season: int = None) -> Optional[int]:
        """
        Get the next gameweek number
        
        Args:
            season: The season year (defaults to current season)
            
        Returns:
            Next gameweek number or None
        """
        season = season or self.current_season
        current = self.get_current_gameweek(season)
        
        if current and current < self.total_gameweeks:
            return current + 1
        
        return None
    
    def get_previous_gameweek(self, season: int = None) -> Optional[int]:
        """
        Get the previous gameweek number
        
        Args:
            season: The season year (defaults to current season)
            
        Returns:
            Previous gameweek number or None
        """
        season = season or self.current_season
        current = self.get_current_gameweek(season)
        
        if current and current > 1:
            return current - 1
        
        return None
    
    def update_current_gameweek(self, season: int = None) -> Dict[str, Any]:
        """
        Force update of current gameweek (useful for scheduled tasks)
        
        Args:
            season: The season year (defaults to current season)
            
        Returns:
            Dict with update results
        """
        season = season or self.current_season
        
        try:
            current_gw = self._calculate_current_gameweek_from_fixtures(season)
            
            if current_gw:
                return {
                    "success": True,
                    "season": season,
                    "current_gameweek": current_gw,
                    "message": f"Successfully updated current gameweek to {current_gw}"
                }
            else:
                return {
                    "success": False,
                    "season": season,
                    "message": "Could not determine current gameweek"
                }
                
        except Exception as e:
            return {
                "success": False,
                "season": season,
                "error": str(e)
            }
    
    def get_gameweek_status(self, season: int = None) -> Dict[str, Any]:
        """
        Get comprehensive gameweek status information
        
        Args:
            season: The season year (defaults to current season)
            
        Returns:
            Dict with gameweek status information
        """
        season = season or self.current_season
        
        try:
            current_gw = self.get_current_gameweek(season)
            next_gw = self.get_next_gameweek(season)
            prev_gw = self.get_previous_gameweek(season)
            
            # Get fixture counts for current gameweek
            current_fixtures = []
            if current_gw:
                current_fixtures = self.get_gameweek_fixtures(season, current_gw)
            
            return {
                "season": season,
                "current_gameweek": current_gw,
                "previous_gameweek": prev_gw,
                "next_gameweek": next_gw,
                "total_gameweeks": self.total_gameweeks,
                "current_fixtures_count": len(current_fixtures),
                "fixtures": current_fixtures[:5] if current_fixtures else [],  # First 5 for preview
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Error getting gameweek status: {e}",
                "season": season
            }
    
    def is_gameweek_completed(self, season: int, gameweek: int) -> bool:
        """
        Check if a gameweek is completed (all matches finished)
        
        Args:
            season: The season year
            gameweek: The gameweek number
            
        Returns:
            True if all matches in gameweek are completed
        """
        try:
            fixtures = self.get_gameweek_fixtures(season, gameweek)
            
            if not fixtures:
                return False
            
            # Check if all fixtures are finished
            completed_statuses = ["FT", "AET", "PEN"]  # Full Time, After Extra Time, Penalties
            
            for fixture in fixtures:
                status = fixture.get("status_short", "")
                if status not in completed_statuses:
                    return False
            
            # Mark gameweek as completed in database
            self.db.client.table("premier_league_gameweeks").update({
                "is_completed": True,
                "updated_at": datetime.now().isoformat()
            }).eq("season", season).eq("gameweek", gameweek).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking gameweek completion: {e}")
            return False
    
    def get_gameweek_dates(self, season: int, gameweek: int) -> Optional[Dict[str, datetime]]:
        """
        Get start and end dates for a specific gameweek
        
        Args:
            season: The season year
            gameweek: The gameweek number
            
        Returns:
            Dict with start_date and end_date or None
        """
        try:
            # Check database first
            gw_data = self.db.client.table("premier_league_gameweeks").select("*").eq("season", season).eq("gameweek", gameweek).execute()
            
            if gw_data.data:
                data = gw_data.data[0]
                return {
                    "start_date": datetime.fromisoformat(data['start_date'].replace('Z', '+00:00')),
                    "end_date": datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
                }
            
            # Calculate from fixtures
            fixtures = self.get_gameweek_fixtures(season, gameweek)
            
            if not fixtures:
                return None
            
            fixture_dates = []
            for fixture in fixtures:
                if fixture["date"]:
                    fixture_dates.append(datetime.fromisoformat(fixture["date"].replace('Z', '+00:00')))
            
            if fixture_dates:
                start_date = min(fixture_dates)
                end_date = max(fixture_dates) + timedelta(days=2)
                
                return {
                    "start_date": start_date,
                    "end_date": end_date
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting gameweek dates: {e}")
            return None
    
    def initialize_all_gameweeks(self, season: int) -> Dict[str, Any]:
        """
        Initialize all gameweeks for a season based on fixture data
        
        Args:
            season: The season year
            
        Returns:
            Dict with initialization results
        """
        try:
            print(f"🔄 Initializing all gameweeks for season {season}...")
            
            # Get all fixtures for the season
            fixtures = self.get_fixtures_by_gameweek(self.premier_league_id, season, None)  # Get all
            
            if not fixtures:
                return {"error": "No fixtures found for season", "season": season}
            
            # Group by gameweek
            gameweek_data = {}
            
            for fixture in fixtures:
                gw = fixture.get("gameweek")
                if gw and 1 <= gw <= self.total_gameweeks:
                    if gw not in gameweek_data:
                        gameweek_data[gw] = []
                    gameweek_data[gw].append(fixture)
            
            # Create gameweek records
            gameweek_records = []
            
            for gameweek, gw_fixtures in gameweek_data.items():
                fixture_dates = [
                    datetime.fromisoformat(f["date"].replace('Z', '+00:00')) 
                    for f in gw_fixtures if f["date"]
                ]
                
                if fixture_dates:
                    start_date = min(fixture_dates)
                    end_date = max(fixture_dates) + timedelta(days=2)
                    
                    gameweek_records.append({
                        "season": season,
                        "gameweek": gameweek,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "is_current": False,
                        "is_completed": False
                    })
            
            # Store gameweek records
            if gameweek_records:
                success = self.store_data(
                    "premier_league_gameweeks",
                    gameweek_records,
                    unique_keys=["season", "gameweek"]
                )
                
                if success:
                    # Now set the current gameweek
                    current_gw = self.get_current_gameweek(season)
                    
                    return {
                        "success": True,
                        "season": season,
                        "total_gameweeks_created": len(gameweek_records),
                        "current_gameweek": current_gw,
                        "message": f"Initialized {len(gameweek_records)} gameweeks for season {season}"
                    }
            
            return {"error": "Failed to create gameweek records", "season": season}
            
        except Exception as e:
            return {"error": f"Error initializing gameweeks: {e}", "season": season}
