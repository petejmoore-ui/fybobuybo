# ============================================================================
# FYBOBUYBO app.py — ELITE REDESIGN v4.0
# CHANGES vs v3:
#   ✅ SEARCH FIXED — event listeners now properly wired to both inputs
#   ✅ BLOG CARDS — real product images pulled from related_products
#   ✅ DESIGN ELEVATION — new premium editorial system (see CSS_TEMPLATE)
#   ✅ BLOG FEATURED — hero image rendered correctly
#   ✅ MOBILE — search drawer works, no overflow
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
PROMPT_VERSION = "v4.0-elite-2026"

os.makedirs("data", exist_ok=True)

PRIVACY_POLICY_HTML = """
<article style="max-width: 900px; margin: 40px auto; padding: 20px;">
  <div style="background: var(--card); padding: 30px; border-radius: 16px; margin-bottom: 30px;">
    <p style="font-size: 1.1rem; line-height: 1.8; margin-bottom: 20px;">
      <strong>Last Updated:</strong> January 23, 2026
    </p>
    <p style="font-size: 1.05rem; line-height: 1.8;">
      FyboBuybo ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your information when you visit our website www.fybobuybo.com.
    </p>
  </div>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">1. Information We Collect</h2>
  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--accent);">1.1 Automatically Collected Information</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">When you visit our website, we automatically collect certain information about your device and browsing behaviour through cookies and similar technologies.</p>
  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--accent);">1.2 Information You Provide</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">We do not currently collect personal information directly from you unless you choose to contact us.</p>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">2. Cookies and Tracking</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">We use essential cookies (theme preference) and Amazon affiliate tracking cookies. You can manage cookies through your browser settings.</p>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">3. Affiliate Relationships</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">FyboBuybo is a participant in the Amazon EU Associates Programme. We earn commissions on qualifying purchases at no extra cost to you.</p>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">4. Your Rights Under UK GDPR</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">You have the right to access, rectify, erase, and port your data. Contact us at infofybobuybo@gmail.com to exercise these rights.</p>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">5. Contact Us</h2>
  <div style="background: var(--card); padding: 20px; border-radius: 12px; margin: 20px 0;">
    <p style="line-height: 1.8;"><strong>Email:</strong> infofybobuybo@gmail.com<br><strong>Website:</strong> www.fybobuybo.com</p>
  </div>
</article>
"""

TERMS_OF_SERVICE_HTML = """
<article style="max-width: 900px; margin: 40px auto; padding: 20px;">
  <div style="background: var(--card); padding: 30px; border-radius: 16px; margin-bottom: 30px;">
    <p style="font-size: 1.1rem; line-height: 1.8;">Welcome to FyboBuybo. By using www.fybobuybo.com, you accept these Terms of Service.</p>
  </div>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">1. About FyboBuybo</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">FyboBuybo is a UK-based product discovery and affiliate marketing website. We are not a retailer — all purchases are made through Amazon UK.</p>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">2. Affiliate Disclosure</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">We earn a commission when you purchase through our links. This does not affect your purchase price.</p>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">3. Limitation of Liability</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">FyboBuybo is provided "as is". We are not liable for product quality, delivery issues, or retailer problems.</p>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">4. Governing Law</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">These terms are governed by the laws of England and Wales.</p>
  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--highlight);">5. Contact</h2>
  <div style="background: var(--card); padding: 20px; border-radius: 12px;">
    <p style="line-height: 1.8;"><strong>Email:</strong> infofybobuybo@gmail.com</p>
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
# HELPER FUNCTIONS
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
    # NOTE: AggregateRating schema intentionally omitted - Amazon affiliate TOS
    # prohibits displaying Amazon review data without live PA API feed.
    # We direct users to Amazon for current ratings instead.
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
    name_lower = name.lower()
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
# CACHE MANAGEMENT
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
# CSS TEMPLATE — ELITE v4
# ============================================================================

CSS_TEMPLATE = """<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Outfit:wght@300;400;500;600;700&display=swap');

/* ─── DESIGN TOKENS ─────────────────────────────────────── */
:root {
  --bg:            #f7f4ef;
  --bg-2:          #ede9e0;
  --bg-3:          #e4dfd5;
  --card:          #ffffff;
  --card-border:   rgba(0,0,0,0.055);
  --accent:        #18120e;
  --accent-2:      #3a2e28;
  --muted:         #7a6e65;
  --hl:            #b8822a;
  --hl-2:          #d4a044;
  --hl-soft:       rgba(184,130,42,0.10);
  --hl-glow:       rgba(184,130,42,0.20);
  --cta:           #18120e;
  --cta-fg:        #f7f4ef;
  --tag-bg:        #ede9e0;
  --nav-bg:        rgba(247,244,239,0.96);
  --border:        rgba(0,0,0,0.07);
  --divider:       rgba(0,0,0,0.06);
  --shadow-sm:     0 1px 3px rgba(24,18,14,0.04),0 4px 14px rgba(24,18,14,0.06);
  --shadow-md:     0 4px 20px rgba(24,18,14,0.08),0 16px 48px rgba(24,18,14,0.10);
  --shadow-lg:     0 8px 36px rgba(24,18,14,0.12),0 28px 72px rgba(24,18,14,0.15);
  --input-bg:      rgba(255,255,255,0.85);
  --ribbon-bg:     #18120e;
  --ribbon-fg:     #d4a044;
  --menu-bg:       #f2ede4;
  --badge-bg:      #ede9e0;
}
.dark {
  --bg:            #161210;
  --bg-2:          #1e1a17;
  --bg-3:          #252019;
  --card:          #231f1c;
  --card-border:   rgba(255,255,255,0.06);
  --accent:        #f0ebe3;
  --accent-2:      #c8bfb5;
  --muted:         #857870;
  --hl:            #d4a044;
  --hl-2:          #e6b55a;
  --hl-soft:       rgba(212,160,68,0.10);
  --hl-glow:       rgba(212,160,68,0.18);
  --cta:           #d4a044;
  --cta-fg:        #161210;
  --tag-bg:        rgba(255,255,255,0.05);
  --nav-bg:        rgba(22,18,16,0.97);
  --border:        rgba(255,255,255,0.07);
  --divider:       rgba(255,255,255,0.06);
  --shadow-sm:     0 1px 3px rgba(0,0,0,0.50),0 4px 14px rgba(0,0,0,0.55);
  --shadow-md:     0 4px 20px rgba(0,0,0,0.55),0 16px 48px rgba(0,0,0,0.65);
  --shadow-lg:     0 8px 36px rgba(0,0,0,0.65),0 28px 72px rgba(0,0,0,0.78);
  --input-bg:      rgba(255,255,255,0.045);
  --ribbon-bg:     #d4a044;
  --ribbon-fg:     #161210;
  --menu-bg:       #1e1a17;
  --badge-bg:      rgba(255,255,255,0.05);
}

/* ─── RESET ─────────────────────────────────────────────── */
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{
  background:var(--bg);color:var(--accent);
  font-family:'Outfit',sans-serif;font-weight:400;
  line-height:1.6;overflow-x:hidden;min-height:100vh;
  transition:background .3s,color .3s;
}
a{text-decoration:none;color:inherit}
img{max-width:100%}
button{font-family:inherit}

