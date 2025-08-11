import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, record_game
from src.utils.formatting import format_money

# Card suits and values
SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def get_value(self):
        if self.rank == "A":
            return 11
        elif self.rank in ["J", "Q", "K"]:
            return 10
        else:
            return int(self.rank)

class Deck:
    def __init__(self):
        self.cards = []
        self.build()
    
    def build(self):
        self.cards = [Card(suit, rank) for suit in SUITS for rank in RANKS]
        random.shuffle(self.cards)
    
    def draw(self):
        if not self.cards:
            self.build()
        return self.cards.pop()

class BlackjackGame:
    def __init__(self, user_id, bet_amount):
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.deck = Deck()
        self.player_hand = []
        self.dealer_hand = []
        self.game_over = False
        self.result = None
        
        # Deal initial cards
        self.player_hand.append(self.deck.draw())
        self.dealer_hand.append(self.deck.draw())
        self.player_hand.append(self.deck.draw())
        self.dealer_hand.append(self.deck.draw())
        
        # Check for natural blackjack
        if self.get_hand_value(self.player_hand) == 21:
            if self.get_hand_value(self.dealer_hand) == 21:
                self.game_over = True
                self.result = "push"  # Tie
            else:
                self.game_over = True
                self.result = "blackjack"  # Player wins with blackjack (pays 3:2)
    
    def get_hand_value(self, hand):
        value = sum(card.get_value() for card in hand)
        
        # Adjust for aces if needed
        num_aces = sum(1 for card in hand if card.rank == "A")
        while value > 21 and num_aces > 0:
            value -= 10  # Convert an ace from 11 to 1
            num_aces -= 1
        
        return value
    
    def player_hit(self):
        self.player_hand.append(self.deck.draw())
        player_value = self.get_hand_value(self.player_hand)
        
        if player_value > 21:
            self.game_over = True
            self.result = "bust"  # Player busts
        
        return player_value
    
    def dealer_play(self):
        dealer_value = self.get_hand_value(self.dealer_hand)
        
        # Dealer hits until 17 or higher
        while dealer_value < 17:
            self.dealer_hand.append(self.deck.draw())
            dealer_value = self.get_hand_value(self.dealer_hand)
        
        player_value = self.get_hand_value(self.player_hand)
        
        if dealer_value > 21:
            self.result = "dealer_bust"  # Dealer busts, player wins
        elif dealer_value > player_value:
            self.result = "dealer_win"  # Dealer wins
        elif dealer_value < player_value:
            self.result = "player_win"  # Player wins
        else:
            self.result = "push"  # Tie
        
        self.game_over = True
        return dealer_value
    
    def get_winnings(self):
        if self.result == "blackjack":
            return self.bet_amount * 2.5  # Blackjack pays 3:2 (original bet + 1.5x)
        elif self.result in ["player_win", "dealer_bust"]:
            return self.bet_amount * 2  # Regular win pays 1:1 (original bet + 1x)
        elif self.result == "push":
            return self.bet_amount  # Push returns original bet
        else:
            return 0  # Loss
    
    def get_player_hand_display(self):
        return " ".join(str(card) for card in self.player_hand)
    
    def get_dealer_hand_display(self, hide_second=False):
        if hide_second and len(self.dealer_hand) > 1:
            return f"{self.dealer_hand[0]} 🂠"  # Show first card and hide second
        return " ".join(str(card) for card in self.dealer_hand)

# Store active games
active_games = {}

