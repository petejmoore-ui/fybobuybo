#!/usr/bin/env python3
# ============================================================================
# FYBOBUYBO app.py — ELITE REDESIGN v6.0
# COLOUR SYSTEM — "Curated Teal" (2026 Premium Editorial)
# Psychology: Deep Teal trust + Warm neutrals + Coral CTA urgency
# WCAG AA compliant throughout
# v6.0 CHANGES: Full visual redesign — "Elite 2026"
#   - BUG FIX 1: Blog post layout — images/cards now constrained properly
#   - BUG FIX 2: "View Details" button — --primary variable defined, contrast fixed
#   - NEW: Deep teal + warm neutral colour palette with CSS custom properties
#   - NEW: Premium editorial typography (Playfair Display H1 + DM Sans body)
#   - NEW: Enhanced card hover effects with spring easing
#   - NEW: Frosted glass sticky navigation
#   - NEW: Improved dark mode palette
#   - NEW: Blog prose product card grid with proper containment
#   - NEW: Focus states, micro-interactions, lazy loading attributes
#   - All URLs, meta tags, structured data, and content UNCHANGED
# ============================================================================

import os
import json
import re
import datetime
import random
from threading import Thread
from products_data import PRODUCTS
from blog_data import BLOG_POSTS
from flask import Flask, render_template_string, request, url_for, abort, Response, jsonify, redirect
from dotenv import load_dotenv
import requests


load_dotenv()

app = Flask(__name__)

from flask_caching import Cache
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 600
})

from gift_finder import gift_finder_bp
app.register_blueprint(gift_finder_bp)

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
PROMPT_VERSION = "v5.2-trusted-voice-2026"

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
        "name": "Trusted Light",
        "bg": "#f8f9fc",
        "card": "#ffffff",
        "accent": "#0f2044",
        "button": "#e8541a",
        "button_hover": "#c94414",
        "tag": "#eef2ff",
        "text_accent": "#1a2840",
        "text_muted": "#5a6478",
        "gradient": "linear-gradient(135deg, #0f2044 0%, #1e3a6e 100%)",
        "card_gradient": "linear-gradient(135deg, rgba(15,32,68,0.04) 0%, rgba(30,58,110,0.04) 100%)",
        "shadow": "0 4px 12px rgba(15,32,68,0.08)",
        "shadow_hover": "0 8px 24px rgba(15,32,68,0.14)",
        "dropdown_bg": "#ffffff",
        "dropdown_border": "rgba(15,32,68,0.12)",
        "nav_bg": "#ffffff",
        "nav_border": "rgba(15,32,68,0.08)"
    },
    {
        "name": "Trusted Dark",
        "bg": "#0b1120",
        "card": "#131e33",
        "accent": "#e8f0fe",
        "button": "#f06030",
        "button_hover": "#ff7744",
        "tag": "#1a2840",
        "text_accent": "#d4e0f5",
        "text_muted": "#8a9bbf",
        "gradient": "linear-gradient(135deg, #1e3a6e 0%, #0f2044 100%)",
        "card_gradient": "linear-gradient(135deg, rgba(30,58,110,0.14) 0%, rgba(15,32,68,0.14) 100%)",
        "shadow": "0 4px 12px rgba(0,0,0,0.45)",
        "shadow_hover": "0 8px 24px rgba(0,0,0,0.65)",
        "dropdown_bg": "#1a2840",
        "dropdown_border": "rgba(212,224,245,0.12)",
        "nav_bg": "#0b1120",
        "nav_border": "rgba(212,224,245,0.08)"
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


# ============================================================================
# STRUCTURED DATA HELPERS — PATCH v5.2.1
# ============================================================================

def generate_itemlist_schema(products, list_name, list_description=""):
    if not products:
        return None
    items = []
    for idx, p in enumerate(products[:20], 1):
        items.append({
            "@type": "ListItem",
            "position": idx,
            "name": p["name"],
            "url": SITE_URL + "/product/" + slugify(p["name"])
        })
    schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": list_name,
        "numberOfItems": len(items),
        "itemListElement": items
    }
    if list_description:
        schema["description"] = list_description
    return json.dumps(schema, ensure_ascii=False)

def generate_product_schema(product):
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product["name"],
        "description": (product.get("info") or product.get("hook") or "")[:200],
        "image": product.get("image", ""),
        "brand": {"@type": "Brand", "name": extract_brand_name(product["name"])},
        "sku": product.get("asin", ""),
        "url": SITE_URL + "/product/" + slugify(product["name"])
    }
    return json.dumps(schema, ensure_ascii=False)

def generate_breadcrumb_schema(breadcrumbs):
    items = []
    for idx, (name, url) in enumerate(breadcrumbs, 1):
        if not url.startswith('http'): url = SITE_URL + url
        items.append({"@type": "ListItem", "position": idx, "name": name, "item": url})
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}, ensure_ascii=False)

def generate_faq_schema(faqs):
    if not faqs:
        return None
    entries = []
    for faq in faqs:
        if faq.get("q") and faq.get("a"):
            entries.append({
                "@type": "Question",
                "name": faq["q"],
                "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}
            })
    if not entries:
        return None
    return json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entries}, ensure_ascii=False)

def generate_website_schema():
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "FyboBuybo",
        "url": SITE_URL + "/",
        "description": "Independent gift curation for UK shoppers — every pick is hand-chosen.",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": SITE_URL + "/?q={search_term_string}"},
            "query-input": "required name=search_term_string"
        }
    }, ensure_ascii=False)

def generate_organisation_schema():
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "FyboBuybo",
        "url": SITE_URL + "/",
        "logo": SITE_URL + "/static/og-default.jpg",
        "description": "Independent gift curation for UK shoppers. Every pick is hand-chosen, updated daily.",
        "contactPoint": {
            "@type": "ContactPoint",
            "email": "infofybobuybo@gmail.com",
            "contactType": "customer service",
            "areaServed": "GB",
            "availableLanguage": "English"
        },
        "sameAs": []
    }, ensure_ascii=False)

def extract_brand_name(product_name):
    if not product_name:
        return "Various"
    generic_words = {"the", "a", "an", "best", "new", "premium", "luxury",
                     "classic", "original", "set", "pack", "pair", "box"}
    words = product_name.split()
    if not words:
        return "Various"
    first = words[0].strip("'\"")
    if first.lower() in generic_words and len(words) > 1:
        return words[0] + " " + words[1]
    return first

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


# ============================================================================
# CHANGE 7 — get_product_title_suffix()
# ============================================================================

def get_product_title_suffix(product):
    season = product.get("season", "")
    category = product.get("category", "")
    if "Mother's Day" in season:
        return "Gift Idea for Mum"
    elif "Father's Day" in season:
        return "Gift Idea for Dad"
    elif "Valentine's Day" in season:
        return "Romantic Gift Idea"
    elif "Christmas" in season:
        return "Christmas Gift Idea"
    elif "Easter" in season:
        return "Easter Gift Idea"
    elif category in ["Baby"]:
        return "Gift for New Parents"
    elif category in ["Beauty"]:
        return "Beauty Gift Idea"
    elif category in ["Toys & Games"]:
        return "Fun Gift Idea"
    elif category in ["Sports & Outdoors"]:
        return "Active Gift Idea"
    elif category in ["Home & Kitchen"]:
        return "Home Gift Idea"
    elif category in ["Electronics"]:
        return "Tech Gift Idea"
    elif category in ["Books"]:
        return "Book Lover Gift"
    elif category in ["Health & Personal Care"]:
        return "Wellness Gift Idea"
    else:
        return "UK Gift Pick"


# ============================================================================
# HOOK GENERATION — v5.2 "Trusted Voice"
# ============================================================================

def select_hook_type(product):
    category = product.get("category", "").lower()
    price_tier = product.get("price_tier", "").lower()
    rating = product.get("manual_rating")
    reviews = product.get("manual_reviews")
    price = product.get("manual_price", "")
    season = product.get("season", "")

    price_value = 0
    if price:
        price_nums = re.findall(r'\d+\.?\d*', str(price))
        if price_nums:
            price_value = float(price_nums[0])

    if rating:
        try:
            if float(rating) >= 4.5 and reviews:
                review_num = int(re.sub(r'[^\d]', '', str(reviews)) or "0")
                if review_num > 3000:
                    return "social-proof"
        except:
            pass

    if price_tier in ["premium", "luxury"] or price_value > 100:
        return random.choice(["quality-craft", "practical-value", "emotion-led"])

    if season or any(kw in category for kw in ["gift", "present"]):
        return random.choice(["gifting-angle", "emotion-led", "lifestyle-story"])

    if any(kw in category for kw in ["beauty", "skincare", "wellness", "spa", "self-care", "fragrance", "personal"]):
        return random.choice(["lifestyle-story", "emotion-led", "benefit-first"])

    if any(kw in category for kw in ["toy", "game", "puzzle", "lego", "play"]):
        return random.choice(["curiosity", "humour", "benefit-first"])

    if any(kw in category for kw in ["home", "kitchen", "storage", "cleaning", "appliance", "decor", "candle", "comfort", "organisation", "organization"]):
        return random.choice(["problem-solution", "uk-context", "practical-value"])

    if any(kw in category for kw in ["electronic", "tech", "gadget", "device", "smart", "digital"]):
        return random.choice(["benefit-first", "quality-craft", "social-proof"])

    if any(kw in category for kw in ["sport", "fitness", "outdoor", "cycling", "yoga"]):
        return random.choice(["lifestyle-story", "benefit-first", "problem-solution"])

    if any(kw in category for kw in ["baby", "infant", "child", "kid", "nursery"]):
        return random.choice(["emotion-led", "gifting-angle", "social-proof"])

    if price_value > 0 and price_value < 20:
        return random.choice(["practical-value", "social-proof", "gifting-angle"])

    if any(kw in category for kw in ["fashion", "clothing", "apparel", "wear"]):
        return random.choice(["lifestyle-story", "quality-craft", "gifting-angle"])

    return random.choice([
        "benefit-first", "lifestyle-story", "quality-craft",
        "problem-solution", "uk-context", "practical-value",
        "social-proof", "curiosity", "gifting-angle", "emotion-led"
    ])


def generate_hook(product):
    if product.get("hook_override") and product["hook_override"].strip():
        return product["hook_override"].strip()
    return generate_smart_fallback(product)

    name = product["name"]
    category = product.get("category", "")
    keywords = product.get("keywords", [])
    pain_points = product.get("pain_points", [])
    pain_point_text = pain_points[0] if pain_points else "everyday practicality"
    keyword_text = ', '.join(keywords[:3]) if keywords else ""

    style = select_hook_type(product)

    style_instructions = {
        "benefit-first":    "Open with the single most useful thing this pick does for the recipient. Be concrete, not vague.",
        "lifestyle-story":  "Paint a small, relatable scene — who uses this, in what moment, and why it fits their life.",
        "quality-craft":    "Focus on what makes this a genuinely well-made or thoughtfully designed pick compared to cheaper alternatives.",
        "problem-solution": "Identify a real, specific frustration this gift solves — then show how this pick fixes it.",
        "uk-context":       "Anchor the copy in something distinctly British — the weather, a habit, a cultural moment — then connect to the product.",
        "practical-value":  "Make a case for why this is a smart buy: durability, versatility, or price-to-quality ratio.",
        "social-proof":     "Mention (honestly) that this pick is popular or well-reviewed, and briefly explain why that makes sense.",
        "curiosity":        "Start with a question or surprising observation that makes the reader want to know more about this pick.",
        "humour":           "Use a single light, warm observation about everyday life that connects to why this gift works — no forced jokes.",
        "urgency":          "Highlight a genuine time-sensitive context (upcoming occasion, seasonal relevance) — no fake scarcity.",
        "emotion-led":      "Describe the feeling of giving or receiving this — the moment it creates, not just what it is.",
        "gifting-angle":    "Speak directly to the gift-giver: who would love this, why they'd be pleased to give it, what reaction it earns.",
    }
    angle = style_instructions.get(style, style_instructions["benefit-first"])

    prompt = f"""You are a knowledgeable, warm British friend helping someone find the perfect gift. You curate and recommend products — you do NOT sell or own them. Think of yourself as a trusted editor at a gift discovery site.

Write a 1–2 sentence hook for this product listing:

PRODUCT: {name}
CATEGORY: {category}
WRITING ANGLE: {angle}
KEY BENEFIT TO HIGHLIGHT: {pain_point_text}
{f"NATURALLY WEAVE IN (if it fits): {keyword_text}" if keyword_text else ""}

STRICT RULES:
- Never say "our product", "we sell", "we stock", "we make", "we offer" or imply ownership
- Use neutral curation language: "this pick", "this gift", "a great find", "worth considering", "top-rated option"
- Vary your sentence structure — do NOT start with "This is", "Whether", or "If you're looking for"
- Wrap ONE specific feature or benefit in <b>bold tags</b> — only the key phrase, not the whole sentence
- Tone: warm, honest, knowledgeable — like advice from a friend, not a sales pitch
- No hype: avoid "game-changer", "must-have", "essential", "incredible", "amazing", "perfect"
- Be specific — generic praise ("great for anyone") is not acceptable
- 1–2 sentences only. No preamble, no sign-off.

Write the hook now:"""

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

        if hook and not re.search(r'[.!?]$', hook):
            hook += "."

        ownership_phrases = [
            "we sell", "we stock", "our product", "our range",
            "we make", "we offer", "we provide", "our collection",
            "in our store", "from us", "buy from us", "we carry"
        ]
        if any(phrase in hook.lower() for phrase in ownership_phrases):
            print(f"⚠ Ownership language detected in hook for '{name[:40]}', using fallback")
            return generate_smart_fallback(product)

        if hook and 20 < len(hook) < 500:
            return hook

    except Exception as e:
        print(f"⚠ API error for '{name[:50]}...': {e}")

    return generate_smart_fallback(product)


