# ============================================================================
# FYBOBUYBO app.py — ELITE REDESIGN v5.0
# Complete visual overhaul: editorial luxury meets conversion-first UX
# Design direction: "Dark Atelier" — editorial magazine energy with amber-gold
# accents, obsidian backgrounds, and razor-sharp typography
# ============================================================================

import os
import json
import re
import datetime
import random
from threading import Thread
from products_data import PRODUCTS
from blog_data import BLOG_POSTS

from flask import Flask, render_template_string, request, url_for, abort, Response, jsonify
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
PROMPT_VERSION = "v5.0-elite-2026"

os.makedirs("data", exist_ok=True)

PRIVACY_POLICY_HTML = """
<article class="legal-article">
  <div class="legal-header-card">
    <p><strong>Last Updated:</strong> January 23, 2026</p>
    <p>FyboBuybo ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your information when you visit our website www.fybobuybo.com.</p>
  </div>
  <h2>1. Information We Collect</h2>
  <h3>1.1 Automatically Collected Information</h3>
  <p>When you visit our website, we automatically collect certain information about your device and browsing behaviour through cookies and similar technologies.</p>
  <h3>1.2 Information You Provide</h3>
  <p>We do not currently collect personal information directly from you unless you choose to contact us.</p>
  <h2>2. Cookies and Tracking</h2>
  <p>We use essential cookies (theme preference) and Amazon affiliate tracking cookies. You can manage cookies through your browser settings.</p>
  <h2>3. Affiliate Relationships</h2>
  <p>FyboBuybo is a participant in the Amazon EU Associates Programme. We earn commissions on qualifying purchases at no extra cost to you.</p>
  <h2>4. Your Rights Under UK GDPR</h2>
  <p>You have the right to access, rectify, erase, and port your data. Contact us at infofybobuybo@gmail.com to exercise these rights.</p>
  <h2>5. Contact Us</h2>
  <div class="legal-contact-card">
    <p><strong>Email:</strong> infofybobuybo@gmail.com<br><strong>Website:</strong> www.fybobuybo.com</p>
  </div>
</article>
"""

TERMS_OF_SERVICE_HTML = """
<article class="legal-article">
  <div class="legal-header-card">
    <p>Welcome to FyboBuybo. By using www.fybobuybo.com, you accept these Terms of Service.</p>
  </div>
  <h2>1. About FyboBuybo</h2>
  <p>FyboBuybo is a UK-based product discovery and affiliate marketing website. We are not a retailer — all purchases are made through Amazon UK.</p>
  <h2>2. Affiliate Disclosure</h2>
  <p>We earn a commission when you purchase through our links. This does not affect your purchase price.</p>
  <h2>3. Limitation of Liability</h2>
  <p>FyboBuybo is provided "as is". We are not liable for product quality, delivery issues, or retailer problems.</p>
  <h2>4. Governing Law</h2>
  <p>These terms are governed by the laws of England and Wales.</p>
  <h2>5. Contact</h2>
  <div class="legal-contact-card">
    <p><strong>Email:</strong> infofybobuybo@gmail.com</p>
  </div>
</article>
"""

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
# HELPER FUNCTIONS (unchanged from v4)
# ============================================================================

def get_product_price_rating(product):
    return {
        "price": product.get("manual_price") or None,
        "rating": product.get("manual_rating") or None,
        "reviews": product.get("manual_reviews") or None
    }

def format_price_display(price_data):
    if isinstance(price_data, str): return price_data
    if isinstance(price_data, dict): return f"£{price_data['amount']:.2f}"
    return str(price_data) if price_data else ""

def format_rating_display(rating, review_count=None):
    if not rating: return ""
    try:
        rating_float = float(rating)
        stars = "⭐" * int(rating_float)
        half_star = "½⭐" if (rating_float % 1) >= 0.5 else ""
        if review_count:
            formatted_count = review_count if isinstance(review_count, str) else f"{review_count:,}"
            return f"{stars}{half_star} {rating_float}/5 ({formatted_count} reviews)"
        return f"{stars}{half_star} {rating_float}/5"
    except: return ""

def get_similar_products(product, all_products, limit=6):
    similar = []
    category_matches = [p for p in all_products if p.get("category") == product.get("category") and p["name"] != product["name"]]
    similar.extend(category_matches[:limit])
    if len(similar) < limit:
        product_seasons = set(s.strip() for s in product.get("season", "").split(",") if s.strip())
        season_matches = [p for p in all_products if p["name"] != product["name"] and p not in similar and any(s.strip() in product_seasons for s in p.get("season", "").split(","))]
        similar.extend(season_matches[:(limit - len(similar))])
    return similar[:limit]

def generate_product_schema(product):
    from datetime import datetime, timedelta
    price_info = get_product_price_rating(product)
    price_value = None
    if price_info.get("price"):
        price_str = format_price_display(price_info["price"])
        price_nums = re.findall(r'\d+\.?\d*', price_str)
        if price_nums: price_value = float(price_nums[0])
    schema = {
        "@context": "https://schema.org", "@type": "Product",
        "name": product["name"],
        "description": (product.get("info") or product.get("hook") or "")[:200],
        "image": product.get("image", ""),
        "brand": {"@type": "Brand", "name": "Various"},
        "sku": product.get("asin", "")
    }
    if price_value:
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        schema["offers"] = {
            "@type": "Offer", "url": product.get("url", ""),
            "availability": "https://schema.org/InStock",
            "seller": {"@type": "Organization", "name": "Amazon UK"},
            "hasMerchantReturnPolicy": {
                "@type": "MerchantReturnPolicy", "applicableCountry": "GB",
                "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                "merchantReturnDays": 30,
                "returnMethod": "https://schema.org/ReturnByMail",
                "returnFees": "https://schema.org/FreeReturn"
            },
            "shippingDetails": {
                "@type": "OfferShippingDetails",
                "shippingRate": {"@type": "MonetaryAmount", "value": "0", "currency": "GBP"},
                "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "GB"},
                "deliveryTime": {
                    "@type": "ShippingDeliveryTime",
                    "handlingTime": {"@type": "QuantitativeValue", "minValue": 0, "maxValue": 2, "unitCode": "DAY"},
                    "transitTime": {"@type": "QuantitativeValue", "minValue": 1, "maxValue": 3, "unitCode": "DAY"}
                }
            }
        }
    return json.dumps(schema, ensure_ascii=False)

def generate_breadcrumb_schema(breadcrumbs):
    items = []
    for idx, (name, url) in enumerate(breadcrumbs, 1):
        if not url.startswith('http'): url = SITE_URL + url
        items.append({"@type": "ListItem", "position": idx, "name": name, "item": url})
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}, ensure_ascii=False)

def ping_search_engines():
    sitemap_url = f"{SITE_URL}/sitemap.xml"
    for url in [f"https://www.google.com/ping?sitemap={sitemap_url}", f"https://www.bing.com/ping?sitemap={sitemap_url}"]:
        try: requests.get(url, timeout=5)
        except: pass

def slugify(text):
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def normalize_for_match(text):
    if not text: return ""
    return text.lower().replace("'", "").replace(" ", "").replace("-", "")

def get_nav_items():
    products = PRODUCTS
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)
            products = cache_data.get("products", PRODUCTS)
        except: pass
    categories = sorted({p["category"] for p in products if p.get("category")})
    seasons_set = set()
    for p in products:
        if p.get("season"):
            for s in p["season"].split(","):
                clean = s.strip()
                if clean: seasons_set.add(clean)
    important_seasons_order = ["Valentine's Day", "Mother's Day", "Easter", "Father's Day", "Summer Gifts", "Back to School", "Halloween", "Christmas"]
    important_seasons = [s for s in important_seasons_order if s in seasons_set]
    other_seasons = sorted(seasons_set - set(important_seasons))
    return {"categories": categories, "seasons": other_seasons + important_seasons}

def paginate(items, page):
    start = (page - 1) * ITEMS_PER_PAGE
    return items[start:start + ITEMS_PER_PAGE], len(items)

def shorten_product_name(name, max_length=80):
    if len(name) <= max_length: return name
    for sep in [',', '(']:
        if sep in name:
            short = name.split(sep, 1)[0].strip()
            if len(short) <= max_length: return short
    words, out = name.split(), ""
    for w in words:
        if len(out + " " + w) <= max_length - 3: out += (" " if out else "") + w
        else: break
    return out + "..."

def select_hook_type(product):
    category = product.get("category", "").lower()
    price_tier = product.get("price_tier", "").lower()
    rating = product.get("manual_rating")
    reviews = product.get("manual_reviews")
    price = product.get("manual_price", "")
    price_value = 0
    if price:
        price_nums = re.findall(r'\d+\.?\d*', str(price))
        if price_nums: price_value = float(price_nums[0])
    if rating:
        try:
            if float(rating) >= 4.5 and reviews:
                if int(re.sub(r'[^\d]', '', str(reviews)) or "0") > 3000: return "social_proof"
        except: pass
    if price_tier in ["premium", "luxury"] or price_value > 100: return "value_proposition"
    if any(kw in category for kw in ["beauty", "gift", "toy", "comfort", "decor", "fashion", "personal", "wellness"]): return "lifestyle"
    if any(kw in category for kw in ["home", "kitchen", "storage", "cleaning", "appliance", "organization"]): return "problem_solution"
    if any(kw in category for kw in ["electronic", "tech", "gadget", "device", "smart", "digital"]): return "comparison"
    if product.get("season"): return "specific_use_case"
    return random.choice(["problem_solution", "lifestyle", "comparison"])

def generate_hook(product):
    if "hook_override" in product and product["hook_override"].strip():
        return product["hook_override"].strip()
    name = product["name"]
    category = product.get("category", "")
    keywords = product.get("keywords", [])
    pain_points = product.get("pain_points", [])
    pain_point_text = pain_points[0] if pain_points else "everyday practicality"
    keyword_text = ', '.join(keywords[:3]) if keywords else ""
    style = random.choice(["benefit-first", "lifestyle-story", "quality-craft", "problem-solution", "uk-context", "practical-value"])
    prompt = f"""You are a sophisticated British copywriter creating product descriptions for UK shoppers.

Write a compelling 1-2 sentence description for this product:

PRODUCT: {name}
CATEGORY: {category}
STYLE: {style}
KEY BENEFIT: {pain_point_text}
{f"KEYWORDS TO MENTION: {keyword_text}" if keyword_text else ""}

REQUIREMENTS:
- Write 1-2 natural, conversational sentences
- Mention one standout feature using <b>tags</b> around it
- Sound warm, helpful, and British
- Focus on practical benefits
- NO hype words like "must-have", "game-changer", "essential"

Write the description now (just the sentences, nothing else):"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=100, top_p=0.9
        )
        hook = response.choices[0].message.content.strip()
        hook = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', hook)
        hook = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', hook)
        if '<b>' not in hook:
            for word in name.split():
                if len(word) > 4 and word[0].isupper():
                    hook = hook.replace(word, f'<b>{word}</b>', 1)
                    break
        if hook and not re.search(r'[.!?]$', hook): hook += "."
        if hook and 20 < len(hook) < 500: return hook
    except Exception as e:
        print(f"⚠ API error for '{name[:50]}...': {e}")
    return generate_smart_fallback(product)

def generate_smart_fallback(product):
    name = product["name"]
    category = product.get("category", "Product")
    if "beauty" in category.lower():
        return f"Elevates your skincare routine with <b>salon-quality formulation</b> designed for everyday British life."
    elif "toy" in category.lower() or "game" in category.lower():
        return f"Brings joy and entertainment to playtime with <b>durable design</b> that stands up to enthusiastic use."
    elif "home" in category.lower() or "kitchen" in category.lower():
        return f"Simplifies daily routines with <b>practical functionality</b> that UK households genuinely appreciate."
    elif "electronic" in category.lower() or "tech" in category.lower():
        return f"Combines smart functionality with <b>intuitive operation</b> for hassle-free use in modern UK homes."
    elif "fashion" in category.lower() or "clothing" in category.lower():
        return f"Delivers <b>quality craftsmanship</b> and versatile style that works effortlessly in any British wardrobe."
    else:
        return f"Appreciated by UK shoppers for its <b>quality construction</b> and practical value in everyday British life."

# ============================================================================
# CACHE MANAGEMENT (unchanged)
# ============================================================================

def should_refresh_cache():
    if not os.path.exists(CACHE_FILE): return True
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        days_old = (datetime.datetime.now() - datetime.datetime.fromisoformat(cache.get("date", "2000-01-01T00:00:00"))).days
        return days_old >= CACHE_REFRESH_DAYS or cache.get("prompt_version") != PROMPT_VERSION
    except: return True

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
        json.dump({"date": today_iso, "prompt_version": PROMPT_VERSION, "products": enriched}, f, indent=2, ensure_ascii=False)
    history = load_history()
    history[datetime.date.today().isoformat()] = enriched
    save_history(history)
    Thread(target=ping_search_engines, daemon=True).start()
    cache.clear()
    return enriched

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f: return json.load(f)
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

def refresh_products(background=False):
    today = str(datetime.date.today())
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)
            cache_date_str = cache_data.get("date", "")
            if cache_date_str.startswith(today): return cache_data.get("products", [])
            cache_date = datetime.datetime.fromisoformat(cache_date_str)
            if (datetime.datetime.now() - cache_date).days < CACHE_REFRESH_DAYS and cache_data.get("prompt_version") == PROMPT_VERSION:
                return cache_data.get("products", [])
        except Exception as e:
            print(f"Cache read failed: {e}")
    return load_or_generate_hooks(PRODUCTS)


# ============================================================================
# CSS TEMPLATE — ELITE v5.0 "The Atelier"
# Design system: Editorial luxury. Warm obsidian + aged parchment + amber-gold.
# Typography: Cormorant Garamond (editorial soul) + DM Sans (clean utility)
# ============================================================================

CSS_TEMPLATE = """<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,500;1,600;1,700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300;1,9..40,400&display=swap');

