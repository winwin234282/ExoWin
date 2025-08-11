import random
from src.database import get_user, update_user_balance, record_transaction, record_game

# Store active poker games for webapp
active_poker_games = {}

class PokerGame:
    def __init__(self, user_id):
        self.user_id = user_id
        self.bet_amount = 0
        self.deck = self.create_deck()
        self.player_hand = []
        self.dealer_hand = []
        self.game_over = False
        self.result = None
        self.winnings = 0
        self.player_hand_rank = None
        self.dealer_hand_rank = None
    
    def create_deck(self):
        """Create a standard 52-card deck"""
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = []
        for suit in suits:
            for rank in ranks:
                deck.append({'rank': rank, 'suit': suit})
        random.shuffle(deck)
        return deck
    
    def start_game(self, bet_amount):
        """Start a new poker game"""
        self.bet_amount = bet_amount
        self.deck = self.create_deck()
        
        # Deal 5 cards to player and dealer
        self.player_hand = [self.deck.pop() for _ in range(5)]
        self.dealer_hand = [self.deck.pop() for _ in range(5)]
        
        return True
    
    def get_hand_rank(self, hand):
        """Get the rank of a poker hand"""
        ranks = [card['rank'] for card in hand]
        suits = [card['suit'] for card in hand]
        
        # Convert face cards to numbers for comparison
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                      '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        
        values = sorted([rank_values[rank] for rank in ranks])
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight = all(values[i] == values[i-1] + 1 for i in range(1, 5))
        
        # Count occurrences of each rank
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        counts = sorted(rank_counts.values(), reverse=True)
        
        # Determine hand rank
        if is_straight and is_flush:
            if values == [10, 11, 12, 13, 14]:
                return (10, 'Royal Flush')
            return (9, 'Straight Flush')
        elif counts == [4, 1]:
            return (8, 'Four of a Kind')
        elif counts == [3, 2]:
            return (7, 'Full House')
        elif is_flush:
            return (6, 'Flush')
        elif is_straight:
            return (5, 'Straight')
        elif counts == [3, 1, 1]:
            return (4, 'Three of a Kind')
        elif counts == [2, 2, 1]:
            return (3, 'Two Pair')
        elif counts == [2, 1, 1, 1]:
            return (2, 'One Pair')
        else:
            return (1, 'High Card')
    
    def finish_game(self):
        """Finish the poker game and determine winner"""
        if self.game_over:
            return False
        
        self.player_hand_rank = self.get_hand_rank(self.player_hand)
        self.dealer_hand_rank = self.get_hand_rank(self.dealer_hand)
        
        player_rank_value = self.player_hand_rank[0]
        dealer_rank_value = self.dealer_hand_rank[0]
        
        if player_rank_value > dealer_rank_value:
            self.result = 'win'
            self.winnings = self.bet_amount * 2
        elif player_rank_value < dealer_rank_value:
            self.result = 'lose'
            self.winnings = 0
        else:
            self.result = 'tie'
            self.winnings = self.bet_amount  # Return bet
        
        self.game_over = True
        return True
    
    def get_game_state(self):
        """Get current game state"""
        return {
            'player_hand': self.player_hand,
            'dealer_hand': self.dealer_hand if self.game_over else [],
            'player_hand_rank': self.player_hand_rank,
            'dealer_hand_rank': self.dealer_hand_rank,
            'game_over': self.game_over,
            'result': self.result,
            'winnings': self.winnings,
            'bet_amount': self.bet_amount
        }

def create_poker_game(user_id, bet_amount):
    """Create a new poker game"""
    game = PokerGame(user_id)
    game.start_game(bet_amount)
    active_poker_games[user_id] = game
    return game

def get_poker_game(user_id):
    """Get active poker game for user"""
    return active_poker_games.get(user_id)

def finish_poker_game(user_id):
    """Finish poker game and determine winner"""
    game = active_poker_games.get(user_id)
    if game:
        return game.finish_game()
    return False

def clear_poker_game(user_id):
    """Clear poker game for user"""
    if user_id in active_poker_games:
        del active_poker_games[user_id]