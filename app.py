import os
import json
import re
import datetime
from datetime import date
from threading import Thread
from products_data import PRODUCTS
from blog_data import BLOGS

from flask import Flask, render_template_string, request, url_for, abort, Response
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CACHE_FILE = "/data/cache.json"
HISTORY_FILE = "/data/history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = "https://fybobuybo.com"
ITEMS_PER_PAGE = 12

# Ensure data directory exists
os.makedirs("/data", exist_ok=True)


# ---------------- BLOG SECTION ---------------- #
BLOG_POSTS = {
    "8-essential-home-products-to-upgrade-your-space-in-2026": {
        "title": "8 Essential Home Products to Upgrade Your Space in 2026",
        "description": "Discover trending home upgrades for 2026 – smart devices, cozy textiles, and practical essentials to refresh your UK home affordably.",
        "heading": "8 Essential Home Upgrades for 2026",
        "subtitle": "Trending Amazon picks to make your space smarter, cozier, and more efficient this year.",
        "date": "2025-12-26",
        "content": """
            <article style="max-width:900px;margin:40px auto;line-height:1.8;font-size:1.1rem;color:#fff;">
                <p>As we step into 2026, many UK households are looking for simple, affordable ways to refresh their living spaces. From energy-saving tech to cozy comforts, here are 8 essential home products trending right now on Amazon.</p>
                
                <h2>1. Philips Hue Smart Bulbs</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/philips-hue-white-smart-bulb-twin-pack-led-b22-bayonet-cap--dimmable-bluetooth--and--zigbee-compatible-works-with-alexa-google-assistant-and-apple-homekit">
        <img src="https://m.media-amazon.com/images/I/71T9DZUoqhL._AC_SX679_.jpg" alt="Philips Hue Smart Bulbs" loading="lazy" style="border-radius:16px;">
    </a>
    <p>Control lighting from your phone, set moods, and save energy – perfect starter smart home upgrade.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
    <a href="/product/philips-hue-white-smart-bulb-twin-pack-led-b22-bayonet-cap--dimmable-bluetooth--and--zigbee-compatible-works-with-alexa-google-assistant-and-apple-homekit">
        <button>View Details & Buy</button>
    </a> <a href="https://amzn.to/4pWqfaj?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Lighting', 'event_label': 'Philips Hue Twin Pack', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>2. Ninja Foodi Max Dual Zone Air Fryer AF400UK - 9.5L</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/ninja-foodi-max-dual-zone-air-fryer-af400uk-9-5l">
        <img src="https://m.media-amazon.com/images/I/519tKaMrTZL._AC_SX679_.jpg" 
             alt="Ninja Foodi Max Dual Zone Air Fryer 9.5L – two independent cooking zones" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Large 9.5L dual-zone air fryer lets you cook two different foods two ways at once and finish at the same time with Sync. Up to 75% less fat than deep frying, 6 functions (air fry, roast, bake, reheat, dehydrate, max crisp) – perfect for quick, healthier family meals.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/ninja-foodi-max-dual-zone-air-fryer-af400uk-9-5l">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/45kdy0K?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Ninja Dual Zone Air Fryer', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>3. MeacoDry Arete Two 12L Dehumidifier and Air Purifier</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/meacodry-arete-two-12l-dehumidifier-and-air-purifier">
        <img src="https://m.media-amazon.com/images/I/51MY3VTr3pL._AC_SX679_.jpg" 
             alt="MeacoDry Arete Two 12L Dehumidifier with HEPA air purification" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Quiet, energy-efficient 12L dehumidifier with built-in HEPA air purifier – perfect for UK homes battling damp, mould, and allergies. Extracts up to 12 litres per day, dries laundry faster, runs ultra-quiet in night mode, and purifies air for healthier breathing all year round.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/meacodry-arete-two-12l-dehumidifier-and-air-purifier">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/49hEeAD?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'MeacoDry Arete Two 12L', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>4. Utopia Towels Luxury Fluffy Bath Mat Rug (50x80cm)</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/utopia-towels-luxury-fluffy-bath-mat-rug-50x80cm---grey">
        <img src="https://m.media-amazon.com/images/I/81WVs6hbW1L._AC_SX679_.jpg" 
             alt="Utopia Towels Luxury Fluffy Grey Bath Mat – soft microfibre rug" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Instant warmth underfoot with non-slip, quick-dry designs. Super-absorbent microfibre that's machine washable and luxuriously plush – bestselling upgrade for cosy bathrooms without the premium price tag.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/utopia-towels-luxury-fluffy-bath-mat-rug-50x80cm---grey">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/4si7AHt?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Utopia Fluffy Bath Mat', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
               <h2>5. SALKING Aromatherapy Essential Oil Diffuser 500ml</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/salking-aromatherapy-essential-oil-diffuser-500ml-ultrasonic-cool-mist-humidifier">
        <img src="https://m.media-amazon.com/images/I/71BdaIxNUaL._AC_SX679_.jpg" 
             alt="SALKING 500ml Aromatherapy Diffuser with LED lights and remote" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Create a relaxing spa atmosphere at home with calming scents. Large 500ml capacity runs up to 15 hours with quiet ultrasonic mist, 7 soothing LED colours, 4 timers, remote control, and auto shut-off – ideal for better sleep, stress relief, and wellness routines.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/salking-aromatherapy-essential-oil-diffuser-500ml-ultrasonic-cool-mist-humidifier">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/3MZhjCD?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'SALKING Aromatherapy Diffuser', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>6. Mia&Coco Electric Heated Throw Blanket 120x160cm</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/mia-and-coco-electric-heated-throw-blanket-120x160cm">
        <img src="https://m.media-amazon.com/images/I/81AJ5sfPWfL._AC_SX679_.jpg" 
             alt="Mia&Coco Electric Heated Throw Blanket – large cosy fleece overblanket" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Stay cozy on the sofa while cutting heating bills. Extra-large 120x160cm flannel fleece throw with 10 heat levels, 9 auto-off timers, machine washable design, and overheat protection – bestselling energy-saving essential for UK winters.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/mia-and-coco-electric-heated-throw-blanket-120x160cm">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/3YmgAhc?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Mia&Coco Heated Throw', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>7. Dyson V15 Detect Advanced Cordless Vacuum Cleaner</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/dyson-v8-advanced-cordless-vacuum-cleaner">
        <img src="https://m.media-amazon.com/images/I/51u1PrfKc2L._AC_SX679_.jpg" 
             alt="Dyson V15 Detect Cordless Vacuum with laser dust detection" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Effortless daily cleaning with laser dust detection, auto-adjusting suction, and HEPA filtration – huge time-saver for busy homes. Reveals invisible dust, deep cleans carpets and hard floors, and runs up to 60 minutes.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/dyson-v8-advanced-cordless-vacuum-cleaner">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/3MZbchx?tag=whoaccepts-21" target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Dyson V15 Detect', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <h2>8. Lifewit Large Capacity Under Bed Storage Organiser Bags (Pack of 2)</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/lifewit-large-capacity-under-bed-storage-organiser-bags-pack-of-2">
        <img src="https://m.media-amazon.com/images/I/71d8uUbZSLL._AC_SX679_.jpg" 
             alt="Lifewit Under Bed Storage Bags – large capacity organisers for clothes and bedding" 
             loading="lazy" style="border-radius:16px;">
    </a>
    <p>Maximise space in smaller UK properties without clutter. Pack of 2 extra-large 100L bags with clear windows, reinforced handles, and breathable fabric – perfect for storing seasonal clothes, duvets, or toys neatly under the bed.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/lifewit-large-capacity-under-bed-storage-organiser-bags-pack-of-2">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/49fUzWa?tag=whoaccepts-21" 
           target="_blank" rel="nofollow sponsored"
           onclick="gtag('event', 'affiliate_click', {'event_category': 'Home & Kitchen', 'event_label': 'Lifewit Under Bed Storage', 'value': 1});">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>
                
                <p>All these products are available with fast delivery. Start your 2026 home refresh today!</p>
            </article>
        """
    },







     

    "10-essential-running-accessories-for-everyday-training-2026": {
        "title": "10 Essential Running Accessories for Everyday Training in 2026",
        "description": "Discover practical running essentials for 2026 – storage, hydration, safety, and comfort accessories ideal for beginners and everyday runners.",
        "heading": "10 Essential Running Accessories for 2026",
        "subtitle": "Practical, affordable running gear to improve comfort, safety, and performance this year.",
        "date": "2025-12-31",
        "content": """
            <article style="max-width:900px;margin:40px auto;line-height:1.8;font-size:1.1rem;color:#fff;">
                <p>Whether you're starting running for the first time or building consistency in 2026, the right accessories can make every run safer and more comfortable. Below are 10 essential running accessories that everyday runners rely on, all widely available online.</p>
                
                <h2>1. Lightweight Running Belt for Phone & Keys</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/haissky-lightweight-running-belt-waist-pack">
        <img src="https://m.media-amazon.com/images/I/51XulFnEUWL._AC_SX425_.jpg" alt="Lightweight running belt with phone pocket" loading="lazy" style="border-radius:16px;">
    </a>
    <p>A slim, bounce-free running belt is one of the most useful accessories for short and long runs. Ideal for carrying your phone, keys, and energy gels without bulky pockets or armbands.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
    <a href="/product/haissky-lightweight-running-belt-waist-pack">
        <button>View Details & Buy</button>
    </a>
    <a href="https://amzn.to/3LpASn2?tag={AFFILIATE_TAG}"
       target="_blank" rel="nofollow sponsored">
        <button style="background:#ff9900;">View on Amazon</button>
    </a>
    </div>
</div>
                
                <h2>2. Reflective Running Armbands for Low-Light Runs</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/reflective-running-armbands-set-of-4">
        <img src="https://m.media-amazon.com/images/I/51IeDoQq7rL._AC_SX679_.jpg" alt="Reflective running armbands for night safety" loading="lazy" style="border-radius:16px;">
    </a>
    <p>Perfect for early morning or evening runs, reflective armbands improve visibility in traffic and poorly lit areas. A simple, low-cost safety upgrade for any runner.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/reflective-running-armbands-set-of-4">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/3L9rfZK?tag={AFFILIATE_TAG}"
           target="_blank" rel="nofollow sponsored">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>

                <h2>3. Lightweight Hydration Vest for Long Runs</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/lumefit-running-vest-phone-holder---hydration-vest-with-water-bottle--reflective-vest-for-men-and-women">
        <img src="https://m.media-amazon.com/images/I/8186wRKgTML._AC_SX679_.jpg" alt="Lightweight running hydration vest with bottles" loading="lazy" style="border-radius:16px;">
    </a>
    <p>For runners increasing distance in 2026, a lightweight hydration vest helps maintain performance without carrying bottles by hand. Adjustable fits make these suitable for beginners and experienced runners alike.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/lumefit-running-vest-phone-holder---hydration-vest-with-water-bottle--reflective-vest-for-men-and-women">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/4sAitou?tag={AFFILIATE_TAG}"
           target="_blank" rel="nofollow sponsored">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>

                <h2>4. Touchscreen-Compatible Running Gloves</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/touchscreen-compatible-running-gloves">
        <img src="https://m.media-amazon.com/images/I/71DXUZ1PXuL._AC_SX679_.jpg" alt="Running gloves with touchscreen fingertips" loading="lazy" style="border-radius:16px;">
    </a>
    <p>Essential for cold-weather runs, lightweight running gloves keep hands warm while allowing phone use without removing them — ideal for winter training and early mornings.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/touchscreen-compatible-running-gloves">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/49iIrnF?tag={AFFILIATE_TAG}"
           target="_blank" rel="nofollow sponsored">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>

                <h2>5. Compression Running Tights for Muscle Support</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/compression-running-tights-for-training">
        <img src="https://m.media-amazon.com/images/I/51EJj5Gm67L._AC_SX679_.jpg" alt="Men’s compression running tights for training and recovery" loading="lazy" style="border-radius:16px;">
    </a>
    <p>Compression tights help reduce muscle fatigue and improve comfort on longer runs. Ideal for cooler weather training, recovery runs, and runners increasing weekly mileage.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/compression-running-tights-for-training">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/4aFtmia?tag={AFFILIATE_TAG}"
           target="_blank" rel="nofollow sponsored">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>

<h2>6. Adjustable Running Headband or Sweatband</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/ear-warmers-headband-with-ponytail-hole">
        <img src="https://m.media-amazon.com/images/I/713-9cSHBJL._AC_SX679_.jpg" alt="Lightweight running headband sweatband" loading="lazy" style="border-radius:16px;">
    </a>
    <p>A simple but effective running essential, sweatbands help keep sweat out of your eyes and improve comfort during warm-weather or high-intensity runs.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/ear-warmers-headband-with-ponytail-hole">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/49aRqZj?tag={AFFILIATE_TAG}"
           target="_blank" rel="nofollow sponsored">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>

<h2>7. Lightweight Running Cap for Sun Protection</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/lightweight-breathable-running-cap">
        <img src="https://m.media-amazon.com/images/I/71JWyjz2zGL._AC_SX679_.jpg" alt="Breathable lightweight running cap" loading="lazy" style="border-radius:16px;">
    </a>
    <p>A breathable running cap protects against sun glare and light rain while improving visibility. Especially useful for summer training and long outdoor runs.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/lightweight-breathable-running-cap">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/3YmhASv?tag={AFFILIATE_TAG}"
           target="_blank" rel="nofollow sponsored">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>

<h2>8. Anti-Blister Running Socks</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/anti-blister-cushioned-running-socks">
        <img src="https://m.media-amazon.com/images/I/8139KpUGwoL._AC_SX679_.jpg" alt="Anti-blister cushioned running socks" loading="lazy" style="border-radius:16px;">
    </a>
    <p>Good socks are one of the most overlooked running essentials. Anti-blister running socks reduce friction, wick moisture, and improve comfort on longer or more frequent runs.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/anti-blister-cushioned-running-socks">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/3KY1nzY?tag={AFFILIATE_TAG}"
           target="_blank" rel="nofollow sponsored">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>

<h2>9. LED Running Light or Clip-On Safety Light</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/led-clip-on-running-safety-light">
        <img src="https://m.media-amazon.com/images/I/81W4PWCupEL._AC_SX679_.jpg" alt="LED clip-on running safety light" loading="lazy" style="border-radius:16px;">
    </a>
    <p>Clip-on LED running lights improve visibility in low-light conditions without bulky headlamps. Ideal for early mornings, evenings, and winter runs.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/led-clip-on-running-safety-light">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/49fdWif?tag={AFFILIATE_TAG}"
           target="_blank" rel="nofollow sponsored">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>

<h2>10. Reusable Soft Water Bottle or Handheld Flask</h2>
<div class="card" style="max-width:600px;margin:40px auto;">
    <a href="/product/reusable-soft-running-water-bottle">
        <img src="https://m.media-amazon.com/images/I/51ABfHBqJKL._AC_SX679_.jpg" alt="Reusable soft water bottle for running" loading="lazy" style="border-radius:16px;">
    </a>
    <p>Soft flasks and handheld bottles provide lightweight hydration for short and medium runs. Collapsible designs reduce bulk as you drink, making them ideal for everyday training.</p>
    
    <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;">
        <a href="/product/reusable-soft-running-water-bottle">
            <button>View Details & Buy</button>
        </a>
        <a href="https://amzn.to/49fUmCp?tag={AFFILIATE_TAG}"
           target="_blank" rel="nofollow sponsored">
            <button style="background:#ff9900;">View on Amazon</button>
        </a>
    </div>
</div>

                <p>These running accessories focus on comfort, safety, and convenience — the areas that matter most when building a consistent running habit in 2026. All items are widely available online with fast delivery.</p>
            </article>
        """
    }
    # Add more posts here later
}
# ---------------- THEMES ---------------- #
THEMES = [
    {
        "bg": "#0f172a",
        "card": "#1e293b",
        "accent": "#38bdf8",
        "button": "#0284c7",
        "tag": "#7dd3fc",
        "text_accent": "#bae6fd",
        "gradient": "linear-gradient(90deg,#0284c7,#38bdf8)"
    }
]

