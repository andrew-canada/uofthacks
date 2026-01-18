# Shopify Product Suggestions API

This app allows admins to permanently replace products in collections via the admin suggestions tab.

## Setup Instructions

### Step 1: Create a Shopify Custom App

1. **Go to your Shopify Admin**:
   - Navigate to: https://parallelapparel-uofthacksdemo.myshopify.com/admin

2. **Enable Custom App Development**:
   - Go to **Settings** → **Apps and sales channels**
   - Click **Develop apps**
   - If prompted, click **Allow custom app development**

3. **Create a New App**:
   - Click **Create an app**
   - App name: `Product Suggestions API`
   - Click **Create app**

4. **Configure API Scopes**:
   - Click **Configure Admin API scopes**
   - Select these scopes:
     - ✅ `read_products` - Read products
     - ✅ `write_products` - Write products
     - ✅ `read_product_listings` - Read product listings
     - ✅ `write_product_listings` - Write product listings
   - Click **Save**

5. **Install the App**:
   - Click **Install app**
   - Click **Install** to confirm

6. **Get Your Credentials**:
   - After installation, you'll see:
     - **API key** (Client ID)
     - **API secret key** (Client secret)
     - **Admin API access token**
   - ⚠️ Copy these immediately - the access token is only shown once!

### Step 2: Configure the App

1. **Create .env file**:
   ```bash
   cp .env.example .env
   ```

2. **Add your credentials to .env**:
   ```env
   SHOPIFY_API_KEY=your_api_key_from_step_1
   SHOPIFY_API_SECRET=your_api_secret_from_step_1
   SHOPIFY_ACCESS_TOKEN=your_access_token_from_step_1
   SHOPIFY_SHOP_DOMAIN=parallelapparel-uofthacksdemo.myshopify.com
   PORT=3000
   ```

### Step 3: Run the App

1. **Install dependencies** (already done):
   ```bash
   npm install
   ```

2. **Start the server**:
   ```bash
   npm start
   ```

3. **Verify it's running**:
   - You should see: `🚀 Product Suggestions API running on port 3000`
   - Test health check: http://localhost:3000/health

### Step 4: Make API Accessible from Shopify

For the theme to call the API, you have two options:

#### Option A: Use ngrok (Quick Testing)
1. Install ngrok: https://ngrok.com/download
2. Run: `ngrok http 3000`
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. Update the theme's API endpoint to use this URL

#### Option B: Deploy to Production (Recommended)
Deploy to a hosting service:
- **Heroku**: Easy deployment, free tier available
- **Railway**: Modern, simple deployment
- **DigitalOcean**: More control, $5/month
- **Vercel/Netlify**: Serverless options

### Step 5: Update Theme Code

Update the `admin-product-suggestions.liquid` file to use your API:

Find line 438 (the `syncWithShopifyAPI` function) and change:
```javascript
const endpoint = '/apps/product-suggestions/sync';
```

To your actual endpoint:
```javascript
const endpoint = 'https://your-api-url.com/api/replace-product';
// Or for local testing: 'http://localhost:3000/api/replace-product'
// Or with ngrok: 'https://abc123.ngrok.io/api/replace-product'
```

## API Endpoints

### POST /api/replace-product
Replace a product in a collection.

**Request:**
```json
{
  "currentProductId": "123456789",
  "replacementProductId": "987654321",
  "collectionId": "456789123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Product replaced successfully",
  "data": {
    "currentProductId": "123456789",
    "replacementProductId": "987654321",
    "replacementProduct": { ... }
  }
}
```

### GET /api/collections
Get all collections.

### GET /api/products
Get all products.

## Testing

1. Start the server: `npm start`
2. Make a test request:
   ```bash
   curl -X POST http://localhost:3000/api/replace-product \
     -H "Content-Type: application/json" \
     -d '{
       "currentProductId": "123",
       "replacementProductId": "456",
       "collectionId": "789"
     }'
   ```

## Troubleshooting

### "Access token is invalid"
- Make sure you copied the access token correctly from Shopify Admin
- The token should start with `shpat_`
- Regenerate the token if needed (you'll need to reinstall the app)

### CORS errors
- Make sure your API URL is accessible from your Shopify store
- Check that CORS is enabled in server.js

### Products not replacing
- Verify the product IDs are correct
- Check that the collection ID exists
- Look at server logs for detailed error messages

## Security Notes

⚠️ **Never commit your .env file to git!**

The `.gitignore` file already excludes it, but always double-check.

## Support

For issues or questions, check the server logs:
```bash
npm start
```

Look for error messages and API responses in the console.
