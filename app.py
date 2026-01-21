import os
import json
import re
import datetime
import random
from threading import Thread
from products_data import PRODUCTS
from blog_data import BLOG_POSTS

from flask import Flask, render_template_string, request, url_for, abort, Response
from groq import Groq
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# --- Staging SEO safeguard ---
if os.environ.get("STAGING") == "true":
    @app.after_request
    def add_header(response):
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        return response

CACHE_FILE = "data/cache.json"
HISTORY_FILE = "data/history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = "https://www.fybobuybo.com"
ITEMS_PER_PAGE = 12

CACHE_REFRESH_DAYS = 10
PROMPT_VERSION = "v3.0-elite-2026"

os.makedirs("data", exist_ok=True)

# ============================================================================
# THEMES
# ============================================================================
THEMES = [
    {
        "name": "Daylight Elegance",
        "bg": "#fdfbf7",
        "card": "#ffffff",
        "accent": "#1a1614",
        "button": "#0066ff",
        "button_hover": "#0052cc",
        "tag": "#e8f4ff",
        "text_accent": "#2c2c2c",
        "text_muted": "#666666",
        "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "card_gradient": "linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)",
        "shadow": "0 4px 12px rgba(0, 0, 0, 0.08)",
        "shadow_hover": "0 8px 24px rgba(0, 0, 0, 0.12)",
        "dropdown_bg": "#ffffff",
        "dropdown_border": "rgba(0, 0, 0, 0.12)",
        "nav_bg": "#ffffff",
        "nav_border": "rgba(0, 0, 0, 0.08)"
    },
    {
        "name": "Midnight Luxe",
        "bg": "#0a0e14",
        "card": "#151922",
        "accent": "#f5f5f0",
        "button": "#4d7fff",
        "button_hover": "#6d93ff",
        "tag": "#1e2838",
        "text_accent": "#e0e0e0",
        "text_muted": "#a0a0a0",
        "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "card_gradient": "linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)",
        "shadow": "0 4px 12px rgba(0, 0, 0, 0.4)",
        "shadow_hover": "0 8px 24px rgba(0, 0, 0, 0.6)",
        "dropdown_bg": "#1a1f2e",
        "dropdown_border": "rgba(255, 255, 255, 0.12)",
        "nav_bg": "#151922",
        "nav_border": "rgba(255, 255, 255, 0.08)"
    }
]

def get_daily_theme():
    return THEMES[datetime.date.today().timetuple().tm_yday % len(THEMES)]

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

HOOK_STYLES = ["benefit-first", "lifestyle-story", "quality-craft", "quiet-genius"]

def generate_hook(product):
    if "hook_override" in product and product["hook_override"].strip():
        return product["hook_override"].strip()

    name = product["name"]
    category = product.get("category", "")
    keywords = product.get("keywords", [])
    pain_points = product.get("pain_points", [])
    price_tier = product.get("price_tier", "")

    style = random.choice(HOOK_STYLES)

    prompt = f"""
You are a sophisticated British copywriter creating calm, elegant 1–2 sentence product highlights 
loved by UK shoppers in 2026.

Core rules:
- Maximum 2 sentences, very concise yet evocative
- Focus purely on practical benefits, real daily value, quality or subtle lifestyle improvement
- Never use these words: staple, essential, go-to, must-have, iconic, game-changer
- Use <b> tags subtly around 1–2 truly standout features only
- Sound understated, refined, trustworthy — quiet confidence, not hype
- Naturally weave in UK context (weather, homes, seasons, value mindset) where organic

Style to use exactly: {style}
Extra context if relevant:
Category: {category}
Price feel: {price_tier}
Common UK context: {', '.join(pain_points) if pain_points else 'everyday practicality and lasting value'}
Target phrases (subtle): {', '.join(keywords) if keywords else 'none'}

Product: {name}

Output only the 1–2 sentences. End with a complete sentence. No explanations.
"""

    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.72 + random.uniform(-0.08, 0.08),
            max_tokens=90
        )
        hook = r.choices[0].message.content.strip()
        hook = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', hook)
        hook = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', hook)
        if not re.search(r'[.!?]$', hook):
            hook += " It's quietly appreciated among UK shoppers."
        return hook
    except Exception as e:
        print(f"Groq error for '{name}': {e}")
        return f"Appreciated for its <b>lasting quality</b> and thoughtful design in everyday British life."

