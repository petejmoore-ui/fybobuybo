#!/usr/bin/env python3
"""
FyboBuybo app.py Patcher — Structured Data & Meta Tags Upgrade
================================================================
Put this file in the SAME FOLDER as your app.py, then run:

    python3 patch_app.py

That's it. It will:
1. Back up your current app.py to app.py.backup
2. Apply all changes
3. Tell you what it did

Changes applied:
- Honest Product schema (removes fake offers/shipping/ratings)
- FAQPage schema on product + blog pages
- WebSite schema with SearchAction on all pages
- Dynamic og:type (product/article/website)
- Grid card microdata removed (misleading for non-shop)
- Category/season/product meta titles improved
- Blog FAQ schema injection from related products
- New helper functions: generate_faq_schema, generate_website_schema, extract_brand_name
"""

import os, sys, shutil

def main():
    if not os.path.exists("app.py"):
        print("ERROR: app.py not found. Put this script in the same folder as app.py.")
        sys.exit(1)

    shutil.copy2("app.py", "app.py.backup")
    print("✓ Backed up app.py → app.py.backup\n")

    with open("app.py", "r", encoding="utf-8") as f:
        c = f.read()

    applied = 0

    # ══════════════════════════════════════════════════════════════
    # 1. Replace old generate_product_schema with honest version
    # ══════════════════════════════════════════════════════════════
    old_schema_start = 'def generate_product_schema(product):\n    from datetime import datetime, timedelta'
    new_schema = '''def generate_product_schema(product):
    """Generate Product JSON-LD with only factual, verifiable attributes.
    No offers (we don't sell), no ratings (not our reviews),
    no shipping (we don't ship). Just the product identity."""
    brand_name = extract_brand_name(product["name"])
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product["name"],
        "description": (product.get("info") or product.get("hook") or "")[:200],
        "image": product.get("image", ""),
        "brand": {"@type": "Brand", "name": brand_name},
        "sku": product.get("asin", ""),
        "url": SITE_URL + "/product/" + slugify(product["name"])
    }
    return json.dumps(schema, ensure_ascii=False)'''

    if old_schema_start in c:
        # Find the end of the old function (next def or next section comment)
        start = c.index(old_schema_start)
        # Find "def generate_breadcrumb_schema" which comes right after
        end_marker = 'def generate_breadcrumb_schema'
        end = c.index(end_marker, start)
        c = c[:start] + new_schema + "\n\n" + c[end:]
        applied += 1
        print("✓ [1] Replaced generate_product_schema (removed offers/ratings/shipping)")
    elif "No offers (we don't sell)" in c:
        print("⊘ [1] Already applied — honest product schema")
    else:
        print("✗ [1] Could not find generate_product_schema to replace")

    # ══════════════════════════════════════════════════════════════
    # 2. Add new helper functions after generate_breadcrumb_schema
    # ══════════════════════════════════════════════════════════════
    if "def generate_faq_schema" not in c:
        marker = "def ping_search_engines():"
        if marker in c:
            new_funcs = '''def generate_faq_schema(faqs):
    """Generate FAQPage JSON-LD from a list of Q&A dicts."""
    if not faqs:
        return None
    entries = []
    for faq in faqs:
        if faq.get("q") and faq.get("a"):
            entries.append({
                "@type": "Question",
                "name": faq["q"],
                "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}
            })
    if not entries:
        return None
    return json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entries}, ensure_ascii=False)

def generate_website_schema():
    """Generate WebSite JSON-LD with SearchAction for sitelinks searchbox."""
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "FyboBuybo",
        "url": SITE_URL + "/",
        "description": "Independent gift curation for UK shoppers — every pick is hand-chosen.",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": SITE_URL + "/?q={search_term_string}"},
            "query-input": "required name=search_term_string"
        }
    }, ensure_ascii=False)

def extract_brand_name(product_name):
    """Extract brand name from the first word(s) of a product name."""
    if not product_name:
        return "Various"
    generic_words = {"the", "a", "an", "best", "new", "premium", "luxury",
                     "classic", "original", "set", "pack", "pair", "box"}
    words = product_name.split()
    if not words:
        return "Various"
    first = words[0].strip("'\\"")
    if first.lower() in generic_words and len(words) > 1:
        return words[0] + " " + words[1]
    return first

'''
            c = c.replace(marker, new_funcs + marker)
            applied += 1
            print("✓ [2] Added generate_faq_schema, generate_website_schema, extract_brand_name")
        else:
            print("✗ [2] Could not find insertion point for new functions")
    else:
        print("⊘ [2] Already applied — helper functions exist")

    # ══════════════════════════════════════════════════════════════
    # 3. Update BASE_HTML: og:type, schema slots
    # ══════════════════════════════════════════════════════════════
    # 3a: Dynamic og:type
    old_og = '<meta property="og:type" content="website">'
    new_og = '<meta property="og:type" content="{{ og_type }}">'
    if old_og in c:
        c = c.replace(old_og, new_og, 1)
        applied += 1
        print("✓ [3a] Made og:type dynamic")
    elif new_og in c:
        print("⊘ [3a] Already applied — og:type is dynamic")

    # 3b: Add faq_schema and website_schema slots
    old_slots = '{% if breadcrumb_schema %}<script type="application/ld+json">{{ breadcrumb_schema|safe }}</script>{% endif %}\n\n{{ css|safe }}'
    new_slots = '{% if breadcrumb_schema %}<script type="application/ld+json">{{ breadcrumb_schema|safe }}</script>{% endif %}\n{% if faq_schema %}<script type="application/ld+json">{{ faq_schema|safe }}</script>{% endif %}\n{% if website_schema %}<script type="application/ld+json">{{ website_schema|safe }}</script>{% endif %}\n\n{{ css|safe }}'
    if 'faq_schema' not in c.split('{{ css|safe }}')[0]:
        if old_slots in c:
            c = c.replace(old_slots, new_slots, 1)
            applied += 1
            print("✓ [3b] Added faq_schema and website_schema slots in HEAD")
        else:
            print("✗ [3b] Could not find schema slots pattern")
    else:
        print("⊘ [3b] Already applied — schema slots exist")

    # ══════════════════════════════════════════════════════════════
    # 4. Remove Product microdata from grid cards
    # ══════════════════════════════════════════════════════════════
    replacements_4 = [
        (' itemscope itemtype="https://schema.org/Product"', ''),
        (' itemprop="image"', ''),
        (' itemprop="name"', ''),
        ('<p class="card-hook" itemprop="description">', '<p class="card-hook">'),
        (' itemprop="dateModified" content="{{ p.date_added }}"', ''),
    ]
    count_4 = 0
    for old, new in replacements_4:
        if old in c:
            c = c.replace(old, new, 1)
            count_4 += 1
    if count_4 > 0:
        applied += 1
        print(f"✓ [4] Removed {count_4} microdata attributes from grid cards")
    else:
        print("⊘ [4] Already applied — grid card microdata removed")

    # ══════════════════════════════════════════════════════════════
    # 5. Update render_page: add faq_schema, website_schema, og_type
    # ══════════════════════════════════════════════════════════════
    if 'faq_schema=faq_schema' not in c:
        # Add FAQ schema generation
        old_render_sd = '''    structured_data = None
    if paged_products and len(paged_products) == 1:
        structured_data = generate_product_schema(paged_products[0])

    breadcrumb_schema = None'''
        new_render_sd = '''    structured_data = None
    if paged_products and len(paged_products) == 1:
        structured_data = generate_product_schema(paged_products[0])

    # FAQ schema for product pages
    faq_schema = None
    if paged_products and len(paged_products) == 1:
        product_faqs = paged_products[0].get("faqs", [])
        if product_faqs:
            faq_schema = generate_faq_schema(product_faqs)

    # WebSite schema (every page)
    website_schema = generate_website_schema()

    # Dynamic og:type
    og_type = "website"
    if '/product/' in request.path:
        og_type = "product"
    elif '/blog/' in request.path and request.path != '/blog' and '/page/' not in request.path:
        og_type = "article"

    breadcrumb_schema = None'''
        if old_render_sd in c:
            c = c.replace(old_render_sd, new_render_sd, 1)
            applied += 1
            print("✓ [5a] Added faq_schema, website_schema, og_type to render_page")
        else:
            print("✗ [5a] Could not find render_page structured_data block")

        # Add new variables to render_template_string call
        old_template_call = '        structured_data=structured_data, breadcrumb_schema=breadcrumb_schema,\n        article_date=article_date'
        new_template_call = '        structured_data=structured_data, breadcrumb_schema=breadcrumb_schema,\n        faq_schema=faq_schema,\n        website_schema=website_schema,\n        og_type=og_type,\n        article_date=article_date'
        if old_template_call in c:
            c = c.replace(old_template_call, new_template_call, 1)
            applied += 1
            print("✓ [5b] Added faq_schema, website_schema, og_type to template call")
        else:
            print("✗ [5b] Could not find template call to update")
    else:
        print("⊘ [5] Already applied — render_page has new variables")

    # ══════════════════════════════════════════════════════════════
    # 6. Improved category meta title & description
    # ══════════════════════════════════════════════════════════════
    old_cat = '''title=f"Best {cat_name} Gifts UK 2026 | Trending Picks – FyboBuybo",
        description=f"Explore popular {cat_name.lower()} gifts loved by UK shoppers – updated daily.",'''
    new_cat = '''title=f"Best {cat_name} Gifts UK 2026 – Curated Picks | FyboBuybo",
        description=f"Hand-picked {cat_name.lower()} gift ideas for UK shoppers in 2026. Browse curated recommendations — find something they\\'ll love.",'''
    if old_cat in c:
        c = c.replace(old_cat, new_cat, 1)
        applied += 1
        print("✓ [6] Improved category page meta title & description")
    else:
        print("⊘ [6] Category meta already updated or pattern differs")

    # ══════════════════════════════════════════════════════════════
    # 7. Improved season meta title & description
    # ══════════════════════════════════════════════════════════════
    old_season = '''title=f"Best {title_season} 2026 – FyboBuybo",
        description=f"Discover the most popular {season_name.lower()} gifts for UK shoppers in 2026.",'''
    new_season = '''title=f"Best {title_season} UK 2026 – Gift Ideas | FyboBuybo",
        description=f"Curated {season_name.lower()} gift ideas for UK shoppers in 2026. Browse hand-picked recommendations — find the perfect gift.",'''
    if old_season in c:
        c = c.replace(old_season, new_season, 1)
        applied += 1
        print("✓ [7] Improved season page meta title & description")
    else:
        print("⊘ [7] Season meta already updated or pattern differs")

    # ══════════════════════════════════════════════════════════════
    # 8. Improved product meta title
    # ══════════════════════════════════════════════════════════════
    old_prod_title = """title=f"{shorten_product_name(found['name'], 50)} | UK Reviews – FyboBuybo","""
    new_prod_title = """title=f"{shorten_product_name(found['name'], 45)} – UK Gift Pick | FyboBuybo","""
    if old_prod_title in c:
        c = c.replace(old_prod_title, new_prod_title, 1)
        applied += 1
        print("✓ [8] Improved product page meta title")
    else:
        print("⊘ [8] Product title already updated or pattern differs")

    # ══════════════════════════════════════════════════════════════
    # 9. Blog FAQ schema injection
    # ══════════════════════════════════════════════════════════════
    if "blog_faq_schema_json" not in c:
        # Find blog_detail function and add FAQ collection
        blog_marker = '    content_html = f"""\n    <div style="max-width:720px;margin:56px auto 0;'
        if blog_marker in c:
            faq_block = '''    # Collect FAQs from related products for structured data
    blog_faqs = []
    for rp in related:
        if rp.get("faqs"):
            blog_faqs.extend(rp["faqs"][:2])
    blog_faq_schema_json = generate_faq_schema(blog_faqs[:10]) if blog_faqs else None

'''
            c = c.replace(blog_marker, faq_block + blog_marker, 1)

            # Add injection before blog's render_page
            bd_pos = c.find("def blog_detail(slug):")
            if bd_pos > -1:
                old_blog_return = '''    return render_page(
        title=post["title"],
        description=post.get("meta_description", post.get("description", "")),
        heading="", subtitle="",
        products=None, similar_products=related,
        article_date=post.get("date", datetime.date.today().isoformat()),
        content=content_html
    )'''
                new_blog_return = '''    # Inject FAQ schema into blog content if available
    if blog_faq_schema_json:
        content_html = f'<script type="application/ld+json">{blog_faq_schema_json}</script>\\n' + content_html

    return render_page(
        title=post["title"],
        description=post.get("meta_description", post.get("description", "")),
        heading="", subtitle="",
        products=None, similar_products=related,
        article_date=post.get("date", datetime.date.today().isoformat()),
        content=content_html
    )'''
                ret_pos = c.find(old_blog_return, bd_pos)
                if ret_pos > -1:
                    c = c[:ret_pos] + new_blog_return + c[ret_pos + len(old_blog_return):]
                    applied += 1
                    print("✓ [9] Added FAQ schema to blog pages")
                else:
                    print("✗ [9] Could not find blog render_page call")
            else:
                print("✗ [9] Could not find blog_detail function")
        else:
            print("✗ [9] Could not find blog content_html marker")
    else:
        print("⊘ [9] Already applied — blog FAQ schema exists")

    # Write result
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(c)

    print(f"\n{'='*60}")
    print(f"DONE — {applied} changes applied to app.py")
    print(f"{'='*60}")
    print(f"Your original is saved as app.py.backup")
    print(f"\nNext: test locally, then push to GitHub.")
    if applied == 0:
        print("\nAll changes were already applied! Your file is up to date.")

if __name__ == "__main__":
    main()
