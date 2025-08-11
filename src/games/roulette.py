import random
from src.database import get_user, update_user_balance, record_transaction, record_game

# Store active roulette games for webapp
active_roulette_games = {}

class RouletteGame:
    def __init__(self, user_id):
        self.user_id = user_id
        self.bets = {}  # {bet_type: amount}
        self.total_bet = 0
        self.winning_number = None
        self.winning_color = None
        self.game_over = False
        self.result = None
        self.winnings = 0
        self.payout_details = []
    
    def place_bet(self, bet_type, amount):
        """Place a bet on the roulette table"""
        if bet_type in self.bets:
            self.bets[bet_type] += amount
        else:
            self.bets[bet_type] = amount
        self.total_bet += amount
        return True
    
    def spin(self):
        """Spin the roulette wheel"""
        self.winning_number = random.randint(0, 36)
        
        # Determine color (0 is green, 1-10 and 19-28 red/black alternate, 11-18 and 29-36 black/red alternate)
        if self.winning_number == 0:
            self.winning_color = 'green'
        elif self.winning_number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
            self.winning_color = 'red'
        else:
            self.winning_color = 'black'
        
        # Calculate winnings
        self.calculate_winnings()
        self.game_over = True
        return self.winning_number
    
    def calculate_winnings(self):
        """Calculate winnings based on bets and winning number"""
        total_winnings = 0
        
        for bet_type, bet_amount in self.bets.items():
            payout = 0
            
            if bet_type == 'red' and self.winning_color == 'red':
                payout = bet_amount * 2
            elif bet_type == 'black' and self.winning_color == 'black':
                payout = bet_amount * 2
            elif bet_type == 'even' and self.winning_number % 2 == 0 and self.winning_number != 0:
                payout = bet_amount * 2
            elif bet_type == 'odd' and self.winning_number % 2 == 1:
                payout = bet_amount * 2
            elif bet_type == 'low' and 1 <= self.winning_number <= 18:
                payout = bet_amount * 2
            elif bet_type == 'high' and 19 <= self.winning_number <= 36:
                payout = bet_amount * 2
            elif bet_type.startswith('number_') and int(bet_type.split('_')[1]) == self.winning_number:
                payout = bet_amount * 36
            elif bet_type == 'first_dozen' and 1 <= self.winning_number <= 12:
                payout = bet_amount * 3
            elif bet_type == 'second_dozen' and 13 <= self.winning_number <= 24:
                payout = bet_amount * 3
            elif bet_type == 'third_dozen' and 25 <= self.winning_number <= 36:
                payout = bet_amount * 3
            
            if payout > 0:
                self.payouts[bet_type] = payout
                total_winnings += payout
        
        self.winnings = total_winnings
        self.result = 'win' if total_winnings > 0 else 'lose'

def create_roulette_game(user_id):
    """Create a new roulette game"""
    game = RouletteGame(user_id)
    active_roulette_games[user_id] = game
    return game

def get_roulette_game(user_id):
    """Get active roulette game for user"""
    return active_roulette_games.get(user_id)

def place_roulette_bet(user_id, bet_type, amount):
    """Place a bet in roulette game"""
    game = active_roulette_games.get(user_id)
    if game:
        return game.place_bet(bet_type, amount)
    return False

def spin_roulette(user_id):
    """Spin the roulette wheel"""
    game = active_roulette_games.get(user_id)
    if game:
        return game.spin()
    return None

def clear_roulette_game(user_id):
    """Clear roulette game for user"""
    if user_id in active_roulette_games:
        del active_roulette_games[user_id]