import os
import json
import datetime
import re
from flask import Flask, render_template_string, abort
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"
HISTORY_FILE = "history.json"

AFFILIATE_TAG = "whoaccepts-21"

PRODUCTS = [
    {
        "name": "VonShef 3 Tray Buffet Server & Hot Plate Food Warmer",
        "category": "Home & Kitchen",
        "image": "https://m.media-amazon.com/images/I/71kTQECp3FL._AC_SX679_.jpg",
        "url": f"https://www.amazon.co.uk/VonShef-Tray-Warmer-Buffet-Server/dp/B073Q5G9VX?tag={AFFILIATE_TAG}",
        "info": "3-tray electric buffet server with adjustable temperature — keeps food warm for parties, hosting, or family meals. Top trending choice for holiday entertaining with easy clean trays."
    },
    # Add other products here...
]

THEMES = [
    { "bg": "#0d0d1f", "card": "#161630", "accent": "#ff4e4e", "button": "#ff4e4e", "button_hover": "#8b5cf6", "tag": "#8b5cf6", "text_accent": "#ff6b6b", "gradient": "linear-gradient(90deg,#ff4e4e,#8b5cf6)" },
    { "bg": "#0f172a", "card": "#1e293b", "accent": "#60a5fa", "button": "#3b82f6", "button_hover": "#93c5fd", "tag": "#93c5fd", "text_accent": "#93c5fd", "gradient": "linear-gradient(90deg,#3b82f6,#60a5fa)" },
    # Add other themes here...
]

def get_daily_theme():
    day_of_year = datetime.date.today().timetuple().tm_yday
    theme_index = day_of_year % len(THEMES)
    return THEMES[theme_index]

CSS_TEMPLATE = """
<style>
/* Base styles */
body {
    margin: 0;
    background: {{bg}};
    color: #fff;
    font-family: 'Outfit', sans-serif;
    padding: 20px;
}
h1 {
    text-align: center;
    font-size: 3.5rem;
    background: {{gradient}};
    -webkit-background-clip: text;
    color: transparent;
}
.subtitle {
    text-align: center;
    opacity: 0.8;
    margin-bottom: 40px;
    font-size: 1.2rem;
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
    color: {{text_accent}};
}

/* Card grid */
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 20px;
    max-width: 1400px;
    margin: auto;
}

/* Card styles */
.card {
    background: {{card}};
    border-radius: 22px;
    padding: 18px;
    text-align: center;
    box-shadow: 0 20px 40px rgba(0, 0, 0, .6);
    transition: 0.3s;
    cursor: pointer;
}
.card:hover {
    transform: scale(1.05);
    box-shadow: 0 20px 60px rgba(0, 0, 0, .5);
}

/* Mobile override */
@media (max-width: 768px) {
    .grid {
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 18px;
    }
    .card {
        padding: 20px;
    }
}

img {
    width: 100%;
    border-radius: 16px;
    transition: 0.3s;
    margin-top: 10px;
}
.card a img:hover {
    opacity: 0.9;
    transform: scale(1.03);
}

/* Button styles */
button {
    background: {{button}};
    border: none;
    padding: 14px 36px;
    border-radius: 50px;
    font-size: 1.2rem;
    font-weight: 900;
    color: white;
    cursor: pointer;
    transition: all 0.3s ease;
}
button:hover {
    transform: scale(1.05);
    background: {{button_hover}};
}

/* Hover effect for the Read More section */
details summary {
    font-weight: 900;
    font-size: 1.1rem;
    color: {{accent}};
    cursor: pointer;
    display: inline-block;
    padding: 10px 20px;
    background: {{card}};
    border: 2px solid {{accent}};
    border-radius: 50px;
    transition: 0.3s;
}
details summary:hover {
    background: {{accent}};
    color: white;
}
details[open] summary {
    border-radius: 50px 50px 0 0;
}
details p {
    background: {{card}};
    padding: 16px;
    border-radius: 0 0 16px 16px;
    border: 2px solid {{accent}};
    border-top: none;
    margin: 0;
    font-size: 0.9rem;
    opacity: 0.9;
}

/* Loading spinner */
#loading-spinner {
    display: none;
    text-align: center;
    margin-top: 50px;
    font-size: 1.5rem;
}

/* Archive section */
.archive {
    margin-top: 80px;
}
.archive h2 {
    text-align: center;
    color: {{accent}};
    font-size: 2.2rem;
    margin-bottom: 40px;
}
.archive details {
    margin-bottom: 20px;
}
.archive summary {
    font-size: 1.5rem;
    cursor: pointer;
    color: {{text_accent}};
}
.archive .category-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 20px;
    margin-top: 20px;
}
.category-link {
    color: {{text_accent}};
    text-decoration: underline;
    cursor: pointer;
    margin: 10px;
    display: inline-block;
}
footer {
    text-align: center;
    opacity: 0.6;
    margin: 60px 0;
}
</style>
"""

MAIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>FyboBuybo</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
    {{ css | safe }}
</head>
<body>
    <h1>FyboBuybo</h1>
    <p class="subtitle">Discover the hottest UK deals right now — from seasonal gifts and essentials to viral gadgets everyone's buying. Updated daily with what's trending!</p>

    <h2 style="text-align:center;font-size:2.4rem;margin:60px 0 40px;color:{{accent}};">Today's Trending Deals</h2>
    <div class="grid" id="product-grid">
        {% for p in today_products %}
            <div class="card">
                <span class="tag">{{ p.category }}</span>
                <h3>{{ p.name }}</h3>
                <a href="{{ p.url }}" target="_blank">
                    <img src="{{ p.image }}" alt="{{ p.name }}">
                </a>
                <div class="hook">{{ p.hook|safe }}</div>
                <details>
                    <summary>Read More ↓</summary>
                    <p>{{ p.info }}</p>
                </details>
                <a href="{{ p.url }}" target="_blank">
                    <button>Check Price</button>
                </a>
            </div>
        {% endfor %}
    </div>

    <!-- Archive with category links -->
    <div class="archive">
        <h2>Trend Archive – Explore Past Hot Deals</h2>
        <p style="text-align:center;">
            Browse by category:
            {% for cat in categories %}
                {% set slug = cat|lower|replace(' & ', '-and-')|replace(' ', '-') %}
                <a href="/category/{{ slug }}" class="category-link">{{ cat }}</a>{% if not loop.last %} | {% endif %}
            {% endfor %}
        </p>
        {% if archive_dates %}
            {% for date in archive_dates %}
                <details>
                    <summary>{{ date }} ({{ archive[date]|length }} deals)</summary>
                    {% set grouped = namespace(data={}) %}
                    {% for p in archive[date] %}
                        {% if grouped.data[p.category] is not defined %}
                            {% set _ = grouped.data.update({p.category: []}) %}
                        {% endif %}
                        {% set _ = grouped.data[p.category].append(p) %}
                    {% endfor %}
                    {% for cat, items in grouped.data.items() %}
                        <h3 style="text-align:left;color:{{text_accent}};margin:30px 0 10px;">{{ cat }}</h3>
                        <div class="category-grid">
                            {% for p in items %}
                                <div class="card">
                                    <span class="tag">{{ p.category }}</span>
                                    <h3>{{ p.name }}</h3>
                                    <a href="{{ p.url }}" target="_blank">
                                        <img src="{{ p.image }}" alt="{{ p.name }}">
                                    </a>
                                    <div class="hook">{{ p.hook|safe }}</div>
                                    <a href="{{ p.url }}" target="_blank">
                                        <button>Check Price</button>
                                    </a>
                                </div>
                            {% endfor %}
                        </div>
                    {% endfor %}
                </details>
            {% endfor %}
        {% else %}
            <p style="text-align:center;">Archive building — check back tomorrow!</p>
        {% endif %}
    </div>

    <footer>Affiliate links may earn commission · Made with AI</footer>
</body>
</html>
"""

CATEGORY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>FyboBuybo - Archive: {{ category_title }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
    {{ css | safe }}
</head>
<body>
    <h1>FyboBuybo</h1>
    <p class="subtitle">Explore the latest deals from the {{ category_title }} category. Browse archived products to find trending deals from previous weeks!</p>
    <div class="grid">
        {% for p in products %}
            <div class="card">
                <span class="tag">{{ p.category }}</span>
                <h3>{{ p.name }}</h3>
                <a href="{{ p.url }}" target="_blank">
                    <img src="{{ p.image }}" alt="{{ p.name }}">
                </a>
                <div class="hook">{{ p.hook|safe }}</div>
                <details>
                    <summary>Read More ↓</summary>
                    <p>{{ p.info }}</p>
                </details>
                <a href="{{ p.url }}" target="_blank">
                    <button>Check Price</button>
                </a>
            </div>
        {% endfor %}
    </div>
    <footer>Affiliate links may earn commission · Made with AI</footer>
</body>
</html>
"""

@app.route('/')
def homepage():
    theme = get_daily_theme()
    today_products = PRODUCTS  # You can filter this to be relevant products of the day
    return render_template_string(MAIN_HTML, 
                                  today_products=today_products, 
                                  css=CSS_TEMPLATE.format(**theme),
                                  accent=theme["accent"])

@app.route('/category/<category>')
def category_page(category):
    category_title = category.replace("-", " ").title()
    filtered_products = [p for p in PRODUCTS if p["category"].lower() == category.lower()]
    theme = get_daily_theme()
    return render_template_string(CATEGORY_HTML, 
                                  category_title=category_title, 
                                  products=filtered_products, 
                                  css=CSS_TEMPLATE.format(**theme),
                                  accent=theme["accent"])

if __name__ == '__main__':
    app.run(debug=True)

