# Testing Theme Extensions on Your Site

This guide shows you how to see the theme extensions (badges, styling, product ordering) working on your Shopify store.

## Quick Test Process

### Step 1: Add Snippets to Your Theme

1. **Go to Shopify Admin**
   - Navigate to: **Online Store** → **Themes** → **Code editor**
   - Or visit: `https://parallelapparel-uofthacksdemo.myshopify.com/admin/themes`

2. **Create Snippets**
   - Click **"Add a new file"** or **"Snippets"** folder
   - Create these files:
     - `trending-badge.liquid`
     - `product-styling.liquid`
     - `collection-order.liquid`
   - Copy content from `frontend/shopify-app/theme-extension/` directory

3. **Include Snippets in Theme Templates**

   **For Product Cards** (e.g., in `snippets/product-card.liquid` or `sections/main-collection-product-grid.liquid`):
   ```liquid
   <div class="product-card" data-product-id="{{ product.id }}" style="position: relative;">
     {% render 'trending-badge', product: product %}
     {% render 'product-styling', product: product %}
     
     {%- comment -%} Your existing product card HTML {%- endcomment -%}
     <a href="{{ product.url }}">
       <img src="{{ product.featured_image | img_url: '300x300' }}" alt="{{ product.title }}">
       <h3>{{ product.title }}</h3>
       <p>{{ product.price | money }}</p>
     </a>
   </div>
   ```

   **For Collections** (e.g., in `templates/collection.liquid`):
   ```liquid
   <div class="collection-products" data-collection-id="{{ collection.id }}">
     {% render 'collection-order', collection: collection %}
     
     {%- for product in collection.products -%}
       {% render 'product-card', product: product %}
     {%- endfor -%}
   </div>
   ```

### Step 2: Start Your Node.js Server

```bash
cd frontend/shopify-app
npm start
```

Server should run on `http://localhost:3000`

### Step 3: Test API Endpoints

#### Test 1: Add a Badge to a Product

First, get a product ID from your store:

```bash
# Get products
curl http://localhost:3000/api/products
```

Or use this in your browser:
```
http://localhost:3000/api/products
```

Copy a product ID (e.g., `gid://shopify/Product/123456789`), then add a badge:

```bash
curl -X POST http://localhost:3000/api/theme-extensions/product-badge \
  -H "Content-Type: application/json" \
  -d '{
    "productId": "gid://shopify/Product/123456789",
    "badgeType": "trending",
    "badgeText": "🔥 Trending Now"
  }'
```

**Or use this JavaScript in browser console:**

```javascript
fetch('http://localhost:3000/api/theme-extensions/product-badge', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    productId: 'gid://shopify/Product/123456789', // Replace with your product ID
    badgeType: 'trending',
    badgeText: '🔥 Trending Now'
  })
})
.then(r => r.json())
.then(data => console.log('Badge added:', data));
```

#### Test 2: View Product with Badge

1. Go to your store's product page or collection page
2. The product with the badge should show a **"🔥 Trending Now"** badge in the top-right corner

If you don't see it:
- Check that the snippet is included in your theme template
- Verify `data-product-id="{{ product.id }}"` is set on the product card
- Check browser console for errors

#### Test 3: Add Product Styling

```bash
curl -X POST http://localhost:3000/api/theme-extensions/product-styling \
  -H "Content-Type: application/json" \
  -d '{
    "productId": "gid://shopify/Product/123456789",
    "styleType": "hero",
    "colorScheme": "#FF6B6B"
  }'
```

Or in browser:

```javascript
fetch('http://localhost:3000/api/theme-extensions/product-styling', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    productId: 'gid://shopify/Product/123456789',
    styleType: 'hero',
    colorScheme: '#FF6B6B'
  })
})
.then(r => r.json())
.then(data => console.log('Styling applied:', data));
```

**Expected result:** Product card should have a red border (hero style)

#### Test 4: Reorder Products in Collection

First, get your collection ID:

```bash
curl http://localhost:3000/api/collections
```

Then set product order:

```bash
curl -X POST http://localhost:3000/api/theme-extensions/collection-order \
  -H "Content-Type: application/json" \
  -d '{
    "collectionId": "gid://shopify/Collection/987654321",
    "productIds": ["gid://shopify/Product/111", "gid://shopify/Product/222"],
    "orderBy": "trending"
  }'
```

Or in browser:

```javascript
fetch('http://localhost:3000/api/theme-extensions/collection-order', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    collectionId: 'gid://shopify/Collection/987654321', // Your collection ID
    productIds: ['gid://shopify/Product/111', 'gid://shopify/Product/222'], // Product IDs in order
    orderBy: 'trending'
  })
})
.then(r => r.json())
.then(data => console.log('Order set:', data));
```

**Expected result:** Products should reorder on collection page

## Quick Test Script

Create a test file `test-theme-extensions.js`:

