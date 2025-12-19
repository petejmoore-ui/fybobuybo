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

AFFILIATE_TAG = "whoaccepts-21"

# Your current products – keep your own image URLs and any custom info you added
PRODUCTS = [
    {
    "name": "FOLOKE LED Light Therapy Mask Skin Care",
    "category": "Beauty & Personal Care",
    "image": "https://m.media-amazon.com/images/I/71rZJYKSpgL._AC_SX425_.jpg",  # Replace with the actual high-res main image from the Amazon page if available
    "url": "https://www.amazon.co.uk/FOLOKE-Light-Therapy-Mask-Skin/dp/B0F6N5ZNY9?tag={AFFILIATE_TAG}",
    "info": "Rechargeable LED light therapy mask with red & near-infrared light for skin rejuvenation, fine line reduction, and improved tone/texture — portable and suitable for home use, with comfortable silicone fit."
},

    {
    "name": "Mini Projector Portable 20000 Lux 4K Supported",
    "category": "Electronics",
    "image": "https://m.media-amazon.com/images/I/61FJ2edQURL._AC_SY300_SX300_QL70_ML2_.jpg",  # Replace with actual high-res from page if available (right-click main photo)
    "url": f"https://www.amazon.co.uk/Projector-Portable-Supported-Rotation-Compatible/dp/B0FMR73KL2?tag={AFFILIATE_TAG}",
    "info": "Compact portable projector with Android 11, built-in apps, 180° rotation, auto keystone — perfect for home cinema, outdoor movies, or gaming. High brightness and compatibility make it a top trending choice."
},
    {"name": "Gezqieunk Christmas Jumper Women Xmas Printed Sweatshirt", "category": "Fashion", 
     "image": "https://m.media-amazon.com/images/I/61Tm7Sqg13L._AC_SX679_.jpg",
     "url": f"https://www.amazon.co.uk/Gezqieunk-Christmas-Sweatshirts-Crewneck-Sweaters/dp/B0FXF94VW8?tag={AFFILIATE_TAG}",
     "info": "Festive oversized jumper with fun Christmas prints — perfect cosy gift, surging in popularity for holiday parties and family photos."},
    {"name": "Karaoke Machine for Kids with Microphone", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81QJgWZmfyL._AC_SX679_.jpg",
     "url": f"https://www.amazon.co.uk/Kids-Karaoke-Machine-Birthday-Girls-Pink/dp/B0DK4NL37F?tag={AFFILIATE_TAG}",
     "info": "Mini karaoke set with lights, Bluetooth, and mic — top Christmas gift for kids, massive sales spike for family sing-alongs."},
    {"name": "L’Oréal Paris Revitalift Laser Anti-Ageing Day Cream", "category": "Beauty", 
     "image": "https://m.media-amazon.com/images/I/41uhhU1DU7L._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/LOreal-Paris-Revitalift-Pro-Xylane-Anti-Ageing/dp/B00SNOAZM8?tag={AFFILIATE_TAG}",
     "info": "Triple-action cream reduces wrinkles and firms skin — huge mover in beauty for gifting season and self-care routines."},
    {"name": "OCOOPA Magnetic Hand Warmers Rechargeable 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/61sa5Gx+ZQL._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/OCOOPA-Magnetic-Rechargeable-Handwarmers-Certified/dp/B0CH34CB3P?tag={AFFILIATE_TAG}",
     "info": "Portable, double-sided heat with magnetic design — essential for cold UK winter walks, commuters, and outdoor events."},
    {"name": "Herd Mentality Board Game", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/61jvW6xtkdL._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/Herd-Mentality-Board-Game-Addictive/dp/B09S3YBBRR?tag={AFFILIATE_TAG}",
     "info": "Hilarious party game where you try to think like the herd — perfect family/party entertainment, flying off shelves for Christmas."},
    {"name": "Amazon Fire TV Stick 4K", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/61TzK204IjL._AC_SX679_.jpg",
     "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B08XVYZ1Y5?tag={AFFILIATE_TAG}",
     "info": "Stream 4K content with Dolby Vision and Alexa voice control — top gift for movie lovers and home entertainment upgrades."},
]

