// Crash Game JavaScript

class CrashGame {
    constructor() {
        this.isGameActive = false;
        this.currentMultiplier = 1.00;
        this.crashPoint = 0;
        this.gameStartTime = 0;
        this.animationId = null;
        this.hasBet = false;
        this.betAmount = 0;
        this.autoCashout = 0;
        this.cashedOut = false;
        
        this.canvas = document.getElementById('crashGraph');
        this.ctx = this.canvas.getContext('2d');
        
        this.initializeGraph();
        this.startNewRound();
    }
    
    initializeGraph() {
        // Set up canvas
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        
        // Draw initial graph
        this.drawGraph();
    }
    
    drawGraph() {
        const width = this.canvas.width / window.devicePixelRatio;
        const height = this.canvas.height / window.devicePixelRatio;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);
        
        // Draw background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.ctx.fillRect(0, 0, width, height);
        
        // Draw grid
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.lineWidth = 1;
        
        // Vertical lines
        for (let i = 0; i <= 10; i++) {
            const x = (width / 10) * i;
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, height);
            this.ctx.stroke();
        }
        
        // Horizontal lines
        for (let i = 0; i <= 5; i++) {
            const y = (height / 5) * i;
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(width, y);
            this.ctx.stroke();
        }
        
        // Draw multiplier curve if game is active
        if (this.isGameActive) {
            this.drawMultiplierCurve();
        }
    }
    
    drawMultiplierCurve() {
        const width = this.canvas.width / window.devicePixelRatio;
        const height = this.canvas.height / window.devicePixelRatio;
        
        const timeElapsed = (Date.now() - this.gameStartTime) / 1000;
        const maxTime = 30; // 30 seconds max display
        const maxMultiplier = 10; // 10x max display
        
        // Draw curve
        this.ctx.strokeStyle = this.cashedOut ? '#10b981' : '#ffd700';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        
        for (let t = 0; t <= timeElapsed; t += 0.1) {
            const x = (t / maxTime) * width;
            const multiplier = Math.min(1 + (t * 0.1), this.currentMultiplier);
            const y = height - ((multiplier - 1) / (maxMultiplier - 1)) * height;
            
            if (t === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }
        
        this.ctx.stroke();
        
        // Draw crash point if crashed
        if (!this.isGameActive && this.crashPoint > 0) {
            const crashTime = Math.log(this.crashPoint) / Math.log(1.1);
            const x = (crashTime / maxTime) * width;
            const y = height - ((this.crashPoint - 1) / (maxMultiplier - 1)) * height;
            
            // Draw crash explosion
            this.ctx.fillStyle = '#ef4444';
            this.ctx.beginPath();
            this.ctx.arc(x, y, 8, 0, 2 * Math.PI);
            this.ctx.fill();
            
            // Draw crash text
            this.ctx.fillStyle = '#ef4444';
            this.ctx.font = 'bold 14px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('CRASH!', x, y - 15);
        }
    }
    
    startNewRound() {
        // Reset game state
        this.isGameActive = false;
        this.currentMultiplier = 1.00;
        this.crashPoint = this.generateCrashPoint();
        this.cashedOut = false;
        this.hasBet = false;
        
        // Update UI
        document.getElementById('multiplier').textContent = '1.00x';
        document.getElementById('crash-status').textContent = 'Place your bets!';
        document.getElementById('crash-status').className = 'crash-status waiting';
        document.getElementById('placeBetBtn').classList.remove('hidden');
        document.getElementById('cashoutBtn').classList.add('hidden');
        document.getElementById('gameResult').classList.add('hidden');
        
        // Clear graph
        this.drawGraph();
        
        // Start countdown
        this.startCountdown();
    }
    
    startCountdown() {
        let countdown = 5;
        const countdownInterval = setInterval(() => {
            document.getElementById('crash-status').textContent = `Starting in ${countdown}s...`;
            countdown--;
            
            if (countdown < 0) {
                clearInterval(countdownInterval);
                this.startGame();
            }
        }, 1000);
    }
    
    startGame() {
        this.isGameActive = true;
        this.gameStartTime = Date.now();
        
        // Update UI
        document.getElementById('crash-status').textContent = 'Game in progress...';
        document.getElementById('crash-status').className = 'crash-status rising';
        document.getElementById('placeBetBtn').classList.add('hidden');
        
        if (this.hasBet) {
            document.getElementById('cashoutBtn').classList.remove('hidden');
            document.getElementById('cashoutBtn').classList.add('cashout-available');
        }
        
        // Start multiplier animation
        this.animateMultiplier();
    }
    
    animateMultiplier() {
        if (!this.isGameActive) return;
        
        const timeElapsed = (Date.now() - this.gameStartTime) / 1000;
        this.currentMultiplier = 1 + (timeElapsed * 0.1);
        
        // Update multiplier display
        const multiplierElement = document.getElementById('multiplier');
        multiplierElement.textContent = `${this.currentMultiplier.toFixed(2)}x`;
        multiplierElement.classList.add('rising');
        
        setTimeout(() => {
            multiplierElement.classList.remove('rising');
        }, 100);
        
        // Check for crash
        if (this.currentMultiplier >= this.crashPoint) {
            this.crashGame();
            return;
        }
        
        // Check for auto cashout
        if (this.hasBet && !this.cashedOut && this.autoCashout > 0 && this.currentMultiplier >= this.autoCashout) {
            this.cashOut(true);
            return;
        }
        
        // Update graph
        this.drawGraph();
        
        // Continue animation
        this.animationId = requestAnimationFrame(() => this.animateMultiplier());
    }
    
    crashGame() {
        this.isGameActive = false;
        
        // Play crash sound
        window.gambleAPI.playSound('crash', 0.6);
        
        // Update UI
        const multiplierElement = document.getElementById('multiplier');
        multiplierElement.textContent = `${this.crashPoint.toFixed(2)}x`;
        multiplierElement.classList.add('crashed');
        
        document.getElementById('crash-status').textContent = 'CRASHED!';
        document.getElementById('crash-status').className = 'crash-status crashed';
        document.getElementById('cashoutBtn').classList.add('hidden');
        document.getElementById('cashoutBtn').classList.remove('cashout-available');
        
        // Show result if user had a bet
        if (this.hasBet && !this.cashedOut) {
            this.showResult(false, 0, `Crashed at ${this.crashPoint.toFixed(2)}x`);
        }
        
        // Draw final graph
        this.drawGraph();
        
        // Start new round after delay
        setTimeout(() => {
            this.startNewRound();
        }, 5000);
    }
    
    generateCrashPoint() {
        // Generate crash point with house edge
        const r = Math.random();
        if (r < 0.01) {
            return 1.0 + Math.random() * 0.1;
        } else if (r < 0.05) {
            return 1.1 + Math.random() * 0.4;
        } else {
            return 0.9 / Math.pow(Math.random(), 0.7);
        }
    }
    
    showResult(won, amount, message) {
        const resultDiv = document.getElementById('gameResult');
        const messageDiv = document.getElementById('resultMessage');
        const amountDiv = document.getElementById('resultAmount');
        
        messageDiv.textContent = message;
        amountDiv.textContent = won ? `+${window.gambleAPI.formatMoney(amount)}` : `-${window.gambleAPI.formatMoney(this.betAmount)}`;
        
        resultDiv.className = `result-display ${won ? 'result-win' : 'result-loss'}`;
        resultDiv.classList.remove('hidden');
        
        // Vibrate on result
        window.gambleAPI.vibrate(won ? [100, 50, 100] : [200]);
        
        // Play sound
        window.gambleAPI.playSound(won ? 'win' : 'lose');
    }
}

