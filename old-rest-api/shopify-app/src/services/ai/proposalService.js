const { validateAssetsMap } = require('../../validators/themeAssets');

function normalizeThemeAssetsPayload(payload) {
  const files = payload.files || payload.assets;
  validateAssetsMap(files);

  const diffSummaries = payload.diffSummaries || {};
  const metadata = payload.metadata || {};

  const fileList = Object.keys(files).map((key) => ({
    key,
    status: 'changed',
    summary: diffSummaries[key] || 'AI-proposed update.'
  }));

  return {
    type: 'theme-assets',
    files,
    fileList,
    diffSummaries,
    metadata
  };
}

function slugify(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

function buildSnippetName(productId, trendName) {
  const cleanedProduct = slugify(productId?.split('/').pop() || productId || 'product');
  const cleanedTrend = slugify(trendName || 'trend');
  return `ai_${cleanedTrend}_${cleanedProduct}`;
}

function normalizeProductCopyPayload(payload) {
  const productId = payload.product_id;
  const generated = payload.generated;

  if (!productId || !generated) {
    throw new Error('product_id and generated are required for product proposal payloads.');
  }

  const metadata = payload.metadata || {};
  const trendName = payload.trend_name || 'trend';
  const snippetName = buildSnippetName(productId, trendName);
  const sectionKey = metadata.section_key || 'sections/main-product.liquid';
  const snippetKey = `snippets/${snippetName}.liquid`;

  const fileList = [
    {
      key: sectionKey,
      status: 'changed',
      summary: 'Insert AI snippet render into product section.'
    },
    {
      key: snippetKey,
      status: 'new',
      summary: 'AI-generated product copy snippet.'
    }
  ];

  return {
    type: 'product-copy',
    productId,
    trendName,
    original: payload.original || {},
    generated,
    metadata: {
      ...metadata,
      sectionKey,
      snippetKey,
      snippetName
    },
    fileList,
    diffSummaries: {}
  };
}

function normalizeProposalPayload(payload) {
  if (payload?.files || payload?.assets) {
    return normalizeThemeAssetsPayload(payload);
  }

  if (payload?.generated && payload?.product_id) {
    return normalizeProductCopyPayload(payload);
  }

  throw new Error('Unsupported proposal payload format.');
}

module.exports = {
  normalizeProposalPayload
};
