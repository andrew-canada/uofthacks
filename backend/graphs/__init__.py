"""
LangGraph module for AI Product Optimizer.
Contains graph nodes, state schema, and workflow definitions.
"""

from .state import GraphState
from .nodes import (
    fetch_products_node,
    fetch_trends_node,
    analyze_products_node,
    generate_recommendations_node,
    apply_updates_node
)

__all__ = [
    'GraphState',
    'fetch_products_node',
    'fetch_trends_node', 
    'analyze_products_node',
    'generate_recommendations_node',
    'apply_updates_node'
]
