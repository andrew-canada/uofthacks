const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');
const { MongoClient, ObjectId, ServerApiVersion } = require('mongodb');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// MongoDB configuration
const MONGODB_URI = process.env.MONGODB_URI;
const DB_NAME = 'thewinningteam';
const SUGGESTIONS_COLLECTION = 'marketing_analysis';
const TRENDS_COLLECTION = 'trends';

let db;
let suggestionsCollection;
let trendsCollection;

// Initialize MongoDB connection (using official MongoDB Node.js driver recommended settings)
async function connectToMongoDB() {
  if (!MONGODB_URI) {
    console.log('⚠️  MONGODB_URI not set');
    return false;
  }

  try {
    // Create a MongoClient with a MongoClientOptions object to set the Stable API version
    const client = new MongoClient(MONGODB_URI, {
      serverApi: {
        version: ServerApiVersion.v1,
        strict: true,
        deprecationErrors: true,
      }
    });
    
    // Connect the client to the server
    await client.connect();
    
    // Send a ping to confirm a successful connection
    await client.db("admin").command({ ping: 1 });
    console.log("✅ Pinged MongoDB deployment. Successfully connected!");
    
    db = client.db(DB_NAME);
    suggestionsCollection = db.collection(SUGGESTIONS_COLLECTION);
    trendsCollection = db.collection(TRENDS_COLLECTION);
    console.log(`   Database: ${DB_NAME}`);
    console.log(`   Collections: ${SUGGESTIONS_COLLECTION}, ${TRENDS_COLLECTION}`);
    return true;
  } catch (error) {
    console.error('❌ MongoDB connection error:', error.message);
    console.log('   Tip: Check if your IP is whitelisted in MongoDB Atlas Network Access');
    return false;
  }
}

// Middleware - CORS configured for iframe embedding (Shopify App Bridge)
app.use(cors({
  origin: function(origin, callback) {
    // Allow requests with no origin (mobile apps, curl, etc.)
    // Allow all origins for maximum compatibility
    callback(null, true);
  },
  credentials: true, // Allow cookies/auth headers
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin']
}));

// Remove X-Frame-Options to allow iframe embedding
app.use((req, res, next) => {
  res.removeHeader('X-Frame-Options');
  // Allow embedding from anywhere
  res.setHeader('Content-Security-Policy', "frame-ancestors *;");
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  next();
});

app.use(express.json());

// Serve static files from 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

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

// ====== PRODUCTS ENDPOINTS ======

