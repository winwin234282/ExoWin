from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user

async def settings_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the settings menu"""
    await show_settings_menu(update, context)

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the settings menu"""
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    user = await get_user(user_id)
    
    # Get current settings (with defaults)
    notifications = user.get('notifications_enabled', True)
    auto_bet = user.get('auto_bet_enabled', False)
    sound_effects = user.get('sound_effects', True)
    animations = user.get('animations_enabled', True)
    
    message = (
        f"⚙️ **Settings** ⚙️\n\n"
        f"🎯 **Game Preferences:**\n"
        f"🔔 Notifications: {'✅ On' if notifications else '❌ Off'}\n"
        f"🎯 Auto-bet: {'✅ On' if auto_bet else '❌ Off'}\n"
        f"🔊 Sound effects: {'✅ On' if sound_effects else '❌ Off'}\n"
        f"🎬 Animations: {'✅ On' if animations else '❌ Off'}\n\n"
        f"🔒 **Security:**\n"
        f"🔐 2FA: ❌ Not set up\n"
        f"📧 Email: ❌ Not verified\n\n"
        f"📱 **App Settings:**\n"
        f"🌙 Dark mode: ✅ On\n"
        f"🌍 Language: 🇺🇸 English"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(f"🔔 Notifications {'✅' if notifications else '❌'}", 
                               callback_data="settings_toggle_notifications"),
            InlineKeyboardButton(f"🎯 Auto-bet {'✅' if auto_bet else '❌'}", 
                               callback_data="settings_toggle_autobet")
        ],
        [
            InlineKeyboardButton(f"🔊 Sound {'✅' if sound_effects else '❌'}", 
                               callback_data="settings_toggle_sound"),
            InlineKeyboardButton(f"🎬 Animations {'✅' if animations else '❌'}", 
                               callback_data="settings_toggle_animations")
        ],
        [
            InlineKeyboardButton("🔒 Security Settings", callback_data="settings_security"),
            InlineKeyboardButton("🌍 Language", callback_data="settings_language")
        ],
        [
            InlineKeyboardButton("📱 App Preferences", callback_data="settings_app"),
            InlineKeyboardButton("🎨 Theme", callback_data="settings_theme")
        ],
        [
            InlineKeyboardButton("📞 Support", callback_data="settings_support"),
            InlineKeyboardButton("ℹ️ About", callback_data="settings_about")
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

async def settings_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings menu callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    if len(data) < 2:
        return
    
    action = data[1]
    
    if action == "toggle":
        await toggle_setting(update, context, data[2])
    elif action == "security":
        await show_security_settings(update, context)
    elif action == "language":
        await show_language_settings(update, context)
    elif action == "app":
        await show_app_preferences(update, context)
    elif action == "theme":
        await show_theme_settings(update, context)
    elif action == "support":
        await show_support_info(update, context)
    elif action == "about":
        await show_about_info(update, context)

async def toggle_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, setting: str):
    """Toggle a user setting"""
    user_id = update.callback_query.from_user.id
    
    from src.database import users_collection
    
    setting_map = {
        "notifications": "notifications_enabled",
        "autobet": "auto_bet_enabled", 
        "sound": "sound_effects",
        "animations": "animations_enabled"
    }
    
    if setting not in setting_map:
        return
    
    db_field = setting_map[setting]
    user = await get_user(user_id)
    current_value = user.get(db_field, True)
    new_value = not current_value
    
    # Update in database
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {db_field: new_value}}
    )
    
    setting_names = {
        "notifications": "Notifications",
        "autobet": "Auto-bet",
        "sound": "Sound effects", 
        "animations": "Animations"
    }
    
    await update.callback_query.answer(
        f"✅ {setting_names[setting]} {'enabled' if new_value else 'disabled'}!",
        show_alert=True
    )
    
    # Refresh the settings menu
    await show_settings_menu(update, context)

