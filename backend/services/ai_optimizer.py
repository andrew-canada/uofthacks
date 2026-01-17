"""
AI Optimizer Service.
Uses Gemini AI to analyze products against trends and generate recommendations.
Designed as a stateless service for LangGraph integration.
"""

import json
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Conditional import for Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. AI features will be limited.")


class AIOptimizer:
    """
    AI-powered product optimization using Gemini.
    Analyzes products against trends and generates marketing recommendations.
    """
    
    def __init__(self):
        self._config = config.ai
        self._model = None
        
        if GEMINI_AVAILABLE and self._config.gemini_api_key:
            genai.configure(api_key=self._config.gemini_api_key)
            self._model = genai.GenerativeModel('gemini-pro')
            print("✅ Gemini AI initialized")
        else:
            print("⚠️ Gemini AI not available - using fallback optimization")
    
    def analyze_products_with_trends(
        self, 
        products: List[Dict[str, Any]], 
        trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze products against current trends using Gemini AI.
        
        Args:
            products: List of product summaries
            trends: List of trend summaries
            
        Returns:
            Analysis results with recommendations
        """
        if not self._model:
            return self._fallback_analysis(products, trends)
        
        # Prepare data for prompt
        products_json = json.dumps(products, indent=2)
        trends_json = json.dumps(trends, indent=2)
        
        prompt = self._build_analysis_prompt(products_json, trends_json)
        
        try:
            response = self._model.generate_content(prompt)
            response_text = self._clean_response(response.text)
            
            analysis_results = json.loads(response_text)
            
            return {
                'success': True,
                'analysis': analysis_results,
                'trends_analyzed': len(trends),
                'products_analyzed': len(products),
                'ai_model': 'gemini-pro'
            }
            
        except json.JSONDecodeError as e:
            print(f'❌ Error parsing Gemini response: {e}')
            return {
                'success': False,
                'error': 'Failed to parse AI response',
                'raw_response': response.text if 'response' in dir() else None
            }
        except Exception as e:
            print(f'❌ Error calling Gemini API: {e}')
            return self._fallback_analysis(products, trends)
    
    def _build_analysis_prompt(self, products_json: str, trends_json: str) -> str:
        """Build the analysis prompt for Gemini."""
        return f"""You are an expert fashion marketing analyst. Analyze the following products against current fashion trends and identify which products would benefit from a marketing makeover.

CURRENT TRENDS:
{trends_json}

OUR PRODUCTS:
{products_json}

TASK:
1. Compare each product to the trends
2. Identify which products align with which trends (if any)
3. For products that could benefit from a trend-based makeover, suggest:
   - Which trend(s) to align with
   - New marketing angle
   - Optimized product title
   - Optimized product description (HTML format with emojis and bullet points)
   - SEO title and description
   - Recommended layout style (choose from: luxury, hero, urgent, minimal)
   - Color scheme suggestion
   - Trust badges to add (array of strings)
   - Whether to show countdown timer (boolean)

EXAMPLE:
If the trend is "Aura Aesthetic" and we have a trench coat, suggest:
- Trend: Aura Aesthetic
- Marketing angle: "Cultivate your mysterious aura with this timeless trench"
- Title: "City Overcoat - Mysterious Elegance Trench"
- Description: HTML with dark academia vibes, emphasizing sophistication
- Layout: luxury
- Color scheme: moody (dark colors)

Return your response as a JSON array with this structure:
[
  {{
    "productId": "gid://shopify/Product/123",
    "productTitle": "Original Product Title",
    "needsMakeover": true,
    "matchedTrends": ["Trend Name"],
    "confidence": 85,
    "recommendations": {{
      "trendAlignment": "Trend Name",
      "marketingAngle": "...",
      "optimizedTitle": "...",
      "optimizedDescription": "<div>HTML content with emojis and bullets</div>",
      "seoTitle": "...",
      "seoDescription": "...",
      "layoutStyle": "luxury",
      "colorScheme": "...",
      "trustBadges": ["badge1", "badge2"],
      "showCountdown": false,
      "reasoning": "Why this product matches this trend"
    }}
  }}
]

Only include products that would benefit from a makeover. Be creative and specific!
Return ONLY the JSON array, no other text."""
    
    def _clean_response(self, response_text: str) -> str:
        """Clean Gemini response by removing markdown code blocks."""
        text = response_text.strip()
        
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        return text.strip()
    
    def _fallback_analysis(
        self, 
        products: List[Dict[str, Any]], 
        trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fallback rule-based analysis when Gemini is unavailable.
        """
        results = []
        
        for product in products:
            price = product.get('price', 0)
            product_type = product.get('type', '').lower()
            
            # Simple matching logic
            matched_trend = None
            for trend in trends:
                target_products = [t.lower() for t in trend.get('target_products', [])]
                if any(target in product_type for target in target_products):
                    matched_trend = trend
                    break
            
            if matched_trend:
                recommendations = self._generate_fallback_recommendations(
                    product, matched_trend, price
                )
                results.append({
                    'productId': product['id'],
                    'productTitle': product.get('title', ''),
                    'needsMakeover': True,
                    'matchedTrends': [matched_trend['name']],
                    'confidence': 70,
                    'recommendations': recommendations
                })
        
        return {
            'success': True,
            'analysis': results,
            'trends_analyzed': len(trends),
            'products_analyzed': len(products),
            'ai_model': 'fallback-rules'
        }
    
    def _generate_fallback_recommendations(
        self, 
        product: Dict[str, Any], 
        trend: Dict[str, Any],
        price: float
    ) -> Dict[str, Any]:
        """Generate rule-based recommendations."""
        
        # Determine layout based on price
        if price > 100:
            layout = 'luxury'
            badges = ['premium', 'handcrafted', 'free_shipping']
            show_countdown = False
        elif price > 50:
            layout = 'hero'
            badges = ['bestseller', 'sustainable', 'free_shipping']
            show_countdown = False
        else:
            layout = 'urgent'
            badges = ['trending', 'limited_stock', 'fast_shipping']
            show_countdown = True
        
        title = product.get('title', 'Product')
        trend_name = trend.get('name', 'Trending')
        marketing_angle = trend.get('marketing_angle', '')
        
        return {
            'trendAlignment': trend_name,
            'marketingAngle': marketing_angle,
            'optimizedTitle': f"{title} - {trend_name} Edition",
            'optimizedDescription': self._generate_description(product, trend, layout),
            'seoTitle': f"{title} | {trend_name} Style",
            'seoDescription': f"Shop our {title}. {marketing_angle[:100]}...",
            'layoutStyle': layout,
            'colorScheme': trend.get('color_palette', ['neutral'])[0] if trend.get('color_palette') else 'neutral',
            'trustBadges': badges,
            'showCountdown': show_countdown,
            'reasoning': f"Product type matches trend's target products: {trend.get('target_products', [])}"
        }
    
    def _generate_description(
        self, 
        product: Dict[str, Any], 
        trend: Dict[str, Any],
        layout: str
    ) -> str:
        """Generate HTML description based on layout style."""
        base_desc = product.get('description', 'Quality product')
        trend_name = trend.get('name', '')
        keywords = trend.get('keywords', [])[:3]
        
        if layout == 'luxury':
            return f"""<div class="ai-optimized luxury">
    <h2>✨ {trend_name} Collection</h2>
    <p><strong>Exceptional craftsmanship meets timeless design.</strong></p>
    <p>{base_desc}</p>
    <ul>
        <li>🎯 {keywords[0].title() if keywords else 'Premium quality'}</li>
        <li>🌟 {keywords[1].title() if len(keywords) > 1 else 'Timeless elegance'}</li>
        <li>💎 Limited availability</li>
    </ul>
</div>"""
        elif layout == 'hero':
            return f"""<div class="ai-optimized hero">
    <h2>🔥 {trend_name} Favorite</h2>
    <p><strong>Join thousands of satisfied customers.</strong></p>
    <p>{base_desc}</p>
    <ul>
        <li>⭐ {keywords[0].title() if keywords else 'Bestselling item'}</li>
        <li>🌱 Sustainably made</li>
        <li>🚚 Free shipping on orders over $50</li>
    </ul>
</div>"""
        else:
            return f"""<div class="ai-optimized urgent">
    <h2>⚡ {trend_name} - Limited Time</h2>
    <p><strong>Don't miss out on this trending style!</strong></p>
    <p>{base_desc}</p>
    <ul>
        <li>🔥 Trending now</li>
        <li>📦 Only a few left in stock</li>
        <li>⚡ Fast shipping available</li>
    </ul>
</div>"""
    
    def get_product_recommendations(
        self, 
        product_id: str, 
        analysis_results: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract recommendations for a specific product from analysis results.
        
        Args:
            product_id: The product ID to find
            analysis_results: Full analysis results
            
        Returns:
            Recommendations dict or None
        """
        if not analysis_results.get('success'):
            return None
        
        for result in analysis_results.get('analysis', []):
            if result.get('productId') == product_id and result.get('needsMakeover'):
                return result.get('recommendations')
        
        return None


# Global singleton instance
ai_optimizer = AIOptimizer()
