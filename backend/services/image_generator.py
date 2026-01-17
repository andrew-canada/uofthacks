"""Image generation service using Google Gemini (Generative AI).

Provides `generate_image_base64(prompt, size)` which returns a base64-encoded image attachment
suitable for use with Shopify's REST image upload (`attachment`). Falls back to None when
Gemini client is unavailable.
"""
import os
import base64
from typing import Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

from . import __name__ as _pkg


def generate_image_base64(prompt: str, size: str = '1024x1024') -> Optional[str]:
    """Generate an image for the given prompt and return it as a base64 string.

    Returns None if the image could not be generated.
    """
    if not GEMINI_AVAILABLE:
        return None

    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GEMINI_APIKEY')
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        # Use image model - this API surface may vary depending on the installed client.
        # We attempt to call the common helper `genai.images.generate` if available.
        if hasattr(genai, 'images') and hasattr(genai.images, 'generate'):
            result = genai.images.generate(prompt=prompt, size=size)
            # result may include base64 bytes under result.data[0].b64_json or result[0].b64_json
            data = getattr(result, 'data', None) or result
            first = data[0]
            b64 = first.get('b64_json') or first.get('image') or first.get('b64')
            if not b64:
                return None
            # ensure it's base64 string
            return b64

        # Fallback: try the older Image.create surface
        if hasattr(genai, 'Image') and hasattr(genai.Image, 'create'):
            im = genai.Image.create(prompt=prompt, size=size)
            b64 = getattr(im, 'b64_json', None) or im.get('b64_json')
            return b64

    except Exception as e:
        print(f'❌ Image generation failed: {e}')
        return None

    return None
