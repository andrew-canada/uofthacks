import requests
import time
import os
import json
from pytubefix import YouTube
from collections import Counter

# Import API keys from config file
try:
    from config import TWELVE_LABS_API_KEY, YOUTUBE_API_KEY, TWELVE_LABS_BASE_URL
except ImportError:
    print("Error: config.py not found!")
    print("Please copy config_template.py to config.py and add your API keys.")
    exit(1)

def parse_duration(duration_str):
    """Parse ISO 8601 duration format (PT#M#S) to seconds"""
    import re
    # Pattern: PT1M30S = 1 minute 30 seconds
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)

    if not match:
        return 0

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    return hours * 3600 + minutes * 60 + seconds

def search_trending_shorts_by_keyword(keyword, max_results=5):
    """Search for trending Shorts by keyword"""
    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        'part': 'snippet',
        'q': keyword,
        'type': 'video',
        'videoDuration': 'short',  # Videos under 4 minutes
        'maxResults': 50,
        'order': 'viewCount',  # Most viewed
        'key': YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    search_data = response.json()

    # Get video IDs
    video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]

    if not video_ids:
        return []

    # Get full details for these videos
    details_url = "https://www.googleapis.com/youtube/v3/videos"
    details_params = {
        'part': 'snippet,statistics,contentDetails',
        'id': ','.join(video_ids),
        'key': YOUTUBE_API_KEY
    }

    details_response = requests.get(details_url, params=details_params)
    details_response.raise_for_status()
    return details_response.json()

