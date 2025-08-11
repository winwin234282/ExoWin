import os
import json
import random
import string
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

load_dotenv()

# In a production environment, you would integrate with actual crypto payment providers
# For this implementation, we'll simulate the crypto payment process

# Supported cryptocurrencies with their details
SUPPORTED_CRYPTOCURRENCIES = {
    "BTC": {
        "name": "Bitcoin",
        "symbol": "BTC",
        "icon": "₿",
        "min_deposit": 0.0005,
        "min_withdrawal": 0.001,
        "withdrawal_fee": 0.0001,
        "exchange_rate": 60000.0,  # USD per 1 BTC (would be fetched from an API in production)
        "confirmations_required": 2,
        "main_wallet": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"  # Example wallet address
    },
    "ETH": {
        "name": "Ethereum",
        "symbol": "ETH",
        "icon": "Ξ",
        "min_deposit": 0.01,
        "min_withdrawal": 0.02,
        "withdrawal_fee": 0.002,
        "exchange_rate": 3000.0,  # USD per 1 ETH
        "confirmations_required": 12,
        "main_wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    },
    "USDT": {
        "name": "Tether (ERC-20)",
        "symbol": "USDT",
        "icon": "₮",
        "min_deposit": 10.0,
        "min_withdrawal": 20.0,
        "withdrawal_fee": 5.0,
        "exchange_rate": 1.0,  # USD per 1 USDT
        "confirmations_required": 12,
        "main_wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    },
    "SOL": {
        "name": "Solana",
        "symbol": "SOL",
        "icon": "◎",
        "min_deposit": 0.2,
        "min_withdrawal": 0.5,
        "withdrawal_fee": 0.01,
        "exchange_rate": 100.0,  # USD per 1 SOL
        "confirmations_required": 32,
        "main_wallet": "9ZNTfG4NyQgxy2SWjSiQoUyBPEvXT2xo7fKc5hPYYJ7b"
    },
    "LTC": {
        "name": "Litecoin",
        "symbol": "LTC",
        "icon": "Ł",
        "min_deposit": 0.1,
        "min_withdrawal": 0.2,
        "withdrawal_fee": 0.01,
        "exchange_rate": 80.0,  # USD per 1 LTC
        "confirmations_required": 6,
        "main_wallet": "LTCmainwallet123456789abcdefghijklmnopqrstuvwxyz"
    },
    "USDC": {
        "name": "USD Coin",
        "symbol": "USDC",
        "icon": "₵",
        "min_deposit": 10.0,
        "min_withdrawal": 20.0,
        "withdrawal_fee": 5.0,
        "exchange_rate": 1.0,  # USD per 1 USDC
        "confirmations_required": 12,
        "main_wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    },
    "BNB": {
        "name": "Binance Coin",
        "symbol": "BNB",
        "icon": "BNB",
        "min_deposit": 0.05,
        "min_withdrawal": 0.1,
        "withdrawal_fee": 0.01,
        "exchange_rate": 400.0,  # USD per 1 BNB
        "confirmations_required": 15,
        "main_wallet": "bnb1jxfh2g85q3v0tdq56fnevx6xcxtcnhtsmcu64m"
    },
    "ADA": {
        "name": "Cardano",
        "symbol": "ADA",
        "icon": "₳",
        "min_deposit": 10.0,
        "min_withdrawal": 20.0,
        "withdrawal_fee": 1.0,
        "exchange_rate": 1.2,  # USD per 1 ADA
        "confirmations_required": 20,
        "main_wallet": "addr1qxck8h7v6ydz5r9lyxaprg7acxgpr5s9xsve4h9h7m3g2cw5a7hr3gf3k0uxmjjwpsr9d5d6z3qzlhtz4qcmr9pyjdsp9yykz"
    },
    "XRP": {
        "name": "Ripple",
        "symbol": "XRP",
        "icon": "✕",
        "min_deposit": 20.0,
        "min_withdrawal": 30.0,
        "withdrawal_fee": 0.25,
        "exchange_rate": 0.8,  # USD per 1 XRP
        "confirmations_required": 1,
        "main_wallet": "rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh"
    },
    "DOGE": {
        "name": "Dogecoin",
        "symbol": "DOGE",
        "icon": "Ð",
        "min_deposit": 50.0,
        "min_withdrawal": 100.0,
        "withdrawal_fee": 5.0,
        "exchange_rate": 0.15,  # USD per 1 DOGE
        "confirmations_required": 6,
        "main_wallet": "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
    },
    "SHIB": {
        "name": "Shiba Inu",
        "symbol": "SHIB",
        "icon": "SHIB",
        "min_deposit": 1000000.0,
        "min_withdrawal": 2000000.0,
        "withdrawal_fee": 100000.0,
        "exchange_rate": 0.00002,  # USD per 1 SHIB
        "confirmations_required": 12,
        "main_wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    }
}

# Store active deposits and withdrawals
active_deposits = {}
active_withdrawals = {}

# Simulate wallet address generation
def generate_wallet_address(crypto):
    """Generate a simulated wallet address for the given cryptocurrency"""
    if crypto == "BTC":
        prefix = "bc1q"
        length = 40
    elif crypto in ["ETH", "USDT", "USDC", "SHIB"]:
        prefix = "0x"
        length = 40
    elif crypto == "LTC":
        prefix = "L"
        length = 34
    elif crypto == "BNB":
        prefix = "bnb1"
        length = 38
    elif crypto == "SOL":
        prefix = ""
        length = 44
    elif crypto == "ADA":
        prefix = "addr1"
        length = 98
    elif crypto == "XRP":
        prefix = "r"
        length = 33
    elif crypto == "DOGE":
        prefix = "D"
        length = 34
    else:
        prefix = ""
        length = 40
    
    # Generate random characters
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length - len(prefix)))
    
    return prefix + random_part

async def show_crypto_deposit_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cryptocurrency deposit options"""
    message = (
        "💰 Crypto Deposit 💰\n\n"
        "Select a cryptocurrency to deposit:"
    )
    
    # Create keyboard with crypto options
    keyboard = []
    row = []
    
    for i, (symbol, crypto) in enumerate(SUPPORTED_CRYPTOCURRENCIES.items()):
        # Create rows with 2 buttons each
        row.append(InlineKeyboardButton(
            f"{crypto['icon']} {crypto['name']}",
            callback_data=f"crypto_deposit_{symbol}"
        ))
        
        if len(row) == 2 or i == len(SUPPORTED_CRYPTOCURRENCIES) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

async def show_crypto_withdrawal_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cryptocurrency withdrawal options"""
    message = (
        "💸 Crypto Withdrawal 💸\n\n"
        "Select a cryptocurrency to withdraw:"
    )
    
    # Create keyboard with crypto options
    keyboard = []
    row = []
    
    for i, (symbol, crypto) in enumerate(SUPPORTED_CRYPTOCURRENCIES.items()):
        # Create rows with 2 buttons each
        row.append(InlineKeyboardButton(
            f"{crypto['icon']} {crypto['name']}",
            callback_data=f"crypto_withdraw_{symbol}"
        ))
        
        if len(row) == 2 or i == len(SUPPORTED_CRYPTOCURRENCIES) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

async def handle_crypto_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, crypto_symbol):
    """Handle cryptocurrency deposit"""
    user_id = update.effective_user.id
    
    if crypto_symbol not in SUPPORTED_CRYPTOCURRENCIES:
        message = "Invalid cryptocurrency selected."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    crypto = SUPPORTED_CRYPTOCURRENCIES[crypto_symbol]
    
    # Store in context that we're waiting for a deposit amount
    context.user_data["crypto_action"] = "deposit_amount"
    context.user_data["crypto_symbol"] = crypto_symbol
    
    min_deposit_usd = crypto["min_deposit"] * crypto["exchange_rate"]
    
    message = (
        f"💰 {crypto['name']} Deposit 💰\n\n"
        f"Minimum deposit: {crypto['min_deposit']} {crypto_symbol} (${min_deposit_usd:.2f})\n\n"
        f"Please enter the amount in {crypto_symbol} you want to deposit:"
    )
    
    keyboard = [
        [InlineKeyboardButton("Cancel", callback_data="crypto_deposit_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

async def handle_crypto_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE, crypto_symbol):
    """Handle cryptocurrency withdrawal"""
    from src.database import get_user, can_withdraw
    
    user_id = update.effective_user.id
    
    # Check if user can withdraw
    if not await can_withdraw(user_id):
        message = (
            "❌ Withdrawal Not Available ❌\n\n"
            "You need at least $50 in your balance to withdraw funds."
        )
        
        keyboard = [
            [InlineKeyboardButton("Back to Crypto Options", callback_data="crypto_withdraw")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
        return
    
    if crypto_symbol not in SUPPORTED_CRYPTOCURRENCIES:
        message = "Invalid cryptocurrency selected."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    crypto = SUPPORTED_CRYPTOCURRENCIES[crypto_symbol]
    user = await get_user(user_id)
    
    # Store in context that we're waiting for a withdrawal amount and address
    context.user_data["crypto_action"] = "withdraw_amount"
    context.user_data["crypto_symbol"] = crypto_symbol
    
    # Calculate maximum withdrawal amount in crypto
    max_withdrawal_crypto = user["balance"] / crypto["exchange_rate"]
    min_withdrawal_usd = crypto["min_withdrawal"] * crypto["exchange_rate"]
    
    message = (
        f"💸 {crypto['name']} Withdrawal 💸\n\n"
        f"Your balance: ${user['balance']:.2f}\n"
        f"Maximum withdrawal: {max_withdrawal_crypto:.8f} {crypto_symbol}\n"
        f"Minimum withdrawal: {crypto['min_withdrawal']} {crypto_symbol} (${min_withdrawal_usd:.2f})\n"
        f"Withdrawal fee: {crypto['withdrawal_fee']} {crypto_symbol}\n\n"
        f"Please enter the amount in {crypto_symbol} you want to withdraw:"
    )
    
    keyboard = [
        [InlineKeyboardButton("Cancel", callback_data="crypto_withdraw_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

async def process_crypto_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process cryptocurrency deposit amount"""
    user_id = update.effective_user.id
    
    if "crypto_symbol" not in context.user_data:
        await update.message.reply_text("An error occurred. Please try again.")
        return False
    
    crypto_symbol = context.user_data["crypto_symbol"]
    crypto = SUPPORTED_CRYPTOCURRENCIES[crypto_symbol]
    
    try:
        amount = float(update.message.text.strip())
        
        # Check minimum deposit
        if amount < crypto["min_deposit"]:
            await update.message.reply_text(
                f"Minimum deposit amount is {crypto['min_deposit']} {crypto_symbol}. Please try again."
            )
            return True
        
        # Generate a unique deposit address
        deposit_address = generate_wallet_address(crypto_symbol)
        
        # Calculate USD value
        usd_value = amount * crypto["exchange_rate"]
        
        # Create a deposit record
        deposit_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        active_deposits[deposit_id] = {
            "user_id": user_id,
            "crypto_symbol": crypto_symbol,
            "amount": amount,
            "usd_value": usd_value,
            "address": deposit_address,
            "status": "pending",
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=24)
        }
        
        # Store the deposit ID in user data
        context.user_data["deposit_id"] = deposit_id
        
        # Create QR code placeholder (in a real implementation, generate an actual QR code)
        qr_code_placeholder = f"[QR Code for {deposit_address}]"
        
        message = (
            f"📥 {crypto['name']} Deposit 📥\n\n"
            f"Amount: {amount} {crypto_symbol} (${usd_value:.2f})\n"
            f"Deposit Address: `{deposit_address}`\n\n"
            f"{qr_code_placeholder}\n\n"
            f"⚠️ Important Instructions ⚠️\n"
            f"1. Send EXACTLY {amount} {crypto_symbol} to the address above\n"
            f"2. Only send {crypto_symbol} to this address\n"
            f"3. This address is valid for 24 hours\n"
            f"4. Requires {crypto['confirmations_required']} confirmations\n\n"
            f"Your deposit will be credited automatically once confirmed."
        )
        
        keyboard = [
            [InlineKeyboardButton("I've Made the Payment", callback_data=f"crypto_deposit_confirm_{deposit_id}")],
            [InlineKeyboardButton("Cancel Deposit", callback_data=f"crypto_deposit_cancel_{deposit_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        
        # Simulate deposit confirmation after a delay (in a real implementation, you'd monitor the blockchain)
        context.job_queue.run_once(
            lambda _: asyncio.create_task(simulate_deposit_confirmation(context, deposit_id)),
            random.randint(60, 180)  # Random delay between 1-3 minutes
        )
        
        # Clear the crypto action
        del context.user_data["crypto_action"]
        del context.user_data["crypto_symbol"]
        
        return True
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a number.")
        return True

async def process_crypto_withdrawal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process cryptocurrency withdrawal amount"""
    from src.database import get_user
    
    user_id = update.effective_user.id
    
    if "crypto_symbol" not in context.user_data:
        await update.message.reply_text("An error occurred. Please try again.")
        return False
    
    crypto_symbol = context.user_data["crypto_symbol"]
    crypto = SUPPORTED_CRYPTOCURRENCIES[crypto_symbol]
    user = await get_user(user_id)
    
    try:
        amount = float(update.message.text.strip())
        
        # Check minimum withdrawal
        if amount < crypto["min_withdrawal"]:
            await update.message.reply_text(
                f"Minimum withdrawal amount is {crypto['min_withdrawal']} {crypto_symbol}. Please try again."
            )
            return True
        
        # Calculate USD value
        usd_value = amount * crypto["exchange_rate"]
        
        # Check if user has enough balance
        if user["balance"] < usd_value:
            await update.message.reply_text(
                f"Insufficient balance. Your balance is ${user['balance']:.2f}, "
                f"but you need ${usd_value:.2f} for this withdrawal."
            )
            return True
        
        # Store withdrawal amount and update action
        context.user_data["withdrawal_amount"] = amount
        context.user_data["crypto_action"] = "withdraw_address"
        
        message = (
            f"💸 {crypto['name']} Withdrawal 💸\n\n"
            f"Amount: {amount} {crypto_symbol} (${usd_value:.2f})\n"
            f"Fee: {crypto['withdrawal_fee']} {crypto_symbol}\n"
            f"You will receive: {amount - crypto['withdrawal_fee']} {crypto_symbol}\n\n"
            f"Please enter your {crypto['name']} wallet address:"
        )
        
        keyboard = [
            [InlineKeyboardButton("Cancel", callback_data="crypto_withdraw_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        return True
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a number.")
        return True

async def process_crypto_withdrawal_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process cryptocurrency withdrawal address"""
    from src.database import get_user, update_user_balance, record_transaction
    
    user_id = update.effective_user.id
    
    if "crypto_symbol" not in context.user_data or "withdrawal_amount" not in context.user_data:
        await update.message.reply_text("An error occurred. Please try again.")
        return False
    
    crypto_symbol = context.user_data["crypto_symbol"]
    amount = context.user_data["withdrawal_amount"]
    crypto = SUPPORTED_CRYPTOCURRENCIES[crypto_symbol]
    
    # Get the withdrawal address
    withdrawal_address = update.message.text.strip()
    
    # Validate address format (basic validation, would be more comprehensive in production)
    valid_address = False
    
    if crypto_symbol == "BTC" and withdrawal_address.startswith(("1", "3", "bc1")):
        valid_address = True
    elif crypto_symbol in ["ETH", "USDT", "USDC", "SHIB"] and withdrawal_address.startswith("0x"):
        valid_address = True
    elif crypto_symbol == "BNB" and withdrawal_address.startswith("bnb"):
        valid_address = True
    elif crypto_symbol == "SOL" and len(withdrawal_address) >= 32:
        valid_address = True
    elif crypto_symbol == "ADA" and withdrawal_address.startswith("addr"):
        valid_address = True
    elif crypto_symbol == "XRP" and withdrawal_address.startswith("r"):
        valid_address = True
    elif crypto_symbol == "DOGE" and withdrawal_address.startswith("D"):
        valid_address = True
    
    if not valid_address:
        await update.message.reply_text(
            f"Invalid {crypto['name']} address format. Please check and try again."
        )
        return True
    
    # Calculate USD value
    usd_value = amount * crypto["exchange_rate"]
    
    # Create a withdrawal record
    withdrawal_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    active_withdrawals[withdrawal_id] = {
        "user_id": user_id,
        "crypto_symbol": crypto_symbol,
        "amount": amount,
        "fee": crypto["withdrawal_fee"],
        "net_amount": amount - crypto["withdrawal_fee"],
        "usd_value": usd_value,
        "address": withdrawal_address,
        "status": "pending",
        "created_at": datetime.now()
    }
    
    # Deduct from user balance
    await update_user_balance(user_id, -usd_value)
    await record_transaction(user_id, -usd_value, "crypto_withdrawal")
    
    # Get updated user data
    user = await get_user(user_id)
    
    message = (
        f"📤 {crypto['name']} Withdrawal Submitted 📤\n\n"
        f"Amount: {amount} {crypto_symbol} (${usd_value:.2f})\n"
        f"Fee: {crypto['withdrawal_fee']} {crypto_symbol}\n"
        f"You will receive: {amount - crypto['withdrawal_fee']} {crypto_symbol}\n"
        f"To address: {withdrawal_address}\n\n"
        f"Status: Pending\n"
        f"Your withdrawal is being processed and will be sent shortly.\n"
        f"Your new balance: ${user['balance']:.2f}"
    )
    
    keyboard = [
        [InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)
    
    # Simulate withdrawal processing after a delay
    context.job_queue.run_once(
        lambda _: asyncio.create_task(simulate_withdrawal_processing(context, withdrawal_id)),
        random.randint(60, 180)  # Random delay between 1-3 minutes
    )
    
    # Clear the crypto action
    del context.user_data["crypto_action"]
    del context.user_data["crypto_symbol"]
    del context.user_data["withdrawal_amount"]
    
    return True

async def simulate_deposit_confirmation(context, deposit_id):
    """Simulate cryptocurrency deposit confirmation"""
    from src.database import get_user, update_user_balance, record_transaction
    
    if deposit_id not in active_deposits:
        return
    
    deposit = active_deposits[deposit_id]
    user_id = deposit["user_id"]
    
    # Update deposit status
    deposit["status"] = "confirmed"
    
    # Add funds to user balance
    await update_user_balance(user_id, deposit["usd_value"])
    await record_transaction(user_id, deposit["usd_value"], "crypto_deposit")
    
    # Get updated user data
    user = await get_user(user_id)
    
    # Send confirmation message
    message = (
        f"✅ Deposit Confirmed ✅\n\n"
        f"Your {deposit['crypto_symbol']} deposit of {deposit['amount']} {deposit['crypto_symbol']} "
        f"(${deposit['usd_value']:.2f}) has been confirmed and credited to your account.\n\n"
        f"New balance: ${user['balance']:.2f}"
    )
    
    try:
        await context.bot.send_message(user_id, message)
    except Exception as e:
        print(f"Error sending deposit confirmation: {e}")

async def simulate_withdrawal_processing(context, withdrawal_id):
    """Simulate cryptocurrency withdrawal processing"""
    if withdrawal_id not in active_withdrawals:
        return
    
    withdrawal = active_withdrawals[withdrawal_id]
    user_id = withdrawal["user_id"]
    
    # Update withdrawal status
    withdrawal["status"] = "completed"
    withdrawal["txid"] = ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))
    
    # Send confirmation message
    message = (
        f"✅ Withdrawal Completed ✅\n\n"
        f"Your {withdrawal['crypto_symbol']} withdrawal of {withdrawal['amount']} {withdrawal['crypto_symbol']} "
        f"(${withdrawal['usd_value']:.2f}) has been processed.\n\n"
        f"Amount sent: {withdrawal['net_amount']} {withdrawal['crypto_symbol']}\n"
        f"To address: {withdrawal['address']}\n"
        f"Transaction ID: {withdrawal['txid']}\n\n"
        f"Thank you for using our service!"
    )
    
    try:
        await context.bot.send_message(user_id, message)
    except Exception as e:
        print(f"Error sending withdrawal confirmation: {e}")

async def handle_crypto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cryptocurrency-related callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    if len(data) < 3:
        return False
    
    action = data[1]
    
    if action == "deposit":
        if data[2] == "cancel":
            # Cancel deposit
            if len(data) > 3:
                deposit_id = data[3]
                if deposit_id in active_deposits:
                    active_deposits[deposit_id]["status"] = "cancelled"
            
            # Return to crypto deposit options
            await show_crypto_deposit_options(update, context)
            return True
        elif data[2] == "confirm":
            # User confirms they've made the payment
            if len(data) > 3:
                deposit_id = data[3]
                if deposit_id in active_deposits:
                    message = (
                        "🔄 Payment Confirmation 🔄\n\n"
                        "Thank you for confirming your payment.\n"
                        "We are now waiting for blockchain confirmation.\n"
                        "This usually takes a few minutes.\n\n"
                        "You will be notified once your deposit is confirmed."
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(message, reply_markup=reply_markup)
                    return True
            
            await query.edit_message_text("An error occurred. Please try again.")
            return True
        else:
            # Handle specific cryptocurrency deposit
            crypto_symbol = data[2]
            await handle_crypto_deposit(update, context, crypto_symbol)
            return True
    
    elif action == "withdraw":
        if data[2] == "cancel":
            # Cancel withdrawal
            # Return to crypto withdrawal options
            await show_crypto_withdrawal_options(update, context)
            return True
        else:
            # Handle specific cryptocurrency withdrawal
            crypto_symbol = data[2]
            await handle_crypto_withdrawal(update, context, crypto_symbol)
            return True
    
    return False

async def crypto_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cryptocurrency-related messages"""
    if "crypto_action" not in context.user_data:
        return False
    
    action = context.user_data["crypto_action"]
    
    if action == "deposit_amount":
        return await process_crypto_deposit_amount(update, context)
    elif action == "withdraw_amount":
        return await process_crypto_withdrawal_amount(update, context)
    elif action == "withdraw_address":
        return await process_crypto_withdrawal_address(update, context)
    
    return False