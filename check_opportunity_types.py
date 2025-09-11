#!/usr/bin/env python3

from supabase_config import SupabaseService

def check_opportunity_types():
    """Check the exact type values in opportunities"""
    
    supabase_service = SupabaseService()
    
    try:
        # Get all opportunities with their exact type values
        result = supabase_service.client.table('opportunities').select('id, title, type').execute()
        opportunities = result.data
        
        print(f"Found {len(opportunities)} opportunities with types:")
        for opp in opportunities:
            print(f"- ID {opp['id']}: '{opp['title']}' -> Type: '{opp['type']}'")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_opportunity_types()