import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, record_game
from src.utils.formatting import format_money

async def coinflip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /coinflip command"""
    if not context.args or len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /coinflip [heads/tails] [amount]\n"
            "Example: /coinflip heads 5"
        )
        return
    
    choice = context.args[0].lower()
    if choice not in ["heads", "tails"]:
        await update.message.reply_text("Please choose either 'heads' or 'tails'")
        return
    
    try:
        bet_amount = float(context.args[1])
        if bet_amount <= 0:
            await update.message.reply_text("Bet amount must be positive")
            return
    except ValueError:
        await update.message.reply_text("Bet amount must be a number")
        return
    
    user = await get_user(update.effective_user.id)
    
    if user["balance"] < bet_amount:
        await update.message.reply_text(
            f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
        )
        return
    
    # Deduct bet amount from user balance
    await update_user_balance(user["user_id"], -bet_amount)
    await record_transaction(user["user_id"], -bet_amount, "bet")
    
    # Determine outcome
    result = random.choice(["heads", "tails"])
    won = choice == result
    
    # Calculate winnings
    winnings = bet_amount * 2 if won else 0
    
    # Record game result
    game_id = await record_game(
        user["user_id"], 
        "coinflip", 
        bet_amount, 
        "win" if won else "loss", 
        winnings
    )
    
    # Update user balance if won
    if won:
        await update_user_balance(user["user_id"], winnings)
        await record_transaction(user["user_id"], winnings, "win", game_id)
    
    # Get updated user data
    user = await get_user(user["user_id"])
    
    # Create result message
    if won:
        message = (
            f"🎉 You won! The coin landed on {result}.\n"
            f"You bet: {format_money(bet_amount)}\n"
            f"You won: {format_money(winnings)}\n"
            f"Your balance: {format_money(user['balance'])}"
        )
    else:
        message = (
            f"😢 You lost! The coin landed on {result}.\n"
            f"You bet: {format_money(bet_amount)}\n"
            f"Your balance: {format_money(user['balance'])}"
        )
    
    # Create play again keyboard
    keyboard = [
        [
            InlineKeyboardButton("Play Again", callback_data=f"coinflip_{bet_amount}_{choice}"),
            InlineKeyboardButton("Double Bet", callback_data=f"coinflip_{bet_amount*2}_{choice}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def coinflip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle coinflip callback queries"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    _, bet_amount, choice = query.data.split("_")
    bet_amount = float(bet_amount)
    
    user = await get_user(query.from_user.id)
    
    if user["balance"] < bet_amount:
        await query.edit_message_text(
            f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
        )
        return
    
    # Deduct bet amount from user balance
    await update_user_balance(user["user_id"], -bet_amount)
    await record_transaction(user["user_id"], -bet_amount, "bet")
    
    # Determine outcome
    result = random.choice(["heads", "tails"])
    won = choice == result
    
    # Calculate winnings
    winnings = bet_amount * 2 if won else 0
    
    # Record game result
    game_id = await record_game(
        user["user_id"], 
        "coinflip", 
        bet_amount, 
        "win" if won else "loss", 
        winnings
    )
    
    # Update user balance if won
    if won:
        await update_user_balance(user["user_id"], winnings)
        await record_transaction(user["user_id"], winnings, "win", game_id)
    
    # Get updated user data
    user = await get_user(user["user_id"])
    
    # Create result message
    if won:
        message = (
            f"🎉 You won! The coin landed on {result}.\n"
            f"You bet: {format_money(bet_amount)}\n"
            f"You won: {format_money(winnings)}\n"
            f"Your balance: {format_money(user['balance'])}"
        )
    else:
        message = (
            f"😢 You lost! The coin landed on {result}.\n"
            f"You bet: {format_money(bet_amount)}\n"
            f"Your balance: {format_money(user['balance'])}"
        )
    
    # Create play again keyboard
    keyboard = [
        [
            InlineKeyboardButton("Play Again", callback_data=f"coinflip_{bet_amount}_{choice}"),
            InlineKeyboardButton("Double Bet", callback_data=f"coinflip_{bet_amount*2}_{choice}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)