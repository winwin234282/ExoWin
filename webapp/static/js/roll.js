// Roll Game JavaScript
class RollGame {
    constructor() {
        this.isRolling = false;
        this.currentBet = 0;
        this.targetNumber = 50;
        this.rollUnder = true;
        this.initializeElements();
        this.bindEvents();
        this.updateMultiplier();
    }

    initializeElements() {
        this.rollBtn = document.getElementById('roll-btn');
        this.betAmountInput = document.getElementById('bet-amount');
        this.targetInput = document.getElementById('target-number');
        this.rollUnderCheckbox = document.getElementById('roll-under');
        this.gameStatus = document.getElementById('game-status');
        this.balanceSpan = document.getElementById('balance');
        this.multiplierSpan = document.getElementById('multiplier');
        this.winChanceSpan = document.getElementById('win-chance');
        this.lastRollSpan = document.getElementById('last-roll');
        this.rollHistory = document.getElementById('roll-history');
    }

    bindEvents() {
        this.rollBtn.addEventListener('click', () => this.roll());
        this.targetInput.addEventListener('input', () => this.updateMultiplier());
        this.rollUnderCheckbox.addEventListener('change', () => {
            this.rollUnder = this.rollUnderCheckbox.checked;
            this.updateMultiplier();
        });
    }

    updateMultiplier() {
        this.targetNumber = parseFloat(this.targetInput.value);
        this.rollUnder = this.rollUnderCheckbox.checked;
        
        let winChance;
        if (this.rollUnder) {
            winChance = this.targetNumber;
        } else {
            winChance = 100 - this.targetNumber;
        }
        
        const multiplier = (98 / winChance); // 2% house edge
        
        this.multiplierSpan.textContent = `${multiplier.toFixed(4)}x`;
        this.winChanceSpan.textContent = `${winChance.toFixed(2)}%`;
    }

    async roll() {
        const betAmount = parseFloat(this.betAmountInput.value);
        
        if (!betAmount || betAmount <= 0) {
            this.showMessage('Please enter a valid bet amount', 'error');
            return;
        }

        if (this.isRolling) {
            this.showMessage('Please wait for current roll to finish!', 'error');
            return;
        }

        this.currentBet = betAmount;
        this.isRolling = true;
        this.rollBtn.disabled = true;
        this.rollBtn.textContent = '🎲 Rolling...';

        // Animate rolling
        this.animateRoll();

        try {
            const response = await fetch('/api/game/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    game_type: 'roll',
                    bet_amount: betAmount,
                    game_data: {
                        target_number: this.targetNumber,
                        roll_under: this.rollUnder
                    }
                })
            });

            const data = await response.json();

            setTimeout(() => {
                if (data.success) {
                    this.handleRollResult(data.result);
                    this.balanceSpan.textContent = data.new_balance;
                } else {
                    this.showMessage(data.error, 'error');
                }
                
                this.isRolling = false;
                this.rollBtn.disabled = false;
                this.rollBtn.textContent = '🎲 Roll Dice';
            }, 2000);

        } catch (error) {
            setTimeout(() => {
                this.showMessage('Network error. Please try again.', 'error');
                this.isRolling = false;
                this.rollBtn.disabled = false;
                this.rollBtn.textContent = '🎲 Roll Dice';
            }, 2000);
        }
    }

    animateRoll() {
        let counter = 0;
        const interval = setInterval(() => {
            this.lastRollSpan.textContent = (Math.random() * 100).toFixed(2);
            counter++;
            
            if (counter >= 20) {
                clearInterval(interval);
            }
        }, 100);
    }

    handleRollResult(result) {
        const rollNumber = result.roll_number;
        const winnings = result.winnings;

        this.lastRollSpan.textContent = rollNumber.toFixed(2);

        // Add to history
        this.addToHistory(rollNumber, winnings > 0);

        if (winnings > 0) {
            this.showMessage(`🎉 Rolled ${rollNumber.toFixed(2)}! Won $${winnings}!`, 'success');
        } else {
            this.showMessage(`💸 Rolled ${rollNumber.toFixed(2)}. Lost $${this.currentBet}`, 'error');
        }
    }

    addToHistory(rollNumber, won) {
        const historyItem = document.createElement('div');
        historyItem.className = `history-item ${won ? 'win' : 'loss'}`;
        historyItem.textContent = rollNumber.toFixed(2);
        
        this.rollHistory.insertBefore(historyItem, this.rollHistory.firstChild);
        
        // Keep only last 10 rolls
        while (this.rollHistory.children.length > 10) {
            this.rollHistory.removeChild(this.rollHistory.lastChild);
        }
    }

    showMessage(message, type) {
        this.gameStatus.textContent = message;
        this.gameStatus.className = `game-status ${type}`;
        this.gameStatus.style.display = 'block';
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new RollGame();
});