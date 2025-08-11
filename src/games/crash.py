import random
import time
import math
from src.database import get_user, update_user_balance, record_transaction, record_game

# Store active crash games for webapp
active_crash_games = {}

class CrashGame:
    def __init__(self, user_id):
        self.user_id = user_id
        self.bet_amount = 0
        self.is_running = False
        self.current_multiplier = 1.0
        self.crash_point = self.generate_crash_point()
        self.start_time = None
        self.cashed_out = False
        self.cash_out_multiplier = None
        self.game_over = False
        self.result = None
        self.winnings = 0
    
    def generate_crash_point(self):
        """Generate a random crash point with house edge"""
        # House edge of approximately 5%
        r = random.random()
        if r < 0.01:  # 1% chance for a very early crash (below 1.1x)
            return random.uniform(1.0, 1.1)
        elif r < 0.05:  # 4% chance for an early crash (1.1x to 1.5x)
            return random.uniform(1.1, 1.5)
        else:  # 95% chance for a normal distribution
            return 0.9 / (random.random() ** 0.7)
    
    def start_game(self, bet_amount):
        """Start a new crash game"""
        self.bet_amount = bet_amount
        self.is_running = True
        self.start_time = time.time()
        self.current_multiplier = 1.0
        self.cashed_out = False
        self.cash_out_multiplier = None
        self.game_over = False
        self.result = None
        self.winnings = 0
        return True
    
    def update_multiplier(self):
        """Update the current multiplier based on elapsed time"""
        if not self.is_running or self.game_over:
            return self.current_multiplier
        
        elapsed = time.time() - self.start_time
        # Multiplier grows exponentially over time
        self.current_multiplier = 1.0 + (elapsed * 0.1) ** 1.5
        
        # Check if we've reached the crash point
        if self.current_multiplier >= self.crash_point:
            self.crash()
        
        return self.current_multiplier
    
    def cash_out(self):
        """Cash out at current multiplier"""
        if not self.is_running or self.cashed_out or self.game_over:
            return False
        
        self.cashed_out = True
        self.cash_out_multiplier = self.current_multiplier
        self.winnings = self.bet_amount * self.current_multiplier
        self.result = 'win'
        self.game_over = True
        return True
    
    def crash(self):
        """Handle game crash"""
        self.is_running = False
        self.game_over = True
        
        if not self.cashed_out:
            self.result = 'crash'
            self.winnings = 0
        
        return True

def create_crash_game(user_id, bet_amount):
    """Create a new crash game"""
    game = CrashGame(user_id)
    game.start_game(bet_amount)
    active_crash_games[user_id] = game
    return game

def get_crash_game(user_id):
    """Get active crash game for user"""
    return active_crash_games.get(user_id)

def update_crash_game(user_id):
    """Update crash game state"""
    game = active_crash_games.get(user_id)
    if game:
        game.update_multiplier()
    return game

def cash_out_crash(user_id):
    """Cash out from crash game"""
    game = active_crash_games.get(user_id)
    if game:
        return game.cash_out()
    return False

def clear_crash_game(user_id):
    """Clear crash game for user"""
    if user_id in active_crash_games:
        del active_crash_games[user_id]