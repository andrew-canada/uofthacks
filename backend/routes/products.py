"""
Products API Routes.
Handles product CRUD and AI optimization endpoints.
"""

from flask import Blueprint, jsonify, request
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import (
    product_service, 
    trends_service, 
    ai_optimizer,
    trend_matcher,
    marketing_generator
)

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


# ============================================================
# NEW SPLIT ENDPOINTS: Trend Matching + Marketing Generation
# ============================================================

@products_bp.route('/match-trends', methods=['POST'])
def match_products_to_trends():
    """
    Step 1: Find which products match which trends.
    
    This endpoint ONLY identifies matches - it does NOT generate new marketing copy.
    Use this to see which products could benefit from trend-based optimization.
    
    Request body (optional):
        product_ids: List of specific product IDs to match (default: all products)
    
    Returns:
        JSON with matches array showing product-trend alignments
    """
    try:
        data = request.get_json() or {}
        product_ids = data.get('product_ids')
        
        # Fetch products
        if product_ids:
            products = []
            for pid in product_ids:
                if not pid.startswith('gid://'):
                    pid = f"gid://shopify/Product/{pid}"
                product = product_service.get_product_by_id(pid)
                if product:
                    products.append(product)
        else:
            products = product_service.fetch_products()
        
        if not products:
            return jsonify({
                'success': False,
                'error': 'No products found'
            }), 404
        
        # Get product summaries
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
        
        trend_summaries = [
            trends_service.get_trend_summary(t) for t in trends
        ]
        
        # Run trend matching (Step 1 only)
        match_results = trend_matcher.find_matches(product_summaries, trend_summaries)
        
        return jsonify({
            'success': True,
            **match_results,
            'products_analyzed': len(product_summaries),
            'trends_available': len(trend_summaries)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@products_bp.route('/<path:product_id>/generate-marketing', methods=['POST'])
def generate_marketing_for_product(product_id):
    """
    Step 2: Generate new marketing copy for a product-trend match.
    
    This takes a product that has been matched to a trend (from /match-trends)
    and generates new marketing copy: title, description, SEO, etc.
    
    Args:
        product_id: Shopify product GID
    
    Request body:
        trend_id: The trend to align the marketing with (required)
        
    Returns:
        JSON with original and generated marketing copy
    """
    try:
        # Handle URL encoding
        if not product_id.startswith('gid://'):
            product_id = f"gid://shopify/Product/{product_id}"
        
        data = request.get_json() or {}
        trend_id = data.get('trend_id')
        
        if not trend_id:
            return jsonify({
                'success': False,
                'error': 'trend_id is required. Use /match-trends first to find matching trends.'
            }), 400
        
        # Fetch the product
        product = product_service.get_product_by_id(product_id)
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        product_summary = product_service.get_product_summary(product)
        
        # Load trends and find the specified one
        trends = trends_service.get_current_trends()
        trend = next((t for t in trends if t.get('id') == trend_id), None)
        
        if not trend:
            return jsonify({
                'success': False,
                'error': f'Trend {trend_id} not found'
            }), 404
        
        trend_summary = trends_service.get_trend_summary(trend)
        
        # Generate marketing (Step 2)
        result = marketing_generator.generate_marketing(
            product_summary, 
            trend_summary,
            match_info=data.get('match_info')
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@products_bp.route('/match-and-generate', methods=['POST'])
def match_and_generate():
    """
    Combined endpoint: Match trends AND generate marketing in one call.
    
    This is a convenience endpoint that combines:
    1. /match-trends - Find matching products
    2. /generate-marketing - Create new copy for each match
    
    Request body (optional):
        product_ids: List of specific product IDs (default: all)
        generate_for_all: If true, generate for all matches (default: false, only top match)
    
    Returns:
        JSON with matches and generated marketing for each
    """
    try:
        data = request.get_json() or {}
        product_ids = data.get('product_ids')
        generate_for_all = data.get('generate_for_all', False)
        
        # Step 1: Get products
        if product_ids:
            products = []
            for pid in product_ids:
                if not pid.startswith('gid://'):
                    pid = f"gid://shopify/Product/{pid}"
                product = product_service.get_product_by_id(pid)
                if product:
                    products.append(product)
        else:
            products = product_service.fetch_products()
        
        if not products:
            return jsonify({
                'success': False,
                'error': 'No products found'
            }), 404
        
        product_summaries = [product_service.get_product_summary(p) for p in products]
        
        # Create lookup dict for product summaries
        products_lookup = {p['id']: p for p in product_summaries}
        
        # Step 2: Load trends
        trends = trends_service.get_current_trends()
        if not trends:
            return jsonify({
                'success': False,
                'error': 'No trends data available'
            }), 500
        
        trend_summaries = [trends_service.get_trend_summary(t) for t in trends]
        trends_lookup = {t['id']: t for t in trend_summaries}
        
        # Step 3: Find matches
        match_results = trend_matcher.find_matches(product_summaries, trend_summaries)
        
        if not match_results.get('success'):
            return jsonify(match_results), 500
        
        # Step 4: Generate marketing for matches
        generated_results = []
        
        for match in match_results.get('matches', []):
            product_id = match.get('product_id')
            product = products_lookup.get(product_id)
            
            if not product:
                continue
            
            matched_trends = match.get('matched_trends', [])
            
            # Generate for top trend only, or all if requested
            trends_to_generate = matched_trends if generate_for_all else matched_trends[:1]
            
            for trend_info in trends_to_generate:
                trend_id = trend_info.get('trend_id')
                trend = trends_lookup.get(trend_id)
                
                if not trend:
                    continue
                
                gen_result = marketing_generator.generate_marketing(
                    product, 
                    trend,
                    match_info=trend_info
                )
                
                generated_results.append({
                    'product_id': product_id,
                    'product_title': match.get('product_title'),
                    'trend_match': trend_info,
                    'marketing': gen_result
                })
        
        return jsonify({
            'success': True,
            'match_results': match_results,
            'generated_marketing': generated_results,
            'products_analyzed': len(product_summaries),
            'matches_found': len(match_results.get('matches', [])),
            'marketing_generated': len(generated_results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
