"""
Enhanced MCP Tools with Supabase Caching
Updated versions of existing tools + new tools for missing endpoints
"""

from typing import Dict, Any, List, Optional
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scrapers.scraper_manager import ScraperManager
from scrapers.lineup_scraper import LineupScraper
from scrapers.goalscorer_scraper import GoalscorerScraper
from scrapers.probable_scorer_scraper import ProbableScorerScraper
from utils.gameweek_calculator import PremierLeagueGameweekCalculator
from config.request_mode_manager import RequestModeManager
from utils.adaptive_rate_limiter import AdaptiveRateLimiter


class EnhancedMCPTools:
    """Enhanced MCP tools with caching and Premier League focus"""
    
    def __init__(self):
        self.scraper_manager = ScraperManager()
        self.lineup_scraper = LineupScraper()
        self.goalscorer_scraper = GoalscorerScraper()
        self.probable_scorer_scraper = ProbableScorerScraper()
        self.gameweek_calculator = PremierLeagueGameweekCalculator()
        self.mode_manager = RequestModeManager()
        self.rate_limiter = AdaptiveRateLimiter()
    
    # ================================
    # NEW TOOLS FOR MISSING ENDPOINTS
    # ================================
    
    def get_fixture_lineups(self, fixture_id: int) -> Dict[str, Any]:
        """
        Retrieve team lineups for a specific fixture.
        
        Args:
            fixture_id (int): The ID of the fixture.
            
        Returns:
            Dict[str, Any]: Lineup data from cache or API.
        """
        try:
            return self.lineup_scraper.scrape_fixture_lineups(fixture_id)
        except Exception as e:
            return {"error": f"Error getting fixture lineups: {e}"}
    
    def get_fixture_goalscorers(self, fixture_id: int) -> Dict[str, Any]:
        """
        Retrieve goal scorers for a specific fixture.
        
        Args:
            fixture_id (int): The ID of the fixture.
            
        Returns:
            Dict[str, Any]: Goal scorer data from cache or API.
        """
        try:
            return self.goalscorer_scraper.scrape_fixture_goalscorers(fixture_id)
        except Exception as e:
            return {"error": f"Error getting fixture goalscorers: {e}"}
    
    def get_probable_scorers(self, fixture_id: int) -> Dict[str, Any]:
        """
        Retrieve probable scorer predictions for a fixture.
        
        Args:
            fixture_id (int): The ID of the fixture.
            
        Returns:
            Dict[str, Any]: Probable scorer predictions.
        """
        try:
            return self.probable_scorer_scraper.scrape_fixture_probable_scorers(fixture_id)
        except Exception as e:
            return {"error": f"Error getting probable scorers: {e}"}
    
    def get_current_gameweek(self, season: int = 2024) -> Dict[str, Any]:
        """
        Get the current Premier League gameweek.
        
        Args:
            season (int): The season year.
            
        Returns:
            Dict[str, Any]: Current gameweek information.
        """
        try:
            current_gw = self.gameweek_calculator.get_current_gameweek(season)
            
            if current_gw:
                fixtures = self.gameweek_calculator.get_gameweek_fixtures(season, current_gw)
                return {
                    "current_gameweek": current_gw,
                    "season": season,
                    "fixtures": fixtures,
                    "total_gameweeks": 38,
                    "fixture_count": len(fixtures)
                }
            else:
                return {"error": "Could not determine current gameweek"}
        except Exception as e:
            return {"error": f"Error getting current gameweek: {e}"}
    
    def get_gameweek_fixtures(self, season: int, gameweek: int) -> Dict[str, Any]:
        """
        Get all fixtures for a specific Premier League gameweek.
        
        Args:
            season (int): The season year.
            gameweek (int): The gameweek number (1-38).
            
        Returns:
            Dict[str, Any]: Fixtures for the specified gameweek.
        """
        try:
            if not (1 <= gameweek <= 38):
                return {"error": "Gameweek must be between 1 and 38"}
            
            fixtures = self.gameweek_calculator.get_gameweek_fixtures(season, gameweek)
            
            return {
                "gameweek": gameweek,
                "season": season,
                "fixtures": fixtures,
                "fixture_count": len(fixtures)
            }
        except Exception as e:
            return {"error": f"Error getting gameweek fixtures: {e}"}
    
    def get_gameweek_complete_data(self, gameweek: int = None, season: int = 2024) -> Dict[str, Any]:
        """
        Get complete data for a gameweek (fixtures, lineups, goalscorers, predictions)
        This is a HIGH-VALUE tool that gets everything in one call!
        
        Args:
            gameweek (int): The gameweek number. If None, uses current gameweek.
            season (int): The season year.
            
        Returns:
            Dict[str, Any]: Complete gameweek data.
        """
        try:
            if gameweek is None:
                gameweek = self.gameweek_calculator.get_current_gameweek(season)
                if not gameweek:
                    return {"error": "Could not determine current gameweek"}
            
            if not (1 <= gameweek <= 38):
                return {"error": "Gameweek must be between 1 and 38"}
            
            # Use scraper manager to get all data
            return self.scraper_manager.scrape_specific_gameweek(gameweek, season)
            
        except Exception as e:
            return {"error": f"Error getting complete gameweek data: {e}"}
    
    # ================================
    # REQUEST MODE MANAGEMENT TOOLS
    # ================================
    
    def get_request_mode_status(self) -> Dict[str, Any]:
        """
        Get current request mode and usage statistics.
        
        Returns:
            Dict[str, Any]: Current mode, usage, and available modes.
        """
        try:
            current_usage = self.rate_limiter._get_current_usage()
            current_mode = self.mode_manager.get_current_mode()
            daily_budget = self.mode_manager.get_daily_budget()
            
            # Get mode comparison
            from config.request_mode_manager import ScalableScheduleManager
            schedule_manager = ScalableScheduleManager()
            mode_comparison = schedule_manager.get_mode_comparison()
            
            return {
                "current_mode": current_mode,
                "daily_budget": daily_budget,
                "current_usage": current_usage,
                "remaining_requests": 7500 - current_usage,
                "mode_budget_remaining": daily_budget - current_usage,
                "usage_percentage": (current_usage / 7500) * 100,
                "mode_usage_percentage": (current_usage / daily_budget) * 100 if daily_budget > 0 else 0,
                "auto_adjust_enabled": self.mode_manager.auto_adjust_enabled,
                "available_modes": mode_comparison
            }
        except Exception as e:
            return {"error": f"Error getting request mode status: {e}"}
    
    def switch_request_mode(self, mode: str, reason: str = "Manual change") -> Dict[str, Any]:
        """
        Switch to a different request mode.
        
        Args:
            mode (str): New mode ('minimal', 'low', 'standard', 'high', 'maximum').
            reason (str): Reason for the change.
            
        Returns:
            Dict[str, Any]: Mode change confirmation and details.
        """
        valid_modes = ['minimal', 'low', 'standard', 'high', 'maximum']
        
        if mode not in valid_modes:
            return {
                "error": f"Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}"
            }
        
        try:
            old_mode = self.mode_manager.get_current_mode()
            old_budget = self.mode_manager.get_daily_budget()
            
            success = self.mode_manager.switch_mode(mode, reason)
            
            if success:
                new_budget = self.mode_manager.get_daily_budget()
                
                return {
                    "success": True,
                    "previous_mode": old_mode,
                    "new_mode": mode,
                    "previous_budget": old_budget,
                    "new_budget": new_budget,
                    "reason": reason,
                    "message": f"Successfully switched from {old_mode} mode ({old_budget} requests/day) to {mode} mode ({new_budget} requests/day)"
                }
            else:
                return {"error": "Failed to switch request mode"}
                
        except Exception as e:
            return {"error": f"Error switching request mode: {e}"}
    
    def get_usage_prediction(self) -> Dict[str, Any]:
        """
        Get prediction of daily usage based on current rate.
        
        Returns:
            Dict[str, Any]: Usage prediction and recommendations.
        """
        try:
            return self.rate_limiter.get_usage_stats()
        except Exception as e:
            return {"error": f"Error getting usage prediction: {e}"}
    
    # ================================
    # ENHANCED EXISTING TOOLS
    # ================================
    
    def get_premier_league_fixtures(self, season: int = 2024, gameweek: int = None) -> Dict[str, Any]:
        """
        Get Premier League fixtures, optionally filtered by gameweek
        Enhanced version of get_league_fixtures focused on Premier League
        
        Args:
            season (int): The season year.
            gameweek (int): Optional gameweek filter.
            
        Returns:
            Dict[str, Any]: Fixture data from cache or API.
        """
        try:
            if gameweek:
                return self.get_gameweek_fixtures(season, gameweek)
            else:
                # Get all fixtures for the season
                fixtures = self.scraper_manager.base_scraper.get_fixtures_by_gameweek(39, season, None)
                return {
                    "season": season,
                    "league_id": 39,
                    "league_name": "Premier League",
                    "fixtures": fixtures,
                    "total_fixtures": len(fixtures)
                }
        except Exception as e:
            return {"error": f"Error getting Premier League fixtures: {e}"}
    
    def get_premier_league_standings(self, season: int = 2024) -> Dict[str, Any]:
        """
        Get Premier League standings from cache or API
        Enhanced version focused on Premier League only
        
        Args:
            season (int): The season year.
            
        Returns:
            Dict[str, Any]: Standings data.
        """
        try:
            # Check cache first
            cached_standings = self.scraper_manager.base_scraper.get_cached_data(
                "standings",
                {"league_id": 39, "season": season},
                max_age_hours=6
            )
            
            if cached_standings:
                print("✅ Using cached Premier League standings")
                return {
                    "season": season,
                    "league_id": 39,
                    "league_name": "Premier League",
                    "standings": sorted(cached_standings, key=lambda x: x["rank"]),
                    "source": "cache"
                }
            
            # Fetch from API via scraper manager
            self.scraper_manager._update_standings()
            
            # Get updated standings
            updated_standings = self.scraper_manager.base_scraper.get_cached_data(
                "standings",
                {"league_id": 39, "season": season},
                max_age_hours=1
            )
            
            return {
                "season": season,
                "league_id": 39,
                "league_name": "Premier League",
                "standings": sorted(updated_standings or [], key=lambda x: x["rank"]),
                "source": "api"
            }
            
        except Exception as e:
            return {"error": f"Error getting Premier League standings: {e}"}
    
    def get_team_fixtures_enhanced(self, team_name: str, type: str = "upcoming", limit: int = 5) -> Dict[str, Any]:
        """
        Enhanced version of get_team_fixtures using cached data
        
        Args:
            team_name (str): The team's name.
            type (str): 'past' or 'upcoming' fixtures.
            limit (int): How many fixtures to retrieve.
            
        Returns:
            Dict[str, Any]: Team fixture data.
        """
        try:
            # Get team info from cache first
            teams = self.scraper_manager.base_scraper.get_premier_league_teams()
            
            # Find matching team
            matching_team = None
            for team in teams:
                if team_name.lower() in team["name"].lower():
                    matching_team = team
                    break
            
            if not matching_team:
                return {"error": f"No team found matching '{team_name}'"}
            
            team_id = matching_team["id"]
            
            # Get fixtures from cache
            all_fixtures = self.scraper_manager.base_scraper.get_cached_data(
                "fixtures",
                {"league_id": 39},
                max_age_hours=6
            )
            
            if not all_fixtures:
                return {"error": "No fixture data available"}
            
            # Filter fixtures for this team
            team_fixtures = [
                f for f in all_fixtures 
                if f["home_team_id"] == team_id or f["away_team_id"] == team_id
            ]
            
            # Sort by date
            team_fixtures.sort(key=lambda x: x["date"] or "")
            
            now = datetime.now()
            
            if type.lower() == "upcoming":
                upcoming = [f for f in team_fixtures if f["date"] and datetime.fromisoformat(f["date"].replace('Z', '+00:00')) > now]
                result_fixtures = upcoming[:limit]
            else:  # past
                past = [f for f in team_fixtures if f["date"] and datetime.fromisoformat(f["date"].replace('Z', '+00:00')) <= now]
                result_fixtures = past[-limit:]  # Last N matches
            
            return {
                "team": matching_team,
                "type": type,
                "fixtures": result_fixtures,
                "total_found": len(result_fixtures),
                "source": "cache"
            }
            
        except Exception as e:
            return {"error": f"Error getting team fixtures: {e}"}
    
    # ================================
    # GAMEWEEK-SPECIFIC TOOLS
    # ================================
    
    def get_gameweek_lineups(self, gameweek: int, season: int = 2024) -> Dict[str, Any]:
        """
        Get lineups for all fixtures in a gameweek
        
        Args:
            gameweek (int): The gameweek number (1-38).
            season (int): The season year.
            
        Returns:
            Dict[str, Any]: All lineups for the gameweek.
        """
        try:
            lineups = self.lineup_scraper.get_lineups_for_gameweek(gameweek, season, 39)
            
            return {
                "gameweek": gameweek,
                "season": season,
                "lineups": lineups,
                "fixtures_with_lineups": len(lineups)
            }
        except Exception as e:
            return {"error": f"Error getting gameweek lineups: {e}"}
    
    def get_gameweek_goalscorers(self, gameweek: int, season: int = 2024) -> Dict[str, Any]:
        """
        Get goalscorers for all fixtures in a gameweek
        
        Args:
            gameweek (int): The gameweek number (1-38).
            season (int): The season year.
            
        Returns:
            Dict[str, Any]: All goalscorers for the gameweek.
        """
        try:
            goalscorers = self.goalscorer_scraper.get_goalscorers_for_gameweek(gameweek, season, 39)
            top_scorers = self.goalscorer_scraper.get_top_scorers_for_gameweek(gameweek, season, 39)
            
            return {
                "gameweek": gameweek,
                "season": season,
                "goalscorers": goalscorers,
                "top_scorers": top_scorers,
                "fixtures_with_goals": len(goalscorers)
            }
        except Exception as e:
            return {"error": f"Error getting gameweek goalscorers: {e}"}
    
    def get_gameweek_probable_scorers(self, gameweek: int, season: int = 2024) -> Dict[str, Any]:
        """
        Get probable scorers for all fixtures in a gameweek
        
        Args:
            gameweek (int): The gameweek number (1-38).
            season (int): The season year.
            
        Returns:
            Dict[str, Any]: All probable scorers for the gameweek.
        """
        try:
            probable_scorers = self.probable_scorer_scraper.get_probable_scorers_for_gameweek(gameweek, season, 39)
            
            return {
                "gameweek": gameweek,
                "season": season,
                "probable_scorers": probable_scorers,
                "fixtures_with_predictions": len(probable_scorers)
            }
        except Exception as e:
            return {"error": f"Error getting gameweek probable scorers: {e}"}
    
    # ================================
    # SYSTEM MANAGEMENT TOOLS
    # ================================
    
    def refresh_current_gameweek_data(self) -> Dict[str, Any]:
        """
        Force refresh all data for current gameweek
        High-value tool for getting latest data
        
        Returns:
            Dict[str, Any]: Refreshed gameweek data.
        """
        try:
            return self.scraper_manager.scrape_current_gameweek_data()
        except Exception as e:
            return {"error": f"Error refreshing current gameweek data: {e}"}
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            Dict[str, Any]: System status including usage, mode, and data freshness.
        """
        try:
            scraping_status = self.scraper_manager.get_scraping_status()
            mode_status = self.get_request_mode_status()
            
            return {
                "system_status": "operational",
                "scraping_status": scraping_status,
                "request_mode_status": mode_status,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Error getting system status: {e}"}
    
    def emergency_data_refresh(self) -> Dict[str, Any]:
        """
        Emergency mode data refresh - only critical data
        
        Returns:
            Dict[str, Any]: Emergency refresh results.
        """
        try:
            return self.scraper_manager.emergency_mode_scrape()
        except Exception as e:
            return {"error": f"Error in emergency data refresh: {e}"}


# Create global instance for easy import
enhanced_tools = EnhancedMCPTools()
