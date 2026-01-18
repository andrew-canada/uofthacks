/**
 * UI Modification Routes
 * 
 * Endpoints for modifying product UI:
 * - Adding trending badges
 * - Reordering products
 * - Updating product styling
 */

const express = require('express');
const router = express.Router();

// In-memory storage for UI state
const uiState = {
  badges: {}, // productId -> badge data
  productOrder: {}, // collectionId -> ordered product IDs
  styling: {} // productId -> styling data
};

/**
 * POST /api/products/:productId/badge
 * Add a badge to a product
 */
router.post('/products/:productId/badge', (req, res) => {
  try {
    const { productId } = req.params;
    const { badge } = req.body;

    if (!badge || !badge.type) {
      return res.status(400).json({
        success: false,
        error: 'Badge type is required'
      });
    }

    uiState.badges[productId] = {
      ...badge,
      productId,
      addedAt: new Date().toISOString(),
      visible: badge.visible !== false
    };

    res.json({
      success: true,
      productId,
      badge: uiState.badges[productId]
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/products/:productId/badge
 * Get badge for a product
 */
router.get('/products/:productId/badge', (req, res) => {
  const { productId } = req.params;
  const badge = uiState.badges[productId];

  if (!badge) {
    return res.status(404).json({
      success: false,
      error: 'Badge not found for this product'
    });
  }

  res.json({
    success: true,
    badge
  });
});

/**
 * DELETE /api/products/:productId/badge
 * Remove badge from product
 */
router.delete('/products/:productId/badge', (req, res) => {
  const { productId } = req.params;
  
  if (uiState.badges[productId]) {
    delete uiState.badges[productId];
    res.json({
      success: true,
      message: 'Badge removed'
    });
  } else {
    res.status(404).json({
      success: false,
      error: 'Badge not found'
    });
  }
});

/**
 * POST /api/products/order
 * Set product ordering for collections
 */
router.post('/products/order', (req, res) => {
  try {
    const { collectionId, productIds, orderBy } = req.body;

    if (!productIds || !Array.isArray(productIds)) {
      return res.status(400).json({
        success: false,
        error: 'productIds array is required'
      });
    }

    const key = collectionId || 'default';
    uiState.productOrder[key] = {
      productIds,
      orderBy: orderBy || 'custom',
      updatedAt: new Date().toISOString()
    };

    res.json({
      success: true,
      collectionId: key,
      productCount: productIds.length,
      order: uiState.productOrder[key]
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/products/order
 * Get product ordering for collection
 */
router.get('/products/order', (req, res) => {
  const { collectionId } = req.query;
  const key = collectionId || 'default';
  const order = uiState.productOrder[key];

  if (!order) {
    return res.json({
      success: true,
      order: null,
      message: 'No custom ordering set'
    });
  }

  res.json({
    success: true,
    order
  });
});

/**
 * POST /api/products/:productId/styling
 * Update product styling
 */
router.post('/products/:productId/styling', (req, res) => {
  try {
    const { productId } = req.params;
    const { style, colorScheme, css, className } = req.body;

    uiState.styling[productId] = {
      productId,
      style: style || 'hero',
      colorScheme: colorScheme || null,
      css: css || null,
      className: className || `product-${style || 'hero'}`,
      updatedAt: new Date().toISOString()
    };

    res.json({
      success: true,
      productId,
      styling: uiState.styling[productId]
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/products/:productId/styling
 * Get product styling
 */
router.get('/products/:productId/styling', (req, res) => {
  const { productId } = req.params;
  const styling = uiState.styling[productId];

  if (!styling) {
    return res.json({
      success: true,
      styling: null,
      message: 'No custom styling set'
    });
  }

  res.json({
    success: true,
    styling
  });
});

/**
 * GET /api/ui/state
 * Get all UI state (badges, order, styling)
 */
router.get('/ui/state', (req, res) => {
  res.json({
    success: true,
    state: {
      badges: uiState.badges,
      productOrder: uiState.productOrder,
      styling: uiState.styling,
      counts: {
        badges: Object.keys(uiState.badges).length,
        orderedCollections: Object.keys(uiState.productOrder).length,
        styledProducts: Object.keys(uiState.styling).length
      }
    }
  });
});

/**
 * GET /api/products/with-ui
 * Get products with UI state (badges, styling) applied
 */
router.get('/products/with-ui', async (req, res) => {
  try {
    // Get products from Shopify
    const productsResponse = await fetch(
      `https://${process.env.SHOPIFY_SHOP_DOMAIN}/admin/api/2025-01/products.json?limit=250`,
      {
        headers: {
          'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!productsResponse.ok) {
      throw new Error('Failed to fetch products');
    }

    const productsData = await productsResponse.json();
    const products = productsData.products || [];

    // Enrich products with UI state
    const enrichedProducts = products.map(product => {
      const productId = product.id.toString();
      return {
        ...product,
        ui: {
          badge: uiState.badges[productId] || null,
          styling: uiState.styling[productId] || null
        }
      };
    });

    res.json({
      success: true,
      products: enrichedProducts,
      uiState: {
        badgesCount: Object.keys(uiState.badges).length,
        styledCount: Object.keys(uiState.styling).length
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;
