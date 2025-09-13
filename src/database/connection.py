"""
Supabase Database Connection Manager
Handles connection to Supabase database with singleton pattern
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseManager:
    """Singleton class for managing Supabase database connections"""
    
    _instance: Optional['SupabaseManager'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self) -> Client:
        """Initialize the Supabase client with environment variables"""
        if self._client is not None:
            return self._client
            
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError(
                "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
            )
        
        try:
            self._client = create_client(url, key)
            print(f"Successfully connected to Supabase at {url[:50]}...")
            return self._client
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")
    
    @property
    def client(self) -> Client:
        """Get the Supabase client, initializing if necessary"""
        if self._client is None:
            self.initialize()
        return self._client
    
    def test_connection(self) -> bool:
        """Test the database connection by querying a simple table"""
        try:
            # Test connection by checking if we can query the request_mode_config table
            result = self.client.table("request_mode_config").select("id").limit(1).execute()
            return True
        except Exception as e:
            print(f"Database connection test failed: {str(e)}")
            return False
    
    def close(self):
        """Close the database connection (if needed)"""
        # Supabase client doesn't need explicit closing, but we can reset our instance
        self._client = None
        
    def get_connection_info(self) -> dict:
        """Get information about the current connection"""
        return {
            "connected": self._client is not None,
            "url": os.getenv("SUPABASE_URL", "Not set")[:50] + "..." if os.getenv("SUPABASE_URL") else "Not set",
            "has_anon_key": bool(os.getenv("SUPABASE_ANON_KEY"))
        }


# Convenience function to get the database client
def get_db_client() -> Client:
    """Get the Supabase database client"""
    manager = SupabaseManager()
    return manager.client


# Convenience function to test the connection
def test_db_connection() -> bool:
    """Test the database connection"""
    manager = SupabaseManager()
    return manager.test_connection()
