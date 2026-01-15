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

# Staging SEO safeguard
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
PROMPT_VERSION = "v2.2-uk-seo-2026"

os.makedirs("data", exist_ok=True)

# ---------------- THEMES ---------------- #
THEMES = [
    {
        "name": "Light Elegance",
        "bg": "#fdfdfd",
        "card": "#ffffff",
        "accent": "#1f2937",
        "button": "#3b82f6",
        "tag": "#dbeafe",
        "text_accent": "#475569",
        "gradient": "linear-gradient(90deg, #3b82f6, #06b6d4)"
    },
    {
        "name": "Dark Luxe",
        "bg": "#0f172a",
        "card": "#1e293b",
        "accent": "#f8fafc",
        "button": "#3b82f6",
        "tag": "#1e40af",
        "text_accent": "#cbd5e1",
        "gradient": "linear-gradient(90deg, #3b82f6, #60a5fa)"
    }
]

DEFAULT_THEME = THEMES[0]  # Light Elegance is the fixed default

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
            pass

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

CSS_TEMPLATE = """<style>
:root {
    --bg: {{bg | default('#fdfdfd')}};
    --card: {{card | default('#ffffff')}};
    --accent: {{accent | default('#1f2937')}};
    --button: {{button | default('#3b82f6')}};
    --tag: {{tag | default('#dbeafe')}};
    --text-accent: {{text_accent | default('#475569')}};
    --gradient: {{gradient | default('linear-gradient(90deg, #3b82f6, #06b6d4)')}};
    --shadow-sm: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    --shadow-md: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    --shadow-lg: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
    --transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

* { box-sizing: border-box; margin:0; padding:0; }

body {
    background: var(--bg);
    color: var(--accent);
    font-family: 'Outfit', system-ui, -apple-system, sans-serif;
    line-height: 1.58;
    min-height: 100vh;
    padding: 1.5rem 1rem 4rem;
    transition: var(--transition);
}

h1 {
    font-size: clamp(2.5rem, 7vw, 4.5rem);
    font-weight: 900;
    letter-spacing: -0.025em;
    text-align: center;
    margin: 2.5rem 0 0.75rem;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    text-align: center;
    max-width: 42rem;
    margin: 0 auto 1.5rem;
    color: var(--text-accent);
    font-size: 1.15rem;
    opacity: 0.9;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.75rem;
    max-width: 1400px;
    margin: 0 auto;
}

.card {
    background: var(--card);
    border-radius: 1.375rem;
    padding: 1.5rem;
    text-align: center;
    box-shadow: var(--shadow-lg);
    border: 1px solid color-mix(in srgb, var(--card) 85%, #000);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}

.card:hover {
    transform: translateY(-12px);
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
}

.card img {
    width: 100%;
    height: 320px;
    object-fit: contain;
    border-radius: 1rem;
    margin: 1rem 0;
    transition: transform 0.5s ease;
}

.card:hover img {
    transform: scale(1.06);
}

.tag {
    background: var(--tag);
    color: var(--accent);
    padding: 0.4rem 1rem;
    border-radius: 999px;
    font-size: 0.875rem;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 1rem;
}

button,
a.button-like {
    background: var(--gradient);
    color: white;
    border: none;
    padding: 0.85rem 2rem;
    border-radius: 999px;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    transition: var(--transition);
    display: inline-block;
    text-decoration: none;
}

button:hover,
a.button-like:hover {
    transform: translateY(-2px) scale(1.04);
    box-shadow: 0 10px 25px rgba(59,130,246,0.3);
    background-position: 100% 50%;
    background-size: 200% 200%;
}

#theme-toggle {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 1000;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    border: none;
    background: var(--button);
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-md);
    transition: var(--transition);
}

#theme-toggle:hover {
    transform: scale(1.1);
}

nav {
    background: var(--card);
    border-radius: 1rem;
    padding: 1rem 1.5rem;
    margin: 1.5rem auto;
    max-width: 1400px;
    box-shadow: var(--shadow-md);
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: space-between;
    align-items: center;
}

.nav-top a,
.nav-desktop a,
.dropdown-content a {
    color: var(--text-accent);
    text-decoration: none;
    font-weight: 600;
    padding: 0.5rem 1rem;
    transition: var(--transition);
}

.nav-top a:hover,
.nav-desktop a:hover,
.dropdown-content a:hover {
    color: var(--accent);
    background: color-mix(in srgb, var(--tag) 30%, transparent);
    border-radius: 0.5rem;
}

#search-input {
    padding: 0.75rem 1.25rem;
    border-radius: 999px;
    border: 1px solid var(--text-accent);
    background: transparent;
    color: var(--accent);
    width: 100%;
    max-width: 360px;
    font-size: 1rem;
}

footer {
    text-align: center;
    margin-top: 6rem;
    color: var(--text-accent);
    font-size: 0.9rem;
    line-height: 1.7;
}

/* Mobile adjustments */
@media (max-width: 768px) {
    .grid { grid-template-columns: 1fr; }
    nav { flex-direction: column; }
}

/* Loading / empty state */
.loading {
    text-align: center;
    padding: 6rem 1rem;
    color: var(--text-accent);
    font-size: 1.25rem;
}
</style>"""