def generate_smart_fallback(product):
    category = product.get("category", "").lower()

    if any(w in category for w in ["beauty", "skincare", "cosmetic", "fragrance", "perfume", "grooming"]):
        fallbacks = [
            "A genuinely lovely pick for anyone who enjoys a <b>proper self-care routine</b> — the kind of gift that gets used every day rather than left on a shelf.",
            "Thoughtfully formulated and <b>well-reviewed by UK shoppers</b>, this is the sort of beauty find that quietly becomes a daily essential.",
            "For the person who's hard to buy for: a <b>considered quality beauty pick</b> that feels indulgent without being over the top.",
        ]
    elif any(w in category for w in ["toy", "game", "puzzle", "play", "board game", "lego"]):
        fallbacks = [
            "This one earns its place in the toy box — <b>genuinely engaging</b> rather than the kind that ends up forgotten after a week.",
            "A top-rated pick for <b>screen-free fun</b> that actually holds attention; parents tend to be just as pleased as the kids.",
            "The sort of gift that sparks <b>hours of creative play</b> — well-made, safe, and refreshingly free of batteries.",
        ]
    elif any(w in category for w in ["home", "kitchen", "cook", "bake", "storage", "organis", "clean", "appliance", "bedding", "linen", "candle", "decor", "comfort"]):
        fallbacks = [
            "A genuinely useful home find that solves a small but <b>surprisingly common household frustration</b> — once you have it, you wonder how you managed without.",
            "Pitched perfectly between practical and thoughtful, this pick makes an <b>ideal housewarming or birthday gift</b> for anyone upgrading their space.",
            "Well-reviewed by UK households and <b>built to last well beyond the warranty</b> — the sort of thing people rebuy when they move.",
        ]
    elif any(w in category for w in ["electronic", "tech", "gadget", "device", "smart", "digital", "camera", "headphone", "speaker", "charger", "laptop", "tablet"]):
        fallbacks = [
            "A strong tech pick that hits a <b>smart balance between features and price</b> — no bloated spec sheet, just what you actually need.",
            "This one consistently earns strong ratings from UK buyers for its <b>reliable everyday performance</b> rather than flashy gimmicks.",
            "For the tech lover who's already got the basics covered: a <b>genuinely useful upgrade</b> that improves something they use every single day.",
        ]
    elif any(w in category for w in ["fashion", "clothing", "apparel", "wear", "bag", "wallet", "accessory", "jewellery", "jewelry", "watch", "shoe"]):
        fallbacks = [
            "A considered fashion pick that works across multiple occasions — the <b>versatility is the real selling point</b> here.",
            "Quality craftsmanship at a fair price point makes this a <b>genuinely satisfying gift to give</b> — or to add to your own wishlist.",
            "The kind of piece that gets complimented and then quietly worn to death: <b>understated, well-made, and endlessly wearable</b>.",
        ]
    elif any(w in category for w in ["sport", "fitness", "exercise", "yoga", "gym", "outdoor", "cycling", "running", "swim"]):
        fallbacks = [
            "A popular pick among UK fitness fans for its <b>durability under regular use</b> — the sort of kit that actually gets used rather than gathering dust.",
            "Ideal for anyone who's been meaning to start (or get back to) regular training: <b>genuinely encouraging to use</b>, not just to own.",
            "Trusted by people who take their health seriously — this pick earns its place with <b>solid performance at a reasonable price</b>.",
        ]
    elif any(w in category for w in ["baby", "infant", "nursery", "newborn", "toddler", "child", "kid"]):
        fallbacks = [
            "A thoughtfully designed pick that parents genuinely rely on — <b>safety-tested, easy to use</b>, and built for the realities of early parenthood.",
            "For the new parents who already have the basics: a <b>genuinely useful addition</b> that makes the early months noticeably easier.",
            "Well-loved by UK families and <b>easy to clean</b> — two things that matter far more than they sound once you have a baby in the house.",
        ]
    elif any(w in category for w in ["book", "stationary", "stationery", "journal", "pen", "notebook", "read", "writing"]):
        fallbacks = [
            "A lovely pick for anyone who still believes <b>a well-chosen book</b> is one of the best gifts you can give.",
            "For the person who has everything: something they'll actually sit down with and enjoy — <b>no batteries, no setup, no returns</b>.",
            "A considered gift for thinkers, readers, and the creatively inclined — <b>beautifully presented</b> and built to last.",
        ]
    elif any(w in category for w in ["pet", "dog", "cat", "animal"]):
        fallbacks = [
            "A top-rated pet pick that solves a <b>genuine day-to-day problem</b> for owners — the kind you'd happily recommend to a friend.",
            "Well-reviewed by UK pet owners who appreciate that <b>their animals are fussy customers too</b> — this one actually passes the test.",
            "Because pets deserve a thoughtful pick too: this find offers <b>genuine quality at a fair price</b> for the animal you're shopping for.",
        ]
    elif any(w in category for w in ["food", "drink", "coffee", "tea", "wine", "chocolate", "snack", "gourmet"]):
        fallbacks = [
            "A brilliant option for anyone who appreciates <b>the finer things in the kitchen or at the table</b> — enjoyable to give and even better to receive.",
            "For the foodie on your list: a <b>genuinely considered pick</b> that goes well beyond the usual supermarket hamper.",
            "The sort of edible gift that <b>signals real thought</b> — not just a last-minute grab from the confectionery aisle.",
        ]
    else:
        fallbacks = [
            "A <b>well-reviewed UK pick</b> that earns its recommendation through consistent quality and practical everyday value.",
            "Consistently popular with UK shoppers for a reason: <b>it simply does what it promises</b>, without any fuss.",
            "Worth considering for anyone who values quality over novelty — this find <b>holds up well over time</b> and rarely disappoints.",
        ]

    idx = hash(product.get("name", "")) % len(fallbacks)
    return fallbacks[idx]


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def should_refresh_cache():
    if not os.path.exists(CACHE_FILE): return True
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache_data = json.load(f)
        days_old = (datetime.datetime.now() - datetime.datetime.fromisoformat(cache_data.get("date", "2000-01-01T00:00:00"))).days
        return days_old >= CACHE_REFRESH_DAYS or cache_data.get("prompt_version") != PROMPT_VERSION
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
# CSS TEMPLATE — v6.0 "Curated Teal" — Elite 2026 Redesign
# ============================================================================
# CHANGES FROM v5.2:
#   - NEW colour palette: deep teal primary (#0d6e6e), warm off-white bg (#faf9f7)
#   - --primary variable NOW DEFINED (fixes Bug Fix 2)
#   - Blog prose: product card images constrained (fixes Bug Fix 1)
#   - Typography: Playfair Display for H1 headings, DM Sans body
#   - Enhanced card shadows, hover spring easing, frosted glass nav
#   - All colours via CSS custom properties — zero hardcoded hex in rules
#   - Dark mode fully updated for teal palette
#   - Focus states: outline with primary colour + offset on all interactive elements
#   - .btn-detail contrast fixed for light mode (Bug Fix 2)
# ============================================================================

