import os
from flask import Flask, render_template
import boto3
import openai

app = Flask(__name__)

# Load environment variables
AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize Amazon PAAPI client (using boto3 for Product Advertising API)
paapi = boto3.client(
    "advertising-api",
    aws_access_key_id=AMAZON_ACCESS_KEY,
    aws_secret_access_key=AMAZON_SECRET_KEY,
    region_name="eu-west-1"  # UK
)

# Example ASINs you want to track
PRODUCT_ASINS = [
    "B08N5WRWNW",  # Example ASINs; replace with real UK ASINs
    "B07XQXZXJC",
    "B07YLD3DL3",
]

def fetch_amazon_products():
    """Fetch product info from Amazon PAAPI"""
    products = []
    for asin in PRODUCT_ASINS:
        try:
            response = paapi.get_items(
                ItemIds=[asin],
                Resources=[
                    "Images.Primary.Medium",
                    "ItemInfo.Title",
                    "ItemInfo.Features",
                    "Offers.Listings.Price"
                ]
            )
            item = response["ItemsResult"]["Items"][0]
            products.append({
                "title": item["ItemInfo"]["Title"]["DisplayValue"],
                "image": item["Images"]["Primary"]["Medium"]["URL"],
                "url": f"https://www.amazon.co.uk/dp/{asin}/?tag={AMAZON_ASSOC_TAG}"
            })
        except Exception as e:
            print(f"Error fetching ASIN {asin}: {e}")
    return products

def generate_hype_text(title):
    """Generate marketing description for product using GPT"""
    prompt = f"Write a short, energetic UK marketing description for this product: {title}"
    response = openai.Completion.create(
        model="gpt-4-mini",
        prompt=prompt,
        max_tokens=80
    )
    return response.choices[0].text.strip()

@app.route("/")
def home():
    products = fetch_amazon_products()
    for product in products:
        product["description"] = generate_hype_text(product["title"])
    return render_template("index.html", products=products)

if __name__ == "__main__":
    app.run(debug=True)
