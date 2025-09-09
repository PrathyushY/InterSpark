#!/usr/bin/env python3
"""
Debug version of the chat route to test search functionality without AI service.
This helps isolate whether the issue is with the search or the AI service.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_search_functionality():
    """Debug the search functionality step by step."""
    print("🔍 Debugging Search Functionality")
    print("=" * 50)
    
    # Step 1: Test Supabase connection
    print("\n1. Testing Supabase connection...")
    try:
        from supabase_config import SupabaseService
        supabase_service = SupabaseService()
        print("   ✅ Supabase connection successful")
    except Exception as e:
        print(f"   ❌ Supabase connection failed: {e}")
        return
    
    # Step 2: Test basic student search
    print("\n2. Testing basic student search...")
    try:
        all_students = supabase_service.search_students(
            search_query="",
            skills="",
            school="",
            grade="",
            location=""
        )
        print(f"   ✅ Found {len(all_students)} total students in database")
        
        if all_students:
            # Show first student's skills
            first_student = all_students[0]
            name = first_student.get('name', 'Unknown')
            skills = first_student.get('skills', [])
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except:
                    skills = [skills] if skills else []
            print(f"   📝 Example student: {name} - Skills: {skills}")
        else:
            print("   ⚠️  No students found in database")
            
    except Exception as e:
        print(f"   ❌ Error in basic search: {e}")
        return
    
    # Step 3: Test Python skills search
    print("\n3. Testing Python skills search...")
    try:
        python_students = supabase_service.search_students_enhanced(
            search_query="python",
            skills="python",
            school="",
            grade="",
            location=""
        )
        print(f"   ✅ Enhanced search found {len(python_students)} students with Python skills")
        
        if python_students:
            for i, student in enumerate(python_students[:3]):
                name = student.get('name', 'Unknown')
                skills = student.get('skills', [])
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = [skills] if skills else []
                print(f"   📝 {i+1}. {name} - Skills: {skills}")
        else:
            print("   ⚠️  No students found with Python skills")
            
    except Exception as e:
        print(f"   ❌ Error in Python search: {e}")
    
    # Step 4: Test regular search for comparison
    print("\n4. Testing regular search for comparison...")
    try:
        regular_python_students = supabase_service.search_students(
            search_query="python",
            skills="python",
            school="",
            grade="",
            location=""
        )
        print(f"   ✅ Regular search found {len(regular_python_students)} students with Python skills")
        
    except Exception as e:
        print(f"   ❌ Error in regular search: {e}")
    
    # Step 5: Test AI service initialization
    print("\n5. Testing AI service initialization...")
    try:
        from ai_service import AIService
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            ai_service = AIService(api_key=api_key)
            print("   ✅ AI service initialized successfully")
            
            # Test the search_database_for_context method
            print("\n6. Testing AI service search method...")
            db_results = ai_service.search_database_for_context(
                "find students with python skills", 
                supabase_service
            )
            print(f"   ✅ AI service search found {db_results['total_matches']} total matches")
            print(f"   📝 Profiles: {len(db_results['profiles'])}, Opportunities: {len(db_results['opportunities'])}")
            
        else:
            print("   ⚠️  GEMINI_API_KEY not found in environment variables")
            print("   💡 AI service will be None, but search should still work")
            
    except Exception as e:
        print(f"   ❌ Error with AI service: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Debug Summary:")
    print("   - If Supabase connection works: ✅")
    print("   - If students are found: ✅") 
    print("   - If Python search works: ✅")
    print("   - If AI service works: ✅")
    print("\n💡 If any step fails, that's where the issue is!")

if __name__ == "__main__":
    debug_search_functionality()
