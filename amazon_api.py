"""
Amazon Product Advertising API Integration
Using amazon-paapi5 (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import json
import datetime
from pathlib import Path
from amazon_paapi5 import AmazonApi, AmazonApiException

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_REGION = "uk"  # UK marketplace

# Path for cached product data
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

# Initialize Amazon API client
amazon_client = AmazonApi(
    access_key=AMAZON_ACCESS_KEY,
    secret_key=AMAZON_SECRET_KEY,
    associate_tag=AMAZON_ASSOC_TAG,
    country=AMAZON_REGION
)

def cache_file_path(asin: str) -> Path:
    """Return the cache file path for a given ASIN."""
    return CACHE_DIR / f"{asin}.json"

def save_to_cache(asin: str, data: dict):
    """Save product data to cache."""
    try:
        with open(cache_file_path(asin), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache for {asin}: {e}")

def load_from_cache(asin: str) -> dict | None:
    """Load product data from cache if it exists."""
    path = cache_file_path(asin)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading cache for {asin}: {e}")
    return None

def format_price_display(price: dict | None) -> str:
    """Format price dictionary into a readable string."""
    if price and "DisplayAmount" in price:
        return price["DisplayAmount"]
    return "Price unavailable"

def format_rating_display(rating: float | None, total_reviews: int | None) -> str:
    """Format rating and review count into a readable string."""
    if rating is not None and total_reviews is not None:
        return f"{rating} / 5 ({total_reviews} reviews)"
    return "Rating unavailable"

def get_amazon_product_data(asin: str) -> dict | None:
    """Fetch product data from Amazon API, with caching."""
    # Try cache first
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        product_data = amazon_client.get_items(item_ids=[asin])
        if not product_data or "ItemsResult" not in product_data:
            print(f"No data returned from Amazon for {asin}")
            return None

        # Save to cache
        save_to_cache(asin, product_data)
        return product_data

    except AmazonApiException as e:
        print(f"Amazon API error for {asin}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        return None

def enrich_products_with_amazon_data(products: list[dict]) -> list[dict]:
    """Enrich a list of products with Amazon data based on ASIN."""
    for product in products:
        asin = product.get("asin")
        if not asin:
            continue
        data = get_amazon_product_data(asin)
        if data:
            item = data["ItemsResult"]["Items"][0]
            product["price"] = format_price_display(item.get("Offers", {}).get("Listings", [{}])[0].get("Price"))
            product["rating"] = format_rating_display(
                item.get("CustomerReviews", {}).get("AverageRating"),
                item.get("CustomerReviews", {}).get("TotalReviews")
            )
    return products
