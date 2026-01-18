/**
 * Test Script for Theme Extensions
 * 
 * Run with: node test-theme-extensions.js
 * 
 * Tests adding badges, styling, and ordering via API
 */

const API_BASE = process.env.API_BASE || 'http://localhost:3000';

async function testThemeExtensions() {
  console.log('🧪 Testing Theme Extensions...\n');

  try {
    // Step 1: Get a product
    console.log('📦 Fetching products...');
    const productsRes = await fetch(`${API_BASE}/api/products`);
    
    if (!productsRes.ok) {
      throw new Error(`API request failed: ${productsRes.status} ${productsRes.statusText}`);
    }
    
    const productsData = await productsRes.json();
    
    if (!productsData.success || !productsData.products || productsData.products.length === 0) {
      console.log('❌ No products found. Make sure your store has products.');
      console.log('   API Response:', productsData);
      return;
    }

    const product = productsData.products[0];
    console.log(`✅ Found product: ${product.title}`);
    console.log(`   Product ID: ${product.id}\n`);

    // Step 2: Add badge
    console.log('1️⃣ Adding trending badge...');
    const badgeRes = await fetch(`${API_BASE}/api/theme-extensions/product-badge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        productId: product.id,
        badgeType: 'trending',
        badgeText: '🔥 Trending Now'
      })
    });
    
    const badgeData = await badgeRes.json();
    if (badgeData.success) {
      console.log('✅ Badge added successfully!');
      console.log(`   Badge: ${badgeData.badge.text}`);
      console.log(`   Metafield ID: ${badgeData.badge.metafield?.id || 'N/A'}\n`);
    } else {
      console.log(`❌ Error adding badge: ${badgeData.error}\n`);
    }

    // Step 3: Add styling
    console.log('2️⃣ Adding hero styling...');
    const styleRes = await fetch(`${API_BASE}/api/theme-extensions/product-styling`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        productId: product.id,
        styleType: 'hero',
        colorScheme: '#FF6B6B'
      })
    });
    
    const styleData = await styleRes.json();
    if (styleData.success) {
      console.log('✅ Styling applied successfully!');
      console.log(`   Style: ${styleData.styling.style}`);
      console.log(`   Color: ${styleData.styling.colorScheme}\n`);
    } else {
      console.log(`❌ Error applying styling: ${styleData.error}\n`);
    }

    // Step 4: Verify metafields
    console.log('3️⃣ Verifying metafields...');
    const verifyRes = await fetch(`${API_BASE}/api/theme-extensions/product-badge/${encodeURIComponent(product.id)}`);
    const verifyData = await verifyRes.json();
    
    if (verifyData.success && verifyData.badge) {
      console.log('✅ Badge metafield verified!');
      console.log(`   Type: ${verifyData.badge.type}`);
      console.log(`   Text: ${verifyData.badge.text}\n`);
    } else {
      console.log('⚠️  Badge metafield not found (may take a moment to appear)');
      console.log(`   Response: ${JSON.stringify(verifyData)}\n`);
    }

    // Step 5: Get products with UI state
    console.log('4️⃣ Fetching products with UI state...');
    const uiRes = await fetch(`${API_BASE}/api/theme-extensions/products-with-ui?limit=5`);
    const uiData = await uiRes.json();
    
    if (uiData.success) {
      console.log(`✅ Found ${uiData.count} products with UI state`);
      const ourProduct = uiData.products.find(p => p.id === product.id);
      if (ourProduct && ourProduct.ui.badge) {
        console.log(`   ✅ Your product has UI state:`);
        console.log(`      Badge: ${ourProduct.ui.badge.type}`);
        console.log(`      Styling: ${ourProduct.ui.styling?.style || 'None'}\n`);
      }
    }

    // Success summary
    console.log('✅ Testing complete!\n');
    console.log('📋 Next steps:');
    console.log(`   1. Go to your Shopify store admin`);
    console.log(`   2. Visit Products → "${product.title}"`);
    console.log(`   3. Scroll down to "Metafields" section`);
    console.log(`   4. You should see:`);
    console.log(`      - namespace: trending_ui, key: badge`);
    console.log(`      - namespace: trending_ui, key: styling`);
    console.log(`\n   5. Visit the product page on your store`);
    console.log(`   6. You should see:`);
    console.log(`      - "🔥 Trending Now" badge (top-right of product card)`);
    console.log(`      - Red border on product card (hero style)`);
    console.log(`\n💡 If you don't see changes on the storefront:`);
    console.log(`   - Make sure snippets are added to your theme (see THEME_EXTENSION_SETUP.md)`);
    console.log(`   - Refresh the product page`);
    console.log(`   - Check browser console for errors`);
    console.log(`   - Verify snippets are included: {% render 'trending-badge', product: product %}`);

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error('\n🔍 Troubleshooting:');
    console.error(`   1. Make sure server is running: ${API_BASE}`);
    console.error(`   2. Check server logs for errors`);
    console.error(`   3. Verify SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN are set`);
    console.error(`   4. Test API health: ${API_BASE}/health`);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  testThemeExtensions().catch(console.error);
}

module.exports = { testThemeExtensions };
