# Marketing & UI MCP Server Setup

This MCP server provides access to marketing generator functions and UI modification tools for the UofTHacks project.

## What It Does

The Marketing & UI MCP Server exposes:

1. **Marketing Generation** - Access to backend marketing generator service
2. **UI Modifications** - Tools to modify product UI (badges, ordering, styling)
3. **Trending Products** - Identify and highlight trending products

## Features

### Tools Available

- `generate_marketing` - Generate marketing content for products using trends
- `add_trending_badge` - Add trending badges to products in UI
- `reorder_products` - Reorder products (move trending to front)
- `apply_marketing_to_product` - Apply generated marketing to products
- `get_trending_products` - Get list of trending products
- `update_product_styling` - Update product UI styling

## Setup

### 1. Install Dependencies

```bash
cd frontend/shopify-app
npm install
```

### 2. Add UI Routes to Server

The `routes/ui-modifications.js` file is already created. Make sure it's imported in `server.js`:

```javascript
const uiModificationsRouter = require('./routes/ui-modifications');
app.use('/api', uiModificationsRouter);
```

### 3. Add Client-Side Script

Add the UI modifications script to your HTML pages:

```html
<script src="/js/ui-modifications.js"></script>
```

### 4. Configure MCP Server in Cursor

Add to Cursor settings.json:

```json
{
  "mcp.servers": {
    "uofthacks-marketing-ui": {
      "command": "node",
      "args": [
        "C:/work/project/git-repo/uofthacks/mcp-servers/marketing-ui-server.js"
      ],
      "env": {
        "BACKEND_API_URL": "http://localhost:5000",
        "FRONTEND_API_URL": "http://localhost:3000"
      }
    }
  }
}
```

**Important:** Update paths to match your project location!

## Usage Examples

### Example 1: Generate Marketing for Product

```javascript
// Via MCP server (from Cursor)
// Call: generate_marketing with productId

// Via API client
const { BackendAPI } = require('./api-client');
const analysis = await BackendAPI.analyzeProduct('product-id');
const marketing = analysis.recommendations;
```

### Example 2: Add Trending Badge

```javascript
// Via API
await fetch('http://localhost:3000/api/products/123/badge', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    badge: {
      type: 'trending',
      text: '🔥 Trending',
      visible: true
    }
  })
});

// Client-side script will automatically apply the badge
```

### Example 3: Reorder Products

```javascript
// Via API
await fetch('http://localhost:3000/api/products/order', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    collectionId: 'collection-123',
    productIds: ['trending-product-1', 'trending-product-2', 'other-product-3'],
    orderBy: 'trending'
  })
});
```

### Example 4: Apply Marketing & Styling

```javascript
// Generate marketing
const marketing = await BackendAPI.analyzeProduct('product-id');

// Apply marketing to product
await BackendAPI.applyRecommendations('product-id', marketing.recommendations);

// Add badge
await fetch(`http://localhost:3000/api/products/product-id/badge`, {
  method: 'POST',
  body: JSON.stringify({
    badge: { type: 'trending', text: '🔥 Trending' }
  })
});

// Update styling
await fetch(`http://localhost:3000/api/products/product-id/styling`, {
  method: 'POST',
  body: JSON.stringify({
    style: marketing.recommendations.layout_style || 'hero',
    colorScheme: marketing.recommendations.color_scheme
  })
});
```

## API Endpoints

### Badges

- `POST /api/products/:productId/badge` - Add badge
- `GET /api/products/:productId/badge` - Get badge
- `DELETE /api/products/:productId/badge` - Remove badge

### Product Ordering

- `POST /api/products/order` - Set product order
- `GET /api/products/order?collectionId=xxx` - Get product order

### Styling

- `POST /api/products/:productId/styling` - Update styling
- `GET /api/products/:productId/styling` - Get styling

### UI State

- `GET /api/ui/state` - Get all UI state
- `GET /api/products/with-ui` - Get products with UI applied

## Client-Side Behavior

The `ui-modifications.js` script automatically:

1. Loads UI state from server on page load
2. Applies badges to product cards
3. Applies styling to product cards
4. Reorders products based on server configuration
5. Watches for dynamically added products and applies UI changes

### Product Card Requirements

For UI modifications to work, product cards should have:

```html
<div class="product-card" data-product-id="123">
  <!-- Product content -->
</div>
```

The script looks for `data-product-id` attributes on product cards.

## Testing

### Test MCP Server Directly

```bash
node mcp-servers/marketing-ui-server.js generate_marketing '{"productId":"123"}'
```

### Test API Endpoints

```bash
# Add badge
curl -X POST http://localhost:3000/api/products/123/badge \
  -H "Content-Type: application/json" \
  -d '{"badge":{"type":"trending","text":"🔥 Trending"}}'

# Get UI state
curl http://localhost:3000/api/ui/state

# Reorder products
curl -X POST http://localhost:3000/api/products/order \
  -H "Content-Type: application/json" \
  -d '{"productIds":["123","456","789"],"orderBy":"trending"}'
```

## Troubleshooting

### Badges Not Appearing

1. Check product cards have `data-product-id` attribute
2. Verify `ui-modifications.js` is loaded
3. Check browser console for errors
4. Verify badge is stored: `GET /api/ui/state`

### Products Not Reordering

1. Check product container selector matches your HTML structure
2. Verify product IDs match between order data and HTML
3. Check browser console for errors

### Styling Not Applying

1. Verify CSS is being injected (check `<style id="ui-modifications-styles">`)
2. Check product cards have correct `data-product-id`
3. Verify styling data in `GET /api/ui/state`

## Next Steps

- Integrate with Shopify theme templates
- Add real-time updates via WebSockets
- Persist UI state to database
- Add analytics for trending products
