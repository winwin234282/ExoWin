#!/usr/bin/env python3
"""
Test script to verify ExoWin 👑 bot functionality
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_database_setup():
    """Test database setup and functions"""
    print("🔧 Testing database setup...")
    
    try:
        from src.database import setup_database, get_system_stats, get_game_statistics
        
        # Test database setup
        setup_result = await setup_database()
        print(f"✅ Database setup: {'Success' if setup_result else 'Failed'}")
        
        # Test system stats
        stats = await get_system_stats()
        print(f"✅ System stats retrieved: {len(stats)} fields")
        
        # Test game statistics
        game_stats = await get_game_statistics()
        print(f"✅ Game statistics retrieved: {len(game_stats)} games")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_admin_functions():
    """Test admin panel functions"""
    print("👑 Testing admin functions...")
    
    try:
        from src.admin import is_admin
        from src.database import get_all_users, search_users
        
        # Test admin check (will be False for test)
        admin_check = await is_admin(12345)
        print(f"✅ Admin check function works: {admin_check}")
        
        # Test user retrieval
        users, count = await get_all_users(limit=10)
        print(f"✅ User retrieval: {count} total users, {len(users)} retrieved")
        
        # Test user search
        search_results, search_count = await search_users("test", limit=5)
        print(f"✅ User search: {search_count} results found")
        
        return True
    except Exception as e:
        print(f"❌ Admin functions test failed: {e}")
        return False

async def test_withdrawal_system():
    """Test withdrawal system"""
    print("💸 Testing withdrawal system...")
    
    try:
        from src.wallet.withdrawal_system import WithdrawalSystem
        
        # Create withdrawal system instance
        withdrawal_system = WithdrawalSystem()
        print("✅ Withdrawal system initialized")
        
        # Test supported cryptocurrencies
        supported_cryptos = withdrawal_system.get_supported_cryptocurrencies()
        print(f"✅ Supported cryptocurrencies: {len(supported_cryptos)}")
        
        return True
    except Exception as e:
        print(f"❌ Withdrawal system test failed: {e}")
        return False

async def test_games_menu():
    """Test games menu structure"""
    print("🎮 Testing games menu...")
    
    try:
        from src.menus.games_menu import show_games_menu
        print("✅ Games menu module imported successfully")
        
        # Test that all game imports work
        from src.games import (
            coinflip_command, dice_command, slots_command,
            roulette_command, blackjack_command, crash_command
        )
        print("✅ All game modules imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Games menu test failed: {e}")
        return False

async def test_bot_imports():
    """Test all bot imports"""
    print("🤖 Testing bot imports...")
    
    try:
        from src.bot import main, setup_bot, post_init
        print("✅ Main bot functions imported")
        
        from src.menus import main_menu_command, games_menu_command
        print("✅ Menu commands imported")
        
        from src.admin import admin_command, broadcast_command
        print("✅ Admin commands imported")
        
        return True
    except Exception as e:
        print(f"❌ Bot imports test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting ExoWin 👑 Bot Functionality Tests\n")
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Admin Functions", test_admin_functions),
        ("Withdrawal System", test_withdrawal_system),
        ("Games Menu", test_games_menu),
        ("Bot Imports", test_bot_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! ExoWin 👑 is ready to run!")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)