/* ─── MARQUEE RIBBON ─────────────────────────────────────── */
.ribbon{
  background:var(--ribbon-bg);color:var(--ribbon-fg);
  padding:8px 0;overflow:hidden;white-space:nowrap;
  font-size:.68rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;
}
.ribbon-inner{display:inline-block;animation:marquee 40s linear infinite}
.ribbon-inner span{margin:0 32px}
.ribbon-inner .sep{opacity:.3;margin:0 8px}
@keyframes marquee{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* ─── NAV ────────────────────────────────────────────────── */
.site-nav{
  position:sticky;top:0;z-index:200;
  background:var(--nav-bg);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);
  padding:0 48px;
}
.nav-inner{
  max-width:1560px;margin:0 auto;
  display:flex;align-items:center;height:66px;gap:16px;
}
.nav-logo{
  font-family:'Playfair Display',serif;font-size:1.55rem;font-weight:700;
  color:var(--accent);letter-spacing:-.02em;flex-shrink:0;
  transition:color .2s;
}
.nav-logo:hover{color:var(--hl)}
.nav-logo em{color:var(--hl);font-style:italic}

.nav-links{display:flex;gap:2px;align-items:center;flex:1}
.nav-links a{
  color:var(--muted);font-size:.875rem;font-weight:500;
  padding:6px 11px;border-radius:6px;transition:color .2s,background .2s;
}
.nav-links a:hover{color:var(--accent);background:var(--tag-bg)}

/* Dropdowns */
.nav-drop{position:relative}
.nav-drop-btn{
  display:flex;align-items:center;gap:5px;color:var(--muted);
  font-size:.875rem;font-weight:500;padding:6px 11px;border-radius:6px;
  cursor:pointer;background:none;border:none;transition:color .2s,background .2s;
}
.nav-drop-btn:hover,.nav-drop.open .nav-drop-btn{color:var(--accent);background:var(--tag-bg)}
.nav-drop-btn svg{width:10px;height:10px;stroke:currentColor;fill:none;transition:transform .22s}
.nav-drop.open .nav-drop-btn svg{transform:rotate(180deg)}
.nav-drop-menu{
  display:none;position:absolute;top:calc(100% + 8px);left:0;
  background:var(--card);border:1px solid var(--border);border-radius:14px;
  padding:6px;min-width:195px;max-height:360px;overflow-y:auto;
  box-shadow:var(--shadow-lg);z-index:300;
}
.nav-drop.open .nav-drop-menu{display:block;animation:dropIn .15s ease}
@keyframes dropIn{from{opacity:0;transform:translateY(-5px)}to{opacity:1;transform:translateY(0)}}
.nav-drop-menu a{
  display:block;padding:8px 12px;border-radius:8px;
  color:var(--accent-2);font-size:.855rem;transition:all .15s;
}
.nav-drop-menu a:hover{background:var(--hl-soft);color:var(--hl)}

/* Search bar */
.nav-search{position:relative;flex-shrink:0}
.nav-search input{
  background:var(--input-bg);border:1px solid var(--border);
  border-radius:24px;padding:8px 16px 8px 36px;
  font-size:.84rem;font-family:inherit;color:var(--accent);
  width:195px;transition:all .25s;outline:none;
}
.nav-search input:focus{
  width:250px;border-color:var(--hl);
  box-shadow:0 0 0 3px var(--hl-glow);
}
.nav-search input::placeholder{color:var(--muted)}
.nav-search-icon{
  position:absolute;left:11px;top:50%;transform:translateY(-50%);
  width:14px;height:14px;stroke:var(--muted);pointer-events:none;fill:none;
}
.nav-right{display:flex;align-items:center;gap:8px;flex-shrink:0}
#theme-btn{
  width:37px;height:37px;border-radius:50%;border:1px solid var(--border);
  background:var(--tag-bg);cursor:pointer;display:flex;align-items:center;
  justify-content:center;transition:all .2s;
}
#theme-btn:hover{background:var(--hl-soft);border-color:var(--hl)}
#theme-btn svg{width:14px;height:14px;stroke:var(--accent);fill:none}

#hamburger{
  display:none;flex-direction:column;gap:5px;cursor:pointer;
  padding:8px;border:none;background:none;flex-shrink:0;
}
#hamburger span{
  display:block;width:21px;height:2px;background:var(--accent);
  border-radius:2px;transition:all .26s ease;
}
#hamburger.open span:nth-child(1){transform:translateY(7px) rotate(45deg)}
#hamburger.open span:nth-child(2){opacity:0;transform:scaleX(0)}
#hamburger.open span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}

/* ─── MOBILE DRAWER ──────────────────────────────────────── */
#mobile-menu{
  display:none;position:fixed;inset:0;
  background:var(--menu-bg);z-index:190;overflow-y:auto;
  padding:80px 24px 48px;flex-direction:column;gap:0;
}
#mobile-menu.open{display:flex;animation:slideIn .26s cubic-bezier(.16,1,.3,1)}
@keyframes slideIn{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:translateY(0)}}

.mm-link{
  font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;
  color:var(--accent);padding:14px 0;
  border-bottom:1px solid var(--divider);display:block;transition:color .2s;
}
.mm-link:hover{color:var(--hl)}
.mm-section-label{
  font-size:.66rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;
  color:var(--hl);margin:28px 0 12px;
  display:flex;align-items:center;gap:8px;
}
.mm-section-label::before{content:'';display:block;width:14px;height:1px;background:var(--hl)}
.mm-pills{display:flex;flex-wrap:wrap;gap:8px}
.mm-pill{
  background:var(--card);border:1px solid var(--border);border-radius:20px;
  padding:7px 16px;font-size:.84rem;font-weight:500;color:var(--accent-2);
  transition:all .2s;display:block;
}
.mm-pill:hover{background:var(--hl-soft);border-color:var(--hl);color:var(--hl)}
.mm-search{margin-top:32px}
.mm-search input{
  width:100%;background:var(--card);border:1px solid var(--border);
  border-radius:12px;padding:13px 18px;font-size:1rem;font-family:inherit;
  color:var(--accent);outline:none;transition:border-color .2s;
}
.mm-search input:focus{border-color:var(--hl)}
.mm-search input::placeholder{color:var(--muted)}

/* ─── HERO ───────────────────────────────────────────────── */
.hero{
  max-width:1560px;margin:0 auto;
  padding:68px 48px 40px;
  display:grid;grid-template-columns:1fr 420px;gap:64px;align-items:center;
}
.hero-eyebrow{
  display:inline-flex;align-items:center;gap:9px;
  font-size:.69rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;
  color:var(--hl);margin-bottom:20px;
}
.hero-eyebrow::before{content:'';display:block;width:22px;height:1px;background:var(--hl)}
.hero h1{
  font-family:'Playfair Display',serif;
  font-size:clamp(2.6rem,5vw,5rem);
  font-weight:900;line-height:1.0;letter-spacing:-.03em;color:var(--accent);
  margin-bottom:22px;
  animation:heroUp .9s cubic-bezier(.16,1,.3,1) both;
}
.hero h1 em{font-style:italic;color:var(--hl)}
@keyframes heroUp{from{opacity:0;transform:translateY(28px)}to{opacity:1;transform:translateY(0)}}
.hero-sub{
  font-size:1.05rem;line-height:1.78;color:var(--muted);
  max-width:480px;margin-bottom:30px;
  animation:heroUp .9s .1s cubic-bezier(.16,1,.3,1) both;
}
.hero-badges{
  display:flex;gap:8px;flex-wrap:wrap;
  animation:heroUp .9s .18s cubic-bezier(.16,1,.3,1) both;
}
.hero-badge{
  display:inline-flex;align-items:center;gap:6px;
  background:var(--badge-bg);border:1px solid var(--border);
  border-radius:20px;padding:6px 14px;font-size:.79rem;font-weight:500;color:var(--muted);
}
.hero-visual{
  display:grid;grid-template-columns:1fr 1fr;gap:14px;
  animation:heroUp .9s .22s cubic-bezier(.16,1,.3,1) both;
}
.hero-img-slot{
  border-radius:18px;overflow:hidden;aspect-ratio:3/4;
  background:var(--bg-2);box-shadow:var(--shadow-md);
}
.hero-img-slot:nth-child(2){margin-top:24px}
.hero-img-slot img{width:100%;height:100%;object-fit:cover;display:block}

