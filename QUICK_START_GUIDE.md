# Quick Start Guide: Product Replacement Feature

## ✅ What's Been Built

You now have a complete system to **permanently replace products** on your Shopify store:

1. **Admin Suggestion Tab** (in your theme) - Already deployed ✅
2. **Shopify API Server** (Node.js app) - Ready to configure ⚙️

## 🚀 Next Steps to Make It Work

### Step 1: Create Shopify Custom App (5 minutes)

1. **Go to Shopify Admin**:
   ```
   https://parallelapparel-uofthacksdemo.myshopify.com/admin/settings/apps/development
   ```

2. **Click "Create an app"**:
   - App name: `Product Suggestions API`
   - Click **Create app**

3. **Configure API Scopes**:
   - Click **Configure Admin API scopes**
   - Check these boxes:
     - ✅ `read_products`
     - ✅ `write_products`
     - ✅ `read_product_listings`
     - ✅ `write_product_listings`
   - Click **Save**

4. **Install the App**:
   - Click **Install app** button
   - Click **Install** to confirm

5. **Copy Your Credentials**:
   After installation, you'll see:
   - **API key** (starts with letters/numbers)
   - **API secret key** (long string)
   - **Admin API access token** (starts with `shpat_`)

   ⚠️ **COPY THESE NOW!** The access token only shows once!

---

### Step 2: Configure the API Server (2 minutes)

1. **Navigate to the app folder**:
   ```bash
   cd /Users/ronitlongia/Desktop/frontend/shopify-app
   ```

2. **Create .env file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit .env file** and paste your credentials:
   ```env
   SHOPIFY_API_KEY=paste_your_api_key_here
   SHOPIFY_API_SECRET=paste_your_api_secret_here
   SHOPIFY_ACCESS_TOKEN=paste_your_access_token_here
   SHOPIFY_SHOP_DOMAIN=parallelapparel-uofthacksdemo.myshopify.com
   PORT=3000
   ```

---

### Step 3: Start the API Server (1 minute)

```bash
cd /Users/ronitlongia/Desktop/frontend/shopify-app
npm start
```

You should see:
```
🚀 Product Suggestions API running on port 3000
📍 Shop: parallelapparel-uofthacksdemo.myshopify.com
```

**Keep this terminal window open!** The server needs to run for the feature to work.

---

### Step 4: Test It! (2 minutes)

1. **Open your Shopify store** (in a new tab):
   ```
   https://parallelapparel-uofthacksdemo.myshopify.com?preview_theme_id=157618045186
   ```

2. **Log in as admin**

3. **Go to a collection page** (e.g., /collections/all)

4. **Look for the blue "Suggestions" tab** on the right edge of the screen

5. **Click it and try the feature**:
   - Click "Get Suggestion"
   - Review the clothing → shoe replacement
   - Click "Accept"
   - Check your browser console (F12) to see the API calls

---

## 🎯 How It Works

### Current Setup (LocalStorage + API Ready)

**Right now:**
- Changes persist in your browser (localStorage)
- API code is ready but commented out
- Works great for testing and demos

**When you click "Accept":**
1. ✅ Product is replaced on the page immediately
2. ✅ Replacement is saved to localStorage
3. ✅ Page refresh shows the replacement
4. ⚠️ Changes only visible to you (not other users)
5. ⚠️ API call happens but collection won't update yet (see below)

### Making Changes Visible to Everyone

The API server is ready, but there's one more thing needed:

**The Challenge:**
- Your theme runs on Shopify's servers (`parallelapparel-uofthacksdemo.myshopify.com`)
- Your API runs locally (`localhost:3000`)
- Browsers block cross-origin requests for security

**The Solution - Choose One:**

#### Option A: Use ngrok (Quick Testing - 5 min)
```bash
# In a new terminal
brew install ngrok  # or download from ngrok.com
ngrok http 3000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

Then update line 589 in `admin-product-suggestions.liquid`:
```javascript
const API_ENDPOINT = 'https://abc123.ngrok.io/api/replace-product';
```

Push the theme:
```bash
cd /Users/ronitlongia/Desktop/frontend/shopify-theme
shopify theme push --development --only sections/admin-product-suggestions.liquid
```

#### Option B: Deploy to Cloud (Production - 15 min)

Deploy to Heroku (free tier):
```bash
cd /Users/ronitlongia/Desktop/frontend/shopify-app
heroku create your-app-name
git init
git add .
git commit -m "Deploy Shopify API"
heroku config:set SHOPIFY_API_KEY=your_key
heroku config:set SHOPIFY_API_SECRET=your_secret
heroku config:set SHOPIFY_ACCESS_TOKEN=your_token
heroku config:set SHOPIFY_SHOP_DOMAIN=parallelapparel-uofthacksdemo.myshopify.com
git push heroku main
```

Then update line 589 with your Heroku URL.

---

## 📁 File Locations

- **Theme file**: `/Users/ronitlongia/Desktop/frontend/shopify-theme/sections/admin-product-suggestions.liquid`
- **API server**: `/Users/ronitlongia/Desktop/frontend/shopify-app/server.js`
- **Configuration**: `/Users/ronitlongia/Desktop/frontend/shopify-app/.env`
- **Documentation**: `/Users/ronitlongia/Desktop/frontend/shopify-app/README.md`

---

## 🐛 Troubleshooting

### "API sync failed, using localStorage only"
✅ **This is normal!** It means:
- LocalStorage is working (changes persist for you)
- API server isn't connected yet
- Follow Step 3 above to connect it

### "Access token is invalid"
- Double-check you copied the `shpat_` token correctly
- Make sure you installed the app in Step 1
- Try regenerating the token

### Server won't start
```bash
# Make sure you're in the right directory
cd /Users/ronitlongia/Desktop/frontend/shopify-app

# Reinstall dependencies
rm -rf node_modules
npm install

# Try again
npm start
```

### Can't see the Suggestions tab
- Make sure you're logged in as admin
- Make sure you're on a page with products
- Check the right side of your screen
- Try refreshing the page

---

## ✨ What You Can Do Now

**Without API (LocalStorage only):**
- ✅ Replace products on the page
- ✅ Changes persist across refreshes (for you only)
- ✅ Visual indicators show replacements
- ✅ Reset all changes button works

**With API Connected:**
- ✅ All of the above, PLUS:
- ✅ Changes are permanent in Shopify
- ✅ Everyone sees the changes
- ✅ Changes persist forever (not just in browser)
- ✅ Actually modifies your product collections

---

## 🎓 Need Help?

Check the detailed documentation:
```
/Users/ronitlongia/Desktop/frontend/shopify-app/README.md
```

Or check server logs:
```bash
cd /Users/ronitlongia/Desktop/frontend/shopify-app
npm start
# Watch for errors in the output
```

---

**You're all set!** 🎉 Follow Steps 1-3 above to make permanent product replacements.
