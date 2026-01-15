"""
Amazon Product Advertising API Integration
100% Compliant with Amazon Associates Terms of Service

This module handles:
- Fetching product prices, ratings, reviews from Amazon PA-API
- 24-hour caching (required by Amazon ToS)
- Error handling and fallbacks
- Rate limiting (1 request/second)
"""

import os
import json
import time
import datetime
from pathlib import Path

# Install with: pip install paapi5-python-sdk --break-system-packages
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.get_items_request import GetItemsRequest
from paapi5_python_sdk.get_items_resource import GetItemsResource
from paapi5_python_sdk.partner_type import PartnerType
from paapi5_python_sdk.rest import ApiException

# Amazon API Credentials (from environment variables)
AMAZON_ACCESS_KEY = os.environ.get('AMAZON_ACCESS_KEY')
AMAZON_SECRET_KEY = os.environ.get('AMAZON_SECRET_KEY')
AMAZON_ASSOCIATE_TAG = os.environ.get('AMAZON_ASSOCIATE_TAG', 'whoaccepts-21')

# Cache directory
CACHE_DIR = Path("data/amazon_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Rate limiting
LAST_REQUEST_TIME = 0
MIN_REQUEST_INTERVAL = 1.0  # 1 second between requests


def get_amazon_product_data(asin):
    """
    Fetch product data from Amazon PA-API or cache
    
    Args:
        asin (str): Amazon ASIN (e.g., 'B08XYZ123')
    
    Returns:
        dict: Product data with price, rating, reviews, etc.
        None: If API call fails or ASIN invalid
    """
    
    # Check if we have valid credentials
    if not AMAZON_ACCESS_KEY or not AMAZON_SECRET_KEY:
        print("⚠️  Amazon API credentials not found. Set AMAZON_ACCESS_KEY and AMAZON_SECRET_KEY in .env")
        return None
    
    # Try to get from cache first
    cached_data = get_cached_data(asin)
    if cached_data:
        return cached_data
    
    # Rate limiting - wait if needed
    global LAST_REQUEST_TIME
    time_since_last = time.time() - LAST_REQUEST_TIME
    if time_since_last < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - time_since_last)
    
    # Create API client
    api = DefaultApi(
        access_key=AMAZON_ACCESS_KEY,
        secret_key=AMAZON_SECRET_KEY,
        host='webservices.amazon.co.uk',
        region='eu-west-1'
    )
    
    # Define what data to fetch
    resources = [
        GetItemsResource.ITEMINFO_TITLE,
        GetItemsResource.OFFERS_LISTINGS_PRICE,
        GetItemsResource.OFFERS_LISTINGS_SAVINGBASIS,
        GetItemsResource.IMAGES_PRIMARY_LARGE,
        GetItemsResource.CUSTOMERREVIEWS_STARRATING,
        GetItemsResource.CUSTOMERREVIEWS_COUNT,
    ]
    
    try:
        # Make API request
        request = GetItemsRequest(
            partner_tag=AMAZON_ASSOCIATE_TAG,
            partner_type=PartnerType.ASSOCIATES,
            marketplace='www.amazon.co.uk',
            item_ids=[asin],
            resources=resources
        )
        
        response = api.get_items(request)
        LAST_REQUEST_TIME = time.time()
        
        # Parse response
        if response.items_result and response.items_result.items:
            item = response.items_result.items[0]
            
            # Extract data
            product_data = {
                'asin': asin,
                'title': item.item_info.title.display_value if item.item_info and item.item_info.title else None,
                'price': None,
                'list_price': None,
                'savings_amount': None,
                'savings_percent': None,
                'rating': None,
                'review_count': None,
                'image_url': None,
                'last_updated': datetime.datetime.now().isoformat()
            }
            
            # Extract price info
            if item.offers and item.offers.listings and len(item.offers.listings) > 0:
                listing = item.offers.listings[0]
                
                if listing.price:
                    product_data['price'] = listing.price.display_amount
                
                if listing.price and listing.price.savings:
                    if listing.price.savings.display_amount:
                        product_data['savings_amount'] = listing.price.savings.display_amount
                    if listing.price.savings.percentage:
                        product_data['savings_percent'] = listing.price.savings.percentage
                
                # Get list price (RRP) if available
                if hasattr(listing, 'saving_basis') and listing.saving_basis:
                    if hasattr(listing.saving_basis, 'display_amount'):
                        product_data['list_price'] = listing.saving_basis.display_amount
            
            # Extract review data
            if item.customer_reviews:
                if item.customer_reviews.star_rating:
                    product_data['rating'] = item.customer_reviews.star_rating.value
                if item.customer_reviews.count:
                    product_data['review_count'] = item.customer_reviews.count
            
            # Extract image
            if item.images and item.images.primary and item.images.primary.large:
                product_data['image_url'] = item.images.primary.large.url
            
            # Cache the data
            save_to_cache(asin, product_data)
            
            return product_data
        
        else:
            print(f"No data returned for ASIN: {asin}")
            return None
            
    except ApiException as e:
        print(f"Amazon API Error for {asin}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {asin}: {e}")
        return None


