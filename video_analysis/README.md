# YouTube Trending Shorts Analysis - Product Trend Finder

Automatically discover and analyze trending YouTube Shorts with product/merch potential using AI-powered video understanding. Perfect for identifying trends you can turn into t-shirts, merchandise, packaging, and accessories.

## Features

- 🎯 **Auto-Rotating Trends**: Automatically selects a different product-ready trend each run
- 🔥 **25+ Trending Keywords**: Curated from actual January 2026 TikTok/YouTube trends
- 🎥 **YouTube Shorts Only**: Analyzes videos ≤60 seconds (no music videos)
- 🤖 **AI-Powered Analysis**: Uses Twelve Labs AI for video understanding
- 📊 **Intelligent Descriptions**: Generates detailed "what is happening" descriptions using title parsing and AI analysis
- 💡 **Context-Based Trending**: Explains WHY videos are trending (not just engagement)
- 💰 **Product Potential**: Every trend has t-shirt/merch/packaging opportunities
- 📄 **Comprehensive JSON Output**: Full trend analysis with keywords, products, demographics, hashtags

## Product-Ready Trends Included

The script automatically rotates through these trending categories:

**Meme/Culture Trends** (apparel): aura, chill guy, sigma, 365 buttons, demure, very mindful

**Food Trends** (packaging/merch): dubai chocolate, matcha, boba, crumbl cookie, tinned fish

**Aesthetic Trends** (apparel/accessories): y2k, cottage core, dark academia, clean girl, mob wife

**Animal Trends** (apparel): capybara, axolotl

**Lifestyle Trends** (apparel): hot girl walk, that girl, glow up

**Pop Culture** (merch): stanley cup, lululemon style

## Setup

### Prerequisites

- Python 3.14+
- YouTube Data API key
- Twelve Labs API key

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd uofthacks
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install requests pytubefix
```

4. Configure API keys:
```bash
cp config_template.py config.py
```

Edit `config.py` and add your API keys:
- Get Twelve Labs API key: https://api.twelvelabs.io/
- Get YouTube Data API key: https://console.cloud.google.com/apis/credentials

## Usage

Run the analysis script - it automatically picks a new trend each time:

```bash
python analyze_trending_videos.py
```

**Example runs:**
- Run 1: Analyzes "aura" trend → finds sigma male meme videos
- Run 2: Analyzes "tinned fish" trend → finds sardine recipe videos
- Run 3: Analyzes "matcha" trend → finds matcha latte videos
- Run 4: Analyzes a different trend from the 25+ keyword list

### How It Works

Each run:
1. **Selects** a random product-ready trend (avoids last 5 used)
2. **Searches** YouTube for Shorts matching that trend
3. **Filters** for videos ≤60 seconds (excludes music)
4. **Downloads** 3 random Shorts from results
5. **Analyzes** with Twelve Labs AI (visual elements + optional summarization)
6. **Generates** detailed "what is happening" descriptions through intelligent title parsing
7. **Identifies** keywords, target products, demographics, and hashtags
8. **Exports** comprehensive trend analysis to JSON

### Output Format

The script generates comprehensive trend analysis in JSON format:

```json
{
  "id": "trend_matcha",
  "name": "Matcha",
  "description": "Matcha trend featuring matcha, drinks, aesthetic content...",
  "keywords": ["matcha", "aesthetic", "drink", "wellness", "trendy"],
  "color_palette": ["green", "neutral", "pastel tones"],
  "target_products": ["drink packaging", "tote bags", "aesthetic apparel", "minimalist merch"],
  "marketing_angle": "Focus on wellness, aesthetics, and trendy lifestyle...",
  "popularity_score": 85,
  "platforms": ["TikTok", "Instagram", "Pinterest"],
  "demographics": ["Millennials", "Gen Z", "Women 18-35"],
  "hashtags": ["#matcha", "#aesthetic", "#wellness", "#matchalatte"],
  "sample_videos": [
    {
      "title": "How to make Iced Strawberry Matcha",
      "url": "https://www.youtube.com/watch?v=...",
      "views": 1500000,
      "likes": 85000,
      "what_is_happening": "This video demonstrates a recipe about matcha drinks and aesthetic lifestyle.",
      "why_its_trending": [
        "part of the viral 'matcha' trend",
        "high engagement and shareability",
        "relatable content format"
      ]
    }
  ]
}
```

## Configuration

### Number of Videos

Edit in [analyze_trending_videos.py:449](analyze_trending_videos.py#L449):
```python
num_videos = 3  # Analyze more/fewer Shorts per trend
```

### Add Your Own Trends

Edit the `get_product_trend_keywords()` function in [analyze_trending_videos.py:360](analyze_trending_videos.py#L360) to add custom trends:
```python
product_trends = [
    "your custom trend",
    "another trend",
    # ... existing trends
]
```

## Project Structure

```
uofthacks/
├── analyze_trending_videos.py  # Main analysis script
├── config_template.py           # Template for API keys
├── config.py                    # Your API keys (gitignored)
├── .trend_history.txt           # Tracks used trends (gitignored)
├── README.md                    # This file
├── SETUP_INSTRUCTIONS.md        # Quick setup guide
├── .gitignore                   # Git ignore rules
└── trending_analysis_*.json     # Output files (gitignored)
```

## How Trends Are Selected

- **First 5 runs**: Random selection from all 25+ trends
- **After 5 runs**: Won't repeat last 5 trends used
- **After all used**: Resets and starts fresh rotation
- **Tracking**: `.trend_history.txt` keeps history (gitignored)

## Notes

- **Processing time**: 1-2 minutes per Short (3-6 min total per run)
- **Rate limits**: Twelve Labs API has limits - script includes delays
- **Randomization**: Different Shorts selected from each trend every run
- **Auto-cleanup**: Downloaded videos deleted after processing
- **API costs**: ~3 video analyses per run
- **Video descriptions**: Generated through intelligent title parsing (matching actions like "ranking", "tutorial", "how to" with subjects like "aura", "glow up", "matcha"). Falls back to Twelve Labs summarization API when available and within rate limits.

## License

MIT License

## Contributing

Pull requests welcome! For major changes, please open an issue first.