def should_refresh_cache():
    if not os.path.exists(CACHE_FILE):
        return True
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        cache_date = datetime.datetime.fromisoformat(cache.get("date", "2000-01-01T00:00:00"))
        days_old = (datetime.datetime.now() - cache_date).days
        if days_old >= CACHE_REFRESH_DAYS:
            return True
        if cache.get("prompt_version") != PROMPT_VERSION:
            return True
        return False
    except Exception:
        return True

def load_or_generate_hooks(products):
    enriched = []
    for p in products:
        p_copy = dict(p)
        p_copy["hook"] = generate_hook(p)
        p_copy.setdefault("date_added", str(datetime.date.today()))
        p_copy["hook_version"] = PROMPT_VERSION
        enriched.append(p_copy)

    today_iso = datetime.datetime.now().isoformat()
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "date": today_iso,
            "prompt_version": PROMPT_VERSION,
            "products": enriched
        }, f, indent=2, ensure_ascii=False)

    history = load_history()
    history_key = datetime.date.today().isoformat()
    history[history_key] = enriched
    save_history(history)

    Thread(target=ping_search_engines, daemon=True).start()
    cache.clear()
    return enriched

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def refresh_products(background=False):
    today = str(datetime.date.today())
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)
            cache_date_str = cache_data.get("date", "")
            if cache_date_str.startswith(today):
                return cache_data.get("products", [])
            cache_date = datetime.datetime.fromisoformat(cache_date_str)
            if (datetime.datetime.now() - cache_date).days < CACHE_REFRESH_DAYS and \
               cache_data.get("prompt_version") == PROMPT_VERSION:
                return cache_data.get("products", [])
        except Exception as e:
            print(f"Cache read failed: {e} — regenerating")
    
    enriched = load_or_generate_hooks(PRODUCTS)
    return enriched

# ============================================================================
# ENHANCED CSS WITH ELITE STYLES
# ============================================================================

