/**
 * Theme App Extension Routes
 * 
 * Manage Theme App Extensions via API:
 * - Create/update app blocks
 * - Manage product badges via metafields
 * - Reorder products via collection updates
 * - Apply styling via theme settings/metafields
 */

const express = require('express');
const router = express.Router();

const SHOPIFY_SHOP_DOMAIN = process.env.SHOPIFY_SHOP_DOMAIN;
const SHOPIFY_ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const SHOPIFY_API_VERSION = process.env.SHOPIFY_API_VERSION || '2025-01';

/**
 * Helper: Make Shopify GraphQL request
 */
async function shopifyGraphQL(query, variables = {}) {
  const url = `https://${SHOPIFY_SHOP_DOMAIN}/admin/api/${SHOPIFY_API_VERSION}/graphql.json`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN
    },
    body: JSON.stringify({ query, variables })
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Shopify API error: ${response.status} - ${error}`);
  }

  const data = await response.json();
  
  if (data.errors) {
    throw new Error(`GraphQL errors: ${JSON.stringify(data.errors)}`);
  }

  return data.data;
}

/**
 * Helper: Make Shopify REST request
 */
async function shopifyREST(endpoint, method = 'GET', body = null) {
  const url = `https://${SHOPIFY_SHOP_DOMAIN}/admin/api/${SHOPIFY_API_VERSION}/${endpoint}`;

  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN
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

/**
 * POST /api/theme-extensions/product-badge
 * Add product badge via metafield
 */
