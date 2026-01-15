"""
Amazon Product Advertising API Integration
Using amazon-paapi (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import datetime
from pathlib import Path
from amazon_paapi import AmazonApi  # No more AmazonApiException

# Optional: caching folder
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Amazon API credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_COUNTRY = "UK"  # For UK marketplace

# Initialize API client
amazon = AmazonApi(
    access_key=AMAZON_ACCESS_KEY,
    secret_key=AMAZON_SECRET_KEY,
    partner_tag=AMAZON_ASSOC_TAG,
    country=AMAZON_COUNTRY
)

# -------------------------------
# Caching helpers
# -------------------------------
def get_cache_file(asin: str) -> Path:
    return CACHE_DIR / f"{asin}.json"

def load_from_cache(asin: str):
    path = get_cache_file(asin)
    if path.exists():
        import json
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_to_cache(asin: str, data):
    path = get_cache_file(asin)
    import json
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)

# -------------------------------
# Fetch product data
# -------------------------------
def get_amazon_product_data(asin: str) -> dict | None:
    """Fetch Amazon product data with caching"""
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        product_data = amazon.get_items([asin])
        save_to_cache(asin, product_data)
        return product_data
    except Exception as e:
        print(f"Amazon API error for {asin}: {e}")
        return None

# -------------------------------
# Optional formatting helpers
# -------------------------------
def format_price_display(price: dict) -> str:
    """Format price dict returned by API"""
    if not price:
        return "N/A"
    amount = price.get("Amount")
    currency = price.get("Currency")
    if amount and currency:
        return f"{amount:.2f} {currency}"
    return "N/A"

def format_rating_display(rating: dict) -> str:
    """Format rating dict returned by API"""
    if not rating:
        return "N/A"
    stars = rating.get("AverageRating")
    count = rating.get("TotalReviews")
    if stars is not None and count is not None:
        return f"{stars} stars ({count} reviews)"
    return "N/A"

# -------------------------------
# Optional enrich helper
# -------------------------------
def enrich_products_with_amazon_data(products: list[dict]) -> list[dict]:
    """Add Amazon data to a list of products with ASINs"""
    for product in products:
        asin = product.get("asin")
        if asin:
            data = get_amazon_product_data(asin)
            product["amazon_data"] = data
    return products