/* ─── DESIGN TOKENS ──────────────────────────────── */
:root {
  /* Surface */
  --bg:           #f5f0e8;
  --bg-2:         #ede7da;
  --bg-3:         #e4dccf;
  --card:         #fdfaf5;
  --card-2:       #f8f3eb;

  /* Type */
  --ink:          #1c1410;
  --ink-2:        #2e2620;
  --ink-3:        #4a3f35;
  --muted:        #7a6e63;
  --muted-2:      #9e9187;

  /* Accent — amber-gold system */
  --gold:         #b8832a;
  --gold-2:       #d4a044;
  --gold-3:       #e8b96a;
  --gold-dim:     rgba(184,131,42,0.12);
  --gold-glow:    rgba(184,131,42,0.22);
  --gold-line:    rgba(184,131,42,0.30);

  /* CTA */
  --cta:          #1c1410;
  --cta-fg:       #f5f0e8;
  --cta-hover:    #2e2620;

  /* UI chrome */
  --border:       rgba(28,20,16,0.08);
  --border-2:     rgba(28,20,16,0.14);
  --divider:      rgba(28,20,16,0.06);
  --nav-bg:       rgba(245,240,232,0.94);
  --input-bg:     rgba(253,250,245,0.90);

  /* Shadows — warm-toned */
  --sh-xs:  0 1px 2px rgba(28,20,16,0.04), 0 2px 6px rgba(28,20,16,0.04);
  --sh-sm:  0 2px 8px rgba(28,20,16,0.05), 0 4px 18px rgba(28,20,16,0.07);
  --sh-md:  0 4px 20px rgba(28,20,16,0.08), 0 12px 40px rgba(28,20,16,0.10);
  --sh-lg:  0 8px 36px rgba(28,20,16,0.11), 0 24px 64px rgba(28,20,16,0.14);
  --sh-xl:  0 16px 56px rgba(28,20,16,0.15), 0 40px 96px rgba(28,20,16,0.18);

  /* Radius */
  --r-sm:  8px;
  --r-md:  14px;
  --r-lg:  20px;
  --r-xl:  28px;
  --r-pill:99px;

  /* Motion */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* ─── DARK MODE ──────────────────────────────────── */
.dark {
  --bg:           #140f0c;
  --bg-2:         #1c1612;
  --bg-3:         #241d18;
  --card:         #1e1813;
  --card-2:       #251f19;
  --ink:          #f0ebe2;
  --ink-2:        #d4ccbf;
  --ink-3:        #b0a898;
  --muted:        #8a7f73;
  --muted-2:      #6a6059;
  --gold:         #d4a044;
  --gold-2:       #e8b96a;
  --gold-3:       #f0c97a;
  --gold-dim:     rgba(212,160,68,0.10);
  --gold-glow:    rgba(212,160,68,0.20);
  --gold-line:    rgba(212,160,68,0.28);
  --cta:          #d4a044;
  --cta-fg:       #140f0c;
  --cta-hover:    #e8b96a;
  --border:       rgba(240,235,226,0.07);
  --border-2:     rgba(240,235,226,0.12);
  --divider:      rgba(240,235,226,0.055);
  --nav-bg:       rgba(20,15,12,0.96);
  --input-bg:     rgba(240,235,226,0.05);
  --sh-xs:  0 1px 2px rgba(0,0,0,0.40), 0 2px 6px rgba(0,0,0,0.45);
  --sh-sm:  0 2px 8px rgba(0,0,0,0.45), 0 4px 18px rgba(0,0,0,0.50);
  --sh-md:  0 4px 20px rgba(0,0,0,0.52), 0 12px 40px rgba(0,0,0,0.58);
  --sh-lg:  0 8px 36px rgba(0,0,0,0.60), 0 24px 64px rgba(0,0,0,0.68);
  --sh-xl:  0 16px 56px rgba(0,0,0,0.70), 0 40px 96px rgba(0,0,0,0.80);
}

/* ─── RESET ──────────────────────────────────────── */
*,*::before,*::after { margin:0; padding:0; box-sizing:border-box; }
html { scroll-behavior:smooth; -webkit-text-size-adjust:100%; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: 'DM Sans', sans-serif;
  font-size: 16px;
  line-height: 1.6;
  overflow-x: hidden;
  min-height: 100vh;
  transition: background .35s ease, color .35s ease;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
a { text-decoration: none; color: inherit; }
img { max-width: 100%; display: block; }
button { font-family: inherit; cursor: pointer; }

/* Grain texture overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 0;
  opacity: .5;
}

/* ─── TICKER / RIBBON ────────────────────────────── */
.ribbon {
  position: relative;
  z-index: 10;
  background: var(--ink);
  color: var(--gold-2);
  padding: 9px 0;
  overflow: hidden;
  white-space: nowrap;
}
.ribbon-track {
  display: inline-flex;
  gap: 0;
  animation: ticker 50s linear infinite;
  will-change: transform;
}
.ribbon-track span {
  font-size: .68rem;
  font-weight: 600;
  letter-spacing: .18em;
  text-transform: uppercase;
  padding: 0 28px;
  flex-shrink: 0;
}
.ribbon-track .sep {
  color: var(--gold);
  opacity: .45;
  padding: 0 2px;
}
@keyframes ticker {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); }
}
.ribbon:hover .ribbon-track { animation-play-state: paused; }

/* ─── NAV ────────────────────────────────────────── */
.site-nav {
  position: sticky;
  top: 0;
  z-index: 200;
  background: var(--nav-bg);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-bottom: 1px solid var(--border);
  transition: background .3s, box-shadow .3s;
}
.site-nav.scrolled {
  box-shadow: var(--sh-sm);
}
.nav-inner {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 52px;
  display: flex;
  align-items: center;
  height: 68px;
  gap: 8px;
}

/* Logo */
.nav-logo {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.75rem;
  font-weight: 600;
  letter-spacing: -.02em;
  color: var(--ink);
  flex-shrink: 0;
  margin-right: 16px;
  transition: opacity .2s;
  display: flex;
  align-items: baseline;
  gap: 1px;
}
.nav-logo:hover { opacity: .78; }
.nav-logo .logo-fybo { color: var(--ink); }
.nav-logo .logo-buybo { color: var(--gold); font-style: italic; }
.nav-logo .logo-dot {
  display: inline-block;
  width: 5px; height: 5px;
  background: var(--gold);
  border-radius: 50%;
  margin: 0 1px 4px;
  flex-shrink: 0;
}

/* Nav links */
.nav-links {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 1;
}
.nav-links > a {
  font-size: .875rem;
  font-weight: 500;
  color: var(--muted);
  padding: 6px 12px;
  border-radius: var(--r-sm);
  transition: color .18s, background .18s;
  letter-spacing: -.01em;
}
.nav-links > a:hover {
  color: var(--ink);
  background: var(--gold-dim);
}

/* Dropdown */
.nav-drop { position: relative; }
.nav-drop-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: .875rem;
  font-weight: 500;
  color: var(--muted);
  padding: 6px 12px;
  border-radius: var(--r-sm);
  background: none;
  border: none;
  transition: color .18s, background .18s;
  letter-spacing: -.01em;
}
.nav-drop-btn:hover,
.nav-drop.open .nav-drop-btn {
  color: var(--ink);
  background: var(--gold-dim);
}
.drop-arrow {
  width: 10px; height: 10px;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
  transition: transform .22s var(--ease-out);
}
.nav-drop.open .drop-arrow { transform: rotate(180deg); }

.nav-drop-menu {
  display: none;
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  background: var(--card);
  border: 1px solid var(--border-2);
  border-radius: var(--r-lg);
  padding: 8px;
  min-width: 200px;
  max-height: 380px;
  overflow-y: auto;
  box-shadow: var(--sh-lg);
  z-index: 300;
}
.nav-drop.open .nav-drop-menu {
  display: block;
  animation: dropIn .18s var(--ease-out);
}
@keyframes dropIn {
  from { opacity: 0; transform: translateY(-6px) scale(.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.nav-drop-menu a {
  display: block;
  padding: 9px 14px;
  border-radius: var(--r-sm);
  font-size: .855rem;
  font-weight: 400;
  color: var(--ink-3);
  transition: all .14s;
  letter-spacing: -.01em;
}
.nav-drop-menu a:hover {
  background: var(--gold-dim);
  color: var(--gold);
  padding-left: 18px;
}

/* Nav search */
.nav-search { position: relative; }
.nav-search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.nav-search-icon {
  position: absolute;
  left: 12px;
  width: 15px; height: 15px;
  stroke: var(--muted);
  fill: none;
  stroke-width: 1.8;
  pointer-events: none;
  transition: stroke .2s;
  z-index: 1;
}
.nav-search input {
  background: var(--input-bg);
  border: 1px solid var(--border);
  border-radius: var(--r-pill);
  padding: 8px 16px 8px 38px;
  font-size: .84rem;
  font-family: inherit;
  color: var(--ink);
  width: 200px;
  transition: all .25s var(--ease-out);
  outline: none;
  letter-spacing: -.01em;
}
.nav-search input:focus {
  width: 260px;
  border-color: var(--gold);
  box-shadow: 0 0 0 3px var(--gold-dim);
  background: var(--card);
}
.nav-search input::placeholder { color: var(--muted-2); }
.nav-search input:focus + .nav-search-icon,
.nav-search-wrap:focus-within .nav-search-icon { stroke: var(--gold); }

/* Nav right */
.nav-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.nav-icon-btn {
  width: 38px; height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .2s;
  flex-shrink: 0;
}
.nav-icon-btn:hover {
  background: var(--gold-dim);
  border-color: var(--gold-line);
}
.nav-icon-btn svg {
  width: 15px; height: 15px;
  stroke: var(--ink-3);
  fill: none;
  stroke-width: 1.8;
}

#hamburger {
  display: none;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 5px;
  width: 38px; height: 38px;
  border: 1px solid var(--border);
  border-radius: 50%;
  background: transparent;
}
#hamburger span {
  display: block;
  width: 18px; height: 1.5px;
  background: var(--ink);
  border-radius: 2px;
  transition: all .26s var(--ease-out);
  transform-origin: center;
}
#hamburger.open span:nth-child(1) { transform: translateY(6.5px) rotate(45deg); }
#hamburger.open span:nth-child(2) { opacity: 0; transform: scaleX(0); }
#hamburger.open span:nth-child(3) { transform: translateY(-6.5px) rotate(-45deg); }

/* ─── MOBILE DRAWER ──────────────────────────────── */
#mobile-menu {
  display: none;
  position: fixed;
  inset: 0;
  background: var(--bg);
  z-index: 190;
  overflow-y: auto;
  padding: 88px 28px 56px;
  flex-direction: column;
}
#mobile-menu.open {
  display: flex;
  animation: mmIn .3s var(--ease-out);
}
@keyframes mmIn {
  from { opacity: 0; transform: translateY(-12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.mm-primary {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 32px;
}
.mm-link {
  font-family: 'Cormorant Garamond', serif;
  font-size: 2.4rem;
  font-weight: 500;
  color: var(--ink);
  padding: 12px 0;
  border-bottom: 1px solid var(--divider);
  display: block;
  transition: color .2s, padding-left .2s;
  letter-spacing: -.03em;
}
.mm-link:hover { color: var(--gold); padding-left: 8px; }
.mm-section {
  margin-bottom: 28px;
}
.mm-label {
  font-size: .66rem;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.mm-label::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--gold-line);
}
.mm-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.mm-pill {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r-pill);
  padding: 8px 18px;
  font-size: .84rem;
  font-weight: 500;
  color: var(--ink-3);
  transition: all .2s;
  letter-spacing: -.01em;
}
.mm-pill:hover {
  background: var(--gold-dim);
  border-color: var(--gold-line);
  color: var(--gold);
}
.mm-search-wrap {
  margin-top: 28px;
  position: relative;
}
.mm-search-wrap svg {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px; height: 16px;
  stroke: var(--muted);
  fill: none;
  stroke-width: 1.8;
  pointer-events: none;
}
.mm-search-wrap input {
  width: 100%;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 14px 18px 14px 46px;
  font-size: 1rem;
  font-family: inherit;
  color: var(--ink);
  outline: none;
  transition: border-color .2s;
  letter-spacing: -.01em;
}
.mm-search-wrap input:focus { border-color: var(--gold); }
.mm-search-wrap input::placeholder { color: var(--muted-2); }

/* ─── HERO ───────────────────────────────────────── */
.hero {
  max-width: 1600px;
  margin: 0 auto;
  padding: clamp(48px,6vw,96px) 52px clamp(36px,4vw,60px);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(40px, 5vw, 80px);
  align-items: center;
  position: relative;
  z-index: 1;
}

/* Large decorative number in background */
.hero::before {
  content: '01';
  position: absolute;
  right: 52px;
  top: 20px;
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(120px, 15vw, 200px);
  font-weight: 700;
  color: var(--gold);
  opacity: .04;
  pointer-events: none;
  line-height: 1;
  letter-spacing: -.05em;
}

.hero-content {}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: .68rem;
  font-weight: 600;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 24px;
}
.hero-eyebrow::before {
  content: '';
  display: block;
  width: 28px;
  height: 1px;
  background: var(--gold);
}

