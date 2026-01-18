const SHOPIFY_SHOP_DOMAIN = process.env.SHOPIFY_SHOP_DOMAIN;
const SHOPIFY_ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const SHOPIFY_API_KEY = process.env.SHOPIFY_API_KEY;
const SHOPIFY_API_SECRET = process.env.SHOPIFY_API_SECRET;
const SHOPIFY_API_VERSION = process.env.SHOPIFY_API_VERSION || '2026-01';
const SHOPIFY_SCOPES = process.env.SHOPIFY_SCOPES
  || 'read_products,write_products,read_product_listings,write_product_listings,read_themes,write_themes';

module.exports = {
  SHOPIFY_SHOP_DOMAIN,
  SHOPIFY_ACCESS_TOKEN,
  SHOPIFY_API_KEY,
  SHOPIFY_API_SECRET,
  SHOPIFY_API_VERSION,
  SHOPIFY_SCOPES
};
