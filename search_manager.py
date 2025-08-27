"""
Management script for search index operations.
Run this script to initialize, rebuild, or manage the search index.
"""

import sys
import os

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search_service import search_service
from supabase_config import supabase_service


def initialize_search_index():
    """Initialize the search index with existing student profiles."""
    print("Initializing search index...")

    try:
        # Get all student profiles from Supabase
        print("Fetching student profiles from database...")
        profiles = supabase_service.search_students()  # Gets all students

        if not profiles:
            print("No student profiles found in database.")
            return

        print(f"Found {len(profiles)} student profiles. Building search index...")

        # Rebuild the search index
        success = search_service.rebuild_index(profiles)

        if success:
            print(
                f"✅ Successfully initialized search index with {len(profiles)} student profiles."
            )

            # Show some statistics
            stats = search_service.get_index_stats()
            print("\nIndex Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        else:
            print("❌ Failed to initialize search index.")

    except Exception as e:
        print(f"❌ Error initializing search index: {e}")


def rebuild_search_index():
    """Rebuild the search index from scratch."""
    print("Rebuilding search index from scratch...")
    initialize_search_index()


def add_sample_profile():
    """Add a sample student profile for testing."""
    sample_profile = {
        "id": "test-student-001",
        "name": "Alex Johnson",
        "email": "alex@example.com",
        "user_type": "student",
        "bio": "Passionate computer science student interested in web development and artificial intelligence. Love building innovative solutions to real-world problems.",
        "skills": "Python, JavaScript, React, Node.js, HTML, CSS, Machine Learning, SQL",
        "school": "Tech High School",
        "grade": "12th",
        "location": "San Francisco, CA",
        "interests": "Programming, AI, Web Development, Mobile Apps, Open Source",
        "github_url": "https://github.com/alexj",
        "linkedin_url": "https://linkedin.com/in/alex-johnson",
        "portfolio_url": "https://alexjohnson.dev",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    success = search_service.index_student_profile(sample_profile)
    if success:
        print("✅ Added sample profile to search index")
    else:
        print("❌ Failed to add sample profile")


def test_search():
    """Test the search functionality."""
    print("\n🔍 Testing search functionality...")

    test_queries = [
        ("python", "", "", ""),
        ("", "JavaScript", "", ""),
        ("", "", "Tech High", ""),
        ("", "", "", "12th"),
        ("web development", "React", "Tech", ""),
    ]

    for i, (query, skills, school, grade) in enumerate(test_queries, 1):
        print(
            f"\nTest {i}: query='{query}', skills='{skills}', school='{school}', grade='{grade}'"
        )
        results = search_service.search_students(query, skills, school, grade)
        print(f"  Found {len(results)} results")

        for result in results[:2]:  # Show first 2 results
            print(
                f"    - {result['name']} ({result['school']}) - Score: {result.get('search_score', 'N/A'):.2f}"
            )


def remove_test_profile():
    """Remove the test profile from the search index."""
    success = search_service.remove_from_index("test-student-001")
    if success:
        print("✅ Removed test profile from search index")
    else:
        print("❌ Failed to remove test profile")


def show_index_stats():
    """Show search index statistics."""
    print("\n📊 Search Index Statistics:")
    stats = search_service.get_index_stats()

    if stats:
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("  No statistics available (index may not exist)")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python search_manager.py [command]")
        print("\nCommands:")
        print("  init       - Initialize search index with existing profiles")
        print("  rebuild    - Rebuild search index from scratch")
        print("  stats      - Show index statistics")
        print("  test       - Test search functionality")
        print("  sample     - Add sample profile for testing")
        print("  remove     - Remove test profile from index")
        return

    command = sys.argv[1].lower()

    if command == "init":
        initialize_search_index()
    elif command == "rebuild":
        rebuild_search_index()
    elif command == "stats":
        show_index_stats()
    elif command == "test":
        test_search()
    elif command == "sample":
        add_sample_profile()
    elif command == "remove":
        remove_test_profile()
    else:
        print(f"Unknown command: {command}")
        print(
            "Use 'python search_manager.py' with no arguments to see available commands."
        )


if __name__ == "__main__":
    main()