/* ─── AFFILIATE BANNER ───────────────────────────────────── */
.affil{max-width:1560px;margin:0 auto;padding:0 48px 16px}
.affil-inner{
  background:var(--hl-soft);border:1px solid rgba(184,130,42,.16);
  border-radius:10px;padding:10px 18px;
  display:flex;align-items:center;gap:10px;font-size:.82rem;color:var(--muted);
}
.affil-inner strong{color:var(--accent)}
.affil-inner a{color:var(--hl);font-weight:500}

/* ─── CATEGORY RAIL ──────────────────────────────────────── */
.cat-rail{
  max-width:1560px;margin:40px auto 0;padding:0 48px;
  display:flex;gap:8px;flex-wrap:wrap;
}
.cat-pill{
  background:var(--card);border:1px solid var(--border);border-radius:24px;
  padding:8px 20px;font-size:.83rem;font-weight:500;color:var(--accent-2);
  transition:all .2s;white-space:nowrap;
}
.cat-pill:hover{background:var(--hl-soft);border-color:var(--hl);color:var(--hl)}

/* ─── SECTION HEADER ─────────────────────────────────────── */
.sec-hdr{
  max-width:1560px;margin:60px auto 0;padding:0 48px;
  display:flex;align-items:flex-end;justify-content:space-between;gap:16px;
  position:relative;z-index:2;
}
.sec-eyebrow{
  display:inline-flex;align-items:center;gap:8px;font-size:.67rem;
  font-weight:700;letter-spacing:.15em;text-transform:uppercase;
  color:var(--hl);margin-bottom:8px;
}
.sec-eyebrow::before{content:'';display:block;width:16px;height:1px;background:var(--hl)}
.sec-title{
  font-family:'Playfair Display',serif;
  font-size:clamp(1.65rem,3vw,2.5rem);
  font-weight:700;letter-spacing:-.025em;line-height:1.1;color:var(--accent);
}
.sec-title em{font-style:italic;color:var(--hl)}

/* ─── PRODUCT GRID + CARD ────────────────────────────────── */
.grid{
  max-width:1560px;margin:28px auto 0;padding:0 48px;
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(275px,1fr));
  gap:22px;
}
.card{
  background:var(--card);border:1px solid var(--card-border);border-radius:20px;
  overflow:hidden;display:flex;flex-direction:column;
  transition:transform .3s cubic-bezier(.34,1.56,.64,1),box-shadow .3s ease;
  box-shadow:var(--shadow-sm);position:relative;
}
.card:hover{transform:translateY(-6px);box-shadow:var(--shadow-md)}
.card-img{
  position:relative;background:var(--bg-2);overflow:hidden;aspect-ratio:1;
}
.card-img img{
  width:100%;height:100%;object-fit:contain;padding:20px;
  transition:transform .5s cubic-bezier(.25,.46,.45,.94);
}
.card:hover .card-img img{transform:scale(1.07)}
.card-cat-badge{
  position:absolute;top:11px;left:11px;
  background:rgba(255,255,255,0.90);backdrop-filter:blur(8px);
  border-radius:20px;padding:3px 10px;font-size:.69rem;font-weight:600;
  letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  box-shadow:0 2px 8px rgba(0,0,0,.08);
}
.dark .card-cat-badge{background:rgba(30,24,20,0.88)}
.card-body{padding:18px 18px 16px;display:flex;flex-direction:column;flex:1}
.card-name{
  font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;
  line-height:1.3;letter-spacing:-.01em;color:var(--accent);
  display:block;margin-bottom:8px;transition:color .2s;
}
.card-name:hover{color:var(--hl)}
.card-hook{font-size:.855rem;line-height:1.65;color:var(--muted);margin-bottom:13px;flex:1}
.card-hook b{color:var(--accent-2);font-weight:600}
.card-div{height:1px;background:var(--divider);margin:0 0 13px}
.card-meta{display:flex;align-items:center;justify-content:space-between;margin-bottom:11px}
.card-rating{font-size:.78rem;color:var(--muted)}
.card-stars{color:#e6a817;letter-spacing:-.04em;margin-right:3px}
.card-date{font-size:.73rem;color:var(--muted);opacity:.6}
.card-cta{display:flex;flex-direction:column;gap:7px}
.btn-amz{
  display:flex;align-items:center;justify-content:center;gap:7px;
  background:var(--cta);color:var(--cta-fg);
  padding:12px 18px;border-radius:10px;
  font-size:.875rem;font-weight:600;transition:all .2s;
  border:none;cursor:pointer;
}
.btn-amz:hover{opacity:.86;transform:translateY(-1px)}
.btn-amz .amz-logo{font-size:.96rem;font-weight:800;font-style:italic}
.btn-detail{
  display:block;text-align:center;font-size:.78rem;color:var(--muted);
  padding:7px;border:1px solid var(--divider);border-radius:8px;transition:all .2s;
}
.btn-detail:hover{color:var(--hl);border-color:var(--hl);background:var(--hl-soft)}

/* ─── BLOG PAGE ──────────────────────────────────────────── */
.blog-wrap{max-width:1560px;margin:44px auto 0;padding:0 48px}

/* Featured post */
.blog-feat{
  display:grid;grid-template-columns:1.35fr 1fr;
  border-radius:24px;overflow:hidden;background:var(--card);
  border:1px solid var(--card-border);box-shadow:var(--shadow-md);
  margin-bottom:56px;transition:box-shadow .3s;text-decoration:none;
  color:inherit;display:grid;
}
.blog-feat:hover{box-shadow:var(--shadow-lg)}
.blog-feat-visual{
  background:var(--bg-2);min-height:340px;
  display:flex;align-items:center;justify-content:center;
  font-size:4.5rem;overflow:hidden;position:relative;
}
.blog-feat-visual img{
  width:100%;height:100%;object-fit:cover;
  transition:transform .5s cubic-bezier(.25,.46,.45,.94);
}
.blog-feat:hover .blog-feat-visual img{transform:scale(1.04)}
.blog-feat-body{
  padding:48px 44px;display:flex;flex-direction:column;
  justify-content:center;gap:16px;
}
.blog-feat-eyebrow{
  display:inline-flex;align-items:center;gap:8px;font-size:.68rem;
  font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--hl);
}
.blog-feat-eyebrow::before{content:'';display:block;width:14px;height:1px;background:var(--hl)}
.blog-feat-title{
  font-family:'Playfair Display',serif;
  font-size:clamp(1.4rem,2.4vw,2.0rem);
  font-weight:900;line-height:1.15;letter-spacing:-.025em;color:var(--accent);
}
.blog-feat-desc{font-size:.94rem;line-height:1.7;color:var(--muted)}
.blog-feat-cta{
  display:inline-flex;align-items:center;gap:8px;font-size:.84rem;
  font-weight:700;color:var(--hl);width:fit-content;
  padding-bottom:2px;border-bottom:1px solid transparent;transition:border-color .2s;
}
.blog-feat-cta:hover{border-color:var(--hl)}

