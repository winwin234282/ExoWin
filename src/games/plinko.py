import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, record_game
from src.utils.formatting import format_money

# Plinko game settings
PLINKO_ROWS = 8
PLINKO_RISK_LEVELS = {
    "low": {
        "description": "Low Risk",
        "multipliers": [1.4, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.4]
    },
    "medium": {
        "description": "Medium Risk",
        "multipliers": [5.6, 2.1, 1.5, 1.0, 0.7, 0.5, 0.3, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.1, 5.6]
    },
    "high": {
        "description": "High Risk",
        "multipliers": [13.0, 3.0, 1.4, 0.7, 0.4, 0.2, 0.1, 0.0, 0.1, 0.2, 0.4, 0.7, 1.4, 3.0, 13.0]
    }
}

# Plinko animation frames
PLINKO_FRAMES = [
    [
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛🔴⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⭐⬛⭐⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⭐⬛⭐⬛⭐⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛⬛",
        "⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛",
        "⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛",
        "⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛"
    ],
    [
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛🔴⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⭐⬛⭐⬛⭐⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛⬛",
        "⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛",
        "⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛",
        "⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛"
    ],
    [
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⭐⬛🔴⬛⭐⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛⬛",
        "⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛",
        "⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛",
        "⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛"
    ],
    [
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⭐⬛⬛⬛⭐⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⭐⬛⭐🔴⭐⬛⭐⬛⬛⬛⬛",
        "⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛",
        "⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛",
        "⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛"
    ],
    [
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⭐⬛⬛⬛⭐⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛⬛",
        "⬛⬛⬛⭐⬛⭐⬛🔴⬛⭐⬛⭐⬛⬛⬛",
        "⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛",
        "⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛"
    ],
    [
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⭐⬛⬛⬛⭐⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛⬛",
        "⬛⬛⬛⭐⬛⭐⬛⬛⬛⭐⬛⭐⬛⬛⬛",
        "⬛⬛⭐⬛⭐⬛⭐🔴⭐⬛⭐⬛⭐⬛⬛",
        "⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛"
    ],
    [
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⭐⬛⬛⬛⭐⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛⬛",
        "⬛⬛⬛⭐⬛⭐⬛⬛⬛⭐⬛⭐⬛⬛⬛",
        "⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛",
        "⬛⭐⬛⭐⬛⭐⬛🔴⬛⭐⬛⭐⬛⭐⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛"
    ],
    [
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⬛⭐⬛⬛⬛⭐⬛⬛⬛⬛⬛",
        "⬛⬛⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛⬛⬛",
        "⬛⬛⬛⭐⬛⭐⬛⬛⬛⭐⬛⭐⬛⬛⬛",
        "⬛⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⭐⬛⬛",
        "⬛⭐⬛⭐⬛⭐⬛⬛⬛⭐⬛⭐⬛⭐⬛",
        "⬛⬛⬛⬛⬛⬛⬛🔴⬛⬛⬛⬛⬛⬛⬛"
    ]
]

