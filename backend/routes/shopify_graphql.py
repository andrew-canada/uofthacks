"""
Shopify GraphQL proxy route.

Allows POST forwarding of GraphQL queries from the frontend to the
Shopify Admin GraphQL API using the configured Admin access token.

Note: This is intended for development/demo. In production, secure and
validate requests appropriately and don't expose raw proxying without
authentication.
"""
from flask import Blueprint, request, jsonify, Response
import sys
import os
import requests
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

shopify_graphql_bp = Blueprint('shopify_graphql', __name__)


@shopify_graphql_bp.route('/admin/graphql', methods=['POST'])
def proxy_graphql():
    """Proxy a GraphQL POST to the Shopify Admin API.

    Expects the request body to be the GraphQL JSON payload (query/variables).
    """
    # Determine target URL
    graphql_url = getattr(config.shopify, 'graphql_url', None)
    if not graphql_url:
        store = getattr(config.shopify, 'store_domain', None)
        api_version = getattr(config.shopify, 'api_version', '2026-01')
        if not store:
            return jsonify({'error': 'Shop domain not configured (SHOP_DOMAIN)'}), 400
        # Normalize store: if a full URL was provided, extract hostname
        if isinstance(store, str) and store.startswith('http'):
            parsed = urlparse(store)
            store = parsed.netloc or parsed.path
        graphql_url = f'https://{store}/admin/api/{api_version}/graphql.json'

    token = getattr(config.shopify, 'access_token', None)
    if not token:
        return jsonify({'error': 'Shopify access token not configured (SHOPIFY_ACCESS_TOKEN)'}), 400

    # Forward the request body and headers
    headers = {
        'Content-Type': request.headers.get('Content-Type', 'application/json'),
        'X-Shopify-Access-Token': token,
    }

    # Ensure graphql_url is a full URL. If user set only a hostname, prefix https://
    final_url = graphql_url
    if not final_url.startswith('http'):
        final_url = 'https://' + final_url

    try:
        resp = requests.post(final_url, headers=headers, data=request.get_data(), timeout=30)
    except requests.RequestException as e:
        return jsonify({'error': 'Failed to connect to Shopify', 'details': str(e)}), 502

    return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type', 'application/json'))
