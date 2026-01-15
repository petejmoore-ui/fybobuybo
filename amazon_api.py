"""
Amazon Product Advertising API Integration
Using python-amazon-paapi (PyPI)
Using amazon-paapi (PyPI)
Handles fetching product data, caching, and formatting
"""

@@ -10,7 +10,7 @@
import datetime
from pathlib import Path

from amazon_paapi import AmazonApi, AmazonApiException
from amazon_paapi import AmazonApi  # Removed AmazonApiException

# Amazon API Credentials from environment
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
@@ -78,11 +78,8 @@ def get_amazon_product_data(asin: str) -> dict | None:
save_to_cache(asin, product_data)
return product_data

    except AmazonApiException as e:
        print(f"Amazon API error for {asin}: {e}")
        return None
except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        print(f"Amazon API error for {asin}: {e}")
return None