// Get all products from Shopify
app.get('/api/products', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 50;
    const data = await shopifyRequest(`products.json?limit=${limit}`, 'GET');

    res.json({
      success: true,
      products: data.products,
      count: data.products.length
    });

  } catch (error) {
    console.error('Error fetching products:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get a single product by ID
app.get('/api/products/:productId', async (req, res) => {
  try {
    let { productId } = req.params;
    
    // Extract numeric ID if it's a GID
    if (productId.includes('gid://')) {
      productId = productId.split('/').pop();
    }

    const data = await shopifyRequest(`products/${productId}.json`, 'GET');

    if (!data.product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    res.json({
      success: true,
      product: data.product
    });

  } catch (error) {
    console.error('Error fetching product:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Analyze all products against current trends
app.post('/api/products/analyze', async (req, res) => {
  try {
    // Fetch products
    const productsData = await shopifyRequest('products.json?limit=250', 'GET');
    const products = productsData.products;

    if (!products || products.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'No products found'
      });
    }

    // Load trends from MongoDB
    const trends = await trendsCollection.find({}).toArray();

    if (!trends || trends.length === 0) {
      return res.status(500).json({
        success: false,
        error: 'No trends data available'
      });
    }

    // Create product summaries
    const productSummaries = products.map(p => ({
      id: p.id,
      title: p.title,
      description: p.body_html,
      tags: p.tags ? p.tags.split(', ') : [],
      productType: p.product_type,
      vendor: p.vendor,
      price: p.variants?.[0]?.price
    }));

    // Create trend summaries
    const trendSummaries = trends.map(t => ({
      id: t._id || t.id,
      name: t.name || t.trend_name,
      description: t.description,
      keywords: t.keywords || [],
      platforms: t.platforms || [],
      popularity: t.popularity || t.engagement_score
    }));

    // Simple matching logic (can be enhanced with AI)
    const analysisResults = {
      success: true,
      productsAnalyzed: products.length,
      trendsAvailable: trends.length,
      recommendations: productSummaries.map(product => {
        const matchingTrends = trendSummaries.filter(trend => {
          const productText = `${product.title} ${product.description || ''} ${product.tags.join(' ')}`.toLowerCase();
          const trendKeywords = trend.keywords || [];
          return trendKeywords.some(kw => productText.includes(kw.toLowerCase()));
        });

        return {
          productId: product.id,
          productTitle: product.title,
          matchingTrends: matchingTrends.map(t => ({
            trendId: t.id,
            trendName: t.name,
            matchScore: 0.7 // Placeholder score
          })),
          needsMakeover: matchingTrends.length > 0
        };
      }).filter(r => r.needsMakeover)
    };

    res.json(analysisResults);

  } catch (error) {
    console.error('Error analyzing products:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Analyze a single product against trends
app.post('/api/products/:productId/analyze', async (req, res) => {
  try {
    let { productId } = req.params;
    
    if (productId.includes('gid://')) {
      productId = productId.split('/').pop();
    }

    const productData = await shopifyRequest(`products/${productId}.json`, 'GET');

    if (!productData.product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    const product = productData.product;
    const trends = await trendsCollection.find({}).toArray();

    const productSummary = {
      id: product.id,
      title: product.title,
      description: product.body_html,
      tags: product.tags ? product.tags.split(', ') : [],
      productType: product.product_type,
      vendor: product.vendor,
      price: product.variants?.[0]?.price
    };

    const trendSummaries = trends.map(t => ({
      id: t._id || t.id,
      name: t.name || t.trend_name,
      description: t.description,
      keywords: t.keywords || [],
      platforms: t.platforms || [],
      popularity: t.popularity || t.engagement_score
    }));

    // Find matching trends
    const productText = `${productSummary.title} ${productSummary.description || ''} ${productSummary.tags.join(' ')}`.toLowerCase();
    const matchingTrends = trendSummaries.filter(trend => {
      const trendKeywords = trend.keywords || [];
      return trendKeywords.some(kw => productText.includes(kw.toLowerCase()));
    });

    res.json({
      success: true,
      product: productSummary,
      analysis: {
        matchingTrends: matchingTrends.map(t => ({
          trendId: t.id,
          trendName: t.name,
          description: t.description,
          matchScore: 0.75
        })),
        needsMakeover: matchingTrends.length > 0,
        trendsAnalyzed: trends.length
      }
    });

  } catch (error) {
    console.error('Error analyzing product:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Match products to trends (Step 1)
app.post('/api/products/match-trends', async (req, res) => {
  try {
    const { product_ids } = req.body || {};
    
    let products;
    if (product_ids && product_ids.length > 0) {
      // Fetch specific products
      products = [];
      for (const pid of product_ids) {
        const numericId = pid.includes('gid://') ? pid.split('/').pop() : pid;
        try {
          const data = await shopifyRequest(`products/${numericId}.json`, 'GET');
          if (data.product) products.push(data.product);
        } catch (e) {
          console.warn(`Could not fetch product ${numericId}`);
        }
      }
    } else {
      // Fetch all products
      const data = await shopifyRequest('products.json?limit=250', 'GET');
      products = data.products;
    }

    if (!products || products.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'No products found'
      });
    }

    const trends = await trendsCollection.find({}).toArray();

    if (!trends || trends.length === 0) {
      return res.status(500).json({
        success: false,
        error: 'No trends data available'
      });
    }

    const matches = products.map(product => {
      const productText = `${product.title} ${product.body_html || ''} ${product.tags || ''}`.toLowerCase();
      
      const matchedTrends = trends
        .map(trend => {
          const keywords = trend.keywords || [];
          const matchingKeywords = keywords.filter(kw => productText.includes(kw.toLowerCase()));
          const matchScore = keywords.length > 0 ? matchingKeywords.length / keywords.length : 0;
          
          return {
            trend_id: trend._id?.toString() || trend.id,
            trend_name: trend.name || trend.trend_name,
            match_score: matchScore,
            matching_keywords: matchingKeywords,
            platforms: trend.platforms || []
          };
        })
        .filter(t => t.match_score > 0)
        .sort((a, b) => b.match_score - a.match_score);

      return {
        product_id: product.id,
        product_title: product.title,
        matched_trends: matchedTrends,
        top_match: matchedTrends[0] || null
      };
    }).filter(m => m.matched_trends.length > 0);

    res.json({
      success: true,
      matches,
      products_analyzed: products.length,
      trends_available: trends.length,
      products_with_matches: matches.length
    });

  } catch (error) {
    console.error('Error matching trends:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Generate marketing for a product-trend match (Step 2)
app.post('/api/products/:productId/generate-marketing', async (req, res) => {
  try {
    let { productId } = req.params;
    const { trend_id, match_info } = req.body || {};

    if (!trend_id) {
      return res.status(400).json({
        success: false,
        error: 'trend_id is required. Use /match-trends first to find matching trends.'
      });
    }

    if (productId.includes('gid://')) {
      productId = productId.split('/').pop();
    }

    const productData = await shopifyRequest(`products/${productId}.json`, 'GET');

    if (!productData.product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    const product = productData.product;

    // Find the trend
    let trend;
    try {
      trend = await trendsCollection.findOne({ _id: new ObjectId(trend_id) });
    } catch (e) {
      trend = await trendsCollection.findOne({ id: trend_id });
    }

    if (!trend) {
      return res.status(404).json({
        success: false,
        error: `Trend ${trend_id} not found`
      });
    }

    // Generate marketing suggestions (placeholder - can integrate with AI)
    const trendName = trend.name || trend.trend_name;
    const trendKeywords = trend.keywords || [];

    const generatedMarketing = {
      success: true,
      product_id: product.id,
      original: {
        title: product.title,
        description: product.body_html
      },
      generated: {
        optimizedTitle: `${product.title} - ${trendName} Style`,
        optimizedDescription: `<p>🔥 Trending Now: ${trendName}</p>${product.body_html || ''}<p>Keywords: ${trendKeywords.slice(0, 5).join(', ')}</p>`,
        seoTitle: `${product.title} | ${trendName} | Shop Now`,
        seoDescription: `Discover our ${product.title} featuring the latest ${trendName} trend. ${trendKeywords.slice(0, 3).join(', ')} and more.`,
        suggestedTags: [...(product.tags ? product.tags.split(', ') : []), ...trendKeywords.slice(0, 5)],
        marketingAngle: trendName,
        trendAlignment: trend.description || `Aligned with ${trendName} trend`
      },
      trend: {
        id: trend._id?.toString() || trend.id,
        name: trendName,
        keywords: trendKeywords
      },
      match_info: match_info || null
    };

    res.json(generatedMarketing);

  } catch (error) {
    console.error('Error generating marketing:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Combined: Match trends AND generate marketing
app.post('/api/products/match-and-generate', async (req, res) => {
  try {
    const { product_ids, generate_for_all } = req.body || {};

    // Step 1: Fetch products
    let products;
    if (product_ids && product_ids.length > 0) {
      products = [];
      for (const pid of product_ids) {
        const numericId = pid.includes('gid://') ? pid.split('/').pop() : pid;
        try {
          const data = await shopifyRequest(`products/${numericId}.json`, 'GET');
          if (data.product) products.push(data.product);
        } catch (e) {
          console.warn(`Could not fetch product ${numericId}`);
        }
      }
    } else {
      const data = await shopifyRequest('products.json?limit=250', 'GET');
      products = data.products;
    }

    if (!products || products.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'No products found'
      });
    }

    // Step 2: Load trends
    const trends = await trendsCollection.find({}).toArray();

    if (!trends || trends.length === 0) {
      return res.status(500).json({
        success: false,
        error: 'No trends data available'
      });
    }

    // Step 3: Match products to trends
    const matches = [];
    const generatedMarketing = [];

    for (const product of products) {
      const productText = `${product.title} ${product.body_html || ''} ${product.tags || ''}`.toLowerCase();
      
      const matchedTrends = trends
        .map(trend => {
          const keywords = trend.keywords || [];
          const matchingKeywords = keywords.filter(kw => productText.includes(kw.toLowerCase()));
          const matchScore = keywords.length > 0 ? matchingKeywords.length / keywords.length : 0;
          
          return {
            trend_id: trend._id?.toString() || trend.id,
            trend_name: trend.name || trend.trend_name,
            match_score: matchScore,
            matching_keywords: matchingKeywords,
            trend_data: trend
          };
        })
        .filter(t => t.match_score > 0)
        .sort((a, b) => b.match_score - a.match_score);

      if (matchedTrends.length > 0) {
        matches.push({
          product_id: product.id,
          product_title: product.title,
          matched_trends: matchedTrends.map(t => ({
            trend_id: t.trend_id,
            trend_name: t.trend_name,
            match_score: t.match_score
          }))
        });

        // Generate marketing for matches
        const trendsToGenerate = generate_for_all ? matchedTrends : matchedTrends.slice(0, 1);

        for (const trendMatch of trendsToGenerate) {
          const trend = trendMatch.trend_data;
          const trendName = trend.name || trend.trend_name;
          const trendKeywords = trend.keywords || [];

          generatedMarketing.push({
            product_id: product.id,
            product_title: product.title,
            trend_match: {
              trend_id: trendMatch.trend_id,
              trend_name: trendMatch.trend_name,
              match_score: trendMatch.match_score
            },
            marketing: {
              optimizedTitle: `${product.title} - ${trendName} Style`,
              optimizedDescription: `<p>🔥 Trending Now: ${trendName}</p>${product.body_html || ''}`,
              seoTitle: `${product.title} | ${trendName}`,
              seoDescription: `Discover ${product.title} with ${trendName} vibes.`,
              suggestedTags: trendKeywords.slice(0, 5)
            }
          });
        }
      }
    }

    res.json({
      success: true,
      match_results: {
        matches,
        products_analyzed: products.length,
        products_with_matches: matches.length
      },
      generated_marketing: generatedMarketing,
      marketing_generated: generatedMarketing.length
    });

  } catch (error) {
    console.error('Error in match-and-generate:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ====== TRENDS ENDPOINTS ======

// Get all trends
app.get('/api/trends', async (req, res) => {
  try {
    if (!trendsCollection) {
      return res.status(503).json({
        success: false,
        error: 'Database not connected. Check MongoDB connection.'
      });
    }

    const { platform, top } = req.query;
    
    let query = {};
    let trends;

    if (platform) {
      // Filter by platform
      query = { platforms: { $in: [platform] } };
      trends = await trendsCollection.find(query).toArray();
    } else if (top) {
      // Get top N trends by popularity
      trends = await trendsCollection
        .find({})
        .sort({ popularity: -1, engagement_score: -1 })
        .limit(parseInt(top))
        .toArray();
    } else {
      trends = await trendsCollection.find({}).toArray();
    }

    res.json({
      success: true,
      trends: trends,
      count: trends.length
    });

  } catch (error) {
    console.error('Error fetching trends:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get a specific trend by ID
app.get('/api/trends/:trendId', async (req, res) => {
  try {
    const { trendId } = req.params;
    
    let trend;
    try {
      trend = await trendsCollection.findOne({ _id: new ObjectId(trendId) });
    } catch (e) {
      trend = await trendsCollection.findOne({ id: trendId });
    }

    if (!trend) {
      return res.status(404).json({
        success: false,
        error: 'Trend not found'
      });
    }

    res.json({
      success: true,
      trend: trend
    });

  } catch (error) {
    console.error('Error fetching trend:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get list of all platforms with trends
app.get('/api/trends/meta/platforms', async (req, res) => {
  try {
    const trends = await trendsCollection.find({}).toArray();
    
    // Extract unique platforms
    const platformsSet = new Set();
    for (const trend of trends) {
      if (trend.platforms && Array.isArray(trend.platforms)) {
        trend.platforms.forEach(p => platformsSet.add(p));
      }
    }

    res.json({
      success: true,
      platforms: Array.from(platformsSet).sort()
    });

  } catch (error) {
    console.error('Error fetching platforms:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Find trends that match a specific product
app.get('/api/trends/match/:productId', async (req, res) => {
  try {
    let { productId } = req.params;

    if (productId.includes('gid://')) {
      productId = productId.split('/').pop();
    }

    const productData = await shopifyRequest(`products/${productId}.json`, 'GET');

    if (!productData.product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    const product = productData.product;
    const trends = await trendsCollection.find({}).toArray();

    const productSummary = {
      id: product.id,
      title: product.title,
      description: product.body_html,
      tags: product.tags ? product.tags.split(', ') : [],
      productType: product.product_type
    };

    const productText = `${productSummary.title} ${productSummary.description || ''} ${productSummary.tags.join(' ')}`.toLowerCase();

    // Calculate match scores
    const matches = trends
      .map(trend => {
        const keywords = trend.keywords || [];
        const matchingKeywords = keywords.filter(kw => productText.includes(kw.toLowerCase()));
        const matchScore = keywords.length > 0 ? matchingKeywords.length / keywords.length : 0;

        return {
          trend: {
            id: trend._id?.toString() || trend.id,
            name: trend.name || trend.trend_name,
            description: trend.description,
            keywords: trend.keywords,
            platforms: trend.platforms,
            popularity: trend.popularity || trend.engagement_score
          },
          matchScore: matchScore,
          matchingKeywords: matchingKeywords
        };
      })
      .filter(m => m.matchScore > 0)
      .sort((a, b) => b.matchScore - a.matchScore);

    res.json({
      success: true,
      product: productSummary,
      matches: matches
    });

  } catch (error) {
    console.error('Error matching trends to product:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ====== SUGGESTION SYSTEM ENDPOINTS ======

// Get all suggestions
app.get('/api/suggestions', async (req, res) => {
  try {
    const suggestions = await suggestionsCollection.find({}).toArray();
    res.json({
      success: true,
      suggestions: suggestions
    });
  } catch (error) {
    console.error('Error fetching suggestions:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
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
      type, // 'new-product', 'price-change', 'description-change', 'replace-product'
      data,
      status: 'pending', // 'pending', 'accepted', 'rejected'
      createdAt: new Date()
    };

    const result = await suggestionsCollection.insertOne(suggestion);
    suggestion._id = result.insertedId;

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
    
    let suggestion;
    try {
      suggestion = await suggestionsCollection.findOne({ _id: new ObjectId(id) });
    } catch (e) {
      // Try finding by string id field for backward compatibility
      suggestion = await suggestionsCollection.findOne({ id: id });
    }

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
            product_type: suggestion.data.newProduct.product_type || 'Shoes',
            tags: suggestion.data.newProduct.tags || ['shoes', 'suggested'],
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

    // Update suggestion in MongoDB
    const updateQuery = suggestion._id 
      ? { _id: suggestion._id }
      : { id: id };
    
    await suggestionsCollection.updateOne(updateQuery, {
      $set: {
        status: 'accepted',
        acceptedAt: new Date(),
        appliedData: suggestion.appliedData
      }
    });

    suggestion.status = 'accepted';
    suggestion.acceptedAt = new Date();

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
app.post('/api/suggestions/:id/reject', async (req, res) => {
  try {
    const { id } = req.params;
    
    let suggestion;
    try {
      suggestion = await suggestionsCollection.findOne({ _id: new ObjectId(id) });
    } catch (e) {
      suggestion = await suggestionsCollection.findOne({ id: id });
    }

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

    const updateQuery = suggestion._id 
      ? { _id: suggestion._id }
      : { id: id };

    await suggestionsCollection.updateOne(updateQuery, {
      $set: {
        status: 'rejected',
        rejectedAt: new Date()
      }
    });

    suggestion.status = 'rejected';
    suggestion.rejectedAt = new Date();

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
app.delete('/api/suggestions/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    let result;
    try {
      result = await suggestionsCollection.deleteOne({ _id: new ObjectId(id) });
    } catch (e) {
      result = await suggestionsCollection.deleteOne({ id: id });
    }

    if (result.deletedCount === 0) {
      return res.status(404).json({
        success: false,
        error: 'Suggestion not found'
      });
    }

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
      type: 'replace-product',
      data: {
        productIdToReplace: randomProduct.id,
        productTitle: randomProduct.title,
        newProduct: {
          title: 'Classic Leather Shoes',
          description: '<p>Premium quality leather shoes - trending now!</p>',
          vendor: 'Trending Shoes'
        },
        reason: 'AI-generated suggestion based on trend analysis',
        trendSource: 'auto-generated',
        confidenceScore: 0.75
      },
      status: 'pending',
      createdAt: new Date()
    });

    // Generate a price change suggestion
    const productForPrice = products[Math.floor(Math.random() * products.length)];
    if (productForPrice.variants && productForPrice.variants.length > 0) {
      const variant = productForPrice.variants[0];
      const currentPrice = parseFloat(variant.price);
      const newPrice = (currentPrice * 0.9).toFixed(2); // 10% discount

      generatedSuggestions.push({
        type: 'price-change',
        data: {
          productId: productForPrice.id,
          variantId: variant.id,
          productTitle: productForPrice.title,
          currentPrice: currentPrice,
          newPrice: newPrice,
          reason: '10% discount to boost sales',
          trendSource: 'market-analysis',
          confidenceScore: 0.72
        },
        status: 'pending',
        createdAt: new Date()
      });
    }

    // Generate a new product suggestion
    generatedSuggestions.push({
      type: 'new-product',
      data: {
        product: {
          title: 'Trendy Sneakers Collection',
          body_html: '<p>New arrival! Limited edition sneakers based on current trends.</p>',
          vendor: 'Fashion Forward',
          product_type: 'Shoes',
          tags: ['new', 'trending', 'sneakers', 'limited-edition'],
          status: 'active'
        },
        reason: 'Trending product opportunity identified',
        trendSource: 'trend-analysis',
        confidenceScore: 0.85
      },
      status: 'pending',
      createdAt: new Date()
    });

    // Insert all generated suggestions into MongoDB
    const result = await suggestionsCollection.insertMany(generatedSuggestions);

    res.json({
      success: true,
      suggestions: generatedSuggestions,
      insertedCount: result.insertedCount,
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

// Check pending suggestions count from MongoDB
app.get('/api/suggestions/stats', async (req, res) => {
  try {
    const stats = await suggestionsCollection.aggregate([
      {
        $group: {
          _id: '$status',
          count: { $sum: 1 }
        }
      }
    ]).toArray();

    const total = await suggestionsCollection.countDocuments();
    
    res.json({
      success: true,
      stats: {
        total,
        byStatus: stats.reduce((acc, curr) => {
          acc[curr._id] = curr.count;
          return acc;
        }, {})
      }
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Start server with MongoDB connection
async function startServer() {
  // Connect to MongoDB first
  const mongoConnected = await connectToMongoDB();
  
  if (!mongoConnected) {
    console.error('❌ Failed to connect to MongoDB. Server will start but database features will not work.');
  }

  app.listen(PORT, async () => {
    console.log(`\n🚀 Product Suggestions API running on port ${PORT}`);
    console.log(`📍 Shop: ${process.env.SHOPIFY_SHOP_DOMAIN}`);
    console.log(`📦 MongoDB: ${mongoConnected ? 'Connected to ' + DB_NAME : 'Not connected'}`);
    console.log(`\n=== Products Endpoints ===`);
    console.log(`  GET    /api/products                         - Get all products`);
    console.log(`  GET    /api/products/:id                     - Get single product`);
    console.log(`  POST   /api/products/analyze                 - Analyze all products vs trends`);
    console.log(`  POST   /api/products/:id/analyze             - Analyze single product`);
    console.log(`  POST   /api/products/match-trends            - Match products to trends`);
    console.log(`  POST   /api/products/:id/generate-marketing  - Generate marketing for product`);
    console.log(`  POST   /api/products/match-and-generate      - Match & generate in one call`);
    console.log(`\n=== Trends Endpoints (MongoDB) ===`);
    console.log(`  GET    /api/trends                           - Get all trends`);
    console.log(`  GET    /api/trends?platform=TikTok           - Filter by platform`);
    console.log(`  GET    /api/trends?top=10                    - Get top N trends`);
    console.log(`  GET    /api/trends/:id                       - Get single trend`);
    console.log(`  GET    /api/trends/meta/platforms            - Get all platforms`);
    console.log(`  GET    /api/trends/match/:productId          - Find trends for product`);
    console.log(`\n=== Suggestions Endpoints (MongoDB) ===`);
    console.log(`  GET    /api/suggestions                      - Get all suggestions`);
    console.log(`  GET    /api/suggestions/stats                - Get suggestion stats`);
    console.log(`  POST   /api/suggestions                      - Create suggestion`);
    console.log(`  POST   /api/suggestions/generate             - Auto-generate suggestions`);
    console.log(`  POST   /api/suggestions/:id/accept           - Accept & apply suggestion`);
    console.log(`  POST   /api/suggestions/:id/reject           - Reject suggestion`);
    console.log(`  DELETE /api/suggestions/:id                  - Delete suggestion`);

    // Log counts from DB
    if (mongoConnected) {
      try {
        const suggestionsCount = await suggestionsCollection.countDocuments({ status: 'pending' });
        const trendsCount = await trendsCollection.countDocuments();
        console.log(`\n📊 Database Stats:`);
        console.log(`   ${suggestionsCount} pending suggestions`);
        console.log(`   ${trendsCount} trends available`);
      } catch (e) {
        console.log('⚠️  Could not fetch database counts');
      }
    }

    console.log(`\n🌐 Access the app at: http://localhost:${PORT}`);
  });
}

// Start the server
startServer();
