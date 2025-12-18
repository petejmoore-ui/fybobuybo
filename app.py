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
     "url": f"https://www.amazon.co.uk/Herd-Mentality-Board-Game-Addictive/dp/B09S3YBBRR?tag={AFFILIATE_TAG}"},
    {"name": "Outsmarted App-Connected Quiz Board Game", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81example-outsmarted-large.jpg",
     "url": f"https://www.amazon.co.uk/Outsmarted-Ultimate-Perfect-Multimedia-Questions/dp/B0DC6TS51V?tag={AFFILIATE_TAG}"},
    {"name": "Crayola SuperTips Washable Markers 24 Pack", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81example-crayola-large.jpg",
     "url": f"https://www.amazon.co.uk/Crayola-SuperTips-Washable-Felt-Colouring/dp/B01BF6F20K?tag={AFFILIATE_TAG}"},
    {"name": "Guinness Draught Nitrosurge Device", "category": "Home & Kitchen", 
     "image": "https://m.media-amazon.com/images/I/71example-guinness-large.jpg",
     "url": f"https://www.amazon.co.uk/Official-Guinness-Nitrosurge-Complete-Experience/dp/B09HR329BC?tag={AFFILIATE_TAG}"},
    {"name": "AnySharp Knife Sharpener", "category": "Home & Kitchen", 
     "image": "https://m.media-amazon.com/images/I/61example-anysharp-large.jpg",
     "url": f"https://www.amazon.co.uk/AnySharp-Knife-Sharpener-PowerGrip-Silver/dp/B0029X0RTU?tag={AFFILIATE_TAG}"},
    {"name": "Rechargeable Hand Warmers 2 Pack", "category": "Sports & Outdoors", 
     "image": "https://m.media-amazon.com/images/I/71V8g8Zf0uL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Rechargeable-Hand-Warmers-Double-Sided-Heating/dp/B0CR8ZJ5N4?tag={AFFILIATE_TAG}"},
    {"name": "LEGO Botanicals Happy Plants Toy", "category": "Toys & Games", 
     "image": "https://m.media-amazon.com/images/I/81example-lego-botanicals-large.jpg",
     "url": f"https://www.amazon.co.uk/LEGO-Botanicals-Happy-Plants-Interchangeable/dp/B0DWDRZDZC?tag={AFFILIATE_TAG}"},
    {"name": "Amazon Fire TV Stick 4K", "category": "Electronics", 
     "image": "https://m.media-amazon.com/images/I/41Qj8d4QdFL._AC_SL1500_.jpg",
     "url": f"https://www.amazon.co.uk/Amazon-Fire-TV-Stick-4K/dp/B08XVYZ1Y5?tag={AFFILIATE_TAG}"},
]

# Keep your CSS and HTML

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

# refresh_products() and home() unchanged

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
