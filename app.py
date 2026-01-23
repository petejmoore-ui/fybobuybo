import os
import json
import re
import datetime
import random
from threading import Thread
from products_data import PRODUCTS
from blog_data import BLOG_POSTS

from flask import Flask, render_template_string, request, url_for, abort, Response, jsonify
from groq import Groq
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# --- Staging SEO safeguard ---
if os.environ.get("STAGING") == "true":
    @app.after_request
    def add_header(response):
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        return response


CACHE_FILE = "data/cache.json"
HISTORY_FILE = "data/history.json"
AFFILIATE_TAG = "whoaccepts-21"
SITE_URL = "https://www.fybobuybo.com"
ITEMS_PER_PAGE = 12

CACHE_REFRESH_DAYS = 10
PROMPT_VERSION = "v3.0-elite-2026"

os.makedirs("data", exist_ok=True)

# Privacy Policy HTML content
PRIVACY_POLICY_HTML = """
<article style="max-width: 900px; margin: 40px auto; padding: 20px;">
  <div style="background: var(--card); padding: 30px; border-radius: 16px; margin-bottom: 30px;">
    <p style="font-size: 1.1rem; line-height: 1.8; margin-bottom: 20px;">
      <strong>Last Updated:</strong> January 23, 2026
    </p>
    <p style="font-size: 1.05rem; line-height: 1.8;">
      FyboBuybo ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your information when you visit our website www.fybobuybo.com.
    </p>
  </div>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">1. Information We Collect</h2>
  
  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">1.1 Automatically Collected Information</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    When you visit our website, we automatically collect certain information about your device and browsing behaviour through cookies and similar technologies:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li><strong>Device Information:</strong> Browser type, operating system, device type</li>
    <li><strong>Usage Data:</strong> Pages visited, time spent on pages, links clicked</li>
    <li><strong>Location Data:</strong> Approximate geographic location based on IP address</li>
    <li><strong>Referral Data:</strong> Website you came from before visiting us</li>
  </ul>

  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">1.2 Information You Provide</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    We do not currently collect personal information directly from you (such as name or email) unless you choose to contact us. Our website does not require registration or account creation.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">2. How We Use Your Information</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    We use the automatically collected information for:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li><strong>Website Functionality:</strong> To remember your preferences (like theme selection)</li>
    <li><strong>Analytics:</strong> To understand how visitors use our site and improve user experience</li>
    <li><strong>Affiliate Tracking:</strong> To track product clicks for our Amazon Associates affiliate programme</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">3. Cookies and Tracking Technologies</h2>
  
  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">3.1 What Are Cookies?</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    Cookies are small text files stored on your device when you visit websites. They help websites remember your preferences and improve your browsing experience.
  </p>

  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">3.2 Cookies We Use</h3>
  
  <div style="background: var(--card); padding: 20px; border-radius: 12px; margin: 20px 0;">
    <h4 style="color: var(--accent); margin-bottom: 10px;">Essential Cookies (Required)</h4>
    <p style="line-height: 1.7; margin-bottom: 10px;">
      <strong>Cookie Name:</strong> <code>themeIndex</code><br>
      <strong>Purpose:</strong> Remembers your light/dark theme preference<br>
      <strong>Duration:</strong> Persistent (until you clear browser data)<br>
      <strong>Legal Basis:</strong> Legitimate interest (website functionality)
    </p>
  </div>

  <div style="background: var(--card); padding: 20px; border-radius: 12px; margin: 20px 0;">
    <h4 style="color: var(--accent); margin-bottom: 10px;">Third-Party Cookies</h4>
    <p style="line-height: 1.7; margin-bottom: 10px;">
      <strong>Amazon Associates:</strong> When you click affiliate links, Amazon may set cookies to track your session for commission purposes. These cookies are controlled by Amazon and subject to <a href="https://www.amazon.co.uk/gp/help/customer/display.html?nodeId=201909010" target="_blank" rel="noopener">Amazon's Privacy Notice</a>.
    </p>
  </div>

  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">3.3 Managing Cookies</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    You can control and delete cookies through your browser settings:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li><strong>Chrome:</strong> Settings > Privacy and security > Cookies and other site data</li>
    <li><strong>Firefox:</strong> Settings > Privacy & Security > Cookies and Site Data</li>
    <li><strong>Safari:</strong> Preferences > Privacy > Manage Website Data</li>
    <li><strong>Edge:</strong> Settings > Cookies and site permissions</li>
  </ul>
  <p style="line-height: 1.8; margin-bottom: 20px; font-style: italic; color: var(--text-muted);">
    Note: Blocking all cookies may affect website functionality, such as theme preferences.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">4. Affiliate Relationships and Amazon</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    FyboBuybo is a participant in the Amazon EU Associates Programme, an affiliate advertising programme designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.co.uk.
  </p>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    When you click on product links and make a purchase on Amazon, we may earn a small commission at no extra cost to you. Amazon handles all transaction data and personal information according to their own privacy policy. We do not receive any of your personal or payment information from Amazon.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">5. Data Sharing and Third Parties</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    We do not sell, trade, or rent your personal information to third parties. We may share aggregated, anonymised data with:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li><strong>Amazon:</strong> For affiliate programme tracking (when you click product links)</li>
    <li><strong>Hosting Provider:</strong> Our website hosting service (necessary for site operation)</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">6. Your Rights Under UK GDPR</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    Under the UK General Data Protection Regulation (UK GDPR) and Data Protection Act 2018, you have the following rights:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li><strong>Right to Access:</strong> Request a copy of data we hold about you</li>
    <li><strong>Right to Rectification:</strong> Request correction of inaccurate data</li>
    <li><strong>Right to Erasure:</strong> Request deletion of your data ("right to be forgotten")</li>
    <li><strong>Right to Restrict Processing:</strong> Request limitation on how we use your data</li>
    <li><strong>Right to Data Portability:</strong> Request transfer of your data to another service</li>
    <li><strong>Right to Object:</strong> Object to processing of your data</li>
    <li><strong>Right to Withdraw Consent:</strong> Withdraw consent for data processing at any time</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">7. Data Retention</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    We retain automatically collected data for as long as necessary to provide our services and comply with legal obligations:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li><strong>Cookie Data:</strong> Stored locally on your device until you clear it or it expires</li>
    <li><strong>Server Logs:</strong> Retained for up to 90 days for security and troubleshooting</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">8. Data Security</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    We implement appropriate technical and organisational measures to protect your data, including:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>HTTPS encryption for all website traffic</li>
    <li>Secure hosting infrastructure</li>
    <li>Regular security updates and monitoring</li>
    <li>Limited data collection (we only collect what's necessary)</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">9. Children's Privacy</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    Our website is not directed at children under 13 years of age. We do not knowingly collect personal information from children. If you believe we have inadvertently collected information from a child, please contact us immediately.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">10. International Data Transfers</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    Our website is hosted in the UK/EU. If you access our site from outside the UK or EU, your data may be transferred to and processed in the UK in accordance with UK GDPR standards.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">11. Changes to This Privacy Policy</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    We may update this Privacy Policy from time to time to reflect changes in our practices or legal requirements. The "Last Updated" date at the top will indicate when changes were made. Continued use of our website after changes constitutes acceptance of the updated policy.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">12. Contact Us</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    If you have questions about this Privacy Policy or wish to exercise your data protection rights, please contact us:
  </p>
  <div style="background: var(--card); padding: 20px; border-radius: 12px; margin: 20px 0;">
    <p style="line-height: 1.8;">
      <strong>Email:</strong> infofybobuybo@gmail.com<br>
      <strong>Website:</strong> www.fybobuybo.com<br>
      <strong>Response Time:</strong> We aim to respond within 30 days
    </p>
  </div>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">13. Complaints</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    If you believe we have not handled your data properly, you have the right to lodge a complaint with the UK's data protection authority:
  </p>
  <div style="background: var(--card); padding: 20px; border-radius: 12px; margin: 20px 0;">
    <p style="line-height: 1.8;">
      <strong>Information Commissioner's Office (ICO)</strong><br>
      Website: <a href="https://ico.org.uk/make-a-complaint/" target="_blank" rel="noopener">ico.org.uk/make-a-complaint</a><br>
      Telephone: 0303 123 1113<br>
      Address: Information Commissioner's Office, Wycliffe House, Water Lane, Wilmslow, Cheshire, SK9 5AF
    </p>
  </div>

  <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); padding: 30px; border-radius: 16px; margin-top: 50px;">
    <h3 style="color: var(--accent); margin-bottom: 15px;">Summary</h3>
    <p style="line-height: 1.8;">
      We collect minimal data (just browsing behaviour and preferences), use it to improve our site, share affiliate tracking data with Amazon, and respect your privacy rights under UK law. You can control cookies through your browser and contact us anytime with questions.
    </p>
  </div>
</article>
"""

