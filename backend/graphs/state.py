"""
LangGraph State Schema.
Defines the typed state that flows through the graph nodes.
"""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field


class ProductSummary(TypedDict):
    """Summary of a Shopify product for AI processing."""
    id: str
    title: str
    type: str
    description: str
    price: float
    tags: List[str]
    vendor: str
    status: str


class TrendSummary(TypedDict):
    """Summary of a trend for AI processing."""
    name: str
    description: str
    keywords: List[str]
    target_products: List[str]
    marketing_angle: str
    color_palette: List[str]
    popularity_score: int


class ProductRecommendation(TypedDict):
    """AI-generated recommendation for a product."""
    productId: str
    productTitle: str
    needsMakeover: bool
    matchedTrends: List[str]
    confidence: int
    recommendations: Dict[str, Any]


class GraphState(TypedDict, total=False):
    """
    Main state schema for the product optimization graph.
    
    This state flows through all nodes and accumulates data
    as the workflow progresses.
    """
    # Input
    product_ids: Optional[List[str]]  # Specific products to analyze, or None for all
    
    # Fetched data
    products: List[Dict[str, Any]]  # Raw product data from Shopify
    product_summaries: List[ProductSummary]  # Processed for AI
    trends: List[Dict[str, Any]]  # Raw trend data
    trend_summaries: List[TrendSummary]  # Processed for AI
    
    # Analysis results
    analysis_results: Dict[str, Any]  # Full analysis from AI
    recommendations: List[ProductRecommendation]  # Extracted recommendations
    
    # Update tracking
    products_to_update: List[str]  # Product IDs approved for update
    updated_products: List[Dict[str, Any]]  # Successfully updated products
    failed_updates: List[Dict[str, str]]  # Products that failed to update
    
    # Metadata
    error: Optional[str]  # Error message if workflow failed
    ai_model_used: str  # Which AI model was used
    timestamp: str  # When workflow ran


@dataclass
class WorkflowConfig:
    """Configuration for the optimization workflow."""
    auto_apply: bool = False  # Whether to auto-apply recommendations
    confidence_threshold: int = 70  # Minimum confidence to recommend
    max_products: int = 50  # Max products to process
    trends_limit: int = 10  # Max trends to consider
    dry_run: bool = True  # If True, don't actually update Shopify