# 6 Daily Rotating Themes
THEMES = [
    { # 1: Original Dark Purple-Red
        "bg": "#0d0d1f",
        "card": "#161630",
        "accent": "#ff4e4e",
        "button": "#ff4e4e",
        "tag": "#8b5cf6",
        "text_accent": "#ff6b6b",
        "gradient": "linear-gradient(90deg,#ff4e4e,#8b5cf6)"
    },
    { # 2: Winter Blue
        "bg": "#0f172a",
        "card": "#1e293b",
        "accent": "#60a5fa",
        "button": "#3b82f6",
        "tag": "#93c5fd",
        "text_accent": "#93c5fd",
        "gradient": "linear-gradient(90deg,#3b82f6,#60a5fa)"
    },
    { # 3: Festive Green-Red
        "bg": "#111827",
        "card": "#1f2937",
        "accent": "#ef4444",
        "button": "#dc2626",
        "tag": "#22c55e",
        "text_accent": "#22c55e",
        "gradient": "linear-gradient(90deg,#dc2626,#22c55e)"
    },
    { # 4: Midnight Teal
        "bg": "#0f172a",
        "card": "#164e63",
        "accent": "#06b6d4",
        "button": "#0891b2",
        "tag": "#22d3ee",
        "text_accent": "#67e8f9",
        "gradient": "linear-gradient(90deg,#0891b2,#22d3ee)"
    },
    { # 5: Sunset Orange
        "bg": "#1e1b4b",
        "card": "#312e81",
        "accent": "#f97316",
        "button": "#ea580c",
        "tag": "#fb923c",
        "text_accent": "#fdba74",
        "gradient": "linear-gradient(90deg,#ea580c,#f97316)"
    },
    { # 6: Emerald Luxury
        "bg": "#022c22",
        "card": "#065f46",
        "accent": "#10b981",
        "button": "#059669",
        "tag": "#34d399",
        "text_accent": "#6ee7b7",
        "gradient": "linear-gradient(90deg,#059669,#34d399)"
    }
]

def get_daily_theme():
    day_of_year = datetime.date.today().timetuple().tm_yday
    theme_index = day_of_year % len(THEMES)
    return THEMES[theme_index]

CSS_TEMPLATE = """
<style>
body{margin:0;background:{{bg}};color:#fff;font-family:'Outfit',sans-serif;padding:20px}
h1{text-align:center;font-size:3.5rem;background:{{gradient}};-webkit-background-clip:text;color:transparent}
.subtitle{text-align:center;opacity:.8;margin-bottom:40px;font-size:1.2rem;max-width:900px;margin-left:auto;margin-right:auto;color:{{text_accent}}}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1400px;margin:auto}
.card{background:{{card}};border-radius:22px;padding:22px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:.3s}
.card:hover{transform:scale(1.05)}
img{width:100%;border-radius:16px;transition:0.3s}
.card a img:hover{opacity:0.9;transform:scale(1.03)}
.tag{background:{{tag}};padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:10px}
button{background:{{button}};border:none;padding:14px 36px;border-radius:50px;font-size:1.2rem;font-weight:900;color:white;cursor:pointer}
.hook{margin:14px 0;line-height:1.5}
footer{text-align:center;opacity:.6;margin:60px 0}

/* Big "Read More" button */
details {margin-top:16px;}
details summary {font-weight:900;font-size:1.1rem;color:{{accent}};cursor:pointer;display:inline-block;padding:10px 20px;background:{{card}};border:2px solid {{accent}};border-radius:50px;transition:0.3s;}
details summary:hover {background:{{accent}};color:white;}
details[open] summary {border-radius:50px 50px 0 0;}
details p {background:{{card}};padding:16px;border-radius:0 0 16px 16px;border:2px solid {{accent}};border-top:none;margin:0;font-size:0.9rem;opacity:0.9;}
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
  
  <a href="{{ p.url }}" target="_blank">
    <img src="{{ p.image }}" alt="{{ p.name }}">
  </a>
  
  <h3>{{ p.name }}</h3>
  <div class="hook">{{ p.hook|safe }}</div>
  
  <details>
    <summary>Read More ↓</summary>
    <p>{{ p.info }}</p>
  </details>
  
  <a href="{{ p.url }}" target="_blank">
    <button>Check Price 🔥</button>
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
                "content": f"Create a unique, exciting 1-2 sentence sales hook starting with the product name '{name}'. Make it relevant to the product's appeal, use <b> tags for bold emphasis (no **), vary the style, and end with a natural call to action like 'Perfect for gifting!' or 'Add to basket today!' Keep it under 120 characters if possible."
            }],
            temperature=1.0,
            max_tokens=120  # Increased from 90 → full sentences
        )
        return r.choices[0].message.content
    except Exception as e:
        print(f"Groq error: {e}")
        return f"<b>{name}</b> is a popular choice this season.<br>Perfect for your basket!"

def refresh_products():
    today = str(datetime.date.today()) + "-reset"

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
    products = refresh_products()
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    return render_template_string(HTML, products=products, css=css)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
