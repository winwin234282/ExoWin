import re
from typing import Optional, Union
from src.utils.logger import bot_logger

class InputValidator:
    """Input validation and sanitization utilities"""
    
    @staticmethod
    def validate_bet_amount(amount: Union[str, float, int]) -> Optional[float]:
        """Validate and sanitize bet amount"""
        try:
            # Convert to float
            if isinstance(amount, str):
                # Check for negative values first
                if amount.strip().startswith('-'):
                    return None
                # Remove any non-numeric characters except decimal point
                amount = re.sub(r'[^\d.]', '', amount)
                if not amount:
                    return None
                amount = float(amount)
            
            amount = float(amount)
            
            # Check bounds
            if amount <= 0:
                return None
            if amount > 10000:  # Max bet limit
                return None
            
            # Round to 2 decimal places
            return round(amount, 2)
            
        except (ValueError, TypeError):
            bot_logger.warning(f"Invalid bet amount: {amount}")
            return None
    
    @staticmethod
    def validate_user_id(user_id: Union[str, int]) -> Optional[int]:
        """Validate Telegram user ID"""
        try:
            user_id = int(user_id)
            if user_id <= 0:
                return None
            return user_id
        except (ValueError, TypeError):
            bot_logger.warning(f"Invalid user ID: {user_id}")
            return None
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """Sanitize user text input"""
        if not isinstance(text, str):
            return ""
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', '', text)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def validate_game_choice(choice: Union[str, int], valid_choices: list) -> Optional[int]:
        """Validate game choice (like dice number, card choice, etc.)"""
        try:
            choice = int(choice)
            if choice in valid_choices:
                return choice
            return None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_crypto_address(address: str, crypto_type: str = "btc") -> bool:
        """Basic crypto address validation"""
        if not isinstance(address, str):
            return False
        
        address = address.strip()
        
        if crypto_type.lower() == "btc":
            # Basic Bitcoin address validation
            if len(address) < 26 or len(address) > 35:
                return False
            if not re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$', address):
                return False
        
        return True

# Global validator instance
validator = InputValidator()