def get_cached_data(asin):
    """
    Get product data from cache if it exists and is fresh (< 24 hours)
    """
    cache_file = CACHE_DIR / f"{asin}.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if cache is fresh (< 24 hours old)
        last_updated = datetime.datetime.fromisoformat(data['last_updated'])
        age_hours = (datetime.datetime.now() - last_updated).total_seconds() / 3600
        
        if age_hours < 24:
            return data
        else:
            # Cache expired
            return None
            
    except Exception as e:
        print(f"Error reading cache for {asin}: {e}")
        return None


def save_to_cache(asin, data):
    """
    Save product data to cache
    """
    cache_file = CACHE_DIR / f"{asin}.json"
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving cache for {asin}: {e}")


def enrich_products_with_amazon_data(products):
    """
    Enrich a list of products with Amazon PA-API data
    
    Args:
        products (list): List of product dicts with 'asin' field
    
    Returns:
        list: Products enriched with Amazon data
    """
    enriched = []
    
    for product in products:
        # Skip if no ASIN
        if 'asin' not in product or not product['asin']:
            enriched.append(product)
            continue
        
        # Get Amazon data
        amazon_data = get_amazon_product_data(product['asin'])
        
        # Merge with product
        if amazon_data:
            product_copy = dict(product)
            product_copy['amazon_price'] = amazon_data.get('price')
            product_copy['amazon_list_price'] = amazon_data.get('list_price')
            product_copy['amazon_savings'] = amazon_data.get('savings_amount')
            product_copy['amazon_savings_percent'] = amazon_data.get('savings_percent')
            product_copy['amazon_rating'] = amazon_data.get('rating')
            product_copy['amazon_reviews'] = amazon_data.get('review_count')
            product_copy['price_last_updated'] = amazon_data.get('last_updated')
            enriched.append(product_copy)
        else:
            enriched.append(product)
    
    return enriched


def batch_enrich_products(products, batch_size=10):
    """
    Enrich products in batches to avoid rate limits
    """
    enriched = []
    
    for i in range(0, len(products), batch_size):
        batch = products[i:i+batch_size]
        enriched_batch = enrich_products_with_amazon_data(batch)
        enriched.extend(enriched_batch)
        
        # Brief pause between batches
        if i + batch_size < len(products):
            time.sleep(2)
    
    return enriched


def format_price_display(product):
    """
    Format price display for templates
    Returns a dict with display-ready price info
    """
    display = {
        'has_price': False,
        'current_price': None,
        'was_price': None,
        'savings': None,
        'savings_percent': None,
        'last_updated': None
    }
    
    if 'amazon_price' in product and product['amazon_price']:
        display['has_price'] = True
        display['current_price'] = product['amazon_price']
        
        if 'amazon_list_price' in product and product['amazon_list_price']:
            display['was_price'] = product['amazon_list_price']
        
        if 'amazon_savings' in product and product['amazon_savings']:
            display['savings'] = product['amazon_savings']
        
        if 'amazon_savings_percent' in product and product['amazon_savings_percent']:
            display['savings_percent'] = product['amazon_savings_percent']
        
        if 'price_last_updated' in product:
            try:
                updated = datetime.datetime.fromisoformat(product['price_last_updated'])
                display['last_updated'] = updated.strftime('%d %b %Y, %H:%M')
            except:
                pass
    
    return display


def format_rating_display(product):
    """
    Format rating display for templates
    """
    display = {
        'has_rating': False,
        'rating': None,
        'stars_full': 0,
        'stars_half': False,
        'stars_empty': 0,
        'review_count': None,
        'review_count_formatted': None
    }
    
    if 'amazon_rating' in product and product['amazon_rating']:
        display['has_rating'] = True
        
        try:
            rating = float(product['amazon_rating'])
            display['rating'] = rating
            display['stars_full'] = int(rating)
            display['stars_half'] = (rating % 1) >= 0.5
            display['stars_empty'] = 5 - display['stars_full'] - (1 if display['stars_half'] else 0)
        except:
            pass
    
    if 'amazon_reviews' in product and product['amazon_reviews']:
        count = product['amazon_reviews']
        display['review_count'] = count
        
        # Format like "1,234 reviews" or "12.3K reviews"
        try:
            count_int = int(count)
            if count_int >= 1000:
                display['review_count_formatted'] = f"{count_int/1000:.1f}K"
            else:
                display['review_count_formatted'] = f"{count_int:,}"
        except:
            display['review_count_formatted'] = str(count)
    
    return display


# Test function
def test_api():
    """
    Test the API with a sample ASIN
    """
    print("Testing Amazon PA-API integration...")
    print(f"Access Key: {AMAZON_ACCESS_KEY[:10]}..." if AMAZON_ACCESS_KEY else "Access Key: NOT SET")
    print(f"Partner Tag: {AMAZON_ASSOCIATE_TAG}")
    
    # Test with a known ASIN (you can change this)
    test_asin = "B08XYZ123"  # Replace with a real ASIN
    
    print(f"\nFetching data for ASIN: {test_asin}")
    data = get_amazon_product_data(test_asin)
    
    if data:
        print("\n✅ Success! Retrieved data:")
        print(json.dumps(data, indent=2))
    else:
        print("\n❌ Failed to retrieve data")
        print("Check your API credentials and ASIN")


if __name__ == "__main__":
    test_api()
