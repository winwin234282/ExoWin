import os
import random
import string
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction
from src.utils.formatting import format_money
from src.wallet.nowpayments import (
    get_api_status, 
    get_crypto_price, 
    create_deposit_payment,
    create_deposit_invoice,
    check_payment_status,
    get_minimum_deposit_amount,
    process_withdrawal,
    SUPPORTED_CRYPTOS as API_SUPPORTED_CRYPTOS
)
from dotenv import load_dotenv

load_dotenv()

# Supported cryptocurrencies with their details
SUPPORTED_CRYPTOS = {
    "BTC": {
        "name": "Bitcoin",
        "icon": "₿",
        "min_deposit": 0.0005,
        "min_withdraw": 0.001,
        "fee": 0.0001,
        "decimals": 8
    },
    "ETH": {
        "name": "Ethereum",
        "icon": "Ξ",
        "min_deposit": 0.01,
        "min_withdraw": 0.02,
        "fee": 0.002,
        "decimals": 6
    },
    "USDT": {
        "name": "Tether (ERC20)",
        "icon": "₮",
        "min_deposit": 20,
        "min_withdraw": 30,
        "fee": 5,
        "decimals": 2
    },
    "SOL": {
        "name": "Solana",
        "icon": "SOL",
        "min_deposit": 0.5,
        "min_withdraw": 1,
        "fee": 0.01,
        "decimals": 4
    },
    "LTC": {
        "name": "Litecoin",
        "icon": "Ł",
        "min_deposit": 0.1,
        "min_withdraw": 0.2,
        "fee": 0.01,
        "decimals": 8
    },
    "USDC": {
        "name": "USD Coin",
        "icon": "₵",
        "min_deposit": 20,
        "min_withdraw": 30,
        "fee": 5,
        "decimals": 2
    },
    "BNB": {
        "name": "Binance Coin",
        "icon": "BNB",
        "min_deposit": 0.05,
        "min_withdraw": 0.1,
        "fee": 0.01,
        "decimals": 4
    },
    "XRP": {
        "name": "Ripple",
        "icon": "XRP",
        "min_deposit": 20,
        "min_withdraw": 30,
        "fee": 0.5,
        "decimals": 2
    },
    "ADA": {
        "name": "Cardano",
        "icon": "ADA",
        "min_deposit": 20,
        "min_withdraw": 30,
        "fee": 1,
        "decimals": 2
    },
    "DOGE": {
        "name": "Dogecoin",
        "icon": "Ð",
        "min_deposit": 100,
        "min_withdraw": 200,
        "fee": 5,
        "decimals": 2
    },
    "MATIC": {
        "name": "Polygon",
        "icon": "MATIC",
        "min_deposit": 10,
        "min_withdraw": 20,
        "fee": 1,
        "decimals": 2
    },
    "AVAX": {
        "name": "Avalanche",
        "icon": "AVAX",
        "min_deposit": 0.5,
        "min_withdraw": 1,
        "fee": 0.05,
        "decimals": 4
    },
    "SHIB": {
        "name": "Shiba Inu",
        "icon": "SHIB",
        "min_deposit": 1000000,
        "min_withdraw": 2000000,
        "fee": 100000,
        "decimals": 0
    }
}

# Store active deposit sessions
active_deposits = {}

# Mock exchange rates (in a real bot, you would fetch these from an API)
EXCHANGE_RATES = {
    "BTC": 60000,
    "ETH": 3000,
    "USDT": 1,
    "SOL": 100,
    "LTC": 80,
    "USDC": 1,
    "BNB": 400,
    "XRP": 0.5,
    "ADA": 0.4,
    "DOGE": 0.1,
    "MATIC": 0.8,
    "AVAX": 30,
    "SHIB": 0.00001
}

def format_crypto_amount(amount, crypto):
    """Format crypto amount with appropriate decimals"""
    decimals = SUPPORTED_CRYPTOS[crypto]["decimals"]
    return f"{amount:.{decimals}f} {crypto}"