.hero-h1 {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(3rem, 5.5vw, 5.5rem);
  font-weight: 600;
  line-height: .98;
  letter-spacing: -.04em;
  color: var(--ink);
  margin-bottom: 26px;
  animation: riseUp 1s var(--ease-out) both;
}
.hero-h1 em {
  font-style: italic;
  color: var(--gold);
}
.hero-h1 .line-2 {
  display: block;
  font-weight: 300;
  color: var(--ink-3);
}
@keyframes riseUp {
  from { opacity: 0; transform: translateY(32px); }
  to   { opacity: 1; transform: translateY(0); }
}

.hero-sub {
  font-size: 1.05rem;
  line-height: 1.75;
  color: var(--muted);
  max-width: 460px;
  margin-bottom: 36px;
  animation: riseUp .9s .12s var(--ease-out) both;
  font-weight: 300;
  letter-spacing: -.01em;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  animation: riseUp .9s .2s var(--ease-out) both;
}
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--cta);
  color: var(--cta-fg);
  padding: 14px 28px;
  border-radius: var(--r-pill);
  font-size: .9rem;
  font-weight: 600;
  letter-spacing: -.01em;
  border: none;
  transition: background .2s, transform .2s, box-shadow .2s;
  box-shadow: var(--sh-sm);
}
.btn-primary:hover {
  background: var(--cta-hover);
  transform: translateY(-2px);
  box-shadow: var(--sh-md);
}
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: var(--muted);
  padding: 14px 22px;
  border-radius: var(--r-pill);
  font-size: .9rem;
  font-weight: 500;
  border: 1px solid var(--border-2);
  transition: all .2s;
  letter-spacing: -.01em;
}
.btn-ghost:hover {
  color: var(--ink);
  border-color: var(--gold-line);
  background: var(--gold-dim);
}

/* Hero stats row */
.hero-stats {
  display: flex;
  gap: 32px;
  margin-top: 44px;
  padding-top: 36px;
  border-top: 1px solid var(--divider);
  animation: riseUp .9s .28s var(--ease-out) both;
}
.hero-stat-num {
  font-family: 'Cormorant Garamond', serif;
  font-size: 2.2rem;
  font-weight: 600;
  color: var(--ink);
  line-height: 1;
  letter-spacing: -.04em;
}
.hero-stat-num span { color: var(--gold); }
.hero-stat-label {
  font-size: .74rem;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: .04em;
  text-transform: uppercase;
  margin-top: 4px;
}

/* Hero visual — collage stack */
.hero-visual {
  position: relative;
  aspect-ratio: 1 / 1.05;
  animation: riseUp .9s .24s var(--ease-out) both;
}
.hero-img-main {
  position: absolute;
  inset: 0;
  border-radius: var(--r-xl);
  overflow: hidden;
  background: var(--bg-2);
  box-shadow: var(--sh-lg);
}
.hero-img-main img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.hero-img-float {
  position: absolute;
  bottom: -20px;
  left: -24px;
  width: 48%;
  aspect-ratio: 1;
  border-radius: var(--r-lg);
  overflow: hidden;
  background: var(--bg-3);
  box-shadow: var(--sh-xl);
  border: 4px solid var(--bg);
}
.hero-img-float img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 12px;
  background: var(--card);
}
/* Gold ornament dot */
.hero-ornament {
  position: absolute;
  top: -18px;
  right: -18px;
  width: 68px;
  height: 68px;
  border-radius: 50%;
  background: var(--gold);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--sh-md), 0 0 0 8px var(--gold-dim);
  animation: pulse 3s ease-in-out infinite;
  z-index: 2;
}
.hero-ornament span {
  font-size: .6rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--cta-fg);
  text-align: center;
  line-height: 1.3;
}
.dark .hero-ornament span { color: var(--bg); }
@keyframes pulse {
  0%,100% { box-shadow: var(--sh-md), 0 0 0 8px var(--gold-dim); }
  50%      { box-shadow: var(--sh-md), 0 0 0 14px var(--gold-dim); }
}

/* ─── DISCLOSURE STRIP ───────────────────────────── */
.affil-strip {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 52px 16px;
}
.affil-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--gold-dim);
  border: 1px solid var(--gold-line);
  border-radius: var(--r-md);
  padding: 10px 18px;
  font-size: .8rem;
  color: var(--muted);
  line-height: 1.5;
}
.affil-inner strong { color: var(--ink-3); font-weight: 600; }
.affil-inner a { color: var(--gold); font-weight: 500; }
.affil-icon {
  flex-shrink: 0;
  width: 14px; height: 14px;
  stroke: var(--gold);
  fill: none;
  stroke-width: 2;
}

/* ─── CATEGORY RAIL ──────────────────────────────── */
.cat-rail {
  max-width: 1600px;
  margin: 36px auto 0;
  padding: 0 52px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.cat-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r-pill);
  padding: 8px 18px;
  font-size: .82rem;
  font-weight: 500;
  color: var(--ink-3);
  transition: all .2s;
  letter-spacing: -.01em;
  white-space: nowrap;
}
.cat-chip:hover {
  background: var(--gold-dim);
  border-color: var(--gold-line);
  color: var(--gold);
  transform: translateY(-1px);
  box-shadow: var(--sh-xs);
}

/* ─── SECTION HEADER ─────────────────────────────── */
.sec-hdr {
  max-width: 1600px;
  margin: 68px auto 0;
  padding: 0 52px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}
.sec-eyebrow {
  font-size: .67rem;
  font-weight: 600;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.sec-eyebrow::before {
  content: '';
  display: block;
  width: 20px;
  height: 1px;
  background: var(--gold);
}
.sec-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(1.8rem, 3vw, 2.8rem);
  font-weight: 600;
  letter-spacing: -.04em;
  line-height: 1.05;
  color: var(--ink);
}
.sec-title em { font-style: italic; color: var(--gold); }
.sec-view-all {
  font-size: .82rem;
  font-weight: 600;
  color: var(--gold);
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid transparent;
  transition: border-color .2s, gap .2s;
  white-space: nowrap;
  flex-shrink: 0;
}
.sec-view-all:hover {
  border-color: var(--gold);
  gap: 10px;
}

/* ─── PRODUCT GRID ───────────────────────────────── */
.grid {
  max-width: 1600px;
  margin: 28px auto 0;
  padding: 0 52px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

/* ─── PRODUCT CARD ───────────────────────────────── */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r-xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: transform .35s var(--ease-spring), box-shadow .35s ease, border-color .3s;
  box-shadow: var(--sh-xs);
  will-change: transform;
}
.card:hover {
  transform: translateY(-8px);
  box-shadow: var(--sh-lg);
  border-color: var(--border-2);
}

/* Card image area */
.card-img {
  position: relative;
  background: var(--bg-2);
  aspect-ratio: 1;
  overflow: hidden;
}
.card-img::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, transparent 60%, rgba(0,0,0,0.04) 100%);
  pointer-events: none;
}
.card-img a { display: block; width: 100%; height: 100%; }
.card-img img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 22px;
  transition: transform .55s cubic-bezier(.25,.46,.45,.94);
  will-change: transform;
}
.card:hover .card-img img { transform: scale(1.08); }

/* Category badge */
.card-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(253,250,245,0.92);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: var(--r-pill);
  padding: 3px 11px;
  font-size: .68rem;
  font-weight: 600;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--ink-3);
  box-shadow: var(--sh-xs);
}
.dark .card-badge {
  background: rgba(30,24,19,0.88);
  color: var(--ink-2);
}

/* Quick-view indicator */
.card-quick {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: var(--gold);
  color: var(--cta-fg);
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: scale(.8);
  transition: all .25s var(--ease-out);
  box-shadow: var(--sh-sm);
}
.dark .card-quick { color: var(--bg); }
.card:hover .card-quick {
  opacity: 1;
  transform: scale(1);
}
.card-quick svg {
  width: 14px; height: 14px;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
}

/* Card body */
.card-body {
  padding: 20px 20px 18px;
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 0;
}

.card-cat {
  font-size: .67rem;
  font-weight: 600;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 7px;
}

.card-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.12rem;
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -.02em;
  color: var(--ink);
  display: block;
  margin-bottom: 10px;
  transition: color .18s;
}
.card-name:hover { color: var(--gold); }

.card-hook {
  font-size: .84rem;
  line-height: 1.65;
  color: var(--muted);
  margin-bottom: 16px;
  flex: 1;
  font-weight: 300;
  letter-spacing: -.005em;
}
.card-hook b {
  color: var(--ink-3);
  font-weight: 500;
}

/* Rating row */
.card-rating {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 14px;
  font-size: .78rem;
  color: var(--muted);
}
.card-stars {
  color: #c4892a;
  font-size: .85rem;
  letter-spacing: -.06em;
  line-height: 1;
}
.dark .card-stars { color: var(--gold-2); }

/* Divider */
.card-div {
  height: 1px;
  background: var(--divider);
  margin: 0 0 14px;
}

/* CTA area */
.card-cta { display: flex; flex-direction: column; gap: 8px; }

.btn-amz {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--cta);
  color: var(--cta-fg);
  padding: 12px 18px;
  border-radius: var(--r-md);
  font-size: .875rem;
  font-weight: 600;
  border: none;
  transition: background .2s, transform .2s, box-shadow .2s;
  letter-spacing: -.01em;
  box-shadow: var(--sh-xs);
}
.btn-amz:hover {
  background: var(--cta-hover);
  transform: translateY(-1px);
  box-shadow: var(--sh-sm);
}
.btn-amz .amz-wordmark {
  font-style: italic;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: -.02em;
}
.btn-amz svg {
  width: 13px; height: 13px;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
  flex-shrink: 0;
}

.btn-detail {
  display: block;
  text-align: center;
  font-size: .79rem;
  font-weight: 500;
  color: var(--muted);
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  transition: all .2s;
  letter-spacing: -.01em;
}
.btn-detail:hover {
  color: var(--gold);
  border-color: var(--gold-line);
  background: var(--gold-dim);
}

