import os, json, datetime
from flask import Flask, render_template_string
from groq import Groq
from amazon_paapi import AmazonApi, errors  # New import

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"

# PA API setup
amazon = AmazonApi(
    os.environ.get("PA_ACCESS_KEY"),
    os.environ.get("PA_SECRET_KEY"),
    os.environ.get("PA_PARTNER_TAG"),
    "UK",  # For amazon.co.uk
    throttling=1  # 1 second between calls to avoid limits
)

# Hot categories for trending items (BrowseNode IDs for UK)
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
/* Your existing CSS here – same as before */
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
    # Same as before
    ...

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
                keywords="",  # Broad search in category
                browse_node_id=node_id,
                resources=["ItemInfo.Title", "Images.Primary.Large", "Offers.Listings.Price", "BrowseNodeInfo.BrowseNodes.SalesRank"]
            )
            for item in results.items:
                sales_rank = min((bn.sales_rank for bn in item.browse_node_info.browse_nodes if bn.sales_rank), default=999999)
                all_items.append({
                    "name": item.item_info.title.display_value if item.item_info.title else "Unknown",
                    "category": cat_name,
                    "image": item.images.primary.large.url if item.images.primary.large else "",
                    "hook": "",  # Filled later
                    "url": item.detail_page_url,  # Already has your affiliate tag!
                    "sales_rank": sales_rank
                })
        except errors.AmazonError as e:
            print(e)

    # Sort by best sales rank, take top 12
    all_items.sort(key=lambda x: x["sales_rank"])
    top_products = all_items[:12]

    # Generate hooks
    for p in top_products:
        p["hook"] = generate_hook(p["name"])

    with open(CACHE_FILE, "w") as f:
        json.dump({"date": today, "products": top_products}, f)

    return top_products

@app.route("/")
def home():
    return render_template_string(HTML, products=refresh_products(), css=CSS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
