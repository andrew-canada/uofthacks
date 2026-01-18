
import os
import json
import requests
from config import PERPLEXITY_KEY
from datetime import datetime, timedelta

# Configuration


API_KEY = PERPLEXITY_KEY

API_URL = "https://api.perplexity.ai/chat/completions"

def get_date_context() -> dict:
    """Generate date context for the prompt"""
    today = datetime.now()
    two_weeks_ago = today - timedelta(days=14)
    return {
        "today": today.strftime("%B %d, %Y"),
        "two_weeks_ago": two_weeks_ago.strftime("%B %d, %Y")
    }

def fetch_genz_trends(count =20):
    """
    Fetch Gen Z trends using Perplexity API
    Returns: JSON object with 20 marketable trends
    """
    dates = get_date_context()

    # Construct the prompt with date context
    prompt = f"""Today is {dates['today']}. Find me {count} marketable popular teen/Gen Z trends which have surfaced between {dates['two_weeks_ago']} and {dates['today']} (maximum 2 weeks old).

For each trend, provide:
- trend_id (1-{count})
- name (concise trend name)
- description (2-3 sentence explanation)
- platform (where it's trending)
- viral_metric (specific numbers if available)
- emergence_date (when it started)
- marketability (High/Medium/Low with brief reason)

These trends should be DIFFERENT from:
 - Turning Chinese / Becoming Chinese
 - 365 Buttons
 - AI Baby Dancing
 - ICM Triplets Dance
 - #2016 Nostalgia
 - January 2026 Mashup Dance
 - TikTok Dance Mashup Compilations
 - Party Music Viral Dance Trends
 - Viral Song Mashup Trends
 - Unfiltered BTS & Real Process Content

Return ONLY a valid JSON object in this exact format:
{{
  "trends": [
    {{
      "trend_id": 1,
      "name": "Trend Name",
      "description": "Detailed description",
      "platform": "Platform name",
      "viral_metric": "Specific metrics",
      "emergence_date": "Date",
      "marketability": "Level - reason"
    }}
  ]
}}

Focus on trends from the last 2 weeks only. Include viral TikTok trends, fashion, music, social media formats, memes, and cultural movements."""

    # API request headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # API request payload
    payload = {
        "model": "sonar-pro",  # Use sonar-pro for best real-time search results
        "messages": [
            {
                "role": "system",
                "content": "You are a Gen Z trend analyst specializing in identifying viral, marketable trends. Always return valid JSON format. Focus on the most recent trends only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,  # Lower temperature for more factual responses
        "top_p": 0.9,
        "return_citations": True,  # Get source citations
        "search_recency_filter": "week",  # Focus on recent content
        "max_tokens": 4000
    }

    try:
        # Make API request
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        # Parse response
        data = response.json()

        # Extract content from response
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])

            # Try to parse JSON from content
            # Handle cases where the model might add markdown formatting
            content_clean = content.strip()
            if content_clean.startswith("```json"):
                content_clean = content_clean[7:]
            if content_clean.startswith("```"):
                content_clean = content_clean[3:]
            if content_clean.endswith("```"):
                content_clean = content_clean[:-3]

            trends_data = json.loads(content_clean.strip())

            # Add metadata
            result = {
                "metadata": {
                    "query_date": dates["today"],
                    "date_range": f"{dates['two_weeks_ago']} to {dates['today']}",
                    "source": "Perplexity Sonar API",
                    "citations": citations[:10] if citations else []  # Top 10 citations
                },
                "trends": trends_data.get("trends", [])
            }

            return result
        else:
            raise ValueError("No content in API response")

    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return {"error": f"API request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Raw content: {content}")
        return {"error": f"Failed to parse JSON: {str(e)}"}
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return {"error": f"Unexpected error: {str(e)}"}

def save_to_file(data, filename="genz_trends.json"):
    """Save trends data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Trends saved to {filename}")

def main():
    """Main execution function"""
    print("🔍 Fetching latest Gen Z trends from Perplexity API...")
    print("=" * 60)

    # Fetch trends
    trends_data = fetch_genz_trends()

    # Check for errors
    if "error" in trends_data:
        print(f"❌ Error: {trends_data['error']}")
        return

    # Display results
    print(f"\n✓ Successfully fetched {len(trends_data.get('trends', []))} trends")
    print(f"Query Date: {trends_data['metadata']['query_date']}")
    print(f"Date Range: {trends_data['metadata']['date_range']}")
    print("\n" + "=" * 60)

    # Print first 3 trends as preview
    print("\n📊 Preview (first 3 trends):\n")
    for trend in trends_data.get('trends', [])[:3]:
        print(f"{trend['trend_id']}. {trend['name']}")
        print(f"   Platform: {trend['platform']}")
        print(f"   Marketability: {trend['marketability']}")
        print()

    # Save to file
    save_to_file(trends_data)

    # Output full JSON
    print("\n" + "=" * 60)
    print("📄 Full JSON Output:")
    print("=" * 60)
    print(json.dumps(trends_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()