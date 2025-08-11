# 🎮 Game Architecture Overview

## Game Categories

### 🎲 Telegram Animated Games
**Location**: `src/games/*_animated.py`  
**Purpose**: Games that use Telegram's native animations in chat  
**Features**: 
- Real-time animations visible to all chat members
- Multiplayer betting and competitions
- Instant results based on animation outcome
- Social gaming experience

**Available Games:**
1. **🎲 Dice** (`dice_animated.py`)
   - Uses Telegram's dice animation (🎲)
   - Solo mode: Guess number 1-6, win 5x
   - Multiplayer: All players bet, winner takes pot
   - Duel mode: 1v1 dice battles

2. **🎰 Slots** (`slots_animated.py`)
   - Uses Telegram's slot machine animation (🎰)
   - Solo mode: Spin for combinations
   - Tournament mode: Compete for highest multiplier
   - Jackpot: 777x multiplier possible

3. **🎯 Darts** (`darts_animated.py`)
   - Uses Telegram's darts animation (🎯)
   - Solo mode: Aim for bullseye (10x multiplier)
   - Challenge mode: 1v1 accuracy contests
   - Scoring: Miss to Bullseye (0x to 10x)

4. **🏀 Basketball** (`basketball_animated.py`)
   - Uses Telegram's basketball animation (🏀)
   - Solo mode: Shoot for perfect shot (8x multiplier)
   - Shootout mode: Compete with other players
   - Scoring: Miss to Perfect (0x to 8x)

5. **⚽ Football** (`football_animated.py`)
   - Uses Telegram's football animation (⚽)
   - Solo mode: Penalty kicks (8x for perfect goal)
   - Tournament mode: Penalty shootouts
   - Scoring: Miss to Perfect Goal (0x to 8x)

6. **🎳 Bowling** (`bowling_animated.py`)
   - Uses Telegram's bowling animation (🎳)
   - Solo mode: Roll for strikes (10x multiplier)
   - Competition mode: Bowling tournaments
   - Scoring: Gutter to Strike (0x to 10x)

### 🎮 Web App Games
**Location**: `webapp/app.py` + `webapp/templates/`  
**Purpose**: Complex interactive games with custom UI  
**Features**:
- Full visual interfaces
- Advanced game mechanics
- Strategy-based gameplay
- Real-time interactions

**Available Games:**
1. **♠️ Blackjack** - Card game with dealer
2. **🎰 Roulette** - Betting table with spinning wheel
3. **💣 Mines** - Grid-based risk/reward game
4. **🏗️ Tower** - Progressive climbing game
5. **🎡 Wheel** - Spin wheel with multiple segments
6. **🚀 Crash** - Multiplier timing game
7. **🟡 Plinko** - Ball physics simulation
8. **🪙 Coinflip** - Simple heads/tails betting

## Technical Implementation

### Telegram Animated Games
- **Animation**: Uses `reply_dice(emoji="🎲")` for native animations
- **Results**: Based on `dice_message.dice.value` from Telegram
- **Multiplayer**: Shared game state in memory (`active_*_games`)
- **Real-time**: All players see the same animation result

### Web App Games
- **Interface**: Flask web application with HTML/CSS/JS
- **API**: RESTful endpoints for game actions
- **Logic**: Server-side game processing
- **Integration**: Telegram Web App API for seamless experience

## User Experience

### Telegram Games Flow:
1. User types `/dice` or uses menu
2. Selects game mode (Solo/Multiplayer/Duel)
3. Chooses bet amount
4. **Animation plays in chat** (visible to all)
5. Results calculated from animation
6. Winnings distributed automatically

### Web App Games Flow:
1. User selects web app game from menu
2. **Mini-app opens** within Telegram
3. Interactive gameplay with visual feedback
4. Real-time balance updates
5. Results sync back to Telegram

## Multiplayer Features

### Telegram Animated Games:
- **Shared Pot**: All players contribute, winner takes all
- **Live Animation**: Everyone sees the same result
- **Social Betting**: Chat-based gaming experience
- **Instant Results**: No waiting for game completion

### Web App Games:
- **Individual Play**: Personal gaming sessions
- **Advanced UI**: Complex game interfaces
- **Strategy Focus**: Skill-based gameplay
- **Detailed Statistics**: Comprehensive game tracking

## Security & Fairness

### Telegram Games:
- **Provably Fair**: Uses Telegram's native random generation
- **Transparent**: All players see the same animation
- **No Manipulation**: Results determined by Telegram servers

### Web App Games:
- **Server-side Logic**: All calculations on secure server
- **Encrypted Communication**: HTTPS for all API calls
- **Balance Validation**: Real-time balance checking
- **Transaction Logging**: Complete audit trail

## Configuration

### Environment Variables:
- `WEBAPP_URL`: Base URL for web app games
- `BOT_TOKEN`: Telegram bot token
- `MONGODB_URI`: Database connection
- `ADMIN_USER_ID`: Admin access control

### Game Settings:
- **Multipliers**: Configurable in each game file
- **Bet Limits**: Adjustable minimum/maximum bets
- **Animation Timing**: Customizable wait times
- **Payout Rates**: Editable in game logic

## Future Enhancements

### Planned Features:
- **Live Tournaments**: Scheduled competitions
- **Leaderboards**: Top players tracking
- **Achievement System**: Unlock rewards
- **Social Features**: Friend challenges
- **Advanced Analytics**: Detailed game statistics

### Technical Improvements:
- **Redis Integration**: Better multiplayer state management
- **WebSocket Support**: Real-time web app updates
- **Mobile Optimization**: Enhanced mobile experience
- **Performance Monitoring**: Game performance tracking