CSS_TEMPLATE = """<style>
:root {
  /* ── Core palette ─────────────────────────────────────────── */
  --bg:           #faf9f7;
  --bg-2:         #f0ede8;
  --bg-3:         #e5e2dd;
  --card:         #ffffff;
  --card-2:       #f7f5f2;
  --ink:          #1a1a1a;
  --ink-2:        #2d2d2d;
  --ink-3:        #444444;
  --muted:        #6b6560;
  --muted-2:      #8a857f;

  /* ── Brand: Deep Teal ─────────────────────────────────────── */
  --primary:      #0d6e6e;
  --primary-2:    #0a5858;
  --primary-3:    #108585;
  --primary-dim:  rgba(13,110,110,0.08);
  --primary-line: rgba(13,110,110,0.22);

  /* ── Accent: Slate (secondary) ────────────────────────────── */
  --slate:        #4a6f6f;
  --slate-2:      #5a8a8a;
  --slate-dim:    rgba(74,111,111,0.10);
  --slate-line:   rgba(74,111,111,0.25);

  /* ── CTA: Coral/Orange ────────────────────────────────────── */
  --cta:          #e8541a;
  --cta-fg:       #ffffff;
  --cta-hover:    #c94414;
  --cta-dim:      rgba(232,84,26,0.09);
  --cta-line:     rgba(232,84,26,0.30);

  /* ── Utility ──────────────────────────────────────────────── */
  --green:        #1a8c5b;
  --green-dim:    rgba(26,140,91,0.10);
  --border:       #e5e2dd;
  --border-2:     #d4d0ca;
  --divider:      rgba(26,26,26,0.06);
  --nav-bg:       rgba(250,249,247,0.92);
  --input-bg:     rgba(255,255,255,0.90);

  /* ── Badge (warm sage) ────────────────────────────────────── */
  --badge-bg:     #e8f0ec;
  --badge-fg:     #2d6b4f;

  /* ── Shadows ──────────────────────────────────────────────── */
  --sh-xs:  0 1px 3px rgba(0,0,0,0.04), 0 2px 6px rgba(0,0,0,0.03);
  --sh-sm:  0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
  --sh-md:  0 4px 20px rgba(0,0,0,0.07), 0 12px 40px rgba(0,0,0,0.06);
  --sh-lg:  0 8px 32px rgba(0,0,0,0.10);
  --sh-xl:  0 16px 56px rgba(0,0,0,0.14);
  --sh-cta: 0 4px 16px rgba(232,84,26,0.30), 0 2px 6px rgba(232,84,26,0.18);

  /* ── Radii ────────────────────────────────────────────────── */
  --r-sm:  8px;
  --r-md:  12px;
  --r-lg:  16px;
  --r-xl:  20px;
  --r-pill:99px;

  /* ── Easing ───────────────────────────────────────────────── */
  --ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* ── Dark mode ──────────────────────────────────────────────── */
.dark {
  --bg:           #0f0f0f;
  --bg-2:         #1a1a1a;
  --bg-3:         #242424;
  --card:         #1c1c1e;
  --card-2:       #242426;
  --ink:          #f5f5f5;
  --ink-2:        #e0e0e0;
  --ink-3:        #b0b0b0;
  --muted:        #8a8a8a;
  --muted-2:      #6a6a6a;
  --primary:      #14a3a3;
  --primary-2:    #17bfbf;
  --primary-3:    #0f8888;
  --primary-dim:  rgba(20,163,163,0.12);
  --primary-line: rgba(20,163,163,0.30);
  --slate:        #5a9e9e;
  --slate-2:      #6fb8b8;
  --slate-dim:    rgba(90,158,158,0.12);
  --slate-line:   rgba(90,158,158,0.28);
  --cta:          #f06030;
  --cta-fg:       #ffffff;
  --cta-hover:    #ff7744;
  --cta-dim:      rgba(240,96,48,0.12);
  --cta-line:     rgba(240,96,48,0.35);
  --green:        #22a86e;
  --green-dim:    rgba(34,168,110,0.12);
  --border:       #2a2a2a;
  --border-2:     #3a3a3a;
  --divider:      rgba(255,255,255,0.06);
  --nav-bg:       rgba(15,15,15,0.95);
  --input-bg:     rgba(255,255,255,0.06);
  --badge-bg:     rgba(20,163,163,0.14);
  --badge-fg:     #14a3a3;
  --sh-xs:  0 1px 3px rgba(0,0,0,0.40), 0 2px 6px rgba(0,0,0,0.35);
  --sh-sm:  0 2px 8px rgba(0,0,0,0.45), 0 4px 18px rgba(0,0,0,0.40);
  --sh-md:  0 4px 20px rgba(0,0,0,0.52), 0 12px 40px rgba(0,0,0,0.48);
  --sh-lg:  0 8px 36px rgba(0,0,0,0.60);
  --sh-xl:  0 16px 56px rgba(0,0,0,0.70);
  --sh-cta: 0 4px 16px rgba(240,96,48,0.40), 0 2px 6px rgba(240,96,48,0.25);
}

/* ── Reset ──────────────────────────────────────────────────── */
*,*::before,*::after { margin:0; padding:0; box-sizing:border-box; }
html { scroll-behavior:smooth; -webkit-text-size-adjust:100%; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: 'DM Sans', system-ui, -apple-system, sans-serif;
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

/* ── Focus states (accessibility) ───────────────────────────── */
:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* ── Subtle noise texture ───────────────────────────────────── */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.025'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 0;
  opacity: .35;
}

/* ── Ticker ribbon ──────────────────────────────────────────── */
.ribbon {
  position: relative;
  z-index: 10;
  background: var(--primary);
  color: rgba(255,255,255,0.85);
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
  color: rgba(255,255,255,0.5);
  padding: 0 2px;
}
@keyframes ticker {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); }
}
.ribbon:hover .ribbon-track { animation-play-state: paused; }

/* ── Navigation — frosted glass ─────────────────────────────── */
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
  border-bottom-color: var(--border-2);
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

.nav-logo {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 1.75rem;
  font-weight: 600;
  letter-spacing: -.02em;
  color: var(--primary);
  flex-shrink: 0;
  margin-right: 16px;
  transition: opacity .2s;
  display: flex;
  align-items: baseline;
  gap: 1px;
}
.nav-logo:hover { opacity: .80; }
.nav-logo .logo-fybo  { color: var(--primary); }
.nav-logo .logo-buybo { color: var(--cta); font-style: italic; }
.nav-logo .logo-dot {
  display: inline-block;
  width: 5px; height: 5px;
  background: var(--cta);
  border-radius: 50%;
  margin: 0 1px 4px;
  flex-shrink: 0;
}

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
  color: var(--primary);
  background: var(--primary-dim);
}

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
  color: var(--primary);
  background: var(--primary-dim);
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
  background: var(--primary-dim);
  color: var(--primary);
  padding-left: 18px;
}

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
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-dim);
  background: var(--card);
}
.nav-search input::placeholder { color: var(--muted-2); }
.nav-search input:focus + .nav-search-icon,
.nav-search-wrap:focus-within .nav-search-icon { stroke: var(--primary); }

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
  background: var(--primary-dim);
  border-color: var(--primary-line);
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

/* ── Mobile menu ────────────────────────────────────────────── */
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
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 2.4rem;
  font-weight: 500;
  color: var(--ink);
  padding: 12px 0;
  border-bottom: 1px solid var(--divider);
  display: block;
  transition: color .2s, padding-left .2s;
  letter-spacing: -.03em;
}
.mm-link:hover { color: var(--primary); padding-left: 8px; }
.mm-section { margin-bottom: 28px; }
.mm-label {
  font-size: .66rem;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--primary);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.mm-label::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--primary-line);
}
.mm-pills { display: flex; flex-wrap: wrap; gap: 8px; }
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
  background: var(--primary-dim);
  border-color: var(--primary-line);
  color: var(--primary);
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
.mm-search-wrap input:focus { border-color: var(--primary); }
.mm-search-wrap input::placeholder { color: var(--muted-2); }

/* ── Hero ───────────────────────────────────────────────────── */
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
  background: linear-gradient(135deg, var(--bg) 0%, var(--bg-2) 100%);
}
.hero::before {
  content: '01';
  position: absolute;
  right: 52px;
  top: 20px;
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: clamp(120px, 15vw, 200px);
  font-weight: 700;
  color: var(--primary);
  opacity: .04;
  pointer-events: none;
  line-height: 1;
  letter-spacing: -.05em;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: .68rem;
  font-weight: 600;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: var(--primary);
  margin-bottom: 24px;
}
.hero-eyebrow::before {
  content: '';
  display: block;
  width: 28px;
  height: 1px;
  background: var(--primary);
}

.hero-h1 {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
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
  color: var(--primary);
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
  box-shadow: var(--sh-cta);
}
.btn-primary:hover {
  background: var(--cta-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(232,84,26,0.42), 0 4px 10px rgba(232,84,26,0.24);
}

.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: var(--primary);
  padding: 14px 22px;
  border-radius: var(--r-pill);
  font-size: .9rem;
  font-weight: 500;
  border: 1px solid var(--primary-line);
  transition: all .2s;
  letter-spacing: -.01em;
}
.btn-ghost:hover {
  background: var(--primary-dim);
  border-color: var(--primary);
  color: var(--primary-2);
}

.hero-stats {
  display: flex;
  gap: 32px;
  margin-top: 44px;
  padding-top: 36px;
  border-top: 1px solid var(--divider);
  animation: riseUp .9s .28s var(--ease-out) both;
}
.hero-stat-num {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 2.2rem;
  font-weight: 600;
  color: var(--ink);
  line-height: 1;
  letter-spacing: -.04em;
}
.hero-stat-num span { color: var(--cta); }
.hero-stat-label {
  font-size: .74rem;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: .04em;
  text-transform: uppercase;
  margin-top: 4px;
}

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

.hero-ornament {
  position: absolute;
  top: -18px;
  right: -18px;
  width: 68px;
  height: 68px;
  border-radius: 50%;
  background: var(--cta);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--sh-md), 0 0 0 8px var(--cta-dim);
  animation: pulse 3s ease-in-out infinite;
  z-index: 2;
}
.hero-ornament span {
  font-size: .6rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: #ffffff;
  text-align: center;
  line-height: 1.3;
}
@keyframes pulse {
  0%,100% { box-shadow: var(--sh-md), 0 0 0 8px var(--cta-dim); }
  50%      { box-shadow: var(--sh-md), 0 0 0 14px var(--cta-dim); }
}

/* ── Affiliate disclosure strip ─────────────────────────────── */
.affil-strip {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 52px 16px;
}
.affil-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--primary-dim);
  border: 1px solid var(--primary-line);
  border-radius: var(--r-md);
  padding: 10px 18px;
  font-size: .8rem;
  color: var(--muted);
  line-height: 1.5;
}
.affil-inner strong { color: var(--ink-3); font-weight: 600; }
.affil-inner a { color: var(--primary); font-weight: 500; }
.affil-icon {
  flex-shrink: 0;
  width: 14px; height: 14px;
  stroke: var(--primary);
  fill: none;
  stroke-width: 2;
}

/* ── Category rail ──────────────────────────────────────────── */
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
  background: var(--primary-dim);
  border-color: var(--primary-line);
  color: var(--primary);
  transform: translateY(-1px);
  box-shadow: var(--sh-xs);
}

/* ── Section headers ────────────────────────────────────────── */
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
  color: var(--primary);
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
  background: var(--primary);
}
.sec-title {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: clamp(1.8rem, 3vw, 2.8rem);
  font-weight: 600;
  letter-spacing: -.04em;
  line-height: 1.05;
  color: var(--ink);
}
.sec-title em { font-style: italic; color: var(--primary); }
.sec-view-all {
  font-size: .82rem;
  font-weight: 600;
  color: var(--primary);
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
  border-color: var(--primary);
  gap: 10px;
}

/* ── Product grid ───────────────────────────────────────────── */
.grid {
  max-width: 1600px;
  margin: 28px auto 0;
  padding: 0 52px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

/* ── Product cards ──────────────────────────────────────────── */
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
  transform: translateY(-6px);
  box-shadow: var(--sh-lg);
  border-color: var(--border-2);
}

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
  background: linear-gradient(to bottom, transparent 60%, rgba(0,0,0,0.02) 100%);
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

.card-badge {
  position: absolute;
  bottom: 12px;
  left: 12px;
  background: var(--badge-bg);
  border: 1px solid var(--primary-line);
  border-radius: var(--r-pill);
  padding: 4px 12px;
  font-size: .65rem;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--badge-fg);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  z-index: 2;
}

.card-quick {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: var(--cta);
  color: #ffffff;
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
  color: var(--primary);
  margin-bottom: 7px;
}

.card-name {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 1.12rem;
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -.02em;
  color: var(--ink);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 10px;
  transition: color .18s;
}
.card-name:hover { color: var(--primary); }

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

.card-rating {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 14px;
  font-size: .78rem;
  color: var(--muted);
}
.card-stars {
  color: var(--green);
  font-size: .85rem;
  letter-spacing: -.06em;
  line-height: 1;
}

.card-div {
  height: 1px;
  background: var(--divider);
  margin: 0 0 14px;
}

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
  box-shadow: var(--sh-cta);
}
.btn-amz:hover {
  background: var(--cta-hover);
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(232,84,26,0.38), 0 3px 8px rgba(232,84,26,0.22);
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

/* ── BUG FIX 2: .btn-detail contrast fixed ──────────────────── */
/* Was: color:var(--muted) which is fine, but article .card button
   styles referenced undefined --primary, causing invisible text.
   Now --primary is defined, AND .btn-detail explicitly uses
   high-contrast colours in both light and dark modes. */
.btn-detail {
  display: block;
  text-align: center;
  font-size: .79rem;
  font-weight: 600;
  color: var(--primary);
  padding: 8px;
  border: 1px solid var(--primary-line);
  border-radius: var(--r-sm);
  transition: all .2s;
  letter-spacing: -.01em;
}
.btn-detail:hover {
  color: var(--card);
  border-color: var(--primary);
  background: var(--primary);
}

/* ── Blog section ───────────────────────────────────────────── */
.blog-wrap {
  max-width: 1600px;
  margin: 52px auto 0;
  padding: 0 52px;
}
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
  color: var(--primary);
}
.blog-feat-label::before {
  content: '';
  display: block;
  width: 16px;
  height: 1px;
  background: var(--primary);
}
.blog-feat-title {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
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
  color: var(--cta);
  margin-top: 4px;
  padding-bottom: 2px;
  border-bottom: 1px solid var(--cta-line);
  width: fit-content;
  transition: gap .2s, border-color .2s;
  letter-spacing: -.01em;
}
.blog-feat-cta:hover { gap: 16px; border-color: var(--cta); }

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
  color: var(--primary);
  display: flex;
  align-items: center;
  gap: 8px;
}
.blog-card-date::before {
  content: '';
  display: block;
  width: 14px;
  height: 1px;
  background: var(--primary);
}
.blog-card-title {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
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
  color: var(--cta);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  transition: gap .2s;
}
.blog-card:hover .blog-card-link { gap: 10px; }

/* ── Blog prose ─────────────────────────────────────────────── */
/* BUG FIX 1: Added containment rules for images and product cards
   within blog post content. Images are now constrained to their
   container width, product card grids use proper CSS Grid with
   overflow:hidden, and all child elements respect max-width. */
.blog-prose {
  font-size: 1.02rem;
  line-height: 1.88;
  color: var(--ink-3);
  font-weight: 300;
  letter-spacing: -.005em;
  overflow-wrap: break-word;
  word-wrap: break-word;
}
.blog-prose h2 {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 1.9rem;
  font-weight: 600;
  color: var(--ink);
  margin: 56px 0 18px;
  letter-spacing: -.04em;
  line-height: 1.15;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--divider);
  padding-left: 16px;
  border-left: 3px solid var(--primary);
}
.blog-prose h3 {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 1.45rem;
  font-weight: 600;
  color: var(--ink);
  margin: 40px 0 14px;
  letter-spacing: -.03em;
}
.blog-prose h4 {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--ink);
  margin: 30px 0 10px;
}
.blog-prose p { margin-bottom: 22px; }
.blog-prose a {
  color: var(--primary);
  font-weight: 500;
  border-bottom: 1px solid var(--primary-line);
  transition: border-color .2s, color .2s;
}
.blog-prose a:hover { color: var(--primary-2); border-color: var(--primary-2); }
.blog-prose strong { color: var(--ink-2); font-weight: 600; }
.blog-prose ul,.blog-prose ol { margin: 0 0 26px; padding-left: 0; list-style: none; }
.blog-prose li { padding-left: 24px; position: relative; margin-bottom: 10px; line-height: 1.75; }
.blog-prose ul li::before {
  content: '';
  position: absolute;
  left: 0; top: 12px;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--primary);
}
.blog-prose ol { counter-reset: ol; }
.blog-prose ol li { counter-increment: ol; }
.blog-prose ol li::before {
  content: counter(ol);
  position: absolute;
  left: 0; top: 3px;
  font-size: .72rem;
  font-weight: 700;
  color: var(--primary);
  font-family: 'DM Sans', sans-serif;
}

/* BUG FIX 1: Image containment within blog prose */
.blog-prose img {
  width: 100%;
  max-width: 100%;
  height: auto;
  border-radius: var(--r-lg);
  margin: 40px 0;
  box-shadow: var(--sh-md);
  object-fit: cover;
}

.blog-prose blockquote {
  border-left: 3px solid var(--primary);
  margin: 40px 0;
  padding: 20px 28px;
  background: var(--primary-dim);
  border-radius: 0 var(--r-md) var(--r-md) 0;
  font-style: italic;
  color: var(--muted);
  font-size: 1.08rem;
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-weight: 400;
}
.blog-prose table { width: 100%; border-collapse: collapse; margin: 34px 0; font-size: .92rem; }
.blog-prose th {
  background: var(--bg-2);
  padding: 13px 18px;
  text-align: left;
  font-weight: 600;
  color: var(--ink);
  border-bottom: 2px solid var(--primary-line);
  font-family: 'DM Sans', sans-serif;
  letter-spacing: -.01em;
  font-size: .84rem;
}
.blog-prose td { padding: 12px 18px; border-bottom: 1px solid var(--divider); color: var(--ink-3); }
.blog-prose tr:last-child td { border-bottom: none; }

/* BUG FIX 1: Product cards inside blog posts — proper grid and containment */
/* BUG FIX 1: Override inline max-width:600px on blog product cards.
   blog_data.py cards use style='max-width:600px;margin:20px auto' which
   squeezes content into a narrow column. !important overrides inline styles. */
.blog-prose .card {
  overflow: hidden;
  max-width: 100% !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
}
.blog-prose .card img {
  width: 100%;
  height: auto;
  max-height: 420px;
  object-fit: contain;
  border-radius: var(--r-sm);
  margin: 0;
  box-shadow: none;
  padding: 20px;
  background: var(--bg-2);
}
.blog-prose .card div[style*='display:grid'],
.blog-prose .card div[style*='display: grid'] {
  overflow: hidden;
}

.blog-prose .blog-btn-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin: 28px 0;
  justify-content: center;
}
.blog-prose .blog-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: var(--r-pill);
  font-size: .875rem;
  font-weight: 600;
  font-family: 'DM Sans', sans-serif;
  letter-spacing: -.01em;
  cursor: pointer;
  transition: all .22s var(--ease-out);
  text-decoration: none !important;
  border: none;
}
.blog-prose .blog-btn-primary {
  background: var(--cta);
  color: #ffffff;
  box-shadow: var(--sh-cta);
}
.blog-prose .blog-btn-primary:hover {
  background: var(--cta-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(232,84,26,0.40);
  color: #ffffff;
  border-bottom-color: transparent;
}
.blog-prose .blog-btn-secondary {
  background: var(--card);
  color: var(--primary);
  border: 1.5px solid var(--primary-line) !important;
  box-shadow: var(--sh-xs);
}
.blog-prose .blog-btn-secondary:hover {
  background: var(--primary-dim);
  border-color: var(--primary) !important;
  transform: translateY(-2px);
  color: var(--primary-2);
  border-bottom-color: var(--primary) !important;
}

/* ── Similar products section ───────────────────────────────── */
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
  transition: transform .26s var(--ease-spring), box-shadow .26s ease, border-color .2s;
  box-shadow: var(--sh-xs);
  color: inherit;
}
.sim-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--sh-md);
  border-color: var(--primary-line);
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
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: .9rem;
  font-weight: 600;
  color: var(--ink-3);
  line-height: 1.35;
  padding: 12px 14px;
  letter-spacing: -.015em;
}

/* ── Product detail ─────────────────────────────────────────── */
.pd-wrap {
  max-width: 1100px;
  margin: 52px auto 0;
  padding: 0 52px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: start;
}
.pd-gallery { position: sticky; top: 84px; }
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
.pd-breadcrumb a { color: var(--primary); transition: opacity .2s; }
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
  color: var(--primary);
}
.pd-cat-tag::before {
  content: '';
  display: block;
  width: 18px;
  height: 1px;
  background: var(--primary);
}
.pd-title {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
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
.pd-divider { height: 1px; background: var(--divider); }
.pd-price-note {
  background: var(--primary-dim);
  border: 1px solid var(--primary-line);
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
  box-shadow: var(--sh-cta);
  letter-spacing: -.02em;
}
.btn-pd-amz:hover {
  background: var(--cta-hover);
  transform: translateY(-2px);
  box-shadow: 0 10px 32px rgba(232,84,26,0.42), 0 4px 12px rgba(232,84,26,0.24);
}
.btn-pd-amz em { font-style: italic; font-weight: 800; font-size: 1.1em; }
.btn-pd-amz svg { width: 15px; height: 15px; stroke: currentColor; fill: none; stroke-width: 2; }
.pd-trust-row { display: flex; gap: 16px; flex-wrap: wrap; }
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
  stroke: var(--green);
  fill: none;
  stroke-width: 2;
  flex-shrink: 0;
}

/* ── Pagination ─────────────────────────────────────────────── */
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
  background: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
  box-shadow: var(--sh-sm);
  transform: translateY(-1px);
}

/* ── Legal pages ────────────────────────────────────────────── */
.legal-article {
  max-width: 820px;
  margin: 52px auto;
  padding: 0 52px 80px;
}
.legal-article h2 {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 1.65rem;
  font-weight: 600;
  color: var(--ink);
  margin: 48px 0 16px;
  letter-spacing: -.04em;
}
.legal-article h3 {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
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
  background: var(--primary-dim);
  border: 1px solid var(--primary-line);
  border-radius: var(--r-lg);
  padding: 20px 24px;
  margin-top: 18px;
}

/* ── Share bar ───────────────────────────────────────────────── */
.share-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 20px 0;
  margin: 36px 0 0;
  border-top: 1px solid var(--divider);
}
.share-label {
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--muted);
  margin-right: 4px;
}
.share-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 16px;
  border-radius: var(--r-pill);
  font-family: 'DM Sans', sans-serif;
  font-size: .78rem;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: all .2s;
  letter-spacing: -.01em;
}
.share-btn svg { width: 14px; height: 14px; fill: currentColor; flex-shrink: 0; }
.share-wa { background: #25D366; color: #fff; }
.share-wa:hover { background: #1ebe59; transform: translateY(-1px); }
.share-fb { background: #1877F2; color: #fff; }
.share-fb:hover { background: #0d6ae0; transform: translateY(-1px); }
.share-x { background: #000000; color: #fff; }
.share-x:hover { background: #333; transform: translateY(-1px); }
.share-em { background: var(--card); color: var(--ink-3); border: 1px solid var(--border); }
.share-em:hover { background: var(--bg-2); transform: translateY(-1px); color: var(--ink); }
.share-copy { background: var(--card); color: var(--ink-3); border: 1px solid var(--border); }
.share-copy:hover { background: var(--bg-2); transform: translateY(-1px); color: var(--ink); }
.share-copy.copied { background: var(--green); color: #fff; border-color: var(--green); }

/* ── Footer ─────────────────────────────────────────────────── */
.site-footer {
  margin-top: 100px;
  background: #1a1a1a;
  border-top: none;
  color: rgba(245,245,245,0.75);
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
.footer-logo {
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 1.8rem;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: -.03em;
  margin-bottom: 14px;
  display: flex;
  align-items: baseline;
  gap: 2px;
}
.footer-logo em { color: var(--cta); font-style: italic; }
.footer-desc {
  font-size: .87rem;
  line-height: 1.78;
  color: rgba(245,245,245,0.55);
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
  color: var(--cta);
}
.footer-tagline::before {
  content: '';
  display: block;
  width: 16px;
  height: 1px;
  background: var(--cta);
}
.footer-col-title {
  font-size: .67rem;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: rgba(245,245,245,0.35);
  margin-bottom: 18px;
}
.footer-col a {
  display: block;
  font-size: .875rem;
  color: rgba(245,245,245,0.60);
  margin-bottom: 10px;
  transition: color .2s, padding-left .2s;
  font-weight: 400;
  letter-spacing: -.01em;
}
.footer-col a:hover { color: #ffffff; padding-left: 5px; }
.footer-divider {
  height: 1px;
  background: rgba(245,245,245,0.08);
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
  color: rgba(245,245,245,0.40);
  line-height: 1.65;
  font-weight: 300;
}
.footer-amz-note {
  font-size: .73rem;
  color: rgba(245,245,245,0.30);
  font-style: italic;
}

/* ── Search overlay ─────────────────────────────────────────── */
#search-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(15,15,15,0.80);
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
  font-family: 'Playfair Display', 'Cormorant Garamond', serif;
  font-size: 1.65rem;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -.04em;
}
.search-close-btn {
  width: 38px; height: 38px;
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
  background: var(--primary-dim);
  border-color: var(--primary-line);
  color: var(--primary);
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

/* ── Cookie consent ─────────────────────────────────────────── */
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
.cookie-text a { color: var(--primary); font-weight: 500; }
.cookie-btns { display: flex; gap: 8px; flex-shrink: 0; }
.btn-cookie-ok {
  background: var(--cta);
  color: #ffffff;
  border: none;
  border-radius: var(--r-md);
  padding: 9px 18px;
  font-size: .82rem;
  font-weight: 600;
  font-family: inherit;
  transition: opacity .2s, background .2s;
}
.btn-cookie-ok:hover { background: var(--cta-hover); }
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
  border-color: var(--primary-line);
  color: var(--primary);
}

/* ── Scroll reveal ──────────────────────────────────────────── */
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity .65s var(--ease-out), transform .65s var(--ease-out);
}
.reveal.in-view { opacity: 1; transform: translateY(0); }

/* ── Responsive ─────────────────────────────────────────────── */
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

/* ── Scrollbar ──────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }

::selection { background: var(--primary-dim); color: var(--primary); }

/* ── BUG FIX 2: Article card buttons — --primary is now defined ──
   These rules target product pick buttons inside blog post content.
   The original code referenced var(--primary) which was undefined,
   causing white text on a transparent/fallback background.
   Now --primary resolves to #0d6e6e (light) / #14a3a3 (dark). */
article .card button {
    display: inline-block;
    padding: 12px 28px;
    border-radius: 50px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.22s ease;
    letter-spacing: 0.4px;
    white-space: nowrap;
    font-family: inherit;
    line-height: 1;
}
article .card a[href^='/product'] button,
article .card a[href^='/product/'] button {
    background: var(--primary);
    color: #fff;
    border-color: var(--primary);
}
article .card a[href^='/product'] button:hover,
article .card a[href^='/product/'] button:hover {
    background: transparent;
    color: var(--primary);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
}
article .card a[href*='amzn.to'] button,
article .card a[href*='amazon.co.uk'] button,
article .card a[href*='amazon.com'] button {
    background: #ff9900 !important;
    color: #111 !important;
    border-color: #ff9900 !important;
}
article .card a[href*='amzn.to'] button:hover,
article .card a[href*='amazon.co.uk'] button:hover,
article .card a[href*='amazon.com'] button:hover {
    background: #e68900 !important;
    border-color: #e68900 !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(255,153,0,0.4);
}
article .card div[style*='display:flex'][style*='justify-content:center'] {
    gap: 14px !important;
    flex-wrap: wrap;
    padding-top: 8px;
}
article .card a[href^='/product'],
article .card a[href*='amzn.to'],
article .card a[href*='amazon'] {
    text-decoration: none;
}
</style>"""



