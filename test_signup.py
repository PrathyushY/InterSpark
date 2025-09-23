#!/usr/bin/env python3
"""
Test script to debug Supabase email confirmation issues.
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv()

from supabase_config import SupabaseService


def test_supabase_signup():
    """Test Supabase user creation with email confirmation."""
    try:
        print("Initializing Supabase service...")
        service = SupabaseService()

        print(f"Base URL: {service._get_base_url()}")
        print(f"Supabase URL: {service.url}")

        # Test user data
        test_email = "test@example.com"  # Use a test email
        test_password = "testpassword123"
        test_user_data = {
            "name": "Test User",
            "user_type": "student",
            "school": "Test School",
            "grade": "12th Grade",
        }

        print(f"Attempting to create user with email: {test_email}")

        result = service.create_user(test_email, test_password, test_user_data)

        print("Result:")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        print(f"Error: {result.get('error')}")

        if result.get("user"):
            print(f"User ID: {result['user']['id']}")
            print(f"Email confirmed: {result['user']['email_confirmed']}")

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_supabase_signup()
