"""
Routes module for AI Product Optimizer.
Contains Flask blueprints for API endpoints.
"""

from .products import products_bp
from .trends import trends_bp
from .health import health_bp
from .shopify_graphql import shopify_graphql_bp

__all__ = ['products_bp', 'trends_bp', 'health_bp', 'shopify_graphql_bp']
