import os
import json
import asyncio
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database import get_user, update_user_balance, record_transaction
from src.utils.formatting import format_money
from src.utils.logger import bot_logger

load_dotenv()

# Withdrawal configuration
WITHDRAWAL_CONFIG = {
    "min_withdrawal_usd": 50.0,
    "max_withdrawal_usd": 10000.0,
    "daily_withdrawal_limit": 5000.0,
    "processing_fee_percent": 2.0,  # 2% processing fee
    "min_processing_fee": 5.0,
    "max_processing_fee": 50.0,
    "auto_approval_limit": 500.0,  # Auto-approve withdrawals under $500
    "manual_review_required": 1000.0,  # Manual review for withdrawals over $1000
}

# Supported withdrawal methods
WITHDRAWAL_METHODS = {
    "BTC": {
        "name": "Bitcoin",
        "symbol": "BTC",
        "icon": "₿",
        "min_amount": 0.001,
        "network_fee": 0.0005,
        "processing_time": "10-30 minutes",
        "confirmations": 2,
        "address_regex": r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$"
    },
    "ETH": {
        "name": "Ethereum",
        "symbol": "ETH",
        "icon": "Ξ",
        "min_amount": 0.01,
        "network_fee": 0.005,
        "processing_time": "5-15 minutes",
        "confirmations": 12,
        "address_regex": r"^0x[a-fA-F0-9]{40}$"
    },
    "USDT": {
        "name": "Tether (ERC-20)",
        "symbol": "USDT",
        "icon": "₮",
        "min_amount": 20.0,
        "network_fee": 5.0,
        "processing_time": "5-15 minutes",
        "confirmations": 12,
        "address_regex": r"^0x[a-fA-F0-9]{40}$"
    },
    "USDC": {
        "name": "USD Coin",
        "symbol": "USDC",
        "icon": "₵",
        "min_amount": 20.0,
        "network_fee": 5.0,
        "processing_time": "5-15 minutes",
        "confirmations": 12,
        "address_regex": r"^0x[a-fA-F0-9]{40}$"
    },
    "LTC": {
        "name": "Litecoin",
        "symbol": "LTC",
        "icon": "Ł",
        "min_amount": 0.1,
        "network_fee": 0.01,
        "processing_time": "5-20 minutes",
        "confirmations": 6,
        "address_regex": r"^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$"
    },
    "TRX": {
        "name": "TRON",
        "symbol": "TRX",
        "icon": "⚡",
        "min_amount": 100.0,
        "network_fee": 1.0,
        "processing_time": "1-5 minutes",
        "confirmations": 20,
        "address_regex": r"^T[A-Za-z1-9]{33}$"
    }
}

# Exchange rates (in production, these would be fetched from an API)
EXCHANGE_RATES = {
    "BTC": 65000.0,
    "ETH": 3200.0,
    "USDT": 1.0,
    "USDC": 1.0,
    "LTC": 85.0,
    "TRX": 0.12
}

