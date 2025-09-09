#!/usr/bin/env python3

from supabase_config import SupabaseService

def test_direct_search():
    """Test direct database search with Python skills"""
    
    supabase_service = SupabaseService()
    
    print("Testing direct search with Python skills...")
    
    # Test the search_students_enhanced method directly
    results = supabase_service.search_students_enhanced(
        search_query="",
        skills="python",
        school="",
        grade="",
        location=""
    )
    
    print(f"Found {len(results)} students with Python skills:")
    for student in results:
        print(f"- {student.get('name', 'Unknown')} from {student.get('school', 'Unknown school')}")
        print(f"  Skills: {student.get('skills', [])}")
        print()

if __name__ == "__main__":
    test_direct_search()