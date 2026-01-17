"""
Shopify Authentication Service.
Handles OAuth token management and API authentication.
Designed as a stateless service for LangGraph integration.
"""

import requests
from datetime import datetime, timedelta
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config


class ShopifyAuth:
    """
    Manages Shopify API authentication.
    Supports both access token and OAuth client credentials flow.
    """
    
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._config = config.shopify
    
    def get_access_token(self) -> str:
        """
        Get a valid access token.
        Uses stored token if available, otherwise fetches via OAuth.
        
        Returns:
            str: Valid Shopify access token
            
        Raises:
            Exception: If unable to obtain token
        """
        # If we have a static access token configured, use it
        if self._config.access_token:
            return self._config.access_token
        
        # Check if cached token is still valid
        if self._access_token and self._token_expiry:
            if datetime.now() < self._token_expiry:
                return self._access_token
        
        # Fetch new token via OAuth
        return self._fetch_oauth_token()
    
    def _fetch_oauth_token(self) -> str:
        """
        Fetch new access token using client credentials.
        
        Returns:
            str: New access token
            
        Raises:
            Exception: If OAuth request fails
        """
        if not self._config.client_id or not self._config.client_secret:
            raise Exception("OAuth credentials not configured. Set SHOPIFY_ACCESS_TOKEN or OAuth credentials.")
        
        try:
            url = f"https://{self._config.store_domain}/admin/oauth/access_token"
            data = {
                'grant_type': 'client_credentials',
                'client_id': self._config.client_id,
                'client_secret': self._config.client_secret
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            self._access_token = result['access_token']
            
            # Token expires in 24 hours, refresh 1 hour before
            expires_in = result.get('expires_in', 86400)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 3600)
            
            print('✅ Shopify access token obtained')
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            print(f'❌ Error getting Shopify access token: {e}')
            raise Exception(f"Failed to obtain Shopify access token: {e}")
    
    def get_headers(self) -> dict:
        """
        Get headers for Shopify API requests.
        
        Returns:
            dict: Headers with authentication
        """
        return {
            'X-Shopify-Access-Token': self.get_access_token(),
            'Content-Type': 'application/json'
        }
    
    def validate_connection(self) -> dict:
        """
        Validate Shopify connection by making a test request.
        
        Returns:
            dict: Connection status and shop info
        """
        try:
            url = f"https://{self._config.store_domain}/admin/api/{self._config.api_version}/shop.json"
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            
            shop_data = response.json().get('shop', {})
            return {
                'connected': True,
                'shop_name': shop_data.get('name'),
                'domain': shop_data.get('domain'),
                'email': shop_data.get('email')
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }


# Global singleton instance
shopify_auth = ShopifyAuth()
