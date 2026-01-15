"""
Amazon Product Advertising API Integration
Using amazon-paapi5 (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
from amazon_paapi import AmazonApi, AmazonApiException
from pathlib import Path
import json
import datetime

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_REGION = "uk"  # UK marketplace

# Cache folder
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_from_cache(asin: str) -> dict | None:
    """Load product data from local cache if available and recent."""
    cache_file = CACHE_DIR / f"{asin}.json"
    if cache_file.exists():
        with open(cache_file, "r") as f:
            data = json.load(f)
        # Cache valid for 1 day
        cached_time = datetime.datetime.fromisoformat(data.get("cached_at"))
        if datetime.datetime.utcnow() - cached_time < datetime.timedelta(days=1):
            return data
    return None

def save_to_cache(asin: str, product_data: dict):
    """Save product data to local cache."""
    cache_file = CACHE_DIR / f"{asin}.json"
    product_data["cached_at"] = datetime.datetime.utcnow().isoformat()
    with open(cache_file, "w") as f:
        json.dump(product_data, f)

def get_amazon_product_data(asin: str) -> dict | None:
    """Fetch product data from Amazon PAAPI or cache."""
    cached = get_from_cache(asin)
    if cached:
        return cached

    try:
        api = AmazonApi(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            associate_tag=AMAZON_ASSOC_TAG,
            country=AMAZON_REGION,
        )

        response = api.get_items(item_ids=[asin])
        if not response.items_result or not response.items_result.items:
            return None

        item = response.items_result.items[0]

        product_data = {
            "asin": asin,
            "title": item.title,
            "url": item.detail_page_url,
            "price": item.offers.listings[0].price.display_amount if item.offers else None,
            "rating": item.customer_reviews.rating if item.customer_reviews else None,
            "total_reviews": item.customer_reviews.total_reviews if item.customer_reviews else None,
            "image_url": item.images.primary.large.url if item.images else None,
        }

        save_to_cache(asin, product_data)
        return product_data

    except AmazonApiException as e:
        print(f"Amazon API error for {asin}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        return None

# Optional helpers to format data
def format_price_display(price: str | None) -> str:
    return price or "N/A"

def format_rating_display(rating: float | None, total_reviews: int | None) -> str:
    if rating and total_reviews:
        return f"{rating} ⭐ ({total_reviews})"
    return "No reviews"
