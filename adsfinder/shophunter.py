"""Track a store on ShopHunter, open its shop page and read the boxes."""
import base64
import re
import time
from pathlib import Path
from urllib.parse import urljoin

from .browser import dump_debug
from .textparse import box_pairs
from .util import log, wait_for_user

# Shared by both lookups: find the text label that is exactly one of our
# domains, then climb to the largest ancestor holding no other domain label.
# That ancestor is the store's row (Recent Activity) or card (collections page).
_FIND_JS = r"""
  const norm = s => (s || '').trim().toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, '');
  const want = new Set(domains.map(norm));
  const DOMAIN = /^(https?:\/\/)?([a-z0-9-]+\.)+[a-z]{2,}\/?$/i;
  const labels = [...document.querySelectorAll('body *')].filter(el => {
    if (el.closest('input, textarea, script, style')) return false;
    const t = (el.textContent || '').trim();
    return DOMAIN.test(t) && ![...el.children].some(c => (c.textContent || '').trim() === t);
  });
  const mine = labels.filter(el => want.has(norm(el.textContent)) && el.getBoundingClientRect().height > 0);
  document.querySelectorAll('[data-af-open]').forEach(e => e.removeAttribute('data-af-open'));
  const rowOf = (label) => {
    let row = label;
    while (row.parentElement && row.parentElement !== document.body) {
      const p = row.parentElement;
      if (labels.some(l => !row.contains(l) && p.contains(l))) break;
      if (p.querySelector('input')) break;
      row = p;
    }
    return row;
  };
  const say = (el) => (el.innerText || el.textContent || '').trim();
"""

# Recent Activity on /shops/track: our row shows "Tracked" + "View Shop" when
# ready, or "Not a Shopify Store" when ShopHunter refuses it.
ROW_JS = "(domains) => {" + _FIND_JS + r"""
  if (!mine.length) return {found: false, status: 'pending'};
  const row = rowOf(mine[0]);            // newest entry is on top
  const text = say(row);
  const view = [...row.querySelectorAll('a, button, [role="button"]')].find(e => /^view\s*shop$/i.test(say(e)));
  const tracked = [...row.querySelectorAll('*')].some(e => /^tracked$/i.test(say(e)));
  const bad = text.match(/not a shopify store|invalid (store )?url|failed|could not|couldn.t/i);
  if (view) view.setAttribute('data-af-open', '1');
  return {found: true, text: text.slice(0, 200), label: say(mine[0]),
          status: bad ? 'rejected' : tracked ? (view ? 'tracked' : 'tracked_noview') : 'pending'};
}"""

# /collections/shops: our card has the store name (a link) above the domain.
CARD_JS = "(domains) => {" + _FIND_JS + r"""
  if (!mine.length) return {found: false};
  const label = mine[0];
  const card = rowOf(label);
  const before = (el) => label.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_PRECEDING;
  const links = [...card.querySelectorAll('a[href]')]
      .filter(a => !/^(#|javascript:)/i.test(a.getAttribute('href')) && say(a));
  // the name link sits just before the domain label; else any link in the card header
  let target = links.filter(before).pop() || links[0];
  if (!target) {
    // name not a link: click the element right before the domain label
    let n = label;
    while (n && !n.previousElementSibling) n = n.parentElement;
    target = n ? n.previousElementSibling : null;
  }
  if (!target) return {found: true, link: false};
  target.setAttribute('data-af-open', '1');
  return {found: true, link: true, name: say(target).slice(0, 80), href: target.getAttribute('href') || ''};
}"""

# Finds each named box: the smallest element whose text is the heading, then
# climbs while the parent still looks like the same card.
BOXES_JS = r"""
(headings) => {
  const lower = headings.map(h => h.toLowerCase());
  const all = [...document.body.querySelectorAll('*')];
  const txt = (el) => (el.textContent || '').trim().toLowerCase();
  const hcount = (el) => el.querySelectorAll('h1,h2,h3,h4,h5,h6').length;
  const res = {};
  headings.forEach((h, idx) => {
    const lh = lower[idx];
    let cands = all.filter(el => { const t = txt(el); return t === lh || (t.startsWith(lh) && t.length < lh.length + 20); });
    cands = cands.filter(el => ![...el.children].some(c => cands.includes(c)));
    const head = cands.find(el => el.getBoundingClientRect().height > 0);
    if (!head) { res[h] = null; return; }
    const others = lower.filter(x => x !== lh);
    let box = head;
    while (box.parentElement && box.parentElement !== document.body) {
      const p = box.parentElement;
      const pt = txt(p);
      if (others.some(o => pt.includes(o))) break;
      if (hcount(p) > Math.max(1, hcount(box))) break;
      const br = box.getBoundingClientRect(), pr = p.getBoundingClientRect();
      if (pr.height > window.innerHeight * 1.6) break;
      if (br.height >= 100 && pr.width > br.width * 1.3) break;
      box = p;
    }
    box.setAttribute('data-af-box', h);
    res[h] = {text: box.innerText || ''};
  });
  return res;
}
"""


