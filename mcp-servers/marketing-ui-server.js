#!/usr/bin/env node
/**
 * MCP Server for Marketing & UI Modifications
 * 
 * Exposes marketing generator functions and UI modification tools
 * to Cursor AI assistant via Model Context Protocol.
 * 
 * This server provides:
 * - Access to backend marketing generator service
 * - Tools to modify product UI (badges, ordering, styling)
 * - Functions to apply trending badges and reorder products
 */

const { spawn } = require('child_process');
const path = require('path');

// Configuration
const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://localhost:5000';
const FRONTEND_API_URL = process.env.FRONTEND_API_URL || 'http://localhost:3000';

// MCP Server Implementation
class MarketingUIServer {
  constructor() {
    this.serverName = 'uofthacks-marketing-ui';
  }

  /**
   * List available resources
   */
  listResources() {
    return [
      {
        uri: 'marketing://generator',
        name: 'Marketing Generator',
        description: 'Access to marketing content generation service',
        mimeType: 'application/json'
      },
      {
        uri: 'ui://products',
        name: 'Product UI State',
        description: 'Current product UI configuration and styling',
        mimeType: 'application/json'
      },
      {
        uri: 'ui://trending',
        name: 'Trending Products',
        description: 'Products with trending badges and ordering',
        mimeType: 'application/json'
      }
    ];
  }

  /**
   * List available tools
   */
  listTools() {
    return [
      {
        name: 'generate_marketing',
        description: 'Generate marketing content for a product using trends',
        inputSchema: {
          type: 'object',
          properties: {
            productId: {
              type: 'string',
              description: 'Product ID to generate marketing for'
            },
            trendId: {
              type: 'string',
              description: 'Optional trend ID to match against'
            }
          },
          required: ['productId']
        }
      },
      {
        name: 'add_trending_badge',
        description: 'Add a trending badge to a product in the UI',
        inputSchema: {
          type: 'object',
          properties: {
            productId: {
              type: 'string',
              description: 'Product ID to add badge to'
            },
            badgeType: {
              type: 'string',
              enum: ['trending', 'hot', 'new', 'popular', 'limited'],
              description: 'Type of badge to add'
            },
            badgeText: {
              type: 'string',
              description: 'Custom badge text (optional)'
            }
          },
          required: ['productId', 'badgeType']
        }
      },
      {
        name: 'reorder_products',
        description: 'Reorder products in UI - move trending products to the front',
        inputSchema: {
          type: 'object',
          properties: {
            collectionId: {
              type: 'string',
              description: 'Collection ID to reorder (optional, reorders all if not specified)'
            },
            orderBy: {
              type: 'string',
              enum: ['trending', 'popularity', 'price', 'newest'],
              description: 'Sort order for products'
            },
            limit: {
              type: 'number',
              description: 'Maximum number of products to show first'
            }
          },
          required: ['orderBy']
        }
      },
      {
        name: 'apply_marketing_to_product',
        description: 'Apply generated marketing content to a product',
        inputSchema: {
          type: 'object',
          properties: {
            productId: {
              type: 'string',
              description: 'Product ID'
            },
            marketingData: {
              type: 'object',
              description: 'Marketing data from generate_marketing tool'
            }
          },
          required: ['productId', 'marketingData']
        }
      },
      {
        name: 'get_trending_products',
        description: 'Get list of products with trending status',
        inputSchema: {
          type: 'object',
          properties: {
            platform: {
              type: 'string',
              description: 'Filter by platform (TikTok, Instagram, etc.)'
            },
            limit: {
              type: 'number',
              description: 'Maximum number of products to return'
            }
          }
        }
      },
      {
        name: 'update_product_styling',
        description: 'Update product UI styling based on trend and marketing data',
        inputSchema: {
          type: 'object',
          properties: {
            productId: {
              type: 'string',
              description: 'Product ID'
            },
            styleType: {
              type: 'string',
              enum: ['luxury', 'hero', 'minimal', 'urgent'],
              description: 'Layout style type'
            },
            colorScheme: {
              type: 'string',
              description: 'Color scheme to apply'
            }
          },
          required: ['productId', 'styleType']
        }
      }
    ];
  }

  /**
   * Call a tool
   */
  async callTool(toolName, arguments_) {
    switch (toolName) {
      case 'generate_marketing':
        return await this.generateMarketing(arguments_.productId, arguments_.trendId);
      
      case 'add_trending_badge':
        return await this.addTrendingBadge(arguments_.productId, arguments_.badgeType, arguments_.badgeText);
      
      case 'reorder_products':
        return await this.reorderProducts(arguments_.collectionId, arguments_.orderBy, arguments_.limit);
      
      case 'apply_marketing_to_product':
        return await this.applyMarketingToProduct(arguments_.productId, arguments_.marketingData);
      
      case 'get_trending_products':
        return await this.getTrendingProducts(arguments_.platform, arguments_.limit);
      
      case 'update_product_styling':
        return await this.updateProductStyling(arguments_.productId, arguments_.styleType, arguments_.colorScheme);
      
      default:
        throw new Error(`Unknown tool: ${toolName}`);
    }
  }

