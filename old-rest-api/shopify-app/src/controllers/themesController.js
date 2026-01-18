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

function buildSnippetContent(proposal) {
  const generated = proposal.generated || {};
  const trendName = proposal.trendName || 'trend';
  const layoutStyle = generated.layout_style || 'classic';
  const colorScheme = generated.color_scheme || 'default';

  if (generated.description_html) {
    return generated.description_html;
  }

  const title = generated.title || proposal.original?.title || 'Product';
  const description = generated.description || proposal.original?.description || '';
  const marketingAngle = generated.marketing_angle || '';

  return [
    `<div class="ai-optimized trend-${trendName} ${layoutStyle} ${colorScheme}">`,
    `  <h2>${title}</h2>`,
    description ? `  <p>${description}</p>` : '',
    marketingAngle ? `  <p class="ai-marketing">${marketingAngle}</p>` : '',
    '</div>'
  ].filter(Boolean).join('\n');
}

async function applyProductProposalToTheme(themeId, proposal) {
  const sectionKey = proposal.metadata?.sectionKey || 'sections/main-product.liquid';
  const snippetKey = proposal.metadata?.snippetKey;
  const snippetName = proposal.metadata?.snippetName;

  if (!snippetKey || !snippetName) {
    throw new Error('Missing snippet metadata for product proposal.');
  }

  const sectionAsset = await assetService.getAsset(themeId, sectionKey);
  if (!sectionAsset?.value) {
    throw new Error(`Section asset not found or empty: ${sectionKey}`);
  }

  const marker = `ai-proposal:${snippetKey}`;
  let updatedSection = sectionAsset.value;

  if (!updatedSection.includes(marker)) {
    updatedSection = [
      updatedSection.trimEnd(),
      '',
      `{% comment %}${marker}{% endcomment %}`,
      `{% render '${snippetName}' %}`,
      `{% comment %}ai-proposal-end:${snippetName}{% endcomment %}`,
      ''
    ].join('\n');
  }

  await assetService.putAsset(themeId, {
    key: sectionKey,
    value: updatedSection
  });

  const snippetContent = buildSnippetContent(proposal);
  await assetService.putAsset(themeId, {
    key: snippetKey,
    value: snippetContent
  });
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
      type: normalized.type,
      files: normalized.files,
      fileList: normalized.fileList,
      diffSummaries: normalized.diffSummaries,
      metadata: normalized.metadata,
      productId: normalized.productId,
      trendName: normalized.trendName,
      original: normalized.original,
      generated: normalized.generated
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
      type: proposal.type,
      status: proposal.status,
      files: proposal.fileList,
      diffSummaries: proposal.diffSummaries,
      draftThemeId: proposal.draftThemeId,
      productId: proposal.productId,
      trendName: proposal.trendName,
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
    if (proposal.type === 'product-copy') {
      await applyProductProposalToTheme(draftThemeId, proposal);
    } else {
      await applyAssetsToTheme(draftThemeId, proposal.files);
    }

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
      if (proposal.type === 'product-copy') {
        await applyProductProposalToTheme(mainTheme.id, proposal);
      } else {
        await applyAssetsToTheme(mainTheme.id, proposal.files);
      }
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
      if (proposal.type === 'product-copy') {
        await applyProductProposalToTheme(draftThemeId, proposal);
      } else {
        await applyAssetsToTheme(draftThemeId, proposal.files);
      }
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
