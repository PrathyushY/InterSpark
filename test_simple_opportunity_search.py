#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase_config import SupabaseService
from ai_service import AIService

# Load environment variables
load_dotenv()

def test_simple_opportunity_search():
    """Test simple opportunity name search"""
    
    # Initialize services
    supabase_service = SupabaseService()
    
    try:
        ai_service = AIService(api_key=os.getenv("GEMINI_API_KEY"))
        print("AI Service initialized successfully")
    except Exception as e:
        print(f"AI Service failed to initialize: {e}")
        return
    
    # Test simple opportunity name search
    query = "Backend Developer"
    print(f"Query: '{query}'")
    
    db_results = ai_service.search_database_for_context(query, supabase_service)
    print(f"Found {len(db_results['opportunities'])} opportunities:")
    for opp in db_results['opportunities']:
        print(f"- {opp.get('title', 'Unknown')}")

if __name__ == "__main__":
    test_simple_opportunity_search()