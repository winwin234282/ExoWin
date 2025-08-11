// Coinflip Game JavaScript

class CoinflipGame {
    constructor() {
        this.selectedChoice = null;
        this.isFlipping = false;
        this.gameStats = {
            totalFlips: 0,
            headsWins: 0,
            tailsWins: 0
        };
        
        this.loadStats();
        this.updateStatsDisplay();
    }
    
    loadStats() {
        // Load stats from localStorage
        const saved = localStorage.getItem('coinflip_stats');
        if (saved) {
            this.gameStats = JSON.parse(saved);
        }
    }
    
    saveStats() {
        localStorage.setItem('coinflip_stats', JSON.stringify(this.gameStats));
    }
    
    updateStatsDisplay() {
        document.getElementById('totalFlips').textContent = this.gameStats.totalFlips;
        document.getElementById('headsWins').textContent = this.gameStats.headsWins;
        document.getElementById('tailsWins').textContent = this.gameStats.tailsWins;
    }
}

// Game instance
let coinflipGame;

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    coinflipGame = new CoinflipGame();
    updateProbabilityDisplay();
});

function selectChoice(choice) {
    if (coinflipGame.isFlipping) return;
    
    // Play click sound
    window.gambleAPI.playSound('click', 0.3);
    
    coinflipGame.selectedChoice = choice;
    
    // Update button states
    const headsBtn = document.getElementById('headsBtn');
    const tailsBtn = document.getElementById('tailsBtn');
    const flipBtn = document.getElementById('flipBtn');
    const choiceValue = document.getElementById('choiceValue');
    
    // Reset button styles
    headsBtn.className = 'btn choice-btn';
    tailsBtn.className = 'btn choice-btn';
    
    // Highlight selected choice
    if (choice === 'heads') {
        headsBtn.classList.add('heads-selected');
        choiceValue.textContent = 'HEADS';
        choiceValue.style.color = '#ffd700';
    } else {
        tailsBtn.classList.add('tails-selected');
        choiceValue.textContent = 'TAILS';
        choiceValue.style.color = '#c0c0c0';
    }
    
    // Enable flip button
    flipBtn.disabled = false;
    flipBtn.classList.add('glow');
    
    // Vibrate
    window.gambleAPI.vibrate([50]);
}

async function flipCoin() {
    if (coinflipGame.isFlipping || !coinflipGame.selectedChoice) return;
    
    const betAmountInput = document.getElementById('betAmount');
    const betAmount = parseFloat(betAmountInput.value);
    
    if (isNaN(betAmount) || betAmount <= 0) {
        window.gambleAPI.showError('Please enter a valid bet amount');
        return;
    }
    
    if (betAmount > window.userData.balance) {
        window.gambleAPI.showError('Insufficient balance');
        return;
    }
    
    coinflipGame.isFlipping = true;
    
    // Disable controls
    const flipBtn = document.getElementById('flipBtn');
    const headsBtn = document.getElementById('headsBtn');
    const tailsBtn = document.getElementById('tailsBtn');
    
    flipBtn.disabled = true;
    headsBtn.disabled = true;
    tailsBtn.disabled = true;
    flipBtn.classList.remove('glow');
    
    showLoading(flipBtn);
    
    try {
        // Play flip sound
        window.gambleAPI.playSound('flip', 0.4);
        
        // Start coin flip animation
        const coin = document.getElementById('coin');
        coin.classList.add('flipping');
        
        // Place bet through API
        const result = await window.gambleAPI.placeBet('coinflip', betAmount, {
            choice: coinflipGame.selectedChoice
        });
        
        if (result) {
            // Wait for animation to complete
            setTimeout(() => {
                coin.classList.remove('flipping');
                
                // Show result
                if (result.result === 'heads') {
                    coin.classList.add('heads-result');
                    coin.classList.remove('tails-result');
                } else {
                    coin.classList.add('tails-result');
                    coin.classList.remove('heads-result');
                }
                
                // Update stats
                coinflipGame.gameStats.totalFlips++;
                if (result.outcome === 'win') {
                    if (result.result === 'heads') {
                        coinflipGame.gameStats.headsWins++;
                    } else {
                        coinflipGame.gameStats.tailsWins++;
                    }
                }
                
                coinflipGame.saveStats();
                coinflipGame.updateStatsDisplay();
                
                // Show result
                showResult(result);
                
                // Add win/loss animation to coin
                if (result.outcome === 'win') {
                    coin.classList.add('coin-win');
                    setTimeout(() => coin.classList.remove('coin-win'), 1000);
                } else {
                    coin.classList.add('coin-lose');
                    setTimeout(() => coin.classList.remove('coin-lose'), 1000);
                }
                
            }, 2000); // Wait for flip animation
        }
    } catch (error) {
        window.gambleAPI.showError('Failed to flip coin');
        coin.classList.remove('flipping');
    } finally {
        setTimeout(() => {
            coinflipGame.isFlipping = false;
            hideLoading(flipBtn, '🎯 Flip Coin');
            headsBtn.disabled = false;
            tailsBtn.disabled = false;
        }, 2000);
    }
}

