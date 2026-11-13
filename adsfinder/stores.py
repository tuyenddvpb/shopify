"""Follow ad links to the real store and check whether it runs on Shopify."""
import json
import queue
import urllib.error
from urllib.parse import urlparse
import re
import threading
import time
import urllib.request
from collections import OrderedDict

from .util import Watch, domain_of, is_excluded, log

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
    if any(k in h for k in ("x-shopid", "x-shopify-stage", "x-sorting-hat-shopid", "x-shopify-request-id",
                            "x-storefront-renderer-rendered")):
        return True
    if "shopify" in h.get("powered-by", "").lower() or "_shopify_" in h.get("set-cookie", ""):
        return True
    return "cdn.shopify.com" in html or "Shopify.theme" in html or "myshopify.com" in html


MYSHOPIFY_JS = "() => (window.Shopify && window.Shopify.shop) || ''"
_MYSHOPIFY = re.compile(
    r'(?:Shopify\.shop\s*=\s*|"myshopify_?domain"\s*:\s*|"shop"\s*:\s*)["\']([a-z0-9-]+\.myshopify\.com)', re.I)


def myshopify_in(html):
    """The store's xxx.myshopify.com name, from Shopify.shop = "..." in the page."""
    m = _MYSHOPIFY.search(html or "")
    return m.group(1).lower() if m else ""


def _read(resp, max_bytes, end):
    chunks, size = [], 0
    while size < max_bytes and time.monotonic() < end:
        chunk = resp.read(65536)
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
    return b"".join(chunks).decode("utf-8", "replace")


def fetch(url, timeout=12, max_bytes=400_000, deadline_s=20):
    """GET a page. Stops reading after max_bytes or deadline_s. Error pages
    (403, 429, 503...) are returned too: their headers still show Shopify."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    end = time.monotonic() + deadline_s
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - http(s) store links
            return resp.geturl(), _read(resp, max_bytes, end), dict(resp.headers), resp.status
    except urllib.error.HTTPError as e:
        try:
            body = _read(e, 100_000, end)
        except Exception:  # noqa: BLE001
            body = ""
        return e.geturl() or url, body, dict(e.headers or {}), e.code


def meta_json(url):
    """Shopify stores answer /meta.json with their myshopify domain."""
    u = urlparse(url)
    try:
        _final, body, _h, status = fetch(f"{u.scheme or 'https'}://{u.netloc}/meta.json",
                                         max_bytes=50_000, deadline_s=10)
        if status == 200:
            data = json.loads(body)
            if isinstance(data, dict) and str(data.get("myshopify_domain", "")).endswith(".myshopify.com"):
                return data["myshopify_domain"].lower()
    except Exception:  # noqa: BLE001
        pass
    return ""


def http_check(url):
    """Plain HTTP check. Returns (final_url, is_shopify or None, note, myshopify, needs_chrome)."""
    try:
        final, html, headers, status = fetch(url)
    except Exception as e:  # noqa: BLE001
        final, html, headers, status = url, "", {}, None
        err = e.__class__.__name__
    else:
        err = f"HTTP {status}" if status and status >= 400 else ""
    if shopify_in(html, headers):
        return final, True, "", myshopify_in(html), False
    mys = meta_json(final)
    if mys:
        return final, True, "nhận ra qua /meta.json", mys, False
    if err:
        return final, None, f"lỗi tải trang: {err}", "", True
    # Tiny pages are usually JS redirects or bot challenges: let Chrome look.
    return final, False, "không thấy dấu hiệu Shopify", "", len(html) < 6000


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


PROBE_JS = "() => ({shop: (" + SHOPIFY_JS.strip() + ")(), mys: (" + MYSHOPIFY_JS + ")()})"


def chrome_check(context, url, timeout_ms=20000, cdp_url=None):
    page = context.new_page()
    page.set_default_timeout(timeout_ms)
    page.on("dialog", _dismiss)
    # Last resort: if Playwright gets stuck on this tab, close the tab through
    # Chrome's own HTTP endpoint so the pending call fails and the run goes on.
    killer = None
    tid = _target_id(context, page)
    if cdp_url and tid:
        killer = threading.Timer(timeout_ms / 1000 * 2 + 10, _close_target, args=(cdp_url, tid))
        killer.daemon = True
        killer.start()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(2000)
        # wait_for_function honours the timeout; a plain evaluate() can wait forever.
        # Poll by interval: requestAnimationFrame stalls in background tabs.
        probe = page.wait_for_function(PROBE_JS, timeout=timeout_ms, polling=250).json_value()
        shop = bool(probe.get("shop"))
        mys = (probe.get("mys") or "").lower() if shop else ""
        return page.url, shop, "kiểm tra bằng Chrome", mys
    finally:
        if killer:
            killer.cancel()
        try:
            page.close(run_before_unload=False)
        except Exception:  # noqa: BLE001
            pass


def _target_id(context, page):
    try:
        cdp = context.new_cdp_session(page)
        tid = cdp.send("Target.getTargetInfo")["targetInfo"]["targetId"]
        cdp.detach()
        return tid
    except Exception:  # noqa: BLE001
        return None


def _close_target(cdp_url, tid):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for method in ("GET", "PUT"):
        try:
            opener.open(urllib.request.Request(f"{cdp_url}/json/close/{tid}", method=method), timeout=5)
            log(f"  Tab bị kẹt, đã tự đóng ({tid[:8]}).")
            return
        except Exception:  # noqa: BLE001
            continue


def _dismiss(dialog):
    try:
        dialog.dismiss()
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
        if needs_chrome and context is not None and cfg.get("store_check_chrome", True):
            chrome_queue.append((d, url, final, shop, note))
            log(f"  [{i}/{len(todo)}] {d}: chưa rõ ({note}), sẽ thử bằng Chrome")
            continue
        db.save_store(d, final, shop, note, mys)
        _log_store(i, len(todo), d, final, shop)

    for j, (d, url, final, shop, note) in enumerate(chrome_queue, 1):
        log(f"  Chrome [{j}/{len(chrome_queue)}] {d}...")
        try:
            with Watch(f"mở {d} bằng Chrome"):
                final, shop, note, mys = chrome_check(context, url, cfg["store_check_timeout"] * 1000,
                                                      cdp_url=cfg.get("cdp_url"))
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