/* ─── BLOG LISTING ───────────────────────────────── */
.blog-wrap {
  max-width: 1600px;
  margin: 52px auto 0;
  padding: 0 52px;
}

/* Featured post */
.blog-feat {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  border-radius: var(--r-xl);
  overflow: hidden;
  background: var(--card);
  border: 1px solid var(--border);
  box-shadow: var(--sh-md);
  margin-bottom: 64px;
  transition: box-shadow .35s, transform .35s var(--ease-spring);
  color: inherit;
}
.blog-feat:hover {
  box-shadow: var(--sh-xl);
  transform: translateY(-4px);
}
.blog-feat-visual {
  background: var(--bg-2);
  min-height: 360px;
  overflow: hidden;
  position: relative;
}
.blog-feat-visual img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform .6s cubic-bezier(.25,.46,.45,.94);
}
.blog-feat:hover .blog-feat-visual img { transform: scale(1.04); }
.blog-feat-visual-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 5rem;
  background: linear-gradient(135deg, var(--bg-2), var(--bg-3));
}
.blog-feat-body {
  padding: clamp(32px, 4vw, 56px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 18px;
}
.blog-feat-label {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: .67rem;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--gold);
}
.blog-feat-label::before {
  content: '';
  display: block;
  width: 16px;
  height: 1px;
  background: var(--gold);
}
.blog-feat-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(1.6rem, 2.8vw, 2.2rem);
  font-weight: 600;
  line-height: 1.12;
  letter-spacing: -.04em;
  color: var(--ink);
}
.blog-feat-desc {
  font-size: .92rem;
  line-height: 1.72;
  color: var(--muted);
  font-weight: 300;
}
.blog-feat-cta {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: .84rem;
  font-weight: 600;
  color: var(--gold);
  margin-top: 4px;
  padding-bottom: 2px;
  border-bottom: 1px solid var(--gold-line);
  width: fit-content;
  transition: gap .2s, border-color .2s;
  letter-spacing: -.01em;
}
.blog-feat-cta:hover { gap: 16px; border-color: var(--gold); }

/* Blog grid */
.blog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 20px;
}
.blog-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r-xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform .3s var(--ease-spring), box-shadow .3s ease;
  box-shadow: var(--sh-xs);
  color: inherit;
}
.blog-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--sh-lg);
}
.blog-card-thumb {
  height: 186px;
  overflow: hidden;
  position: relative;
  background: linear-gradient(135deg, var(--bg-2), var(--bg-3));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
}
.blog-card-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  inset: 0;
  transition: transform .5s cubic-bezier(.25,.46,.45,.94);
}
.blog-card-thumb img.product-img {
  object-fit: contain;
  padding: 20px;
}
.blog-card:hover .blog-card-thumb img { transform: scale(1.06); }
.blog-card-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  flex: 1;
}
.blog-card-date {
  font-size: .67rem;
  font-weight: 700;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: var(--gold);
  display: flex;
  align-items: center;
  gap: 8px;
}
.blog-card-date::before {
  content: '';
  display: block;
  width: 14px;
  height: 1px;
  background: var(--gold);
}
.blog-card-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.18rem;
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -.025em;
  color: var(--ink);
}
.blog-card-desc {
  font-size: .84rem;
  line-height: 1.65;
  color: var(--muted);
  flex: 1;
  font-weight: 300;
}
.blog-card-link {
  font-size: .79rem;
  font-weight: 600;
  color: var(--gold);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  transition: gap .2s;
}
.blog-card:hover .blog-card-link { gap: 10px; }

/* ─── BLOG PROSE ─────────────────────────────────── */
.blog-prose {
  font-size: 1.02rem;
  line-height: 1.88;
  color: var(--ink-3);
  font-weight: 300;
  letter-spacing: -.005em;
}
.blog-prose h2 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.9rem;
  font-weight: 600;
  color: var(--ink);
  margin: 56px 0 18px;
  letter-spacing: -.04em;
  line-height: 1.15;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--divider);
}
.blog-prose h3 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.45rem;
  font-weight: 600;
  color: var(--ink);
  margin: 40px 0 14px;
  letter-spacing: -.03em;
}
.blog-prose h4 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--ink);
  margin: 30px 0 10px;
}
.blog-prose p { margin-bottom: 22px; }
.blog-prose a { color: var(--gold); font-weight: 500; border-bottom: 1px solid var(--gold-line); transition: border-color .2s; }
.blog-prose a:hover { border-color: var(--gold); }
.blog-prose strong { color: var(--ink-2); font-weight: 600; }
.blog-prose ul,.blog-prose ol { margin: 0 0 26px; padding-left: 0; list-style: none; }
.blog-prose li { padding-left: 24px; position: relative; margin-bottom: 10px; line-height: 1.75; }
.blog-prose ul li::before { content: ''; position: absolute; left: 0; top: 12px; width: 6px; height: 6px; border-radius: 50%; background: var(--gold); }
.blog-prose ol { counter-reset: ol; }
.blog-prose ol li { counter-increment: ol; }
.blog-prose ol li::before { content: counter(ol); position: absolute; left: 0; top: 3px; font-size: .72rem; font-weight: 700; color: var(--gold); font-family: 'DM Sans', sans-serif; }
.blog-prose img { width: 100%; border-radius: var(--r-lg); margin: 40px 0; box-shadow: var(--sh-md); }
.blog-prose blockquote {
  border-left: 3px solid var(--gold);
  margin: 40px 0;
  padding: 20px 28px;
  background: var(--gold-dim);
  border-radius: 0 var(--r-md) var(--r-md) 0;
  font-style: italic;
  color: var(--muted);
  font-size: 1.08rem;
  font-family: 'Cormorant Garamond', serif;
  font-weight: 400;
}
.blog-prose table { width: 100%; border-collapse: collapse; margin: 34px 0; font-size: .92rem; }
.blog-prose th { background: var(--bg-2); padding: 13px 18px; text-align: left; font-weight: 600; color: var(--ink); border-bottom: 2px solid var(--border-2); font-family: 'DM Sans', sans-serif; letter-spacing: -.01em; font-size: .84rem; }
.blog-prose td { padding: 12px 18px; border-bottom: 1px solid var(--divider); color: var(--ink-3); }
.blog-prose tr:last-child td { border-bottom: none; }

/* ─── SIMILAR PRODUCTS ───────────────────────────── */
.similar-sec {
  max-width: 1600px;
  margin: 72px auto 0;
  padding: 0 52px;
}
.similar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 28px;
}
.sim-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
  display: block;
  transition: transform .26s var(--ease-spring), box-shadow .26s ease;
  box-shadow: var(--sh-xs);
  color: inherit;
}
.sim-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--sh-md);
}
.sim-img {
  aspect-ratio: 1;
  background: var(--bg-2);
  overflow: hidden;
}
.sim-img img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 14px;
  transition: transform .4s ease;
}
.sim-card:hover .sim-img img { transform: scale(1.07); }
.sim-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: .9rem;
  font-weight: 600;
  color: var(--ink-3);
  line-height: 1.35;
  padding: 12px 14px;
  letter-spacing: -.015em;
}

/* ─── PRODUCT DETAIL ─────────────────────────────── */
.pd-wrap {
  max-width: 1100px;
  margin: 52px auto 0;
  padding: 0 52px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: start;
}
.pd-gallery {
  position: sticky;
  top: 84px;
}
.pd-img-main {
  background: var(--bg-2);
  border-radius: var(--r-xl);
  overflow: hidden;
  aspect-ratio: 1;
  border: 1px solid var(--border);
  box-shadow: var(--sh-md);
}
.pd-img-main img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 36px;
  display: block;
}
.pd-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-top: 4px;
}
.pd-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: .75rem;
  font-weight: 500;
  color: var(--muted);
  flex-wrap: wrap;
}
.pd-breadcrumb a { color: var(--gold); transition: opacity .2s; }
.pd-breadcrumb a:hover { opacity: .78; }
.pd-breadcrumb span { opacity: .4; }
.pd-cat-tag {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-size: .68rem;
  font-weight: 700;
  letter-spacing: .17em;
  text-transform: uppercase;
  color: var(--gold);
}
.pd-cat-tag::before {
  content: '';
  display: block;
  width: 18px;
  height: 1px;
  background: var(--gold);
}
.pd-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(1.7rem, 3.2vw, 2.5rem);
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -.04em;
  color: var(--ink);
}
.pd-hook {
  font-size: 1rem;
  line-height: 1.75;
  color: var(--muted);
  font-weight: 300;
}
.pd-hook b { color: var(--ink-3); font-weight: 500; }
.pd-divider {
  height: 1px;
  background: var(--divider);
}
.pd-price-note {
  background: var(--gold-dim);
  border: 1px solid var(--gold-line);
  border-radius: var(--r-md);
  padding: 13px 18px;
  font-size: .84rem;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 10px;
  font-style: italic;
}
.btn-pd-amz {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: var(--cta);
  color: var(--cta-fg);
  padding: 18px 32px;
  border-radius: var(--r-pill);
  font-size: 1rem;
  font-weight: 600;
  transition: background .2s, transform .2s, box-shadow .2s;
  box-shadow: var(--sh-sm);
  letter-spacing: -.02em;
}
.btn-pd-amz:hover {
  background: var(--cta-hover);
  transform: translateY(-2px);
  box-shadow: var(--sh-md);
}
.btn-pd-amz em { font-style: italic; font-weight: 800; font-size: 1.1em; }
.btn-pd-amz svg { width: 15px; height: 15px; stroke: currentColor; fill: none; stroke-width: 2; }
.pd-trust-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.pd-trust-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: .76rem;
  color: var(--muted);
  font-weight: 500;
}
.pd-trust-item svg {
  width: 14px; height: 14px;
  stroke: var(--gold);
  fill: none;
  stroke-width: 2;
  flex-shrink: 0;
}

/* ─── PAGINATION ─────────────────────────────────── */
.pager {
  max-width: 1600px;
  margin: 56px auto;
  padding: 0 52px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}
.pager a {
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--ink-3);
  padding: 11px 28px;
  border-radius: var(--r-pill);
  font-size: .875rem;
  font-weight: 600;
  transition: all .2s;
  letter-spacing: -.01em;
  box-shadow: var(--sh-xs);
}
.pager a:hover {
  background: var(--cta);
  color: var(--cta-fg);
  border-color: var(--cta);
  box-shadow: var(--sh-sm);
  transform: translateY(-1px);
}

/* ─── LEGAL ARTICLES ─────────────────────────────── */
.legal-article {
  max-width: 820px;
  margin: 52px auto;
  padding: 0 52px 80px;
}
.legal-article h2 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.65rem;
  font-weight: 600;
  color: var(--ink);
  margin: 48px 0 16px;
  letter-spacing: -.04em;
}
.legal-article h3 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--ink-2);
  margin: 28px 0 10px;
}
.legal-article p {
  font-size: .94rem;
  line-height: 1.82;
  color: var(--ink-3);
  margin-bottom: 18px;
  font-weight: 300;
}
.legal-header-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 28px 32px;
  margin-bottom: 36px;
  box-shadow: var(--sh-xs);
}
.legal-contact-card {
  background: var(--gold-dim);
  border: 1px solid var(--gold-line);
  border-radius: var(--r-lg);
  padding: 20px 24px;
  margin-top: 18px;
}

/* ─── FOOTER ─────────────────────────────────────── */
.site-footer {
  margin-top: 100px;
  background: var(--bg-2);
  border-top: 1px solid var(--border);
}
.footer-inner {
  max-width: 1600px;
  margin: 0 auto;
  padding: 60px 52px 40px;
}
.footer-top {
  display: grid;
  grid-template-columns: 2.2fr 1fr 1fr;
  gap: 60px;
  margin-bottom: 48px;
}
.footer-brand {}
.footer-logo {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -.03em;
  margin-bottom: 14px;
  display: flex;
  align-items: baseline;
  gap: 2px;
}
.footer-logo em { color: var(--gold); font-style: italic; }
.footer-desc {
  font-size: .87rem;
  line-height: 1.78;
  color: var(--muted);
  max-width: 300px;
  font-weight: 300;
}
.footer-tagline {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: .72rem;
  font-weight: 600;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--gold);
}
.footer-tagline::before {
  content: '';
  display: block;
  width: 16px;
  height: 1px;
  background: var(--gold);
}
.footer-col-title {
  font-size: .67rem;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 18px;
}
.footer-col a {
  display: block;
  font-size: .875rem;
  color: var(--ink-3);
  margin-bottom: 10px;
  transition: color .2s, padding-left .2s;
  font-weight: 400;
  letter-spacing: -.01em;
}
.footer-col a:hover { color: var(--gold); padding-left: 5px; }
.footer-divider {
  height: 1px;
  background: var(--border);
  margin-bottom: 28px;
}
.footer-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.footer-legal {
  font-size: .76rem;
  color: var(--muted);
  line-height: 1.65;
  font-weight: 300;
}
.footer-amz-note {
  font-size: .73rem;
  color: var(--muted-2);
  font-style: italic;
}

