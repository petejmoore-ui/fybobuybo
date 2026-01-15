"""
Amazon Product Advertising API Integration
Using python-amazon-paapi (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import datetime
import json
from pathlib import Path
from amazon_paapi import AmazonApi, AmazonApiException

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_LOCALE = "uk"  # UK store

# Simple file-based cache
CACHE_DIR = Path("./amazon_cache")
CACHE_DIR.mkdir(exist_ok=True)

def cache_path(asin: str) -> Path:
    return CACHE_DIR / f"{asin}.json"

def save_to_cache(asin: str, data: dict):
    try:
        with open(cache_path(asin), "w") as f:
            json.dump({"timestamp": datetime.datetime.utcnow().isoformat(), "data": data}, f)
    except Exception as e:
        print(f"Failed to save cache for {asin}: {e}")

def load_from_cache(asin: str, max_age_hours: int = 24) -> dict | None:
    path = cache_path(asin)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            cached = json.load(f)
        ts = datetime.datetime.fromisoformat(cached["timestamp"])
        if (datetime.datetime.utcnow() - ts).total_seconds() > max_age_hours * 3600:
            return None
        return cached["data"]
    except Exception as e:
        print(f"Failed to load cache for {asin}: {e}")
        return None

# Initialize Amazon API client
amazon = AmazonApi(
    access_key=AMAZON_ACCESS_KEY,
    secret_key=AMAZON_SECRET_KEY,
    associate_tag=AMAZON_ASSOC_TAG,
    locale=AMAZON_LOCALE
)

def get_amazon_product_data(asin: str) -> dict | None:
    """Fetch Amazon product data with caching"""
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        product_data = amazon.get_items([asin])
        save_to_cache(asin, product_data)
        return product_data
    except AmazonApiException as e:
        print(f"Amazon API error for {asin}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        return None

# Formatting helpers
def format_price_display(price_info: dict | None) -> str | None:
    if not price_info:
        return None
    amount = price_info.get("Amount")
    currency = price_info.get("Currency")
    if amount is None or currency is None:
        return None
    return f"{amount:.2f} {currency}"

def format_rating_display(rating: float | None) -> str | None:
    if rating is None:
        return None
    return f"{rating:.1f} ★"

# New function to enrich a list of products
def enrich_products_with_amazon_data(products: list[dict]) -> list[dict]:
    """
    Given a list of product dicts with 'asin',
    fetch and add Amazon data (price & rating)
    """
    enriched = []
    for product in products:
        asin = product.get("asin")
        if not asin:
            enriched.append(product)
            continue
        data = get_amazon_product_data(asin)
        if data:
            product["amazon_price"] = format_price_display(
                data.get("Offers", {}).get("Price")
            )
            product["amazon_rating"] = format_rating_display(
                data.get("CustomerReviews", {}).get("AverageRating")
            )
        enriched.append(product)
    return enriched
