#!/usr/bin/env python3
"""
InterSpark Flask Application Setup and Runner
This script sets up and runs the InterSpark Flask application.
"""

import os
import sys
from app import app

def setup_application():
    """Set up the Flask application."""
    print("🚀 Setting up InterSpark Flask Application...")
    print("✅ Application setup complete!")
    print("📝 Note: Database functionality has been removed - ready for Supabase integration!")

def run_application():
    """Run the Flask application."""
    print("\n" + "="*50)
    print("🌟 Welcome to InterSpark Flask Application!")
    print("="*50)
    print("\n📋 Application Information:")
    print("   • Name: InterSpark")
    print("   • Description: Connecting students with opportunities")
    print("   • Framework: Flask with Jinja2 templating")
    print("   • Database: Ready for Supabase integration")
    print("   • Styling: Tailwind CSS")
    
    print("\n� Status:")
    print("   • SQLAlchemy removed ✅")
    print("   • Dummy data removed ✅") 
    print("   • Routes simplified ✅")
    print("   • Ready for Supabase ✅")
    
    print("\n🚀 Starting server...")
    print("   • Local: http://localhost:5000")
    print("   • Press Ctrl+C to stop the server")
    print("   • Note: Authentication and data features are placeholders until Supabase is integrated")
    print("\n" + "="*50 + "\n")
    
    # Run the Flask app
    app.run(debug=True, port=5000)

if __name__ == "__main__":
    try:
        setup_application()
        run_application()
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for using InterSpark! Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
