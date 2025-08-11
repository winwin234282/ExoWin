import random

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
    
    def to_dict(self):
        return {
            'suit': self.suit,
            'rank': self.rank,
            'value': self.get_value()
        }

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
        
        # Check for blackjack
        if self.get_hand_value(self.player_hand) == 21:
            if self.get_hand_value(self.dealer_hand) == 21:
                self.result = "push"
            else:
                self.result = "blackjack"
            self.game_over = True
    
    def get_hand_value(self, hand):
        value = 0
        aces = 0
        
        for card in hand:
            if card.rank == "A":
                aces += 1
                value += 11
            else:
                value += card.get_value()
        
        # Adjust for aces
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def hit(self):
        if self.game_over:
            return False
        
        self.player_hand.append(self.deck.draw())
        
        if self.get_hand_value(self.player_hand) > 21:
            self.result = "bust"
            self.game_over = True
        
        return True
    
    def stand(self):
        if self.game_over:
            return
        
        # Dealer plays
        while self.get_hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.draw())
        
        player_value = self.get_hand_value(self.player_hand)
        dealer_value = self.get_hand_value(self.dealer_hand)
        
        if dealer_value > 21:
            self.result = "dealer_bust"
        elif player_value > dealer_value:
            self.result = "player_win"
        elif dealer_value > player_value:
            self.result = "dealer_win"
        else:
            self.result = "push"
        
        self.game_over = True
    
    def get_winnings(self):
        if self.result == "blackjack":
            return self.bet_amount * 2.5  # 3:2 payout
        elif self.result in ["player_win", "dealer_bust"]:
            return self.bet_amount * 2
        elif self.result == "push":
            return self.bet_amount  # Return original bet
        else:
            return 0
    
    def to_dict(self):
        return {
            'player_hand': [card.to_dict() for card in self.player_hand],
            'dealer_hand': [card.to_dict() for card in self.dealer_hand],
            'player_value': self.get_hand_value(self.player_hand),
            'dealer_value': self.get_hand_value(self.dealer_hand),
            'game_over': self.game_over,
            'result': self.result,
            'bet_amount': self.bet_amount,
            'winnings': self.get_winnings() if self.game_over else 0
        }

# Game logic functions for webapp API
def create_blackjack_game(user_id, bet_amount):
    """Create a new blackjack game"""
    return BlackjackGame(user_id, bet_amount)

def hit_blackjack(game):
    """Player hits in blackjack game"""
    game.hit()
    return game.to_dict()

def stand_blackjack(game):
    """Player stands in blackjack game"""
    game.stand()
    return game.to_dict()

# Store active games (in production, use Redis or database)
active_blackjack_games = {}

def get_game(user_id):
    """Get active game for user"""
    return active_blackjack_games.get(user_id)

def set_game(user_id, game):
    """Set active game for user"""
    active_blackjack_games[user_id] = game

def clear_game(user_id):
    """Clear active game for user"""
    if user_id in active_blackjack_games:
        del active_blackjack_games[user_id]