# Terms of Service HTML content  
TERMS_OF_SERVICE_HTML = """
<article style="max-width: 900px; margin: 40px auto; padding: 20px;">
  <div style="background: var(--card); padding: 30px; border-radius: 16px; margin-bottom: 30px;">
    <p style="font-size: 1.1rem; line-height: 1.8; margin-bottom: 20px;">
      <strong>Last Updated:</strong> January 23, 2026
    </p>
    <p style="font-size: 1.05rem; line-height: 1.8;">
      Welcome to FyboBuybo. By accessing and using www.fybobuybo.com, you accept and agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our website.
    </p>
  </div>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">1. About FyboBuybo</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    FyboBuybo is a UK-based product discovery and affiliate marketing website. We curate and recommend products available on Amazon.co.uk and other retailers, earning a commission when you make purchases through our affiliate links.
  </p>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    <strong>Important:</strong> We are not a retailer. We do not sell products directly, handle transactions, or ship items. All purchases are made through third-party retailers (primarily Amazon UK).
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">2. Use of Our Website</h2>
  
  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">2.1 Permitted Use</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    You may use FyboBuybo for:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>Browsing and discovering gift ideas and product recommendations</li>
    <li>Reading our blog content and seasonal guides</li>
    <li>Clicking through to retailer websites to make purchases</li>
    <li>Sharing our content on social media (with attribution)</li>
  </ul>

  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">2.2 Prohibited Use</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    You must not:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>Use our website for any unlawful purpose</li>
    <li>Attempt to gain unauthorised access to our systems or data</li>
    <li>Copy, reproduce, or redistribute our content without permission (except for personal, non-commercial use)</li>
    <li>Use automated systems (bots, scrapers) to access our website</li>
    <li>Interfere with the proper functioning of our website</li>
    <li>Remove or obscure our affiliate disclosures or links</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">3. Affiliate Disclosure</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    FyboBuybo participates in the Amazon EU Associates Programme and other affiliate programmes. This means:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>We earn a commission when you purchase products through our affiliate links</li>
    <li>This commission does not increase your purchase price</li>
    <li>Our recommendations are based on product quality and suitability for UK shoppers</li>
    <li>We may receive products for review, but this does not influence our honest assessments</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">4. Product Information and Accuracy</h2>
  
  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">4.1 Information Accuracy</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    We make reasonable efforts to ensure product information (descriptions, prices, availability) is accurate at the time of publication. However:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li><strong>Prices change:</strong> Retailers frequently update pricing. Always check current prices on the retailer's website</li>
    <li><strong>Stock varies:</strong> Product availability changes constantly</li>
    <li><strong>Specifications may differ:</strong> Manufacturers may update products without notice</li>
    <li><strong>AI-generated content:</strong> Product descriptions may be partially generated using AI technology</li>
  </ul>

  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">4.2 No Guarantees</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    We provide product recommendations in good faith, but we do not guarantee:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>Product performance, quality, or suitability for your specific needs</li>
    <li>Availability or delivery times</li>
    <li>That prices shown match current retailer prices</li>
    <li>That products meet your expectations</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">5. Third-Party Retailers and Transactions</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    When you purchase through our affiliate links:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>You are entering into a contract with the retailer (e.g., Amazon), not with FyboBuybo</li>
    <li>The retailer's terms and conditions apply to your purchase</li>
    <li>Returns, refunds, and customer service are handled by the retailer</li>
    <li>We are not responsible for order fulfilment, shipping, or product quality</li>
    <li>Any disputes must be resolved with the retailer directly</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">6. Intellectual Property</h2>
  
  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">6.1 Our Content</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    All content on FyboBuybo (text, images, design, code, logos) is owned by or licensed to us and is protected by UK and international copyright laws.
  </p>

  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">6.2 Product Images</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    Product images are sourced from Amazon and other retailers for the purpose of product identification and affiliate linking. These images remain the property of their respective owners.
  </p>

  <h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-accent);">6.3 Permitted Use</h3>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    You may view and share our content for personal, non-commercial use. For commercial use, republication, or large-scale copying, please contact us for permission.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">7. Limitation of Liability</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    To the fullest extent permitted by UK law:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>FyboBuybo is provided "as is" without warranties of any kind</li>
    <li>We are not liable for any direct, indirect, or consequential damages arising from your use of our website</li>
    <li>We are not liable for product quality, delivery issues, or retailer problems</li>
    <li>We are not liable for losses resulting from inaccurate product information</li>
    <li>Our total liability shall not exceed £100 for any claim</li>
  </ul>
  <p style="line-height: 1.8; margin-bottom: 20px; font-style: italic; color: var(--text-muted);">
    Nothing in these terms excludes or limits our liability for death or personal injury caused by negligence, fraud, or any liability that cannot be excluded by UK law.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">8. Links to Third-Party Websites</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    Our website contains links to third-party websites (primarily Amazon). We are not responsible for:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>The content, privacy practices, or terms of third-party websites</li>
    <li>Any damages or losses from your use of third-party websites</li>
    <li>The availability or accuracy of external websites</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">9. User-Generated Content</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    If we add features allowing user comments or reviews in the future, you agree that:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>You grant us a non-exclusive licence to use, display, and distribute your content</li>
    <li>Your content must be lawful, truthful, and not infringe others' rights</li>
    <li>We may remove any content at our discretion</li>
    <li>You are responsible for any content you post</li>
  </ul>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">10. Changes to Our Website and Terms</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    We reserve the right to:
  </p>
  <ul style="margin-left: 30px; line-height: 2; margin-bottom: 20px;">
    <li>Modify or discontinue our website or any features at any time</li>
    <li>Update these Terms of Service (changes take effect when posted)</li>
    <li>Change our product selection, affiliate partners, or business model</li>
  </ul>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    Continued use of our website after changes constitutes acceptance of updated terms.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">11. Governing Law and Jurisdiction</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    These Terms of Service are governed by the laws of England and Wales. Any disputes will be subject to the exclusive jurisdiction of the courts of England and Wales.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">12. Severability</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    If any provision of these terms is found to be unenforceable or invalid, that provision will be limited or eliminated to the minimum extent necessary so that these Terms of Service will otherwise remain in full force and effect.
  </p>

  <h2 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent);">13. Contact Information</h2>
  <p style="line-height: 1.8; margin-bottom: 20px;">
    For questions about these Terms of Service, please contact us:
  </p>
  <div style="background: var(--card); padding: 20px; border-radius: 12px; margin: 20px 0;">
    <p style="line-height: 1.8;">
      <strong>Email:</strong> infofybobuybo@gmail.com<br>
      <strong>Website:</strong> www.fybobuybo.com
    </p>
  </div>

  <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); padding: 30px; border-radius: 16px; margin-top: 50px;">
    <h3 style="color: var(--accent); margin-bottom: 15px;">Key Takeaways</h3>
    <ul style="margin-left: 20px; line-height: 2;">
      <li>We're an affiliate site, not a retailer—purchases happen on Amazon</li>
      <li>Prices and availability may change—always verify on the retailer's site</li>
      <li>We earn commissions but it doesn't affect your price</li>
      <li>Use our site respectfully and lawfully</li>
      <li>Contact the retailer for purchase issues, contact us for website questions</li>
    </ul>
  </div>
</article>
"""

# Cookie Consent Banner
COOKIE_CONSENT_HTML = """
<!-- Cookie Consent Banner -->
<div id="cookie-consent" style="display: none; position: fixed; bottom: 0; left: 0; right: 0; background: var(--card); padding: 20px 30px; box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15); z-index: 10000; border-top: 3px solid var(--button);">
  <div style="max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 30px; flex-wrap: wrap;">
    <div style="flex: 1; min-width: 300px;">
      <h3 style="margin: 0 0 10px 0; font-size: 1.1rem; color: var(--accent);">🍪 We Value Your Privacy</h3>
      <p style="margin: 0; line-height: 1.6; font-size: 0.95rem; color: var(--text-accent);">
        We use essential cookies to remember your preferences (like theme choice) and affiliate cookies to track product clicks. 
        <a href="/privacy-policy" style="color: var(--button); font-weight: 600; text-decoration: underline;">Learn more in our Privacy Policy</a>
      </p>
    </div>
    <div style="display: flex; gap: 15px; flex-shrink: 0; flex-wrap: wrap;">
      <button id="cookie-accept" style="background: var(--button); color: white; padding: 12px 30px; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 0.95rem; white-space: nowrap;">
        Accept All
      </button>
      <button id="cookie-essential" style="background: transparent; color: var(--text-accent); padding: 12px 30px; border: 2px solid var(--dropdown-border); border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 0.95rem; white-space: nowrap;">
        Essential Only
      </button>
    </div>
  </div>
</div>

<style>
#cookie-consent button:hover {
  opacity: 0.9;
  transform: translateY(-2px);
  transition: all 0.2s ease;
}
#cookie-accept:hover {
  background: var(--button-hover);
}
#cookie-essential:hover {
  background: var(--tag);
}
@media (max-width: 768px) {
  #cookie-consent {
    padding: 20px;
  }
  #cookie-consent > div {
    flex-direction: column;
    align-items: stretch;
  }
  #cookie-consent button {
    width: 100%;
  }
}
</style>

<script>
(function() {
  const CONSENT_KEY = 'fybobuybo_cookie_consent';
  const CONSENT_VERSION = '1.0';
  
  function getCookieConsent() {
    try {
      const consent = localStorage.getItem(CONSENT_KEY);
      return consent ? JSON.parse(consent) : null;
    } catch (e) {
      return null;
    }
  }
  
  function setCookieConsent(level) {
    const consent = {
      level: level,
      version: CONSENT_VERSION,
      timestamp: new Date().toISOString()
    };
    localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
  }
  
  function showCookieBanner() {
    const banner = document.getElementById('cookie-consent');
    if (banner) {
      banner.style.display = 'block';
    }
  }
  
  function hideCookieBanner() {
    const banner = document.getElementById('cookie-consent');
    if (banner) {
      banner.style.display = 'none';
    }
  }
  
  const consent = getCookieConsent();
  
  if (!consent || consent.version !== CONSENT_VERSION) {
    showCookieBanner();
  }
  
  const acceptBtn = document.getElementById('cookie-accept');
  if (acceptBtn) {
    acceptBtn.addEventListener('click', function() {
      setCookieConsent('all');
      hideCookieBanner();
    });
  }
  
  const essentialBtn = document.getElementById('cookie-essential');
  if (essentialBtn) {
    essentialBtn.addEventListener('click', function() {
      setCookieConsent('essential');
      hideCookieBanner();
    });
  }
})();
</script>
"""

