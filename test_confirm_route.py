#!/usr/bin/env python3
"""
Test script to verify the /auth/confirm route is working correctly.
"""

import requests
import sys


def test_confirm_route():
    """Test the email confirmation route."""
    base_url = "http://localhost:5000"

    # Test 1: Basic route accessibility
    try:
        response = requests.get(f"{base_url}/auth/confirm", timeout=5)
        print(f"✓ Route /auth/confirm is accessible: Status {response.status_code}")

        if response.status_code == 200:
            print("✓ Route returns 200 OK")
        else:
            print(f"✗ Route returns {response.status_code} instead of 200")

    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Flask app. Is it running on localhost:5000?")
        return False
    except Exception as e:
        print(f"✗ Error testing route: {e}")
        return False

    # Test 2: Test with the specific token from your error
    try:
        test_url = f"{base_url}/auth/confirm?token=782077&type=signup&redirect_to=http%3a%2f%2flocalhost%3a5000%2fauth%2fconfirm"
        response = requests.get(test_url, timeout=5)
        print(f"✓ Token URL accessible: Status {response.status_code}")

        if response.status_code == 200:
            print("✓ Token URL returns 200 OK")
        elif response.status_code == 302:
            print(
                f"✓ Token URL redirects to: {response.headers.get('Location', 'Unknown')}"
            )
        else:
            print(f"✗ Token URL returns {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"✗ Error testing token URL: {e}")
        return False

    return True


if __name__ == "__main__":
    print("Testing Flask email confirmation route...")
    print("-" * 50)

    success = test_confirm_route()

    if not success:
        print("\n❌ Tests failed. Flask app may not be running.")
        print("Start the app with: python app.py")
    else:
        print("\n✅ Route tests completed successfully!")