def generate_wallet_address(crypto):
    """Generate a mock wallet address for the specified cryptocurrency"""
    if crypto == "BTC":
        prefix = "bc1"
        length = 40
    elif crypto == "ETH" or crypto == "USDT" or crypto == "USDC" or crypto == "MATIC":
        prefix = "0x"
        length = 40
    elif crypto == "LTC":
        prefix = "L"
        length = 34
    elif crypto == "BNB":
        prefix = "bnb1"
        length = 38
    elif crypto == "XRP":
        prefix = "r"
        length = 33
    elif crypto == "SOL":
        prefix = ""
        length = 44
    elif crypto == "ADA":
        prefix = "addr1"
        length = 40
    elif crypto == "DOGE":
        prefix = "D"
        length = 34
    elif crypto == "AVAX":
        prefix = "X-avax1"
        length = 40
    elif crypto == "SHIB":
        prefix = "0x"
        length = 40
    else:
        prefix = ""
        length = 40
    
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length - len(prefix)))
    return prefix + random_part

def convert_to_usd(amount, crypto):
    """Convert crypto amount to USD"""
    return amount * EXCHANGE_RATES[crypto]

def convert_from_usd(amount, crypto):
    """Convert USD amount to crypto"""
    return amount / EXCHANGE_RATES[crypto]