# ============================================================================
# BASE HTML TEMPLATE — v6.0
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
<meta property="og:type" content="{{ og_type }}">
<meta property="og:url" content="{{ canonical_url }}">
<meta property="og:site_name" content="FyboBuybo">
<meta property="og:locale" content="en_GB">
<meta property="og:image" content="{% if products and products|length > 0 and products[0].image %}{{ products[0].image }}{% else %}{{ SITE_URL }}/static/og-default.jpg{% endif %}">
<meta name="google-site-verification" content="googleb2fd2d2e239922f5">
<meta name="twitter:card" content="summary_large_image">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://m.media-amazon.com">
<link rel="preload" as="style"
  href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600;1,700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300;1,9..40,400&display=swap"
  onload="this.onload=null;this.rel='stylesheet'">
<noscript>
  <link rel="stylesheet"
    href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600;1,700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300;1,9..40,400&display=swap">
</noscript>

{% if structured_data %}<script type="application/ld+json">{{ structured_data|safe }}</script>{% endif %}
{% if breadcrumb_schema %}<script type="application/ld+json">{{ breadcrumb_schema|safe }}</script>{% endif %}
{% if faq_schema %}<script type="application/ld+json">{{ faq_schema|safe }}</script>{% endif %}
{% if website_schema %}<script type="application/ld+json">{{ website_schema|safe }}</script>{% endif %}
{% if itemlist_schema %}<script type="application/ld+json">{{ itemlist_schema|safe }}</script>{% endif %}
{% if organisation_schema %}<script type="application/ld+json">{{ organisation_schema|safe }}</script>{% endif %}

{{ css|safe }}
</head>
<body>

<!-- ═══ TICKER RIBBON ═══════════════════════════════════════════ -->
<div class="ribbon" aria-hidden="true" role="marquee">
  <div class="ribbon-track">
    {% for _ in range(2) %}
    <span>Hand-picked for UK Shoppers</span><span class="sep">✦</span>
    <span>Gift Curation</span><span class="sep">✦</span>
    <span>No Ads · No Sponsored Picks</span><span class="sep">✦</span>
    <span>Refreshed Every Day</span><span class="sep">✦</span>
    <span>Top-Rated Finds · 2026</span><span class="sep">✦</span>
    {% endfor %}
  </div>
</div>

<!-- ═══ NAVIGATION ══════════════════════════════════════════════ -->
<header class="site-nav" id="site-nav">
  <div class="nav-inner">

    <a href="/" class="nav-logo" aria-label="FyboBuybo Home">
      <span class="logo-fybo">Fybo</span><span class="logo-buybo">Buybo</span>
    </a>

    <nav class="nav-links" aria-label="Primary navigation">
      <a href="/">Home</a>
      <a href="/blog">Blog</a>
      <a href="/gift-finder">Gift Finder</a>

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
    <a href="/gift-finder" class="mm-link" tabindex="-1">Gift Finder</a>
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
      <span class="line-2">{{ "Curated, daily" }}</span>
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
      <img src="{{ products[0].image }}" alt="{{ products[0].name }}"
           loading="eager" fetchpriority="high" width="480" height="480">
    </div>
    <div class="hero-img-float">
      <img src="{{ products[1].image }}" alt="{{ products[1].name }}"
           loading="lazy" width="240" height="240">
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
    <span><strong>Affiliate Disclosure:</strong> This site earns a small commission when you buy through our links — at no extra cost to you. It's how we keep the curation going. <a href="/privacy-policy">Learn more →</a></span>
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

{% if content %}{{ content|safe }}{% endif %}

<!-- ═══ SECTION HEADER ══════════════════════════════════════════ -->
{% if products and products|length > 1 %}
<div class="sec-hdr reveal" id="picks">
  <div>
    <div class="sec-eyebrow">Carefully curated · updated daily</div>
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
  <article class="card reveal" style="animation-delay:{{ loop.index0 * 0.04 }}s" role="listitem">
    <div class="card-img">
      <span class="card-badge">{{ p.category }}</span>
      <a href="/product/{{ slugify(p.name) }}" tabindex="-1" aria-hidden="true">
        <img src="{{ p.image }}" alt="{{ p.name }}" loading="lazy" width="400" height="400">
      </a>
      <div class="card-quick" aria-hidden="true">
        <svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
      </div>
    </div>

    <div class="card-body">
      <div class="card-cat">{{ p.category }}</div>
      <a href="/product/{{ slugify(p.name) }}" class="card-name">{{ shorten_product_name(p.name) }}</a>
      <p class="card-hook">{{ p.hook|safe }}</p>

      {% if price_info.rating %}
      <div class="card-rating">
        <span class="card-stars">{% for i in range(price_info.rating|int) %}★{% endfor %}</span>
        <span>Highly rated</span>
      </div>
      {% endif %}

      <div class="card-div"></div>
      {% if p.get('last_updated') or p.date_added %}
      <div style="font-size:.7rem;color:var(--muted-2);margin-bottom:8px;font-style:italic">Updated {{ p.get('last_updated') or p.date_added }}</div>
      {% endif %}
      <div class="card-cta">
        {% if p.url %}
        <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored noopener" class="btn-amz"
           aria-label="Check price for {{ p.name }} on Amazon">
          Check price on <span class="amz-wordmark">amazon</span>
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
        <p class="footer-desc">An independent gift curation site for UK shoppers. Every pick is chosen — we earn a small commission on purchases at no extra cost to you.</p>
        <div class="footer-tagline">No paid placements</div>
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
    This site uses essential cookies and affiliate tracking.
    <a href="/privacy-policy">Privacy policy</a>
  </div>
  <div class="cookie-btns">
    <button class="btn-cookie-ok" id="cookie-accept">Accept All</button>
    <button class="btn-cookie-ess" id="cookie-essential">Essential Only</button>
  </div>
