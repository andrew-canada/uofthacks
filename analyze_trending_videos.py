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

def get_trending_videos(max_results=5, region_code='US'):
    """Get currently trending videos from YouTube - fetches different videos each time"""
    url = "https://www.googleapis.com/youtube/v3/videos"

    # Fetch more videos than needed so we can randomize selection
    fetch_count = max_results * 3

    params = {
        'part': 'snippet,statistics,contentDetails',
        'chart': 'mostPopular',
        'regionCode': region_code,
        'maxResults': fetch_count,
        'videoCategoryId': '0',  # All categories
        'key': YOUTUBE_API_KEY
    }

    print(f"\n{'='*60}")
    print(f"Fetching Trending Videos from YouTube")
    print(f"{'='*60}\n")

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    all_videos = []
    for item in data.get('items', []):
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
            'category_id': item['snippet']['categoryId'],
            'tags': item['snippet'].get('tags', [])
        }
        all_videos.append(video_info)

    # Randomly sample videos for variety each run
    import random
    selected_videos = random.sample(all_videos, min(max_results, len(all_videos)))

    for video_info in selected_videos:
        print(f"✓ {video_info['title']}")
        print(f"  Views: {video_info['views']:,} | Likes: {video_info['likes']:,}")
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

def generate_video_description(video_info, detected_elements):
    """Generate a specific description of what's in the video and why it's trending"""

    # Sort elements by prevalence
    sorted_elements = sorted(
        detected_elements.items(),
        key=lambda x: x[1]['segment_count'],
        reverse=True
    )

    # Build description
    description = f"This is '{video_info['title']}'. "

    # Analyze main content
    top_elements = [elem[0] for elem in sorted_elements[:5]]

    # Determine video type and description based on detected objects
    if 'music' in top_elements or 'dancing' in top_elements or 'performance' in top_elements:
        description += "The video features musical content with performances and dancing. "
        video_type = "Music/Performance"
    elif 'sports' in top_elements or 'game' in top_elements or 'competition' in top_elements:
        description += "The video showcases sports or gaming content with competitive action. "
        video_type = "Sports/Gaming"
    elif 'food' in top_elements or 'cooking' in top_elements:
        description += "The video focuses on food and cooking content. "
        video_type = "Food/Cooking"
    elif 'product' in top_elements or 'unboxing' in top_elements or 'shopping' in top_elements:
        description += "The video presents product reviews, unboxing, or shopping content. "
        video_type = "Product/Review"
    elif 'celebrity' in top_elements or 'famous person' in top_elements:
        description += "The video features celebrity or famous personality content. "
        video_type = "Celebrity/Entertainment"
    elif 'children' in top_elements or 'baby' in top_elements or 'kids' in top_elements:
        description += "The video contains child-friendly or family content. "
        video_type = "Family/Kids"
    elif 'animal' in top_elements or 'pet' in top_elements:
        description += "The video showcases animals or pets. "
        video_type = "Animals/Pets"
    else:
        description += "The video contains entertainment content. "
        video_type = "General Entertainment"

    # Add specific visual elements
    if detected_elements:
        main_objects = ', '.join(top_elements[:3])
        description += f"Key visual elements detected include: {main_objects}. "

    # Analyze contextual trending reasons
    trending_reasons = analyze_trending_context(video_info)

    # Add engagement metrics
    engagement_rate = video_info['likes'] / max(video_info['views'], 1) * 100

    # Add trending analysis with CONTEXT
    description += f"\n\nWhy it's trending: "
    if trending_reasons:
        description += f"This video is trending because {', '.join(trending_reasons)}. "
    else:
        description += "This video is gaining traction through viewer engagement. "

    # Add stats
    description += f"It has accumulated {video_info['views']:,} views and {video_info['likes']:,} likes "
    description += f"({engagement_rate:.1f}% engagement rate), demonstrating strong viewer interest."

    return {
        'description': description,
        'video_type': video_type,
        'trending_reasons': trending_reasons,
        'engagement_rate': round(engagement_rate, 2),
        'top_visual_elements': top_elements[:5]
    }

def main():
    print("\n" + "="*60)
    print("YOUTUBE TRENDING VIDEO ANALYSIS")
    print("="*60)

    # Step 1: Get trending videos
    num_videos = 3  # Analyze top 3 trending videos
    trending_videos = get_trending_videos(max_results=num_videos)

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
            video_description_analysis = generate_video_description(video_info, detected_elements)

            # Build analysis result
            video_analysis = {
                'video_info': video_info,
                'detected_objects': detected_elements,
                'description_analysis': video_description_analysis,
                'top_elements': sorted(
                    detected_elements.items(),
                    key=lambda x: x[1]['segment_count'],
                    reverse=True
                )[:10]  # Top 10 detected elements
            }

            analysis_results.append(video_analysis)

            print(f"\n  📝 Video Type: {video_description_analysis['video_type']}")
            print(f"  📊 Engagement Rate: {video_description_analysis['engagement_rate']}%")
            print(f"\n  Top detected elements:")
            for element, data in video_analysis['top_elements'][:5]:
                print(f"    • {element.upper()}: {data['segment_count']} segments")

            print(f"\n  🔥 Trending Factors:")
            for reason in video_description_analysis['trending_reasons']:
                print(f"    • {reason}")

        # Clean up video file
        if os.path.exists(video_path):
            os.remove(video_path)

    # Step 4: Aggregate trends across all videos
    print(f"\n\n{'='*60}")
    print("TREND ANALYSIS SUMMARY")
    print(f"{'='*60}\n")

    # Count common elements across videos
    all_elements = Counter()
    for result in analysis_results:
        for element in result['detected_objects'].keys():
            all_elements[element] += 1

    # Identify trending themes
    trending_themes = all_elements.most_common(10)

    final_report = {
        'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'videos_analyzed': len(analysis_results),
        'trending_themes': [
            {'theme': theme, 'appears_in_videos': count}
            for theme, count in trending_themes
        ],
        'individual_video_analysis': [
            {
                'title': r['video_info']['title'],
                'url': r['video_info']['url'],
                'views': r['video_info']['views'],
                'likes': r['video_info']['likes'],
                'video_description': r['description_analysis']['description'],
                'video_type': r['description_analysis']['video_type'],
                'trending_reasons': r['description_analysis']['trending_reasons'],
                'engagement_rate': r['description_analysis']['engagement_rate'],
                'top_visual_elements': r['description_analysis']['top_visual_elements'],
                'detected_objects': {k: v['segment_count'] for k, v in r['detected_objects'].items()}
            }
            for r in analysis_results
        ]
    }

    # Print summary
    print("🔥 TRENDING THEMES ACROSS VIDEOS:")
    for theme_data in final_report['trending_themes']:
        print(f"  • {theme_data['theme'].upper()}: Found in {theme_data['appears_in_videos']}/{num_videos} videos")

    # Save to JSON
    output_file = f"trending_analysis_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump(final_report, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ Analysis complete! Results saved to: {output_file}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
