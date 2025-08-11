#!/usr/bin/env python3
"""
Startup script for Gamble Bot
Runs both the Telegram bot and the Flask web app
"""

import os
import sys
import asyncio
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_webapp():
    """Start the Flask web app in a separate thread"""
    try:
        from webapp.app import app
        port = int(os.getenv('FLASK_PORT', 12000))
        debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        print(f"🌐 Starting Flask Web App on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
    except Exception as e:
        print(f"❌ Error starting web app: {e}")

def start_bot():
    """Start the Telegram bot"""
    try:
        print("🤖 Starting Telegram Bot...")
        from main import main
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

def main():
    """Main startup function"""
    print("🎰 Starting Gamble Bot System...")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = ['BOT_TOKEN', 'MONGODB_URI', 'WEBAPP_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        sys.exit(1)
    
    # Start web app in a separate thread
    webapp_thread = threading.Thread(target=start_webapp, daemon=True)
    webapp_thread.start()
    
    # Give web app time to start
    time.sleep(2)
    
    # Start the bot (this will block)
    try:
        start_bot()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Gamble Bot System...")
        print("👋 Goodbye!")

if __name__ == '__main__':
    main()