```javascript
const API_BASE = 'http://localhost:3000';

async function testThemeExtensions() {
  console.log('🧪 Testing Theme Extensions...\n');

  // Step 1: Get a product
  const productsRes = await fetch(`${API_BASE}/api/products`);
  const productsData = await productsRes.json();
  
  if (!productsData.success || productsData.products.length === 0) {
    console.log('❌ No products found. Make sure your store has products.');
    return;
  }

  const product = productsData.products[0];
  console.log(`✅ Found product: ${product.title} (ID: ${product.id})\n`);

  // Step 2: Add badge
  console.log('1️⃣ Adding trending badge...');
  const badgeRes = await fetch(`${API_BASE}/api/theme-extensions/product-badge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      productId: product.id,
      badgeType: 'trending',
      badgeText: '🔥 Trending Now'
    })
  });
  const badgeData = await badgeRes.json();
  console.log(badgeData.success ? '✅ Badge added!' : `❌ Error: ${badgeData.error}\n`);

  // Step 3: Add styling
  console.log('\n2️⃣ Adding hero styling...');
  const styleRes = await fetch(`${API_BASE}/api/theme-extensions/product-styling`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      productId: product.id,
      styleType: 'hero',
      colorScheme: '#FF6B6B'
    })
  });
  const styleData = await styleRes.json();
  console.log(styleData.success ? '✅ Styling applied!' : `❌ Error: ${styleData.error}\n`);

  // Step 4: Verify metafields
  console.log('\n3️⃣ Verifying metafields...');
  const verifyRes = await fetch(`${API_BASE}/api/theme-extensions/product-badge/${encodeURIComponent(product.id)}`);
  const verifyData = await verifyRes.json();
  
  if (verifyData.success && verifyData.badge) {
    console.log('✅ Badge metafield found:', verifyData.badge);
  } else {
    console.log('⚠️  Badge metafield not found (may take a moment to appear)');
  }

  console.log('\n✅ Testing complete!');
  console.log(`\n📋 Next steps:`);
  console.log(`   1. Visit your product page: ${product.title}`);
  console.log(`   2. You should see a "🔥 Trending Now" badge`);
  console.log(`   3. Product card should have red border (hero style)`);
  console.log(`\n💡 If you don't see changes:`);
  console.log(`   - Make sure snippets are added to your theme`);
  console.log(`   - Refresh the product page`);
  console.log(`   - Check browser console for errors`);
}

testThemeExtensions().catch(console.error);
```

Run it:

```bash
node test-theme-extensions.js
```

## Using MCP Server (from Cursor)

If you've set up the MCP server in Cursor, you can ask:

**"Add a trending badge to product [product-id]"**

The MCP server will call the API endpoint and set the metafield.

## Verifying Metafields in Shopify Admin

To see metafields directly:

1. **Go to Product Page**
   - Admin → Products → Select a product
   - Scroll down to **"Metafields"** section
   - Look for `trending_ui.badge` and `trending_ui.styling`

2. **Or use GraphQL Admin API**
   ```graphql
   query {
     product(id: "gid://shopify/Product/123456789") {
       id
       title
       metafields(namespace: "trending_ui") {
         edges {
           node {
             key
             value
             type
           }
         }
       }
     }
   }
   ```

## Troubleshooting

### Badges Not Showing

1. **Check snippet is included**
   - Open theme code editor
   - Find your product card template
   - Verify `{% render 'trending-badge', product: product %}` is present

2. **Check product ID**
   - Product card needs `data-product-id="{{ product.id }}"`
   - Verify metafield was set: `GET /api/theme-extensions/product-badge/:productId`

3. **Check browser console**
   - Open DevTools (F12)
   - Look for Liquid syntax errors
   - Check for JavaScript errors

### Styling Not Applying

1. **Check CSS**
   - Inspect product card element
   - Verify `product-styling.liquid` snippet is included
   - Check if styles are being applied (inspect element styles)

2. **Check metafield**
   - Verify styling metafield exists via API
   - Check `namespace: trending_ui, key: styling`

### Products Not Reordering

1. **Check collection ID**
   - Verify collection ID is correct
   - Collection template needs `data-collection-id="{{ collection.id }}"`

2. **Check collection order snippet**
   - Verify `{% render 'collection-order', collection: collection %}` is in collection template

## Quick Visual Test

1. **Add badge** → Refresh product page → Should see badge
2. **Add styling** → Refresh product page → Should see border/color
3. **Set collection order** → Refresh collection page → Products should reorder

## Example: Full Test Flow

```bash
# 1. Start server
cd frontend/shopify-app
npm start

# 2. Get product ID (in new terminal)
curl http://localhost:3000/api/products | jq '.products[0].id'

# 3. Add badge (replace PRODUCT_ID)
curl -X POST http://localhost:3000/api/theme-extensions/product-badge \
  -H "Content-Type: application/json" \
  -d "{\"productId\":\"YOUR_PRODUCT_ID\",\"badgeType\":\"trending\"}"

# 4. Visit product page in browser - should see badge!
```

## Need Help?

- Check `THEME_EXTENSION_SETUP.md` for setup instructions
- Verify API endpoints are working: `GET http://localhost:3000/health`
- Check server logs for errors
- Verify environment variables: `SHOPIFY_SHOP_DOMAIN`, `SHOPIFY_ACCESS_TOKEN`