CSS_TEMPLATE = """<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@400;600;700&display=swap');

:root {
    --bg: {{bg}};
    --card: {{card}};
    --accent: {{accent}};
    --button: {{button}};
    --button-hover: {{button_hover}};
    --tag: {{tag}};
    --text-accent: {{text_accent}};
    --text-muted: {{text_muted}};
    --gradient: {{gradient}};
    --card-gradient: {{card_gradient}};
    --shadow: {{shadow}};
    --shadow-hover: {{shadow_hover}};
    --dropdown-bg: {{dropdown_bg}};
    --dropdown-border: {{dropdown_border}};
    --nav-bg: {{nav_bg}};
    --nav-border: {{nav_border}};
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body { 
    background: var(--bg); 
    color: var(--accent); 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    padding: 20px;
    transition: background 0.3s ease, color 0.3s ease;
    overflow-x: hidden;
}

h1 { 
    text-align: center; 
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.5rem, 8vw, 5rem);
    font-weight: 900;
    margin: 60px 0 20px;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    line-height: 1.1;
    animation: fadeInUp 0.8s ease;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.subtitle { 
    text-align: center; 
    color: var(--text-accent); 
    font-size: clamp(1rem, 2vw, 1.2rem);
    max-width: 900px; 
    margin: 20px auto 40px;
    line-height: 1.6;
}

.grid { 
    display: grid; 
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
    gap: 32px; 
    max-width: 1600px; 
    margin: 60px auto;
    padding: 0 20px;
}

.card { 
    background: var(--card);
    border-radius: 20px; 
    padding: 28px; 
    text-align: center; 
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
    position: relative; 
    overflow: hidden;
}

.card::before { 
    content: "";
    position: absolute; 
    top: 0; left: 0; right: 0; bottom: 0; 
    background: var(--card-gradient);
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
    border-radius: 20px;
}

.card:hover { 
    transform: translateY(-8px); 
    box-shadow: var(--shadow-hover);
}

.card:hover::before { opacity: 1; }

.card img { 
    width: 100%; 
    max-height: 380px; 
    object-fit: contain; 
    border-radius: 16px; 
    margin: 20px 0; 
    display: block;
    transition: transform 0.4s ease;
}

.card:hover img { transform: scale(1.05); }

.card h2 {
    font-size: 1.3rem;
    font-weight: 700;
    margin: 16px 0;
    color: var(--accent);
    line-height: 1.3;
}

.card p {
    color: var(--text-accent);
    line-height: 1.7;
    margin: 16px 0;
}

.tag { 
    background: var(--tag); 
    color: var(--button);
    padding: 8px 18px; 
    border-radius: 24px; 
    font-size: 0.85rem;
    font-weight: 600;
    display: inline-block; 
    margin-bottom: 12px;
}

/* ELITE PRODUCT METRICS - NEW! */
.product-metrics {
    background: linear-gradient(to bottom, transparent, var(--tag));
    border-radius: 12px;
    padding: 16px;
    margin: 20px 0;
}

.price-display {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-bottom: 12px;
}

.price-label {
    font-size: 0.9rem;
    color: var(--text-muted);
    font-weight: 500;
}

.price-value {
    font-size: 1.4rem;
    font-weight: 800;
    color: #006600;
    letter-spacing: -0.02em;
}

.rating-display {
    text-align: center;
    color: var(--text-accent);
    font-size: 0.95rem;
}

.check-amazon-notice {
    text-align: center;
    padding: 12px;
    font-size: 0.95rem;
    font-style: italic;
}

/* ELITE AMAZON CTA - NEW! */
button { 
    background: linear-gradient(135deg, #ff9900 0%, #ff8c00 100%);
    border: none; 
    padding: 14px 32px; 
    border-radius: 50px; 
    font-size: 1rem; 
    font-weight: 700;
    color: white; 
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(255, 153, 0, 0.3);
}

button:hover { 
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(255, 153, 0, 0.4);
}

nav { 
    background: var(--nav-bg);
    padding: 20px; 
    margin: 20px 0 60px; 
    border-radius: 16px; 
    box-shadow: var(--shadow);
    border: 1px solid var(--nav-border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
}

.nav-links {
    display: flex;
    gap: 32px;
    align-items: center;
}

.nav-links a {
    color: var(--text-accent);
    font-weight: 600;
    font-size: 1.05rem;
    padding: 8px 16px;
    border-radius: 8px;
    transition: all 0.2s ease;
}

.nav-links a:hover {
    background: var(--tag);
    color: var(--button);
}

.dropdown {
    position: relative;
}

.dropdown-toggle {
    background: var(--card);
    color: var(--accent);
    border: 1px solid var(--dropdown-border);
    padding: 10px 20px;
    border-radius: 24px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
}

.dropdown-toggle:hover {
    background: var(--tag);
    border-color: var(--button);
}

.dropdown-toggle::after {
    content: '▼';
    font-size: 0.7rem;
    transition: transform 0.2s ease;
}

.dropdown.active .dropdown-toggle::after {
    transform: rotate(180deg);
}

.dropdown-menu {
    display: none;
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    background: var(--dropdown-bg);
    border: 1px solid var(--dropdown-border);
    border-radius: 12px;
    padding: 8px 0;
    min-width: 220px;
    max-height: 400px;
    overflow-y: auto;
    box-shadow: var(--shadow-hover);
    z-index: 1000;
}

.dropdown.active .dropdown-menu {
    display: block;
}

.dropdown-menu a {
    display: block;
    padding: 12px 20px;
    color: var(--text-accent);
    font-size: 0.95rem;
    font-weight: 500;
    transition: all 0.2s ease;
    white-space: nowrap;
}

.dropdown-menu a:hover {
    background: var(--tag);
    color: var(--button);
    padding-left: 24px;
}

#search-form {
    flex: 1;
    max-width: 400px;
}

#search-input {
    width: 100%;
    padding: 12px 20px;
    border-radius: 24px;
    border: 1px solid var(--dropdown-border);
    background: var(--card);
    color: var(--accent);
    font-size: 0.95rem;
    transition: all 0.2s ease;
}

#search-input:focus {
    outline: none;
    border-color: var(--button);
    box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.1);
}

#search-input::placeholder {
    color: var(--text-muted);
}

#theme-toggle {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 999;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    border: 1px solid var(--dropdown-border);
    cursor: pointer;
    background: var(--card);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
}

#theme-toggle:hover {
    transform: scale(1.1);
    box-shadow: var(--shadow-hover);
}

#theme-toggle svg {
    width: 20px;
    height: 20px;
    fill: var(--accent);
}

footer {
    text-align: center;
    color: var(--text-muted);
    margin: 100px 0 60px;
    font-size: 0.95rem;
    line-height: 1.8;
}

footer p { margin: 12px 0; }

a {
    color: var(--text-accent);
    text-decoration: none;
    transition: color 0.2s ease;
}

a:hover { color: var(--button); }

.pagination {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 60px 0;
}

.pagination a {
    background: var(--button);
    padding: 12px 24px;
    border-radius: 50px;
    color: white;
    font-weight: 700;
    transition: all 0.3s ease;
}

.pagination a:hover {
    transform: translateY(-2px);
    background: var(--button-hover);
}

article {
    color: var(--text-accent);
}

article h2 {
    color: var(--accent);
    margin-top: 40px;
    margin-bottom: 16px;
}

article p {
    color: var(--text-accent);
    line-height: 1.8;
}

article a {
    color: var(--button);
    font-weight: 600;
}

.grid .card.hidden {
    display: none;
}

/* SIMILAR PRODUCTS SECTION - NEW! */
.similar-products-section {
    max-width: 1400px;
    margin: 80px auto;
    padding: 40px 20px;
}

.similar-products-heading {
    text-align: center;
    font-family: 'Playfair Display', serif;
    font-size: 2.5rem;
    font-weight: 900;
    margin-bottom: 12px;
    color: var(--accent);
}

.similar-products-subtitle {
    text-align: center;
    font-size: 1.1rem;
    color: var(--text-muted);
    margin-bottom: 40px;
}

.similar-products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 28px;
}

.similar-product-card {
    background: var(--card);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
}

.similar-product-card:hover {
    transform: translateY(-6px);
    box-shadow: var(--shadow-hover);
}

.similar-product-card img {
    width: 100%;
    max-height: 220px;
    object-fit: contain;
    border-radius: 12px;
    margin-bottom: 16px;
}

.similar-product-card h3 {
    font-size: 1.05rem;
    line-height: 1.4;
    margin-bottom: 12px;
    color: var(--accent);
    min-height: 2.8em;
}

.similar-price {
    font-size: 1.2rem;
    font-weight: 700;
    color: #006600;
}

/* INFO FOOTER - NEW! */
.product-info-footer {
    max-width: 900px;
    margin: 40px auto;
    padding: 24px;
    background: var(--tag);
    border-radius: 12px;
    font-size: 0.9rem;
    line-height: 1.7;
}

.product-info-footer p {
    margin: 8px 0;
    color: var(--text-muted);
}

@media (max-width: 768px) {
    nav {
        flex-direction: column;
        align-items: stretch;
    }
    
    .nav-links {
        flex-direction: column;
        gap: 12px;
        width: 100%;
    }
    
    .nav-links a {
        text-align: center;
    }
    
    .dropdown {
        width: 100%;
    }
    
    .dropdown-toggle {
        width: 100%;
        justify-content: center;
    }
    
    .dropdown-menu {
        left: 0;
        right: 0;
        min-width: auto;
    }
    
    #search-form {
        max-width: none;
    }
    
    .grid {
        grid-template-columns: 1fr;
        gap: 24px;
    }
    
    h1 {
        font-size: 2.5rem;
    }
}

::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: var(--bg);
}

::-webkit-scrollbar-thumb {
    background: var(--button);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--button-hover);
}
</style>"""

