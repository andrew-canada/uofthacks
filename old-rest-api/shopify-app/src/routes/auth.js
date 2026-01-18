const express = require('express');

const {
  SHOPIFY_API_KEY,
  SHOPIFY_SCOPES
} = require('../config/shopify');

const router = express.Router();

router.get('/install', (req, res) => {
  const shop = req.query.shop;

  if (!shop) {
    return res.status(400).send('Missing shop parameter');
  }

  const redirectUri = process.env.SHOPIFY_REDIRECT_URI
    || `${req.protocol}://${req.get('host')}/callback`;

  const installUrl = `https://${shop}/admin/oauth/authorize?client_id=${SHOPIFY_API_KEY}&scope=${SHOPIFY_SCOPES}&redirect_uri=${encodeURIComponent(redirectUri)}`;
  return res.redirect(installUrl);
});

router.get('/callback', async (req, res) => {
  const { shop, code } = req.query;

  if (!shop || !code) {
    return res.status(400).send('Missing required parameters');
  }

  return res.redirect(`/embedded.html?shop=${shop}&apiKey=${SHOPIFY_API_KEY}`);
});

router.get('/app', (req, res) => {
  const shop = req.query.shop;
  const host = req.query.host;

  if (!shop) {
    return res.status(400).send('Missing shop parameter. Please install the app first.');
  }

  return res.redirect(`/embedded.html?shop=${shop}&host=${host || ''}&apiKey=${SHOPIFY_API_KEY}`);
});

module.exports = router;
