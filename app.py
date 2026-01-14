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
    'CACHE_TYPE': 'SimpleCache',    # in-memory, perfect for small/medium traffic
    'CACHE_DEFAULT_TIMEOUT': 300    # 5 minutes – good balance for daily refresh
})

# --- Staging SEO safeguard ---
if os.environ.get("STAGING") == "true":
    @app.after_request
    def add_header(response):
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        return response
# -----------------------------

CACHE_FILE = "data/cache.json"
HISTORY_FILE = "data/history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = "https://www.fybobuybo.com"
ITEMS_PER_PAGE = 12

# Cache settings
CACHE_REFRESH_DAYS = 10
PROMPT_VERSION = "v2.2-uk-seo-2026"

os.makedirs("data", exist_ok=True)

# ---------------- THEMES ---------------- #
THEMES = [
    {
        "bg": "#0f172a",
        "card": "#1e293b",
        "accent": "#38bdf8",
        "button": "#0284c7",
        "tag": "#7dd3fc",
        "text_accent": "#bae6fd",
        "gradient": "linear-gradient(90deg,#0284c7,#38bdf8)"
    }
]

def get_daily_theme():
    return THEMES[datetime.date.today().timetuple().tm_yday % len(THEMES)]

# ---------------- SEO: ping search engines ---------------- #
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
            pass  # silent fail

# ---------------- AI HOOK GENERATION ---------------- #
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
            hook += " It’s quietly appreciated among UK shoppers."

        return hook

    except Exception as e:
        print(f"Groq error for '{name}': {e}")
        return f"Appreciated for its <b>lasting quality</b> and thoughtful design in everyday British life."

# ---------------- CACHING ---------------- #
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

    cache.clear()  # if you already added caching

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
                cache = json.load(f)
            cache_date_str = cache.get("date", "")
            if cache_date_str.startswith(today):
                return cache.get("products", [])
            cache_date = datetime.datetime.fromisoformat(cache_date_str)
            if (datetime.datetime.now() - cache_date).days < CACHE_REFRESH_DAYS and \
               cache.get("prompt_version") == PROMPT_VERSION:
                return cache.get("products", [])
        except Exception as e:
            print(f"Cache read failed: {e} — regenerating")

    enriched = load_or_generate_hooks(PRODUCTS)
    return enriched

# ---------------- HELPERS ---------------- #
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
                cache = json.load(f)
            products = cache.get("products", PRODUCTS)
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

FALLBACK_HOOK = "A popular choice among UK shoppers for its quality and everyday appeal."

