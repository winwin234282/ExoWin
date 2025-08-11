import os
from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv

load_dotenv()

PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

async def create_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int):
    """Create a payment invoice for the user"""
    chat_id = update.effective_chat.id
    title = "Add funds to your gambling wallet"
    description = f"Add ${amount/100:.2f} to your gambling wallet"
    payload = f"deposit_{update.effective_user.id}_{amount}"
    currency = "USD"
    prices = [LabeledPrice("Deposit", amount)]
    
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=currency,
        prices=prices
    )

async def process_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answer the PreCheckoutQuery"""
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def process_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payment"""
    payment = update.message.successful_payment
    amount = payment.total_amount / 100  # Convert from cents to dollars
    
    # Extract user_id from payload
    payload_parts = payment.invoice_payload.split('_')
    user_id = int(payload_parts[1])
    
    # Record transaction and update balance
    from src.database import record_transaction, update_user_balance
    await record_transaction(user_id, amount, "deposit")
    user = await update_user_balance(user_id, amount)
    
    await update.message.reply_text(
        f"Payment of ${amount:.2f} was successful! Your new balance is ${user['balance']:.2f}"
    )