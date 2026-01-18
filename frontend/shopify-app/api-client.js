/**
 * API Client for UofTHacks Backend APIs
 * 
 * Provides helper functions to call:
 * - Backend Flask API (http://localhost:5000)
 * - Shopify API
 * - Frontend Express API (http://localhost:3000)
 */

const BACKEND_API_BASE = process.env.BACKEND_API_URL || 'http://localhost:5000';
const FRONTEND_API_BASE = process.env.FRONTEND_API_URL || 'http://localhost:3000';

/**
 * Generic API request helper
 * @param {string} url - Full URL or endpoint path
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
 * @param {object} body - Request body (optional)
 * @param {object} headers - Additional headers (optional)
 * @returns {Promise<object>} Response data
 */
async function apiRequest(url, method = 'GET', body = null, headers = {}) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers
    }
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    return await response.text();
  } catch (error) {
    console.error(`API Request failed: ${method} ${url}`, error);
    throw error;
  }
}

// ============================================
// Backend Flask API Client (http://localhost:5000)
// ============================================

const BackendAPI = {
  /**
   * Health check
   */
  async healthCheck() {
    return apiRequest(`${BACKEND_API_BASE}/health`);
  },

  /**
   * Get all products
   */
  async getProducts() {
    return apiRequest(`${BACKEND_API_BASE}/api/products`);
  },

  /**
   * Get single product
   */
  async getProduct(productId) {
    return apiRequest(`${BACKEND_API_BASE}/api/products/${productId}`);
  },

  /**
   * Analyze products with AI
   */
  async analyzeProducts(productIds = null) {
    const body = productIds ? { product_ids: productIds } : {};
    return apiRequest(`${BACKEND_API_BASE}/api/products/analyze`, 'POST', body);
  },

  /**
   * Analyze single product
   */
  async analyzeProduct(productId) {
    return apiRequest(`${BACKEND_API_BASE}/api/products/${productId}/analyze`, 'POST');
  },

  /**
   * Apply AI recommendations to product
   */
  async applyRecommendations(productId, recommendations) {
    return apiRequest(
      `${BACKEND_API_BASE}/api/products/${productId}/apply`,
      'POST',
      { recommendations }
    );
  },

  /**
   * Get all trends
   */
  async getTrends(filters = {}) {
    const params = new URLSearchParams(filters);
    const url = `${BACKEND_API_BASE}/api/trends${params.toString() ? '?' + params : ''}`;
    return apiRequest(url);
  },

  /**
   * Get single trend
   */
  async getTrend(trendId) {
    return apiRequest(`${BACKEND_API_BASE}/api/trends/${trendId}`);
  },

  /**
   * Match product to trends
   */
  async matchProductToTrends(productId) {
    return apiRequest(`${BACKEND_API_BASE}/api/trends/match/${productId}`);
  }
};

// ============================================
// Frontend Express API Client (http://localhost:3000)
// ============================================

const FrontendAPI = {
  /**
   * Health check
   */
  async healthCheck() {
    return apiRequest(`${FRONTEND_API_BASE}/health`);
  },

  /**
   * Get all products
   */
  async getProducts() {
    return apiRequest(`${FRONTEND_API_BASE}/api/products`);
  },

  /**
   * Get all collections
   */
  async getCollections() {
    return apiRequest(`${FRONTEND_API_BASE}/api/collections`);
  },

  /**
   * Replace product in collection
   */
  async replaceProduct(currentProductId, replacementProductId, collectionId = null) {
    return apiRequest(
      `${FRONTEND_API_BASE}/api/replace-product`,
      'POST',
      { currentProductId, replacementProductId, collectionId }
    );
  },

  /**
   * Create and replace product
   */
  async createAndReplace(productIdToReplace) {
    return apiRequest(
      `${FRONTEND_API_BASE}/api/create-and-replace`,
      'POST',
      { productIdToReplace }
    );
  },

  /**
   * Get all suggestions
   */
  async getSuggestions() {
    return apiRequest(`${FRONTEND_API_BASE}/api/suggestions`);
  },

  /**
   * Create suggestion
   */
  async createSuggestion(type, data) {
    return apiRequest(
      `${FRONTEND_API_BASE}/api/suggestions`,
      'POST',
      { type, data }
    );
  },

  /**
   * Accept suggestion
   */
  async acceptSuggestion(suggestionId) {
    return apiRequest(
      `${FRONTEND_API_BASE}/api/suggestions/${suggestionId}/accept`,
      'POST'
    );
  },

  /**
   * Reject suggestion
   */
  async rejectSuggestion(suggestionId) {
    return apiRequest(
      `${FRONTEND_API_BASE}/api/suggestions/${suggestionId}/reject`,
      'POST'
    );
  },

  /**
   * Generate auto-suggestions
   */
  async generateSuggestions() {
    return apiRequest(`${FRONTEND_API_BASE}/api/suggestions/generate`, 'POST');
  }
};

// ============================================
// Shopify API Client Helper
// ============================================

const ShopifyAPI = {
  /**
   * Make Shopify API request
   * @param {string} shopDomain - Shopify shop domain
   * @param {string} accessToken - Shopify access token
   * @param {string} endpoint - API endpoint (e.g., 'products.json')
   * @param {string} method - HTTP method
   * @param {object} body - Request body
   * @param {string} apiVersion - API version (default: '2025-01')
   */
  async request(shopDomain, accessToken, endpoint, method = 'GET', body = null, apiVersion = '2025-01') {
    const url = `https://${shopDomain}/admin/api/${apiVersion}/${endpoint}`;
    
    const headers = {
      'X-Shopify-Access-Token': accessToken,
      'Content-Type': 'application/json'
    };

    return apiRequest(url, method, body, headers);
  },

  /**
   * Get products
   */
  async getProducts(shopDomain, accessToken, limit = 250) {
    return this.request(shopDomain, accessToken, `products.json?limit=${limit}`);
  },

  /**
   * Get single product
   */
  async getProduct(shopDomain, accessToken, productId) {
    return this.request(shopDomain, accessToken, `products/${productId}.json`);
  },

  /**
   * Create product
   */
  async createProduct(shopDomain, accessToken, productData) {
    return this.request(
      shopDomain,
      accessToken,
      'products.json',
      'POST',
      { product: productData }
    );
  },

  /**
   * Update product
   */
  async updateProduct(shopDomain, accessToken, productId, productData) {
    return this.request(
      shopDomain,
      accessToken,
      `products/${productId}.json`,
      'PUT',
      { product: productData }
    );
  },

  /**
   * Delete product
   */
  async deleteProduct(shopDomain, accessToken, productId) {
    return this.request(
      shopDomain,
      accessToken,
      `products/${productId}.json`,
      'DELETE'
    );
  },

  /**
   * Get collections
   */
  async getCollections(shopDomain, accessToken) {
    return this.request(shopDomain, accessToken, 'custom_collections.json');
  },

  /**
   * GraphQL query
   */
  async graphql(shopDomain, accessToken, query, variables = {}) {
    const url = `https://${shopDomain}/admin/api/2025-01/graphql.json`;
    
    return apiRequest(
      url,
      'POST',
      { query, variables },
      {
        'X-Shopify-Access-Token': accessToken,
        'Content-Type': 'application/json'
      }
    );
  }
};

// Export clients
module.exports = {
  apiRequest,
  BackendAPI,
  FrontendAPI,
  ShopifyAPI
};