# ---------------- CSS ---------------- #
CSS_TEMPLATE = """<style>
body { margin:0; background:{{bg}}; color:#fff; font-family:'Outfit',sans-serif; padding:20px 20px 40px; }
h1 { text-align:center; font-size:3rem; background:{{gradient}}; -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:40px 0 10px; }
.subtitle { text-align:center; opacity:.85; max-width:900px; margin:20px auto; color:{{text_accent}}; font-size:1.1rem; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:24px; max-width:1400px; margin:auto; }
.card { background:{{card}}; border-radius:22px; padding:20px; text-align:center; box-shadow:0 20px 40px rgba(0,0,0,.6); transition:transform .3s,box-shadow .3s; }
.card:hover { transform:translateY(-8px); box-shadow:0 30px 60px rgba(0,0,0,.7); }

/* Images - restored original sizing */
img { width:100%; border-radius:16px; margin:16px 0; }
.card img { 
    width: 100%; 
    max-height: 380px; 
    object-fit: contain; 
    background: #111827; 
    border-radius: 16px; 
    margin: 16px 0; 
    display: block; 
}

/* Single product detail page - prevent massive images */
.grid:has(> .card:only-child) .card img {
    max-height: 500px;          /* bigger than grid cards but contained */
    max-width: 80%;             /* prevent full-width stretch */
    width: auto; 
    height: auto; 
    margin: 20px auto; 
    display: block; 
}
.grid:has(> .card:only-child) {
    justify-items: center;      /* center single card */
}

.tag { background:{{tag}}; padding:6px 14px; border-radius:20px; font-size:.85rem; display:inline-block; margin-bottom:12px; }
button {
    background:{{button}}; border:none; padding:12px 28px; border-radius:50px; font-size:1rem; font-weight:900;
    color:white; cursor:pointer; transition:.3s;
}
button:hover { opacity:.9; transform:scale(1.03); }
footer { text-align:center; opacity:.7; margin:80px 0 40px; font-size:.9rem; line-height:1.6; }
a { color:{{text_accent}}; text-decoration:none; }

/* Nav container */
nav {
    background:{{card}}; padding:16px; margin:20px 0 40px; border-radius:16px;
    box-shadow:0 10px 30px rgba(0,0,0,.4); text-align:center;
    display:flex; flex-direction:column; align-items:center; gap:16px;
}

/* Top row: Home + Blog */
.nav-top {
    display:flex; justify-content:center; gap:40px; width:100%;
}
.nav-top a {
    color:{{text_accent}}; font-weight:700; font-size:1.2rem; transition:.2s;
}
.nav-top a:hover { opacity:.8; }

/* Desktop horizontal categories + seasons */
.nav-desktop {
    display: none;
    flex-wrap: wrap; justify-content:center; gap:16px; width:100%;
}
.nav-desktop a {
    margin: 0 12px;
}

/* Mobile dropdowns */
.nav-middle {
    display:flex; justify-content:center; gap:24px; flex-wrap:nowrap;
}

/* Dropdown buttons */
.categories-dropdown, .seasons-dropdown {
    position: relative;
}
.categories-dropdown button, .seasons-dropdown button {
    background: #334155; color: #bae6fd; border: 1px solid #475569;
    padding: 10px 24px; border-radius: 999px; font-weight: 600; font-size: 1rem;
    cursor: pointer; transition: all 0.2s; min-width:140px;
}
.categories-dropdown button:hover, .seasons-dropdown button:hover { 
    background: #475569; color: white; transform: translateY(-1px); 
}
.dropdown-content {
    display: none; position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
    background: {{card}}; border-radius: 12px; padding: 12px 0; min-width: 240px;
    max-height: 60vh; overflow-y: auto;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 100; margin-top: 8px;
}
.dropdown-content a {
    display: block; padding: 10px 24px; color: {{text_accent}}; text-decoration: none;
    font-size: 1rem; white-space: nowrap;
}
.dropdown-content a:hover { background: #334155; }

/* Search bar */
#search-form {
    width:100%; max-width:400px; text-align:center;
}
#search-input {
    padding:10px 20px; border-radius:999px; border:1px solid {{text_accent}}; 
    background:transparent; color:white; width:100%; font-size:1rem; text-align:center;
}

/* Seasons horizontal links (desktop only) */
nav .season-link { 
    color: #a5b4fc; font-size: 1rem; font-weight: 600; padding: 4px 10px; 
    border-radius: 8px; transition: all 0.2s ease; 
}
nav .season-link:hover { 
    opacity: 1; color: #c7d2fe; background: rgba(56, 189, 248, 0.12); 
}

/* Mobile */
@media (max-width:768px) {
    .nav-desktop { display: none !important; }
    .nav-middle { display: flex !important; gap:20px; justify-content:center; }
    .grid { grid-template-columns:1fr; }
}

/* Desktop */
@media (min-width:769px) {
    nav { flex-direction:row; justify-content:space-between; align-items:center; padding:16px 24px; flex-wrap:wrap; }
    .nav-top { flex:0 0 auto; }
    .nav-middle { display:none !important; }
    .nav-desktop { display: flex !important; flex-wrap:wrap; justify-content:center; gap:16px; width:100%; }
    #search-form { flex:0 0 auto; margin-left:auto; max-width:300px; }
    .categories-dropdown, .seasons-dropdown { display: none !important; }
    nav a { margin:0 12px; }
}

/* Rest unchanged */
.pagination { display:flex; justify-content:center; gap:16px; margin:40px 0; }
.pagination a { background:{{button}}; padding:10px 16px; border-radius:12px; color:white; text-decoration:none; font-weight:700; transition:.2s; }
.pagination a:hover { opacity:.9; }
.loading { text-align:center; opacity:.8; margin:80px 0; font-size:1.3rem; color:{{text_accent}}; }
</style>"""


