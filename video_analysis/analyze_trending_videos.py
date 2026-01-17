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

def get_detailed_video_description(index_id, video_id):
    """
    Get detailed description of what's happening in the video using Twelve Labs summarize.
    Note: This endpoint may have rate limits. Fallback to title-based description if unavailable.
    """

    # Create a summarize task
    url = f"{TWELVE_LABS_BASE_URL}/summarize"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "video_id": video_id,
        "type": "summary"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        # Handle rate limiting
        if response.status_code == 429:
            return None  # Will fall back to title-based description

        if response.status_code in [200, 201]:
            result = response.json()
            task_id = result.get('_id')

            if task_id:
                # Poll for completion (max 15 seconds to avoid long waits)
                for _ in range(15):
                    status_url = f"{TWELVE_LABS_BASE_URL}/summarize/{task_id}"
                    status_response = requests.get(status_url, headers=headers)

                    if status_response.status_code == 200:
                        status_data = status_response.json()

                        if status_data.get('status') == 'ready':
                            summary = status_data.get('summary', '')
                            if summary:
                                return summary.strip()
                            break
                        elif status_data.get('status') == 'failed':
                            break

                    time.sleep(1)

    except Exception as e:
        pass  # Silently fall back to title-based description

    return None

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

def extract_colors_from_elements(detected_elements):
    """Extract color information from detected visual elements"""
    colors = []

    # Common color-related keywords to search for
    color_keywords = {
        'red': 'red', 'pink': 'pink', 'hot pink': 'hot pink',
        'blue': 'blue', 'navy': 'navy blue', 'electric blue': 'electric blue',
        'yellow': 'yellow', 'sunshine': 'sunshine yellow',
        'green': 'green', 'lime': 'lime green', 'neon': 'neon green',
        'orange': 'orange', 'purple': 'purple', 'black': 'black',
        'white': 'white', 'brown': 'brown', 'gold': 'gold',
        'bright': 'bright colors', 'colorful': 'vibrant colors',
        'pastel': 'pastel tones', 'dark': 'dark tones'
    }

    # Detect colors from visual elements (you can enhance this with actual color detection)
    for element in detected_elements.keys():
        for keyword, color_name in color_keywords.items():
            if keyword in element.lower() and color_name not in colors:
                colors.append(color_name)

    # Default color palette if none detected
    if not colors:
        colors = ["neutral", "modern tones", "versatile palette"]

    return colors[:5]  # Return top 5 colors

def extract_keywords_from_trend(trend_keyword, detected_elements, video_infos):
    """Extract descriptive keywords for the trend"""
    keywords = []

    # Base keywords from trend name
    trend_words = trend_keyword.lower().split()
    keywords.extend(trend_words)

    # Extract from detected elements
    visual_descriptors = []
    for element in detected_elements.keys():
        if element in ['person', 'people', 'dancing', 'performance', 'action', 'movement']:
            visual_descriptors.append('energetic')
        if element in ['food', 'cooking', 'eating']:
            visual_descriptors.append('culinary')
        if element in ['outdoor', 'nature', 'landscape']:
            visual_descriptors.append('natural')
        if element in ['text', 'graphics']:
            visual_descriptors.append('bold')
            visual_descriptors.append('expressive')

    keywords.extend(list(set(visual_descriptors)))

    # Add common trend descriptors
    trend_descriptors = {
        'aura': ['confident', 'dominant', 'powerful', 'impressive', 'stoic'],
        'matcha': ['healthy', 'aesthetic', 'calming', 'trendy', 'green'],
        'glow up': ['transformation', 'beauty', 'self-improvement', 'before-after', 'inspiring'],
        'chill guy': ['relaxed', 'laid-back', 'casual', 'meme', 'humorous'],
        'sigma': ['independent', 'masculine', 'alpha', 'confident', 'self-reliant'],
        'dubai chocolate': ['luxury', 'viral', 'exotic', 'indulgent', 'premium'],
        'boba': ['sweet', 'aesthetic', 'Asian', 'trendy', 'photogenic'],
        'capybara': ['cute', 'wholesome', 'calm', 'animal', 'peaceful'],
        'y2k': ['nostalgic', '2000s', 'retro', 'colorful', 'futuristic'],
        'cottage core': ['rustic', 'natural', 'cozy', 'vintage', 'pastoral'],
        'dark academia': ['scholarly', 'vintage', 'intellectual', 'moody', 'classic']
    }

    if trend_keyword.lower() in trend_descriptors:
        keywords.extend(trend_descriptors[trend_keyword.lower()])

    # Remove duplicates and return top 7
    unique_keywords = list(dict.fromkeys(keywords))
    return unique_keywords[:7]

