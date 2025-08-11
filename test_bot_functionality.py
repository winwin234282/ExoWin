#!/usr/bin/env python3
"""
Test script to verify ExoWin bot functionality
"""
import asyncio
import sys
import os
sys.path.append("/root/ExoWinBot/src")

from database import get_user, get_system_stats
from wallet.nowpayments import NOWPaymentsAPI

async def test_database():
    """Test database connectivity and functions"""
    print("🔍 Testing Database...")
    try:
        # Test basic user retrieval
        user = await get_user(123456789)  # Test user ID
        print(f"✅ Database connection: OK")
        print(f"✅ User retrieval: OK")
        
        # Test system stats
        stats = await get_system_stats()
        print(f"✅ System stats: OK - {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

async def test_nowpayments():
    """Test NOWPayments API"""
    print("\n💰 Testing NOWPayments...")
    try:
        api = NOWPaymentsAPI()
        if not api.api_key:
            print("⚠️ NOWPayments API key not configured")
            return False
            
        status = await api.get_status()
        print(f"✅ NOWPayments API: OK - {status}")
        return True
    except Exception as e:
        print(f"❌ NOWPayments error: {e}")
        return False

async def test_imports():
    """Test all game imports"""
    print("\n🎮 Testing Game Imports...")
    try:
        # Test animated games
        from games.dice_animated import dice_command, dice_callback
        from games.darts_animated import darts_command, darts_callback
        from games.slots_animated import slots_command, slots_callback
        from games.bowling_animated import bowling_command, bowling_callback
        from games.basketball_animated import basketball_command, basketball_callback
        from games.football_animated import football_command, football_callback
        print("✅ Animated games imports: OK")
        
        # Test web app games
        from games.blackjack import blackjack_command, blackjack_callback
        from games.roulette import roulette_command, roulette_callback
        from games.mines import mines_command, mines_callback
        from games.tower import tower_command, tower_callback
        from games.wheel import wheel_command, wheel_callback
        from games.crash import crash_command, crash_callback
        from games.plinko import plinko_command, plinko_callback
        print("✅ Web app games imports: OK")
        
        # Test simple games
        from games.coinflip import coinflip_command, coinflip_callback
        from games.lottery import lottery_command, lottery_callback
        from games.poker import poker_command, poker_callback
        print("✅ Simple games imports: OK")
        
        # Test admin
        from admin import admin_command, admin_callback
        print("✅ Admin imports: OK")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 ExoWin Bot Functionality Test\n")
    
    results = []
    results.append(await test_database())
    results.append(await test_nowpayments())
    results.append(await test_imports())
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed - check logs above")

if __name__ == "__main__":
    asyncio.run(main())
