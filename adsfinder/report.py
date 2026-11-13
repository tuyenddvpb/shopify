"""Build one self-contained HTML report for a run."""
import base64
import json
from datetime import datetime
from pathlib import Path

from .util import days_since, money_to_float

ADS_PER_STORE = 3


def _b64_file(path):
    try:
        return base64.b64encode(Path(path).read_bytes()).decode()
    except (OSError, TypeError):
        return None


def _revenue(boxes):
    """Best guess at monthly revenue for sorting."""
    best = None
    for box in (boxes or {}).values():
        for label, value in box.get("pairs", []):
            if "revenue" in label.lower() and "$" in value:
                v = money_to_float(value)
                if v is not None:
                    if "month" in label.lower() or "30" in label:
                        return v
                    best = best if best is not None else v
    return best


def collect(db, run_id):
    ads = [dict(a) for a in db.run_ads(run_id)]
    stores = {}
    for ad in ads:
        d = ad["domain"] or ""
        stores.setdefault(d, []).append(ad)
    out = []
    for domain, items in stores.items():
        items.sort(key=lambda a: a["started"] or "9999")
        store = db.get_store(domain) if domain else None
        sh = db.get_shophunter(domain) if domain else None
        boxes = json.loads(sh["boxes_json"]) if sh and sh["boxes_json"] else {}
        images = json.loads(sh["images_json"]) if sh and sh["images_json"] else {}
        earliest = items[0]["started"]
        kws = sorted({k for a in items for k in (a["run_keywords"] or "").split("|") if k})
        out.append({
            "domain": domain,
            "store_url": (store["final_url"] if store else None) or (items[0]["link_url"] or ""),
            "is_shopify": store["is_shopify"] if store else None,
            "keywords": kws,
            "pages": sorted({a["page_name"] for a in items if a["page_name"]}),
            "ads_count": len(items),
            "versions": sum(a["versions"] or 1 for a in items),
            "earliest": earliest,
            "days": days_since(earliest) if earliest else None,
            "ads": [
                {
                    "id": a["library_id"],
                    "page": a["page_name"],
                    "started": a["started"],
                    "days": days_since(a["started"]) if a["started"] else None,
                    "versions": a["versions"],
                    "body": a["body"],
                    "link": a["link_url"],
                    "shot": _b64_file(a["shot_path"]) if i < ADS_PER_STORE else None,
                }
                for i, a in enumerate(items)
            ],
            "sh": {
                "status": sh["status"],
                "shop_url": sh["shop_url"],
                "error": sh["error"],
                "fetched_at": sh["fetched_at"],
                "boxes": {k: v.get("pairs", []) for k, v in boxes.items()},
                "images": images,
            } if sh else None,
            "revenue": _revenue(boxes),
        })
    return out


