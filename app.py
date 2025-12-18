import os
import json
import datetime
from flask import Flask, render_template_string
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "cache.json"

AFFILIATE_TAG = "https://amzn.to/4pMfBmH"  # <<< REPLACE WITH YOUR REAL TAG!

# Real trending products – December 18, 2025 (Movers & Shakers + Best Sellers)
PRODUCTS = [
    {"name": "Rechargeable Hand Warmers 10000mAh 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/71V8g8Zf0uL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Rechargeable-Hand-Warmers-Double-Sided/dp/B0CR8ZJ5N4?tag={AFFILIATE_TAG}"},
    {"name": "LEGO Icons Williams Racing FW14B & Nigel Mansell", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81f8e9jVJqL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/LEGO-10356-Williams-Racing-Nigel/dp/B0DJY4K7XW?tag={AFFILIATE_TAG}"},
    {"name": "EasyAcc 1200ml Electric Dehumidifier", "category": "Home & Kitchen", 
     "image": "https://m.media-amazon.com/images/I/71eL5f5rE2L._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/EasyAcc-Dehumidifier-Electric-Portable-Bedroom/dp/B0CM9J3X8V?tag={AFFILIATE_TAG}"},
    {"name": "Sanex Expert Skin Health Hypoallergenic Shower Gel", "category": "Beauty", 
     "image": "https://m.media-amazon.com/images/I/71fR2wZ5uPL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Sanex-Biomeprotect-Hypoallergenic-Shower-570ml/dp/B0977C19NL?tag={AFFILIATE_TAG}"},
    {"name": "TOSY Magnet Fidget Spinner Glow", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81kW5uO8eGL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/TOSY-Magnet-Fidget-Spinner-Rechargeable/dp/B0CL5QJ2QW?tag={AFFILIATE_TAG}"},
    {"name": "Ginger Fox Taskmaster Card Game", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81pXU1r6tBL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Ginger-Fox-Taskmaster-Competitive-Challenges/dp/B0CL5R8X9P?tag={AFFILIATE_TAG}"},
    {"name": "Herd Mentality Board Game", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81qB8nF8kUL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Herd-Mentality-Board-Game-Addictive/dp/B09S3YBBRR?tag={AFFILIATE_TAG}"},
    {"name": "Amazon Fire TV Stick 4K", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/41Qj8d4QdFL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B08XVYZ1Y5?tag={AFFILIATE_TAG}"},
]

CSS = """
<style>
/* Your existing CSS – unchanged */
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
  <img src="{{ p.image }}" alt="{{ p.name }}">
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
                "content": f"Create a unique, exciting 1-2 sentence sales hook for this trending UK Amazon product: '{name}'. Make it urgent and fun, use **bold** for emphasis, vary the style, and end with a strong call to action like 'Snag it now!' or 'Don't wait!'"
            }],
            temperature=1.0,  # Max creativity for originality
            max_tokens=90
        )
        return r.choices[0].message.content
    except Exception:
        return f"**{name}** is the hottest pick everyone's rushing to buy!<br>**Grab yours before stocks run out!** 🔥"

def refresh_products():
    today = str(datetime.date.today())

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            data = json.load(f)
            if data.get("date") == today:
                return data["products"]

    enriched = []
    for p in PRODUCTS:
        enriched.append({**p, "hook": generate_hook(p["name"])})

    with open(CACHE_FILE, "w") as f:
        json.dump({"date": today, "products": enriched}, f)

    return enriched

@app.route("/")
def home():
    return render_template_string(HTML, products=refresh_products(), css=CSS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
