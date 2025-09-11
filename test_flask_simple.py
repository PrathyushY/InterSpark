#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase_config import SupabaseService
from ai_service import AIService

# Load environment variables
load_dotenv()

def test_flask_simple():
    """Test searching for Flask without the word 'skills'"""
    
    # Initialize services
    supabase_service = SupabaseService()
    
    try:
        ai_service = AIService(api_key=os.getenv("GEMINI_API_KEY"))
        print("AI Service initialized successfully")
    except Exception as e:
        print(f"AI Service failed to initialize: {e}")
        return
    
    # Test query for Flask without 'skills'
    query = "Show me Flask opportunities"
    print(f"\nTesting query: '{query}'")
    
    # Test database search
    print("\n--- Testing database search ---")
    db_results = ai_service.search_database_for_context(query, supabase_service)
    print(f"Database results: Found {len(db_results['opportunities'])} opportunities")
    
    for opp in db_results['opportunities']:
        print(f"- {opp.get('title', 'Unknown')} at {opp.get('profiles', {}).get('name', 'Unknown org')}")

if __name__ == "__main__":
    test_flask_simple()