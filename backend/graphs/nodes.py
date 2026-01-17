"""
LangGraph Node Functions.
Each function represents a node in the optimization workflow graph.
Nodes are pure functions that take state and return state updates.
"""

from typing import Dict, Any
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import product_service, trends_service, ai_optimizer
from .state import GraphState


def fetch_products_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: Fetch products from Shopify.
    
    Reads: product_ids (optional)
    Writes: products, product_summaries
    """
    try:
        product_ids = state.get('product_ids')
        
        if product_ids:
            # Fetch specific products
            products = []
            for pid in product_ids:
                product = product_service.get_product_by_id(pid)
                if product:
                    products.append(product)
        else:
            # Fetch all products
            products = product_service.fetch_products()
        
        # Generate summaries
        summaries = [
            product_service.get_product_summary(p) for p in products
        ]
        
        return {
            'products': products,
            'product_summaries': summaries,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'error': f"Failed to fetch products: {str(e)}",
            'products': [],
            'product_summaries': []
        }


def fetch_trends_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: Fetch current trends.
    
    Reads: Nothing
    Writes: trends, trend_summaries
    """
    try:
        trends = trends_service.get_current_trends()
        
        summaries = [
            trends_service.get_trend_summary(t) for t in trends
        ]
        
        return {
            'trends': trends,
            'trend_summaries': summaries
        }
        
    except Exception as e:
        return {
            'error': f"Failed to fetch trends: {str(e)}",
            'trends': [],
            'trend_summaries': []
        }


def analyze_products_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: Analyze products against trends using AI.
    
    Reads: product_summaries, trend_summaries
    Writes: analysis_results, ai_model_used
    """
    try:
        product_summaries = state.get('product_summaries', [])
        trend_summaries = state.get('trend_summaries', [])
        
        if not product_summaries:
            return {
                'error': 'No products to analyze',
                'analysis_results': {'success': False}
            }
        
        if not trend_summaries:
            return {
                'error': 'No trends available for analysis',
                'analysis_results': {'success': False}
            }
        
        results = ai_optimizer.analyze_products_with_trends(
            product_summaries,
            trend_summaries
        )
        
        return {
            'analysis_results': results,
            'ai_model_used': results.get('ai_model', 'unknown')
        }
        
    except Exception as e:
        return {
            'error': f"Analysis failed: {str(e)}",
            'analysis_results': {'success': False, 'error': str(e)}
        }


def generate_recommendations_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: Extract and filter recommendations from analysis.
    
    Reads: analysis_results
    Writes: recommendations, products_to_update
    """
    try:
        analysis = state.get('analysis_results', {})
        
        if not analysis.get('success'):
            return {
                'recommendations': [],
                'products_to_update': []
            }
        
        # Extract recommendations that meet threshold
        recommendations = []
        products_to_update = []
        
        for item in analysis.get('analysis', []):
            if item.get('needsMakeover') and item.get('confidence', 0) >= 70:
                recommendations.append(item)
                products_to_update.append(item['productId'])
        
        return {
            'recommendations': recommendations,
            'products_to_update': products_to_update
        }
        
    except Exception as e:
        return {
            'error': f"Failed to generate recommendations: {str(e)}",
            'recommendations': [],
            'products_to_update': []
        }


def apply_updates_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: Apply recommendations to Shopify products.
    
    Reads: products_to_update, recommendations
    Writes: updated_products, failed_updates
    """
    try:
        products_to_update = state.get('products_to_update', [])
        recommendations = state.get('recommendations', [])
        
        if not products_to_update:
            return {
                'updated_products': [],
                'failed_updates': []
            }
        
        # Create lookup for recommendations
        rec_lookup = {r['productId']: r.get('recommendations', {}) for r in recommendations}
        
        updated = []
        failed = []
        
        for product_id in products_to_update:
            recs = rec_lookup.get(product_id, {})
            
            if not recs:
                failed.append({
                    'productId': product_id,
                    'error': 'No recommendations found'
                })
                continue
            
            try:
                # Build update payload
                import json
                updates = {
                    'title': recs.get('optimizedTitle'),
                    'descriptionHtml': recs.get('optimizedDescription'),
                    'seo': {
                        'title': recs.get('seoTitle'),
                        'description': recs.get('seoDescription')
                    },
                    'metafields': [
                        {
                            'namespace': 'ai_optimizer',
                            'key': 'layout_style',
                            'value': recs.get('layoutStyle', 'hero'),
                            'type': 'single_line_text_field'
                        },
                        {
                            'namespace': 'ai_optimizer',
                            'key': 'trend_alignment',
                            'value': recs.get('trendAlignment', ''),
                            'type': 'single_line_text_field'
                        },
                        {
                            'namespace': 'ai_optimizer',
                            'key': 'trust_badges',
                            'value': json.dumps(recs.get('trustBadges', [])),
                            'type': 'json'
                        }
                    ]
                }
                
                result = product_service.update_product(product_id, updates)
                updated.append(result)
                
            except Exception as e:
                failed.append({
                    'productId': product_id,
                    'error': str(e)
                })
        
        return {
            'updated_products': updated,
            'failed_updates': failed
        }
        
    except Exception as e:
        return {
            'error': f"Failed to apply updates: {str(e)}",
            'updated_products': [],
            'failed_updates': []
        }


# Conditional routing functions for the graph
def should_continue_to_analysis(state: GraphState) -> str:
    """Determine if we should proceed to analysis."""
    if state.get('error'):
        return 'error'
    if not state.get('product_summaries') or not state.get('trend_summaries'):
        return 'error'
    return 'analyze'


def should_apply_updates(state: GraphState) -> str:
    """Determine if we should apply updates."""
    if state.get('error'):
        return 'error'
    if not state.get('products_to_update'):
        return 'done'
    return 'apply'
