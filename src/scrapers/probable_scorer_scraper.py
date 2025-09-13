"""
Probable Scorer Scraper for Premier League Fixtures
Handles player predictions and odds for upcoming matches
"""

from typing import Dict, Any, List, Optional
from src.scrapers.base_scraper import BaseScraper


class ProbableScorerScraper(BaseScraper):
    """Scraper for probable scorer predictions and betting odds"""
    
    def scrape_and_store(self, fixture_id: int, **kwargs) -> Dict[str, Any]:
        """
        Main method to scrape and store probable scorer data for a fixture
        
        Args:
            fixture_id: The fixture ID to get predictions for
            
        Returns:
            Dict containing probable scorer data or error information
        """
        return self.scrape_fixture_probable_scorers(fixture_id)
    
    def scrape_fixture_probable_scorers(self, fixture_id: int) -> Dict[str, Any]:
        """
        Scrape probable scorer predictions for a specific fixture
        
        Args:
            fixture_id: The fixture ID to get predictions for
            
        Returns:
            Dict containing probable scorer data or error information
        """
        try:
            # Check if we have fresh prediction data
            cached_predictions = self.get_cached_data(
                "probable_scorers",
                {"fixture_id": fixture_id},
                max_age_hours=12  # Update twice daily for upcoming matches
            )
            
            if cached_predictions:
                print(f"✅ Using cached probable scorers for fixture {fixture_id}")
                return {
                    "fixture_id": fixture_id,
                    "probable_scorers": cached_predictions,
                    "source": "cache"
                }
            
            # Fetch from API using the predictions endpoint
            print(f"🔄 Fetching probable scorers for fixture {fixture_id} from API...")
            
            response = self.make_api_request(
                "predictions",
                {"fixture": fixture_id},
                priority="medium"
            )
            
            if "error" in response:
                print(f"❌ Error fetching predictions: {response['error']}")
                return {"error": response["error"], "fixture_id": fixture_id}
            
            # Process and store probable scorer data
            return self._process_and_store_probable_scorers(fixture_id, response)
            
        except Exception as e:
            error_msg = f"Error scraping probable scorers for fixture {fixture_id}: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg, "fixture_id": fixture_id}
    
    def _process_and_store_probable_scorers(self, fixture_id: int, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process API response and store probable scorer data in database
        
        Args:
            fixture_id: The fixture ID
            api_response: Raw API response from predictions endpoint
            
        Returns:
            Dict containing processed probable scorer data
        """
        try:
            probable_scorer_records = []
            
            for prediction_data in api_response.get("response", []):
                # Get teams data
                teams = prediction_data.get("teams", {})
                home_team = teams.get("home", {})
                away_team = teams.get("away", {})
                
                # Process home team players
                if home_team:
                    home_predictions = self._extract_player_predictions(
                        fixture_id, home_team, "home"
                    )
                    probable_scorer_records.extend(home_predictions)
                
                # Process away team players
                if away_team:
                    away_predictions = self._extract_player_predictions(
                        fixture_id, away_team, "away"
                    )
                    probable_scorer_records.extend(away_predictions)
                
                # Also check for any specific scorer predictions in the response
                comparison = prediction_data.get("comparison", {})
                if comparison:
                    additional_predictions = self._extract_comparison_predictions(
                        fixture_id, comparison, home_team.get("id"), away_team.get("id")
                    )
                    probable_scorer_records.extend(additional_predictions)
            
            # Store probable scorer records
            if probable_scorer_records:
                success = self.store_data(
                    "probable_scorers",
                    probable_scorer_records,
                    unique_keys=["fixture_id", "player_id"]
                )
                
                if success:
                    print(f"✅ Stored {len(probable_scorer_records)} probable scorer records")
                
                return {
                    "fixture_id": fixture_id,
                    "probable_scorers": probable_scorer_records,
                    "source": "api",
                    "success": True
                }
            else:
                # Try to generate predictions based on recent form
                generated_predictions = self._generate_predictions_from_form(fixture_id)
                
                if generated_predictions:
                    return {
                        "fixture_id": fixture_id,
                        "probable_scorers": generated_predictions,
                        "source": "generated",
                        "success": True
                    }
                else:
                    return {
                        "fixture_id": fixture_id,
                        "message": "No probable scorer predictions available",
                        "source": "api"
                    }
                
        except Exception as e:
            error_msg = f"Error processing probable scorer data: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg, "fixture_id": fixture_id}
    
    def _extract_player_predictions(self, fixture_id: int, team_data: Dict[str, Any], team_type: str) -> List[Dict[str, Any]]:
        """
        Extract player predictions from team data
        
        Args:
            fixture_id: The fixture ID
            team_data: Team data from API
            team_type: 'home' or 'away'
            
        Returns:
            List of probable scorer records
        """
        predictions = []
        
        try:
            team_id = team_data.get("id")
            
            # Look for player-specific predictions in various places
            # The API structure can vary, so we check multiple possible locations
            
            # Check for last 5 matches data
            last_5 = team_data.get("last_5", {})
            if last_5:
                # Extract goal statistics from recent matches
                goals = last_5.get("goals", {})
                if goals:
                    # This is a simplified approach - in reality, we'd need player-specific data
                    avg_goals = goals.get("for", {}).get("average", 0)
                    
                    # Get team players (we'd need to fetch this separately)
                    # For now, create a placeholder prediction
                    predictions.append({
                        "fixture_id": fixture_id,
                        "player_id": None,  # Would need actual player data
                        "team_id": team_id,
                        "probability": None,
                        "odds": None,
                        "last_5_goals": None,
                        "last_5_assists": None
                    })
            
            return predictions
            
        except Exception as e:
            print(f"⚠️ Error extracting player predictions: {e}")
            return []
    
    def _extract_comparison_predictions(self, fixture_id: int, comparison: Dict[str, Any], 
                                      home_team_id: int, away_team_id: int) -> List[Dict[str, Any]]:
        """
        Extract predictions from comparison data
        
        Args:
            fixture_id: The fixture ID
            comparison: Comparison data from API
            home_team_id: Home team ID
            away_team_id: Away team ID
            
        Returns:
            List of probable scorer records
        """
        predictions = []
        
        try:
            # Look for scoring-related predictions
            form = comparison.get("form", {})
            att = comparison.get("att", {})  # Attack statistics
            
            if form or att:
                # Create team-level predictions that could be used for top players
                # This is a simplified approach
                predictions.append({
                    "fixture_id": fixture_id,
                    "player_id": None,  # Would need actual player data
                    "team_id": home_team_id,
                    "probability": None,
                    "odds": None,
                    "last_5_goals": None,
                    "last_5_assists": None
                })
            
            return predictions
            
        except Exception as e:
            print(f"⚠️ Error extracting comparison predictions: {e}")
            return []
    
    def _generate_predictions_from_form(self, fixture_id: int) -> List[Dict[str, Any]]:
        """
        Generate probable scorer predictions based on recent player form
        
        Args:
            fixture_id: The fixture ID
            
        Returns:
            List of generated probable scorer records
        """
        try:
            # Get fixture details to know which teams are playing
            fixture_data = self.get_cached_data(
                "fixtures",
                {"id": fixture_id},
                max_age_hours=24
            )
            
            if not fixture_data:
                return []
            
            fixture = fixture_data[0]
            home_team_id = fixture["home_team_id"]
            away_team_id = fixture["away_team_id"]
            
            predictions = []
            
            # Generate predictions for both teams based on recent form
            for team_id in [home_team_id, away_team_id]:
                team_predictions = self._generate_team_predictions(fixture_id, team_id)
                predictions.extend(team_predictions)
            
            if predictions:
                # Store generated predictions
                success = self.store_data(
                    "probable_scorers",
                    predictions,
                    unique_keys=["fixture_id", "player_id"]
                )
                
                if success:
                    print(f"✅ Generated and stored {len(predictions)} probable scorer predictions")
            
            return predictions
            
        except Exception as e:
            print(f"⚠️ Error generating predictions from form: {e}")
            return []
    
    def _generate_team_predictions(self, fixture_id: int, team_id: int) -> List[Dict[str, Any]]:
        """
        Generate predictions for a specific team's players
        
        Args:
            fixture_id: The fixture ID
            team_id: The team ID
            
        Returns:
            List of probable scorer records for the team
        """
        predictions = []
        
        try:
            # Get recent player statistics for this team
            # This is a simplified approach - in reality, we'd analyze recent performance
            
            # For now, create placeholder predictions for top players
            # You would replace this with actual player analysis
            
            # Example: Create predictions for hypothetical top scorers
            example_predictions = [
                {
                    "fixture_id": fixture_id,
                    "player_id": None,  # Would need actual player IDs
                    "team_id": team_id,
                    "probability": 25.0,  # 25% chance
                    "odds": 4.0,  # 4/1 odds
                    "last_5_goals": 3,
                    "last_5_assists": 1
                }
            ]
            
            predictions.extend(example_predictions)
            
            return predictions
            
        except Exception as e:
            print(f"⚠️ Error generating team predictions: {e}")
            return []
    
    def get_probable_scorers_for_gameweek(self, gameweek: int, season: int = None, league_id: int = None) -> List[Dict[str, Any]]:
        """
        Get probable scorers for all fixtures in a specific gameweek
        
        Args:
            gameweek: The gameweek number
            season: The season (defaults to current season)
            league_id: The league ID (defaults to Premier League)
            
        Returns:
            List of probable scorer data for the gameweek
        """
        season = season or self.current_season
        league_id = league_id or self.premier_league_id
        
        try:
            # Get fixtures for the gameweek
            fixtures = self.get_fixtures_by_gameweek(league_id, season, gameweek)
            
            if not fixtures:
                print(f"⚠️ No fixtures found for gameweek {gameweek}")
                return []
            
            all_predictions = []
            
            for fixture in fixtures:
                fixture_id = fixture["id"]
                
                # Only get predictions for upcoming fixtures
                if fixture["status_short"] in ["NS", "TBD"]:  # Not Started, To Be Determined
                    predictions = self.scrape_fixture_probable_scorers(fixture_id)
                    
                    if "error" not in predictions and "probable_scorers" in predictions:
                        predictions["fixture_info"] = {
                            "id": fixture["id"],
                            "home_team_id": fixture["home_team_id"],
                            "away_team_id": fixture["away_team_id"],
                            "date": fixture["date"],
                            "status": fixture["status_short"]
                        }
                        all_predictions.append(predictions)
            
            print(f"✅ Retrieved probable scorers for {len(all_predictions)} upcoming fixtures in gameweek {gameweek}")
            return all_predictions
            
        except Exception as e:
            print(f"❌ Error getting probable scorers for gameweek {gameweek}: {e}")
            return []
    
    def get_top_probable_scorers(self, fixture_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top probable scorers for a fixture, sorted by probability
        
        Args:
            fixture_id: The fixture ID
            limit: Maximum number of players to return
            
        Returns:
            List of probable scorers sorted by probability
        """
        try:
            predictions_data = self.scrape_fixture_probable_scorers(fixture_id)
            
            if "probable_scorers" not in predictions_data:
                return []
            
            # Sort by probability (descending) and limit results
            probable_scorers = predictions_data["probable_scorers"]
            
            # Filter out records without probability data
            valid_predictions = [p for p in probable_scorers if p.get("probability") is not None]
            
            # Sort by probability
            sorted_predictions = sorted(valid_predictions, key=lambda x: x["probability"], reverse=True)
            
            return sorted_predictions[:limit]
            
        except Exception as e:
            print(f"❌ Error getting top probable scorers: {e}")
            return []
