# --- Section 1: Setup, SEO, Themes, AI Hooks, Caching --- #

import os, json, re, datetime, random
from threading import Thread
from products_data import PRODUCTS
from blog_data import BLOG_POSTS

from flask import Flask, render_template_string, request, url_for, abort, Response
from groq import Groq
from dotenv import load_dotenv
import requests

# --- Core site settings ---
SITE_URL = "https://www.fybobuybo.com"
ITEMS_PER_PAGE = 12
CACHE_REFRESH_DAYS = 10
AFFILIATE_TAG = "whoaccepts-21"
PROMPT_VERSION = "v2.2-uk-seo-2026"

# --- SEO: automatic search engine ping ---
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
            pass  # silently ignore failures

# --- Environment setup ---
load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- Staging SEO safeguard ---
if os.environ.get("STAGING") == "true":
    @app.after_request
    def add_header(response):
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        return response

# --- Cache / History files ---
CACHE_FILE = "data/cache.json"
HISTORY_FILE = "data/history.json"
os.makedirs("data", exist_ok=True)

# ---------------- THEMES ---------------- #
THEMES = [{"bg":"#0f172a","card":"#1e293b","accent":"#38bdf8","button":"#0284c7",
           "tag":"#7dd3fc","text_accent":"#bae6fd","gradient":"linear-gradient(90deg,#0284c7,#38bdf8)"}]

def get_daily_theme():
    return THEMES[datetime.date.today().timetuple().tm_yday % len(THEMES)]

# ---------------- AI HOOK GENERATION ---------------- #
HOOK_STYLES = ["benefit-first","lifestyle-story","quality-craft","quiet-genius"]
FALLBACK_HOOK = "A popular choice among UK shoppers for its quality and everyday appeal."

def generate_hook(product):
    if "hook_override" in product and product["hook_override"].strip():
        return product["hook_override"].strip()
    name = product["name"]
    category = product.get("category","")
    keywords = product.get("keywords",[])
    pain_points = product.get("pain_points",[])
    price_tier = product.get("price_tier","")
    style = random.choice(HOOK_STYLES)
    prompt = f"""
You are a sophisticated British copywriter creating calm, elegant 1–2 sentence product highlights 
loved by UK shoppers in 2026.

Core rules:
- Max 2 sentences
- Focus on practical benefits
- Avoid hype words
- Use <b> tags subtly around standout features
- Sound refined, trustworthy

Style: {style}
Category: {category}
Price feel: {price_tier}
Common UK context: {', '.join(pain_points) if pain_points else 'everyday practicality and lasting value'}
Target phrases: {', '.join(keywords) if keywords else 'none'}
Product: {name}
Output only the sentences.
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
        return FALLBACK_HOOK

# ---------------- CACHING ---------------- #
def should_refresh_cache():
    if not os.path.exists(CACHE_FILE):
        return True
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        cache_date = datetime.datetime.fromisoformat(cache.get("date","2000-01-01T00:00:00"))
        days_old = (datetime.datetime.now() - cache_date).days
        if days_old >= CACHE_REFRESH_DAYS:
            return True
        if cache.get("prompt_version") != PROMPT_VERSION:
            return True
        return False
    except:
        return True

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(HISTORY_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)

def load_or_generate_hooks(products):
    enriched = []
    for p in products:
        p_copy = dict(p)
        p_copy["hook"] = generate_hook(p)
        p_copy.setdefault("date_added", str(datetime.date.today()))
        p_copy["hook_version"] = PROMPT_VERSION
        enriched.append(p_copy)
    today_iso = datetime.datetime.now().isoformat()
    with open(CACHE_FILE,"w",encoding="utf-8") as f:
        json.dump({"date": today_iso,"prompt_version":PROMPT_VERSION,"products":enriched},f,indent=2,ensure_ascii=False)
    history = load_history()
    history_key = datetime.date.today().isoformat()
    history[history_key] = enriched
    save_history(history)

    # --- SEO: ping Google/Bing asynchronously after sitemap updates ---
    Thread(target=ping_search_engines, daemon=True).start()

    return enriched

def refresh_products(background=False):
    today = str(datetime.date.today())
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache = json.load(f)
            cache_date_str = cache.get("date","")
            if cache_date_str.startswith(today):
                return cache.get("products",[])
            cache_date = datetime.datetime.fromisoformat(cache_date_str)
            if (datetime.datetime.now()-cache_date).days < CACHE_REFRESH_DAYS and cache.get("prompt_version")==PROMPT_VERSION:
                return cache.get("products",[])
        except Exception as e:
            print(f"Cache read failed: {e}")
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
        "Valentine's Day","Mother's Day","Easter","Father's Day",
        "Summer Gifts","Back to School","Halloween","Christmas"
    ]
    important_seasons = [s for s in important_seasons_order if s in seasons_set]
    other_seasons = sorted(seasons_set - set(important_seasons))
    seasons = other_seasons + important_seasons
    return {"categories": categories,"seasons": seasons}

def paginate(items, page):
    start = (page-1)*ITEMS_PER_PAGE
    end = start+ITEMS_PER_PAGE
    return items[start:end], len(items)

def shorten_product_name(name,max_length=80):
    if len(name)<=max_length:
        return name
    for sep in [',','(']:
        if sep in name:
            short = name.split(sep,1)[0].strip()
            if len(short)<=max_length:
                return short
    words,out = name.split(), ""
    for w in words:
        if len(out + " " + w) <= max_length-3:
            out += (" " if out else "") + w
        else:
            break
    return out+"..."

def ensure_hook(p):
    if "hook" not in p or not p["hook"]:
        p["hook"] = FALLBACK_HOOK
    return p


# --- Section 2: CSS, Base HTML Template, and Page Rendering --- #

from flask import render_template_string, Markup

# ---------------- BASE_CSS ---------------- #
BASE_CSS = """
/* ==========================
   Global & Layout
   ========================== */