# ============================================================================
# THEMES
# ============================================================================
THEMES = [
    {
        "name": "Daylight Elegance",
        "bg": "#fdfbf7",
        "card": "#ffffff",
        "accent": "#1a1614",
        "button": "#0066ff",
        "button_hover": "#0052cc",
        "tag": "#e8f4ff",
        "text_accent": "#2c2c2c",
        "text_muted": "#666666",
        "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "card_gradient": "linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)",
        "shadow": "0 4px 12px rgba(0, 0, 0, 0.08)",
        "shadow_hover": "0 8px 24px rgba(0, 0, 0, 0.12)",
        "dropdown_bg": "#ffffff",
        "dropdown_border": "rgba(0, 0, 0, 0.12)",
        "nav_bg": "#ffffff",
        "nav_border": "rgba(0, 0, 0, 0.08)"
    },
    {
        "name": "Midnight Luxe",
        "bg": "#0a0e14",
        "card": "#151922",
        "accent": "#f5f5f0",
        "button": "#4d7fff",
        "button_hover": "#6d93ff",
        "tag": "#1e2838",
        "text_accent": "#e0e0e0",
        "text_muted": "#a0a0a0",
        "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "card_gradient": "linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)",
        "shadow": "0 4px 12px rgba(0, 0, 0, 0.4)",
        "shadow_hover": "0 8px 24px rgba(0, 0, 0, 0.6)",
        "dropdown_bg": "#1a1f2e",
        "dropdown_border": "rgba(255, 255, 255, 0.12)",
        "nav_bg": "#151922",
        "nav_border": "rgba(255, 255, 255, 0.08)"
    }
]

def get_daily_theme():
    return THEMES[datetime.date.today().timetuple().tm_yday % len(THEMES)]

# ============================================================================
# ELITE HELPER FUNCTIONS - NEW!
# ============================================================================

def get_product_price_rating(product):
    """Extract price and rating with manual override support"""
    price = product.get("manual_price") or None
    rating = product.get("manual_rating") or None
    reviews = product.get("manual_reviews") or None
    
    return {
        "price": price,
        "rating": rating,
        "reviews": reviews
    }

def format_price_display(price_data):
    """Format price for display - handles both manual and API prices"""
    if isinstance(price_data, str):
        return price_data  # Already formatted (e.g., "£16.95")
    if isinstance(price_data, dict):
        return f"£{price_data['amount']:.2f}"
    return str(price_data) if price_data else ""

def format_rating_display(rating, review_count=None):
    """Format rating with stars for display"""
    if not rating:
        return ""
    try:
        rating_float = float(rating)
        stars = "⭐" * int(rating_float)
        half_star = "½⭐" if (rating_float % 1) >= 0.5 else ""
        
        if review_count:
            if isinstance(review_count, str):
                formatted_count = review_count
            else:
                formatted_count = f"{review_count:,}"
            return f"{stars}{half_star} {rating_float}/5 ({formatted_count} reviews)"
        return f"{stars}{half_star} {rating_float}/5"
    except:
        return ""

def get_similar_products(product, all_products, limit=6):
    """Get similar products for SEO and user engagement"""
    similar = []
    
    # Same category
    category_matches = [
        p for p in all_products 
        if p.get("category") == product.get("category") 
        and p["name"] != product["name"]
    ]
    similar.extend(category_matches[:limit])
    
    if len(similar) < limit:
        # Add same season products
        product_seasons = set(s.strip() for s in product.get("season", "").split(",") if s.strip())
        season_matches = [
            p for p in all_products
            if p["name"] != product["name"]
            and p not in similar
            and any(s.strip() in product_seasons for s in p.get("season", "").split(","))
        ]
        similar.extend(season_matches[:(limit - len(similar))])
    
    return similar[:limit]

def generate_product_schema(product):
    """Generate JSON-LD schema for product pages"""
    price_info = get_product_price_rating(product)
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product["name"],
        "description": product.get("info", product.get("hook", "")),
        "image": product.get("image", ""),
        "brand": {
            "@type": "Brand",
            "name": "Various"
        }
    }
    
    if price_info.get("price"):
        price_str = format_price_display(price_info["price"])
        price_value = re.sub(r'[^\d.]', '', price_str)
        if price_value:
            schema["offers"] = {
                "@type": "Offer",
                "url": product.get("url", ""),
                "priceCurrency": "GBP",
                "price": price_value,
                "availability": "https://schema.org/InStock",
                "seller": {
                    "@type": "Organization",
                    "name": "Amazon UK"
                }
            }
    
    if price_info.get("rating"):
        try:
            rating_val = float(price_info["rating"])
            review_count = price_info.get("reviews", "1")
            if isinstance(review_count, str):
                review_count = re.sub(r'[^\d]', '', review_count) or "1"
            
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(rating_val),
                "bestRating": "5",
                "reviewCount": str(review_count)
            }
        except:
            pass
    
    return json.dumps(schema, ensure_ascii=False)

def generate_breadcrumb_schema(breadcrumbs):
    """Generate breadcrumb schema for navigation"""
    items = []
    for idx, (name, url) in enumerate(breadcrumbs, 1):
        items.append({
            "@type": "ListItem",
            "position": idx,
            "name": name,
            "item": SITE_URL + url
        })
    
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items
    }
    
    return json.dumps(schema, ensure_ascii=False)

# ============================================================================
# EXISTING HELPER FUNCTIONS
# ============================================================================

def ping_search_engines():
    sitemap_url = f"{SITE_URL}/sitemap.xml"
    engines = [
        f"https://www.google.com/ping?sitemap={sitemap_url}",
        f"https://www.bing.com/ping?sitemap={sitemap_url}"
    ]
    for url in engines:
        try:
            requests.get(url, timeout=5)
        except Exception:
            pass

def slugify(text):
    text = text.lower()
    text = re.sub(r'&', '-and-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    text = re.sub(r'-+', '-', text)  # Collapse multiple hyphens to single hyphen
    text = text.strip('-')  # Remove leading/trailing hyphens
    return text

def normalize_for_match(text):
    if not text:
        return ""
    return text.lower().replace("'", "").replace(" ", "").replace("-", "")

def get_nav_items():
    products = PRODUCTS
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)
            products = cache_data.get("products", PRODUCTS)
        except:
            pass

    categories = sorted({p["category"] for p in products if p.get("category")})

    seasons_set = set()
    for p in products:
        if p.get("season"):
            for s in p["season"].split(","):
                clean = s.strip()
                if clean:
                    seasons_set.add(clean)

    important_seasons_order = [
        "Valentine's Day", "Mother's Day", "Easter", "Father's Day",
        "Summer Gifts", "Back to School", "Halloween", "Christmas"
    ]
    important_seasons = [s for s in important_seasons_order if s in seasons_set]
    other_seasons = sorted(seasons_set - set(important_seasons))
    seasons = other_seasons + important_seasons

    return {
        "categories": categories,
        "seasons": seasons
    }

def paginate(items, page):
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return items[start:end], len(items)

def shorten_product_name(name, max_length=80):
    if len(name) <= max_length:
        return name
    for sep in [',', '(']:
        if sep in name:
            short = name.split(sep, 1)[0].strip()
            if len(short) <= max_length:
                return short
    words, out = name.split(), ""
    for w in words:
        if len(out + " " + w) <= max_length - 3:
            out += (" " if out else "") + w
        else:
            break
    return out + "..."


# ============================================================================
# FIXED ELITE HOOK GENERATION - RELAXED QUALITY CHECKS
# Replace your current generate_hook section with this
# ============================================================================

def select_hook_type(product):
    """Intelligently select hook type based on product attributes"""
    
    category = product.get("category", "").lower()
    price_tier = product.get("price_tier", "").lower()
    rating = product.get("manual_rating")
    reviews = product.get("manual_reviews")
    price = product.get("manual_price", "")
    
    # Extract numeric price if available
    price_value = 0
    if price:
        price_str = str(price)
        price_nums = re.findall(r'\d+\.?\d*', price_str)
        if price_nums:
            price_value = float(price_nums[0])
    
    # Social proof for highly-rated products with many reviews
    if rating:
        try:
            rating_float = float(rating)
            if rating_float >= 4.5 and reviews:
                review_count_str = re.sub(r'[^\d]', '', str(reviews))
                if review_count_str and int(review_count_str) > 3000:
                    return "social_proof"
        except:
            pass
    
    # Value proposition for premium products
    if price_tier in ["premium", "luxury"] or price_value > 100:
        return "value_proposition"
    
    # Lifestyle for gifts, beauty, comfort
    lifestyle_keywords = ["beauty", "gift", "toy", "comfort", "decor", "fashion", "personal", "wellness"]
    if any(kw in category for kw in lifestyle_keywords):
        return "lifestyle"
    
    # Problem-solution for practical home items
    practical_keywords = ["home", "kitchen", "storage", "cleaning", "appliance", "organization"]
    if any(kw in category for kw in practical_keywords):
        return "problem_solution"
    
    # Comparison for tech, upgrades, replacements
    tech_keywords = ["electronic", "tech", "gadget", "device", "smart", "digital"]
    if any(kw in category for kw in tech_keywords):
        return "comparison"
    
    # Specific use case for seasonal/specialized
    if product.get("season"):
        return "specific_use_case"
    
    # Default fallback - rotate between top 3
    return random.choice(["problem_solution", "lifestyle", "comparison"])


def build_problem_solution_prompt(name, category, pain_points, keywords):
    """Build prompt for problem-solution hook"""
    pain_point = pain_points[0] if pain_points else "everyday challenges"
    keyword_text = ', '.join(keywords[:3]) if keywords else "practical benefits"
    
    return f"""You are a UK e-commerce copywriter specializing in problem-solution messaging.

TASK: Write a compelling 2-sentence product hook that:
1. First sentence: Identifies a relatable UK household frustration or pain point
2. Second sentence: Presents this product as the elegant solution

PRODUCT: {name}
CATEGORY: {category}
KEY PAIN POINT: {pain_point}
TARGET PHRASES (weave naturally): {keyword_text}

RULES:
- Start with "Tired of..." OR "Struggling with..." OR "Fed up with..." OR "Banish..." OR "Say goodbye to..."
- Use <b></b> tags on ONE key product feature (not generic words like "quality" or "great")
- Include specific numbers/specs when possible (e.g., "12L capacity", "75% less energy")
- Reference UK context naturally (British weather, home types, energy costs)
- Professional yet warm tone—like a knowledgeable friend's recommendation
- Keep it concise but substantial

OUTPUT: Exactly 2 sentences. No preamble, no explanation."""


