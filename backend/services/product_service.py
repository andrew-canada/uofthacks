"""
Shopify Product Service.
Handles CRUD operations for Shopify products via GraphQL API.
Designed as a stateless service for LangGraph integration.
"""

import requests
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from .shopify_auth import shopify_auth


class ProductService:
    """
    Manages Shopify product operations.
    All methods are stateless and can be used as LangGraph nodes.
    """
    
    def __init__(self):
        self._config = config.shopify
        self._auth = shopify_auth
    
    def fetch_products(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch products from Shopify.
        
        Args:
            limit: Maximum number of products to fetch (default 50)
            
        Returns:
            List of product dictionaries
            
        Raises:
            Exception: If API request fails
        """
        query = """
        query FetchProducts($first: Int!) {
          products(first: $first) {
            edges {
              node {
                id
                title
                description
                descriptionHtml
                handle
                productType
                tags
                vendor
                status
                createdAt
                updatedAt
                seo {
                  title
                  description
                }
                images(first: 5) {
                  edges {
                    node {
                      id
                      url
                      altText
                    }
                  }
                }
                variants(first: 5) {
                  edges {
                    node {
                      id
                      title
                      price
                      sku
                      inventoryQuantity
                    }
                  }
                }
                metafields(first: 20, namespace: "ai_optimizer") {
                  edges {
                    node {
                      namespace
                      key
                      value
                      type
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        try:
            response = requests.post(
                self._config.graphql_url,
                json={'query': query, 'variables': {'first': limit}},
                headers=self._auth.get_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'errors' in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            products = [edge['node'] for edge in data['data']['products']['edges']]
            print(f'✅ Fetched {len(products)} products')
            return products
            
        except requests.exceptions.RequestException as e:
            print(f'❌ Error fetching products: {e}')
            raise Exception(f"Failed to fetch products: {e}")
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single product by ID.
        
        Args:
            product_id: Shopify product GID
            
        Returns:
            Product dictionary or None if not found
        """
        query = """
        query GetProduct($id: ID!) {
          product(id: $id) {
            id
            title
            description
            descriptionHtml
            handle
            productType
            tags
            vendor
            status
            seo {
              title
              description
            }
            images(first: 5) {
              edges {
                node {
                  id
                  url
                  altText
                }
              }
            }
            variants(first: 5) {
              edges {
                node {
                  id
                  title
                  price
                  sku
                }
              }
            }
            metafields(first: 20, namespace: "ai_optimizer") {
              edges {
                node {
                  namespace
                  key
                  value
                  type
                }
              }
            }
          }
        }
        """
        
        try:
            response = requests.post(
                self._config.graphql_url,
                json={'query': query, 'variables': {'id': product_id}},
                headers=self._auth.get_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            return data['data'].get('product')
            
        except Exception as e:
            print(f'❌ Error fetching product {product_id}: {e}')
            return None
    
    def update_product(self, product_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a product with new data.
        
        Args:
            product_id: Shopify product GID
            updates: Dictionary of fields to update
            
        Returns:
            Updated product data
            
        Raises:
            Exception: If update fails
        """
        mutation = """
        mutation UpdateProduct($input: ProductInput!) {
          productUpdate(input: $input) {
            product {
              id
              title
              descriptionHtml
              seo {
                title
                description
              }
              metafields(first: 20, namespace: "ai_optimizer") {
                edges {
                  node {
                    namespace
                    key
                    value
                  }
                }
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            'input': {
                'id': product_id,
                **updates
            }
        }
        
        try:
            response = requests.post(
                self._config.graphql_url,
                json={'query': mutation, 'variables': variables},
                headers=self._auth.get_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data['data']['productUpdate']['userErrors']:
                errors = data['data']['productUpdate']['userErrors']
                raise Exception(f"Update errors: {errors}")
            
            print(f'✅ Product {product_id} updated successfully')
            return data['data']['productUpdate']['product']
            
        except requests.exceptions.RequestException as e:
            print(f'❌ Error updating product: {e}')
            raise Exception(f"Failed to update product: {e}")

    def add_product_image(self, product_gids: str, attachment_base64: str, alt_text: str = '') -> Dict[str, Any]:
      """Upload an image to a Shopify product using REST API `products/<id>/images.json`.

      Args:
        product_gids: Shopify product GID (gid://shopify/Product/<id>)
        attachment_base64: base64 encoded image data (no data: prefix)
        alt_text: alt text for the image

      Returns:
        Parsed JSON response from Shopify or raises Exception on failure.
      """
      # Extract numeric id from gid
      try:
        numeric = product_gids.rsplit('/', 1)[-1]
      except Exception:
        raise Exception('Invalid product GID')

      # Build REST URL from configured graphql_url by swapping path to REST endpoint
      try:
        rest_base = self._config.rest_url
      except Exception:
        # derive from graphql url
        rest_base = self._config.graphql_url.replace('/admin/api/2024-10/graphql.json', '')

      url = f"{rest_base}/admin/api/2024-10/products/{numeric}/images.json"
      payload = {'image': {'attachment': attachment_base64, 'alt': alt_text}}

      try:
        res = requests.post(url, json=payload, headers=self._auth.get_headers())
        res.raise_for_status()
        return res.json()
      except Exception as e:
        print(f'❌ Failed to upload product image: {e} - response: {getattr(res, "text", None)}')
        raise
    
    def get_product_summary(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a summary of product data for AI analysis.
        
        Args:
            product: Full product data
            
        Returns:
            Simplified product summary
        """
        price = 0.0
        if product.get('variants', {}).get('edges'):
            price = float(product['variants']['edges'][0]['node'].get('price', 0))
        
        return {
            'id': product['id'],
            'title': product.get('title', ''),
            'type': product.get('productType', ''),
            'description': product.get('description', ''),
            'price': price,
            'tags': product.get('tags', []),
            'vendor': product.get('vendor', ''),
            'status': product.get('status', ''),
            'image_count': len(product.get('images', {}).get('edges', [])),
            'has_seo': bool(product.get('seo', {}).get('title'))
        }


# Global singleton instance
product_service = ProductService()
