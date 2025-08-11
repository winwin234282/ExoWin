# User-specific callback handling code to insert into admin_panel.py

    elif section == "user":
        # Handle user-specific actions
        if len(data) < 4:
            return
            
        action = data[2]
        user_id = int(data[3])
        
        if action == "addbalance":
            # Set context for adding balance
            context.user_data["admin_action"] = "add_balance"
            context.user_data["target_user_id"] = user_id
            
            message = (
                f"💰 **Add Balance** 💰\n\n"
                f"Target User ID: `{user_id}`\n\n"
                f"Please enter the amount to add to this user's balance:\n"
                f"Example: 100 (adds $100)\n"
                f"Example: -50 (removes $50)"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("Cancel", callback_data="admin_users")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif action == "history":
            # Show full user history
            from src.database import get_user_transactions, get_user_games, get_user
            
            user = await get_user(user_id)
            if not user:
                await query.edit_message_text("❌ User not found.")
                return
                
            transactions = await get_user_transactions(user_id, 20)
            games = await get_user_games(user_id, 20)
            
            message = (
                f"📊 **Full History - User {user_id}** 📊\n\n"
                f"**User Info:**\n"
                f"• Balance: {format_money(user['balance'])}\n"
                f"• Status: {🚫 BANNED if user.get(is_banned) else ✅ Active}\n\n"
                f"**Recent Transactions ({len(transactions)}):**\n"
            )
            
            for i, tx in enumerate(transactions[:10], 1):
                tx_type = tx.get('type', 'unknown')
                amount = tx.get('amount', 0)
                timestamp = tx.get('timestamp', 'Unknown')
                message += f"{i}. {tx_type}: ${amount:.2f} - {timestamp}\n"
                
            message += f"\n**Recent Games ({len(games)}):**\n"
            
            for i, game in enumerate(games[:10], 1):
                game_type = game.get('game_type', 'unknown')
                bet_amount = game.get('bet_amount', 0)
                result = game.get('result', 'unknown')
                timestamp = game.get('timestamp', 'Unknown')
                message += f"{i}. {game_type}: ${bet_amount:.2f} - {result} - {timestamp}\n"
            
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Back to User Management", callback_data="admin_users")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif action == "ban":
            # Toggle ban status
            from src.database import ban_user, get_user
            
            user = await get_user(user_id)
            if not user:
                await query.edit_message_text("❌ User not found.")
                return
                
            # Toggle ban status
            new_ban_status = not user.get('is_banned', False)
            updated_user = await ban_user(user_id, new_ban_status)
            
            action_text = "banned" if new_ban_status else "unbanned"
            status_emoji = "🚫" if new_ban_status else "✅"
            
            message = (
                f"{status_emoji} **User {action_text.title()}** {status_emoji}\n\n"
                f"User ID: `{user_id}`\n"
                f"Status: {BANNED if new_ban_status else ACTIVE}\n"
                f"Balance: {format_money(updated_user['balance'])}\n\n"
                f"User has been successfully {action_text}."
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Back to User Management", callback_data="admin_users")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif action == "edit":
            # Show edit user options
            from src.database import get_user
            
            user = await get_user(user_id)
            if not user:
                await query.edit_message_text("❌ User not found.")
                return
                
            message = (
                f"✏️ **Edit User {user_id}** ✏️\n\n"
                f"**Current Info:**\n"
                f"• Balance: {format_money(user['balance'])}\n"
                f"• Status: {🚫 BANNED if user.get(is_banned) else ✅ Active}\n\n"
                f"Select what to edit:"
            )
            
            ban_text = "Unban User" if user.get('is_banned') else "Ban User"
            keyboard = [
                [
                    InlineKeyboardButton("💰 Change Balance", callback_data=f"admin_user_addbalance_{user_id}"),
                    InlineKeyboardButton(f"🚫 {ban_text}", callback_data=f"admin_user_ban_{user_id}")
                ],
                [
                    InlineKeyboardButton("📊 View History", callback_data=f"admin_user_history_{user_id}")
                ],
                [
                    InlineKeyboardButton("🔙 Back to User Management", callback_data="admin_users")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

