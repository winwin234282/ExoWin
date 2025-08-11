from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import os
import asyncio
from src.database import get_user, update_user_balance, record_transaction
from src.wallet.nowpayments import verify_ipn_request, handle_ipn_notification

app = Flask(__name__)

@app.route('/webhook/nowpayments', methods=['POST'])
def nowpayments_webhook():
    """Handle NOWPayments IPN webhook"""
    try:
        # Get the signature from headers
        signature = request.headers.get('x-nowpayments-sig')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 400
        
        # Get the payload
        payload = request.get_data()
        
        # Verify the signature
        secret = os.getenv('NOWPAYMENTS_IPN_SECRET')
        if not secret:
            return jsonify({'error': 'IPN secret not configured'}), 500
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Parse the payment data
        payment_data = json.loads(payload.decode('utf-8'))
        
        # Process the payment
        asyncio.run(process_payment(payment_data))
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

async def process_payment(payment_data):
    """Process confirmed payment"""
    try:
        payment_status = payment_data.get('payment_status')
        payment_id = payment_data.get('payment_id')
        order_id = payment_data.get('order_id')
        actually_paid = float(payment_data.get('actually_paid', 0))
        
        # Only process confirmed payments
        if payment_status != 'confirmed':
            return
        
        # Extract user_id from order_id (format: "deposit_USER_ID_TIMESTAMP")
        if not order_id or not order_id.startswith('deposit_'):
            return
        
        parts = order_id.split('_')
        if len(parts) < 3:
            return
        
        user_id = int(parts[1])
        
        # Get user and verify they exist
        user = await get_user(user_id)
        if not user:
            return
        
        # Add funds to user balance
        await update_user_balance(user_id, actually_paid)
        
        # Record the transaction
        await record_transaction(
            user_id=user_id,
            amount=actually_paid,
            transaction_type="deposit",
            description=f"Crypto deposit - Payment ID: {payment_id}"
        )
        
        print(f"Payment processed: User {user_id} deposited ${actually_paid}")
        
    except Exception as e:
        print(f"Error processing payment: {str(e)}")

@app.route('/webhook/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12001, debug=False)