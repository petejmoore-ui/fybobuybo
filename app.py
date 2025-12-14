import os
from flask import Flask, render_template
from groq import GroqClient
import boto3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Grok client
GROK_API_KEY = os.getenv("GROK_API_KEY")
grok = GroqClient(api_key=GROK_API_KEY)

# Amazon PAAPI client
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
ASSOCIATE_TAG = os.getenv("ASSOCIATE_TAG")

paapi = boto3.client(
    'productadvertisingapi',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='uk'
)

def fetch_trending_products():
    # Example: get top 8 trending products in UK
    response = paapi.search_items(
        Keywords='trending',
        SearchIndex='All',
        ItemCount=8,
        Resources=['Images.Primary.Large', 'ItemInfo.Title', 'Offers.Listings.Price']
    )
    products = []
    for item in response['ItemsResult']['Items']:
        title = item['ItemInfo']['Title']['DisplayValue']
        image = item['Images']['Primary']['Large']['URL']
        url = item['DetailPageURL']
        hook_prompt = f"Write a fun, exciting 2-line hook for this product: {title}"
        hook = grok.complete(prompt=hook_prompt, max_output_tokens=60)
        products.append({
            "title": title,
            "image": image,
            "url": url,
            "hook": hook.text
        })
    return products

@app.route("/")
def home():
    products = fetch_trending_products()
    return render_template("index.html", products=products)

if __name__ == "__main__":
    app.run(debug=True)
