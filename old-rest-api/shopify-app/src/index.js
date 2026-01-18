const dotenv = require('dotenv');

dotenv.config();

const app = require('./app');
const { initializeSuggestions } = require('./routes/suggestions');
const { SHOPIFY_SHOP_DOMAIN } = require('./config/shopify');

const PORT = process.env.PORT || 3000;

app.listen(PORT, async () => {
  console.log(`\n🚀 Product Suggestions API running on port ${PORT}`);
  console.log(`📍 Shop: ${SHOPIFY_SHOP_DOMAIN}`);
  console.log(`\nEndpoints:`);
  console.log(`  GET  /health - Health check`);
  console.log(`  POST /api/replace-product - Replace product in collection`);
  console.log(`  POST /api/create-and-replace - Create shoe and replace product in all collections`);
  console.log(`  GET  /api/collections - Get all collections`);
  console.log(`  GET  /api/products - Get all products`);
  console.log(`\n  === Suggestion System ===`);
  console.log(`  GET    /api/suggestions - Get all suggestions`);
  console.log(`  POST   /api/suggestions - Create a new suggestion`);
  console.log(`  POST   /api/suggestions/generate - Generate auto-suggestions`);
  console.log(`  POST   /api/suggestions/:id/accept - Accept a suggestion`);
  console.log(`  POST   /api/suggestions/:id/reject - Reject a suggestion`);
  console.log(`  DELETE /api/suggestions/:id - Delete a suggestion`);
  console.log(`\n  === Theme AI Pipeline ===`);
  console.log(`  POST /api/themes/ai-proposals - Create AI proposal`);
  console.log(`  GET  /api/themes/ai-proposals/:id - Fetch proposal`);
  console.log(`  POST /api/themes/ai-proposals/:id/apply-to-draft - Apply to draft theme`);
  console.log(`  POST /api/themes/ai-proposals/:id/apply-to-main - Apply to main theme`);
  console.log(`  GET  /api/themes/drafts/:id/preview-url - Preview URL`);

  await initializeSuggestions();

  console.log(`\n🌐 Access the app at:`);
  console.log(`   Admin: http://localhost:${PORT}/admin.html`);
  console.log(`   Public: http://localhost:${PORT}/suggestions.html`);
});