async def plinko_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /plinko command"""
    if not context.args:
        # Show plinko game info
        message = (
            "🎮 Plinko Game 🎮\n\n"
            "Drop a ball and watch it bounce through pegs to determine your prize!\n\n"
            "How to play:\n"
            "1. Choose a risk level (Low, Medium, High)\n"
            "2. Place your bet\n"
            "3. Watch the ball drop and see where it lands\n\n"
            "Usage: /plinko [risk_level] [amount]\n"
            "Example: /plinko medium 10\n\n"
            "Risk Levels:\n"
            "• Low: Safer bets with smaller payouts (max 1.4x)\n"
            "• Medium: Balanced risk and reward (max 5.6x)\n"
            "• High: High risk with potential big wins (max 13.0x)"
        )
        
        # Create keyboard for quick bets
        keyboard = [
            [
                InlineKeyboardButton("Low Risk", callback_data="plinko_risk_low"),
                InlineKeyboardButton("Medium Risk", callback_data="plinko_risk_medium"),
                InlineKeyboardButton("High Risk", callback_data="plinko_risk_high")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        return
    
    # Process command arguments
    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /plinko [risk_level] [amount]\n"
            "Example: /plinko medium 10"
        )
        return
    
    risk_level = context.args[0].lower()
    if risk_level not in PLINKO_RISK_LEVELS:
        await update.message.reply_text(
            "Invalid risk level. Choose from: low, medium, high"
        )
        return
    
    try:
        bet_amount = float(context.args[1])
        if bet_amount <= 0:
            await update.message.reply_text("Bet amount must be positive")
            return
    except ValueError:
        await update.message.reply_text("Bet amount must be a number")
        return
    
    # Start the plinko game
    await play_plinko(update, context, risk_level, bet_amount)

async def plinko_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plinko callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    if len(data) < 3:
        return
    
    action = data[1]
    
    if action == "risk":
        risk_level = data[2]
        
        # Show bet amount selection
        message = (
            f"🎮 Plinko - {PLINKO_RISK_LEVELS[risk_level]['description']} 🎮\n\n"
            "Select your bet amount:"
        )
        
        keyboard = []
        for amount in [1, 5, 10, 25, 50, 100]:
            keyboard.append([
                InlineKeyboardButton(f"${amount}", callback_data=f"plinko_bet_{risk_level}_{amount}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("Custom Amount", callback_data=f"plinko_custom_{risk_level}")
        ])
        
        keyboard.append([
            InlineKeyboardButton("Back", callback_data="plinko_back")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif action == "bet":
        risk_level = data[2]
        bet_amount = float(data[3])
        
        # Start the plinko game
        await play_plinko(update, context, risk_level, bet_amount)
    
    elif action == "custom":
        risk_level = data[2]
        
        # Store in context that we're waiting for a custom amount
        context.user_data["plinko_action"] = "custom_bet"
        context.user_data["plinko_risk"] = risk_level
        
        message = (
            f"🎮 Plinko - {PLINKO_RISK_LEVELS[risk_level]['description']} 🎮\n\n"
            "Enter your bet amount:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("Cancel", callback_data="plinko_back")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif action == "back":
        # Return to main plinko info
        message = (
            "🎮 Plinko Game 🎮\n\n"
            "Drop a ball and watch it bounce through pegs to determine your prize!\n\n"
            "How to play:\n"
            "1. Choose a risk level (Low, Medium, High)\n"
            "2. Place your bet\n"
            "3. Watch the ball drop and see where it lands\n\n"
            "Usage: /plinko [risk_level] [amount]\n"
            "Example: /plinko medium 10\n\n"
            "Risk Levels:\n"
            "• Low: Safer bets with smaller payouts (max 1.4x)\n"
            "• Medium: Balanced risk and reward (max 5.6x)\n"
            "• High: High risk with potential big wins (max 13.0x)"
        )
        
        # Create keyboard for quick bets
        keyboard = [
            [
                InlineKeyboardButton("Low Risk", callback_data="plinko_risk_low"),
                InlineKeyboardButton("Medium Risk", callback_data="plinko_risk_medium"),
                InlineKeyboardButton("High Risk", callback_data="plinko_risk_high")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif action == "again":
        risk_level = data[2]
        bet_amount = float(data[3])
        
        # Play again with the same settings
        await play_plinko(update, context, risk_level, bet_amount)

async def plinko_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plinko action messages"""
    if "plinko_action" not in context.user_data:
        return False
    
    action = context.user_data["plinko_action"]
    
    if action == "custom_bet":
        risk_level = context.user_data["plinko_risk"]
        
        try:
            bet_amount = float(update.message.text.strip())
            if bet_amount <= 0:
                await update.message.reply_text("Bet amount must be positive")
                return True
        except ValueError:
            await update.message.reply_text("Bet amount must be a number")
            return True
        
        # Clear the plinko action
        del context.user_data["plinko_action"]
        del context.user_data["plinko_risk"]
        
        # Start the plinko game
        await play_plinko(update, context, risk_level, bet_amount)
        return True
    
    return False

