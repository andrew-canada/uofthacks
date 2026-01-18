# Theme App Extension Setup

This app uses **Shopify Theme App Extensions** with metafields to modify UI, rather than directly manipulating HTML.

## How It Works

### 1. **Metafields Store UI State**
- Product badges → `namespace: trending_ui, key: badge`
- Product styling → `namespace: trending_ui, key: styling`
- Collection order → `namespace: trending_ui, key: product_order`

### 2. **Theme Extension Snippets**
Liquid snippets read metafields and apply UI changes:
- `trending-badge.liquid` - Displays product badges
- `product-styling.liquid` - Applies styling
- `collection-order.liquid` - Reorders products

### 3. **API Endpoints Manage Metafields**
All UI modifications go through API endpoints that set metafields via Shopify Admin API.

## Setup

### Step 1: Copy Theme Extension Snippets

Copy the snippet files to your Shopify theme:

```bash
# From theme-extension directory
cp trending-badge.liquid /path/to/theme/snippets/
cp product-styling.liquid /path/to/theme/snippets/
cp collection-order.liquid /path/to/theme/snippets/
```

Or upload via Shopify Admin:
1. Go to **Online Store** → **Themes** → **Code editor**
2. Navigate to **Snippets**
3. Create new snippets and paste the content

### Step 2: Include Snippets in Theme Templates

#### In Product Card Template:

```liquid
{%- comment -%} Add to product-card.liquid or product-grid-item.liquid {%- endcomment -%}
<div class="product-card" data-product-id="{{ product.id }}" style="position: relative;">
  {% render 'trending-badge', product: product %}
  {% render 'product-styling', product: product %}
  
  {%- comment -%} Your existing product card content {%- endcomment -%}
  <a href="{{ product.url }}">
    <img src="{{ product.featured_image | img_url: '300x300' }}" alt="{{ product.title }}">
    <h3>{{ product.title }}</h3>
    <p>{{ product.price | money }}</p>
  </a>
</div>
```

#### In Collection Template:

```liquid
{%- comment -%} Add to collection.liquid or collection-template.liquid {%- endcomment -%}
<div class="collection-products" data-collection-id="{{ collection.id }}">
  {% render 'collection-order', collection: collection %}
  
  {%- for product in collection.products -%}
    {% render 'product-card', product: product %}
  {%- endfor -%}
</div>
```

### Step 3: Start Server

```bash
cd frontend/shopify-app
npm start
```

### Step 4: Configure MCP Server

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

## API Endpoints

### Product Badges

```javascript
// Add badge
POST /api/theme-extensions/product-badge
{
  "productId": "gid://shopify/Product/123",
  "badgeType": "trending",
  "badgeText": "🔥 Trending"
}

// Get badge
GET /api/theme-extensions/product-badge/:productId

// Remove badge
DELETE /api/theme-extensions/product-badge/:productId
```

### Product Styling

```javascript
// Set styling
POST /api/theme-extensions/product-styling
{
  "productId": "gid://shopify/Product/123",
  "styleType": "hero",
  "colorScheme": "#FF6B6B"
}
```

### Collection Ordering

```javascript
// Set product order
POST /api/theme-extensions/collection-order
{
  "collectionId": "gid://shopify/Collection/456",
  "productIds": ["gid://shopify/Product/123", "gid://shopify/Product/789"],
  "orderBy": "trending"
}

// Get products with order
GET /api/theme-extensions/collection/:collectionId/products
```

### Get All Products with UI State

```javascript
// Get products with badges and styling
GET /api/theme-extensions/products-with-ui?limit=50
```

## Usage Examples

### Example 1: Add Trending Badge via API

```javascript
const response = await fetch('http://localhost:3000/api/theme-extensions/product-badge', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    productId: 'gid://shopify/Product/123',
    badgeType: 'trending',
    badgeText: '🔥 Trending Now'
  })
});

const result = await response.json();
// Badge is now stored in metafield
// Theme extension will automatically display it
```

### Example 2: Reorder Products in Collection

```javascript
// Get trending products
const productsResponse = await fetch('http://localhost:3000/api/theme-extensions/products-with-ui');
const { products } = await productsResponse.json();

// Sort by trending status
const trendingProducts = products
  .filter(p => p.ui.badge?.type === 'trending')
  .map(p => p.id);

// Set collection order
await fetch('http://localhost:3000/api/theme-extensions/collection-order', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    collectionId: 'gid://shopify/Collection/456',
    productIds: trendingProducts,
    orderBy: 'trending'
  })
});

// Order is stored in collection metafield
// Theme extension will automatically reorder products
```

### Example 3: Apply Marketing & Styling

```javascript
// 1. Generate marketing
const marketing = await BackendAPI.analyzeProduct('product-id');

// 2. Add badge
await fetch('/api/theme-extensions/product-badge', {
  method: 'POST',
  body: JSON.stringify({
    productId: 'product-id',
    badgeType: marketing.recommendations.trust_badges?.[0] || 'trending'
  })
});

// 3. Apply styling
await fetch('/api/theme-extensions/product-styling', {
  method: 'POST',
  body: JSON.stringify({
    productId: 'product-id',
    styleType: marketing.recommendations.layout_style || 'hero',
    colorScheme: marketing.recommendations.color_scheme
  })
});

// All UI changes are stored in metafields
// Theme extensions automatically apply them
```

## MCP Server Usage

From Cursor AI, you can ask:

- **"Add a trending badge to product 123"**
  - Calls `add_trending_badge` tool
  - Sets metafield via API
  - Theme extension displays badge automatically

- **"Reorder products in collection 456 to show trending first"**
  - Calls `reorder_products` tool
  - Sets collection order metafield
  - Theme extension reorders products automatically

- **"Apply hero styling to product 789"**
  - Calls `update_product_styling` tool
  - Sets styling metafield
  - Theme extension applies styles automatically

## How Theme Extensions Work

1. **API sets metafield** → Stores UI state in Shopify
2. **Theme snippet reads metafield** → Liquid code reads the metafield value
3. **Snippet applies UI** → Badges, styling, ordering applied via Liquid/JS
4. **No direct HTML manipulation** → Everything goes through Shopify metafields/API

## Benefits

✅ **No theme code injection** - Uses standard Shopify metafields  
✅ **API-driven** - All changes via REST/GraphQL APIs  
✅ **Theme-safe** - Works with any Shopify theme  
✅ **Persistent** - State stored in Shopify, survives theme updates  
✅ **MCP-enabled** - Accessible via Cursor AI assistant  

## Troubleshooting

### Badges Not Showing

1. Check metafield exists: `GET /api/theme-extensions/product-badge/:productId`
2. Verify snippet is included in theme template
3. Check product card has `data-product-id` attribute
4. Ensure metafield namespace is `trending_ui` and key is `badge`

### Styling Not Applying

1. Check styling metafield: Look for `trending_ui.styling` metafield
2. Verify `product-styling.liquid` snippet is included
3. Check CSS classes match theme's structure

### Products Not Reordering

1. Check collection order metafield exists
2. Verify `collection-order.liquid` snippet is included
3. Ensure collection container has correct `data-collection-id`

## Next Steps

- Deploy snippets to production theme
- Test with different themes
- Add more UI modification options
- Create theme extension app block (optional)
