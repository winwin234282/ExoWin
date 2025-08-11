import traceback
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from src.utils.logger import bot_logger

def handle_errors(func):
    """Decorator to handle errors in bot commands"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            # Log the error
            bot_logger.error(f"Error in {func.__name__}: {str(e)}")
            bot_logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Send user-friendly error message
            error_message = (
                "🚫 **Oops! Something went wrong.**\n\n"
                "Our team has been notified. Please try again in a moment.\n"
                "If the problem persists, contact support."
            )
            
            try:
                if update.message:
                    await update.message.reply_text(error_message, parse_mode='Markdown')
                elif update.callback_query:
                    await update.callback_query.message.reply_text(error_message, parse_mode='Markdown')
            except Exception as send_error:
                bot_logger.error(f"Failed to send error message: {send_error}")
    
    return wrapper

def handle_callback_errors(func):
    """Decorator to handle errors in callback queries"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            # Log the error
            bot_logger.error(f"Error in callback {func.__name__}: {str(e)}")
            bot_logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Answer the callback query to prevent loading state
            if update.callback_query:
                try:
                    await update.callback_query.answer("❌ An error occurred. Please try again.", show_alert=True)
                except Exception:
                    pass
    
    return wrapper

class GameError(Exception):
    """Custom exception for game-related errors"""
    pass

class InsufficientFundsError(GameError):
    """Exception for insufficient balance"""
    pass

class InvalidBetError(GameError):
    """Exception for invalid bet amounts"""
    pass

class DatabaseError(Exception):
    """Exception for database-related errors"""
    pass