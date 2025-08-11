import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.games.blackjack import Card, Deck, BlackjackGame

class TestBlackjackGame(unittest.TestCase):
    """Test blackjack game logic"""
    
    def test_card_values(self):
        """Test card value calculations"""
        # Number cards
        card_5 = Card("♠️", "5")
        self.assertEqual(card_5.get_value(), 5)
        
        # Face cards
        king = Card("♥️", "K")
        self.assertEqual(king.get_value(), 10)
        
        queen = Card("♦️", "Q")
        self.assertEqual(queen.get_value(), 10)
        
        jack = Card("♣️", "J")
        self.assertEqual(jack.get_value(), 10)
        
        # Ace
        ace = Card("♠️", "A")
        self.assertEqual(ace.get_value(), 11)
    
    def test_deck_creation(self):
        """Test deck creation and shuffling"""
        deck = Deck()
        
        # Should have 52 cards
        self.assertEqual(len(deck.cards), 52)
        
        # Should be able to draw cards
        card = deck.draw()
        self.assertIsInstance(card, Card)
        self.assertEqual(len(deck.cards), 51)
    
    def test_blackjack_game_initialization(self):
        """Test blackjack game initialization"""
        game = BlackjackGame(user_id=123456, bet_amount=10.0)
        
        self.assertEqual(game.user_id, 123456)
        self.assertEqual(game.bet_amount, 10.0)
        # Game automatically deals initial cards
        self.assertEqual(len(game.player_hand), 2)
        self.assertEqual(len(game.dealer_hand), 2)
        # Game might be over if blackjack is dealt
        self.assertIsInstance(game.game_over, bool)
    
    def test_hand_value_calculation(self):
        """Test hand value calculation with aces"""
        game = BlackjackGame(user_id=123456, bet_amount=10.0)
        
        # Test normal hand
        game.player_hand = [Card("♠️", "K"), Card("♥️", "5")]
        self.assertEqual(game.get_hand_value(game.player_hand), 15)
        
        # Test blackjack
        game.player_hand = [Card("♠️", "A"), Card("♥️", "K")]
        self.assertEqual(game.get_hand_value(game.player_hand), 21)
        
        # Test ace adjustment
        game.player_hand = [Card("♠️", "A"), Card("♥️", "A"), Card("♦️", "9")]
        value = game.get_hand_value(game.player_hand)
        self.assertEqual(value, 21)  # A + A + 9 = 1 + 1 + 9 = 11, then one ace becomes 11

if __name__ == '__main__':
    unittest.main()