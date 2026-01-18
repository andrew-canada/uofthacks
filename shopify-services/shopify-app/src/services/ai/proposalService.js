const { validateAssetsMap } = require('../../validators/themeAssets');

function normalizeProposalPayload(payload) {
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
    files,
    fileList,
    diffSummaries,
    metadata
  };
}

module.exports = {
  normalizeProposalPayload
};
