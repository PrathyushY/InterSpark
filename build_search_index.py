"""
Build script to generate search index for serverless deployment.
This script should be run during the build process to create the search_profiles.json file.
"""

import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def build_search_index():
    """Build the search index for serverless deployment."""
    try:
        # Import services
        from supabase_config import supabase_service
        from search_service_serverless import ServerlessSearchService

        print("🔍 Building search index for serverless deployment...")

        # Create search service instance
        search_service = ServerlessSearchService()

        # Build index from database
        success = search_service.build_index_from_db(supabase_service)

        if success:
            stats = search_service.get_stats()
            print(f"✅ Successfully built search index!")
            print(f"   - Total profiles: {stats['total_profiles']}")
            print(f"   - Output file: {stats['profiles_file']}")
            print(f"   - File exists: {stats['file_exists']}")

            # Verify the file was created
            if os.path.exists("search_profiles.json"):
                file_size = os.path.getsize("search_profiles.json")
                print(f"   - File size: {file_size} bytes")

                # Show a sample of the data
                with open("search_profiles.json", "r") as f:
                    data = json.load(f)
                    print(f"   - Last updated: {data.get('last_updated', 'Unknown')}")

                    if data.get("profiles"):
                        sample_profile = data["profiles"][0]
                        print(
                            f"   - Sample profile: {sample_profile.get('name', 'Unknown')} ({sample_profile.get('school', 'Unknown')})"
                        )

            return True

        else:
            print("❌ Failed to build search index")
            return False

    except Exception as e:
        print(f"❌ Error building search index: {e}")
        import traceback

        traceback.print_exc()
        return False


def verify_search_index():
    """Verify that the search index file is valid and contains data."""
    try:
        if not os.path.exists("search_profiles.json"):
            print("❌ Search profiles file not found")
            return False

        with open("search_profiles.json", "r") as f:
            data = json.load(f)

        profiles = data.get("profiles", [])
        if not profiles:
            print("❌ No profiles found in search index")
            return False

        print(f"✅ Search index verified: {len(profiles)} profiles")

        # Test search functionality
        from search_service_serverless import ServerlessSearchService

        search_service = ServerlessSearchService()

        # Test a simple search
        results = search_service.search_students("python", "", "", "", 5)
        print(f"✅ Test search for 'python': {len(results)} results")

        return True

    except Exception as e:
        print(f"❌ Error verifying search index: {e}")
        return False


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python build_search_index.py [build|verify]")
        print("\nCommands:")
        print("  build   - Build search index from database")
        print("  verify  - Verify existing search index")
        return

    command = sys.argv[1].lower()

    if command == "build":
        success = build_search_index()
        sys.exit(0 if success else 1)
    elif command == "verify":
        success = verify_search_index()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
