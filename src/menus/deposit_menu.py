from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user
from src.utils.formatting import format_money
from src.wallet.nowpayments import create_deposit_payment, create_deposit_invoice

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
    keyboard = [
        [
            InlineKeyboardButton("₿ Bitcoin", callback_data=f"crypto_btc_{amount}"),
            InlineKeyboardButton("⟠ Ethereum", callback_data=f"crypto_eth_{amount}")
        ],
        [
            InlineKeyboardButton("💰 USDT", callback_data=f"crypto_usdt_{amount}"),
            InlineKeyboardButton("💰 USDC", callback_data=f"crypto_usdc_{amount}")
        ],
        [
            InlineKeyboardButton("🪙 Litecoin", callback_data=f"crypto_ltc_{amount}"),
            InlineKeyboardButton("🟣 Solana", callback_data=f"crypto_sol_{amount}")
        ],
        [
            InlineKeyboardButton("🟡 BNB", callback_data=f"crypto_bnb_{amount}"),
            InlineKeyboardButton("🔴 Tron", callback_data=f"crypto_trx_{amount}")
        ],
        [
            InlineKeyboardButton("🔒 Monero", callback_data=f"crypto_xmr_{amount}"),
            InlineKeyboardButton("🟠 DAI", callback_data=f"crypto_dai_{amount}")
        ],
        [
            InlineKeyboardButton("🐕 Dogecoin", callback_data=f"crypto_doge_{amount}"),
            InlineKeyboardButton("🐕 Shiba Inu", callback_data=f"crypto_shib_{amount}")
        ],
        [
            InlineKeyboardButton("₿ Bitcoin Cash", callback_data=f"crypto_bch_{amount}"),
            InlineKeyboardButton("🟣 Polygon", callback_data=f"crypto_matic_{amount}")
        ],
        [
            InlineKeyboardButton("💎 Toncoin", callback_data=f"crypto_ton_{amount}"),
            InlineKeyboardButton("🪙 NotCoin", callback_data=f"crypto_not_{amount}")
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
    
    elif action == "crypto" and len(data) >= 4:
        # Handle cryptocurrency selection
        crypto_currency = data[2].upper()
        amount = float(data[3])
        
        await process_crypto_deposit(update, context, crypto_currency, amount)

async def process_crypto_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, crypto_currency: str, amount: float):
    """Process cryptocurrency deposit"""
    user_id = update.callback_query.from_user.id
    
    try:
        # Create payment using NOWPayments
        payment = await create_deposit_payment(user_id, amount, crypto_currency)
        
        if payment:
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
            
            message = (
                f"💰 **{crypto_currency} Deposit** 💰\n\n"
                f"💵 Amount: ${amount:.2f}\n"
                f"💰 Pay: {pay_amount} {crypto_currency}\n\n"
                f"📍 **Send to this address:**\n"
                f"`{payment_address}`\n\n"
                f"⏰ Payment expires in 30 minutes\n"
                f"🔍 Payment ID: `{payment_id}`\n\n"
                f"After sending, your funds will be credited automatically!"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Check Payment", callback_data=f"check_payment_{payment_id}")
                ],
                [
                    InlineKeyboardButton("📋 Copy Address", callback_data=f"copy_address_{payment_id}")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Deposit", callback_data="menu_deposit")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            message = (
                "❌ **Payment Error** ❌\n\n"
                "Could not create payment. Please try again later or contact support."
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