from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user
from src.utils.formatting import format_money
from src.wallet.nowpayments import create_deposit_payment, create_deposit_invoice

def format_crypto_address(address, crypto_currency):
    """Format cryptocurrency address for better display"""
    if not address:
        return "Address not available"
    
    # For long addresses, show first 8 and last 8 characters with ... in between
    if len(address) > 20:
        return f"{address[:8]}...{address[-8:]}"
    return address

def get_network_info(crypto_currency):
    """Get network information for cryptocurrency"""
    network_info = {
        "BTC": {"network": "Bitcoin", "confirmations": "1-3", "explorer": "bitcoin"},
        "ETH": {"network": "Ethereum (ERC-20)", "confirmations": "12-35", "explorer": "ethereum"},
        "USDT": {"network": "Ethereum (ERC-20)", "confirmations": "12-35", "explorer": "ethereum"},
        "USDC": {"network": "Ethereum (ERC-20)", "confirmations": "12-35", "explorer": "ethereum"},
        "LTC": {"network": "Litecoin", "confirmations": "6-12", "explorer": "litecoin"},
        "SOL": {"network": "Solana", "confirmations": "1-2", "explorer": "solana"},
        "BNB": {"network": "BNB Smart Chain", "confirmations": "15-30", "explorer": "bnb"},
        "TRX": {"network": "Tron (TRC-20)", "confirmations": "20-30", "explorer": "tron"},
        "XMR": {"network": "Monero", "confirmations": "10-20", "explorer": "monero"},
        "DAI": {"network": "Ethereum (ERC-20)", "confirmations": "12-35", "explorer": "ethereum"},
        "DOGE": {"network": "Dogecoin", "confirmations": "6-12", "explorer": "dogecoin"},
        "SHIB": {"network": "Ethereum (ERC-20)", "confirmations": "12-35", "explorer": "ethereum"},
        "BCH": {"network": "Bitcoin Cash", "confirmations": "6-12", "explorer": "bitcoin-cash"},
        "MATIC": {"network": "Polygon", "confirmations": "128-256", "explorer": "polygon"},
        "TON": {"network": "TON", "confirmations": "1-2", "explorer": "ton"},
        "NOT": {"network": "TON", "confirmations": "1-2", "explorer": "ton"}
    }
    return network_info.get(crypto_currency, {"network": crypto_currency, "confirmations": "Variable", "explorer": "bitcoin"})

def generate_payment_uri(crypto_currency, address, amount):
    """Generate payment URI for wallet apps"""
    crypto_lower = crypto_currency.lower()
    
    # Standard cryptocurrency URI schemes
    uri_schemes = {
        "BTC": f"bitcoin:{address}?amount={amount}",
        "ETH": f"ethereum:{address}?value={amount}",
        "LTC": f"litecoin:{address}?amount={amount}",
        "BCH": f"bitcoincash:{address}?amount={amount}",
        "DOGE": f"dogecoin:{address}?amount={amount}",
        "SOL": f"solana:{address}?amount={amount}",
        "TRX": f"tron:{address}?amount={amount}"
    }
    
    return uri_schemes.get(crypto_currency, f"{crypto_lower}:{address}?amount={amount}")