/* ─── SEARCH OVERLAY ─────────────────────────────── */
#search-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(20,15,12,0.80);
  backdrop-filter: blur(12px);
  z-index: 500;
  padding: 80px 24px 40px;
  overflow-y: auto;
}
#search-overlay.open {
  display: block;
  animation: fadeUp .22s var(--ease-out);
}
@keyframes fadeUp {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.search-panel {
  max-width: 1100px;
  margin: 0 auto;
  background: var(--bg);
  border-radius: var(--r-xl);
  padding: 36px;
  position: relative;
  box-shadow: var(--sh-xl);
  animation: panelIn .26s var(--ease-out);
}
@keyframes panelIn {
  from { opacity: 0; transform: translateY(16px) scale(.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.search-panel-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.search-panel-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.65rem;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -.04em;
}
.search-close-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--card);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  color: var(--ink-3);
  transition: all .2s;
}
.search-close-btn:hover {
  background: var(--gold-dim);
  border-color: var(--gold-line);
}
.search-count-txt {
  font-size: .84rem;
  color: var(--muted);
  margin-bottom: 24px;
  font-weight: 300;
}
.search-res-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 16px;
}

/* ─── COOKIE BAR ─────────────────────────────────── */
#cookie-bar {
  display: none;
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--card);
  border: 1px solid var(--border-2);
  border-radius: var(--r-xl);
  padding: 18px 24px;
  box-shadow: var(--sh-xl);
  z-index: 1000;
  max-width: 580px;
  width: calc(100% - 32px);
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}
#cookie-bar.show { display: flex; animation: cookiePop .32s var(--ease-out); }
@keyframes cookiePop {
  from { opacity: 0; transform: translateX(-50%) translateY(20px); }
  to   { opacity: 1; transform: translateX(-50%) translateY(0); }
}
.cookie-text {
  flex: 1;
  min-width: 180px;
  font-size: .82rem;
  color: var(--muted);
  line-height: 1.6;
  font-weight: 300;
}
.cookie-text a { color: var(--gold); font-weight: 500; }
.cookie-btns { display: flex; gap: 8px; flex-shrink: 0; }
.btn-cookie-ok {
  background: var(--cta);
  color: var(--cta-fg);
  border: none;
  border-radius: var(--r-md);
  padding: 9px 18px;
  font-size: .82rem;
  font-weight: 600;
  font-family: inherit;
  transition: opacity .2s;
}
.btn-cookie-ok:hover { opacity: .82; }
.btn-cookie-ess {
  background: transparent;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 9px 14px;
  font-size: .82rem;
  font-weight: 500;
  font-family: inherit;
  transition: all .2s;
}
.btn-cookie-ess:hover {
  border-color: var(--gold-line);
  color: var(--gold);
}

/* ─── SCROLL ANIMATION ───────────────────────────── */
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity .65s var(--ease-out), transform .65s var(--ease-out);
}
.reveal.in-view {
  opacity: 1;
  transform: translateY(0);
}

/* ─── RESPONSIVE ─────────────────────────────────── */
@media (max-width: 1200px) {
  .hero { grid-template-columns: 1fr; }
  .hero-visual { display: none; }
  .hero-h1 { font-size: clamp(2.6rem, 6vw, 4rem); }
  .footer-top { grid-template-columns: 1fr 1fr; gap: 36px; }
  .blog-feat { grid-template-columns: 1fr; }
  .blog-feat-visual { min-height: 240px; }
  .pd-wrap { grid-template-columns: 1fr; padding: 0 32px; }
  .pd-gallery { position: static; }
}
@media (max-width: 768px) {
  .nav-inner { padding: 0 20px; height: 60px; }
  .nav-links, .nav-search { display: none; }
  #hamburger { display: flex; }

  .hero { padding: 32px 20px 20px; }
  .hero-h1 { font-size: 2.4rem; }
  .hero-sub { font-size: .95rem; }
  .hero-stats { gap: 20px; }

  .grid { padding: 0 16px; grid-template-columns: 1fr; gap: 16px; }
  .blog-grid { padding: 0 16px; grid-template-columns: 1fr; }
  .blog-wrap { padding: 0 16px; }
  .cat-rail { padding: 0 16px; }
  .sec-hdr { padding: 0 16px; }
  .affil-strip { padding: 0 16px 12px; }
  .similar-sec { padding: 0 16px; }
  .pager { padding: 0 16px; }
  .footer-inner { padding: 40px 20px 32px; }
  .footer-top { grid-template-columns: 1fr; gap: 28px; }
  .footer-bottom { flex-direction: column; align-items: flex-start; }
  .legal-article { padding: 0 20px 60px; }
  .pd-wrap { padding: 0 16px; gap: 28px; margin-top: 28px; }
  .cookie-btns { width: 100%; }
  .btn-cookie-ok, .btn-cookie-ess { flex: 1; text-align: center; }
  .blog-feat-body { padding: 28px 22px; }
  .hero-actions { gap: 10px; }
}
@media (max-width: 480px) {
  .hero-h1 { font-size: 2rem; }
  .similar-grid { grid-template-columns: repeat(2, 1fr); }
  .search-panel { padding: 24px 20px; }
  .grid { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
}

/* ─── SCROLLBAR ──────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted-2); }

/* ─── SELECTION ──────────────────────────────────── */
::selection { background: var(--gold-glow); color: var(--ink); }
</style>"""


# ============================================================================
# BASE HTML TEMPLATE — ELITE v5.0
# ============================================================================

BASE_HTML = """<!DOCTYPE html>
<html lang="en-GB" class="">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="author" content="FyboBuybo">

<title>{{ title }}</title>
<meta name="description" content="{{ description | truncate(155,true,'...') }}">
<link rel="canonical" href="{{ canonical_url }}">
{% if prev_page_url %}<link rel="prev" href="{{ prev_page_url }}">{% endif %}
{% if next_page_url %}<link rel="next" href="{{ next_page_url }}">{% endif %}

<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description | truncate(200,true,'...') }}">
<meta property="og:type" content="website">
<meta property="og:url" content="{{ canonical_url }}">
<meta property="og:site_name" content="FyboBuybo">
<meta property="og:locale" content="en_GB">
<meta property="og:image" content="{% if products and products|length > 0 and products[0].image %}{{ products[0].image }}{% else %}{{ SITE_URL }}/static/og-default.jpg{% endif %}">
<meta name="google-site-verification" content="googleb2fd2d2e239922f5">
<meta name="twitter:card" content="summary_large_image">

<script async src="https://www.googletagmanager.com/gtag/js?id=G-C1YNKZS6PG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-C1YNKZS6PG');</script>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://m.media-amazon.com">

{% if structured_data %}<script type="application/ld+json">{{ structured_data|safe }}</script>{% endif %}
{% if breadcrumb_schema %}<script type="application/ld+json">{{ breadcrumb_schema|safe }}</script>{% endif %}

{{ css|safe }}
</head>
<body>

<!-- ═══ TICKER RIBBON ═══════════════════════════════════════════ -->
<div class="ribbon" aria-hidden="true" role="marquee">
  <div class="ribbon-track">
    {% for _ in range(2) %}
    <span>Curated UK Gifts</span><span class="sep">✦</span>
    <span>Updated Daily</span><span class="sep">✦</span>
    <span>Thoughtfully Picked</span><span class="sep">✦</span>
    <span>Loved by UK Shoppers</span><span class="sep">✦</span>
    <span>Best Sellers 2026</span><span class="sep">✦</span>
    {% endfor %}
  </div>
</div>

<!-- ═══ NAVIGATION ══════════════════════════════════════════════ -->
<header class="site-nav" id="site-nav">
  <div class="nav-inner">

    <a href="/" class="nav-logo" aria-label="FyboBuybo Home">
      <span class="logo-fybo">Fybo</span><span class="logo-dot"></span><span class="logo-buybo">Buybo</span>
    </a>

    <nav class="nav-links" aria-label="Primary navigation">
      <a href="/">Home</a>
      <a href="/blog">Blog</a>

      <div class="nav-drop">
        <button class="nav-drop-btn" type="button" aria-expanded="false" aria-haspopup="true">
          Categories
          <svg class="drop-arrow" viewBox="0 0 12 12"><path d="M2 4l4 4 4-4"/></svg>
        </button>
        <div class="nav-drop-menu" role="menu">
          {% for cat in nav_items.categories %}
          <a href="/category/{{ slugify(cat) }}" role="menuitem">{{ cat }}</a>
          {% endfor %}
        </div>
      </div>

      {% if nav_items.seasons %}
      <div class="nav-drop">
        <button class="nav-drop-btn" type="button" aria-expanded="false" aria-haspopup="true">
          Seasonal
          <svg class="drop-arrow" viewBox="0 0 12 12"><path d="M2 4l4 4 4-4"/></svg>
        </button>
        <div class="nav-drop-menu" role="menu">
          {% for season in nav_items.seasons %}
          <a href="/season/{{ slugify(season) }}" role="menuitem">{{ season }}</a>
          {% endfor %}
        </div>
      </div>
      {% endif %}
    </nav>

    <div class="nav-right">
      <div class="nav-search" role="search">
        <div class="nav-search-wrap">
          <input type="search" id="search-input" placeholder="Search gifts…" aria-label="Search gifts" autocomplete="off" spellcheck="false">
          <svg class="nav-search-icon" viewBox="0 0 16 16">
            <circle cx="6.5" cy="6.5" r="4.5"/><path d="M10 10l3.5 3.5"/>
          </svg>
        </div>
      </div>

      <button class="nav-icon-btn" id="theme-btn" aria-label="Toggle colour theme">
        <svg id="icon-sun" viewBox="0 0 24 24" stroke-width="1.8">
          <circle cx="12" cy="12" r="4"/>
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
        </svg>
        <svg id="icon-moon" viewBox="0 0 24 24" stroke-width="1.8" style="display:none">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>

      <button id="hamburger" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu">
        <span></span><span></span><span></span>
      </button>
    </div>

  </div>
</header>

<!-- ═══ MOBILE DRAWER ═══════════════════════════════════════════ -->
<div id="mobile-menu" role="dialog" aria-modal="true" aria-label="Navigation menu">
  <div class="mm-primary">
    <a href="/" class="mm-link" tabindex="-1">Home</a>
    <a href="/blog" class="mm-link" tabindex="-1">Blog</a>
  </div>

  {% if nav_items.categories %}
  <div class="mm-section">
    <div class="mm-label">Categories</div>
    <div class="mm-pills">
      {% for cat in nav_items.categories %}
      <a href="/category/{{ slugify(cat) }}" class="mm-pill">{{ cat }}</a>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if nav_items.seasons %}
  <div class="mm-section">
    <div class="mm-label">Seasonal Collections</div>
    <div class="mm-pills">
      {% for season in nav_items.seasons %}
      <a href="/season/{{ slugify(season) }}" class="mm-pill">{{ season }}</a>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <div class="mm-search-wrap">
    <svg viewBox="0 0 16 16"><circle cx="6.5" cy="6.5" r="4.5"/><path d="M10 10l3.5 3.5"/></svg>
    <input type="search" id="mobile-search-input" placeholder="Search gifts…" aria-label="Search" autocomplete="off">
  </div>
</div>

