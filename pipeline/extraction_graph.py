"""Shopify site extractor (LangGraph Edition)

Usage:
  python extraction.py --store your-store.myshopify.com --token shpat_xxx --out shop_export.json
"""

import os
import sys
import time
import json
import argparse
from typing import Optional, List, TypedDict, Any

import requests

# --- LANGGRAPH IMPORTS ---
from langgraph.graph import StateGraph, END, START

# --- CONSTANTS & QUERIES (Unchanged) ---
GRAPHQL_PRODUCT_QUERY = '''
query productsPage($first: Int!, $after: String) {
  products(first: $first, after: $after) {
    pageInfo { hasNextPage }
    edges {
      cursor
      node {
        id
        title
        handle
        vendor
        productType
        tags
        publishedAt
        createdAt
        updatedAt
        descriptionHtml
        description
        onlineStoreUrl
        images(first: 250) { edges { node { id altText originalSrc width height } } }
        variants(first: 250) { edges { node { id title sku price inventoryQuantity } } }
        metafields(first: 250) { edges { node { id namespace key type value } } }
      }
    }
  }
}
'''

GRAPHQL_SHOP_QUERY = '''
query shopInfo { shop { id name myshopifyDomain email primaryDomain { host } } }
'''


# --- HELPER FUNCTIONS (Unchanged Logic) ---
def _graphql_request(url: str, token: str, query: str, variables: dict):
    headers = {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': token,
    }
    payload = {'query': query, 'variables': variables}
    for attempt in range(1, 6):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
        except requests.RequestException as e:
            wait = attempt * 1.5
            time.sleep(wait)
            if attempt == 5:
                raise
            continue

        if r.status_code == 200:
            data = r.json()
            if 'errors' in data:
                raise RuntimeError(f"GraphQL errors: {data['errors']}")
            return data.get('data')
        elif r.status_code in (429, 502, 503, 504):
            wait = attempt * 2
            time.sleep(wait)
            continue
        else:
            raise RuntimeError(f"GraphQL request failed: {r.status_code} {r.text}")


def fetch_shop_info(shop_domain: str, token: str, api_version: str) -> dict:
    url = f'https://{shop_domain}/admin/api/{api_version}/graphql.json'
    data = _graphql_request(url, token, GRAPHQL_SHOP_QUERY, {})
    return data.get('shop') if data else {}


def _filter_shop(shop: dict) -> dict:
    if not shop:
        return {}
    out = {}
    if 'name' in shop:
        out['name'] = shop.get('name')
    if 'myshopifyDomain' in shop:
        out['myshopifyDomain'] = shop.get('myshopifyDomain')
    if 'email' in shop:
        out['email'] = shop.get('email')
    pd = shop.get('primaryDomain') or {}
    if isinstance(pd, dict) and 'host' in pd:
        out['primaryDomain'] = pd.get('host')
    return out


def _filter_product_node(node: dict) -> dict:
    out = {}
    for key in ('title', 'handle', 'vendor', 'productType', 'tags', 'description', 'descriptionHtml', 'onlineStoreUrl'):
        if key in node and node.get(key) not in (None, '', []):
            out[key] = node.get(key)

    imgs = []
    for img in node.get('images', []):
        if not isinstance(img, dict): continue
        src = img.get('originalSrc') or img.get('src')
        alt = img.get('altText') or img.get('alt')
        if src:
            item = {'src': src}
            if alt: item['alt'] = alt
            imgs.append(item)
    if imgs: out['images'] = imgs

    vars_out = []
    for v in node.get('variants', []):
        if not isinstance(v, dict): continue
        v_item = {}
        for vk in ('title', 'sku', 'price'):
            if vk in v and v.get(vk) not in (None, ''):
                v_item[vk] = v.get(vk)
        if v_item: vars_out.append(v_item)
    if vars_out: out['variants'] = vars_out

    mfs = []
    for m in node.get('metafields', []):
        if not isinstance(m, dict): continue
        mf = {}
        for mk in ('namespace', 'key', 'type', 'value'):
            if mk in m and m.get(mk) not in (None, ''):
                mf[mk] = m.get(mk)
        if mf: mfs.append(mf)
    if mfs: out['metafields'] = mfs

    if 'tags' in out and isinstance(out['tags'], str):
        out['tags'] = [t.strip() for t in out['tags'].split(',') if t.strip()]

    return out


