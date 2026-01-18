# TrendID - AI-Powered Trend Arbitrage for Shopify

A trend-arbitrage engine that identifies emerging social signals and "re-skins" Shopify vendors' products to embody specific internet subcultures. By attaching viral terminology to everyday items, we allow consumers to purchase the "status" of a trend before it reaches mainstream saturation.

## 💡 Inspiration

The inspiration came from observing the massive disconnect between digital velocity and physical retail. Trends like "Aura," the "Chill Guy," and the "Off-Duty CEO" create overnight demand for specific identities, yet traditional brands take months to react. We realized that any generic item could become a high-status asset if it were rebranded with the right "cultural code" at the exact moment a trend peaks.

## 🎯 What It Does

TrendID is a trend-arbitrage engine. We identify emerging social signals and "re-skin" Shopify vendors' products to embody a specific internet subculture. By attaching viral terminology to everyday items, we allow consumers to purchase the "status" of a trend before it reaches mainstream saturation.

## 🔧 How It Works

We use a comprehensive pipeline that processes trends end-to-end:

1. **Trend Discovery**: We begin by identifying seven metadata tags per call via API-based web scraping using Perplexity's Sonar API.

2. **Video Analysis**: These tags are fed into the YouTube Data API (Google Cloud), which scrapes two videos published within a short timeframe with the highest viewer/hour gross rate across these seven metrics.

3. **Semantic Analysis**: Videos are processed through TwelveLabs Pegasus 1.2 API to uncover video-based semantic insights—from scene descriptions to analysis of which actions place videos in trend territory.

4. **Data Structuring**: The output is a structured JSON file focusing on key trend aspects, paired with another JSON encapsulating all key Shopify store data including product types.

5. **AI Optimization**: This creates a semantic planning table pushed into MongoDB—the hive mind of marketable tweaks to maximize traction and sales.

6. **Autonomous Updates**: We use Shopify's Admin GraphQL API to autonomously update store pages with trend-aligned product descriptions, tags, and marketing copy.

## 🛠 Tech Stack

**Backend:**
- Python (Flask) - API and pipeline orchestration
- Node.js (Express) - Shopify API integration
- MongoDB Atlas - Trend and suggestion storage

**AI/ML:**
- TwelveLabs Pegasus 1.2 - Video semantic analysis
- Google Gemini - Content generation
- Perplexity Sonar API - Trend metadata scraping

**APIs:**
- YouTube Data API v3 (Google Cloud)
- Shopify Admin REST & GraphQL APIs

**Infrastructure:**
- Render - Node.js backend hosting
- Vercel - Frontend hosting
- MongoDB Atlas - Database

**Frontend:**
- React + TypeScript
- Shopify Polaris UI components
- Vite build system

## 🎨 Trend Categories

**Meme/Culture**: aura, chill guy, sigma, 365 buttons, demure, very mindful

**Food**: dubai chocolate, matcha, boba, crumbl cookie, tinned fish

**Aesthetic**: y2k, cottage core, dark academia, clean girl, mob wife, off-duty CEO

**Animals**: capybara, axolotl

**Lifestyle**: hot girl walk, that girl, glow up

**Pop Culture**: stanley cup, lululemon style

## 🏆 UofTHacks 2026

Built for UofTHacks 13 - combining AI, video analysis, and e-commerce automation to bridge the gap between viral trends and retail velocity.