/* Blog grid */
.blog-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(305px,1fr));gap:22px;
}
.blog-card{
  background:var(--card);border:1px solid var(--card-border);border-radius:20px;
  overflow:hidden;display:flex;flex-direction:column;
  transition:transform .28s cubic-bezier(.34,1.56,.64,1),box-shadow .28s ease;
  box-shadow:var(--shadow-sm);text-decoration:none;color:inherit;
}
.blog-card:hover{transform:translateY(-5px);box-shadow:var(--shadow-md)}

/* ── Blog card thumbnail ── */
.blog-card-thumb{
  height:176px;overflow:hidden;position:relative;
  background:linear-gradient(135deg,var(--bg-2),var(--bg-3));
  display:flex;align-items:center;justify-content:center;font-size:2.8rem;
}
/* Image fills the thumb */
.blog-card-thumb img{
  width:100%;height:100%;
  object-fit:cover;           /* fills — great for lifestyle photos */
  transition:transform .45s cubic-bezier(.25,.46,.45,.94);
  position:absolute;inset:0;
}
/* Product images look better contained */
.blog-card-thumb img.product-img{
  object-fit:contain;
  padding:20px;
}
.blog-card:hover .blog-card-thumb img{transform:scale(1.05)}

.blog-card-body{padding:22px;display:flex;flex-direction:column;gap:8px;flex:1}
.blog-card-meta{
  display:flex;align-items:center;gap:6px;font-size:.67rem;
  font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--hl);
}
.blog-card-meta::before{content:'';display:block;width:11px;height:1px;background:var(--hl)}
.blog-card-title{
  font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;
  line-height:1.3;letter-spacing:-.012em;color:var(--accent);
}
.blog-card-desc{font-size:.855rem;line-height:1.65;color:var(--muted);flex:1}
.blog-card-link{
  font-size:.78rem;font-weight:700;color:var(--hl);
  display:inline-flex;align-items:center;gap:4px;margin-top:4px;
}

/* ─── BLOG PROSE ─────────────────────────────────────────── */
.blog-prose{font-size:1.02rem;line-height:1.85;color:var(--accent-2)}
.blog-prose h2{
  font-family:'Playfair Display',serif;font-size:1.65rem;font-weight:700;
  color:var(--accent);margin:50px 0 16px;letter-spacing:-.02em;line-height:1.2;
  padding-bottom:14px;border-bottom:1px solid var(--divider);
}
.blog-prose h3{
  font-family:'Playfair Display',serif;font-size:1.26rem;font-weight:700;
  color:var(--accent);margin:36px 0 12px;
}
.blog-prose h4{font-family:'Playfair Display',serif;font-size:1.04rem;font-weight:700;color:var(--accent);margin:28px 0 10px}
.blog-prose p{margin-bottom:22px}
.blog-prose a{color:var(--hl);font-weight:500;border-bottom:1px solid var(--hl-soft);transition:border-color .2s}
.blog-prose a:hover{border-color:var(--hl)}
.blog-prose strong{color:var(--accent);font-weight:600}
.blog-prose ul,.blog-prose ol{margin:0 0 24px;padding-left:0;list-style:none}
.blog-prose li{font-size:1rem;line-height:1.75;color:var(--accent-2);margin-bottom:10px;padding-left:22px;position:relative}
.blog-prose ul li::before{content:'';position:absolute;left:0;top:11px;width:5px;height:5px;border-radius:50%;background:var(--hl)}
.blog-prose ol{counter-reset:ol-count}
.blog-prose ol li{counter-increment:ol-count}
.blog-prose ol li::before{content:counter(ol-count);position:absolute;left:0;top:3px;font-size:.75rem;font-weight:700;color:var(--hl)}
.blog-prose img{width:100%;border-radius:16px;margin:36px 0;box-shadow:var(--shadow-md);display:block}
.blog-prose blockquote{
  border-left:3px solid var(--hl);margin:36px 0;padding:18px 24px;
  background:var(--hl-soft);border-radius:0 14px 14px 0;
  font-style:italic;color:var(--muted);font-size:1.05rem;
}
.blog-prose table{width:100%;border-collapse:collapse;margin:32px 0;font-size:.94rem}
.blog-prose th{background:var(--bg-2);padding:12px 16px;text-align:left;font-weight:700;color:var(--accent);border-bottom:2px solid var(--border);font-family:'Playfair Display',serif}
.blog-prose td{padding:12px 16px;border-bottom:1px solid var(--divider);color:var(--accent-2)}
.blog-prose tr:last-child td{border-bottom:none}

/* ─── SIMILAR PRODUCTS ───────────────────────────────────── */
.similar-sec{max-width:1560px;margin:68px auto 0;padding:0 48px}
.similar-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(195px,1fr));
  gap:16px;margin-top:28px;
}
.sim-card{
  background:var(--card);border:1px solid var(--card-border);border-radius:14px;
  overflow:hidden;display:block;
  transition:transform .24s ease,box-shadow .24s ease;box-shadow:var(--shadow-sm);
}
.sim-card:hover{transform:translateY(-4px);box-shadow:var(--shadow-md)}
.sim-card-img{aspect-ratio:1;background:var(--bg-2);overflow:hidden}
.sim-card-img img{width:100%;height:100%;object-fit:contain;padding:12px}
.sim-card-name{font-family:'Playfair Display',serif;font-size:.85rem;font-weight:600;color:var(--accent);line-height:1.35;padding:12px}

/* ─── PAGINATION ─────────────────────────────────────────── */
.pager{
  max-width:1560px;margin:52px auto;padding:0 48px;
  display:flex;justify-content:center;gap:10px;
}
.pager a{
  background:var(--card);border:1px solid var(--border);color:var(--accent);
  padding:10px 26px;border-radius:8px;font-size:.87rem;font-weight:600;transition:all .2s;
}
.pager a:hover{background:var(--cta);color:var(--cta-fg);border-color:var(--cta)}

/* ─── FOOTER ─────────────────────────────────────────────── */
.site-footer{margin-top:96px;border-top:1px solid var(--border);background:var(--bg-2)}
.footer-inner{max-width:1560px;margin:0 auto;padding:52px 48px 36px}
.footer-top{display:grid;grid-template-columns:2fr 1fr 1fr;gap:56px;margin-bottom:44px}
.footer-logo{
  font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;
  color:var(--accent);letter-spacing:-.02em;margin-bottom:12px;
}
.footer-logo em{color:var(--hl);font-style:italic}
.footer-desc{font-size:.87rem;line-height:1.75;color:var(--muted);max-width:295px}
.footer-col-ttl{font-size:.68rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);margin-bottom:16px}
.footer-col a{display:block;font-size:.875rem;color:var(--muted);margin-bottom:9px;transition:color .2s}
.footer-col a:hover{color:var(--hl)}
.footer-btm{
  padding-top:24px;border-top:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
}
.footer-legal,.footer-amazon{font-size:.74rem;color:var(--muted);line-height:1.6}
.footer-amazon{font-style:italic}