def fetch_all_products(shop_domain: str, token: str, api_version: str) -> list:
    url = f'https://{shop_domain}/admin/api/{api_version}/graphql.json'
    products = []
    first = 100
    after = None

    while True:
        variables = {'first': first, 'after': after}
        data = _graphql_request(url, token, GRAPHQL_PRODUCT_QUERY, variables)
        if not data or 'products' not in data:
            break

        edges = data['products']['edges']
        for edge in edges:
            node = edge.get('node')
            if node is None: continue
            node['images'] = [e['node'] for e in node.get('images', {}).get('edges', [])]
            node['variants'] = [e['node'] for e in node.get('variants', {}).get('edges', [])]
            node['metafields'] = [e['node'] for e in node.get('metafields', {}).get('edges', [])]
            filtered = _filter_product_node(node)
            products.append(filtered)

        page_info = data['products']['pageInfo']
        if page_info.get('hasNextPage'):
            after = edges[-1]['cursor'] if edges else None
            time.sleep(0.3)
            continue
        break

    return products


# --- LANGGRAPH IMPLEMENTATION ---

# 1. Define the State
class ExtractionState(TypedDict):
    # Inputs
    store: str
    token: str
    out_path: str
    api_version: str
    
    # Internal Storage
    shop_metadata: dict
    products: List[dict]
    
    # Status
    status: str

# 2. Define the Nodes
def node_get_shop_info(state: ExtractionState):
    """Fetches shop metadata."""
    print(f"[{state['store']}] Fetching shop info...")
    raw_info = fetch_shop_info(state['store'], state['token'], state['api_version'])
    clean_info = _filter_shop(raw_info)
    return {"shop_metadata": clean_info}

def node_get_products(state: ExtractionState):
    """Fetches all products via pagination."""
    print(f"[{state['store']}] Fetching products (this may take a while)...")
    prods = fetch_all_products(state['store'], state['token'], state['api_version'])
    return {"products": prods}

def node_save_export(state: ExtractionState):
    """Writes the final JSON to disk."""
    payload = {
        'exported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'shop': state['shop_metadata'],
        'products_count': len(state['products']),
        'products': state['products'],
    }
    
    with open(state['out_path'], 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Success! Wrote export to {state['out_path']} ({len(state['products'])} products)")
    return {"status": "completed"}

# 3. Build the Graph
def build_graph():
    workflow = StateGraph(ExtractionState)
    
    # Add Nodes
    workflow.add_node("fetch_info", node_get_shop_info)
    workflow.add_node("fetch_products", node_get_products)
    workflow.add_node("save_file", node_save_export)
    
    # Add Edges (Linear Flow)
    workflow.add_edge(START, "fetch_info")
    workflow.add_edge("fetch_info", "fetch_products")
    workflow.add_edge("fetch_products", "save_file")
    workflow.add_edge("save_file", END)
    
    return workflow.compile()


# --- MAIN EXECUTION ---
def main(argv: Optional[list] = None):
    parser = argparse.ArgumentParser(description='Export Shopify store data to JSON')
    parser.add_argument('--store', required=True, help='Shop domain')
    parser.add_argument('--token', required=False, help='Admin API token')
    parser.add_argument('--out', default='shop_export.json', help='Output file')
    parser.add_argument('--api-version', default='2024-10', help='API version')
    args = parser.parse_args(argv)

    token = args.token or os.environ.get('SHOPIFY_ACCESS_TOKEN')
    if not token:
        print('Error: Admin API token required via --token or SHOPIFY_ACCESS_TOKEN env var')
        sys.exit(2)

    # Initialize the Graph
    app = build_graph()
    
    # Initial State
    initial_state = {
        "store": args.store,
        "token": token,
        "out_path": args.out,
        "api_version": args.api_version,
        "shop_metadata": {},
        "products": [],
        "status": "started"
    }

    # Execute
    try:
        app.invoke(initial_state)
    except Exception as e:
        print(f"❌ Workflow Failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()