async def show_security_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show security settings"""
    message = (
        f"🔒 **Security Settings** 🔒\n\n"
        f"🛡️ **Account Protection:**\n"
        f"🔐 Password: ❌ Not set\n"
        f"🔑 2FA: ❌ Disabled\n"
        f"📱 Login alerts: ✅ Enabled\n"
        f"🚫 Account lock: ❌ Disabled\n\n"
        f"⚠️ **Recommendations:**\n"
        f"• Set up 2FA for extra security\n"
        f"• Enable account lock for large withdrawals\n"
        f"• Keep login alerts enabled\n\n"
        f"🔒 Coming soon: Enhanced security features!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔐 Set Password", callback_data="security_password"),
            InlineKeyboardButton("🔑 Setup 2FA", callback_data="security_2fa")
        ],
        [
            InlineKeyboardButton("📱 Login Alerts", callback_data="security_alerts"),
            InlineKeyboardButton("🚫 Account Lock", callback_data="security_lock")
        ],
        [
            InlineKeyboardButton("🔙 Back to Settings", callback_data="menu_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_language_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language settings"""
    message = (
        f"🌍 **Language Settings** 🌍\n\n"
        f"🎯 **Current Language:** 🇺🇸 English\n\n"
        f"🌐 **Available Languages:**\n"
        f"🇺🇸 English (Current)\n"
        f"🇪🇸 Spanish (Coming Soon)\n"
        f"🇫🇷 French (Coming Soon)\n"
        f"🇩🇪 German (Coming Soon)\n"
        f"🇷🇺 Russian (Coming Soon)\n"
        f"🇨🇳 Chinese (Coming Soon)\n\n"
        f"🔄 More languages coming soon!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🇺🇸 English ✅", callback_data="lang_en")
        ],
        [
            InlineKeyboardButton("🇪🇸 Español 🔄", callback_data="lang_es_soon"),
            InlineKeyboardButton("🇫🇷 Français 🔄", callback_data="lang_fr_soon")
        ],
        [
            InlineKeyboardButton("🇩🇪 Deutsch 🔄", callback_data="lang_de_soon"),
            InlineKeyboardButton("🇷🇺 Русский 🔄", callback_data="lang_ru_soon")
        ],
        [
            InlineKeyboardButton("🔙 Back to Settings", callback_data="menu_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_app_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show app preferences"""
    message = (
        f"📱 **App Preferences** 📱\n\n"
        f"🎨 **Display:**\n"
        f"🌙 Dark mode: ✅ Enabled\n"
        f"🎬 Animations: ✅ Enabled\n"
        f"🔊 Sound effects: ✅ Enabled\n\n"
        f"🎮 **Gameplay:**\n"
        f"⚡ Quick bet: ❌ Disabled\n"
        f"🎯 Auto-bet: ❌ Disabled\n"
        f"📊 Show statistics: ✅ Enabled\n\n"
        f"📱 **Interface:**\n"
        f"🔢 Show balance: ✅ Always\n"
        f"⏰ Show time: ✅ Enabled\n"
        f"🎪 Compact mode: ❌ Disabled"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🌙 Dark Mode ✅", callback_data="app_toggle_dark"),
            InlineKeyboardButton("⚡ Quick Bet ❌", callback_data="app_toggle_quick")
        ],
        [
            InlineKeyboardButton("📊 Statistics ✅", callback_data="app_toggle_stats"),
            InlineKeyboardButton("🎪 Compact Mode ❌", callback_data="app_toggle_compact")
        ],
        [
            InlineKeyboardButton("🔙 Back to Settings", callback_data="menu_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_theme_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show theme settings"""
    message = (
        f"🎨 **Theme Settings** 🎨\n\n"
        f"🌙 **Current Theme:** Dark\n\n"
        f"🎯 **Available Themes:**\n"
        f"🌙 Dark (Current)\n"
        f"☀️ Light (Available)\n"
        f"🎮 Gaming (Coming Soon)\n"
        f"💎 Premium (VIP Only)\n"
        f"🎊 Neon (Coming Soon)\n\n"
        f"🎨 Choose your preferred theme:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🌙 Dark ✅", callback_data="theme_dark"),
            InlineKeyboardButton("☀️ Light", callback_data="theme_light")
        ],
        [
            InlineKeyboardButton("🎮 Gaming 🔄", callback_data="theme_gaming_soon"),
            InlineKeyboardButton("💎 Premium 👑", callback_data="theme_premium_vip")
        ],
        [
            InlineKeyboardButton("🎊 Neon 🔄", callback_data="theme_neon_soon")
        ],
        [
            InlineKeyboardButton("🔙 Back to Settings", callback_data="menu_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_support_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show support information"""
    message = (
        f"📞 **Support & Help** 📞\n\n"
        f"🎯 **Need Help?**\n"
        f"Our support team is here to help you!\n\n"
        f"📧 **Contact Methods:**\n"
        f"💬 Telegram: @GambleBotSupport\n"
        f"📧 Email: support@gamblebot.com\n"
        f"🌐 Website: www.gamblebot.com\n\n"
        f"⏰ **Support Hours:**\n"
        f"🕐 24/7 Automated Support\n"
        f"👨‍💼 Live Agent: 9 AM - 6 PM UTC\n\n"
        f"❓ **Common Issues:**\n"
        f"• Payment not received\n"
        f"• Withdrawal delays\n"
        f"• Game technical issues\n"
        f"• Account verification"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("💬 Contact Support", url="https://t.me/GambleBotSupport")
        ],
        [
            InlineKeyboardButton("❓ FAQ", callback_data="support_faq"),
            InlineKeyboardButton("📋 Report Issue", callback_data="support_report")
        ],
        [
            InlineKeyboardButton("🔙 Back to Settings", callback_data="menu_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_about_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show about information"""
    message = (
        f"ℹ️ **About Gamble Bot** ℹ️\n\n"
        f"🎰 **Version:** 2.0.0\n"
        f"🚀 **Release:** December 2024\n"
        f"👨‍💻 **Developer:** Gamble Bot Team\n\n"
        f"🎯 **Features:**\n"
        f"• 🎮 12+ Interactive Games\n"
        f"• 💰 Cryptocurrency Payments\n"
        f"• 🔒 Secure & Anonymous\n"
        f"• 📱 Mobile Optimized\n"
        f"• 🎁 Daily Bonuses\n"
        f"• 👥 Referral Program\n\n"
        f"🔒 **Security:**\n"
        f"• 🛡️ SSL Encrypted\n"
        f"• 🔐 Secure Payments\n"
        f"• 🚫 No KYC Required\n"
        f"• 💰 Instant Withdrawals\n\n"
        f"📜 **Legal:**\n"
        f"• 📋 Terms of Service\n"
        f"• 🔒 Privacy Policy\n"
        f"• ⚖️ Responsible Gambling"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📋 Terms of Service", callback_data="about_terms"),
            InlineKeyboardButton("🔒 Privacy Policy", callback_data="about_privacy")
        ],
        [
            InlineKeyboardButton("⚖️ Responsible Gambling", callback_data="about_responsible")
        ],
        [
            InlineKeyboardButton("🔙 Back to Settings", callback_data="menu_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def settings_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings menu callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    if len(data) < 2:
        return
    
    action = data[1]
    
    if action == "notifications":
        await show_notification_settings(update, context)
    elif action == "security":
        await show_security_settings(update, context)
    elif action == "privacy":
        await show_privacy_settings(update, context)
    elif action == "language":
        await show_language_settings(update, context)
    elif action == "preferences":
        await show_app_preferences(update, context)
    elif action == "theme":
        await show_theme_settings(update, context)
    elif action == "support":
        await show_support_info(update, context)
    elif action == "about":
        await show_about_info(update, context)
