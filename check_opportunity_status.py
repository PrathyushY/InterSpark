#!/usr/bin/env python3

from supabase_config import SupabaseService

def check_opportunity_status():
    """Check the status values in opportunities"""
    
    supabase_service = SupabaseService()
    
    try:
        # Get all opportunities with their status values
        result = supabase_service.client.table('opportunities').select('id, title, status').execute()
        opportunities = result.data
        
        print(f"Found {len(opportunities)} opportunities with statuses:")
        for opp in opportunities:
            print(f"- ID {opp['id']}: '{opp['title']}' -> Status: '{opp['status']}'")
            
        # Count by status
        status_counts = {}
        for opp in opportunities:
            status = opp['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
        print(f"\nStatus breakdown:")
        for status, count in status_counts.items():
            print(f"- {status}: {count} opportunities")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_opportunity_status()