def build_social_proof_prompt(name, category, rating, reviews, keywords):
    """Build prompt for social proof hook"""
    keyword_text = ', '.join(keywords[:3]) if keywords else "key benefits"
    review_text = f"{rating}/5 from {reviews} reviews" if rating and reviews else "thousands of 5-star reviews"
    
    return f"""You are a UK e-commerce copywriter specializing in social proof messaging.

TASK: Write a compelling 2-sentence hook that leverages product popularity:
1. First sentence: Lead with impressive rating/review statistic from UK buyers
2. Second sentence: Explain the specific reason so many people love it

PRODUCT: {name}
RATING DATA: {review_text}
CATEGORY: {category}
MAIN BENEFITS: {keyword_text}

RULES:
- Start with review statistic: "Over [X] UK shoppers rate this..." OR "With [X] 5-star reviews..."
- Use <b></b> tags on the standout benefit that drives the ratings
- Include specific, measurable benefit (time saved, money saved, problem solved)
- Trust-building, factual tone with warmth
- Keep it concise

OUTPUT: Exactly 2 sentences. No preamble, no explanation."""


def build_value_prop_prompt(name, category, price_tier, keywords):
    """Build prompt for value proposition hook"""
    keyword_text = ', '.join(keywords[:3]) if keywords else "premium features"
    
    return f"""You are a UK e-commerce copywriter specializing in premium product positioning.

TASK: Frame this as a worthwhile investment with long-term value:
1. First sentence: Position as an investment with lasting benefit
2. Second sentence: Specific quality feature that justifies the price

PRODUCT: {name}
CATEGORY: {category}
QUALITY MARKERS: {keyword_text}

RULES:
- Start with investment framing: "A genuine investment in..." OR "Worth every penny for..."
- Use <b></b> tags on premium feature, material, or technology
- Sophisticated British tone—understated luxury
- Keep it concise

OUTPUT: Exactly 2 sentences. No preamble, no explanation."""


def build_lifestyle_prompt(name, category, pain_points, keywords):
    """Build prompt for lifestyle integration hook"""
    context = pain_points[0] if pain_points else "everyday moments"
    feeling = ', '.join(keywords[:2]) if keywords else "comfort and satisfaction"
    
    return f"""You are a UK e-commerce copywriter specializing in lifestyle messaging.

TASK: Paint a vivid picture of life with this product:
1. First sentence: Create an evocative scene of using the product
2. Second sentence: Emotional benefit it brings to daily life

PRODUCT: {name}
CATEGORY: {category}
LIFESTYLE CONTEXT: {context}
DESIRED FEELING: {feeling}

RULES:
- Start with scene-setting: "Picture this..." OR "Imagine..." OR describe a moment
- Use <b></b> tags on sensory detail or emotional benefit
- Include UK lifestyle references (Sunday mornings, rainy days, cozy evenings)
- Warm, inviting tone
- Keep it concise

OUTPUT: Exactly 2 sentences. No preamble, no explanation."""


def build_comparison_prompt(name, category, pain_points, keywords):
    """Build prompt for comparison/upgrade hook"""
    replaces = pain_points[0] if pain_points else "standard alternatives"
    advantage = ', '.join(keywords[:2]) if keywords else "key improvements"
    
    return f"""You are a UK e-commerce copywriter specializing in comparison messaging.

TASK: Position this as superior to common alternatives:
1. First sentence: "Unlike [alternative]..." + key disadvantage
2. Second sentence: How this product solves that problem better

PRODUCT: {name}
CATEGORY: {category}
REPLACES: {replaces}
KEY ADVANTAGE: {advantage}

RULES:
- Start with: "Unlike traditional..." OR "While most..."
- Use <b></b> tags on the differentiating feature
- Be specific about the improvement
- Educational, helpful tone
- Keep it concise

OUTPUT: Exactly 2 sentences. No preamble, no explanation."""


def build_use_case_prompt(name, category, pain_points, keywords, season=""):
    """Build prompt for specific use case hook"""
    scenario = pain_points[0] if pain_points else "specific needs"
    perfect_for = ', '.join(keywords[:2]) if keywords else "this purpose"
    season_context = f"SEASONAL CONTEXT: {season}" if season else "TIMING: Year-round use"
    
    return f"""You are a UK e-commerce copywriter specializing in use-case messaging.

TASK: Address a very specific scenario or need:
1. First sentence: Describe the exact situation this is perfect for
2. Second sentence: Why this product is ideal for that need

PRODUCT: {name}
CATEGORY: {category}
SPECIFIC SCENARIO: {scenario}
{season_context}
PERFECT FOR: {perfect_for}

RULES:
- Start with: "For [specific people/situation]..." OR "Perfect when..."
- Use <b></b> tags on the feature that makes it perfect
- Include UK-specific details
- Helpful, advisory tone
- Keep it concise

OUTPUT: Exactly 2 sentences. No preamble, no explanation."""


def passes_quality_check(hook, product):
    """Verify hook meets MINIMUM quality standards - RELAXED VERSION"""
    
    # Must exist and be reasonable length
    if not hook or len(hook) < 30:
        return False
    
    if len(hook) > 400:  # More lenient
        return False
    
    # Check for most egregious banned words only
    banned = ["must-have", "game-changer"]  # Reduced list
    hook_lower = hook.lower()
    if any(word in hook_lower for word in banned):
        return False
    
    # Should have at least 1 sentence
    if '.' not in hook and '!' not in hook and '?' not in hook:
        return False
    
    # That's it! Much simpler quality check
    return True


def generate_fallback_hook(product):
    """Generate a safe fallback hook if AI generation fails"""
    name = product["name"]
    category = product.get("category", "product")
    
    # Simple, safe fallback
    return f"Appreciated by UK shoppers for its <b>quality construction</b> and thoughtful design. This {category.lower()} delivers reliable performance in everyday British life."


# ============================================================================
# ULTRA-RELIABLE HOOK GENERATION - WORKS FOR ALL PRODUCTS
# Replace your generate_hook function with this version
# ============================================================================

def generate_hook(product):
    """
    Generate varied, conversion-focused hooks
    GUARANTEED to work for every product
    """
    
    # Check for manual override first
    if "hook_override" in product and product["hook_override"].strip():
        return product["hook_override"].strip()
    
    name = product["name"]
    category = product.get("category", "")
    keywords = product.get("keywords", [])
    pain_points = product.get("pain_points", [])
    price_tier = product.get("price_tier", "")
    
    # Use a simple rotation system instead of complex selection
    # This ensures variety without complex logic
    styles = [
        "benefit-first", 
        "lifestyle-story", 
        "quality-craft", 
        "problem-solution",
        "uk-context",
        "practical-value"
    ]
    
    style = random.choice(styles)
    
    # Build context strings
    pain_point_text = pain_points[0] if pain_points else "everyday practicality"
    keyword_text = ', '.join(keywords[:3]) if keywords else ""
    
    # SIMPLIFIED PROMPT - No strict requirements
    prompt = f"""You are a sophisticated British copywriter creating product descriptions for UK shoppers.

Write a compelling 1-2 sentence description for this product:

PRODUCT: {name}
CATEGORY: {category}
STYLE: {style}
KEY BENEFIT: {pain_point_text}
{f"KEYWORDS TO MENTION: {keyword_text}" if keyword_text else ""}

REQUIREMENTS:
- Write 1-2 natural, conversational sentences
- Mention one standout feature using <b>tags</b> around it
- Sound warm, helpful, and British
- Focus on practical benefits
- NO hype words like "must-have", "game-changer", "essential"

Write the description now (just the sentences, nothing else):"""

    try:
        # Single attempt with generous parameters
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100,
            top_p=0.9
        )
        
        hook = response.choices[0].message.content.strip()
        
        # Clean up formatting
        hook = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', hook)
        hook = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', hook)
        
        # Add <b> tags if none exist (pick a word from the name)
        if '<b>' not in hook:
            # Find a good word to bold from the product name
            words = name.split()
            for word in words:
                if len(word) > 4 and word[0].isupper():
                    hook = hook.replace(word, f'<b>{word}</b>', 1)
                    break
        
        # Ensure ends with punctuation
        if hook and not re.search(r'[.!?]$', hook):
            hook += "."
        
        # Basic sanity check - if hook exists and is reasonable, use it
        if hook and len(hook) > 20 and len(hook) < 500:
            print(f"✓ Generated hook for: {name[:50]}...")
            return hook
        else:
            # Generate smart fallback based on category
            return generate_smart_fallback(product)
            
    except Exception as e:
        print(f"⚠ API error for '{name[:50]}...': {e}")
        return generate_smart_fallback(product)


def generate_smart_fallback(product):
    """
    Generate category-specific fallback hooks that are still unique
    """
    name = product["name"]
    category = product.get("category", "Product")
    
    # Extract key feature from name
    name_lower = name.lower()
    
    # Category-specific templates
    if "beauty" in category.lower():
        if "set" in name_lower:
            return f"A thoughtfully curated beauty set that brings <b>professional-quality skincare</b> into your daily routine. Loved by UK shoppers for reliable results."
        else:
            return f"Elevates your skincare routine with <b>salon-quality formulation</b> in a product designed for everyday British life."
    
    elif "toy" in category.lower() or "game" in category.lower():
        if "lego" in name_lower or "building" in name_lower:
            return f"Sparks creativity and keeps young minds engaged for hours with <b>quality construction</b> that lasts. A favourite among UK families."
        else:
            return f"Brings joy and entertainment to playtime with <b>durable design</b> that stands up to enthusiastic use."
    
    elif "home" in category.lower() or "kitchen" in category.lower():
        if "candle" in name_lower:
            return f"Creates instant ambiance with <b>long-lasting fragrance</b> that transforms any room. A small luxury for everyday British homes."
        elif "storage" in name_lower or "organiz" in name_lower:
            return f"Tackles clutter and maximizes space with <b>clever design</b> that fits seamlessly into UK homes."
        else:
            return f"Simplifies daily routines with <b>practical functionality</b> that UK households genuinely appreciate."
    
    elif "electronic" in category.lower() or "tech" in category.lower():
        return f"Combines smart functionality with <b>intuitive operation</b> for hassle-free use in modern UK homes."
    
    elif "fashion" in category.lower() or "clothing" in category.lower():
        if "pyjama" in name_lower or "sleepwear" in name_lower:
            return f"Wraps you in <b>luxuriously soft comfort</b> perfect for cozy evenings and restful nights."
        else:
            return f"Delivers <b>quality craftsmanship</b> and versatile style that works effortlessly in any British wardrobe."
    
    elif "book" in category.lower():
        return f"Captures precious memories in a <b>beautifully crafted format</b> that's made to last for years of enjoyment."
    
    # Generic but still decent fallback
    else:
        features = []
        if "quality" not in name_lower:
            features.append("quality construction")
        if "design" not in name_lower:
            features.append("thoughtful design")
        if "durable" not in name_lower:
            features.append("lasting durability")
        
        feature = random.choice(features) if features else "reliable performance"
        
        return f"Appreciated by UK shoppers for its <b>{feature}</b> and practical value. This {category.lower()} delivers dependable results in everyday British life."





