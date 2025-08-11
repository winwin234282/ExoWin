from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, claim_daily_bonus, add_referral
from src.utils.formatting import format_money
from datetime import datetime, timedelta

async def bonuses_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the bonuses menu"""
    await show_bonuses_menu(update, context)

async def show_bonuses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the bonuses menu"""
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    user = await get_user(user_id)
    
    # Check if user can claim daily bonus
    last_bonus = user.get('last_daily_bonus')
    can_claim_daily = True
    if last_bonus:
        if isinstance(last_bonus, str):
            # Handle string datetime
            try:
                last_bonus = datetime.fromisoformat(last_bonus.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                last_bonus = datetime.now() - timedelta(days=1)  # Allow claim if parsing fails
        
        time_since_bonus = datetime.now() - last_bonus
        can_claim_daily = time_since_bonus >= timedelta(hours=24)
    
    # Calculate next bonus time
    next_bonus_time = ""
    if not can_claim_daily and last_bonus:
        next_bonus = last_bonus + timedelta(hours=24)
        time_left = next_bonus - datetime.now()
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        next_bonus_time = f"⏰ Next bonus in: {hours}h {minutes}m"
    
    message = (
        f"🎁 **Bonuses & Rewards** 🎁\n\n"
        f"💰 Current balance: {format_money(user['balance'])}\n\n"
        f"🎯 **Available Bonuses:**\n\n"
        f"🎁 Daily Bonus: {'✅ Available!' if can_claim_daily else '❌ Claimed'}\n"
        f"{next_bonus_time}\n\n"
        f"🎮 Referral Bonus: 🔄 Active\n"
        f"🏆 VIP Rewards: 🔄 Coming Soon\n"
        f"🎊 Special Events: 🔄 Check Back Later"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎁 Daily Bonus" + (" ✅" if can_claim_daily else " ❌"), 
                               callback_data="bonus_daily" if can_claim_daily else "bonus_daily_unavailable")
        ],
        [
            InlineKeyboardButton("👥 Referral Program", callback_data="bonus_referral"),
            InlineKeyboardButton("🏆 VIP Rewards", callback_data="bonus_vip")
        ],
        [
            InlineKeyboardButton("🎊 Special Events", callback_data="bonus_events"),
            InlineKeyboardButton("🎯 Bonus History", callback_data="bonus_history")
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

async def claim_daily_bonus_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim daily bonus"""
    user_id = update.callback_query.from_user.id
    
    # Try to claim daily bonus
    success, result = await claim_daily_bonus(user_id)
    
    if success:
        bonus_amount = result
        message = (
            f"🎉 **Daily Bonus Claimed!** 🎉\n\n"
            f"💰 **Bonus Amount:** {format_money(bonus_amount)}\n"
            f"🔥 **Streak Bonus:** Included!\n\n"
            f"✅ Bonus added to your balance!\n"
            f"🎯 Come back tomorrow for more!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🎁 View Bonuses", callback_data="menu_bonuses")
            ],
            [
                InlineKeyboardButton("🎮 Play Games", callback_data="menu_games")
            ]
        ]
    else:
        error_message = result
        message = (
            f"❌ **Cannot Claim Bonus** ❌\n\n"
            f"📅 {error_message}\n\n"
            f"⏰ **Next bonus available:**\n"
            f"Come back in a few hours!\n\n"
            f"🎯 Keep your streak alive!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Check Again", callback_data="bonus_daily")
            ],
            [
                InlineKeyboardButton("🔙 Back to Bonuses", callback_data="menu_bonuses")
            ]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_referral_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral program details"""
    user_id = update.callback_query.from_user.id
    
    referral_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    
    total_referrals = user.get('total_referrals', 0)
    referral_earnings = user.get('total_referral_bonuses', 0)
    
    message = (
        f"👥 **Referral Program** 👥\n\n"
        f"🎯 **How it works:**\n"
        f"• Share your referral link\n"
        f"• Friends join using your link\n"
        f"• You both get bonus rewards!\n\n"
        f"💰 **Rewards:**\n"
        f"• You get: $2 per referral\n"
        f"• Friend gets: $1 bonus\n\n"
        f"🔗 **Your referral link:**\n"
        f"`{referral_link}`\n\n"
        f"📊 **Your stats:**\n"
        f"👥 Referrals: {total_referrals}\n"
        f"💰 Earned: {format_money(referral_earnings)}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_referral_{user_id}")
        ],
        [
            InlineKeyboardButton("📊 Referral Stats", callback_data="referral_stats")
        ],
        [
            InlineKeyboardButton("🔙 Back to Bonuses", callback_data="menu_bonuses")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_vip_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show VIP rewards program"""
    user_id = update.callback_query.from_user.id
    user = await get_user(user_id)
    
    total_deposits = user.get('total_deposits', 0)
    total_games = user.get('total_bets', 0)
    
    # Calculate VIP level
    vip_level = 0
    if total_deposits >= 100:
        vip_level = 1
    if total_deposits >= 500:
        vip_level = 2
    if total_deposits >= 1000:
        vip_level = 3
    if total_deposits >= 5000:
        vip_level = 4
    
    vip_names = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"]
    current_vip = vip_names[vip_level] if vip_level < len(vip_names) else "Diamond"
    
    message = (
        f"🏆 **VIP Rewards Program** 🏆\n\n"
        f"👑 Current Level: **{current_vip}** (Level {vip_level})\n"
        f"💰 Total Deposited: {format_money(total_deposits)}\n"
        f"🎮 Games Played: {total_games:,}\n\n"
        f"🎯 **VIP Benefits:**\n"
        f"• Higher daily bonuses\n"
        f"• Exclusive games access\n"
        f"• Priority support\n"
        f"• Special promotions\n\n"
        f"📈 **Next Level Requirements:**\n"
        f"💰 Deposit: ${max(0, [100, 500, 1000, 5000][min(vip_level, 3)] - total_deposits):.2f} more"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Deposit to Upgrade", callback_data="menu_deposit")
        ],
        [
            InlineKeyboardButton("🏆 VIP Benefits", callback_data="vip_benefits")
        ],
        [
            InlineKeyboardButton("🔙 Back to Bonuses", callback_data="menu_bonuses")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_special_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show special events and promotions"""
    message = (
        f"🎊 **Special Events** 🎊\n\n"
        f"🎯 **Current Events:**\n\n"
        f"🎁 **Welcome Bonus**\n"
        f"Get $1 free to start playing!\n"
        f"Status: ✅ Claimed\n\n"
        f"🎰 **Weekend Multiplier**\n"
        f"2x winnings on weekends!\n"
        f"Status: 🔄 Coming Soon\n\n"
        f"🏆 **Monthly Tournament**\n"
        f"Compete for the top prize!\n"
        f"Status: 🔄 Coming Soon\n\n"
        f"📅 Check back regularly for new events!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎁 Claim Bonuses", callback_data="events_claim")
        ],
        [
            InlineKeyboardButton("🏆 Tournament", callback_data="events_tournament"),
            InlineKeyboardButton("📅 Event Calendar", callback_data="events_calendar")
        ],
        [
            InlineKeyboardButton("🔙 Back to Bonuses", callback_data="menu_bonuses")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_bonus_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bonus claim history"""
    user_id = update.callback_query.from_user.id
    user = await get_user(user_id)
    
    daily_streak = user.get('daily_bonus_streak', 0)
    last_bonus = user.get('last_daily_bonus', 'Never')
    
    if isinstance(last_bonus, datetime):
        last_bonus = last_bonus.strftime('%Y-%m-%d %H:%M')
    elif hasattr(last_bonus, 'strftime'):
        last_bonus = last_bonus.strftime('%Y-%m-%d %H:%M')
    
    total_daily_earned = user.get('total_daily_bonuses', 0)
    total_referral_earned = user.get('total_referral_bonuses', 0)
    total_event_earned = user.get('total_event_bonuses', 0)
    
    message = (
        f"🎯 **Bonus History** 🎯\n\n"
        f"📊 **Daily Bonus:**\n"
        f"🔥 Current streak: {daily_streak} days\n"
        f"📅 Last claimed: {last_bonus}\n\n"
        f"💰 **Total bonuses earned:**\n"
        f"🎁 Daily bonuses: {format_money(total_daily_earned)}\n"
        f"👥 Referral bonuses: {format_money(total_referral_earned)}\n"
        f"🎊 Event bonuses: {format_money(total_event_earned)}\n\n"
        f"🎯 Keep claiming daily to build your streak!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="bonus_history")
        ],
        [
            InlineKeyboardButton("🔙 Back to Bonuses", callback_data="menu_bonuses")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def bonuses_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bonuses menu callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    if len(data) < 2:
        return
    
    action = data[1]
    
    if action == "daily":
        await claim_daily_bonus(update, context)
    elif action == "referral":
        await show_referral_program(update, context)
    elif action == "vip":
        await show_vip_rewards(update, context)
    elif action == "events":
        await show_special_events(update, context)
    elif action == "history":
        await show_bonus_history(update, context)
