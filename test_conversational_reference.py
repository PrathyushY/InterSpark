#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase_config import SupabaseService
from ai_service import AIService

# Load environment variables
load_dotenv()

def test_conversational_reference():
    """Test conversational references with context"""
    
    # Initialize services
    supabase_service = SupabaseService()
    
    try:
        ai_service = AIService(api_key=os.getenv("GEMINI_API_KEY"))
        print("AI Service initialized successfully")
    except Exception as e:
        print(f"AI Service failed to initialize: {e}")
        return
    
    # First, search for Backend Developer to get context
    print("=== Step 1: Getting Backend Developer opportunity ===")
    db_results = ai_service.search_database_for_context("Backend Developer", supabase_service)
    print(f"Found {len(db_results['opportunities'])} opportunities")
    
    # Now test conversational reference with that context
    print("\n=== Step 2: Testing conversational reference ===")
    query = "summarize this opportunity for me"
    print(f"Query: '{query}'")
    
    try:
        ai_response = ai_service.generate_response_with_context(query, db_results, [])
        print(f"AI Response: {ai_response}")
    except Exception as e:
        print(f"AI response generation failed: {e}")

if __name__ == "__main__":
    test_conversational_reference()