class PokerGame {
    constructor() {
        this.gameState = null;
        this.userId = this.getUserId();
        this.balance = 0;
        this.initializeGame();
    }

    getUserId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('user_id');
    }

    async initializeGame() {
        await this.updateBalance();
        this.setupEventListeners();
    }

    async updateBalance() {
        try {
            const response = await fetch('/api/user/balance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.userId })
            });
            const data = await response.json();
            if (data.success) {
                this.balance = data.balance;
                document.getElementById('balance').textContent = `$${this.balance.toFixed(2)}`;
            }
        } catch (error) {
            console.error('Error updating balance:', error);
        }
    }

    setupEventListeners() {
        document.getElementById('start-game').addEventListener('click', () => this.startGame());
        document.getElementById('finish-game').addEventListener('click', () => this.finishGame());
    }

    async startGame() {
        const betAmount = parseFloat(document.getElementById('bet-amount').value);
        if (!betAmount || betAmount <= 0) {
            alert('Please enter a valid bet amount');
            return;
        }

        if (betAmount > this.balance) {
            alert('Insufficient balance');
            return;
        }

        try {
            const response = await fetch('/api/poker/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    bet_amount: betAmount
                })
            });

            const data = await response.json();
            if (data.success) {
                this.gameState = data.game;
                this.balance = data.new_balance;
                this.updateUI();
            } else {
                alert(data.error || 'Failed to start game');
            }
        } catch (error) {
            console.error('Error starting game:', error);
            alert('Error starting game');
        }
    }

    async finishGame() {
        if (!this.gameState) {
            alert('No active game');
            return;
        }

        try {
            const response = await fetch('/api/poker/finish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.userId })
            });

            const data = await response.json();
            if (data.success) {
                this.gameState = data.game;
                this.balance = data.new_balance;
                this.updateUI();
                this.showResult();
            } else {
                alert(data.error || 'Failed to finish game');
            }
        } catch (error) {
            console.error('Error finishing game:', error);
            alert('Error finishing game');
        }
    }

    updateUI() {
        document.getElementById('balance').textContent = `$${this.balance.toFixed(2)}`;
        
        if (this.gameState) {
            // Update player hand
            const playerHandDiv = document.getElementById('player-hand');
            playerHandDiv.innerHTML = '';
            this.gameState.player_hand.forEach(card => {
                const cardDiv = document.createElement('div');
                cardDiv.className = 'card';
                cardDiv.textContent = `${card.rank}${card.suit}`;
                playerHandDiv.appendChild(cardDiv);
            });

            // Update dealer hand if game is over
            if (this.gameState.game_over && this.gameState.dealer_hand.length > 0) {
                const dealerHandDiv = document.getElementById('dealer-hand');
                dealerHandDiv.innerHTML = '';
                this.gameState.dealer_hand.forEach(card => {
                    const cardDiv = document.createElement('div');
                    cardDiv.className = 'card';
                    cardDiv.textContent = `${card.rank}${card.suit}`;
                    dealerHandDiv.appendChild(cardDiv);
                });
            }

            // Update game controls
            document.getElementById('start-game').style.display = this.gameState.game_over ? 'block' : 'none';
            document.getElementById('finish-game').style.display = this.gameState.game_over ? 'none' : 'block';
        }
    }

    showResult() {
        if (this.gameState && this.gameState.game_over) {
            const resultDiv = document.getElementById('game-result');
            let message = '';
            
            if (this.gameState.result === 'win') {
                message = `You win! ${this.gameState.player_hand_rank[1]} beats ${this.gameState.dealer_hand_rank[1]}. Winnings: $${this.gameState.winnings.toFixed(2)}`;
            } else if (this.gameState.result === 'lose') {
                message = `You lose! ${this.gameState.dealer_hand_rank[1]} beats ${this.gameState.player_hand_rank[1]}.`;
            } else {
                message = `It's a tie! Both have ${this.gameState.player_hand_rank[1]}. Bet returned.`;
            }
            
            resultDiv.textContent = message;
            resultDiv.style.display = 'block';
        }
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new PokerGame();
});