body {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    background: {{ theme.bg }};
    color: #e2e8f0;
    margin: 0;
    padding: 0;
}
a { text-decoration: none; color: inherit; }
header { background: {{ theme.card }}; padding: 1rem; text-align: center; }
header h1 { margin: 0; font-size: 2rem; }
header nav { margin-top: 0.5rem; }
header nav a { margin: 0 0.8rem; color: {{ theme.accent }}; font-weight: 600; }
.container { max-width: 1300px; margin: auto; padding: 1rem; }

/* ==========================
   Cards
   ========================== */
.product-card {
    background: {{ theme.card }};
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
    transition: transform 0.2s, box-shadow 0.2s;
}
.product-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 18px rgba(0,0,0,0.4);
}
.product-name { font-weight: 700; margin-bottom: 0.4rem; font-size: 1.4rem; }
.product-hook { font-style: italic; color: {{ theme.text_accent }}; margin-bottom: 0.6rem; }
.blog-card { border-left: 4px solid {{ theme.accent }}; padding-left: 1rem; }

/* ==========================
   Buttons
   ========================== */
button {
    background: {{ theme.button }};
    color: white;
    border: none;
    padding: 0.6rem 1.2rem;
    border-radius: 0.3rem;
    cursor: pointer;
    font-weight: bold;
}
button:hover { opacity: 0.9; }

/* ==========================
   Breadcrumbs & Pagination
   ========================== */
