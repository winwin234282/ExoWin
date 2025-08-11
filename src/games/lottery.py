import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, record_game
from src.utils.formatting import format_money

# Store lottery data
lottery_data = {
    "active": False,
    "pot": 0.0,
    "ticket_price": 5.0,  # $5 per ticket
    "participants": {},  # {user_id: number_of_tickets}
    "end_time": None,
    "last_winner": None,
    "last_pot": 0.0
}

async def lottery_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /lottery command"""
    if not context.args:
        # Show lottery status
        await show_lottery_status(update, context)
        return
    
    command = context.args[0].lower()
    
    if command == "buy":
        # Buy lottery tickets
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /lottery buy [number_of_tickets]\n"
                "Example: /lottery buy 5"
            )
            return
        
        try:
            num_tickets = int(context.args[1])
            if num_tickets <= 0:
                await update.message.reply_text("Number of tickets must be positive")
                return
        except ValueError:
            await update.message.reply_text("Number of tickets must be a number")
            return
        
        await buy_lottery_tickets(update, context, num_tickets)
    
    elif command == "start" and await is_admin(update.effective_user.id):
        # Start a new lottery (admin only)
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /lottery start [duration_hours]\n"
                "Example: /lottery start 24"
            )
            return
        
        try:
            duration_hours = int(context.args[1])
            if duration_hours <= 0:
                await update.message.reply_text("Duration must be positive")
                return
        except ValueError:
            await update.message.reply_text("Duration must be a number")
            return
        
        await start_lottery(update, context, duration_hours)
    
    elif command == "end" and await is_admin(update.effective_user.id):
        # End the current lottery (admin only)
        await end_lottery(update, context)
    
    else:
        await update.message.reply_text(
            "Lottery commands:\n"
            "/lottery - Show lottery status\n"
            "/lottery buy [number_of_tickets] - Buy lottery tickets\n"
            "\nAdmin commands:\n"
            "/lottery start [duration_hours] - Start a new lottery\n"
            "/lottery end - End the current lottery"
        )

async def is_admin(user_id):
    """Check if a user is an admin"""
    # Only @OgSellz is admin
    return user_id == 123456789  # Replace with actual user ID of @OgSellz

async def show_lottery_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the current lottery status"""
    if not lottery_data["active"]:
        if lottery_data["last_winner"]:
            # Show last lottery results
            message = (
                "🎟️ Lottery Results 🎟️\n\n"
                f"The last lottery has ended!\n"
                f"Total pot: {format_money(lottery_data['last_pot'])}\n"
                f"Winner: {lottery_data['last_winner']['name']}\n"
                f"Winning amount: {format_money(lottery_data['last_pot'])}\n\n"
                "A new lottery will start soon!"
            )
        else:
            message = (
                "🎟️ No Active Lottery 🎟️\n\n"
                "There is no active lottery at the moment.\n"
                "An admin will start a new lottery soon!"
            )
    else:
        # Calculate time remaining
        time_remaining = lottery_data["end_time"] - datetime.now()
        hours, remainder = divmod(time_remaining.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Count total tickets
        total_tickets = sum(lottery_data["participants"].values())
        
        message = (
            "🎟️ Active Lottery 🎟️\n\n"
            f"Current pot: {format_money(lottery_data['pot'])}\n"
            f"Ticket price: {format_money(lottery_data['ticket_price'])}\n"
            f"Total tickets sold: {total_tickets}\n"
            f"Time remaining: {int(hours)}h {int(minutes)}m {int(seconds)}s\n\n"
            "Your tickets: "
        )
        
        user_id = update.effective_user.id
        if user_id in lottery_data["participants"]:
            user_tickets = lottery_data["participants"][user_id]
            win_chance = (user_tickets / total_tickets) * 100 if total_tickets > 0 else 0
            message += f"{user_tickets} ({win_chance:.2f}% chance to win)\n\n"
        else:
            message += "0 (0% chance to win)\n\n"
        
        message += "Use /lottery buy [number] to purchase tickets!"
    
    # Create keyboard
    keyboard = []
    if lottery_data["active"]:
        keyboard.append([
            InlineKeyboardButton("Buy 1 Ticket", callback_data="lottery_buy_1"),
            InlineKeyboardButton("Buy 5 Tickets", callback_data="lottery_buy_5")
        ])
        keyboard.append([
            InlineKeyboardButton("Buy 10 Tickets", callback_data="lottery_buy_10"),
            InlineKeyboardButton("Buy 20 Tickets", callback_data="lottery_buy_20")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def buy_lottery_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE, num_tickets):
    """Buy lottery tickets"""
    if not lottery_data["active"]:
        await update.message.reply_text("There is no active lottery at the moment.")
        return
    
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    total_cost = num_tickets * lottery_data["ticket_price"]
    
    if user["balance"] < total_cost:
        await update.message.reply_text(
            f"You don't have enough funds. Your balance: {format_money(user['balance'])}\n"
            f"Cost for {num_tickets} tickets: {format_money(total_cost)}"
        )
        return
    
    # Deduct cost from user balance
    await update_user_balance(user_id, -total_cost)
    await record_transaction(user_id, -total_cost, "lottery_tickets")
    
    # Add tickets to lottery
    if user_id in lottery_data["participants"]:
        lottery_data["participants"][user_id] += num_tickets
    else:
        lottery_data["participants"][user_id] = num_tickets
    
    # Add to pot (80% goes to pot, 20% to house)
    lottery_data["pot"] += total_cost * 0.8
    
    # Get updated user data
    user = await get_user(user_id)
    
    # Calculate win chance
    total_tickets = sum(lottery_data["participants"].values())
    user_tickets = lottery_data["participants"][user_id]
    win_chance = (user_tickets / total_tickets) * 100
    
    message = (
        f"You purchased {num_tickets} lottery tickets for {format_money(total_cost)}!\n\n"
        f"Your tickets: {user_tickets}\n"
        f"Win chance: {win_chance:.2f}%\n"
        f"Current pot: {format_money(lottery_data['pot'])}\n"
        f"Your balance: {format_money(user['balance'])}"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("Buy More Tickets", callback_data="lottery_buy_more"),
            InlineKeyboardButton("Lottery Status", callback_data="lottery_status")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def start_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE, duration_hours):
    """Start a new lottery"""
    if lottery_data["active"]:
        await update.message.reply_text("A lottery is already active. End it first.")
        return
    
    # Set up new lottery
    lottery_data["active"] = True
    lottery_data["pot"] = 0.0
    lottery_data["participants"] = {}
    lottery_data["end_time"] = datetime.now() + timedelta(hours=duration_hours)
    
    message = (
        "🎟️ New Lottery Started! 🎟️\n\n"
        f"Duration: {duration_hours} hours\n"
        f"Ticket price: {format_money(lottery_data['ticket_price'])}\n"
        f"Use /lottery buy [number] to purchase tickets!\n\n"
        f"The lottery will end on {lottery_data['end_time'].strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await update.message.reply_text(message)
    
    # Schedule lottery end
    context.job_queue.run_once(
        lambda _: asyncio.create_task(auto_end_lottery(context)),
        duration_hours * 3600,
        name="lottery_end"
    )

async def end_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End the current lottery and pick a winner"""
    if not lottery_data["active"]:
        await update.message.reply_text("There is no active lottery to end.")
        return
    
    # Cancel scheduled end if it exists
    for job in context.job_queue.get_jobs_by_name("lottery_end"):
        job.schedule_removal()
    
    # Pick a winner
    await pick_lottery_winner(update, context)

async def auto_end_lottery(context):
    """Automatically end the lottery when time is up"""
    if lottery_data["active"]:
        # Create a dummy update to pass to pick_lottery_winner
        # In a real bot, you'd announce this in a specific channel
        await pick_lottery_winner(None, context, auto=True)

async def pick_lottery_winner(update, context, auto=False):
    """Pick a lottery winner"""
    if not lottery_data["participants"]:
        message = "The lottery has ended, but there were no participants. No winner was selected."
        
        # Reset lottery data
        lottery_data["active"] = False
        lottery_data["last_winner"] = None
        lottery_data["last_pot"] = 0.0
        
        if auto:
            # Announce in a channel or to all participants
            pass
        else:
            await update.message.reply_text(message)
        return
    
    # Create a list of tickets where each user appears according to their number of tickets
    tickets = []
    for user_id, num_tickets in lottery_data["participants"].items():
        tickets.extend([user_id] * num_tickets)
    
    # Pick a random winner
    winner_id = random.choice(tickets)
    winner = await get_user(winner_id)
    
    # Award the pot to the winner
    pot_amount = lottery_data["pot"]
    await update_user_balance(winner_id, pot_amount)
    await record_transaction(winner_id, pot_amount, "lottery_win")
    
    # Record game result
    await record_game(
        winner_id, 
        "lottery", 
        lottery_data["participants"].get(winner_id, 0) * lottery_data["ticket_price"], 
        "win", 
        pot_amount
    )
    
    # Store last winner info
    lottery_data["last_winner"] = {
        "id": winner_id,
        "name": winner.get("username", f"User {winner_id}")
    }
    lottery_data["last_pot"] = pot_amount
    
    # Reset lottery data
    lottery_data["active"] = False
    
    # Create winner message
    total_tickets = sum(lottery_data["participants"].values())
    winner_tickets = lottery_data["participants"].get(winner_id, 0)
    win_chance = (winner_tickets / total_tickets) * 100
    
    message = (
        "🎉 Lottery Results 🎉\n\n"
        f"Winner: {lottery_data['last_winner']['name']}\n"
        f"Prize: {format_money(pot_amount)}\n"
        f"Winning tickets: {winner_tickets}/{total_tickets} ({win_chance:.2f}% chance)\n\n"
        "Congratulations to the winner! A new lottery will start soon."
    )
    
    if auto:
        # Announce in a channel or to all participants
        pass
    else:
        await update.message.reply_text(message)

async def lottery_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lottery callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    
    if data[1] == "buy":
        if len(data) > 2:
            try:
                num_tickets = int(data[2])
                await buy_lottery_tickets(update, context, num_tickets)
                return
            except ValueError:
                pass
    
    elif data[1] == "buy_more":
        # Show ticket purchase options
        keyboard = [
            [
                InlineKeyboardButton("Buy 1 Ticket", callback_data="lottery_buy_1"),
                InlineKeyboardButton("Buy 5 Tickets", callback_data="lottery_buy_5")
            ],
            [
                InlineKeyboardButton("Buy 10 Tickets", callback_data="lottery_buy_10"),
                InlineKeyboardButton("Buy 20 Tickets", callback_data="lottery_buy_20")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "How many lottery tickets would you like to buy?",
            reply_markup=reply_markup
        )
        return
    
    elif data[1] == "status":
        # Show lottery status
        await show_lottery_status(update, context)
        return
    
    # Default fallback
    await query.edit_message_text("Invalid option or lottery has ended.")