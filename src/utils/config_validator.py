import os
from typing import List, Tuple
from src.utils.logger import bot_logger

class ConfigValidator:
    """Validate environment configuration"""
    
    REQUIRED_VARS = [
        "BOT_TOKEN",
        "MONGODB_URI", 
        "DATABASE_NAME",
        "ADMIN_USER_ID",
        "SECRET_KEY",
        "FLASK_SECRET_KEY"
    ]
    
    OPTIONAL_VARS = [
        "PAYMENT_PROVIDER_TOKEN",
        "NOWPAYMENTS_API_KEY", 
        "NOWPAYMENTS_IPN_SECRET",
        "WEBHOOK_URL",
        "WEBAPP_URL",
        "DEBUG",
        "FLASK_PORT"
    ]
    
    @classmethod
    def validate_config(cls) -> Tuple[bool, List[str]]:
        """Validate all configuration variables"""
        missing_vars = []
        warnings = []
        
        # Check required variables
        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value or value == f"your_{var.lower()}_here":
                missing_vars.append(var)
        
        # Check optional but important variables
        for var in cls.OPTIONAL_VARS:
            value = os.getenv(var)
            if not value or "your_" in value.lower():
                warnings.append(f"Optional variable {var} not configured")
        
        # Validate specific formats
        admin_id = os.getenv("ADMIN_USER_ID")
        if admin_id and not admin_id.isdigit():
            missing_vars.append("ADMIN_USER_ID (must be numeric)")
        
        flask_port = os.getenv("FLASK_PORT", "12000")
        if not flask_port.isdigit():
            warnings.append("FLASK_PORT should be numeric")
        
        # Log results
        if missing_vars:
            bot_logger.error(f"Missing required configuration: {missing_vars}")
        
        if warnings:
            bot_logger.warning(f"Configuration warnings: {warnings}")
        
        return len(missing_vars) == 0, missing_vars + warnings
    
    @classmethod
    def get_config_status(cls) -> str:
        """Get human-readable configuration status"""
        is_valid, issues = cls.validate_config()
        
        if is_valid:
            return "✅ Configuration is valid and ready for production"
        else:
            return f"⚠️ Configuration issues found:\n" + "\n".join(f"- {issue}" for issue in issues)

# Validate on import
config_validator = ConfigValidator()