class WithdrawalSystem:
    def __init__(self):
        self.pending_withdrawals = {}
        
    async def show_withdrawal_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main withdrawal menu"""
        user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
        user = await get_user(user_id)
        
        # Check if user can withdraw
        if user['balance'] < WITHDRAWAL_CONFIG['min_withdrawal_usd']:
            message = (
                "❌ **Withdrawal Not Available** ❌\n\n"
                f"💰 Current balance: {format_money(user['balance'])}\n"
                f"💸 Minimum withdrawal: {format_money(WITHDRAWAL_CONFIG['min_withdrawal_usd'])}\n\n"
                "Keep playing to increase your balance! 🎮"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
            ]
        else:
            message = (
                f"💸 **Withdrawal Center** 💸\n\n"
                f"💰 Available balance: {format_money(user['balance'])}\n"
                f"💸 Min withdrawal: {format_money(WITHDRAWAL_CONFIG['min_withdrawal_usd'])}\n"
                f"💸 Max withdrawal: {format_money(WITHDRAWAL_CONFIG['max_withdrawal_usd'])}\n"
                f"💳 Processing fee: {WITHDRAWAL_CONFIG['processing_fee_percent']}%\n\n"
                "🔒 **Secure & Fast Withdrawals**\n"
                "• Automated processing\n"
                "• Multiple cryptocurrencies\n"
                "• Low fees & fast transfers\n\n"
                "Select your preferred cryptocurrency:"
            )
            
            # Create cryptocurrency buttons
            keyboard = []
            row = []
            
            for symbol, method in WITHDRAWAL_METHODS.items():
                row.append(InlineKeyboardButton(
                    f"{method['icon']} {method['name']}",
                    callback_data=f"withdraw_{symbol}"
                ))
                
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            
            if row:  # Add remaining buttons
                keyboard.append(row)
            
            keyboard.extend([
                [InlineKeyboardButton("📊 Withdrawal History", callback_data="withdraw_history")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_crypto_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, crypto_symbol: str):
        """Handle cryptocurrency selection for withdrawal"""
        user_id = update.callback_query.from_user.id
        user = await get_user(user_id)
        
        if crypto_symbol not in WITHDRAWAL_METHODS:
            await update.callback_query.edit_message_text("❌ Invalid cryptocurrency selected.")
            return
        
        method = WITHDRAWAL_METHODS[crypto_symbol]
        exchange_rate = EXCHANGE_RATES[crypto_symbol]
        
        # Calculate amounts
        max_crypto_amount = user['balance'] / exchange_rate
        min_usd_amount = WITHDRAWAL_CONFIG['min_withdrawal_usd']
        min_crypto_amount = max(min_usd_amount / exchange_rate, method['min_amount'])
        
        # Store withdrawal context
        context.user_data['withdrawal_crypto'] = crypto_symbol
        context.user_data['withdrawal_step'] = 'amount'
        
        message = (
            f"💸 **{method['name']} Withdrawal** 💸\n\n"
            f"💰 Your balance: {format_money(user['balance'])}\n"
            f"💱 Exchange rate: 1 {crypto_symbol} = ${exchange_rate:,.2f}\n\n"
            f"📊 **Withdrawal Limits:**\n"
            f"• Min amount: {min_crypto_amount:.8f} {crypto_symbol}\n"
            f"• Max amount: {max_crypto_amount:.8f} {crypto_symbol}\n"
            f"• Network fee: {method['network_fee']} {crypto_symbol}\n"
            f"• Processing time: {method['processing_time']}\n\n"
            f"💡 **Enter the amount in {crypto_symbol} you want to withdraw:**"
        )
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="withdraw_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def process_withdrawal_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process withdrawal amount input"""
        if 'withdrawal_crypto' not in context.user_data:
            await update.message.reply_text("❌ Withdrawal session expired. Please start again.")
            return False
        
        user_id = update.effective_user.id
        user = await get_user(user_id)
        crypto_symbol = context.user_data['withdrawal_crypto']
        method = WITHDRAWAL_METHODS[crypto_symbol]
        exchange_rate = EXCHANGE_RATES[crypto_symbol]
        
        try:
            amount = float(update.message.text.strip())
            
            # Validate amount
            if amount < method['min_amount']:
                await update.message.reply_text(
                    f"❌ Minimum withdrawal amount is {method['min_amount']} {crypto_symbol}"
                )
                return True
            
            # Calculate USD value
            usd_value = amount * exchange_rate
            
            # Check if user has enough balance
            processing_fee = max(
                min(usd_value * WITHDRAWAL_CONFIG['processing_fee_percent'] / 100, 
                    WITHDRAWAL_CONFIG['max_processing_fee']),
                WITHDRAWAL_CONFIG['min_processing_fee']
            )
            
            total_usd_needed = usd_value + processing_fee
            
            if user['balance'] < total_usd_needed:
                await update.message.reply_text(
                    f"❌ Insufficient balance!\n\n"
                    f"Required: ${total_usd_needed:.2f}\n"
                    f"Available: {format_money(user['balance'])}\n"
                    f"(Including ${processing_fee:.2f} processing fee)"
                )
                return True
            
            # Store amount and move to address step
            context.user_data['withdrawal_amount'] = amount
            context.user_data['withdrawal_usd_value'] = usd_value
            context.user_data['withdrawal_fee'] = processing_fee
            context.user_data['withdrawal_step'] = 'address'
            
            net_amount = amount - method['network_fee']
            
            message = (
                f"💸 **Withdrawal Summary** 💸\n\n"
                f"💰 Amount: {amount} {crypto_symbol}\n"
                f"💵 USD Value: ${usd_value:.2f}\n"
                f"💳 Processing Fee: ${processing_fee:.2f}\n"
                f"⛽ Network Fee: {method['network_fee']} {crypto_symbol}\n"
                f"📤 You'll receive: {net_amount:.8f} {crypto_symbol}\n\n"
                f"🏦 **Please enter your {method['name']} wallet address:**\n\n"
                f"⚠️ **Important:** Make sure the address is correct!\n"
                f"Transactions cannot be reversed."
            )
            
            keyboard = [
                [InlineKeyboardButton("❌ Cancel", callback_data="withdraw_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return True
            
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
            return True
    
    async def process_withdrawal_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process withdrawal address input"""
        import re
        
        if 'withdrawal_crypto' not in context.user_data or 'withdrawal_amount' not in context.user_data:
            await update.message.reply_text("❌ Withdrawal session expired. Please start again.")
            return False
        
        user_id = update.effective_user.id
        crypto_symbol = context.user_data['withdrawal_crypto']
        amount = context.user_data['withdrawal_amount']
        usd_value = context.user_data['withdrawal_usd_value']
        processing_fee = context.user_data['withdrawal_fee']
        
        method = WITHDRAWAL_METHODS[crypto_symbol]
        address = update.message.text.strip()
        
        # Validate address format
        if not re.match(method['address_regex'], address):
            await update.message.reply_text(
                f"❌ Invalid {method['name']} address format!\n\n"
                f"Please check your address and try again."
            )
            return True
        
        # Create withdrawal request
        withdrawal_id = self._generate_withdrawal_id()
        
        withdrawal_request = {
            'id': withdrawal_id,
            'user_id': user_id,
            'crypto_symbol': crypto_symbol,
            'amount': amount,
            'usd_value': usd_value,
            'processing_fee': processing_fee,
            'address': address,
            'status': 'pending',
            'created_at': datetime.now(),
            'requires_manual_review': usd_value > WITHDRAWAL_CONFIG['auto_approval_limit']
        }
        
        self.pending_withdrawals[withdrawal_id] = withdrawal_request
        
        # Show confirmation
        net_amount = amount - method['network_fee']
        
        message = (
            f"✅ **Withdrawal Request Created** ✅\n\n"
            f"🆔 Request ID: `{withdrawal_id}`\n"
            f"💰 Amount: {amount} {crypto_symbol}\n"
            f"📤 You'll receive: {net_amount:.8f} {crypto_symbol}\n"
            f"🏦 Address: `{address[:10]}...{address[-10:]}`\n"
            f"⏱️ Processing time: {method['processing_time']}\n\n"
            f"{'🔍 **Manual Review Required**' if withdrawal_request['requires_manual_review'] else '⚡ **Auto-Processing**'}\n"
            f"{'Your withdrawal will be reviewed by our team.' if withdrawal_request['requires_manual_review'] else 'Your withdrawal will be processed automatically.'}\n\n"
            f"💡 You'll receive a notification when processed."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm Withdrawal", callback_data=f"withdraw_confirm_{withdrawal_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"withdraw_cancel_{withdrawal_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return True
    
    async def confirm_withdrawal(self, update: Update, context: ContextTypes.DEFAULT_TYPE, withdrawal_id: str):
        """Confirm and process withdrawal"""
        if withdrawal_id not in self.pending_withdrawals:
            await update.callback_query.edit_message_text("❌ Withdrawal request not found or expired.")
            return
        
        withdrawal = self.pending_withdrawals[withdrawal_id]
        user_id = withdrawal['user_id']
        
        # Verify user
        if update.callback_query.from_user.id != user_id:
            await update.callback_query.answer("❌ Unauthorized", show_alert=True)
            return
        
        # Deduct balance
        total_deduction = withdrawal['usd_value'] + withdrawal['processing_fee']
        await update_user_balance(user_id, -total_deduction)
        
        # Record transaction
        await record_transaction(
            user_id, 
            -total_deduction, 
            "withdrawal", 
            description=f"{withdrawal['crypto_symbol']} withdrawal to {withdrawal['address'][:10]}..."
        )
        
        # Update withdrawal status
        withdrawal['status'] = 'confirmed'
        withdrawal['confirmed_at'] = datetime.now()
        
        # Simulate processing (in production, this would integrate with actual crypto APIs)
        if not withdrawal['requires_manual_review']:
            # Auto-process small withdrawals
            context.job_queue.run_once(
                lambda _: asyncio.create_task(self._simulate_withdrawal_processing(context, withdrawal_id)),
                30  # Process after 30 seconds
            )
        
        method = WITHDRAWAL_METHODS[withdrawal['crypto_symbol']]
        net_amount = withdrawal['amount'] - method['network_fee']
        
        message = (
            f"🎉 **Withdrawal Confirmed!** 🎉\n\n"
            f"🆔 Request ID: `{withdrawal_id}`\n"
            f"💰 Amount: {withdrawal['amount']} {withdrawal['crypto_symbol']}\n"
            f"📤 You'll receive: {net_amount:.8f} {withdrawal['crypto_symbol']}\n"
            f"🏦 Address: `{withdrawal['address']}`\n\n"
            f"{'🔍 Your withdrawal is being reviewed by our team.' if withdrawal['requires_manual_review'] else '⚡ Your withdrawal is being processed automatically.'}\n\n"
            f"💡 You'll receive a notification when completed."
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 View Status", callback_data=f"withdraw_status_{withdrawal_id}")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clean up context
        for key in list(context.user_data.keys()):
            if key.startswith('withdrawal_'):
                del context.user_data[key]
    
    async def _simulate_withdrawal_processing(self, context: ContextTypes.DEFAULT_TYPE, withdrawal_id: str):
        """Simulate withdrawal processing (replace with real API integration)"""
        if withdrawal_id not in self.pending_withdrawals:
            return
        
        withdrawal = self.pending_withdrawals[withdrawal_id]
        
        # Simulate processing delay
        await asyncio.sleep(30)
        
        # Update status to completed
        withdrawal['status'] = 'completed'
        withdrawal['completed_at'] = datetime.now()
        withdrawal['tx_hash'] = self._generate_fake_tx_hash()
        
        # Notify user
        try:
            method = WITHDRAWAL_METHODS[withdrawal['crypto_symbol']]
            net_amount = withdrawal['amount'] - method['network_fee']
            
            message = (
                f"✅ **Withdrawal Completed!** ✅\n\n"
                f"🆔 Request ID: `{withdrawal_id}`\n"
                f"💰 Amount sent: {net_amount:.8f} {withdrawal['crypto_symbol']}\n"
                f"🏦 To address: `{withdrawal['address']}`\n"
                f"🔗 TX Hash: `{withdrawal['tx_hash']}`\n\n"
                f"🎉 Your withdrawal has been successfully processed!"
            )
            
            await context.bot.send_message(
                chat_id=withdrawal['user_id'],
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            bot_logger.error(f"Failed to send withdrawal completion notification: {e}")
    
    def _generate_withdrawal_id(self) -> str:
        """Generate unique withdrawal ID"""
        import random
        import string
        return 'WD' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def _generate_fake_tx_hash(self) -> str:
        """Generate fake transaction hash for simulation"""
        import random
        import string
        return '0x' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))

# Global withdrawal system instance
withdrawal_system = WithdrawalSystem()