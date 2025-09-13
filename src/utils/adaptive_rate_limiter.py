"""
Adaptive Rate Limiter with Request Mode Awareness
Manages API rate limiting with automatic mode adjustment
"""

from datetime import datetime, date
from typing import Dict, Any, Optional
from src.database.connection import SupabaseManager
from src.config.request_mode_manager import RequestModeManager


class AdaptiveRateLimiter:
    """Rate limiter that adapts based on current request mode and usage patterns"""
    
    def __init__(self):
        self.db = SupabaseManager()
        self.mode_manager = RequestModeManager()
        self.hard_limit = 1000  # Never exceed this
        self.emergency_threshold = 900   # Start emergency mode
        self.warning_threshold = 800     # Start warnings
        
    def can_make_request(self, endpoint: str, priority: str = 'medium') -> bool:
        """
        Check if request is allowed based on mode and current usage
        
        Args:
            endpoint: API endpoint being requested
            priority: Request priority ('critical', 'highest', 'high', 'medium', 'low')
            
        Returns:
            bool: True if request is allowed, False otherwise
        """
        try:
            # Get current usage and limits
            current_usage = self._get_current_usage()
            current_mode = self.mode_manager.get_current_mode()
            daily_budget = self.mode_manager.get_daily_budget()
            
            # Hard limit check - never exceed 1000
            if current_usage >= self.hard_limit:
                print(f"HARD LIMIT REACHED: {current_usage}/{self.hard_limit} requests used")
                return False
            
            # Emergency mode - only critical requests
            if current_usage >= self.emergency_threshold:
                allowed = priority in ['critical', 'highest']
                if not allowed:
                    print(f"EMERGENCY MODE: Only critical requests allowed ({current_usage}/{self.hard_limit})")
                return allowed
            
            # Mode-specific budget check
            if current_usage >= daily_budget:
                # Only allow high priority requests when over mode budget
                allowed = priority in ['highest', 'high']
                if not allowed:
                    print(f"MODE BUDGET EXCEEDED: {current_usage}/{daily_budget} for {current_mode} mode")
                return allowed
            
            # Check if endpoint is allowed in current mode
            if not self._is_endpoint_allowed_in_mode(endpoint, current_mode):
                print(f"ENDPOINT NOT ALLOWED: {endpoint} not permitted in {current_mode} mode")
                return False
            
            # Auto-adjust mode if needed
            if self.mode_manager.auto_adjust_enabled:
                self._check_and_adjust_mode(current_usage)
            
            return True
            
        except Exception as e:
            print(f"Error in rate limiter: {e}")
            # Fail safe - allow request but log error
            return True
    
    def record_request(self, endpoint: str = "", success: bool = True) -> bool:
        """
        Record that a request was made and increment counters
        
        Args:
            endpoint: The endpoint that was called
            success: Whether the request was successful
            
        Returns:
            bool: True if recorded successfully
        """
        try:
            today = date.today()
            
            # Get or create today's counter
            result = self.db.client.table("daily_request_counter").select("*").eq("date", today.isoformat()).execute()
            
            if result.data:
                # Update existing record
                current_count = result.data[0]["request_count"]
                new_count = current_count + 1
                
                self.db.client.table("daily_request_counter").update({
                    "request_count": new_count,
                    "last_reset": datetime.now().isoformat()
                }).eq("date", today.isoformat()).execute()
                
            else:
                # Create new record for today
                self.db.client.table("daily_request_counter").insert({
                    "date": today.isoformat(),
                    "request_count": 1,
                    "last_reset": datetime.now().isoformat()
                }).execute()
            
            return True
            
        except Exception as e:
            print(f"Error recording request: {e}")
            return False
    
    def _get_current_usage(self) -> int:
        """Get current daily usage from database"""
        try:
            today = date.today()
            result = self.db.client.table("daily_request_counter").select("request_count").eq("date", today.isoformat()).execute()
            
            if result.data:
                return result.data[0]["request_count"]
            return 0
            
        except Exception as e:
            print(f"Error getting current usage: {e}")
            return 0
    
    def _is_endpoint_allowed_in_mode(self, endpoint: str, mode: str) -> bool:
        """Check if endpoint is allowed in current mode"""
        try:
            mode_schedule = self.mode_manager.get_mode_schedule(mode)
            
            if not mode_schedule or 'schedules' not in mode_schedule:
                return True  # Default allow if no schedule found
            
            # Check if any schedule item matches the endpoint
            for schedule_item in mode_schedule['schedules'].values():
                endpoint_pattern = schedule_item.get('endpoint', '')
                
                # Simple pattern matching - could be enhanced
                if any(pattern in endpoint for pattern in [
                    '/teams', '/fixtures', '/standings', '/players', '/predictions', 
                    '/lineups', '/events', '/statistics'
                ]):
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error checking endpoint permissions: {e}")
            return True  # Default allow on error
    
    def _check_and_adjust_mode(self, current_usage: int):
        """Auto-adjust mode based on usage projection"""
        try:
            current_hour = datetime.now().hour
            
            if current_hour == 0:
                return  # Can't project at midnight
            
            # Calculate projected usage
            time_remaining = 24 - current_hour
            hourly_rate = current_usage / current_hour
            projected_daily = hourly_rate * 24
            
            # Determine appropriate mode based on projection
            current_mode = self.mode_manager.get_current_mode()
            new_mode = None
            
            if projected_daily > 6500:
                new_mode = 'minimal'
                reason = f"Auto-downgrade: projected {projected_daily:.0f} requests (>6500)"
            elif projected_daily > 5000 and current_mode in ['maximum', 'high']:
                new_mode = 'low'
                reason = f"Auto-downgrade: projected {projected_daily:.0f} requests (>5000)"
            elif projected_daily > 3500 and current_mode == 'maximum':
                new_mode = 'standard'
                reason = f"Auto-downgrade: projected {projected_daily:.0f} requests (>3500)"
            elif projected_daily < 1000 and current_mode == 'minimal':
                new_mode = 'low'
                reason = f"Auto-upgrade: projected {projected_daily:.0f} requests (<1000)"
            elif projected_daily < 2000 and current_mode in ['minimal', 'low']:
                new_mode = 'standard'
                reason = f"Auto-upgrade: projected {projected_daily:.0f} requests (<2000)"
            
            if new_mode and new_mode != current_mode:
                print(f"AUTO-ADJUSTING MODE: {current_mode} -> {new_mode}")
                self.mode_manager.switch_mode(new_mode, reason)
                
        except Exception as e:
            print(f"Error in auto-adjustment: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics and projections"""
        try:
            current_usage = self._get_current_usage()
            current_mode = self.mode_manager.get_current_mode()
            daily_budget = self.mode_manager.get_daily_budget()
            
            current_hour = datetime.now().hour
            hourly_rate = current_usage / current_hour if current_hour > 0 else 0
            projected_daily = hourly_rate * 24
            
            return {
                "current_usage": current_usage,
                "daily_budget": daily_budget,
                "hard_limit": self.hard_limit,
                "remaining_requests": self.hard_limit - current_usage,
                "mode_budget_remaining": max(0, daily_budget - current_usage),
                "current_mode": current_mode,
                "usage_percentage": (current_usage / self.hard_limit) * 100,
                "mode_usage_percentage": (current_usage / daily_budget) * 100 if daily_budget > 0 else 0,
                "hourly_rate": round(hourly_rate, 2),
                "projected_daily": round(projected_daily),
                "will_exceed_limit": projected_daily > self.hard_limit,
                "status": self._get_usage_status(current_usage, projected_daily)
            }
            
        except Exception as e:
            return {"error": f"Failed to get usage stats: {e}"}
    
    def _get_usage_status(self, current_usage: int, projected_daily: float) -> str:
        """Get human-readable status of current usage"""
        if current_usage >= self.hard_limit:
            return "CRITICAL - Hard limit reached"
        elif current_usage >= self.emergency_threshold:
            return "EMERGENCY - Emergency mode active"
        elif projected_daily > self.hard_limit:
            return "DANGER - Will exceed daily limit"
        elif current_usage >= self.warning_threshold:
            return "WARNING - Approaching limits"
        elif projected_daily > 6000:
            return "CAUTION - High usage projected"
        else:
            return "NORMAL - Usage within safe limits"
    
    def reset_daily_counter(self) -> bool:
        """Reset the daily counter (for testing or manual reset)"""
        try:
            today = date.today()
            
            # Reset or create today's counter
            result = self.db.client.table("daily_request_counter").select("id").eq("date", today.isoformat()).execute()
            
            if result.data:
                # Update existing
                self.db.client.table("daily_request_counter").update({
                    "request_count": 0,
                    "last_reset": datetime.now().isoformat()
                }).eq("date", today.isoformat()).execute()
            else:
                # Create new
                self.db.client.table("daily_request_counter").insert({
                    "date": today.isoformat(),
                    "request_count": 0,
                    "last_reset": datetime.now().isoformat()
                }).execute()
            
            print("Daily request counter reset successfully")
            return True
            
        except Exception as e:
            print(f"Error resetting daily counter: {e}")
            return False
