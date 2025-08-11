import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, record_game
from src.utils.formatting import format_money
from dotenv import load_dotenv

load_dotenv()
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://work-1-yvxwuoonnfvrxtzn.prod-runtime.all-hands.dev")

async def tower_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a tower game"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    message = (
        f"🗼 **Tower Game** 🗼\n\n"
        f"💰 Balance: {format_money(user['balance'])}\n\n"
        f"🎯 **How to Play:**\n"
        f"• Climb the tower level by level\n"
        f"• Choose the correct block 🟢\n"
        f"• Avoid the wrong blocks 🔴\n"
        f"• Cash out anytime to win!\n\n"
        f"⚡ **Features:**\n"
        f"• 8 levels to climb\n"
        f"• Increasing multipliers\n"
        f"• Risk vs reward strategy\n\n"
        f"🎮 Click below to start climbing!"
    )
    
    webapp_url = f"{WEBAPP_URL}/games/tower?user_id={user_id}"
    
    keyboard = [
        [
            InlineKeyboardButton("🎮 Play Tower", web_app=WebAppInfo(url=webapp_url))
        ],
        [
            InlineKeyboardButton("📊 Game Rules", callback_data="tower_rules"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="tower_leaderboard")
        ],
        [
            InlineKeyboardButton("🔙 Back to Games", callback_data="menu_games")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def tower_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tower game callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    action = data[1] if len(data) > 1 else ""
    
    if action == "rules":
        await show_tower_rules(update, context)
    elif action == "leaderboard":
        await show_tower_leaderboard(update, context)
    elif action == "play":
        await tower_command(update, context)

async def show_tower_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show tower game rules"""
    message = (
        f"📋 **Tower Game Rules** 📋\n\n"
        f"🎯 **Objective:**\n"
        f"Climb the tower by choosing correct blocks\n\n"
        f"🎮 **How to Play:**\n"
        f"1️⃣ Set your bet amount\n"
        f"2️⃣ Choose difficulty (2-4 blocks per level)\n"
        f"3️⃣ Click the correct block to advance\n"
        f"4️⃣ Cash out anytime to secure winnings\n\n"
        f"💰 **Payouts:**\n"
        f"• Level 1: 1.5x multiplier\n"
        f"• Level 2: 2.25x multiplier\n"
        f"• Level 3: 3.38x multiplier\n"
        f"• Level 4: 5.06x multiplier\n"
        f"• Level 5: 7.59x multiplier\n"
        f"• Level 6: 11.39x multiplier\n"
        f"• Level 7: 17.09x multiplier\n"
        f"• Level 8: 25.63x multiplier\n\n"
        f"⚡ **Strategy Tips:**\n"
        f"• Easier difficulty = Lower multipliers\n"
        f"• Cash out early to secure profits\n"
        f"• Higher levels = Exponential rewards"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎮 Play Now", callback_data="tower_play")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="tower_play")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_tower_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show tower leaderboard"""
    message = (
        f"🏆 **Tower Leaderboard** 🏆\n\n"
        f"📊 **Coming Soon!**\n\n"
        f"The leaderboard will track:\n"
        f"• Highest levels reached\n"
        f"• Biggest single wins\n"
        f"• Most consistent climbers\n"
        f"• Best win streaks\n\n"
        f"🗼 Start climbing to be featured when leaderboards launch!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎮 Start Climbing", callback_data="tower_play")
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="tower_leaderboard")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="tower_play")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def tower_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tower game messages"""
    return False  # No message handling needed for tower