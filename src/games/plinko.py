import random
from src.database import get_user, update_user_balance, record_transaction, record_game

# Store active plinko games for webapp
active_plinko_games = {}

class PlinkoGame:
    def __init__(self, user_id, rows=16):
        self.user_id = user_id
        self.rows = rows
        self.bet_amount = 0
        self.risk_level = 'medium'  # low, medium, high
        self.multipliers = self.get_multipliers()
        self.ball_path = []
        self.final_slot = None
        self.game_over = False
        self.result = None
        self.winnings = 0
    
    def get_multipliers(self):
        """Get multipliers based on risk level"""
        if self.risk_level == 'low':
            # Lower risk, more consistent payouts
            return [0.5, 1.0, 1.2, 1.5, 2.0, 3.0, 5.0, 10.0, 5.0, 3.0, 2.0, 1.5, 1.2, 1.0, 0.5]
        elif self.risk_level == 'medium':
            # Medium risk
            return [0.3, 0.5, 1.0, 1.5, 2.0, 5.0, 10.0, 50.0, 10.0, 5.0, 2.0, 1.5, 1.0, 0.5, 0.3]
        else:  # high
            # High risk, high reward
            return [0.2, 0.3, 0.5, 1.0, 2.0, 10.0, 50.0, 1000.0, 50.0, 10.0, 2.0, 1.0, 0.5, 0.3, 0.2]
    
    def start_game(self, bet_amount, risk_level='medium'):
        """Start a new plinko game"""
        self.bet_amount = bet_amount
        self.risk_level = risk_level
        self.multipliers = self.get_multipliers()
        return True
    
    def drop_ball(self):
        """Simulate dropping a ball through the plinko board"""
        if self.game_over:
            return False
        
        # Simulate ball path
        position = self.rows // 2  # Start in the middle
        self.ball_path = [position]
        
        # Ball bounces left or right at each peg
        for row in range(self.rows):
            # 50% chance to go left or right
            if random.random() < 0.5:
                position = max(0, position - 1)  # Go left
            else:
                position = min(len(self.multipliers) - 1, position + 1)  # Go right
            
            self.ball_path.append(position)
        
        # Final position determines the multiplier
        self.final_slot = position
        multiplier = self.multipliers[self.final_slot]
        
        self.winnings = self.bet_amount * multiplier
        self.game_over = True
        self.result = 'win' if multiplier > 1.0 else 'lose'
        
        return {
            'ball_path': self.ball_path,
            'final_slot': self.final_slot,
            'multiplier': multiplier,
            'winnings': self.winnings
        }
    
    def get_game_state(self):
        """Get current game state"""
        return {
            'rows': self.rows,
            'risk_level': self.risk_level,
            'multipliers': self.multipliers,
            'ball_path': self.ball_path,
            'final_slot': self.final_slot,
            'game_over': self.game_over,
            'result': self.result,
            'winnings': self.winnings,
            'bet_amount': self.bet_amount
        }

def create_plinko_game(user_id, bet_amount, risk_level='medium'):
    """Create a new plinko game"""
    game = PlinkoGame(user_id)
    game.start_game(bet_amount, risk_level)
    active_plinko_games[user_id] = game
    return game

def get_plinko_game(user_id):
    """Get active plinko game for user"""
    return active_plinko_games.get(user_id)

def drop_plinko_ball(user_id):
    """Drop a ball in plinko game"""
    game = active_plinko_games.get(user_id)
    if game:
        return game.drop_ball()
    return None

def clear_plinko_game(user_id):
    """Clear plinko game for user"""
    if user_id in active_plinko_games:
        del active_plinko_games[user_id]