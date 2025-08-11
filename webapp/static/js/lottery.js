class LotteryGame {
    constructor() {
        this.gameState = null;
        this.userId = this.getUserId();
        this.balance = 0;
        this.selectedNumbers = [];
        this.initializeGame();
    }

    getUserId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('user_id');
    }

    async initializeGame() {
        await this.updateBalance();
        this.setupEventListeners();
        this.createNumberGrid();
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
        document.getElementById('draw-numbers').addEventListener('click', () => this.drawNumbers());
        document.getElementById('clear-selection').addEventListener('click', () => this.clearSelection());
    }

    createNumberGrid() {
        const gridDiv = document.getElementById('number-grid');
        gridDiv.innerHTML = '';
        
        for (let i = 1; i <= 49; i++) {
            const numberDiv = document.createElement('div');
            numberDiv.className = 'number-cell';
            numberDiv.textContent = i;
            numberDiv.addEventListener('click', () => this.toggleNumber(i, numberDiv));
            gridDiv.appendChild(numberDiv);
        }
    }

    toggleNumber(number, element) {
        if (this.selectedNumbers.includes(number)) {
            // Remove number
            this.selectedNumbers = this.selectedNumbers.filter(n => n !== number);
            element.classList.remove('selected');
        } else if (this.selectedNumbers.length < 6) {
            // Add number
            this.selectedNumbers.push(number);
            element.classList.add('selected');
        } else {
            alert('You can only select 6 numbers');
        }
        
        this.updateSelectedNumbers();
    }

    updateSelectedNumbers() {
        const selectedDiv = document.getElementById('selected-numbers');
        selectedDiv.textContent = `Selected: ${this.selectedNumbers.sort((a, b) => a - b).join(', ')}`;
        
        // Enable/disable draw button
        document.getElementById('draw-numbers').disabled = this.selectedNumbers.length !== 6 || !this.gameState;
    }

    clearSelection() {
        this.selectedNumbers = [];
        document.querySelectorAll('.number-cell').forEach(cell => {
            cell.classList.remove('selected');
        });
        this.updateSelectedNumbers();
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
            const response = await fetch('/api/lottery/start', {
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

    async selectNumbers() {
        if (this.selectedNumbers.length !== 6) {
            alert('Please select exactly 6 numbers');
            return;
        }

        try {
            const response = await fetch('/api/lottery/select', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    numbers: this.selectedNumbers
                })
            });

            const data = await response.json();
            if (data.success) {
                this.gameState = data.game;
                this.updateUI();
            } else {
                alert(data.error || 'Failed to select numbers');
            }
        } catch (error) {
            console.error('Error selecting numbers:', error);
            alert('Error selecting numbers');
        }
    }

    async drawNumbers() {
        if (this.selectedNumbers.length !== 6) {
            alert('Please select exactly 6 numbers first');
            return;
        }

        // First select the numbers
        await this.selectNumbers();

        try {
            const response = await fetch('/api/lottery/draw', {
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
                alert(data.error || 'Failed to draw numbers');
            }
        } catch (error) {
            console.error('Error drawing numbers:', error);
            alert('Error drawing numbers');
        }
    }

    updateUI() {
        document.getElementById('balance').textContent = `$${this.balance.toFixed(2)}`;
        
        if (this.gameState) {
            // Update selected numbers display
            if (this.gameState.selected_numbers.length > 0) {
                document.getElementById('your-numbers').textContent = 
                    `Your Numbers: ${this.gameState.selected_numbers.join(', ')}`;
            }

            // Update winning numbers if drawn
            if (this.gameState.winning_numbers.length > 0) {
                document.getElementById('winning-numbers').textContent = 
                    `Winning Numbers: ${this.gameState.winning_numbers.join(', ')}`;
                document.getElementById('bonus-number').textContent = 
                    `Bonus Number: ${this.gameState.bonus_number}`;
            }

            // Update game controls
            const gameStarted = this.gameState.selected_numbers.length > 0;
            document.getElementById('start-game').style.display = this.gameState.game_over ? 'block' : 'none';
            document.getElementById('draw-numbers').style.display = gameStarted && !this.gameState.game_over ? 'block' : 'none';
            
            this.updateSelectedNumbers();
        }
    }

    showResult() {
        if (this.gameState && this.gameState.game_over) {
            const resultDiv = document.getElementById('game-result');
            let message = '';
            
            if (this.gameState.matches > 0) {
                message = `Congratulations! You matched ${this.gameState.matches} numbers! Winnings: $${this.gameState.winnings.toFixed(2)}`;
            } else {
                message = `No matches this time. Better luck next time!`;
            }
            
            resultDiv.textContent = message;
            resultDiv.style.display = 'block';

            // Reset for new game
            this.clearSelection();
            this.gameState = null;
        }
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new LotteryGame();
});