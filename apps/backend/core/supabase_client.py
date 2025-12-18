"""
Supabase client configuration
"""
from supabase import create_client
from core.config import settings
import os

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Initialize Supabase client
if SUPABASE_URL and SUPABASE_KEY:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase_client = None
    print("⚠️ Warning: Supabase credentials not configured")


def get_supabase_client():
    """Get Supabase client instance"""
    if not supabase_client:
        raise ValueError("Supabase not configured. Check SUPABASE_URL and SUPABASE_KEY")
    return supabase_client


class SupabaseAuth:
    """Supabase authentication helper"""
    
    @staticmethod
    def get_user(token: str):
        """Get user from JWT token"""
        try:
            user = supabase_client.auth.get_user(token)
            return user
        except Exception as e:
            print(f"Auth error: {e}")
            return None
    
    @staticmethod
    def sign_up(email: str, password: str):
        """Sign up new user"""
        try:
            response = supabase_client.auth.sign_up(
                {"email": email, "password": password}
            )
            return response
        except Exception as e:
            print(f"Sign up error: {e}")
            return None
    
    @staticmethod
    def sign_in(email: str, password: str):
        """Sign in user"""
        try:
            response = supabase_client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            return response
        except Exception as e:
            print(f"Sign in error: {e}")
            return None


class SupabaseDB:
    """Supabase database helper"""
    
    @staticmethod
    def query(table: str):
        """Query a table"""
        return supabase_client.table(table).select("*")
    
    @staticmethod
    def insert(table: str, data: dict):
        """Insert data"""
        return supabase_client.table(table).insert(data).execute()
    
    @staticmethod
    def update(table: str, data: dict, match: dict):
        """Update data"""
        query = supabase_client.table(table)
        for key, value in match.items():
            query = query.eq(key, value)
        return query.update(data).execute()
    
    @staticmethod
    def delete(table: str, match: dict):
        """Delete data"""
        query = supabase_client.table(table)
        for key, value in match.items():
            query = query.eq(key, value)
        return query.delete().execute()
