"""
Lineup Scraper for Premier League Fixtures
Handles team lineups (starting XI and substitutes) for matches
"""

from typing import Dict, Any, List, Optional
from src.scrapers.base_scraper import BaseScraper


class LineupScraper(BaseScraper):
    """Scraper for fixture lineups - starting XI and substitutes"""
    
    def scrape_and_store(self, fixture_id: int, **kwargs) -> Dict[str, Any]:
        """
        Main method to scrape and store lineup data for a fixture
        
        Args:
            fixture_id: The fixture ID to get lineups for
            
        Returns:
            Dict containing lineup data or error information
        """
        return self.scrape_fixture_lineups(fixture_id)
    
    def scrape_fixture_lineups(self, fixture_id: int) -> Dict[str, Any]:
        """
        Scrape team lineups for a specific fixture
        
        Args:
            fixture_id: The fixture ID to get lineups for
            
        Returns:
            Dict containing lineup data or error information
        """
        try:
            # Check if we already have fresh lineup data
            cached_lineups = self.get_cached_data(
                "fixture_lineups",
                {"fixture_id": fixture_id},
                max_age_hours=2  # Lineups don't change much once announced
            )
            
            if cached_lineups:
                print(f"✅ Using cached lineups for fixture {fixture_id}")
                # Also get the lineup players
                lineup_players = []
                for lineup in cached_lineups:
                    players = self.get_cached_data(
                        "lineup_players",
                        {"lineup_id": lineup["id"]},
                        max_age_hours=2
                    )
                    if players:
                        lineup_players.extend(players)
                
                return {
                    "fixture_id": fixture_id,
                    "lineups": cached_lineups,
                    "players": lineup_players,
                    "source": "cache"
                }
            
            # Fetch from API
            print(f"🔄 Fetching lineups for fixture {fixture_id} from API...")
            
            response = self.make_api_request(
                "fixtures/lineups",
                {"fixture": fixture_id},
                priority="high"
            )
            
            if "error" in response:
                print(f"❌ Error fetching lineups: {response['error']}")
                return {"error": response["error"], "fixture_id": fixture_id}
            
            # Process and store lineup data
            return self._process_and_store_lineups(fixture_id, response)
            
        except Exception as e:
            error_msg = f"Error scraping lineups for fixture {fixture_id}: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg, "fixture_id": fixture_id}
    
    def _process_and_store_lineups(self, fixture_id: int, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process API response and store lineup data in database
        
        Args:
            fixture_id: The fixture ID
            api_response: Raw API response
            
        Returns:
            Dict containing processed lineup data
        """
        try:
            lineup_records = []
            player_records = []
            
            for team_data in api_response.get("response", []):
                team_info = team_data.get("team", {})
                coach_info = team_data.get("coach", {})
                formation = team_data.get("formation", "")
                
                # Create lineup record
                lineup_record = {
                    "fixture_id": fixture_id,
                    "team_id": team_info.get("id"),
                    "formation": formation,
                    "coach_id": coach_info.get("id"),
                    "coach_name": coach_info.get("name"),
                    "coach_photo": coach_info.get("photo")
                }
                
                lineup_records.append(lineup_record)
                
                # Process starting XI
                for player_data in team_data.get("startXI", []):
                    player_info = player_data.get("player", {})
                    player_record = {
                        "fixture_id": fixture_id,  # We'll update this with lineup_id after insert
                        "team_id": team_info.get("id"),
                        "player_id": player_info.get("id"),
                        "player_name": player_info.get("name"),
                        "player_number": player_info.get("number"),
                        "player_pos": player_info.get("pos"),
                        "grid": player_info.get("grid"),
                        "is_starter": True
                    }
                    player_records.append(player_record)
                
                # Process substitutes
                for player_data in team_data.get("substitutes", []):
                    player_info = player_data.get("player", {})
                    player_record = {
                        "fixture_id": fixture_id,  # We'll update this with lineup_id after insert
                        "team_id": team_info.get("id"),
                        "player_id": player_info.get("id"),
                        "player_name": player_info.get("name"),
                        "player_number": player_info.get("number"),
                        "player_pos": player_info.get("pos"),
                        "grid": player_info.get("grid"),
                        "is_starter": False
                    }
                    player_records.append(player_record)
            
            # Store lineup records
            if lineup_records:
                success = self.store_data(
                    "fixture_lineups", 
                    lineup_records, 
                    unique_keys=["fixture_id", "team_id"]
                )
                
                if success:
                    print(f"✅ Stored {len(lineup_records)} lineup records")
                    
                    # Get the inserted lineup IDs and update player records
                    stored_lineups = self.get_cached_data(
                        "fixture_lineups",
                        {"fixture_id": fixture_id},
                        max_age_hours=1
                    )
                    
                    if stored_lineups:
                        # Create mapping of team_id to lineup_id
                        team_to_lineup = {lineup["team_id"]: lineup["id"] for lineup in stored_lineups}
                        
                        # Update player records with correct lineup_id
                        for player_record in player_records:
                            team_id = player_record["team_id"]
                            if team_id in team_to_lineup:
                                player_record["lineup_id"] = team_to_lineup[team_id]
                                # Remove fixture_id as we have lineup_id now
                                del player_record["fixture_id"]
                                del player_record["team_id"]
                        
                        # Store player records
                        if player_records:
                            player_success = self.store_data(
                                "lineup_players",
                                player_records,
                                unique_keys=["lineup_id", "player_id"]
                            )
                            
                            if player_success:
                                print(f"✅ Stored {len(player_records)} player records")
                
                return {
                    "fixture_id": fixture_id,
                    "lineups": lineup_records,
                    "players": player_records,
                    "source": "api",
                    "success": True
                }
            else:
                return {
                    "fixture_id": fixture_id,
                    "message": "No lineup data available yet",
                    "source": "api"
                }
                
        except Exception as e:
            error_msg = f"Error processing lineup data: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg, "fixture_id": fixture_id}
    
    def get_lineups_for_gameweek(self, gameweek: int, season: int = None, league_id: int = None) -> List[Dict[str, Any]]:
        """
        Get lineups for all fixtures in a specific gameweek
        
        Args:
            gameweek: The gameweek number
            season: The season (defaults to current season)
            league_id: The league ID (defaults to Premier League)
            
        Returns:
            List of lineup data for the gameweek
        """
        season = season or self.current_season
        league_id = league_id or self.premier_league_id
        
        try:
            # Get fixtures for the gameweek
            fixtures = self.get_fixtures_by_gameweek(league_id, season, gameweek)
            
            if not fixtures:
                print(f"⚠️ No fixtures found for gameweek {gameweek}")
                return []
            
            all_lineups = []
            
            for fixture in fixtures:
                fixture_id = fixture["id"]
                lineups = self.scrape_fixture_lineups(fixture_id)
                
                if "error" not in lineups:
                    lineups["fixture_info"] = {
                        "id": fixture["id"],
                        "home_team_id": fixture["home_team_id"],
                        "away_team_id": fixture["away_team_id"],
                        "date": fixture["date"],
                        "status": fixture["status_short"]
                    }
                    all_lineups.append(lineups)
                else:
                    print(f"⚠️ Could not get lineups for fixture {fixture_id}: {lineups.get('error')}")
            
            print(f"✅ Retrieved lineups for {len(all_lineups)}/{len(fixtures)} fixtures in gameweek {gameweek}")
            return all_lineups
            
        except Exception as e:
            print(f"❌ Error getting lineups for gameweek {gameweek}: {e}")
            return []
    
    def get_team_lineup(self, fixture_id: int, team_id: int) -> Optional[Dict[str, Any]]:
        """
        Get lineup for a specific team in a fixture
        
        Args:
            fixture_id: The fixture ID
            team_id: The team ID
            
        Returns:
            Dict containing team lineup data or None
        """
        try:
            # Get lineup data
            lineup_data = self.get_cached_data(
                "fixture_lineups",
                {"fixture_id": fixture_id, "team_id": team_id},
                max_age_hours=6
            )
            
            if not lineup_data:
                # Try to fetch from API
                full_lineups = self.scrape_fixture_lineups(fixture_id)
                if "lineups" in full_lineups:
                    lineup_data = [l for l in full_lineups["lineups"] if l["team_id"] == team_id]
            
            if not lineup_data:
                return None
            
            lineup = lineup_data[0]
            
            # Get players for this lineup
            players = self.get_cached_data(
                "lineup_players",
                {"lineup_id": lineup["id"]},
                max_age_hours=6
            )
            
            if players:
                starters = [p for p in players if p["is_starter"]]
                substitutes = [p for p in players if not p["is_starter"]]
                
                return {
                    "lineup": lineup,
                    "starting_xi": starters,
                    "substitutes": substitutes
                }
            
            return {"lineup": lineup, "starting_xi": [], "substitutes": []}
            
        except Exception as e:
            print(f"❌ Error getting team lineup: {e}")
            return None
