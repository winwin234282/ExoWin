// Roulette Game JavaScript
class RouletteGame {
    constructor() {
        this.isSpinning = false;
        this.currentBets = {};
        this.totalBet = 0;
        this.initializeElements();
        this.bindEvents();
        this.createRouletteWheel();
        this.createBettingTable();
    }

    initializeElements() {
        this.wheelContainer = document.getElementById('roulette-wheel');
        this.bettingTable = document.getElementById('betting-table');
        this.spinBtn = document.getElementById('spin-btn');
        this.clearBetsBtn = document.getElementById('clear-bets-btn');
        this.betAmountInput = document.getElementById('bet-amount');
        this.totalBetSpan = document.getElementById('total-bet');
        this.balanceSpan = document.getElementById('balance');
        this.gameStatus = document.getElementById('game-status');
        this.winningNumber = document.getElementById('winning-number');
    }

    bindEvents() {
        this.spinBtn.addEventListener('click', () => this.spin());
        this.clearBetsBtn.addEventListener('click', () => this.clearBets());
    }

    createRouletteWheel() {
        const numbers = [
            0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5,
            24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
        ];

        const wheel = document.createElement('div');
        wheel.className = 'wheel';
        wheel.id = 'wheel';

        numbers.forEach((num, index) => {
            const segment = document.createElement('div');
            segment.className = 'wheel-segment';
            segment.style.transform = `rotate(${index * (360 / numbers.length)}deg)`;
            
            if (num === 0) {
                segment.classList.add('green');
            } else if ([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36].includes(num)) {
                segment.classList.add('red');
            } else {
                segment.classList.add('black');
            }
            
            segment.textContent = num;
            wheel.appendChild(segment);
        });

        const pointer = document.createElement('div');
        pointer.className = 'wheel-pointer';
        pointer.textContent = '▼';

        this.wheelContainer.appendChild(wheel);
        this.wheelContainer.appendChild(pointer);
    }

    createBettingTable() {
        const table = document.createElement('div');
        table.className = 'betting-grid';

        // Create number grid (0-36)
        for (let i = 0; i <= 36; i++) {
            const cell = document.createElement('div');
            cell.className = 'bet-cell number-cell';
            cell.textContent = i;
            cell.dataset.bet = `number_${i}`;
            
            if (i === 0) {
                cell.classList.add('green');
            } else if ([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36].includes(i)) {
                cell.classList.add('red');
            } else {
                cell.classList.add('black');
            }
            
            cell.addEventListener('click', () => this.placeBet(`number_${i}`, 35));
            table.appendChild(cell);
        }

        // Create outside bets
        const outsideBets = [
            { name: 'Red', type: 'color_red', payout: 1 },
            { name: 'Black', type: 'color_black', payout: 1 },
            { name: 'Even', type: 'even', payout: 1 },
            { name: 'Odd', type: 'odd', payout: 1 },
            { name: '1-18', type: 'low', payout: 1 },
            { name: '19-36', type: 'high', payout: 1 },
            { name: '1st 12', type: 'dozen_1', payout: 2 },
            { name: '2nd 12', type: 'dozen_2', payout: 2 },
            { name: '3rd 12', type: 'dozen_3', payout: 2 }
        ];

        outsideBets.forEach(bet => {
            const cell = document.createElement('div');
            cell.className = 'bet-cell outside-bet';
            cell.textContent = bet.name;
            cell.dataset.bet = bet.type;
            cell.addEventListener('click', () => this.placeBet(bet.type, bet.payout));
            table.appendChild(cell);
        });

        this.bettingTable.appendChild(table);
    }

    placeBet(betType, payout) {
        if (this.isSpinning) return;

        const betAmount = parseFloat(this.betAmountInput.value);
        if (!betAmount || betAmount <= 0) {
            this.showMessage('Please enter a valid bet amount', 'error');
            return;
        }

        if (!this.currentBets[betType]) {
            this.currentBets[betType] = { amount: 0, payout: payout };
        }

        this.currentBets[betType].amount += betAmount;
        this.totalBet += betAmount;
        this.totalBetSpan.textContent = this.totalBet;

        // Visual feedback
        const cell = document.querySelector(`[data-bet="${betType}"]`);
        if (cell) {
            cell.classList.add('has-bet');
            const chip = document.createElement('div');
            chip.className = 'chip';
            chip.textContent = `$${this.currentBets[betType].amount}`;
            cell.appendChild(chip);
        }

        this.showMessage(`Bet $${betAmount} on ${betType.replace('_', ' ')}`, 'info');
    }

    clearBets() {
        this.currentBets = {};
        this.totalBet = 0;
        this.totalBetSpan.textContent = '0';

        // Remove visual chips
        document.querySelectorAll('.chip').forEach(chip => chip.remove());
        document.querySelectorAll('.has-bet').forEach(cell => cell.classList.remove('has-bet'));

        this.showMessage('All bets cleared', 'info');
    }

    async spin() {
        if (this.isSpinning || Object.keys(this.currentBets).length === 0) {
            this.showMessage('Please place at least one bet', 'error');
            return;
        }

        this.isSpinning = true;
        this.spinBtn.disabled = true;
        this.clearBetsBtn.disabled = true;

        // Play wheel spin sound
        window.gambleAPI.playSound('wheel_spin', 0.5);

        // Animate wheel spinning
        const wheel = document.getElementById('wheel');
        wheel.style.transition = 'transform 3s ease-out';
        wheel.style.transform = `rotate(${Math.random() * 360 + 1440}deg)`;

        this.showMessage('🎰 Spinning...', 'info');

        try {
            const response = await fetch('/api/game/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    game_type: 'roulette',
                    bet_amount: this.totalBet,
                    game_data: {
                        bets: this.currentBets
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
            }, 3000);

        } catch (error) {
            setTimeout(() => {
                this.showMessage('Network error. Please try again.', 'error');
                this.resetSpin();
            }, 3000);
        }
    }

    handleSpinResult(result) {
        this.winningNumber.textContent = result.winning_number;
        this.winningNumber.style.display = 'block';

        if (result.winnings > 0) {
            window.gambleAPI.playSound('win', 0.5);
            this.showMessage(`🎉 Winner! Number ${result.winning_number}! Won $${result.winnings}`, 'success');
        } else {
            window.gambleAPI.playSound('lose', 0.5);
            this.showMessage(`💸 Number ${result.winning_number}. Better luck next time!`, 'error');
        }

        // Highlight winning number
        const winningCell = document.querySelector(`[data-bet="number_${result.winning_number}"]`);
        if (winningCell) {
            winningCell.classList.add('winning-number');
            setTimeout(() => {
                winningCell.classList.remove('winning-number');
            }, 5000);
        }
    }

    resetSpin() {
        this.isSpinning = false;
        this.spinBtn.disabled = false;
        this.clearBetsBtn.disabled = false;
        this.clearBets();

        // Reset wheel animation
        const wheel = document.getElementById('wheel');
        wheel.style.transition = 'none';
        wheel.style.transform = 'rotate(0deg)';
    }

    showMessage(message, type) {
        this.gameStatus.textContent = message;
        this.gameStatus.className = `game-status ${type}`;
        this.gameStatus.style.display = 'block';
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new RouletteGame();
});