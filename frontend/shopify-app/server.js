const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Serve static files from 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Shopify configuration
const SHOPIFY_SHOP_DOMAIN = process.env.SHOPIFY_SHOP_DOMAIN;
const SHOPIFY_ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const SHOPIFY_API_VERSION = '2025-01';

// In-memory storage for suggestions
let suggestions = [];

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

// ====== SUGGESTION SYSTEM ENDPOINTS ======

// Get all suggestions
app.get('/api/suggestions', (req, res) => {
  res.json({
    success: true,
    suggestions: suggestions
  });
});

// Create a new suggestion
app.post('/api/suggestions', async (req, res) => {
  try {
    const { type, data } = req.body;

    if (!type || !data) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: type and data'
      });
    }

    const suggestion = {
      id: Date.now().toString(),
      type, // 'new-product', 'price-change', 'description-change', 'replace-product'
      data,
      status: 'pending', // 'pending', 'accepted', 'rejected'
      createdAt: new Date().toISOString()
    };

    suggestions.push(suggestion);

    res.json({
      success: true,
      suggestion
    });

  } catch (error) {
    console.error('Error creating suggestion:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Accept a suggestion (apply it)
app.post('/api/suggestions/:id/accept', async (req, res) => {
  try {
    const { id } = req.params;
    const suggestion = suggestions.find(s => s.id === id);

    if (!suggestion) {
      return res.status(404).json({
        success: false,
        error: 'Suggestion not found'
      });
    }

    if (suggestion.status !== 'pending') {
      return res.status(400).json({
        success: false,
        error: 'Suggestion has already been processed'
      });
    }

    let result;

    // Apply the suggestion based on type
    switch (suggestion.type) {
      case 'new-product':
        result = await shopifyRequest('products.json', 'POST', {
          product: suggestion.data.product
        });
        suggestion.appliedData = result.product;
        break;

      case 'price-change':
        const priceUpdateData = {
          product: {
            variants: [{
              id: suggestion.data.variantId,
              price: suggestion.data.newPrice
            }]
          }
        };
        result = await shopifyRequest(`products/${suggestion.data.productId}.json`, 'PUT', priceUpdateData);
        suggestion.appliedData = result.product;
        break;

      case 'description-change':
        const descUpdateData = {
          product: {
            body_html: suggestion.data.newDescription
          }
        };
        result = await shopifyRequest(`products/${suggestion.data.productId}.json`, 'PUT', descUpdateData);
        suggestion.appliedData = result.product;
        break;

      case 'replace-product':
        // Create new shoe product
        const newProduct = await shopifyRequest('products.json', 'POST', {
          product: {
            title: suggestion.data.newProduct.title || 'Classic Leather Shoes',
            body_html: suggestion.data.newProduct.description || '<p>Premium quality leather shoes</p>',
            vendor: suggestion.data.newProduct.vendor || 'Trending Shoes',
            product_type: 'Shoes',
            tags: ['shoes', 'suggested'],
            status: 'active'
          }
        });

        const newProductId = newProduct.product.id;

        // Get old product's collections
        const collectsData = await shopifyRequest(`collects.json?product_id=${suggestion.data.productIdToReplace}&limit=250`, 'GET');
        const collectionIds = collectsData.collects.map(collect => collect.collection_id);

        // Remove old product from collections
        for (const collect of collectsData.collects) {
          await shopifyRequest(`collects/${collect.id}.json`, 'DELETE');
        }

        // Add new product to collections
        for (const collectionId of collectionIds) {
          await shopifyRequest('collects.json', 'POST', {
            collect: {
              product_id: newProductId,
              collection_id: collectionId
            }
          });
        }

        // Delete old product
        await shopifyRequest(`products/${suggestion.data.productIdToReplace}.json`, 'DELETE');

        suggestion.appliedData = {
          newProductId,
          oldProductId: suggestion.data.productIdToReplace,
          collectionsUpdated: collectionIds.length
        };
        break;

      default:
        return res.status(400).json({
          success: false,
          error: 'Unknown suggestion type'
        });
    }

    suggestion.status = 'accepted';
    suggestion.acceptedAt = new Date().toISOString();

    res.json({
      success: true,
      suggestion,
      message: 'Suggestion applied successfully'
    });

  } catch (error) {
    console.error('Error accepting suggestion:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Reject a suggestion
app.post('/api/suggestions/:id/reject', (req, res) => {
  try {
    const { id } = req.params;
    const suggestion = suggestions.find(s => s.id === id);

    if (!suggestion) {
      return res.status(404).json({
        success: false,
        error: 'Suggestion not found'
      });
    }

    if (suggestion.status !== 'pending') {
      return res.status(400).json({
        success: false,
        error: 'Suggestion has already been processed'
      });
    }

    suggestion.status = 'rejected';
    suggestion.rejectedAt = new Date().toISOString();

    res.json({
      success: true,
      suggestion,
      message: 'Suggestion rejected'
    });

  } catch (error) {
    console.error('Error rejecting suggestion:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Delete a suggestion
app.delete('/api/suggestions/:id', (req, res) => {
  try {
    const { id } = req.params;
    const index = suggestions.findIndex(s => s.id === id);

    if (index === -1) {
      return res.status(404).json({
        success: false,
        error: 'Suggestion not found'
      });
    }

    suggestions.splice(index, 1);

    res.json({
      success: true,
      message: 'Suggestion deleted'
    });

  } catch (error) {
    console.error('Error deleting suggestion:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Generate auto-suggestions (helper endpoint)
app.post('/api/suggestions/generate', async (req, res) => {
  try {
    const productsData = await shopifyRequest('products.json?limit=250', 'GET');
    const products = productsData.products;

    if (products.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No products available'
      });
    }

    const generatedSuggestions = [];

    // Generate a random product replacement suggestion
    const randomProduct = products[Math.floor(Math.random() * products.length)];
    generatedSuggestions.push({
      id: Date.now().toString() + '-1',
      type: 'replace-product',
      data: {
        productIdToReplace: randomProduct.id,
        productTitle: randomProduct.title,
        newProduct: {
          title: 'Classic Leather Shoes',
          description: '<p>Premium quality leather shoes - trending now!</p>',
          vendor: 'Trending Shoes'
        }
      },
      status: 'pending',
      createdAt: new Date().toISOString()
    });

    // Generate a price change suggestion
    const productForPrice = products[Math.floor(Math.random() * products.length)];
    if (productForPrice.variants && productForPrice.variants.length > 0) {
      const variant = productForPrice.variants[0];
      const currentPrice = parseFloat(variant.price);
      const newPrice = (currentPrice * 0.9).toFixed(2); // 10% discount

      generatedSuggestions.push({
        id: Date.now().toString() + '-2',
        type: 'price-change',
        data: {
          productId: productForPrice.id,
          variantId: variant.id,
          productTitle: productForPrice.title,
          currentPrice: currentPrice,
          newPrice: newPrice,
          reason: '10% discount to boost sales'
        },
        status: 'pending',
        createdAt: new Date().toISOString()
      });
    }

    // Generate a new product suggestion
    generatedSuggestions.push({
      id: Date.now().toString() + '-3',
      type: 'new-product',
      data: {
        product: {
          title: 'Trendy Sneakers Collection',
          body_html: '<p>New arrival! Limited edition sneakers based on current trends.</p>',
          vendor: 'Fashion Forward',
          product_type: 'Shoes',
          tags: ['new', 'trending', 'sneakers', 'limited-edition'],
          status: 'active'
        }
      },
      status: 'pending',
      createdAt: new Date().toISOString()
    });

    // Add all generated suggestions to the list
    suggestions.push(...generatedSuggestions);

    res.json({
      success: true,
      suggestions: generatedSuggestions,
      message: `Generated ${generatedSuggestions.length} suggestions`
    });

  } catch (error) {
    console.error('Error generating suggestions:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Auto-generate initial suggestions on startup
async function initializeSuggestions() {
  try {
    console.log('🔄 Generating initial suggestions...');
    const productsData = await shopifyRequest('products.json?limit=250', 'GET');
    const products = productsData.products;

    if (products.length === 0) {
      console.log('⚠️  No products found in store');
      return;
    }

    // Generate a random product replacement suggestion
    const randomProduct = products[Math.floor(Math.random() * products.length)];
    suggestions.push({
      id: Date.now().toString() + '-1',
      type: 'replace-product',
      data: {
        productIdToReplace: randomProduct.id,
        productTitle: randomProduct.title,
        newProduct: {
          title: 'Classic Leather Shoes',
          description: '<p>Premium quality leather shoes - trending now!</p>',
          vendor: 'Trending Shoes'
        }
      },
      status: 'pending',
      createdAt: new Date().toISOString()
    });

    // Generate a price change suggestion
    const productForPrice = products[Math.floor(Math.random() * products.length)];
    if (productForPrice.variants && productForPrice.variants.length > 0) {
      const variant = productForPrice.variants[0];
      const currentPrice = parseFloat(variant.price);
      const newPrice = (currentPrice * 0.9).toFixed(2);

      suggestions.push({
        id: Date.now().toString() + '-2',
        type: 'price-change',
        data: {
          productId: productForPrice.id,
          variantId: variant.id,
          productTitle: productForPrice.title,
          currentPrice: currentPrice,
          newPrice: newPrice,
          reason: '10% discount to boost sales'
        },
        status: 'pending',
        createdAt: new Date().toISOString()
      });
    }

    // Generate a new product suggestion
    suggestions.push({
      id: Date.now().toString() + '-3',
      type: 'new-product',
      data: {
        product: {
          title: 'Trendy Sneakers Collection',
          body_html: '<p>New arrival! Limited edition sneakers based on current trends.</p>',
          vendor: 'Fashion Forward',
          product_type: 'Shoes',
          tags: ['new', 'trending', 'sneakers', 'limited-edition'],
          status: 'active'
        }
      },
      status: 'pending',
      createdAt: new Date().toISOString()
    });

    console.log(`✅ Generated ${suggestions.length} initial suggestions`);
  } catch (error) {
    console.error('❌ Error generating initial suggestions:', error.message);
  }
}

app.listen(PORT, async () => {
  console.log(`\n🚀 Product Suggestions API running on port ${PORT}`);
  console.log(`📍 Shop: ${process.env.SHOPIFY_SHOP_DOMAIN}`);
  console.log(`\nEndpoints:`);
  console.log(`  GET  /health - Health check`);
  console.log(`  POST /api/replace-product - Replace product in collection`);
  console.log(`  POST /api/create-and-replace - Create shoe and replace product in all collections`);
  console.log(`  GET  /api/collections - Get all collections`);
  console.log(`  GET  /api/products - Get all products`);
  console.log(`\n  === Suggestion System ===`);
  console.log(`  GET    /api/suggestions - Get all suggestions`);
  console.log(`  POST   /api/suggestions - Create a new suggestion`);
  console.log(`  POST   /api/suggestions/generate - Generate auto-suggestions`);
  console.log(`  POST   /api/suggestions/:id/accept - Accept a suggestion`);
  console.log(`  POST   /api/suggestions/:id/reject - Reject a suggestion`);
  console.log(`  DELETE /api/suggestions/:id - Delete a suggestion`);

  // Generate initial suggestions only if token is configured
  if (SHOPIFY_ACCESS_TOKEN && SHOPIFY_ACCESS_TOKEN !== 'your_access_token_here') {
    await initializeSuggestions();
  } else {
    console.log('⚠️  SHOPIFY_ACCESS_TOKEN not configured - skipping initial suggestions');
    console.log('   Configure the token in Render environment variables to enable automatic suggestions');
  }

  console.log(`\n🌐 Access the app at:`);
  console.log(`   Admin: http://localhost:${PORT}/admin.html`);
  console.log(`   Public: http://localhost:${PORT}/suggestions.html`);
});
