#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase_config import SupabaseService
from ai_service import AIService

# Load environment variables
load_dotenv()

def test_name_searches():
    """Test searching by opportunity names and profile names"""
    
    # Initialize services
    supabase_service = SupabaseService()
    
    try:
        ai_service = AIService(api_key=os.getenv("GEMINI_API_KEY"))
        print("AI Service initialized successfully")
    except Exception as e:
        print(f"AI Service failed to initialize: {e}")
        return
    
    # Test opportunity name search
    print("\n=== Testing Opportunity Name Search ===")
    query = "Show me Backend Developer opportunities"
    print(f"Query: '{query}'")
    
    db_results = ai_service.search_database_for_context(query, supabase_service)
    print(f"Found {len(db_results['opportunities'])} opportunities:")
    for opp in db_results['opportunities']:
        print(f"- {opp.get('title', 'Unknown')}")
    
    # Test profile name search  
    print("\n=== Testing Profile Name Search ===")
    query = "Find Hridhay"
    print(f"Query: '{query}'")
    
    db_results = ai_service.search_database_for_context(query, supabase_service)
    print(f"Found {len(db_results['profiles'])} profiles:")
    for profile in db_results['profiles']:
        print(f"- {profile.get('name', 'Unknown')}")

if __name__ == "__main__":
    test_name_searches()