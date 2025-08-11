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
                this.gameState = response.game;
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
                this.gameState = response.game;
                this.updateDisplay();
                if (response.new_balance !== undefined) {
                    this.balanceSpan.textContent = response.new_balance;
                }

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
                this.gameState = response.game;
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
        let endpoint = '/api/game/bet';
        let requestData = {
            user_id: getUserId(),
            game_type: 'blackjack',
            bet_amount: this.currentBet,
            game_data: {
                action: action,
                game_state: this.gameState,
                ...extraData
            }
        };

        // Use specific blackjack endpoints for better handling
        if (action === 'deal') {
            endpoint = '/api/blackjack/deal';
            requestData = {
                user_id: getUserId(),
                bet_amount: this.currentBet
            };
        } else if (action === 'hit') {
            endpoint = '/api/blackjack/hit';
            requestData = {
                user_id: getUserId()
            };
        } else if (action === 'stand') {
            endpoint = '/api/blackjack/stand';
            requestData = {
                user_id: getUserId()
            };
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        return await response.json();
    }

    updateDisplay() {
        // Display player cards
        this.displayCards(this.gameState.player_hand, this.playerCardsDiv);
        this.playerTotalDiv.textContent = `Total: ${this.gameState.player_value}`;

        // Display dealer cards
        if (this.gameState.game_over) {
            this.displayCards(this.gameState.dealer_hand, this.dealerCardsDiv, true);
            this.dealerTotalDiv.textContent = `Total: ${this.gameState.dealer_value}`;
            this.dealerTotalDiv.style.display = 'block';
        } else {
            this.displayCards(this.gameState.dealer_hand, this.dealerCardsDiv, false);
            this.dealerTotalDiv.style.display = 'none';
        }

        // Update game status
        let message = '';
        if (this.gameState.result) {
            if (this.gameState.result === 'blackjack') {
                message = '🃏 BLACKJACK!';
            } else if (this.gameState.result === 'bust') {
                message = '💥 BUST!';
            } else if (this.gameState.result === 'player_win') {
                message = '🎉 You Win!';
            } else if (this.gameState.result === 'dealer_win') {
                message = '😔 Dealer Wins';
            } else if (this.gameState.result === 'push') {
                message = '🤝 Push (Tie)';
            } else if (this.gameState.result === 'dealer_bust') {
                message = '🎉 Dealer Busts - You Win!';
            }
        } else {
            message = 'Your turn - Hit or Stand?';
        }
        
        this.gameStatus.textContent = message;
        this.gameStatus.className = `game-status ${this.gameState.result || 'playing'}`;
        this.gameStatus.style.display = 'block';
    }

    displayCards(cards, container, showAll = true) {
        container.innerHTML = '';
        cards.forEach((card, index) => {
            if (!showAll && index === 1) {
                container.appendChild(this.createCardBack());
            } else {
                container.appendChild(this.createCard(card.rank, card.suit));
            }
        });
    }

    createCard(rank, suit = '♠️') {
        const card = document.createElement('div');
        card.className = 'card';
        if (suit === '♥️' || suit === '♦️') {
            card.classList.add('red');
        }
        
        card.innerHTML = `${rank}<br>${suit}`;
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
            if (this.gameState.result === 'blackjack') {
                window.gambleAPI.playSound('blackjack', 0.6);
                this.showMessage(`🃏 BLACKJACK! You won $${this.gameState.winnings.toFixed(2)}!`, 'success');
            } else if (this.gameState.result === 'push') {
                window.gambleAPI.playSound('win', 0.3);
                this.showMessage(`🤝 PUSH! Your bet of $${this.currentBet.toFixed(2)} was returned`, 'info');
            } else {
                window.gambleAPI.playSound('win', 0.5);
                this.showMessage(`🎉 You won $${this.gameState.winnings.toFixed(2)}!`, 'success');
            }
        } else {
            // Check for bust
            if (this.gameState.result === 'bust') {
                window.gambleAPI.playSound('bust', 0.5);
                this.showMessage(`💥 BUST! You lost $${this.currentBet.toFixed(2)}`, 'error');
            } else {
                window.gambleAPI.playSound('lose', 0.5);
                this.showMessage(`💸 You lost $${this.currentBet.toFixed(2)}`, 'error');
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