# ============================================================================
# BASE HTML TEMPLATE WITH ENHANCEMENTS
# ============================================================================

BASE_HTML = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{{ title }}</title>
<meta name="description" content="{{ description | truncate(155, true, '...') }}">
<link rel="canonical" href="{{ canonical_url }}">
{% if prev_page_url %}<link rel="prev" href="{{ prev_page_url }}">{% endif %}
{% if next_page_url %}<link rel="next" href="{{ next_page_url }}">{% endif %}

<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description | truncate(200, true, '...') }}">
<meta property="og:type" content="{% if products|length == 1 %}product{% elif '/blog' in request.path %}article{% else %}website{% endif %}">
<meta property="og:url" content="{{ canonical_url }}">
<meta property="og:site_name" content="FyboBuybo">
<meta property="og:image" content="{% if products and products[0].image %}{{ products[0].image }}{% else %}{{ SITE_URL }}/static/og-default.jpg{% endif %}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ title }}">
<meta name="twitter:description" content="{{ description | truncate(200, true, '...') }}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://m.media-amazon.com">

{{ css|safe }}
</head>
<body>

<button id="theme-toggle" aria-label="Toggle theme">
  <svg id="theme-icon-sun" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="5"/>
    <line x1="12" y1="1" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="12" y1="21" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="1" y1="12" x2="3" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="21" y1="12" x2="23" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>
  <svg id="theme-icon-moon" viewBox="0 0 24 24" style="display: none;">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
