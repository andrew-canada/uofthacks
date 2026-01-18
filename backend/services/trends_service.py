"""
Trends Service.
Loads and manages trend data from various sources.
Designed as a stateless service for LangGraph integration.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


class TrendsService:
    """
    Manages fashion/product trend data.
    Currently loads from JSON, can be extended to fetch from APIs.
    """
    
    def __init__(self):
        self._data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data'
        )
    
    def get_current_trends(self) -> List[Dict[str, Any]]:
        """
        Load current trends from sample_trends.json.
        
        Returns:
            List of trend dictionaries
        """
        try:
            trends_file = os.path.join(self._data_dir, 'sample_trends.json')
            with open(trends_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            trends = data.get('trends', [])
            print(f'✅ Loaded {len(trends)} trends')
            return trends
            
        except FileNotFoundError:
            print('⚠️ sample_trends.json not found, returning empty trends')
            return []
        except Exception as e:
            print(f'❌ Error loading trends: {e}')
            return []
    
    def get_trend_by_id(self, trend_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific trend by its ID.
        
        Args:
            trend_id: The trend identifier
            
        Returns:
            Trend dictionary or None if not found
        """
        trends = self.get_current_trends()
        return next((t for t in trends if t['id'] == trend_id), None)
    
    def get_trends_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """
        Filter trends by social platform.
        
        Args:
            platform: Platform name (TikTok, Instagram, Pinterest, etc.)
            
        Returns:
            List of trends active on that platform
        """
        trends = self.get_current_trends()
        return [t for t in trends if platform in t.get('platforms', [])]
    
    def get_top_trends(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top trends sorted by popularity score.
        
        Args:
            limit: Number of trends to return
            
        Returns:
            List of top trends
        """
        trends = self.get_current_trends()
        sorted_trends = sorted(
            trends, 
            key=lambda t: t.get('popularity_score', 0), 
            reverse=True
        )
        return sorted_trends[:limit]
    
    def get_trend_summary(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a summary of trend data for AI analysis.
        
        Args:
            trend: Full trend data
            
        Returns:
            Simplified trend summary
        """
        return {
            'id': trend.get('id', ''),
            'name': trend.get('name', ''),
            'description': trend.get('description', ''),
            'keywords': trend.get('keywords', []),
            'target_products': trend.get('target_products', []),
            'marketing_angle': trend.get('marketing_angle', ''),
            'color_palette': trend.get('color_palette', []),
            'popularity_score': trend.get('popularity_score', 0),
            'platforms': trend.get('platforms', [])
        }
    
    def match_trend_to_product(self, product: Dict[str, Any], trend: Dict[str, Any]) -> float:
        """
        Calculate a simple match score between a product and trend.
        
        Args:
            product: Product summary dict
            trend: Trend dict
            
        Returns:
            Match score 0-100
        """
        score = 0.0
        
        product_type = product.get('type', '').lower()
        product_title = product.get('title', '').lower()
        product_tags = [t.lower() for t in product.get('tags', [])]
        
        # Check target products
        for target in trend.get('target_products', []):
            target_lower = target.lower()
            if target_lower in product_type or target_lower in product_title:
                score += 30
            for tag in product_tags:
                if target_lower in tag:
                    score += 10
        
        # Check keywords
        all_product_text = f"{product_title} {product_type} {' '.join(product_tags)}".lower()
        for keyword in trend.get('keywords', []):
            if keyword.lower() in all_product_text:
                score += 5
        
        return min(score, 100)


# Global singleton instance
trends_service = TrendsService()
