"""Follow ad links to the real store and check whether it runs on Shopify."""
import queue
import re
import threading
import time
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


def fetch(url, timeout=12, max_bytes=400_000, deadline_s=20):
    """GET a page. Stops reading after max_bytes or deadline_s, whichever first."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    end = time.monotonic() + deadline_s
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - http(s) store links
        chunks, size = [], 0
        while size < max_bytes and time.monotonic() < end:
            chunk = resp.read(65536)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        return resp.geturl(), b"".join(chunks).decode("utf-8", "replace"), dict(resp.headers)


def http_check(url):
    """Plain HTTP check. Returns (final_url, is_shopify or None, note, myshopify, needs_chrome)."""
    try:
        final, html, headers = fetch(url)
    except Exception as e:  # noqa: BLE001
        return url, None, f"lỗi tải trang: {e.__class__.__name__}", "", True
    if shopify_in(html, headers):
        return final, True, "", myshopify_in(html), False
    # Tiny pages are usually JS redirects or bot challenges: let Chrome look.
    small = len(html) < 6000
    return final, False, "không thấy dấu hiệu Shopify", "", small


def _with_deadline(fn, arg, seconds):
    """Run fn(arg) in a daemon thread; give up after `seconds` (DNS/TLS can hang)."""
    box = {}

    def target():
        try:
            box["v"] = fn(arg)
        except Exception as e:  # noqa: BLE001
            box["e"] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(seconds)
    if t.is_alive():
        return None
    if "e" in box:
        raise box["e"]
    return box["v"]


def chrome_check(context, url, timeout_ms=20000):
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(2000)
        shop = bool(page.evaluate(SHOPIFY_JS))
        mys = (page.evaluate(MYSHOPIFY_JS) or "").lower() if shop else ""
        return page.url, shop, "kiểm tra bằng Chrome", mys
    finally:
        try:
            page.close()
        except Exception:  # noqa: BLE001
            pass


def check(url, context=None):
    """Return (final_url, is_shopify or None, note, myshopify_domain)."""
    res = _with_deadline(http_check, url, 30) or (url, None, "quá thời gian chờ", "", True)
    final, shop, note, mys, needs_chrome = res
    if not needs_chrome or context is None:
        return final, shop, note, mys
    try:
        return chrome_check(context, url)
    except Exception as e:  # noqa: BLE001
        return final, shop if shop is False else None, f"{note}; Chrome: {e.__class__.__name__}", ""


def group_by_store(ads, excluded):
    """{domain: [ad, ...]} ordered by number of ads, most first."""
    groups = {}
    for ad in ads:
        d = ad["domain"]
        if d and not is_excluded(d, excluded):
            groups.setdefault(d, []).append(ad)
    return OrderedDict(sorted(groups.items(), key=lambda kv: -len(kv[1])))


def resolve_all(db, groups, cfg, context):
    """Check each store once (cached). Returns {domain: store row dict}.

    Plain HTTP checks run in parallel threads, each with a hard deadline; only
    stores that failed or returned a near-empty page are opened in Chrome."""
    todo = [(d, ads[0]["link_url"] or f"https://{d}") for d, ads in groups.items()
            if db.get_store(d, cfg["store_check_hours"]) is None]
    cached = len(groups) - len(todo)
    if cached:
        log(f"  {cached} store đã kiểm tra gần đây, dùng lại kết quả.")
    if todo:
        log(f"  Kiểm tra {len(todo)} store ({cfg['store_check_workers']} luồng song song)...")

    jobs, results = queue.Queue(), queue.Queue()
    for item in todo:
        jobs.put(item)

    def worker():
        while True:
            try:
                d, url = jobs.get_nowait()
            except queue.Empty:
                return
            res = _with_deadline(http_check, url, cfg["store_check_timeout"])
            results.put((d, url, res or (url, None, "quá thời gian chờ", "", True)))

    for _ in range(min(cfg["store_check_workers"], len(todo))):
        threading.Thread(target=worker, daemon=True).start()

    chrome_queue = []
    for i in range(1, len(todo) + 1):
        while True:
            try:
                d, url, (final, shop, note, mys, needs_chrome) = results.get(timeout=1)
                break
            except queue.Empty:  # short waits keep Ctrl+C working
                continue
        if needs_chrome and context is not None:
            chrome_queue.append((d, url, final, shop, note))
            log(f"  [{i}/{len(todo)}] {d}: chưa rõ ({note}), sẽ thử bằng Chrome")
            continue
        db.save_store(d, final, shop, note, mys)
        _log_store(i, len(todo), d, final, shop)

    for j, (d, url, final, shop, note) in enumerate(chrome_queue, 1):
        log(f"  Chrome [{j}/{len(chrome_queue)}] {d}...")
        try:
            final, shop, note, mys = chrome_check(context, url, cfg["store_check_timeout"] * 1000)
        except Exception as e:  # noqa: BLE001
            shop = shop if shop is False else None
            note, mys = f"{note}; Chrome: {e.__class__.__name__}", ""
        db.save_store(d, final, shop, note, mys)
        _log_store(j, len(chrome_queue), d, final, shop)

    return {d: dict(db.get_store(d)) for d in groups}


def _log_store(i, n, domain, final, shop):
    fd = domain_of(final)
    label = "Shopify" if shop else "không phải Shopify" if shop is False else "chưa rõ"
    log(f"  [{i}/{n}] {domain}{' -> ' + fd if fd and fd != domain else ''}: {label}")
