const { shopifyRequest } = require('../../lib/shopifyClient');
const { SHOPIFY_SHOP_DOMAIN } = require('../../config/shopify');

async function listThemes() {
  const data = await shopifyRequest('themes.json', 'GET');
  return data.themes || [];
}

async function getMainTheme() {
  const themes = await listThemes();
  const mainTheme = themes.find((theme) => theme.role === 'main');
  if (!mainTheme) {
    throw new Error('Main theme not found.');
  }
  return mainTheme;
}

async function createTheme({ name, src, role = 'unpublished' }) {
  const data = await shopifyRequest('themes.json', 'POST', {
    theme: {
      name,
      src,
      role
    }
  });
  return data.theme;
}

async function createDraftFromMain(draftName) {
  const mainTheme = await getMainTheme();
  const src = `https://${SHOPIFY_SHOP_DOMAIN}/admin/themes/${mainTheme.id}/download`;

  return createTheme({
    name: draftName || `AI Draft - ${new Date().toISOString()}`,
    src,
    role: 'unpublished'
  });
}

async function publishTheme(themeId) {
  const data = await shopifyRequest(`themes/${themeId}.json`, 'PUT', {
    theme: {
      id: themeId,
      role: 'main'
    }
  });

  return data.theme;
}

module.exports = {
  listThemes,
  getMainTheme,
  createTheme,
  createDraftFromMain,
  publishTheme
};
