"""
helpers.py
──────────
Pure utility functions. No Flask, no AI, no file I/O.
Safe to import anywhere without side effects.
"""

import re
import json
import os

ITEMS_PER_PAGE = 12


# ── Text helpers ─────────────────────────────────────────────────────────────

def slugify(text):
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text


def normalize_for_match(text):
    if not text:
        return ""
    return text.lower().replace("'", "").replace(" ", "").replace("-", "")


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


# ── Pagination ───────────────────────────────────────────────────────────────

def paginate(items, page, per_page=ITEMS_PER_PAGE):
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], len(items)


# ── Navigation ───────────────────────────────────────────────────────────────

def get_nav_items(cache_file, products_fallback):
    """
    Build the categories + seasons lists for the nav dropdowns.
    Reads from cache if available, otherwise uses products_fallback.
    """
    products = products_fallback
    if os.path.exists(cache_file):
        try:
            with open(cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)
            products = cache_data.get("products", products_fallback)
        except Exception:
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
        "Summer Gifts", "Back to School", "Halloween", "Christmas",
    ]
    important_seasons = [s for s in important_seasons_order if s in seasons_set]
    other_seasons = sorted(seasons_set - set(important_seasons))
    seasons = other_seasons + important_seasons

    return {"categories": categories, "seasons": seasons}


# ── Price / rating formatting ─────────────────────────────────────────────────

def get_product_price_rating(product):
    """Return price, rating and reviews from manual override fields."""
    return {
        "price":   product.get("manual_price")   or None,
        "rating":  product.get("manual_rating")  or None,
        "reviews": product.get("manual_reviews") or None,
    }


def format_price_display(price_data):
    if isinstance(price_data, str):
        return price_data
    if isinstance(price_data, dict):
        return f"£{price_data['amount']:.2f}"
    return str(price_data) if price_data else ""


def format_rating_display(rating, review_count=None):
    if not rating:
        return ""
    try:
        rating_float = float(rating)
        stars = "⭐" * int(rating_float)
        half_star = "½⭐" if (rating_float % 1) >= 0.5 else ""
        if review_count:
            formatted_count = (
                review_count if isinstance(review_count, str)
                else f"{review_count:,}"
            )
            return f"{stars}{half_star} {rating_float}/5 ({formatted_count} reviews)"
        return f"{stars}{half_star} {rating_float}/5"
    except Exception:
        return ""


# ── Product similarity ────────────────────────────────────────────────────────

def get_similar_products(product, all_products, limit=6):
    similar = []

    category_matches = [
        p for p in all_products
        if p.get("category") == product.get("category")
        and p["name"] != product["name"]
    ]
    similar.extend(category_matches[:limit])

    if len(similar) < limit:
        product_seasons = set(
            s.strip() for s in product.get("season", "").split(",") if s.strip()
        )
        season_matches = [
            p for p in all_products
            if p["name"] != product["name"]
            and p not in similar
            and any(
                s.strip() in product_seasons
                for s in p.get("season", "").split(",")
            )
        ]
        similar.extend(season_matches[: (limit - len(similar))])

    return similar[:limit]