def _find_input(page):
    cands = [
        page.get_by_label(re.compile(r"shopify store url", re.I)),
        page.get_by_placeholder(re.compile(r"store|shopify|url|domain", re.I)),
        page.locator("xpath=//*[contains(normalize-space(.), 'Shopify Store URL')]/following::input[1]"),
        page.locator("input[type='url'], input[type='text']"),
    ]
    for c in cands:
        try:
            if c.count() and c.first.is_visible():
                return c.first
        except Exception:  # noqa: BLE001
            continue
    return None


def _submit(page, inp):
    btn = page.get_by_role("button", name=re.compile(r"track\s*store|^track|^add|analy[sz]e", re.I))
    try:
        if btn.count() and btn.first.is_visible() and btn.first.is_enabled():
            btn.first.click()
            return
    except Exception:  # noqa: BLE001
        pass
    inp.press("Enter")


def _ensure_login(page, track_url):
    for _ in range(3):
        if "login" in page.url or "sign" in page.url or page.locator("input[type='password']").count():
            wait_for_user("ShopHunter chưa đăng nhập. Hãy đăng nhập trong cửa sổ Chrome đang mở.")
            page.goto(track_url, wait_until="domcontentloaded")
        else:
            return


def _open_marked(context, page):
    """Open the element marked data-af-open (View Shop button or store-name link)."""
    el = page.locator('[data-af-open="1"]').first
    href = el.get_attribute("href")
    if href and not href.startswith("javascript"):
        shop = context.new_page()
        shop.goto(urljoin(page.url, href), wait_until="domcontentloaded", timeout=60000)
        return shop
    before = page.url
    try:
        with context.expect_page(timeout=8000) as info:
            el.click()
        shop = info.value
    except Exception:  # noqa: BLE001 - opened in the same tab
        shop = page
        if shop.url == before:
            shop.wait_for_timeout(3000)
    shop.wait_for_load_state("domcontentloaded")
    return shop


def _track(page, url, domains, cfg):
    """Way 1: enter the store on /shops/track and watch its Recent Activity row.

    Returns (status, info) with status tracked / tracked_noview / rejected / timeout."""
    page.goto(cfg["shophunter_track_url"], wait_until="domcontentloaded", timeout=60000)
    _ensure_login(page, cfg["shophunter_track_url"])
    page.wait_for_timeout(2000)
    inp = _find_input(page)
    if inp is None:
        raise RuntimeError("không tìm thấy ô 'Shopify Store URL'")
    inp.fill("")
    inp.fill(url)
    _submit(page, inp)
    deadline = time.time() + cfg["shophunter_wait_seconds"]
    noview_since = None
    state = {"status": "pending"}
    while time.time() < deadline:
        page.wait_for_timeout(3000)
        state = page.evaluate(ROW_JS, domains)
        if state["status"] in ("tracked", "rejected"):
            return state["status"], state
        if state["status"] == "tracked_noview":
            noview_since = noview_since or time.time()
            if time.time() - noview_since > 15:
                return "tracked_noview", state
    return "timeout", state


def _from_collections(page, domains, cfg):
    """Way 2: find the store's card on /collections/shops, scrolling as needed."""
    page.goto(cfg["shophunter_collections_url"], wait_until="domcontentloaded", timeout=60000)
    _ensure_login(page, cfg["shophunter_collections_url"])
    page.wait_for_timeout(3000)
    last_h, stale = 0, 0
    for _ in range(60):
        res = page.evaluate(CARD_JS, domains)
        if res.get("found"):
            return res
        h = page.evaluate("() => document.documentElement.scrollHeight")
        stale = stale + 1 if h == last_h else 0
        if stale >= 3:
            break
        last_h = h
        page.mouse.wheel(0, 2500)
        page.evaluate("() => { document.querySelectorAll('*').forEach(e => { if (e.scrollHeight > e.clientHeight + 50 && getComputedStyle(e).overflowY.match(/auto|scroll/)) e.scrollTop += 2500; }); }")
        page.wait_for_timeout(1500)
    return {"found": False}


