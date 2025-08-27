"""
Fallback search profiles data for when database is not accessible during build.
This ensures the app can still function in serverless environments.
"""

FALLBACK_PROFILES = {
    "last_updated": "2024-08-27T00:00:00Z",
    "profiles": [
        # This will be empty initially - profiles should be built from database
        # If database build fails, the app will still work but with no search results
    ],
}