/* ─── SEARCH OVERLAY ─────────────────────────────────────── */
#search-overlay{
  display:none;position:fixed;
  top:0;left:0;right:0;bottom:0;
  background:rgba(0,0,0,0.72);backdrop-filter:blur(8px);
  z-index:210;padding:80px 24px 40px;overflow-y:auto;
}
#search-overlay.open{display:block;animation:fadeIn .2s ease}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.search-box{
  max-width:1100px;margin:0 auto;background:var(--bg);
  border-radius:24px;padding:36px;position:relative;
}
.search-box-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.search-box-title{font-family:'Playfair Display',serif;font-size:1.55rem;font-weight:700;color:var(--accent)}
.search-close{
  background:var(--tag-bg);border:1px solid var(--border);width:37px;height:37px;
  border-radius:50%;cursor:pointer;font-size:1.2rem;color:var(--accent);
  display:flex;align-items:center;justify-content:center;transition:all .2s;
}
.search-close:hover{background:var(--hl-soft)}
.search-count{font-size:.85rem;color:var(--muted);margin-bottom:24px}
.search-res-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(225px,1fr));gap:18px}

/* ─── COOKIE BAR ─────────────────────────────────────────── */
#cookie-bar{
  display:none;position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
  background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:18px 24px;box-shadow:var(--shadow-lg);z-index:1000;
  max-width:600px;width:calc(100% - 32px);
  align-items:center;gap:18px;flex-wrap:wrap;
}
#cookie-bar.show{display:flex;animation:cookiePop .32s cubic-bezier(.16,1,.3,1)}
@keyframes cookiePop{from{opacity:0;transform:translateX(-50%) translateY(16px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
.cookie-text{flex:1;min-width:180px;font-size:.83rem;color:var(--muted);line-height:1.6}
.cookie-text a{color:var(--hl)}
.cookie-btns{display:flex;gap:8px;flex-shrink:0}
.btn-ok{background:var(--cta);color:var(--cta-fg);border:none;border-radius:8px;padding:9px 18px;font-size:.82rem;font-weight:600;cursor:pointer;font-family:inherit}
.btn-ok:hover{opacity:.86}
.btn-ess{background:none;color:var(--muted);border:1px solid var(--border);border-radius:8px;padding:9px 14px;font-size:.82rem;font-weight:500;cursor:pointer;font-family:inherit;transition:all .2s}
.btn-ess:hover{border-color:var(--hl);color:var(--hl)}

/* ─── PRODUCT DETAIL ─────────────────────────────────────── */
.pd{max-width:1100px;margin:44px auto 0;padding:0 48px;display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:start}
.pd-img{background:var(--bg-2);border-radius:24px;overflow:hidden;aspect-ratio:1;border:1px solid var(--card-border);position:sticky;top:84px}
.pd-img img{width:100%;height:100%;object-fit:contain;padding:36px;display:block}
.pd-info{display:flex;flex-direction:column;gap:18px;padding-top:4px}
.pd-cat{display:inline-flex;align-items:center;gap:8px;font-size:.69rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--hl)}
.pd-cat::before{content:'';display:block;width:16px;height:1px;background:var(--hl)}
.pd-title{font-family:'Playfair Display',serif;font-size:clamp(1.5rem,3vw,2.2rem);font-weight:900;line-height:1.15;letter-spacing:-.025em;color:var(--accent)}
.pd-div{height:1px;background:var(--divider)}
.pd-price-note{background:var(--hl-soft);border:1px solid rgba(184,130,42,.2);border-radius:12px;padding:12px 17px;font-size:.86rem;color:var(--muted);font-style:italic}

/* ─── RESPONSIVE ─────────────────────────────────────────── */
@media(max-width:1024px){
  .hero{grid-template-columns:1fr;padding:48px 32px 28px}
  .hero-visual{display:none}
  .footer-top{grid-template-columns:1fr 1fr}
  .blog-feat{grid-template-columns:1fr}
  .blog-feat-visual{min-height:210px}
  .pd{grid-template-columns:1fr;padding:0 32px}
  .pd-img{position:static}
}
@media(max-width:768px){
  .site-nav{padding:0 16px}
  .nav-inner{height:56px}
  .nav-links,.nav-search{display:none}
  #hamburger{display:flex}

  .hero{padding:26px 16px 14px}
  .hero h1{font-size:2rem}
  .hero-sub{font-size:.92rem}

  .grid,.blog-grid,.similar-grid,.cat-rail,.affil,.sec-hdr,.similar-sec,.pager,.blog-wrap{padding-left:16px!important;padding-right:16px!important}
  .grid{grid-template-columns:1fr}
  .blog-grid{grid-template-columns:1fr}

  .blog-feat-body{padding:22px 20px}
  .blog-feat-title{font-size:1.3rem}

  .footer-inner{padding:36px 16px 28px}
  .footer-top{grid-template-columns:1fr;gap:26px}
  .footer-btm{flex-direction:column;align-items:flex-start}

  .cookie-btns{width:100%}
  .btn-ok,.btn-ess{flex:1;text-align:center}

  .pd{padding:0 16px;gap:24px;margin-top:24px}
}
@media(max-width:480px){
  .hero h1{font-size:1.78rem}
  .similar-grid{grid-template-columns:repeat(2,1fr)}
}

/* ─── SCROLLBAR ──────────────────────────────────────────── */
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--muted)}
</style>"""


# ============================================================================
# BASE HTML TEMPLATE — ELITE v4
# ============================================================================

BASE_HTML = """<!DOCTYPE html>
<html lang="en-GB">
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

<!-- RIBBON -->
<div class="ribbon" aria-hidden="true">
  <div class="ribbon-inner">
    {% for i in range(2) %}
    <span>Curated UK Gifts</span><span class="sep">·</span>
    <span>Updated Daily</span><span class="sep">·</span>
    <span>Thoughtfully Picked</span><span class="sep">·</span>
    <span>UK Shoppers Love</span><span class="sep">·</span>
    <span>Best Sellers 2026</span><span class="sep">·</span>
    {% endfor %}
  </div>
</div>

<!-- NAV -->
<header class="site-nav">
  <div class="nav-inner">
    <a href="/" class="nav-logo">Fybo<em>Buybo</em></a>

    <nav class="nav-links" aria-label="Primary">
      <a href="/">Home</a>
      <a href="/blog">Blog</a>

      <div class="nav-drop">
        <button class="nav-drop-btn" type="button" aria-expanded="false" aria-haspopup="true">
          Categories
          <svg viewBox="0 0 12 12" stroke-width="2"><path d="M2 4l4 4 4-4"/></svg>
        </button>
        <div class="nav-drop-menu">
          {% for cat in nav_items.categories %}
          <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
          {% endfor %}
        </div>
      </div>

      {% if nav_items.seasons %}
      <div class="nav-drop">
        <button class="nav-drop-btn" type="button" aria-expanded="false" aria-haspopup="true">
          Seasonal
          <svg viewBox="0 0 12 12" stroke-width="2"><path d="M2 4l4 4 4-4"/></svg>
        </button>
        <div class="nav-drop-menu">
          {% for season in nav_items.seasons %}
          <a href="/season/{{ slugify(season) }}">{{ season }}</a>
          {% endfor %}
        </div>
      </div>
      {% endif %}
    </nav>

    <div class="nav-right">
      <div class="nav-search">
        <svg class="nav-search-icon" viewBox="0 0 16 16" stroke-width="1.6">
          <circle cx="6.5" cy="6.5" r="4.5"/><path d="M10 10l3.5 3.5"/>
        </svg>
        <input type="search" id="search-input" placeholder="Search gifts…" aria-label="Search gifts" autocomplete="off">
      </div>
      <button id="theme-btn" aria-label="Toggle dark mode">
        <svg id="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>
        <svg id="icon-moon" viewBox="0 0 24 24" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
      <button id="hamburger" aria-label="Open menu" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>

