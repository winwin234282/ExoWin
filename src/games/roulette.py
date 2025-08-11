import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, record_game
from src.utils.formatting import format_money

# Roulette wheel numbers and their colors
ROULETTE_WHEEL = {
    0: "green",
    1: "red", 2: "black", 3: "red", 4: "black", 5: "red", 6: "black", 7: "red", 8: "black",
    9: "red", 10: "black", 11: "black", 12: "red", 13: "black", 14: "red", 15: "black",
    16: "red", 17: "black", 18: "red", 19: "red", 20: "black", 21: "red", 22: "black",
    23: "red", 24: "black", 25: "red", 26: "black", 27: "red", 28: "black", 29: "black",
    30: "red", 31: "black", 32: "red", 33: "black", 34: "red", 35: "black", 36: "red"
}

# Bet types and their payouts
BET_TYPES = {
    "number": {"payout": 35, "description": "Bet on a specific number (0-36)"},
    "red": {"payout": 1, "description": "Bet on red numbers"},
    "black": {"payout": 1, "description": "Bet on black numbers"},
    "even": {"payout": 1, "description": "Bet on even numbers (not 0)"},
    "odd": {"payout": 1, "description": "Bet on odd numbers"},
    "low": {"payout": 1, "description": "Bet on numbers 1-18"},
    "high": {"payout": 1, "description": "Bet on numbers 19-36"},
    "dozen1": {"payout": 2, "description": "Bet on numbers 1-12"},
    "dozen2": {"payout": 2, "description": "Bet on numbers 13-24"},
    "dozen3": {"payout": 2, "description": "Bet on numbers 25-36"},
    "column1": {"payout": 2, "description": "Bet on numbers 1,4,7,10,13,16,19,22,25,28,31,34"},
    "column2": {"payout": 2, "description": "Bet on numbers 2,5,8,11,14,17,20,23,26,29,32,35"},
    "column3": {"payout": 2, "description": "Bet on numbers 3,6,9,12,15,18,21,24,27,30,33,36"}
}

def is_winning_bet(bet_type, bet_value, result):
    """Check if a bet is a winner based on the roulette result"""
    if bet_type == "number":
        return int(bet_value) == result
    elif bet_type == "red":
        return ROULETTE_WHEEL[result] == "red"
    elif bet_type == "black":
        return ROULETTE_WHEEL[result] == "black"
    elif bet_type == "even":
        return result != 0 and result % 2 == 0
    elif bet_type == "odd":
        return result % 2 == 1
    elif bet_type == "low":
        return 1 <= result <= 18
    elif bet_type == "high":
        return 19 <= result <= 36
    elif bet_type == "dozen1":
        return 1 <= result <= 12
    elif bet_type == "dozen2":
        return 13 <= result <= 24
    elif bet_type == "dozen3":
        return 25 <= result <= 36
    elif bet_type == "column1":
        return result % 3 == 1
    elif bet_type == "column2":
        return result % 3 == 2
    elif bet_type == "column3":
        return result % 3 == 0 and result != 0
    return False