</button>

<nav>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/blog">Blog</a>
  </div>
  
  <div class="dropdown categories-dropdown">
    <button class="dropdown-toggle" type="button">Categories</button>
    <div class="dropdown-menu">
      {% for cat in nav_items.categories %}
        <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
      {% endfor %}
    </div>
  </div>
  
  {% if nav_items.seasons %}
  <div class="dropdown seasons-dropdown">
    <button class="dropdown-toggle" type="button">Seasonal</button>
    <div class="dropdown-menu">
      {% for season in nav_items.seasons %}
        <a href="/season/{{ slugify(season) }}">{{ season }}</a>
      {% endfor %}
    </div>
  </div>
  {% endif %}
  
  <form id="search-form" role="search">
    <input type="search" id="search-input" placeholder="Search gifts..." aria-label="Search">
  </form>
</nav>

<h1>{{ heading }}</h1>
<p class="subtitle">{{ subtitle }}</p>
<p style="text-align:center;color:var(--text-muted);margin-bottom:60px;font-weight:500;">
    ✔ UK-focused · ✔ Updated daily · ✔ Thoughtfully curated
</p>

{% if products %}
<div class="grid">
  {% for p in products %}
  <div class="card" itemscope itemtype="https://schema.org/Product">
      <span class="tag">{{ p.category }}</span>
      <a href="/product/{{ slugify(p.name) }}" itemprop="url">
          <h2 itemprop="name">{{ shorten_product_name(p.name) }}</h2>
      </a>
      <a href="/product/{{ slugify(p.name) }}">
          <img src="{{ p.image }}" alt="{{ p.name }}" loading="lazy" itemprop="image">
      </a>
      <p itemprop="description">{{ p.hook|safe }}</p>

      {% if p.date_added %}
      <p style="font-size:0.85rem; opacity:.65; margin:16px 0 8px; color:var(--text-muted);">
          ↳ Featured {{ p.date_added }}
      </p>
      {% endif %}

      <div class="product-metrics">
          {% set price_info = get_product_price_rating(p) %}
          
          {% if price_info.price %}
          <div class="price-display">
              <span class="price-label">Price:</span>
              <span class="price-value">{{ format_price_display(price_info.price) }}</span>
          </div>
          {% endif %}
          
          {% if price_info.rating %}
          <div class="rating-display">
              {{ format_rating_display(price_info.rating, price_info.reviews) }}
          </div>
          {% endif %}
          
          {% if not price_info.price and not price_info.rating %}
          <div class="check-amazon-notice">
              <span style="color: var(--text-muted); font-style: italic; font-size: 0.95rem;">
                  View on Amazon for pricing
              </span>
          </div>
          {% endif %}
      </div>

      {% if p.url %}
      <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored noopener">
          <button>Check current price</button>
      </a>
      <p style="margin-top:12px; font-size:.9rem; opacity:.75; text-align:center;">
          <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored noopener">View on Amazon UK</a>
      </p>
      {% endif %}

      {% if p.category %}
      <p style="font-size:.9rem; opacity:.7; margin-top:20px; text-align:center;">
          More <a href="/category/{{ slugify(p.category) }}">{{ p.category }}</a>
      </p>
      {% endif %}
  </div>
  {% endfor %}
</div>

{% if similar_products %}
<section class="similar-products-section">
    <h2 class="similar-products-heading">Customers Also Viewed</h2>
    <p class="similar-products-subtitle">Popular alternatives in {{ products[0].category if products else 'this category' }}</p>
    
    <div class="similar-products-grid">
        {% for similar in similar_products %}
        <div class="similar-product-card">
            <a href="/product/{{ slugify(similar.name) }}">
                <img src="{{ similar.image }}" alt="{{ similar.name }}" loading="lazy">
                <h3>{{ shorten_product_name(similar.name, 60) }}</h3>
            </a>
            {% set similar_price = get_product_price_rating(similar) %}
            {% if similar_price.price %}
            <p class="similar-price">{{ format_price_display(similar_price.price) }}</p>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}

{% endif %}

