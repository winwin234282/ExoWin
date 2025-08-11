import random
from src.database import get_user, update_user_balance, record_transaction, record_game

# Store active tower games for webapp
active_tower_games = {}

class TowerGame:
    def __init__(self, user_id, levels=8, tiles_per_level=4):
        self.user_id = user_id
        self.levels = levels
        self.tiles_per_level = tiles_per_level
        self.bet_amount = 0
        self.current_level = 0
        self.tower_layout = []  # [level][tile] = True/False (safe/trap)
        self.current_multiplier = 1.0
        self.game_over = False
        self.result = None
        self.winnings = 0
        self.cashed_out = False
        
        # Generate tower layout
        self.generate_tower()
    
    def generate_tower(self):
        """Generate the tower layout with safe tiles and traps"""
        self.tower_layout = []
        for level in range(self.levels):
            # Each level has 1 safe tile and 3 traps (for 4 tiles per level)
            level_tiles = [True] + [False] * (self.tiles_per_level - 1)
            random.shuffle(level_tiles)
            self.tower_layout.append(level_tiles)
    
    def start_game(self, bet_amount):
        """Start a new tower game"""
        self.bet_amount = bet_amount
        self.current_level = 0
        self.current_multiplier = 1.0
        return True
    
    def choose_tile(self, tile_index):
        """Choose a tile on the current level"""
        if self.game_over or self.current_level >= self.levels:
            return False
        
        if tile_index >= self.tiles_per_level:
            return False
        
        is_safe = self.tower_layout[self.current_level][tile_index]
        
        if is_safe:
            # Advance to next level
            self.current_level += 1
            self.calculate_multiplier()
            
            # Check if reached the top
            if self.current_level >= self.levels:
                self.game_over = True
                self.result = 'completed'
                self.winnings = self.bet_amount * self.current_multiplier
            
            return {'success': True, 'level': self.current_level, 'multiplier': self.current_multiplier}
        else:
            # Hit a trap
            self.game_over = True
            self.result = 'trap'
            self.winnings = 0
            return {'success': False, 'level': self.current_level}
    
    def calculate_multiplier(self):
        """Calculate current multiplier based on level reached"""
        # Multiplier increases exponentially with each level
        # Base multiplier of 1.5x per level
        self.current_multiplier = (1.5 ** self.current_level)
    
    def cash_out(self):
        """Cash out at current level"""
        if self.game_over or self.cashed_out or self.current_level == 0:
            return False
        
        self.cashed_out = True
        self.game_over = True
        self.result = 'cashout'
        self.winnings = self.bet_amount * self.current_multiplier
        return True
    
    def get_game_state(self):
        """Get current game state"""
        return {
            'levels': self.levels,
            'tiles_per_level': self.tiles_per_level,
            'current_level': self.current_level,
            'current_multiplier': self.current_multiplier,
            'game_over': self.game_over,
            'result': self.result,
            'winnings': self.winnings,
            'bet_amount': self.bet_amount,
            'cashed_out': self.cashed_out
        }

def create_tower_game(user_id, bet_amount):
    """Create a new tower game"""
    game = TowerGame(user_id)
    game.start_game(bet_amount)
    active_tower_games[user_id] = game
    return game

def get_tower_game(user_id):
    """Get active tower game for user"""
    return active_tower_games.get(user_id)

def choose_tower_tile(user_id, tile_index):
    """Choose a tile in tower game"""
    game = active_tower_games.get(user_id)
    if game:
        return game.choose_tile(tile_index)
    return None

def cash_out_tower(user_id):
    """Cash out from tower game"""
    game = active_tower_games.get(user_id)
    if game:
        return game.cash_out()
    return False

def clear_tower_game(user_id):
    """Clear tower game for user"""
    if user_id in active_tower_games:
        del active_tower_games[user_id]