  /**
   * Generate marketing content via backend API
   */
  async generateMarketing(productId, trendId = null) {
    try {
      // First, analyze the product to get trend matches
      const analyzeUrl = `${BACKEND_API_URL}/api/products/${productId}/analyze`;
      const analyzeResponse = await fetch(analyzeUrl, { method: 'POST' });
      
      if (!analyzeResponse.ok) {
        throw new Error(`Failed to analyze product: ${analyzeResponse.statusText}`);
      }
      
      const analysis = await analyzeResponse.json();
      
      // Get marketing recommendations from analysis
      const recommendations = analysis.recommendations || {};
      
      return {
        success: true,
        productId,
        marketing: {
          title: recommendations.title || analysis.product?.title,
          description: recommendations.description || analysis.product?.description,
          description_html: recommendations.description_html,
          seo_title: recommendations.seo_title,
          seo_description: recommendations.seo_description,
          marketing_angle: recommendations.marketing_angle,
          suggested_tags: recommendations.suggested_tags || [],
          color_scheme: recommendations.color_scheme,
          layout_style: recommendations.layout_style || 'hero',
          trust_badges: recommendations.trust_badges || ['trending'],
          show_countdown: recommendations.show_countdown || false
        },
        trend_matches: analysis.trend_matches || []
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Add trending badge to product via Theme App Extension (metafield)
   */
  async addTrendingBadge(productId, badgeType, badgeText = null) {
    try {
      // Use theme extension API which stores badge in metafield
      const response = await fetch(`${THEME_EXTENSIONS_API}/product-badge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId,
          badgeType,
          badgeText: badgeText || this.getDefaultBadgeText(badgeType)
        })
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to add badge: ${error}`);
      }

      const result = await response.json();
      return {
        success: true,
        productId,
        badge: result.badge,
        note: 'Badge stored in metafield. Theme extension will display it automatically.'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Reorder products based on trending status via Theme App Extension (metafield)
   */
  async reorderProducts(collectionId = null, orderBy = 'trending', limit = null) {
    try {
      // Get products with UI state
      const productsUrl = `${THEME_EXTENSIONS_API}/products-with-ui?limit=${limit || 250}`;
      const productsResponse = await fetch(productsUrl);
      const productsData = await productsResponse.json();
      
      if (!productsData.success) {
        throw new Error(productsData.error || 'Failed to get products');
      }

      let products = productsData.products || [];

      // Sort products based on orderBy
      products = await this.sortProducts(products, orderBy);

      // Extract product IDs in order
      const productIds = products.map(p => p.id);

      // Store order in collection metafield via API
      if (collectionId) {
        const orderResponse = await fetch(`${THEME_EXTENSIONS_API}/collection-order`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            collectionId,
            productIds,
            orderBy
          })
        });

        if (!orderResponse.ok) {
          throw new Error('Failed to save collection order');
        }
      }

      return {
        success: true,
        collectionId,
        orderBy,
        productCount: productIds.length,
        productIds,
        note: collectionId 
          ? 'Product order stored in collection metafield. Theme extension will apply it automatically.'
          : 'Products sorted. Provide collectionId to store order in metafield.'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Sort products by criteria
   */
  async sortProducts(products, orderBy) {
    switch (orderBy) {
      case 'trending':
        // Sort by trending tag presence, then by popularity
        return products.sort((a, b) => {
          const aTrending = a.tags?.includes('trending') || false;
          const bTrending = b.tags?.includes('trending') || false;
          if (aTrending !== bTrending) return bTrending - aTrending;
          return (b.popularity || 0) - (a.popularity || 0);
        });
      
      case 'popularity':
        return products.sort((a, b) => (b.popularity || 0) - (a.popularity || 0));
      
      case 'price':
        return products.sort((a, b) => {
          const aPrice = parseFloat(a.variants?.[0]?.price || 0);
          const bPrice = parseFloat(b.variants?.[0]?.price || 0);
          return aPrice - bPrice;
        });
      
      case 'newest':
        return products.sort((a, b) => {
          const aDate = new Date(a.created_at || 0);
          const bDate = new Date(b.created_at || 0);
          return bDate - aDate;
        });
      
      default:
        return products;
    }
  }

  /**
   * Apply marketing data to product
   */
  async applyMarketingToProduct(productId, marketingData) {
    try {
      // Call backend API to apply recommendations
      const applyUrl = `${BACKEND_API_URL}/api/products/${productId}/apply`;
      const response = await fetch(applyUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recommendations: marketingData })
      });

      if (!response.ok) {
        throw new Error(`Failed to apply marketing: ${response.statusText}`);
      }

      const result = await response.json();
      return {
        success: true,
        productId,
        applied: result,
        ui_changes: {
          badge: marketingData.trust_badges?.[0] || null,
          style: marketingData.layout_style || 'hero',
          color: marketingData.color_scheme || null
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get trending products
   */
  async getTrendingProducts(platform = null, limit = 10) {
    try {
      // Get trends from backend
      const trendsUrl = platform 
        ? `${BACKEND_API_URL}/api/trends?platform=${platform}`
        : `${BACKEND_API_URL}/api/trends?top=${limit}`;
      
      const trendsResponse = await fetch(trendsUrl);
      const trendsData = await trendsResponse.json();

      // Get products
      const productsResponse = await fetch(`${FRONTEND_API_URL}/api/products`);
      const productsData = await productsResponse.json();
      const products = productsData.products || [];

      // Match products to trends
      const trendingProducts = products.filter(p => 
        p.tags?.includes('trending') || 
        trendsData.trends?.some(t => 
          p.title?.toLowerCase().includes(t.name?.toLowerCase())
        )
      ).slice(0, limit);

      return {
        success: true,
        platform,
        count: trendingProducts.length,
        products: trendingProducts.map(p => ({
          id: p.id,
          title: p.title,
          trending: true,
          badge: 'trending'
        }))
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Update product styling via Theme App Extension (metafield)
   */
  async updateProductStyling(productId, styleType, colorScheme = null) {
    try {
      // Store styling in metafield via theme extension API
      const response = await fetch(`${THEME_EXTENSIONS_API}/product-styling`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId,
          styleType,
          colorScheme: colorScheme || this.getColorForStyle(styleType),
          className: `product-${styleType}`
        })
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to update styling: ${error}`);
      }

      const result = await response.json();
      return {
        success: true,
        productId,
        styling: result.styling,
        note: 'Styling stored in metafield. Theme extension will apply it automatically.'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Helper: Get default badge text
   */
  getDefaultBadgeText(badgeType) {
    const badges = {
      trending: '🔥 Trending',
      hot: '🔥 Hot',
      new: '✨ New',
      popular: '⭐ Popular',
      limited: '⏰ Limited'
    };
    return badges[badgeType] || 'Badge';
  }

  /**
   * Helper: Get color for style type
   */
  getColorForStyle(styleType) {
    const colors = {
      luxury: '#2C2C2C',
      hero: '#FF6B6B',
      minimal: '#F5F5F5',
      urgent: '#FFB800'
    };
    return colors[styleType] || '#667EEA';
  }

  /**
   * Helper: Generate CSS for style type
   */
  generateStyleCSS(styleType, colorScheme) {
    const styles = {
      luxury: `
        .product-luxury {
          border: 1px solid ${colorScheme || '#2C2C2C'};
          padding: 20px;
          background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%);
        }
      `,
      hero: `
        .product-hero {
          border: 2px solid ${colorScheme || '#FF6B6B'};
          padding: 20px;
          background: #fff;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
      `,
      minimal: `
        .product-minimal {
          border: 1px solid #e0e0e0;
          padding: 20px;
          background: ${colorScheme || '#F5F5F5'};
        }
      `,
      urgent: `
        .product-urgent {
          border: 2px dashed ${colorScheme || '#FFB800'};
          padding: 20px;
          background: #fffaf0;
          animation: pulse 2s infinite;
        }
      `
    };
    return styles[styleType] || styles.hero;
  }

  /**
   * Read a resource
   */
  async readResource(uri) {
    if (uri === 'marketing://generator') {
      return JSON.stringify({
        service: 'Marketing Generator',
        backend_url: BACKEND_API_URL,
        available_methods: ['generate_marketing', 'apply_marketing_to_product']
      }, null, 2);
    }
    
    if (uri === 'ui://products') {
      try {
        const response = await fetch(`${FRONTEND_API_URL}/api/products`);
        const data = await response.json();
        return JSON.stringify(data, null, 2);
      } catch (error) {
        return JSON.stringify({ error: error.message }, null, 2);
      }
    }

    if (uri === 'ui://trending') {
      const result = await this.getTrendingProducts(null, 20);
      return JSON.stringify(result, null, 2);
    }

    throw new Error(`Unknown resource: ${uri}`);
  }
}

// Export for use
module.exports = { MarketingUIServer };

// Run as MCP server if executed directly
if (require.main === module) {
  const server = new MarketingUIServer();
  
  // Simple CLI interface for testing
  if (process.argv[2]) {
    const tool = process.argv[2];
    const args = process.argv[3] ? JSON.parse(process.argv[3]) : {};
    
    server.callTool(tool, args)
      .then(result => {
        console.log(JSON.stringify(result, null, 2));
      })
      .catch(error => {
        console.error('Error:', error.message);
        process.exit(1);
      });
  } else {
    console.log('Marketing & UI MCP Server');
    console.log('Available tools:', server.listTools().map(t => t.name).join(', '));
    console.log('\nUsage: node marketing-ui-server.js <tool> <args_json>');
  }
}