<!-- MOBILE DRAWER -->
<div id="mobile-menu" role="dialog" aria-modal="true" aria-label="Navigation">
  <a href="/" class="mm-link">Home</a>
  <a href="/blog" class="mm-link">Blog</a>

  {% if nav_items.categories %}
  <div>
    <div class="mm-section-label">Categories</div>
    <div class="mm-pills">
      {% for cat in nav_items.categories %}
      <a href="/category/{{ slugify(cat) }}" class="mm-pill">{{ cat }}</a>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if nav_items.seasons %}
  <div>
    <div class="mm-section-label">Seasonal Collections</div>
    <div class="mm-pills">
      {% for season in nav_items.seasons %}
      <a href="/season/{{ slugify(season) }}" class="mm-pill">{{ season }}</a>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <div class="mm-search">
    <input type="search" id="mobile-search-input" placeholder="Search gifts…" aria-label="Search" autocomplete="off">
  </div>
</div>

<!-- HERO (listing pages only) -->
{% if heading %}
<section class="hero">
  <div>
    <div class="hero-eyebrow">Updated daily · UK picks</div>
    <h1>{{ heading }}</h1>
    <p class="hero-sub">{{ subtitle }}</p>
    <div class="hero-badges">
      <span class="hero-badge">✓ UK-focused curation</span>
      <span class="hero-badge">✓ Thoughtfully chosen</span>
      <span class="hero-badge">✓ Refreshed every day</span>
    </div>
  </div>
  {% if products and products|length > 1 %}
  <div class="hero-visual" aria-hidden="true">
    <div class="hero-img-slot">
      <img src="{{ products[0].image }}" alt="{{ products[0].name }}" loading="eager">
    </div>
    <div class="hero-img-slot">
      <img src="{{ products[1].image }}" alt="{{ products[1].name }}" loading="eager">
    </div>
  </div>
  {% endif %}
</section>
{% endif %}

<!-- AFFILIATE DISCLOSURE -->
<div class="affil">
  <div class="affil-inner">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--hl)" stroke-width="2" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
    <span><strong>Affiliate Disclosure:</strong> We earn a commission on purchases through our links, at no extra cost to you. <a href="/privacy-policy">Learn more →</a></span>
  </div>
</div>

<!-- CATEGORY RAIL (homepage) -->
{% if request.path == '/' and nav_items.categories %}
<div class="cat-rail">
  {% for cat in nav_items.categories %}
  <a href="/category/{{ slugify(cat) }}" class="cat-pill">{{ cat }}</a>
  {% endfor %}
</div>
{% endif %}

<!-- PAGE CONTENT (blog detail / product detail / legal pages) -->
{% if content %}{{ content|safe }}{% endif %}

<!-- SECTION HEADER for listing pages -->
{% if products and products|length > 1 %}
<div class="sec-hdr">
  <div>
    <div class="sec-eyebrow">Hand-picked for you</div>
    <h2 class="sec-title">Today's <em>Top Picks</em></h2>
  </div>
</div>
{% endif %}

<!-- PRODUCT GRID -->
{% if products %}
<div class="grid">
{% for p in products %}
{% set price_info = get_product_price_rating(p) %}
<article class="card" itemscope itemtype="https://schema.org/Product">
  <div class="card-img">
    <span class="card-cat-badge">{{ p.category }}</span>
    <a href="/product/{{ slugify(p.name) }}">
      <img src="{{ p.image }}" alt="{{ p.name }}" loading="lazy" itemprop="image">
    </a>
  </div>
  <div class="card-body">
    <a href="/product/{{ slugify(p.name) }}" class="card-name" itemprop="name">{{ shorten_product_name(p.name) }}</a>
    <p class="card-hook" itemprop="description">{{ p.hook|safe }}</p>
    <div class="card-div"></div>
    <div class="card-meta">
      {% if price_info.rating %}
      <div class="card-rating">
        <span class="card-stars">{% for i in range(price_info.rating|int) %}★{% endfor %}</span>
        <span style="font-size:.77rem;color:var(--muted)">Highly rated on Amazon</span>
      </div>
      {% else %}<div></div>{% endif %}
      {% if p.date_added %}<span class="card-date">{{ p.date_added }}</span>{% endif %}
    </div>
    <div class="card-cta">
      {% if p.url %}
      <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored noopener" class="btn-amz">
        <span>View on</span><span class="amz-logo">amazon</span>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
      </a>
      {% endif %}
      <a href="/product/{{ slugify(p.name) }}" class="btn-detail">View full details →</a>
    </div>
  </div>
</article>
{% endfor %}
</div>
{% endif %}

<!-- SIMILAR PRODUCTS -->
{% if similar_products %}
<section class="similar-sec">
  <div class="sec-hdr" style="padding:0;margin:0 0 28px">
    <div>
      <div class="sec-eyebrow">You might also like</div>
      <h2 class="sec-title">More <em>Great Picks</em></h2>
    </div>
  </div>
  <div class="similar-grid">
    {% for s in similar_products %}
    <a href="/product/{{ slugify(s.name) }}" class="sim-card">
      <div class="sim-card-img">
        <img src="{{ s.image }}" alt="{{ s.name }}" loading="lazy">
      </div>
      <div class="sim-card-name">{{ shorten_product_name(s.name, 60) }}</div>
    </a>
    {% endfor %}
  </div>
</section>
{% endif %}

<!-- PAGINATION -->
{% if next_page_url or prev_page_url %}
<div class="pager">
  {% if prev_page_url %}<a href="{{ prev_page_url }}">← Previous</a>{% endif %}
  {% if next_page_url %}<a href="{{ next_page_url }}">Next →</a>{% endif %}
</div>
{% endif %}

<!-- FOOTER -->
<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-top">
      <div>
        <div class="footer-logo">Fybo<em>Buybo</em></div>
        <p class="footer-desc">Thoughtfully curated UK gifts, updated daily. We do the research so you can give the perfect present.</p>
      </div>
      <div class="footer-col">
        <div class="footer-col-ttl">Explore</div>
        <a href="/">Home</a>
        <a href="/blog">Blog</a>
        {% for cat in nav_items.categories[:5] %}
        <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
        {% endfor %}
      </div>
      <div class="footer-col">
        <div class="footer-col-ttl">Legal</div>
        <a href="/privacy-policy">Privacy Policy</a>
        <a href="/terms">Terms of Service</a>
        <a href="mailto:infofybobuybo@gmail.com">Contact Us</a>
      </div>
    </div>
    <div class="footer-btm">
      <p class="footer-legal">© 2026 FyboBuybo. All rights reserved. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. As an Amazon Associate, we earn from qualifying purchases.</p>
      <p class="footer-amazon">Prices and availability may change. Always verify on Amazon.</p>
    </div>
  </div>
</footer>

<!-- SEARCH OVERLAY -->
<div id="search-overlay" role="dialog" aria-label="Search results" aria-modal="true">
  <div class="search-box">
    <div class="search-box-hdr">
      <h2 class="search-box-title">Search Results</h2>
      <button class="search-close" id="search-close" aria-label="Close">×</button>
    </div>
    <p class="search-count" id="search-count"></p>
    <div class="search-res-grid" id="search-res-grid"></div>
  </div>
</div>

