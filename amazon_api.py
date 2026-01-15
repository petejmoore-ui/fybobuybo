"""
Amazon Product Advertising API Integration
Using amazon-paapi5 (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import datetime
import json
from pathlib import Path

from amazon_paapi5 import AmazonApi, AmazonApiException

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_MARKETPLACE = "www.amazon.co.uk"  # UK

# Simple local cache directory
CACHE_DIR = Path("./amazon_cache")
CACHE_DIR.mkdir(exist_ok=True)

# Initialize Amazon API client
amazon = AmazonApi(
    access_key=AMAZON_ACCESS_KEY,
    secret_key=AMAZON_SECRET_KEY,
    partner_tag=AMAZON_ASSOC_TAG,
    marketplace=AMAZON_MARKETPLACE
)

def cache_path(asin: str) -> Path:
    return CACHE_DIR / f"{asin}.json"

def save_to_cache(asin: str, data: dict):
    with open(cache_path(asin), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_from_cache(asin: str) -> dict | None:
    path = cache_path(asin)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def format_price_display(price: dict) -> str:
    if not price:
        return "N/A"
    return f"{price.get('Amount', 'N/A')} {price.get('Currency', '')}"

def format_rating_display(rating: dict) -> str:
    if not rating:
        return "N/A"
    return f"{rating.get('Rating', 0)} / 5 ({rating.get('Count', 0)} reviews)"

def get_amazon_product_data(asin: str) -> dict | None:
    """
    Fetch product data from Amazon, with local caching.
    """
    # Check cache first
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        response = amazon.get_items([asin])
        item = response.get("ItemsResult", {}).get("Items", [{}])[0]

        product_data = {
            "asin": asin,
            "title": item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue"),
            "url": item.get("DetailPageURL"),
            "price": item.get("Offers", {}).get("Listings", [{}])[0].get("Price"),
            "rating": item.get("CustomerReviews", {}),
            "images": item.get("Images", {}),
            "last_updated": datetime.datetime.utcnow().isoformat(),
        }

        save_to_cache(asin, product_data)
        return product_data

    except AmazonApiException as e:
        print(f"Amazon API error for {asin}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        return None
