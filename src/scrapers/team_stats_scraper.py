"""
Team Statistics Scraper for Premier League Teams
Handles team performance stats, form, and Last 5 results
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.scrapers.base_scraper import BaseScraper


class TeamStatisticsScraper(BaseScraper):
    """Scraper for team statistics and form analysis"""
    
    def scrape_and_store(self, team_id: int, season: int = None, **kwargs) -> Dict[str, Any]:
        """
        Main method to scrape and store team statistics
        
        Args:
            team_id: The team ID to get statistics for
            season: The season (defaults to current season)
            
        Returns:
            Dict containing team statistics or error information
        """
        return self.scrape_team_statistics(team_id, season)
    
    def scrape_team_statistics(self, team_id: int, season: int = None) -> Dict[str, Any]:
        """
        Scrape comprehensive team statistics
        
        Args:
            team_id: The team ID
            season: The season (defaults to current season)
            
        Returns:
            Dict containing team statistics or error information
        """
        season = season or self.current_season
        
        try:
            # Check if we have fresh team statistics
            cached_stats = self.get_cached_data(
                "team_statistics",
                {"team_id": team_id, "season": season},
                max_age_hours=24  # Update daily
            )
            
            if cached_stats:
                print(f"Using cached team statistics for team {team_id}")
                return {
                    "team_id": team_id,
                    "season": season,
                    "statistics": cached_stats[0],
                    "source": "cache"
                }
            
            # Calculate from existing fixture data first (faster)
            calculated_stats = self._calculate_team_stats_from_fixtures(team_id, season)
            
            if calculated_stats:
                return calculated_stats
            
            # Fallback to API if needed
            print(f"Fetching team statistics for team {team_id} from API...")
            
            response = self.make_api_request(
                "teams/statistics",
                {"league": self.premier_league_id, "season": season, "team": team_id},
                priority="medium"
            )
            
            if "error" in response:
                print(f"Error fetching team statistics: {response['error']}")
                return {"error": response["error"], "team_id": team_id}
            
            # Process and store team statistics
            return self._process_and_store_team_stats(team_id, season, response)
            
        except Exception as e:
            error_msg = f"Error scraping team statistics for team {team_id}: {e}"
            print(f"Error: {error_msg}")
            return {"error": error_msg, "team_id": team_id}
    
    def _calculate_team_stats_from_fixtures(self, team_id: int, season: int) -> Optional[Dict[str, Any]]:
        """
        Calculate team statistics from existing fixture data (fast, no API calls)
        
        Args:
            team_id: The team ID
            season: The season
            
        Returns:
            Dict with calculated statistics or None
        """
        try:
            # Get all completed fixtures for this team
            fixtures = self.db.client.table("fixtures").select("*").eq("league_id", self.premier_league_id).eq("season", season).eq("status_short", "FT").or_(f"home_team_id.eq.{team_id},away_team_id.eq.{team_id}").order("date", desc=True).execute()
            
            if not fixtures.data:
                return None
            
            # Calculate statistics
            stats = {
                "matches_played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "clean_sheets": 0,
                "form": "",
                "last_5_results": [],
                "home_record": {"played": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0},
                "away_record": {"played": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}
            }
            
            last_5_count = 0
            
            for fixture in fixtures.data:
                is_home = fixture["home_team_id"] == team_id
                
                if is_home:
                    team_score = fixture["home_score"]
                    opponent_score = fixture["away_score"]
                    record_key = "home_record"
                else:
                    team_score = fixture["away_score"]
                    opponent_score = fixture["home_score"]
                    record_key = "away_record"
                
                if team_score is None or opponent_score is None:
                    continue  # Skip fixtures without scores
                
                # Overall statistics
                stats["matches_played"] += 1
                stats["goals_for"] += team_score
                stats["goals_against"] += opponent_score
                
                # Home/Away record
                stats[record_key]["played"] += 1
                stats[record_key]["goals_for"] += team_score
                stats[record_key]["goals_against"] += opponent_score
                
                # Result calculation
                if team_score > opponent_score:
                    stats["wins"] += 1
                    stats[record_key]["wins"] += 1
                    result_char = "W"
                elif team_score < opponent_score:
                    stats["losses"] += 1
                    stats[record_key]["losses"] += 1
                    result_char = "L"
                else:
                    stats["draws"] += 1
                    stats[record_key]["draws"] += 1
                    result_char = "D"
                
                # Clean sheet
                if opponent_score == 0:
                    stats["clean_sheets"] += 1
                
                # Last 5 form
                if last_5_count < 5:
                    stats["form"] += result_char
                    stats["last_5_results"].append({
                        "fixture_id": fixture["id"],
                        "date": fixture["date"],
                        "opponent_id": fixture["away_team_id"] if is_home else fixture["home_team_id"],
                        "is_home": is_home,
                        "team_score": team_score,
                        "opponent_score": opponent_score,
                        "result": result_char
                    })
                    last_5_count += 1
            
            # Store calculated statistics
            team_stats_record = {
                "team_id": team_id,
                "league_id": self.premier_league_id,
                "season": season,
                **stats
            }
            
            success = self.store_data(
                "team_statistics",
                [team_stats_record],
                unique_keys=["team_id", "league_id", "season"]
            )
            
            if success:
                print(f"Stored calculated team statistics for team {team_id}")
                
                return {
                    "team_id": team_id,
                    "season": season,
                    "statistics": team_stats_record,
                    "source": "calculated_from_fixtures",
                    "success": True
                }
            
            return None
            
        except Exception as e:
            print(f"Error calculating team stats from fixtures: {e}")
            return None
    
    def _process_and_store_team_stats(self, team_id: int, season: int, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process API response and store team statistics
        
        Args:
            team_id: The team ID
            season: The season
            api_response: Raw API response from teams/statistics endpoint
            
        Returns:
            Dict containing processed team statistics
        """
        try:
            response_data = api_response.get("response", {})
            
            if not response_data:
                return {"error": "No team statistics data in API response"}
            
            # Extract team statistics from API response
            fixtures = response_data.get("fixtures", {})
            goals = response_data.get("goals", {})
            
            team_stats_record = {
                "team_id": team_id,
                "league_id": self.premier_league_id,
                "season": season,
                "matches_played": fixtures.get("played", {}).get("total", 0),
                "wins": fixtures.get("wins", {}).get("total", 0),
                "draws": fixtures.get("draws", {}).get("total", 0),
                "losses": fixtures.get("loses", {}).get("total", 0),
                "goals_for": goals.get("for", {}).get("total", {}).get("total", 0),
                "goals_against": goals.get("against", {}).get("total", {}).get("total", 0),
                "clean_sheets": response_data.get("clean_sheet", {}).get("total", 0),
                "form": "",  # Will be calculated separately
                "last_5_results": [],  # Will be calculated from fixtures
                "home_record": {
                    "played": fixtures.get("played", {}).get("home", 0),
                    "wins": fixtures.get("wins", {}).get("home", 0),
                    "draws": fixtures.get("draws", {}).get("home", 0),
                    "losses": fixtures.get("loses", {}).get("home", 0),
                    "goals_for": goals.get("for", {}).get("total", {}).get("home", 0),
                    "goals_against": goals.get("against", {}).get("total", {}).get("home", 0)
                },
                "away_record": {
                    "played": fixtures.get("played", {}).get("away", 0),
                    "wins": fixtures.get("wins", {}).get("away", 0),
                    "draws": fixtures.get("draws", {}).get("away", 0),
                    "losses": fixtures.get("loses", {}).get("away", 0),
                    "goals_for": goals.get("for", {}).get("total", {}).get("away", 0),
                    "goals_against": goals.get("against", {}).get("total", {}).get("away", 0)
                }
            }
            
            # Calculate form from fixtures
            form_data = self._calculate_team_form(team_id, season)
            if form_data:
                team_stats_record.update(form_data)
            
            # Store team statistics
            success = self.store_data(
                "team_statistics",
                [team_stats_record],
                unique_keys=["team_id", "league_id", "season"]
            )
            
            if success:
                print(f"Stored team statistics for team {team_id}")
                
                return {
                    "team_id": team_id,
                    "season": season,
                    "statistics": team_stats_record,
                    "source": "api",
                    "success": True
                }
            
            return {"error": "Failed to store team statistics"}
            
        except Exception as e:
            error_msg = f"Error processing team statistics: {e}"
            print(f"Error: {error_msg}")
            return {"error": error_msg, "team_id": team_id}
    
    def _calculate_team_form(self, team_id: int, season: int) -> Dict[str, Any]:
        """
        Calculate team's last 5 form from fixtures
        
        Args:
            team_id: The team ID
            season: The season
            
        Returns:
            Dict with form and last 5 results
        """
        try:
            # Get last 5 completed fixtures for team
            fixtures = self.db.client.table("fixtures").select("*").eq("league_id", self.premier_league_id).eq("season", season).eq("status_short", "FT").or_(f"home_team_id.eq.{team_id},away_team_id.eq.{team_id}").order("date", desc=True).limit(5).execute()
            
            if not fixtures.data:
                return {"form": "", "last_5_results": []}
            
            form = ""
            last_5_results = []
            
            for fixture in fixtures.data:
                is_home = fixture["home_team_id"] == team_id
                
                if is_home:
                    team_score = fixture["home_score"]
                    opponent_score = fixture["away_score"]
                    opponent_id = fixture["away_team_id"]
                else:
                    team_score = fixture["away_score"]
                    opponent_score = fixture["home_score"]
                    opponent_id = fixture["home_team_id"]
                
                if team_score is None or opponent_score is None:
                    continue
                
                # Determine result
                if team_score > opponent_score:
                    result_char = "W"
                elif team_score < opponent_score:
                    result_char = "L"
                else:
                    result_char = "D"
                
                form += result_char
                
                last_5_results.append({
                    "fixture_id": fixture["id"],
                    "date": fixture["date"],
                    "opponent_id": opponent_id,
                    "is_home": is_home,
                    "team_score": team_score,
                    "opponent_score": opponent_score,
                    "result": result_char,
                    "gameweek": fixture.get("gameweek")
                })
            
            return {
                "form": form,
                "last_5_results": last_5_results
            }
            
        except Exception as e:
            print(f"Error calculating team form: {e}")
            return {"form": "", "last_5_results": []}
    
    def scrape_all_team_statistics(self, season: int = None) -> Dict[str, Any]:
        """
        Calculate statistics for all Premier League teams
        
        Args:
            season: The season (defaults to current season)
            
        Returns:
            Dict with results for all teams
        """
        season = season or self.current_season
        
        try:
            # Get all Premier League teams
            teams = self.get_premier_league_teams()
            
            if not teams:
                return {"error": "No Premier League teams found"}
            
            results = {
                "season": season,
                "teams_processed": 0,
                "teams_success": 0,
                "teams_failed": 0,
                "errors": []
            }
            
            for team in teams:
                team_id = team["id"]
                team_name = team["name"]
                
                print(f"Processing statistics for {team_name} (ID: {team_id})...")
                
                stats_result = self.scrape_team_statistics(team_id, season)
                results["teams_processed"] += 1
                
                if "error" not in stats_result:
                    results["teams_success"] += 1
                    print(f"Success: {team_name} statistics updated")
                else:
                    results["teams_failed"] += 1
                    results["errors"].append(f"{team_name}: {stats_result['error']}")
                    print(f"Failed: {team_name} - {stats_result['error']}")
            
            print(f"Team statistics scraping complete: {results['teams_success']}/{results['teams_processed']} teams successful")
            return results
            
        except Exception as e:
            return {"error": f"Error scraping all team statistics: {e}"}
    
    def get_team_last_5_results(self, team_id: int, season: int = None) -> Dict[str, Any]:
        """
        Get team's last 5 results with opponent details
        
        Args:
            team_id: The team ID
            season: The season (defaults to current season)
            
        Returns:
            Dict with last 5 results and form
        """
        season = season or self.current_season
        
        try:
            # Try to get from cached team statistics first
            cached_stats = self.get_cached_data(
                "team_statistics",
                {"team_id": team_id, "season": season},
                max_age_hours=6
            )
            
            if cached_stats and cached_stats[0].get("last_5_results"):
                stats = cached_stats[0]
                
                # Enhance with opponent names
                enhanced_results = []
                for result in stats["last_5_results"]:
                    # Get opponent team name
                    opponent_team = self.get_cached_data(
                        "teams",
                        {"id": result["opponent_id"]},
                        max_age_hours=168
                    )
                    
                    enhanced_result = result.copy()
                    if opponent_team:
                        enhanced_result["opponent_name"] = opponent_team[0]["name"]
                    
                    enhanced_results.append(enhanced_result)
                
                return {
                    "team_id": team_id,
                    "season": season,
                    "form": stats["form"],
                    "last_5_results": enhanced_results,
                    "source": "cache"
                }
            
            # Calculate from fixtures if not cached
            form_data = self._calculate_team_form(team_id, season)
            
            if form_data:
                return {
                    "team_id": team_id,
                    "season": season,
                    "form": form_data["form"],
                    "last_5_results": form_data["last_5_results"],
                    "source": "calculated"
                }
            
            return {"error": "No form data available"}
            
        except Exception as e:
            return {"error": f"Error getting last 5 results: {e}"}
    
    def get_team_form_comparison(self, team1_id: int, team2_id: int, season: int = None) -> Dict[str, Any]:
        """
        Compare form between two teams
        
        Args:
            team1_id: First team ID
            team2_id: Second team ID
            season: The season (defaults to current season)
            
        Returns:
            Dict with form comparison
        """
        try:
            team1_form = self.get_team_last_5_results(team1_id, season)
            team2_form = self.get_team_last_5_results(team2_id, season)
            
            if "error" in team1_form or "error" in team2_form:
                return {"error": "Could not get form data for comparison"}
            
            # Calculate form scores (W=3, D=1, L=0)
            def calculate_form_score(form_string):
                score = 0
                for char in form_string:
                    if char == "W":
                        score += 3
                    elif char == "D":
                        score += 1
                return score
            
            team1_score = calculate_form_score(team1_form["form"])
            team2_score = calculate_form_score(team2_form["form"])
            
            return {
                "team1_id": team1_id,
                "team2_id": team2_id,
                "team1_form": team1_form["form"],
                "team2_form": team2_form["form"],
                "team1_form_score": team1_score,
                "team2_form_score": team2_score,
                "better_form": "team1" if team1_score > team2_score else "team2" if team2_score > team1_score else "equal",
                "team1_last_5": team1_form["last_5_results"],
                "team2_last_5": team2_form["last_5_results"]
            }
            
        except Exception as e:
            return {"error": f"Error comparing team form: {e}"}
    
    def get_premier_league_form_table(self, season: int = None) -> Dict[str, Any]:
        """
        Get Premier League standings with form indicators
        
        Args:
            season: The season (defaults to current season)
            
        Returns:
            Dict with standings and form data
        """
        season = season or self.current_season
        
        try:
            # Get current standings
            standings = self.get_cached_data(
                "standings",
                {"league_id": self.premier_league_id, "season": season},
                max_age_hours=12
            )
            
            if not standings:
                return {"error": "No standings data available"}
            
            # Enhance with form data
            enhanced_standings = []
            
            for standing in standings:
                team_id = standing["team_id"]
                
                # Get team form
                form_data = self.get_team_last_5_results(team_id, season)
                
                enhanced_standing = standing.copy()
                if "error" not in form_data:
                    enhanced_standing["form"] = form_data["form"]
                    enhanced_standing["last_5_results"] = form_data["last_5_results"]
                else:
                    enhanced_standing["form"] = ""
                    enhanced_standing["last_5_results"] = []
                
                enhanced_standings.append(enhanced_standing)
            
            # Sort by rank
            enhanced_standings.sort(key=lambda x: x.get("rank", 999))
            
            return {
                "season": season,
                "league_id": self.premier_league_id,
                "standings_with_form": enhanced_standings,
                "source": "enhanced_cache"
            }
            
        except Exception as e:
            return {"error": f"Error getting form table: {e}"}
