#!/usr/bin/env python3
"""
Test script to verify the enhanced search functionality works correctly.
This tests the search without requiring the AI service to be initialized.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test if Supabase connection works."""
    try:
        from supabase_config import SupabaseService
        supabase_service = SupabaseService()
        print("✅ Supabase connection successful")
        return supabase_service
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return None

def test_enhanced_search(supabase_service):
    """Test the enhanced search functionality."""
    if not supabase_service:
        print("❌ Cannot test search - no Supabase connection")
        return
    
    print("\n🔍 Testing Enhanced Search Functionality")
    print("=" * 50)
    
    # Test 1: Search for Python skills
    print("\n1. Testing Python skills search:")
    try:
        results = supabase_service.search_students_enhanced(
            search_query="python",
            skills="python",
            school="",
            grade="",
            location=""
        )
        print(f"   Found {len(results)} students with Python skills")
        
        if results:
            for i, student in enumerate(results[:3]):  # Show first 3
                name = student.get('name', 'Unknown')
                skills = student.get('skills', [])
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = [skills] if skills else []
                print(f"   {i+1}. {name} - Skills: {skills[:5]}")
        else:
            print("   No students found with Python skills")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Search for any programming skills
    print("\n2. Testing general programming skills search:")
    try:
        results = supabase_service.search_students_enhanced(
            search_query="programming",
            skills="",
            school="",
            grade="",
            location=""
        )
        print(f"   Found {len(results)} students matching 'programming'")
        
        if results:
            for i, student in enumerate(results[:3]):  # Show first 3
                name = student.get('name', 'Unknown')
                bio = student.get('bio', '')[:100] + "..." if len(student.get('bio', '')) > 100 else student.get('bio', '')
                print(f"   {i+1}. {name} - Bio: {bio}")
        else:
            print("   No students found matching 'programming'")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Search with multiple skills
    print("\n3. Testing multiple skills search (Python, JavaScript):")
    try:
        results = supabase_service.search_students_enhanced(
            search_query="",
            skills="python,javascript",
            school="",
            grade="",
            location=""
        )
        print(f"   Found {len(results)} students with Python OR JavaScript skills")
        
        if results:
            for i, student in enumerate(results[:3]):  # Show first 3
                name = student.get('name', 'Unknown')
                skills = student.get('skills', [])
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = [skills] if skills else []
                print(f"   {i+1}. {name} - Skills: {skills[:5]}")
        else:
            print("   No students found with Python or JavaScript skills")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_regular_search(supabase_service):
    """Test the regular search for comparison."""
    if not supabase_service:
        return
    
    print("\n🔍 Testing Regular Search (for comparison)")
    print("=" * 50)
    
    try:
        results = supabase_service.search_students(
            search_query="python",
            skills="python",
            school="",
            grade="",
            location=""
        )
        print(f"Regular search found {len(results)} students with Python skills")
        
        if results:
            for i, student in enumerate(results[:3]):  # Show first 3
                name = student.get('name', 'Unknown')
                skills = student.get('skills', [])
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = [skills] if skills else []
                print(f"   {i+1}. {name} - Skills: {skills[:5]}")
        else:
            print("   No students found with Python skills")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    print("🧪 Testing Enhanced Search Functionality")
    print("=" * 60)
    
    # Test Supabase connection
    supabase_service = test_supabase_connection()
    
    if supabase_service:
        # Test enhanced search
        test_enhanced_search(supabase_service)
        
        # Test regular search for comparison
        test_regular_search(supabase_service)
        
        print("\n" + "=" * 60)
        print("✅ Search functionality test completed!")
        print("\nIf you see results above, the search is working.")
        print("If you see 0 results, check your database for student profiles with skills.")
    else:
        print("\n❌ Cannot proceed with tests - Supabase connection failed")
        print("Make sure your .env file has the correct SUPABASE_URL and SUPABASE_PUBLIC_KEY")

if __name__ == "__main__":
    main()
