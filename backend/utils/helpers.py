"""
Helper utility functions.
"""

import re
from typing import Dict, Any
import html


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: HTML string
        
    Returns:
        Plain text without HTML tags
    """
    if not text:
        return ""
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    clean = html.unescape(clean)
    # Normalize whitespace
    clean = ' '.join(clean.split())
    
    return clean


def truncate_text(text: str, max_length: int = 150, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: String to append when truncating
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text or ""
    
    # Find last space before max_length
    truncate_at = max_length - len(suffix)
    last_space = text.rfind(' ', 0, truncate_at)
    
    if last_space > 0:
        return text[:last_space] + suffix
    else:
        return text[:truncate_at] + suffix


def format_price(price: float, currency: str = "USD") -> str:
    """
    Format a price value.
    
    Args:
        price: Price as float
        currency: Currency code
        
    Returns:
        Formatted price string
    """
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'CAD': 'C$',
        'AUD': 'A$'
    }
    
    symbol = currency_symbols.get(currency, '$')
    return f"{symbol}{price:.2f}"


def slugify(text: str) -> str:
    """
    Convert text to URL-safe slug.
    
    Args:
        text: Text to convert
        
    Returns:
        URL-safe slug
    """
    if not text:
        return ""
    
    # Lowercase
    slug = text.lower()
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Remove non-alphanumeric characters (except hyphens)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


def merge_dicts(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        updates: Dictionary with updates
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result
