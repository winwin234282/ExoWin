import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.validators import InputValidator

class TestInputValidator(unittest.TestCase):
    """Test input validation functions"""
    
    def setUp(self):
        self.validator = InputValidator()
    
    def test_validate_bet_amount(self):
        """Test bet amount validation"""
        # Valid amounts
        self.assertEqual(self.validator.validate_bet_amount("10.50"), 10.50)
        self.assertEqual(self.validator.validate_bet_amount(25), 25.0)
        self.assertEqual(self.validator.validate_bet_amount(100.99), 100.99)
        
        # Invalid amounts
        self.assertIsNone(self.validator.validate_bet_amount("0"))
        self.assertIsNone(self.validator.validate_bet_amount("-5"))
        self.assertIsNone(self.validator.validate_bet_amount("abc"))
        self.assertIsNone(self.validator.validate_bet_amount(""))
        self.assertIsNone(self.validator.validate_bet_amount(15000))  # Too high
    
    def test_validate_user_id(self):
        """Test user ID validation"""
        # Valid IDs
        self.assertEqual(self.validator.validate_user_id("123456"), 123456)
        self.assertEqual(self.validator.validate_user_id(789012), 789012)
        
        # Invalid IDs
        self.assertIsNone(self.validator.validate_user_id("0"))
        self.assertIsNone(self.validator.validate_user_id("-123"))
        self.assertIsNone(self.validator.validate_user_id("abc"))
        self.assertIsNone(self.validator.validate_user_id(""))
    
    def test_sanitize_text(self):
        """Test text sanitization"""
        # Normal text
        self.assertEqual(self.validator.sanitize_text("Hello World"), "Hello World")
        
        # Text with dangerous characters
        self.assertEqual(self.validator.sanitize_text("Hello<script>"), "Helloscript")
        self.assertEqual(self.validator.sanitize_text('Test"quote'), "Testquote")
        
        # Long text
        long_text = "a" * 2000
        result = self.validator.sanitize_text(long_text, max_length=100)
        self.assertEqual(len(result), 100)
    
    def test_validate_game_choice(self):
        """Test game choice validation"""
        valid_choices = [1, 2, 3, 4, 5, 6]
        
        # Valid choices
        self.assertEqual(self.validator.validate_game_choice("3", valid_choices), 3)
        self.assertEqual(self.validator.validate_game_choice(5, valid_choices), 5)
        
        # Invalid choices
        self.assertIsNone(self.validator.validate_game_choice("7", valid_choices))
        self.assertIsNone(self.validator.validate_game_choice("abc", valid_choices))
        self.assertIsNone(self.validator.validate_game_choice("0", valid_choices))

if __name__ == '__main__':
    unittest.main()