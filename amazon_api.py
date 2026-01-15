"""
Amazon Product Advertising API Integration
Handles fetching product data, caching, and formatting
UK Amazon (amazon.co.uk)
"""

import os
import datetime
from pathlib import Path
import json

# Correct import for amightygirl paapi5 SDK
from amightygirl.paapi5_python_sdk.amazon_api import AmazonApi, AmazonApiException

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_REGION = "uk"

# Simple caching directory
CACHE_DIR = Path("amazon_cache")
CACHE_DIR.mkdir(exist_ok=True)


def load_from_cache(asin: str) -> dict | None:
    """Load product data from local cache if it exists and is fresh (1 day)."""
    cache_file = CACHE_DIR / f"{asin}.json"
    if cache_file.exists():
        mtime = datetime.datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.datetime.now() - mtime < datetime.timedelta(days=1):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def save_to_cache(asin: str, data: dict) -> None:
    """Save product data to local cache."""
    cache_file = CACHE_DIR / f"{asin}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_amazon_product_data(asin: str) -> dict | None:
    """Fetch product data from Amazon API or cache."""
    # Try cache first
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        api = AmazonApi(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            partner_tag=AMAZON_ASSOC_TAG,
            country=AMAZON_REGION
        )
        product_data = api.get_items([asin])[0]  # get_items returns a list

        # Save to cache
        save_to_cache(asin, product_data)
        return product_data

    except AmazonApiException as e:
        print(f"Amazon API error for {asin}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        return None


# Optional helper formatting functions
def format_price_display(product: dict) -> str:
    """Return formatted price string for a product."""
    price = product.get("Offers", {}).get("Listings", [{}])[0].get("Price", {}).get("DisplayAmount")
    return price or "N/A"


def format_rating_display(product: dict) -> str:
    """Return formatted rating string for a product."""
    rating = product.get("CustomerReviews", {}).get("StarRating")
    count = product.get("CustomerReviews", {}).get("TotalReviews")
    if rating and count:
        return f"{rating} ⭐ ({count})"
    return "No reviews"
