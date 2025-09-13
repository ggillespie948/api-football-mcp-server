"""
Goalscorer Scraper for Premier League Fixtures
Handles goal scorer information for completed and live matches
"""

from typing import Dict, Any, List, Optional
from src.scrapers.base_scraper import BaseScraper


class GoalscorerScraper(BaseScraper):
    """Scraper for fixture goal scorers and assists"""
    
    def scrape_and_store(self, fixture_id: int, **kwargs) -> Dict[str, Any]:
        """
        Main method to scrape and store goalscorer data for a fixture
        
        Args:
            fixture_id: The fixture ID to get goalscorers for
            
        Returns:
            Dict containing goalscorer data or error information
        """
        return self.scrape_fixture_goalscorers(fixture_id)
    
    def scrape_fixture_goalscorers(self, fixture_id: int) -> Dict[str, Any]:
        """
        Scrape goal scorers for a specific fixture
        
        Args:
            fixture_id: The fixture ID to get goalscorers for
            
        Returns:
            Dict containing goalscorer data or error information
        """
        try:
            # Check if we have fresh goalscorer data
            cached_goalscorers = self.get_cached_data(
                "fixture_goalscorers",
                {"fixture_id": fixture_id},
                max_age_hours=1  # Update frequently during/after matches
            )
            
            if cached_goalscorers:
                print(f"✅ Using cached goalscorers for fixture {fixture_id}")
                return {
                    "fixture_id": fixture_id,
                    "goalscorers": cached_goalscorers,
                    "source": "cache"
                }
            
            # Fetch from API using the players endpoint for fixture
            print(f"🔄 Fetching goalscorers for fixture {fixture_id} from API...")
            
            response = self.make_api_request(
                "fixtures/players",
                {"fixture": fixture_id},
                priority="high"
            )
            
            if "error" in response:
                print(f"❌ Error fetching fixture players: {response['error']}")
                return {"error": response["error"], "fixture_id": fixture_id}
            
            # Process and store goalscorer data
            return self._process_and_store_goalscorers(fixture_id, response)
            
        except Exception as e:
            error_msg = f"Error scraping goalscorers for fixture {fixture_id}: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg, "fixture_id": fixture_id}
    
    def _process_and_store_goalscorers(self, fixture_id: int, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process API response and store goalscorer data in database
        
        Args:
            fixture_id: The fixture ID
            api_response: Raw API response from fixtures/players endpoint
            
        Returns:
            Dict containing processed goalscorer data
        """
        try:
            goalscorer_records = []
            
            for team_data in api_response.get("response", []):
                team_info = team_data.get("team", {})
                team_id = team_info.get("id")
                
                for player_data in team_data.get("players", []):
                    player_info = player_data.get("player", {})
                    player_id = player_info.get("id")
                    
                    # Get player statistics for this match
                    for stats in player_data.get("statistics", []):
                        goals_data = stats.get("goals", {})
                        goals_total = goals_data.get("total") or 0
                        
                        # If player scored goals, we need to get details from events
                        if goals_total and goals_total > 0:
                            # We'll need to cross-reference with fixture events to get timing
                            # For now, create records with the goal count
                            for goal_num in range(goals_total):
                                goalscorer_record = {
                                    "fixture_id": fixture_id,
                                    "team_id": team_id,
                                    "player_id": player_id,
                                    "assist_player_id": None,  # We'll try to get this from events
                                    "time_elapsed": None,      # We'll try to get this from events
                                    "time_extra": None,
                                    "goal_type": "Normal Goal"  # Default, we'll refine this from events
                                }
                                goalscorer_records.append(goalscorer_record)
            
            # Try to enhance goalscorer data with event details
            enhanced_goalscorers = self._enhance_with_events(fixture_id, goalscorer_records)
            
            # Store goalscorer records
            if enhanced_goalscorers:
                success = self.store_data(
                    "fixture_goalscorers",
                    enhanced_goalscorers,
                    unique_keys=["fixture_id", "player_id", "time_elapsed"]
                )
                
                if success:
                    print(f"✅ Stored {len(enhanced_goalscorers)} goalscorer records")
                
                return {
                    "fixture_id": fixture_id,
                    "goalscorers": enhanced_goalscorers,
                    "source": "api",
                    "success": True
                }
            else:
                return {
                    "fixture_id": fixture_id,
                    "message": "No goals scored in this fixture yet",
                    "source": "api"
                }
                
        except Exception as e:
            error_msg = f"Error processing goalscorer data: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg, "fixture_id": fixture_id}
    
    def _enhance_with_events(self, fixture_id: int, goalscorer_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance goalscorer records with detailed timing and type from fixture events
        
        Args:
            fixture_id: The fixture ID
            goalscorer_records: Basic goalscorer records
            
        Returns:
            Enhanced goalscorer records with event details
        """
        try:
            # Get fixture events
            events_response = self.make_api_request(
                "fixtures/events",
                {"fixture": fixture_id},
                priority="medium"
            )
            
            if "error" in events_response:
                print(f"⚠️ Could not get events for fixture {fixture_id}: {events_response['error']}")
                return goalscorer_records
            
            # Process events to find goal details
            enhanced_records = []
            goal_events = []
            
            for event in events_response.get("response", []):
                event_type = event.get("type", "").lower()
                event_detail = event.get("detail", "").lower()
                
                # Check if this is a goal event
                if event_type == "goal" or "goal" in event_detail:
                    goal_events.append({
                        "player_id": event.get("player", {}).get("id"),
                        "assist_id": event.get("assist", {}).get("id"),
                        "team_id": event.get("team", {}).get("id"),
                        "time_elapsed": event.get("time", {}).get("elapsed"),
                        "time_extra": event.get("time", {}).get("extra"),
                        "goal_type": self._determine_goal_type(event_detail),
                        "comments": event.get("comments")
                    })
            
            # Match goalscorer records with events
            for record in goalscorer_records:
                player_id = record["player_id"]
                team_id = record["team_id"]
                
                # Find matching goal event
                matching_event = None
                for i, event in enumerate(goal_events):
                    if (event["player_id"] == player_id and 
                        event["team_id"] == team_id and 
                        event not in [e.get("matched_event") for e in enhanced_records]):
                        matching_event = event
                        break
                
                if matching_event:
                    # Enhance record with event details
                    enhanced_record = record.copy()
                    enhanced_record.update({
                        "assist_player_id": matching_event["assist_id"],
                        "time_elapsed": matching_event["time_elapsed"],
                        "time_extra": matching_event["time_extra"],
                        "goal_type": matching_event["goal_type"]
                    })
                    enhanced_record["matched_event"] = matching_event
                    enhanced_records.append(enhanced_record)
                else:
                    # Keep original record
                    enhanced_records.append(record)
            
            # Clean up the matched_event field
            for record in enhanced_records:
                if "matched_event" in record:
                    del record["matched_event"]
            
            print(f"✅ Enhanced {len(enhanced_records)} goalscorer records with event details")
            return enhanced_records
            
        except Exception as e:
            print(f"⚠️ Error enhancing with events: {e}")
            return goalscorer_records
    
    def _determine_goal_type(self, event_detail: str) -> str:
        """
        Determine goal type from event detail string
        
        Args:
            event_detail: The event detail from API
            
        Returns:
            Goal type string
        """
        detail_lower = event_detail.lower()
        
        if "penalty" in detail_lower:
            return "Penalty"
        elif "own goal" in detail_lower:
            return "Own Goal"
        elif "free kick" in detail_lower:
            return "Free Kick"
        elif "header" in detail_lower:
            return "Header"
        else:
            return "Normal Goal"
    
    def get_goalscorers_for_gameweek(self, gameweek: int, season: int = None, league_id: int = None) -> List[Dict[str, Any]]:
        """
        Get goalscorers for all fixtures in a specific gameweek
        
        Args:
            gameweek: The gameweek number
            season: The season (defaults to current season)
            league_id: The league ID (defaults to Premier League)
            
        Returns:
            List of goalscorer data for the gameweek
        """
        season = season or self.current_season
        league_id = league_id or self.premier_league_id
        
        try:
            # Get fixtures for the gameweek
            fixtures = self.get_fixtures_by_gameweek(league_id, season, gameweek)
            
            if not fixtures:
                print(f"⚠️ No fixtures found for gameweek {gameweek}")
                return []
            
            all_goalscorers = []
            
            for fixture in fixtures:
                fixture_id = fixture["id"]
                goalscorers = self.scrape_fixture_goalscorers(fixture_id)
                
                if "error" not in goalscorers and "goalscorers" in goalscorers:
                    goalscorers["fixture_info"] = {
                        "id": fixture["id"],
                        "home_team_id": fixture["home_team_id"],
                        "away_team_id": fixture["away_team_id"],
                        "date": fixture["date"],
                        "status": fixture["status_short"],
                        "home_score": fixture["home_score"],
                        "away_score": fixture["away_score"]
                    }
                    all_goalscorers.append(goalscorers)
            
            print(f"✅ Retrieved goalscorers for {len(all_goalscorers)} fixtures in gameweek {gameweek}")
            return all_goalscorers
            
        except Exception as e:
            print(f"❌ Error getting goalscorers for gameweek {gameweek}: {e}")
            return []
    
    def get_player_goals_in_fixture(self, fixture_id: int, player_id: int) -> List[Dict[str, Any]]:
        """
        Get all goals scored by a specific player in a fixture
        
        Args:
            fixture_id: The fixture ID
            player_id: The player ID
            
        Returns:
            List of goal records for the player
        """
        try:
            goals = self.get_cached_data(
                "fixture_goalscorers",
                {"fixture_id": fixture_id, "player_id": player_id},
                max_age_hours=1
            )
            
            if not goals:
                # Try to fetch fresh data
                goalscorer_data = self.scrape_fixture_goalscorers(fixture_id)
                if "goalscorers" in goalscorer_data:
                    goals = [g for g in goalscorer_data["goalscorers"] if g["player_id"] == player_id]
            
            return goals or []
            
        except Exception as e:
            print(f"❌ Error getting player goals: {e}")
            return []
    
    def get_top_scorers_for_gameweek(self, gameweek: int, season: int = None, league_id: int = None) -> List[Dict[str, Any]]:
        """
        Get top scorers for a specific gameweek
        
        Args:
            gameweek: The gameweek number
            season: The season (defaults to current season)
            league_id: The league ID (defaults to Premier League)
            
        Returns:
            List of players sorted by goals scored in the gameweek
        """
        try:
            goalscorer_data = self.get_goalscorers_for_gameweek(gameweek, season, league_id)
            
            # Count goals per player
            player_goals = {}
            
            for fixture_data in goalscorer_data:
                for goal in fixture_data.get("goalscorers", []):
                    player_id = goal["player_id"]
                    
                    if player_id not in player_goals:
                        player_goals[player_id] = {
                            "player_id": player_id,
                            "goals": 0,
                            "fixtures": []
                        }
                    
                    player_goals[player_id]["goals"] += 1
                    player_goals[player_id]["fixtures"].append({
                        "fixture_id": goal["fixture_id"],
                        "team_id": goal["team_id"],
                        "goal_type": goal["goal_type"],
                        "time_elapsed": goal["time_elapsed"]
                    })
            
            # Sort by goals scored
            top_scorers = sorted(player_goals.values(), key=lambda x: x["goals"], reverse=True)
            
            return top_scorers
            
        except Exception as e:
            print(f"❌ Error getting top scorers for gameweek {gameweek}: {e}")
            return []