# ---------------- HTML TEMPLATE ---------------- #
BASE_HTML = """<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="google-site-verification" content="ZDatY7MyS9eDAYQB97mQ_dxlAv2dgd2IqG1kPg82imU" />

    <title>{{ title }}</title>
    <meta name="description" content="{{ description | truncate(155, true, '...') }}">

    <link rel="canonical" href="{{ canonical_url }}">
    {% if prev_page_url %}<link rel="prev" href="{{ prev_page_url }}">{% endif %}
    {% if next_page_url %}<link rel="next" href="{{ next_page_url }}">{% endif %}

    <!-- Open Graph -->
    <meta property="og:title" content="{{ title }}">
    <meta property="og:description" content="{{ description | truncate(200, true, '...') }}">
    <meta property="og:type" content="{% if products|length == 1 %}product{% elif '/blog' in request.path %}article{% else %}website{% endif %}">
    <meta property="og:url" content="{{ canonical_url }}">
    <meta property="og:site_name" content="FyboBuybo">
    <meta property="og:image" content="{% if products and products[0].image %}{{ products[0].image }}{% else %}{{ SITE_URL }}/static/og-default.jpg{% endif %}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="{{ title }} – UK gift ideas">

    <!-- Twitter / X Cards -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@CryptoSolGood">
    <meta name="twitter:title" content="{{ title }}">
    <meta name="twitter:description" content="{{ description | truncate(200, true, '...') }}">
    <meta name="twitter:image" content="{% if products and products[0].image %}{{ products[0].image }}{% else %}{{ SITE_URL }}/static/og-default.jpg{% endif %}">
    <meta name="twitter:image:alt" content="{{ title }} – popular UK presents">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">

    <script async src="https://www.googletagmanager.com/gtag/js?id=G-C1YNKZS6PG"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-C1YNKZS6PG');
    </script>

    {{ css|safe }}
</head>
<body>

<!-- Search JS (client-side filtering) -->
<script>
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("search-input");
    if (!searchInput) return;

    const cards = document.querySelectorAll(".grid .card");

    searchInput.addEventListener("input", function(e) {
        const query = e.target.value.toLowerCase().trim();

        cards.forEach(card => {
            const name = card.querySelector("h2")?.textContent.toLowerCase() || "";
            const hook = card.querySelector("p:not([style])")?.textContent.toLowerCase() || "";
            const category = card.querySelector(".tag")?.textContent.toLowerCase() || "";

            const matches = name.includes(query) || hook.includes(query) || category.includes(query);

            card.style.display = matches ? "" : "none";
        });

        const visibleCards = Array.from(cards).filter(c => c.style.display !== "none");
        let noResults = document.getElementById("no-results");
        if (query.length > 0 && visibleCards.length === 0) {
            if (!noResults) {
                noResults = document.createElement("p");
                noResults.id = "no-results";
                noResults.style.textAlign = "center";
                noResults.style.opacity = "0.8";
                noResults.style.margin = "40px 0";
                noResults.style.fontSize = "1.1rem";
                noResults.textContent = "No matching gifts found – try a different search.";
                document.querySelector(".grid")?.after(noResults);
            }
        } else if (noResults) {
            noResults.remove();
        }
    });
});
</script>

<nav aria-label="Main navigation">
    <!-- Top row: Home + Blog (always visible) -->
    <div class="nav-top">
        <a href="/">Home</a>
        <a href="/blog">Blog</a>
    </div>

    <!-- Horizontal categories + seasons (desktop only) -->
    <div class="nav-desktop">
        {% for cat in nav_items.categories %}
            <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
        {% endfor %}

        {% if nav_items.seasons %}
            <span style="margin:0 14px;opacity:0.5;" aria-hidden="true">•</span>

            {% for season in nav_items.seasons %}
                <a href="/season/{{ slugify(season) }}" class="season-link">{{ season }}</a>
            {% endfor %}
        {% endif %}
    </div>

    <!-- Mobile dropdowns: Categories + Seasonal -->
    <div class="nav-middle">
        <div class="categories-dropdown">
            <button>Categories ▼</button>
            <div class="dropdown-content">
                {% for cat in nav_items.categories %}
                    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
                {% endfor %}
            </div>
        </div>

        {% if nav_items.seasons %}
            <div class="seasons-dropdown">
                <button>Seasonal ▼</button>
                <div class="dropdown-content">
                    {% for season in nav_items.seasons %}
                        <a href="/season/{{ slugify(season) }}">{{ season }}</a>
                    {% endfor %}
                </div>
            </div>
        {% endif %}
    </div>

    <!-- Search bar (bottom on mobile, right on desktop) -->
    <form id="search-form">
        <input type="search" id="search-input" placeholder="Search gifts..." />
    </form>
</nav>

<!-- Dropdown JS -->
<script>
document.addEventListener("DOMContentLoaded", function() {
    const dropdowns = document.querySelectorAll(".categories-dropdown, .seasons-dropdown");
    
    dropdowns.forEach(dropdown => {
        const btn = dropdown.querySelector("button");
        const content = dropdown.querySelector(".dropdown-content");
        
        if (!btn || !content) return;
        
        btn.addEventListener("click", function(e) {
            e.stopPropagation();
            const isOpen = content.style.display === "block";
            document.querySelectorAll(".dropdown-content").forEach(el => el.style.display = "none");
            content.style.display = isOpen ? "none" : "block";
        });
    });

    document.addEventListener("click", function(e) {
        if (!e.target.closest(".categories-dropdown, .seasons-dropdown")) {
            document.querySelectorAll(".dropdown-content").forEach(el => el.style.display = "none");
        }
    });
});
</script>

<h1>{{ heading }}</h1>
<p class="subtitle">{{ subtitle }}</p>

<p style="text-align:center;opacity:.7;margin-bottom:40px;">
    ✔ UK-focused · ✔ Updated daily · ✔ Thoughtfully curated gifts
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
        <img src="{{ p.image }}" 
             alt="{{ p.name }} – {{ p.info | truncate(100) }}" 
             loading="lazy" 
             itemprop="image">
    </a>
    <p itemprop="description">{{ p.hook|safe }}</p>
    {% if p.date_added %}
    <p style="font-size:0.85rem;opacity:.7;margin:16px 0 8px;color:#94a3b8;text-align:center;">
        ↳ Featured on {{ p.date_added }}
    </p>
    {% endif %}
    <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored noopener" 
       aria-label="View {{ p.name }} on Amazon"
       onclick="gtag('event', 'affiliate_click', { 
           'event_category': '{{ p.category }}', 
           'event_label': '{{ p.name }}', 
           'value': 1
       });">
        <button>View on Amazon</button>
    </a>
    {% if p.category %}
    <p style="font-size:.85rem;opacity:.7;margin-top:16px;">
        More <a href="/category/{{ slugify(p.category) }}">{{ p.category }}</a> gifts
    </p>
    {% endif %}

    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Product",
      "name": "{{ shorten_product_name(p.name) | e }}",
      "image": "{{ p.image }}",
      "description": "{{ p.info | e }}",
      "url": "{{ SITE_URL }}/product/{{ slugify(p.name) }}",
      "brand": {"@type": "Brand", "name": "{{ p.brand or 'Various' | e }}"},
      "offers": {
        "@type": "Offer",
        "url": "{{ p.url }}",
        "availability": "https://schema.org/InStock",
        "seller": {"@type": "Organization", "name": "Amazon.co.uk"}
      }
    }
    </script>
</div>
{% endfor %}
</div>

<!-- Page-level Breadcrumb -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "{{ SITE_URL }}/"}
    {% if request.path != "/" %},
    {"@type": "ListItem", "position": 2, "name": "{{ heading }}", "item": "{{ canonical_url }}"}
    {% endif %}
  ]
}
</script>

{% if related_products %}
<h2 style="text-align:center;margin:60px 0 20px;font-size:2rem;background:{{gradient}};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
    More Popular {{ related_products[0].category if related_products else 'UK' }} Gifts
</h2>
<div class="grid">
    {% for rp in related_products %}
    <div class="card" itemscope itemtype="https://schema.org/Product">
        <span class="tag">{{ rp.category }}</span>
        <a href="/product/{{ slugify(rp.name) }}" itemprop="url">
            <h2 itemprop="name">{{ shorten_product_name(rp.name) }}</h2>
        </a>
        <a href="/product/{{ slugify(rp.name) }}">
            <img src="{{ rp.image }}" alt="{{ rp.name }} – {{ rp.info | truncate(100) }}" loading="lazy" itemprop="image">
        </a>
        <p itemprop="description">{{ rp.hook|safe }}</p>
        <a href="{{ rp.url }}" target="_blank" rel="nofollow sponsored noopener">
            <button>View on Amazon</button>
        </a>
    </div>
    {% endfor %}
</div>
{% endif %}

{% else %}
<p class="loading">
    Loading today's gifts...<br>
    <small>Generating fresh AI descriptions – this only happens once per day.</small>
</p>
{% endif %}

<footer>
    <p><strong>As an Amazon Associate, I earn from qualifying purchases.</strong></p>
    <p>FyboBuybo is an independent UK gifts site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.</p>
    <p style="opacity:.8;font-size:.9rem;margin-top:20px;">
        All product information, prices, and availability are accurate at the time of publication and subject to change.
    </p>
</footer>

<!-- Homepage structured data -->
{% if request.path == "/" %}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "FyboBuybo",
  "url": "{{ SITE_URL }}",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "{{ SITE_URL }}/?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "FyboBuybo",
  "url": "{{ SITE_URL }}",
  "sameAs": [
    "https://twitter.com/CryptoSolGood",
    "https://www.pinterest.co.uk/petejmoore/"
  ]
}
</script>
{% endif %}

</body>
</html>
"""

