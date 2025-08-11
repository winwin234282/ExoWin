// Plinko Game JavaScript
class PlinkoGame {
    constructor() {
        this.isPlaying = false;
        this.currentBet = 0;
        this.risk = 'medium';
        this.rows = 12;
        this.initializeElements();
        this.bindEvents();
        this.createBoard();
    }

    initializeElements() {
        this.dropBtn = document.getElementById('drop-btn');
        this.betAmountInput = document.getElementById('bet-amount');
        this.riskSelect = document.getElementById('risk-level');
        this.plinkoBoard = document.getElementById('plinko-board');
        this.gameStatus = document.getElementById('game-status');
        this.balanceSpan = document.getElementById('balance');
        this.multiplierDisplay = document.getElementById('multiplier-display');
    }

    bindEvents() {
        this.dropBtn.addEventListener('click', () => this.dropBall());
        this.riskSelect.addEventListener('change', () => {
            this.risk = this.riskSelect.value;
            this.createBoard();
        });
    }

    createBoard() {
        this.plinkoBoard.innerHTML = '';
        
        // Create pegs
        for (let row = 0; row < this.rows; row++) {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'plinko-row';
            
            for (let peg = 0; peg <= row; peg++) {
                const pegDiv = document.createElement('div');
                pegDiv.className = 'peg';
                rowDiv.appendChild(pegDiv);
            }
            
            this.plinkoBoard.appendChild(rowDiv);
        }

        // Create multiplier slots at bottom
        const slotsDiv = document.createElement('div');
        slotsDiv.className = 'multiplier-slots';
        
        const multipliers = this.getMultipliers();
        multipliers.forEach((mult, index) => {
            const slot = document.createElement('div');
            slot.className = 'multiplier-slot';
            slot.dataset.multiplier = mult;
            slot.textContent = `${mult}x`;
            
            // Color coding based on multiplier
            if (mult >= 10) slot.classList.add('high');
            else if (mult >= 3) slot.classList.add('medium');
            else slot.classList.add('low');
            
            slotsDiv.appendChild(slot);
        });
        
        this.plinkoBoard.appendChild(slotsDiv);
    }

    getMultipliers() {
        const multiplierSets = {
            low: [0.2, 0.5, 1, 1.5, 2, 3, 2, 1.5, 1, 0.5, 0.2],
            medium: [0.1, 0.3, 0.5, 1, 2, 5, 10, 5, 2, 1, 0.5, 0.3, 0.1],
            high: [0.1, 0.2, 0.3, 0.5, 1, 3, 8, 20, 8, 3, 1, 0.5, 0.3, 0.2, 0.1]
        };
        
        return multiplierSets[this.risk] || multiplierSets.medium;
    }

    async dropBall() {
        const betAmount = parseFloat(this.betAmountInput.value);
        
        if (!betAmount || betAmount <= 0) {
            this.showMessage('Please enter a valid bet amount', 'error');
            return;
        }

        if (this.isPlaying) {
            this.showMessage('Wait for current ball to finish!', 'error');
            return;
        }

        this.currentBet = betAmount;
        this.isPlaying = true;
        this.dropBtn.disabled = true;

        // Play ball drop sound
        window.gambleAPI.playSound('ball_drop', 0.4);

        // Create and animate ball
        const ball = document.createElement('div');
        ball.className = 'plinko-ball';
        ball.textContent = '🔴';
        this.plinkoBoard.appendChild(ball);

        // Animate ball falling
        this.animateBall(ball);

        try {
            const response = await fetch('/api/game/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    game_type: 'plinko',
                    bet_amount: betAmount,
                    game_data: {
                        risk: this.risk,
                        rows: this.rows
                    }
                })
            });

            const data = await response.json();

            setTimeout(() => {
                if (data.success) {
                    this.handleResult(data.result);
                    this.balanceSpan.textContent = data.new_balance;
                } else {
                    this.showMessage(data.error, 'error');
                }
                
                this.isPlaying = false;
                this.dropBtn.disabled = false;
                ball.remove();
            }, 3000);

        } catch (error) {
            setTimeout(() => {
                this.showMessage('Network error. Please try again.', 'error');
                this.isPlaying = false;
                this.dropBtn.disabled = false;
                ball.remove();
            }, 3000);
        }
    }

    animateBall(ball) {
        let currentRow = 0;
        let currentPosition = 0.5; // Start at center

        const animateStep = () => {
            if (currentRow >= this.rows) {
                // Ball reached bottom
                const finalSlot = Math.floor(currentPosition * this.getMultipliers().length);
                const slot = document.querySelectorAll('.multiplier-slot')[finalSlot];
                if (slot) {
                    slot.classList.add('ball-landed');
                    setTimeout(() => slot.classList.remove('ball-landed'), 1000);
                }
                return;
            }

            // Random bounce left or right
            const bounce = Math.random() < 0.5 ? -0.1 : 0.1;
            currentPosition = Math.max(0, Math.min(1, currentPosition + bounce));

            // Update ball position
            const rowElement = document.querySelector(`[data-level="${this.rows - 1 - currentRow}"]`);
            if (rowElement) {
                const rect = rowElement.getBoundingClientRect();
                const boardRect = this.plinkoBoard.getBoundingClientRect();
                
                ball.style.left = `${currentPosition * 100}%`;
                ball.style.top = `${((currentRow + 1) / this.rows) * 80}%`;
            }

            currentRow++;
            setTimeout(animateStep, 200);
        };

        animateStep();
    }

    handleResult(result) {
        const multiplier = result.multiplier;
        const winnings = result.winnings;

        if (winnings > 0) {
            window.gambleAPI.playSound('win', 0.5);
            this.showMessage(`🎉 Ball landed on ${multiplier}x! Won $${winnings}!`, 'success');
        } else {
            window.gambleAPI.playSound('lose', 0.5);
            this.showMessage(`💸 Ball landed on ${multiplier}x. Lost $${this.currentBet}`, 'error');
        }

        // Highlight the winning multiplier
        const slots = document.querySelectorAll('.multiplier-slot');
        slots.forEach(slot => {
            if (parseFloat(slot.dataset.multiplier) === multiplier) {
                slot.classList.add('winning-slot');
                setTimeout(() => slot.classList.remove('winning-slot'), 3000);
            }
        });
    }

    showMessage(message, type) {
        this.gameStatus.textContent = message;
        this.gameStatus.className = `game-status ${type}`;
        this.gameStatus.style.display = 'block';
    }
}

// Initialize game when page loads
let plinkoGame;
document.addEventListener('DOMContentLoaded', () => {
    plinkoGame = new PlinkoGame();
});

// Global functions for HTML onclick handlers
function dropBall() {
    if (plinkoGame) {
        plinkoGame.dropBall();
    }
}

function selectRisk(risk) {
    if (plinkoGame) {
        plinkoGame.risk = risk;
        plinkoGame.createBoard();
        
        // Update UI
        document.querySelectorAll('.risk-btn').forEach(btn => btn.classList.remove('selected'));
        document.getElementById(risk + 'Risk').classList.add('selected');
    }
}

function setBetAmount(amount) {
    const betInput = document.getElementById('betAmount');
    if (betInput) {
        betInput.value = amount.toFixed(2);
    }
}

function playAgain() {
    if (plinkoGame) {
        plinkoGame.dropBall();
    }
}