# ============================================================================
# CACHE AND PRODUCT MANAGEMENT
# ============================================================================

def should_refresh_cache():
    if not os.path.exists(CACHE_FILE):
        return True
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        cache_date = datetime.datetime.fromisoformat(cache.get("date", "2000-01-01T00:00:00"))
        days_old = (datetime.datetime.now() - cache_date).days
        if days_old >= CACHE_REFRESH_DAYS:
            return True
        if cache.get("prompt_version") != PROMPT_VERSION:
            return True
        return False
    except Exception:
        return True

def load_or_generate_hooks(products):
    enriched = []
    for p in products:
        p_copy = dict(p)
        p_copy["hook"] = generate_hook(p)
        p_copy.setdefault("date_added", str(datetime.date.today()))
        p_copy["hook_version"] = PROMPT_VERSION
        enriched.append(p_copy)

    today_iso = datetime.datetime.now().isoformat()
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "date": today_iso,
            "prompt_version": PROMPT_VERSION,
            "products": enriched
        }, f, indent=2, ensure_ascii=False)

    history = load_history()
    history_key = datetime.date.today().isoformat()
    history[history_key] = enriched
    save_history(history)

    Thread(target=ping_search_engines, daemon=True).start()
    cache.clear()
    return enriched

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def refresh_products(background=False):
    today = str(datetime.date.today())
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)
            cache_date_str = cache_data.get("date", "")
            if cache_date_str.startswith(today):
                return cache_data.get("products", [])
            cache_date = datetime.datetime.fromisoformat(cache_date_str)
            if (datetime.datetime.now() - cache_date).days < CACHE_REFRESH_DAYS and \
               cache_data.get("prompt_version") == PROMPT_VERSION:
                return cache_data.get("products", [])
        except Exception as e:
            print(f"Cache read failed: {e} — regenerating")
    
    enriched = load_or_generate_hooks(PRODUCTS)
    return enriched

# ============================================================================
# ENHANCED CSS WITH ELITE STYLES
# ============================================================================

CSS_TEMPLATE = """<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@400;600;700&display=swap');

:root {
    --bg: {{bg}};
    --card: {{card}};
    --accent: {{accent}};
    --button: {{button}};
    --button-hover: {{button_hover}};
    --tag: {{tag}};
    --text-accent: {{text_accent}};
    --text-muted: {{text_muted}};
    --gradient: {{gradient}};
    --card-gradient: {{card_gradient}};
    --shadow: {{shadow}};
    --shadow-hover: {{shadow_hover}};
    --dropdown-bg: {{dropdown_bg}};
    --dropdown-border: {{dropdown_border}};
    --nav-bg: {{nav_bg}};
    --nav-border: {{nav_border}};
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body { 
    background: var(--bg); 
    color: var(--accent); 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    padding: 20px;
    transition: background 0.3s ease, color 0.3s ease;
    overflow-x: hidden;
}

h1 { 
    text-align: center; 
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.5rem, 8vw, 5rem);
    font-weight: 900;
    margin: 60px 0 20px;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    line-height: 1.1;
    animation: fadeInUp 0.8s ease;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.subtitle { 
    text-align: center; 
    color: var(--text-accent); 
    font-size: clamp(1rem, 2vw, 1.2rem);
    max-width: 900px; 
    margin: 20px auto 40px;
    line-height: 1.6;
}

.grid { 
    display: grid; 
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
    gap: 32px; 
    max-width: 1600px; 
    margin: 60px auto;
    padding: 0 20px;
}

.card { 
    background: var(--card);
    border-radius: 20px; 
    padding: 28px; 
    text-align: center; 
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
    position: relative; 
    overflow: hidden;
}

.card::before { 
    content: "";
    position: absolute; 
    top: 0; left: 0; right: 0; bottom: 0; 
    background: var(--card-gradient);
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
    border-radius: 20px;
}

.card:hover { 
    transform: translateY(-8px); 
    box-shadow: var(--shadow-hover);
}

.card:hover::before { opacity: 1; }

.card img { 
    width: 100%; 
    max-height: 380px; 
    object-fit: contain; 
    border-radius: 16px; 
    margin: 20px 0; 
    display: block;
    transition: transform 0.4s ease;
}

.card:hover img { transform: scale(1.05); }

.card h2 {
    font-size: 1.3rem;
    font-weight: 700;
    margin: 16px 0;
    color: var(--accent);
    line-height: 1.3;
}

.card p {
    color: var(--text-accent);
    line-height: 1.7;
    margin: 16px 0;
}

.tag { 
    background: var(--tag); 
    color: var(--button);
    padding: 8px 18px; 
    border-radius: 24px; 
    font-size: 0.85rem;
    font-weight: 600;
    display: inline-block; 
    margin-bottom: 12px;
}

/* ELITE PRODUCT METRICS - NEW! */
.product-metrics {
    background: linear-gradient(to bottom, transparent, var(--tag));
    border-radius: 12px;
    padding: 16px;
    margin: 20px 0;
}

.price-display {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-bottom: 12px;
}

.price-label {
    font-size: 0.9rem;
    color: var(--text-muted);
    font-weight: 500;
}

.price-value {
    font-size: 1.4rem;
    font-weight: 800;
    color: #006600;
    letter-spacing: -0.02em;
}

.rating-display {
    text-align: center;
    color: var(--text-accent);
    font-size: 0.95rem;
}

.check-amazon-notice {
    text-align: center;
    padding: 12px;
    font-size: 0.95rem;
    font-style: italic;
}

/* ELITE AMAZON CTA - NEW! */
button { 
    background: linear-gradient(135deg, #ff9900 0%, #ff8c00 100%);
    border: none; 
    padding: 14px 32px; 
    border-radius: 50px; 
    font-size: 1rem; 
    font-weight: 700;
    color: white; 
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(255, 153, 0, 0.3);
}

button:hover { 
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(255, 153, 0, 0.4);
}
a.button {
    display: inline-block;
    background: linear-gradient(135deg, #ff9900 0%, #ff8c00 100%);
    padding: 14px 32px;
    border-radius: 50px;
    font-size: 1rem;
    font-weight: 700;
    color: white;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(255, 153, 0, 0.3);
}

a.button:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(255, 153, 0, 0.4);
    color: white;
}


nav { 
    background: var(--nav-bg);
    padding: 20px; 
    margin: 20px 0 60px; 
    border-radius: 16px; 
    box-shadow: var(--shadow);
    border: 1px solid var(--nav-border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
}

.nav-links {
    display: flex;
    gap: 32px;
    align-items: center;
}

.nav-links a {
    color: var(--text-accent);
    font-weight: 600;
    font-size: 1.05rem;
    padding: 8px 16px;
    border-radius: 8px;
    transition: all 0.2s ease;
}

.nav-links a:hover {
    background: var(--tag);
    color: var(--button);
}

.dropdown {
    position: relative;
}

.dropdown-toggle {
    background: var(--card);
    color: var(--accent);
    border: 1px solid var(--dropdown-border);
    padding: 10px 20px;
    border-radius: 24px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
}

.dropdown-toggle:hover {
    background: var(--tag);
    border-color: var(--button);
}

.dropdown-toggle::after {
    content: '▼';
    font-size: 0.7rem;
    transition: transform 0.2s ease;
}

.dropdown.active .dropdown-toggle::after {
    transform: rotate(180deg);
}

.dropdown-menu {
    display: none;
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    background: var(--dropdown-bg);
    border: 1px solid var(--dropdown-border);
    border-radius: 12px;
    padding: 8px 0;
    min-width: 220px;
    max-height: 400px;
    overflow-y: auto;
    box-shadow: var(--shadow-hover);
    z-index: 1000;
}

.dropdown.active .dropdown-menu {
    display: block;
}

.dropdown-menu a {
    display: block;
    padding: 12px 20px;
    color: var(--text-accent);
    font-size: 0.95rem;
    font-weight: 500;
    transition: all 0.2s ease;
    white-space: nowrap;
}

.dropdown-menu a:hover {
    background: var(--tag);
    color: var(--button);
    padding-left: 24px;
}

#search-form {
    flex: 1;
    max-width: 400px;
}

#search-input {
    width: 100%;
    padding: 12px 20px;
    border-radius: 24px;
    border: 1px solid var(--dropdown-border);
    background: var(--card);
    color: var(--accent);
    font-size: 0.95rem;
    transition: all 0.2s ease;
}

#search-input:focus {
    outline: none;
    border-color: var(--button);
    box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.1);
}

#search-input::placeholder {
    color: var(--text-muted);
}

/* SEARCH RESULTS MODAL */
#search-results {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    z-index: 9999;
    overflow-y: auto;
    padding: 40px 20px;
}

#search-results.active {
    display: block;
}

.search-modal {
    max-width: 1200px;
    margin: 0 auto;
    background: var(--bg);
    border-radius: 20px;
    padding: 40px;
    position: relative;
}

.search-close {
    position: absolute;
    top: 20px;
    right: 20px;
    background: var(--card);
    border: none;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1.5rem;
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
}

.search-close:hover {
    background: var(--tag);
}

.search-results-title {
    font-size: 2rem;
    margin-bottom: 30px;
    color: var(--accent);
}

.search-results-count {
    color: var(--text-muted);
    margin-bottom: 20px;
    font-size: 1.1rem;
}

#theme-toggle {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 999;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    border: 1px solid var(--dropdown-border);
    cursor: pointer;
    background: var(--card);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
}

#theme-toggle:hover {
    transform: scale(1.1);
    box-shadow: var(--shadow-hover);
}

#theme-toggle svg {
    width: 20px;
    height: 20px;
    fill: var(--accent);
}

footer {
    text-align: center;
    color: var(--text-muted);
    margin: 100px 0 60px;
    font-size: 0.95rem;
    line-height: 1.8;
}

footer p { margin: 12px 0; }

a {
    color: var(--text-accent);
    text-decoration: none;
    transition: color 0.2s ease;
}

a:hover { color: var(--button); }

.pagination {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 60px 0;
}

.pagination a {
    background: var(--button);
    padding: 12px 24px;
    border-radius: 50px;
    color: white;
    font-weight: 700;
    transition: all 0.3s ease;
}

.pagination a:hover {
    transform: translateY(-2px);
    background: var(--button-hover);
}

article {
    color: var(--text-accent);
}

article h2 {
    color: var(--accent);
    margin-top: 40px;
    margin-bottom: 16px;
}

article p {
    color: var(--text-accent);
    line-height: 1.8;
}

article a {
    color: var(--button);
    font-weight: 600;
}

.grid .card.hidden {
    display: none;
}

/* SIMILAR PRODUCTS SECTION - NEW! */
.similar-products-section {
    max-width: 1400px;
    margin: 80px auto;
    padding: 40px 20px;
}

.similar-products-heading {
    text-align: center;
    font-family: 'Playfair Display', serif;
    font-size: 2.5rem;
    font-weight: 900;
    margin-bottom: 12px;
    color: var(--accent);
}

.similar-products-subtitle {
    text-align: center;
    font-size: 1.1rem;
    color: var(--text-muted);
    margin-bottom: 40px;
}

.similar-products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 28px;
}

.similar-product-card {
    background: var(--card);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
}

.similar-product-card:hover {
    transform: translateY(-6px);
    box-shadow: var(--shadow-hover);
}

.similar-product-card img {
    width: 100%;
    max-height: 220px;
    object-fit: contain;
    border-radius: 12px;
    margin-bottom: 16px;
}

.similar-product-card h3 {
    font-size: 1.05rem;
    line-height: 1.4;
    margin-bottom: 12px;
    color: var(--accent);
    min-height: 2.8em;
}

.similar-price {
    font-size: 1.2rem;
    font-weight: 700;
    color: #006600;
}

/* INFO FOOTER - NEW! */
.product-info-footer {
    max-width: 900px;
    margin: 40px auto;
    padding: 24px;
    background: var(--tag);
    border-radius: 12px;
    font-size: 0.9rem;
    line-height: 1.7;
}

.product-info-footer p {
    margin: 8px 0;
    color: var(--text-muted);
}

@media (max-width: 768px) {
    nav {
        flex-direction: column;
        align-items: stretch;
    }
    
    .nav-links {
        flex-direction: column;
        gap: 12px;
        width: 100%;
    }
    
    .nav-links a {
        text-align: center;
    }
    
    .dropdown {
        width: 100%;
    }
    
    .dropdown-toggle {
        width: 100%;
        justify-content: center;
    }
    
    .dropdown-menu {
        left: 0;
        right: 0;
        min-width: auto;
    }
    
    #search-form {
        max-width: none;
    }
    
    .grid {
        grid-template-columns: 1fr;
        gap: 24px;
    }
    
    h1 {
        font-size: 2.5rem;
    }
}

::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: var(--bg);
}

::-webkit-scrollbar-thumb {
    background: var(--button);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--button-hover);
}
</style>"""

