import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, update_user_balance, record_transaction, record_game
from src.utils.formatting import format_money

# Card suits and values
SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS)}

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def get_value(self):
        return RANK_VALUES[self.rank]

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

class PokerHand:
    def __init__(self, cards):
        self.cards = cards
        self.rank_counts = {}
        self.suit_counts = {}
        self.analyze_hand()
    
    def analyze_hand(self):
        # Count ranks and suits
        for card in self.cards:
            if card.rank in self.rank_counts:
                self.rank_counts[card.rank] += 1
            else:
                self.rank_counts[card.rank] = 1
            
            if card.suit in self.suit_counts:
                self.suit_counts[card.suit] += 1
            else:
                self.suit_counts[card.suit] = 1
    
    def is_royal_flush(self):
        """Check for royal flush (A, K, Q, J, 10, all same suit)"""
        if len(self.suit_counts) != 1:
            return False
        
        ranks = [card.rank for card in self.cards]
        return set(ranks) == set(["10", "J", "Q", "K", "A"])
    
    def is_straight_flush(self):
        """Check for straight flush (5 consecutive cards, all same suit)"""
        if len(self.suit_counts) != 1:
            return False
        
        return self.is_straight()
    
    def is_four_of_a_kind(self):
        """Check for four of a kind"""
        return 4 in self.rank_counts.values()
    
    def is_full_house(self):
        """Check for full house (three of a kind and a pair)"""
        return 3 in self.rank_counts.values() and 2 in self.rank_counts.values()
    
    def is_flush(self):
        """Check for flush (all same suit)"""
        return len(self.suit_counts) == 1
    
    def is_straight(self):
        """Check for straight (5 consecutive cards)"""
        values = sorted([RANK_VALUES[card.rank] for card in self.cards])
        
        # Check for A-5 straight
        if values == [0, 1, 2, 3, 12]:  # 2,3,4,5,A
            return True
        
        # Check for regular straight
        return values == list(range(min(values), max(values) + 1))
    
    def is_three_of_a_kind(self):
        """Check for three of a kind"""
        return 3 in self.rank_counts.values()
    
    def is_two_pair(self):
        """Check for two pair"""
        pairs = [rank for rank, count in self.rank_counts.items() if count == 2]
        return len(pairs) == 2
    
    def is_pair(self):
        """Check for a pair"""
        return 2 in self.rank_counts.values()
    
    def get_hand_rank(self):
        """Get the rank of the hand (higher is better)"""
        if self.is_royal_flush():
            return 9, "Royal Flush"
        elif self.is_straight_flush():
            return 8, "Straight Flush"
        elif self.is_four_of_a_kind():
            return 7, "Four of a Kind"
        elif self.is_full_house():
            return 6, "Full House"
        elif self.is_flush():
            return 5, "Flush"
        elif self.is_straight():
            return 4, "Straight"
        elif self.is_three_of_a_kind():
            return 3, "Three of a Kind"
        elif self.is_two_pair():
            return 2, "Two Pair"
        elif self.is_pair():
            return 1, "Pair"
        else:
            return 0, "High Card"

# Store active video poker games
active_poker_games = {}

class VideoPokerGame:
    def __init__(self, user_id, bet_amount):
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.deck = Deck()
        self.hand = []
        self.held_cards = [False] * 5
        self.game_over = False
        
        # Deal initial hand
        for _ in range(5):
            self.hand.append(self.deck.draw())
    
    def hold_card(self, index):
        """Hold or unhold a card"""
        if 0 <= index < len(self.hand):
            self.held_cards[index] = not self.held_cards[index]
            return True
        return False
    
    def draw_new_cards(self):
        """Replace unheld cards with new ones"""
        for i in range(len(self.hand)):
            if not self.held_cards[i]:
                self.hand[i] = self.deck.draw()
        
        self.game_over = True
    
    def get_hand_display(self):
        """Get a string representation of the hand with hold indicators"""
        cards = []
        for i, card in enumerate(self.hand):
            if self.held_cards[i]:
                cards.append(f"[{card}]")
            else:
                cards.append(f"{card}")
        return " ".join(cards)
    
    def get_payout(self):
        """Calculate payout based on hand rank"""
        poker_hand = PokerHand(self.hand)
        rank, hand_name = poker_hand.get_hand_rank()
        
        # Payout multipliers
        payouts = {
            9: 800,  # Royal Flush
            8: 50,   # Straight Flush
            7: 25,   # Four of a Kind
            6: 9,    # Full House
            5: 6,    # Flush
            4: 4,    # Straight
            3: 3,    # Three of a Kind
            2: 2,    # Two Pair
            1: 1,    # Jacks or Better (pair of Jacks or higher)
            0: 0     # Nothing
        }
        
        # Special case for Jacks or Better
        if rank == 1:  # Pair
            pair_rank = [r for r, c in poker_hand.rank_counts.items() if c == 2][0]
            if pair_rank not in ["J", "Q", "K", "A"]:
                return 0, hand_name  # Pair lower than Jacks
        
        return payouts[rank] * self.bet_amount, hand_name