async def play_plinko(update: Update, context: ContextTypes.DEFAULT_TYPE, risk_level, bet_amount):
    """Play a round of plinko"""
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.callback_query.from_user.id
    
    # Get user data
    user = await get_user(user_id)
    
    # Check if user has enough balance
    if user["balance"] < bet_amount:
        message = f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    # Deduct bet amount from user balance
    await update_user_balance(user_id, -bet_amount)
    await record_transaction(user_id, -bet_amount, "bet")
    
    # Show initial animation
    message = (
        f"🎮 Plinko - {PLINKO_RISK_LEVELS[risk_level]['description']} 🎮\n\n"
        f"Bet: {format_money(bet_amount)}\n\n"
        "Dropping the ball..."
    )
    
    if hasattr(update, 'callback_query') and update.callback_query:
        game_message = await update.callback_query.edit_message_text(message)
    else:
        game_message = await update.message.reply_text(message)
    
    # Simulate the ball dropping through the plinko board
    for i, frame in enumerate(PLINKO_FRAMES):
        # Add a small delay between frames
        if i > 0:
            await context.bot.edit_message_text(
                chat_id=game_message.chat_id,
                message_id=game_message.message_id,
                text=f"🎮 Plinko - {PLINKO_RISK_LEVELS[risk_level]['description']} 🎮\n\n"
                     f"Bet: {format_money(bet_amount)}\n\n"
                     f"{''.join(frame)}"
            )
    
    # Determine the final position and multiplier
    multipliers = PLINKO_RISK_LEVELS[risk_level]["multipliers"]
    final_position = random.randint(0, len(multipliers) - 1)
    multiplier = multipliers[final_position]
    
    # Calculate winnings
    winnings = bet_amount * multiplier
    
    # Record game result
    game_id = await record_game(
        user_id, 
        "plinko", 
        bet_amount, 
        "win" if winnings > 0 else "loss", 
        winnings
    )
    
    # Update user balance if won
    if winnings > 0:
        await update_user_balance(user_id, winnings)
        await record_transaction(user_id, winnings, "win", game_id)
    
    # Get updated user data
    user = await get_user(user_id)
    
    # Create final result display
    result_display = ["⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛"]
    for row in PLINKO_FRAMES[-1][1:-1]:
        result_display.append(row)
    
    # Add the multipliers row
    multiplier_row = "⬛"
    for m in multipliers:
        if m == 0:
            multiplier_row += "0️⃣"
        else:
            multiplier_row += f"{m:.1f}".replace(".", "").ljust(2, "0")
    multiplier_row += "⬛"
    result_display.append(multiplier_row)
    
    # Highlight the winning multiplier
    highlight_row = "⬛" + "⬛" * final_position + "🔴" + "⬛" * (len(multipliers) - final_position - 1) + "⬛"
    result_display.append(highlight_row)
    
    # Create result message
    if winnings > 0:
        result_text = (
            f"🎮 Plinko Result 🎮\n\n"
            f"Bet: {format_money(bet_amount)}\n"
            f"Multiplier: {multiplier}x\n"
            f"Win: {format_money(winnings)}\n"
            f"Balance: {format_money(user['balance'])}\n\n"
            f"{''.join(result_display)}"
        )
    else:
        result_text = (
            f"🎮 Plinko Result 🎮\n\n"
            f"Bet: {format_money(bet_amount)}\n"
            f"Multiplier: {multiplier}x\n"
            f"Loss: {format_money(bet_amount)}\n"
            f"Balance: {format_money(user['balance'])}\n\n"
            f"{''.join(result_display)}"
        )
    
    # Create play again keyboard
    keyboard = [
        [
            InlineKeyboardButton("Play Again", callback_data=f"plinko_again_{risk_level}_{bet_amount}"),
            InlineKeyboardButton("Change Bet", callback_data=f"plinko_risk_{risk_level}")
        ],
        [
            InlineKeyboardButton("Change Risk", callback_data="plinko_back")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.edit_message_text(
        chat_id=game_message.chat_id,
        message_id=game_message.message_id,
        text=result_text,
        reply_markup=reply_markup
    )