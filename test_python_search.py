#!/usr/bin/env python3
"""
Simple test script to verify Python skills search is working.
Run this to debug the search functionality.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_python_search():
    """Test specifically for Python skills search."""
    print("Testing Python Skills Search")
    print("=" * 40)
    
    try:
        # Test Supabase connection
        from supabase_config import SupabaseService
        supabase_service = SupabaseService()
        print("Supabase connection successful")
        
        # Test 1: Get all students first
        print("\n1. Getting all students...")
        all_students = supabase_service.search_students(
            search_query="",
            skills="",
            school="",
            grade="",
            location=""
        )
        print(f"   Found {len(all_students)} total students")
        
        if all_students:
            # Show skills from first few students
            print("\n   Sample student skills:")
            for i, student in enumerate(all_students[:3]):
                name = student.get('name', 'Unknown')
                skills = student.get('skills', [])
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = [skills] if skills else []
                print(f"   {i+1}. {name}: {skills}")
        
        # Test 2: Search for Python specifically
        print("\n2. Searching for Python skills...")
        python_students = supabase_service.search_students_enhanced(
            search_query="",
            skills="python",
            school="",
            grade="",
            location=""
        )
        print(f"   Enhanced search found {len(python_students)} students with Python skills")
        
        if python_students:
            print("\n   Python students found:")
            for i, student in enumerate(python_students):
                name = student.get('name', 'Unknown')
                skills = student.get('skills', [])
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = [skills] if skills else []
                print(f"   {i+1}. {name}: {skills}")
        else:
            print("   No students found with Python skills")
            
            # Let's check if any students have skills at all
            print("\n   Checking if any students have skills...")
            students_with_skills = []
            for student in all_students:
                skills = student.get('skills', [])
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = [skills] if skills else []
                if skills:
                    students_with_skills.append(student)
            
            print(f"   Found {len(students_with_skills)} students with any skills")
            if students_with_skills:
                print("   Sample skills found:")
                for i, student in enumerate(students_with_skills[:3]):
                    name = student.get('name', 'Unknown')
                    skills = student.get('skills', [])
                    if isinstance(skills, str):
                        try:
                            skills = json.loads(skills)
                        except:
                            skills = [skills] if skills else []
                    print(f"   {i+1}. {name}: {skills}")
        
        # Test 3: Try regular search for comparison
        print("\n3. Testing regular search for comparison...")
        regular_python = supabase_service.search_students(
            search_query="python",
            skills="python",
            school="",
            grade="",
            location=""
        )
        print(f"   Regular search found {len(regular_python)} students with Python skills")
        
        # Test 4: Try case-insensitive search
        print("\n4. Testing case-insensitive search...")
        case_insensitive = supabase_service.search_students_enhanced(
            search_query="Python",
            skills="Python",
            school="",
            grade="",
            location=""
        )
        print(f"   Case-insensitive search found {len(case_insensitive)} students with Python skills")
        
        # Test 5: Try partial match
        print("\n5. Testing partial match...")
        partial_match = supabase_service.search_students_enhanced(
            search_query="py",
            skills="py",
            school="",
            grade="",
            location=""
        )
        print(f"   Partial match search found {len(partial_match)} students with 'py' skills")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_python_search()