def get_daily_theme():
    return THEMES[datetime.date.today().timetuple().tm_yday % len(THEMES)]

# ---------------- IMPROVED AI HOOK ---------------- #
def generate_hook(name):
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"""
Write a calm, elegant 1–2 sentence description explaining why this product is popular among UK shoppers.
Focus on its practical benefits, quality, or appeal in daily life.
Vary the phrasing across different products — avoid repeating common words like "staple", "essential", or "go-to".
Use <b> tags subtly for key features.
End with a complete sentence.
Product: {name}
"""
            }],
            temperature=0.7,
            max_tokens=120
        )
        hook = r.choices[0].message.content.strip()
        hook = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', hook)
        if not re.search(r'[.!?]$', hook):
            hook += " among UK shoppers."
        return hook
    except Exception as e:
        print(f"Groq error: {e}")
        return "A popular choice among UK shoppers for its quality and everyday appeal."

# ---------------- STORAGE ---------------- #
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def enrich_products(products):
    enriched = []
    for p in products:
        p_copy = dict(p)
        p_copy["hook"] = generate_hook(p["name"])
        # Ensure date_added is carried over
        if "date_added" not in p_copy:
            p_copy["date_added"] = str(datetime.date.today())
        enriched.append(p_copy)
    return enriched

def refresh_products(background=False):
    today = str(datetime.date.today())
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cache = json.load(f)
            if cache.get("date") == today:
                return cache["products"]

    def do_refresh():
        enriched = enrich_products(PRODUCTS)
        with open(CACHE_FILE, "w") as f:
            json.dump({"date": today, "products": enriched}, f)
        history = load_history()
        history[today] = enriched
        save_history(history)

    if background:
        Thread(target=do_refresh).start()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                cached = json.load(f).get("products", [])
                if cached:
                    return cached
        return [{"name": p["name"], "category": p["category"], "image": p["image"],
                 "url": p["url"], "info": p["info"], "hook": p["info"]} for p in PRODUCTS]
    else:
        do_refresh()
        with open(CACHE_FILE) as f:
            return json.load(f)["products"]

