const express = require('express');

const themesController = require('../controllers/themesController');

const router = express.Router();

router.post('/ai-proposals', themesController.createProposal);
router.get('/ai-proposals/:id', themesController.getProposal);
router.post('/ai-proposals/:id/apply-to-draft', themesController.applyToDraft);
router.post('/ai-proposals/:id/apply-to-main', themesController.applyToMain);
router.get('/drafts/:id/preview-url', themesController.previewUrl);

module.exports = router;