async def crypto_deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /deposit command for crypto deposits"""
    # Check if NOWPayments API is operational
    api_status = await get_api_status()
    if not api_status:
        await update.message.reply_text(
            "❌ Crypto deposit service is currently unavailable. Please try again later."
        )
        return
    
    # Show deposit options
    message = (
        "💰 Crypto Deposit Options 💰\n\n"
        "Choose a deposit method:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Select Specific Cryptocurrency", callback_data="crypto_select_currency"),
            InlineKeyboardButton("Multi-Currency Invoice", callback_data="crypto_invoice")
        ],
        [
            InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def crypto_withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /withdraw command for crypto withdrawals"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    # Check if user can withdraw
    if user["balance"] < 50:
        await update.message.reply_text(
            "❌ Withdrawal Not Available ❌\n\n"
            f"Your current balance: {format_money(user['balance'])}\n\n"
            "You need at least $50 to withdraw funds.\n"
            "Keep playing to increase your balance!"
        )
        return
    
    # Show list of supported cryptocurrencies
    message = (
        "💸 Crypto Withdrawal 💸\n\n"
        f"Available balance: {format_money(user['balance'])}\n\n"
        "Select a cryptocurrency for withdrawal:"
    )
    
    # Create keyboard with crypto options
    keyboard = []
    row = []
    
    for i, (symbol, data) in enumerate(SUPPORTED_CRYPTOS.items()):
        if i % 3 == 0 and i > 0:
            keyboard.append(row)
            row = []
        
        row.append(InlineKeyboardButton(
            f"{data['icon']} {data['name']}", 
            callback_data=f"crypto_withdraw_{symbol}"
        ))
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def crypto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crypto wallet callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data.split("_")
    
    if len(data) < 2:
        return
    
    action = data[1]
    
    # Handle select currency option
    if action == "select":
        if data[2] == "currency":
            # Show list of supported cryptocurrencies
            message = (
                "💰 Crypto Deposit 💰\n\n"
                "Select a cryptocurrency to deposit:"
            )
            
            # Create keyboard with crypto options
            keyboard = []
            row = []
            
            # Filter to only include cryptocurrencies supported by NOWPayments API
            supported_cryptos = {k: v for k, v in SUPPORTED_CRYPTOS.items() if k in API_SUPPORTED_CRYPTOS}
            
            for i, (symbol, data) in enumerate(supported_cryptos.items()):
                if i % 3 == 0 and i > 0:
                    keyboard.append(row)
                    row = []
                
                row.append(InlineKeyboardButton(
                    f"{data['icon']} {data['name']}", 
                    callback_data=f"crypto_deposit_{symbol}"
                ))
            
            if row:
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("Back", callback_data="crypto_deposit_options")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            return
    
    # Handle deposit options
    elif action == "deposit":
        if len(data) < 3:
            # Show deposit options
            message = (
                "💰 Crypto Deposit Options 💰\n\n"
                "Choose a deposit method:"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("Select Specific Cryptocurrency", callback_data="crypto_select_currency"),
                    InlineKeyboardButton("Multi-Currency Invoice", callback_data="crypto_invoice")
                ],
                [
                    InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            return
        
        crypto = data[2]
        if crypto in SUPPORTED_CRYPTOS and crypto in API_SUPPORTED_CRYPTOS:
            # Get minimum deposit amount from API
            min_deposit = await get_minimum_deposit_amount(crypto)
            if min_deposit is None:
                min_deposit = SUPPORTED_CRYPTOS[crypto]['min_deposit']
            
            # Show deposit amount selection
            message = (
                f"📥 Deposit {SUPPORTED_CRYPTOS[crypto]['name']} 📥\n\n"
                f"Minimum deposit: {min_deposit} {crypto}\n\n"
                "Enter the USD amount you want to deposit:"
            )
            
            # Store in context that we're waiting for a deposit amount
            context.user_data["crypto_action"] = "deposit_amount"
            context.user_data["crypto_symbol"] = crypto
            
            keyboard = [
                [
                    InlineKeyboardButton("$10", callback_data=f"crypto_amount_{crypto}_10"),
                    InlineKeyboardButton("$25", callback_data=f"crypto_amount_{crypto}_25"),
                    InlineKeyboardButton("$50", callback_data=f"crypto_amount_{crypto}_50")
                ],
                [
                    InlineKeyboardButton("$100", callback_data=f"crypto_amount_{crypto}_100"),
                    InlineKeyboardButton("$250", callback_data=f"crypto_amount_{crypto}_250"),
                    InlineKeyboardButton("$500", callback_data=f"crypto_amount_{crypto}_500")
                ],
                [
                    InlineKeyboardButton("Custom Amount", callback_data=f"crypto_custom_{crypto}")
                ],
                [
                    InlineKeyboardButton("Back", callback_data="crypto_select_currency")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            # Return to crypto selection
            await query.edit_message_text(
                "❌ Selected cryptocurrency is not supported. Please choose another one.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back to Crypto Selection", callback_data="crypto_select_currency")
                ]])
            )
    
    # Handle invoice creation
    elif action == "invoice":
        # Show invoice amount selection
        message = (
            "💰 Multi-Currency Invoice 💰\n\n"
            "This will create an invoice that can be paid with any supported cryptocurrency.\n\n"
            "Select the USD amount for your deposit:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("$10", callback_data="crypto_invoice_amount_10"),
                InlineKeyboardButton("$25", callback_data="crypto_invoice_amount_25"),
                InlineKeyboardButton("$50", callback_data="crypto_invoice_amount_50")
            ],
            [
                InlineKeyboardButton("$100", callback_data="crypto_invoice_amount_100"),
                InlineKeyboardButton("$250", callback_data="crypto_invoice_amount_250"),
                InlineKeyboardButton("$500", callback_data="crypto_invoice_amount_500")
            ],
            [
                InlineKeyboardButton("Custom Amount", callback_data="crypto_invoice_custom")
            ],
            [
                InlineKeyboardButton("Back", callback_data="crypto_deposit_options")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    # Handle invoice amount selection
    elif action == "invoice" and len(data) > 2 and data[2] == "amount" and len(data) > 3:
        try:
            amount_usd = float(data[3])
            
            # Create invoice using NOWPayments API
            invoice = await create_deposit_invoice(user_id, amount_usd)
            
            if invoice and "invoice_url" in invoice:
                message = (
                    f"✅ Invoice Created ✅\n\n"
                    f"Amount: ${amount_usd:.2f}\n\n"
                    f"Please click the button below to open the payment page. You can choose from multiple cryptocurrencies for your payment.\n\n"
                    f"Your deposit will be credited automatically after confirmation."
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("Open Payment Page", url=invoice["invoice_url"])
                    ],
                    [
                        InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(message, reply_markup=reply_markup)
            else:
                await query.edit_message_text(
                    "❌ Failed to create invoice. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Back", callback_data="crypto_deposit_options")
                    ]])
                )
        except ValueError:
            await query.edit_message_text("Invalid amount. Please try again.")
    
    # Handle custom invoice amount
    elif action == "invoice" and len(data) > 2 and data[2] == "custom":
        # Store in context that we're waiting for a custom invoice amount
        context.user_data["crypto_action"] = "invoice_custom"
        
        message = (
            "💰 Custom Invoice Amount 💰\n\n"
            "Please enter the USD amount you want to deposit (minimum $10):"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("Cancel", callback_data="crypto_invoice")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    # Handle specific crypto amount selection
    elif action == "amount" and len(data) > 3:
        crypto = data[2]
        try:
            amount_usd = float(data[3])
            
            # Create payment using NOWPayments API
            payment = await create_deposit_payment(user_id, amount_usd, crypto)
            
            if payment and "pay_address" in payment:
                # Calculate crypto amount based on the exchange rate
                crypto_amount = payment.get("pay_amount", 0)
                
                message = (
                    f"📥 {SUPPORTED_CRYPTOS[crypto]['name']} Deposit 📥\n\n"
                    f"Amount: {crypto_amount} {crypto}\n"
                    f"USD Value: ${amount_usd:.2f}\n\n"
                    f"Please send exactly {crypto_amount} {crypto} to the following address:\n\n"
                    f"`{payment['pay_address']}`\n\n"
                    "⚠️ Send only on the correct network! ⚠️\n\n"
                    f"Payment ID: {payment['payment_id']}\n\n"
                    "Your deposit will be credited automatically after confirmation.\n"
                    "This usually takes 10-30 minutes depending on the network."
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("Check Payment Status", callback_data=f"crypto_check_{payment['payment_id']}")
                    ],
                    [
                        InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await query.edit_message_text(
                    "❌ Failed to create payment. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Back", callback_data=f"crypto_deposit_{crypto}")
                    ]])
                )
        except ValueError:
            await query.edit_message_text("Invalid amount. Please try again.")
    
    # Handle custom amount for specific crypto
    elif action == "custom" and len(data) > 2:
        crypto = data[2]
        
        # Store in context that we're waiting for a custom amount
        context.user_data["crypto_action"] = "deposit_custom"
        context.user_data["crypto_symbol"] = crypto
        
        message = (
            f"💰 Custom {SUPPORTED_CRYPTOS[crypto]['name']} Deposit 💰\n\n"
            f"Please enter the USD amount you want to deposit (minimum $10):"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("Cancel", callback_data=f"crypto_deposit_{crypto}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    # Handle payment status check
    elif action == "check" and len(data) > 2:
        payment_id = data[2]
        
        # Check payment status using NOWPayments API
        payment_status = await check_payment_status(payment_id)
        
        if payment_status:
            status = payment_status.get("payment_status", "waiting")
            
            if status in ["confirmed", "finished", "sending", "partially_paid"]:
                message = (
                    "✅ Payment Confirmed ✅\n\n"
                    "Your deposit has been confirmed and will be credited to your account shortly.\n\n"
                    "Thank you for your deposit!"
                )
            elif status in ["waiting", "confirming"]:
                message = (
                    "⏳ Payment Pending ⏳\n\n"
                    "We're waiting for your payment to be confirmed on the blockchain.\n"
                    "This usually takes 10-30 minutes depending on the network.\n\n"
                    "Please check back later."
                )
            else:
                message = (
                    f"ℹ️ Payment Status: {status.capitalize()} ℹ️\n\n"
                    "If you've already sent the payment, please wait for it to be confirmed.\n"
                    "If you haven't sent it yet, please follow the instructions in the previous message.\n\n"
                    "For assistance, please contact support."
                )
            
            keyboard = [
                [
                    InlineKeyboardButton("Check Again", callback_data=f"crypto_check_{payment_id}")
                ],
                [
                    InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await query.edit_message_text(
                "❌ Failed to check payment status. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                ]])
            )
    
    # Handle withdraw cryptocurrency selection
    elif action == "withdraw":
        if len(data) < 3:
            # Show list of supported cryptocurrencies for withdrawal
            user = await get_user(user_id)
            
            # Check if user can withdraw
            if user["balance"] < 50:
                await query.edit_message_text(
                    "❌ Withdrawal Not Available ❌\n\n"
                    f"Your current balance: {format_money(user['balance'])}\n\n"
                    "You need at least $50 to withdraw funds.\n"
                    "Keep playing to increase your balance!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                    ]])
                )
                return
            
            message = (
                "💸 Crypto Withdrawal 💸\n\n"
                f"Available balance: {format_money(user['balance'])}\n\n"
                "Select a cryptocurrency for withdrawal:"
            )
            
            # Create keyboard with crypto options
            keyboard = []
            row = []
            
            # Filter to only include cryptocurrencies supported by NOWPayments API
            supported_cryptos = {k: v for k, v in SUPPORTED_CRYPTOS.items() if k in API_SUPPORTED_CRYPTOS}
            
            for i, (symbol, data) in enumerate(supported_cryptos.items()):
                if i % 3 == 0 and i > 0:
                    keyboard.append(row)
                    row = []
                
                row.append(InlineKeyboardButton(
                    f"{data['icon']} {data['name']}", 
                    callback_data=f"crypto_withdraw_{symbol}"
                ))
            
            if row:
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            return
        
        crypto = data[2]
        if crypto in SUPPORTED_CRYPTOS and crypto in API_SUPPORTED_CRYPTOS:
            user = await get_user(user_id)
            
            # Show withdrawal form
            message = (
                f"📤 Withdraw {SUPPORTED_CRYPTOS[crypto]['name']} 📤\n\n"
                f"Available balance: {format_money(user['balance'])}\n\n"
                f"Please enter your {crypto} wallet address and the USD amount you want to withdraw in the following format:\n\n"
                f"address,amount\n\n"
                f"Example: {generate_wallet_address(crypto)},50\n\n"
                f"Note: Minimum withdrawal is $50 and a network fee will be deducted from the withdrawal amount."
            )
            
            # Store in context that we're waiting for withdrawal info
            context.user_data["crypto_action"] = "withdraw"
            context.user_data["crypto_symbol"] = crypto
            
            keyboard = [
                [
                    InlineKeyboardButton("Cancel", callback_data="wallet_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            # Return to crypto selection
            await query.edit_message_text(
                "❌ Selected cryptocurrency is not supported for withdrawals. Please choose another one.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back", callback_data="crypto_withdraw")
                ]])
            )

async def crypto_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crypto wallet action messages"""
    user_id = update.effective_user.id
    
    if "crypto_action" not in context.user_data:
        return False
    
    action = context.user_data["crypto_action"]
    
    if action == "deposit_custom":
        # Process custom deposit amount for specific cryptocurrency
        crypto = context.user_data["crypto_symbol"]
        
        try:
            amount_usd = float(update.message.text.strip())
            
            if amount_usd < 10:
                await update.message.reply_text(
                    "Minimum deposit amount is $10."
                )
                return True
            
            # Create payment using NOWPayments API
            payment = await create_deposit_payment(user_id, amount_usd, crypto)
            
            if payment and "pay_address" in payment:
                # Get crypto amount from payment
                crypto_amount = payment.get("pay_amount", 0)
                
                # Show deposit instructions
                message = (
                    f"📥 {SUPPORTED_CRYPTOS[crypto]['name']} Deposit 📥\n\n"
                    f"Amount: {crypto_amount} {crypto}\n"
                    f"USD Value: ${amount_usd:.2f}\n\n"
                    f"Please send exactly {crypto_amount} {crypto} to the following address:\n\n"
                    f"`{payment['pay_address']}`\n\n"
                    "⚠️ Send only on the correct network! ⚠️\n\n"
                    f"Payment ID: {payment['payment_id']}\n\n"
                    "Your deposit will be credited automatically after confirmation.\n"
                    "This usually takes 10-30 minutes depending on the network."
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("Check Payment Status", callback_data=f"crypto_check_{payment['payment_id']}")
                    ],
                    [
                        InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await update.message.reply_text(
                    "❌ Failed to create payment. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                    ]])
                )
        
        except ValueError:
            await update.message.reply_text("Invalid amount. Please enter a number.")
        
        # Clear the crypto action
        del context.user_data["crypto_action"]
        del context.user_data["crypto_symbol"]
        return True
    
    elif action == "invoice_custom":
        # Process custom invoice amount
        try:
            amount_usd = float(update.message.text.strip())
            
            if amount_usd < 10:
                await update.message.reply_text(
                    "Minimum deposit amount is $10."
                )
                return True
            
            # Create invoice using NOWPayments API
            invoice = await create_deposit_invoice(user_id, amount_usd)
            
            if invoice and "invoice_url" in invoice:
                message = (
                    f"✅ Invoice Created ✅\n\n"
                    f"Amount: ${amount_usd:.2f}\n\n"
                    f"Please click the button below to open the payment page. You can choose from multiple cryptocurrencies for your payment.\n\n"
                    f"Your deposit will be credited automatically after confirmation."
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("Open Payment Page", url=invoice["invoice_url"])
                    ],
                    [
                        InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(
                    "❌ Failed to create invoice. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Back to Wallet", callback_data="wallet_main")
                    ]])
                )
        
        except ValueError:
            await update.message.reply_text("Invalid amount. Please enter a number.")
        
        # Clear the crypto action
        del context.user_data["crypto_action"]
        return True
    
    elif action == "withdraw":
        # Process withdrawal request
        crypto = context.user_data["crypto_symbol"]
        
        try:
            # Parse the input for address and amount
            input_text = update.message.text.strip()
            
            if "," not in input_text:
                await update.message.reply_text(
                    "Invalid format. Please enter your withdrawal information in the format: address,amount"
                )
                return True
            
            address, amount_str = input_text.split(",", 1)
            address = address.strip()
            amount_usd = float(amount_str.strip())
            
            # Validate address (in a real implementation, you would do more thorough validation)
            if len(address) < 10:
                await update.message.reply_text("Invalid wallet address.")
                return True
            
            # Get user balance
            user = await get_user(user_id)
            
            # Check minimum withdrawal
            if amount_usd < 50:
                await update.message.reply_text(
                    "Minimum withdrawal amount is $50."
                )
                return True
            
            # Check if user has enough balance
            if user["balance"] < amount_usd:
                await update.message.reply_text(
                    f"Insufficient funds. Your balance is {format_money(user['balance'])}."
                )
                return True
            
            # Get current exchange rate
            rate = await get_crypto_price(crypto)
            if not rate:
                # Fallback to our static rates if API fails
                rate = 1 / EXCHANGE_RATES[crypto]
            
            # Calculate crypto amount
            crypto_amount = amount_usd * rate
            
            # Calculate fee (in a real implementation, get this from the API)
            fee_crypto = SUPPORTED_CRYPTOS[crypto]["fee"]
            net_amount_crypto = crypto_amount - fee_crypto
            
            if net_amount_crypto <= 0:
                await update.message.reply_text(
                    f"Withdrawal amount is too small to cover the fee of {fee_crypto} {crypto}."
                )
                return True
            
            # Process withdrawal through NOWPayments API
            withdrawal = await process_withdrawal(user_id, address, crypto, net_amount_crypto)
            
            if withdrawal:
                # Deduct from user balance
                await update_user_balance(user_id, -amount_usd)
                await record_transaction(
                    user_id, 
                    -amount_usd, 
                    "withdrawal", 
                    details={
                        "crypto": crypto,
                        "amount_crypto": crypto_amount,
                        "fee_crypto": fee_crypto,
                        "net_amount_crypto": net_amount_crypto,
                        "address": address,
                        "withdrawal_id": withdrawal.get("id", "unknown")
                    }
                )
                
                # Show confirmation
                message = (
                    f"✅ Withdrawal Request Submitted ✅\n\n"
                    f"Cryptocurrency: {SUPPORTED_CRYPTOS[crypto]['name']}\n"
                    f"Amount: {crypto_amount:.8f} {crypto}\n"
                    f"Fee: {fee_crypto} {crypto}\n"
                    f"Net Amount: {net_amount_crypto:.8f} {crypto}\n"
                    f"Address: {address}\n\n"
                    f"USD Value: {format_money(amount_usd)}\n"
                    f"New Balance: {format_money(user['balance'] - amount_usd)}\n\n"
                    "Your withdrawal is being processed and will be completed within 24 hours."
                )
                
                await update.message.reply_text(message)
            else:
                await update.message.reply_text(
                    "❌ Failed to process withdrawal. Please try again later or contact support."
                )
        
        except ValueError:
            await update.message.reply_text("Invalid amount. Please enter a number.")
        except Exception as e:
            await update.message.reply_text(f"An error occurred: {str(e)}")
        
        # Clear the crypto action
        del context.user_data["crypto_action"]
        del context.user_data["crypto_symbol"]
        return True
    
    return False

async def simulate_deposit_confirmation(context, deposit_id):
    """Simulate a deposit confirmation (for demo purposes)"""
    if deposit_id not in active_deposits or active_deposits[deposit_id]["status"] != "pending":
        return
    
    deposit = active_deposits[deposit_id]
    user_id = deposit["user_id"]
    usd_amount = deposit["usd_amount"]
    crypto = deposit["crypto"]
    
    # Mark deposit as confirmed
    deposit["status"] = "confirmed"
    
    # Add funds to user's balance
    await update_user_balance(user_id, usd_amount)
    await record_transaction(user_id, usd_amount, "crypto_deposit")
    
    # Get updated user data
    user = await get_user(user_id)
    
    # Send confirmation message
    message = (
        "🎉 Deposit Confirmed 🎉\n\n"
        f"Your {format_crypto_amount(deposit['amount'], crypto)} deposit has been confirmed!\n\n"
        f"USD Value: {format_money(usd_amount)}\n"
        f"New balance: {format_money(user['balance'])}\n\n"
        "Thank you for your deposit! Enjoy gambling responsibly."
    )
    
    try:
        await context.bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        print(f"Error sending deposit confirmation: {e}")