"""Track a store on ShopHunter, open its shop page and read the boxes."""
import base64
import re
import time
from pathlib import Path
from urllib.parse import urljoin

from .browser import dump_debug
from .textparse import box_pairs
from .util import log, wait_for_user

# Finds the "View shop" / "Tracked" controls that belong to this store's row:
# for each control, count how many levels up we must climb before the domain
# text appears, and keep the closest one.
STATE_JS = r"""
(domain) => {
  const d = domain.toLowerCase().replace(/^www\./, '');
  const els = [...document.querySelectorAll('a, button, [role="button"]')]
      .filter(e => e.getBoundingClientRect().width > 0);
  const depth = (el) => {
    let n = el;
    for (let i = 0; i < 12 && n; i++, n = n.parentElement)
      if ((n.textContent || '').toLowerCase().includes(d)) return i;
    return 99;
  };
  const pick = (re) => {
    const all = els.filter(e => re.test((e.innerText || e.textContent || '').trim()));
    let best = null, bd = 99;
    for (const e of all) { const k = depth(e); if (k < bd) { bd = k; best = e; } }
    return {all, best, near: bd < 99};
  };
  const view = pick(/^view\s*shop$/i);
  const tracked = pick(/^tracked$/i);
  document.querySelectorAll('[data-af-view]').forEach(e => e.removeAttribute('data-af-view'));
  let target = view.near ? view.best : (view.all.length === 1 ? view.all[0] : null);
  if (target) target.setAttribute('data-af-view', '1');
  const body = document.body.innerText || '';
  const err = (body.match(/(not a (valid )?shopify store|invalid (store )?url|limit reached|reached your limit|upgrade (your )?plan|something went wrong|couldn.t find)[^\n]*/i) || [''])[0];
  return {view: !!target, viewNear: view.near, tracked: tracked.near || (tracked.all.length === 1),
          analyzing: /analy[sz]ing|processing|tracking\.\.\./i.test(body), err};
}
"""

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
    inp.press("Enter")
    page.wait_for_timeout(2500)
    form_btn = inp.locator("xpath=ancestor::form[1]//button")
    named = page.get_by_role("button", name=re.compile(r"^(track|add|analy[sz]e|submit|search)", re.I))
    for btn in (form_btn, named):
        try:
            if btn.count() and btn.first.is_visible() and btn.first.is_enabled():
                btn.first.click()
                return
        except Exception:  # noqa: BLE001
            continue


def _ensure_login(page, track_url):
    for _ in range(3):
        if "login" in page.url or "sign" in page.url or page.locator("input[type='password']").count():
            wait_for_user("ShopHunter chưa đăng nhập. Hãy đăng nhập trong cửa sổ Chrome đang mở.")
            page.goto(track_url, wait_until="domcontentloaded")
        else:
            return


def _open_view_shop(context, page):
    el = page.locator('[data-af-view="1"]').first
    href = el.get_attribute("href")
    if href and not href.startswith("javascript"):
        shop = context.new_page()
        shop.goto(urljoin(page.url, href), wait_until="domcontentloaded", timeout=60000)
        return shop
    try:
        with context.expect_page(timeout=8000) as info:
            el.click()
        shop = info.value
    except Exception:  # noqa: BLE001 - same-tab navigation
        shop = page
    shop.wait_for_load_state("domcontentloaded")
    return shop


def analyze(context, domain, cfg, images_dir, debug_dir):
    """Return {status, shop_url, boxes: {name: {text, pairs}}, images: {name: b64}, error}."""
    track_url = cfg["shophunter_track_url"]
    result = {"status": "error", "shop_url": None, "boxes": {}, "images": {}, "error": None}
    page = context.new_page()
    shop = None
    try:
        page.goto(track_url, wait_until="domcontentloaded", timeout=60000)
        _ensure_login(page, track_url)
        page.wait_for_timeout(2000)
        inp = _find_input(page)
        if inp is None:
            raise RuntimeError("không tìm thấy ô 'Shopify Store URL'")
        inp.fill("")
        inp.fill(f"https://{domain}")
        _submit(page, inp)

        deadline = time.time() + cfg["shophunter_wait_seconds"]
        state = {}
        while time.time() < deadline:
            state = page.evaluate(STATE_JS, domain)
            if state["view"] and (state["tracked"] or state["viewNear"]):
                break
            if state["err"] and not state["analyzing"]:
                result["status"] = "rejected"
                raise RuntimeError(f"ShopHunter báo: {state['err'][:150]}")
            page.wait_for_timeout(3000)
        else:
            result["status"] = "timeout"
            raise RuntimeError(f"chờ {cfg['shophunter_wait_seconds']}s chưa thấy Tracked / View shop")
        if not state.get("viewNear"):
            log("  Lưu ý: không thấy tên store cạnh nút View shop, đã chọn nút duy nhất trên trang.")

        shop = _open_view_shop(context, page)
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
            result["error"] = "không thấy box: " + ", ".join(missing)
            dump_debug(shop, debug_dir, f"shophunter-{domain}")
        result["status"] = "ok" if result["boxes"] else "no_data"
    except Exception as e:  # noqa: BLE001
        result["error"] = str(e)
        log(f"  Lỗi ShopHunter ({domain}): {e}")
        dump_debug(shop or page, debug_dir, f"shophunter-{domain}")
    finally:
        for p in {page, shop} - {None}:
            try:
                p.close()
            except Exception:  # noqa: BLE001
                pass
    return result