# ---------------- HELPERS ---------------- #
def slugify(text):
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text

def get_categories(history):
    # Use only today's products for nav categories (prevents old duplicates)
    today_str = str(datetime.date.today())
    today_products = history.get(today_str, [])
    if not today_products:
        # Fallback: use current static PRODUCTS list
        today_products = PRODUCTS
    
    cats = set()
    for p in today_products:
        cats.add(p["category"])
        if "season" in p:
            for s in p["season"].split(","):
                stripped = s.strip()
                if stripped:
                    cats.add(stripped)
    return sorted(cats)

def paginate(items, page):
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return items[start:end], len(items)

def shorten_product_name(name, max_length=80):
    if len(name) <= max_length:
        return name
    
    if ',' in name:
        shortened = name.split(',', 1)[0].strip()
        if len(shortened) <= max_length:
            return shortened
    
    if '(' in name:
        shortened = name.split('(', 1)[0].strip()
        if len(shortened) <= max_length:
            return shortened
    
    words = name.split()
    shortened = ''
    for word in words:
        if len(shortened + ' ' + word) <= max_length - 3:
            shortened += (' ' + word) if shortened else word
        else:
            break
    return shortened + '...'

def ensure_hook(p):
    # If hook is missing or fallback, regenerate
    if "hook" not in p or p["hook"] == p.get("info") or "well-regarded product" in p["hook"]:
        p["hook"] = generate_hook(p["name"])
    return p

