#!/usr/bin/env python3
"""
Quick test script to verify email confirmation is working on port 5001
"""

import requests
import time


def test_confirmation():
    """Test the email confirmation endpoint"""
    print("🔄 Testing email confirmation endpoint...")

    # Wait a moment for Flask to be ready
    time.sleep(2)

    try:
        # Test the endpoint
        url = "http://localhost:5001/auth/confirm?token=782077&type=signup"
        response = requests.get(url, timeout=10)

        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("✅ Route is accessible!")
            print("📄 Response content preview:")
            print(response.text[:500])
        elif response.status_code == 302:
            print(f"🔄 Redirect to: {response.headers.get('Location')}")
            print("✅ This is expected for confirmation flow")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print("📄 Response:", response.text[:300])

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app on port 5001")
        print("💡 Make sure Flask is running: python3 app.py")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_confirmation()
