# 💰 Wallet System Setup Guide

This guide explains how to set up the cryptocurrency wallet system using NOWPayments API.

## 🔧 Configuration

### 1. Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

```bash
# NOWPayments Configuration
NOWPAYMENTS_API_KEY=your_nowpayments_api_key_here
NOWPAYMENTS_IPN_SECRET=your_nowpayments_ipn_secret_here
NOWPAYMENTS_IPN_URL=https://your-domain.com/webhook/nowpayments

# Webhook Configuration
WEBHOOK_URL=https://your-domain.com
```

### 2. NOWPayments Account Setup

1. **Create Account**: Sign up at [NOWPayments](https://nowpayments.io/)
2. **Get API Key**: Go to Settings → API Keys → Generate new key
3. **Set IPN Secret**: Go to Settings → IPN Settings → Set IPN secret
4. **Configure IPN URL**: Set to `https://your-domain.com/webhook/nowpayments`

### 3. Webhook Setup

The webhook handler is located at `src/webhook.py` and handles:
- Payment confirmations
- Balance updates
- Transaction recording

Make sure your server is accessible from the internet for IPN notifications.

## 🎮 How It Works

### Deposit Flow

1. **User selects deposit amount** → Deposit menu shows preset amounts ($10, $25, $50, etc.)
2. **User selects cryptocurrency** → Shows supported cryptos (BTC, ETH, USDT, etc.)
3. **Payment created** → NOWPayments API creates payment with unique address
4. **User sends payment** → User sends crypto to the provided address
5. **Payment confirmed** → NOWPayments sends IPN notification
6. **Balance updated** → User's balance is automatically credited

### Supported Cryptocurrencies

- Bitcoin (BTC)
- Ethereum (ETH)
- Tether USDT (USDT)
- USD Coin (USDC)
- Litecoin (LTC)
- Solana (SOL)
- Binance Coin (BNB)
- Tron (TRX)
- Monero (XMR)
- DAI (DAI)
- Dogecoin (DOGE)
- Shiba Inu (SHIB)
- Bitcoin Cash (BCH)
- Polygon (MATIC)
- Toncoin (TON)
- NotCoin (NOT)

## 🧪 Testing

Run the test script to verify your setup:

```bash
python test_nowpayments.py
```

This will test:
- API connectivity
- Available currencies
- Exchange rates
- Webhook configuration

## 🔒 Security Features

### IPN Verification
- All webhook requests are verified using HMAC-SHA512
- Invalid signatures are rejected
- Only confirmed payments are processed

### Payment Validation
- User ID extracted from order ID
- Amount validation
- Duplicate payment prevention

### Error Handling
- Comprehensive error logging
- Graceful failure handling
- User-friendly error messages

## 📱 User Interface

### Deposit Menu
- Clean, intuitive interface
- Preset amount buttons
- Custom amount input
- Cryptocurrency selection with icons

### Payment Status
- Real-time status checking
- Payment confirmation notifications
- Address copying functionality
- Clear payment instructions

## 🔧 Troubleshooting

### Common Issues

1. **API Key Invalid**
   - Check your NOWPayments API key
   - Ensure it's correctly set in `.env`

2. **Webhook Not Receiving**
   - Verify your domain is accessible
   - Check IPN URL configuration
   - Ensure webhook endpoint is running

3. **Payment Not Credited**
   - Check webhook logs
   - Verify IPN secret matches
   - Check payment status in NOWPayments dashboard

### Debug Mode

Enable debug logging by setting:
```bash
DEBUG=true
```

### Logs

Check these files for debugging:
- Webhook logs: Console output from `webhook.py`
- Bot logs: Application logs
- NOWPayments dashboard: Payment status and history

## 🚀 Production Deployment

### Requirements
- SSL certificate (HTTPS required for webhooks)
- Accessible domain/IP
- MongoDB database
- Python 3.8+

### Deployment Checklist
- [ ] Configure all environment variables
- [ ] Set up SSL certificate
- [ ] Configure webhook URL
- [ ] Test payment flow
- [ ] Monitor webhook logs
- [ ] Set up backup systems

## 📊 Monitoring

### Key Metrics
- Payment success rate
- Average confirmation time
- Failed payment reasons
- User deposit patterns

### Alerts
Set up monitoring for:
- Webhook failures
- API errors
- Database connection issues
- Payment processing delays

## 🆘 Support

For issues with:
- **NOWPayments API**: Contact NOWPayments support
- **Bot Integration**: Check this documentation and logs
- **Webhook Issues**: Verify server configuration

## 📝 Notes

- Minimum deposit: $10 USD
- Payment expiration: 30 minutes
- Confirmation time: 10-30 minutes (network dependent)
- All amounts are processed in USD equivalent
- Real-time exchange rates from NOWPayments API