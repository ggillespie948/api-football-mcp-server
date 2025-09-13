"""
Scraper Manager - Coordinates all Premier League data scrapers
Handles orchestration of different scrapers based on request mode and scheduling
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from src.scrapers.base_scraper import BaseScraper
from src.scrapers.lineup_scraper import LineupScraper
from src.scrapers.goalscorer_scraper import GoalscorerScraper
from src.scrapers.probable_scorer_scraper import ProbableScorerScraper
from src.utils.gameweek_calculator import PremierLeagueGameweekCalculator
from src.config.request_mode_manager import RequestModeManager


class ScraperManager:
    """Coordinates all scrapers and manages data collection strategy"""
    
    def __init__(self):
        self.base_scraper = BaseScraper()
        self.lineup_scraper = LineupScraper()
        self.goalscorer_scraper = GoalscorerScraper()
        self.probable_scorer_scraper = ProbableScorerScraper()
        self.gameweek_calculator = PremierLeagueGameweekCalculator()
        self.mode_manager = RequestModeManager()
        
        # Premier League specifics
        self.premier_league_id = 39
        self.current_season = 2024
    
    def scrape_current_gameweek_data(self) -> Dict[str, Any]:
        """
        Scrape all data for the current gameweek
        This is a HIGH-VALUE operation that gets everything you need
        """
        try:
            print("🏈 Starting current gameweek data scrape...")
            
            # Get current gameweek
            current_gw = self.gameweek_calculator.get_current_gameweek(self.current_season)
            
            if not current_gw:
                return {"error": "Could not determine current gameweek"}
            
            print(f"📅 Current gameweek: {current_gw}")
            
            # Get fixtures for current gameweek
            fixtures = self.gameweek_calculator.get_gameweek_fixtures(self.current_season, current_gw)
            
            if not fixtures:
                return {"error": f"No fixtures found for gameweek {current_gw}"}
            
            results = {
                "gameweek": current_gw,
                "season": self.current_season,
                "fixtures": fixtures,
                "lineups": [],
                "goalscorers": [],
                "probable_scorers": [],
                "scrape_summary": {
                    "total_fixtures": len(fixtures),
                    "lineups_scraped": 0,
                    "goalscorers_scraped": 0,
                    "predictions_scraped": 0,
                    "errors": []
                }
            }
            
            # Scrape data for each fixture
            for fixture in fixtures:
                fixture_id = fixture["id"]
                status = fixture.get("status_short", "")
                
                print(f"🔄 Processing fixture {fixture_id} ({status})...")
                
                # Scrape lineups (for all fixtures, especially upcoming ones)
                if status in ["NS", "TBD", "1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT"]:
                    lineup_data = self.lineup_scraper.scrape_fixture_lineups(fixture_id)
                    if "error" not in lineup_data:
                        results["lineups"].append(lineup_data)
                        results["scrape_summary"]["lineups_scraped"] += 1
                    else:
                        results["scrape_summary"]["errors"].append(f"Lineup error for {fixture_id}: {lineup_data['error']}")
                
                # Scrape goalscorers (for live and completed fixtures)
                if status in ["1H", "HT", "2H", "ET", "BT", "P", "FT", "AET", "PEN"]:
                    goalscorer_data = self.goalscorer_scraper.scrape_fixture_goalscorers(fixture_id)
                    if "error" not in goalscorer_data:
                        results["goalscorers"].append(goalscorer_data)
                        results["scrape_summary"]["goalscorers_scraped"] += 1
                    else:
                        results["scrape_summary"]["errors"].append(f"Goalscorer error for {fixture_id}: {goalscorer_data['error']}")
                
                # Scrape probable scorers (for upcoming fixtures only)
                if status in ["NS", "TBD"]:
                    prediction_data = self.probable_scorer_scraper.scrape_fixture_probable_scorers(fixture_id)
                    if "error" not in prediction_data:
                        results["probable_scorers"].append(prediction_data)
                        results["scrape_summary"]["predictions_scraped"] += 1
                    else:
                        results["scrape_summary"]["errors"].append(f"Prediction error for {fixture_id}: {prediction_data['error']}")
            
            # Update standings after processing all fixtures
            self._update_standings()
            
            print(f"✅ Completed gameweek {current_gw} data scrape")
            print(f"📊 Summary: {results['scrape_summary']}")
            
            return results
            
        except Exception as e:
            error_msg = f"Error scraping current gameweek data: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def scrape_specific_gameweek(self, gameweek: int, season: int = None) -> Dict[str, Any]:
        """
        Scrape all data for a specific gameweek
        
        Args:
            gameweek: The gameweek number (1-38)
            season: The season year (defaults to current season)
            
        Returns:
            Dict with all scraped data for the gameweek
        """
        season = season or self.current_season
        
        if not (1 <= gameweek <= 38):
            return {"error": "Gameweek must be between 1 and 38"}
        
        try:
            print(f"🏈 Starting gameweek {gameweek} data scrape...")
            
            # Get fixtures for the gameweek
            fixtures = self.gameweek_calculator.get_gameweek_fixtures(season, gameweek)
            
            if not fixtures:
                return {"error": f"No fixtures found for gameweek {gameweek}"}
            
            # Use the same logic as current gameweek scrape
            return self._scrape_gameweek_data(gameweek, season, fixtures)
            
        except Exception as e:
            return {"error": f"Error scraping gameweek {gameweek}: {e}"}
    
    def _scrape_gameweek_data(self, gameweek: int, season: int, fixtures: List[Dict]) -> Dict[str, Any]:
        """Helper method to scrape data for any gameweek"""
        results = {
            "gameweek": gameweek,
            "season": season,
            "fixtures": fixtures,
            "lineups": [],
            "goalscorers": [],
            "probable_scorers": [],
            "scrape_summary": {
                "total_fixtures": len(fixtures),
                "lineups_scraped": 0,
                "goalscorers_scraped": 0,
                "predictions_scraped": 0,
                "errors": []
            }
        }
        
        # Process each fixture (same logic as current gameweek)
        for fixture in fixtures:
            fixture_id = fixture["id"]
            status = fixture.get("status_short", "")
            
            # Lineups for all relevant fixtures
            if status in ["NS", "TBD", "1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT"]:
                lineup_data = self.lineup_scraper.scrape_fixture_lineups(fixture_id)
                if "error" not in lineup_data:
                    results["lineups"].append(lineup_data)
                    results["scrape_summary"]["lineups_scraped"] += 1
            
            # Goalscorers for live/completed fixtures
            if status in ["1H", "HT", "2H", "ET", "BT", "P", "FT", "AET", "PEN"]:
                goalscorer_data = self.goalscorer_scraper.scrape_fixture_goalscorers(fixture_id)
                if "error" not in goalscorer_data:
                    results["goalscorers"].append(goalscorer_data)
                    results["scrape_summary"]["goalscorers_scraped"] += 1
            
            # Probable scorers for upcoming fixtures
            if status in ["NS", "TBD"]:
                prediction_data = self.probable_scorer_scraper.scrape_fixture_probable_scorers(fixture_id)
                if "error" not in prediction_data:
                    results["probable_scorers"].append(prediction_data)
                    results["scrape_summary"]["predictions_scraped"] += 1
        
        return results
    
    def _update_standings(self) -> bool:
        """Update Premier League standings"""
        try:
            print("🔄 Updating Premier League standings...")
            
            response = self.base_scraper.make_api_request(
                "standings",
                {"league": self.premier_league_id, "season": self.current_season},
                priority="medium"
            )
            
            if "error" in response:
                print(f"❌ Error fetching standings: {response['error']}")
                return False
            
            # Process standings data
            standings_records = []
            
            for league_data in response.get("response", []):
                for standing_data in league_data.get("league", {}).get("standings", []):
                    for team_standing in standing_data:
                        team_info = team_standing.get("team", {})
                        
                        standings_record = {
                            "league_id": self.premier_league_id,
                            "season": self.current_season,
                            "team_id": team_info.get("id"),
                            "rank": team_standing.get("rank"),
                            "points": team_standing.get("points"),
                            "goals_diff": team_standing.get("goalsDiff"),
                            "group_name": team_standing.get("group"),
                            "form": team_standing.get("form"),
                            "status": team_standing.get("status"),
                            "description": team_standing.get("description"),
                            "played": team_standing.get("all", {}).get("played"),
                            "win": team_standing.get("all", {}).get("win"),
                            "draw": team_standing.get("all", {}).get("draw"),
                            "lose": team_standing.get("all", {}).get("lose"),
                            "goals_for": team_standing.get("all", {}).get("goals", {}).get("for"),
                            "goals_against": team_standing.get("all", {}).get("goals", {}).get("against")
                        }
                        
                        standings_records.append(standings_record)
            
            # Store standings
            if standings_records:
                success = self.base_scraper.store_data(
                    "standings",
                    standings_records,
                    unique_keys=["league_id", "season", "team_id"]
                )
                
                if success:
                    print(f"✅ Updated standings for {len(standings_records)} teams")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error updating standings: {e}")
            return False
    
    def get_scraping_status(self) -> Dict[str, Any]:
        """Get current status of all scrapers and data freshness"""
        try:
            current_gw = self.gameweek_calculator.get_current_gameweek()
            mode = self.mode_manager.get_current_mode()
            usage_stats = self.base_scraper.get_usage_summary()
            
            return {
                "current_gameweek": current_gw,
                "current_season": self.current_season,
                "request_mode": mode,
                "usage_stats": usage_stats,
                "last_update": datetime.now().isoformat(),
                "available_scrapers": [
                    "lineups",
                    "goalscorers", 
                    "probable_scorers",
                    "gameweek_calculator"
                ]
            }
            
        except Exception as e:
            return {"error": f"Error getting scraping status: {e}"}
    
    def emergency_mode_scrape(self) -> Dict[str, Any]:
        """
        Emergency mode scraping - only critical data
        Used when approaching API rate limits
        """
        try:
            print("🚨 EMERGENCY MODE: Scraping only critical data...")
            
            current_gw = self.gameweek_calculator.get_current_gameweek()
            
            if not current_gw:
                return {"error": "Could not determine current gameweek"}
            
            # Get only live fixtures
            fixtures = self.gameweek_calculator.get_gameweek_fixtures(self.current_season, current_gw)
            live_fixtures = [f for f in fixtures if f.get("status_short") in ["1H", "HT", "2H", "ET", "BT"]]
            
            if not live_fixtures:
                return {"message": "No live fixtures to scrape in emergency mode"}
            
            results = {
                "mode": "emergency",
                "gameweek": current_gw,
                "live_fixtures": len(live_fixtures),
                "goalscorers": []
            }
            
            # Only scrape goalscorers for live fixtures
            for fixture in live_fixtures:
                goalscorer_data = self.goalscorer_scraper.scrape_fixture_goalscorers(fixture["id"])
                if "error" not in goalscorer_data:
                    results["goalscorers"].append(goalscorer_data)
            
            print(f"✅ Emergency scrape completed - {len(results['goalscorers'])} fixtures processed")
            return results
            
        except Exception as e:
            return {"error": f"Error in emergency mode scrape: {e}"}