def determine_target_products(trend_keyword, detected_elements):
    """Determine target product types for this trend"""
    products = []

    # Trend-specific product mapping
    trend_products = {
        'aura': ['graphic tees', 'hoodies', 'statement shirts', 'sigma apparel', 'meme merchandise'],
        'matcha': ['drink packaging', 'tote bags', 'aesthetic apparel', 'minimalist merch', 'wellness products'],
        'glow up': ['beauty products', 'motivational apparel', 'transformation merch', 'self-care items', 'wellness gear'],
        'chill guy': ['casual tees', 'relaxed hoodies', 'meme apparel', 'comfort wear', 'laid-back accessories'],
        'sigma': ['masculine apparel', 'motivational tees', 'gym wear', 'alpha merch', 'confidence apparel'],
        'dubai chocolate': ['luxury packaging', 'exotic treats', 'premium merch', 'viral food items', 'gift boxes'],
        'boba': ['drink accessories', 'aesthetic tees', 'Asian fusion merch', 'cute apparel', 'kawaii items'],
        'tinned fish': ['food packaging', 'culinary apparel', 'chef merch', 'gourmet items', 'cooking accessories'],
        'capybara': ['animal tees', 'cute hoodies', 'plushies', 'wholesome merch', 'kawaii accessories'],
        'y2k': ['retro tees', 'nostalgic hoodies', '2000s apparel', 'colorful accessories', 'futuristic merch'],
        'cottage core': ['rustic tees', 'vintage apparel', 'nature merch', 'cozy hoodies', 'pastoral accessories'],
        'dark academia': ['scholarly apparel', 'vintage tees', 'intellectual merch', 'classic hoodies', 'literary items']
    }

    if trend_keyword.lower() in trend_products:
        products = trend_products[trend_keyword.lower()]
    else:
        # Default products
        products = ['graphic tees', 'hoodies', 'accessories', 'statement pieces', 'merchandise']

    return products[:5]

def calculate_popularity_score(video_infos):
    """Calculate popularity score based on engagement metrics"""
    total_views = sum(v['views'] for v in video_infos)
    total_likes = sum(v['likes'] for v in video_infos)
    avg_engagement = (total_likes / total_views * 100) if total_views > 0 else 0

    # Score from 0-100 based on total engagement
    if total_views > 50000000:  # 50M+ views
        base_score = 90
    elif total_views > 20000000:  # 20M+ views
        base_score = 80
    elif total_views > 5000000:  # 5M+ views
        base_score = 70
    else:
        base_score = 60

    # Adjust by engagement rate
    engagement_bonus = min(avg_engagement * 2, 10)

    return min(int(base_score + engagement_bonus), 100)

