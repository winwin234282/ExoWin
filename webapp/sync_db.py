import os
import pymongo
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, Dict, Any
from src.utils.logger import db_logger

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "exowin_bot")

# Use synchronous pymongo client for webapp
client = pymongo.MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
users_collection = db["users"]
transactions_collection = db["transactions"]
games_collection = db["games"]

def get_user(user_id: int, user_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Get user from database or create if not exists"""
    try:
        db_logger.debug(f"Getting user {user_id}")
        user = users_collection.find_one({"user_id": user_id})
        if not user:
            user = {
                "user_id": user_id,
                "balance": 1.0,  # Starting balance of $1
                "created_at": datetime.now(),
                "last_active": datetime.now(),
                "total_bets": 0,
                "total_wins": 0,
                "total_losses": 0,
                "total_deposits": 0,
                "total_withdrawals": 0,
                "is_banned": False,
                # New fields for bonuses and settings
                "daily_bonus_streak": 0,
                "last_daily_bonus": None,
                "total_daily_bonuses": 0.0,
                "total_referrals": 0,
                "total_referral_bonuses": 0.0,
                "total_event_bonuses": 0.0,
                "referred_by": None,
                # Settings
                "notifications_enabled": True,
                "sound_effects": True,
                "theme": "dark",
                "language": "en",
                "auto_bet_enabled": False,
                "quick_bet_enabled": False,
                # User info fields
                "username": None,
                "first_name": None,
                "last_name": None
            }
            
            # Add user data if provided
            if user_data:
                user.update({
                    "username": user_data.get('username'),
                    "first_name": user_data.get('first_name'),
                    "last_name": user_data.get('last_name')
                })
            
            users_collection.insert_one(user)
            db_logger.info(f"Created new user {user_id}")
        else:
            # Update last active and user info if provided
            update_data = {"last_active": datetime.now()}
            if user_data:
                update_data.update({
                    "username": user_data.get('username'),
                    "first_name": user_data.get('first_name'),
                    "last_name": user_data.get('last_name')
                })
            
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
        
        # Remove MongoDB ObjectId for JSON serialization
        if '_id' in user:
            del user['_id']
        
        return user
    except Exception as e:
        db_logger.error(f"Database error in get_user: {e}")
        raise

def update_user_balance(user_id: int, amount: float) -> bool:
    """Update user balance"""
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}, "$set": {"last_active": datetime.now()}}
        )
        
        # Update stats based on transaction type
        if amount > 0:
            users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"total_wins": 1}}
            )
        elif amount < 0:
            users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"total_losses": 1}}
            )
        
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"total_bets": 1}}
        )
        
        return True
    except Exception as e:
        db_logger.error(f"Database error in update_user_balance: {e}")
        raise

def record_transaction(user_id: int, amount: float, transaction_type: str, game_id: str = None, description: str = None) -> str:
    """Record a transaction"""
    try:
        transaction = {
            "user_id": user_id,
            "amount": amount,
            "type": transaction_type,  # deposit, withdrawal, bet, win
            "game_id": game_id,
            "description": description,
            "timestamp": datetime.now()
        }
        result = transactions_collection.insert_one(transaction)
        
        # Update user stats for deposits and withdrawals
        if transaction_type == "deposit":
            users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"total_deposits": amount}}
            )
        elif transaction_type == "withdrawal":
            users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"total_withdrawals": amount}}
            )
        
        return str(result.inserted_id)
    except Exception as e:
        db_logger.error(f"Database error in record_transaction: {e}")
        raise

def record_game(user_id: int, game_type: str, bet_amount: float, outcome: str, winnings: float) -> str:
    """Record a game result"""
    try:
        game = {
            "user_id": user_id,
            "game_type": game_type,
            "bet_amount": bet_amount,
            "outcome": outcome,
            "winnings": winnings,
            "timestamp": datetime.now()
        }
        result = games_collection.insert_one(game)
        return str(result.inserted_id)
    except Exception as e:
        db_logger.error(f"Database error in record_game: {e}")
        raise