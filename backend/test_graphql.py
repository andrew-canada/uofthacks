#!/usr/bin/env python3
"""Simple test script to POST a GraphQL query to the local backend proxy
and print the raw response for debugging.

Usage:
  python test_graphql.py
  TEST_GRAPHQL_ENDPOINT=http://127.0.0.1:5000/admin/graphql python test_graphql.py
  TEST_GRAPHQL_QUERY='{ shop { name myshopifyDomain } }' python test_graphql.py
"""
import os
import json
import sys
import requests


def main():
    endpoint = os.environ.get('TEST_GRAPHQL_ENDPOINT', 'http://127.0.0.1:5000/admin/graphql')
    query = os.environ.get('TEST_GRAPHQL_QUERY', '{ shop { name myshopifyDomain } }')

    payload = {'query': query}
    headers = {'Content-Type': 'application/json'}

    print(f'POST {endpoint}')
    try:
        r = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    except Exception as e:
        print('Request failed:', e)
        sys.exit(2)

    print('HTTP', r.status_code)
    ct = r.headers.get('Content-Type', '')
    print('Content-Type:', ct)

    try:
        data = r.json()
        print(json.dumps(data, indent=2))
    except Exception:
        print(r.text)


if __name__ == '__main__':
    main()
