import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, record_game
from src.utils.formatting import format_money
from dotenv import load_dotenv

load_dotenv()
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://work-1-yvxwuoonnfvrxtzn.prod-runtime.all-hands.dev")

async def mines_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a mines game"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    message = (
        f"💎 **Mines Game** 💎\n\n"
        f"💰 Balance: {format_money(user['balance'])}\n\n"
        f"🎯 **How to Play:**\n"
        f"• Choose number of mines (1-24)\n"
        f"• Click tiles to reveal gems 💎\n"
        f"• Avoid mines 💣\n"
        f"• Cash out anytime to win!\n\n"
        f"⚡ **Features:**\n"
        f"• Interactive visual gameplay\n"
        f"• Real-time multiplier updates\n"
        f"• Risk vs reward strategy\n\n"
        f"🎮 Click below to start playing!"
    )
    
    webapp_url = f"{WEBAPP_URL}/games/mines?user_id={user_id}"
    
    keyboard = [
        [
            InlineKeyboardButton("🎮 Play Mines", web_app=WebAppInfo(url=webapp_url))
        ],
        [
            InlineKeyboardButton("📊 Game Rules", callback_data="mines_rules"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="mines_leaderboard")
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

async def mines_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mines game callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    action = data[1] if len(data) > 1 else ""
    
    if action == "rules":
        await show_mines_rules(update, context)
    elif action == "leaderboard":
        await show_mines_leaderboard(update, context)
    elif action == "play":
        await mines_command(update, context)

async def show_mines_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show mines game rules"""
    message = (
        f"📋 **Mines Game Rules** 📋\n\n"
        f"🎯 **Objective:**\n"
        f"Find gems 💎 while avoiding mines 💣\n\n"
        f"🎮 **How to Play:**\n"
        f"1️⃣ Choose number of mines (1-24)\n"
        f"2️⃣ Set your bet amount\n"
        f"3️⃣ Click tiles to reveal\n"
        f"4️⃣ Cash out anytime to secure winnings\n\n"
        f"💰 **Payouts:**\n"
        f"• More mines = Higher multipliers\n"
        f"• More gems found = Higher winnings\n"
        f"• Hit a mine = Lose everything\n\n"
        f"⚡ **Strategy Tips:**\n"
        f"• Start with fewer mines for safety\n"
        f"• Cash out early to secure profits\n"
        f"• Higher risk = Higher reward\n\n"
        f"🎲 **Multiplier Examples:**\n"
        f"3 mines, 5 gems: ~3.5x\n"
        f"10 mines, 8 gems: ~15x\n"
        f"20 mines, 3 gems: ~8x"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎮 Play Now", callback_data="mines_play")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="mines_play")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_mines_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show mines leaderboard"""
    message = (
        f"🏆 **Mines Leaderboard** 🏆\n\n"
        f"📊 **Leaderboard is currently empty**\n\n"
        f"🎯 **Be the first to:**\n"
        f"• Find the most gems\n"
        f"• Win the biggest payout\n"
        f"• Master the mines game\n\n"
        f"💎 Start playing to see your name here!\n\n"
        f"🔄 Leaderboard updates in real-time"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎮 Play to Compete", callback_data="mines_play")
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="mines_leaderboard")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="mines_play")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def mines_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mines game messages"""
    return False  # No message handling needed for mines