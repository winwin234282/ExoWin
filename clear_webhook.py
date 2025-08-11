import requests
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Delete webhook
response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
print("Delete webhook response:", response.json())

# Get webhook info
response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
print("Webhook info:", response.json())
