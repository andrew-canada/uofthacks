/**
 * Examples of using Node.js to call APIs
 * 
 * Run these examples with:
 *   node examples/api-usage-examples.js
 */

const { BackendAPI, FrontendAPI, ShopifyAPI } = require('../api-client');
require('dotenv').config();

// ============================================
// Example 1: Call Backend Flask API
// ============================================

async function exampleBackendAPI() {
  console.log('\n=== Backend API Examples ===\n');

  try {
    // Health check
    console.log('1. Health Check:');
    const health = await BackendAPI.healthCheck();
    console.log(health);

    // Get all products
    console.log('\n2. Get Products:');
    const products = await BackendAPI.getProducts();
    console.log(`Found ${products.length || 0} products`);

    // Get all trends
    console.log('\n3. Get Trends:');
    const trends = await BackendAPI.getTrends({ platform: 'TikTok' });
    console.log(`Found ${trends.length || 0} TikTok trends`);

    // Analyze products
    console.log('\n4. Analyze Products:');
    const analysis = await BackendAPI.analyzeProducts();
    console.log('Analysis complete:', analysis);

  } catch (error) {
    console.error('Backend API Error:', error.message);
  }
}

// ============================================
// Example 2: Call Frontend Express API
// ============================================

async function exampleFrontendAPI() {
  console.log('\n=== Frontend API Examples ===\n');

  try {
    // Health check
    console.log('1. Health Check:');
    const health = await FrontendAPI.healthCheck();
    console.log(health);

    // Get products
    console.log('\n2. Get Products:');
    const products = await FrontendAPI.getProducts();
    console.log(`Found ${products.products?.length || 0} products`);

    // Get collections
    console.log('\n3. Get Collections:');
    const collections = await FrontendAPI.getCollections();
    console.log(`Found ${collections.collections?.length || 0} collections`);

    // Get suggestions
    console.log('\n4. Get Suggestions:');
    const suggestions = await FrontendAPI.getSuggestions();
    console.log(`Found ${suggestions.suggestions?.length || 0} suggestions`);

  } catch (error) {
    console.error('Frontend API Error:', error.message);
  }
}

// ============================================
// Example 3: Call Shopify API Directly
// ============================================

async function exampleShopifyAPI() {
  console.log('\n=== Shopify API Examples ===\n');

  const shopDomain = process.env.SHOPIFY_SHOP_DOMAIN;
  const accessToken = process.env.SHOPIFY_ACCESS_TOKEN;

  if (!shopDomain || !accessToken) {
    console.log('⚠️  Shopify credentials not configured');
    console.log('Set SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN in .env');
    return;
  }

  try {
    // Get products
    console.log('1. Get Products:');
    const productsData = await ShopifyAPI.getProducts(shopDomain, accessToken, 10);
    console.log(`Found ${productsData.products?.length || 0} products`);

    // Get collections
    console.log('\n2. Get Collections:');
    const collectionsData = await ShopifyAPI.getCollections(shopDomain, accessToken);
    console.log(`Found ${collectionsData.custom_collections?.length || 0} collections`);

    // GraphQL example
    console.log('\n3. GraphQL Query:');
    const graphqlQuery = `
      query {
        shop {
          name
          myshopifyDomain
        }
      }
    `;
    const shopInfo = await ShopifyAPI.graphql(shopDomain, accessToken, graphqlQuery);
    console.log('Shop Info:', shopInfo.data?.shop);

  } catch (error) {
    console.error('Shopify API Error:', error.message);
  }
}

// ============================================
// Example 4: Using fetch() directly
// ============================================

async function exampleFetchDirectly() {
  console.log('\n=== Using fetch() Directly ===\n');

  // Example 1: Simple GET request
  console.log('1. Simple GET request:');
  try {
    const response = await fetch('http://localhost:5000/health');
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error('Error:', error.message);
  }

  // Example 2: POST request with body
  console.log('\n2. POST request with body:');
  try {
    const response = await fetch('http://localhost:3000/api/suggestions/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    const data = await response.json();
    console.log(`Generated ${data.suggestions?.length || 0} suggestions`);
  } catch (error) {
    console.error('Error:', error.message);
  }

  // Example 3: POST request with body data
  console.log('\n3. POST with data:');
  try {
    const response = await fetch('http://localhost:3000/api/suggestions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        type: 'new-product',
        data: {
          product: {
            title: 'Test Product',
            body_html: '<p>Test description</p>',
            vendor: 'Test Vendor',
            product_type: 'Test',
            status: 'active'
          }
        }
      })
    });
    const data = await response.json();
    console.log('Created suggestion:', data.suggestion?.id);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// ============================================
// Example 5: Using axios (if installed)
// ============================================

async function exampleAxios() {
  // Uncomment and install axios if you prefer it over fetch:
  // npm install axios
  
  /*
  const axios = require('axios');

  try {
    // GET request
    const response = await axios.get('http://localhost:5000/health');
    console.log(response.data);

    // POST request
    const postResponse = await axios.post('http://localhost:3000/api/suggestions', {
      type: 'new-product',
      data: { product: { title: 'Test' } }
    });
    console.log(postResponse.data);

  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
  */
}

// ============================================
// Example 6: Error handling patterns
// ============================================

async function exampleErrorHandling() {
  console.log('\n=== Error Handling Examples ===\n');

  try {
    // Try to get a non-existent product
    await BackendAPI.getProduct('non-existent-id');
  } catch (error) {
    console.log('Error caught:', error.message);
    // Handle error appropriately
  }

  // Using try-catch with multiple requests
  try {
    const [products, trends] = await Promise.all([
      BackendAPI.getProducts(),
      BackendAPI.getTrends()
    ]);
    console.log(`Got ${products.length} products and ${trends.length} trends`);
  } catch (error) {
    console.error('One or more requests failed:', error.message);
  }
}

// ============================================
// Run Examples
// ============================================

async function runAllExamples() {
  console.log('🚀 Node.js API Usage Examples\n');
  console.log('Make sure your servers are running:');
  console.log('  - Backend: http://localhost:5000');
  console.log('  - Frontend: http://localhost:3000\n');

  await exampleBackendAPI();
  await exampleFrontendAPI();
  await exampleShopifyAPI();
  await exampleFetchDirectly();
  await exampleErrorHandling();

  console.log('\n✅ Examples complete!');
}

// Run if executed directly
if (require.main === module) {
  runAllExamples().catch(console.error);
}

// Export for use in other files
module.exports = {
  exampleBackendAPI,
  exampleFrontendAPI,
  exampleShopifyAPI,
  exampleFetchDirectly,
  exampleErrorHandling
};
