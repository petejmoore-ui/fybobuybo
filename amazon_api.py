"""
Amazon Product Advertising API Integration
Using python-amazon-paapi (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import datetime
from pathlib import Path
from amazon_paapi import AmazonApi  # Removed AmazonApiException

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_REGION = os.environ.get("AMAZON_REGION", "us")

# Initialize Amazon API client
amazon_api = AmazonApi(
    AMAZON_ACCESS_KEY,
    AMAZON_SECRET_KEY,
    AMAZON_ASSOC_TAG,
    AMAZON_REGION
)

# Example cache path (adjust as needed)
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

def save_to_cache(asin: str, data: dict):
    """Save product data to cache."""
    path = CACHE_DIR / f"{asin}.json"
    import json
    with open(path, "w") as f:
        json.dump(data, f)

def load_from_cache(asin: str) -> dict | None:
    """Load product data from cache if it exists."""
    path = CACHE_DIR / f"{asin}.json"
    if path.exists():
        import json
        with open(path, "r") as f:
            return json.load(f)
    return None

def get_amazon_product_data(asin: str) -> dict | None:
    """Fetch product data from Amazon API, with caching."""
    # Try cache first
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        product_data = amazon_api.get_items(asin=asin)  # Adjust call as needed
        save_to_cache(asin, product_data)
        return product_data

    except Exception as e:
        print(f"Amazon API error for {asin}: {e}")
        return None

# Optional helpers for formatting
def format_price_display(price: float) -> str:
    return f"${price:.2f}"

def format_rating_display(rating: float) -> str:
    return f"{rating:.1f} / 5"