<!-- ═══ HERO (listing pages only) ══════════════════════════════ -->
{% if heading %}
<section class="hero" aria-label="Page header">
  <div class="hero-content">
    <div class="hero-eyebrow">Updated daily · Handpicked for UK shoppers</div>
    <h1 class="hero-h1">{{ heading|replace("FyboBuybo – ", "")|replace(" Gifts", "")|safe }}<em> Gifts</em>
      <span class="line-2">{{ "Loved across the UK" }}</span>
    </h1>
    <p class="hero-sub">{{ subtitle }}</p>
    <div class="hero-actions">
      {% if request.path == '/blog' or request.path.startswith('/blog/') %}
      <a href="/" class="btn-primary">
        Browse gift picks
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </a>
      <a href="#articles" class="btn-ghost">Read guides →</a>
      {% else %}
      <a href="#picks" class="btn-primary">
        Browse picks
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </a>
      <a href="/blog" class="btn-ghost">Gift guides →</a>
      {% endif %}
    </div>
    <div class="hero-stats">
      <div>
        {% if request.path == '/blog' or request.path.startswith('/blog/') %}
        <div class="hero-stat-num">{{ total_posts if total_posts else '' }}<span>+</span></div>
        <div class="hero-stat-label">Gift guides</div>
        {% else %}
        <div class="hero-stat-num">{{ products|length if products else '' }}<span>+</span></div>
        <div class="hero-stat-label">Curated picks</div>
        {% endif %}
      </div>
      <div>
        <div class="hero-stat-num"><span>✦</span></div>
        <div class="hero-stat-label">Refreshed daily</div>
      </div>
      <div>
        <div class="hero-stat-num"><span>UK</span></div>
        <div class="hero-stat-label">Gift ideas</div>
      </div>
    </div>
  </div>

  {% if products and products|length > 1 %}
  <div class="hero-visual" aria-hidden="true">
    <div class="hero-img-main">
      <img src="{{ products[0].image }}" alt="{{ products[0].name }}" loading="eager" width="480" height="480">
    </div>
    <div class="hero-img-float">
      <img src="{{ products[1].image }}" alt="{{ products[1].name }}" loading="eager" width="240" height="240">
    </div>
    <div class="hero-ornament">
      <span>New<br>Daily</span>
    </div>
  </div>
  {% endif %}
</section>
{% endif %}

<!-- ═══ AFFILIATE DISCLOSURE ════════════════════════════════════ -->
<div class="affil-strip">
  <div class="affil-inner">
    <svg class="affil-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
    <span><strong>Affiliate Disclosure:</strong> We earn a small commission on purchases through our links — at no extra cost to you. <a href="/privacy-policy">Learn more →</a></span>
  </div>
</div>

<!-- ═══ CATEGORY RAIL (homepage) ════════════════════════════════ -->
{% if request.path == '/' and nav_items.categories %}
<nav class="cat-rail" aria-label="Browse categories">
  {% for cat in nav_items.categories %}
  <a href="/category/{{ slugify(cat) }}" class="cat-chip">{{ cat }}</a>
  {% endfor %}
</nav>
{% endif %}

<!-- ═══ INLINE CONTENT (blog / product / legal) ════════════════ -->
{% if content %}{{ content|safe }}{% endif %}

<!-- ═══ SECTION HEADER ══════════════════════════════════════════ -->
{% if products and products|length > 1 %}
<div class="sec-hdr reveal" id="picks">
  <div>
    <div class="sec-eyebrow">Hand-picked for you</div>
    <h2 class="sec-title">Today's <em>Top Picks</em></h2>
  </div>
  <a href="/blog" class="sec-view-all">Gift guides →</a>
</div>
{% endif %}

<!-- ═══ PRODUCT GRID ═════════════════════════════════════════════ -->
{% if products %}
<div class="grid" role="list">
  {% for p in products %}
  {% set price_info = get_product_price_rating(p) %}
  <article class="card reveal" style="animation-delay:{{ loop.index0 * 0.04 }}s" role="listitem" itemscope itemtype="https://schema.org/Product">
    <div class="card-img">
      <span class="card-badge">{{ p.category }}</span>
      <a href="/product/{{ slugify(p.name) }}" tabindex="-1" aria-hidden="true">
        <img src="{{ p.image }}" alt="{{ p.name }}" loading="lazy" width="400" height="400" itemprop="image">
      </a>
      <div class="card-quick" aria-hidden="true">
        <svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
      </div>
    </div>

    <div class="card-body">
      <div class="card-cat">{{ p.category }}</div>
      <a href="/product/{{ slugify(p.name) }}" class="card-name" itemprop="name">{{ shorten_product_name(p.name) }}</a>
      <p class="card-hook" itemprop="description">{{ p.hook|safe }}</p>

      {% if price_info.rating %}
      <div class="card-rating">
        <span class="card-stars">{% for i in range(price_info.rating|int) %}★{% endfor %}</span>
        <span>Popular pick</span>
      </div>
      {% endif %}

      <div class="card-div"></div>
      {% if p.date_added %}
      <div style="font-size:.7rem;color:var(--muted-2);margin-bottom:10px;letter-spacing:.02em" itemprop="dateModified" content="{{ p.date_added }}">Updated {{ p.date_added }}</div>
      {% endif %}
      <div class="card-cta">
        {% if p.url %}
        <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored noopener" class="btn-amz"
           aria-label="View {{ p.name }} on Amazon">
          View on <span class="amz-wordmark">amazon</span>
          <svg viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        </a>
        {% endif %}
        <a href="/product/{{ slugify(p.name) }}" class="btn-detail">Full details →</a>
      </div>
    </div>
  </article>
  {% endfor %}
</div>
{% endif %}

<!-- ═══ SIMILAR PRODUCTS ═════════════════════════════════════════ -->
{% if similar_products %}
<section class="similar-sec reveal" aria-label="Similar products">
  <div class="sec-hdr" style="padding:0;margin:0 0 0">
    <div>
      <div class="sec-eyebrow">You might also like</div>
      <h2 class="sec-title">More <em>Great Picks</em></h2>
    </div>
  </div>
  <div class="similar-grid">
    {% for s in similar_products %}
    <a href="/product/{{ slugify(s.name) }}" class="sim-card" aria-label="{{ s.name }}">
      <div class="sim-img">
        <img src="{{ s.image }}" alt="{{ s.name }}" loading="lazy" width="200" height="200">
      </div>
      <div class="sim-name">{{ shorten_product_name(s.name, 60) }}</div>
    </a>
    {% endfor %}
  </div>
</section>
{% endif %}

<!-- ═══ PAGINATION ════════════════════════════════════════════════ -->
{% if next_page_url or prev_page_url %}
<nav class="pager" aria-label="Pagination">
  {% if prev_page_url %}<a href="{{ prev_page_url }}" rel="prev">← Previous</a>{% endif %}
  {% if next_page_url %}<a href="{{ next_page_url }}" rel="next">Next →</a>{% endif %}
</nav>
{% endif %}

<!-- ═══ FOOTER ════════════════════════════════════════════════════ -->
<footer class="site-footer" role="contentinfo">
  <div class="footer-inner">
    <div class="footer-top">
      <div class="footer-brand">
        <div class="footer-logo">Fybo<em>Buybo</em></div>
        <p class="footer-desc">Thoughtfully curated UK gifts, updated every day. We do the research so you find the perfect present — every time.</p>
        <div class="footer-tagline">Trusted by UK shoppers</div>
      </div>
      <div class="footer-col">
        <div class="footer-col-title">Explore</div>
        <a href="/">Home</a>
        <a href="/blog">Gift Guides</a>
        {% for cat in nav_items.categories[:5] %}
        <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
        {% endfor %}
      </div>
      <div class="footer-col">
        <div class="footer-col-title">Legal</div>
        <a href="/privacy-policy">Privacy Policy</a>
        <a href="/terms">Terms of Service</a>
        <a href="mailto:infofybobuybo@gmail.com">Contact Us</a>
      </div>
    </div>
    <div class="footer-divider"></div>
    <div class="footer-bottom">
      <p class="footer-legal">© 2026 FyboBuybo. All rights reserved. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. As an Amazon Associate, we earn from qualifying purchases.</p>
      <p class="footer-amz-note">Prices and availability subject to change. Always verify on Amazon.</p>
    </div>
  </div>
</footer>

<!-- ═══ SEARCH OVERLAY ════════════════════════════════════════════ -->
<div id="search-overlay" role="dialog" aria-label="Search results" aria-modal="true" aria-live="polite">
  <div class="search-panel">
    <div class="search-panel-hdr">
      <h2 class="search-panel-title">Search Results</h2>
      <button class="search-close-btn" id="search-close" aria-label="Close search">×</button>
    </div>
    <p class="search-count-txt" id="search-count"></p>
    <div class="search-res-grid" id="search-res-grid"></div>
  </div>
</div>

<!-- ═══ COOKIE CONSENT ════════════════════════════════════════════ -->
<div id="cookie-bar" role="dialog" aria-label="Cookie consent" aria-live="polite">
  <div class="cookie-text">
    We use essential cookies and affiliate tracking to personalise your experience.
    <a href="/privacy-policy">Privacy policy</a>
  </div>
  <div class="cookie-btns">
    <button class="btn-cookie-ok" id="cookie-accept">Accept All</button>
    <button class="btn-cookie-ess" id="cookie-essential">Essential Only</button>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════
     SCRIPTS
     ═══════════════════════════════════════════════════════════════ -->
<script>
// ── THEME ──────────────────────────────────────────────────────
(function() {
  const root = document.documentElement;
  let dark = localStorage.getItem('fybo-dark') === '1';
  function applyTheme(d) {
    root.classList.toggle('dark', d);
    document.getElementById('icon-sun').style.display  = d ? 'none'  : 'block';
    document.getElementById('icon-moon').style.display = d ? 'block' : 'none';
  }
  applyTheme(dark);
  document.getElementById('theme-btn').addEventListener('click', function() {
    dark = !dark;
    localStorage.setItem('fybo-dark', dark ? '1' : '0');
    applyTheme(dark);
  });
})();

