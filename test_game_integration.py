#!/usr/bin/env python3
"""
Test script to verify game integration and admin functionality
"""
import asyncio
import sys
import os
sys.path.append("/root/ExoWinBot/src")

from unittest.mock import Mock, AsyncMock
from telegram import Update, CallbackQuery, User, Message, Chat
from telegram.ext import ContextTypes

# Import the functions we want to test
from menus.games_menu import games_menu_callback, show_games_menu
from admin.admin_panel import admin_callback

async def create_mock_update(callback_data, user_id=123456789):
    """Create a mock update object for testing"""
    user = User(id=user_id, first_name="Test", is_bot=False)
    chat = Chat(id=user_id, type="private")
    message = Message(message_id=1, date=None, chat=chat)
    
    callback_query = CallbackQuery(
        id="test",
        from_user=user,
        chat_instance="test",
        data=callback_data,
        message=message
    )
    
    # Mock the answer method
    callback_query.answer = AsyncMock()
    callback_query.edit_message_text = AsyncMock()
    
    update = Update(update_id=1, callback_query=callback_query)
    return update

async def test_games_menu():
    """Test games menu functionality"""
    print("🎮 Testing Games Menu Integration...")
    
    try:
        # Test main games menu
        update = await create_mock_update("menu_games")
        context = Mock()
        
        await show_games_menu(update, context)
        print("✅ Games menu display: OK")
        
        # Test individual game callbacks
        game_tests = [
            "game_dice", "game_darts", "game_slots", "game_bowling",
            "game_basketball", "game_football", "game_blackjack",
            "game_roulette", "game_mines", "game_tower", "game_wheel",
            "game_crash", "game_plinko", "game_coinflip", "game_lottery", "game_poker"
        ]
        
        for game in game_tests:
            try:
                update = await create_mock_update(game)
                await games_menu_callback(update, context)
                print(f"✅ {game}: OK")
            except Exception as e:
                print(f"❌ {game}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Games menu error: {e}")
        return False

async def test_admin_panel():
    """Test admin panel functionality"""
    print("\n👑 Testing Admin Panel...")
    
    try:
        context = Mock()
        
        # Test admin sections
        admin_tests = [
            "admin_users", "admin_analytics", "admin_stats", 
            "admin_financial", "admin_settings", "admin_promos",
            "admin_broadcast", "admin_system"
        ]
        
        for admin_section in admin_tests:
            try:
                update = await create_mock_update(admin_section, user_id=7818147082)
                await admin_callback(update, context)
                print(f"✅ {admin_section}: OK")
            except Exception as e:
                print(f"❌ {admin_section}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Admin panel error: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🚀 ExoWin Bot Integration Test\n")
    
    results = []
    results.append(await test_games_menu())
    results.append(await test_admin_panel())
    
    print(f"\n📊 Integration Test Results:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 All integration tests passed!")
    else:
        print("⚠️ Some integration tests failed - check logs above")

if __name__ == "__main__":
    asyncio.run(main())