def _norm(d):
    d = (d or "").lower().strip()
    d = re.sub(r"^https?://", "", d).split("/")[0]
    return d[4:] if d.startswith("www.") else d


def analyze(context, domain, cfg, images_dir, debug_dir, myshopify=""):
    """Return {status, shop_url, boxes: {name: {text, pairs}}, images: {name: b64}, error}."""
    domains = [d for d in dict.fromkeys([_norm(domain), _norm(myshopify)]) if d]
    result = {"status": "error", "shop_url": None, "boxes": {}, "images": {}, "error": None}
    page = context.new_page()
    shop = None
    try:
        status, info = _track(page, f"https://{domain}", domains, cfg)
        if status == "rejected" and myshopify:
            log(f"  ShopHunter báo '{' '.join(info.get('text', '').split())[:80]}', thử lại với {myshopify}")
            status, info = _track(page, f"https://{myshopify}", domains, cfg)
        if status == "rejected":
            result["status"] = "rejected"
            raise RuntimeError("ShopHunter: " + " ".join(info.get("text", "").split())[:150])
        if status == "tracked":
            log("  Đã Tracked, mở View Shop.")
            shop = _open_marked(context, page)
        else:
            log("  Chưa thấy View Shop" + (" (hết thời gian chờ)" if status == "timeout" else "") +
                ", tìm trong trang Collections.")
            card = _from_collections(page, domains, cfg)
            if not card.get("found"):
                result["status"] = "timeout" if status == "timeout" else "not_found"
                raise RuntimeError("không thấy store trong Recent Activity lẫn Collections")
            if not card.get("link"):
                raise RuntimeError("thấy store trong Collections nhưng không thấy link tên store")
            shop = _open_marked(context, page)
        result["shop_url"] = shop.url

        headings = cfg["shophunter_boxes"]
        try:
            shop.get_by_text(headings[0], exact=False).first.wait_for(timeout=60000)
        except Exception:  # noqa: BLE001
            pass
        try:
            shop.wait_for_load_state("networkidle", timeout=20000)
        except Exception:  # noqa: BLE001
            pass
        shop.wait_for_timeout(3000)  # let charts finish animating

        body = _norm_text(shop.evaluate("() => document.body.innerText || ''"))
        warn = [] if any(d in body for d in domains) else [
            f"trang shop không hiện {domains[0]}, có thể đã mở nhầm store"]

        boxes = shop.evaluate(BOXES_JS, headings)
        Path(images_dir).mkdir(parents=True, exist_ok=True)
        missing = []
        for name in headings:
            b = boxes.get(name)
            if not b:
                missing.append(name)
                continue
            result["boxes"][name] = {"text": b["text"], "pairs": box_pairs(b["text"], name)}
            if name in cfg["shophunter_image_boxes"]:
                loc = shop.locator(f'[data-af-box="{name}"]').first
                loc.scroll_into_view_if_needed(timeout=5000)
                shop.wait_for_timeout(1500)
                path = Path(images_dir) / f"{domain}-{name.replace(' ', '_')}.png"
                loc.screenshot(path=str(path), timeout=15000)
                result["images"][name] = base64.b64encode(path.read_bytes()).decode()
        if missing:
            warn.append("không thấy box: " + ", ".join(missing))
        if warn:
            result["error"] = "; ".join(warn)
            log("  Lưu ý: " + result["error"])
            dump_debug(shop, debug_dir, f"shophunter-{domain}")
        result["status"] = "ok" if result["boxes"] else "no_data"
    except Exception as e:  # noqa: BLE001
        result["error"] = str(e)
        log(f"  Lỗi ShopHunter ({domain}): {e}")
        if result["status"] != "rejected":
            dump_debug(shop or page, debug_dir, f"shophunter-{domain}")
    finally:
        for p in {page, shop} - {None}:
            try:
                p.close()
            except Exception:  # noqa: BLE001
                pass
    return result


def _norm_text(t):
    return re.sub(r"https?://(www\.)?", "", (t or "").lower()).replace("www.", "")
