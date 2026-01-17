# YouTube Trending Shorts Analysis - Product Trend Finder

Automatically discover and analyze trending YouTube Shorts with product/merch potential using AI-powered video understanding. Perfect for identifying trends you can turn into t-shirts, merchandise, packaging, and accessories.

## Features

- 🎯 **Auto-Rotating Trends**: Automatically selects a different product-ready trend each run
- 🔥 **25+ Trending Keywords**: Curated from actual January 2026 TikTok/YouTube trends
- 🎥 **YouTube Shorts Only**: Analyzes videos ≤60 seconds (no music videos)
- 🤖 **AI-Powered Analysis**: Uses Twelve Labs AI for video understanding
- 📊 **Detailed Descriptions**: Shows what's happening in videos beyond just views/likes
- 💡 **Context-Based Trending**: Explains WHY videos are trending (not just engagement)
- 💰 **Product Potential**: Every trend has t-shirt/merch/packaging opportunities
- 📄 **Clean JSON Output**: Simple, focused reports for each trend

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
5. **Analyzes** with Twelve Labs AI
6. **Generates** detailed descriptions of what's happening
7. **Identifies** why they're trending (beyond views/likes)
8. **Exports** to JSON with trend name and product potential

### Output Format

```json
{
  "analysis_timestamp": "2026-01-17 08:01:22",
  "trend_analyzed": "matcha",
  "product_potential": "t-shirts, merch, accessories, packaging",
  "videos_analyzed": 3,
  "videos": [
    {
      "title": "How to make Iced Strawberry Matcha",
      "url": "https://www.youtube.com/watch?v=...",
      "channel": "Channel Name",
      "duration_seconds": 31,
      "what_is_happening": "This 'matcha' trend video shows...",
      "why_its_trending": [
        "part of the viral 'matcha' trend",
        "tutorial content"
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

## License

MIT License

## Contributing

Pull requests welcome! For major changes, please open an issue first.