def determine_platforms_and_demographics(trend_keyword):
    """Determine which platforms and demographics for this trend"""
    trend_data = {
        'aura': {
            'platforms': ['TikTok', 'YouTube Shorts', 'Instagram Reels'],
            'demographics': ['Gen Z', 'Young Men', 'Teens']
        },
        'matcha': {
            'platforms': ['TikTok', 'Instagram', 'Pinterest'],
            'demographics': ['Millennials', 'Gen Z', 'Women 18-35']
        },
        'glow up': {
            'platforms': ['TikTok', 'Instagram', 'YouTube Shorts'],
            'demographics': ['Gen Z', 'Teens', 'Young Adults']
        },
        'chill guy': {
            'platforms': ['TikTok', 'Instagram', 'Twitter'],
            'demographics': ['Gen Z', 'Millennials', 'Meme Culture']
        },
        'sigma': {
            'platforms': ['TikTok', 'YouTube', 'Instagram'],
            'demographics': ['Young Men', 'Teens', 'Gen Z']
        }
    }

    default = {
        'platforms': ['TikTok', 'Instagram', 'YouTube Shorts'],
        'demographics': ['Gen Z', 'Millennials']
    }

    return trend_data.get(trend_keyword.lower(), default)

def generate_marketing_angle(trend_keyword, keywords):
    """Generate marketing angle based on trend and keywords"""
    trend_angles = {
        'aura': "Focus on confidence, dominance, and personal power. Use 'radiate confidence', 'command respect', 'embrace your aura'",
        'matcha': "Focus on wellness, aesthetics, and trendy lifestyle. Use 'embrace wellness', 'aesthetic living', 'green goodness'",
        'glow up': "Focus on transformation, self-improvement, and empowerment. Use 'transform yourself', 'become your best self', 'glow differently'",
        'chill guy': "Focus on relaxation, humor, and laid-back attitude. Use 'stay chill', 'embrace calm', 'unbothered energy'",
        'sigma': "Focus on independence, self-reliance, and masculine energy. Use 'walk alone', 'self-made', 'alpha mindset'"
    }

    if trend_keyword.lower() in trend_angles:
        return trend_angles[trend_keyword.lower()]

    # Generate based on keywords
    keyword_str = ', '.join(keywords[:3])
    return f"Focus on {keyword_str} themes. Emphasize authenticity, trend participation, and self-expression"

def extract_hashtags(trend_keyword, video_infos):
    """Extract and generate relevant hashtags"""
    hashtags = [f"#{trend_keyword.replace(' ', '')}"]

    # Extract from video tags
    for video in video_infos:
        for tag in video.get('tags', []):
            tag_clean = tag.lower().replace(' ', '')
            if len(tag_clean) > 2 and tag_clean not in [h[1:] for h in hashtags]:
                hashtags.append(f"#{tag_clean}")

    # Add trend-specific hashtags
    trend_hashtags = {
        'aura': ['#sigma', '#confidence', '#dominant', '#powerful'],
        'matcha': ['#matchalatte', '#wellness', '#aesthetic', '#greentea'],
        'glow up': ['#transformation', '#glowup', '#beforeandafter', '#selflove'],
        'chill guy': ['#chillvibes', '#meme', '#relaxed', '#unbothered'],
        'sigma': ['#sigmamale', '#alpha', '#mindset', '#grind']
    }

    if trend_keyword.lower() in trend_hashtags:
        hashtags.extend(trend_hashtags[trend_keyword.lower()])

    # Remove duplicates
    unique_hashtags = list(dict.fromkeys(hashtags))
    return unique_hashtags[:8]

