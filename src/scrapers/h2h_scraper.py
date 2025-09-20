"""
Head-to-Head Scraper for Premier League Teams
Handles historical matchup records between teams
"""

from typing import Dict, Any, List, Optional
from src.scrapers.base_scraper import BaseScraper


class HeadToHeadScraper(BaseScraper):
    """Scraper for head-to-head records between teams"""
    
    def scrape_and_store(self, team1_id: int, team2_id: int, **kwargs) -> Dict[str, Any]:
        """
        Main method to scrape and store H2H data between two teams
        
        Args:
            team1_id: First team ID
            team2_id: Second team ID
            
        Returns:
            Dict containing H2H data or error information
        """
        return self.scrape_h2h_record(team1_id, team2_id)
    
    def scrape_h2h_record(self, team1_id: int, team2_id: int) -> Dict[str, Any]:
        """
        Scrape head-to-head record between two teams
        
        Args:
            team1_id: First team ID
            team2_id: Second team ID
            
        Returns:
            Dict containing H2H data or error information
        """
        try:
            # Check if we have fresh H2H data (check both directions)
            cached_h2h = self.get_cached_data(
                "head_to_head",
                {"team1_id": team1_id, "team2_id": team2_id},
                max_age_hours=720  # Update monthly (30 days)
            )
            
            if not cached_h2h:
                # Try reverse direction
                cached_h2h = self.get_cached_data(
                    "head_to_head",
                    {"team1_id": team2_id, "team2_id": team1_id},
                    max_age_hours=720
                )
            
            if cached_h2h:
                print(f"Using cached H2H for teams {team1_id} vs {team2_id}")
                
                # Get recent fixtures between these teams
                recent_fixtures = self._get_recent_h2h_fixtures(team1_id, team2_id, limit=10)
                
                return {
                    "team1_id": team1_id,
                    "team2_id": team2_id,
                    "h2h_record": cached_h2h[0],
                    "recent_fixtures": recent_fixtures,
                    "source": "cache"
                }
            
            # Calculate from existing fixture data first (faster)
            calculated_h2h = self._calculate_h2h_from_fixtures(team1_id, team2_id)
            
            if calculated_h2h:
                return calculated_h2h
            
            # Fallback to API if needed
            print(f"Fetching H2H for teams {team1_id} vs {team2_id} from API...")
            
            response = self.make_api_request(
                "fixtures/headtohead",
                {"h2h": f"{team1_id}-{team2_id}"},
                priority="low"
            )
            
            if "error" in response:
                print(f"Error fetching H2H: {response['error']}")
                return {"error": response["error"], "team1_id": team1_id, "team2_id": team2_id}
            
            # Process and store H2H data
            return self._process_and_store_h2h(team1_id, team2_id, response)
            
        except Exception as e:
            error_msg = f"Error scraping H2H for teams {team1_id} vs {team2_id}: {e}"
            print(f"Error: {error_msg}")
            return {"error": error_msg, "team1_id": team1_id, "team2_id": team2_id}
    
    def _calculate_h2h_from_fixtures(self, team1_id: int, team2_id: int) -> Optional[Dict[str, Any]]:
        """
        Calculate H2H record from existing fixture data (fast, no API calls)
        
        Args:
            team1_id: First team ID
            team2_id: Second team ID
            
        Returns:
            Dict with calculated H2H record or None
        """
        try:
            # Get all completed fixtures between these teams
            fixtures = self.db.client.table("fixtures").select("*").eq("league_id", self.premier_league_id).eq("status_short", "FT").or_(
                f"and(home_team_id.eq.{team1_id},away_team_id.eq.{team2_id}),and(home_team_id.eq.{team2_id},away_team_id.eq.{team1_id})"
            ).order("date", desc=True).execute()
            
            if not fixtures.data:
                return None
            
            # Calculate H2H statistics
            total_matches = 0
            team1_wins = 0
            team2_wins = 0
            draws = 0
            last_match = None
            
            for fixture in fixtures.data:
                if fixture["home_score"] is None or fixture["away_score"] is None:
                    continue
                
                total_matches += 1
                
                # Track last match
                if not last_match:
                    last_match = fixture
                
                # Determine winner
                home_score = fixture["home_score"]
                away_score = fixture["away_score"]
                
                if fixture["home_team_id"] == team1_id:
                    # Team1 is home
                    if home_score > away_score:
                        team1_wins += 1
                    elif home_score < away_score:
                        team2_wins += 1
                    else:
                        draws += 1
                else:
                    # Team2 is home
                    if home_score > away_score:
                        team2_wins += 1
                    elif home_score < away_score:
                        team1_wins += 1
                    else:
                        draws += 1
            
            if total_matches == 0:
                return None
            
            # Create H2H record
            h2h_record = {
                "team1_id": team1_id,
                "team2_id": team2_id,
                "total_matches": total_matches,
                "team1_wins": team1_wins,
                "team2_wins": team2_wins,
                "draws": draws,
                "last_match_id": last_match["id"] if last_match else None,
                "last_match_date": last_match["date"] if last_match else None
            }
            
            # Store H2H record
            success = self.store_data(
                "head_to_head",
                [h2h_record],
                unique_keys=["team1_id", "team2_id"]
            )
            
            if success:
                print(f"Stored calculated H2H record for teams {team1_id} vs {team2_id}")
                
                # Get recent fixtures
                recent_fixtures = self._get_recent_h2h_fixtures(team1_id, team2_id, limit=5)
                
                return {
                    "team1_id": team1_id,
                    "team2_id": team2_id,
                    "h2h_record": h2h_record,
                    "recent_fixtures": recent_fixtures,
                    "source": "calculated_from_fixtures",
                    "success": True
                }
            
            return None
            
        except Exception as e:
            print(f"Error calculating H2H from fixtures: {e}")
            return None
    
    def _get_recent_h2h_fixtures(self, team1_id: int, team2_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent fixtures between two teams
        
        Args:
            team1_id: First team ID
            team2_id: Second team ID
            limit: Number of recent fixtures to return
            
        Returns:
            List of recent fixtures between the teams
        """
        try:
            # Get recent fixtures between these teams
            fixtures = self.db.client.table("fixtures").select("*").eq("league_id", self.premier_league_id).or_(
                f"and(home_team_id.eq.{team1_id},away_team_id.eq.{team2_id}),and(home_team_id.eq.{team2_id},away_team_id.eq.{team1_id})"
            ).order("date", desc=True).limit(limit).execute()
            
            recent_fixtures = []
            
            for fixture in fixtures.data:
                # Determine which team was home/away
                if fixture["home_team_id"] == team1_id:
                    team1_home = True
                    team1_score = fixture["home_score"]
                    team2_score = fixture["away_score"]
                else:
                    team1_home = False
                    team1_score = fixture["away_score"]
                    team2_score = fixture["home_score"]
                
                # Determine result from team1's perspective
                if team1_score is not None and team2_score is not None:
                    if team1_score > team2_score:
                        result = "team1_win"
                    elif team1_score < team2_score:
                        result = "team2_win"
                    else:
                        result = "draw"
                else:
                    result = "not_played"
                
                recent_fixtures.append({
                    "fixture_id": fixture["id"],
                    "date": fixture["date"],
                    "gameweek": fixture.get("gameweek"),
                    "team1_home": team1_home,
                    "team1_score": team1_score,
                    "team2_score": team2_score,
                    "result": result,
                    "status": fixture["status_short"]
                })
            
            return recent_fixtures
            
        except Exception as e:
            print(f"Error getting recent H2H fixtures: {e}")
            return []
    
    def generate_all_h2h_records(self, season: int = None) -> Dict[str, Any]:
        """
        Generate H2H records for all Premier League team combinations
        
        Args:
            season: The season (defaults to current season)
            
        Returns:
            Dict with results for all team combinations
        """
        season = season or self.current_season
        
        try:
            # Get all Premier League teams
            teams = self.get_premier_league_teams()
            
            if not teams:
                return {"error": "No Premier League teams found"}
            
            results = {
                "season": season,
                "combinations_processed": 0,
                "combinations_success": 0,
                "combinations_failed": 0,
                "total_combinations": 0,
                "errors": []
            }
            
            # Calculate total combinations (n choose 2)
            total_teams = len(teams)
            results["total_combinations"] = (total_teams * (total_teams - 1)) // 2
            
            for i, team1 in enumerate(teams):
                for team2 in teams[i+1:]:  # Avoid duplicates and self-matches
                    team1_id = team1["id"]
                    team2_id = team2["id"]
                    team1_name = team1["name"]
                    team2_name = team2["name"]
                    
                    print(f"Processing H2H: {team1_name} vs {team2_name}")
                    
                    h2h_result = self.scrape_h2h_record(team1_id, team2_id)
                    results["combinations_processed"] += 1
                    
                    if "error" not in h2h_result:
                        results["combinations_success"] += 1
                        print(f"Success: {team1_name} vs {team2_name} H2H updated")
                    else:
                        results["combinations_failed"] += 1
                        results["errors"].append(f"{team1_name} vs {team2_name}: {h2h_result['error']}")
                        print(f"Failed: {team1_name} vs {team2_name} - {h2h_result['error']}")
            
            print(f"H2H generation complete: {results['combinations_success']}/{results['combinations_processed']} combinations successful")
            return results
            
        except Exception as e:
            return {"error": f"Error generating all H2H records: {e}"}