# ============================================================================
# BASE HTML TEMPLATE WITH ENHANCEMENTS
# ============================================================================

BASE_HTML = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="author" content="FyboBuybo">

<title>{{ title }}</title>
<meta name="description" content="{{ description | truncate(155, true, '...') }}">
<link rel="canonical" href="{{ canonical_url }}">
{% if prev_page_url %}<link rel="prev" href="{{ prev_page_url }}">{% endif %}
{% if next_page_url %}<link rel="next" href="{{ next_page_url }}">{% endif %}

<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description | truncate(200, true, '...') }}">
<meta property="og:type" content="{% if products|length == 1 %}product{% elif '/blog' in request.path %}article{% else %}website{% endif %}">
<meta property="og:url" content="{{ canonical_url }}">
<meta property="og:site_name" content="FyboBuybo">
<meta property="og:locale" content="en_GB">
<meta property="og:image" content="{% if products|length > 0 and products[0].image %}{{ products[0].image }}{% else %}{{ SITE_URL }}/static/og-default.jpg{% endif %}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ title }}">
<meta name="twitter:description" content="{{ description | truncate(200, true, '...') }}">
<meta name="twitter:image" content="{% if products|length > 0 and products[0].image %}{{ products[0].image }}{% else %}{{ SITE_URL }}/static/og-default.jpg{% endif %}">

{% if '/blog' in request.path and products|length == 0 %}
<meta property="article:published_time" content="{{ article_date }}">
<meta property="article:author" content="FyboBuybo">
{% endif %}

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://m.media-amazon.com">

{% if structured_data %}
<script type="application/ld+json">
{{ structured_data|safe }}
</script>
{% endif %}

{% if breadcrumb_schema %}
<script type="application/ld+json">
{{ breadcrumb_schema|safe }}
</script>
{% endif %}

{{ css|safe }}
</head>
<body>

<button id="theme-toggle" aria-label="Toggle theme">
  <svg id="theme-icon-sun" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="5"/>
    <line x1="12" y1="1" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="12" y1="21" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="1" y1="12" x2="3" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="21" y1="12" x2="23" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>
  <svg id="theme-icon-moon" viewBox="0 0 24 24" style="display:none;">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
</button>

<nav aria-label="Primary navigation">
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/blog">Blog</a>
  </div>

  <div class="dropdown categories-dropdown">
    <button class="dropdown-toggle" type="button">Categories</button>
    <div class="dropdown-menu">
      {% for cat in nav_items.categories %}
        <a href="/category/{{ slugify(cat) }}">{{ cat }}</a>
      {% endfor %}
    </div>
  </div>

  {% if nav_items.seasons %}
  <div class="dropdown seasons-dropdown">
    <button class="dropdown-toggle" type="button">Seasonal</button>
    <div class="dropdown-menu">
      {% for season in nav_items.seasons %}
        <a href="/season/{{ slugify(season) }}">{{ season }}</a>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <form id="search-form" role="search">
    <input type="search" id="search-input" placeholder="Search all gifts..." aria-label="Search">
  </form>
</nav>

<!-- Search Results Modal -->
<div id="search-results">
  <div class="search-modal">
    <button class="search-close" aria-label="Close search">&times;</button>
    <h2 class="search-results-title">Search Results</h2>
    <p class="search-results-count"></p>
    <div id="search-results-grid" class="grid"></div>
  </div>
</div>

<h1>{{ heading }}</h1>
<p class="subtitle">{{ subtitle }}</p>
<p style="text-align:center;color:var(--text-muted);margin-bottom:60px;font-weight:500;">
  ✔ UK-focused · ✔ Updated daily · ✔ Thoughtfully curated
</p>

{% if content %}
  {{ content|safe }}
{% endif %}

{% if products %}
<div class="grid">
{% for p in products %}
<div class="card" itemscope itemtype="https://schema.org/Product">
  <span class="tag">{{ p.category }}</span>

  <a href="/product/{{ slugify(p.name) }}" itemprop="url">
    <h2 itemprop="name">{{ shorten_product_name(p.name) }}</h2>
  </a>

  <a href="/product/{{ slugify(p.name) }}">
    <img src="{{ p.image }}" alt="{{ p.name }}" loading="lazy" itemprop="image">
  </a>

  <p itemprop="description">{{ p.hook|safe }}</p>

  {% if p.date_added %}
  <p style="font-size:.85rem;opacity:.65;margin:16px 0 8px;">
    ↳ Featured {{ p.date_added }}
  </p>
  {% endif %}

  <div class="product-metrics">
    {% set price_info = get_product_price_rating(p) %}

    {% if price_info.price %}
    <div class="price-display">
      <span class="price-label">Price:</span>
      <span class="price-value">{{ format_price_display(price_info.price) }}</span>
    </div>
    {% endif %}

    {% if price_info.rating %}
    <div class="rating-display">
      {{ format_rating_display(price_info.rating, price_info.reviews) }}
    </div>
    {% endif %}

    {% if not price_info.price and not price_info.rating %}
    <div class="check-amazon-notice">
      <span style="font-style:italic;opacity:.75;">
        View on Amazon for pricing
      </span>
    </div>
    {% endif %}
  </div>

  {% if p.url %}
  <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored noopener" class="button">
    Check current price
  </a>
  <p style="margin-top:12px;font-size:.9rem;opacity:.75;text-align:center;">
    <a href="{{ p.url }}" target="_blank" rel="nofollow sponsored noopener">
      View on Amazon UK
    </a>
  </p>
  {% endif %}

  {% if p.category %}
  <p style="font-size:.9rem;opacity:.7;margin-top:20px;text-align:center;">
    More <a href="/category/{{ slugify(p.category) }}">{{ p.category }}</a>
  </p>
  {% endif %}
</div>
{% endfor %}
</div>
{% endif %}