// Game instance
let crashGame;

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    crashGame = new CrashGame();
});

// Game functions
async function placeBet() {
    const betAmountInput = document.getElementById('betAmount');
    const autoCashoutInput = document.getElementById('autoCashout');
    
    const betAmount = parseFloat(betAmountInput.value);
    const autoCashout = parseFloat(autoCashoutInput.value);
    
    if (isNaN(betAmount) || betAmount <= 0) {
        window.gambleAPI.showError('Please enter a valid bet amount');
        return;
    }
    
    if (betAmount > window.userData.balance) {
        window.gambleAPI.showError('Insufficient balance');
        return;
    }
    
    if (isNaN(autoCashout) || autoCashout < 1.01) {
        window.gambleAPI.showError('Auto cashout must be at least 1.01x');
        return;
    }
    
    // Disable bet button
    const placeBetBtn = document.getElementById('placeBetBtn');
    showLoading(placeBetBtn);
    
    try {
        // Place bet through API
        const result = await window.gambleAPI.placeBet('crash', betAmount, {
            target_multiplier: autoCashout
        });
        
        if (result) {
            crashGame.hasBet = true;
            crashGame.betAmount = betAmount;
            crashGame.autoCashout = autoCashout;
            
            // Show auto cashout indicator
            showAutoCashoutIndicator(autoCashout);
            
            window.gambleAPI.showSuccess(`Bet placed: ${window.gambleAPI.formatMoney(betAmount)}`);
        }
    } catch (error) {
        window.gambleAPI.showError('Failed to place bet');
    } finally {
        hideLoading(placeBetBtn, '💰 Place Bet');
    }
}

async function cashOut(isAuto = false) {
    if (!crashGame.hasBet || crashGame.cashedOut || !crashGame.isGameActive) {
        return;
    }
    
    crashGame.cashedOut = true;
    const winnings = crashGame.betAmount * crashGame.currentMultiplier;
    
    // Update balance locally
    window.userData.balance += winnings;
    window.gambleAPI.updateBalanceDisplay(window.userData.balance);
    
    // Hide cashout button
    document.getElementById('cashoutBtn').classList.add('hidden');
    document.getElementById('cashoutBtn').classList.remove('cashout-available');
    
    // Show result
    crashGame.showResult(true, winnings, 
        `${isAuto ? 'Auto-' : ''}Cashed out at ${crashGame.currentMultiplier.toFixed(2)}x`);
    
    window.gambleAPI.showSuccess(`Cashed out: ${window.gambleAPI.formatMoney(winnings)}`);
}

function setBetAmount(amount) {
    document.getElementById('betAmount').value = amount.toFixed(2);
    window.gambleAPI.vibrate([50]);
}

function showAutoCashoutIndicator(multiplier) {
    const indicator = document.createElement('div');
    indicator.className = 'auto-cashout-indicator';
    indicator.textContent = `Auto cashout set at ${multiplier.toFixed(2)}x`;
    
    const controls = document.querySelector('.betting-controls');
    controls.appendChild(indicator);
    
    // Remove after game ends
    setTimeout(() => {
        if (indicator.parentNode) {
            indicator.remove();
        }
    }, 30000);
}

// Initialize game
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    document.getElementById('betAmount').addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        if (value > window.userData.balance) {
            e.target.style.borderColor = '#ef4444';
        } else {
            e.target.style.borderColor = 'rgba(255, 255, 255, 0.2)';
        }
    });
    
    // Auto-focus on bet amount input
    document.getElementById('betAmount').focus();
});