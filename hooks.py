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

