"""
Gemini Integration Module
Sends Twelve Labs analysis + Shopify products to Gemini for store optimization recommendations
"""

from google import genai
import json
from datetime import datetime
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'video_analysis'))
from config import GEMINI_API_KEY


def generate_store_recommendations(twelve_labs_json_path, shopify_json_path, output_path):
    """
    Takes Twelve Labs analysis + Shopify products,
    sends to Gemini for store optimization recommendations

    Args:
        twelve_labs_json_path: Path to Twelve Labs analysis JSON
        shopify_json_path: Path to Shopify products JSON
        output_path: Path to save Gemini recommendations

    Returns:
        dict: Structured recommendations in required format
    """

    print("Loading input data...")

    # Load Twelve Labs analysis
    try:
        with open(twelve_labs_json_path, 'r') as f:
            trends_data = json.load(f)
        print(f"✓ Loaded Twelve Labs analysis ({len(trends_data.get('trends', []))} trends)")
    except FileNotFoundError:
        print(f"✗ Error: {twelve_labs_json_path} not found")
        raise
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing {twelve_labs_json_path}: {e}")
        raise

    # Load Shopify products
    try:
        with open(shopify_json_path, 'r') as f:
            shopify_data = json.load(f)
        product_count = len(shopify_data.get('products', []))
        print(f"✓ Loaded Shopify products ({product_count} products)")
    except FileNotFoundError:
        print(f"✗ Error: {shopify_json_path} not found")
        raise
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing {shopify_json_path}: {e}")
        raise

    # Configure Gemini
    print("Configuring Gemini API...")
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("✗ Error: GEMINI_API_KEY not configured in config.py")
        raise ValueError("Please set GEMINI_API_KEY in pipeline/video_analysis/config.py")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Use gemini-flash-latest (stable model)
    model_name = 'models/gemini-flash-latest'
    print(f"✓ Using {model_name} model")

    # Construct prompt
    current_timestamp = datetime.now().isoformat()
    prompt = f"""
You are an expert e-commerce and SEO consultant. Analyze the following data and provide actionable recommendations.

SOCIAL MEDIA TRENDS (from video analysis):
{json.dumps(trends_data, indent=2)}

SHOPIFY STORE PRODUCTS:
{json.dumps(shopify_data, indent=2)}

Based on this information, generate recommendations for how the Shopify store should adapt to align with current social media trends for better SEO and conversions.

For EACH trend, provide:
1. **id**: Unique identifier (use trend_id from input as string)
2. **name**: Trend name
3. **description**: 2-3 sentence summary of the trend based on video analysis
4. **keywords**: SEO keywords extracted from video analysis (8-12 keywords that users would search for)
5. **color_palette**: Color scheme suggestions based on trend aesthetics (4-6 hex codes like "#F5F5DC")
6. **target_products**: List of product titles from the Shopify store that match this trend (use exact product titles)
7. **marketing_angle**: One compelling sentence on how to position products for this trend
8. **popularity_score**: Estimate 1-100 based on viral metrics and views
9. **platforms**: Where this trend is popular (e.g., ["TikTok", "Instagram", "YouTube"])
10. **demographics**: Target audience (e.g., ["Gen Z", "Ages 16-24", "Female-leaning"])
11. **hashtags**: Recommended hashtags for social media marketing (10-15 hashtags with # prefix)

Output MUST be valid JSON in this exact format:
{{
  "trends": [
    {{
      "id": "1",
      "name": "Example Trend Name",
      "description": "Two to three sentence description of the trend.",
      "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"],
      "color_palette": ["#FFFFFF", "#000000", "#FF0000", "#00FF00"],
      "target_products": ["Product Title 1", "Product Title 2"],
      "marketing_angle": "Compelling marketing sentence here",
      "popularity_score": 85,
      "platforms": ["TikTok", "Instagram"],
      "demographics": ["Gen Z", "Ages 16-24"],
      "hashtags": ["#trend", "#viral", "#fashion", "#style", "#aesthetic", "#fyp", "#foryou", "#trending", "#explore", "#shopping"]
    }}
  ],
  "last_updated": "{current_timestamp}",
  "source": "Gemini Analysis",
  "version": "1.0"
}}

IMPORTANT:
- Return ONLY valid JSON, no other text before or after
- Ensure all fields are present for each trend
- Use exact product titles from the Shopify data
- Make sure color_palette contains valid hex codes
- Ensure id is a string, not a number
- Make sure popularity_score is a number (not null)

Return ONLY the JSON, no markdown formatting or explanatory text.
"""

    print("Sending request to Gemini...")

    try:
        # Call Gemini
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        # Parse response
        response_text = response.text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        print("✓ Received response from Gemini")
        print("Parsing JSON...")

        # Parse JSON
        recommendations = json.loads(response_text)

        # Validate structure
        if "trends" not in recommendations:
            raise ValueError("Response missing 'trends' field")

        print(f"✓ Parsed recommendations for {len(recommendations['trends'])} trends")

        # Save to file
        with open(output_path, 'w') as f:
            json.dump(recommendations, f, indent=2)

        print(f"✓ Saved recommendations to {output_path}")

        return recommendations

    except json.JSONDecodeError as e:
        print(f"✗ Error parsing Gemini response as JSON: {e}")
        print(f"Response text: {response_text[:500]}...")
        raise
    except Exception as e:
        print(f"✗ Error calling Gemini API: {e}")
        raise


if __name__ == "__main__":
    # Test the module
    print("Testing Gemini Integration...")
    try:
        recommendations = generate_store_recommendations(
            twelve_labs_json_path="twelve_labs_analysis.json",
            shopify_json_path="shop_export.json",
            output_path="gemini_recommendations.json"
        )
        print(f"\n✓ Generated {len(recommendations['trends'])} recommendations")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