def generate_comprehensive_trend_analysis(trend_keyword, all_detected_elements, video_infos):
    """Generate comprehensive trend analysis matching the required format"""

    # Aggregate all detected elements across videos
    aggregated_elements = {}
    for elements in all_detected_elements:
        for key, value in elements.items():
            if key in aggregated_elements:
                aggregated_elements[key]['segment_count'] += value['segment_count']
            else:
                aggregated_elements[key] = value.copy()

    # Generate trend ID
    trend_id = f"trend_{trend_keyword.lower().replace(' ', '_')}"

    # Extract comprehensive data
    keywords = extract_keywords_from_trend(trend_keyword, aggregated_elements, video_infos)
    color_palette = extract_colors_from_elements(aggregated_elements)
    target_products = determine_target_products(trend_keyword, aggregated_elements)
    marketing_angle = generate_marketing_angle(trend_keyword, keywords)
    popularity_score = calculate_popularity_score(video_infos)
    platform_demo = determine_platforms_and_demographics(trend_keyword)
    hashtags = extract_hashtags(trend_keyword, video_infos)

    # Generate description
    description = f"{trend_keyword.title()} trend featuring {', '.join(keywords[:3])} content. "
    if aggregated_elements:
        top_elements = sorted(aggregated_elements.keys(), key=lambda x: aggregated_elements[x]['segment_count'], reverse=True)[:3]
        description += f"Characterized by {', '.join(top_elements)}. "
    description += f"Popular among {', '.join(platform_demo['demographics'])} on {', '.join(platform_demo['platforms'])}."

    return {
        "id": trend_id,
        "name": trend_keyword.title(),
        "description": description,
        "keywords": keywords,
        "color_palette": color_palette,
        "target_products": target_products,
        "marketing_angle": marketing_angle,
        "popularity_score": popularity_score,
        "platforms": platform_demo['platforms'],
        "demographics": platform_demo['demographics'],
        "hashtags": hashtags
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
    all_detected_elements = []

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

            # Get detailed description of what's happening
            print(f"\n4. Getting detailed video description...")
            detailed_description = get_detailed_video_description(index_id, video_id)

            # Analyze objects
            print(f"\n5. Analyzing visual elements...")
            detected_elements = analyze_video_objects(index_id)
            all_detected_elements.append(detected_elements)

            # Build comprehensive description from detected elements and video metadata
            if not detailed_description or len(detailed_description) < 50:
                # Intelligent fallback: build description from video title + detected elements
                title = video_info['title']
                title_lower = title.lower()

                description_parts = []

                # Analyze title for context
                title_actions = {
                    'tutorial': 'demonstrates a tutorial',
                    'how to': 'shows how to',
                    'ranking': 'ranks and compares',
                    'review': 'reviews',
                    'unboxing': 'unboxes',
                    'try': 'attempts',
                    'challenge': 'takes on a challenge',
                    'reaction': 'reacts to content',
                    'vs': 'compares different things',
                    'transformation': 'showcases a transformation',
                    'before and after': 'shows before and after results',
                    'pov': 'presents a point-of-view scenario',
                    'storytime': 'tells a story',
                    'day in': 'shows a day in the life',
                    'get ready': 'shows a get-ready routine',
                    'outfit': 'displays outfit choices',
                    'makeup': 'demonstrates makeup techniques',
                    'cooking': 'shows cooking',
                    'recipe': 'demonstrates a recipe',
                    'workout': 'shows a workout routine',
                    'fails': 'showcases fails or mistakes',
                    'moments': 'highlights key moments',
                    'best': 'presents the best examples'
                }

                title_subjects = {
                    'aura': 'aura points and social dominance',
                    'sigma': 'sigma mindset and masculinity',
                    'matcha': 'matcha drinks and aesthetic lifestyle',
                    'glow up': 'transformation and self-improvement',
                    'aesthetic': 'aesthetic visuals and styling',
                    'outfit': 'fashion and clothing',
                    'makeup': 'makeup and beauty',
                    'food': 'food and cooking',
                    'recipe': 'recipes and cooking',
                    'dance': 'dancing and choreography',
                    'funny': 'comedy and humor',
                    'prank': 'pranks and reactions'
                }

                # Find matching action
                action_found = None
                for keyword, action in title_actions.items():
                    if keyword in title_lower:
                        action_found = action
                        break

                # Find matching subject
                subject_found = None
                for keyword, subject in title_subjects.items():
                    if keyword in title_lower:
                        subject_found = subject
                        break

                # Build intelligent description
                if action_found and subject_found:
                    detailed_description = f"This video {action_found} about {subject_found}."
                elif action_found:
                    detailed_description = f"This video {action_found}."
                elif subject_found:
                    detailed_description = f"This video focuses on {subject_found}."
                else:
                    # Fall back to element-based description
                    sorted_elements = sorted(
                        detected_elements.items(),
                        key=lambda x: x[1]['segment_count'],
                        reverse=True
                    )

                    if sorted_elements and len(sorted_elements) >= 2:
                        top_elements = [elem[0] for elem in sorted_elements[:5]]

                        if 'people' in top_elements or 'person' in top_elements:
                            if 'dancing' in top_elements:
                                detailed_description = "This video shows people dancing and performing choreography."
                            elif 'performance' in top_elements:
                                detailed_description = "This video features people performing for the camera."
                            elif 'sports' in top_elements or 'action' in top_elements:
                                detailed_description = "This video captures people engaged in athletic or action-based activities."
                            else:
                                detailed_description = "This video features people in a short-form content format."
                        elif 'product' in top_elements or 'shopping' in top_elements:
                            detailed_description = "This video showcases and demonstrates various products."
                        elif 'food' in top_elements or 'cooking' in top_elements:
                            detailed_description = "This video features food preparation or culinary content."
                        else:
                            # Ultra fallback
                            detailed_description = f"This short-form video is about {selected_trend}, featuring engaging visual content."
                    else:
                        detailed_description = f"This short-form video is part of the {selected_trend} trend, featuring engaging content popular on social media."

            # Build analysis result
            video_analysis = {
                'video_info': video_info,
                'detected_elements': detected_elements,
                'detailed_description': detailed_description
            }

            analysis_results.append(video_analysis)

            print(f"  ✓ Detected {len(detected_elements)} visual elements")
            print(f"  ✓ Generated description: {detailed_description[:100]}...")

        # Clean up video file
        if os.path.exists(video_path):
            os.remove(video_path)

    # Step 4: Generate comprehensive trend analysis
    print(f"\n\n{'='*60}")
    print("GENERATING COMPREHENSIVE TREND ANALYSIS")
    print(f"{'='*60}\n")

    # Extract video infos
    video_infos = [r['video_info'] for r in analysis_results]

    # Generate comprehensive analysis
    print(f"📊 Analyzing {len(analysis_results)} videos for trend patterns...")
    comprehensive_trend = generate_comprehensive_trend_analysis(
        selected_trend,
        all_detected_elements,
        video_infos
    )

    # Add sample videos to the trend data with descriptions
    comprehensive_trend['sample_videos'] = [
        {
            'title': r['video_info']['title'],
            'url': r['video_info']['url'],
            'views': r['video_info']['views'],
            'likes': r['video_info']['likes'],
            'what_is_happening': r.get('detailed_description', 'Video content analysis'),
            'why_its_trending': [
                f"part of the viral '{selected_trend}' trend",
                "high engagement and shareability",
                "relatable content format"
            ]
        }
        for r in analysis_results
    ]

    # Print summary
    print(f"\n✅ COMPREHENSIVE TREND ANALYSIS COMPLETE")
    print(f"\nTrend: {comprehensive_trend['name']}")
    print(f"Popularity Score: {comprehensive_trend['popularity_score']}/100")
    print(f"Keywords: {', '.join(comprehensive_trend['keywords'])}")
    print(f"Target Products: {', '.join(comprehensive_trend['target_products'])}")
    print(f"Platforms: {', '.join(comprehensive_trend['platforms'])}")
    print(f"Demographics: {', '.join(comprehensive_trend['demographics'])}")
    print(f"Hashtags: {', '.join(comprehensive_trend['hashtags'][:5])}")

    # Save to JSON
    output_file = f"trending_analysis_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump(comprehensive_trend, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ Analysis complete! Results saved to: {output_file}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
