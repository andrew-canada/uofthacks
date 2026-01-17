# YouTube Trending Video Analysis with Twelve Labs AI

Analyze trending YouTube videos using AI-powered video understanding to identify visual content, objects, and determine why videos are trending.

## Features

- 🔥 Fetches currently trending videos from YouTube
- 🎥 Downloads and analyzes videos using Twelve Labs AI
- 🔍 Detects objects, people, animals, and visual elements in videos
- 📊 Generates detailed descriptions of video content
- 💡 Analyzes WHY videos are trending (events, collaborations, viral content, etc.)
- 📄 Exports comprehensive JSON reports with all findings

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

### Analyze Trending Videos

Run the main analysis script:

```bash
python analyze_trending_videos.py
```

This will:
1. Fetch 3 random trending videos from YouTube
2. Download each video
3. Upload to Twelve Labs for AI analysis
4. Detect objects and visual elements
5. Generate descriptions and trending analysis
6. Save results to `trending_analysis_<timestamp>.json`

### Output Format

The JSON output includes:

```json
{
  "analysis_timestamp": "2026-01-17 07:09:44",
  "videos_analyzed": 3,
  "trending_themes": [...],
  "individual_video_analysis": [
    {
      "title": "Video Title",
      "url": "YouTube URL",
      "views": 285531,
      "likes": 19312,
      "video_description": "Detailed description...",
      "video_type": "Music/Performance",
      "trending_reasons": ["the Super Bowl is upcoming", "collaboration between popular artists"],
      "engagement_rate": 6.76,
      "top_visual_elements": ["person", "music", "dancing"],
      "detected_objects": {
        "person": 3,
        "music": 2,
        ...
      }
    }
  ]
}
```

## Video Types Detected

- Music/Performance
- Sports/Gaming
- Food/Cooking
- Product/Review
- Celebrity/Entertainment
- Family/Kids
- Animals/Pets
- General Entertainment

## Trending Factors Analyzed

The system analyzes video context to determine trending reasons:

- **Event-based**: Super Bowl, Olympics, Grammy Awards, etc.
- **Celebrity**: Collaborations, new releases, official content
- **Viral content**: Giveaways, challenges, reactions, breaking news
- **Content type**: Live streams, trailers, exclusives

## Configuration

Edit the number of videos analyzed in `analyze_trending_videos.py`:

```python
num_videos = 3  # Change this to analyze more/fewer videos
```

Change region for trending videos:

```python
trending_videos = get_trending_videos(max_results=num_videos, region_code='US')
# Change 'US' to other country codes: 'CA', 'GB', 'JP', etc.
```

## Project Structure

```
uofthacks/
├── analyze_trending_videos.py  # Main analysis script
├── config_template.py           # Template for API keys
├── config.py                    # Your API keys (gitignored)
├── README.md                    # This file
├── .gitignore                   # Git ignore rules
└── trending_analysis_*.json     # Output files (gitignored)
```

## Notes

- Videos are randomized each run for variety
- Downloaded videos are automatically cleaned up after processing
- Rate limits: Twelve Labs has API rate limits - adjust delays if needed
- Processing time: Each video takes 1-2 minutes to analyze

## License

MIT License

## Contributing

Pull requests welcome! For major changes, please open an issue first.