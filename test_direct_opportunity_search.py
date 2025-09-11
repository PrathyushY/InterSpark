#!/usr/bin/env python3

from supabase_config import SupabaseService

def test_direct_opportunity_search():
    """Test direct opportunity search"""
    
    supabase_service = SupabaseService()
    
    print("Testing direct opportunity search...")
    
    # Test the search_opportunities method directly
    results = supabase_service.search_opportunities(
        search_query="",
        opportunity_type="Internship",
        category="",
        location="",
        skills_needed=""
    )
    
    print(f"Found {len(results)} internship opportunities:")
    for opp in results:
        print(f"- {opp.get('title', 'Unknown')} (Status: {opp.get('status', 'Unknown')})")
        print(f"  Type: {opp.get('type', 'Unknown')}")
        print(f"  ID: {opp.get('id', 'Unknown')}")
        print()

if __name__ == "__main__":
    test_direct_opportunity_search()