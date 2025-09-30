#!/usr/bin/env python3
"""
Debug script to test email confirmation with detailed logging
"""

import requests
import time


def test_confirmation_debug():
    """Test the confirmation with the actual token from the user's error"""
    print("🔍 Debug Testing Email Confirmation...")
    print("-" * 50)

    # The actual URL from the user's error
    test_url = "http://localhost:5001/auth/confirm?token=782077&type=signup&redirect_to=http%3a%2f%2flocalhost%3a5001%2fauth%2fconfirm"

    print(f"Testing URL: {test_url}")
    print()

    try:
        response = requests.get(test_url, allow_redirects=False, timeout=10)

        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")

        if response.status_code == 302:
            redirect_location = response.headers.get("Location", "No location header")
            print(f"\n🔄 Redirect Location: {redirect_location}")

            # Follow the redirect to see the final result
            if redirect_location and redirect_location.startswith("http"):
                print("\n🔄 Following redirect...")
                final_response = requests.get(redirect_location, timeout=10)
                print(f"📊 Final Status: {final_response.status_code}")

                # Look for flash messages or error indicators
                if "verification failed" in final_response.text.lower():
                    print("❌ Found 'verification failed' in response")
                elif "confirmed successfully" in final_response.text.lower():
                    print("✅ Found 'confirmed successfully' in response")
                else:
                    print("🤔 No clear success/failure message found")

        elif response.status_code == 200:
            print("\n📄 Response Content Preview:")
            content = response.text[:500]
            print(content)

        else:
            print(f"\n⚠️ Unexpected status: {response.status_code}")
            print("📄 Response:", response.text[:300])

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app on port 5001")
        print("💡 Make sure Flask is running with: python3 app.py")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_confirmation_debug()
