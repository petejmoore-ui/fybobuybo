import os
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from amazon_paapi import AmazonAPI
from groq import GroqClient

app = Flask(__name__)

# Load environment variables
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG")
REGION = os.getenv("REGION", "uk")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Amazon API
amazon = AmazonAPI(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG, REGION)

# Initialize Groq AI
groq_client = GroqClient(api_key=GROQ_API_KEY)

# Cached trending products
trending_products = []

def fetch_trending_products():
    global trending_products
    try:
        # Example category query
        products = amazon.search_products(keywords="trending", search_index="All", item_count=8)
        trending_products = [{
            "title": p.title,
            "url": p.detail_page_url,
            "image": p.images.primary.medium.url,
            "price": p.price_and_currency[0] if p.price_and_currency else "N/A",
            "category": p.product_group
        } for p in products]
        print("Fetched latest trending products.")
    except Exception as e:
        print("Error fetching products:", e)

# Schedule fetching every 6 hours
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_trending_products, "interval", hours=6)
scheduler.start()

# Fetch on startup
fetch_trending_products()

@app.route("/")
def index():
    return render_template("index.html", products=trending_products)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