def build(db, run_id, cfg):
    run = db.get_run(run_id)
    stores = collect(db, run_id)
    meta = {
        "run_id": run_id,
        "keywords": json.loads(run["keywords"]),
        "country": cfg["country"],
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "boxes": cfg["shophunter_boxes"],
    }
    payload = json.dumps({"meta": meta, "stores": stores}, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", payload)
    out_dir = Path(cfg["reports_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"report-{datetime.now():%Y%m%d-%H%M}-run{run_id}.html"
    path.write_text(html, encoding="utf-8")
    db.finish_run(run_id, path)
    return path


TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ads Finder Report</title>
<style>
:root {
  --bg: #f6f7f9; --card: #ffffff; --text: #1b1f24; --muted: #5f6b7a; --line: #e3e7ec;
  --accent: #2f6fdf; --good: #1d8a4e; --warn: #b26b00; --bad: #c0392b; --chip: #eef2f7;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #111418; --card: #1a1f25; --text: #e7ebf0; --muted: #98a3b1; --line: #2b323b;
          --accent: #6ea0ff; --good: #4cc38a; --warn: #f0b04a; --bad: #ff7a6b; --chip: #242b34; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
       font: 14px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
header { padding: 20px 16px 8px; max-width: 1280px; margin: 0 auto; }
h1 { font-size: 22px; margin: 0 0 4px; }
.sub { color: var(--muted); }
.bar { position: sticky; top: 0; z-index: 5; background: var(--bg); border-bottom: 1px solid var(--line); }
.bar .in { max-width: 1280px; margin: 0 auto; padding: 10px 16px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
input, select { font: inherit; color: var(--text); background: var(--card); border: 1px solid var(--line);
                border-radius: 8px; padding: 6px 10px; }
input[type=search] { flex: 1 1 220px; }
label.chk { display: flex; gap: 6px; align-items: center; color: var(--muted); }
main { max-width: 1280px; margin: 0 auto; padding: 16px; display: grid; gap: 16px; }
.store { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
.top { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: baseline; justify-content: space-between; }
.top h2 { margin: 0; font-size: 18px; word-break: break-all; }
.top h2 a { color: var(--text); text-decoration: none; }
.top h2 a:hover { text-decoration: underline; }
.stats { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 12px; }
.chip { background: var(--chip); border-radius: 999px; padding: 2px 10px; font-size: 12.5px; color: var(--muted); }
.chip b { color: var(--text); }
.chip.good b { color: var(--good); } .chip.warn b { color: var(--warn); } .chip.bad b { color: var(--bad); }
.cols { display: grid; grid-template-columns: minmax(0, 340px) minmax(0, 1fr); gap: 16px; }
@media (max-width: 860px) { .cols { grid-template-columns: minmax(0, 1fr); } }
.ads { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }
.ad { flex: 0 0 160px; font-size: 12px; color: var(--muted); }
.ad img { width: 160px; height: 240px; object-fit: contain; object-position: top; border-radius: 8px;
          border: 1px solid var(--line); display: block; background: var(--chip); }
.ad .noimg { width: 160px; height: 60px; border-radius: 8px; background: var(--chip); display: grid; place-items: center; }
.ad a { color: var(--accent); }
.more { font-size: 12px; color: var(--muted); margin-top: 6px; }
.boxes { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
.box { border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; }
.box h3 { margin: 0 0 6px; font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
.box table { width: 100%; border-collapse: collapse; }
.box td { padding: 3px 0; border-bottom: 1px dashed var(--line); vertical-align: top; }
.box td:last-child { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
.box tr:last-child td { border-bottom: 0; }
.trend { grid-column: 1 / -1; }
.trend img { width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--line); background: #fff; }
.note { color: var(--muted); font-size: 13px; }
.err { color: var(--bad); font-size: 13px; }
.links a { color: var(--accent); margin-right: 12px; font-size: 13px; }
.empty { text-align: center; color: var(--muted); padding: 40px; }
dialog { border: 0; padding: 0; background: transparent; max-width: 95vw; }
dialog img { max-width: 95vw; max-height: 92vh; border-radius: 8px; }
dialog::backdrop { background: rgba(0,0,0,.75); }
</style>
</head>
<body>
<header>
  <h1>Ads Finder Report</h1>
  <div class="sub" id="sub"></div>
</header>
<div class="bar"><div class="in">
  <input type="search" id="q" placeholder="Tìm store, page, nội dung ad...">
  <select id="kw"><option value="">Tất cả từ khóa</option></select>
  <select id="sort">
    <option value="revenue">Sắp xếp: doanh thu</option>
    <option value="ads">Sắp xếp: số ad</option>
    <option value="days">Sắp xếp: chạy lâu nhất</option>
  </select>
  <label class="chk"><input type="checkbox" id="onlysh"> Chỉ store có dữ liệu ShopHunter</label>
  <span class="sub" id="count"></span>
</div></div>
<main id="list"></main>
<dialog id="zoom"><img alt=""></dialog>
<script type="application/json" id="data">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = (v) => v == null ? '—' : '$' + (v >= 1e6 ? (v/1e6).toFixed(1) + 'M' : v >= 1e3 ? (v/1e3).toFixed(1) + 'K' : v.toFixed(0));

$('#sub').textContent = `Từ khóa: ${DATA.meta.keywords.join(', ')} · Quốc gia: ${DATA.meta.country} · Tạo lúc ${DATA.meta.generated} · ${DATA.stores.length} store`;
for (const k of DATA.meta.keywords) $('#kw').insertAdjacentHTML('beforeend', `<option>${esc(k)}</option>`);

function shBlock(s) {
  const sh = s.sh;
  if (!s.domain) return '<p class="note">Ad không có link store.</p>';
  if (!sh) return `<p class="note">${s.is_shopify === 0 ? 'Không phải store Shopify, bỏ qua ShopHunter.' : 'Chưa tra ShopHunter (vượt giới hạn số store mỗi lượt hoặc lượt chạy bị dừng).'}</p>`;
  let h = '';
  if (sh.error) h += `<p class="err">ShopHunter: ${esc(sh.error)}</p>`;
  const boxes = DATA.meta.boxes.filter(b => sh.boxes[b] && sh.boxes[b].length && !sh.images[b]);
  if (boxes.length || Object.keys(sh.images).length) {
    h += '<div class="boxes">';
    for (const b of boxes) {
      h += `<div class="box"><h3>${esc(b)}</h3><table>` +
        sh.boxes[b].map(([k, v]) => k ? `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>` : `<tr><td colspan="2">${esc(v)}</td></tr>`).join('') +
        '</table></div>';
    }
    for (const [b, img] of Object.entries(sh.images)) {
      h += `<div class="box trend"><h3>${esc(b)}</h3><img loading="lazy" src="data:image/png;base64,${img}" alt="${esc(b)} ${esc(s.domain)}" data-zoom></div>`;
    }
    h += '</div>';
  }
  h += `<p class="note">Cập nhật ShopHunter: ${esc(sh.fetched_at || '')}</p>`;
  return h;
}

function card(s) {
  const ads = s.ads.filter(a => a.shot).map(a => `
    <div class="ad">
      <img loading="lazy" src="data:image/jpeg;base64,${a.shot}" alt="Ad ${esc(a.id)}" data-zoom>
      <div>${a.days != null ? a.days + ' ngày' : ''}${a.versions > 1 ? ' · ' + a.versions + ' phiên bản' : ''}</div>
      <a href="https://www.facebook.com/ads/library/?id=${esc(a.id)}" target="_blank" rel="noopener">Xem ad</a>
    </div>`).join('') || s.ads.slice(0, 3).map(a => `
    <div class="ad"><div class="noimg">Không có ảnh</div>
      <a href="https://www.facebook.com/ads/library/?id=${esc(a.id)}" target="_blank" rel="noopener">Xem ad</a></div>`).join('');
  const rest = s.ads.length - Math.min(3, s.ads.length);
  const shop = s.is_shopify === 1 ? '<span class="chip good"><b>Shopify</b></span>' :
               s.is_shopify === 0 ? '<span class="chip bad"><b>Không phải Shopify</b></span>' : '';
  const daysCls = s.days >= 30 ? 'good' : s.days >= 7 ? 'warn' : '';
  return `<section class="store">
    <div class="top">
      <h2>${s.domain ? `<a href="${esc(s.store_url || 'https://' + s.domain)}" target="_blank" rel="noopener">${esc(s.domain)}</a>` : 'Không rõ store'}</h2>
      <div class="links">
        ${s.sh && s.sh.shop_url ? `<a href="${esc(s.sh.shop_url)}" target="_blank" rel="noopener">Mở trên ShopHunter</a>` : ''}
        ${s.ads[0] && s.ads[0].link ? `<a href="${esc(s.ads[0].link)}" target="_blank" rel="noopener">Trang đích của ad</a>` : ''}
      </div>
    </div>
    <div class="stats">
      ${shop}
      <span class="chip">Doanh thu <b>${money(s.revenue)}</b></span>
      <span class="chip">Ads <b>${s.ads_count}</b></span>
      <span class="chip">Phiên bản <b>${s.versions}</b></span>
      <span class="chip ${daysCls}">Ad lâu nhất <b>${s.days ?? '—'} ngày</b></span>
      ${s.pages.length ? `<span class="chip">Page <b>${esc(s.pages.join(', '))}</b></span>` : ''}
      ${s.keywords.map(k => `<span class="chip">#${esc(k)}</span>`).join('')}
    </div>
    <div class="cols">
      <div><div class="ads">${ads}</div>${rest > 0 ? `<div class="more">+${rest} ad khác</div>` : ''}
        ${s.ads[0] && s.ads[0].body ? `<p class="note">“${esc(s.ads[0].body)}”</p>` : ''}</div>
      <div>${shBlock(s)}</div>
    </div>
  </section>`;
}

function render() {
  const q = $('#q').value.toLowerCase(), kw = $('#kw').value, only = $('#onlysh').checked, sort = $('#sort').value;
  let list = DATA.stores.filter(s =>
    (!kw || s.keywords.includes(kw)) &&
    (!only || (s.sh && s.sh.status === 'ok')) &&
    (!q || (s.domain + ' ' + s.pages.join(' ') + ' ' + s.ads.map(a => a.body).join(' ')).toLowerCase().includes(q)));
  const key = { revenue: s => s.revenue ?? -1, ads: s => s.ads_count, days: s => s.days ?? -1 }[sort];
  list.sort((a, b) => key(b) - key(a) || b.ads_count - a.ads_count);
  $('#count').textContent = `${list.length} / ${DATA.stores.length} store`;
  $('#list').innerHTML = list.length ? list.map(card).join('') : '<div class="empty">Không có store nào khớp bộ lọc.</div>';
}
['q', 'kw', 'sort', 'onlysh'].forEach(id => $('#' + id).addEventListener('input', render));
document.addEventListener('click', e => {
  if (e.target.matches('[data-zoom]')) { const d = $('#zoom'); d.querySelector('img').src = e.target.src; d.showModal(); }
  else if (e.target.closest('dialog')) $('#zoom').close();
});
render();
</script>
</body>
</html>
"""
