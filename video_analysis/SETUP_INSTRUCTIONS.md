# Setup Instructions

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd uofthacks
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install requests pytubefix
   ```

4. **Setup API keys**
   ```bash
   cp config_template.py config.py
   ```
   
   Then edit `config.py` and replace:
   - `your_twelve_labs_api_key_here` with your Twelve Labs API key
   - `your_youtube_api_key_here` with your YouTube Data API key

5. **Run the analysis**
   ```bash
   python analyze_trending_videos.py
   ```

## Getting API Keys

### Twelve Labs API Key
1. Go to https://api.twelvelabs.io/
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to `config.py`

### YouTube Data API Key
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable YouTube Data API v3
4. Go to Credentials → Create Credentials → API Key
5. Copy the key to `config.py`

## What Gets Analyzed

The script will:
- Fetch 3 random trending videos
- Download each video (then delete after processing)
- Upload to Twelve Labs for AI analysis
- Detect objects, people, scenes
- Determine WHY the video is trending
- Generate a JSON report with all findings

## Output

Results are saved to `trending_analysis_<timestamp>.json` with:
- Video descriptions
- Detected objects
- Trending reasons (events, collaborations, viral factors)
- Engagement metrics
- Visual elements breakdown
