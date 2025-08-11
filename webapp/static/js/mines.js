// Mines Game JavaScript
class MinesGame {
    constructor() {
        this.gameState = null;
        this.isPlaying = false;
        this.currentBet = 0;
        this.minesCount = 3;
        this.gridSize = 25; // 5x5 grid
        this.initializeElements();
        this.bindEvents();
        this.createGrid();
    }

    initializeElements() {
        this.startBtn = document.getElementById('start-btn');
        this.cashoutBtn = document.getElementById('cashout-btn');
        this.betAmountInput = document.getElementById('bet-amount');
        this.minesCountInput = document.getElementById('mines-count');
        this.gameGrid = document.getElementById('game-grid');
        this.gameStatus = document.getElementById('game-status');
        this.currentMultiplier = document.getElementById('current-multiplier');
        this.potentialWin = document.getElementById('potential-win');
        this.balanceSpan = document.getElementById('balance');
        this.gemsFound = document.getElementById('gems-found');
        this.minesLeft = document.getElementById('mines-left');
    }

    bindEvents() {
        this.startBtn.addEventListener('click', () => this.startGame());
        this.cashoutBtn.addEventListener('click', () => this.cashout());
        this.minesCountInput.addEventListener('change', () => {
            this.minesCount = parseInt(this.minesCountInput.value);
            this.updateMultiplierDisplay();
        });
    }

    createGrid() {
        this.gameGrid.innerHTML = '';
        this.gameGrid.style.gridTemplateColumns = 'repeat(5, 1fr)';
        
        for (let i = 0; i < this.gridSize; i++) {
            const cell = document.createElement('div');
            cell.className = 'mine-cell';
            cell.dataset.index = i;
            cell.addEventListener('click', () => this.revealCell(i));
            this.gameGrid.appendChild(cell);
        }
    }

    async startGame() {
        const betAmount = parseFloat(this.betAmountInput.value);
        
        if (!betAmount || betAmount <= 0) {
            this.showMessage('Please enter a valid bet amount', 'error');
            return;
        }

        this.currentBet = betAmount;
        this.minesCount = parseInt(this.minesCountInput.value);
        this.isPlaying = true;

        try {
            const response = await fetch('/api/game/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    game_type: 'mines',
                    bet_amount: betAmount,
                    game_data: {
                        action: 'start',
                        mines_count: this.minesCount
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                this.gameState = data.result;
                this.balanceSpan.textContent = data.new_balance;
                this.updateGameDisplay();
                this.enableGrid();
                this.startBtn.disabled = true;
                this.cashoutBtn.disabled = false;
                this.showMessage('💎 Find gems and avoid mines!', 'info');
            } else {
                this.showMessage(data.error, 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        }
    }

    async revealCell(index) {
        if (!this.isPlaying || this.gameState.revealed_cells.includes(index)) {
            return;
        }

        const cell = document.querySelector(`[data-index="${index}"]`);
        cell.classList.add('revealing');

        try {
            const response = await fetch('/api/game/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    game_type: 'mines',
                    bet_amount: this.currentBet,
                    game_data: {
                        action: 'reveal',
                        cell_index: index,
                        game_state: this.gameState
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                this.gameState = data.result;
                this.balanceSpan.textContent = data.new_balance;
                
                if (this.gameState.hit_mine) {
                    // Hit a mine
                    window.gambleAPI.playSound('explosion', 0.7);
                    cell.classList.add('mine');
                    cell.textContent = '💣';
                    this.showMessage(`💥 BOOM! You hit a mine! Lost $${this.currentBet}`, 'error');
                    this.endGame(false);
                } else {
                    // Found a gem
                    window.gambleAPI.playSound('safe_click', 0.4);
                    cell.classList.add('gem');
                    cell.textContent = '💎';
                    this.updateGameDisplay();
                    
                    if (this.gameState.gems_found === this.gridSize - this.minesCount) {
                        // Found all gems
                        window.gambleAPI.playSound('jackpot', 0.6);
                        this.showMessage(`🎉 All gems found! Won $${this.gameState.winnings}!`, 'success');
                        this.endGame(true);
                    } else {
                        this.showMessage(`💎 Gem found! Multiplier: ${this.gameState.multiplier.toFixed(2)}x`, 'success');
                    }
                }
            } else {
                this.showMessage(data.error, 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        }

        cell.classList.remove('revealing');
    }

    async cashout() {
        if (!this.isPlaying || this.gameState.gems_found === 0) {
            this.showMessage('No gems found to cash out!', 'error');
            return;
        }

        try {
            const response = await fetch('/api/game/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    game_type: 'mines',
                    bet_amount: this.currentBet,
                    game_data: {
                        action: 'cashout',
                        game_state: this.gameState
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                this.balanceSpan.textContent = data.new_balance;
                this.showMessage(`💰 Cashed out! Won $${data.result.winnings}!`, 'success');
                this.endGame(true);
            } else {
                this.showMessage(data.error, 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        }
    }

    updateGameDisplay() {
        if (!this.gameState) return;

        this.gemsFound.textContent = this.gameState.gems_found;
        this.minesLeft.textContent = this.minesCount;
        this.currentMultiplier.textContent = `${this.gameState.multiplier.toFixed(2)}x`;
        this.potentialWin.textContent = `$${(this.currentBet * this.gameState.multiplier).toFixed(2)}`;
    }

    updateMultiplierDisplay() {
        // Calculate base multiplier for display
        const safeSpots = this.gridSize - this.minesCount;
        const baseMultiplier = Math.pow(1.2, safeSpots);
        this.currentMultiplier.textContent = `${baseMultiplier.toFixed(2)}x`;
    }

    enableGrid() {
        document.querySelectorAll('.mine-cell').forEach(cell => {
            cell.classList.add('clickable');
        });
    }

    disableGrid() {
        document.querySelectorAll('.mine-cell').forEach(cell => {
            cell.classList.remove('clickable');
        });
    }

    endGame(won) {
        this.isPlaying = false;
        this.disableGrid();
        this.startBtn.disabled = false;
        this.cashoutBtn.disabled = true;

        // Reveal all mines if lost
        if (!won && this.gameState && this.gameState.mine_positions) {
            this.gameState.mine_positions.forEach(pos => {
                const cell = document.querySelector(`[data-index="${pos}"]`);
                if (cell && !cell.classList.contains('mine')) {
                    cell.classList.add('mine');
                    cell.textContent = '💣';
                }
            });
        }

        setTimeout(() => {
            this.resetGame();
        }, 3000);
    }

    resetGame() {
        this.gameState = null;
        this.currentBet = 0;
        this.createGrid();
        this.gemsFound.textContent = '0';
        this.currentMultiplier.textContent = '1.00x';
        this.potentialWin.textContent = '$0.00';
        this.gameStatus.style.display = 'none';
    }

    showMessage(message, type) {
        this.gameStatus.textContent = message;
        this.gameStatus.className = `game-status ${type}`;
        this.gameStatus.style.display = 'block';
    }
}

// Initialize game when page loads
let minesGame;
document.addEventListener('DOMContentLoaded', () => {
    minesGame = new MinesGame();
});

// Global functions for HTML onclick handlers
function startGame() {
    if (minesGame) {
        minesGame.startGame();
    }
}

function cashOut() {
    if (minesGame) {
        minesGame.cashOut();
    }
}

function setBetAmount(amount) {
    const betInput = document.getElementById('betAmount');
    if (betInput) {
        betInput.value = amount.toFixed(2);
    }
}

function playAgain() {
    if (minesGame) {
        minesGame.resetGame();
    }
}