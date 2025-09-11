#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase_config import SupabaseService
from ai_service import AIService

# Load environment variables
load_dotenv()

def test_opportunity_search():
    """Test the AI opportunity search functionality"""
    
    # Initialize services
    supabase_service = SupabaseService()
    
    try:
        ai_service = AIService(api_key=os.getenv("GEMINI_API_KEY"))
        print("AI Service initialized successfully")
    except Exception as e:
        print(f"AI Service failed to initialize: {e}")
        return
    
    # Test query for opportunities
    query = "Show me internship opportunities"
    print(f"\nTesting query: '{query}'")
    
    # Test database search
    print("\n--- Testing database search ---")
    db_results = ai_service.search_database_for_context(query, supabase_service)
    print(f"Database results: Found {len(db_results['opportunities'])} opportunities")
    
    for opp in db_results['opportunities']:
        print(f"- {opp.get('title', 'Unknown')} at {opp.get('profiles', {}).get('name', 'Unknown org')}")
    
    # Test AI response generation
    print("\n--- Testing AI response generation ---")
    try:
        ai_response = ai_service.generate_response_with_context(query, db_results, [])
        print(f"AI Response: {ai_response}")
    except Exception as e:
        print(f"AI response generation failed: {e}")

if __name__ == "__main__":
    test_opportunity_search()