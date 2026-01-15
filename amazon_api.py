"""
Amazon Product Advertising API Integration
Using python-amazon-paapi (PyPI package: python-amazon-paapi >=5.0.0)
Handles fetching product data, caching, and formatting
"""

import os
from amazon_paapi import AmazonApi  # Correct import - no AmazonApiException
from pathlib import Path
import json
import datetime

# Amazon API Credentials from environment variables
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_REGION = "uk"  # UK marketplace (lowercase, as required)

# Cache folder (note: ephemeral on Render - consider persistent storage for prod)
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_from_cache(asin: str) -> dict | None:
    """Load product data from local cache if available and not older than 1 day."""
    cache_file = CACHE_DIR / f"{asin}.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Cache valid for 1 day
        cached_time_str = data.get("cached_at")
        if cached_time_str:
            cached_time = datetime.datetime.fromisoformat(cached_time_str)
            if datetime.datetime.utcnow() - cached_time < datetime.timedelta(days=1):
                return data
    return None

def save_to_cache(asin: str, product_data: dict):
    """Save product data to local cache with timestamp."""
    cache_file = CACHE_DIR / f"{asin}.json"
    product_data["cached_at"] = datetime.datetime.utcnow().isoformat()
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(product_data, f, ensure_ascii=False, indent=2)

def get_amazon_product_data(asin: str) -> dict | None:
    """
    Fetch product data from Amazon PA-API (or cache).
    Returns dict with product info or None on failure.
    """
    # Try cache first
    cached = get_from_cache(asin)
    if cached:
        return cached

    if not all([AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG]):
        print(f"Missing Amazon API credentials for ASIN {asin}")
        return None

    try:
        # Initialize API client with throttling to avoid rate limits
        api = AmazonApi(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            associate_tag=AMAZON_ASSOC_TAG,
            country=AMAZON_REGION,
            throttling=2,  # Wait 2 seconds between requests (adjust as needed)
        )

        response = api.get_items(item_ids=[asin])

        if not response.items_result or not response.items_result.items:
            print(f"No items found for ASIN {asin}")
            return None

        item = response.items_result.items[0]

        # Safely extract fields (some may be missing)
        price = None
        if item.offers and item.offers.listings and item.offers.listings[0].price:
            price = item.offers.listings[0].price.display_amount

        rating = None
        total_reviews = None
        if item.customer_reviews:
            rating = item.customer_reviews.rating
            total_reviews = item.customer_reviews.total_reviews

        image_url = None
        if item.images and item.images.primary and item.images.primary.large:
            image_url = item.images.primary.large.url

        product_data = {
            "asin": asin,
            "title": item.item_info.title.display_value if item.item_info and item.item_info.title else None,
            "url": item.detail_page_url,
            "price": price,
            "rating": rating,
            "total_reviews": total_reviews,
            "image_url": image_url,
        }

        save_to_cache(asin, product_data)
        return product_data

    except Exception as e:
        print(f"Amazon API error for ASIN {asin}: {type(e).__name__} - {e}")
        return None

# Formatting helpers (unchanged)
def format_price_display(price: str | None) -> str:
    return price or "N/A"

def format_rating_display(rating: float | None, total_reviews: int | None) -> str:
    if rating is not None and total_reviews is not None:
        return f"{rating:.1f} ⭐ ({total_reviews})"
    return "No reviews"
