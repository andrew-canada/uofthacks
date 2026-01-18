# Shopify App Backend

This service exposes product tools plus the AI theme proposal pipeline via the Shopify Admin REST API.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create `.env` using this template:
   ```env
   SHOPIFY_API_KEY=your_api_key_from_shopify
   SHOPIFY_API_SECRET=your_api_secret_from_shopify
   SHOPIFY_ACCESS_TOKEN=your_access_token_from_shopify
   SHOPIFY_SHOP_DOMAIN=your-store.myshopify.com
   SHOPIFY_API_VERSION=2026-01
   SHOPIFY_SCOPES=read_products,write_products,read_product_listings,write_product_listings,read_themes,write_themes
   THEME_ASSET_MAX_BYTES=500000
   PORT=3000
   ```

3. Run the server:
   ```bash
   npm start
   ```

## Scripts

- `npm start` - start server
- `npm run dev` - start server in dev mode

## Theme AI Pipeline Endpoints

- `POST /api/themes/ai-proposals`
- `GET /api/themes/ai-proposals/:id`
- `POST /api/themes/ai-proposals/:id/apply-to-draft`
- `POST /api/themes/ai-proposals/:id/apply-to-main`
- `GET /api/themes/drafts/:id/preview-url`