{% if products %}
    {% if products|length == 1 %}
    <div class="product-info-footer">
        <p>
            <strong>Information Accuracy:</strong>
            Product details verified as of
            <time datetime="{{ today }}">{{ today_formatted }}</time>.
            Amazon prices may vary.
        </p>
        <p><strong>As an Amazon Associate, we earn from qualifying purchases.</strong></p>
    </div>
    {% endif %}
{% else %}
    <p style="text-align:center; color:var(--text-accent); margin:100px 0; font-size:1.4rem;">
        Loading today's gifts...
    </p>
{% endif %}



{% if products and (next_page_url or prev_page_url) %}
<div class="pagination">
    {% if prev_page_url %}<a href="{{ prev_page_url }}">← Previous</a>{% endif %}
    {% if next_page_url %}<a href="{{ next_page_url }}">Next →</a>{% endif %}
</div>
{% endif %}

<footer>
    <p><strong>As an Amazon Associate, I earn from qualifying purchases.</strong></p>
    <p>Information Accuracy: All product details, prices, and availability were verified as of date featured. Amazon prices and stock levels may change.</p>
    <p>FyboBuybo is an independent UK gifts site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc.</p>
</footer>

<script>
const THEMES = {{ themes_json|safe }};
let currentTheme = parseInt(localStorage.getItem('themeIndex')) || 0;

function applyTheme(themeIndex) {
  const theme = THEMES[themeIndex];
  const root = document.documentElement;
  
  Object.keys(theme).forEach(key => {
    if (key !== 'name') {
      root.style.setProperty(`--${key.replace(/_/g, '-')}`, theme[key]);
    }
  });

  document.getElementById('theme-icon-sun').style.display = themeIndex === 0 ? 'block' : 'none';
  document.getElementById('theme-icon-moon').style.display = themeIndex === 1 ? 'block' : 'none';
  localStorage.setItem('themeIndex', themeIndex);
}

applyTheme(currentTheme);

document.getElementById('theme-toggle').addEventListener('click', () => {
  currentTheme = (currentTheme + 1) % THEMES.length;
  applyTheme(currentTheme);
});

document.querySelectorAll('.dropdown').forEach(dropdown => {
  const toggle = dropdown.querySelector('.dropdown-toggle');
  toggle.addEventListener('click', (e) => {
    e.stopPropagation();
    document.querySelectorAll('.dropdown').forEach(d => {
      if (d !== dropdown) d.classList.remove('active');
    });
    dropdown.classList.toggle('active');
  });
});

document.addEventListener('click', () => {
  document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('active'));
});

const searchInput = document.getElementById('search-input');
if (searchInput) {
  searchInput.addEventListener('input', function(e) {
    const query = e.target.value.toLowerCase().trim();
    const cards = document.querySelectorAll('.grid .card');
    
    cards.forEach(card => {
      const name = card.querySelector('h2')?.textContent.toLowerCase() || '';
      const desc = card.querySelector('p[itemprop="description"]')?.textContent.toLowerCase() || '';
      const cat = card.querySelector('.tag')?.textContent.toLowerCase() || '';
      const matches = name.includes(query) || desc.includes(query) || cat.includes(query);
      card.classList.toggle('hidden', !matches);
    });
  });
}
</script>

