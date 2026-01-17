# UofTHacks - Product Trend Finder & AI Optimizer

End-to-end platform for discovering viral YouTube Shorts trends and automatically generating optimized product designs for Shopify. Built with YouTube API, Twelve Labs AI, and LangGraph.

## 🎯 Project Overview

This platform helps you identify trending content on YouTube Shorts and turn those trends into profitable products:

1. **Trend Discovery** (Video Analysis): Automatically discovers and analyzes trending YouTube Shorts with product/merch potential
2. **Product Generation** (Backend): Uses AI to generate optimized product designs, descriptions, and pricing
3. **Shopify Integration** (Backend): Automatically creates products in your Shopify store

## 📁 Project Structure

```
uofthacks/
├── video_analysis/          # YouTube Shorts trend analysis
│   ├── analyze_trending_videos.py
│   ├── config_template.py
│   └── README.md
├── backend/                 # AI product generator & Shopify integration
│   ├── app.py
│   ├── services/
│   ├── graphs/              # LangGraph workflows
│   ├── routes/
│   └── README.md
├── venv/                    # Python virtual environment
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Video Analysis (Trend Discovery)

Analyzes trending YouTube Shorts and identifies product opportunities:

```bash
cd video_analysis
python3 -m venv venv
source venv/bin/activate
pip install requests pytubefix
cp config_template.py config.py
# Add your API keys to config.py
python analyze_trending_videos.py
```

**Features:**
- Auto-rotates through 25+ product-ready trends
- Filters for YouTube Shorts (≤60 seconds, no music)
- AI-powered analysis with Twelve Labs
- Outputs JSON with trend analysis

**See [video_analysis/README.md](video_analysis/README.md) for details**

### 2. Backend (Product Generation)

AI-powered product generator with Shopify integration:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Configure your API keys in .env
python app.py
```

**Features:**
- LangGraph AI workflow for product optimization
- Automatic product generation from trends
- Shopify API integration
- RESTful API endpoints

**See [backend/README.md](backend/README.md) for details**

## 🛠 Tech Stack

**Video Analysis:**
- Python 3.14+
- YouTube Data API v3
- Twelve Labs AI (video understanding)
- pytubefix (video download)

**Backend:**
- Python 3.14+
- Flask (REST API)
- LangGraph (AI workflows)
- Anthropic Claude (product generation)
- Shopify API
- YouTube Data API v3

## 🔑 Required API Keys

- **YouTube Data API**: https://console.cloud.google.com/apis/credentials
- **Twelve Labs API**: https://api.twelvelabs.io/
- **Anthropic API**: https://console.anthropic.com/
- **Shopify Admin API**: https://shopify.dev/docs/api/admin

## 📊 How It Works

1. **Trend Discovery**: Video analysis script searches YouTube Shorts for trending keywords (aura, matcha, chill guy, etc.)
2. **AI Analysis**: Twelve Labs analyzes video content to understand what's happening and why it's trending
3. **Product Generation**: Backend uses Claude AI to create product designs, descriptions, and pricing
4. **Optimization**: LangGraph workflow optimizes products for maximum conversion
5. **Publishing**: Automated Shopify integration creates products in your store

## 🎨 Product-Ready Trends

**Meme/Culture**: aura, chill guy, sigma, 365 buttons, demure, very mindful

**Food**: dubai chocolate, matcha, boba, crumbl cookie, tinned fish

**Aesthetic**: y2k, cottage core, dark academia, clean girl, mob wife

**Animals**: capybara, axolotl

**Lifestyle**: hot girl walk, that girl, glow up

**Pop Culture**: stanley cup, lululemon style

## 📝 License

MIT License

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first.

## 🏆 UofTHacks 2026

Built for UofTHacks - combining AI, video analysis, and e-commerce automation.
