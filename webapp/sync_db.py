import os
import pymongo
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, Dict, Any
from src.utils.logger import db_logger

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "gamble_bot")

# Use synchronous pymongo client for webapp
client = pymongo.MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
users_collection = db["users"]
transactions_collection = db["transactions"]
games_collection = db["games"]

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user from database or create if not exists"""
    try:
        db_logger.debug(f"Getting user {user_id}")
        user = users_collection.find_one({"user_id": user_id})
        if not user:
            user = {
                "user_id": user_id,
                "balance": 1.0,
                "total_wins": 0,
                "total_losses": 0,
                "total_bets": 0,
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow()
            }
            users_collection.insert_one(user)
            db_logger.info(f"Created new user {user_id}")
        else:
            # Update last active
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"last_active": datetime.utcnow()}}
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
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}}
        )
        return result.modified_count > 0
    except Exception as e:
        db_logger.error(f"Database error in update_user_balance: {e}")
        raise

def record_transaction(user_id: int, amount: float, transaction_type: str, game_id: str = None, description: str = None) -> str:
    """Record a transaction"""
    try:
        transaction = {
            "user_id": user_id,
            "amount": amount,
            "type": transaction_type,
            "game_id": game_id,
            "description": description,
            "timestamp": datetime.utcnow()
        }
        result = transactions_collection.insert_one(transaction)
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
            "timestamp": datetime.utcnow()
        }
        result = games_collection.insert_one(game)
        
        # Update user stats
        if winnings > 0:
            users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"total_wins": 1, "total_bets": 1}}
            )
        else:
            users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"total_losses": 1, "total_bets": 1}}
            )
        
        return str(result.inserted_id)
    except Exception as e:
        db_logger.error(f"Database error in record_game: {e}")
        raise