</body>
</html>
"""

# ============================================================================
# RENDER PAGE FUNCTION
# ============================================================================

@cache.cached(timeout=300, key_prefix=lambda: request.full_path)
def render_page(title, description, heading, subtitle, products=None, page=1, page_url=None, similar_products=None, today=None, today_formatted=None):
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    
    nav_items = get_nav_items()
    
    canonical = SITE_URL + request.path
    page_num = int(request.args.get("page", 1))
    if page_num > 1:
        canonical += f"?page={page_num}"

    paged_products = []
    total_pages = 1
    if products:
        paged_products, total_items = paginate(products, page)
        total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    next_url = page_url(page + 1) if page_url and page < total_pages else None
    prev_url = page_url(page - 1) if page_url and page > 1 else None

    themes_json = json.dumps(THEMES)
    
    # Add today's date if not provided
    if not today:
        today = datetime.date.today().isoformat()
        today_formatted = datetime.date.today().strftime("%B %d, %Y")

    return render_template_string(
        BASE_HTML,
        title=title,
        description=description,
        heading=heading,
        subtitle=subtitle,
        products=paged_products,
        nav_items=nav_items,
        css=css,
        canonical_url=canonical,
        SITE_URL=SITE_URL,
        slugify=slugify,
        shorten_product_name=shorten_product_name,
        similar_products=similar_products or [],
        next_page_url=next_url,
        prev_page_url=prev_url,
        themes_json=themes_json,
        get_product_price_rating=get_product_price_rating,
        format_price_display=format_price_display,
        format_rating_display=format_rating_display,
        today=today,
        today_formatted=today_formatted
    )

# ============================================================================
# ROUTES
# ============================================================================

@app.route("/")
def home():
    products = refresh_products(background=True)[:ITEMS_PER_PAGE]
    return render_page(
        title="FyboBuybo – Trending UK Gifts & Popular Presents 2026",
        description="Discover today's trending UK gifts and popular presents across toys, beauty, electronics, home and more – refreshed daily with thoughtful picks for British shoppers.",
        heading="FyboBuybo – Trending UK Gifts",
        subtitle="A curated selection of popular gifts and presents, refreshed daily.",
        products=products
    )

@app.route("/category/<slug>")
@app.route("/category/<slug>/page/<int:page>")
def category(slug, page=1):
    all_products = refresh_products(background=True)
    filtered = [p for p in all_products if slugify(p.get("category", "")) == slug]
    if not filtered:
        abort(404)
    
    cat_name = filtered[0]["category"]
    
    def page_url(p_num):
        return url_for("category", slug=slug, page=p_num)
    
    return render_page(
        title=f"{cat_name} Gifts – FyboBuybo",
        description=f"Explore popular {cat_name.lower()} gifts loved by UK shoppers – updated daily with quality picks.",
        heading=cat_name,
        subtitle=f"Hand-picked {cat_name.lower()}, refreshed daily.",
        products=filtered,
        page=page,
        page_url=page_url
    )

@app.route("/season/<season_slug>")
@app.route("/season/<season_slug>/page/<int:page>")
def seasonal_collection(season_slug, page=1):
    all_products = refresh_products(background=True)
    season_name = season_slug.replace('-', ' ').title()
    norm_slug = normalize_for_match(season_slug)

    filtered = [
        p for p in all_products
        if p.get("season") and any(norm_slug in normalize_for_match(s.strip()) for s in p["season"].split(","))
    ]
    if not filtered:
        abort(404)
    
    filtered.sort(key=lambda p: p.get("date_added", "2000-01-01"), reverse=True)
    
    def page_url(p_num):
        return url_for("seasonal_collection", season_slug=season_slug, page=p_num)
    
    title_season = season_name
    if "day" in season_name.lower() or "christmas" in season_name.lower():
        title_season += " Gifts"

    return render_page(
        title=f"Best {title_season} 2026 – FyboBuybo",
        description=f"Discover the most popular {season_name.lower()} gifts for UK shoppers in 2026 – thoughtful, trending & updated daily.",
        heading=title_season,
        subtitle="Perfect seasonal presents • refreshed every day",
        products=filtered,
        page=page,
        page_url=page_url
    )

@app.route("/product/<path:product_slug>")
def product_detail(product_slug):
    all_products = refresh_products(background=True)
    found = next((p for p in all_products if slugify(p["name"]) == product_slug), None)
    if not found:
        abort(404)

    # Get similar products for SEO
    similar = get_similar_products(found, all_products, limit=6)
    
    # Add today's date for footer
    today = datetime.date.today()
    today_formatted = today.strftime("%B %d, %Y")

    return render_page(
        title=f"{shorten_product_name(found['name'])} – FyboBuybo",
        description=found.get("info", "A thoughtful gift choice popular among UK shoppers."),
        heading=shorten_product_name(found["name"]),
        subtitle="A popular UK gift choice",
        products=[found],
        similar_products=similar,
        today=today.isoformat(),
        today_formatted=today_formatted
    )

POSTS_PER_PAGE = 8

def load_blog_posts(page=1):
    posts = [
        {**v, "slug": k} for k, v in BLOG_POSTS.items()
    ]
    posts.sort(key=lambda x: x.get("date", "1900-01-01"), reverse=True)
    
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    paginated = posts[start:end]
    total_pages = (len(posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    
    return paginated, total_pages, len(posts)

@app.route("/blog")
@app.route("/blog/page/<int:page>")
def blog_list(page=1):
    paginated, total_pages, total_posts = load_blog_posts(page)
    if not paginated and page > 1:
        abort(404)

    theme = get_daily_theme()

    def page_url(p_num):
        return url_for("blog_list", page=p_num) if p_num <= total_pages else None

    rendered = render_page(
        title="FyboBuybo Blog – Gift Guides, Tips & Inspiration 2026",
        description="Latest UK gift ideas, seasonal guides, home tips and thoughtful present recommendations – updated regularly.",
        heading="FyboBuybo Blog",
        subtitle="Gift guides, trends and inspiration for UK shoppers",
        products=None,
        page=page,
        page_url=page_url
    )

    blog_html = '<div class="grid" style="max-width:1100px; margin:40px auto;">'
    accent_color = theme["accent"]
    for post in paginated:
        date_str = datetime.datetime.strptime(post["date"], "%Y-%m-%d").strftime("%d %B %Y")
        blog_html += f'''
        <div class="card" style="text-align:left; padding:24px;">
            <h2 style="font-size:1.6rem; margin-bottom:8px;"><a href="/blog/{post["slug"]}">{post["title"]}</a></h2>
            <p style="opacity:0.7; font-size:0.95rem; margin:0 0 12px;">{date_str}</p>
            <p style="line-height:1.6;">{post.get("description", "")}</p>
            <a href="/blog/{post["slug"]}" style="color:{accent_color}; font-weight:600;">Read more →</a>
        </div>
        '''
    blog_html += '</div>'

    insert_point = rendered.find('<p class="subtitle">') 
    if insert_point > -1:
        insert_after = rendered.find('</p>', insert_point) + 4
        rendered = rendered[:insert_after] + blog_html + rendered[insert_after:]

    if total_pages > 1:
        pag_html = '<div class="pagination">'
        if page > 1:
            pag_html += f'<a href="{url_for("blog_list", page=page-1)}">« Previous</a>'
        if page < total_pages:
            pag_html += f'<a href="{url_for("blog_list", page=page+1)}">Next »</a>'
        pag_html += '</div>'
        rendered = rendered.replace('</body>', pag_html + '</body>')

    return rendered

@app.route("/blog/<slug>")
def blog_detail(slug):
    post = BLOG_POSTS.get(slug)
    if not post:
        abort(404)

    all_products = refresh_products(background=True)
    related = [p for p in all_products if p["category"] in ["Home & Kitchen", "Electronics"]][:6]

    rendered = render_page(
        title=post["title"],
        description=post.get("description", "Gift inspiration and practical tips from FyboBuybo."),
        heading=post.get("heading", post["title"]),
        subtitle=post.get("subtitle", "Gift guide & inspiration"),
        products=None,
        similar_products=related
    )

    content_html = f'''
    <div style="max-width:900px; margin:40px auto; line-height:1.7; font-size:1.05rem;">
        {post.get("content", "<p>Content coming soon.</p>")}
    </div>
    '''

    insert_point = rendered.find('<p class="subtitle">')
    if insert_point > -1:
        insert_after = rendered.find('</p>', insert_point) + 4
        rendered = rendered[:insert_after] + content_html + rendered[insert_after:]

    return rendered

@app.route("/robots.txt")
def robots():
    txt = f"""User-agent: *
