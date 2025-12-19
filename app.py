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

PRODUCTS = [
    {"name": "Gezqieunk Christmas Jumper Women Xmas Printed Sweatshirt", "category": "Fashion", 
     "image": "https://m.media-amazon.com/images/I/61Tm7Sqg13L._AC_SX679_.jpg",
     "url": f"https://www.amazon.co.uk/Gezqieunk-Christmas-Sweatshirts-Crewneck-Sweaters/dp/B0FXF94VW8?tag={AFFILIATE_TAG}",
     "info": "Festive oversized jumper with fun Christmas prints — perfect cosy gift, surging in popularity for holiday parties and family photos.",
     "price": "19.99"},  # Approximate/current from search
    {"name": "Karaoke Machine for Kids with Microphone", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81QJgWZmfyL._AC_SX679_.jpg",
     "url": f"https://www.amazon.co.uk/Kids-Karaoke-Machine-Birthday-Girls-Pink/dp/B0DK4NL37F?tag={AFFILIATE_TAG}",
     "info": "Mini karaoke set with lights, Bluetooth, and mic — top Christmas gift for kids, massive sales spike for family sing-alongs.",
     "price": "29.99"},
    {"name": "L’Oréal Paris Revitalift Laser Anti-Ageing Day Cream", "category": "Beauty", 
     "image": "https://m.media-amazon.com/images/I/41uhhU1DU7L._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/LOreal-Paris-Revitalift-Pro-Xylane-Anti-Ageing/dp/B00SNOAZM8?tag={AFFILIATE_TAG}",
     "info": "Triple-action cream reduces wrinkles and firms skin — huge mover in beauty for gifting season and self-care routines.",
     "price": "19.99"},
    {"name": "OCOOPA Magnetic Hand Warmers Rechargeable 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/61sa5Gx+ZQL._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/OCOOPA-Magnetic-Rechargeable-Handwarmers-Certified/dp/B0CH34CB3P?tag={AFFILIATE_TAG}",
     "info": "Portable, double-sided heat with magnetic design — essential for cold UK winter walks, commuters, and outdoor events.",
     "price": "29.99"},
    {"name": "Herd Mentality Board Game", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/61jvW6xtkdL._AC_SY300_SX300_QL70_ML2_.jpg",
     "url": f"https://www.amazon.co.uk/Herd-Mentality-Board-Game-Addictive/dp/B09S3YBBRR?tag={AFFILIATE_TAG}",
     "info": "Hilarious party game where you try to think like the herd — perfect family/party entertainment, flying off shelves for Christmas.",
     "price": "16.99"},
    {"name": "Amazon Fire TV Stick 4K", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/61TzK204IjL._AC_SX679_.jpg",
     "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B08XVYZ1Y5?tag={AFFILIATE_TAG}",
     "info": "Stream 4K content with Dolby Vision and Alexa voice control — top gift for movie lovers and home entertainment upgrades.",
     "price": "39.99"},
]

CSS = """
<style>
/* Your existing CSS */
</style>
"""

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FyboBuybo - Hottest Amazon UK Deals Today {{ today_date }}</title>
<meta name="description" content="Discover today's top trending Amazon UK deals — seasonal Christmas gifts, winter essentials, viral gadgets. Updated daily!">
<meta name="robots" content="index, follow">

<!-- Open Graph -->
<meta property="og:title" content="FyboBuybo - Hottest Amazon UK Deals {{ today_date }}">
<meta property="og:description" content="Today's top trending Amazon UK deals — winter essentials, Christmas gifts, and viral gadgets everyone's buying. Updated daily!">
<meta property="og:type" content="website">
<meta property="og:url" content="https://fybobuybo.onrender.com/">
<meta property="og:image" content="https://m.media-amazon.com/images/I/61Tm7Sqg13L._AC_SX679_.jpg">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="FyboBuybo - Hottest Amazon UK Deals {{ today_date }}">
<meta name="twitter:description" content="Today's top trending Amazon UK deals — winter essentials, Christmas gifts, and viral gadgets everyone's buying. Updated daily!">
<meta name="twitter:image" content="https://m.media-amazon.com/images/I/61Tm7Sqg13L._AC_SX679_.jpg">

<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
{{ css | safe }}

<!-- Structured Data JSON-LD with Price -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "FyboBuybo - Trending Amazon UK Deals",
  "description": "Daily updated list of the hottest trending products on Amazon UK.",
  "url": "https://fybobuybo.onrender.com/",
  "mainEntity": {
    "@type": "ItemList",
    "name": "Today's Trending Deals {{ today_date }}",
    "numberOfItems": {{ products|length }},
    "itemListElement": [
      {% for p in products %}
      {
        "@type": "ListItem",
        "position": {{ loop.index }},
        "item": {
          "@type": "Product",
          "name": "{{ p.name }}",
          "image": "{{ p.image }}",
          "description": "{{ p.info }}",
          "url": "{{ p.url }}",
          "offers": {
            "@type": "Offer",
            "priceCurrency": "GBP",
            "price": "{{ p.price }}",
            "url": "{{ p.url }}",
            "availability": "https://schema.org/InStock",
            "seller": {
              "@type": "Organization",
              "name": "Amazon UK"
            }
          }
        }
      }{% if not loop.last %},{% endif %}
      {% endfor %}
    ]
  }
}
</script>
</head>
<body>
<!-- Your body HTML unchanged -->
</body>
</html>
"""

# generate_hook, refresh_products, home() unchanged

@app.route("/")
def home():
    products = refresh_products()
    today_date = datetime.date.today().strftime("%B %d, %Y")
    return render_template_string(HTML, products=products, css=CSS, today_date=today_date)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
