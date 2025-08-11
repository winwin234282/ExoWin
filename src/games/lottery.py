import random
from src.database import get_user, update_user_balance, record_transaction, record_game

# Store active lottery games for webapp
active_lottery_games = {}

class LotteryGame:
    def __init__(self, user_id):
        self.user_id = user_id
        self.bet_amount = 0
        self.selected_numbers = []
        self.winning_numbers = []
        self.bonus_number = None
        self.matches = 0
        self.game_over = False
        self.result = None
        self.winnings = 0
        self.payout_multipliers = {
            6: 1000,  # Jackpot
            5: 100,   # 5 matches
            4: 10,    # 4 matches
            3: 3,     # 3 matches
            2: 1.5,   # 2 matches
            1: 0,     # 1 match - no payout
            0: 0      # No matches
        }
    
    def start_game(self, bet_amount):
        """Start a new lottery game"""
        self.bet_amount = bet_amount
        return True
    
    def select_numbers(self, numbers):
        """Select lottery numbers (6 numbers from 1-49)"""
        if len(numbers) != 6:
            return False
        
        if any(num < 1 or num > 49 for num in numbers):
            return False
        
        if len(set(numbers)) != 6:  # Check for duplicates
            return False
        
        self.selected_numbers = sorted(numbers)
        return True
    
    def draw_numbers(self):
        """Draw winning lottery numbers"""
        if self.game_over or not self.selected_numbers:
            return False
        
        # Draw 6 winning numbers from 1-49
        all_numbers = list(range(1, 50))
        self.winning_numbers = sorted(random.sample(all_numbers, 6))
        
        # Draw bonus number from remaining numbers
        remaining_numbers = [n for n in all_numbers if n not in self.winning_numbers]
        self.bonus_number = random.choice(remaining_numbers)
        
        # Count matches
        self.matches = len(set(self.selected_numbers) & set(self.winning_numbers))
        
        # Calculate winnings
        multiplier = self.payout_multipliers.get(self.matches, 0)
        self.winnings = self.bet_amount * multiplier
        
        # Determine result
        if self.matches >= 3:
            self.result = 'win'
        else:
            self.result = 'lose'
        
        self.game_over = True
        return True
    
    def get_game_state(self):
        """Get current game state"""
        return {
            'selected_numbers': self.selected_numbers,
            'winning_numbers': self.winning_numbers,
            'bonus_number': self.bonus_number,
            'matches': self.matches,
            'game_over': self.game_over,
            'result': self.result,
            'winnings': self.winnings,
            'bet_amount': self.bet_amount,
            'payout_multipliers': self.payout_multipliers
        }

def create_lottery_game(user_id, bet_amount):
    """Create a new lottery game"""
    game = LotteryGame(user_id)
    game.start_game(bet_amount)
    active_lottery_games[user_id] = game
    return game

def get_lottery_game(user_id):
    """Get active lottery game for user"""
    return active_lottery_games.get(user_id)

def select_lottery_numbers(user_id, numbers):
    """Select numbers for lottery game"""
    game = active_lottery_games.get(user_id)
    if game:
        return game.select_numbers(numbers)
    return False

def draw_lottery_numbers(user_id):
    """Draw winning lottery numbers"""
    game = active_lottery_games.get(user_id)
    if game:
        return game.draw_numbers()
    return False

def clear_lottery_game(user_id):
    """Clear lottery game for user"""
    if user_id in active_lottery_games:
        del active_lottery_games[user_id]