Disallow:

Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(txt, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    history = load_history()
    today = str(datetime.date.today())
    urls = set()
    urls.add((SITE_URL + "/", today))

    all_products = []
    for day_products in history.values():
        all_products.extend(day_products)

    for p in all_products:
        lastmod = p.get("date_added", today)
        if p.get("category"):
            urls.add((f"{SITE_URL}/category/{slugify(p['category'])}", lastmod))
        if p.get("name"):
            urls.add((f"{SITE_URL}/product/{slugify(p['name'])}", lastmod))

    seasons = ["Valentine's Day", "Mother's Day", "Easter", "Father's Day",
               "Summer Gifts", "Back to School", "Halloween", "Christmas"]
    for season in seasons:
        urls.add((f"{SITE_URL}/season/{slugify(season)}", today))

    blog_lastmod = today
    if BLOG_POSTS:
        blog_dates = [post.get("date", today) for post in BLOG_POSTS.values()]
        blog_lastmod = max(blog_dates)
        for slug, post in BLOG_POSTS.items():
            urls.add((f"{SITE_URL}/blog/{slug}", post.get("date", today)))
    urls.add((f"{SITE_URL}/blog", blog_lastmod))

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, lastmod in sorted(urls):
        sitemap_xml += f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>\n'
    sitemap_xml += '</urlset>'
    return Response(sitemap_xml, mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