<!-- COOKIE BAR -->
<div id="cookie-bar" role="dialog" aria-label="Cookie consent">
  <div class="cookie-text">
    We use essential cookies and affiliate tracking.
    <a href="/privacy-policy">Learn more</a>
  </div>
  <div class="cookie-btns">
    <button class="btn-ok" id="cookie-accept">Accept All</button>
    <button class="btn-ess" id="cookie-essential">Essential Only</button>
  </div>
</div>

<!-- ============================================================
     SCRIPTS
     ============================================================ -->
<script>
// ── THEME ──────────────────────────────────────────────────────
const root = document.documentElement;
let dark = localStorage.getItem('fybo-dark') === '1';
function applyDark(d) {
  root.classList.toggle('dark', d);
  document.getElementById('icon-sun').style.display = d ? 'none' : 'block';
  document.getElementById('icon-moon').style.display = d ? 'block' : 'none';
}
applyDark(dark);
document.getElementById('theme-btn').onclick = () => {
  dark = !dark;
  localStorage.setItem('fybo-dark', dark ? '1' : '0');
  applyDark(dark);
};

// ── HAMBURGER ──────────────────────────────────────────────────
const burger = document.getElementById('hamburger');
const mMenu = document.getElementById('mobile-menu');
burger.onclick = () => {
  const open = mMenu.classList.toggle('open');
  burger.classList.toggle('open', open);
  burger.setAttribute('aria-expanded', String(open));
  document.body.style.overflow = open ? 'hidden' : '';
};
mMenu.querySelectorAll('a').forEach(a => {
  a.onclick = () => {
    mMenu.classList.remove('open');
    burger.classList.remove('open');
    burger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  };
});

// ── DESKTOP DROPDOWNS ──────────────────────────────────────────
document.querySelectorAll('.nav-drop').forEach(dd => {
  const btn = dd.querySelector('.nav-drop-btn');
  btn.onclick = e => {
    e.stopPropagation();
    const isOpen = dd.classList.contains('open');
    document.querySelectorAll('.nav-drop').forEach(x => {
      x.classList.remove('open');
      x.querySelector('.nav-drop-btn').setAttribute('aria-expanded', 'false');
    });
    if (!isOpen) {
      dd.classList.add('open');
      btn.setAttribute('aria-expanded', 'true');
    }
  };
});
document.addEventListener('click', () => {
  if (overlay.classList.contains('open')) return;
  document.querySelectorAll('.nav-drop').forEach(dd => {
    dd.classList.remove('open');
    dd.querySelector('.nav-drop-btn')?.setAttribute('aria-expanded', 'false');
  });
});

// ── SEARCH — FIXED ─────────────────────────────────────────────
// Products are fetched once, then all searching is client-side (fast).
let allProducts = [];
let searchTimer;

async function loadProducts() {
  try {
    const r = await fetch('/api/search-products');
    const d = await r.json();
    allProducts = d.products || [];
  } catch(e) { console.warn('Search load failed', e); }
}
loadProducts();

function pySlugify(t) {
  return t.toLowerCase()
    .replace(/&/g, '-and-')
    .replace(/\s+/g, '-')
    .replace(/[^\w-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
}
function shortenName(n, l=70) {
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

function renderResults(products, q) {
  countEl.textContent = products.length
    ? `${products.length} result${products.length !== 1 ? 's' : ''} for "${q}"`
    : `No results for "${q}"`;

  resGrid.innerHTML = products.length
    ? products.map(p => `
        <article class="card">
          <div class="card-img">
            <span class="card-cat-badge">${p.category || ''}</span>
            <a href="/product/${pySlugify(p.name)}">
              <img src="${p.image || ''}" alt="${p.name}" loading="lazy">
            </a>
          </div>
          <div class="card-body">
            <a href="/product/${pySlugify(p.name)}" class="card-name">${shortenName(p.name)}</a>
            <p class="card-hook">${p.hook || ''}</p>
            <div class="card-cta">
              ${p.url ? `<a href="${p.url}" target="_blank" rel="nofollow sponsored noopener" class="btn-amz">
                <span>View on</span><span class="amz-logo">amazon</span></a>` : ''}
              <a href="/product/${pySlugify(p.name)}" class="btn-detail">View full details →</a>
            </div>
          </div>
        </article>`).join('')
    : '<p style="text-align:center;padding:60px 20px;color:var(--muted)">No results found — try a different search.</p>';

  overlay.classList.add('open');
  const activeInput = document.activeElement;
  setTimeout(() => { if (activeInput) activeInput.focus(); }, 10);
}

// Prevent clicks inside overlay from bubbling to document (which closes dropdowns)
document.getElementById('search-overlay').addEventListener('click', e => {
  e.stopPropagation();
});

function closeSearch() {
  overlay.classList.remove('open');
}

function doSearch(q) {
  clearTimeout(searchTimer);
  const trimmed = q.trim();
  if (trimmed.length < 3) {
    if (overlay.classList.contains('open')) closeSearch();
    return;
  }
  searchTimer = setTimeout(() => {
    const ql = trimmed.toLowerCase();
    const words = ql.split(/\s+/).filter(w => w.length > 0);

    const scored = allProducts.map(p => {
      const name   = (p.name || '').toLowerCase();
      const cat    = (p.category || '').toLowerCase();
      const hook   = (p.hook || '').toLowerCase();
      const info   = (p.info || '').toLowerCase();
      const keys   = (p.keywords || []).join(' ').toLowerCase();
      const season = (p.season || '').toLowerCase();

      let score = 0;

      for (const word of words) {
        if (word.length < 3 && words.length > 1) continue;

        // Name matches score highest
        if (name.startsWith(word))           score += 20;
        else if (name.includes(' ' + word))  score += 15;
        else if (name.includes(word) && word.length >= 4) score += 8;

        // Category
        if (cat === word)                    score += 12;
        else if (cat.includes(word) && word.length >= 4) score += 6;

        // Keywords
        if (keys.includes(word) && word.length >= 4) score += 5;

        // Hook/info — only 4+ char words to avoid noise
        if (word.length >= 4) {
          if (hook.includes(word))   score += 3;
          if (info.includes(word))   score += 2;
          if (season.includes(word)) score += 4;
        }
      }

      // Bonus: full phrase matches name directly
      if (name.includes(ql)) score += 25;

      return { p, score };
    });

    const MIN_SCORE = 8;
    const hits = scored
      .filter(x => x.score >= MIN_SCORE)
      .sort((a, b) => b.score - a.score)
      .map(x => x.p);

    renderResults(hits, trimmed);
  }, 220);
}

// Wire up BOTH inputs
searchInp.addEventListener('input',  e => doSearch(e.target.value));
searchInp.addEventListener('keydown', e => { if (e.key === 'Escape') { closeSearch(); searchInp.value = ''; } });
if (mSearchInp) {
  mSearchInp.addEventListener('input', e => doSearch(e.target.value));
  mSearchInp.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeSearch(); mSearchInp.value = ''; }
  });
}

