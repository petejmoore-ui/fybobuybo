# ============================================================================
# ELITE HELPER FUNCTIONS - NEW!
# ============================================================================

def get_product_price_rating(product):
    """Extract price and rating with manual override support"""
    price = product.get("manual_price") or None
    rating = product.get("manual_rating") or None
    reviews = product.get("manual_reviews") or None
    
    return {
        "price": price,
        "rating": rating,
        "reviews": reviews
    }

def format_price_display(price_data):
    """Format price for display - handles both manual and API prices"""
    if isinstance(price_data, str):
        return price_data  # Already formatted (e.g., "£16.95")
    if isinstance(price_data, dict):
        return f"£{price_data['amount']:.2f}"
    return str(price_data) if price_data else ""

def format_rating_display(rating, review_count=None):
    """Format rating with stars for display"""
    if not rating:
        return ""
    try:
        rating_float = float(rating)
        stars = "⭐" * int(rating_float)
        half_star = "½⭐" if (rating_float % 1) >= 0.5 else ""
        
        if review_count:
            if isinstance(review_count, str):
                formatted_count = review_count
            else:
                formatted_count = f"{review_count:,}"
            return f"{stars}{half_star} {rating_float}/5 ({formatted_count} reviews)"
        return f"{stars}{half_star} {rating_float}/5"
    except:
        return ""

def get_similar_products(product, all_products, limit=6):
    """Get similar products for SEO and user engagement"""
    similar = []
    
    # Same category
    category_matches = [
        p for p in all_products 
        if p.get("category") == product.get("category") 
        and p["name"] != product["name"]
    ]
    similar.extend(category_matches[:limit])
    
    if len(similar) < limit:
        # Add same season products
        product_seasons = set(s.strip() for s in product.get("season", "").split(",") if s.strip())
        season_matches = [
            p for p in all_products
            if p["name"] != product["name"]
            and p not in similar
            and any(s.strip() in product_seasons for s in p.get("season", "").split(","))
        ]
        similar.extend(season_matches[:(limit - len(similar))])
    
    return similar[:limit]



def generate_product_schema(product):
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product["name"],
        "description": (product.get("info") or product.get("hook") or "")[:200],
        "image": product.get("image", ""),
        "sku": product.get("asin", "")
    }

    return json.dumps(schema, ensure_ascii=False)

def generate_breadcrumb_schema(breadcrumbs):
    """Generate breadcrumb schema for navigation"""
    items = []
    
    for idx, (name, url) in enumerate(breadcrumbs, 1):
        # Ensure the URL is full (no double 'https://example.com' in the URL)
        if not url.startswith('http'):
            url = SITE_URL + url  # Prepend SITE_URL if the URL is relative

        items.append({
            "@type": "ListItem",
            "position": idx,
            "name": name,
            "item": url
        })
    
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items
    }
    
    return json.dumps(schema, ensure_ascii=False)



# ============================================================================
# EXISTING HELPER FUNCTIONS
# ============================================================================

def ping_search_engines():
    sitemap_url = f"{SITE_URL}/sitemap.xml"
    engines = [
        f"https://www.google.com/ping?sitemap={sitemap_url}",
        f"https://www.bing.com/ping?sitemap={sitemap_url}"
    ]
    for url in engines:
        try:
            requests.get(url, timeout=5)
        except Exception:
            pass

def slugify(text):
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    text = re.sub(r'-+', '-', text)  # Collapse multiple hyphens to single hyphen
    text = text.strip('-')  # Remove leading/trailing hyphens
    return text

def normalize_for_match(text):
    if not text:
        return ""
    return text.lower().replace("'", "").replace(" ", "").replace("-", "")

def get_nav_items():
    products = PRODUCTS
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)
            products = cache_data.get("products", PRODUCTS)
        except:
            pass

    categories = sorted({p["category"] for p in products if p.get("category")})

    seasons_set = set()
    for p in products:
        if p.get("season"):
            for s in p["season"].split(","):
                clean = s.strip()
                if clean:
                    seasons_set.add(clean)

    important_seasons_order = [
        "Valentine's Day", "Mother's Day", "Easter", "Father's Day",
        "Summer Gifts", "Back to School", "Halloween", "Christmas"
    ]
    important_seasons = [s for s in important_seasons_order if s in seasons_set]
    other_seasons = sorted(seasons_set - set(important_seasons))
    seasons = other_seasons + important_seasons

    return {
        "categories": categories,
        "seasons": seasons
    }

def paginate(items, page):
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return items[start:end], len(items)

def shorten_product_name(name, max_length=80):
    if len(name) <= max_length:
        return name
    for sep in [',', '(']:
        if sep in name:
            short = name.split(sep, 1)[0].strip()
            if len(short) <= max_length:
                return short
    words, out = name.split(), ""
    for w in words:
        if len(out + " " + w) <= max_length - 3:
            out += (" " if out else "") + w
        else:
            break
    return out + "..."
