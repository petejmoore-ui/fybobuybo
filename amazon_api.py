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

# Amazon API credentials from environment variables
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_PARTNER_TAG = os.environ.get("AMAZON_PARTNER_TAG")
AMAZON_MARKETPLACE = "www.amazon.co.uk"  # UK marketplace

# Cache folder
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def load_from_cache(asin: str) -> dict | None:
    cache_file = CACHE_DIR / f"{asin}.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_to_cache(asin: str, data: dict) -> None:
    cache_file = CACHE_DIR / f"{asin}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_price_display(price: dict) -> str:
    if not price or "Amount" not in price or "Currency" not in price:
        return "N/A"
    return f"{price['Amount']} {price['Currency']}"


def format_rating_display(rating: dict) -> str:
    if not rating or "Value" not in rating or "TotalReviews" not in rating:
        return "N/A"
    return f"{rating['Value']} / 5 ({rating['TotalReviews']} reviews)"


def enrich_products_with_amazon_data(asin: str) -> dict | None:
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        amazon = AmazonApi(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            partner_tag=AMAZON_PARTNER_TAG,
            marketplace=AMAZON_MARKETPLACE,
        )

        response = amazon.get_items([asin])
        if not response or not response.get("ItemsResult", {}).get("Items"):
            return None

        item = response["ItemsResult"]["Items"][0]

        product_data = {
            "asin": asin,
            "title": item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue"),
            "price": format_price_display(
                item.get("Offers", {}).get("Listings", [{}])[0].get("Price")
            ),
            "rating": format_rating_display(item.get("CustomerReviews")),
            "url": item.get("DetailPageURL"),
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