document.getElementById('search-close').onclick = closeSearch;
overlay.addEventListener('click', e => { if (e.target === overlay) closeSearch(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSearch(); });

// ── COOKIE ─────────────────────────────────────────────────────
(function() {
  const KEY = 'fybo_consent_v1';
  const bar = document.getElementById('cookie-bar');
  if (!bar) return;
  try { if (!localStorage.getItem(KEY)) bar.classList.add('show'); } catch(e) { bar.classList.add('show'); }
  function dismiss(v) {
    try { localStorage.setItem(KEY, v); } catch(e) {}
    bar.classList.remove('show');
  }
  document.getElementById('cookie-accept')?.addEventListener('click', () => dismiss('all'));
  document.getElementById('cookie-essential')?.addEventListener('click', () => dismiss('essential'));
})();
</script>
</body>
</html>"""


# ============================================================================
# RENDER PAGE
# ============================================================================

def render_page(title, description, heading, subtitle, products=None, page=1,
                page_url=None, similar_products=None, today=None,
                today_formatted=None, article_date=None, content=None):
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
        cookie_consent=""
    )


# ============================================================================
# ROUTES
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
        subtitle="A curated selection of popular gifts and presents, refreshed daily.",
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
        rating_html = f"""<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <span style="color:var(--star-col);font-size:1.15rem;letter-spacing:-.04em">{stars}</span>
          <span style="font-size:.9rem;color:var(--muted);font-weight:500">Highly rated on Amazon</span>
          <a href="{found.get('url','')}" target="_blank" rel="nofollow sponsored noopener"
             style="font-size:.82rem;color:var(--hl);font-weight:600;text-decoration:underline">
            See current ratings →</a>
        </div>"""

    amazon_btn = ""
    if found.get("url"):
        amazon_btn = f"""<a href="{found["url"]}" target="_blank" rel="nofollow sponsored noopener"
           style="display:flex;align-items:center;justify-content:center;gap:10px;background:var(--cta);color:var(--cta-fg);padding:17px 32px;border-radius:12px;font-size:1rem;font-weight:700;transition:opacity .2s;margin-top:4px">
          View on <em style="font-style:italic;font-weight:800;font-size:1.1rem">amazon</em>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/>
          </svg></a>"""

    info_html = f'<p style="font-size:.94rem;line-height:1.78;color:var(--muted)">{found["info"]}</p>' if found.get("info") else ""
    date_html = f'<p style="font-size:.76rem;color:var(--muted);opacity:.65;margin-top:4px">Featured {found["date_added"]}</p>' if found.get("date_added") else ""

    content_html = f"""
    <div class="pd">
      <div class="pd-img"><img src="{found["image"]}" alt="{found["name"]}"></div>
      <div class="pd-info">
        <div class="pd-cat">{found.get("category", "")}</div>
        <h1 class="pd-title">{found["name"]}</h1>
        {rating_html}
        <div class="pd-div"></div>
        <p style="font-size:1rem;line-height:1.75;color:var(--muted)">{found.get("hook", "")}</p>
        {info_html}
        <div class="pd-price-note">💡 Check Amazon for the current live price</div>
        {amazon_btn}
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
    """
    Returns (img_tag_html, is_product_img) or (None, False).
    Uses fuzzy matching so related_products field doesn't need to be an exact slug.
    Priority: post["featured_image"] -> post["image"] -> first img in content -> related_products fuzzy match -> category hint fallback
    """
    img_url = post.get("featured_image") or post.get("image")
    img_alt = post.get("featured_image_alt") or post.get("title", "")
    if img_url:
        return (
            f'<img src="{img_url}" alt="{img_alt}" style="width:100%;height:100%;object-fit:cover;position:absolute;inset:0;display:block" onerror="this.style.display=\'none\'">',
            False
        )

    # Extract first image URL directly from the blog post content
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
        import re as _re
        return _re.sub(r'[^a-z0-9]', '', s.lower()) if s else ''
    if post.get("related_products") and all_products:
        # Build lookup map from fuzzy product name -> product
        product_map = {}
        for p in all_products:
            if p.get("image"):
                product_map[fuzz(p["name"])] = p
                product_map[fuzz(slugify(p["name"]))] = p
        for rel in post["related_products"]:
            rel_fuzz = fuzz(rel)
            # Exact fuzzy match
            if rel_fuzz in product_map:
                p = product_map[rel_fuzz]
                return (
                    f'<img src="{p["image"]}" alt="{post["title"]}" class="product-img" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block">',
                    True
                )
            # Partial match — either is substring of the other
            for pfuzz, p in product_map.items():
                if len(rel_fuzz) > 5 and (rel_fuzz in pfuzz or pfuzz in rel_fuzz):
                    return (
                        f'<img src="{p["image"]}" alt="{post["title"]}" class="product-img" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block">',
                        True
                    )

    # Category-hint fallback based on title keywords
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

    # ── FEATURED ──────────────────────────────────────────────────
    if featured:
        feat_date = datetime.datetime.strptime(featured["date"], "%Y-%m-%d").strftime("%d %B %Y")
        feat_img_html, _ = get_blog_post_image(featured, all_products)

        if feat_img_html:
            feat_visual = f'<div class="blog-feat-visual" style="overflow:hidden;position:relative">{feat_img_html}</div>'
        else:
            feat_visual = '<div class="blog-feat-visual">📖</div>'

        blog_html += f"""
        <a href="/blog/{featured["slug"]}" class="blog-feat">
          {feat_visual}
          <div class="blog-feat-body">
            <div class="blog-feat-eyebrow">{feat_date} · Featured Guide</div>
            <div class="blog-feat-title">{featured["title"]}</div>
            <div class="blog-feat-desc">{featured.get("description", "")}</div>
            <div class="blog-feat-cta">Read the full guide →</div>
          </div>
        </a>"""

    # ── GRID ──────────────────────────────────────────────────────
    if grid_posts:
        blog_html += """
        <div class="sec-hdr" style="padding:0;margin:0 0 28px">
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
                # Emoji fallback
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
                <div class="blog-card-meta">{date_str}</div>
                <div class="blog-card-title">{post["title"]}</div>
                <div class="blog-card-desc">{post.get("description", "")}</div>
                <div class="blog-card-link">Read article →</div>
              </div>
            </a>"""

        blog_html += "</div>"  # .blog-grid

    # Pagination inside blog wrapper
    if total_pages > 1:
        blog_html += '<div class="pager" style="margin-top:52px;margin-bottom:0">'
        if page > 1: blog_html += f'<a href="{url_for("blog_list", page=page-1)}">← Previous</a>'
        if page < total_pages: blog_html += f'<a href="{url_for("blog_list", page=page+1)}">Next →</a>'
        blog_html += "</div>"

    blog_html += "</div>"  # .blog-wrap

    rendered = render_page(
        title="FyboBuybo Blog – Gift Guides, Tips & Inspiration 2026",
        description="Latest UK gift ideas, seasonal guides, home tips and thoughtful present recommendations.",
        heading="FyboBuybo Blog",
        subtitle="Gift guides, trends and inspiration for UK shoppers",
        products=None, page=page,
    )

    # Inject blog content after PRODUCT GRID comment
    insert = rendered.find("<!-- PRODUCT GRID -->")
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
    <div style="max-width:760px;margin:48px auto 0;padding:0 40px">
      <div style="display:inline-flex;align-items:center;gap:8px;font-size:.69rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--hl);margin-bottom:20px">
        <span style="display:block;width:16px;height:1px;background:var(--hl)"></span>
        {date_str} · Gift Guide
      </div>
      <h1 style="font-family:'Playfair Display',serif;font-size:clamp(1.9rem,4vw,3rem);font-weight:900;line-height:1.1;letter-spacing:-.03em;color:var(--accent);margin-bottom:18px">{post.get("heading", post["title"])}</h1>
      <p style="font-size:1.08rem;line-height:1.75;color:var(--muted);margin-bottom:40px;padding-bottom:36px;border-bottom:1px solid var(--divider)">{post.get("description", "")}</p>
    </div>
    <div style="max-width:760px;margin:0 auto;padding:0 40px 80px">
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