async def roulette_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /roulette command"""
    # Show roulette betting options
    message = (
        "🎲 Roulette Game 🎲\n\n"
        "Place your bet using the format:\n"
        "/roulette [bet_type] [bet_value] [amount]\n\n"
        "Examples:\n"
        "/roulette number 17 10 - Bet $10 on number 17\n"
        "/roulette red 10 - Bet $10 on red\n"
        "/roulette even 5 - Bet $5 on even numbers\n\n"
        "Available bet types:"
    )
    
    for bet_type, info in BET_TYPES.items():
        message += f"\n• {bet_type}: {info['description']} (Payout {info['payout']}:1)"
    
    # Create keyboard for quick bets
    keyboard = [
        [
            InlineKeyboardButton("Red", callback_data="roulette_bet_red"),
            InlineKeyboardButton("Black", callback_data="roulette_bet_black"),
            InlineKeyboardButton("Green (0)", callback_data="roulette_bet_number_0")
        ],
        [
            InlineKeyboardButton("Even", callback_data="roulette_bet_even"),
            InlineKeyboardButton("Odd", callback_data="roulette_bet_odd")
        ],
        [
            InlineKeyboardButton("1-18", callback_data="roulette_bet_low"),
            InlineKeyboardButton("19-36", callback_data="roulette_bet_high")
        ],
        [
            InlineKeyboardButton("1st Dozen (1-12)", callback_data="roulette_bet_dozen1"),
            InlineKeyboardButton("2nd Dozen (13-24)", callback_data="roulette_bet_dozen2"),
            InlineKeyboardButton("3rd Dozen (25-36)", callback_data="roulette_bet_dozen3")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if not context.args:
        await update.message.reply_text(message, reply_markup=reply_markup)
        return
    
    # Process bet if arguments are provided
    if len(context.args) < 2:
        await update.message.reply_text("Invalid bet format. Use /roulette for help.")
        return
    
    bet_type = context.args[0].lower()
    
    # Validate bet type
    if bet_type not in BET_TYPES:
        await update.message.reply_text(f"Invalid bet type: {bet_type}. Use /roulette for help.")
        return
    
    # Handle different bet formats
    if bet_type == "number":
        if len(context.args) < 3:
            await update.message.reply_text("For number bets, use: /roulette number [0-36] [amount]")
            return
        
        try:
            bet_value = int(context.args[1])
            if bet_value < 0 or bet_value > 36:
                await update.message.reply_text("Number must be between 0 and 36")
                return
            bet_amount = float(context.args[2])
        except ValueError:
            await update.message.reply_text("Invalid number or bet amount")
            return
    else:
        bet_value = None
        try:
            bet_amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("Invalid bet amount")
            return
    
    if bet_amount <= 0:
        await update.message.reply_text("Bet amount must be positive")
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
    
    # Spin the roulette wheel
    spinning_message = await update.message.reply_text("🎲 Spinning the roulette wheel...")
    
    # Simulate spinning animation
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=spinning_message.message_id,
        text="🎲 Spinning the roulette wheel...\n⚫️ ⚫️ ⚫️"
    )
    
    # Determine the result
    result = random.randint(0, 36)
    result_color = ROULETTE_WHEEL[result]
    
    # Check if bet wins
    if bet_type == "number":
        won = result == bet_value
    else:
        won = is_winning_bet(bet_type, bet_value, result)
    
    # Calculate winnings
    if won:
        winnings = bet_amount * (BET_TYPES[bet_type]["payout"] + 1)  # +1 to include original bet
    else:
        winnings = 0
    
    # Record game result
    game_id = await record_game(
        user["user_id"], 
        "roulette", 
        bet_amount, 
        "win" if won else "loss", 
        winnings if won else 0
    )
    
    # Update user balance if won
    if won:
        await update_user_balance(user["user_id"], winnings)
        await record_transaction(user["user_id"], winnings, "win", game_id)
    
    # Get updated user data
    user = await get_user(user["user_id"])
    
    # Create result message
    result_emoji = "🟢" if result_color == "green" else "🔴" if result_color == "red" else "⚫️"
    
    bet_description = f"number {bet_value}" if bet_type == "number" else bet_type
    
    if won:
        result_message = (
            f"🎲 The ball landed on {result} {result_emoji}\n\n"
            f"🎉 You won! Your bet on {bet_description} was successful.\n"
            f"You bet: {format_money(bet_amount)}\n"
            f"You won: {format_money(winnings)}\n"
            f"Your balance: {format_money(user['balance'])}"
        )
    else:
        result_message = (
            f"🎲 The ball landed on {result} {result_emoji}\n\n"
            f"😢 You lost! Your bet on {bet_description} was unsuccessful.\n"
            f"You bet: {format_money(bet_amount)}\n"
            f"Your balance: {format_money(user['balance'])}"
        )
    
    # Create play again keyboard
    keyboard = [
        [
            InlineKeyboardButton("Play Again", callback_data=f"roulette_again_{bet_type}_{bet_value}_{bet_amount}"),
            InlineKeyboardButton("Double Bet", callback_data=f"roulette_again_{bet_type}_{bet_value}_{bet_amount*2}")
        ],
        [
            InlineKeyboardButton("New Bet", callback_data="roulette_new")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=spinning_message.message_id,
        text=result_message,
        reply_markup=reply_markup
    )

async def roulette_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle roulette callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    # Handle bet selection
    if data[1] == "bet":
        if data[2] == "number":
            # Show number selection keyboard
            keyboard = []
            row = []
            for i in range(37):
                row.append(InlineKeyboardButton(str(i), callback_data=f"roulette_number_{i}"))
                if len(row) == 6:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            keyboard.append([InlineKeyboardButton("Back", callback_data="roulette_new")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Choose a number (0-36):", reply_markup=reply_markup)
            return
        
        # For other bet types, show amount selection
        bet_type = data[2]
        bet_value = data[3] if len(data) > 3 else None
        
        keyboard = []
        for amount in [1, 5, 10, 25, 50, 100]:
            keyboard.append([InlineKeyboardButton(
                f"${amount}", 
                callback_data=f"roulette_amount_{bet_type}_{bet_value}_{amount}" if bet_value else f"roulette_amount_{bet_type}_{amount}"
            )])
        keyboard.append([InlineKeyboardButton("Back", callback_data="roulette_new")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(f"You selected {bet_type}. Choose your bet amount:", reply_markup=reply_markup)
        return
    
    # Handle number selection
    if data[1] == "number":
        number = data[2]
        keyboard = []
        for amount in [1, 5, 10, 25, 50, 100]:
            keyboard.append([InlineKeyboardButton(
                f"${amount}", 
                callback_data=f"roulette_amount_number_{number}_{amount}"
            )])
        keyboard.append([InlineKeyboardButton("Back", callback_data="roulette_bet_number")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(f"You selected number {number}. Choose your bet amount:", reply_markup=reply_markup)
        return
    
    # Handle amount selection and place bet
    if data[1] == "amount":
        bet_type = data[2]
        
        if bet_type == "number":
            bet_value = int(data[3])
            bet_amount = float(data[4])
        else:
            bet_value = None
            bet_amount = float(data[3])
        
        user = await get_user(query.from_user.id)
        
        if user["balance"] < bet_amount:
            await query.edit_message_text(
                f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
            )
            return
        
        # Deduct bet amount from user balance
        await update_user_balance(user["user_id"], -bet_amount)
        await record_transaction(user["user_id"], -bet_amount, "bet")
        
        # Spin the roulette wheel
        await query.edit_message_text("🎲 Spinning the roulette wheel...")
        
        # Simulate spinning animation
        await query.edit_message_text(
            text="🎲 Spinning the roulette wheel...\n⚫️ ⚫️ ⚫️"
        )
        
        # Determine the result
        result = random.randint(0, 36)
        result_color = ROULETTE_WHEEL[result]
        
        # Check if bet wins
        if bet_type == "number":
            won = result == bet_value
        else:
            won = is_winning_bet(bet_type, bet_value, result)
        
        # Calculate winnings
        if won:
            winnings = bet_amount * (BET_TYPES[bet_type]["payout"] + 1)  # +1 to include original bet
        else:
            winnings = 0
        
        # Record game result
        game_id = await record_game(
            user["user_id"], 
            "roulette", 
            bet_amount, 
            "win" if won else "loss", 
            winnings if won else 0
        )
        
        # Update user balance if won
        if won:
            await update_user_balance(user["user_id"], winnings)
            await record_transaction(user["user_id"], winnings, "win", game_id)
        
        # Get updated user data
        user = await get_user(user["user_id"])
        
        # Create result message
        result_emoji = "🟢" if result_color == "green" else "🔴" if result_color == "red" else "⚫️"
        
        bet_description = f"number {bet_value}" if bet_type == "number" else bet_type
        
        if won:
            result_message = (
                f"🎲 The ball landed on {result} {result_emoji}\n\n"
                f"🎉 You won! Your bet on {bet_description} was successful.\n"
                f"You bet: {format_money(bet_amount)}\n"
                f"You won: {format_money(winnings)}\n"
                f"Your balance: {format_money(user['balance'])}"
            )
        else:
            result_message = (
                f"🎲 The ball landed on {result} {result_emoji}\n\n"
                f"😢 You lost! Your bet on {bet_description} was unsuccessful.\n"
                f"You bet: {format_money(bet_amount)}\n"
                f"Your balance: {format_money(user['balance'])}"
            )
        
        # Create play again keyboard
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data=f"roulette_again_{bet_type}_{bet_value}_{bet_amount}"),
                InlineKeyboardButton("Double Bet", callback_data=f"roulette_again_{bet_type}_{bet_value}_{bet_amount*2}")
            ],
            [
                InlineKeyboardButton("New Bet", callback_data="roulette_new")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=result_message,
            reply_markup=reply_markup
        )
        return
    
    # Handle "play again" option
    if data[1] == "again":
        bet_type = data[2]
        bet_value = data[3] if bet_type == "number" else None
        bet_amount = float(data[4] if bet_type == "number" else data[3])
        
        # Redirect to amount selection with the same bet
        if bet_type == "number":
            callback_data = f"roulette_amount_number_{bet_value}_{bet_amount}"
        else:
            callback_data = f"roulette_amount_{bet_type}_{bet_amount}"
        
        # Create a new callback query with the redirect data
        context.user_data["redirect_callback"] = callback_data
        await roulette_callback(update, context)
        return
    
    # Handle "new bet" option
    if data[1] == "new":
        # Show roulette betting options
        message = (
            "🎲 Roulette Game 🎲\n\n"
            "Choose your bet type:"
        )
        
        # Create keyboard for quick bets
        keyboard = [
            [
                InlineKeyboardButton("Red", callback_data="roulette_bet_red"),
                InlineKeyboardButton("Black", callback_data="roulette_bet_black"),
                InlineKeyboardButton("Green (0)", callback_data="roulette_bet_number_0")
            ],
            [
                InlineKeyboardButton("Even", callback_data="roulette_bet_even"),
                InlineKeyboardButton("Odd", callback_data="roulette_bet_odd")
            ],
            [
                InlineKeyboardButton("1-18", callback_data="roulette_bet_low"),
                InlineKeyboardButton("19-36", callback_data="roulette_bet_high")
            ],
            [
                InlineKeyboardButton("1st Dozen (1-12)", callback_data="roulette_bet_dozen1"),
                InlineKeyboardButton("2nd Dozen (13-24)", callback_data="roulette_bet_dozen2"),
                InlineKeyboardButton("3rd Dozen (25-36)", callback_data="roulette_bet_dozen3")
            ],
            [
                InlineKeyboardButton("Pick a Number (0-36)", callback_data="roulette_bet_number")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        return