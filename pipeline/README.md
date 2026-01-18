# Pipeline Documentation

## Overview

This pipeline analyzes Gen Z social media trends and generates SEO-optimized recommendations for your Shopify store.

## Pipeline Flow

```
1. Perplexity API → Fetch 10 Gen Z trends (last 2 weeks)
                     ↓
2. YouTube API → Search for trending short videos
                     ↓
3. Twelve Labs → Analyze video content (visual + audio)
                     ↓
4. Save to JSON → twelve_labs_analysis.json (no MongoDB)
                     ↓
5. Gemini AI → Combine Twelve Labs + Shopify products
                     ↓
6. Generate → gemini_recommendations.json (structured output)
                     ↓
7. MongoDB → Store only Gemini recommendations
```

## Setup

### 1. Configure API Keys

Edit `pipeline/video_analysis/config.py` and add your Gemini API key:

```python
GEMINI_API_KEY = "your-actual-gemini-api-key"
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

All other API keys are already configured:
- ✓ Twelve Labs API Key
- ✓ YouTube Data API Key
- ✓ Perplexity API Key
- ✓ MongoDB Connection String

### 2. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Ensure Shopify Export Exists

Make sure you have a `shop_export.json` file in the pipeline directory with your Shopify products.

If you don't have it, run the extraction script:

```bash
cd pipeline
python extraction.py
```

## Running the Pipeline

```bash
cd pipeline
python pipeline.py
```

## Output Files

### 1. `twelve_labs_analysis.json`

Raw video analysis from Twelve Labs:

```json
{
  "analysis_date": "2026-01-18T14:30:00",
  "trends": [
    {
      "trend_id": 1,
      "name": "Coastal Grandmother Aesthetic",
      "description": "...",
      "platform": "TikTok",
      "viral_metric": "2.3B views",
      "emergence_date": "Jan 5, 2026",
      "marketability": "High - fashion/lifestyle",
      "analyzed_videos": [
        {
          "title": "Coastal grandma morning routine",
          "url": "https://youtube.com/...",
          "what_is_happening": "Person in linen outfit preparing tea...",
          "why_its_trending": [
            "Nostalgia for simpler times",
            "Aesthetic lighting and colors",
            "Relatable lifestyle content"
          ]
        }
      ]
    }
  ]
}
```

### 2. `gemini_recommendations.json`

SEO-optimized recommendations from Gemini:

```json
{
  "trends": [
    {
      "id": "1",
      "name": "Coastal Grandmother Aesthetic",
      "description": "Trend focusing on relaxed, sophisticated lifestyle...",
      "keywords": [
        "coastal grandmother",
        "linen fashion",
        "cottage core",
        "relaxed aesthetic"
      ],
      "color_palette": ["#F5F5DC", "#E8DCC4", "#A8B5C1", "#6B8E95"],
      "target_products": [
        "Linen Blend Oversized Shirt",
        "Natural Woven Basket Bag"
      ],
      "marketing_angle": "Embrace timeless elegance with our curated collection",
      "popularity_score": 87,
      "platforms": ["TikTok", "Instagram", "Pinterest"],
      "demographics": ["Gen Z", "Millennials", "Ages 18-35"],
      "hashtags": [
        "#coastalgrandmother",
        "#linenfashion",
        "#cottagecore"
      ]
    }
  ],
  "last_updated": "2026-01-18T15:45:00",
  "source": "Gemini Analysis",
  "version": "1.0"
}
```

### 3. MongoDB Collection: `recommendations`

The `gemini_recommendations.json` is stored in MongoDB in the `thewinningteam` database, `recommendations` collection.

Each run overwrites the previous recommendations to keep data fresh.

## Key Features

### No MongoDB in Trend Analysis
- Twelve Labs results are saved directly to JSON
- No database overhead during video analysis
- Easy to debug and inspect intermediate results

### Structured Gemini Output
- Gemini receives full context (trends + products)
- Outputs exact schema needed for Shopify integration
- Includes SEO keywords, hashtags, and product matching

### SEO-Ready Data
- Keywords extracted from actual video content
- Hashtags for social media marketing
- Color palettes from trend aesthetics
- Product-trend alignment
- Demographic targeting

## Pipeline Configuration

Edit constants in `pipeline.py`:

```python
ANALYZED_VIDEOS_COUNT_AT_A_TIME = 1  # Videos to analyze per trend
TRENDS_IDENTIFIED_COUNT_AT_A_TIME = 10  # Trends to fetch from Perplexity
```

## Troubleshooting

### Gemini API Error
- Make sure you set `GEMINI_API_KEY` in `config.py`
- Get your key from: https://aistudio.google.com/app/apikey

### Shopify Export Missing
- Run `python extraction.py` to generate `shop_export.json`
- Make sure you have valid Shopify API credentials

### MongoDB Connection Error
- Verify `MONGODB_CONNECTION_STRING` in `config.py`
- Check your network connection to MongoDB Atlas

### Twelve Labs API Quota
- Pipeline uses 1 video per trend by default
- Multiple API keys are configured for load balancing
- Adjust `ANALYZED_VIDEOS_COUNT_AT_A_TIME` to reduce usage

## Next Steps

After running the pipeline:

1. **Review recommendations**: Check `gemini_recommendations.json`
2. **Apply to Shopify**: Use the backend API to update product metadata
3. **Implement SEO**: Use keywords and hashtags in product descriptions
4. **Update store design**: Apply color palettes and marketing angles
5. **Monitor results**: Track which trend-product matches perform best
