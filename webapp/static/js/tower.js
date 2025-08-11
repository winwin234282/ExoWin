// Tower Game JavaScript
class TowerGame {
    constructor() {
        this.gameState = null;
        this.isPlaying = false;
        this.currentBet = 0;
        this.currentLevel = 0;
        this.difficulty = 'medium'; // easy, medium, hard
        this.initializeElements();
        this.bindEvents();
        this.createTower();
    }

    initializeElements() {
        this.startBtn = document.getElementById('start-btn');
        this.cashoutBtn = document.getElementById('cashout-btn');
        this.betAmountInput = document.getElementById('bet-amount');
        this.difficultySelect = document.getElementById('difficulty');
        this.towerContainer = document.getElementById('tower-container');
        this.gameStatus = document.getElementById('game-status');
        this.currentLevel = document.getElementById('current-level');
        this.currentMultiplier = document.getElementById('current-multiplier');
        this.potentialWin = document.getElementById('potential-win');
        this.balanceSpan = document.getElementById('balance');
    }

    bindEvents() {
        this.startBtn.addEventListener('click', () => this.startGame());
        this.cashoutBtn.addEventListener('click', () => this.cashout());
        this.difficultySelect.addEventListener('change', () => {
            this.difficulty = this.difficultySelect.value;
            this.createTower();
        });
    }

    createTower() {
        this.towerContainer.innerHTML = '';
        const levels = 10;
        const blocksPerLevel = this.getBlocksPerLevel();

        for (let level = levels - 1; level >= 0; level--) {
            const levelDiv = document.createElement('div');
            levelDiv.className = 'tower-level';
            levelDiv.dataset.level = level;

            for (let block = 0; block < blocksPerLevel; block++) {
                const blockDiv = document.createElement('div');
                blockDiv.className = 'tower-block';
                blockDiv.dataset.level = level;
                blockDiv.dataset.block = block;
                blockDiv.addEventListener('click', () => this.selectBlock(level, block));
                levelDiv.appendChild(blockDiv);
            }

            this.towerContainer.appendChild(levelDiv);
        }
    }

    getBlocksPerLevel() {
        switch (this.difficulty) {
            case 'easy': return 2; // 1 safe, 1 mine
            case 'medium': return 3; // 2 safe, 1 mine
            case 'hard': return 4; // 3 safe, 1 mine
            default: return 3;
        }
    }

    getMultiplier(level) {
        const base = this.difficulty === 'easy' ? 1.5 : this.difficulty === 'medium' ? 1.3 : 1.2;
        return Math.pow(base, level + 1);
    }

    async startGame() {
        const betAmount = parseFloat(this.betAmountInput.value);
        
        if (!betAmount || betAmount <= 0) {
            this.showMessage('Please enter a valid bet amount', 'error');
            return;
        }

        this.currentBet = betAmount;
        this.currentLevel = 0;
        this.isPlaying = true;
        this.difficulty = this.difficultySelect.value;

        try {
            const response = await fetch('/api/game/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    game_type: 'tower',
                    bet_amount: betAmount,
                    game_data: {
                        action: 'start',
                        difficulty: this.difficulty
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                this.gameState = data.result;
                this.balanceSpan.textContent = data.new_balance;
                this.updateGameDisplay();
                this.enableLevel(0);
                this.startBtn.disabled = true;
                this.cashoutBtn.disabled = false;
                this.showMessage('🏗️ Start climbing! Pick a safe block.', 'info');
            } else {
                this.showMessage(data.error, 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        }
    }

    async selectBlock(level, block) {
        if (!this.isPlaying || level !== this.currentLevel) {
            return;
        }

        const blockElement = document.querySelector(`[data-level="${level}"][data-block="${block}"]`);
        blockElement.classList.add('selected');
        
        // Play click sound
        window.gambleAPI.playSound('click', 0.3);

        try {
            const response = await fetch('/api/game/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    game_type: 'tower',
                    bet_amount: this.currentBet,
                    game_data: {
                        action: 'select',
                        level: level,
                        block: block,
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
                    window.gambleAPI.playSound('explosion', 0.6);
                    blockElement.classList.add('mine');
                    blockElement.textContent = '💣';
                    this.showMessage(`💥 BOOM! You hit a mine! Lost $${this.currentBet}`, 'error');
                    this.revealMines();
                    this.endGame(false);
                } else {
                    // Safe block
                    window.gambleAPI.playSound('gem_collect', 0.4);
                    blockElement.classList.add('safe');
                    blockElement.textContent = '💎';
                    this.currentLevel++;
                    
                    if (this.currentLevel >= 10) {
                        // Reached the top!
                        window.gambleAPI.playSound('jackpot', 0.7);
                        this.showMessage(`🎉 You reached the top! Won $${this.gameState.winnings}!`, 'success');
                        this.endGame(true);
                    } else {
                        this.enableLevel(this.currentLevel);
                        this.updateGameDisplay();
                        this.showMessage(`✅ Safe! Level ${this.currentLevel + 1}`, 'success');
                    }
                }
            } else {
                this.showMessage(data.error, 'error');
                blockElement.classList.remove('selected');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
            blockElement.classList.remove('selected');
        }
    }

    async cashout() {
        if (!this.isPlaying || this.currentLevel === 0) {
            this.showMessage('Complete at least one level to cash out!', 'error');
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
                    game_type: 'tower',
                    bet_amount: this.currentBet,
                    game_data: {
                        action: 'cashout',
                        game_state: this.gameState
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                window.gambleAPI.playSound('cashout', 0.6);
                this.balanceSpan.textContent = data.new_balance;
                this.showMessage(`💰 Cashed out at level ${this.currentLevel}! Won $${data.result.winnings}!`, 'success');
                this.endGame(true);
            } else {
                this.showMessage(data.error, 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        }
    }

    enableLevel(level) {
        // Disable all levels
        document.querySelectorAll('.tower-block').forEach(block => {
            block.classList.remove('active');
        });

        // Enable current level
        document.querySelectorAll(`[data-level="${level}"]`).forEach(block => {
            if (!block.classList.contains('selected')) {
                block.classList.add('active');
            }
        });
    }

    updateGameDisplay() {
        if (!this.gameState) return;

        this.currentLevel.textContent = this.currentLevel + 1;
        this.currentMultiplier.textContent = `${this.gameState.multiplier.toFixed(2)}x`;
        this.potentialWin.textContent = `$${(this.currentBet * this.gameState.multiplier).toFixed(2)}`;
    }

    updateMultiplierDisplay() {
        const multiplier = this.getMultiplier(0);
        this.currentMultiplier.textContent = `${multiplier.toFixed(2)}x`;
    }

    revealMines() {
        if (this.gameState && this.gameState.mine_positions) {
            this.gameState.mine_positions.forEach(pos => {
                const block = document.querySelector(`[data-level="${pos.level}"][data-block="${pos.block}"]`);
                if (block && !block.classList.contains('selected')) {
                    block.classList.add('mine');
                    block.textContent = '💣';
                }
            });
        }
    }

    endGame(won) {
        this.isPlaying = false;
        this.disableAllBlocks();
        this.startBtn.disabled = false;
        this.cashoutBtn.disabled = true;

        setTimeout(() => {
            this.resetGame();
        }, 3000);
    }

    disableAllBlocks() {
        document.querySelectorAll('.tower-block').forEach(block => {
            block.classList.remove('active');
        });
    }

    resetGame() {
        this.gameState = null;
        this.currentBet = 0;
        this.currentLevel = 0;
        this.createTower();
        this.currentLevel.textContent = '1';
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
document.addEventListener('DOMContentLoaded', () => {
    new TowerGame();
});