# ---------------- HTML TEMPLATE ---------------- #
BASE_HTML = """<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }}</title>
    <meta name="description" content="{{ description | truncate(160, true, '...') }}">
    <link rel="canonical" href="{{ canonical_url }}">

    <!-- Open Graph / Twitter -->
    <meta property="og:title" content="{{ title }}">
    <meta property="og:description" content="{{ description | truncate(200) }}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{{ canonical_url }}">
    <meta property="og:image" content="{{ SITE_URL }}/static/og-default.jpg">
    <meta name="twitter:card" content="summary_large_image">

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;900&display=swap" rel="stylesheet">

    {{ css|safe }}
</head>
<body>

    <!-- Theme Toggle -->
    <button id="theme-toggle" aria-label="Toggle dark mode">
        <svg id="theme-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/>
            <line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/>
            <line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
    </button>

    <nav aria-label="Main navigation">
        <div class="nav-top">
            <a href="/">Home</a>
            <a href="/blog">Blog</a>
        </div>

        <div class="nav-desktop">
            {% for cat in nav_items.categories %}
                <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
            {% endfor %}
            {% if nav_items.seasons %}
                <span style="margin:0 1rem; opacity:0.4;">•</span>
                {% for season in nav_items.seasons %}
                    <a href="/season/{{ slugify(season) }}">{{ season }}</a>
                {% endfor %}
            {% endif %}
        </div>

        <form id="search-form" role="search">
            <input type="search" id="search-input" placeholder="Search gifts..." aria-label="Search gifts">
        </form>
    </nav>

    <h1>{{ heading }}</h1>
    <p class="subtitle">{{ subtitle }}</p>

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
                <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored" class="button-like">
                    Check price on Amazon
                </a>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <p class="loading">Loading curated gifts...</p>
    {% endif %}

    <footer>
        <p>As an Amazon Associate, I earn from qualifying purchases.</p>
        <p>FyboBuybo – thoughtful UK gift ideas • independent site</p>
    </footer>

    <script>
        const THEMES = [
            { name: "Light", bg: "#fdfdfd", card: "#ffffff", accent: "#1f2937", button: "#3b82f6", tag: "#dbeafe", text_accent: "#475569", gradient: "linear-gradient(90deg, #3b82f6, #06b6d4)" },
            { name: "Dark",  bg: "#0f172a", card: "#1e293b", accent: "#f8fafc", button: "#3b82f6", tag: "#1e40af", text_accent: "#cbd5e1", gradient: "linear-gradient(90deg, #3b82f6, #60a5fa)" }
        ];

        let currentTheme = parseInt(localStorage.getItem('theme')) || 0;

        function applyTheme(idx) {
            const t = THEMES[idx];
            document.documentElement.style.setProperty('--bg', t.bg);
            document.documentElement.style.setProperty('--card', t.card);
            document.documentElement.style.setProperty('--accent', t.accent);
            document.documentElement.style.setProperty('--button', t.button);
            document.documentElement.style.setProperty('--tag', t.tag);
            document.documentElement.style.setProperty('--text-accent', t.text_accent);
            document.documentElement.style.setProperty('--gradient', t.gradient);

            document.querySelectorAll('.card').forEach(el => el.style.background = t.card);
            document.querySelectorAll('.tag').forEach(el => el.style.background = t.tag);
            document.querySelectorAll('button, a.button-like').forEach(el => el.style.background = t.gradient);
            document.querySelectorAll('h1').forEach(el => el.style.background = t.gradient);

            localStorage.setItem('theme', idx);
        }

        applyTheme(currentTheme);

        document.getElementById('theme-toggle').addEventListener('click', () => {
            currentTheme = (currentTheme + 1) % 2;
            applyTheme(currentTheme);
        });
    </script>

    <!-- Add your existing search + dropdown JavaScript here if needed -->
</body>
</html>"""

# ---------------- ROUTES / PAGE RENDERER ---------------- #
@cache.cached(timeout=300, key_prefix=lambda: request.full_path)
def render_page(title, description, heading, subtitle, products=None, page=1, page_url=None, related_products=None):
    theme = DEFAULT_THEME
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

    # Inject blog list after subtitle
    blog_html = '<div class="grid" style="max-width:1100px; margin:40px auto;">'
    
    # Use accent from the default theme (consistent with site theme)
    accent_color = DEFAULT_THEME["accent"]
    
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

    return render_page(
        title=post["title"],
        description=post.get("description", "Gift inspiration and practical tips from FyboBuybo."),
        heading=post.get("heading", post["title"]),
        subtitle=post.get("subtitle", "Gift guide & inspiration"),
        products=None,
        related_products=related
    )

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

    blog_lastmod = today
    if BLOG_POSTS:
        blog_dates = [post.get("date", today) for post in BLOG_POSTS.values()]
        blog_lastmod = max(blog_dates) if blog_dates else today
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
