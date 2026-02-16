import os
import json
import datetime
from threading import Thread


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "product_cache.json")
HISTORY_FILE = os.path.join(BASE_DIR, "product_history.json")


# ============================================================================
# CACHE AND PRODUCT MANAGEMENT
# ============================================================================

def should_refresh_cache(cache_refresh_days, prompt_version):
    if not os.path.exists(CACHE_FILE):
        return True

    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)

        cache_date = datetime.datetime.fromisoformat(
            cache.get("date", "2000-01-01T00:00:00")
        )

        days_old = (datetime.datetime.now() - cache_date).days

        if days_old >= cache_refresh_days:
            return True

        if cache.get("prompt_version") != prompt_version:
            return True

        return False

    except Exception:
        return True


def load_or_generate_hooks(
    products,
    generate_hook_func,
    prompt_version,
    ping_search_engines_func=None,
    flask_cache=None
):
    enriched = []

    for p in products:
        p_copy = dict(p)
        p_copy["hook"] = generate_hook_func(p)
        p_copy.setdefault("date_added", str(datetime.date.today()))
        p_copy["hook_version"] = prompt_version
        enriched.append(p_copy)

    today_iso = datetime.datetime.now().isoformat()

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "date": today_iso,
                "prompt_version": prompt_version,
                "products": enriched,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    history = load_history()
    history_key = datetime.date.today().isoformat()
    history[history_key] = enriched
    save_history(history)

    if ping_search_engines_func:
        Thread(target=ping_search_engines_func, daemon=True).start()

    if flask_cache:
        flask_cache.clear()

    return enriched


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def refresh_products(
    products,
    generate_hook_func,
    cache_refresh_days,
    prompt_version,
    ping_search_engines_func=None,
    flask_cache=None,
    background=False,
):
    today = str(datetime.date.today())

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)

            cache_date_str = cache_data.get("date", "")

            if cache_date_str.startswith(today):
                return cache_data.get("products", [])

            cache_date = datetime.datetime.fromisoformat(cache_date_str)

            if (
                (datetime.datetime.now() - cache_date).days < cache_refresh_days
                and cache_data.get("prompt_version") == prompt_version
            ):
                return cache_data.get("products", [])

        except Exception as e:
            print(f"Cache read failed: {e} — regenerating")

    return load_or_generate_hooks(
        products,
        generate_hook_func,
        prompt_version,
        ping_search_engines_func,
        flask_cache,
    )
