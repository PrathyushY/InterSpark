#!/usr/bin/env python3

import os
import time
from dotenv import load_dotenv
from ai_service import AIService

# Load environment variables
load_dotenv()

def test_name_extraction():
    """Test the AI name extraction functionality"""
    
    try:
        ai_service = AIService(api_key=os.getenv("GEMINI_API_KEY"))
        print("AI Service initialized successfully")
    except Exception as e:
        print(f"AI Service failed to initialize: {e}")
        return
    
    # Test queries with names
    queries = [
        "summarize Hridhay's profile for me",
        "Tell me about Prathyush",
        "Show me John's information"
    ]
    
    for query in queries:
        print(f"\nTesting query: '{query}'")
        
        # Test enhanced query
        enhanced = ai_service.enhance_search_query(query)
        print(f"Enhanced query: {enhanced}")
        
        # Wait to avoid rate limits
        time.sleep(2)

if __name__ == "__main__":
    test_name_extraction()