// ── NAV SHADOW ON SCROLL ───────────────────────────────────────
(function() {
  const nav = document.getElementById('site-nav');
  function onScroll() {
    nav.classList.toggle('scrolled', window.scrollY > 20);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
})();

// ── HAMBURGER / MOBILE MENU ────────────────────────────────────
(function() {
  const burger = document.getElementById('hamburger');
  const menu   = document.getElementById('mobile-menu');
  burger.addEventListener('click', function() {
    const open = menu.classList.toggle('open');
    burger.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  });
  menu.querySelectorAll('a').forEach(function(a) {
    a.addEventListener('click', function() {
      menu.classList.remove('open');
      burger.classList.remove('open');
      burger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });
  // Close on ESC
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && menu.classList.contains('open')) {
      menu.classList.remove('open');
      burger.classList.remove('open');
      burger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
  });
})();

// ── DESKTOP DROPDOWNS ──────────────────────────────────────────
(function() {
  const drops = document.querySelectorAll('.nav-drop');
  drops.forEach(function(dd) {
    const btn = dd.querySelector('.nav-drop-btn');
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const isOpen = dd.classList.contains('open');
      drops.forEach(function(x) {
        x.classList.remove('open');
        x.querySelector('.nav-drop-btn').setAttribute('aria-expanded', 'false');
      });
      if (!isOpen) {
        dd.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
  document.addEventListener('click', function() {
    drops.forEach(function(dd) {
      dd.classList.remove('open');
      const btn = dd.querySelector('.nav-drop-btn');
      if (btn) btn.setAttribute('aria-expanded', 'false');
    });
  });
})();

// ── SCROLL REVEAL ──────────────────────────────────────────────
(function() {
  const els = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    els.forEach(function(el) { el.classList.add('in-view'); });
    return;
  }
  const io = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
  els.forEach(function(el) { io.observe(el); });
})();

// ── SEARCH ─────────────────────────────────────────────────────
var allProducts = [];
var searchTimer;

async function loadProducts() {
  try {
    const r = await fetch('/api/search-products');
    const d = await r.json();
    allProducts = d.products || [];
  } catch(e) { console.warn('Search preload failed', e); }
}
loadProducts();

function pySlug(t) {
  return t.toLowerCase()
    .replace(/&/g, '-and-')
    .replace(/\s+/g, '-')
    .replace(/[^\w-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
}
function shortName(n, l) {
  l = l || 70;
  if (n.length <= l) return n;
  for (const s of [',','(']) {
    if (n.includes(s)) { const x = n.split(s)[0].trim(); if (x.length <= l) return x; }
  }
  return n.slice(0, l - 1) + '…';
}

const overlay    = document.getElementById('search-overlay');
const countEl    = document.getElementById('search-count');
const resGrid    = document.getElementById('search-res-grid');
const searchInp  = document.getElementById('search-input');
const mSearchInp = document.getElementById('mobile-search-input');

function buildCard(p) {
  return `<article class="card">
    <div class="card-img">
      <span class="card-badge">${p.category||''}</span>
      <a href="/product/${pySlug(p.name)}" tabindex="-1" aria-hidden="true">
        <img src="${p.image||''}" alt="${p.name}" loading="lazy">
      </a>
    </div>
    <div class="card-body">
      <div class="card-cat">${p.category||''}</div>
      <a href="/product/${pySlug(p.name)}" class="card-name">${shortName(p.name)}</a>
      <p class="card-hook">${p.hook||''}</p>
      <div class="card-cta">
        ${p.url ? `<a href="${p.url}" target="_blank" rel="nofollow sponsored noopener" class="btn-amz">
          View on <span class="amz-wordmark">amazon</span></a>` : ''}
        <a href="/product/${pySlug(p.name)}" class="btn-detail">Full details →</a>
      </div>
    </div>
  </article>`;
}

function renderResults(products, q) {
  countEl.textContent = products.length
    ? `${products.length} result${products.length !== 1 ? 's' : ''} for "${q}"`
    : `No results for "${q}"`;
  resGrid.innerHTML = products.length
    ? products.map(buildCard).join('')
    : '<p style="text-align:center;padding:64px 24px;color:var(--muted);font-size:.95rem">No results found — try a different term.</p>';
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeSearch() {
  overlay.classList.remove('open');
  document.body.style.overflow = '';
}

function doSearch(q) {
  clearTimeout(searchTimer);
  const t = q.trim();
  if (t.length < 3) { if (overlay.classList.contains('open')) closeSearch(); return; }
  searchTimer = setTimeout(function() {
    const ql    = t.toLowerCase();
    const words = ql.split(/\s+/).filter(function(w) { return w.length > 0; });
    const scored = allProducts.map(function(p) {
      const name   = (p.name   || '').toLowerCase();
      const cat    = (p.category || '').toLowerCase();
      const hook   = (p.hook   || '').toLowerCase();
      const info   = (p.info   || '').toLowerCase();
      const keys   = (p.keywords || []).join(' ').toLowerCase();
      const season = (p.season || '').toLowerCase();
      let score = 0;
      for (const w of words) {
        if (w.length < 3 && words.length > 1) continue;
        if (name.startsWith(w))            score += 20;
        else if (name.includes(' ' + w))   score += 15;
        else if (name.includes(w) && w.length >= 4) score += 8;
        if (cat === w)                     score += 12;
        else if (cat.includes(w) && w.length >= 4) score += 6;
        if (keys.includes(w) && w.length >= 4)  score += 5;
        if (w.length >= 4) {
          if (hook.includes(w))   score += 3;
          if (info.includes(w))   score += 2;
          if (season.includes(w)) score += 4;
        }
      }
      if (name.includes(ql)) score += 25;
      return { p: p, score: score };
    });
    const hits = scored
      .filter(function(x) { return x.score >= 8; })
      .sort(function(a, b) { return b.score - a.score; })
      .map(function(x) { return x.p; });
    renderResults(hits, t);
  }, 200);
}

// Wire both inputs
searchInp.addEventListener('input', function(e) { doSearch(e.target.value); });
searchInp.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { closeSearch(); searchInp.value = ''; }
});
if (mSearchInp) {
  mSearchInp.addEventListener('input', function(e) { doSearch(e.target.value); });
  mSearchInp.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') { closeSearch(); mSearchInp.value = ''; }
  });
}
document.getElementById('search-close').addEventListener('click', closeSearch);
overlay.addEventListener('click', function(e) { if (e.target === overlay) closeSearch(); });
overlay.addEventListener('click', function(e) { e.stopPropagation(); }, false);
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeSearch(); });

