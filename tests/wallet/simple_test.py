#!/usr/bin/env python3
"""
Simple test for NOWPayments API without bot dependencies
"""

import asyncio
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test_nowpayments_basic():
    """Basic test of NOWPayments API"""
    print("🧪 Testing NOWPayments API...")
    print("=" * 50)
    
    # Check if API key is configured
    api_key = os.getenv("NOWPAYMENTS_API_KEY")
    if not api_key or api_key == "your_nowpayments_api_key_here":
        print("❌ NOWPAYMENTS_API_KEY not configured!")
        print("Please set your NOWPayments API key in the .env file")
        return False
    
    print(f"✅ API Key configured: {api_key[:8]}...")
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    base_url = "https://api.nowpayments.io/v1"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test API status
            print("\n📡 Testing API Status...")
            async with session.get(f"{base_url}/status", headers=headers) as response:
                if response.status == 200:
                    status_data = await response.json()
                    print(f"✅ API Status: {status_data}")
                else:
                    print(f"❌ API Status failed: {response.status}")
                    return False
            
            # Test available currencies
            print("\n💰 Testing Available Currencies...")
            async with session.get(f"{base_url}/currencies", headers=headers) as response:
                if response.status == 200:
                    currencies_data = await response.json()
                    currencies = currencies_data.get("currencies", [])
                    print(f"✅ Available currencies: {len(currencies)} found")
                    
                    # Check for common cryptocurrencies
                    common_cryptos = ["BTC", "ETH", "USDT", "USDC", "LTC", "SOL"]
                    available_common = [c for c in common_cryptos if c in currencies]
                    print(f"✅ Common cryptos available: {available_common}")
                else:
                    print(f"❌ Currencies request failed: {response.status}")
                    return False
            
            # Test exchange rate
            print("\n💱 Testing Exchange Rates...")
            async with session.get(f"{base_url}/estimate?amount=1&currency_from=BTC&currency_to=USD", headers=headers) as response:
                if response.status == 200:
                    rate_data = await response.json()
                    btc_rate = rate_data.get("estimated_amount", 0)
                    print(f"✅ BTC/USD rate: ${btc_rate}")
                else:
                    print(f"⚠️ Exchange rate request failed: {response.status}")
            
            # Test minimum payment amount
            print("\n💵 Testing Minimum Payment Amount...")
            async with session.get(f"{base_url}/min-amount?currency_from=BTC&currency_to=USD", headers=headers) as response:
                if response.status == 200:
                    min_data = await response.json()
                    min_amount = min_data.get("min_amount", 0)
                    print(f"✅ BTC minimum payment: {min_amount} BTC")
                else:
                    print(f"⚠️ Min amount request failed: {response.status}")
    
    except Exception as e:
        print(f"❌ Error during API test: {str(e)}")
        return False
    
    # Test webhook configuration
    print("\n🔗 Testing Webhook Configuration...")
    webhook_url = os.getenv("NOWPAYMENTS_IPN_URL") or os.getenv("WEBHOOK_URL")
    ipn_secret = os.getenv("NOWPAYMENTS_IPN_SECRET")
    
    if webhook_url and webhook_url != "https://your-domain.com/webhook/nowpayments":
        print(f"✅ Webhook URL configured: {webhook_url}")
    else:
        print("⚠️ Webhook URL not configured or using placeholder")
        print("Set NOWPAYMENTS_IPN_URL or WEBHOOK_URL in your .env file")
    
    if ipn_secret and ipn_secret != "your_nowpayments_ipn_secret_here":
        print(f"✅ IPN Secret configured: {ipn_secret[:8]}...")
    else:
        print("⚠️ IPN Secret not configured")
        print("Set NOWPAYMENTS_IPN_SECRET in your .env file")
    
    print("\n" + "=" * 50)
    print("✅ NOWPayments API test completed!")
    
    return True

if __name__ == "__main__":
    print("🚀 NOWPayments Simple API Test")
    print("This script will test your NOWPayments API configuration")
    print()
    
    success = asyncio.run(test_nowpayments_basic())
    
    if success:
        print("\n🎉 All tests passed!")
        print("Your NOWPayments API configuration is working correctly.")
        print("\n📋 Next Steps:")
        print("1. Configure your webhook URL for production")
        print("2. Set up your IPN secret")
        print("3. Test the complete deposit flow with your bot")
    else:
        print("\n❌ Some tests failed.")
        print("Please check your configuration and try again.")