</div>

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
  function onScroll() { nav.classList.toggle('scrolled', window.scrollY > 20); }
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
      var btn = dd.querySelector('.nav-drop-btn');
      if (btn) btn.setAttribute('aria-expanded', 'false');
    });
  });
})();

// ── SCROLL REVEAL ──────────────────────────────────────────────
(function() {
  var els = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    els.forEach(function(el) { el.classList.add('in-view'); });
    return;
  }
  var io = new IntersectionObserver(function(entries) {
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
    var r = await fetch('/api/search-products');
    var d = await r.json();
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
  for (var s of [',','(']) {
    if (n.includes(s)) { var x = n.split(s)[0].trim(); if (x.length <= l) return x; }
  }
  return n.slice(0, l - 1) + '…';
}

var overlay    = document.getElementById('search-overlay');
var countEl    = document.getElementById('search-count');
var resGrid    = document.getElementById('search-res-grid');
var searchInp  = document.getElementById('search-input');
var mSearchInp = document.getElementById('mobile-search-input');

function buildCard(p) {
  return '<article class="card">' +
    '<div class="card-img">' +
      '<span class="card-badge">' + (p.category||'') + '</span>' +
      '<a href="/product/' + pySlug(p.name) + '" tabindex="-1" aria-hidden="true">' +
        '<img src="' + (p.image||'') + '" alt="' + p.name + '" loading="lazy" width="400" height="400">' +
      '</a>' +
    '</div>' +
    '<div class="card-body">' +
      '<div class="card-cat">' + (p.category||'') + '</div>' +
      '<a href="/product/' + pySlug(p.name) + '" class="card-name">' + shortName(p.name) + '</a>' +
      '<p class="card-hook">' + (p.hook||'') + '</p>' +
      '<div class="card-cta">' +
        (p.url ? '<a href="' + p.url + '" target="_blank" rel="nofollow sponsored noopener" class="btn-amz">' +
          'Check price on <span class="amz-wordmark">amazon</span></a>' : '') +
        '<a href="/product/' + pySlug(p.name) + '" class="btn-detail">Full details →</a>' +
      '</div>' +
    '</div>' +
  '</article>';
}

function renderResults(products, q) {
  countEl.textContent = products.length
    ? products.length + ' result' + (products.length !== 1 ? 's' : '') + ' for "' + q + '"'
    : 'No results for "' + q + '"';
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
  var t = q.trim();
  if (t.length < 3) { if (overlay.classList.contains('open')) closeSearch(); return; }
  searchTimer = setTimeout(function() {
    var ql    = t.toLowerCase();
    var words = ql.split(/\s+/).filter(function(w) { return w.length > 0; });
    var scored = allProducts.map(function(p) {
      var name   = (p.name   || '').toLowerCase();
      var cat    = (p.category || '').toLowerCase();
      var hook   = (p.hook   || '').toLowerCase();
      var info   = (p.info   || '').toLowerCase();
      var keys   = (p.keywords || []).join(' ').toLowerCase();
      var season = (p.season || '').toLowerCase();
      var score = 0;
      for (var w of words) {
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
    var hits = scored
      .filter(function(x) { return x.score >= 8; })
      .sort(function(a, b) { return b.score - a.score; })
      .map(function(x) { return x.p; });
    renderResults(hits, t);
  }, 200);
}

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
  var KEY = 'fybo_consent_v1';
  var bar = document.getElementById('cookie-bar');
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

<script async src="https://www.googletagmanager.com/gtag/js?id=G-C1YNKZS6PG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-C1YNKZS6PG');</script>

</body>
</html>"""



# ============================================================================
# RENDER PAGE — v6.0 (unchanged logic, only CSS/template updated above)
# ============================================================================

def render_page(title, description, heading, subtitle, products=None, page=1,
                page_url=None, similar_products=None, today=None,
                today_formatted=None, article_date=None, content=None, total_posts=None, **kwargs):
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

    faq_schema = kwargs.get("faq_schema_override") or None
    if not faq_schema and paged_products and len(paged_products) == 1:
        product_faqs = paged_products[0].get("faqs", [])
        if product_faqs:
            faq_schema = generate_faq_schema(product_faqs)

    website_schema = generate_website_schema()

    organisation_schema = None
    if request.path == '/':
        organisation_schema = generate_organisation_schema()

    og_type = "website"
    if '/product/' in request.path:
        og_type = "product"
    elif '/blog/' in request.path and request.path != '/blog' and '/page/' not in request.path:
        og_type = "article"

    category_itemlist = kwargs.get("itemlist_schema") or None
    if not category_itemlist and '/category/' in request.path and paged_products:
        cat_name = paged_products[0].get('category', 'Gifts')
        category_itemlist = generate_itemlist_schema(
            paged_products,
            f"Best {cat_name} Gifts UK 2026",
            f"Hand-picked {cat_name.lower()} gift ideas for UK shoppers."
        )

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
        faq_schema=faq_schema,
        website_schema=website_schema,
        organisation_schema=organisation_schema,
        og_type=og_type,
        article_date=article_date, content=content or "",
        itemlist_schema=category_itemlist,
        cookie_consent="", total_posts=total_posts
    )



# ============================================================================
# SEASONAL LANDING PAGES
# ============================================================================

SEASONAL_LANDING_PAGES = {

    "valentines-day": {
        "title": "Best Valentine's Day Gifts 2026 UK — Romantic Ideas They'll Love | FyboBuybo",
        "description": "Handpicked Valentine's Day gift ideas for 2026, curated for UK shoppers. From romantic keepsakes to luxury treats — find something they'll treasure.",
        "heading": "Best Valentine\u2019s Day Gifts 2026 \u2014 Romantic Ideas They\u2019ll Love",
        "subtitle": "Hand-picked daily from top-rated Amazon UK products. Thoughtful gifts for him, her, or anyone you love.",
        "intro": """Valentine's Day in the UK falls on <strong>Saturday 14 February 2026</strong>, giving you a full 
            weekend to celebrate. Whether you're shopping for a partner, a new relationship, or a friend who 
            deserves something lovely, finding a gift that feels personal rather than generic makes all the 
            difference. We update these picks daily, choosing from thousands of highly rated products on 
            Amazon UK. Every recommendation below has been selected for genuine quality, thoughtful gifting 
            potential, and strong buyer reviews from UK shoppers \u2014 no filler, no sponsored placements. 
            From luxury skincare and jewellery to personalised keepsakes and experience-style gifts, there's 
            something here for every budget and every kind of love.""",
        "buying_guide_title": "How to Choose the Perfect Valentine\u2019s Day Gift",
        "buying_guide": """<strong>Think about what they actually enjoy.</strong> The most appreciated Valentine's gifts 
            connect to something real \u2014 their favourite scent, a hobby they love, or a running joke between you. 
            Generic gifts feel generic.
            <strong>Experiences count.</strong> A voucher for a meal, a spa day, or even a cosy night in with 
            a luxury hamper can mean more than something wrapped.
            <strong>Presentation matters.</strong> Most Amazon UK items offer gift wrapping at checkout \u2014 a 
            small touch that makes a real difference on Valentine's Day.
            <strong>Order by 11 February</strong> for standard delivery, or use Amazon Prime for next-day options.""",
        "faqs": [
            {"q": "When is Valentine's Day 2026 in the UK?", "a": "Valentine's Day is always on 14 February. In 2026, that falls on a Saturday, giving couples a full weekend to celebrate."},
            {"q": "What are the most popular Valentine's Day gifts in the UK?", "a": "According to UK retail trends, the most popular gifts include flowers, chocolates, fragrances, jewellery, and experience vouchers. Personalised gifts like engraved items and photo books have grown significantly in recent years."},
            {"q": "What should I buy my partner if we've just started dating?", "a": "Keep it thoughtful but not over the top. A quality candle, a box of premium chocolates, or a small piece of jewellery shows effort without too much pressure. Avoid anything too personal early on."},
            {"q": "How much should I spend on a Valentine's Day gift?", "a": "UK shoppers typically spend between \u00a320 and \u00a360 on a Valentine's gift. The thought behind it matters more than the price \u2014 a well-chosen \u00a315 present can feel more romantic than an expensive but impersonal one."},
            {"q": "Can I get Valentine's Day gifts delivered in time?", "a": "If you order through Amazon UK by around 11 February 2026, standard delivery should arrive before the 14th. Amazon Prime members can often get next-day or same-day delivery right up to 13 February."}
        ],
        "internal_links": """Looking for more inspiration? Browse our 
            <a href="/category/beauty">beauty gifts</a>, 
            <a href="/category/fashion">fashion picks</a>, or 
            <a href="/blog">gift guides</a>. You might also like our 
            <a href="/season/mothers-day">Mother's Day</a> or 
            <a href="/season/christmas">Christmas gift collections</a>.""",
        "itemlist_name": "Best Valentine's Day Gifts 2026 UK"
    },

    "mothers-day": {
        "title": "Best Mother's Day Gifts 2026 UK \u2014 Unique Ideas for Every Mum | FyboBuybo",
        "description": "Discover handpicked Mother\u2019s Day gift ideas for 2026, curated for UK shoppers. From beauty to home \u2014 find something she\u2019ll actually love.",
        "heading": "Best Mother\u2019s Day Gifts 2026 \u2014 Thoughtful Ideas for Every Mum",
        "subtitle": "Hand-picked daily from thousands of top-rated Amazon UK products. No sponsored picks \u2014 just gifts she\u2019ll genuinely love.",
        "intro": """Mother's Day in the UK falls on <strong>Sunday 15 March 2026</strong> this year, 
            and finding something she'll genuinely love \u2014 not just another token gesture \u2014 takes 
            a bit of thought. That's what this page is for. We hand-pick and update these 
            recommendations daily, drawing from thousands of highly rated products on Amazon UK. 
            Whether your mum is into skincare, home comforts, books, or gadgets, you'll find 
            something here that feels personal and considered. Every pick below has been chosen 
            for quality, thoughtful gifting potential, and strong UK buyer reviews \u2014 no filler, 
            no sponsored placements.""",
        "buying_guide_title": "How to Choose the Perfect Mother\u2019s Day Gift",
        "buying_guide": """<strong>Think about her actual routine.</strong> The best gifts fit into her life \u2014 a quality 
            skincare product she'd use every morning, a kitchen gadget she's been eyeing, or a book from 
            an author she already loves.
            <strong>Don't overthink the price.</strong> A thoughtful \u00a315 gift that shows you know her 
            beats an expensive one that misses the mark. Focus on what she'd choose for herself.
            <strong>Presentation counts.</strong> Most Amazon UK items offer gift wrapping at checkout \u2014 
            it's a small detail that makes a real difference.
            <strong>Order by 12 March</strong> for standard delivery, or check for next-day Prime options 
            if you're cutting it close.""",
        "faqs": [
            {"q": "When is Mother's Day 2026 in the UK?", "a": "Mother's Day 2026 in the UK is Sunday 15 March. It falls on the fourth Sunday of Lent each year, so the date changes annually. In 2027 it will be 30 March."},
            {"q": "What are the most popular Mother's Day gifts in the UK?", "a": "According to UK retail trends, the most popular categories are flowers, chocolates, fragrances, skincare sets, and personalised gifts such as photo books or engraved jewellery. Experiences like spa days and afternoon teas have also grown in popularity."},
            {"q": "What should I buy my mum if I don't know what she likes?", "a": "A luxury hand cream or candle set from a well-known brand tends to be a safe and appreciated choice. These are items most people enjoy but rarely buy for themselves. Look for highly rated options with strong reviews from UK buyers."},
            {"q": "How much should I spend on a Mother's Day gift?", "a": "There is no fixed rule, but UK shoppers typically spend between \u00a315 and \u00a350 on a Mother's Day gift. The thought behind the gift matters more than the price \u2014 a well-chosen \u00a320 present can feel more personal than something expensive but generic."},
            {"q": "Can I get Mother's Day gifts delivered in time?", "a": "If you order through Amazon UK by around 12 March 2026, standard delivery should arrive before Mother's Day on 15 March. Amazon Prime members can often get next-day or same-day delivery on eligible items right up to 14 March."}
        ],
        "internal_links": """Looking for more inspiration? Browse our 
            <a href="/category/beauty">beauty gifts</a>, 
            <a href="/category/home-and-kitchen">home &amp; kitchen picks</a>, or 
            <a href="/blog">gift guides</a>. You might also like our 
            <a href="/season/valentines-day">Valentine's Day</a> or 
            <a href="/season/easter">Easter gift collections</a>.""",
        "itemlist_name": "Best Mother's Day Gifts 2026 UK"
    },

    "easter": {
        "title": "Best Easter Gifts & Ideas 2026 UK \u2014 Fun Picks for All Ages | FyboBuybo",
        "description": "Curated Easter gift ideas for 2026. From chocolate alternatives to kids' craft sets and spring treats \u2014 handpicked for UK shoppers.",
        "heading": "Best Easter Gifts 2026 \u2014 Fun Ideas for All Ages",
        "subtitle": "Beyond the chocolate egg. Thoughtful Easter picks for kids, adults, and the whole family \u2014 updated daily.",
        "intro": """Easter 2026 falls on <strong>Sunday 5 April</strong>, with the bank holiday weekend running from 
            Good Friday (3 April) through Easter Monday (6 April). It's a brilliant time for family gifts, 
            spring treats, and thoughtful alternatives to the usual chocolate egg. We update these picks daily, 
            drawing from thousands of top-rated Amazon UK products. Whether you're looking for craft kits 
            for the kids, gourmet chocolate for grown-ups, or something to enjoy over the four-day weekend, 
            every recommendation here is chosen for quality and strong UK buyer reviews \u2014 no filler, 
            no sponsored placements.""",
        "buying_guide_title": "How to Choose the Perfect Easter Gift",
        "buying_guide": """<strong>Think beyond chocolate.</strong> While Easter eggs are traditional, gifts like craft kits, 
            spring-themed books, garden sets, and baking supplies offer something memorable and lasting.
            <strong>Match the age.</strong> For young children, look for interactive gifts they can enjoy over 
            the four-day weekend. For adults, gourmet food hampers or spring homeware make excellent choices.
            <strong>Plan for the long weekend.</strong> Easter is one of the few four-day breaks in the UK 
            calendar \u2014 gifts that encourage family activities tend to go down well.
            <strong>Order by 1 April</strong> for standard delivery, or use Prime for last-minute options.""",
        "faqs": [
            {"q": "When is Easter 2026 in the UK?", "a": "Easter Sunday 2026 is on 5 April. Good Friday is 3 April and Easter Monday is 6 April, creating a four-day bank holiday weekend across England, Wales, and Northern Ireland."},
            {"q": "What are popular Easter gifts besides chocolate?", "a": "Popular alternatives include craft kits, spring-themed books, gardening sets, baking supplies, personalised Easter baskets, and soft toys."},
            {"q": "What should I put in an Easter basket for kids?", "a": "A mix of small treats works well: a chocolate egg, a small toy or book, some craft supplies, and perhaps spring-themed stickers or hair accessories."},
            {"q": "How much do people typically spend on Easter gifts in the UK?", "a": "Most UK shoppers spend between \u00a310 and \u00a330 per person on Easter gifts."},
            {"q": "Can I get Easter gifts delivered before the bank holiday weekend?", "a": "If you order through Amazon UK by around 1 April 2026, standard delivery should arrive before Good Friday on 3 April."}
        ],
        "internal_links": """Looking for more inspiration? Browse our 
            <a href="/category/toys-and-games">toys &amp; games</a>, 
            <a href="/category/home-and-kitchen">home &amp; kitchen picks</a>, or 
            <a href="/blog">gift guides</a>.""",
        "itemlist_name": "Best Easter Gifts 2026 UK"
    },

    "fathers-day": {
        "title": "Best Father's Day Gifts 2026 UK \u2014 Ideas He'll Actually Use | FyboBuybo",
        "description": "Handpicked Father\u2019s Day gift ideas for 2026. From tech to tools, outdoor gear to grooming \u2014 curated for UK dads.",
        "heading": "Best Father\u2019s Day Gifts 2026 \u2014 Ideas He\u2019ll Actually Use",
        "subtitle": "Skip the novelty socks. Thoughtful Father's Day picks he'll genuinely appreciate \u2014 updated daily.",
        "intro": """Father's Day in the UK falls on <strong>Sunday 21 June 2026</strong>. Finding something he'll 
            actually use \u2014 rather than another novelty mug gathering dust \u2014 is the real challenge. That's 
            what this page is for. We hand-pick and update these recommendations daily.""",
        "buying_guide_title": "How to Choose the Perfect Father\u2019s Day Gift",
        "buying_guide": """<strong>Think about what he actually does.</strong> The best gifts for dads fit into their 
            real routines \u2014 a quality tool he'd use in the shed, a gadget for his kitchen, or something 
            for a hobby he already enjoys.
            <strong>Practical beats novelty.</strong> Dads are notoriously hard to buy for because they 
            often won't buy nice things for themselves. Upgrade something he uses every day.
            <strong>Order by 18 June</strong> for standard delivery, or use Prime for next-day options.""",
        "faqs": [
            {"q": "When is Father's Day 2026 in the UK?", "a": "Father's Day 2026 in the UK is Sunday 21 June. It falls on the third Sunday of June each year."},
            {"q": "What are the most popular Father's Day gifts in the UK?", "a": "The most popular gifts include clothing, grooming products, tech gadgets, tools, food and drink hampers, and experience days."},
            {"q": "What should I buy my dad if he says he doesn't want anything?", "a": "A quality consumable gift works well \u2014 premium coffee, craft beer, or a food hamper he'd never buy himself."},
            {"q": "How much should I spend on a Father's Day gift?", "a": "UK shoppers typically spend between \u00a315 and \u00a345 on a Father's Day gift."},
            {"q": "Can I get Father's Day gifts delivered in time?", "a": "If you order through Amazon UK by around 18 June 2026, standard delivery should arrive before Father's Day on 21 June."}
        ],
        "internal_links": """Looking for more inspiration? Browse our 
            <a href="/category/electronics">electronics</a>, 
            <a href="/category/sports-and-outdoors">sports &amp; outdoors picks</a>, or 
            <a href="/blog">gift guides</a>.""",
        "itemlist_name": "Best Father's Day Gifts 2026 UK"
    },

    "summer-gifts": {
        "title": "Best Summer Gifts 2026 UK \u2014 Seasonal Picks for Warm Weather | FyboBuybo",
        "description": "Curated summer gift ideas for UK shoppers in 2026. Outdoor living, garden finds, travel essentials, and seasonal treats.",
        "heading": "Best Summer Gifts 2026 \u2014 Seasonal Picks for Warm Weather",
        "subtitle": "Make the most of the British summer. Garden finds, outdoor treats, and travel picks \u2014 updated daily.",
        "intro": "The UK summer of 2026 brings long evenings, garden gatherings, and barbecues. Whether you're shopping for a birthday or just something to enjoy the season, we've got you covered. Updated daily from top-rated Amazon UK products.",
        "buying_guide_title": "How to Choose the Perfect Summer Gift",
        "buying_guide": """<strong>Think outdoor and portable.</strong> The best summer gifts work in the garden, 
            at the park, or on holiday.
            <strong>Consider the British weather.</strong> Versatile gifts that work in both sunshine and 
            the inevitable drizzle are always practical for UK summers.""",
        "faqs": [
            {"q": "What are good summer gifts for someone in the UK?", "a": "Popular UK summer gifts include garden accessories, BBQ tools, picnic sets, outdoor games, travel essentials, and cold-brew drink kits."},
            {"q": "When is the best time to buy summer gifts?", "a": "June through August is peak summer gifting season in the UK."},
            {"q": "What outdoor gifts work well for UK weather?", "a": "Waterproof picnic blankets, all-weather garden games, and versatile layers are practical and appreciated."},
            {"q": "What's a good summer gift under \u00a325?", "a": "A quality insulated water bottle, a garden game set, or a portable Bluetooth speaker all make excellent summer gifts under \u00a325."},
            {"q": "Are garden gifts popular in the UK?", "a": "Very much so. With over 80% of UK homes having a garden, garden gifts are consistently popular during summer months."}
        ],
        "internal_links": """Browse our <a href="/category/home-and-kitchen">home &amp; kitchen</a> or <a href="/category/sports-and-outdoors">sports &amp; outdoors</a> picks.""",
        "itemlist_name": "Best Summer Gifts 2026 UK"
    },

    "summer-essentials": {
        "title": "Summer Essentials 2026 UK \u2014 Must-Have Picks for the Season | FyboBuybo",
        "description": "The summer essentials every UK household needs in 2026. Sun care, outdoor living, travel must-haves \u2014 handpicked and updated daily.",
        "heading": "Summer Essentials 2026 \u2014 Must-Have Picks for the Season",
        "subtitle": "Everything you need to make the most of a British summer. Practical, well-reviewed, and chosen for UK life.",
        "intro": "British summers are short, unpredictable, and absolutely worth making the most of. This collection brings together everyday essentials from sun protection to outdoor dining supplies. Updated daily from Amazon UK products.",
        "buying_guide_title": "How to Pick the Right Summer Essentials",
        "buying_guide": """<strong>Start with sun protection.</strong> SPF, hats, and quality sunglasses are the non-negotiables.
            <strong>Upgrade your outdoor setup.</strong> A decent cool bag, a waterproof blanket, and portable seating transform any park visit.""",
        "faqs": [
            {"q": "What are the must-have summer essentials in the UK?", "a": "Key essentials include quality SPF sunscreen, insulated water bottles, portable fans, waterproof picnic blankets, and insect repellent."},
            {"q": "What sun cream factor should I use in the UK?", "a": "Dermatologists recommend at least SPF 30, even on cloudy days."},
            {"q": "What's worth buying for UK camping trips?", "a": "A quality cool bag, portable power bank, insect repellent, waterproof torch, and compact camp chair."},
            {"q": "Are insulated water bottles worth it?", "a": "Yes \u2014 a good insulated bottle keeps drinks cold for 24 hours or hot for 12."},
            {"q": "When should I start buying summer essentials in the UK?", "a": "April and May are ideal for stocking up before popular items sell out."}
        ],
        "internal_links": """Browse our <a href="/category/health-and-personal-care">health &amp; personal care</a> or <a href="/category/sports-and-outdoors">sports &amp; outdoors</a> picks.""",
        "itemlist_name": "Summer Essentials 2026 UK"
    },

    "back-to-school": {
        "title": "Best Back to School Supplies 2026 UK \u2014 Essentials for Every Age | FyboBuybo",
        "description": "Curated back to school essentials for UK students in 2026. Stationery, bags, tech, and organisation picks \u2014 updated daily.",
        "heading": "Best Back to School Picks 2026 \u2014 Essentials for Every Age",
        "subtitle": "From primary to sixth form. Quality school supplies that last \u2014 handpicked for UK students and parents.",
        "intro": "The September school run comes around fast. We've curated these back-to-school picks from thousands of top-rated Amazon UK products, covering stationery, bags, tech, and organisation essentials.",
        "buying_guide_title": "How to Choose the Right Back to School Supplies",
        "buying_guide": """<strong>Buy for durability, not novelty.</strong> Plain, well-made supplies last the whole year.
            <strong>Label everything.</strong> A label maker saves hours of lost property stress.
            <strong>Check the school's specific requirements</strong> before buying to avoid returns.""",
        "faqs": [
            {"q": "When do UK schools go back in September 2026?", "a": "Most UK schools return in the first or second week of September 2026. Check your school's published term dates."},
            {"q": "What school supplies does my child need?", "a": "Core supplies include a durable school bag, pencil case with pens and pencils, ruler, eraser, sharpener, notebooks, and a water bottle."},
            {"q": "What's a good school bag for UK students?", "a": "Look for a bag with padded shoulder straps, water-resistant material, and enough space for A4 folders."},
            {"q": "How much do parents spend on back to school in the UK?", "a": "UK parents spend an average of \u00a3100\u2013\u00a3250 per child on back-to-school supplies, uniform, and shoes combined."},
            {"q": "Are refurbished laptops good for school?", "a": "Yes, from reputable sellers. Look for at least 8GB RAM, an SSD, and 6+ hour battery life."}
        ],
        "internal_links": """Browse our <a href="/category/books">books</a> or <a href="/category/electronics">electronics</a> picks.""",
        "itemlist_name": "Best Back to School Supplies 2026 UK"
    },

    "halloween": {
        "title": "Best Halloween Gifts & Ideas 2026 UK \u2014 Spooky Picks for All Ages | FyboBuybo",
        "description": "Curated Halloween ideas for UK shoppers in 2026. Costumes, decorations, party supplies, and themed gifts \u2014 handpicked daily.",
        "heading": "Best Halloween Picks 2026 \u2014 Spooky Ideas for All Ages",
        "subtitle": "From costumes to decorations. Fun, well-reviewed Halloween finds for UK families \u2014 updated daily.",
        "intro": "Halloween 2026 falls on <strong>Saturday 31 October</strong>, making it perfect for parties and trick-or-treating. Curated from thousands of top-rated Amazon UK products.",
        "buying_guide_title": "How to Plan a Brilliant Halloween",
        "buying_guide": """<strong>Start with the front door.</strong> LED pumpkin lights, door wreaths, and window silhouettes create atmosphere.
            <strong>Costumes don't need to cost a fortune.</strong> A well-chosen accessory often works better than a full outfit.
            <strong>Order by 27 October</strong> for standard delivery.""",
        "faqs": [
            {"q": "When is Halloween 2026?", "a": "Halloween is always on 31 October. In 2026, that falls on a Saturday."},
            {"q": "Is Halloween widely celebrated in the UK?", "a": "Yes \u2014 Halloween has grown significantly in the UK over the past two decades."},
            {"q": "What are the most popular Halloween costumes in the UK?", "a": "Classic choices like witches, vampires, ghosts, and skeletons remain popular."},
            {"q": "How much do UK families spend on Halloween?", "a": "UK households typically spend between \u00a315 and \u00a350 on Halloween."},
            {"q": "Where can I buy pumpkins for carving in the UK?", "a": "Supermarkets, farm shops, and local greengrocers all stock carving pumpkins from early October."}
        ],
        "internal_links": """Browse our <a href="/category/toys-and-games">toys &amp; games</a> or <a href="/season/christmas">Christmas collection</a>.""",
        "itemlist_name": "Best Halloween Picks 2026 UK"
    },

    "christmas": {
        "title": "Best Christmas Gifts 2026 UK \u2014 Curated Ideas for Everyone | FyboBuybo",
        "description": "Handpicked Christmas gift ideas for 2026. Thoughtful presents for him, her, kids, and the home \u2014 curated for UK shoppers.",
        "heading": "Best Christmas Gifts 2026 \u2014 Thoughtful Ideas for Everyone",
        "subtitle": "Hand-picked daily from top-rated Amazon UK products. Find something they\u2019ll genuinely love this Christmas.",
        "intro": "<strong>Christmas Day 2026 falls on Friday 25 December</strong>. Finding gifts that feel personal and considered is what this page is for. Updated daily from thousands of top-rated Amazon UK products.",
        "buying_guide_title": "How to Choose the Perfect Christmas Gift",
        "buying_guide": """<strong>Start early, buy thoughtfully.</strong> The best Christmas gifts come from noticing what people mention they want throughout the year.
            <strong>Set a budget per person.</strong> A well-chosen \u00a320 gift beats a rushed \u00a350 one.
            <strong>Order by 19 December</strong> for standard Royal Mail delivery.""",
        "faqs": [
            {"q": "What are the most popular Christmas gifts in the UK for 2026?", "a": "Trending categories include tech gadgets, premium beauty sets, personalised gifts, experience vouchers, and quality homeware."},
            {"q": "When is the best time to start Christmas shopping in the UK?", "a": "October and November offer the best selection and competitive prices, especially around Black Friday (27 November 2026)."},
            {"q": "How much do UK households spend on Christmas gifts?", "a": "UK households spend an average of \u00a3500\u2013\u00a3800 on Christmas gifts combined."},
            {"q": "What's the last day to order for Christmas delivery on Amazon UK?", "a": "For standard delivery, aim to order by around 19 December. Amazon Prime members can typically order with next-day delivery right up to 23 December."},
            {"q": "What are good Christmas gifts under \u00a320?", "a": "Quality candles, premium socks, books, artisan food gifts, phone accessories, and novelty board games all make excellent sub-\u00a320 gifts."}
        ],
        "internal_links": """Browse our <a href="/category/toys-and-games">toys &amp; games</a>, <a href="/category/electronics">electronics</a>, or <a href="/blog">gift guides</a>.""",
        "itemlist_name": "Best Christmas Gifts 2026 UK"
    },

    "winter-essentials": {
        "title": "Winter Essentials 2026 UK \u2014 Stay Warm & Cosy All Season | FyboBuybo",
        "description": "Curated winter essentials for UK shoppers. Warm clothing, home comforts, and cold-weather gear \u2014 handpicked and updated daily.",
        "heading": "Winter Essentials 2026 \u2014 Stay Warm & Cosy All Season",
        "subtitle": "Beat the British winter. Practical warmth, home comforts, and cold-weather gear \u2014 chosen for UK conditions.",
        "intro": "British winters are cold, damp, and long \u2014 but they don't have to be miserable. This collection brings together practical essentials from thermal layers to cosy home upgrades. Updated daily from Amazon UK products.",
        "buying_guide_title": "How to Choose the Right Winter Essentials",
        "buying_guide": """<strong>Layer intelligently.</strong> A good base layer, mid-layer, and waterproof outer keeps you warmer than one heavy coat.
            <strong>Invest in extremities.</strong> Quality gloves, a warm hat, and decent socks make a bigger difference than most expect.""",
        "faqs": [
            {"q": "What are the must-have winter essentials in the UK?", "a": "Key items include a waterproof coat, thermal base layers, quality gloves, a warm hat, waterproof boots, a hot water bottle, and draught excluders."},
            {"q": "What's the warmest material for winter clothing?", "a": "Merino wool offers the best warmth-to-weight ratio and regulates temperature naturally."},
            {"q": "How can I stay warm at home without high heating bills?", "a": "Draught excluders, thermal curtains, heated throws, quality slippers, and a good hot water bottle can significantly reduce heating reliance."},
            {"q": "What winter boots are best for UK weather?", "a": "Look for boots with waterproof membranes, good grip soles, and insulation. UK winters are more wet than freezing."},
            {"q": "When should I start buying winter essentials in the UK?", "a": "September and October offer the best selection before popular sizes sell out."}
        ],
        "internal_links": """Browse our <a href="/category/home-and-kitchen">home &amp; kitchen</a> or <a href="/season/christmas">Christmas gifts</a>.""",
        "itemlist_name": "Winter Essentials 2026 UK"
    },

    "spring": {
        "title": "Best Spring Picks 2026 UK \u2014 Fresh Finds for the New Season | FyboBuybo",
        "description": "Curated spring products for UK shoppers in 2026. Garden, home refresh, outdoor living, and seasonal picks \u2014 updated daily.",
        "heading": "Best Spring Picks 2026 \u2014 Fresh Finds for the New Season",
        "subtitle": "Refresh your home, garden, and wardrobe for spring. Thoughtful picks for the new season \u2014 updated daily.",
        "intro": "Spring in the UK means lighter evenings, garden plans, and that satisfying urge to refresh everything. Updated daily from thousands of Amazon UK products.",
        "buying_guide_title": "How to Make the Most of Spring",
        "buying_guide": """<strong>Start with the garden.</strong> March and April are the best months to get the garden ready.
            <strong>Refresh, don't replace.</strong> New cushion covers, a fresh doormat, or a deep clean can transform a room without a big spend.""",
        "faqs": [
            {"q": "When does spring start in the UK?", "a": "Meteorological spring runs from 1 March to 31 May. The spring equinox falls around 20 March."},
            {"q": "What should I plant in spring in the UK?", "a": "March to May is ideal for potatoes, peas, broad beans, and salad leaves outdoors."},
            {"q": "What are good spring cleaning essentials?", "a": "A quality microfibre cloth set, steam cleaner, all-purpose cleaner, and storage organisers cover most spring cleaning needs."},
            {"q": "When should I start mowing the lawn in the UK?", "a": "Most UK lawns benefit from a first cut in late March or early April."},
            {"q": "What are popular spring home refresh ideas?", "a": "Lighter cushion covers, fresh indoor plants, new doormats, spring-scented candles, and updated bathroom accessories."}
        ],
        "internal_links": """Browse our <a href="/category/home-and-kitchen">home &amp; kitchen</a> or <a href="/season/easter">Easter gifts</a>.""",
        "itemlist_name": "Best Spring Picks 2026 UK"
    },

    "new-year-essentials": {
        "title": "New Year Essentials 2026 UK \u2014 Fresh Start Picks | FyboBuybo",
        "description": "Start 2026 right with curated new year essentials. Fitness, organisation, self-improvement, and home picks for UK shoppers.",
        "heading": "New Year Essentials 2026 \u2014 Fresh Start Picks",
        "subtitle": "New year, better habits. Practical picks for fitness, organisation, and self-improvement \u2014 updated daily.",
        "intro": "January is the month of fresh starts. Whether you're getting into fitness, organising your home, or improving your diet, this collection brings together the most practical picks. Updated daily from Amazon UK products.",
        "buying_guide_title": "How to Choose New Year Essentials That Actually Last",
        "buying_guide": """<strong>Pick one habit and equip it properly.</strong> Buying everything at once leads to overwhelm.
            <strong>Buy quality over quantity.</strong> A \u00a340 yoga mat that lasts years beats a \u00a310 one that peels after two months.""",
        "faqs": [
            {"q": "What are the best new year essentials for 2026?", "a": "Popular categories include fitness equipment, organisation tools, kitchen upgrades for healthier cooking, and self-improvement books."},
            {"q": "How do I stick to new year resolutions?", "a": "Start with one specific, measurable goal. Having the right equipment and tracking progress increases success rates."},
            {"q": "What fitness equipment is best for home workouts?", "a": "A yoga mat, resistance bands, and adjustable dumbbells cover most home workout needs."},
            {"q": "What's a good planner for 2026?", "a": "Look for a planner with weekly and monthly views, goal-setting pages, and space for notes."},
            {"q": "Is January a good time to buy fitness equipment?", "a": "January sees the widest selection but highest demand. Consider buying in late December when pre-new-year sales often start."}
        ],
        "internal_links": """Browse our <a href="/category/health-and-personal-care">health &amp; personal care</a> or <a href="/category/sports-and-outdoors">sports &amp; outdoors</a> picks.""",
        "itemlist_name": "New Year Essentials 2026 UK"
    },
}


# ============================================================================
# UNIVERSAL SEASONAL CONTENT GENERATOR
# ============================================================================

def generate_seasonal_content(season_slug, products):
    page_data = SEASONAL_LANDING_PAGES.get(season_slug)
    if not page_data:
        return None, None, None, None

    content_before = f"""
    <div style="max-width:900px;margin:0 auto;padding:0 24px 40px">
      <div class="blog-prose">
        <p style="font-size:1.08rem;line-height:1.85;color:var(--muted);font-weight:300">
          {page_data['intro']}
        </p>
      </div>
    </div>
    """

    buying_guide = f"""
    <div style="max-width:900px;margin:48px auto 0;padding:0 24px">
      <div class="blog-prose">
        <h2 style="font-size:1.6rem;margin-top:0;border-bottom:1px solid var(--divider);padding-bottom:14px">{page_data['buying_guide_title']}</h2>
        <p style="font-size:.98rem;line-height:1.82;color:var(--ink-3);font-weight:300">
          {page_data['buying_guide']}
        </p>
      </div>
    </div>
    """

    faq_html = """
    <div style="max-width:900px;margin:56px auto 0;padding:0 24px">
      <div class="blog-prose">
        <h2 style="font-size:1.6rem;margin-top:0;border-bottom:1px solid var(--divider);padding-bottom:14px">Frequently Asked Questions</h2>
    """
    for faq in page_data['faqs']:
        faq_html += f"""
        <div style="margin:24px 0;padding-bottom:20px;border-bottom:1px solid var(--divider)">
          <h3 style="font-size:1.15rem;margin:0 0 10px;font-family:'Playfair Display','Cormorant Garamond',serif;color:var(--ink);letter-spacing:-.02em">{faq['q']}</h3>
          <p style="font-size:.94rem;line-height:1.78;color:var(--muted);margin:0;font-weight:300">{faq['a']}</p>
        </div>
        """
    faq_html += """
      </div>
    </div>
    """

    links_html = f"""
    <div style="max-width:900px;margin:32px auto 48px;padding:0 24px">
      <div class="blog-prose">
        <p style="font-size:.92rem;line-height:1.75;color:var(--muted);font-weight:300">
          {page_data['internal_links']}
        </p>
      </div>
    </div>
    """

    content_after = buying_guide + faq_html + links_html

    faq_schema = generate_faq_schema(page_data['faqs'])

    itemlist_items = []
    for idx, p in enumerate(products[:12], 1):
        itemlist_items.append({
            "@type": "ListItem",
            "position": idx,
            "name": p["name"],
            "url": SITE_URL + "/product/" + slugify(p["name"])
        })

    itemlist_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": page_data.get("itemlist_name", f"Best {season_slug.replace('-', ' ').title()} UK"),
        "description": f"Hand-picked {season_slug.replace('-', ' ')} picks for UK shoppers, updated daily.",
        "numberOfItems": len(itemlist_items),
        "itemListElement": itemlist_items
    }, ensure_ascii=False) if itemlist_items else None

    return content_before, content_after, faq_schema, itemlist_schema


# ============================================================================
# ROUTES
# ============================================================================

# ============================================================================
# 301 REDIRECTS — fixing old URLs Google has indexed
# ============================================================================

@app.route("/product/echo-dot-5th-generation-smart-speaker-with-alexa--deep-sea-blue")
def redirect_echo_dot():
    return redirect("/product/echo-dot-5th-generation-smart-speaker-with-alexa-deep-sea-blue", code=301)

@app.route("/product/cosrx-advanced-snail-96-mucin-power-essence-100ml--snail-secretion-filtrate-96-skin-repair-serum")
def redirect_cosrx():
    return redirect("/product/cosrx-advanced-snail-96-mucin-power-essence-100ml-snail-secretion-filtrate-96-skin-repair-serum", code=301)

@app.route("/product/anua-azelaic-acid-10-hyaluron-redness-soothing-serum--facial-serum-for-sensitive-skin")
def redirect_anua():
    return redirect("/product/anua-azelaic-acid-10-hyaluron-redness-soothing-serum-facial-serum-for-sensitive-skin", code=301)

@app.route("/product/lego-speed-champions-ferrari-sf-24-f1-race-car-toy--model-kit-with-formula-1-driver-minifigure--gift-for-10-year-old-boys-girls--and--adult-motorsport-fans--77242")
def redirect_lego_ferrari():
    return redirect("/product/lego-speed-champions-ferrari-sf-24-f1-race-car-toy-model-kit-with-formula-1-driver-minifigure-gift-for-10-year-old-boys-girls-and-adult-motorsport-fans-77242", code=301)

@app.route("/category/summer-essentials")
def redirect_summer_essentials():
    return redirect("/season/summer-essentials", code=301)

@app.route("/category/valentines-day")
def redirect_valentines_category():
    return redirect("/season/valentines-day", code=301)

@app.route("/category/christmas-gift-ideas")
def redirect_christmas_category():
    return redirect("/season/christmas", code=301)

@app.route("/category/toys--and--games")
def redirect_toys():
    return redirect("/category/toys-and-games", code=301)

@app.route("/category/health--and--personal-care")
def redirect_health():
    return redirect("/category/health-and-personal-care", code=301)

@app.route("/category/sports--and--outdoors")
def redirect_sports():
    return redirect("/category/sports-and-outdoors", code=301)

@app.route("/category/home--and--kitchen")
def redirect_home():
    return redirect("/category/home-and-kitchen", code=301)

@app.route("/privacy-policy")
@cache.cached(timeout=86400, key_prefix='privacy-policy')
def privacy_policy():
    return render_page(
        title="Privacy Policy – FyboBuybo",
        description="Our commitment to protecting your privacy in accordance with UK GDPR.",
        heading="Privacy Policy", subtitle="How we collect, use, and protect your data",
        content=PRIVACY_POLICY_HTML
    )

@app.route("/terms")
@cache.cached(timeout=86400, key_prefix='terms')
def terms_of_service():
    return render_page(
        title="Terms of Service – FyboBuybo",
        description="Terms and conditions for using FyboBuybo, including affiliate disclosures.",
        heading="Terms of Service", subtitle="Legal terms for using our website",
        content=TERMS_OF_SERVICE_HTML
    )

@app.route("/api/search-products")
@cache.cached(timeout=600, key_prefix='api-search-products')
def api_search_products():
    all_products = refresh_products(background=True)
    return jsonify({'products': [{
        'name': p['name'], 'category': p.get('category', ''),
        'image': p.get('image', ''), 'hook': p.get('hook', ''),
        'info': p.get('info', ''), 'keywords': p.get('keywords', []),
        'season': p.get('season', ''), 'url': p.get('url', '')
    } for p in all_products]})

@app.route("/")
@cache.cached(timeout=300, key_prefix='homepage')
def home():
    products = refresh_products(background=True)[:ITEMS_PER_PAGE]
    return render_page(
        title="FyboBuybo – Trending UK Gifts & Popular Presents 2026",
        description="Discover today's trending UK gifts and popular presents across toys, beauty, electronics, home and more – refreshed daily.",
        heading="FyboBuybo – Trending UK Gifts",
        subtitle="Every pick on this site is chosen to help find interesting gifts. Refreshed daily for UK shoppers.",
        products=products
    )

@app.route("/category/<slug>")
@app.route("/category/<slug>/page/<int:page>")
@cache.cached(timeout=1800, key_prefix=lambda: request.url)
def category(slug, page=1):
    all_products = refresh_products(background=True)
    filtered = [p for p in all_products if slugify(p.get("category", "")) == slug]
    if not filtered: abort(404)
    cat_name = filtered[0]["category"]
    def page_url(p): return url_for("category", slug=slug, page=p)
    return render_page(
        title=f"Best {cat_name} Gifts UK 2026 — Handpicked for UK Shoppers | FyboBuybo",
        description=f"Hand-picked {cat_name.lower()} gift ideas for UK shoppers in 2026. Browse curated recommendations — find something they'll love.",
        heading=f"Best {cat_name} Gifts UK 2026",
        subtitle=f"The best {cat_name.lower()} gift ideas for UK shoppers in 2026 — updated regularly.",
        products=filtered, page=page, page_url=page_url
    )

@app.route("/season/<season_slug>")
@app.route("/season/<season_slug>/page/<int:page>")
@cache.cached(timeout=1800, key_prefix=lambda: request.url)
def seasonal_collection(season_slug, page=1):
    all_products = refresh_products(background=True)
    norm_slug = normalize_for_match(season_slug)
    filtered = [p for p in all_products if p.get("season") and any(norm_slug in normalize_for_match(s.strip()) for s in p["season"].split(","))]
    if not filtered: abort(404)
    filtered.sort(key=lambda p: p.get("date_added", "2000-01-01"), reverse=True)
    season_name = season_slug.replace('-', ' ').title()
    def page_url(p): return url_for("seasonal_collection", season_slug=season_slug, page=p)
    title_season = season_name + (" Gifts" if "day" in season_name.lower() or "christmas" in season_name.lower() else "")

    content_before, content_after, faq_schema_json, itemlist_schema_json = generate_seasonal_content(season_slug, filtered)

    if content_before is not None:
        page_data = SEASONAL_LANDING_PAGES[season_slug]

        rendered = render_page(
            title=page_data["title"],
            description=page_data["description"],
            heading=page_data["heading"],
            subtitle=page_data["subtitle"],
            products=filtered, page=page, page_url=page_url,
            content=content_before,
            faq_schema_override=faq_schema_json,
            itemlist_schema=itemlist_schema_json
        )

        footer_marker = "<!-- \u2550\u2550\u2550 FOOTER"
        insert_point = rendered.find(footer_marker)
        if insert_point > -1:
            rendered = rendered[:insert_point] + content_after + "\n" + rendered[insert_point:]

        return rendered

    return render_page(
        title=f"Best {title_season} UK 2026 \u2013 Gift Ideas | FyboBuybo",
        description=f"Curated {season_name.lower()} gift ideas for UK shoppers in 2026. Browse hand-picked recommendations \u2014 find the perfect gift.",
        heading=title_season,
        subtitle=f"Top-rated {season_name.lower()} gift ideas for UK shoppers \u2014 handpicked with recommendations.",
        products=filtered, page=page, page_url=page_url
    )

@app.route("/product/<path:product_slug>")
@cache.cached(timeout=1800, key_prefix=lambda: request.url)
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
          <span style="color:var(--green);font-size:1.2rem;letter-spacing:-.06em;line-height:1">{stars}</span>
          <span style="font-size:.88rem;color:var(--muted);font-weight:400">Highly rated by buyers</span>
          <a href="{found.get('url','')}" target="_blank" rel="nofollow sponsored noopener"
             style="font-size:.82rem;color:var(--primary);font-weight:600;border-bottom:1px solid var(--primary-line)">
            See current ratings →</a>
        </div>"""

    amazon_btn = ""
    if found.get("url"):
        amazon_btn = f"""<a href="{found["url"]}" target="_blank" rel="nofollow sponsored noopener" class="btn-pd-amz">
          Check price on <em>amazon</em>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/>
          </svg></a>"""

    trust_row = """<div class="pd-trust-row">
      <div class="pd-trust-item">
        <svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        Fulfilled by Amazon UK
      </div>
      <div class="pd-trust-item">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
        Live price on Amazon
      </div>
      <div class="pd-trust-item">
        <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        Amazon's standard returns apply
      </div>
    </div>"""

    info_html = f'<p class="pd-hook">{found["info"]}</p>' if found.get("info") else ""
    date_html = f'<p style="font-size:.74rem;color:var(--muted-2);margin-top:2px;font-style:italic">Featured {found["date_added"]}</p>' if found.get("date_added") else ""

    product_url = SITE_URL + "/product/" + slugify(found["name"])
    share_text = f"Check out this gift idea: {shorten_product_name(found['name'], 60)}"
    share_bar = f"""<div class="share-bar" aria-label="Share this product">
      <span class="share-label">Share</span>
      <a href="https://wa.me/?text={share_text}%20{product_url}" target="_blank" rel="noopener" class="share-btn share-wa" aria-label="Share on WhatsApp">
        <svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
        WhatsApp
      </a>
      <a href="https://www.facebook.com/sharer/sharer.php?u={product_url}" target="_blank" rel="noopener" class="share-btn share-fb" aria-label="Share on Facebook">
        <svg viewBox="0 0 24 24"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>
        Facebook
      </a>
      <a href="https://twitter.com/intent/tweet?text={share_text}&url={product_url}" target="_blank" rel="noopener" class="share-btn share-x" aria-label="Share on X">
        <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        X
      </a>
      <a href="mailto:?subject=Great%20gift%20idea&body={share_text}%20{product_url}" class="share-btn share-em" aria-label="Share via email">
        <svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        Email
      </a>
      <button class="share-btn share-copy" onclick="navigator.clipboard.writeText('{product_url}').then(function(){{var b=event.target.closest('.share-copy');b.classList.add('copied');b.innerHTML='Copied!';setTimeout(function(){{b.classList.remove('copied');b.innerHTML='<svg viewBox=&quot;0 0 24 24&quot; style=&quot;width:14px;height:14px;fill:currentColor&quot;><path d=&quot;M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z&quot;/></svg> Copy link';}},2000)}})" aria-label="Copy link">
        <svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
        Copy link
      </button>
    </div>"""

    content_html = f"""
    <div class="pd-wrap">
      <div class="pd-gallery">
        <div class="pd-img-main">
          <img src="{found['image']}" alt="{found['name']}"
               loading="eager" fetchpriority="high" width="600" height="600">
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
        <div class="pd-price-note">💡 Prices update frequently on Amazon. The price shown when you click may differ — always check before purchasing.</div>
        {amazon_btn}
        {trust_row}
        {date_html}
        {share_bar}
      </div>
    </div>"""

    suffix = get_product_title_suffix(found)
    return render_page(
        title=f"{shorten_product_name(found['name'], 45)} — {suffix} | FyboBuybo",
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
            f'<img src="{img_url}" alt="{img_alt}" loading="eager" width="780" height="440" style="width:100%;height:100%;object-fit:cover;position:absolute;inset:0;display:block" onerror="this.style.display=\'none\'">',
            False
        )

    content = post.get("content", "")
    img_match = re.search(r"src='(https://m\.media-amazon\.com/[^']+)'", content)
    if not img_match:
        img_match = re.search(r'src="(https://m\.media-amazon\.com/[^"]+)"', content)
    if img_match:
        return (
            f'<img src="{img_match.group(1)}" alt="{post.get("title","")}" class="product-img" loading="lazy" width="400" height="400" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block" onerror="this.style.display=\'none\'">',
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
                    f'<img src="{p["image"]}" alt="{post["title"]}" class="product-img" loading="lazy" width="400" height="400" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block">',
                    True
                )
            for pfuzz, p in product_map.items():
                if len(rel_fuzz) > 5 and (rel_fuzz in pfuzz or pfuzz in rel_fuzz):
                    return (
                        f'<img src="{p["image"]}" alt="{post["title"]}" class="product-img" loading="lazy" width="400" height="400" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block">',
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
                        f'<img src="{p["image"]}" alt="{post["title"]}" class="product-img" loading="lazy" width="400" height="400" style="width:100%;height:100%;object-fit:contain;padding:18px;position:absolute;inset:0;display:block">',
                        True
                    )

    return None, False


@app.route("/blog")
@app.route("/blog/page/<int:page>")
@cache.cached(timeout=900, key_prefix=lambda: request.url)
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
        subtitle="Practical gift guides written to help you find something genuinely great — not just another list.",
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
@cache.cached(timeout=3600, key_prefix=lambda: request.url)
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

    blog_faqs = []
    for rp in related:
        if rp.get("faqs"):
            blog_faqs.extend(rp["faqs"][:2])
    blog_faq_schema_json = generate_faq_schema(blog_faqs[:10]) if blog_faqs else None

    blog_itemlist_schema = None
    if related:
        itemlist_items = []
        for idx, p in enumerate(related[:12], 1):
            itemlist_items.append({
                "@type": "ListItem",
                "position": idx,
                "name": p["name"],
                "url": SITE_URL + "/product/" + slugify(p["name"])
            })
        blog_itemlist_schema = json.dumps({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": post.get("heading", post["title"]),
            "numberOfItems": len(itemlist_items),
            "itemListElement": itemlist_items
        }, ensure_ascii=False)

    from jinja2 import Template
    raw_content = post.get("content", "<p>Content coming soon.</p>")
    content_html_body = Template(raw_content).render(slugify=slugify)
    date_str = datetime.datetime.strptime(post.get("date", "2026-01-01"), "%Y-%m-%d").strftime("%d %B %Y")

    blog_url = SITE_URL + "/blog/" + slug
    blog_share_text = f"Great gift guide: {post.get('heading', post['title'])[:60]}"
    blog_share_bar = f"""<div class="share-bar" aria-label="Share this guide">
      <span class="share-label">Share this guide</span>
      <a href="https://wa.me/?text={blog_share_text}%20{blog_url}" target="_blank" rel="noopener" class="share-btn share-wa" aria-label="Share on WhatsApp">
        <svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
        WhatsApp
      </a>
      <a href="https://www.facebook.com/sharer/sharer.php?u={blog_url}" target="_blank" rel="noopener" class="share-btn share-fb" aria-label="Share on Facebook">
        <svg viewBox="0 0 24 24"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>
        Facebook
      </a>
      <a href="https://twitter.com/intent/tweet?text={blog_share_text}&url={blog_url}" target="_blank" rel="noopener" class="share-btn share-x" aria-label="Share on X">
        <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        X
      </a>
      <a href="mailto:?subject=Great%20gift%20guide&body={blog_share_text}%20{blog_url}" class="share-btn share-em" aria-label="Share via email">
        <svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        Email
      </a>
      <button class="share-btn share-copy" onclick="navigator.clipboard.writeText('{blog_url}').then(function(){{var b=event.target.closest('.share-copy');b.classList.add('copied');b.innerHTML='Copied!';setTimeout(function(){{b.classList.remove('copied');b.innerHTML='<svg viewBox=&quot;0 0 24 24&quot; style=&quot;width:14px;height:14px;fill:currentColor&quot;><path d=&quot;M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z&quot;/></svg> Copy link';}},2000)}})" aria-label="Copy link">
        <svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
        Copy link
      </button>
    </div>"""

    content_html = f"""
    <div style="max-width:900px;margin:56px auto 0;padding:0 24px">
      <div style="display:inline-flex;align-items:center;gap:10px;font-size:.68rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--primary);margin-bottom:22px">
        <span style="display:block;width:18px;height:1px;background:var(--primary)"></span>
        {date_str} · Gift Guide
      </div>
      <h1 style="font-family:'Playfair Display','Cormorant Garamond',serif;font-size:clamp(2rem,4vw,3.2rem);font-weight:600;line-height:1.08;letter-spacing:-.05em;color:var(--ink);margin-bottom:20px">{post.get("heading", post["title"])}</h1>
      <p style="font-size:1.06rem;line-height:1.78;color:var(--muted);margin-bottom:44px;padding-bottom:40px;border-bottom:1px solid var(--divider);font-weight:300">{post.get("description", "")}</p>
    </div>
    <div style="max-width:900px;margin:0 auto;padding:0 24px 40px">
      <div class="blog-prose">{content_html_body}</div>
      {blog_share_bar}
    </div>
    """

    if blog_faq_schema_json:
        content_html = f'<script type="application/ld+json">{blog_faq_schema_json}</script>\n' + content_html

    return render_page(
        title=post["title"],
        description=post.get("meta_description", post.get("description", "")),
        heading="", subtitle="",
        products=None, similar_products=related,
        article_date=post.get("date", datetime.date.today().isoformat()),
        content=content_html,
        itemlist_schema=blog_itemlist_schema
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
