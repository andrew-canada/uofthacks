"""
Marketing Generator Service.
Takes a product-trend match and generates new marketing copy.
Designed as a stateless service for LangGraph integration.
"""

import json
from typing import Dict, Any, Optional, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Conditional import for Gemini
try:
    import google.genai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Using template-based generation.")


class MarketingGenerator:
    """
    Generates new marketing content for products based on trend alignment.
    Takes existing product data and transforms it to match a trend's style.
    """
    
    def __init__(self):
        self._config = config.ai
        self._model = None
        
        if GEMINI_AVAILABLE and self._config.gemini_api_key:
            try:
                os.environ.setdefault('GENAI_API_KEY', self._config.gemini_api_key)
                if hasattr(genai, 'GenerativeModel'):
                    self._model = genai.GenerativeModel('gemini-pro')
                    print("✅ Marketing Generator: Gemini AI initialized")
                else:
                    Client = getattr(genai, 'Client', None)
                    if Client is not None:
                        try:
                            try:
                                client = Client(api_key=self._config.gemini_api_key)
                            except TypeError:
                                client = Client()

                            self._model = client
                            print("✅ Marketing Generator: Gemini client initialized")
                        except Exception as e:
                            self._model = None
                            print("⚠️ Marketing Generator: Gemini client failed to initialize:", e)
                    else:
                        self._model = None
                        print("⚠️ Marketing Generator: google-genai present but no compatible model found")
            except Exception as e:
                self._model = None
                print("⚠️ Marketing Generator init failed:", e)
        else:
            print("⚠️ Marketing Generator: Using template-based generation")
    
    def generate_marketing(
        self,
        product: Dict[str, Any],
        trend: Dict[str, Any],
        match_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate new marketing copy for a product aligned with a trend.
        
        Args:
            product: Product data with title, description, type, price, etc.
            trend: Trend data with name, keywords, marketing_angle, color_palette
            match_info: Optional match metadata (confidence, reasons)
            
        Returns:
            {
                "success": true,
                "product_id": "gid://...",
                "trend_name": "Aura Aesthetic",
                "original": {
                    "title": "Classic Trench Coat",
                    "description": "A classic trench coat..."
                },
                "generated": {
                    "title": "Classic Trench Coat - Cultivate Your Aura",
                    "description": "...",
                    "description_html": "<div>...</div>",
                    "seo_title": "...",
                    "seo_description": "...",
                    "marketing_angle": "...",
                    "suggested_tags": [...],
                    "color_scheme": "...",
                    "layout_style": "luxury" | "hero" | "minimal" | "urgent",
                    "trust_badges": [...],
                    "show_countdown": false
                },
                "method": "gemini" | "template"
            }
        """
        if self._model:
            return self._ai_generate(product, trend, match_info)
        else:
            return self._template_generate(product, trend, match_info)
    
    def _ai_generate(
        self,
        product: Dict[str, Any],
        trend: Dict[str, Any],
        match_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use Gemini to generate marketing copy."""
        
        prompt = self._build_generation_prompt(product, trend, match_info)
        
        try:
            response_text = self._call_genai(prompt)
            response_text = self._clean_response(response_text)

            generated = json.loads(response_text)
            
            return {
                'success': True,
                'product_id': product.get('id', ''),
                'trend_name': trend.get('name', ''),
                'original': {
                    'title': product.get('title', ''),
                    'description': product.get('description', '')
                },
                'generated': generated,
                'method': 'gemini'
            }
            
        except json.JSONDecodeError as e:
            print(f'❌ Error parsing Gemini response: {e}')
            return self._template_generate(product, trend, match_info)

    def _call_genai(self, prompt: str) -> str:
        if not self._model:
            raise RuntimeError('GenAI model not initialized')

        try:
            if hasattr(self._model, 'generate_content') and callable(self._model.generate_content):
                resp = self._model.generate_content(prompt)
                return getattr(resp, 'text', str(resp))
        except Exception:
            pass

        try:
            responses = getattr(self._model, 'responses', None)
            if responses is not None and hasattr(responses, 'generate'):
                try:
                    resp = responses.generate(model='gemini-pro', input=prompt)
                except TypeError:
                    resp = responses.generate(model='gemini-pro', prompt=prompt)

                if hasattr(resp, 'output_text'):
                    return resp.output_text
                if hasattr(resp, 'text'):
                    return resp.text
                out = getattr(resp, 'output', None)
                if out:
                    try:
                        parts = []
                        for item in out:
                            if isinstance(item, dict):
                                for c in item.get('content', []):
                                    t = c.get('text') or c.get('text_raw') or c.get('markdown')
                                    if t:
                                        parts.append(t)
                        if parts:
                            return '\n'.join(parts)
                    except Exception:
                        pass
                return str(resp)
        except Exception:
            pass

        try:
            if hasattr(self._model, 'generate_text'):
                resp = self._model.generate_text(model='gemini-pro', input=prompt)
                if hasattr(resp, 'text'):
                    return resp.text
                return str(resp)
        except Exception:
            pass

        try:
            if callable(self._model):
                resp = self._model(prompt)
                return str(resp)
        except Exception:
            pass

        raise RuntimeError('Unable to call GenAI client with known interfaces')
    
    def _build_generation_prompt(
        self,
        product: Dict[str, Any],
        trend: Dict[str, Any],
        match_info: Optional[Dict[str, Any]]
    ) -> str:
        """Build the prompt for marketing generation."""
        
        product_json = json.dumps(product, indent=2)
        trend_json = json.dumps(trend, indent=2)
        trend_name = trend.get('name', 'the trend')
        trend_id = trend.get('id', 'trend')
        
        return f"""You are an expert fashion copywriter. Your task is to rewrite product marketing copy to align with a specific trend.

CURRENT PRODUCT:
{product_json}

TARGET TREND:
{trend_json}

The trend includes:
- name: The trend name (USE THIS in your marketing!)
- keywords: Words/themes to incorporate naturally
- marketing_angle: The approach to take (FOLLOW THIS CLOSELY)
- color_palette: Visual style reference
- hashtags: Social media context

TASK:
Transform the product's marketing to align with the "{trend_name}" trend.

Guidelines:
1. KEEP the product's core identity but INFUSE the trend's style
2. Use trend keywords NATURALLY in the copy - don't force them
3. Follow the marketing_angle from the trend data
4. Make it feel authentic, not forced or gimmicky
5. Create urgency/desire appropriate to the trend

EXAMPLE for "Aura Aesthetic" trend with a trench coat:
- OLD title: "Classic Trench Coat"
- NEW title: "Classic Trench Coat - Cultivate Your Aura"
- NEW description: "Elevate your mysterious aura with this timeless trench. Dark academia sophistication meets modern elegance."

Return ONLY a JSON object with this exact structure:
{{
    "title": "New product title - incorporate trend naturally",
    "description": "Plain text description (2-3 sentences, use trend's marketing_angle)",
    "description_html": "<div class='trend-{trend_id}'>\\n    <h2>✨ Trend-appropriate headline</h2>\\n    <p><strong>Hook line using marketing_angle</strong></p>\\n    <p>Product description</p>\\n    <ul>\\n        <li>🎯 Benefit 1 using trend keyword</li>\\n        <li>✨ Benefit 2</li>\\n        <li>💫 Benefit 3</li>\\n    </ul>\\n</div>",
    "seo_title": "SEO optimized title with trend name (50-60 chars)",
    "seo_description": "SEO meta description using marketing_angle (150-160 chars)",
    "marketing_angle": "One sentence describing the marketing approach",
    "suggested_tags": ["trend-keyword-1", "trend-keyword-2", "product-type"],
    "color_scheme": "Primary color from trend's color_palette",
    "layout_style": "luxury",
    "trust_badges": ["premium", "trending", "limited"],
    "show_countdown": false,
    "social_caption": "Instagram/TikTok caption with 2-3 relevant hashtags from the trend"
}}

For layout_style, choose based on trend:
- "luxury": Aura Aesthetic, Quiet Luxury (sophisticated, minimal, dark/muted)
- "hero": Popular items, Gorpcore (bold, confident, action-oriented)
- "minimal": Coastal Grandmother (clean, breezy, light colors)
- "urgent": Y2K Revival, Dopamine Dressing (energetic, FOMO, bright)

Return ONLY valid JSON, no other text or explanation."""
    
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
    
    def _template_generate(
        self,
        product: Dict[str, Any],
        trend: Dict[str, Any],
        match_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback template-based generation."""
        
        title = product.get('title', 'Product')
        description = product.get('description', '')
        price = product.get('price', 0)
        trend_name = trend.get('name', 'Trending')
        trend_id = trend.get('id', 'trend')
        marketing_angle = trend.get('marketing_angle', '')
        keywords = trend.get('keywords', [])
        color_palette = trend.get('color_palette', [])
        hashtags = trend.get('hashtags', [])
        
        # Determine layout style based on trend
        layout_map = {
            'Aura Aesthetic': 'luxury',
            'Quiet Luxury': 'luxury',
            'Dopamine Dressing': 'urgent',
            'Y2K Revival': 'urgent',
            'Coastal Grandmother': 'minimal',
            'Gorpcore': 'hero'
        }
        layout_style = layout_map.get(trend_name, 'hero')
        
        # Generate new title using marketing angle hints
        if 'aura' in trend_name.lower():
            new_title = f"{title} - Cultivate Your Aura"
        elif 'luxury' in trend_name.lower():
            new_title = f"{title} - Quiet Luxury Essential"
        elif 'dopamine' in trend_name.lower():
            new_title = f"{title} - Boost Your Mood"
        elif 'coastal' in trend_name.lower():
            new_title = f"{title} - Effortlessly Chic"
        elif 'y2k' in trend_name.lower():
            new_title = f"{title} - Y2K Icon"
        elif 'gorpcore' in trend_name.lower():
            new_title = f"{title} - Trail to Street"
        else:
            new_title = f"{title} - {trend_name} Edition"
        
        # Generate description
        new_description = self._generate_description_template(
            title, description, trend_name, keywords, marketing_angle, layout_style
        )
        
        # Generate HTML description
        html_description = self._generate_html_template(
            title, description, trend_name, trend_id, keywords, layout_style
        )
        
        # Trust badges based on layout
        badges_map = {
            'luxury': ['premium', 'handcrafted', 'limited-edition'],
            'hero': ['bestseller', 'trending', 'top-rated'],
            'minimal': ['timeless', 'sustainable', 'versatile'],
            'urgent': ['trending-now', 'selling-fast', 'limited-time']
        }
        
        return {
            'success': True,
            'product_id': product.get('id', ''),
            'trend_name': trend_name,
            'original': {
                'title': title,
                'description': description
            },
            'generated': {
                'title': new_title,
                'description': new_description,
                'description_html': html_description,
                'seo_title': f"{title} | {trend_name} Style | Shop Now",
                'seo_description': f"{new_description[:150]}..." if len(new_description) > 150 else new_description,
                'marketing_angle': marketing_angle,
                'suggested_tags': [kw.lower().replace(' ', '-') for kw in keywords[:5]],
                'color_scheme': color_palette[0] if color_palette else 'neutral',
                'layout_style': layout_style,
                'trust_badges': badges_map.get(layout_style, ['trending']),
                'show_countdown': layout_style == 'urgent',
                'social_caption': f"✨ {new_title} ✨\n\n{new_description[:80]}...\n\n{' '.join(hashtags[:4])}"
            },
            'method': 'template'
        }
    
    def _generate_description_template(
        self,
        title: str,
        original_desc: str,
        trend_name: str,
        keywords: list,
        marketing_angle: str,
        layout_style: str
    ) -> str:
        """Generate plain text description based on trend."""
        
        keyword_str = ', '.join(keywords[:2]) if keywords else 'style'
        
        templates = {
            'luxury': f"Elevate your presence with the {title}. Embodying {keyword_str}, this piece brings {trend_name} sophistication to your wardrobe. {marketing_angle}",
            'hero': f"The {title} everyone's been waiting for. Embrace {keyword_str} with this {trend_name} must-have. {marketing_angle}",
            'minimal': f"Effortless {keyword_str} defined. The {title} delivers {trend_name} vibes with timeless, understated appeal. {marketing_angle}",
            'urgent': f"🔥 {title} is trending NOW! Get the {trend_name} look before it's gone. {marketing_angle}"
        }
        
        return templates.get(layout_style, templates['hero'])
    
    def _generate_html_template(
        self,
        title: str,
        original_desc: str,
        trend_name: str,
        trend_id: str,
        keywords: list,
        layout_style: str
    ) -> str:
        """Generate HTML description based on layout style."""
        
        keyword_bullets = '\n'.join([f"        <li>✨ {kw.title()}</li>" for kw in keywords[:3]])
        
        templates = {
            'luxury': f"""<div class="ai-optimized trend-{trend_id} luxury">
    <h2>✨ {trend_name} Collection</h2>
    <p><strong>Timeless sophistication. Mysterious elegance.</strong></p>
    <p>{original_desc or f'Discover the {title} - where style meets substance.'}</p>
    <ul>
{keyword_bullets}
        <li>💎 Limited availability</li>
    </ul>
</div>""",
            'hero': f"""<div class="ai-optimized trend-{trend_id} hero">
    <h2>🔥 {trend_name} Essential</h2>
    <p><strong>Join the movement. Elevate your style.</strong></p>
    <p>{original_desc or f'The {title} - a must-have for trendsetters.'}</p>
    <ul>
{keyword_bullets}
        <li>⭐ Customer favorite</li>
    </ul>
</div>""",
            'minimal': f"""<div class="ai-optimized trend-{trend_id} minimal">
    <h2>{trend_name}</h2>
    <p><strong>Effortless. Timeless. You.</strong></p>
    <p>{original_desc or f'The {title} - understated elegance for every day.'}</p>
    <ul>
{keyword_bullets}
    </ul>
</div>""",
            'urgent': f"""<div class="ai-optimized trend-{trend_id} urgent">
    <h2>⚡ {trend_name} Alert!</h2>
    <p><strong>🔥 Trending NOW - Don't miss out!</strong></p>
    <p>{original_desc or f'Get the {title} before everyone else!'}</p>
    <ul>
{keyword_bullets}
        <li>⏰ Limited time only!</li>
    </ul>
</div>"""
        }
        
        return templates.get(layout_style, templates['hero'])
    
    def generate_batch(
        self,
        matches: List[Dict[str, Any]],
        products_lookup: Dict[str, Dict],
        trends_lookup: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate marketing for multiple product-trend matches.
        
        Args:
            matches: List of match objects from TrendMatcher
            products_lookup: Dict mapping product_id to product data
            trends_lookup: Dict mapping trend_id to trend data
            
        Returns:
            List of generation results
        """
        results = []
        
        for match in matches:
            product_id = match.get('product_id')
            product = products_lookup.get(product_id)
            
            if not product:
                continue
            
            # Generate for the top matched trend
            matched_trends = match.get('matched_trends', [])
            if not matched_trends:
                continue
            
            top_trend_info = matched_trends[0]
            trend_id = top_trend_info.get('trend_id')
            trend = trends_lookup.get(trend_id)
            
            if not trend:
                continue
            
            result = self.generate_marketing(product, trend, top_trend_info)
            results.append(result)
        
        return results


# Note: Do not instantiate at import time to avoid calling external
# SDKs during module import. Use services.get_marketing_generator() to
# obtain a lazily-initialized singleton.
