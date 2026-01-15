"""
Amazon Product Advertising API Integration
Using amazon-paapi5 (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import json
import datetime
from pathlib import Path

from amazon_paapi5.amazon_paapi import AmazonApi  # Correct import for amazon-paapi5

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_MARKETPLACE = "www.amazon.co.uk"  # UK marketplace

# Cache folder
CACHE_DIR = Path("amazon_cache")
CACHE_DIR.mkdir(exist_ok=True)


def save_to_cache(asin: str, data: dict) -> None:
    """Save product data to cache"""
    filepath = CACHE_DIR / f"{asin}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_from_cache(asin: str) -> dict | None:
    """Load product data from cache if it exists"""
    filepath = CACHE_DIR / f"{asin}.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def format_price_display(price: dict) -> str:
    """Format price dictionary from API"""
    if not price:
        return "N/A"
    amount = price.get("Amount")
    currency = price.get("Currency")
    return f"{currency} {amount}" if amount else "N/A"


def format_rating_display(rating: float, total_reviews: int) -> str:
    """Format rating and review count"""
    if rating is None or total_reviews is None:
        return "No ratings"
    return f"{rating:.1f} ★ ({total_reviews})"


def get_amazon_product_data(asin: str) -> dict | None:
    """Fetch product data from Amazon API or cache"""
    # Check cache first
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        amazon = AmazonApi(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            associate_tag=AMAZON_ASSOC_TAG,
            marketplace=AMAZON_MARKETPLACE,
        )
        response = amazon.get_items([asin])
        if not response.items:
            return None

        item = response.items[0]
        product_data = {
            "asin": asin,
            "title": item.title,
            "price": format_price_display(item.price),
            "rating": format_rating_display(item.rating, item.total_reviews),
            "url": item.detail_page_url,
            "image_url": item.main_image.url if item.main_image else None,
            "last_updated": datetime.datetime.utcnow().isoformat(),
        }

        save_to_cache(asin, product_data)
        return product_data

    except Exception as e:
        print(f"Amazon API error for {asin}: {e}")
        return None
