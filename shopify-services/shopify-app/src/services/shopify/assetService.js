const { shopifyRequest } = require('../../lib/shopifyClient');

async function listAssets(themeId) {
  const data = await shopifyRequest(`themes/${themeId}/assets.json`, 'GET');
  return data.assets || [];
}

async function getAsset(themeId, key) {
  const params = new URLSearchParams();
  params.set('asset[key]', key);
  const data = await shopifyRequest(`themes/${themeId}/assets.json?${params.toString()}`, 'GET');
  return data.asset;
}

async function putAsset(themeId, asset) {
  const payload = {
    asset: {
      key: asset.key,
      value: asset.value
    }
  };

  if (asset.attachment) {
    payload.asset.attachment = asset.attachment;
    delete payload.asset.value;
  }

  if (asset.src) {
    payload.asset.src = asset.src;
    delete payload.asset.value;
  }

  if (asset.source_key) {
    payload.asset.source_key = asset.source_key;
    delete payload.asset.value;
  }

  const data = await shopifyRequest(`themes/${themeId}/assets.json`, 'PUT', payload);
  return data.asset;
}

async function deleteAsset(themeId, key) {
  const params = new URLSearchParams();
  params.set('asset[key]', key);
  const data = await shopifyRequest(`themes/${themeId}/assets.json?${params.toString()}`, 'DELETE');
  return data;
}

module.exports = {
  listAssets,
  getAsset,
  putAsset,
  deleteAsset
};
