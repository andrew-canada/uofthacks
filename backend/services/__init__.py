"""
Services module for AI Product Optimizer.
Each service is designed as a stateless class for easy LangGraph node integration.
"""

from .shopify_auth import ShopifyAuth, shopify_auth
from .product_service import ProductService, product_service
from .trends_service import TrendsService, trends_service
from .ai_optimizer import AIOptimizer, ai_optimizer
from .video_analyzer import VideoAnalyzer, video_analyzer
from .trend_matcher import TrendMatcher, trend_matcher
from .marketing_generator import MarketingGenerator, marketing_generator

__all__ = [
    'ShopifyAuth', 'shopify_auth',
    'ProductService', 'product_service', 
    'TrendsService', 'trends_service',
    'AIOptimizer', 'ai_optimizer',
    'VideoAnalyzer', 'video_analyzer',
    'TrendMatcher', 'trend_matcher',
    'MarketingGenerator', 'marketing_generator'
]
