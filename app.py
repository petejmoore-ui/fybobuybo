from flask import Flask, render_template
import os
from dotenv import load_dotenv
import requests
import datetime
import hashlib
import hmac
import base64
from urllib.parse import quote

load_dotenv()  # Load .env file with API keys

app = Flask(__name__)

# Amazon API credentials
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG")
AMAZON_ENDPOINT = "webservices.amazon.co.uk"
AMAZON_URI = "/paapi5/getitems"

# Helper to create signed request (Amazon requires HMAC signing)
def sign_request(payload):
    # For PAAPI5, Amazon recommends using the official SDK (boto3 or amazon-paapi)
    # If using requests directly, signing is needed, which is complex
    # We'll use boto3 in practice for simplicity
    return payload

# Example function to fetch trending products
def get_trending_products():
    """
    This function fetches trending UK products via Amazon API.
    Currently, as a demo, it returns a static list.
    Replace the static list with a call to the Product Advertising API.
    """
    # Replace this block with real API call
    products = [
        {
            "title": "Guinness Draught Nitrosurge",
            "image": "https://images-na.ssl-images-amazon.com/images/I/81EXAMPLE.jpg",
            "url": f"https://www.amazon.co.uk/dp/B000EXAMPLE?tag={AMAZON_ASSOC_TAG}"
        },
        {
            "title": "Velvet Toilet Tissue 24 Rolls",
            "image": "https://images-na.ssl-images-amazon.com/images/I/71EXAMPLE.jpg",
            "url": f"https://www.amazon.co.uk/dp/B000EXAMPLE?tag={AMAZON_ASSOC_TAG}"
        },
        {
            "title": "Nutrition Geeks Magnesium Glycinate",
            "image": "https://images-na.ssl-images-amazon.com/images/I/61EXAMPLE.jpg",
            "url": f"https://www.amazon.co.uk/dp/B000EXAMPLE?tag={AMAZON_ASSOC_TAG}"
        }
    ]
    return products

@app.route("/")
def index():
    products = get_trending_products()
    return render_template("index.html", products=products)

if __name__ == "__main__":
    app.run(debug=True)
