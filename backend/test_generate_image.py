#!/usr/bin/env python3
"""Smoke-test image generation by calling the backend apply endpoint for a product.

Usage:
  python test_generate_image.py <product_id>
  TEST_PRODUCT_ID=123 python test_generate_image.py
  TEST_SERVER=http://127.0.0.1:5000 TEST_PRODUCT_ID=123 python test_generate_image.py

This script POSTs to `/api/products/<id>/apply` with a minimal payload and prints
the HTTP status and response body for debugging.
"""
import os
import sys
import json
import requests


def main():
    server = os.environ.get('TEST_SERVER', 'http://127.0.0.1:5000')
    product_id = None
    if len(sys.argv) > 1:
        product_id = sys.argv[1]
    else:
        product_id = os.environ.get('TEST_PRODUCT_ID')

    if not product_id:
        print('Usage: python test_generate_image.py <product_id> OR set TEST_PRODUCT_ID env var')
        sys.exit(2)

    url = f"{server.rstrip('/')}/api/products/{product_id}/apply"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'trigger': 'smoke-test',
        'dry_run': True
    }

    print('POST', url)
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
    except Exception as e:
        print('Request failed:', e)
        sys.exit(3)

    print('HTTP', r.status_code)
    ct = r.headers.get('Content-Type', '')
    print('Content-Type:', ct)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)


if __name__ == '__main__':
    main()