async def deposit_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the deposit menu"""
    await show_deposit_menu(update, context)

async def show_deposit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the deposit amount selection menu"""
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    user = await get_user(user_id)
    
    message = (
        f"💰 **Deposit Funds** 💰\n\n"
        f"💳 Current balance: {format_money(user['balance'])}\n\n"
        f"Select deposit amount:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("💰 $10", callback_data="deposit_amount_10"),
            InlineKeyboardButton("💰 $25", callback_data="deposit_amount_25")
        ],
        [
            InlineKeyboardButton("💰 $50", callback_data="deposit_amount_50"),
            InlineKeyboardButton("💰 $100", callback_data="deposit_amount_100")
        ],
        [
            InlineKeyboardButton("💰 $250", callback_data="deposit_amount_250"),
            InlineKeyboardButton("💰 $500", callback_data="deposit_amount_500")
        ],
        [
            InlineKeyboardButton("💰 $1000", callback_data="deposit_amount_1000"),
            InlineKeyboardButton("💰 Custom", callback_data="deposit_amount_custom")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_currency_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: float):
    """Show cryptocurrency selection menu matching Image 1 (without Card/PayPal option)"""
    message = (
        f"💰 **Select top-up currency** 💰\n\n"
        f"💵 Amount: ${amount:.2f}\n\n"
        f"Choose your preferred cryptocurrency:"
    )
    
    # Create the cryptocurrency selection keyboard matching Image 1 (without Card/PayPal)
    # Using consistent callback pattern: deposit_[crypto]_[amount]
    keyboard = [
        [
            InlineKeyboardButton("₿ Bitcoin", callback_data=f"deposit_btc_{amount}"),
            InlineKeyboardButton("⟠ Ethereum", callback_data=f"deposit_eth_{amount}")
        ],
        [
            InlineKeyboardButton("💰 USDT", callback_data=f"deposit_usdt_{amount}"),
            InlineKeyboardButton("💰 USDC", callback_data=f"deposit_usdc_{amount}")
        ],
        [
            InlineKeyboardButton("🪙 Litecoin", callback_data=f"deposit_ltc_{amount}"),
            InlineKeyboardButton("🟣 Solana", callback_data=f"deposit_sol_{amount}")
        ],
        [
            InlineKeyboardButton("🟡 BNB", callback_data=f"deposit_bnb_{amount}"),
            InlineKeyboardButton("🔴 Tron", callback_data=f"deposit_trx_{amount}")
        ],
        [
            InlineKeyboardButton("🔒 Monero", callback_data=f"deposit_xmr_{amount}"),
            InlineKeyboardButton("🟠 DAI", callback_data=f"deposit_dai_{amount}")
        ],
        [
            InlineKeyboardButton("🐕 Dogecoin", callback_data=f"deposit_doge_{amount}"),
            InlineKeyboardButton("🐕 Shiba Inu", callback_data=f"deposit_shib_{amount}")
        ],
        [
            InlineKeyboardButton("₿ Bitcoin Cash", callback_data=f"deposit_bch_{amount}"),
            InlineKeyboardButton("🟣 Polygon", callback_data=f"deposit_matic_{amount}")
        ],
        [
            InlineKeyboardButton("💎 Toncoin", callback_data=f"deposit_ton_{amount}"),
            InlineKeyboardButton("🪙 NotCoin", callback_data=f"deposit_not_{amount}")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_deposit")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def deposit_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deposit menu callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    if len(data) < 2:
        return
    
    action = data[1]
    
    if action == "amount":
        # Handle deposit amount selection
        if len(data) >= 3:
            if data[2] == "custom":
                # Store in context that we're waiting for a custom amount
                context.user_data["deposit_action"] = "custom_amount"
                
                message = (
                    "💰 **Custom Deposit Amount** 💰\n\n"
                    "Please enter the amount you want to deposit:\n"
                    "💵 Minimum: $10\n"
                    "💵 Maximum: $10,000\n\n"
                    "Example: 25.50"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="menu_deposit")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                try:
                    amount = float(data[2])
                    await show_currency_selection(update, context, amount)
                except ValueError:
                    await query.edit_message_text("❌ Invalid amount.")
    
    elif len(data) >= 4 and data[1] in ["btc", "eth", "usdt", "usdc", "ltc", "sol", "bnb", "trx", "xmr", "dai", "doge", "shib", "bch", "matic", "ton", "not"]:
        # Handle cryptocurrency selection - unified pattern
        crypto_currency = data[1].upper()
        amount = float(data[2])
        
        await process_crypto_deposit(update, context, crypto_currency, amount)
    
    elif action == "show" and len(data) >= 3 and data[1] == "payment":
        # Handle showing payment details again
        payment_id = data[2]
        await show_payment_details(update, context, payment_id)
    
    elif action == "check" and len(data) >= 3 and data[1] == "payment":
        # Handle payment status check
        payment_id = data[2]
        await check_payment_status_callback(update, context, payment_id)
    
    elif action == "copy" and len(data) >= 3:
        # Handle copy functionality
        copy_type = data[1]  # "address" or "amount"
        payment_id = data[2]
        payment_info = context.user_data.get(f"payment_{payment_id}")
        
        if payment_info:
            crypto_currency = payment_info['crypto_currency']
            payment_address = payment_info['payment_address']
            pay_amount = payment_info['pay_amount']
            
            if copy_type == "address":
                message = (
                    f"📋 **Copy {crypto_currency} Address** 📋\n\n"
                    f"**Deposit Address:**\n"
                    f"`{payment_address}`\n\n"
                    f"📱 **How to copy:**\n"
                    f"• **Mobile:** Tap and hold the address above\n"
                    f"• **Desktop:** Select the address and Ctrl+C\n\n"
                    f"⚠️ **Important:** Make sure you copy the complete address!\n\n"
                    f"💡 **Next steps:**\n"
                    f"1. Copy this address\n"
                    f"2. Open your {crypto_currency} wallet\n"
                    f"3. Paste the address in the 'Send to' field\n"
                    f"4. Enter amount: `{pay_amount} {crypto_currency}`"
                )
            elif copy_type == "amount":
                message = (
                    f"📋 **Copy {crypto_currency} Amount** 📋\n\n"
                    f"**Exact Amount to Send:**\n"
                    f"`{pay_amount}`\n\n"
                    f"📱 **How to copy:**\n"
                    f"• **Mobile:** Tap and hold the amount above\n"
                    f"• **Desktop:** Select the amount and Ctrl+C\n\n"
                    f"⚠️ **Critical:** Send EXACTLY this amount!\n"
                    f"• Too little = payment not detected\n"
                    f"• Too much = overpayment (may be lost)\n\n"
                    f"💡 **Tip:** Copy this amount and paste it in your wallet's amount field."
                )
            else:
                message = "❌ Invalid copy request."
            
            keyboard = [
                [
                    InlineKeyboardButton("📋 Copy Address", callback_data=f"deposit_copy_address_{payment_id}"),
                    InlineKeyboardButton("📋 Copy Amount", callback_data=f"deposit_copy_amount_{payment_id}")
                ],
                [
                    InlineKeyboardButton("✅ Check Payment Status", callback_data=f"deposit_check_payment_{payment_id}")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Payment", callback_data=f"deposit_show_payment_{payment_id}"),
                    InlineKeyboardButton("🔙 Back to Deposit", callback_data="menu_deposit")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ Payment information not found.")

async def show_payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: str):
    """Show payment details again"""
    payment_info = context.user_data.get(f"payment_{payment_id}")
    
    if not payment_info:
        await update.callback_query.edit_message_text("❌ Payment information not found.")
        return
    
    crypto_currency = payment_info['crypto_currency']
    payment_address = payment_info['payment_address']
    pay_amount = payment_info['pay_amount']
    amount_usd = payment_info['amount_usd']
    
    # Get network information
    network_info = get_network_info(crypto_currency)
    
    message = (
        f"💰 **{crypto_currency} Deposit Payment** 💰\n\n"
        f"💵 **USD Amount:** ${amount_usd:.2f}\n"
        f"💰 **Pay Exactly:** `{pay_amount} {crypto_currency}`\n\n"
        f"📍 **Deposit Address:**\n"
        f"```\n{payment_address}\n```\n\n"
        f"🌐 **Network:** {network_info['network']}\n"
        f"⏱️ **Confirmations:** {network_info['confirmations']} blocks\n"
        f"⏰ **Expires:** 30 minutes\n\n"
        f"⚠️ **CRITICAL INSTRUCTIONS:**\n"
        f"• Send ONLY {crypto_currency} to this address\n"
        f"• Send EXACTLY `{pay_amount} {crypto_currency}`\n"
        f"• Use {network_info['network']} network\n"
        f"• Double-check the address before sending\n\n"
        f"🔍 **Payment ID:** `{payment_id}`\n\n"
        f"💡 **How to pay:**\n"
        f"1. Click 'Copy Address' below\n"
        f"2. Open your {crypto_currency} wallet\n"
        f"3. Paste the address and enter the exact amount\n"
        f"4. Send the transaction\n"
        f"5. Click 'Check Payment Status' to monitor\n\n"
        f"✅ **Auto-credit:** Funds credited after blockchain confirmation!"
    )
    
    # Generate payment URI for wallet apps
    payment_uri = generate_payment_uri(crypto_currency, payment_address, pay_amount)
    explorer_url = f"https://blockchair.com/{network_info['explorer']}/address/{payment_address}"
    
    keyboard = [
        [
            InlineKeyboardButton("📋 Copy Address", callback_data=f"deposit_copy_address_{payment_id}"),
            InlineKeyboardButton("📋 Copy Amount", callback_data=f"deposit_copy_amount_{payment_id}")
        ],
        [
            InlineKeyboardButton("📱 Open in Wallet", url=payment_uri),
            InlineKeyboardButton("🔍 View on Explorer", url=explorer_url)
        ],
        [
            InlineKeyboardButton("✅ Check Payment Status", callback_data=f"deposit_check_payment_{payment_id}")
        ],
        [
            InlineKeyboardButton("🔙 Back to Deposit", callback_data="menu_deposit")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def check_payment_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: str):
    """Check payment status and update user"""
    from src.wallet.nowpayments import check_payment_status
    
    try:
        payment_status = await check_payment_status(payment_id)
        
        if payment_status:
            status = payment_status.get("payment_status", "waiting")
            payment_info = context.user_data.get(f"payment_{payment_id}")
            
            if status in ["confirmed", "finished"]:
                message = (
                    "✅ **Payment Confirmed** ✅\n\n"
                    "Your deposit has been confirmed and credited to your account!\n\n"
                    "Thank you for your deposit. You can now start gambling!"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("🎮 Play Games", callback_data="menu_games")
                    ],
                    [
                        InlineKeyboardButton("💰 Check Balance", callback_data="menu_profile")
                    ]
                ]
            elif status in ["waiting", "confirming"]:
                crypto_currency = payment_info.get("crypto_currency", "crypto") if payment_info else "crypto"
                pay_amount = payment_info.get("pay_amount", "amount") if payment_info else "amount"
                
                message = (
                    "⏳ **Payment Pending** ⏳\n\n"
                    f"We're waiting for your {crypto_currency} payment to be confirmed.\n"
                    f"Expected amount: {pay_amount} {crypto_currency}\n\n"
                    "This usually takes 10-30 minutes depending on network congestion.\n\n"
                    "Please check back later or contact support if you've already sent the payment."
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Check Again", callback_data=f"deposit_check_payment_{payment_id}")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back to Deposit", callback_data="menu_deposit")
                    ]
                ]
            else:
                message = (
                    f"ℹ️ **Payment Status: {status.capitalize()}** ℹ️\n\n"
                    "If you've sent the payment, please wait for blockchain confirmation.\n"
                    "If you haven't sent it yet, please follow the payment instructions.\n\n"
                    "For assistance, please contact support."
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Check Again", callback_data=f"deposit_check_payment_{payment_id}")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back to Deposit", callback_data="menu_deposit")
                    ]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            message = (
                "❌ **Status Check Failed** ❌\n\n"
                "Could not retrieve payment status. Please try again later."
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Try Again", callback_data=f"deposit_check_payment_{payment_id}")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Deposit", callback_data="menu_deposit")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    except Exception as e:
        message = (
            "❌ **Error Checking Status** ❌\n\n"
            f"Error: {str(e)}\n\n"
            "Please try again later or contact support."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔙 Back to Deposit", callback_data="menu_deposit")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def process_crypto_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, crypto_currency: str, amount: float):
    """Process cryptocurrency deposit"""
    user_id = update.callback_query.from_user.id
    
    try:
        # Validate cryptocurrency is supported
        from src.wallet.nowpayments import SUPPORTED_CRYPTOS
        if crypto_currency not in SUPPORTED_CRYPTOS:
            message = (
                f"❌ **Unsupported Cryptocurrency** ❌\n\n"
                f"{crypto_currency} is not currently supported.\n"
                f"Please choose from our supported cryptocurrencies."
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Back", callback_data="menu_deposit")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Create payment using NOWPayments
        payment = await create_deposit_payment(user_id, amount, crypto_currency)
        
        if payment and payment.get("payment_id"):
            payment_id = payment.get("payment_id")
            payment_address = payment.get("pay_address")
            pay_amount = payment.get("pay_amount")
            
            # Store payment info in context for tracking
            context.user_data[f"payment_{payment_id}"] = {
                "user_id": user_id,
                "amount_usd": amount,
                "crypto_currency": crypto_currency,
                "payment_address": payment_address,
                "pay_amount": pay_amount
            }
            
            # Get network information
            network_info = get_network_info(crypto_currency)
            
            message = (
                f"💰 **{crypto_currency} Deposit Payment** 💰\n\n"
                f"💵 **USD Amount:** ${amount:.2f}\n"
                f"💰 **Pay Exactly:** `{pay_amount} {crypto_currency}`\n\n"
                f"📍 **Deposit Address:**\n"
                f"```\n{payment_address}\n```\n\n"
                f"🌐 **Network:** {network_info['network']}\n"
                f"⏱️ **Confirmations:** {network_info['confirmations']} blocks\n"
                f"⏰ **Expires:** 30 minutes\n\n"
                f"⚠️ **CRITICAL INSTRUCTIONS:**\n"
                f"• Send ONLY {crypto_currency} to this address\n"
                f"• Send EXACTLY `{pay_amount} {crypto_currency}`\n"
                f"• Use {network_info['network']} network\n"
                f"• Double-check the address before sending\n\n"
                f"🔍 **Payment ID:** `{payment_id}`\n\n"
                f"💡 **How to pay:**\n"
                f"1. Click 'Copy Address' below\n"
                f"2. Open your {crypto_currency} wallet\n"
                f"3. Paste the address and enter the exact amount\n"
                f"4. Send the transaction\n"
                f"5. Click 'Check Payment Status' to monitor\n\n"
                f"✅ **Auto-credit:** Funds credited after blockchain confirmation!"
            )
            
            # Generate payment URI for wallet apps
            payment_uri = generate_payment_uri(crypto_currency, payment_address, pay_amount)
            explorer_url = f"https://blockchair.com/{network_info['explorer']}/address/{payment_address}"
            
            keyboard = [
                [
                    InlineKeyboardButton("📋 Copy Address", callback_data=f"deposit_copy_address_{payment_id}"),
                    InlineKeyboardButton("📋 Copy Amount", callback_data=f"deposit_copy_amount_{payment_id}")
                ],
                [
                    InlineKeyboardButton("📱 Open in Wallet", url=payment_uri),
                    InlineKeyboardButton("🔍 View on Explorer", url=explorer_url)
                ],
                [
                    InlineKeyboardButton("✅ Check Payment Status", callback_data=f"deposit_check_payment_{payment_id}")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Deposit", callback_data="menu_deposit")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            error_msg = "Could not create payment"
            if payment and "message" in payment:
                error_msg = payment["message"]
            
            message = (
                "❌ **Payment Error** ❌\n\n"
                f"{error_msg}\n\n"
                "Please try again later or contact support."
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Back", callback_data="menu_deposit")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    except Exception as e:
        message = (
            "❌ **Payment Error** ❌\n\n"
            f"Error: {str(e)}\n\n"
            "Please try again later or contact support."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔙 Back", callback_data="menu_deposit")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def deposit_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deposit-related messages"""
    user_id = update.effective_user.id
    
    if "deposit_action" not in context.user_data:
        return False
    
    action = context.user_data["deposit_action"]
    
    if action == "custom_amount":
        # Process custom deposit amount
        try:
            amount = float(update.message.text.strip())
            
            if amount < 10:
                await update.message.reply_text("❌ Minimum deposit amount is $10.")
                return True
            
            if amount > 10000:
                await update.message.reply_text("❌ Maximum deposit amount is $10,000.")
                return True
            
            # Clear the deposit action
            del context.user_data["deposit_action"]
            
            # Show currency selection for this amount
            # We need to create a fake callback query to use the existing function
            class FakeQuery:
                def __init__(self, user_id):
                    self.from_user = type('obj', (object,), {'id': user_id})
                    
                async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            
            fake_update = type('obj', (object,), {'callback_query': FakeQuery(user_id)})
            await show_currency_selection(fake_update, context, amount)
            
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please enter a number.")
        
        return True
    
    return False