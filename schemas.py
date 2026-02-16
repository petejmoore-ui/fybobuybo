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
