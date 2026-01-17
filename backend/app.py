"""
AI Product Optimizer Backend - Main Application.
Flask server with REST API endpoints for product optimization.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from routes import products_bp, trends_bp, health_bp
from config import config


def create_app():
    """
    Application factory for Flask app.
    
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Disable strict slashes to avoid 308 redirects
    app.url_map.strict_slashes = False
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(trends_bp, url_prefix='/api/trends')
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'name': 'AI Product Optimizer Backend',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'products': '/api/products',
                'trends': '/api/trends'
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    
    return app


# Create the application instance
app = create_app()


if __name__ == '__main__':
    port = config.server.port
    debug = config.server.debug
    
    # Print startup info
    print("=" * 50)
    print("🚀 AI Product Optimizer Backend")
    print("=" * 50)
    print(f"📍 Server: http://localhost:{port}")
    print(f"📊 Store: {config.shopify.store_domain or 'Not configured'}")
    print(f"🤖 AI: {'Enabled' if config.ai.gemini_api_key else 'Disabled'}")
    print(f"🎬 Video Analysis: {'Enabled' if config.ai.twelve_labs_api_key else 'Disabled'}")
    print(f"🐛 Debug Mode: {debug}")
    print("=" * 50)
    print("\n📚 Available Endpoints:")
    print("  GET  /health              - Health check")
    print("  GET  /health/config       - Configuration status")
    print("  GET  /health/services     - All services status")
    print("  GET  /api/products        - List all products")
    print("  POST /api/products/analyze - Analyze products with AI")
    print("  POST /api/products/<id>/apply - Apply recommendations")
    print("  GET  /api/trends          - List current trends")
    print("  GET  /api/trends/<id>     - Get specific trend")
    print("=" * 50 + "\n")
    
    app.run(debug=debug, port=port, host='0.0.0.0')