// ── COOKIE CONSENT ─────────────────────────────────────────────
(function() {
  const KEY = 'fybo_consent_v1';
  const bar = document.getElementById('cookie-bar');
  if (!bar) return;
  try { if (!localStorage.getItem(KEY)) setTimeout(function() { bar.classList.add('show'); }, 1200); }
  catch(e) { bar.classList.add('show'); }
  function dismiss(v) {
    try { localStorage.setItem(KEY, v); } catch(e) {}
    bar.classList.remove('show');
  }
  var okBtn  = document.getElementById('cookie-accept');
  var essBtn = document.getElementById('cookie-essential');
  if (okBtn)  okBtn.addEventListener('click',  function() { dismiss('all'); });
  if (essBtn) essBtn.addEventListener('click', function() { dismiss('essential'); });
})();
</script>
</body>
</html>"""


# ============================================================================
# RENDER PAGE
# ============================================================================

def render_page(title, description, heading, subtitle, products=None, page=1,
                page_url=None, similar_products=None, today=None,
                today_formatted=None, article_date=None, content=None, total_posts=None):
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    nav_items = get_nav_items()

    canonical = SITE_URL + request.path.rstrip('/')
    if request.path == '/': canonical = SITE_URL + '/'
    page_num = int(request.args.get("page", 1))
    if page_num > 1: canonical += f"?page={page_num}"

    paged_products, total_pages = [], 1
    if products:
        paged_products, total_items = paginate(products, page)
        total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    next_url = page_url(page + 1) if page_url and page < total_pages else None
    prev_url = page_url(page - 1) if page_url and page > 1 else None

    if not today:
        today = datetime.date.today().isoformat()
        today_formatted = datetime.date.today().strftime("%B %d, %Y")

    structured_data = None
    if paged_products and len(paged_products) == 1:
        structured_data = generate_product_schema(paged_products[0])

    breadcrumb_schema = None
    breadcrumbs = [("Home", "/")]
    if '/category/' in request.path and paged_products:
        breadcrumbs.append((paged_products[0]['category'], request.path))
    elif '/season/' in request.path:
        breadcrumbs.append((request.path.split('/')[-1].replace('-', ' ').title(), request.path))
    elif '/product/' in request.path and paged_products:
        if paged_products[0].get('category'):
            breadcrumbs.append((paged_products[0]['category'], f"/category/{slugify(paged_products[0]['category'])}"))
        breadcrumbs.append((paged_products[0]['name'], request.path))
    elif '/blog' in request.path:
        breadcrumbs.append(("Blog", "/blog"))
        if request.path != '/blog' and '/page/' not in request.path:
            breadcrumbs.append((title.split(' – ')[0], request.path))
    if len(breadcrumbs) > 1:
        breadcrumb_schema = generate_breadcrumb_schema(breadcrumbs)

    return render_template_string(
        BASE_HTML,
        title=title, description=description, heading=heading, subtitle=subtitle,
        products=paged_products, nav_items=nav_items, css=css,
        canonical_url=canonical, SITE_URL=SITE_URL,
        slugify=slugify, shorten_product_name=shorten_product_name,
        similar_products=similar_products or [],
        next_page_url=next_url, prev_page_url=prev_url,
        themes_json=json.dumps(THEMES),
        get_product_price_rating=get_product_price_rating,
        format_price_display=format_price_display,
        format_rating_display=format_rating_display,
        today=today, today_formatted=today_formatted,
        structured_data=structured_data, breadcrumb_schema=breadcrumb_schema,
        article_date=article_date, content=content or "",
        cookie_consent="", total_posts=total_posts
    )


# ============================================================================
# ROUTES (unchanged logic, new HTML from render_page)
# ============================================================================

@app.route("/privacy-policy")
def privacy_policy():
    return render_page(
        title="Privacy Policy – FyboBuybo",
        description="Our commitment to protecting your privacy in accordance with UK GDPR.",
        heading="Privacy Policy", subtitle="How we collect, use, and protect your data",
        content=PRIVACY_POLICY_HTML
    )

@app.route("/terms")
def terms_of_service():
    return render_page(
        title="Terms of Service – FyboBuybo",
        description="Terms and conditions for using FyboBuybo, including affiliate disclosures.",
        heading="Terms of Service", subtitle="Legal terms for using our website",
        content=TERMS_OF_SERVICE_HTML
    )

@app.route("/api/search-products")
def api_search_products():
    all_products = refresh_products(background=True)
    return jsonify({'products': [{
        'name': p['name'], 'category': p.get('category', ''),
        'image': p.get('image', ''), 'hook': p.get('hook', ''),
        'info': p.get('info', ''), 'keywords': p.get('keywords', []),
        'season': p.get('season', ''), 'url': p.get('url', '')
    } for p in all_products]})

@app.route("/")
def home():
    products = refresh_products(background=True)[:ITEMS_PER_PAGE]
    return render_page(
        title="FyboBuybo – Trending UK Gifts & Popular Presents 2026",
        description="Discover today's trending UK gifts and popular presents across toys, beauty, electronics, home and more – refreshed daily.",
        heading="FyboBuybo – Trending UK Gifts",
        subtitle="A curated selection of popular gifts and presents, refreshed daily for UK shoppers.",
        products=products
    )

@app.route("/category/<slug>")
@app.route("/category/<slug>/page/<int:page>")
def category(slug, page=1):
    all_products = refresh_products(background=True)
    filtered = [p for p in all_products if slugify(p.get("category", "")) == slug]
    if not filtered: abort(404)
    cat_name = filtered[0]["category"]
    def page_url(p): return url_for("category", slug=slug, page=p)
    return render_page(
        title=f"Best {cat_name} Gifts UK 2026 | Trending Picks – FyboBuybo",
        description=f"Explore popular {cat_name.lower()} gifts loved by UK shoppers – updated daily.",
        heading=f"Best {cat_name} Gifts UK 2026",
        subtitle=f"Hand-picked {cat_name.lower()} loved by UK shoppers.",
        products=filtered, page=page, page_url=page_url
    )

@app.route("/season/<season_slug>")
@app.route("/season/<season_slug>/page/<int:page>")
def seasonal_collection(season_slug, page=1):
    all_products = refresh_products(background=True)
    norm_slug = normalize_for_match(season_slug)
    filtered = [p for p in all_products if p.get("season") and any(norm_slug in normalize_for_match(s.strip()) for s in p["season"].split(","))]
    if not filtered: abort(404)
    filtered.sort(key=lambda p: p.get("date_added", "2000-01-01"), reverse=True)
    season_name = season_slug.replace('-', ' ').title()
    def page_url(p): return url_for("seasonal_collection", season_slug=season_slug, page=p)
    title_season = season_name + (" Gifts" if "day" in season_name.lower() or "christmas" in season_name.lower() else "")
    return render_page(
        title=f"Best {title_season} 2026 – FyboBuybo",
        description=f"Discover the most popular {season_name.lower()} gifts for UK shoppers in 2026.",
        heading=title_season, subtitle="Perfect seasonal presents • refreshed every day",
        products=filtered, page=page, page_url=page_url
    )

@app.route("/product/<path:product_slug>")
def product_detail(product_slug):
    all_products = refresh_products(background=True)
    found = next((p for p in all_products if slugify(p["name"]) == product_slug), None)
    if not found: abort(404)

    similar = get_similar_products(found, all_products, limit=6)
    today = datetime.date.today()
    today_formatted = today.strftime("%B %d, %Y")
    price_info = get_product_price_rating(found)

    rating_html = ""
    if price_info.get("rating"):
        stars = "★" * int(float(price_info["rating"]))
        rating_html = f"""<div class="pd-rating-row" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <span style="color:#c4892a;font-size:1.2rem;letter-spacing:-.06em;line-height:1">{stars}</span>
          <span style="font-size:.88rem;color:var(--muted);font-weight:400">Popular pick</span>
          <a href="{found.get('url','')}" target="_blank" rel="nofollow sponsored noopener"
             style="font-size:.82rem;color:var(--gold);font-weight:600;border-bottom:1px solid var(--gold-line)">
            See current ratings →</a>
        </div>"""

    amazon_btn = ""
    if found.get("url"):
        amazon_btn = f"""<a href="{found["url"]}" target="_blank" rel="nofollow sponsored noopener" class="btn-pd-amz">
          View on <em>amazon</em>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/>
          </svg></a>"""

    trust_row = """<div class="pd-trust-row">
      <div class="pd-trust-item">
        <svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        Sold via Amazon UK
      </div>
      <div class="pd-trust-item">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
        Check Amazon for live price
      </div>
      <div class="pd-trust-item">
        <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        Secure checkout on Amazon
      </div>
    </div>"""

    info_html = f'<p class="pd-hook">{found["info"]}</p>' if found.get("info") else ""
    date_html = f'<p style="font-size:.74rem;color:var(--muted-2);margin-top:2px;font-style:italic">Featured {found["date_added"]}</p>' if found.get("date_added") else ""

    content_html = f"""
    <div class="pd-wrap">
      <div class="pd-gallery">
        <div class="pd-img-main">
          <img src="{found["image"]}" alt="{found["name"]}" width="600" height="600">
        </div>
      </div>
      <div class="pd-info">
        <nav class="pd-breadcrumb" aria-label="Breadcrumb">
          <a href="/">Home</a>
          <span>›</span>
          <a href="/category/{slugify(found.get('category',''))}">{found.get('category','')}</a>
          <span>›</span>
          <span style="color:var(--muted)">{shorten_product_name(found['name'], 40)}</span>
        </nav>
        <div class="pd-cat-tag">{found.get('category', '')}</div>
        <h1 class="pd-title">{found["name"]}</h1>
        {rating_html}
        <div class="pd-divider"></div>
        <p class="pd-hook">{found.get("hook", "")}</p>
        {info_html}
        <div class="pd-price-note">💡 Prices change frequently — always check Amazon for the current price before purchasing</div>
        {amazon_btn}
        {trust_row}
        {date_html}
      </div>
    </div>"""

    return render_page(
        title=f"{shorten_product_name(found['name'], 50)} | UK Reviews – FyboBuybo",
        description=f"{found.get('info', '')[:120].rstrip()} – Loved by UK shoppers. Free delivery via Amazon Prime.",
        heading="", subtitle="",
        products=None, similar_products=similar,
        today=today.isoformat(), today_formatted=today_formatted,
        content=content_html
    )


# ============================================================================
# BLOG
# ============================================================================

POSTS_PER_PAGE = 8

def load_blog_posts(page=1):
    posts = [{**v, "slug": k} for k, v in BLOG_POSTS.items()]
    posts.sort(key=lambda x: x.get("date", "1900-01-01"), reverse=True)
    start = (page - 1) * POSTS_PER_PAGE
    paginated = posts[start:start + POSTS_PER_PAGE]
    total_pages = (len(posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    return paginated, total_pages, len(posts)


def get_blog_post_image(post, all_products):
    img_url = post.get("featured_image") or post.get("image")
    img_alt = post.get("featured_image_alt") or post.get("title", "")
    if img_url:
        return (
            f'<img src="{img_url}" alt="{img_alt}" style="width:100%;height:100%;object-fit:cover;position:absolute;inset:0;display:block" onerror="this.style.display=\'none\'">',
            False
        )

    content = post.get("content", "")
    img_match = re.search(r"src='(https://m\.media-amazon\.com/[^']+)'", content)
    if not img_match:
        img_match = re.search(r'src="(https://m\.media-amazon\.com/[^"]+)"', content)
    if img_match:
        return (
            f'<img src="{img_match.group(1)}" alt="{post.get("title","")}" class="product-img" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block" onerror="this.style.display=\'none\'">',
            True
        )

    def fuzz(s):
        return re.sub(r'[^a-z0-9]', '', s.lower()) if s else ''

    if post.get("related_products") and all_products:
        product_map = {}
        for p in all_products:
            if p.get("image"):
                product_map[fuzz(p["name"])] = p
                product_map[fuzz(slugify(p["name"]))] = p
        for rel in post["related_products"]:
            rel_fuzz = fuzz(rel)
            if rel_fuzz in product_map:
                p = product_map[rel_fuzz]
                return (
                    f'<img src="{p["image"]}" alt="{post["title"]}" class="product-img" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block">',
                    True
                )
            for pfuzz, p in product_map.items():
                if len(rel_fuzz) > 5 and (rel_fuzz in pfuzz or pfuzz in rel_fuzz):
                    return (
                        f'<img src="{p["image"]}" alt="{post["title"]}" class="product-img" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block">',
                        True
                    )

    title_lower = post["title"].lower()
    category_hints = {
        "baby": ["baby", "nursery", "infant", "monitor"],
        "yoga": ["sport", "fitness", "health", "wellness"],
        "monitor": ["electronics", "tech", "baby"],
        "candle": ["home", "beauty", "wellbeing"],
        "kitchen": ["kitchen", "home", "cooking"],
        "beauty": ["beauty", "skincare", "personal care"],
        "fitbit": ["electronics", "tech", "fitness"],
        "garmin": ["electronics", "tech", "fitness"],
        "gift": ["toys", "beauty", "home"],
        "book": ["learning", "education", "books"],
    }
    for kw, cats in category_hints.items():
        if kw in title_lower:
            for p in all_products:
                if p.get("image") and any(c.lower() in p.get("category", "").lower() for c in cats):
                    return (
                        f'<img src="{p["image"]}" alt="{post["title"]}" class="product-img" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block">',
                        True
                    )

    return None, False


@app.route("/blog")
@app.route("/blog/page/<int:page>")
def blog_list(page=1):
    paginated, total_pages, total_posts = load_blog_posts(page)
    if not paginated and page > 1: abort(404)

    all_products = refresh_products(background=True)
    featured = paginated[0] if paginated else None
    grid_posts = paginated[1:] if len(paginated) > 1 else paginated

    blog_html = '<div class="blog-wrap">'

    if featured:
        feat_date = datetime.datetime.strptime(featured["date"], "%Y-%m-%d").strftime("%d %B %Y")
        feat_img_html, _ = get_blog_post_image(featured, all_products)

        if feat_img_html:
            feat_visual = f'<div class="blog-feat-visual" style="overflow:hidden;position:relative">{feat_img_html}</div>'
        else:
            feat_visual = '<div class="blog-feat-visual"><div class="blog-feat-visual-placeholder">📖</div></div>'

        blog_html += f"""
        <a href="/blog/{featured["slug"]}" class="blog-feat">
          {feat_visual}
          <div class="blog-feat-body">
            <div class="blog-feat-label">{feat_date} · Featured Guide</div>
            <div class="blog-feat-title">{featured["title"]}</div>
            <div class="blog-feat-desc">{featured.get("description", "")}</div>
            <div class="blog-feat-cta">Read the full guide →</div>
          </div>
        </a>"""

    if grid_posts:
        blog_html += """
        <div class="sec-hdr" id="articles" style="padding:0;margin:0 0 28px">
          <div>
            <div class="sec-eyebrow">All articles</div>
            <h2 class="sec-title">Latest <em>Guides</em></h2>
          </div>
        </div>
        <div class="blog-grid">"""

        for post in grid_posts:
            date_str = datetime.datetime.strptime(post["date"], "%Y-%m-%d").strftime("%d %B %Y")
            post_img_html, is_product = get_blog_post_image(post, all_products)

            if post_img_html:
                thumb = f'<div class="blog-card-thumb" style="position:relative">{post_img_html}</div>'
            else:
                tl = post["title"].lower()
                emoji = "📝"
                if any(w in tl for w in ["gift","present","christmas","birthday"]): emoji = "🎁"
                elif any(w in tl for w in ["home","kitchen","decor"]): emoji = "🏠"
                elif any(w in tl for w in ["beauty","skincare","self-care"]): emoji = "✨"
                elif any(w in tl for w in ["tech","gadget","electronic"]): emoji = "⚡"
                elif any(w in tl for w in ["book","read"]): emoji = "📚"
                elif any(w in tl for w in ["yoga","fitness","health"]): emoji = "🧘"
                elif any(w in tl for w in ["baby","monitor","nursery"]): emoji = "👶"
                thumb = f'<div class="blog-card-thumb">{emoji}</div>'

            blog_html += f"""
            <a href="/blog/{post["slug"]}" class="blog-card">
              {thumb}
              <div class="blog-card-body">
                <div class="blog-card-date">{date_str}</div>
                <div class="blog-card-title">{post["title"]}</div>
                <div class="blog-card-desc">{post.get("description", "")}</div>
                <div class="blog-card-link">Read article →</div>
              </div>
            </a>"""

        blog_html += "</div>"

    if total_pages > 1:
        blog_html += '<div class="pager" style="margin-top:52px;margin-bottom:0">'
        if page > 1: blog_html += f'<a href="{url_for("blog_list", page=page-1)}" rel="prev">← Previous</a>'
        if page < total_pages: blog_html += f'<a href="{url_for("blog_list", page=page+1)}" rel="next">Next →</a>'
        blog_html += "</div>"

    blog_html += "</div>"

    rendered = render_page(
        title="FyboBuybo Blog – Gift Guides, Tips & Inspiration 2026",
        description="Latest UK gift ideas, seasonal guides, home tips and thoughtful present recommendations.",
        heading="FyboBuybo Blog",
        subtitle="Gift guides, trends and inspiration for UK shoppers",
        products=None, page=page,
        total_posts=total_posts,
    )

    insert = rendered.find("<!-- ═══ PRODUCT GRID")
    if insert > -1:
        rendered = rendered[:insert] + blog_html + rendered[insert:]
    else:
        rendered = rendered.replace("</footer>", blog_html + "</footer>", 1)

    return rendered


@app.route("/blog/<slug>")
def blog_detail(slug):
    post = BLOG_POSTS.get(slug)
    if not post: abort(404)

    all_products = refresh_products(background=True)
    related = []
    if post.get("related_products"):
        for ps in post["related_products"]:
            p = next((x for x in all_products if slugify(x["name"]) == ps), None)
            if p: related.append(p)
    if not related:
        related = [p for p in all_products if p["category"] in ["Home & Kitchen", "Electronics"]][:6]

    from jinja2 import Template
    raw_content = post.get("content", "<p>Content coming soon.</p>")
    content_html_body = Template(raw_content).render(slugify=slugify)
    date_str = datetime.datetime.strptime(post.get("date", "2026-01-01"), "%Y-%m-%d").strftime("%d %B %Y")

    content_html = f"""
    <div style="max-width:720px;margin:56px auto 0;padding:0 48px">
      <div style="display:inline-flex;align-items:center;gap:10px;font-size:.68rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--gold);margin-bottom:22px">
        <span style="display:block;width:18px;height:1px;background:var(--gold)"></span>
        {date_str} · Gift Guide
      </div>
      <h1 style="font-family:'Cormorant Garamond',serif;font-size:clamp(2rem,4vw,3.2rem);font-weight:600;line-height:1.08;letter-spacing:-.05em;color:var(--ink);margin-bottom:20px">{post.get("heading", post["title"])}</h1>
      <p style="font-size:1.06rem;line-height:1.78;color:var(--muted);margin-bottom:44px;padding-bottom:40px;border-bottom:1px solid var(--divider);font-weight:300">{post.get("description", "")}</p>
    </div>
    <div style="max-width:720px;margin:0 auto;padding:0 48px 96px">
      <div class="blog-prose">{content_html_body}</div>
    </div>
    """

    return render_page(
        title=post["title"],
        description=post.get("meta_description", post.get("description", "")),
        heading="", subtitle="",
        products=None, similar_products=related,
        article_date=post.get("date", datetime.date.today().isoformat()),
        content=content_html
    )


# ============================================================================
# STATIC ROUTES
# ============================================================================

@app.route("/robots.txt")
def robots():
    return Response(f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /data/
Crawl-delay: 1
Sitemap: {SITE_URL}/sitemap.xml
""", mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    history = load_history()
    today = str(datetime.date.today())
    urls = set()
    urls.add((SITE_URL + "/", today, "1.0", "daily"))
    urls.add((SITE_URL + "/blog", today, "0.9", "daily"))

    all_products = []
    for day_products in history.values(): all_products.extend(day_products)

    categories_seen, products_seen = set(), set()
    for p in all_products:
        if p.get("category") and p["category"] not in categories_seen:
            categories_seen.add(p["category"])
            urls.add((f"{SITE_URL}/category/{slugify(p['category'])}", p.get("date_added", today), "0.8", "weekly"))
        if p.get("name") and p["name"] not in products_seen:
            products_seen.add(p["name"])
            urls.add((f"{SITE_URL}/product/{slugify(p['name'])}", p.get("date_added", today), "0.7", "weekly"))

    for season in ["Valentine's Day", "Mother's Day", "Easter", "Father's Day", "Summer Gifts", "Back to School", "Halloween", "Christmas"]:
        urls.add((f"{SITE_URL}/season/{slugify(season)}", today, "0.8", "weekly"))

    for slug, post in BLOG_POSTS.items():
        urls.add((f"{SITE_URL}/blog/{slug}", post.get("date", today), "0.6", "monthly"))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, lastmod, priority, changefreq in sorted(urls):
        xml += f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>\n"
    xml += "</urlset>"
    return Response(xml, mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
