"""
Amazon Product Advertising API Integration
Using python-amazon-paapi (PyPI: python-amazon-paapi >=5.0.0)
Handles fetching product data, caching, batch enrichment, and formatting
"""

import os
from amazon_paapi import AmazonApi
from pathlib import Path
import json
import datetime
from typing import List, Dict, Optional

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_REGION = "uk"  # UK marketplace

# Cache folder (ephemeral on Render)
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_from_cache(asin: str) -> Optional[Dict]:
    cache_file = CACHE_DIR / f"{asin}.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_time_str = data.get("cached_at")
        if cached_time_str:
            cached_time = datetime.datetime.fromisoformat(cached_time_str)
            if datetime.datetime.utcnow() - cached_time < datetime.timedelta(days=1):
                return data
    return None

def save_to_cache(asin: str, product_data: Dict):
    cache_file = CACHE_DIR / f"{asin}.json"
    product_data["cached_at"] = datetime.datetime.utcnow().isoformat()
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(product_data, f, ensure_ascii=False, indent=2)

def get_amazon_product_data(asin: str) -> Optional[Dict]:
    cached = get_from_cache(asin)
    if cached:
        return cached

    if not all([AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG]):
        print(f"Missing Amazon API credentials for ASIN {asin}")
        return None

    try:
        api = AmazonApi(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            associate_tag=AMAZON_ASSOC_TAG,
            country=AMAZON_REGION,
            throttling=2,  # seconds between requests
        )

        response = api.get_items(item_ids=[asin])

        if not response.items_result or not response.items_result.items:
            print(f"No items found for ASIN {asin}")
            return None

        item = response.items_result.items[0]

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

        title = None
        if item.item_info and item.item_info.title:
            title = item.item_info.title.display_value

        product_data = {
            "asin": asin,
            "title": title,
            "url": item.detail_page_url,
            "price": price,
            "rating": rating,
            "total_reviews": total_reviews,
            "image_url": image_url,
        }

        save_to_cache(asin, product_data)
        return product_data

    except Exception as e:
        print(f"Amazon API error for ASIN {asin}: {type(e).__name__} - {str(e)}")
        return None

def enrich_products_with_amazon_data(products: List[Dict]) -> List[Dict]:
    """
    Enrich a list of product dicts with Amazon data.
    Each product must have an 'asin' key.
    Returns the enriched list (original dicts updated in-place + returns it).
    """
    enriched = []
    asin_to_product = {}

    # Collect ASINs and map back to original products
    asins = []
    for product in products:
        asin = product.get("asin")
        if asin:
            asins.append(asin)
            asin_to_product[asin] = product

    if not asins:
        return products  # Nothing to enrich

    # Batch fetch (library supports up to 10 per call)
    batch_size = 10
    for i in range(0, len(asins), batch_size):
        batch_asins = asins[i:i + batch_size]
        try:
            api = AmazonApi(
                access_key=AMAZON_ACCESS_KEY,
                secret_key=AMAZON_SECRET_KEY,
                associate_tag=AMAZON_ASSOC_TAG,
                country=AMAZON_REGION,
                throttling=2,
            )
            response = api.get_items(item_ids=batch_asins)

            if response.items_result and response.items_result.items:
                for item in response.items_result.items:
                    asin = item.asin  # or item.asin if available; fallback to input order if needed
                    amazon_data = get_amazon_product_data(asin)  # Reuse single fetch + cache
                    if amazon_data:
                        original_product = asin_to_product.get(asin, {})
                        original_product.update(amazon_data)
                        enriched.append(original_product)
        except Exception as e:
            print(f"Batch enrichment error for ASINs {batch_asins}: {type(e).__name__} - {str(e)}")

    # Add back any products without ASIN or failed enrichment
    for product in products:
        if product.get("asin") not in asin_to_product:
            enriched.append(product)

    return enriched

# Formatting helpers
def format_price_display(price: Optional[str]) -> str:
    return price or "N/A"

def format_rating_display(rating: Optional[float], total_reviews: Optional[int]) -> str:
    if rating is not None and total_reviews is not None:
        return f"{rating:.1f} ⭐ ({total_reviews})"
    return "No reviews"
