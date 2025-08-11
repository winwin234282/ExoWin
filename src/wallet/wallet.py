from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, can_withdraw
from src.utils.formatting import format_money
import os
from dotenv import load_dotenv

load_dotenv()

PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /wallet command"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    message = (
        "💰 Wallet 💰\n\n"
        f"Balance: {format_money(user['balance'])}\n\n"
        "Use the buttons below to manage your wallet."
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Deposit", callback_data="wallet_deposit"),
            InlineKeyboardButton("Withdraw", callback_data="wallet_withdraw")
        ],
        [
            InlineKeyboardButton("Transaction History", callback_data="wallet_history")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data.split("_")
    
    if len(data) < 2:
        return
    
    action = data[1]
    
    if action == "deposit":
        # Show deposit options
        message = (
            "💳 Deposit Funds 💳\n\n"
            "Select an amount to deposit:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("$10", callback_data="wallet_deposit_10"),
                InlineKeyboardButton("$25", callback_data="wallet_deposit_25"),
                InlineKeyboardButton("$50", callback_data="wallet_deposit_50")
            ],
            [
                InlineKeyboardButton("$100", callback_data="wallet_deposit_100"),
                InlineKeyboardButton("$250", callback_data="wallet_deposit_250"),
                InlineKeyboardButton("$500", callback_data="wallet_deposit_500")
            ],
            [
                InlineKeyboardButton("Custom Amount", callback_data="wallet_deposit_custom")
            ],
            [
                InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif action == "deposit" and len(data) > 2:
        # Process deposit
        if data[2] == "custom":
            # Store in context that we're waiting for a custom amount
            context.user_data["wallet_action"] = "deposit_custom"
            
            message = (
                "💰 Custom Deposit 💰\n\n"
                "Please enter the amount you want to deposit (minimum $10):"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("Cancel", callback_data="wallet_deposit")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            try:
                amount = int(data[2])
                await create_payment_invoice(update, context, amount)
            except ValueError:
                await query.edit_message_text("Invalid amount.")
    
    elif action == "withdraw":
        # Show withdrawal options
        user = await get_user(user_id)
        can_withdraw_funds = await can_withdraw(user_id)
        
        if not can_withdraw_funds:
            message = (
                "❌ Withdrawal Not Available ❌\n\n"
                f"Your current balance: {format_money(user['balance'])}\n\n"
                "You need at least $50 to withdraw funds.\n"
                "Keep playing to increase your balance!"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            return
        
        message = (
            "💸 Withdraw Funds 💸\n\n"
            f"Available balance: {format_money(user['balance'])}\n\n"
            "Select an amount to withdraw:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("$50", callback_data="wallet_withdraw_50"),
                InlineKeyboardButton("$100", callback_data="wallet_withdraw_100")
            ],
            [
                InlineKeyboardButton("$250", callback_data="wallet_withdraw_250"),
                InlineKeyboardButton("All Funds", callback_data="wallet_withdraw_all")
            ],
            [
                InlineKeyboardButton("Custom Amount", callback_data="wallet_withdraw_custom")
            ],
            [
                InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif action == "withdraw" and len(data) > 2:
        # Process withdrawal
        user = await get_user(user_id)
        
        if data[2] == "custom":
            # Store in context that we're waiting for a custom amount
            context.user_data["wallet_action"] = "withdraw_custom"
            
            message = (
                "💰 Custom Withdrawal 💰\n\n"
                f"Available balance: {format_money(user['balance'])}\n\n"
                "Please enter the amount you want to withdraw (minimum $50):"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("Cancel", callback_data="wallet_withdraw")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
        elif data[2] == "all":
            # Withdraw all funds
            amount = user["balance"]
            await process_withdrawal(update, context, amount)
        else:
            try:
                amount = int(data[2])
                if user["balance"] < amount:
                    message = (
                        "❌ Insufficient Funds ❌\n\n"
                        f"Your current balance: {format_money(user['balance'])}\n"
                        f"Requested withdrawal: {format_money(amount)}\n\n"
                        "Please select a lower amount."
                    )
                    
                    keyboard = [
                        [
                            InlineKeyboardButton("Back to Withdraw", callback_data="wallet_withdraw")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(message, reply_markup=reply_markup)
                else:
                    await process_withdrawal(update, context, amount)
            except ValueError:
                await query.edit_message_text("Invalid amount.")
    
    elif action == "history":
        # Show transaction history
        message = (
            "📜 Transaction History 📜\n\n"
            "Your recent transactions will be shown here.\n"
            "(Implementation would query the database for transaction history)"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif action == "main":
        # Return to main wallet view
        user = await get_user(user_id)
        
        message = (
            "💰 Wallet 💰\n\n"
            f"Balance: {format_money(user['balance'])}\n\n"
            "Use the buttons below to manage your wallet."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("Deposit", callback_data="wallet_deposit"),
                InlineKeyboardButton("Withdraw", callback_data="wallet_withdraw")
            ],
            [
                InlineKeyboardButton("Transaction History", callback_data="wallet_history")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)

async def wallet_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet action messages"""
    user_id = update.effective_user.id
    
    if "wallet_action" not in context.user_data:
        return False
    
    action = context.user_data["wallet_action"]
    
    if action == "deposit_custom":
        # Process custom deposit amount
        try:
            amount = float(update.message.text.strip())
            
            if amount < 10:
                await update.message.reply_text("Minimum deposit amount is $10.")
                return True
            
            # Convert to cents for payment processing
            cents = int(amount * 100)
            
            # Create payment invoice
            await create_payment_invoice(update, context, cents)
        except ValueError:
            await update.message.reply_text("Invalid amount. Please enter a number.")
        
        # Clear the wallet action
        del context.user_data["wallet_action"]
        return True
    
    elif action == "withdraw_custom":
        # Process custom withdrawal amount
        try:
            amount = float(update.message.text.strip())
            
            if amount < 50:
                await update.message.reply_text("Minimum withdrawal amount is $50.")
                return True
            
            user = await get_user(user_id)
            
            if user["balance"] < amount:
                await update.message.reply_text(
                    f"Insufficient funds. Your balance is {format_money(user['balance'])}."
                )
                return True
            
            # Process withdrawal
            await process_withdrawal(update, context, amount)
        except ValueError:
            await update.message.reply_text("Invalid amount. Please enter a number.")
        
        # Clear the wallet action
        del context.user_data["wallet_action"]
        return True
    
    return False

async def create_payment_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, amount_cents):
    """Create a payment invoice for the user"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    title = "Add funds to your gambling wallet"
    description = f"Add ${amount_cents/100:.2f} to your gambling wallet"
    payload = f"deposit_{user_id}_{amount_cents}"
    currency = "USD"
    prices = [LabeledPrice("Deposit", amount_cents)]
    
    try:
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency=currency,
            prices=prices
        )
        
        # If this is a callback query, answer it
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.answer()
    except Exception as e:
        error_message = (
            "❌ Payment Error ❌\n\n"
            f"Could not create payment invoice: {str(e)}\n\n"
            "Please try again later or contact support."
        )
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_message)
        else:
            await update.message.reply_text(error_message)

async def process_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answer the PreCheckoutQuery"""
    query = update.pre_checkout_query
    
    # Always approve the checkout
    await query.answer(ok=True)

async def process_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payment"""
    payment = update.message.successful_payment
    amount = payment.total_amount / 100  # Convert from cents to dollars
    
    # Extract user_id from payload
    payload_parts = payment.invoice_payload.split('_')
    user_id = int(payload_parts[1])
    
    # Record transaction and update balance
    await record_transaction(user_id, amount, "deposit")
    user = await update_user_balance(user_id, amount)
    
    # Send confirmation message
    message = (
        "✅ Payment Successful ✅\n\n"
        f"Amount: {format_money(amount)}\n"
        f"New balance: {format_money(user['balance'])}\n\n"
        "Thank you for your deposit! Enjoy gambling responsibly."
    )
    
    await update.message.reply_text(message)

async def process_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE, amount):
    """Process a withdrawal request"""
    user_id = update.effective_user.id
    
    # Check if user can withdraw
    if not await can_withdraw(user_id):
        message = (
            "❌ Withdrawal Not Available ❌\n\n"
            "You need at least $50 to withdraw funds."
        )
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    # Deduct amount from user balance
    await update_user_balance(user_id, -amount)
    await record_transaction(user_id, -amount, "withdrawal")
    
    # Get updated user data
    user = await get_user(user_id)
    
    # In a real bot, you would process the withdrawal through your payment provider here
    
    # Send confirmation message
    message = (
        "✅ Withdrawal Request Submitted ✅\n\n"
        f"Amount: {format_money(amount)}\n"
        f"New balance: {format_money(user['balance'])}\n\n"
        "Your withdrawal is being processed and will be completed within 24 hours."
    )
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(message)
    else:
        await update.message.reply_text(message)