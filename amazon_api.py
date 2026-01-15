"""
Amazon Product Advertising API Integration
Using python-amazon-paapi (PyPI)
Using amazon-paapi (PyPI)
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
AMAZON_REGION = os.environ.get("AMAZON_REGION", "US")


def get_amazon_product_data(asin: str) -> dict | None:
    try:
        amazon = AmazonApi(
            AMAZON_ACCESS_KEY,
            AMAZON_SECRET_KEY,
            AMAZON_ASSOC_TAG,
            AMAZON_REGION,
        )

        product_data = amazon.get_items(asin)

        save_to_cache(asin, product_data)
        return product_data

    except AmazonApiException as e:
        print(f"Amazon API error for {asin}: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        return None


