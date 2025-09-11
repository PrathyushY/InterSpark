#!/usr/bin/env python3

from supabase_config import SupabaseService

def check_opportunities():
    """Check what opportunities exist in the database"""
    
    supabase_service = SupabaseService()
    
    # Get all opportunities
    try:
        opportunities = supabase_service.get_opportunities()
        print(f"Found {len(opportunities)} total opportunities:")
        
        for opp in opportunities:
            print(f"- {opp.get('title', 'Unknown')} ({opp.get('status', 'Unknown status')})")
            print(f"  Type: {opp.get('type', 'Unknown')}")
            print(f"  ID: {opp.get('id', 'Unknown')}")
            print()
            
    except Exception as e:
        print(f"Error getting opportunities: {e}")

if __name__ == "__main__":
    check_opportunities()