# The purpose of this file is to orchestrate the complete pipeline:
# 1. Fetch Gen Z trends from Perplexity
# 2. Analyze trends with YouTube + Twelve Labs
# 3. Feed results to Gemini for store recommendations
# 4. Store Gemini output in MongoDB

import sys
import json
from datetime import datetime

from trend_identification.trends import fetch_genz_trends
from video_analysis.analyze_trending_videos import analyze_trend
from gemini_integration import generate_store_recommendations
from store_recommendations import store_gemini_recommendations

ANALYZED_VIDEOS_COUNT_AT_A_TIME = 1
TRENDS_IDENTIFIED_COUNT_AT_A_TIME = 10


def main():
    print("=" * 60)
    print("STEP 1: Fetch Gen Z Trends from Perplexity")
    print("=" * 60)

    trends_response = fetch_genz_trends(count=TRENDS_IDENTIFIED_COUNT_AT_A_TIME)
    trends = trends_response["trends"]

    print(f"✓ Found {len(trends)} trends\n")

    print("=" * 60)
    print("STEP 2: Analyze Trends with YouTube + Twelve Labs")
    print("=" * 60)

    analyzed_trends = []

    for idx, trend in enumerate(trends, 1):
        print(f"\n[{idx}/{len(trends)}] Analyzing: {trend['name']}")

        try:
            # Analyze trend with YouTube + Twelve Labs
            analysis = analyze_trend(trend["name"], count=ANALYZED_VIDEOS_COUNT_AT_A_TIME)

            # Combine trend metadata with video analysis
            trend_with_analysis = {
                "trend_id": trend.get("trend_id", idx),
                "name": trend["name"],
                "description": trend.get("description", ""),
                "platform": trend.get("platform", ""),
                "viral_metric": trend.get("viral_metric", ""),
                "emergence_date": trend.get("emergence_date", ""),
                "marketability": trend.get("marketability", ""),
                "analyzed_videos": analysis["sample_videos"]
            }
            analyzed_trends.append(trend_with_analysis)
            print(f"✓ Analyzed {len(analysis['sample_videos'])} videos")

        except Exception as e:
            print(f"✗ Error analyzing {trend['name']}: {e}")
            continue

    # Save Twelve Labs output to JSON
    twelve_labs_output = {
        "analysis_date": datetime.now().isoformat(),
        "trends": analyzed_trends
    }

    twelve_labs_file = "twelve_labs_analysis.json"
    with open(twelve_labs_file, "w") as f:
        json.dump(twelve_labs_output, f, indent=2)

    print(f"\n✓ Saved Twelve Labs analysis to {twelve_labs_file}")
    print(f"✓ Total trends analyzed: {len(analyzed_trends)}")

    print("\n" + "=" * 60)
    print("STEP 3: Generate Recommendations with Gemini")
    print("=" * 60)

    try:
        recommendations = generate_store_recommendations(
            twelve_labs_json_path=twelve_labs_file,
            shopify_json_path="shop_export.json",
            output_path="gemini_recommendations.json"
        )
        print("✓ Gemini recommendations generated")
    except Exception as e:
        print(f"✗ Error generating Gemini recommendations: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("STEP 4: Store Recommendations in MongoDB")
    print("=" * 60)

    try:
        store_gemini_recommendations("gemini_recommendations.json")
        print("✓ Recommendations stored in MongoDB")
    except Exception as e:
        print(f"✗ Error storing recommendations in MongoDB: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"✓ Twelve Labs analysis: {twelve_labs_file}")
    print(f"✓ Gemini recommendations: gemini_recommendations.json")
    print(f"✓ MongoDB: recommendations collection updated")
    print("=" * 60)


if __name__ == "__main__":
    main()
