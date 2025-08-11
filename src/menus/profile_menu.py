from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user
from src.utils.formatting import format_money, format_user_stats

async def profile_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the profile menu"""
    await show_profile_menu(update, context)

async def show_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the user profile menu"""
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    user = await get_user(user_id)
    
    # Calculate win rate
    total_games = user.get('total_bets', 0)
    total_wins = user.get('total_wins', 0)
    win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
    
    # Calculate profit/loss
    total_deposits = user.get('total_deposits', 0)
    total_withdrawals = user.get('total_withdrawals', 0)
    current_balance = user.get('balance', 0)
    net_profit = current_balance + total_withdrawals - total_deposits - 1  # Subtract initial $1
    
    message = (
        f"👤 **Your Profile** 👤\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"💰 Balance: {format_money(user['balance'])}\n"
        f"📅 Member since: {user.get('created_at', 'Unknown').strftime('%Y-%m-%d') if hasattr(user.get('created_at', ''), 'strftime') else 'Unknown'}\n\n"
        f"📊 **Statistics:**\n"
        f"🎮 Total games: {total_games:,}\n"
        f"🏆 Total wins: {total_wins:,}\n"
        f"📉 Total losses: {user.get('total_losses', 0):,}\n"
        f"📈 Win rate: {win_rate:.1f}%\n\n"
        f"💸 **Financial:**\n"
        f"💰 Total deposited: {format_money(total_deposits)}\n"
        f"💸 Total withdrawn: {format_money(total_withdrawals)}\n"
        f"📊 Net profit/loss: {format_money(net_profit)}\n\n"
        f"🎯 **Achievements:**\n"
        f"{'🏆 High Roller' if total_deposits >= 1000 else '🎯 Beginner'}\n"
        f"{'💎 VIP Player' if total_games >= 100 else '🎮 Casual Player'}\n"
        f"{'🔥 Lucky Streak' if win_rate >= 60 else '🎲 Learning'}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Detailed Stats", callback_data="profile_stats"),
            InlineKeyboardButton("🏆 Achievements", callback_data="profile_achievements")
        ],
        [
            InlineKeyboardButton("📜 Game History", callback_data="profile_history"),
            InlineKeyboardButton("💰 Transaction History", callback_data="profile_transactions")
        ],
        [
            InlineKeyboardButton("⚙️ Account Settings", callback_data="profile_settings"),
            InlineKeyboardButton("🔒 Security", callback_data="profile_security")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def profile_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile menu callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    if len(data) < 2:
        return
    
    action = data[1]
    
    if action == "stats":
        await show_detailed_stats(update, context)
    elif action == "achievements":
        await show_achievements(update, context)
    elif action == "history":
        await show_game_history(update, context)
    elif action == "transactions":
        await show_transaction_history(update, context)
    elif action == "settings":
        await show_account_settings(update, context)
    elif action == "security":
        await show_security_settings(update, context)

async def show_detailed_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed user statistics"""
    user_id = update.callback_query.from_user.id
    user = await get_user(user_id)
    
    message = (
        f"📊 **Detailed Statistics** 📊\n\n"
        f"{format_user_stats(user)}\n\n"
        f"Keep playing to improve your stats!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh Stats", callback_data="profile_stats")
        ],
        [
            InlineKeyboardButton("🔙 Back to Profile", callback_data="menu_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user achievements"""
    user_id = update.callback_query.from_user.id
    user = await get_user(user_id)
    
    total_games = user.get('total_bets', 0)
    total_wins = user.get('total_wins', 0)
    total_deposits = user.get('total_deposits', 0)
    win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
    
    achievements = []
    
    # Game-based achievements
    if total_games >= 10:
        achievements.append("🎮 **Rookie Gambler** - Played 10+ games")
    if total_games >= 50:
        achievements.append("🎯 **Regular Player** - Played 50+ games")
    if total_games >= 100:
        achievements.append("💎 **VIP Player** - Played 100+ games")
    if total_games >= 500:
        achievements.append("👑 **Gambling Legend** - Played 500+ games")
    
    # Win-based achievements
    if total_wins >= 5:
        achievements.append("🏆 **First Wins** - Won 5+ games")
    if total_wins >= 25:
        achievements.append("🔥 **Hot Streak** - Won 25+ games")
    if total_wins >= 100:
        achievements.append("⭐ **Champion** - Won 100+ games")
    
    # Deposit-based achievements
    if total_deposits >= 50:
        achievements.append("💰 **Investor** - Deposited $50+")
    if total_deposits >= 500:
        achievements.append("💎 **High Roller** - Deposited $500+")
    if total_deposits >= 1000:
        achievements.append("👑 **Whale** - Deposited $1000+")
    
    # Special achievements
    if win_rate >= 70:
        achievements.append("🍀 **Lucky Player** - 70%+ win rate")
    if win_rate >= 80:
        achievements.append("🌟 **Master Gambler** - 80%+ win rate")
    
    if not achievements:
        achievements.append("🎯 **New Player** - Start playing to unlock achievements!")
    
    message = (
        f"🏆 **Your Achievements** 🏆\n\n"
        + "\n".join(achievements) +
        f"\n\n🎮 Keep playing to unlock more achievements!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔙 Back to Profile", callback_data="menu_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_game_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent game history"""
    user_id = update.callback_query.from_user.id
    
    message = (
        f"📜 **Game History** 📜\n\n"
        f"Your recent games will be displayed here.\n"
        f"(This feature will show your last 10 games with results)\n\n"
        f"🎮 Coming soon: Detailed game history with filters!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="profile_history")
        ],
        [
            InlineKeyboardButton("🔙 Back to Profile", callback_data="menu_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show transaction history"""
    user_id = update.callback_query.from_user.id
    
    message = (
        f"💰 **Transaction History** 💰\n\n"
        f"Your recent deposits and withdrawals will be displayed here.\n"
        f"(This feature will show your transaction history)\n\n"
        f"💳 Coming soon: Detailed transaction history!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="profile_transactions")
        ],
        [
            InlineKeyboardButton("🔙 Back to Profile", callback_data="menu_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_account_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show account settings"""
    message = (
        f"⚙️ **Account Settings** ⚙️\n\n"
        f"Manage your account preferences:\n\n"
        f"🔔 Notifications: Enabled\n"
        f"🎯 Auto-bet: Disabled\n"
        f"🔒 2FA: Not set up\n"
        f"📧 Email: Not verified\n\n"
        f"⚙️ Coming soon: Full account customization!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications"),
            InlineKeyboardButton("🎯 Auto-bet", callback_data="settings_autobet")
        ],
        [
            InlineKeyboardButton("🔒 Setup 2FA", callback_data="settings_2fa"),
            InlineKeyboardButton("📧 Verify Email", callback_data="settings_email")
        ],
        [
            InlineKeyboardButton("🔙 Back to Profile", callback_data="menu_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_security_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show security settings"""
    message = (
        f"🔒 **Security Settings** 🔒\n\n"
        f"Protect your account:\n\n"
        f"🔐 Password: Not set\n"
        f"🔑 2FA: Disabled\n"
        f"📱 Login alerts: Enabled\n"
        f"🚫 Account lock: Disabled\n\n"
        f"🛡️ Coming soon: Enhanced security features!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔐 Set Password", callback_data="security_password"),
            InlineKeyboardButton("🔑 Enable 2FA", callback_data="security_2fa")
        ],
        [
            InlineKeyboardButton("📱 Login Alerts", callback_data="security_alerts"),
            InlineKeyboardButton("🚫 Account Lock", callback_data="security_lock")
        ],
        [
            InlineKeyboardButton("🔙 Back to Profile", callback_data="menu_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def profile_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile menu callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    if len(data) < 2:
        return
    
    action = data[1]
    
    if action == "stats":
        await show_detailed_stats(update, context)
    elif action == "achievements":
        await show_achievements(update, context)
    elif action == "history":
        await show_game_history(update, context)
    elif action == "transactions":
        await show_transaction_history(update, context)
    elif action == "settings":
        await show_account_settings(update, context)
    elif action == "security":
        await show_security_settings(update, context)
