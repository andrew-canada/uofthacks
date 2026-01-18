"""
Services module for AI Product Optimizer.
Each service is designed as a stateless class for easy LangGraph node integration.
"""

from .shopify_auth import ShopifyAuth, shopify_auth
from .product_service import ProductService, product_service
from .trends_service import TrendsService, trends_service
from .ai_optimizer import AIOptimizer
from .video_analyzer import VideoAnalyzer, video_analyzer
from .trend_matcher import TrendMatcher
from .marketing_generator import MarketingGenerator

__all__ = [
    'ShopifyAuth', 'shopify_auth',
    'ProductService', 'product_service', 
    'TrendsService', 'trends_service',
    'AIOptimizer',
    'VideoAnalyzer', 'video_analyzer',
    'TrendMatcher',
    'MarketingGenerator'
]

# Lazy singletons to avoid initializing external SDKs at import time
_ai_optimizer = None
_trend_matcher = None
_marketing_generator = None

def get_ai_optimizer() -> AIOptimizer:
    global _ai_optimizer
    if _ai_optimizer is None:
        _ai_optimizer = AIOptimizer()
    return _ai_optimizer

def get_trend_matcher() -> TrendMatcher:
    global _trend_matcher
    if _trend_matcher is None:
        _trend_matcher = TrendMatcher()
    return _trend_matcher

def get_marketing_generator() -> MarketingGenerator:
    global _marketing_generator
    if _marketing_generator is None:
        _marketing_generator = MarketingGenerator()
    return _marketing_generator

# Backwards-compatible exports (callables)
__all__.extend([
    'get_ai_optimizer', 'get_trend_matcher', 'get_marketing_generator'
])