# ---------------- CSS ---------------- #
CSS_TEMPLATE = """<style>
body{margin:0;background:{{bg}};color:#fff;font-family:'Outfit',sans-serif;padding:20px 20px 40px}
h1{text-align:center;font-size:3rem;background:{{gradient}};-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:40px 0 10px}
.subtitle{text-align:center;opacity:.85;max-width:900px;margin:20px auto;color:{{text_accent}};font-size:1.1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1400px;margin:auto}
.card{background:{{card}};border-radius:22px;padding:20px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.6);transition:transform .3s,box-shadow .3s}
.card:hover{transform:translateY(-8px);box-shadow:0 30px 60px rgba(0,0,0,.7)}
img{width:100%;border-radius:16px;margin:16px 0}
.tag{background:{{tag}};padding:6px 14px;border-radius:20px;font-size:.85rem;display:inline-block;margin-bottom:12px}
button{
    background:{{button}};
    border:none;
    padding:16px 36px;
    border-radius:50px;
    font-size:1.1rem;
    font-weight:900;
    color:white;
    cursor:pointer;
    transition:.3s;
    animation: pulse 2.5s infinite ease-in-out;
}
button:hover{
    opacity:.9;
    transform:scale(1.05);
    animation:none;
}
@keyframes pulse{
    0%{box-shadow:0 0 0 0 rgba(2,132,199,0.4);}
    70%{box-shadow:0 0 0 12px rgba(2,132,199,0);}
    100%{box-shadow:0 0 0 0 rgba(2,132,199,0);}
}
@media (prefers-reduced-motion: reduce){
    button{animation:none;}
}
footer{text-align:center;opacity:.7;margin:80px 0 40px;font-size:.9rem;line-height:1.6}
a{color:{{text_accent}};text-decoration:none}
nav{background:{{card}};padding:16px;margin:20px 0 40px;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.4);text-align:center}
nav a{margin:0 16px;color:{{text_accent}};font-weight:700;font-size:1.1rem;transition:.2s}
nav a:hover{opacity:.8}
.pagination{display:flex;justify-content:center;gap:16px;margin:40px 0}
.pagination a{background:{{button}};padding:10px 16px;border-radius:12px;color:white;text-decoration:none;font-weight:700;transition:.2s}
.pagination a:hover{opacity:.9}
.loading{text-align:center;opacity:.8;margin:80px 0;font-size:1.3rem;color:{{text_accent}};}
@media (max-width:768px){
    nav a{margin:0 10px;font-size:1rem}
    .grid{grid-template-columns:1fr}
}

/* Single product page - center card & constrain image */
.grid:has(> .card:only-child) .card {
    max-width: 600px;
    margin: 0 auto;
}
.grid:has(> .card:only-child) img {
    max-width: 500px;
    width: 100%;
    height: auto;
    margin: 20px auto;
    display: block;
    border-radius: 16px;
}

/* Uniform titles & aligned images */
.card h2 {
    min-height: 70px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 12px 0;
    font-size: 1.25rem;
    line-height: 1.3;
    font-weight: 900;
}

.card img {
    width: 100%;
    max-height: 380px;
    object-fit: contain;
    background: #111827;
    border-radius: 16px;
    margin: 16px 0;
}

/* Button & "More" spacing */
.card > a[onclick] {
    margin: 20px 0 10px;
}
.card p:last-of-type {
    margin: 10px 0;
    font-size: .85rem;
    opacity: .7;
}
</style>"""

