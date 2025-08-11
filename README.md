# ExoWin 👑 - Production-Grade Telegram Bot

A comprehensive, production-ready Telegram gambling bot with advanced features, secure admin controls, and cryptocurrency withdrawal capabilities.

## 🚀 Features

- **🎮 Unified Games Menu** - Access all games from a single, streamlined interface
- **👑 Advanced Admin Panel** - Complete user management and real-time analytics
- **💸 Cryptocurrency Withdrawals** - Support for multiple cryptocurrencies (BTC, ETH, LTC, DOGE, etc.)
- **📊 Real-time Analytics** - Live statistics and financial tracking
- **📢 Broadcast System** - Send messages to all users with progress tracking
- **🔒 Production Security** - Secure authentication and input validation
- **⚡ High Performance** - Optimized database queries with proper indexing

## 📁 Project Structure

```
ExoWinBot/
├── src/                    # Main source code
│   ├── admin/             # Admin panel and controls
│   ├── database/          # Database functions and models
│   ├── games/             # Game implementations
│   ├── menus/             # Bot menus and navigation
│   ├── utils/             # Utility functions
│   └── wallet/            # Withdrawal system
├── webapp/                # Web application (if needed)
├── docs/                  # Documentation
├── tests/                 # Test files
├── logs/                  # Log files (gitignored)
├── main.py               # Main bot entry point
└── requirements.txt      # Python dependencies
```

## 🛠️ Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the Bot**
   ```bash
   python main.py
   ```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Setup Guide](docs/SETUP_GUIDE.md)** - Complete installation and configuration
- **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Detailed feature overview
- **[Game Architecture](docs/GAME_ARCHITECTURE.md)** - Game system documentation
- **[Improvements Summary](docs/IMPROVEMENTS_SUMMARY.md)** - Recent enhancements

## 🧪 Testing

Run tests to verify functionality:

```bash
# Run all tests
python -m pytest tests/

# Run specific test files
python tests/test_bot_functionality.py
python tests/test_imports.py
```

## 🔧 Configuration

Key environment variables:
- `BOT_TOKEN` - Your Telegram bot token
- `MONGODB_URI` - MongoDB connection string
- `ADMIN_USER_ID` - Admin user ID for bot management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation in `docs/`
- Review test files in `tests/`
- Open an issue on GitHub

---

**ExoWin 👑** - Where gaming meets excellence!