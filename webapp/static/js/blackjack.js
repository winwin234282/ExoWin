// Blackjack Game JavaScript
class BlackjackGame {
    constructor() {
        this.gameState = null;
        this.currentBet = 0;
        this.isPlaying = false;
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.dealBtn = document.getElementById('deal-btn');
        this.hitBtn = document.getElementById('hit-btn');
        this.standBtn = document.getElementById('stand-btn');
        this.doubleBtn = document.getElementById('double-btn');
        this.betAmountInput = document.getElementById('bet-amount');
        this.betControls = document.getElementById('bet-controls');
        this.gameControls = document.getElementById('game-controls');
        this.gameStatus = document.getElementById('game-status');
        this.playerCardsDiv = document.getElementById('player-cards');
        this.dealerCardsDiv = document.getElementById('dealer-cards');
        this.playerTotalDiv = document.getElementById('player-total');
        this.dealerTotalDiv = document.getElementById('dealer-total');
        this.balanceSpan = document.getElementById('balance');
    }

    bindEvents() {
        this.dealBtn.addEventListener('click', () => this.dealCards());
        this.hitBtn.addEventListener('click', () => this.hit());
        this.standBtn.addEventListener('click', () => this.stand());
        this.doubleBtn.addEventListener('click', () => this.doubleDown());
    }

    async dealCards() {
        const betAmount = parseFloat(this.betAmountInput.value);
        
        if (!betAmount || betAmount <= 0) {
            this.showMessage('Please enter a valid bet amount', 'error');
            return;
        }

        // Play card deal sound
        window.gambleAPI.playSound('card_deal', 0.4);

        this.currentBet = betAmount;
        this.isPlaying = true;
        this.dealBtn.disabled = true;

        try {
            const response = await this.makeGameRequest('deal', { bet_amount: betAmount });
            
            if (response.success) {
                this.gameState = response.result;
                this.updateDisplay();
                this.balanceSpan.textContent = response.new_balance;

                if (this.gameState.game_over) {
                    this.endGame();
                } else {
                    this.betControls.style.display = 'none';
                    this.gameControls.style.display = 'flex';
                }
            } else {
                this.showMessage(response.error, 'error');
                this.resetGame();
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
            this.resetGame();
        }
    }

    async hit() {
        if (!this.isPlaying) return;

        // Play card deal sound
        window.gambleAPI.playSound('card_deal', 0.4);

        try {
            const response = await this.makeGameRequest('hit');
            
            if (response.success) {
                this.gameState = response.result;
                this.updateDisplay();
                this.balanceSpan.textContent = response.new_balance;

                if (this.gameState.game_over) {
                    this.endGame();
                }
            } else {
                this.showMessage(response.error, 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        }
    }

    async stand() {
        if (!this.isPlaying) return;

        try {
            const response = await this.makeGameRequest('stand');
            
            if (response.success) {
                this.gameState = response.result;
                this.updateDisplay();
                this.balanceSpan.textContent = response.new_balance;
                this.endGame();
            } else {
                this.showMessage(response.error, 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        }
    }

    async doubleDown() {
        if (!this.isPlaying) return;

        try {
            const response = await this.makeGameRequest('double', { bet_amount: this.currentBet });
            
            if (response.success) {
                this.gameState = response.result;
                this.currentBet *= 2;
                this.updateDisplay();
                this.balanceSpan.textContent = response.new_balance;
                this.endGame();
            } else {
                this.showMessage(response.error, 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        }
    }

    async makeGameRequest(action, extraData = {}) {
        const response = await fetch('/api/game/bet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: getUserId(),
                game_type: 'blackjack',
                bet_amount: this.currentBet,
                game_data: {
                    action: action,
                    game_state: this.gameState,
                    ...extraData
                }
            })
        });
        
        return await response.json();
    }

    updateDisplay() {
        // Display player cards
        this.displayCards(this.gameState.player_cards, this.playerCardsDiv);
        this.playerTotalDiv.textContent = `Total: ${this.gameState.player_total}`;

        // Display dealer cards
        if (this.gameState.game_over) {
            this.displayCards(this.gameState.dealer_cards, this.dealerCardsDiv, true);
            this.dealerTotalDiv.textContent = `Total: ${this.gameState.dealer_total}`;
            this.dealerTotalDiv.style.display = 'block';
        } else {
            this.displayCards(this.gameState.dealer_cards, this.dealerCardsDiv, false);
            this.dealerTotalDiv.style.display = 'none';
        }

        // Update game status
        this.gameStatus.textContent = this.gameState.message;
        this.gameStatus.className = `game-status ${this.gameState.outcome || 'playing'}`;
        this.gameStatus.style.display = 'block';
    }

    displayCards(cards, container, showAll = true) {
        container.innerHTML = '';
        cards.forEach((cardValue, index) => {
            if (!showAll && index === 1) {
                container.appendChild(this.createCardBack());
            } else {
                const suits = ['♠️', '♥️', '♦️', '♣️'];
                const suit = suits[Math.floor(Math.random() * suits.length)];
                container.appendChild(this.createCard(cardValue, suit));
            }
        });
    }

    createCard(value, suit = '♠️') {
        const card = document.createElement('div');
        card.className = 'card';
        if (suit === '♥️' || suit === '♦️') {
            card.classList.add('red');
        }
        
        let displayValue = value;
        if (value === 11) displayValue = 'J';
        else if (value === 12) displayValue = 'Q';
        else if (value === 13) displayValue = 'K';
        else if (value === 1) displayValue = 'A';
        
        card.innerHTML = `${displayValue}<br>${suit}`;
        return card;
    }

    createCardBack() {
        const card = document.createElement('div');
        card.className = 'card card-back';
        card.textContent = '🂠';
        return card;
    }

    endGame() {
        this.isPlaying = false;
        this.gameControls.style.display = 'none';
        this.betControls.style.display = 'block';
        this.dealBtn.disabled = false;
        
        if (this.gameState.winnings > 0) {
            // Check for blackjack
            if (this.gameState.player_total === 21 && this.gameState.player_cards.length === 2) {
                window.gambleAPI.playSound('blackjack', 0.6);
                this.showMessage(`🃏 BLACKJACK! You won ${this.gameState.winnings} coins!`, 'success');
            } else {
                window.gambleAPI.playSound('win', 0.5);
                this.showMessage(`🎉 You won ${this.gameState.winnings} coins!`, 'success');
            }
        } else {
            // Check for bust
            if (this.gameState.player_total > 21) {
                window.gambleAPI.playSound('bust', 0.5);
                this.showMessage(`💥 BUST! You lost ${this.currentBet} coins`, 'error');
            } else {
                window.gambleAPI.playSound('lose', 0.5);
                this.showMessage(`💸 You lost ${this.currentBet} coins`, 'error');
            }
        }
    }

    resetGame() {
        this.isPlaying = false;
        this.gameState = null;
        this.currentBet = 0;
        this.dealBtn.disabled = false;
        this.betControls.style.display = 'block';
        this.gameControls.style.display = 'none';
        this.gameStatus.style.display = 'none';
        this.playerCardsDiv.innerHTML = '';
        this.dealerCardsDiv.innerHTML = '';
        this.playerTotalDiv.textContent = 'Total: 0';
        this.dealerTotalDiv.textContent = 'Total: 0';
        this.dealerTotalDiv.style.display = 'none';
    }

    showMessage(message, type) {
        const messageDiv = document.getElementById('game-message');
        messageDiv.textContent = message;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new BlackjackGame();
});