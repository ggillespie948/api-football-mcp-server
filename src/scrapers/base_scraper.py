"""
Enhanced Base Scraper Class with Mode-Aware Rate Limiting
Provides common functionality for all API Football scrapers
"""

import os
import requests
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from src.utils.adaptive_rate_limiter import AdaptiveRateLimiter
from src.database.connection import SupabaseManager
from src.config.request_mode_manager import RequestModeManager
from src.config.settings import get_settings


class BaseScraper:
    """Base class for all API Football scrapers with enhanced rate limiting"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db = SupabaseManager()
        self.rate_limiter = AdaptiveRateLimiter()
        self.mode_manager = RequestModeManager()
        
        # API Configuration
        self.api_key = self.settings.RAPID_API_KEY_FOOTBALL
        self.base_url = self.settings.BASE_API_URL
        self.headers = self.settings.get_api_headers()
        
        # Premier League specific - use global settings
        self.premier_league_id = self.settings.PREMIER_LEAGUE_ID
        self.current_season = self.settings.DEFAULT_SEASON
        
        print(f"BaseScraper initialized: Premier League {self.premier_league_id}, Season {self.current_season}")
        
        # Request settings
        self.default_timeout = 30
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("RAPID_API_KEY_FOOTBALL is not set in environment variables")
    
    def scrape_and_store(self, **kwargs) -> Dict[str, Any]:
        """Base implementation - can be overridden by subclasses"""
        return {"message": "Base scraper - override this method"}
    
    def make_api_request(self, endpoint: str, params: Dict[str, Any], priority: str = 'medium') -> Dict[str, Any]:
        """
        Make an API request with rate limiting and error handling
        
        Args:
            endpoint: API endpoint (e.g., 'fixtures', 'teams')
            params: Query parameters
            priority: Request priority for rate limiting
            
        Returns:
            Dict containing API response or error information
        """
        # Check rate limits before making request
        if not self.rate_limiter.can_make_request(endpoint, priority):
            return {
                "error": "Rate limit exceeded or request not allowed in current mode",
                "endpoint": endpoint,
                "priority": priority,
                "current_mode": self.mode_manager.get_current_mode()
            }
        
        # Build full URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Attempt request with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.default_timeout
                )
                
                # Check for successful response
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                
                # Log successful request
                self.log_api_request(
                    endpoint=endpoint,
                    params=params,
                    response_size=len(response.content),
                    status_code=response.status_code,
                    success=True
                )
                
                # Record request in rate limiter
                self.rate_limiter.record_request(endpoint, success=True)
                
                return data
                
            except requests.exceptions.Timeout:
                error_msg = f"Request timeout (attempt {attempt + 1}/{self.max_retries})"
                if attempt < self.max_retries - 1:
                    print(f"{error_msg}, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self._handle_request_error(endpoint, params, error_msg)
                    return {"error": error_msg}
                    
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 0
                error_msg = f"HTTP {status_code} error: {str(e)}"
                
                # Don't retry on client errors (4xx)
                if 400 <= status_code < 500:
                    self._handle_request_error(endpoint, params, error_msg, status_code)
                    return {"error": error_msg, "status_code": status_code}
                
                # Retry on server errors (5xx)
                if attempt < self.max_retries - 1:
                    print(f"{error_msg}, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self._handle_request_error(endpoint, params, error_msg, status_code)
                    return {"error": error_msg, "status_code": status_code}
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed: {str(e)}"
                if attempt < self.max_retries - 1:
                    print(f"{error_msg}, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self._handle_request_error(endpoint, params, error_msg)
                    return {"error": error_msg}
                    
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self._handle_request_error(endpoint, params, error_msg)
                return {"error": error_msg}
        
        # Should not reach here, but just in case
        return {"error": "All retry attempts failed"}
    
    def _handle_request_error(self, endpoint: str, params: Dict, error: str, status_code: int = 0):
        """Handle and log request errors"""
        print(f"API Request Error - Endpoint: {endpoint}, Error: {error}")
        
        # Log failed request
        self.log_api_request(
            endpoint=endpoint,
            params=params,
            response_size=0,
            status_code=status_code,
            error_message=error,
            success=False
        )
        
        # Still record request for rate limiting (failed requests count too)
        self.rate_limiter.record_request(endpoint, success=False)
    
    def log_api_request(self, endpoint: str, params: Dict, response_size: int, 
                       status_code: int, error_message: str = None, success: bool = True):
        """Log API request to database for monitoring"""
        try:
            self.db.client.table("api_request_log").insert({
                "endpoint": endpoint,
                "params": params,
                "response_size": response_size,
                "status_code": status_code,
                "error_message": error_message,
                "request_timestamp": datetime.now().isoformat()
            }).execute()
        except Exception as e:
            print(f"Failed to log API request: {e}")
    
    def get_cached_data(self, table_name: str, filters: Dict[str, Any], 
                       max_age_hours: int = 24) -> Optional[List[Dict]]:
        """
        Get cached data from database if it's fresh enough
        
        Args:
            table_name: Database table to query
            filters: Filters to apply (e.g., {'league_id': 39, 'season': 2024})
            max_age_hours: Maximum age of data in hours
            
        Returns:
            List of records if fresh data exists, None otherwise
        """
        try:
            # Build query
            query = self.db.client.table(table_name).select("*")
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            # Check data age
            cutoff_time = datetime.now().replace(microsecond=0) - \
                         datetime.timedelta(hours=max_age_hours)
            
            query = query.gte("updated_at", cutoff_time.isoformat())
            
            result = query.execute()
            
            if result.data:
                print(f"Using cached data from {table_name} ({len(result.data)} records)")
                return result.data
            else:
                print(f"No fresh cached data in {table_name}")
                return None
                
        except Exception as e:
            print(f"Error getting cached data from {table_name}: {e}")
            return None
    
    def store_data(self, table_name: str, data: List[Dict[str, Any]], 
                  unique_keys: List[str] = None) -> bool:
        """
        Store data in database with upsert functionality
        
        Args:
            table_name: Target table name
            data: List of records to store
            unique_keys: Keys to use for upsert conflict resolution
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not data:
                print(f"No data to store in {table_name}")
                return True
            
            # Add timestamps
            now = datetime.now().isoformat()
            for record in data:
                if 'created_at' not in record:
                    record['created_at'] = now
                record['updated_at'] = now
            
            # Use upsert if unique keys provided
            if unique_keys:
                result = self.db.client.table(table_name).upsert(
                    data, 
                    on_conflict=','.join(unique_keys)
                ).execute()
            else:
                result = self.db.client.table(table_name).insert(data).execute()
            
            print(f"Successfully stored {len(data)} records in {table_name}")
            return True
            
        except Exception as e:
            print(f"Error storing data in {table_name}: {e}")
            return False
    
    def get_premier_league_teams(self) -> List[Dict[str, Any]]:
        """Get list of Premier League teams from cache or API"""
        # Try cache first
        cached_teams = self.get_cached_data(
            "teams", 
            {"league_id": self.premier_league_id}, 
            max_age_hours=168  # 1 week
        )
        
        if cached_teams:
            return cached_teams
        
        # Fetch from API
        print("Fetching Premier League teams from API...")
        response = self.make_api_request(
            "teams",
            {"league": self.premier_league_id, "season": self.current_season},
            priority="low"
        )
        
        if "error" in response:
            print(f"Error fetching teams: {response['error']}")
            return []
        
        # Process and store teams
        teams = []
        for team_data in response.get("response", []):
            team = team_data.get("team", {})
            venue = team_data.get("venue", {})
            
            teams.append({
                "id": team.get("id"),
                "name": team.get("name"),
                "code": team.get("code"),
                "country": team.get("country"),
                "founded": team.get("founded"),
                "logo": team.get("logo"),
                "venue_id": venue.get("id"),
                "venue_name": venue.get("name"),
                "venue_capacity": venue.get("capacity")
            })
        
        # Store in database
        if teams:
            self.store_data("teams", teams, unique_keys=["id"])
        
        return teams
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary for monitoring"""
        return self.rate_limiter.get_usage_stats()
    
    def is_data_fresh(self, table_name: str, filters: Dict[str, Any], 
                     max_age_hours: int) -> bool:
        """Check if cached data is fresh enough"""
        try:
            query = self.db.client.table(table_name).select("updated_at")
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.order("updated_at", desc=True).limit(1).execute()
            
            if not result.data:
                return False
            
            last_update = datetime.fromisoformat(result.data[0]["updated_at"].replace('Z', '+00:00'))
            cutoff = datetime.now().replace(tzinfo=last_update.tzinfo) - \
                    timedelta(hours=max_age_hours)
            
            return last_update > cutoff
            
        except Exception as e:
            print(f"Error checking data freshness: {e}")
            return False
    
    def extract_gameweek_from_round(self, round_str: str) -> Optional[int]:
        """
        Extract gameweek number from API Football round string
        
        Examples:
        - "Regular Season - 15" -> 15
        - "1st Round" -> 1
        - "Quarter-finals" -> None (cup competition)
        """
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
    
    def get_fixtures_by_gameweek(self, league_id: int, season: int, gameweek: int) -> List[Dict[str, Any]]:
        """
        Get fixtures for a specific gameweek and competition
        This is a COMMON USE CASE as you mentioned!
        """
        try:
            # Try cache first
            cached_fixtures = self.get_cached_data(
                "fixtures",
                {
                    "league_id": league_id,
                    "season": season,
                    "gameweek": gameweek
                },
                max_age_hours=6  # Refresh every 6 hours
            )
            
            if cached_fixtures:
                print(f"Using cached fixtures for gameweek {gameweek}")
                return cached_fixtures
            
            # Fetch from API if not cached
            print(f"Fetching gameweek {gameweek} fixtures from API...")
            
            # Get all fixtures for the season
            response = self.make_api_request(
                "fixtures",
                {
                    "league": league_id,
                    "season": season
                },
                priority="high"
            )
            
            if "error" in response:
                print(f"❌ Error fetching fixtures: {response['error']}")
                return []
            
            # Process and filter fixtures for this gameweek
            gameweek_fixtures = []
            all_fixtures = []
            
            for fixture_data in response.get("response", []):
                fixture = fixture_data.get("fixture", {})
                league = fixture_data.get("league", {})
                teams = fixture_data.get("teams", {})
                goals = fixture_data.get("goals", {})
                
                # Extract gameweek from round
                round_str = league.get("round", "")
                extracted_gameweek = self.extract_gameweek_from_round(round_str)
                
                fixture_record = {
                    "id": fixture.get("id"),
                    "referee": fixture.get("referee"),
                    "timezone": fixture.get("timezone"),
                    "date": fixture.get("date"),
                    "timestamp": fixture.get("timestamp"),
                    "league_id": league.get("id"),
                    "season": league.get("season"),
                    "round": round_str,
                    "gameweek": extracted_gameweek,
                    "home_team_id": teams.get("home", {}).get("id"),
                    "away_team_id": teams.get("away", {}).get("id"),
                    "home_score": goals.get("home"),
                    "away_score": goals.get("away"),
                    "status_long": fixture.get("status", {}).get("long"),
                    "status_short": fixture.get("status", {}).get("short"),
                    "status_elapsed": fixture.get("status", {}).get("elapsed"),
                    "venue_id": fixture.get("venue", {}).get("id"),
                    "venue_name": fixture.get("venue", {}).get("name"),
                    "venue_city": fixture.get("venue", {}).get("city")
                }
                
                all_fixtures.append(fixture_record)
                
                # Filter for requested gameweek
                if extracted_gameweek == gameweek:
                    gameweek_fixtures.append(fixture_record)
            
            # Store all fixtures in database
            if all_fixtures:
                self.store_data("fixtures", all_fixtures, unique_keys=["id"])
                print(f"✅ Stored {len(all_fixtures)} fixtures in database")
            
            print(f"✅ Found {len(gameweek_fixtures)} fixtures for gameweek {gameweek}")
            return gameweek_fixtures
            
        except Exception as e:
            print(f"❌ Error getting fixtures for gameweek {gameweek}: {e}")
            return []
    
    def get_current_gameweek_fixtures(self, league_id: int = None, season: int = None) -> List[Dict[str, Any]]:
        """Get fixtures for the current gameweek - another common use case"""
        league_id = league_id or self.premier_league_id
        season = season or self.current_season
        
        # This would use the gameweek calculator we'll implement next
        # For now, let's assume we can determine current gameweek
        try:
            # Get current gameweek from database or calculate it
            current_gw_result = self.db.client.table("premier_league_gameweeks").select("gameweek").eq("season", season).eq("is_current", True).limit(1).execute()
            
            if current_gw_result.data:
                current_gameweek = current_gw_result.data[0]["gameweek"]
                return self.get_fixtures_by_gameweek(league_id, season, current_gameweek)
            else:
                print("⚠️ Current gameweek not found in database")
                return []
                
        except Exception as e:
            print(f"❌ Error getting current gameweek fixtures: {e}")
            return []
