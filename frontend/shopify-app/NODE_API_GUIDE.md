# Node.js API Client Guide

This guide shows you how to use Node.js to send commands to APIs in the UofTHacks project.

## Quick Start

### 1. Using the API Client Library

The `api-client.js` file provides helper functions for all APIs:

```javascript
const { BackendAPI, FrontendAPI, ShopifyAPI } = require('./api-client');

// Call backend API
const products = await BackendAPI.getProducts();
const trends = await BackendAPI.getTrends();

// Call frontend API
const collections = await FrontendAPI.getCollections();
await FrontendAPI.replaceProduct(123, 456, 789);

// Call Shopify API directly
const shopProducts = await ShopifyAPI.getProducts(shopDomain, accessToken);
```

### 2. Using fetch() Directly

Node.js (v18+) has built-in `fetch()`:

```javascript
// GET request
const response = await fetch('http://localhost:5000/api/products');
const data = await response.json();

// POST request
const response = await fetch('http://localhost:3000/api/replace-product', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    currentProductId: 123,
    replacementProductId: 456
  })
});
const data = await response.json();
```

### 3. Using axios (Optional)

If you prefer axios, install it first:

```bash
npm install axios
```

Then use it:

```javascript
const axios = require('axios');

// GET request
const response = await axios.get('http://localhost:5000/api/products');

// POST request
const response = await axios.post('http://localhost:3000/api/suggestions', {
  type: 'new-product',
  data: { product: { title: 'Test' } }
});
```

## API Client Reference

### BackendAPI

All methods return Promises. Base URL: `http://localhost:5000`

#### `healthCheck()`
Check backend health.

#### `getProducts()`
Get all products from backend.

#### `getProduct(productId)`
Get single product by ID.

#### `analyzeProducts(productIds = null)`
Analyze products with AI. Pass array of IDs or null for all.

#### `getTrends(filters = {})`
Get trends. Filters: `{ platform: 'TikTok', top: 5 }`

#### `getTrend(trendId)`
Get single trend by ID.

#### `matchProductToTrends(productId)`
Match a product to relevant trends.

### FrontendAPI

Base URL: `http://localhost:3000`

#### `getProducts()`
Get products from Shopify via frontend API.

#### `getCollections()`
Get all collections.

#### `replaceProduct(currentProductId, replacementProductId, collectionId)`
Replace product in collection.

#### `getSuggestions()`
Get all suggestions.

#### `createSuggestion(type, data)`
Create a new suggestion. Types: `'new-product'`, `'price-change'`, `'replace-product'`

#### `acceptSuggestion(suggestionId)`
Accept and apply a suggestion.

### ShopifyAPI

Direct Shopify API access.

#### `request(shopDomain, accessToken, endpoint, method, body, apiVersion)`
Make a raw Shopify API request.

#### `getProducts(shopDomain, accessToken, limit)`
Get products from Shopify.

#### `getProduct(shopDomain, accessToken, productId)`
Get single product.

#### `graphql(shopDomain, accessToken, query, variables)`
Execute GraphQL query.

## Common Patterns

### Pattern 1: Sequential Requests

```javascript
const products = await BackendAPI.getProducts();
const trends = await BackendAPI.getTrends();
const analysis = await BackendAPI.analyzeProducts(products.map(p => p.id));
```

### Pattern 2: Parallel Requests

```javascript
const [products, trends, collections] = await Promise.all([
  BackendAPI.getProducts(),
  BackendAPI.getTrends(),
  FrontendAPI.getCollections()
]);
```

### Pattern 3: Error Handling

```javascript
try {
  const products = await BackendAPI.getProducts();
  console.log('Got products:', products);
} catch (error) {
  console.error('Failed to get products:', error.message);
  // Handle error
}
```

### Pattern 4: Conditional Requests

```javascript
const health = await BackendAPI.healthCheck();
if (health.status === 'ok') {
  const products = await BackendAPI.getProducts();
}
```

## Examples

### Example 1: Analyze and Replace Product

```javascript
const { BackendAPI, FrontendAPI } = require('./api-client');

async function analyzeAndReplace(productId) {
  // Get product analysis
  const analysis = await BackendAPI.analyzeProduct(productId);
  
  // Get trend matches
  const trendMatches = await BackendAPI.matchProductToTrends(productId);
  
  // Create replacement suggestion
  const suggestion = await FrontendAPI.createSuggestion('replace-product', {
    productIdToReplace: productId,
    newProduct: {
      title: analysis.recommendations.title,
      description: analysis.recommendations.description
    }
  });
  
  // Accept the suggestion
  await FrontendAPI.acceptSuggestion(suggestion.suggestion.id);
  
  console.log('Product replaced successfully!');
}
```

### Example 2: Batch Process Products

```javascript
async function batchProcess() {
  // Get all products
  const products = await BackendAPI.getProducts();
  
  // Process each product
  for (const product of products) {
    try {
      const analysis = await BackendAPI.analyzeProduct(product.id);
      console.log(`Analyzed: ${product.title}`, analysis);
    } catch (error) {
      console.error(`Failed to analyze ${product.title}:`, error.message);
    }
  }
}
```

### Example 3: Sync Trends and Products

```javascript
async function syncTrendsAndProducts() {
  // Get current trends
  const trends = await BackendAPI.getTrends({ top: 10 });
  
  // Get products
  const products = await BackendAPI.getProducts();
  
  // Match products to trends
  for (const product of products) {
    const matches = await BackendAPI.matchProductToTrends(product.id);
    if (matches.length > 0) {
      console.log(`${product.title} matches ${matches.length} trends`);
    }
  }
}
```

## Running Examples

See `examples/api-usage-examples.js` for more examples:

```bash
cd frontend/shopify-app
node examples/api-usage-examples.js
```

## Troubleshooting

### "fetch is not defined"

Node.js 18+ includes `fetch()`. For older versions:

```bash
npm install node-fetch
```

```javascript
const fetch = require('node-fetch');
```

### "ECONNREFUSED" Error

Make sure your servers are running:

- Backend: `cd backend && python app.py`
- Frontend: `cd frontend/shopify-app && npm start`

### CORS Errors

CORS is already configured in both servers. If you still see errors:

1. Check server URLs are correct
2. Ensure servers are running
3. Check firewall/network settings

## Best Practices

1. **Use the API client library** - It handles headers, errors, and URL construction
2. **Handle errors** - Always wrap API calls in try-catch
3. **Use async/await** - Makes code more readable
4. **Add timeouts** - For long-running requests
5. **Rate limiting** - Be mindful of API rate limits (especially Shopify)

## Next Steps

- See `api-client.js` for all available methods
- Check `examples/api-usage-examples.js` for working examples
- Read API documentation in `backend/README.md` and `frontend/shopify-app/README.md`
