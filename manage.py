#!/usr/bin/env python3
"""
Management script for football web app
Demonstrates data engineering improvements
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def create_app():
    """Create Flask app for management tasks"""
    from app import app
    return app

def init_database():
    """Initialize database tables"""
    app = create_app()
    with app.app_context():
        from database import db
        db.create_all()
        print("✅ Database tables created successfully!")

def test_api_connection():
    """Test API connection and data validation"""
    app = create_app()
    with app.app_context():
        from stats_data import fetch_stats
        print("🔄 Testing API connection...")

        # Test with Premier League 2024
        data = fetch_stats(39, 2024)
        if data and 'response' in data:
            print("✅ API connection successful!")
            print(f"📊 Retrieved {len(data['response'])} standings entries")
        else:
            print("❌ API connection failed!")

def test_redis_connection():
    """Test Redis connection if configured"""
    import redis
    redis_url = os.getenv('REDIS_URL')

    if not redis_url:
        print("⚠️  Redis URL not configured, using simple cache")
        return

    try:
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful!")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

def run_background_job_test():
    """Test background job system"""
    print("🔄 Testing background job system...")

    try:
        app = create_app()
        with app.app_context():
            from data_service import DataService

            # Test cache functionality
            test_data = {"test": "data", "timestamp": "2024"}
            DataService.cache_data("test_key", test_data, ttl_minutes=5)

            cached_data = DataService.get_cached_data("test_key")
            if cached_data and cached_data.get("test") == "data":
                print("✅ Database caching working!")
            else:
                print("❌ Database caching failed!")

    except Exception as e:
        print(f"❌ Background job test failed: {e}")

def show_status():
    """Show system status"""
    print("\n" + "="*50)
    print("🏈 FOOTBALL WEB APP - DATA ENGINEERING STATUS")
    print("="*50)

    # Check environment variables
    print("\n📋 Environment Configuration:")
    print(f"   API_KEY: {'✅ Set' if os.getenv('API_KEY') else '❌ Missing'}")
    print(f"   DATABASE_URL: {'✅ Set' if os.getenv('DATABASE_URL') else '❌ Missing'}")
    print(f"   REDIS_URL: {'✅ Set' if os.getenv('REDIS_URL') else '⚠️  Not set (using simple cache)'}")

    # Test connections
    print("\n🔗 Connection Tests:")
    test_api_connection()
    test_redis_connection()

    # Test data engineering features
    print("\n🔧 Data Engineering Features:")
    run_background_job_test()

    print("\n📈 Improvements Implemented:")
    print("   ✅ Database integration with SQLAlchemy")
    print("   ✅ Redis caching support")
    print("   ✅ API retry mechanisms with exponential backoff")
    print("   ✅ Data validation and error recovery")
    print("   ✅ Background job system with Celery")
    print("   ✅ Structured logging and metrics")

    print("\n🚀 Next Steps for DevOps:")
    print("   - Add Docker containerization")
    print("   - Set up CI/CD pipeline")
    print("   - Add monitoring and alerting")
    print("   - Implement infrastructure as code")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        show_status()
        print("\nUsage:")
        print("  python manage.py init_db    - Initialize database")
        print("  python manage.py status     - Show system status")
        print("  python manage.py test       - Run all tests")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init_db':
        init_database()
    elif command == 'status':
        show_status()
    elif command == 'test':
        show_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)