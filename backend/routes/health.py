"""
Health Check Routes.
Provides system status and configuration validation endpoints.
"""

from flask import Blueprint, jsonify
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from services import shopify_auth, video_analyzer

health_bp = Blueprint('health', __name__)


@health_bp.route('/', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        JSON with service status
    """
    return jsonify({
        'status': 'OK',
        'message': 'AI Product Optimizer Backend Running',
        'version': '1.0.0'
    })


@health_bp.route('/config', methods=['GET'])
def config_status():
    """
    Check configuration status for all services.
    
    Returns:
        JSON with configuration validation results
    """
    validation = config.validate()
    
    return jsonify({
        'status': 'OK',
        'configuration': validation,
        'store': config.shopify.store_domain if config.shopify.store_domain else 'Not configured',
        'ai_enabled': validation['gemini_configured'],
        'video_analysis_enabled': validation['twelve_labs_configured']
    })


@health_bp.route('/shopify', methods=['GET'])
def shopify_status():
    """
    Test Shopify API connection.
    
    Returns:
        JSON with Shopify connection status
    """
    try:
        connection = shopify_auth.validate_connection()
        return jsonify({
            'status': 'OK' if connection['connected'] else 'ERROR',
            **connection
        })
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'connected': False,
            'error': str(e)
        }), 500


@health_bp.route('/services', methods=['GET'])
def services_status():
    """
    Check status of all integrated services.
    
    Returns:
        JSON with all service statuses
    """
    validation = config.validate()
    
    services = {
        'shopify': {
            'configured': validation['shopify_configured'],
            'store': config.shopify.store_domain or None
        },
        'gemini': {
            'configured': validation['gemini_configured'],
            'model': 'gemini-pro' if validation['gemini_configured'] else None
        },
        'twelve_labs': {
            'configured': validation['twelve_labs_configured'],
            'available': video_analyzer.is_available()
        },
        'youtube': {
            'configured': validation['youtube_configured']
        }
    }
    
    all_ready = all([
        validation['shopify_configured'],
        validation['gemini_configured']
    ])
    
    return jsonify({
        'status': 'READY' if all_ready else 'PARTIAL',
        'message': 'All core services ready' if all_ready else 'Some services not configured',
        'services': services
    })
