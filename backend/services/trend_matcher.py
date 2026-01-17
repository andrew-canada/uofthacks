"""
Trend Matcher Service.
Compares products to current trends and identifies potential matches.
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
    print("⚠️ google-generativeai not installed. Using fallback matching.")


class TrendMatcher:
    """
    Identifies which products match which trends.
    Returns structured match data without generating new content.
    """
    
    def __init__(self):
        self._config = config.ai
        self._model = None
        
        if GEMINI_AVAILABLE and self._config.gemini_api_key:
            genai.configure(api_key=self._config.gemini_api_key)
            self._model = genai.GenerativeModel('gemini-pro')
            print("✅ Trend Matcher: Gemini AI initialized")
        else:
            print("⚠️ Trend Matcher: Using rule-based matching")
    
    def find_matches(
        self, 
        products: List[Dict[str, Any]], 
        trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Find which products match which trends.
        
        Args:
            products: List of product summaries with id, title, type, description, tags
            trends: List of trends with name, keywords, target_products, etc.
            
        Returns:
            {
                "success": true,
                "matches": [
                    {
                        "product_id": "gid://...",
                        "product_title": "Classic Trench Coat",
                        "product_type": "Coats",
                        "matched_trends": [
                            {
                                "trend_name": "Aura Aesthetic",
                                "trend_id": "trend_001",
                                "confidence": 92,
                                "match_reasons": ["trench coats in target_products", "vintage keyword match"]
                            }
                        ]
                    }
                ],
                "unmatched_products": [...],
                "method": "gemini" | "fallback"
            }
        """
        if self._model:
            return self._ai_match(products, trends)
        else:
            return self._rule_based_match(products, trends)
    
    def _ai_match(
        self, 
        products: List[Dict[str, Any]], 
        trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use Gemini to find product-trend matches."""
        
        prompt = self._build_match_prompt(products, trends)
        
        try:
            response = self._model.generate_content(prompt)
            response_text = self._clean_response(response.text)
            
            result = json.loads(response_text)
            result['method'] = 'gemini'
            result['success'] = True
            
            return result
            
        except json.JSONDecodeError as e:
            print(f'❌ Error parsing Gemini response: {e}')
            return self._rule_based_match(products, trends)
        except Exception as e:
            print(f'❌ Error in AI matching: {e}')
            return self._rule_based_match(products, trends)
    
    def _build_match_prompt(
        self, 
        products: List[Dict[str, Any]], 
        trends: List[Dict[str, Any]]
    ) -> str:
        """Build the prompt for trend matching."""
        
        products_json = json.dumps(products, indent=2)
        trends_json = json.dumps(trends, indent=2)
        
        return f"""You are a fashion trend analyst. Your task is to match products to current trends.

CURRENT TRENDS:
{trends_json}

Each trend has:
- id: Unique identifier (e.g., "trend_001")
- name: The trend name (e.g., "Aura Aesthetic")
- target_products: Product types that fit this trend (e.g., ["trench coats", "blazers"])
- keywords: Style keywords associated with the trend
- color_palette: Colors that match the trend
- marketing_angle: How to market products for this trend

PRODUCTS TO ANALYZE:
{products_json}

Each product has:
- id: Product identifier
- title: Product name
- type: Product category
- description: Current product description
- tags: Product tags

TASK:
1. For each product, check if it matches any trend based on:
   - Product type/title matching trend's target_products (MOST IMPORTANT - check if product title or type contains any of the target_products)
   - Product title/description containing trend keywords
   - Product tags aligning with trend
   
2. A product can match multiple trends
3. Only include matches with confidence >= 50

MATCHING EXAMPLES:
- "Classic Trench Coat" (type: "Coats") → matches "Aura Aesthetic" because "trench coats" is in target_products
- "Wool Blazer" → matches "Aura Aesthetic" because "blazers" is in target_products  
- "Fleece Jacket" → matches "Gorpcore" because "fleece jackets" is in target_products
- "Cashmere Sweater" → matches "Quiet Luxury" because "cashmere sweaters" is in target_products

Return ONLY a JSON object with this exact structure:
{{
    "matches": [
        {{
            "product_id": "gid://shopify/Product/123",
            "product_title": "Classic Trench Coat",
            "product_type": "Coats",
            "matched_trends": [
                {{
                    "trend_name": "Aura Aesthetic",
                    "trend_id": "trend_001",
                    "confidence": 92,
                    "match_reasons": ["'trench coats' in target_products matches product title"]
                }}
            ]
        }}
    ],
    "unmatched_products": [
        {{
            "product_id": "gid://shopify/Product/456",
            "product_title": "Basic Socks",
            "reason": "No matching target_products found in any trend"
        }}
    ]
}}

Return ONLY valid JSON, no other text."""
    
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
    
    def _rule_based_match(
        self, 
        products: List[Dict[str, Any]], 
        trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback rule-based matching when AI is unavailable."""
        
        matches = []
        unmatched = []
        
        for product in products:
            product_matches = self._match_product_to_trends(product, trends)
            
            if product_matches:
                matches.append({
                    'product_id': product['id'],
                    'product_title': product.get('title', ''),
                    'product_type': product.get('type', ''),
                    'matched_trends': product_matches
                })
            else:
                unmatched.append({
                    'product_id': product['id'],
                    'product_title': product.get('title', ''),
                    'reason': 'No matching trends found'
                })
        
        return {
            'success': True,
            'matches': matches,
            'unmatched_products': unmatched,
            'method': 'fallback'
        }
    
    def _match_product_to_trends(
        self, 
        product: Dict[str, Any], 
        trends: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Match a single product against all trends."""
        
        matched_trends = []
        
        product_type = product.get('type', '').lower()
        product_title = product.get('title', '').lower()
        product_desc = product.get('description', '').lower()
        product_tags = [t.lower() for t in product.get('tags', [])]
        
        all_product_text = f"{product_title} {product_type} {product_desc} {' '.join(product_tags)}"
        
        for trend in trends:
            confidence = 0
            reasons = []
            
            # Check target_products (highest weight)
            target_products = trend.get('target_products', [])
            for target in target_products:
                target_lower = target.lower()
                # Check if target is in product title or type
                if target_lower in product_title or target_lower in product_type:
                    confidence += 50
                    reasons.append(f"'{target}' in target_products matches product")
                    break
                # Also check partial matches (e.g., "trench" in "trench coat")
                target_words = target_lower.split()
                for word in target_words:
                    if len(word) > 3 and word in product_title:
                        confidence += 35
                        reasons.append(f"'{word}' from target_products found in title")
                        break
            
            # Check keywords (medium weight)
            keywords = trend.get('keywords', [])
            keyword_matches = []
            for keyword in keywords:
                if keyword.lower() in all_product_text:
                    keyword_matches.append(keyword)
                    confidence += 5
            
            if keyword_matches:
                reasons.append(f"keywords match: {', '.join(keyword_matches[:3])}")
            
            # Check product tags against trend hashtags
            hashtags = [h.replace('#', '').lower() for h in trend.get('hashtags', [])]
            tag_matches = set(product_tags) & set(hashtags)
            if tag_matches:
                confidence += 10
                reasons.append(f"tag matches: {', '.join(tag_matches)}")
            
            # Only include if confidence meets threshold
            if confidence >= 35:
                matched_trends.append({
                    'trend_name': trend.get('name', ''),
                    'trend_id': trend.get('id', ''),
                    'confidence': min(confidence, 100),
                    'match_reasons': reasons
                })
        
        # Sort by confidence
        matched_trends.sort(key=lambda x: x['confidence'], reverse=True)
        
        return matched_trends


# Global singleton instance
trend_matcher = TrendMatcher()
