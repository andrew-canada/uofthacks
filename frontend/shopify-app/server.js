const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Shopify configuration
const SHOPIFY_SHOP_DOMAIN = process.env.SHOPIFY_SHOP_DOMAIN;
const SHOPIFY_ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const SHOPIFY_API_VERSION = '2025-01';

// Helper function to make Shopify API requests
async function shopifyRequest(endpoint, method = 'GET', body = null) {
  const url = `https://${SHOPIFY_SHOP_DOMAIN}/admin/api/${SHOPIFY_API_VERSION}/${endpoint}`;

  const options = {
    method,
    headers: {
      'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
      'Content-Type': 'application/json',
    }
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Shopify API error: ${response.status} - ${error}`);
  }

  return response.json();
}

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Product Suggestions API is running' });
});

// Endpoint to replace product in collection
app.post('/api/replace-product', async (req, res) => {
  try {
    const { currentProductId, replacementProductId, collectionId } = req.body;

    if (!currentProductId || !replacementProductId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: currentProductId and replacementProductId'
      });
    }

    console.log(`Replacing product ${currentProductId} with ${replacementProductId}`);

    // If collection ID is provided, update the collection
    if (collectionId) {
      // Remove current product from collection (if exists)
      try {
        await shopifyRequest(`collects.json?product_id=${currentProductId}&collection_id=${collectionId}`, 'GET')
          .then(async (data) => {
            if (data.collects && data.collects.length > 0) {
              const collectId = data.collects[0].id;
              await shopifyRequest(`collects/${collectId}.json`, 'DELETE');
              console.log(`Removed product ${currentProductId} from collection`);
            }
          });
      } catch (error) {
        console.log('Product not in collection or already removed:', error.message);
      }

      // Add replacement product to collection
      try {
        await shopifyRequest('collects.json', 'POST', {
          collect: {
            product_id: replacementProductId,
            collection_id: collectionId
          }
        });
        console.log(`Added product ${replacementProductId} to collection`);
      } catch (error) {
        console.log('Error adding product to collection:', error.message);
      }
    }

    // Get product details for response
    const replacementProduct = await shopifyRequest(`products/${replacementProductId}.json`, 'GET');

    res.json({
      success: true,
      message: 'Product replaced successfully',
      data: {
        currentProductId,
        replacementProductId,
        collectionId,
        replacementProduct: replacementProduct.product
      }
    });

  } catch (error) {
    console.error('Error replacing product:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      details: error
    });
  }
});

// Endpoint to get all collections
app.get('/api/collections', async (req, res) => {
  try {
    const data = await shopifyRequest('custom_collections.json', 'GET');

    res.json({
      success: true,
      collections: data.custom_collections
    });

  } catch (error) {
    console.error('Error fetching collections:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Endpoint to get products
app.get('/api/products', async (req, res) => {
  try {
    const data = await shopifyRequest('products.json?limit=250', 'GET');

    res.json({
      success: true,
      products: data.products
    });

  } catch (error) {
    console.error('Error fetching products:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`\n🚀 Product Suggestions API running on port ${PORT}`);
  console.log(`📍 Shop: ${process.env.SHOPIFY_SHOP_DOMAIN}`);
  console.log(`\nEndpoints:`);
  console.log(`  GET  /health - Health check`);
  console.log(`  POST /api/replace-product - Replace product in collection`);
  console.log(`  GET  /api/collections - Get all collections`);
  console.log(`  GET  /api/products - Get all products`);
});
