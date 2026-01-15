"""
Amazon Product Advertising API Integration
Using amazon-paapi (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import json
import time
import datetime
from pathlib import Path

from amazon_paapi import AmazonApi  # Removed AmazonApiException

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOCIATE_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG", "whoaccepts-21")

# Cache directory
CACHE_DIR = Path("data/amazon_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Rate limiting
LAST_REQUEST_TIME = 0
MIN_REQUEST_INTERVAL = 1.0  # 1 request/sec


def get_amazon_product_data(asin: str) -> dict | None:
    """
    Fetch product data from Amazon PA-API or cache.
    """
    if not AMAZON_ACCESS_KEY or not AMAZON_SECRET_KEY:
        print("⚠️  Amazon API credentials not set.")
        return None

    # Check cache
    cached = get_cached_data(asin)
    if cached:
        return cached

    # Rate limiting
    global LAST_REQUEST_TIME
    delta = time.time() - LAST_REQUEST_TIME
    if delta < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - delta)

    try:
        api = AmazonApi(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            associate_tag=AMAZON_ASSOCIATE_TAG,
            country="UK"
        )

        items = api.get_items([asin])
        LAST_REQUEST_TIME = time.time()

        if not items or asin not in items:
            print(f"No data returned for ASIN {asin}")
            return None

        item = items[asin]

        product_data = {
            "asin": asin,
            "title": item.title,
            "price": item.price_and_currency[0] if item.price_and_currency else None,
            "list_price": item.list_price_and_currency[0] if item.list_price_and_currency else None,
            "savings_amount": item.savings_and_currency[0] if item.savings_and_currency else None,
            "savings_percent": item.savings_percent,
            "rating": item.rating,
            "review_count": item.review_count,
            "image_url": item.images[0] if item.images else None,
            "last_updated": datetime.datetime.now().isoformat()
        }

        save_to_cache(asin, product_data)
        return product_data

    except Exception as e:
        print(f"Amazon API error for {asin}: {e}")
        return None


def get_cached_data(asin: str) -> dict | None:
    cache_file = CACHE_DIR / f"{asin}.json"
    if not cache_file.exists():
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        last_updated = datetime.datetime.fromisoformat(data["last_updated"])
        age_hours = (datetime.datetime.now() - last_updated).total_seconds() / 3600
        if age_hours < 24:
            return data
    except Exception as e:
        print(f"Error reading cache for {asin}: {e}")
    return None


def save_to_cache(asin: str, data: dict):
    cache_file = CACHE_DIR / f"{asin}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving cache for {asin}: {e}")


def enrich_products_with_amazon_data(products: list[dict]) -> list[dict]:
    """
    Adds Amazon pricing and rating info to your products without overwriting
    your site's own content (name, image, info, etc.).
    """
    enriched = []
    for product in products:
        # Skip products without ASIN
        if not product.get("asin"):
            enriched.append(product)
            continue

        amazon_data = get_amazon_product_data(product["asin"])

        if amazon_data:
            # Only append Amazon-specific fields
            amazon_fields = {
                "amazon_price": amazon_data.get("price"),
                "amazon_list_price": amazon_data.get("list_price"),
                "amazon_savings": amazon_data.get("savings_amount"),
                "amazon_savings_percent": amazon_data.get("savings_percent"),
                "amazon_rating": amazon_data.get("rating"),
                "amazon_reviews": amazon_data.get("review_count"),
                "price_last_updated": amazon_data.get("last_updated")
            }

            # Merge with your product without overwriting your existing keys
            enriched_product = dict(product)
            enriched_product.update(amazon_fields)
            enriched.append(enriched_product)
        else:
            enriched.append(product)

    return enriched



def format_price_display(product: dict) -> dict:
    display = {
        "has_price": False,
        "current_price": None,
        "was_price": None,
        "savings": None,
        "savings_percent": None,
        "last_updated": None
    }
    if product.get("amazon_price"):
        display["has_price"] = True
        display["current_price"] = product.get("amazon_price")
        display["was_price"] = product.get("amazon_list_price")
        display["savings"] = product.get("amazon_savings")
        display["savings_percent"] = product.get("amazon_savings_percent")
        if product.get("price_last_updated"):
            try:
                dt = datetime.datetime.fromisoformat(product["price_last_updated"])
                display["last_updated"] = dt.strftime("%d %b %Y, %H:%M")
            except:
                pass
    return display


def format_rating_display(product: dict) -> dict:
    display = {
        "has_rating": False,
        "rating": None,
        "stars_full": 0,
        "stars_half": False,
        "stars_empty": 5,
        "review_count": None,
        "review_count_formatted": None
    }
    rating = product.get("amazon_rating")
    if rating:
        display["has_rating"] = True
        try:
            rating = float(rating)
            display["rating"] = rating
            display["stars_full"] = int(rating)
            display["stars_half"] = (rating % 1) >= 0.5
            display["stars_empty"] = 5 - display["stars_full"] - (1 if display["stars_half"] else 0)
        except:
            pass
    reviews = product.get("amazon_reviews")
    if reviews:
        try:
            count = int(reviews)
            display["review_count"] = count
            display["review_count_formatted"] = f"{count/1000:.1f}K" if count >= 1000 else f"{count:,}"
        except:
            display["review_count_formatted"] = str(reviews)
    return display





if __name__ == "__main__":
    test_api()
