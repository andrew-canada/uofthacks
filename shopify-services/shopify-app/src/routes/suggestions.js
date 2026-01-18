const express = require('express');

const { shopifyRequest } = require('../lib/shopifyClient');
const suggestionStore = require('../services/storage/suggestionStore');

const router = express.Router();

router.get('/', (req, res) => {
  res.json({
    success: true,
    suggestions: suggestionStore.getAll()
  });
});

router.post('/', async (req, res) => {
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
      type,
      data,
      status: 'pending',
      createdAt: new Date().toISOString()
    };

    suggestionStore.addSuggestion(suggestion);

    return res.json({
      success: true,
      suggestion
    });
  } catch (error) {
    console.error('Error creating suggestion:', error);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.post('/:id/accept', async (req, res) => {
  try {
    const { id } = req.params;
    const suggestion = suggestionStore.findById(id);

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

    switch (suggestion.type) {
      case 'new-product':
        result = await shopifyRequest('products.json', 'POST', {
          product: suggestion.data.product
        });
        suggestion.appliedData = result.product;
        break;

      case 'price-change':
        result = await shopifyRequest(`products/${suggestion.data.productId}.json`, 'PUT', {
          product: {
            variants: [{
              id: suggestion.data.variantId,
              price: suggestion.data.newPrice
            }]
          }
        });
        suggestion.appliedData = result.product;
        break;

      case 'description-change':
        result = await shopifyRequest(`products/${suggestion.data.productId}.json`, 'PUT', {
          product: {
            body_html: suggestion.data.newDescription
          }
        });
        suggestion.appliedData = result.product;
        break;

      case 'replace-product': {
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
        const collectsData = await shopifyRequest(`collects.json?product_id=${suggestion.data.productIdToReplace}&limit=250`, 'GET');
        const collectionIds = collectsData.collects.map((collect) => collect.collection_id);

        for (const collect of collectsData.collects) {
          await shopifyRequest(`collects/${collect.id}.json`, 'DELETE');
        }

        for (const collectionId of collectionIds) {
          await shopifyRequest('collects.json', 'POST', {
            collect: {
              product_id: newProductId,
              collection_id: collectionId
            }
          });
        }

        await shopifyRequest(`products/${suggestion.data.productIdToReplace}.json`, 'DELETE');

        suggestion.appliedData = {
          newProductId,
          oldProductId: suggestion.data.productIdToReplace,
          collectionsUpdated: collectionIds.length
        };
        break;
      }

      default:
        return res.status(400).json({
          success: false,
          error: 'Unknown suggestion type'
        });
    }

    suggestion.status = 'accepted';
    suggestion.acceptedAt = new Date().toISOString();

    return res.json({
      success: true,
      suggestion,
      message: 'Suggestion applied successfully'
    });
  } catch (error) {
    console.error('Error accepting suggestion:', error);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.post('/:id/reject', (req, res) => {
  try {
    const { id } = req.params;
    const suggestion = suggestionStore.findById(id);

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

    return res.json({
      success: true,
      suggestion,
      message: 'Suggestion rejected'
    });
  } catch (error) {
    console.error('Error rejecting suggestion:', error);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.delete('/:id', (req, res) => {
  try {
    const { id } = req.params;
    const removed = suggestionStore.removeById(id);

    if (!removed) {
      return res.status(404).json({
        success: false,
        error: 'Suggestion not found'
      });
    }

    return res.json({
      success: true,
      message: 'Suggestion deleted'
    });
  } catch (error) {
    console.error('Error deleting suggestion:', error);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.post('/generate', async (req, res) => {
  try {
    const generatedSuggestions = await generateAutoSuggestions();

    return res.json({
      success: true,
      suggestions: generatedSuggestions,
      message: `Generated ${generatedSuggestions.length} suggestions`
    });
  } catch (error) {
    console.error('Error generating suggestions:', error);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

async function generateAutoSuggestions() {
  const productsData = await shopifyRequest('products.json?limit=250', 'GET');
  const products = productsData.products;

  if (products.length === 0) {
    throw new Error('No products available');
  }

  const generatedSuggestions = [];
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

  const productForPrice = products[Math.floor(Math.random() * products.length)];
  if (productForPrice.variants && productForPrice.variants.length > 0) {
    const variant = productForPrice.variants[0];
    const currentPrice = parseFloat(variant.price);
    const newPrice = (currentPrice * 0.9).toFixed(2);

    generatedSuggestions.push({
      id: Date.now().toString() + '-2',
      type: 'price-change',
      data: {
        productId: productForPrice.id,
        variantId: variant.id,
        productTitle: productForPrice.title,
        currentPrice,
        newPrice,
        reason: '10% discount to boost sales'
      },
      status: 'pending',
      createdAt: new Date().toISOString()
    });
  }

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

  suggestionStore.addMany(generatedSuggestions);
  return generatedSuggestions;
}

async function initializeSuggestions() {
  try {
    console.log('🔄 Generating initial suggestions...');
    await generateAutoSuggestions();
    console.log(`✅ Generated ${suggestionStore.getAll().length} initial suggestions`);
  } catch (error) {
    console.error('❌ Error generating initial suggestions:', error.message);
  }
}

module.exports = router;
module.exports.initializeSuggestions = initializeSuggestions;