# ---------------- HTML TEMPLATE ---------------- #
BASE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="google-site-verification" content="ZDatY7MyS9eDAYQB97mQ_dxlAv2dgd2IqG1kPg82imU" />
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<meta name="description" content="{{ description }}">
<link rel="canonical" href="{{ canonical_url }}">
{% if next_page_url %}
<link rel="next" href="{{ next_page_url }}">
{% endif %}
{% if prev_page_url %}
<link rel="prev" href="{{ prev_page_url }}">
{% endif %}
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-C1YNKZS6PG"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-C1YNKZS6PG');
</script>
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description }}">
<meta property="og:type" content="website">
<meta property="og:url" content="{{ canonical_url }}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&display=swap" rel="stylesheet">
{{ css|safe }}
</head>
<body>

<nav>
    <a href="/">Home</a>
    <a href="/blog">Blog</a>
    {% for cat in categories %}
    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
    {% endfor %}
</nav>

<h1>{{ heading }}</h1>
<p class="subtitle">{{ subtitle }}</p>

<p style="text-align:center;opacity:.7;margin-bottom:40px;">
✔ UK-focused · ✔ Updated daily · ✔ Thoughtfully curated gifts
</p>

{% if products %}
<div class="grid">
{% for p in products %}
<div class="card">
    <span class="tag">{{ p.category }}</span>
    <a href="/product/{{ slugify(p.name) }}">
        <h2>{{ shorten_product_name(p.name) }}</h2>
    </a>

    <a href="/product/{{ slugify(p.name) }}">
        <img src="{{ p.image }}" alt="{{ p.name }} – {{ p.info }}" loading="lazy">
    </a>

       <p>{{ p.hook|safe }}</p>

    {% if p.date_added %}
    <p style="font-size:0.85rem;opacity:.7;margin:16px 0 8px;color:#94a3b8;text-align:center;">
        ↳ Featured on {{ p.date_added }}
    </p>
    {% endif %}

   <script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ shorten_product_name(p.name) }}",
  "image": "{{ p.image }}",
  "description": "{{ p.info }}",
  "url": "{{ p.url }}",
  "brand": {"@type": "Brand", "name": "{{ p.brand or 'Various' }}"},
  "offers": {
    "@type": "Offer",
    "url": "{{ p.url }}",
    "availability": "https://schema.org/InStock",
    "seller": {
      "@type": "Organization",
      "name": "Amazon"
    }
  }
}
</script>

   <script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "{{ SITE_URL }}/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "{{ p.category }}",
      "item": "{{ SITE_URL }}/category/{{ slugify(p.category) }}"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "{{ shorten_product_name(p.name) }}"
    }
  ]
}
</script>

    <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored" 
       aria-label="View {{ p.name }} on Amazon"
       onclick="gtag('event', 'affiliate_click', { 
           'event_category': '{{ p.category }}', 
           'event_label': '{{ p.name }}', 
           'value': 1,
           'page_path': window.location.pathname
       });">
        <button>View on Amazon</button>
    </a>

    <p style="font-size:.85rem;opacity:.7;margin-top:16px;">
        More <a href="/category/{{ slugify(p.category) }}">{{ p.category }}</a> gifts
    </p>