{% if similar_products %}
<section class="similar-products-section">
  <h2 class="similar-products-heading">Customers Also Viewed</h2>
  <p class="similar-products-subtitle">
    Popular alternatives in {{ products[0].category if products|length > 0 else 'this category' }}
  </p>

  <div class="similar-products-grid">
    {% for similar in similar_products %}
    <div class="similar-product-card">
      <a href="/product/{{ slugify(similar.name) }}">
        <img src="{{ similar.image }}" alt="{{ similar.name }}" loading="lazy">
        <h3>{{ shorten_product_name(similar.name, 60) }}</h3>
      </a>
      {% set similar_price = get_product_price_rating(similar) %}
      {% if similar_price.price %}
      <p class="similar-price">{{ format_price_display(similar_price.price) }}</p>
      {% endif %}
    </div>
    {% endfor %}
  </div>
</section>
{% endif %}

{% if products and (next_page_url or prev_page_url) %}
<div class="pagination">
  {% if prev_page_url %}<a href="{{ prev_page_url }}">← Previous</a>{% endif %}
  {% if next_page_url %}<a href="{{ next_page_url }}">Next →</a>{% endif %}
</div>
{% endif %}

<footer>
  <p><strong>As an Amazon Associate, I earn from qualifying purchases.</strong></p>
  <p>All product details were verified as of date featured. Prices and availability may change.</p>
  <p>FyboBuybo is an independent UK gifts site. Amazon and the Amazon logo are trademarks of Amazon.com, Inc.</p>
  
  <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid var(--dropdown-border);">
    <p style="margin: 10px 0;">
      <a href="/privacy-policy" style="margin: 0 15px;">Privacy Policy</a> · 
      <a href="/terms" style="margin: 0 15px;">Terms of Service</a> · 
      <a href="mailto:hello@fybobuybo.com" style="margin: 0 15px;">Contact</a>
    </p>
    <p style="font-size: 0.85rem; opacity: 0.7; margin-top: 15px;">
      © 2026 FyboBuybo. All rights reserved.
    </p>
  </div>
</footer>

<script>
const THEMES = {{ themes_json|default('[]')|safe }};
let currentTheme = parseInt(localStorage.getItem('themeIndex')) || 0;

function applyTheme(index) {
  if (!THEMES.length) return;
  const theme = THEMES[index % THEMES.length];
  const root = document.documentElement;

  Object.keys(theme).forEach(k => {
    if (k !== 'name') {
      root.style.setProperty(`--${k.replace(/_/g,'-')}`, theme[k]);
    }
  });

  document.getElementById('theme-icon-sun').style.display = index === 0 ? 'block' : 'none';
  document.getElementById('theme-icon-moon').style.display = index === 1 ? 'block' : 'none';
  localStorage.setItem('themeIndex', index);
}

applyTheme(currentTheme);

document.getElementById('theme-toggle')?.addEventListener('click', () => {
  currentTheme = (currentTheme + 1) % THEMES.length;
  applyTheme(currentTheme);
});

document.querySelectorAll('.dropdown').forEach(d => {
  d.querySelector('.dropdown-toggle')?.addEventListener('click', e => {
    e.stopPropagation();
    document.querySelectorAll('.dropdown').forEach(x => x !== d && x.classList.remove('active'));
    d.classList.toggle('active');
  });
});

document.addEventListener('click', () => {
  document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('active'));
});

// GLOBAL SEARCH FUNCTIONALITY
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const searchResultsGrid = document.getElementById('search-results-grid');
const searchResultsCount = document.querySelector('.search-results-count');
const searchClose = document.querySelector('.search-close');

let searchTimeout;
let allProducts = [];

// Fetch all products for search
async function loadAllProducts() {
  try {
    const response = await fetch('/api/search-products');
    const data = await response.json();
    allProducts = data.products || [];
  } catch (error) {
    console.error('Failed to load products:', error);
  }
}

// Initialize product data
loadAllProducts();

if (searchInput) {
  searchInput.addEventListener('input', e => {
    const query = e.target.value.trim();
    
    clearTimeout(searchTimeout);
    
    if (query.length < 2) {
      searchResults.classList.remove('active');
      return;
    }
    
    searchTimeout = setTimeout(() => {
      performSearch(query);
    }, 300);
  });
}

function performSearch(query) {
  const queryLower = query.toLowerCase();
  
  const matches = allProducts.filter(product => {
    const searchableText = [
      product.name,
      product.category,
      product.hook,
      product.info,
      ...(product.keywords || []),
      product.season
    ].join(' ').toLowerCase();
    
    return searchableText.includes(queryLower);
  });
  
  displaySearchResults(matches, query);
}

