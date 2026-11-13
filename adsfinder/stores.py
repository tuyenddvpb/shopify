"""Follow ad links to the real store and check whether it runs on Shopify."""
import re
import urllib.request
from collections import OrderedDict

from .util import domain_of, is_excluded, log

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

SHOPIFY_JS = r"""
() => !!(window.Shopify && (window.Shopify.shop || window.Shopify.theme))
   || !!document.querySelector('link[href*="cdn.shopify.com"], script[src*="cdn.shopify.com"], meta[name="shopify-checkout-api-token"]')
"""


def shopify_in(html, headers):
    h = {k.lower(): v for k, v in (headers or {}).items()}
    if "x-shopid" in h or "x-shopify-stage" in h or "shopify" in h.get("powered-by", "").lower():
        return True
    return "cdn.shopify.com" in html or "Shopify.theme" in html or "myshopify.com" in html


MYSHOPIFY_JS = "() => (window.Shopify && window.Shopify.shop) || ''"
_MYSHOPIFY = re.compile(
    r'(?:Shopify\.shop\s*=\s*|"myshopify_?domain"\s*:\s*|"shop"\s*:\s*)["\']([a-z0-9-]+\.myshopify\.com)', re.I)


def myshopify_in(html):
    """The store's xxx.myshopify.com name, from Shopify.shop = "..." in the page."""
    m = _MYSHOPIFY.search(html or "")
    return m.group(1).lower() if m else ""


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - http(s) store links
        html = resp.read(400_000).decode("utf-8", "replace")
        return resp.geturl(), html, dict(resp.headers)


def check(url, context=None):
    """Return (final_url, is_shopify or None, note, myshopify_domain)."""
    try:
        final, html, headers = fetch(url)
        if shopify_in(html, headers):
            return final, True, "", myshopify_in(html)
        note = "không thấy dấu hiệu Shopify"
    except Exception as e:  # noqa: BLE001
        final, note = url, f"lỗi tải trang: {e.__class__.__name__}"
    if context is None:
        return final, None if note.startswith("lỗi") else False, note, ""
    # Some stores block plain HTTP clients or redirect with JS: retry in Chrome.
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)
        shop = bool(page.evaluate(SHOPIFY_JS))
        mys = (page.evaluate(MYSHOPIFY_JS) or "").lower() if shop else ""
        return page.url, shop, "kiểm tra bằng Chrome", mys
    except Exception as e:  # noqa: BLE001
        return final, None, f"{note}; Chrome: {e.__class__.__name__}", ""
    finally:
        page.close()


def group_by_store(ads, excluded):
    """{domain: [ad, ...]} ordered by number of ads, most first."""
    groups = {}
    for ad in ads:
        d = ad["domain"]
        if d and not is_excluded(d, excluded):
            groups.setdefault(d, []).append(ad)
    return OrderedDict(sorted(groups.items(), key=lambda kv: -len(kv[1])))


def resolve_all(db, groups, cfg, context):
    """Check each store once (cached), returns {domain: store row-like dict}.

    A store reached through a redirect is stored under its final domain too."""
    out = {}
    for domain, ads in groups.items():
        row = db.get_store(domain, cfg["store_check_hours"])
        if row is None:
            final, shop, note, mys = check(ads[0]["link_url"] or f"https://{domain}", context)
            db.save_store(domain, final, shop, note, mys)
            row = db.get_store(domain)
            fd = domain_of(final)
            label = "Shopify" if shop else "không phải Shopify" if shop is False else "chưa rõ"
            log(f"  {domain}{' -> ' + fd if fd and fd != domain else ''}: {label}")
        out[domain] = dict(row)
    return out
