#!/usr/bin/env python3
"""
Advanced Supabase email verification debugging script
"""

import sys
import os

sys.path.append("/Users/prathyet/Websites/InterSpark")

from supabase_config import SupabaseService
from dotenv import load_dotenv
import json

load_dotenv()


def debug_supabase_auth():
    """Debug Supabase auth configuration and test different verification approaches"""
    print("🔍 Advanced Supabase Auth Debugging...")
    print("-" * 60)

    try:
        supabase_service = SupabaseService()
        auth_client = supabase_service.client.auth

        # Test token (use a recent one from your logs)
        test_token = "151318"  # From your latest attempt

        print(f"🧪 Testing token: {test_token}")
        print(f"🔗 Supabase URL: {supabase_service.client.supabase_url}")
        print()

        # Test 1: Check current session
        print("1. 📋 Checking current session...")
        try:
            session = auth_client.get_session()
            print(f"   Current session: {session}")
        except Exception as e:
            print(f"   ❌ Session check failed: {e}")

        # Test 2: Try different verification methods
        verification_methods = [
            (
                "exchange_code_for_session",
                lambda: auth_client.exchange_code_for_session(test_token),
            ),
            (
                "verify_otp_signup",
                lambda: auth_client.verify_otp({"token": test_token, "type": "signup"}),
            ),
            (
                "verify_otp_email",
                lambda: auth_client.verify_otp({"token": test_token, "type": "email"}),
            ),
            (
                "verify_otp_token_hash",
                lambda: auth_client.verify_otp(
                    {"token_hash": test_token, "type": "signup"}
                ),
            ),
        ]

        for method_name, method_func in verification_methods:
            print(
                f"\n2.{verification_methods.index((method_name, method_func)) + 1} 🧪 Testing {method_name}..."
            )
            try:
                result = method_func()
                print(f"   ✅ Success!")
                print(f"   📋 Result type: {type(result)}")
                print(f"   📋 Result: {str(result)[:200]}...")

                # Try to extract user info
                if hasattr(result, "user") and result.user:
                    print(f"   👤 User ID: {result.user.id}")
                    print(f"   📧 User Email: {result.user.email}")
                elif hasattr(result, "session") and result.session:
                    print(f"   🔑 Session found")
                elif isinstance(result, dict) and "user" in result:
                    print(f"   👤 Dict User ID: {result['user']['id']}")

            except Exception as e:
                print(f"   ❌ Failed: {e}")
                print(f"   📋 Error type: {type(e)}")

        # Test 3: Check auth settings
        print(f"\n3. ⚙️ Auth Configuration Check...")
        print(f"   Supabase URL: {supabase_service.client.supabase_url}")
        print(f"   Has auth client: {auth_client is not None}")

        # Test 4: Try manual user lookup (if we have user management access)
        print(f"\n4. 👥 User Management Test...")
        try:
            # This might not work if we don't have admin access
            users_response = supabase_service.client.auth.admin.list_users()
            print(f"   ✅ Can access user management")
            print(f"   📊 Response: {str(users_response)[:200]}...")
        except Exception as e:
            print(f"   ⚠️ Cannot access user management: {e}")

    except Exception as e:
        print(f"❌ Failed to initialize Supabase: {e}")


def check_email_settings():
    """Check if email confirmation is properly configured in Supabase"""
    print(f"\n" + "=" * 60)
    print("📧 EMAIL CONFIGURATION CHECKLIST")
    print("=" * 60)

    checklist = [
        "✅ Supabase Auth → Settings → Email confirmation: ENABLED",
        "✅ Supabase Auth → Templates → Confirm signup: CONFIGURED",
        "✅ Email template uses correct redirect URL (http://localhost:5001)",
        "✅ SMTP provider configured (or using Supabase default)",
        "✅ Email domain is verified (if using custom SMTP)",
        "✅ No email rate limiting hitting your test emails",
    ]

    for item in checklist:
        print(f"   {item}")

    print("\n💡 Common Issues:")
    print("   🔸 Email confirmation disabled in Supabase dashboard")
    print("   🔸 Wrong redirect URL in email template")
    print("   🔸 SMTP not configured properly")
    print("   🔸 Email template has wrong URL format")
    print("   🔸 Rate limiting preventing email delivery")


if __name__ == "__main__":
    debug_supabase_auth()
    check_email_settings()
