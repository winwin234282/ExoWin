#!/usr/bin/env python3
"""
Simple test to verify all imports work correctly
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all critical imports"""
    print("🚀 Testing ExoWin 👑 Bot Imports\n")
    
    tests = []
    
    # Test database imports
    try:
        from src.database.db import (
            get_user, update_user_balance, record_transaction,
            get_system_stats, get_game_statistics, setup_database
        )
        tests.append(("Database Functions", True))
    except Exception as e:
        tests.append(("Database Functions", False, str(e)))
    
    # Test admin imports
    try:
        from src.admin.admin_panel import (
            admin_command, admin_callback, admin_message_handler,
            is_admin, broadcast_command
        )
        tests.append(("Admin Panel", True))
    except Exception as e:
        tests.append(("Admin Panel", False, str(e)))
    
    # Test withdrawal system
    try:
        from src.wallet.withdrawal_system import WithdrawalSystem
        tests.append(("Withdrawal System", True))
    except Exception as e:
        tests.append(("Withdrawal System", False, str(e)))
    
    # Test games menu
    try:
        from src.menus.games_menu import show_games_menu
        tests.append(("Games Menu", True))
    except Exception as e:
        tests.append(("Games Menu", False, str(e)))
    
    # Test main menu
    try:
        from src.menus.main_menu import show_main_menu
        tests.append(("Main Menu", True))
    except Exception as e:
        tests.append(("Main Menu", False, str(e)))
    
    # Test bot main
    try:
        from src.bot import main, setup_bot, post_init
        tests.append(("Bot Main", True))
    except Exception as e:
        tests.append(("Bot Main", False, str(e)))
    
    # Test game imports
    try:
        from src.games.coinflip import coinflip_command
        from src.games.dice import dice_command
        from src.games.slots import slots_command
        tests.append(("Game Commands", True))
    except Exception as e:
        tests.append(("Game Commands", False, str(e)))
    
    # Print results
    passed = 0
    total = len(tests)
    
    for test in tests:
        if len(test) == 2:  # Success case
            name, success = test
            if success:
                print(f"✅ {name}: PASSED")
                passed += 1
            else:
                print(f"❌ {name}: FAILED")
        else:  # Error case
            name, success, error = test
            print(f"❌ {name}: FAILED - {error}")
    
    print(f"\n📊 Import Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All imports successful! ExoWin 👑 is ready!")
        return True
    else:
        print("⚠️  Some imports failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)