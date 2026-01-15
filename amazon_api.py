"""
Amazon Product Advertising API Integration
Using python-amazon-paapi (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import datetime
from pathlib import Path
from amazon_paapi import AmazonApi  # Only import AmazonApi

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOCIATE_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG")
AMAZON_COUNTRY = "co.uk"  # UK site

# Optional cache directory
CACHE_DIR = Path("amazon_cache")
CACHE_DIR.mkdir(exist_ok=True)


def save_to_cache(asin: str, data: dict):
    """Save product data to cache"""
    cache_file = CACHE_DIR / f"{asin}.json"
    import json
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_from_cache(asin: str) -> dict | None:
    """Load product data from cache if available"""
    cache_file = CACHE_DIR / f"{asin}.json"
    if cache_file.exists():
        import json
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_amazon_product_data(asin: str) -> dict | None:
    """Fetch product data from Amazon API, with caching"""
    # Check cache first
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        amazon = AmazonApi(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            associate_tag=AMAZON_ASSOCIATE_TAG,
            country=AMAZON_COUNTRY
        )

        product_data = amazon.get_items([asin])[0]  # Returns a list of products
        save_to_cache(asin, product_data)
        return product_data

    except Exception as e:
        # Catch all errors from the API
        print(f"Amazon API error for {asin}: {e}")
        return None


def format_price_display(price: dict | None) -> str:
    """Format Amazon price dictionary for display"""
    if not price:
        return "N/A"
    amount = price.get("Amount")
    currency = price.get("Currency")
    if amount is None or currency is None:
        return "N/A"
    return f"{currency} {amount:.2f}"


def format_rating_display(rating: float | None) -> str:
    """Format Amazon rating for display"""
    if rating is None:
        return "No rating"
    return f"{rating:.1f} / 5"
