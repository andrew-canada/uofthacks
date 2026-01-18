const proposalStore = require('../services/storage/proposalStore');
const { normalizeProposalPayload } = require('../services/ai/proposalService');
const themeService = require('../services/shopify/themeService');
const assetService = require('../services/shopify/assetService');
const { SHOPIFY_SHOP_DOMAIN } = require('../config/shopify');

function buildPreviewUrl(themeId, previewPath = '/') {
  const path = previewPath.startsWith('/') ? previewPath : `/${previewPath}`;
  return `https://${SHOPIFY_SHOP_DOMAIN}${path}?preview_theme_id=${themeId}`;
}

async function applyAssetsToTheme(themeId, files) {
  const results = [];

  for (const [key, value] of Object.entries(files)) {
    const updated = await assetService.putAsset(themeId, {
      key,
      value
    });
    results.push(updated);
  }

  return results;
}

async function ensureDraftTheme(proposal, draftName) {
  if (proposal.draftThemeId) {
    return proposal.draftThemeId;
  }

  const draftTheme = await themeService.createDraftFromMain(draftName);
  proposalStore.updateProposal(proposal.id, {
    draftThemeId: draftTheme.id,
    draftThemeName: draftTheme.name
  });

  return draftTheme.id;
}

async function createProposal(req, res) {
  try {
    const normalized = normalizeProposalPayload(req.body || {});
    const proposal = proposalStore.createProposal({
      files: normalized.files,
      fileList: normalized.fileList,
      diffSummaries: normalized.diffSummaries,
      metadata: normalized.metadata
    });

    return res.json({
      success: true,
      proposal
    });
  } catch (error) {
    return res.status(400).json({
      success: false,
      error: error.message
    });
  }
}

async function getProposal(req, res) {
  const proposal = proposalStore.getProposal(req.params.id);

  if (!proposal) {
    return res.status(404).json({
      success: false,
      error: 'Proposal not found'
    });
  }

  return res.json({
    success: true,
    proposal: {
      id: proposal.id,
      status: proposal.status,
      files: proposal.fileList,
      diffSummaries: proposal.diffSummaries,
      draftThemeId: proposal.draftThemeId,
      createdAt: proposal.createdAt
    }
  });
}

async function applyToDraft(req, res) {
  try {
    const proposal = proposalStore.getProposal(req.params.id);
    if (!proposal) {
      return res.status(404).json({
        success: false,
        error: 'Proposal not found'
      });
    }

    const draftThemeId = await ensureDraftTheme(proposal, req.body?.draftName);
    await applyAssetsToTheme(draftThemeId, proposal.files);

    proposalStore.updateProposal(proposal.id, {
      status: 'draft-applied'
    });

    return res.json({
      success: true,
      draftThemeId,
      previewUrl: buildPreviewUrl(draftThemeId, req.body?.previewPath)
    });
  } catch (error) {
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

async function applyToMain(req, res) {
  try {
    const proposal = proposalStore.getProposal(req.params.id);
    if (!proposal) {
      return res.status(404).json({
        success: false,
        error: 'Proposal not found'
      });
    }

    const strategy = req.body?.strategy || 'publish-draft';

    if (strategy === 'copy-assets') {
      const mainTheme = await themeService.getMainTheme();
      await applyAssetsToTheme(mainTheme.id, proposal.files);
      proposalStore.updateProposal(proposal.id, {
        status: 'main-updated',
        mainThemeId: mainTheme.id
      });

      return res.json({
        success: true,
        strategy,
        mainThemeId: mainTheme.id
      });
    }

    const draftThemeId = await ensureDraftTheme(proposal, req.body?.draftName);

    if (proposal.status !== 'draft-applied') {
      await applyAssetsToTheme(draftThemeId, proposal.files);
    }

    const publishedTheme = await themeService.publishTheme(draftThemeId);
    proposalStore.updateProposal(proposal.id, {
      status: 'published',
      mainThemeId: publishedTheme.id
    });

    return res.json({
      success: true,
      strategy: 'publish-draft',
      mainThemeId: publishedTheme.id
    });
  } catch (error) {
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

async function previewUrl(req, res) {
  const { id } = req.params;
  const previewPath = req.query.path || '/';

  return res.json({
    success: true,
    previewUrl: buildPreviewUrl(id, previewPath)
  });
}

module.exports = {
  createProposal,
  getProposal,
  applyToDraft,
  applyToMain,
  previewUrl
};
