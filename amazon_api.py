import os
import time
from typing import List, Dict, Optional
from amazon_paapi import AmazonApi  # Correct import: AmazonApi (capital A, lowercase i)

# Amazon Product Advertising API Configuration
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY", "")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG", "whoaccepts-21")  # or "AMAZON_PARTNER_TAG" if your env uses that
AMAZON_COUNTRY = "UK"  # Uppercase as per lib docs/examples; lib handles lowercase too

# Rate limiting (global, simple)
LAST_API_CALL = 0
MIN_API_INTERVAL = 1.0  # seconds between calls

def get_amazon_api() -> Optional[AmazonApi]:
    """Initialize Amazon API client if credentials are available."""
    if not AMAZON_ACCESS_KEY or not AMAZON_SECRET_KEY:
        print("Warning: Amazon API credentials not set in environment variables")
        return None
    
    try:
        api = AmazonApi(
            access_key=AMAZON_ACCESS_KEY,
            secret_key=AMAZON_SECRET_KEY,
            associate_tag=AMAZON_ASSOC_TAG,
            country=AMAZON_COUNTRY
        )
        return api
    except Exception as e:
        print(f"Error initializing Amazon API: {e}")
        return None

def fetch_product_info(asin: str, api: Optional[AmazonApi] = None) -> Optional[Dict]:
    """
    Fetch product information from Amazon Product Advertising API.
    
    Args:
        asin: Amazon Standard Identification Number
        api: Optional pre-initialized AmazonApi instance
        
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
        # Fetch product details with specific resources (efficient)
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
        
        if not response or not response.items_result or not response.items_result.items:
            print(f"No data returned for ASIN: {asin}")
            return None
        
        item = response.items_result.items[0]
        result = {}
        
        # Extract price
        try:
            if item.offers and item.offers.listings:
                listing = item.offers.listings[0]
                if listing.price and listing.price.display_amount:
                    result['price'] = listing.price.display_amount
                elif listing.price and listing.price.amount:
                    result['price'] = f"£{float(listing.price.amount):.2f}"
        except Exception as e:
            print(f"Error extracting price for {asin}: {e}")
        
        # Extract rating & reviews
        try:
            if item.customer_reviews:
                if item.customer_reviews.star_rating:
                    result['rating'] = item.customer_reviews.star_rating.value
                if item.customer_reviews.count:
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
        
        # Only fetch if product has ASIN and doesn't already have price
        asin = product.get('asin')
        if asin and 'price' not in product:
            amazon_data = fetch_product_info(asin, api)
            if amazon_data:
                enriched_product.update(amazon_data)
                print(f"Enriched product: {product.get('name', 'Unknown')} with Amazon data")
        
        enriched_products.append(enriched_product)
    
    return enriched_products

def format_price_display(price: Optional[str]) -> str:
    """
    Format price for display.
    """
    if not price:
        return "N/A"
    return price  # Already formatted like "£29.99" from API

def format_rating_display(rating: Optional[str], total_reviews: Optional[int] = None) -> str:
    """
    Format rating for display with stars.
    """
    if not rating:
        return "No rating"
    
    try:
        rating_value = float(rating)
        full_stars = "★" * int(rating_value)
        half_star = "½" if rating_value % 1 >= 0.5 else ""
        empty_stars = "☆" * (5 - int(rating_value) - (1 if half_star else 0))
        stars = full_stars + half_star + empty_stars
        
        if total_reviews:
            return f"{stars} {rating_value:.1f} ({total_reviews:,} reviews)"
        return f"{stars} {rating_value:.1f}"
    except (ValueError, TypeError):
        return "No rating"