async def blackjack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /blackjack command"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /blackjack [amount]\n"
            "Example: /blackjack 10"
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
    
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    if user["balance"] < bet_amount:
        await update.message.reply_text(
            f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
        )
        return
    
    # Deduct bet amount from user balance
    await update_user_balance(user_id, -bet_amount)
    await record_transaction(user_id, -bet_amount, "bet")
    
    # Create a new blackjack game
    game = BlackjackGame(user_id, bet_amount)
    active_games[user_id] = game
    
    # Check if game is already over (natural blackjack)
    if game.game_over:
        winnings = game.get_winnings()
        
        # Record game result
        game_id = await record_game(
            user_id, 
            "blackjack", 
            bet_amount, 
            "win" if winnings > 0 else "loss", 
            winnings
        )
        
        # Update user balance with winnings
        if winnings > 0:
            await update_user_balance(user_id, winnings)
            await record_transaction(user_id, winnings, "win", game_id)
        
        # Get updated user data
        user = await get_user(user_id)
        
        # Create result message
        player_value = game.get_hand_value(game.player_hand)
        dealer_value = game.get_hand_value(game.dealer_hand)
        
        if game.result == "blackjack":
            message = (
                f"🃏 Blackjack! 🃏\n\n"
                f"Your hand: {game.get_player_hand_display()} ({player_value})\n"
                f"Dealer's hand: {game.get_dealer_hand_display()} ({dealer_value})\n\n"
                f"You got a natural blackjack! You win {format_money(winnings)}!\n"
                f"Your balance: {format_money(user['balance'])}"
            )
        else:  # Push (both have blackjack)
            message = (
                f"🃏 Push! 🃏\n\n"
                f"Your hand: {game.get_player_hand_display()} ({player_value})\n"
                f"Dealer's hand: {game.get_dealer_hand_display()} ({dealer_value})\n\n"
                f"Both you and the dealer got blackjack. Your bet is returned.\n"
                f"Your balance: {format_money(user['balance'])}"
            )
        
        # Create play again keyboard
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data=f"blackjack_new_{bet_amount}"),
                InlineKeyboardButton("Double Bet", callback_data=f"blackjack_new_{bet_amount*2}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        
        # Remove the game from active games
        del active_games[user_id]
        return
    
    # Show initial game state
    player_value = game.get_hand_value(game.player_hand)
    
    message = (
        f"🃏 Blackjack Game 🃏\n\n"
        f"Your hand: {game.get_player_hand_display()} ({player_value})\n"
        f"Dealer's hand: {game.get_dealer_hand_display(hide_second=True)}\n\n"
        f"Your bet: {format_money(bet_amount)}\n\n"
        f"What would you like to do?"
    )
    
    # Create action keyboard
    keyboard = [
        [
            InlineKeyboardButton("Hit", callback_data="blackjack_hit"),
            InlineKeyboardButton("Stand", callback_data="blackjack_stand")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def blackjack_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle blackjack callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action = query.data.split("_")[1]
    
    # Handle new game request
    if action == "new":
        bet_amount = float(query.data.split("_")[2])
        user = await get_user(user_id)
        
        if user["balance"] < bet_amount:
            await query.edit_message_text(
                f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
            )
            return
        
        # Deduct bet amount from user balance
        await update_user_balance(user_id, -bet_amount)
        await record_transaction(user_id, -bet_amount, "bet")
        
        # Create a new blackjack game
        game = BlackjackGame(user_id, bet_amount)
        active_games[user_id] = game
        
        # Check if game is already over (natural blackjack)
        if game.game_over:
            winnings = game.get_winnings()
            
            # Record game result
            game_id = await record_game(
                user_id, 
                "blackjack", 
                bet_amount, 
                "win" if winnings > 0 else "loss", 
                winnings
            )
            
            # Update user balance with winnings
            if winnings > 0:
                await update_user_balance(user_id, winnings)
                await record_transaction(user_id, winnings, "win", game_id)
            
            # Get updated user data
            user = await get_user(user_id)
            
            # Create result message
            player_value = game.get_hand_value(game.player_hand)
            dealer_value = game.get_hand_value(game.dealer_hand)
            
            if game.result == "blackjack":
                message = (
                    f"🃏 Blackjack! 🃏\n\n"
                    f"Your hand: {game.get_player_hand_display()} ({player_value})\n"
                    f"Dealer's hand: {game.get_dealer_hand_display()} ({dealer_value})\n\n"
                    f"You got a natural blackjack! You win {format_money(winnings)}!\n"
                    f"Your balance: {format_money(user['balance'])}"
                )
            else:  # Push (both have blackjack)
                message = (
                    f"🃏 Push! 🃏\n\n"
                    f"Your hand: {game.get_player_hand_display()} ({player_value})\n"
                    f"Dealer's hand: {game.get_dealer_hand_display()} ({dealer_value})\n\n"
                    f"Both you and the dealer got blackjack. Your bet is returned.\n"
                    f"Your balance: {format_money(user['balance'])}"
                )
            
            # Create play again keyboard
            keyboard = [
                [
                    InlineKeyboardButton("Play Again", callback_data=f"blackjack_new_{bet_amount}"),
                    InlineKeyboardButton("Double Bet", callback_data=f"blackjack_new_{bet_amount*2}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            
            # Remove the game from active games
            del active_games[user_id]
            return
        
        # Show initial game state
        player_value = game.get_hand_value(game.player_hand)
        
        message = (
            f"🃏 Blackjack Game 🃏\n\n"
            f"Your hand: {game.get_player_hand_display()} ({player_value})\n"
            f"Dealer's hand: {game.get_dealer_hand_display(hide_second=True)}\n\n"
            f"Your bet: {format_money(bet_amount)}\n\n"
            f"What would you like to do?"
        )
        
        # Create action keyboard
        keyboard = [
            [
                InlineKeyboardButton("Hit", callback_data="blackjack_hit"),
                InlineKeyboardButton("Stand", callback_data="blackjack_stand")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        return
    
    # Handle game actions
    if user_id not in active_games:
        await query.edit_message_text("No active game found. Start a new game with /blackjack [amount]")
        return
    
    game = active_games[user_id]
    
    if action == "hit":
        # Player takes another card
        player_value = game.player_hit()
        
        if game.game_over:  # Player busted
            winnings = game.get_winnings()
            
            # Record game result
            game_id = await record_game(
                user_id, 
                "blackjack", 
                game.bet_amount, 
                "loss", 
                0
            )
            
            # Get updated user data
            user = await get_user(user_id)
            
            message = (
                f"🃏 Bust! 🃏\n\n"
                f"Your hand: {game.get_player_hand_display()} ({player_value})\n"
                f"Dealer's hand: {game.get_dealer_hand_display()} ({game.get_hand_value(game.dealer_hand)})\n\n"
                f"You busted! You lose {format_money(game.bet_amount)}.\n"
                f"Your balance: {format_money(user['balance'])}"
            )
            
            # Create play again keyboard
            keyboard = [
                [
                    InlineKeyboardButton("Play Again", callback_data=f"blackjack_new_{game.bet_amount}"),
                    InlineKeyboardButton("Double Bet", callback_data=f"blackjack_new_{game.bet_amount*2}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            
            # Remove the game from active games
            del active_games[user_id]
        else:
            # Game continues
            message = (
                f"🃏 Blackjack Game 🃏\n\n"
                f"Your hand: {game.get_player_hand_display()} ({player_value})\n"
                f"Dealer's hand: {game.get_dealer_hand_display(hide_second=True)}\n\n"
                f"Your bet: {format_money(game.bet_amount)}\n\n"
                f"What would you like to do?"
            )
            
            # Create action keyboard
            keyboard = [
                [
                    InlineKeyboardButton("Hit", callback_data="blackjack_hit"),
                    InlineKeyboardButton("Stand", callback_data="blackjack_stand")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif action == "stand":
        # Dealer plays
        dealer_value = game.dealer_play()
        player_value = game.get_hand_value(game.player_hand)
        
        winnings = game.get_winnings()
        
        # Record game result
        game_id = await record_game(
            user_id, 
            "blackjack", 
            game.bet_amount, 
            "win" if winnings > 0 else "loss" if winnings == 0 else "push", 
            winnings
        )
        
        # Update user balance with winnings
        if winnings > 0:
            await update_user_balance(user_id, winnings)
            await record_transaction(user_id, winnings, "win", game_id)
        
        # Get updated user data
        user = await get_user(user_id)
        
        # Create result message based on game result
        if game.result == "dealer_bust":
            result_text = f"Dealer busts! You win {format_money(winnings)}!"
        elif game.result == "player_win":
            result_text = f"You win {format_money(winnings)}!"
        elif game.result == "dealer_win":
            result_text = f"Dealer wins. You lose {format_money(game.bet_amount)}."
        else:  # Push
            result_text = "Push! Your bet is returned."
        
        message = (
            f"🃏 Game Over 🃏\n\n"
            f"Your hand: {game.get_player_hand_display()} ({player_value})\n"
            f"Dealer's hand: {game.get_dealer_hand_display()} ({dealer_value})\n\n"
            f"{result_text}\n"
            f"Your balance: {format_money(user['balance'])}"
        )
        
        # Create play again keyboard
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data=f"blackjack_new_{game.bet_amount}"),
                InlineKeyboardButton("Double Bet", callback_data=f"blackjack_new_{game.bet_amount*2}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
        # Remove the game from active games
        del active_games[user_id]