function displaySearchResults(products, query) {
  searchResultsCount.textContent = `Found ${products.length} result${products.length !== 1 ? 's' : ''} for "${query}"`;
  
  searchResultsGrid.innerHTML = '';
  
  if (products.length === 0) {
    searchResultsGrid.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:40px;">No products found. Try a different search term.</p>';
  } else {
    products.forEach(p => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <span class="tag">${p.category}</span>
        <a href="/product/${slugify(p.name)}">
          <h2>${shortenProductName(p.name)}</h2>
        </a>
        <a href="/product/${slugify(p.name)}">
          <img src="${p.image}" alt="${p.name}" loading="lazy">
        </a>
        <p>${p.hook || ''}</p>
        ${p.url ? `<a href="${p.url}" target="_blank" rel="nofollow sponsored noopener" class="button">View on Amazon</a>` : ''}
      `;
      searchResultsGrid.appendChild(card);
    });
  }
  
  searchResults.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function slugify(text) {
  return text.toLowerCase()
    .replace(/&/g, '-and-')
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function shortenProductName(name, maxLength = 80) {
  if (name.length <= maxLength) return name;
  
  const separators = [',', '('];
  for (const sep of separators) {
    if (name.includes(sep)) {
      const short = name.split(sep)[0].trim();
      if (short.length <= maxLength) return short;
    }
  }
  
  const words = name.split(' ');
  let result = '';
  for (const word of words) {
    if ((result + ' ' + word).length <= maxLength - 3) {
      result += (result ? ' ' : '') + word;
    } else {
      break;
    }
  }
  return result + '...';
}

if (searchClose) {
  searchClose.addEventListener('click', () => {
    searchResults.classList.remove('active');
    document.body.style.overflow = '';
    searchInput.value = '';
  });
}

// Close on background click
searchResults?.addEventListener('click', (e) => {
  if (e.target === searchResults) {
    searchResults.classList.remove('active');
    document.body.style.overflow = '';
    searchInput.value = '';
  }
});

// Close on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && searchResults.classList.contains('active')) {
    searchResults.classList.remove('active');
    document.body.style.overflow = '';
    searchInput.value = '';
  }
});
</script>

{{ cookie_consent|safe }}

</body>
</html>
"""

# ============================================================================
# RENDER PAGE FUNCTION - UPDATED WITH SEO ENHANCEMENTS
# ============================================================================

def render_page(title, description, heading, subtitle, products=None, page=1, page_url=None, similar_products=None, today=None, today_formatted=None, article_date=None, content=None):
    theme = get_daily_theme()
    css = render_template_string(CSS_TEMPLATE, **theme)
    
    nav_items = get_nav_items()
    
    canonical = SITE_URL + request.path
    page_num = int(request.args.get("page", 1))
    if page_num > 1:
        canonical += f"?page={page_num}"

    paged_products = []
    total_pages = 1
    if products:
        paged_products, total_items = paginate(products, page)
        total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    next_url = page_url(page + 1) if page_url and page < total_pages else None
    prev_url = page_url(page - 1) if page_url and page > 1 else None

    themes_json = json.dumps(THEMES)
    
    # Add today's date if not provided
    if not today:
        today = datetime.date.today().isoformat()
        today_formatted = datetime.date.today().strftime("%B %d, %Y")

    # Generate structured data for product pages
    structured_data = None
    if paged_products and len(paged_products) == 1:
        structured_data = generate_product_schema(paged_products[0])

    # Generate breadcrumb schema
    breadcrumb_schema = None
    breadcrumbs = [("Home", "/")]

    if '/category/' in request.path and paged_products:
        breadcrumbs.append((paged_products[0]['category'], request.path))
    elif '/season/' in request.path:
        season_name = request.path.split('/')[-1].replace('-', ' ').title()
        breadcrumbs.append((season_name, request.path))
    elif '/product/' in request.path and paged_products:
        if paged_products[0].get('category'):
            breadcrumbs.append((paged_products[0]['category'], f"/category/{slugify(paged_products[0]['category'])}"))
        breadcrumbs.append((paged_products[0]['name'], request.path))
    elif '/blog' in request.path:
        breadcrumbs.append(("Blog", "/blog"))
        if request.path != '/blog' and not '/page/' in request.path:
            breadcrumbs.append((title.split(' – ')[0], request.path))

    if len(breadcrumbs) > 1:
        breadcrumb_schema = generate_breadcrumb_schema(breadcrumbs)

    return render_template_string(
        BASE_HTML,
        title=title,
        description=description,
        heading=heading,
        subtitle=subtitle,
        products=paged_products,
        nav_items=nav_items,
        css=css,
        canonical_url=canonical,
        SITE_URL=SITE_URL,
        slugify=slugify,
        shorten_product_name=shorten_product_name,
        similar_products=similar_products or [],
        next_page_url=next_url,
        prev_page_url=prev_url,
        themes_json=themes_json,
        get_product_price_rating=get_product_price_rating,
        format_price_display=format_price_display,
        format_rating_display=format_rating_display,
        today=today,
        today_formatted=today_formatted,
        structured_data=structured_data,
        breadcrumb_schema=breadcrumb_schema,
        article_date=article_date,
        content=content or "",
        cookie_consent=COOKIE_CONSENT_HTML
    )



# ============================================================================
# ROUTES - CACHING REMOVED FROM SEO-CRITICAL PAGES
# ============================================================================

@app.route("/privacy-policy")
def privacy_policy():
    """Privacy policy page - required by UK GDPR"""
    return render_page(
        title="Privacy Policy – FyboBuybo",
        description="Our commitment to protecting your privacy and data in accordance with UK GDPR and Data Protection Act 2018.",
        heading="Privacy Policy",
        subtitle="How we collect, use, and protect your data",
        content=PRIVACY_POLICY_HTML
    )

@app.route("/terms")
def terms_of_service():
    """Terms of Service page - legal requirements for affiliate site"""
    return render_page(
        title="Terms of Service – FyboBuybo",
        description="Terms and conditions for using FyboBuybo, including affiliate disclosures and limitation of liability.",
        heading="Terms of Service",
        subtitle="Legal terms for using our website",
        content=TERMS_OF_SERVICE_HTML
    )
# API endpoint for search
@app.route("/api/search-products")
def api_search_products():
    all_products = refresh_products(background=True)
    # Return minimal data needed for search
    search_data = [{
        'name': p['name'],
        'category': p.get('category', ''),
        'image': p.get('image', ''),
        'hook': p.get('hook', ''),
        'info': p.get('info', ''),
        'keywords': p.get('keywords', []),
        'season': p.get('season', ''),
        'url': p.get('url', '')
    } for p in all_products]
    
    return jsonify({'products': search_data})

@app.route("/")
def home():
    products = refresh_products(background=True)[:ITEMS_PER_PAGE]
    return render_page(
        title="FyboBuybo – Trending UK Gifts & Popular Presents 2026",
        description="Discover today's trending UK gifts and popular presents across toys, beauty, electronics, home and more – refreshed daily with thoughtful picks for British shoppers.",
        heading="FyboBuybo – Trending UK Gifts",
        subtitle="A curated selection of popular gifts and presents, refreshed daily.",
        products=products
    )

@app.route("/category/<slug>")
@app.route("/category/<slug>/page/<int:page>")
def category(slug, page=1):
    all_products = refresh_products(background=True)
    filtered = [p for p in all_products if slugify(p.get("category", "")) == slug]
    if not filtered:
        abort(404)
    
    cat_name = filtered[0]["category"]
    
    def page_url(p_num):
        return url_for("category", slug=slug, page=p_num)
    
    return render_page(
        title=f"{cat_name} Gifts – FyboBuybo",
        description=f"Explore popular {cat_name.lower()} gifts loved by UK shoppers – updated daily with quality picks.",
        heading=cat_name,
        subtitle=f"Hand-picked {cat_name.lower()}, refreshed daily.",
        products=filtered,
        page=page,
        page_url=page_url
    )

@app.route("/season/<season_slug>")
@app.route("/season/<season_slug>/page/<int:page>")
def seasonal_collection(season_slug, page=1):
    all_products = refresh_products(background=True)
    season_name = season_slug.replace('-', ' ').title()
    norm_slug = normalize_for_match(season_slug)

    filtered = [
        p for p in all_products
        if p.get("season") and any(norm_slug in normalize_for_match(s.strip()) for s in p["season"].split(","))
    ]
    if not filtered:
        abort(404)
    
    filtered.sort(key=lambda p: p.get("date_added", "2000-01-01"), reverse=True)
    
    def page_url(p_num):
        return url_for("seasonal_collection", season_slug=season_slug, page=p_num)
    
    title_season = season_name
    if "day" in season_name.lower() or "christmas" in season_name.lower():
        title_season += " Gifts"

    return render_page(
        title=f"Best {title_season} 2026 – FyboBuybo",
        description=f"Discover the most popular {season_name.lower()} gifts for UK shoppers in 2026 – thoughtful, trending & updated daily.",
        heading=title_season,
        subtitle="Perfect seasonal presents • refreshed every day",
        products=filtered,
        page=page,
        page_url=page_url
    )

@app.route("/product/<path:product_slug>")
def product_detail(product_slug):
    all_products = refresh_products(background=True)
    found = next((p for p in all_products if slugify(p["name"]) == product_slug), None)
    if not found:
        abort(404)

    # Get similar products for SEO
    similar = get_similar_products(found, all_products, limit=6)
    
    # Add today's date for footer
    today = datetime.date.today()
    today_formatted = today.strftime("%B %d, %Y")

    return render_page(
        title=f"{shorten_product_name(found['name'])} – FyboBuybo",
        description=found.get("info", "A thoughtful gift choice popular among UK shoppers."),
        heading=shorten_product_name(found["name"]),
        subtitle="A popular UK gift choice",
        products=[found],
        similar_products=similar,
        today=today.isoformat(),
        today_formatted=today_formatted
    )

POSTS_PER_PAGE = 8

def load_blog_posts(page=1):
    posts = [
        {**v, "slug": k} for k, v in BLOG_POSTS.items()
    ]
    posts.sort(key=lambda x: x.get("date", "1900-01-01"), reverse=True)
    
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    paginated = posts[start:end]
    total_pages = (len(posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    
    return paginated, total_pages, len(posts)

@app.route("/blog")
@app.route("/blog/page/<int:page>")
def blog_list(page=1):
    paginated, total_pages, total_posts = load_blog_posts(page)
    if not paginated and page > 1:
        abort(404)

    theme = get_daily_theme()

    def page_url(p_num):
        return url_for("blog_list", page=p_num) if p_num <= total_pages else None

    rendered = render_page(
        title="FyboBuybo Blog – Gift Guides, Tips & Inspiration 2026",
        description="Latest UK gift ideas, seasonal guides, home tips and thoughtful present recommendations – updated regularly.",
        heading="FyboBuybo Blog",
        subtitle="Gift guides, trends and inspiration for UK shoppers",
        products=None,
        page=page,
        page_url=page_url
    )

    blog_html = '<div class="grid" style="max-width:1100px; margin:40px auto;">'
    accent_color = theme["accent"]
    for post in paginated:
        date_str = datetime.datetime.strptime(post["date"], "%Y-%m-%d").strftime("%d %B %Y")
        blog_html += f'''
        <div class="card" style="text-align:left; padding:24px;">
            <h2 style="font-size:1.6rem; margin-bottom:8px;"><a href="/blog/{post["slug"]}">{post["title"]}</a></h2>
            <p style="opacity:0.7; font-size:0.95rem; margin:0 0 12px;">{date_str}</p>
            <p style="line-height:1.6;">{post.get("description", "")}</p>
            <a href="/blog/{post["slug"]}" style="color:{accent_color}; font-weight:600;">Read more →</a>
        </div>
        '''
    blog_html += '</div>'

    insert_point = rendered.find('<p class="subtitle">') 
    if insert_point > -1:
        insert_after = rendered.find('</p>', insert_point) + 4
        rendered = rendered[:insert_after] + blog_html + rendered[insert_after:]

    if total_pages > 1:
        pag_html = '<div class="pagination">'
        if page > 1:
            pag_html += f'<a href="{url_for("blog_list", page=page-1)}">« Previous</a>'
        if page < total_pages:
            pag_html += f'<a href="{url_for("blog_list", page=page+1)}">Next »</a>'
        pag_html += '</div>'
        rendered = rendered.replace('</body>', pag_html + '</body>')

    return rendered

@app.route("/blog/<slug>")
def blog_detail(slug):
    post = BLOG_POSTS.get(slug)
    if not post:
        abort(404)

    all_products = refresh_products(background=True)
    
    # Get related products based on the post's related_products field
    related = []
    if post.get("related_products"):
        for product_slug in post["related_products"]:
            product = next((p for p in all_products if slugify(p["name"]) == product_slug), None)
            if product:
                related.append(product)
    
    # If no specific related products, fall back to category-based
    if not related:
        related = [p for p in all_products if p["category"] in ["Home & Kitchen", "Electronics"]][:6]

    # Render blog content with Jinja2 for any template variables
    from jinja2 import Template
    raw_content = post.get("content", "<p>Content coming soon.</p>")
    content_html = f'<div style="max-width:900px; margin:40px auto; line-height:1.7; font-size:1.05rem;">{Template(raw_content).render(slugify=slugify)}</div>'

    rendered = render_page(
        title=post["title"],
        description=post.get("meta_description", post.get("description", "Gift inspiration and practical tips from FyboBuybo.")),
        heading=post.get("heading", post["title"]),
        subtitle=post.get("subtitle", "Gift guide & inspiration"),
        products=None,
        similar_products=related,
        article_date=post.get("date", datetime.date.today().isoformat()),
        content=content_html
    )

    return rendered

@app.route("/robots.txt")
def robots():
    txt = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /data/
Crawl-delay: 1

Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(txt, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    history = load_history()
    today = str(datetime.date.today())
    urls = set()
    
    # Homepage - highest priority
    urls.add((SITE_URL + "/", today, "1.0", "daily"))
    
    # Blog listing
    urls.add((SITE_URL + "/blog", today, "0.9", "daily"))

    all_products = []
    for day_products in history.values():
        all_products.extend(day_products)

    # Categories - high priority
    categories_seen = set()
    for p in all_products:
        if p.get("category") and p["category"] not in categories_seen:
            categories_seen.add(p["category"])
            lastmod = p.get("date_added", today)
            urls.add((f"{SITE_URL}/category/{slugify(p['category'])}", lastmod, "0.8", "weekly"))
    
    # Products - medium priority
    products_seen = set()
    for p in all_products:
        if p.get("name") and p["name"] not in products_seen:
            products_seen.add(p["name"])
            lastmod = p.get("date_added", today)
            urls.add((f"{SITE_URL}/product/{slugify(p['name'])}", lastmod, "0.7", "weekly"))

    # Seasonal collections
    seasons = ["Valentine's Day", "Mother's Day", "Easter", "Father's Day",
               "Summer Gifts", "Back to School", "Halloween", "Christmas"]
    for season in seasons:
        urls.add((f"{SITE_URL}/season/{slugify(season)}", today, "0.8", "weekly"))

    # Blog posts
    for slug, post in BLOG_POSTS.items():
        urls.add((f"{SITE_URL}/blog/{slug}", post.get("date", today), "0.6", "monthly"))

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url_data in sorted(urls):
        url, lastmod, priority, changefreq = url_data
        sitemap_xml += f'''  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>
'''
    
    sitemap_xml += '</urlset>'
    return Response(sitemap_xml, mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
