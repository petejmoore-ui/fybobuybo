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

AFFILIATE_TAG = "whoaccepts-21"  # Your tag!

# Real trending products – December 18, 2025 (Best Sellers + Movers & Shakers)
PRODUCTS = [
    {"name": "Herd Mentality Board Game", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81qB8nF8kUL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Herd-Mentality-Board-Game-Addictive/dp/B09S3YBBRR?tag={AFFILIATE_TAG}",
     "info": "Hilarious party game where you try to think like the herd — perfect family entertainment, massive Christmas bestseller."},
    {"name": "Gaiatop Magnetic Hand Warmers Rechargeable 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/81kW5uO8eGL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Gaiatop-Magnetic-Rechargeable-Portable-Penguin/dp/B0CL5QJ2QW?tag={AFFILIATE_TAG}",
     "info": "Cute penguin design with fast heating — top winter essential for cold hands, surging in sales."},
    {"name": "OCOOPA UT3 Lite Magnetic Hand Warmers Rechargeable 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/71V8g8Zf0uL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/OCOOPA-Magnetic-Rechargeable-Handwarmers-Certified/dp/B0CH34CB3P?tag={AFFILIATE_TAG}",
     "info": "Ultra-thin, magnetic for pairing — long-lasting heat, ideal for outdoor activities and commuting."},
    {"name": "L’Oréal Paris Revitalift Laser Anti-Ageing Day Cream", "category": "Beauty", 
     "image": "https://m.media-amazon.com/images/I/71v3iK7pLZL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/LOreal-Paris-Revitalift-Pro-Xylane-Anti-Ageing/dp/B00SNOAZM8?tag={AFFILIATE_TAG}",
     "info": "Advanced formula reduces wrinkles — popular gifting choice for skincare lovers this season."},
    {"name": "Amazon Fire TV Stick 4K", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/41Qj8d4QdFL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B08XVYZ1Y5?tag={AFFILIATE_TAG}",
     "info": "4K streaming with Alexa — top entertainment upgrade, perfect for movie nights and Christmas binge-watching."},
    {"name": "Sanex Expert Skin Health Hypoallergenic Shower Gel", "category": "Beauty", 
     "image": "https://m.media-amazon.com/images/I/71fR2wZ5uPL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Sanex-Biomeprotect-Hypoallergenic-Shower-570ml/dp/B0977C19NL?tag={AFFILIATE_TAG}",
     "info": "Gentle for sensitive skin with 12-hour hydration — everyday essential trending for winter dryness."},
]

CSS = """
<style>
body{margin:0;background:#0d0d1f;color:#fff;font-family:'Outfit',sans-serif;padding:20px}
h1{text-align:center;font-size:3.5rem;background:linear-gradient(90deg,#ff4e4e,#8b5cf6);-webkit-background-clip:text;color:transparent}
.subtitle{text-align:center;opacity:.8;margin-bottom:40px;font-size:1.2rem;max-width:900px;margin-left:auto;margin-right:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1400px;margin:auto}
.card{background:#161630;border-radius:22px;padding:22px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:.3s}
.card:hover{transform:scale(1.05)}
img{width:100%;border-radius:16px;transition:0.3s}
.card a img:hover{opacity:0.9;transform:scale(1.03)}
.tag{background:#8b5cf6;padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:10px}
button{background:#ff4e4e;border:none;padding:14px 36px;border-radius:50px;font-size:1.2rem;font-weight:900;color:white;cursor:pointer}
.hook{margin:14px 0;line-height:1.5}
footer{text-align:center;opacity:.6;margin:60px 0}

/* Big, pressable "Read More" button */
details {margin-top:16px;}
details summary {font-weight:900;font-size:1.1rem;color:#ff4e4e;cursor:pointer;display:inline-block;padding:10px 20px;background:#161630;border:2px solid #ff4e4e;border-radius:50px;transition:0.3s;}
details summary:hover {background:#ff4e4e;color:white;}
details[open] summary {border-radius:50px 50px 0 0;}
details p {background:#161630;padding:16px;border-radius:0 0 16px 16px;border:2px solid #ff4e4e;border-top:none;margin:0;font-size:0.9rem;opacity:0.9;}
</style>
"""

HTML = """
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

<div class="grid">
{% for p in products %}
<div class="card">
  <span class="tag">{{ p.category }}</span>
  
  <!-- Clickable image -->
  <a href="{{ p.url }}" target="_blank">
    <img src="{{ p.image }}" alt="{{ p.name }}">
  </a>
  
  <h3>{{ p.name }}</h3>
  <div class="hook">{{ p.hook|safe }}</div>
  
  <!-- Big pressable "Read More" -->
  <details>
    <summary>Read More ↓</summary>
    <p>{{ p.info }}</p>
  </details>
  
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
            temperature=1.0,
            max_tokens=90
        )
        return r.choices[0].message.content
    except Exception:
        return f"**{name}** is the must-have everyone's rushing to buy!<br>**Grab yours before stocks run out!** 🔥"

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
