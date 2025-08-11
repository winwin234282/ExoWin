import random
import asyncio
import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, record_game
from src.utils.formatting import format_money

# Store active crash games
active_crash_games = {}

class CrashGame:
    def __init__(self, chat_id, message_id, context):
        self.chat_id = chat_id
        self.message_id = message_id
        self.context = context
        self.players = {}  # {user_id: {"bet": amount, "cashed_out": False, "multiplier": None}}
        self.is_running = False
        self.current_multiplier = 1.0
        self.crash_point = self.generate_crash_point()
        self.start_time = None
        self.task = None
    
    def generate_crash_point(self):
        """Generate a random crash point with house edge"""
        # House edge of approximately 5%
        # This formula creates a distribution where most crashes happen below 2x
        # but occasionally allows for very high multipliers
        r = random.random()
        if r < 0.01:  # 1% chance for a very early crash (below 1.1x)
            return random.uniform(1.0, 1.1)
        elif r < 0.05:  # 4% chance for an early crash (1.1x to 1.5x)
            return random.uniform(1.1, 1.5)
        else:  # 95% chance for a normal distribution
            # Use a formula that gives an expected value slightly below 2.0
            # e = 0.05 (house edge)
            # Expected value = (1-e)/e = 19
            # Using a distribution where: crash_point = 0.9 / (random.random() ^ 0.7)
            return 0.9 / (random.random() ** 0.7)
    
    def add_player(self, user_id, bet_amount):
        """Add a player to the game"""
        if not self.is_running:
            self.players[user_id] = {
                "bet": bet_amount,
                "cashed_out": False,
                "multiplier": None
            }
            return True
        return False
    
    def cash_out(self, user_id):
        """Player cashes out at current multiplier"""
        if (user_id in self.players and 
            self.is_running and 
            not self.players[user_id]["cashed_out"]):
            
            self.players[user_id]["cashed_out"] = True
            self.players[user_id]["multiplier"] = self.current_multiplier
            return True
        return False
    
    def get_winnings(self, user_id):
        """Calculate winnings for a player"""
        if user_id in self.players and self.players[user_id]["cashed_out"]:
            multiplier = self.players[user_id]["multiplier"]
            bet = self.players[user_id]["bet"]
            return bet * multiplier
        return 0
    
    async def start_game(self):
        """Start the crash game"""
        if not self.players:
            return False
        
        self.is_running = True
        self.current_multiplier = 1.0
        
        # Create and start the game task
        self.task = asyncio.create_task(self.run_game())
        return True
    
    async def run_game(self):
        """Run the crash game simulation"""
        try:
            # Initial game state
            await self.update_game_display()
            
            # Increase multiplier until crash point
            while self.current_multiplier < self.crash_point:
                # Wait a bit (shorter intervals at the beginning, longer as multiplier increases)
                await asyncio.sleep(0.1 + (self.current_multiplier / 50))
                
                # Increase multiplier (slower growth at higher values)
                growth_factor = max(0.05, 0.2 - (self.current_multiplier / 50))
                self.current_multiplier += growth_factor
                
                # Update display
                await self.update_game_display()
                
                # Check if all players cashed out
                if all(player["cashed_out"] for player in self.players.values()):
                    break
            
            # Game crashed
            await self.game_crashed()
        except Exception as e:
            print(f"Error in crash game: {e}")
            await self.game_crashed()
    
    async def update_game_display(self):
        """Update the game display"""
        # Create the game display message
        multiplier_text = f"{self.current_multiplier:.2f}x"
        
        message = (
            f"🚀 Crash Game 🚀\n\n"
            f"Current Multiplier: {multiplier_text}\n\n"
            f"Players:\n"
        )
        
        for user_id, data in self.players.items():
            user = await get_user(user_id)
            username = user.get("username", f"User {user_id}")
            
            if data["cashed_out"]:
                cashout_multiplier = f"{data['multiplier']:.2f}x"
                winnings = data["bet"] * data["multiplier"]
                message += f"✅ {username}: {format_money(data['bet'])} (Cashed out at {cashout_multiplier}, won {format_money(winnings)})\n"
            else:
                message += f"🔄 {username}: {format_money(data['bet'])}\n"
        
        # Create keyboard
        keyboard = []
        
        # Add cash out button for active players
        for user_id, data in self.players.items():
            if not data["cashed_out"] and self.is_running:
                keyboard.append([
                    InlineKeyboardButton("💰 Cash Out", callback_data=f"crash_cashout_{user_id}")
                ])
                break  # Only add one cash out button
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        # Update the message
        try:
            await self.context.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=message,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error updating crash game display: {e}")
    
    async def game_crashed(self):
        """Handle game crash"""
        self.is_running = False
        
        # Process results for all players
        for user_id, data in self.players.items():
            bet_amount = data["bet"]
            
            if data["cashed_out"]:
                # Player cashed out successfully
                multiplier = data["multiplier"]
                winnings = bet_amount * multiplier
                
                # Record game and transaction
                game_id = await record_game(
                    user_id, 
                    "crash", 
                    bet_amount, 
                    "win", 
                    winnings
                )
                
                # Update user balance
                await update_user_balance(user_id, winnings)
                await record_transaction(user_id, winnings, "win", game_id)
            else:
                # Player didn't cash out in time
                game_id = await record_game(
                    user_id, 
                    "crash", 
                    bet_amount, 
                    "loss", 
                    0
                )
        
        # Create final message
        crash_point_text = f"{self.crash_point:.2f}x"
        
        message = (
            f"💥 CRASHED AT {crash_point_text} 💥\n\n"
            f"Results:\n"
        )
        
        for user_id, data in self.players.items():
            user = await get_user(user_id)
            username = user.get("username", f"User {user_id}")
            
            if data["cashed_out"]:
                cashout_multiplier = f"{data['multiplier']:.2f}x"
                winnings = data["bet"] * data["multiplier"]
                message += f"✅ {username}: {format_money(data['bet'])} (Cashed out at {cashout_multiplier}, won {format_money(winnings)})\n"
            else:
                message += f"❌ {username}: {format_money(data['bet'])} (Didn't cash out in time)\n"
        
        # Add user balances
        message += "\nCurrent balances:\n"
        for user_id in self.players:
            user = await get_user(user_id)
            username = user.get("username", f"User {user_id}")
            message += f"{username}: {format_money(user['balance'])}\n"
        
        # Create keyboard for new game
        keyboard = [
            [
                InlineKeyboardButton("🎮 New Game", callback_data="crash_new")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Update the message
        try:
            await self.context.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=message,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error updating crash game final display: {e}")
        
        # Remove this game from active games
        if self.chat_id in active_crash_games:
            del active_crash_games[self.chat_id]

async def crash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /crash command"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if a game is already active in this chat
    if chat_id in active_crash_games:
        game = active_crash_games[chat_id]
        
        # If game is not running yet, allow joining
        if not game.is_running:
            if not context.args:
                await update.message.reply_text(
                    "Usage: /crash [amount] to join the current game"
                )
                return
            
            try:
                bet_amount = float(context.args[0])
                if bet_amount <= 0:
                    await update.message.reply_text("Bet amount must be positive")
                    return
            except ValueError:
                await update.message.reply_text("Bet amount must be a number")
                return
            
            user = await get_user(user_id)
            
            if user["balance"] < bet_amount:
                await update.message.reply_text(
                    f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
                )
                return
            
            # Deduct bet amount from user balance
            await update_user_balance(user_id, -bet_amount)
            await record_transaction(user_id, -bet_amount, "bet")
            
            # Add player to the game
            game.add_player(user_id, bet_amount)
            
            # Update the game display
            await game.update_game_display()
            
            # Notify the user
            await update.message.reply_text(f"You joined the crash game with {format_money(bet_amount)}")
        else:
            await update.message.reply_text("A game is already in progress. Wait for it to finish.")
        return
    
    # Start a new game
    if not context.args:
        # Just show the game info if no bet amount is provided
        message = (
            "🚀 Crash Game 🚀\n\n"
            "In this game, a multiplier increases until it crashes.\n"
            "Place a bet and cash out before the crash to win!\n"
            "The longer you wait, the higher the multiplier, but if you wait too long, you lose everything.\n\n"
            "Use /crash [amount] to start a new game or join an existing one."
        )
        await update.message.reply_text(message)
        return
    
    try:
        bet_amount = float(context.args[0])
        if bet_amount <= 0:
            await update.message.reply_text("Bet amount must be positive")
            return
    except ValueError:
        await update.message.reply_text("Bet amount must be a number")
        return
    
    user = await get_user(user_id)
    
    if user["balance"] < bet_amount:
        await update.message.reply_text(
            f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
        )
        return
    
    # Deduct bet amount from user balance
    await update_user_balance(user_id, -bet_amount)
    await record_transaction(user_id, -bet_amount, "bet")
    
    # Create initial game message
    message = (
        f"🚀 Crash Game 🚀\n\n"
        f"Waiting for players...\n\n"
        f"Players:\n"
        f"🔄 {update.effective_user.first_name}: {format_money(bet_amount)}\n\n"
        f"Use /crash [amount] to join this game.\n"
        f"The game will start in 30 seconds or when someone presses Start Game."
    )
    
    keyboard = [
        [
            InlineKeyboardButton("▶️ Start Game", callback_data="crash_start")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the initial message
    game_message = await update.message.reply_text(message, reply_markup=reply_markup)
    
    # Create a new crash game
    game = CrashGame(chat_id, game_message.message_id, context)
    game.add_player(user_id, bet_amount)
    
    # Store the game
    active_crash_games[chat_id] = game
    
    # Schedule game start after 30 seconds if not started manually
    context.job_queue.run_once(
        lambda _: asyncio.create_task(auto_start_crash_game(chat_id, context)),
        30,
        name=f"crash_autostart_{chat_id}"
    )

async def auto_start_crash_game(chat_id, context):
    """Automatically start a crash game if it hasn't started yet"""
    if chat_id in active_crash_games:
        game = active_crash_games[chat_id]
        if not game.is_running:
            await game.start_game()

async def crash_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crash game callback queries"""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    data = query.data.split("_")
    
    if data[1] == "start":
        # Start the game
        if chat_id in active_crash_games:
            game = active_crash_games[chat_id]
            if not game.is_running:
                # Cancel the auto-start job if it exists
                for job in context.job_queue.get_jobs_by_name(f"crash_autostart_{chat_id}"):
                    job.schedule_removal()
                
                # Start the game
                await game.start_game()
    
    elif data[1] == "cashout":
        # Cash out
        if chat_id in active_crash_games:
            game = active_crash_games[chat_id]
            cashout_user_id = int(data[2])
            
            # Only allow the player who placed the bet to cash out
            if user_id == cashout_user_id:
                game.cash_out(user_id)
                await game.update_game_display()
    
    elif data[1] == "new":
        # Show bet amount selection for new game
        keyboard = []
        for amount in [1, 5, 10, 25, 50, 100]:
            keyboard.append([
                InlineKeyboardButton(f"${amount}", callback_data=f"crash_bet_{amount}")
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🚀 Start a new Crash game\n\nSelect your bet amount:",
            reply_markup=reply_markup
        )
    
    elif data[1] == "bet":
        # Place bet for new game
        try:
            bet_amount = float(data[2])
        except (ValueError, IndexError):
            return
        
        user = await get_user(user_id)
        
        if user["balance"] < bet_amount:
            await query.edit_message_text(
                f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
            )
            return
        
        # Deduct bet amount from user balance
        await update_user_balance(user_id, -bet_amount)
        await record_transaction(user_id, -bet_amount, "bet")
        
        # Create initial game message
        message = (
            f"🚀 Crash Game 🚀\n\n"
            f"Waiting for players...\n\n"
            f"Players:\n"
            f"🔄 {query.from_user.first_name}: {format_money(bet_amount)}\n\n"
            f"Use /crash [amount] to join this game.\n"
            f"The game will start in 30 seconds or when someone presses Start Game."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("▶️ Start Game", callback_data="crash_start")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Update the message
        await query.edit_message_text(message, reply_markup=reply_markup)
        
        # Create a new crash game
        game = CrashGame(chat_id, query.message.message_id, context)
        game.add_player(user_id, bet_amount)
        
        # Store the game
        active_crash_games[chat_id] = game
        
        # Schedule game start after 30 seconds if not started manually
        context.job_queue.run_once(
            lambda _: asyncio.create_task(auto_start_crash_game(chat_id, context)),
            30,
            name=f"crash_autostart_{chat_id}"
        )