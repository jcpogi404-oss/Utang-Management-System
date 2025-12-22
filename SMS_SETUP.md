# SMS Notification Setup Guide

## Overview
The system sends SMS notifications to customers when they receive credit.

## SMS Provider: Semaphore
We use Semaphore SMS API for sending text messages in the Philippines.

## Setup Instructions

### 1. Sign up for Semaphore
- Go to https://semaphore.co/
- Create an account
- Verify your account

### 2. Get Your API Key
- Log in to your Semaphore dashboard
- Go to API Settings
- Copy your API key

### 3. Configure the System

**Option A: Using Environment Variable (Recommended)**
```bash
export SEMAPHORE_API_KEY="your_actual_api_key_here"
```

**Option B: Direct Configuration**
Edit `app_sqlite.py` and replace:
```python
API_KEY = os.getenv('SEMAPHORE_API_KEY', 'YOUR_API_KEY_HERE')
```
with:
```python
API_KEY = 'your_actual_api_key_here'
```

### 4. Test the System
1. Start the application
2. Add a new credit with a valid Philippine phone number (09XXXXXXXXX)
3. Customer should receive an SMS notification

## SMS Message Format
```
Kumusta [Customer Name]!

May bagong utang ka sa Tindahan ni Annie:
Produkto: [Product Name]
Halaga: ₱[Amount]
Petsa nin Pagbayad: [Payment Date]

Salamat!
```

## Phone Number Format
- Must be 11 digits
- Format: 09XXXXXXXXX
- Example: 09171234567

## Pricing
- Check Semaphore pricing at https://semaphore.co/pricing
- Approximately ₱0.50 - ₱1.00 per SMS

## Troubleshooting

### SMS not sending?
1. Check if API key is configured correctly
2. Verify phone number format (09XXXXXXXXX)
3. Check Semaphore account balance
4. Look at console logs for error messages

### Testing without SMS
If you don't have an API key yet, the system will still work but won't send SMS. Check console logs to see what would have been sent.

## Alternative SMS Providers
If you prefer different SMS providers, you can modify the `send_sms_notification()` function in `app_sqlite.py`:
- Twilio (https://twilio.com)
- Vonage/Nexmo (https://vonage.com)
- Movider (https://movider.co)
- Chikka API
