# app.py
from flask import Flask, render_template
import os
import boto3
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Amazon PAAPI credentials from .env
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG")
AMAZON_REGION = "uk"  # UK store

# Boto3 client for PAAPI
paapi = boto3.client(
    "paapi5",
    aws_access_key_id=AMAZON_ACCESS_KEY,
    aws_secret_access_key=AMAZON_SECRET_KEY,
    region_name=AMAZON_REGION,
)

# List of search keywords/categories to show
CATEGORIES = ["drinks", "health", "games", "tech", "home", "books"]

def fetch_amazon_products(keywords, max_results=5):
    products = []
    for keyword in keywords:
        try:
            response = paapi.search_items(
                PartnerTag=AMAZON_PARTNER_TAG,
                PartnerType="Associates",
                Keywords=keyword,
                Marketplace="www.amazon.co.uk",
                Resources=[
                    "ItemInfo.Title",
                    "Offers.Listings.Price",
                    "Images.Primary.Large",
                    "DetailPageURL",
                ],
                ItemCount=max_results
            )
            for item in response["ItemsResult"]["Items"]:
                products.append({
                    "title": item["ItemInfo"]["Title"]["DisplayValue"],
                    "price": item.get("Offers", {}).get("Listings", [{}])[0].get("Price", {}).get("DisplayAmount", "N/A"),
                    "image": item["Images"]["Primary"]["Large"]["URL"],
                    "url": item["DetailPageURL"],
                    "category": keyword.capitalize()
                })
        except Exception as e:
            print(f"Error fetching {keyword}: {e}")
    return products

@app.route("/")
def index():
    items = fetch_amazon_products(CATEGORIES)
    return render_template("index.html", items=items)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
