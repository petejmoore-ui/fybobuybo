"""
Amazon Product Advertising API Integration (UK)
Using amightygirl.paapi5-python-sdk (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import datetime
from pathlib import Path
import json

# Correct import for amazon-paapi5
from amightygirl.paapi5_python_sdk import AmazonApi, AmazonApiException

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_PARTNER_TAG = os.environ.get("AMAZON_PARTNER_TAG")  # Your Associate Tag
AMAZON_COUNTRY = "uk"  # UK store

# Cache directory
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

def cache_file_path(asin: str) -> Path:
    """Return the cache file path for a given ASIN."""
    return CACHE_DIR / f"{asin}.json"

def save_to_cache(asin: str, data: dict):
    """Save product data to a cache file."""
    with open(cache_file_path(asin), "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.datetime.utcnow().isoformat(), "data": data}, f)

def load_from_cache(asin: str) -> dict | None:
    """Load product data from cache if it's recent (24h)."""
    path = cache_file_path(asin)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            cached = json.load(f)
        timestamp = datetime.datetime.fromisoformat(cached["timestamp"])
        if (datetime.datetime.utcnow() - timestamp).total_seconds() > 86400:  # 24h
            return None
        return cached["data"]
    except Exception:
        return None

def format_price_display(price: float | None) -> str:
    if price is None:
        return "Price not available"
    return f"£{price:.2f}"

def format_rating_display(rating: float | None) -> str:
    if rating is None:
        return "No rating"
    return f"{rating:.1f}/5"

def enrich_products_with_amazon_data(asin: str) -> dict | None:
    """Fetch product data from Amazon, with caching."""
    # Return cached data if available
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        api = AmazonApi(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG, AMAZON_COUNTRY)
        product = api.get_items([asin])[0]  # get_items returns a list
        product_data = {
            "title": product.title,
            "asin": product.asin,
            "price": product.price.amount if product.price else None,
            "currency": product.price.currency if product.price else "GBP",
            "rating": product.rating,
            "url": product.detail_page_url,
        }
        save_to_cache(asin, product_data)
        return product_data

    except AmazonApiException as e:
        print(f"Amazon API error for {asin}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        return None
