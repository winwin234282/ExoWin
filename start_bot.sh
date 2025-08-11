#!/bin/bash

# ExoWin Bot Startup Script
echo "🚀 Starting ExoWin Bot..."

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH=/root/ExoWinBot

# Start the bot with PM2
pm2 start --name "exowin-bot" --interpreter python src/bot.py

# Start the webapp with PM2
pm2 start --name "exowin-webapp" --interpreter python webapp/app.py

# Start the webhook service with PM2
pm2 start --name "exowin-webhook" --interpreter python src/webhook.py

# Show PM2 status
pm2 list

echo "✅ ExoWin Bot started successfully!"
echo "🌐 Web App: http://192.250.226.90:12000"
echo "🔗 Webhook: http://192.250.226.90:12001"
