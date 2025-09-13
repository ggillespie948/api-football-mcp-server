"""
Request Mode Management System
Handles different request cadence modes and automatic adjustment
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from src.database.connection import SupabaseManager


class RequestMode(Enum):
    """Available request modes with different cadence levels"""
    MINIMAL = "minimal"        # ~500 requests/day - Basic data only
    LOW = "low"               # ~1,500 requests/day - Essential data
    STANDARD = "standard"     # ~3,000 requests/day - Full coverage
    HIGH = "high"             # ~5,000 requests/day - High frequency updates
    MAXIMUM = "maximum"       # ~7,000 requests/day - Real-time updates


class ScalableScheduleManager:
    """Manages different request cadence modes and their schedules"""
    
    PREMIER_LEAGUE_ID = 39
    
    def __init__(self, mode: RequestMode = RequestMode.STANDARD):
        self.mode = mode
        self.schedules = self._build_mode_schedules()
    
    def _build_mode_schedules(self) -> Dict[RequestMode, Dict[str, Any]]:
        """Build different schedule configurations for each mode"""
        
        return {
            RequestMode.MINIMAL: {
                'daily_budget': 100,
                'description': 'Basic fixtures and standings only',
                'schedules': {
                    'teams': {
                        'frequency': 'monthly',  # Once per month
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': 'teams'
                    },
                    'fixtures': {
                        'frequency': 'daily',  # Once per day
                        'priority': 'high',
                        'estimated_requests': 1,
                        'endpoint': '/fixtures?league=39&season=2024'
                    },
                    'standings': {
                        'frequency': 'daily',  # Once per day
                        'priority': 'medium',
                        'estimated_requests': 1,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'daily',  # Once per day
                        'priority': 'high',
                        'estimated_requests': 1,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    # NO lineups, goalscorers, probable_scorers, or live updates
                }
            },
            
            RequestMode.LOW: {
                'daily_budget': 300,
                'description': 'Essential data with basic match updates',
                'schedules': {
                    'teams': {
                        'frequency': 'weekly',
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': 'teams'
                    },
                    'fixtures': {
                        'frequency': 'twice_daily',  # Morning and evening
                        'priority': 'high',
                        'estimated_requests': 2,
                        'endpoint': 'fixtures'
                    },
                    'standings': {
                        'frequency': 'daily',
                        'priority': 'medium',
                        'estimated_requests': 1,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'every_6_hours',  # 4 times per day
                        'priority': 'high',
                        'estimated_requests': 4,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    'goalscorers': {
                        'frequency': 'post_match_only',  # After matches end
                        'priority': 'medium',
                        'estimated_requests': 20,  # 10 matches × 2 checks
                        'endpoint': '/fixtures/players?fixture={fixture_id}'
                    },
                    # NO lineups, probable_scorers, or live updates
                }
            },
            
            RequestMode.STANDARD: {
                'daily_budget': 600,
                'description': 'Full coverage with moderate update frequency',
                'schedules': {
                    'teams': {
                        'frequency': 'weekly',
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': 'teams'
                    },
                    'fixtures': {
                        'frequency': 'twice_daily',
                        'priority': 'high',
                        'estimated_requests': 2,
                        'endpoint': '/fixtures?league=39&season=2024'
                    },
                    'standings': {
                        'frequency': 'daily',
                        'priority': 'medium',
                        'estimated_requests': 1,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'every_3_hours',  # 8 times per day
                        'priority': 'high',
                        'estimated_requests': 8,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    'lineups': {
                        'frequency': 'match_day_limited',  # 2 hours before + 2 updates
                        'priority': 'high',
                        'estimated_requests': 60,  # 10 fixtures × 2 teams × 3 checks
                        'endpoint': '/fixtures/lineups?fixture={fixture_id}'
                    },
                    'goalscorers': {
                        'frequency': 'post_match',
                        'priority': 'high',
                        'estimated_requests': 50,  # 10 matches × 5 checks
                        'endpoint': '/fixtures/players?fixture={fixture_id}'
                    },
                    'probable_scorers': {
                        'frequency': 'pre_match_daily',  # Once per day before match
                        'priority': 'medium',
                        'estimated_requests': 20,  # 10 fixtures × 2 updates
                        'endpoint': '/predictions?fixture={fixture_id}'
                    },
                    # NO live updates
                }
            },
            
            RequestMode.HIGH: {
                'daily_budget': 800,
                'description': 'High frequency updates with live match tracking',
                'schedules': {
                    'teams': {
                        'frequency': 'weekly',
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': 'teams'
                    },
                    'fixtures': {
                        'frequency': 'three_times_daily',
                        'priority': 'high',
                        'estimated_requests': 3,
                        'endpoint': '/fixtures?league=39&season=2024'
                    },
                    'standings': {
                        'frequency': 'twice_daily',
                        'priority': 'medium',
                        'estimated_requests': 2,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'hourly',
                        'priority': 'high',
                        'estimated_requests': 24,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    'lineups': {
                        'frequency': 'match_day_frequent',  # Multiple updates
                        'priority': 'highest',
                        'estimated_requests': 120,  # 10 fixtures × 2 teams × 6 checks
                        'endpoint': '/fixtures/lineups?fixture={fixture_id}'
                    },
                    'goalscorers': {
                        'frequency': 'during_and_post_match',
                        'priority': 'high',
                        'estimated_requests': 80,  # 10 matches × 8 checks
                        'endpoint': '/fixtures/players?fixture={fixture_id}'
                    },
                    'probable_scorers': {
                        'frequency': 'pre_match_frequent',
                        'priority': 'medium',
                        'estimated_requests': 40,  # 10 fixtures × 4 updates
                        'endpoint': '/predictions?fixture={fixture_id}'
                    },
                    'live_fixtures': {
                        'frequency': 'every_5_minutes',  # During match windows
                        'priority': 'highest',
                        'estimated_requests': 500,  # Match days only
                        'active_hours': '12:00-22:00',
                        'endpoint': '/fixtures?live=all&league=39'
                    }
                }
            },
            
            RequestMode.MAXIMUM: {
                'daily_budget': 1000,  # Use full allocation
                'description': 'Maximum frequency with real-time updates',
                'schedules': {
                    'teams': {
                        'frequency': 'weekly',
                        'priority': 'low',
                        'estimated_requests': 1,
                        'endpoint': 'teams'
                    },
                    'fixtures': {
                        'frequency': 'four_times_daily',
                        'priority': 'high',
                        'estimated_requests': 4,
                        'endpoint': '/fixtures?league=39&season=2024'
                    },
                    'standings': {
                        'frequency': 'three_times_daily',
                        'priority': 'medium',
                        'estimated_requests': 3,
                        'endpoint': '/standings?league=39&season=2024'
                    },
                    'current_gameweek': {
                        'frequency': 'every_30_minutes',
                        'priority': 'high',
                        'estimated_requests': 48,
                        'endpoint': '/fixtures?league=39&season=2024&next=10'
                    },
                    'lineups': {
                        'frequency': 'match_day_maximum',
                        'priority': 'highest',
                        'estimated_requests': 200,  # 10 fixtures × 2 teams × 10 checks
                        'endpoint': '/fixtures/lineups?fixture={fixture_id}'
                    },
                    'goalscorers': {
                        'frequency': 'real_time',
                        'priority': 'highest',
                        'estimated_requests': 100,  # 10 matches × 10 checks
                        'endpoint': '/fixtures/players?fixture={fixture_id}'
                    },
                    'probable_scorers': {
                        'frequency': 'pre_match_maximum',
                        'priority': 'medium',
                        'estimated_requests': 60,  # 10 fixtures × 6 updates
                        'endpoint': '/predictions?fixture={fixture_id}'
                    },
                    'live_fixtures': {
                        'frequency': 'every_2_minutes',
                        'priority': 'highest',
                        'estimated_requests': 1000,
                        'active_hours': '12:00-22:00',
                        'endpoint': '/fixtures?live=all&league=39'
                    },
                    'live_events': {
                        'frequency': 'every_minute',  # Real-time events
                        'priority': 'highest',
                        'estimated_requests': 500,
                        'active_hours': '12:00-22:00',
                        'endpoint': '/fixtures/events?fixture={fixture_id}'
                    }
                }
            }
        }
    
    def get_current_schedule(self) -> Dict[str, Any]:
        """Get the schedule for current mode"""
        return self.schedules[self.mode]
    
    def switch_mode(self, new_mode: RequestMode) -> Dict[str, Any]:
        """Switch to a different request mode"""
        old_mode = self.mode
        self.mode = new_mode
        
        return {
            "previous_mode": old_mode.value,
            "new_mode": new_mode.value,
            "previous_budget": self.schedules[old_mode]['daily_budget'],
            "new_budget": self.schedules[new_mode]['daily_budget'],
            "description": self.schedules[new_mode]['description']
        }
    
    def get_mode_comparison(self) -> Dict[str, Any]:
        """Compare all available modes"""
        comparison = {}
        
        for mode in RequestMode:
            schedule = self.schedules[mode]
            comparison[mode.value] = {
                "daily_budget": schedule['daily_budget'],
                "description": schedule['description'],
                "endpoints_covered": len(schedule['schedules']),
                "live_updates": 'live_fixtures' in schedule['schedules']
            }
        
        return comparison


class RequestModeManager:
    """Manages request mode configuration in the database"""
    
    def __init__(self):
        self.db = SupabaseManager()
        self.schedule_manager = ScalableScheduleManager()
    
    def get_current_mode(self) -> str:
        """Get current request mode from database"""
        try:
            result = self.db.client.table("request_mode_config").select("current_mode").limit(1).execute()
            return result.data[0]["current_mode"] if result.data else "standard"
        except Exception as e:
            print(f"Error getting current mode: {e}")
            return "standard"
    
    def get_daily_budget(self) -> int:
        """Get daily budget for current mode"""
        try:
            result = self.db.client.table("request_mode_config").select("daily_budget").limit(1).execute()
            return result.data[0]["daily_budget"] if result.data else 3000
        except Exception as e:
            print(f"Error getting daily budget: {e}")
            return 3000
    
    def get_auto_adjust_enabled(self) -> bool:
        """Check if auto-adjust is enabled"""
        try:
            result = self.db.client.table("request_mode_config").select("auto_adjust_enabled").limit(1).execute()
            return result.data[0]["auto_adjust_enabled"] if result.data else True
        except Exception as e:
            print(f"Error getting auto-adjust setting: {e}")
            return True
    
    @property
    def auto_adjust_enabled(self) -> bool:
        return self.get_auto_adjust_enabled()
    
    def switch_mode(self, new_mode: str, reason: str = "Manual change") -> bool:
        """Switch to a new request mode"""
        try:
            # Validate mode
            if new_mode not in [mode.value for mode in RequestMode]:
                raise ValueError(f"Invalid mode: {new_mode}")
            
            # Get mode info
            mode_enum = RequestMode(new_mode)
            schedule_manager = ScalableScheduleManager(mode_enum)
            mode_info = schedule_manager.get_current_schedule()
            
            # Update database
            self.db.client.table("request_mode_config").update({
                "current_mode": new_mode,
                "daily_budget": mode_info['daily_budget'],
                "last_mode_change": datetime.now().isoformat(),
                "reason_for_change": reason,
                "updated_at": datetime.now().isoformat()
            }).eq("id", 1).execute()
            
            print(f"Successfully switched to {new_mode} mode")
            return True
            
        except Exception as e:
            print(f"Error switching mode: {e}")
            return False
    
    def get_mode_schedule(self, mode: str) -> Dict[str, Any]:
        """Get schedule configuration for a specific mode"""
        try:
            mode_enum = RequestMode(mode)
            schedule_manager = ScalableScheduleManager(mode_enum)
            return schedule_manager.get_current_schedule()
        except ValueError:
            return {}
    
    def enable_auto_adjust(self, enabled: bool = True) -> bool:
        """Enable or disable auto-adjustment"""
        try:
            self.db.client.table("request_mode_config").update({
                "auto_adjust_enabled": enabled,
                "updated_at": datetime.now().isoformat()
            }).eq("id", 1).execute()
            
            print(f"Auto-adjustment {'enabled' if enabled else 'disabled'}")
            return True
            
        except Exception as e:
            print(f"Error updating auto-adjust setting: {e}")
            return False
    
    def get_emergency_mode_schedule(self) -> Dict[str, Any]:
        """Get emergency minimal schedule when approaching limits"""
        return {
            'daily_budget': 100,
            'description': 'Emergency mode - critical requests only',
            'schedules': {
                'live_fixtures': {
                    'frequency': 'every_10_minutes',  # Only during active matches
                    'priority': 'critical',
                    'estimated_requests': 50,
                    'endpoint': '/fixtures?live=all&league=39'
                },
                'current_gameweek': {
                    'frequency': 'every_12_hours',
                    'priority': 'critical',
                    'estimated_requests': 2,
                    'endpoint': '/fixtures?league=39&season=2024&next=10'
                }
            }
        }
