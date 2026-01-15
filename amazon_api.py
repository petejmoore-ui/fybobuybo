"""
Amazon Product Advertising API Integration
Using python-amazon-paapi (PyPI)
Handles fetching product data, caching, and formatting
"""

import os
import datetime
from pathlib import Path

from amazon_paapi import AmazonApi, AmazonApiException

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
AMAZON_REGION = os.environ.get("AMAZON_REGION", "co.uk")  # default to UK

# Initialize Amazon API client
amazon_api = AmazonApi(
    access_key=AMAZON_ACCESS_KEY,
    secret_key=AMAZON_SECRET_KEY,
    partner_tag=AMAZON_ASSOC_TAG,
    country=AMAZON_REGION
)

# Cache folder
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

def cache_file_path(asin: str) -> Path:
    return CACHE_DIR / f"{asin}.json"

def save_to_cache(asin: str, data: dict):
    path = cache_file_path(asin)
    path.write_text(str(data))

def load_from_cache(asin: str) -> dict | None:
    path = cache_file_path(asin)
    if path.exists():
        return eval(path.read_text())
    return None

def get_amazon_product_data(asin: str) -> dict | None:
    # Try cache first
    cached = load_from_cache(asin)
    if cached:
        return cached

    try:
        product_data = amazon_api.get_items([asin])
        save_to_cache(asin, product_data)
        return product_data
    except AmazonApiException as e:
        print(f"Amazon API error for {asin}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        return None