# ---------------- ROUTES / PAGE RENDERER ---------------- #
@cache.cached(timeout=300, key_prefix=lambda: request.full_path)
def render_page(title, description, heading, subtitle, products=None, page=1, page_url=None, related_products=None):
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
        related_products=related_products or [],
        next_page_url=next_url,
        prev_page_url=prev_url
    )


# ---------------- HOME ---------------- #
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


# ---------------- CATEGORY ---------------- #
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


# ---------------- SEASONAL ---------------- #
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


# ---------------- PRODUCT DETAIL ---------------- #
@app.route("/product/<path:product_slug>")
def product_detail(product_slug):
    all_products = refresh_products(background=True)
    found = next((p for p in all_products if slugify(p["name"]) == product_slug), None)
    if not found:
        abort(404)
    
    related = [
        p for p in all_products
        if p["category"] == found["category"] and p["name"] != found["name"]
    ][:6]

    return render_page(
        title=f"{shorten_product_name(found['name'])} – FyboBuybo",
        description=found.get("info", "A thoughtful gift choice popular among UK shoppers."),
        heading=shorten_product_name(found["name"]),
        subtitle="A popular UK gift choice",
        products=[found],
        related_products=related
    )


# ---------------- BLOG ---------------- #
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

    theme = get_daily_theme()  # Get theme for accent color

    def page_url(p_num):
        return url_for("blog_list", page=p_num) if p_num <= total_pages else None

    rendered = render_page(
        title="FyboBuybo Blog – Gift Guides, Tips & Inspiration 2026",
        description="Latest UK gift ideas, seasonal guides, home tips and thoughtful present recommendations – updated regularly.",
        heading="FyboBuybo Blog",
        subtitle="Gift guides, trends and inspiration for UK shoppers",
        products=None,  # no products grid
        page=page,
        page_url=page_url
    )

    # Inject blog list after subtitle
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

    # Insert after subtitle block
    insert_point = rendered.find('<p class="subtitle">') 
    if insert_point > -1:
        insert_after = rendered.find('</p>', insert_point) + 4
        rendered = rendered[:insert_after] + blog_html + rendered[insert_after:]

    # Add pagination if needed
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
        related_products=related
    )

    # Inject full blog content after subtitle
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


# ---------------- SEO FILES ---------------- #
@app.route("/robots.txt")
def robots():
    txt = f"""
User-agent: *
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

    # Blog
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