.breadcrumb { color: #94a3b8; font-size: 0.9rem; margin-bottom: 1rem; }
.pagination { display: flex; gap: 12px; justify-content: center; margin: 1.6rem 0; }
.pagination button { padding: 0.5rem 1rem; }

/* ==========================
   Tags / Season Labels
   ========================== */
.season-tag {
    background: {{ theme.tag }};
    border-radius: 0.25rem;
    padding: 0.2rem 0.6rem;
    font-size: 0.8rem;
    margin-right: 0.4rem;
}

/* ==========================
   Responsive
   ========================== */
@media (max-width: 768px) {
    header nav { font-size: .9rem; }
}
"""


# ---------------- BASE_HTML ---------------- #
BASE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} – FyboBuyBo</title>
<meta name="description" content="{{ meta_description }}">
<meta name="keywords" content="{{ meta_keywords }}">
<link rel="canonical" href="{{ canonical_url }}">

<style>{{ base_css }}</style>
</head>
<body>
<header>
    <h1><a href="/">FyboBuyBo</a></h1>
    <nav>
        {% for cat in nav.categories %}
            <a href="{{ url_for('category', slug=slugify(cat)) }}">{{ cat }}</a>
        {% endfor %}
        {% if nav.seasons %}
            {% for season in nav.seasons %}
                <a href="{{ url_for('seasonal_collection', season_slug=slugify(season)) }}"
                   class="season-link">{{ season }}</a>
            {% endfor %}
        {% endif %}
        <a href="/blog">Blog</a>
    </nav>
</header>

<main class="container">
    {% if breadcrumbs %}
    <div class="breadcrumb">
        {% for crumb in breadcrumbs %}
            {% if not loop.last %}
                <a href="{{ crumb.url }}">{{ crumb.name }}</a> &raquo;
            {% else %}
                {{ crumb.name }}
            {% endif %}
        {% endfor %}
    </div>
    {% endif %}

    {% if products %}
        {% for p in products %}
            {{ render_product_card(p)|safe }}
        {% endfor %}
    {% elif blog_posts %}
        {% for post in blog_posts %}
        <div class="product-card blog-card">
            <h2 class="product-name">{{ post.title }}</h2>
            {% if post.date %}
            <p class="post-date">{{ post.date }}</p>
            {% endif %}
            <p class="product-hook">{{ post.description }}</p>
            <a href="{{ SITE_URL }}/blog/{{ post.slug }}">
                <button>Read More</button>
            </a>
        </div>
        {% endfor %}
    {% endif %}

    {% if next_page_url or prev_page_url %}
    <div class="pagination">
        {% if prev_page_url %}<a href="{{ prev_page_url }}"><button>« Previous</button></a>{% endif %}
        {% if next_page_url %}<a href="{{ next_page_url }}"><button>Next »</button></a>{% endif %}
    </div>
    {% endif %}
</main>

<footer>
    <p>&copy; {{ current_year }} FyboBuyBo. All rights reserved.</p>
    <p>As an Amazon Associate, I earn from qualifying purchases.</p>
</footer>
</body>
</html>
"""


# ---------------- BREADCRUMB HELPERS ---------------- #
def make_breadcrumbs(items):
    crumbs = [{"name": "Home", "url": url_for("home")}]
    for name, url in items:
        crumbs.append({"name": name, "url": url})
    return crumbs


# ---------------- ROUTES / PAGES ---------------- #
def render_page(title, description, heading, subtitle, products, page=1, page_url=lambda p: "#", related_products=None):
    theme = get_daily_theme()
    return render_template_string(
        BASE_HTML,
        title=title,
        meta_description=description,
        meta_keywords="",
        canonical_url=SITE_URL + request.path,
        base_css=BASE_CSS,
        theme=theme,
        nav=get_nav_items(),
        breadcrumbs=None,
        products=products,
        blog_posts=[],
        current_year=datetime.datetime.now().year,
        SITE_URL=SITE_URL,
        slugify=slugify,
        render_product_card=render_product_card,
        next_page_url=page_url(page+1) if page_url and products else None,
        prev_page_url=page_url(page-1) if page_url and page>1 else None
    )

# ---------------- HOME PAGE ---------------- #
@app.route("/")
def home():
    products = refresh_products(background=True)[:ITEMS_PER_PAGE]
    return render_page(
        title="FyboBuybo – Trending UK Gifts & Popular Presents",
        description="Discover today's trending UK gifts and popular presents across toys, beauty, electronics and more.",
        heading="FyboBuybo – Trending UK Gifts",
        subtitle="A curated selection of popular gifts and presents, refreshed daily.",
        products=products
    )

# ---------------- CATEGORY PAGE ---------------- #
@app.route("/category/<slug>")
@app.route("/category/<slug>/page/<int:page>")
def category(slug, page=1):
    products = refresh_products(background=True)
    filtered = [p for p in products if slugify(p.get("category","")) == slug]
    if not filtered:
        abort(404)
    cat_name = filtered[0]["category"]
    def page_url(p_num): return url_for("category", slug=slug, page=p_num)
    return render_page(
        title=f"{cat_name} – FyboBuybo",
        description=f"Explore popular {cat_name.lower()} in the UK.",
        heading=cat_name,
        subtitle=f"Hand-picked selection of {cat_name.lower()}, updated daily.",
        products=filtered,
        page=page,
        page_url=page_url
    )

# ---------------- SEASONAL COLLECTION ---------------- #
@app.route("/season/<season_slug>")
@app.route("/season/<season_slug>/page/<int:page>")
def seasonal_collection(season_slug, page=1):
    products = refresh_products(background=True)
    season_name = season_slug.replace('-', ' ').title()
    norm_slug = normalize_for_match(season_slug)
    filtered = [
        p for p in products
        if p.get("season") and any(norm_slug in normalize_for_match(s.strip()) for s in p["season"].split(","))
    ]
    if not filtered:
        abort(404)
    filtered.sort(key=lambda p: p.get("date_added","2000-01-01"), reverse=True)
    def page_url(p_num): return url_for("seasonal_collection", season_slug=season_slug, page=p_num)
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
    products = refresh_products(background=True)
    found = next((p for p in products if slugify(p["name"]) == product_slug), None)
    if not found:
        abort(404)
    related = [p for p in products if p["category"] == found["category"] and p["name"] != found["name"]][:6]
    return render_page(
        title=f"{shorten_product_name(found['name'])} – FyboBuybo",
        description=found["info"],
        heading=shorten_product_name(found["name"]),
        subtitle="A popular UK gift choice",
        products=[found],
        related_products=related
    )

# ---------------- BLOG LIST ---------------- #
POSTS_PER_PAGE = 8

def load_blog_posts():
    # Flatten BLOG_POSTS dict to a list of posts sorted by date descending
    posts = [
        {**v, "slug": k} for k, v in BLOG_POSTS.items()
    ]
    posts.sort(key=lambda x: x.get("date", "1900-01-01"), reverse=True)
    return posts

# ---------------- BLOG LIST ---------------- #
@app.route("/blog")
@app.route("/blog/page/<int:page>")
def blog_list(page=1):
    posts = load_blog_posts()
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    paginated = posts[start:end]
    if not paginated:
        abort(404)

    # Breadcrumbs: Home → Blog
    breadcrumbs = make_breadcrumbs([("Blog", url_for("blog_list"))])

    theme = get_daily_theme()

    return render_template_string(
        BASE_HTML,
        title="FyboBuybo Blog – Tips, Guides & Gift Ideas",
        meta_description="Read the latest gift guides, trends, and tips from FyboBuybo Blog.",
        meta_keywords="blog, gifts, UK, tips, guides",
        canonical_url=SITE_URL + request.path,
        base_css=BASE_CSS,
        theme=theme,
        nav=get_nav_items(),
        breadcrumbs=breadcrumbs,
        products=[],            # no product cards
        blog_posts=paginated,   # display blog posts
        current_year=datetime.datetime.now().year,
        SITE_URL=SITE_URL,
        slugify=slugify,
        render_product_card=render_product_card,
        next_page_url=url_for("blog_list", page=page+1) if end < len(posts) else None,
        prev_page_url=url_for("blog_list", page=page-1) if page > 1 else None
    )


# ---------------- BLOG DETAIL ---------------- #
@app.route("/blog/<slug>")
def blog_detail(slug):
    post = BLOG_POSTS.get(slug)
    if not post:
        abort(404)

    # Breadcrumbs: Home → Blog → Post
    breadcrumbs = make_breadcrumbs([
        ("Blog", url_for("blog_list")),
        (post["title"], request.path)
    ])

    all_products = refresh_products(background=True)
    related = [p for p in all_products if p["category"] in ["Home & Kitchen", "Electronics"]][:6]

    theme = get_daily_theme()

    return render_template_string(
        BASE_HTML,
        title=post["title"],
        meta_description=post.get("description", ""),
        meta_keywords="blog, gifts, UK, tips, guides",
        canonical_url=SITE_URL + request.path,
        base_css=BASE_CSS,
        theme=theme,
        nav=get_nav_items(),
        breadcrumbs=breadcrumbs,
        products=[],            # no product cards
        blog_posts=[post],      # single post
        current_year=datetime.datetime.now().year,
        SITE_URL=SITE_URL,
        slugify=slugify,
        render_product_card=render_product_card,
        next_page_url=None,
        prev_page_url=None
    )




# ---------------- ROBOTS.TXT ---------------- #
@app.route("/robots.txt")
def robots():
    sitemap_url = f"{SITE_URL}/sitemap.xml"
    txt = f"""User-agent: *
Disallow:

Sitemap: {sitemap_url}
"""
    return Response(txt, mimetype="text/plain")

# ---------------- SITEMAP.XML ---------------- #
@app.route("/sitemap.xml")
def sitemap():
    history = load_history()
    urls = set()
    today = str(datetime.date.today())

    # Homepage
    urls.add((SITE_URL + "/", today))

    # Products & Categories
    all_products = [p for day in history.values() for p in day]
    for p in all_products:
        lastmod = p.get("date_added", today)
        if p.get("category"):
            urls.add((f"{SITE_URL}/category/{slugify(p['category'])}", lastmod))
        if p.get("name"):
            urls.add((f"{SITE_URL}/product/{slugify(p['name'])}", lastmod))

    # Seasonal pages
    seasons = ["Valentine's Day", "Mother's Day", "Easter", "Father's Day",
               "Summer Gifts", "Back to School", "Halloween", "Christmas"]
    for season in seasons:
        season_slug = slugify(season)
        season_products = [p for p in all_products if p.get("season") and season.lower() in p["season"].lower()]
        lastmod = max((p.get("date_added", today) for p in season_products), default=today)
        urls.add((f"{SITE_URL}/season/{season_slug}", lastmod))

    # Blog pages
    for slug, post in BLOG_POSTS.items():
        lastmod = post.get("date", today)
        urls.add((f"{SITE_URL}/blog/{slug}", lastmod))
    blog_lastmod = max((post.get("date", today) for post in BLOG_POSTS.values()), default=today)
    urls.add((SITE_URL + "/blog", blog_lastmod))

    # Build XML
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, lastmod in sorted(urls):
        sitemap_xml += f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>\n'
    sitemap_xml += '</urlset>'
    return Response(sitemap_xml, mimetype="application/xml")
