def format_money(amount: float) -> str:
    """Format money amount with $ sign and 2 decimal places"""
    return f"${amount:.2f}"

def format_user_stats(user: dict) -> str:
    """Format user statistics for display"""
    return (
        f"💰 Balance: ${user['balance']:.2f}\n"
        f"🎮 Total bets: {user['total_bets']}\n"
        f"🏆 Wins: {user['total_wins']}\n"
        f"❌ Losses: {user['total_losses']}\n"
        f"📥 Total deposits: ${user.get('total_deposits', 0):.2f}\n"
        f"📤 Total withdrawals: ${user.get('total_withdrawals', 0):.2f}"
    )