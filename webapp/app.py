from flask import Flask, render_template, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os
import sys
import json
import asyncio
import random
import secrets
from datetime import timedelta
from dotenv import load_dotenv

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from webapp.sync_db import get_user, update_user_balance, record_transaction, record_game
from src.utils.logger import webapp_logger
from src.utils.validators import validator
from src.utils.error_handler import GameError, InsufficientFundsError, InvalidBetError

app = Flask(__name__)
CORS(app, origins="*", allow_headers="*", methods="*")

# Configure Flask for Telegram Web Apps
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(hours=24)

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Gamble Bot Web App Server Running'})

@app.route('/games/<game_name>')
def game_page(game_name):
    """Serve game pages"""
    user_id = request.args.get('user_id')
    if not user_id:
        return "User ID required", 400
    
    # Get user data
    try:
        user = get_user(int(user_id))
    except Exception as e:
        return f"Error loading user data: {str(e)}", 500
    
    return render_template(f'games/{game_name}.html', user=user, user_id=user_id)

@app.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    """Get user data API endpoint"""
    try:
        user = get_user(user_id)
        
        return jsonify({
            'success': True,
            'user': {
                'user_id': user['user_id'],
                'balance': user['balance'],
                'total_bets': user.get('total_bets', 0),
                'total_wins': user.get('total_wins', 0),
                'total_losses': user.get('total_losses', 0)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/game/bet', methods=['POST'])
def place_bet():
    """Place a bet API endpoint"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        game_type = data.get('game_type')
        bet_amount = float(data.get('bet_amount'))
        game_data = data.get('game_data', {})
        
        if not all([user_id, game_type, bet_amount]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Get user and check balance
        user = get_user(user_id)
        
        if user['balance'] < bet_amount:
            return jsonify({
                'success': False, 
                'error': 'Insufficient balance',
                'balance': user['balance']
            }), 400
        
        # Deduct bet amount
        update_user_balance(user_id, -bet_amount)
        record_transaction(user_id, -bet_amount, "bet", f"{game_type} bet")
        
        # Process game logic based on game type
        result = process_game_logic(game_type, bet_amount, game_data)
        
        # Record game result
        game_id = record_game(
            user_id, game_type, bet_amount, 
            result['outcome'], result['winnings']
        )
        
        # Update balance if won
        if result['winnings'] > 0:
            update_user_balance(user_id, result['winnings'])
            record_transaction(user_id, result['winnings'], "win", f"{game_type} win")
        
        # Get updated user data
        updated_user = get_user(user_id)
        
        return jsonify({
            'success': True,
            'result': result,
            'new_balance': updated_user['balance'],
            'game_id': game_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def process_game_logic(game_type, bet_amount, game_data):
    """Process game logic and return result"""
    try:
        if game_type == 'coinflip':
            # Coinflip game logic
            user_choice = game_data.get('choice', 'heads')  # heads or tails
            result = random.choice(['heads', 'tails'])
            
            if user_choice == result:
                winnings = bet_amount * 2  # 2x multiplier for correct guess
                return {
                    'outcome': 'win',
                    'winnings': winnings,
                    'result': result,
                    'user_choice': user_choice,
                    'multiplier': 2.0,
                    'message': f'You chose {user_choice} and it landed on {result}! You won!'
                }
            else:
                return {
                    'outcome': 'loss',
                    'winnings': 0,
                    'result': result,
                    'user_choice': user_choice,
                    'message': f'You chose {user_choice} but it landed on {result}. Better luck next time!'
                }
        
        elif game_type == 'crash':
            # Crash game logic
            crash_point = round(random.uniform(1.01, 10.0), 2)
            cash_out_at = game_data.get('cash_out_at', 2.0)
            
            if cash_out_at <= crash_point:
                winnings = bet_amount * cash_out_at
                return {
                    'outcome': 'win',
                    'winnings': winnings,
                    'crash_point': crash_point,
                    'cash_out_at': cash_out_at,
                    'multiplier': cash_out_at,
                    'message': f'Cashed out at {cash_out_at}x! Crash was at {crash_point}x'
                }
            else:
                return {
                    'outcome': 'loss',
                    'winnings': 0,
                    'crash_point': crash_point,
                    'cash_out_at': cash_out_at,
                    'message': f'Crashed at {crash_point}x before your cash out at {cash_out_at}x!'
                }
        
        elif game_type == 'dice':
            # Dice game logic
            target = game_data.get('target', 50)  # Target number (1-100)
            over_under = game_data.get('over_under', 'over')  # 'over' or 'under'
            
            roll = random.randint(1, 100)
            
            won = False
            if over_under == 'over' and roll > target:
                won = True
            elif over_under == 'under' and roll < target:
                won = True
            
            if won:
                # Calculate multiplier based on probability
                if over_under == 'over':
                    probability = (100 - target) / 100
                else:
                    probability = target / 100
                
                multiplier = 0.95 / probability  # 95% RTP
                winnings = bet_amount * multiplier
                
                return {
                    'outcome': 'win',
                    'winnings': winnings,
                    'roll': roll,
                    'target': target,
                    'over_under': over_under,
                    'multiplier': multiplier,
                    'message': f'Rolled {roll}! You won with {over_under} {target}!'
                }
            else:
                return {
                    'outcome': 'loss',
                    'winnings': 0,
                    'roll': roll,
                    'target': target,
                    'over_under': over_under,
                    'message': f'Rolled {roll}. You needed {over_under} {target}.'
                }
        
        elif game_type == 'plinko':
            # Plinko game logic
            risk_level = game_data.get('risk', 'medium')  # low, medium, high
            
            # Define multipliers for different risk levels
            multipliers = {
                'low': [0.5, 0.7, 1.0, 1.2, 1.5, 1.2, 1.0, 0.7, 0.5],
                'medium': [0.2, 0.5, 1.0, 2.0, 5.0, 2.0, 1.0, 0.5, 0.2],
                'high': [0.1, 0.3, 0.5, 2.0, 10.0, 2.0, 0.5, 0.3, 0.1]
            }
            
            # Simulate ball drop (weighted towards center)
            weights = [1, 2, 4, 6, 8, 6, 4, 2, 1]
            bucket = random.choices(range(9), weights=weights)[0]
            multiplier = multipliers[risk_level][bucket]
            
            winnings = bet_amount * multiplier
            
            return {
                'outcome': 'win' if multiplier > 1.0 else 'loss',
                'winnings': winnings,
                'bucket': bucket,
                'multiplier': multiplier,
                'risk_level': risk_level,
                'message': f'Ball landed in bucket {bucket + 1} with {multiplier}x multiplier!'
            }
        
        elif game_type == 'mines':
            # Mines game logic
            mines_count = game_data.get('mines', 3)
            revealed_positions = game_data.get('revealed', [])
            action = game_data.get('action', 'reveal')  # 'reveal' or 'cashout'
            
            # Generate consistent mine positions for this game session
            seed = game_data.get('seed', random.randint(1, 1000000))
            random.seed(seed)
            mine_positions = random.sample(range(25), mines_count)
            random.seed()  # Reset seed
            
            if action == 'reveal':
                position = game_data.get('position')
                if position in mine_positions:
                    return {
                        'outcome': 'loss',
                        'winnings': 0,
                        'mine_positions': mine_positions,
                        'hit_mine': True,
                        'position': position,
                        'message': 'Hit a mine! Game over.'
                    }
                else:
                    # Calculate current multiplier
                    gems_found = len(revealed_positions) + 1
                    safe_tiles = 25 - mines_count
                    multiplier = 1.0
                    for i in range(gems_found):
                        multiplier *= (safe_tiles - i) / (25 - mines_count - i)
                    
                    return {
                        'outcome': 'continue',
                        'winnings': 0,
                        'position': position,
                        'gems_found': gems_found,
                        'multiplier': multiplier,
                        'hit_mine': False,
                        'seed': seed,
                        'message': f'Found a gem! Current multiplier: {multiplier:.2f}x'
                    }
            
            elif action == 'cashout':
                gems_found = len(revealed_positions)
                if gems_found == 0:
                    multiplier = 1.0
                else:
                    safe_tiles = 25 - mines_count
                    multiplier = 1.0
                    for i in range(gems_found):
                        multiplier *= (safe_tiles - i) / (25 - mines_count - i)
                
                winnings = bet_amount * multiplier
                
                return {
                    'outcome': 'win',
                    'winnings': winnings,
                    'gems_found': gems_found,
                    'multiplier': multiplier,
                    'message': f'Cashed out with {gems_found} gems! Multiplier: {multiplier:.2f}x'
                }
        
        elif game_type == 'roulette':
            # Roulette game logic
            bet_type = game_data.get('bet_type', 'number')  # number, color, odd_even
            bet_value = game_data.get('bet_value')
            
            # Generate winning number (0-36)
            winning_number = random.randint(0, 36)
            
            # Determine color
            if winning_number == 0:
                winning_color = 'green'
            elif winning_number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
                winning_color = 'red'
            else:
                winning_color = 'black'
            
            won = False
            multiplier = 0
            
            if bet_type == 'number' and bet_value == winning_number:
                won = True
                multiplier = 36  # 36:1 payout for single number
            elif bet_type == 'color' and bet_value == winning_color:
                won = True
                multiplier = 2  # 2:1 payout for color
            elif bet_type == 'odd_even':
                if bet_value == 'odd' and winning_number % 2 == 1 and winning_number != 0:
                    won = True
                    multiplier = 2
                elif bet_value == 'even' and winning_number % 2 == 0 and winning_number != 0:
                    won = True
                    multiplier = 2
            
            winnings = bet_amount * multiplier if won else 0
            
            return {
                'outcome': 'win' if won else 'loss',
                'winnings': winnings,
                'winning_number': winning_number,
                'winning_color': winning_color,
                'bet_type': bet_type,
                'bet_value': bet_value,
                'multiplier': multiplier,
                'message': f'Ball landed on {winning_number} ({winning_color})!'
            }
        
        elif game_type == 'slots':
            # Slots game logic
            symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
            weights = [30, 25, 20, 15, 7, 2, 1]  # Weighted probabilities
            
            # Spin reels
            reel1 = random.choices(symbols, weights=weights)[0]
            reel2 = random.choices(symbols, weights=weights)[0]
            reel3 = random.choices(symbols, weights=weights)[0]
            
            # Check for wins
            multiplier = 0
            if reel1 == reel2 == reel3:
                # Three of a kind
                symbol_multipliers = {
                    '🍒': 5, '🍋': 10, '🍊': 15, '🍇': 20,
                    '🔔': 50, '💎': 100, '7️⃣': 500
                }
                multiplier = symbol_multipliers.get(reel1, 5)
            elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
                # Two of a kind
                multiplier = 2
            
            winnings = bet_amount * multiplier
            
            return {
                'outcome': 'win' if multiplier > 0 else 'loss',
                'winnings': winnings,
                'reels': [reel1, reel2, reel3],
                'multiplier': multiplier,
                'message': f'Reels: {reel1} {reel2} {reel3}' + (f' - {multiplier}x win!' if multiplier > 0 else ' - No match')
            }
        
        elif game_type == 'blackjack':
            # Simplified blackjack logic
            action = game_data.get('action', 'deal')
            
            if action == 'deal':
                # Deal initial cards
                player_cards = [random.randint(1, 11), random.randint(1, 11)]
                dealer_cards = [random.randint(1, 11)]
                
                player_total = sum(player_cards)
                
                # Handle aces
                if player_total > 21 and 11 in player_cards:
                    player_cards[player_cards.index(11)] = 1
                    player_total = sum(player_cards)
                
                if player_total == 21:
                    # Blackjack!
                    winnings = bet_amount * 2.5
                    return {
                        'outcome': 'win',
                        'winnings': winnings,
                        'player_cards': player_cards,
                        'dealer_cards': dealer_cards,
                        'player_total': player_total,
                        'multiplier': 2.5,
                        'message': 'Blackjack! You won!'
                    }
                elif player_total > 21:
                    # Bust
                    return {
                        'outcome': 'loss',
                        'winnings': 0,
                        'player_cards': player_cards,
                        'dealer_cards': dealer_cards,
                        'player_total': player_total,
                        'message': 'Bust! You went over 21.'
                    }
                else:
                    # Continue game
                    return {
                        'outcome': 'continue',
                        'winnings': 0,
                        'player_cards': player_cards,
                        'dealer_cards': dealer_cards,
                        'player_total': player_total,
                        'message': f'Your total: {player_total}. Hit or Stand?'
                    }
        
        elif game_type == 'tower':
            # Tower game logic
            action = game_data.get('action', 'start')
            
            if action == 'select_tile':
                level = game_data.get('level', 0)
                tile = game_data.get('tile', 0)
                current_level = game_data.get('current_level', 0)
                
                # Each level has 2 safe tiles and 1 dangerous tile
                safe_tiles = random.sample(range(3), 2)
                
                if tile in safe_tiles:
                    # Safe tile - advance level
                    new_level = current_level + 1
                    multipliers = [1.0, 1.5, 2.25, 3.38, 5.06, 7.59, 11.39, 17.09]
                    
                    if new_level >= 8:
                        # Reached the top!
                        winnings = bet_amount * multipliers[7]
                        return {
                            'outcome': 'win',
                            'winnings': winnings,
                            'level': new_level,
                            'multiplier': multipliers[7],
                            'message': 'You reached the top of the tower!'
                        }
                    else:
                        return {
                            'outcome': 'continue',
                            'winnings': 0,
                            'level': new_level,
                            'multiplier': multipliers[new_level],
                            'message': f'Safe! Advanced to level {new_level + 1}'
                        }
                else:
                    # Dangerous tile - game over
                    return {
                        'outcome': 'loss',
                        'winnings': 0,
                        'level': current_level,
                        'message': 'Hit a dangerous tile! Game over.'
                    }
        
        elif game_type == 'wheel':
            # Wheel of Fortune game logic
            selected_segment = game_data.get('selected_segment', 1)
            
            # Define wheel segments with their multipliers
            segments = {
                1: 2, 2: 3, 3: 5, 4: 2,
                5: 10, 6: 3, 7: 5, 8: 20
            }
            
            # Spin the wheel (weighted towards lower multipliers)
            weights = [25, 20, 15, 25, 8, 20, 15, 2]  # Lower chance for higher multipliers
            winning_segment = random.choices(list(segments.keys()), weights=weights)[0]
            
            if winning_segment == selected_segment:
                multiplier = segments[winning_segment]
                winnings = bet_amount * multiplier
                return {
                    'outcome': 'win',
                    'winnings': winnings,
                    'winning_segment': winning_segment,
                    'selected_segment': selected_segment,
                    'multiplier': multiplier,
                    'message': f'Perfect prediction! {multiplier}x multiplier!'
                }
            else:
                return {
                    'outcome': 'loss',
                    'winnings': 0,
                    'winning_segment': winning_segment,
                    'selected_segment': selected_segment,
                    'message': f'Wheel landed on segment {winning_segment}'
                }
        
        elif game_type == 'roll':
            # Simple dice roll game (alias for dice)
            return process_game_logic('dice', bet_amount, game_data)
        
        # Default case for unimplemented games
        return {
            'outcome': 'loss',
            'winnings': 0,
            'message': f'Game {game_type} not implemented yet'
        }
        
    except Exception as e:
        return {
            'outcome': 'error',
            'winnings': 0,
            'message': f'Game error: {str(e)}'
        }

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 12000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)