#!/bin/bash

# ExoWin Bot Startup Script
echo "🚀 Starting ExoWin Bot..."

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Start the bot
echo "🤖 Launching ExoWin Bot..."
python main.py

