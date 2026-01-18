const express = require('express');

const { shopifyRequest } = require('../lib/shopifyClient');

const router = express.Router();

router.post('/replace-product', async (req, res) => {
  try {
    const { currentProductId, replacementProductId, collectionId } = req.body;

    if (!currentProductId || !replacementProductId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: currentProductId and replacementProductId'
      });
    }

    if (collectionId) {
      try {
        await shopifyRequest(`collects.json?product_id=${currentProductId}&collection_id=${collectionId}`, 'GET')
          .then(async (data) => {
            if (data.collects && data.collects.length > 0) {
              const collectId = data.collects[0].id;
              await shopifyRequest(`collects/${collectId}.json`, 'DELETE');
            }
          });
      } catch (error) {
        console.log('Product not in collection or already removed:', error.message);
      }

      try {
        await shopifyRequest('collects.json', 'POST', {
          collect: {
            product_id: replacementProductId,
            collection_id: collectionId
          }
        });
      } catch (error) {
        console.log('Error adding product to collection:', error.message);
      }
    }

    const replacementProduct = await shopifyRequest(`products/${replacementProductId}.json`, 'GET');

    return res.json({
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
    return res.status(500).json({
      success: false,
      error: error.message,
      details: error
    });
  }
});

router.get('/collections', async (req, res) => {
  try {
    const data = await shopifyRequest('custom_collections.json', 'GET');

    return res.json({
      success: true,
      collections: data.custom_collections
    });
  } catch (error) {
    console.error('Error fetching collections:', error);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/products', async (req, res) => {
  try {
    const data = await shopifyRequest('products.json?limit=250', 'GET');

    return res.json({
      success: true,
      products: data.products
    });
  } catch (error) {
    console.error('Error fetching products:', error);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.post('/create-and-replace', async (req, res) => {
  try {
    const { productIdToReplace } = req.body;

    if (!productIdToReplace) {
      return res.status(400).json({
        success: false,
        error: 'Missing required field: productIdToReplace'
      });
    }

    const newProduct = await shopifyRequest('products.json', 'POST', {
      product: {
        title: 'Classic Leather Shoes',
        body_html: '<p>Premium quality leather shoes - placeholder product</p>',
        vendor: 'Trending Shoes',
        product_type: 'Shoes',
        tags: ['shoes', 'placeholder', 'trending'],
        status: 'active'
      }
    });

    const newProductId = newProduct.product.id;
    const collectsData = await shopifyRequest(`collects.json?product_id=${productIdToReplace}&limit=250`, 'GET');
    const collectionIds = collectsData.collects.map((collect) => collect.collection_id);

    for (const collect of collectsData.collects) {
      try {
        await shopifyRequest(`collects/${collect.id}.json`, 'DELETE');
      } catch (error) {
        console.log(`Error removing from collection ${collect.collection_id}:`, error.message);
      }
    }

    for (const collectionId of collectionIds) {
      try {
        await shopifyRequest('collects.json', 'POST', {
          collect: {
            product_id: newProductId,
            collection_id: collectionId
          }
        });
      } catch (error) {
        console.log(`Error adding to collection ${collectionId}:`, error.message);
      }
    }

    try {
      await shopifyRequest(`products/${productIdToReplace}.json`, 'DELETE');
    } catch (error) {
      console.log('Error deleting old product:', error.message);
    }

    return res.json({
      success: true,
      message: 'Product replaced successfully',
      data: {
        oldProductId: productIdToReplace,
        newProductId,
        collectionsUpdated: collectionIds.length,
        newProduct: newProduct.product
      }
    });
  } catch (error) {
    console.error('Error creating and replacing product:', error);
    return res.status(500).json({
      success: false,
      error: error.message,
      details: error
    });
  }
});

module.exports = router;
