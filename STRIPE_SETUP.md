# Stripe Setup Guide

This guide will help you set up Stripe integration for the Table Flask application.

## Step 1: Create a Stripe Account

1. Go to [https://stripe.com](https://stripe.com)
2. Click "Sign up" and create an account
3. Complete the verification process (you can start with test mode)

## Step 2: Get Your API Keys

1. Log in to your Stripe Dashboard
2. Navigate to [https://dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys)
3. You'll see two keys:
   - **Publishable key**: Starts with `pk_test_` (safe to use in frontend)
   - **Secret key**: Starts with `sk_test_` (keep this secure, backend only)

## Step 3: Create Products and Prices

1. Go to [https://dashboard.stripe.com/test/products](https://dashboard.stripe.com/test/products)
2. Click "Add product"
3. Create two products:

### Product 1: Single Table Analysis
- **Name**: Single Table Analysis
- **Description**: Analyze one Excel table at a time
- **Pricing**: 
  - Model: One-time payment
  - Price: Set your desired amount (e.g., $9.99)
  - Currency: USD (or your preferred currency)

### Product 2: Multi Table Analysis
- **Name**: Multi Table Analysis  
- **Description**: Analyze multiple Excel tables simultaneously
- **Pricing**:
  - Model: One-time payment
  - Price: Set your desired amount (e.g., $19.99)
  - Currency: USD (or your preferred currency)

4. After creating each product, copy the **Price ID** (starts with `price_`)

## Step 4: Set Up Webhooks (Optional but Recommended)

1. Go to [https://dashboard.stripe.com/test/webhooks](https://dashboard.stripe.com/test/webhooks)
2. Click "Add endpoint"
3. Endpoint URL: `http://your-domain.com/api/stripe-webhook` (for local testing: `http://localhost:5000/api/stripe-webhook`)
4. Select events to listen for:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the **Webhook signing secret** (starts with `whsec_`)

## Step 5: Update Your .env File

Replace the placeholder values in your `.env` file with the real values:

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_actual_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret_here
STRIPE_SINGLE_TABLE_PRICE_ID=price_your_actual_single_table_price_id
STRIPE_MULTI_TABLE_PRICE_ID=price_your_actual_multi_table_price_id
```

## Step 6: Test the Integration

1. Restart your Flask application
2. Go to the subscription page
3. Use Stripe's test card numbers:
   - **Success**: `4242424242424242`
   - **Decline**: `4000000000000002`
   - **Requires authentication**: `4000002500003155`
   - Use any future expiry date, any 3-digit CVC, and any postal code

## Step 7: Going Live (Production)

When you're ready for production:

1. Activate your Stripe account (complete business verification)
2. Switch to live mode in the Stripe Dashboard
3. Get your live API keys (they start with `pk_live_` and `sk_live_`)
4. Update your production `.env` file with live keys
5. Update webhook endpoints to use your production domain

## Troubleshooting

### Common Issues:

1. **"Invalid API key"**: Make sure you copied the full key without extra spaces
2. **"No such price"**: Verify the price IDs are correct and exist in your Stripe account
3. **Webhook failures**: Check that your webhook URL is accessible and returns 200 status

### Test Mode vs Live Mode:
- Test keys only work with test payments
- Live keys only work with real payments
- Make sure you're using the correct mode consistently

### Security Notes:
- Never commit real API keys to version control
- Keep secret keys secure on the server side only
- Use environment variables for all sensitive data
- Regularly rotate your API keys if needed

## Support

- Stripe Documentation: [https://stripe.com/docs](https://stripe.com/docs)
- Stripe Support: Available in your Stripe Dashboard
- Test Cards: [https://stripe.com/docs/testing#cards](https://stripe.com/docs/testing#cards)
