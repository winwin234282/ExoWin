import random
from src.database import get_user, update_user_balance, record_transaction, record_game

# Store active mines games for webapp
active_mines_games = {}

class MinesGame:
    def __init__(self, user_id, mines_count=5, grid_size=25):
        self.user_id = user_id
        self.mines_count = mines_count
        self.grid_size = grid_size
        self.bet_amount = 0
        self.grid = [False] * grid_size  # False = safe, True = mine
        self.revealed = [False] * grid_size
        self.mines_positions = []
        self.gems_found = 0
        self.current_multiplier = 1.0
        self.game_over = False
        self.result = None
        self.winnings = 0
        self.cashed_out = False
        
        # Place mines randomly
        self.place_mines()
    
    def place_mines(self):
        """Randomly place mines on the grid"""
        self.mines_positions = random.sample(range(self.grid_size), self.mines_count)
        for pos in self.mines_positions:
            self.grid[pos] = True
    
    def start_game(self, bet_amount):
        """Start a new mines game"""
        self.bet_amount = bet_amount
        return True
    
    def reveal_tile(self, position):
        """Reveal a tile on the grid"""
        if self.game_over or self.revealed[position]:
            return False
        
        self.revealed[position] = True
        
        if self.grid[position]:  # Hit a mine
            self.game_over = True
            self.result = 'mine'
            self.winnings = 0
            return {'hit_mine': True, 'position': position}
        else:  # Found a gem
            self.gems_found += 1
            self.calculate_multiplier()
            return {'hit_mine': False, 'position': position, 'multiplier': self.current_multiplier}
    
    def calculate_multiplier(self):
        """Calculate current multiplier based on gems found"""
        # Multiplier increases with each gem found
        # Formula: multiplier = (total_safe_tiles / remaining_safe_tiles)
        total_safe_tiles = self.grid_size - self.mines_count
        remaining_safe_tiles = total_safe_tiles - self.gems_found
        
        if remaining_safe_tiles > 0:
            self.current_multiplier = total_safe_tiles / remaining_safe_tiles
        else:
            self.current_multiplier = total_safe_tiles
    
    def cash_out(self):
        """Cash out with current multiplier"""
        if self.game_over or self.cashed_out:
            return False
        
        self.cashed_out = True
        self.game_over = True
        self.result = 'cashout'
        self.winnings = self.bet_amount * self.current_multiplier
        return True
    
    def get_game_state(self):
        """Get current game state"""
        return {
            'grid_size': self.grid_size,
            'mines_count': self.mines_count,
            'revealed': self.revealed,
            'gems_found': self.gems_found,
            'current_multiplier': self.current_multiplier,
            'game_over': self.game_over,
            'result': self.result,
            'winnings': self.winnings,
            'bet_amount': self.bet_amount,
            'cashed_out': self.cashed_out
        }

def create_mines_game(user_id, bet_amount, mines_count=5):
    """Create a new mines game"""
    game = MinesGame(user_id, mines_count)
    game.start_game(bet_amount)
    active_mines_games[user_id] = game
    return game

def get_mines_game(user_id):
    """Get active mines game for user"""
    return active_mines_games.get(user_id)

def reveal_mines_tile(user_id, position):
    """Reveal a tile in mines game"""
    game = active_mines_games.get(user_id)
    if game:
        return game.reveal_tile(position)
    return None

def cash_out_mines(user_id):
    """Cash out from mines game"""
    game = active_mines_games.get(user_id)
    if game:
        return game.cash_out()
    return False

def clear_mines_game(user_id):
    """Clear mines game for user"""
    if user_id in active_mines_games:
        del active_mines_games[user_id]