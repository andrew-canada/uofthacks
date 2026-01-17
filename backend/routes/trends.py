"""
Trends API Routes.
Handles trend data endpoints.
"""

from flask import Blueprint, jsonify, request
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import trends_service

trends_bp = Blueprint('trends', __name__)


@trends_bp.route('/', methods=['GET'])
def get_trends():
    """
    Get all current trends.
    
    Query params:
        platform (str): Filter by platform (TikTok, Instagram, etc.)
        top (int): Return only top N trends by popularity
    
    Returns:
        JSON with trends array
    """
    try:
        platform = request.args.get('platform')
        top = request.args.get('top', type=int)
        
        if platform:
            trends = trends_service.get_trends_by_platform(platform)
        elif top:
            trends = trends_service.get_top_trends(limit=top)
        else:
            trends = trends_service.get_current_trends()
        
        return jsonify({
            'success': True,
            'trends': trends,
            'count': len(trends)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trends_bp.route('/<trend_id>', methods=['GET'])
def get_trend(trend_id):
    """
    Get a specific trend by ID.
    
    Args:
        trend_id: The trend identifier
    
    Returns:
        JSON with trend data
    """
    try:
        trend = trends_service.get_trend_by_id(trend_id)
        
        if not trend:
            return jsonify({
                'success': False,
                'error': 'Trend not found'
            }), 404
        
        return jsonify({
            'success': True,
            'trend': trend
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trends_bp.route('/platforms', methods=['GET'])
def get_platforms():
    """
    Get list of all platforms with trends.
    
    Returns:
        JSON with platforms array
    """
    try:
        trends = trends_service.get_current_trends()
        
        # Extract unique platforms
        platforms = set()
        for trend in trends:
            platforms.update(trend.get('platforms', []))
        
        return jsonify({
            'success': True,
            'platforms': sorted(list(platforms))
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trends_bp.route('/match/<path:product_id>', methods=['GET'])
def match_product_to_trends(product_id):
    """
    Find trends that match a specific product.
    
    Args:
        product_id: Shopify product GID
    
    Returns:
        JSON with matching trends and scores
    """
    try:
        from services import product_service
        
        # Handle URL encoding
        if not product_id.startswith('gid://'):
            product_id = f"gid://shopify/Product/{product_id}"
        
        product = product_service.get_product_by_id(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        product_summary = product_service.get_product_summary(product)
        trends = trends_service.get_current_trends()
        
        # Calculate match scores
        matches = []
        for trend in trends:
            score = trends_service.match_trend_to_product(product_summary, trend)
            if score > 0:
                matches.append({
                    'trend': trend,
                    'matchScore': score
                })
        
        # Sort by score
        matches.sort(key=lambda x: x['matchScore'], reverse=True)
        
        return jsonify({
            'success': True,
            'product': product_summary,
            'matches': matches
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