def get_trending_videos(max_results=5, region_code='US', trend_filter=None):
    """Get currently trending YouTube Shorts (excluding music videos)"""

    # If trend_filter specified, search by keyword instead of trending chart
    if trend_filter:
        data = search_trending_shorts_by_keyword(trend_filter, max_results)
    else:
        url = "https://www.googleapis.com/youtube/v3/videos"
        fetch_count = 50

        params = {
            'part': 'snippet,statistics,contentDetails',
            'chart': 'mostPopular',
            'regionCode': region_code,
            'maxResults': fetch_count,
            'videoCategoryId': '0',
            'key': YOUTUBE_API_KEY
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    print(f"\n{'='*60}")
    if trend_filter:
        print(f"Searching for YouTube Shorts - '{trend_filter.upper()}' Trend")
    else:
        print(f"Fetching Trending YouTube Shorts (Non-Music)")
    print(f"{'='*60}\n")

    all_shorts = []
    for item in data.get('items', []):
        # Get duration
        duration_str = item['contentDetails'].get('duration', 'PT0S')
        duration_seconds = parse_duration(duration_str)

        # Get category (10 = Music, 24 = Entertainment)
        category_id = item['snippet']['categoryId']

        # Filter: Only Shorts (<=60 seconds) and NOT music videos
        is_short = duration_seconds <= 60 and duration_seconds > 0
        is_music_category = category_id == '10'

        # Also check title/description for music indicators
        title_lower = item['snippet']['title'].lower()
        description_lower = item['snippet'].get('description', '').lower()

        is_music_video = (
            'official music video' in title_lower or
            'music video' in title_lower or
            'official video' in title_lower
        )

        if is_short and not is_music_category and not is_music_video:
            video_info = {
                'video_id': item['id'],
                'url': f"https://www.youtube.com/watch?v={item['id']}",
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'description': item['snippet'].get('description', ''),
                'views': int(item['statistics'].get('viewCount', 0)),
                'likes': int(item['statistics'].get('likeCount', 0)),
                'comments': int(item['statistics'].get('commentCount', 0)),
                'published_at': item['snippet']['publishedAt'],
                'category_id': category_id,
                'tags': item['snippet'].get('tags', []),
                'duration_seconds': duration_seconds
            }
            all_shorts.append(video_info)

    filter_msg = f" matching '{trend_filter}' trend" if trend_filter else ""
    source_msg = f"searched videos" if trend_filter else f"trending videos"
    print(f"Found {len(all_shorts)} YouTube Shorts{filter_msg} (from {source_msg})")

    if len(all_shorts) == 0:
        print(f"\n⚠️  No YouTube Shorts found{filter_msg}!")
        print("Try running again or adjust filters.\n")
        return []

    # Randomly sample videos for variety each run
    import random
    selected_videos = random.sample(all_shorts, min(max_results, len(all_shorts)))

    print(f"\nSelected {len(selected_videos)} Shorts for analysis:\n")
    for video_info in selected_videos:
        print(f"✓ {video_info['title']}")
        print(f"  Duration: {video_info['duration_seconds']}s | Views: {video_info['views']:,} | Likes: {video_info['likes']:,}")
        print(f"  URL: {video_info['url']}\n")

    return selected_videos

def download_video_with_pytube(video_url, output_name):
    """Download video using pytube"""
    try:
        yt = YouTube(video_url)

        # Get the lowest resolution stream to make it faster
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').first()

        if not stream:
            stream = yt.streams.filter(file_extension='mp4').first()

        print(f"  Downloading: {yt.title[:50]}...")
        print(f"  Resolution: {stream.resolution}, Size: {stream.filesize / 1024 / 1024:.2f} MB")

        stream.download(filename=output_name)
        return output_name
    except Exception as e:
        print(f"  Error downloading: {e}")
        return None

def create_index():
    """Create a Twelve Labs index"""
    url = f"{TWELVE_LABS_BASE_URL}/indexes"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "index_name": f"trending_analysis_{int(time.time())}",
        "models": [
            {
                "model_name": "marengo3.0",
                "model_options": ["visual", "audio"]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error: {response.text}")
    response.raise_for_status()

    index_id = response.json()['_id']
    return index_id

def upload_video_to_twelve_labs(index_id, video_path):
    """Upload video file to Twelve Labs"""
    url = f"{TWELVE_LABS_BASE_URL}/tasks"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    with open(video_path, 'rb') as video_file:
        files = {
            'video_file': (os.path.basename(video_path), video_file, 'video/mp4'),
        }
        data = {
            'index_id': index_id,
            'language': 'en'
        }

        response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code != 201:
            print(f"  Error: {response.text}")
            return None

        task_id = response.json()['_id']
        return task_id

def wait_for_processing(task_id):
    """Wait for video processing to complete"""
    url = f"{TWELVE_LABS_BASE_URL}/tasks/{task_id}"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    while True:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        status = response.json()['status']

        if status == 'ready':
            video_id = response.json()['video_id']
            return video_id
        elif status == 'failed':
            print("  Processing failed!")
            return None

        time.sleep(3)

def analyze_video_objects(index_id):
    """Analyze video for objects and themes"""
    url = f"{TWELVE_LABS_BASE_URL}/search"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    # Comprehensive object detection queries
    detection_queries = [
        "person", "people", "crowd",
        "animal", "pet", "dog", "cat",
        "car", "vehicle", "transportation",
        "food", "cooking", "eating",
        "sports", "game", "competition",
        "music", "dancing", "performance",
        "technology", "phone", "computer",
        "nature", "outdoor", "landscape",
        "indoor", "home", "room",
        "product", "shopping", "unboxing",
        "children", "baby", "kids",
        "celebrity", "famous person",
        "action", "movement", "activity",
        "text", "words", "graphics"
    ]

    detected_elements = {}

    for query in detection_queries:
        files = {
            "query_text": (None, query),
            "index_id": (None, index_id),
            "search_options": (None, "visual"),
            "page_limit": (None, "3")
        }

        try:
            response = requests.post(url, headers=headers, files=files)

            if response.status_code == 200:
                results = response.json()
                count = len(results.get('data', []))
                if count > 0:
                    detected_elements[query] = {
                        'segment_count': count,
                        'timestamps': [
                            {'start': r.get('start', 0), 'end': r.get('end', 0)}
                            for r in results.get('data', [])
                        ]
                    }

            # Small delay to avoid rate limiting
            time.sleep(0.5)
        except Exception as e:
            print(f"  Error analyzing '{query}': {e}")
            continue

    return detected_elements

def analyze_trending_context(video_info):
    """Analyze why the video is trending based on title, tags, and description"""
    title_lower = video_info['title'].lower()
    description_lower = video_info['description'].lower()
    tags_lower = [tag.lower() for tag in video_info.get('tags', [])]
    all_text = f"{title_lower} {description_lower} {' '.join(tags_lower)}"

    trending_reasons = []

    # Event-based trending
    events = {
        'super bowl': 'the Super Bowl is upcoming',
        'superbowl': 'the Super Bowl is upcoming',
        'nfl': 'NFL season/events',
        'nba': 'NBA season activity',
        'world cup': 'World Cup events',
        'olympics': 'Olympic events',
        'grammy': 'Grammy Awards season',
        'oscar': 'Oscar Awards season',
        'emmy': 'Emmy Awards season',
        'election': 'current election cycle',
        'presidential': 'political campaign season',
        'trailer': 'new movie/show trailer release',
        'official': 'official release or announcement',
        'halftime': 'major sporting event halftime show',
        'playoff': 'playoff season',
        'championship': 'championship events'
    }

    for keyword, reason in events.items():
        if keyword in all_text:
            trending_reasons.append(reason)
            break  # Take first match

    # Celebrity/Artist trending
    celebrity_indicators = ['ft ', 'feat', 'featuring', 'official music video', 'music video']
    if any(indicator in all_text for indicator in celebrity_indicators):
        # Extract artist names from title
        if 'ft ' in title_lower or 'feat' in title_lower:
            trending_reasons.append(f"collaboration between popular artists")
        elif 'official' in title_lower and 'music' in title_lower:
            trending_reasons.append("new music release from popular artist")

    # Viral/Entertainment content
    viral_keywords = {
        'live': 'live streaming content',
        'giveaway': 'giveaway/contest attracting viewers',
        'free': 'free content offer',
        'breaking': 'breaking news or announcement',
        'exclusive': 'exclusive content release',
        'first': 'first look or premiere',
        'leaked': 'leaked content generating buzz',
        'reaction': 'reaction video trend',
        'challenge': 'viral challenge participation',
        'tutorial': 'educational/how-to content',
        'review': 'product review interest',
        'unboxing': 'unboxing trend',
        'prank': 'prank/comedy content',
        'exposed': 'exposé or revelation',
        'drama': 'drama or controversy'
    }

    for keyword, reason in viral_keywords.items():
        if keyword in all_text and reason not in trending_reasons:
            trending_reasons.append(reason)

    # If no specific reason found, analyze general appeal
    if not trending_reasons:
        if 'official' in all_text:
            trending_reasons.append("official content from verified source")
        else:
            trending_reasons.append("general viral appeal and shareability")

    return trending_reasons

def generate_video_description(video_info, detected_elements, index_id, video_id, trend_keyword):
    """Generate a specific description of what's in the video and why it's trending"""

    # Sort elements by prevalence to understand the video
    sorted_elements = sorted(
        detected_elements.items(),
        key=lambda x: x[1]['segment_count'],
        reverse=True
    )

    # Build a detailed description based on detected elements
    description_parts = []

    # Check for people/characters
    people_elements = [e for e in sorted_elements if e[0] in ['person', 'people', 'crowd', 'celebrity', 'famous person']]
    if people_elements:
        description_parts.append(f"featuring {people_elements[0][0]}")

    # Check for actions/activities
    action_elements = [e for e in sorted_elements if e[0] in ['action', 'movement', 'activity', 'dancing', 'sports', 'game', 'performance']]
    if action_elements:
        activities = ', '.join([e[0] for e in action_elements[:2]])
        description_parts.append(f"engaged in {activities}")

    # Check for setting
    setting_elements = [e for e in sorted_elements if e[0] in ['indoor', 'outdoor', 'nature', 'landscape', 'home', 'room']]
    if setting_elements:
        description_parts.append(f"in an {setting_elements[0][0]} setting")

    # Check for specific objects/themes
    object_elements = [e for e in sorted_elements if e[0] in ['car', 'vehicle', 'food', 'animal', 'pet', 'phone', 'computer', 'product']]
    if object_elements:
        objects = ', '.join([e[0] for e in object_elements[:2]])
        description_parts.append(f"with {objects}")

    # Check for text/graphics
    text_elements = [e for e in sorted_elements if e[0] in ['text', 'words', 'graphics']]
    if text_elements:
        description_parts.append("and text overlays")

    # Build final description
    title = video_info['title']
    tags = video_info.get('tags', [])

    if description_parts:
        description = f"This '{trend_keyword}' trend video shows a short-form clip {' '.join(description_parts)}. "
    else:
        description = f"This is a '{trend_keyword}' trend video titled '{title}'. "

    # Add context based on title keywords
    title_lower = title.lower()
    description += f"The video relates to the current '{trend_keyword}' trend through its content and presentation style."

    # Analyze contextual trending reasons (non-engagement based)
    trending_reasons = analyze_trending_context(video_info)

    # Add trend-specific reason if not already present
    trend_lower = trend_keyword.lower()
    if not any(trend_lower in r.lower() for r in trending_reasons):
        trending_reasons.insert(0, f"part of the viral '{trend_keyword}' trend")

    return {
        'what_is_happening': description,
        'why_its_trending': trending_reasons if trending_reasons else ['viral short-form content appeal']
    }

def get_product_trend_keywords():
    """
    Get list of current trending keywords with product/merch potential.
    Based on actual TikTok/YouTube trends from January 2026.
    """
    # Product-ready trends (can make t-shirts, merch, accessories, food products)
    product_trends = [
        # Viral meme trends (apparel potential)
        "aura",
        "chill guy",
        "sigma",
        "365 buttons",
        "demure",
        "very mindful",

        # Food trends (packaging, merchandise)
        "dubai chocolate",
        "matcha",
        "boba",
        "crumbl cookie",
        "tinned fish",

        # Aesthetic/fashion trends (apparel, accessories)
        "y2k",
        "cottage core",
        "dark academia",
        "clean girl",
        "mob wife",

        # Animal trends (apparel, accessories)
        "capybara",
        "axolotl",

        # Lifestyle trends (apparel, accessories)
        "hot girl walk",
        "that girl",
        "glow up",

        # Pop culture (apparel potential)
        "stanley cup",
        "lululemon style",
    ]

    return product_trends

def select_random_trend():
    """Select a random product trend, avoiding recent repeats"""
    trends = get_product_trend_keywords()

    # Track previously used trends to ensure variety
    history_file = ".trend_history.txt"
    used_trends = []

    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            used_trends = [line.strip() for line in f.readlines()]

    # Filter out recently used trends (last 5)
    recent_trends = used_trends[-5:] if len(used_trends) >= 5 else used_trends
    available_trends = [t for t in trends if t not in recent_trends]

    # If all trends used recently, reset
    if not available_trends:
        available_trends = trends
        used_trends = []

    # Select random trend
    import random
    selected_trend = random.choice(available_trends)

    # Update history
    used_trends.append(selected_trend)
    with open(history_file, 'w') as f:
        f.write('\n'.join(used_trends))

    return selected_trend

def main():
    print("\n" + "="*60)
    print("YOUTUBE TRENDING SHORTS - PRODUCT TREND ANALYSIS")
    print("="*60)

    # Step 1: Select a random product-ready trend
    selected_trend = select_random_trend()
    print(f"\n🎯 ANALYZING TREND: '{selected_trend.upper()}'")
    print(f"💡 Product Potential: T-shirts, merch, accessories, packaging")
    print(f"{'='*60}")

    # Get trending Shorts for this trend
    num_videos = 3  # Analyze top 3 trending videos
    trending_videos = get_trending_videos(max_results=num_videos, trend_filter=selected_trend)

    if not trending_videos:
        print("No trending videos found!")
        return

    # Step 2: Create Twelve Labs index
    print(f"\n{'='*60}")
    print("Creating Twelve Labs Index")
    print(f"{'='*60}\n")
    index_id = create_index()
    print(f"Index created: {index_id}\n")

    # Step 3: Analyze each trending video
    analysis_results = []

    for i, video_info in enumerate(trending_videos, 1):
        print(f"\n{'='*60}")
        print(f"Analyzing Video {i}/{num_videos}: {video_info['title'][:50]}...")
        print(f"{'='*60}")

        # Download video
        video_filename = f"trending_{i}.mp4"
        print(f"\n1. Downloading video...")
        video_path = download_video_with_pytube(video_info['url'], video_filename)

        if not video_path:
            print("  Skipping due to download error")
            continue

        # Upload to Twelve Labs
        print(f"\n2. Uploading to Twelve Labs...")
        task_id = upload_video_to_twelve_labs(index_id, video_path)

        if not task_id:
            os.remove(video_path)
            continue

        # Wait for processing
        print(f"\n3. Processing video (this may take a minute)...")
        video_id = wait_for_processing(task_id)

        if video_id:
            print(f"  ✓ Processing complete!")

            # Analyze objects
            print(f"\n4. Analyzing video content...")
            detected_elements = analyze_video_objects(index_id)

            # Generate detailed description
            print(f"\n5. Generating video description and trending analysis...")
            video_description_analysis = generate_video_description(video_info, detected_elements, index_id, video_id, selected_trend)

            # Build analysis result
            video_analysis = {
                'video_info': video_info,
                'description_analysis': video_description_analysis
            }

            analysis_results.append(video_analysis)

            print(f"\n  📝 What's Happening:")
            print(f"      {video_description_analysis['what_is_happening'][:150]}...")

            print(f"\n  🔥 Why It's Trending:")
            for reason in video_description_analysis['why_its_trending']:
                print(f"    • {reason}")

        # Clean up video file
        if os.path.exists(video_path):
            os.remove(video_path)

    # Step 4: Create simplified final report
    print(f"\n\n{'='*60}")
    print("TREND ANALYSIS SUMMARY")
    print(f"{'='*60}\n")

    final_report = {
        'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'trend_analyzed': selected_trend,
        'product_potential': 't-shirts, merch, accessories, packaging',
        'videos_analyzed': len(analysis_results),
        'videos': [
            {
                'title': r['video_info']['title'],
                'url': r['video_info']['url'],
                'channel': r['video_info']['channel'],
                'duration_seconds': r['video_info']['duration_seconds'],
                'what_is_happening': r['description_analysis']['what_is_happening'],
                'why_its_trending': r['description_analysis']['why_its_trending']
            }
            for r in analysis_results
        ]
    }

    # Print summary
    print(f"🔥 ANALYZED {len(analysis_results)} '{selected_trend.upper()}' TREND VIDEOS")
    for i, video in enumerate(final_report['videos'], 1):
        print(f"\n  Video {i}: {video['title'][:50]}...")
        print(f"  Why trending: {', '.join(video['why_its_trending'])}")

    # Save to JSON
    output_file = f"trending_analysis_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump(final_report, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ Analysis complete! Results saved to: {output_file}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
