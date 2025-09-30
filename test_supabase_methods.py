#!/usr/bin/env python3
"""
Check available Supabase auth methods and test different approaches
"""

import sys
import os

sys.path.append("/Users/prathyet/Websites/InterSpark")

from supabase_config import SupabaseService
from dotenv import load_dotenv

load_dotenv()


def test_supabase_methods():
    """Test what auth methods are available in our Supabase client"""
    print("🔍 Checking Supabase Auth Methods...")
    print("-" * 50)

    try:
        supabase_service = SupabaseService()
        auth_client = supabase_service.client.auth

        print("Available auth methods:")
        methods = [method for method in dir(auth_client) if not method.startswith("_")]
        for method in sorted(methods):
            print(f"  - {method}")

        print("\n📝 Testing signup token verification approaches...")

        # Test token (this will fail but show us the error message)
        test_token = "782077"

        print(f"\n1. Testing verify_otp with signup type:")
        try:
            result = auth_client.verify_otp({"token": test_token, "type": "signup"})
            print(f"   ✅ Success: {result}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"   📋 Error type: {type(e)}")

        # Check if exchangeCodeForSession exists
        if hasattr(auth_client, "exchangeCodeForSession"):
            print(f"\n2. Testing exchangeCodeForSession:")
            try:
                result = auth_client.exchangeCodeForSession(test_token)
                print(f"   ✅ Success: {result}")
            except Exception as e:
                print(f"   ❌ Error: {e}")

        # Check if confirm exists
        if hasattr(auth_client, "confirm"):
            print(f"\n3. Testing confirm method:")
            try:
                result = auth_client.confirm(test_token, "signup")
                print(f"   ✅ Success: {result}")
            except Exception as e:
                print(f"   ❌ Error: {e}")

    except Exception as e:
        print(f"❌ Error initializing Supabase: {e}")


if __name__ == "__main__":
    test_supabase_methods()
