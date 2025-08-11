// Wheel Game JavaScript
class WheelGame {
    constructor() {
        this.isSpinning = false;
        this.currentBet = 0;
        this.risk = 'medium';
        this.initializeElements();
        this.bindEvents();
        this.createWheel();
    }

    initializeElements() {
        this.spinBtn = document.getElementById('spin-btn');
        this.betAmountInput = document.getElementById('bet-amount');
        this.riskSelect = document.getElementById('risk-level');
        this.wheelContainer = document.getElementById('wheel-container');
        this.gameStatus = document.getElementById('game-status');
        this.balanceSpan = document.getElementById('balance');
        this.multiplierDisplay = document.getElementById('multiplier-display');
    }

    bindEvents() {
        this.spinBtn.addEventListener('click', () => this.spin());
        this.riskSelect.addEventListener('change', () => {
            this.risk = this.riskSelect.value;
            this.createWheel();
        });
    }

    createWheel() {
        this.wheelContainer.innerHTML = '';
        
        const wheel = document.createElement('div');
        wheel.className = 'wheel';
        wheel.id = 'wheel';

        const segments = this.getSegments();
        const segmentAngle = 360 / segments.length;

        segments.forEach((segment, index) => {
            const segmentDiv = document.createElement('div');
            segmentDiv.className = 'wheel-segment';
            segmentDiv.style.transform = `rotate(${index * segmentAngle}deg)`;
            segmentDiv.style.transformOrigin = '50% 100%';
            segmentDiv.dataset.multiplier = segment.multiplier;
            segmentDiv.textContent = `${segment.multiplier}x`;
            
            // Color coding
            if (segment.multiplier >= 10) segmentDiv.classList.add('high');
            else if (segment.multiplier >= 2) segmentDiv.classList.add('medium');
            else segmentDiv.classList.add('low');
            
            wheel.appendChild(segmentDiv);
        });

        const pointer = document.createElement('div');
        pointer.className = 'wheel-pointer';
        pointer.textContent = '▼';

        this.wheelContainer.appendChild(wheel);
        this.wheelContainer.appendChild(pointer);

        // Update multiplier display
        this.updateMultiplierDisplay();
    }

    getSegments() {
        const segmentSets = {
            low: [
                { multiplier: 1.2 }, { multiplier: 1.5 }, { multiplier: 2 }, { multiplier: 1.2 },
                { multiplier: 1.5 }, { multiplier: 3 }, { multiplier: 1.2 }, { multiplier: 1.5 },
                { multiplier: 2 }, { multiplier: 1.2 }, { multiplier: 1.5 }, { multiplier: 5 }
            ],
            medium: [
                { multiplier: 0.5 }, { multiplier: 1 }, { multiplier: 2 }, { multiplier: 0.5 },
                { multiplier: 1.5 }, { multiplier: 3 }, { multiplier: 0.5 }, { multiplier: 2 },
                { multiplier: 5 }, { multiplier: 0.5 }, { multiplier: 1 }, { multiplier: 10 }
            ],
            high: [
                { multiplier: 0.2 }, { multiplier: 0.5 }, { multiplier: 1 }, { multiplier: 2 },
                { multiplier: 0.2 }, { multiplier: 1.5 }, { multiplier: 5 }, { multiplier: 0.2 },
                { multiplier: 3 }, { multiplier: 10 }, { multiplier: 0.2 }, { multiplier: 20 }
            ]
        };
        
        return segmentSets[this.risk] || segmentSets.medium;
    }

    async spin() {
        const betAmount = parseFloat(this.betAmountInput.value);
        
        if (!betAmount || betAmount <= 0) {
            this.showMessage('Please enter a valid bet amount', 'error');
            return;
        }

        if (this.isSpinning) {
            this.showMessage('Wheel is already spinning!', 'error');
            return;
        }

        this.currentBet = betAmount;
        this.isSpinning = true;
        this.spinBtn.disabled = true;

        // Play wheel spin sound
        window.gambleAPI.playSound('wheel_spin', 0.5);

        // Animate wheel spinning
        const wheel = document.getElementById('wheel');
        const spins = 5 + Math.random() * 5; // 5-10 full rotations
        const finalAngle = Math.random() * 360;
        const totalRotation = spins * 360 + finalAngle;

        wheel.style.transition = 'transform 4s cubic-bezier(0.25, 0.1, 0.25, 1)';
        wheel.style.transform = `rotate(${totalRotation}deg)`;

        this.showMessage('🎡 Spinning the wheel...', 'info');

        try {
            const response = await fetch('/api/game/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    game_type: 'wheel',
                    bet_amount: betAmount,
                    game_data: {
                        risk: this.risk
                    }
                })
            });

            const data = await response.json();

            setTimeout(() => {
                if (data.success) {
                    this.handleSpinResult(data.result);
                    this.balanceSpan.textContent = data.new_balance;
                } else {
                    this.showMessage(data.error, 'error');
                }
                
                this.resetSpin();
            }, 4000);

        } catch (error) {
            setTimeout(() => {
                this.showMessage('Network error. Please try again.', 'error');
                this.resetSpin();
            }, 4000);
        }
    }

    handleSpinResult(result) {
        const multiplier = result.multiplier;
        const winnings = result.winnings;

        // Highlight winning segment
        const segments = document.querySelectorAll('.wheel-segment');
        segments.forEach(segment => {
            if (parseFloat(segment.dataset.multiplier) === multiplier) {
                segment.classList.add('winning-segment');
                setTimeout(() => segment.classList.remove('winning-segment'), 3000);
            }
        });

        if (winnings > 0) {
            // Check for high multiplier jackpot
            if (multiplier >= 10) {
                window.gambleAPI.playSound('jackpot', 0.7);
            } else {
                window.gambleAPI.playSound('win', 0.5);
            }
            this.showMessage(`🎉 Landed on ${multiplier}x! Won $${winnings}!`, 'success');
        } else {
            window.gambleAPI.playSound('lose', 0.5);
            this.showMessage(`💸 Landed on ${multiplier}x. Lost $${this.currentBet}`, 'error');
        }
    }

    updateMultiplierDisplay() {
        const segments = this.getSegments();
        const maxMultiplier = Math.max(...segments.map(s => s.multiplier));
        this.multiplierDisplay.textContent = `Max: ${maxMultiplier}x`;
    }

    resetSpin() {
        this.isSpinning = false;
        this.spinBtn.disabled = false;

        // Reset wheel position
        const wheel = document.getElementById('wheel');
        setTimeout(() => {
            wheel.style.transition = 'none';
            wheel.style.transform = 'rotate(0deg)';
        }, 1000);
    }

    showMessage(message, type) {
        this.gameStatus.textContent = message;
        this.gameStatus.className = `game-status ${type}`;
        this.gameStatus.style.display = 'block';
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new WheelGame();
});