async def poker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /poker command"""
    if not context.args:
        await update.message.reply_text(
            "🃏 Video Poker 🃏\n\n"
            "Play Jacks or Better video poker!\n\n"
            "Usage: /poker [amount]\n"
            "Example: /poker 5\n\n"
            "Payouts:\n"
            "Royal Flush: 800x\n"
            "Straight Flush: 50x\n"
            "Four of a Kind: 25x\n"
            "Full House: 9x\n"
            "Flush: 6x\n"
            "Straight: 4x\n"
            "Three of a Kind: 3x\n"
            "Two Pair: 2x\n"
            "Jacks or Better: 1x"
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
    
    # Create a new poker game
    game = VideoPokerGame(user_id, bet_amount)
    active_poker_games[user_id] = game
    
    # Show initial hand
    message = (
        f"🃏 Video Poker - Bet: {format_money(bet_amount)} 🃏\n\n"
        f"Your hand:\n{game.get_hand_display()}\n\n"
        f"Select cards to hold, then press 'Draw' to replace the others."
    )
    
    # Create keyboard for card selection
    keyboard = []
    for i in range(5):
        keyboard.append([
            InlineKeyboardButton(f"Hold Card {i+1}", callback_data=f"poker_hold_{i}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("Draw New Cards", callback_data="poker_draw")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def poker_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle poker callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in active_poker_games:
        await query.edit_message_text("No active poker game found. Start a new game with /poker [amount]")
        return
    
    game = active_poker_games[user_id]
    data = query.data.split("_")
    
    if data[1] == "hold":
        # Hold or unhold a card
        index = int(data[2])
        game.hold_card(index)
        
        # Update display
        message = (
            f"🃏 Video Poker - Bet: {format_money(game.bet_amount)} 🃏\n\n"
            f"Your hand:\n{game.get_hand_display()}\n\n"
            f"Select cards to hold, then press 'Draw' to replace the others."
        )
        
        # Create keyboard for card selection
        keyboard = []
        for i in range(5):
            hold_text = "Unhold" if game.held_cards[i] else "Hold"
            keyboard.append([
                InlineKeyboardButton(f"{hold_text} Card {i+1}", callback_data=f"poker_hold_{i}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("Draw New Cards", callback_data="poker_draw")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif data[1] == "draw":
        # Draw new cards
        game.draw_new_cards()
        
        # Calculate payout
        winnings, hand_name = game.get_payout()
        
        # Record game result
        game_id = await record_game(
            user_id, 
            "poker", 
            game.bet_amount, 
            "win" if winnings > 0 else "loss", 
            winnings
        )
        
        # Update user balance if won
        if winnings > 0:
            await update_user_balance(user_id, winnings)
            await record_transaction(user_id, winnings, "win", game_id)
        
        # Get updated user data
        user = await get_user(user_id)
        
        # Create result message
        if winnings > 0:
            result_text = f"🎉 {hand_name}! You won {format_money(winnings)}!"
        else:
            result_text = f"😢 {hand_name}. No win."
        
        message = (
            f"🃏 Video Poker - Final Hand 🃏\n\n"
            f"Your hand:\n{game.get_hand_display()}\n\n"
            f"{result_text}\n"
            f"Your balance: {format_money(user['balance'])}"
        )
        
        # Create play again keyboard
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data=f"poker_new_{game.bet_amount}"),
                InlineKeyboardButton("Double Bet", callback_data=f"poker_new_{game.bet_amount*2}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
        # Remove the game from active games
        del active_poker_games[user_id]
    
    elif data[1] == "new":
        # Start a new game
        bet_amount = float(data[2])
        user = await get_user(user_id)
        
        if user["balance"] < bet_amount:
            await query.edit_message_text(
                f"You don't have enough funds. Your balance: {format_money(user['balance'])}"
            )
            return
        
        # Deduct bet amount from user balance
        await update_user_balance(user_id, -bet_amount)
        await record_transaction(user_id, -bet_amount, "bet")
        
        # Create a new poker game
        game = VideoPokerGame(user_id, bet_amount)
        active_poker_games[user_id] = game
        
        # Show initial hand
        message = (
            f"🃏 Video Poker - Bet: {format_money(bet_amount)} 🃏\n\n"
            f"Your hand:\n{game.get_hand_display()}\n\n"
            f"Select cards to hold, then press 'Draw' to replace the others."
        )
        
        # Create keyboard for card selection
        keyboard = []
        for i in range(5):
            keyboard.append([
                InlineKeyboardButton(f"Hold Card {i+1}", callback_data=f"poker_hold_{i}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("Draw New Cards", callback_data="poker_draw")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)