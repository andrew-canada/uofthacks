"""
Products API Routes.
Handles product CRUD and AI optimization endpoints.
"""

from flask import Blueprint, jsonify, request
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import product_service, trends_service, ai_optimizer

products_bp = Blueprint('products', __name__)


@products_bp.route('/', methods=['GET'])
def get_products():
    """
    Get all products from Shopify.
    
    Query params:
        limit (int): Max products to return (default 50)
    
    Returns:
        JSON with success status and products array
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        products = product_service.fetch_products(limit=limit)
        
        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@products_bp.route('/<path:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Get a single product by ID.
    
    Args:
        product_id: Shopify product GID (URL encoded)
    
    Returns:
        JSON with product data
    """
    try:
        # Handle URL encoding of GID
        if not product_id.startswith('gid://'):
            product_id = f"gid://shopify/Product/{product_id}"
        
        product = product_service.get_product_by_id(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        return jsonify({
            'success': True,
            'product': product
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@products_bp.route('/analyze', methods=['POST'])
def analyze_all_products():
    """
    Analyze ALL products against current trends using Gemini AI.
    
    This endpoint:
    1. Fetches all products from Shopify
    2. Loads current trends from JSON
    3. Sends to Gemini for analysis
    4. Returns products that need makeovers with recommendations
    
    Returns:
        JSON with analysis results and recommendations
    """
    try:
        # Fetch products
        products = product_service.fetch_products()
        
        if not products:
            return jsonify({
                'success': False,
                'error': 'No products found'
            }), 404
        
        # Get product summaries for AI
        product_summaries = [
            product_service.get_product_summary(p) for p in products
        ]
        
        # Load trends
        trends = trends_service.get_current_trends()
        
        if not trends:
            return jsonify({
                'success': False,
                'error': 'No trends data available'
            }), 500
        
        # Get trend summaries for AI
        trend_summaries = [
            trends_service.get_trend_summary(t) for t in trends
        ]
        
        # Run AI analysis
        analysis_results = ai_optimizer.analyze_products_with_trends(
            product_summaries, 
            trend_summaries
        )
        
        return jsonify(analysis_results)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@products_bp.route('/<path:product_id>/analyze', methods=['POST'])
def analyze_single_product(product_id):
    """
    Analyze a single product against trends.
    
    Args:
        product_id: Shopify product GID
    
    Returns:
        JSON with product and recommendations
    """
    try:
        # Handle URL encoding
        if not product_id.startswith('gid://'):
            product_id = f"gid://shopify/Product/{product_id}"
        
        # Fetch the specific product
        product = product_service.get_product_by_id(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        # Get summary
        product_summary = product_service.get_product_summary(product)
        
        # Load trends
        trends = trends_service.get_current_trends()
        trend_summaries = [trends_service.get_trend_summary(t) for t in trends]
        
        # Run AI analysis on just this product
        analysis_results = ai_optimizer.analyze_products_with_trends(
            [product_summary],
            trend_summaries
        )
        
        return jsonify({
            'success': True,
            'product': product,
            'analysis': analysis_results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@products_bp.route('/<path:product_id>/apply', methods=['POST'])
def apply_recommendations(product_id):
    """
    Apply AI recommendations to a specific product.
    
    Args:
        product_id: Shopify product GID
    
    Request body (optional):
        recommendations: Pre-computed recommendations to apply
    
    Returns:
        JSON with updated product data
    """
    try:
        # Handle URL encoding
        if not product_id.startswith('gid://'):
            product_id = f"gid://shopify/Product/{product_id}"
        
        # Check if recommendations are provided in request
        data = request.get_json() or {}
        recommendations = data.get('recommendations')
        
        # If no recommendations provided, run fresh analysis
        if not recommendations:
            product = product_service.get_product_by_id(product_id)
            
            if not product:
                return jsonify({
                    'success': False,
                    'error': 'Product not found'
                }), 404
            
            product_summary = product_service.get_product_summary(product)
            trends = trends_service.get_current_trends()
            trend_summaries = [trends_service.get_trend_summary(t) for t in trends]
            
            analysis_results = ai_optimizer.analyze_products_with_trends(
                [product_summary],
                trend_summaries
            )
            
            recommendations = ai_optimizer.get_product_recommendations(
                product_id,
                analysis_results
            )
            
            if not recommendations:
                return jsonify({
                    'success': False,
                    'error': 'No recommendations found for this product. It may not need a makeover.'
                }), 404
        
        # Build update payload
        updates = {
            'title': recommendations.get('optimizedTitle'),
            'descriptionHtml': recommendations.get('optimizedDescription'),
            'seo': {
                'title': recommendations.get('seoTitle'),
                'description': recommendations.get('seoDescription')
            },
            'metafields': [
                {
                    'namespace': 'ai_optimizer',
                    'key': 'layout_style',
                    'value': recommendations.get('layoutStyle', 'hero'),
                    'type': 'single_line_text_field'
                },
                {
                    'namespace': 'ai_optimizer',
                    'key': 'color_scheme',
                    'value': recommendations.get('colorScheme', 'neutral'),
                    'type': 'single_line_text_field'
                },
                {
                    'namespace': 'ai_optimizer',
                    'key': 'show_countdown',
                    'value': str(recommendations.get('showCountdown', False)).lower(),
                    'type': 'boolean'
                },
                {
                    'namespace': 'ai_optimizer',
                    'key': 'trust_badges',
                    'value': json.dumps(recommendations.get('trustBadges', [])),
                    'type': 'json'
                },
                {
                    'namespace': 'ai_optimizer',
                    'key': 'trend_alignment',
                    'value': recommendations.get('trendAlignment', ''),
                    'type': 'single_line_text_field'
                },
                {
                    'namespace': 'ai_optimizer',
                    'key': 'marketing_angle',
                    'value': recommendations.get('marketingAngle', ''),
                    'type': 'single_line_text_field'
                }
            ]
        }
        
        # Update the product
        updated_product = product_service.update_product(product_id, updates)
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully with trend-based recommendations',
            'product': updated_product,
            'appliedRecommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
