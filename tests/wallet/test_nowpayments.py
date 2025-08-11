#!/usr/bin/env python3
"""
Test script for NOWPayments integration
Run this to verify your NOWPayments API setup
"""

import asyncio
import os
from dotenv import load_dotenv
from src.wallet.nowpayments import (
    get_api_status,
    nowpayments_client,
    create_deposit_payment,
    check_payment_status,
    SUPPORTED_CRYPTOS
)

load_dotenv()

async def test_nowpayments_integration():
    """Test NOWPayments API integration"""
    print("🧪 Testing NOWPayments Integration...")
    print("=" * 50)
    
    # Check if API key is configured
    api_key = os.getenv("NOWPAYMENTS_API_KEY")
    if not api_key or api_key == "your_nowpayments_api_key_here":
        print("❌ NOWPAYMENTS_API_KEY not configured!")
        print("Please set your NOWPayments API key in the .env file")
        return False
    
    print(f"✅ API Key configured: {api_key[:8]}...")
    
    # Test API status
    print("\n📡 Testing API Status...")
    status = await get_api_status()
    if status:
        print(f"✅ API Status: {status}")
    else:
        print("❌ Failed to get API status")
        return False
    
    # Test available currencies
    print("\n💰 Testing Available Currencies...")
    currencies = await nowpayments_client.get_available_currencies()
    if currencies:
        print(f"✅ Available currencies: {len(currencies)} found")
        print(f"Supported by bot: {SUPPORTED_CRYPTOS}")
        
        # Check which of our supported cryptos are available
        available_supported = [c for c in SUPPORTED_CRYPTOS if c in currencies]
        unavailable_supported = [c for c in SUPPORTED_CRYPTOS if c not in currencies]
        
        print(f"✅ Available supported cryptos: {available_supported}")
        if unavailable_supported:
            print(f"⚠️ Unavailable supported cryptos: {unavailable_supported}")
    else:
        print("❌ Failed to get available currencies")
        return False
    
    # Test exchange rate
    print("\n💱 Testing Exchange Rates...")
    btc_rate = await nowpayments_client.get_exchange_rates("BTC", "USD")
    if btc_rate:
        print(f"✅ BTC/USD rate: ${btc_rate}")
    else:
        print("⚠️ Failed to get BTC exchange rate")
    
    # Test minimum payment amount
    print("\n💵 Testing Minimum Payment Amounts...")
    btc_min = await nowpayments_client.get_min_payment_amount("BTC", "USD")
    if btc_min:
        print(f"✅ BTC minimum payment: {btc_min} BTC")
    else:
        print("⚠️ Failed to get BTC minimum payment amount")
    
    # Test payment creation (without actually creating one)
    print("\n🧾 Testing Payment Creation (dry run)...")
    print("This would create a payment for $10 USD in BTC")
    print("Skipping actual payment creation to avoid test payments")
    
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
    print("✅ NOWPayments integration test completed!")
    print("\n📋 Setup Checklist:")
    print("1. ✅ API Key configured")
    print("2. ✅ API is accessible")
    print("3. ✅ Supported cryptocurrencies available")
    print("4. ⚠️ Configure webhook URL for production" if not webhook_url or "your-domain" in webhook_url else "4. ✅ Webhook URL configured")
    print("5. ⚠️ Configure IPN secret for production" if not ipn_secret or "your_nowpayments" in ipn_secret else "5. ✅ IPN Secret configured")
    
    return True

async def test_deposit_flow():
    """Test the complete deposit flow"""
    print("\n🔄 Testing Complete Deposit Flow...")
    print("=" * 50)
    
    # Test creating a small payment
    print("Creating test payment for $10 USD in BTC...")
    
    try:
        payment = await create_deposit_payment(
            user_id=123456789,  # Test user ID
            amount_usd=10.0,
            crypto_currency="BTC"
        )
        
        if payment and "payment_id" in payment:
            payment_id = payment["payment_id"]
            pay_address = payment.get("pay_address", "N/A")
            pay_amount = payment.get("pay_amount", "N/A")
            
            print(f"✅ Payment created successfully!")
            print(f"Payment ID: {payment_id}")
            print(f"Pay Address: {pay_address}")
            print(f"Pay Amount: {pay_amount} BTC")
            
            # Test checking payment status
            print(f"\nChecking payment status...")
            status = await check_payment_status(payment_id)
            if status:
                print(f"✅ Payment status: {status.get('payment_status', 'unknown')}")
            else:
                print("⚠️ Could not check payment status")
            
            print(f"\n⚠️ Test payment created with ID: {payment_id}")
            print("This is a real payment - do not send funds to the address!")
            
        else:
            print("❌ Failed to create payment")
            if payment:
                print(f"Error: {payment}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating payment: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 NOWPayments Integration Test")
    print("This script will test your NOWPayments API configuration")
    print()
    
    # Run basic integration test
    success = asyncio.run(test_nowpayments_integration())
    
    if success:
        print("\n" + "=" * 50)
        response = input("Do you want to test payment creation? (y/N): ").lower().strip()
        if response == 'y':
            asyncio.run(test_deposit_flow())
        else:
            print("Skipping payment creation test.")
    
    print("\n🎉 Test completed!")
    print("If all tests passed, your NOWPayments integration is ready!")