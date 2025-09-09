#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from ai_service import AIService

# Load environment variables
load_dotenv()

def test_skill_extraction():
    """Test the AI skill extraction functionality"""
    
    try:
        ai_service = AIService(api_key=os.getenv("GEMINI_API_KEY"))
        print("AI Service initialized successfully")
    except Exception as e:
        print(f"AI Service failed to initialize: {e}")
        return
    
    # Test queries
    queries = [
        "Help me find students with Python skills",
        "Looking for Python developers",
        "I need someone who knows Python",
        "Find students with Python experience",
        "Python programming students"
    ]
    
    for query in queries:
        print(f"\nTesting query: '{query}'")
        
        # Test skill extraction
        skills = ai_service.extract_skills_from_query(query)
        print(f"Extracted skills: {skills}")
        
        # Test enhanced query
        enhanced = ai_service.enhance_search_query(query)
        print(f"Enhanced query: {enhanced}")

if __name__ == "__main__":
    test_skill_extraction()