"""Search the Meta Ad Library page and read the ad cards."""
from pathlib import Path
from urllib.parse import urlencode

from .browser import dump_debug
from .util import days_since, domain_of, is_excluded, log, parse_fb_date, unwrap_fb_link, wait_for_user

# Runs in the page. Every ad card shows "Library ID: <digits>"; climb from that
# text to the largest ancestor that still holds exactly one Library ID: that's the card.
EXTRACT_JS = r"""
() => {
  const count = (el) => ((el.textContent || '').match(/Library ID:?\s*\d+/g) || []).length;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const starts = [];
  let n;
  while ((n = walker.nextNode())) {
    if (/Library ID/.test(n.nodeValue) && n.parentElement) starts.push(n.parentElement);
  }
  const seen = new Set();
  const out = [];
  for (const s of starts) {
    let el = s;
    while (count(el) === 0 && el.parentElement) el = el.parentElement;   // number in a sibling span
    let card = el;
    while (card.parentElement && card.parentElement !== document.body && count(card.parentElement) === 1)
      card = card.parentElement;
    const text = card.innerText || card.textContent || '';
    const idm = text.match(/Library ID:?\s*(\d+)/);
    if (!idm || seen.has(idm[1])) continue;
    seen.add(idm[1]);
    const id = idm[1];
    card.setAttribute('data-af-id', id);

    const started = (text.match(/Started running on\s+([A-Za-z]{3,9}\.? \d{1,2}, \d{4})/) || [])[1] || '';
    const vm = text.match(/(\d+)\s+ads?\s+use(?:s)? this creative and text/i);
    const versions = vm ? parseInt(vm[1], 10) : (/multiple versions/i.test(text) ? 2 : 1);

    const anchors = [...card.querySelectorAll('a[href]')];
    const decode = (h) => {
      try {
        const u = new URL(h, location.href);
        if (u.hostname.endsWith('facebook.com') && u.pathname.startsWith('/l.php'))
          return u.searchParams.get('u') || h;
        return u.href;
      } catch (e) { return h; }
    };
    const social = /(^|\.)(facebook\.com|fb\.com|fb\.me|instagram\.com|messenger\.com|whatsapp\.com)$/i;
    const links = [];
    for (const a of anchors) {
      const h = decode(a.getAttribute('href'));
      try { if (!social.test(new URL(h).hostname)) links.push(h); } catch (e) {}
    }
    let pageName = '', pageUrl = '';
    for (const a of anchors) {
      const t = (a.innerText || '').trim();
      let u; try { u = new URL(a.href); } catch (e) { continue; }
      if (/(^|\.)facebook\.com$/.test(u.hostname) && !u.pathname.startsWith('/ads/library')
          && !u.pathname.startsWith('/l.php') && t && t.length < 80) {
        pageName = t; pageUrl = u.origin + u.pathname; break;
      }
    }
    const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
    const sp = lines.findIndex(l => /^Sponsored$/i.test(l));
    const body = (sp >= 0 ? lines.slice(sp + 1, sp + 6) : []).join(' ').slice(0, 400);
    const v = card.querySelector('video');
    let poster = v ? (v.poster || '') : '';
    if (!poster) {
      const img = [...card.querySelectorAll('img')].find(i => (i.naturalWidth || i.width) >= 150);
      if (img) poster = img.src;
    }
    out.push({
      library_id: id, started_text: started, versions, page_name: pageName, page_url: pageUrl,
      links, body, video_url: v ? (v.currentSrc || v.src || '') : '', poster_url: poster,
      has_video: !!v,
    });
  }
  return out;
}
"""

COUNT_JS = r"() => ((document.body.innerText || '').match(/Library ID:?\s*\d+/g) || []).length"


def search_url(keyword, cfg):
    return cfg["adlibrary_url"] + "?" + urlencode({
        "active_status": "active",
        "ad_type": "all",
        "country": cfg["country"],
        "is_targeted_country": "false",
        "media_type": cfg["media_type"],
        "q": keyword,
        "search_type": cfg["search_type"],
    })


def _wait_results(page, timeout_s=45):
    """Return True when ad cards show, False when the search has no results."""
    for _ in range(timeout_s):
        url = page.url
        if "/login" in url or "checkpoint" in url:
            wait_for_user("Facebook đang yêu cầu đăng nhập hoặc xác minh. Hãy xử lý trong cửa sổ Chrome.")
            continue
        if page.evaluate(COUNT_JS) > 0:
            return True
        body = page.evaluate("() => document.body.innerText || ''")
        if "No ads match" in body or "0 results" in body or "No results" in body:
            return False
        page.wait_for_timeout(1000)
    return False


def search(page, keyword, cfg, shots_dir, debug_dir):
    log(f"Ad Library: tìm '{keyword}' ({cfg['country']})")
    page.goto(search_url(keyword, cfg), wait_until="domcontentloaded", timeout=60000)
    if not _wait_results(page):
        log("  Không thấy ad nào (hoặc trang chưa tải).")
        dump_debug(page, debug_dir, f"adlib-{keyword}")
        return []

    want = cfg["max_ads_per_keyword"]
    last, stale = 0, 0
    while True:
        n = page.evaluate(COUNT_JS)
        if n >= want:
            break
        stale = stale + 1 if n == last else 0
        if stale >= 4:
            break
        last = n
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2500)
    log(f"  Thấy {page.evaluate(COUNT_JS)} ad, đang đọc...")

    raw = page.evaluate(EXTRACT_JS)[:want]
    Path(shots_dir).mkdir(parents=True, exist_ok=True)
    ads = []
    for r in raw:
        ad = normalize(r, cfg)
        if ad is None:
            continue
        try:
            loc = page.locator(f'[data-af-id="{ad["library_id"]}"]').first
            loc.scroll_into_view_if_needed(timeout=5000)
            page.wait_for_timeout(300)
            path = Path(shots_dir) / f"{ad['library_id']}.jpg"
            loc.screenshot(path=str(path), type="jpeg", quality=60, timeout=10000)
            ad["shot_path"] = str(path)
        except Exception as e:  # noqa: BLE001
            log(f"  Không chụp được ad {ad['library_id']}: {e.__class__.__name__}")
        ads.append(ad)
    with_store = sum(1 for a in ads if a.get("domain"))
    log(f"  Lấy được {len(ads)} ad, {with_store} ad có link store.")
    return ads


def normalize(r, cfg):
    started = parse_fb_date(r.get("started_text"))
    if cfg.get("min_days_running") and started:
        if days_since(started) < cfg["min_days_running"]:
            return None
    link, domain = "", ""
    for raw_link in r.get("links") or []:
        u = unwrap_fb_link(raw_link)
        d = domain_of(u)
        if d and not is_excluded(d, cfg["exclude_domains"]):
            link, domain = u, d
            break
    return {
        "library_id": r["library_id"],
        "country": cfg["country"],
        "page_name": r.get("page_name") or "",
        "page_url": r.get("page_url") or "",
        "started": started.isoformat() if started else None,
        "versions": r.get("versions") or 1,
        "body": r.get("body") or "",
        "video_url": r.get("video_url") or "",
        "poster_url": r.get("poster_url") or "",
        "link_url": link,
        "domain": domain,
    }