router.post('/product-badge', async (req, res) => {
  try {
    const { productId, badgeType, badgeText } = req.body;

    if (!productId || !badgeType) {
      return res.status(400).json({
        success: false,
        error: 'productId and badgeType are required'
      });
    }

    // Create metafield for product badge
    const mutation = `
      mutation CreateProductBadgeMetafield($metafields: [MetafieldsSetInput!]!) {
        metafieldsSet(metafields: $metafields) {
          metafields {
            id
            namespace
            key
            value
            type
          }
          userErrors {
            field
            message
          }
        }
      }
    `;

    const badgeValue = JSON.stringify({
      type: badgeType,
      text: badgeText || getDefaultBadgeText(badgeType),
      visible: true,
      addedAt: new Date().toISOString()
    });

    const variables = {
      metafields: [
        {
          ownerId: productId,
          namespace: 'trending_ui',
          key: 'badge',
          value: badgeValue,
          type: 'json'
        }
      ]
    };

    const result = await shopifyGraphQL(mutation, variables);

    if (result.metafieldsSet.userErrors.length > 0) {
      throw new Error(JSON.stringify(result.metafieldsSet.userErrors));
    }

    res.json({
      success: true,
      productId,
      badge: {
        type: badgeType,
        text: badgeText || getDefaultBadgeText(badgeType),
        metafield: result.metafieldsSet.metafields[0]
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/theme-extensions/product-badge/:productId
 * Get product badge metafield
 */
router.get('/product-badge/:productId', async (req, res) => {
  try {
    const { productId } = req.params;

    const query = `
      query GetProductBadge($id: ID!) {
        product(id: $id) {
          id
          metafield(namespace: "trending_ui", key: "badge") {
            id
            value
            type
          }
        }
      }
    `;

    const result = await shopifyGraphQL(query, { id: productId });

    if (!result.product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    const badge = result.product.metafield
      ? JSON.parse(result.product.metafield.value)
      : null;

    res.json({
      success: true,
      productId,
      badge
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/theme-extensions/product-styling
 * Set product styling via metafield
 */
router.post('/product-styling', async (req, res) => {
  try {
    const { productId, styleType, colorScheme, className } = req.body;

    if (!productId || !styleType) {
      return res.status(400).json({
        success: false,
        error: 'productId and styleType are required'
      });
    }

    const stylingValue = JSON.stringify({
      style: styleType,
      colorScheme: colorScheme || getColorForStyle(styleType),
      className: className || `product-${styleType}`,
      updatedAt: new Date().toISOString()
    });

    const mutation = `
      mutation CreateProductStylingMetafield($metafields: [MetafieldsSetInput!]!) {
        metafieldsSet(metafields: $metafields) {
          metafields {
            id
            namespace
            key
            value
          }
          userErrors {
            field
            message
          }
        }
      }
    `;

    const variables = {
      metafields: [
        {
          ownerId: productId,
          namespace: 'trending_ui',
          key: 'styling',
          value: stylingValue,
          type: 'json'
        }
      ]
    };

    const result = await shopifyGraphQL(mutation, variables);

    if (result.metafieldsSet.userErrors.length > 0) {
      throw new Error(JSON.stringify(result.metafieldsSet.userErrors));
    }

    res.json({
      success: true,
      productId,
      styling: JSON.parse(stylingValue)
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/theme-extensions/collection-order
 * Set product order for a collection via metafield
 */
router.post('/collection-order', async (req, res) => {
  try {
    const { collectionId, productIds, orderBy } = req.body;

    if (!collectionId || !productIds || !Array.isArray(productIds)) {
      return res.status(400).json({
        success: false,
        error: 'collectionId and productIds array are required'
      });
    }

    const orderValue = JSON.stringify({
      productIds,
      orderBy: orderBy || 'trending',
      updatedAt: new Date().toISOString()
    });

    const mutation = `
      mutation CreateCollectionOrderMetafield($metafields: [MetafieldsSetInput!]!) {
        metafieldsSet(metafields: $metafields) {
          metafields {
            id
            namespace
            key
            value
          }
          userErrors {
            field
            message
          }
        }
      }
    `;

    const variables = {
      metafields: [
        {
          ownerId: collectionId,
          namespace: 'trending_ui',
          key: 'product_order',
          value: orderValue,
          type: 'json'
        }
      ]
    };

    const result = await shopifyGraphQL(mutation, variables);

    if (result.metafieldsSet.userErrors.length > 0) {
      throw new Error(JSON.stringify(result.metafieldsSet.userErrors));
    }

    res.json({
      success: true,
      collectionId,
      order: {
        productIds,
        orderBy: orderBy || 'trending',
        productCount: productIds.length
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/theme-extensions/products-with-ui
 * Get products with UI state (badges, styling) from metafields
 */
router.get('/products-with-ui', async (req, res) => {
  try {
    const { limit = 50 } = req.query;

    const query = `
      query GetProductsWithUI($first: Int!) {
        products(first: $first) {
          edges {
            node {
              id
              title
              handle
              tags
              metafields(first: 20, namespace: "trending_ui") {
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
        }
      }
    `;

    const result = await shopifyGraphQL(query, { first: parseInt(limit) });

    const products = result.products.edges.map(edge => {
      const product = edge.node;
      const metafields = product.metafields.edges.reduce((acc, mf) => {
        acc[mf.node.key] = JSON.parse(mf.node.value);
        return acc;
      }, {});

      return {
        id: product.id,
        title: product.title,
        handle: product.handle,
        tags: product.tags,
        ui: {
          badge: metafields.badge || null,
          styling: metafields.styling || null
        }
      };
    });

    res.json({
      success: true,
      products,
      count: products.length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/theme-extensions/collection/:collectionId/products
 * Get products in collection with UI state and ordering
 */
router.get('/collection/:collectionId/products', async (req, res) => {
  try {
    const { collectionId } = req.params;

    // Get collection order metafield
    const collectionQuery = `
      query GetCollectionOrder($id: ID!) {
        collection(id: $id) {
          id
          title
          metafield(namespace: "trending_ui", key: "product_order") {
            value
          }
          products(first: 250) {
            edges {
              node {
                id
                title
                handle
                tags
                metafields(first: 20, namespace: "trending_ui") {
                  edges {
                    node {
                      key
                      value
                    }
                  }
                }
              }
            }
          }
        }
      }
    `;

    const result = await shopifyGraphQL(collectionQuery, { id: collectionId });

    if (!result.collection) {
      return res.status(404).json({
        success: false,
        error: 'Collection not found'
      });
    }

    // Parse order if exists
    const order = result.collection.metafield
      ? JSON.parse(result.collection.metafield.value)
      : null;

    // Map products with UI state
    const products = result.collection.products.edges.map(edge => {
      const product = edge.node;
      const metafields = product.metafields.edges.reduce((acc, mf) => {
        acc[mf.node.key] = JSON.parse(mf.node.value);
        return acc;
      }, {});

      return {
        id: product.id,
        title: product.title,
        handle: product.handle,
        tags: product.tags,
        ui: {
          badge: metafields.badge || null,
          styling: metafields.styling || null
        },
        // Calculate position based on order
        position: order?.productIds?.indexOf(product.id) ?? -1
      };
    });

    // Sort by order if exists
    if (order && order.productIds) {
      products.sort((a, b) => {
        const aPos = order.productIds.indexOf(a.id);
        const bPos = order.productIds.indexOf(b.id);
        if (aPos === -1 && bPos === -1) return 0;
        if (aPos === -1) return 1;
        if (bPos === -1) return -1;
        return aPos - bPos;
      });
    }

    res.json({
      success: true,
      collectionId,
      order: order?.orderBy || null,
      products,
      count: products.length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * DELETE /api/theme-extensions/product-badge/:productId
 * Remove product badge metafield
 */
router.delete('/product-badge/:productId', async (req, res) => {
  try {
    const { productId } = req.params;

    // First get the metafield ID
    const query = `
      query GetProductBadge($id: ID!) {
        product(id: $id) {
          metafield(namespace: "trending_ui", key: "badge") {
            id
          }
        }
      }
    `;

    const result = await shopifyGraphQL(query, { id: productId });

    if (!result.product?.metafield) {
      return res.status(404).json({
        success: false,
        error: 'Badge metafield not found'
      });
    }

    // Delete metafield
    const mutation = `
      mutation DeleteMetafield($id: ID!) {
        metafieldDelete(metafieldId: $id) {
          deletedId
          userErrors {
            field
            message
          }
        }
      }
    `;

    const deleteResult = await shopifyGraphQL(mutation, { id: result.product.metafield.id });

    if (deleteResult.metafieldDelete.userErrors.length > 0) {
      throw new Error(JSON.stringify(deleteResult.metafieldDelete.userErrors));
    }

    res.json({
      success: true,
      productId,
      message: 'Badge removed'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Helper functions
function getDefaultBadgeText(badgeType) {
  const badges = {
    trending: '🔥 Trending',
    hot: '🔥 Hot',
    new: '✨ New',
    popular: '⭐ Popular',
    limited: '⏰ Limited'
  };
  return badges[badgeType] || 'Badge';
}

function getColorForStyle(styleType) {
  const colors = {
    luxury: '#2C2C2C',
    hero: '#FF6B6B',
    minimal: '#F5F5F5',
    urgent: '#FFB800'
  };
  return colors[styleType] || '#667EEA';
}

module.exports = router;