function showResult(result) {
    const resultDiv = document.getElementById('gameResult');
    const messageDiv = document.getElementById('resultMessage');
    const amountDiv = document.getElementById('resultAmount');
    
    const won = result.outcome === 'win';
    const message = won ? 
        `🎉 You won! The coin landed on ${result.result.toUpperCase()}!` :
        `😢 You lost! The coin landed on ${result.result.toUpperCase()}.`;
    
    messageDiv.textContent = message;
    amountDiv.textContent = won ? 
        `+${window.gambleAPI.formatMoney(result.winnings)}` : 
        `-${window.gambleAPI.formatMoney(parseFloat(document.getElementById('betAmount').value))}`;
    
    resultDiv.className = `result-display ${won ? 'result-win' : 'result-loss'}`;
    resultDiv.classList.remove('hidden');
    
    // Vibrate based on result
    window.gambleAPI.vibrate(won ? [100, 50, 100] : [200]);
    
    // Play sound
    window.gambleAPI.playSound(won ? 'win' : 'lose');
    
    // Show notification
    if (won) {
        window.gambleAPI.showSuccess(`Won ${window.gambleAPI.formatMoney(result.winnings)}!`);
    } else {
        window.gambleAPI.showError('Better luck next time!');
    }
}

function setBetAmount(amount) {
    document.getElementById('betAmount').value = amount.toFixed(2);
    window.gambleAPI.vibrate([50]);
}

function playAgain() {
    // Reset game state
    document.getElementById('gameResult').classList.add('hidden');
    document.getElementById('flipBtn').disabled = coinflipGame.selectedChoice === null;
    
    // Reset coin position
    const coin = document.getElementById('coin');
    coin.className = 'coin';
    
    window.gambleAPI.vibrate([50]);
}

function updateProbabilityDisplay() {
    // Add probability display
    const probabilityDiv = document.createElement('div');
    probabilityDiv.className = 'probability-display';
    probabilityDiv.innerHTML = `
        <div class="probability-text">Win Probability</div>
        <div class="probability-value">50.0%</div>
        <div class="probability-text">Payout: 2.00x</div>
    `;
    
    const bettingControls = document.querySelector('.betting-controls');
    bettingControls.appendChild(probabilityDiv);
}

// Add event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Bet amount validation
    document.getElementById('betAmount').addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        if (value > window.userData.balance) {
            e.target.style.borderColor = '#ef4444';
        } else {
            e.target.style.borderColor = 'rgba(255, 255, 255, 0.2)';
        }
    });
    
    // Coin click to flip (if choice is selected)
    document.getElementById('coin').addEventListener('click', () => {
        if (coinflipGame.selectedChoice && !coinflipGame.isFlipping) {
            flipCoin();
        }
    });
});