</div>
{% endfor %}
</div>

{# === RELATED PRODUCTS SECTION (only shows on single product pages) === #}

<h2 style="text-align:center;margin:60px 0 20px;font-size:2rem;background:{{gradient}};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
    More Popular {{ related_products[0].category if related_products else 'UK' }} Gifts
</h2>

{% if related_products %}
<div class="grid">
    {% for rp in related_products %}
    <div class="card">
        <span class="tag">{{ rp.category }}</span>
        <a href="/product/{{ slugify(rp.name) }}">
            <h2>{{ shorten_product_name(rp.name) }}</h2>
        </a>
        <a href="/product/{{ slugify(rp.name) }}">
            <img src="{{ rp.image }}" alt="{{ rp.name }} – {{ rp.info }}" loading="lazy">
        </a>
        <p>{{ rp.hook|safe }}</p>
        <a href="{{ rp.url }}" target="_blank" rel="nofollow sponsored" 
           aria-label="View {{ rp.name }} on Amazon">
            <button>View on Amazon</button>
        </a>
    </div>
    {% endfor %}
</div>
{% else %}
<p style="text-align:center;opacity:.7;">Check out more top gifts across the UK!</p>
{% endif %}



{% else %}
<p class="loading">
    Loading today's gifts...<br>
    <small>Generating fresh AI descriptions – this only happens once per day.</small>
</p>
{% endif %}

<footer>
    <p><strong>As an Amazon Associate, I earn from qualifying purchases.</strong></p>
    <p>FyboBuybo is an independent UK gifts site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.</p>
</footer>

</body>
</html>
"""

# ---------------- ROUTES ---------------- #
def render_page(title, description, heading, subtitle, products, page=1, page_url=lambda p: "#", related_products=None):
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    history = load_history()
    categories = get_categories(history)
    canonical = SITE_URL + request.path
    page_num = int(request.args.get("page", 1))
    if page_num > 1:
        canonical += f"?page={page_num}"

    paged_products, total_items = paginate(products, page)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    # ---------------- Pagination rel links ---------------- #
    next_page_url = page_url(page + 1) if page < total_pages else None
    prev_page_url = page_url(page - 1) if page > 1 else None

    return render_template_string(
        BASE_HTML,
        title=title,
        description=description,
        heading=heading,
        subtitle=subtitle,
        products=paged_products,
        categories=categories,
        css=css,
        canonical_url=canonical,
        SITE_URL=SITE_URL,
        slugify=slugify,
        shorten_product_name=shorten_product_name,
        related_products=related_products or [],
        total_pages=total_pages,
        page=page,
        page_url=page_url,
        button=theme["button"],
        next_page_url=next_page_url,
        prev_page_url=prev_page_url
    )


@app.route("/")
def home():
    products = refresh_products(background=False)[:ITEMS_PER_PAGE]
    return render_page(
        title="FyboBuybo – Trending UK Gifts & Popular Presents",
        description="Discover today's trending UK gifts and popular presents across toys, beauty, electronics and more. Independently curated and refreshed daily.",
        heading="FyboBuybo – Trending UK Gifts",
        subtitle="A curated selection of popular gifts and presents, refreshed daily.",
        products=products
    )

@app.route("/category/<slug>")
def category(slug):
    history = load_history()
    unique_products = {}
    for day in history.values():
        for p in day:
            # Match on category OR any season tag
            if slugify(p["category"]) == slug or ("season" in p and slugify(slug) in [slugify(s.strip()) for s in p["season"].split(",")]):
                key = p["name"] + p["url"]
                unique_products[key] = p
    products = [ensure_hook(p) for p in unique_products.values()]
    
    if not products:
        abort(404)
    
    # Use the original name for display (find first match)
    cat_name = next((p["category"] if slugify(p["category"]) == slug else s.strip() 
                     for p in unique_products.values() 
                     for s in (p.get("season", "").split(",") if "season" in p else []) 
                     if slugify(s.strip()) == slug), slug.replace("-", " ").title())

    def page_url(p):
        return url_for("category", slug=slug, page=p)

    page = int(request.args.get("page", 1))
    return render_page(
        title=f"{cat_name} – FyboBuybo",
        description=f"Explore popular {cat_name.lower()} in the UK, featuring trending gifts and bestsellers.",
        heading=cat_name,
        subtitle=f"Hand-picked selection of {cat_name.lower()}, updated daily.",
        products=products,
        page=page,
        page_url=page_url
    )


@app.route("/product/<path:product_slug>")
def product_detail(product_slug):
    decoded_slug = product_slug.replace("-", " ").lower()

    history = load_history()
    today_str = str(datetime.date.today())
    all_days = history.copy()
    today_products = refresh_products(background=True)
    all_days[today_str] = today_products

    found_product = None
    for day_prods in all_days.values():
        for p in day_prods:
            if slugify(p["name"]) == product_slug:
                found_product = ensure_hook(p)
                break
        if found_product:
            break

    if not found_product:
        abort(404)

    # ---------------- Related products ----------------
    related = []
    for day_prods in all_days.values():
        for p in day_prods:
            if p["category"] == found_product["category"] and p["name"] != found_product["name"]:
                related.append(ensure_hook(p))

    # Remove duplicates and limit to 6
    related = list({p["name"] + p["url"]: p for p in related}.values())[:6]

    # Fallback: if no related products, show other popular items from the same season
    if not related and "season" in found_product:
        for day_prods in all_days.values():
            for p in day_prods:
                if p["name"] != found_product["name"] and any(
                    s.strip() in p.get("season", "") for s in found_product["season"].split(",")
                ):
                    related.append(ensure_hook(p))
        related = list({p["name"] + p["url"]: p for p in related}.values())[:6]

    return render_page(
        title=f"{shorten_product_name(found_product['name'])} – FyboBuybo",
        description=found_product["info"],
        heading=shorten_product_name(found_product["name"]),
        subtitle="A popular UK gift choice",
        products=[found_product],
        related_products=related
        
    )
    
@app.route("/blog")
def blog_index():
    # Sort posts by date descending (newest first)
    sorted_posts = sorted(
        BLOG_POSTS.items(),
        key=lambda x: x[1].get("date", "1900-01-01"),
        reverse=True
    )
    
    post_list_html = """
    <div style="max-width:900px;margin:60px auto;padding:20px;">
        <h2 style="text-align:center;margin-bottom:40px;font-size:2rem;background:{{ gradient }};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            Latest Articles
        </h2>
        <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:30px;">
    """
    
    for slug, post in sorted_posts:
        # Format date nicely: December 31, 2025
        from datetime import datetime
        date_obj = datetime.strptime(post["date"], "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
        
        post_list_html += f"""
            <div class="card">
                <h3 style="font-size:1.5rem;margin-bottom:8px;">
                    <a href="/blog/{slug}" style="color:#bae6fd;text-decoration:none;">
                        {post['title']}
                    </a>
                </h3>
                <p style="opacity:.7;font-size:0.95rem;margin:0 0 12px 0;color:#94a3b8;">
                    {formatted_date}
                </p>
                <p style="opacity:.85;font-size:1rem;line-height:1.6;">
                    {post['description']}
                </p>
            </div>
        """
    
    post_list_html += """
        </div>
    </div>
    """
    
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    
    rendered = render_template_string(
        BASE_HTML,
        title="Blog – FyboBuybo",
        description="Gift guides, home tips, and trending product recommendations",
        heading="FyboBuybo Blog",
        subtitle="Latest articles on gifts and home inspiration",
        products=[],
        categories=[], 
        css=css,
        canonical_url=SITE_URL + "/blog",
        SITE_URL=SITE_URL,
        slugify=slugify,
        shorten_product_name=shorten_product_name,
        related_products=[],
        gradient=theme["gradient"],
        next_page_url=None,
        prev_page_url=None
    )
    
    rendered = rendered.replace('{% for cat in categories %}\n    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>\n    {% endfor %}', '')
    
    subtitle_end = rendered.find('</p>', rendered.find('<p class="subtitle">')) + 4
    rendered = rendered[:subtitle_end] + post_list_html + rendered[subtitle_end:]
    
    rendered = rendered.replace('<div class="grid">\n</div>', '').replace('<div class="grid"></div>', '')
    
    return rendered

@app.route("/blog/<slug>")
def blog_detail(slug):
    post = BLOG_POSTS.get(slug)
    if not post:
        abort(404)
    
    all_products = refresh_products(background=True)
    related = [p for p in all_products if p["category"] in ["Home & Kitchen", "Electronics"]][:6]
    
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    
    rendered = render_template_string(
        BASE_HTML,
        title=post["title"],
        description=post["description"],
        heading=post["heading"],
        subtitle=post["subtitle"],
        products=[],
        categories=[],
        css=css,
        canonical_url=SITE_URL + request.path,
        SITE_URL=SITE_URL,
        slugify=slugify,
        shorten_product_name=shorten_product_name,
        related_products=related,
        gradient=theme["gradient"],
        next_page_url=None,
        prev_page_url=None
    )
    
    rendered = rendered.replace('{% for cat in categories %}\n    <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>\n    {% endfor %}', '')
    
    subtitle_end = rendered.find('</p>', rendered.find('<p class="subtitle">')) + 4
    rendered = rendered[:subtitle_end] + post["content"] + rendered[subtitle_end:]
    
    rendered = rendered.replace('<div class="grid">\n</div>', '').replace('<div class="grid"></div>', '')
    
    return rendered

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
    urls = {
        (SITE_URL + "/", str(datetime.date.today())),
        (SITE_URL + "/all-gifts", str(datetime.date.today()))
    }

    for day_products in history.values():
        for p in day_products:
            # Category URLs
            urls.add((SITE_URL + "/category/" + slugify(p["category"]), str(datetime.date.today())))
            # Product URLs
            urls.add((SITE_URL + "/product/" + slugify(p["name"]), str(datetime.date.today())))

    sitemap_xml = "<?xml version='1.0' encoding='UTF-8'?>\n"
    sitemap_xml += "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"

    for url, lastmod in sorted(urls):
        sitemap_xml += f"""
  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
  </url>"""

    sitemap_xml += "\n</urlset>"
    return Response(sitemap_xml, mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
