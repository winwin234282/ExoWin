// Base JavaScript for Gamble Bot Web Apps

class GambleBotAPI {
    constructor() {
        this.baseUrl = window.location.origin;
        this.userId = window.userData?.user_id;
    }

    async getUserData() {
        try {
            const response = await fetch(`${this.baseUrl}/api/user/${this.userId}`);
            const data = await response.json();
            
            if (data.success) {
                window.userData = data.user;
                this.updateBalanceDisplay(data.user.balance);
                return data.user;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error fetching user data:', error);
            this.showError('Failed to load user data');
            return null;
        }
    }

    async placeBet(gameType, betAmount, gameData = {}) {
        try {
            const response = await fetch(`${this.baseUrl}/api/game/bet`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    game_type: gameType,
                    bet_amount: betAmount,
                    game_data: gameData
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateBalanceDisplay(data.new_balance);
                window.userData.balance = data.new_balance;
                return data.result;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error placing bet:', error);
            this.showError(error.message || 'Failed to place bet');
            return null;
        }
    }

    updateBalanceDisplay(balance) {
        const balanceElement = document.getElementById('balance');
        if (balanceElement) {
            balanceElement.textContent = balance.toFixed(2);
            
            // Add animation
            balanceElement.style.transform = 'scale(1.1)';
            setTimeout(() => {
                balanceElement.style.transform = 'scale(1)';
            }, 200);
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '12px 20px',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '600',
            zIndex: '1000',
            maxWidth: '90%',
            textAlign: 'center'
        });
        
        // Set background color based on type
        switch (type) {
            case 'success':
                notification.style.background = 'linear-gradient(45deg, #10b981, #059669)';
                break;
            case 'error':
                notification.style.background = 'linear-gradient(45deg, #ef4444, #dc2626)';
                break;
            default:
                notification.style.background = 'linear-gradient(45deg, #3b82f6, #1d4ed8)';
        }
        
        // Add to page
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    formatMoney(amount) {
        return `$${amount.toFixed(2)}`;
    }

    vibrate(pattern = [100]) {
        if (window.Telegram?.WebApp?.HapticFeedback) {
            window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
        } else if (navigator.vibrate) {
            navigator.vibrate(pattern);
        }
    }

    playSound(soundName, volume = 0.3) {
        // Play sound effects if enabled
        if (window.userData?.sound_effects !== false) {
            try {
                const audio = new Audio(`/static/sounds/${soundName}.mp3`);
                audio.volume = Math.max(0, Math.min(1, volume)); // Clamp volume between 0-1
                audio.play().catch(() => {
                    // Ignore audio play errors (user interaction required)
                });
            } catch (error) {
                // Ignore audio errors
            }
        }
    }

    // Play multiple sounds in sequence
    playSoundSequence(sounds, delay = 100) {
        if (window.userData?.sound_effects === false) return;
        
        sounds.forEach((sound, index) => {
            setTimeout(() => {
                if (typeof sound === 'string') {
                    this.playSound(sound);
                } else {
                    this.playSound(sound.name, sound.volume || 0.3);
                }
            }, index * delay);
        });
    }

    // Available sound effects
    get sounds() {
        return {
            // Basic outcomes
            win: 'win',
            lose: 'lose',
            jackpot: 'jackpot',
            
            // Game actions
            spin: 'spin',
            click: 'click',
            cardDeal: 'card_deal',
            diceRoll: 'dice_roll',
            explosion: 'explosion',
            safeClick: 'safe_click',
            crash: 'crash',
            tension: 'tension',
            blackjack: 'blackjack',
            bust: 'bust',
            plinkoDrops: 'plinko_drop',
            pegHit: 'peg_hit',
            notification: 'notification',
            flip: 'flip',
            roll: 'roll',
            wheelSpin: 'wheel_spin',
            ballDrop: 'ball_drop',
            climb: 'climb',
            fall: 'fall'
        };
    }
}

// Initialize API
window.gambleAPI = new GambleBotAPI();

// Utility functions
function showLoading(element) {
    if (element) {
        element.innerHTML = '<div class="spinner"></div>';
        element.disabled = true;
    }
}

function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

function animateElement(element, animationClass) {
    element.classList.add(animationClass);
    setTimeout(() => {
        element.classList.remove(animationClass);
    }, 1000);
}

// Auto-refresh balance every 30 seconds
setInterval(async () => {
    await window.gambleAPI.getUserData();
}, 30000);

// Handle Telegram Web App events
if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.onEvent('mainButtonClicked', () => {
        // Handle main button click
        console.log('Main button clicked');
    });
    
    window.Telegram.WebApp.onEvent('backButtonClicked', () => {
        // Handle back button click
        window.history.back();
    });
}

// Prevent zoom on double tap
let lastTouchEnd = 0;
document.addEventListener('touchend', function (event) {
    const now = (new Date()).getTime();
    if (now - lastTouchEnd <= 300) {
        event.preventDefault();
    }
    lastTouchEnd = now;
}, false);

// Add CSS for notifications
const notificationCSS = `
.notification {
    animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateX(-50%) translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
    }
}
`;

const style = document.createElement('style');
style.textContent = notificationCSS;
document.head.appendChild(style);

// Helper functions for game templates
function getUserId() {
    return window.userData?.user_id || window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
}

function showMessage(message, type = 'info') {
    window.gambleAPI.showNotification(message, type);
}

function updateBalance(newBalance) {
    window.gambleAPI.updateBalanceDisplay(newBalance);
}