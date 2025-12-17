import os
import json
import datetime
from flask import Flask, render_template_string
from groq import Groq
from amazon_paapi import AmazonApi, errors
from dotenv import load_dotenv  # <-- New: for local .env support

# Load .env file if it exists (only affects local runs – Render ignores it)
load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"

# PA API setup – keys come from Render env vars or local .env
amazon = AmazonApi(
    os.environ.get("PA_ACCESS_KEY"),
    os.environ.get("PA_SECRET_KEY"),
    os.environ.get("PA_PARTNER_TAG"),
    "UK",
    throttling=1
)

# Hot UK categories (BrowseNode IDs)
CATEGORIES = {
    "Electronics": "560798",
    "Books": "266239",
    "Home & Kitchen": "3147781",
    "Beauty": "66235",
    "Toys & Games": "468294",
    "Health": "65801031",
}

CSS = """
<style>
body{margin:0;background:#0d0d1f;color:#fff;font-family:'Outfit',sans-serif;padding:20px}
h1{text-align:center;font-size:3.5rem;background:linear-gradient(90deg,#ff4e4e,#8b5cf6);-webkit-background-clip:text;color:transparent}
.subtitle{text-align:center;opacity:.8;margin-bottom:40px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1400px;margin:auto}
.card{background:#161630;border-radius:22px;padding:22px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:.3s}
.card:hover{transform:scale(1.05)}
img{width:100%;border-radius:16px}
.tag{background:#8b5cf6;padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:10px}
button{background:#ff4e4e;border:none;padding:14px 36px;border-radius:50px;font-size:1.2rem;font-weight:900;color:white;cursor:pointer}
.hook{margin:14px 0;line-height:1.5}
footer{text-align:center;opacity:.6;margin:60px 0}
</style>
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ForYourBuysOnly</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
{{ css | safe }}
</head>
<body>
<h1>ForYourBuysOnly</h1>
<p class="subtitle">Top UK trending buys · Updated daily</p>

<div class="grid">
{% for p in products %}
<div class="card">
  <span class="tag">{{ p.category }}</span>
  {% if p.image %}
  <img src="{{ p.image }}" alt="{{ p.name }}">
  {% else %}
  <img src="https://via.placeholder.com/400x400/111/fff?text=No+Image">
  {% endif %}
  <h3>{{ p.name }}</h3>
  <div class="hook">{{ p.hook|safe }}</div>
  <a href="{{ p.url }}" target="_blank">
    <button>Grab It Now 🔥</button>
  </a>
</div>
{% endfor %}
</div>

<footer>Affiliate links may earn commission · Made with AI</footer>
</body>
</html>
"""

def generate_hook(name):
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"Write a short, exciting 2-line hype hook for this trending UK product: '{name}'. Use bold."
            }],
            temperature=0.85,
            max_tokens=100
        )
        return r.choices[0].message.content
    except Exception:
        return f"<b>{name} is flying off shelves in the UK!</b><br>Grab it before it's gone."

def refresh_products():
    today = str(datetime.date.today())

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            data = json.load(f)
            if data.get("date") == today:
                return data["products"]

    all_items = []
    for cat_name, node_id in CATEGORIES.items():
        try:
            results = amazon.search_items(
                keywords="",
                browse_node_id=node_id,
                resources=[
                    "ItemInfo.Title",
                    "Images.Primary.Large",
                    "BrowseNodeInfo.BrowseNodes.SalesRank"
                ],
                item_count=10
            )
            for item in results.items:
                sales_rank = min(
                    (bn.sales_rank for bn in getattr(item.browse_node_info, 'browse_nodes', []) if bn.sales_rank),
                    default=999999
                )
                all_items.append({
                    "name": getattr(item.item_info.title, 'display_value', 'Unknown') if item.item_info.title else "Unknown",
                    "category": cat_name,
                    "image": item.images.primary.large.url if item.images and item.images.primary.large else "",
                    "hook": "",
                    "url": item.detail_page_url or f"https://www.amazon.co.uk/s?k={item.item_info.title.display_value.replace(' ', '+') if item.item_info.title else ''}&tag={os.environ.get('PA_PARTNER_TAG')}",
                    "sales_rank": sales_rank
                })
        except errors.AmazonError as e:
            print(f"Amazon API error: {e}")

    # Sort by best sales rank, take top 12
    all_items.sort(key=lambda x: x["sales_rank"])
    top_products = all_items[:12]

    # Generate AI hooks
    for p in top_products:
        p["hook"] = generate_hook(p["name"])

    # Cache for the day
    with open(CACHE_FILE, "w") as f:
        json.dump({"date": today, "products": top_products}, f)

    return top_products

@app.route("/")
def home():
    return render_template_string(HTML, products=refresh_products(), css=CSS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
