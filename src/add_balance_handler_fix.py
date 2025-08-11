    elif action == "add_balance":
        # Add balance to a user
        # Check if target_user_id is already set in context (from user search)
        if "target_user_id" in context.user_data:
            # User-specific add balance (from search results)
            try:
                amount = float(update.message.text.strip())
                target_user_id = context.user_data["target_user_id"]
                
                user = await get_user(target_user_id)
                if not user:
                    await update.message.reply_text(f"❌ User with ID {target_user_id} not found.")
                    del context.user_data["admin_action"]
                    del context.user_data["target_user_id"]
                    return True

                # Add balance to user (can be negative to remove balance)
                await update_user_balance(target_user_id, amount)
                await record_transaction(target_user_id, amount, "admin_add" if amount > 0 else "admin_remove")

                # Get updated user data
                user = await get_user(target_user_id)

                action_text = "Added" if amount > 0 else "Removed"
                message = (
                    f"💰 **Balance {action_text}** 💰\n\n"
                    f"{action_text} {format_money(abs(amount))} {to if amount > 0 else from} user {target_user_id}.\n"
                    f"New balance: {format_money(user['balance'])}"
                )

                keyboard = [
                    [
                        InlineKeyboardButton("🔙 Back to User Management", callback_data="admin_users")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
                
                # Clear context
                del context.user_data["target_user_id"]
                
            except ValueError:
                await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
                return True
        else:
            # Original format: user_id amount
            parts = update.message.text.strip().split()

            if len(parts) != 2:
                await update.message.reply_text("❌ Invalid format. Please use: user_id amount")
                return True

            try:
                target_user_id = int(parts[0])
                amount = float(parts[1])

                if amount <= 0:
                    await update.message.reply_text("❌ Amount must be positive.")
                    return True

                user = await get_user(target_user_id)

                if user:
                    # Add balance to user
                    await update_user_balance(target_user_id, amount)
                    await record_transaction(target_user_id, amount, "admin_add")

                    # Get updated user data
                    user = await get_user(target_user_id)

                    message = (
                        f"💰 **Balance Added** 💰\n\n"
                        f"Added {format_money(amount)} to user {target_user_id}.\n"
                        f"New balance: {format_money(user['balance'])}"
                    )

                    keyboard = [
                        [
                            InlineKeyboardButton("🔙 Back to User Management", callback_data="admin_users")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"❌ User with ID {target_user_id} not found.")
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID or amount.")

        # Clear the admin action
        del context.user_data["admin_action"]
        return True
