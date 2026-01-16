import os
import time
from typing import List, Dict, Optional
from amazon.paapi import AmazonAPI

# Amazon Product Advertising API Configuration
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY", "")
AMAZON_PARTNER_TAG = os.environ.get("AMAZON_PARTNER_TAG", "whoaccepts-21")
AMAZON_COUNTRY = "UK"

# Rate limiting
LAST_API_CALL = 0
MIN_API_INTERVAL = 1.0  # 1 second between calls to respect API limits

def get_amazon_api():
    """Initialize Amazon API client if credentials are available."""
    if not AMAZON_ACCESS_KEY or not AMAZON_SECRET_KEY:
        print("Warning: Amazon API credentials not set in environment variables")
        return None
    
    try:
        api = AmazonAPI(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            partner_tag=AMAZON_PARTNER_TAG,
            country=AMAZON_COUNTRY
        )
        return api
    except Exception as e:
        print(f"Error initializing Amazon API: {e}")
        return None

def fetch_product_info(asin: str, api: Optional[AmazonAPI] = None) -> Optional[Dict]:
    """
    Fetch product information from Amazon Product Advertising API.
    
    Args:
        asin: Amazon Standard Identification Number
        api: Optional pre-initialized AmazonAPI instance
        
    Returns:
        Dictionary with price and rating information, or None if unavailable
    """
    global LAST_API_CALL
    
    if not asin:
        return None
    
    # Initialize API if not provided
    if api is None:
        api = get_amazon_api()
    
    if api is None:
        return None
    
    # Rate limiting
    current_time = time.time()
    time_since_last_call = current_time - LAST_API_CALL
    if time_since_last_call < MIN_API_INTERVAL:
        time.sleep(MIN_API_INTERVAL - time_since_last_call)
    
    try:
        # Fetch product details
        response = api.get_items(
            item_ids=[asin],
            resources=[
                "ItemInfo.Title",
                "Offers.Listings.Price",
                "CustomerReviews.StarRating",
                "CustomerReviews.Count"
            ]
        )
        
        LAST_API_CALL = time.time()
        
        if not response or not response.items:
            print(f"No data returned for ASIN: {asin}")
            return None
        
        item = response.items[0]
        result = {}
        
        # Extract price
        try:
            if hasattr(item, 'offers') and item.offers and item.offers.listings:
                listing = item.offers.listings[0]
                if hasattr(listing, 'price') and listing.price:
                    if hasattr(listing.price, 'display_amount'):
                        result['price'] = listing.price.display_amount
                    elif hasattr(listing.price, 'amount'):
                        result['price'] = f"£{listing.price.amount:.2f}"
        except Exception as e:
            print(f"Error extracting price for {asin}: {e}")
        
        # Extract rating
        try:
            if hasattr(item, 'customer_reviews') and item.customer_reviews:
                if hasattr(item.customer_reviews, 'star_rating'):
                    result['rating'] = item.customer_reviews.star_rating.value
                if hasattr(item.customer_reviews, 'count'):
                    result['total_reviews'] = item.customer_reviews.count
        except Exception as e:
            print(f"Error extracting rating for {asin}: {e}")
        
        return result if result else None
        
    except Exception as e:
        print(f"Error fetching Amazon data for ASIN {asin}: {e}")
        LAST_API_CALL = time.time()
        return None

def enrich_products_with_amazon_data(products: List[Dict]) -> List[Dict]:
    """
    Enrich product list with Amazon API data.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        List of products enriched with Amazon data
    """
    api = get_amazon_api()
    
    if api is None:
        print("Amazon API not available - skipping enrichment")
        return products
    
    enriched_products = []
    
    for product in products:
        enriched_product = product.copy()
        
        # Only fetch if product has ASIN and doesn't already have fresh data
        asin = product.get('asin')
        if asin and not product.get('price'):
            amazon_data = fetch_product_info(asin, api)
            if amazon_data:
                enriched_product.update(amazon_data)
                print(f"Enriched product: {product.get('name', 'Unknown')} with Amazon data")
        
        enriched_products.append(enriched_product)
    
    return enriched_products

def format_price_display(price: Optional[str]) -> str:
    """
    Format price for display.
    
    Args:
        price: Price string from Amazon API
        
    Returns:
        Formatted price string
    """
    if not price:
        return ""
    
    # Price is already formatted from API (e.g., "£29.99")
    return price

def format_rating_display(rating: Optional[str], total_reviews: Optional[int] = None) -> str:
    """
    Format rating for display.
    
    Args:
        rating: Rating value (e.g., "4.5")
        total_reviews: Optional number of reviews
        
    Returns:
        Formatted rating string with stars
    """
    if not rating:
        return ""
    
    try:
        rating_value = float(rating)
        stars = "★" * int(rating_value) + "☆" * (5 - int(rating_value))
        
        if total_reviews:
            return f"{stars} {rating_value}/5 ({total_reviews:,} reviews)"
        else:
            return f"{stars} {rating_value}/5"
    except (ValueError, TypeError):
        return ""
