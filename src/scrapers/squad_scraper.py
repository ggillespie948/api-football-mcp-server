"""
Squad Scraper for Premier League Teams
Handles team rosters and player information
"""

from typing import Dict, Any, List, Optional
from src.scrapers.base_scraper import BaseScraper


class SquadScraper(BaseScraper):
    """Scraper for team squads and player rosters"""
    
    def scrape_and_store(self, team_id: int, season: int = None, **kwargs) -> Dict[str, Any]:
        """
        Main method to scrape and store squad data for a team
        
        Args:
            team_id: The team ID to get squad for
            season: The season (defaults to current season)
            
        Returns:
            Dict containing squad data or error information
        """
        return self.scrape_team_squad(team_id, season)
    
    def scrape_team_squad(self, team_id: int, season: int = None) -> Dict[str, Any]:
        """
        Scrape squad/roster for a specific team
        
        Args:
            team_id: The team ID to get squad for
            season: The season (defaults to current season)
            
        Returns:
            Dict containing squad data or error information
        """
        season = season or self.current_season
        
        try:
            # Check if we have fresh squad data
            cached_squad = self.get_cached_data(
                "team_squads",
                {"team_id": team_id, "season": season},
                max_age_hours=168  # Update weekly (7 days)
            )
            
            if cached_squad:
                print(f"Using cached squad for team {team_id}")
                
                # Get player details
                player_details = []
                for squad_member in cached_squad:
                    player_info = self.get_cached_data(
                        "players",
                        {"id": squad_member["player_id"]},
                        max_age_hours=168
                    )
                    if player_info:
                        player_details.extend(player_info)
                
                return {
                    "team_id": team_id,
                    "season": season,
                    "squad": cached_squad,
                    "players": player_details,
                    "source": "cache"
                }
            
            # Fetch from API
            print(f"Fetching squad for team {team_id} from API...")
            
            response = self.make_api_request(
                "players",
                {"team": team_id, "season": season},
                priority="medium"
            )
            
            if "error" in response:
                print(f"Error fetching squad: {response['error']}")
                return {"error": response["error"], "team_id": team_id}
            
            # Process and store squad data
            return self._process_and_store_squad(team_id, season, response)
            
        except Exception as e:
            error_msg = f"Error scraping squad for team {team_id}: {e}"
            print(f"Error: {error_msg}")
            return {"error": error_msg, "team_id": team_id}
    
    def _process_and_store_squad(self, team_id: int, season: int, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process API response and store squad data in database
        
        Args:
            team_id: The team ID
            season: The season
            api_response: Raw API response from players endpoint
            
        Returns:
            Dict containing processed squad data
        """
        try:
            squad_records = []
            player_records = []
            
            for player_data in api_response.get("response", []):
                player_info = player_data.get("player", {})
                statistics = player_data.get("statistics", [])
                
                # Store player information
                player_record = {
                    "id": player_info.get("id"),
                    "firstname": player_info.get("firstname"),
                    "lastname": player_info.get("lastname"),
                    "age": player_info.get("age"),
                    "birth_date": player_info.get("birth", {}).get("date"),
                    "birth_place": player_info.get("birth", {}).get("place"),
                    "birth_country": player_info.get("birth", {}).get("country"),
                    "nationality": player_info.get("nationality"),
                    "height": player_info.get("height"),
                    "weight": player_info.get("weight"),
                    "photo": player_info.get("photo")
                }
                player_records.append(player_record)
                
                # Store squad membership
                if statistics:
                    for stat in statistics:
                        games_info = stat.get("games", {})
                        squad_record = {
                            "team_id": team_id,
                            "player_id": player_info.get("id"),
                            "season": season,
                            "position": games_info.get("position"),
                            "jersey_number": games_info.get("number"),
                            "is_active": True
                        }
                        squad_records.append(squad_record)
                        break  # Only need one statistics entry for squad info
            
            # Store player records (upsert to handle updates)
            if player_records:
                success = self.store_data(
                    "players",
                    player_records,
                    unique_keys=["id"]
                )
                
                if success:
                    print(f"Stored {len(player_records)} player records")
            
            # Store squad records
            if squad_records:
                success = self.store_data(
                    "team_squads",
                    squad_records,
                    unique_keys=["team_id", "player_id", "season"]
                )
                
                if success:
                    print(f"Stored {len(squad_records)} squad records")
                
                return {
                    "team_id": team_id,
                    "season": season,
                    "squad": squad_records,
                    "players": player_records,
                    "source": "api",
                    "success": True
                }
            else:
                return {
                    "team_id": team_id,
                    "season": season,
                    "message": "No squad data available",
                    "source": "api"
                }
                
        except Exception as e:
            error_msg = f"Error processing squad data: {e}"
            print(f"Error: {error_msg}")
            return {"error": error_msg, "team_id": team_id}
    
    def scrape_all_premier_league_squads(self, season: int = None) -> Dict[str, Any]:
        """
        Scrape squads for all Premier League teams
        
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
                "total_players": 0,
                "errors": []
            }
            
            for team in teams:
                team_id = team["id"]
                team_name = team["name"]
                
                print(f"Processing squad for {team_name} (ID: {team_id})...")
                
                squad_result = self.scrape_team_squad(team_id, season)
                results["teams_processed"] += 1
                
                if "error" not in squad_result:
                    results["teams_success"] += 1
                    if "players" in squad_result:
                        results["total_players"] += len(squad_result["players"])
                    print(f"Success: {team_name} squad updated")
                else:
                    results["teams_failed"] += 1
                    results["errors"].append(f"{team_name}: {squad_result['error']}")
                    print(f"Failed: {team_name} - {squad_result['error']}")
            
            print(f"Squad scraping complete: {results['teams_success']}/{results['teams_processed']} teams successful")
            return results
            
        except Exception as e:
            return {"error": f"Error scraping all squads: {e}"}
    
    def get_team_squad_from_cache(self, team_id: int, season: int = None) -> List[Dict[str, Any]]:
        """
        Get team squad from cache with player details
        
        Args:
            team_id: The team ID
            season: The season (defaults to current season)
            
        Returns:
            List of squad members with player details
        """
        season = season or self.current_season
        
        try:
            # Get squad members
            squad_members = self.get_cached_data(
                "team_squads",
                {"team_id": team_id, "season": season, "is_active": True},
                max_age_hours=168
            )
            
            if not squad_members:
                return []
            
            # Get player details for each squad member
            squad_with_details = []
            
            for member in squad_members:
                player_id = member["player_id"]
                
                # Get player details
                player_details = self.get_cached_data(
                    "players",
                    {"id": player_id},
                    max_age_hours=168
                )
                
                if player_details:
                    player = player_details[0]
                    squad_with_details.append({
                        "player_id": player_id,
                        "name": f"{player.get('firstname', '')} {player.get('lastname', '')}".strip(),
                        "position": member.get("position"),
                        "jersey_number": member.get("jersey_number"),
                        "age": player.get("age"),
                        "nationality": player.get("nationality"),
                        "height": player.get("height"),
                        "weight": player.get("weight"),
                        "photo": player.get("photo")
                    })
            
            return squad_with_details
            
        except Exception as e:
            print(f"Error getting squad from cache: {e}")
            return []
    
    def get_squad_by_position(self, team_id: int, position: str, season: int = None) -> List[Dict[str, Any]]:
        """
        Get squad members by position (e.g., "Goalkeeper", "Defender")
        
        Args:
            team_id: The team ID
            position: The position to filter by
            season: The season (defaults to current season)
            
        Returns:
            List of players in the specified position
        """
        try:
            all_squad = self.get_team_squad_from_cache(team_id, season)
            
            # Filter by position
            position_players = [
                player for player in all_squad 
                if player.get("position", "").lower() == position.lower()
            ]
            
            return position_players
            
        except Exception as e:
            print(f"Error getting squad by position: {e}")
            return []
