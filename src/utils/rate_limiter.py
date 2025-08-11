import time
from collections import defaultdict
from typing import Dict, Tuple
from src.utils.logger import bot_logger

class RateLimiter:
    """Rate limiter to prevent spam and abuse"""
    
    def __init__(self):
        # user_id -> (last_action_time, action_count)
        self.user_actions: Dict[int, Tuple[float, int]] = defaultdict(lambda: (0, 0))
        # user_id -> (last_bet_time, bet_count)
        self.user_bets: Dict[int, Tuple[float, int]] = defaultdict(lambda: (0, 0))
        
    def check_action_limit(self, user_id: int, max_actions: int = 10, window: int = 60) -> bool:
        """Check if user is within action rate limit"""
        current_time = time.time()
        last_time, count = self.user_actions[user_id]
        
        # Reset counter if window has passed
        if current_time - last_time > window:
            self.user_actions[user_id] = (current_time, 1)
            return True
        
        # Check if within limit
        if count >= max_actions:
            bot_logger.warning(f"Rate limit exceeded for user {user_id}: {count} actions in {window}s")
            return False
        
        # Increment counter
        self.user_actions[user_id] = (last_time, count + 1)
        return True
    
    def check_bet_limit(self, user_id: int, bet_amount: float, max_bets: int = 5, window: int = 60, max_bet_amount: float = 1000) -> bool:
        """Check if user is within betting rate limit"""
        current_time = time.time()
        last_time, count = self.user_bets[user_id]
        
        # Check bet amount limit
        if bet_amount > max_bet_amount:
            bot_logger.warning(f"Bet amount too high for user {user_id}: ${bet_amount}")
            return False
        
        # Reset counter if window has passed
        if current_time - last_time > window:
            self.user_bets[user_id] = (current_time, 1)
            return True
        
        # Check if within limit
        if count >= max_bets:
            bot_logger.warning(f"Bet rate limit exceeded for user {user_id}: {count} bets in {window}s")
            return False
        
        # Increment counter
        self.user_bets[user_id] = (last_time, count + 1)
        return True
    
    def get_remaining_time(self, user_id: int, limit_type: str = "action") -> int:
        """Get remaining cooldown time in seconds"""
        current_time = time.time()
        
        if limit_type == "action":
            last_time, _ = self.user_actions[user_id]
            return max(0, int(60 - (current_time - last_time)))
        else:
            last_time, _ = self.user_bets[user_id]
            return max(0, int(60 - (current_time - last_time)))

# Global rate limiter instance
rate_limiter = RateLimiter()