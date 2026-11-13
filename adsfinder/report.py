"""Build an HTML report for one run or several (last N days)."""
import base64
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from .textparse import box_pairs
from .util import days_since, money_to_float

ADS_PER_STORE = 4


EMBED_MAX_STORES = 40   # "auto": embed images up to this many stores, else write image files


def _b64_file(path):
    try:
        return base64.b64encode(Path(path).read_bytes()).decode()
    except (OSError, TypeError):
        return None


def _safe(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:120]


def _revenue(boxes):
    """Monthly revenue for sorting: 'Month' in a revenue box, else week x 4.3, else day x 30."""
    found = {}
    for name, rows in boxes.items():
        for label, value, *_ in rows:
            lab = label.lower()
            if "revenue" not in name.lower() and "revenue" not in lab:
                continue
            v = money_to_float(value) if "$" in value else None
            if v is None:
                continue
            for key, mult in (("month", 1), ("week", 4.3), ("day", 30), ("daily", 30)):
                if key in lab:
                    found.setdefault(key, v * mult)
                    break
    for key in ("month", "week", "day", "daily"):
        if key in found:
            return found[key]
    return None


def collect(db, run_ids, shopify_only=True):
    """Stores seen in the given run(s). Images are left as file paths / base64 for attach_images()."""
    ads = [dict(a) for a in db.run_ads(run_ids)]
    stores = {}
    for ad in ads:
        if ad["domain"]:
            stores.setdefault(ad["domain"], []).append(ad)
    out = []
    for domain, items in stores.items():
        store = db.get_store(domain)
        if shopify_only and not (store and store["is_shopify"] == 1):
            continue
        items.sort(key=lambda a: a["started"] or "9999")
        sh = db.get_shophunter(domain)
        raw = json.loads(sh["boxes_json"]) if sh and sh["boxes_json"] else {}
        # re-parse stored text so parser fixes apply to old runs too
        boxes = {k: box_pairs(v.get("text", ""), k) for k, v in raw.items()}
        images = json.loads(sh["images_json"]) if sh and sh["images_json"] else {}
        earliest = items[0]["started"]
        kws = sorted({k for a in items for k in (a["run_keywords"] or "").split("|") if k})
        out.append({
            "domain": domain,
            "store_url": (store["final_url"] if store else None) or (items[0]["link_url"] or ""),
            "keywords": kws,
            "pages": sorted({a["page_name"] for a in items if a["page_name"]}),
            "ads_count": len(items),
            "versions": sum(a["versions"] or 1 for a in items),
            "earliest": earliest,
            "days": days_since(earliest) if earliest else None,
            "body": next((a["body"] for a in items if a["body"]), ""),
            "link": items[0]["link_url"],
            "ads": [
                {
                    "id": a["library_id"],
                    "days": days_since(a["started"]) if a["started"] else None,
                    "versions": a["versions"],
                    "shot": a["shot_path"] if i < ADS_PER_STORE else None,
                }
                for i, a in enumerate(items)
            ],
            "sh": {
                "status": sh["status"],
                "shop_url": sh["shop_url"],
                "error": sh["error"],
                "fetched_at": sh["fetched_at"],
                "boxes": boxes,
                "images": images,
            } if sh else None,
            "revenue": _revenue(boxes),
        })
    return out


def attach_images(stores, embed, out_dir):
    """Turn image refs into <img src> values: data: URIs, or files under out_dir/assets/."""
    assets = Path(out_dir) / "assets"
    for s in stores:
        for a in s["ads"]:
            path = a.pop("shot")
            a["img"] = None
            if not path or not Path(path).exists():
                continue
            if embed:
                a["img"] = "data:image/jpeg;base64," + _b64_file(path)
            else:
                dest = assets / "ads" / Path(path).name
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.copyfile(path, dest)
                a["img"] = f"assets/ads/{dest.name}"
        sh = s["sh"]
        if not sh:
            continue
        stamp = re.sub(r"\D", "", sh.get("fetched_at") or "")
        for name, b64 in list(sh["images"].items()):
            if embed:
                sh["images"][name] = "data:image/png;base64," + b64
            else:
                dest = assets / "charts" / _safe(f"{s['domain']}-{name}-{stamp}.png")
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    dest.write_bytes(base64.b64decode(b64))
                sh["images"][name] = f"assets/charts/{dest.name}"
    return stores


def build(db, run_ids, cfg, embed=None, label=None):
    """run_ids: one id or a list. embed: True / False / None (= config, default auto)."""
    ids = [run_ids] if isinstance(run_ids, int) else list(run_ids)
    keywords = []
    for rid in ids:
        keywords += json.loads(db.get_run(rid)["keywords"])
    stores = collect(db, ids)
    if embed is None:
        mode = cfg.get("report_embed_images", "auto")
        embed = len(stores) <= EMBED_MAX_STORES if mode == "auto" else bool(mode)
    out_dir = Path(cfg["reports_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    attach_images(stores, embed, out_dir)
    meta = {
        "runs": ids,
        "keywords": list(dict.fromkeys(keywords)),
        "country": cfg["country"],
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "label": label or (f"lượt #{ids[0]}" if len(ids) == 1 else f"{len(ids)} lượt"),
        "boxes": cfg["shophunter_boxes"],
        "image_boxes": cfg["shophunter_image_boxes"],
        "embedded": embed,
    }
    payload = json.dumps({"meta": meta, "stores": stores}, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", payload)
    suffix = f"run{ids[0]}" if len(ids) == 1 else f"runs{ids[0]}-{ids[-1]}"
    path = out_dir / f"report-{datetime.now():%Y%m%d-%H%M}-{suffix}.html"
    path.write_text(html, encoding="utf-8")
    if len(ids) == 1:
        db.finish_run(ids[0], path)
    return path


TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ads Finder Report</title>
<style>
:root {
  --bg: #f4f6f9; --card: #ffffff; --text: #1b1f24; --muted: #667281; --line: #e3e7ec;
  --accent: #2f6fdf; --up: #1d8a4e; --down: #c0392b; --chip: #eef2f7; --rank: #1b1f24;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #111418; --card: #1a1f25; --text: #e7ebf0; --muted: #98a3b1; --line: #2b323b;
          --accent: #6ea0ff; --up: #4cc38a; --down: #ff7a6b; --chip: #242b34; --rank: #e7ebf0; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
       font: 13px/1.45 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.wrap { max-width: 1600px; margin: 0 auto; padding: 0 16px; }
header { padding: 16px 0 6px; }
h1 { font-size: 20px; margin: 0 0 2px; }
.sub { color: var(--muted); }
.bar { position: sticky; top: 0; z-index: 5; background: var(--bg); border-bottom: 1px solid var(--line); }
.bar .wrap { padding-top: 8px; padding-bottom: 8px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
input, select { font: inherit; color: var(--text); background: var(--card); border: 1px solid var(--line);
                border-radius: 8px; padding: 5px 9px; }
input[type=search] { flex: 1 1 200px; }
label.chk { display: flex; gap: 6px; align-items: center; color: var(--muted); }
main { display: grid; gap: 12px; padding: 12px 0 24px; grid-template-columns: repeat(4, minmax(0, 1fr)); align-items: start; }
@media (max-width: 1250px) { main { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 940px)  { main { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 620px)  { main { grid-template-columns: minmax(0, 1fr); } }
.store { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 12px;
         display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.hd { display: flex; gap: 8px; align-items: baseline; min-width: 0; }
.rank { font-weight: 700; color: var(--muted); }
.hd h2 { margin: 0; font-size: 15px; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hd h2 a { color: var(--text); text-decoration: none; }
.hd h2 a:hover { text-decoration: underline; }
.links { display: flex; gap: 10px; font-size: 12px; }
.links a { color: var(--accent); text-decoration: none; }
.links a:hover { text-decoration: underline; }
.chips { display: flex; flex-wrap: wrap; gap: 4px; }
.chip { background: var(--chip); border-radius: 999px; padding: 1px 8px; font-size: 11.5px; color: var(--muted); white-space: nowrap; }
.chip b { color: var(--text); font-weight: 600; }
.rev { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid var(--line); border-radius: 8px; }
.rev > div { padding: 6px 8px; min-width: 0; }
.rev > div + div { border-left: 1px solid var(--line); }
.rev .l { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
.rev .v { font-size: 15px; font-weight: 700; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rev .c { font-size: 11px; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.up { color: var(--up); } .down { color: var(--down); }
.chart img { width: 100%; height: auto; display: block; border-radius: 8px; border: 1px solid var(--line); cursor: zoom-in; }
.kv { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 4px 10px; }
.kv div { min-width: 0; }
.kv .l { font-size: 11px; color: var(--muted); }
.kv .v { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ads { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; }
.ad { min-width: 0; font-size: 11px; color: var(--muted); text-align: center; }
.ad img { width: 100%; aspect-ratio: 2 / 3; object-fit: cover; object-position: top; display: block;
          border-radius: 6px; border: 1px solid var(--line); background: var(--chip); cursor: zoom-in; }
.ad a { color: var(--accent); text-decoration: none; }
.body { color: var(--muted); font-size: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.note { color: var(--muted); font-size: 12px; }
.err { color: var(--down); font-size: 12px; }
.sec { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; margin-bottom: 2px; }
.pager { display: flex; gap: 8px; align-items: center; justify-content: center; padding: 4px 0 28px; color: var(--muted); }
.pager button { font: inherit; color: var(--text); background: var(--card); border: 1px solid var(--line);
                border-radius: 8px; padding: 5px 12px; cursor: pointer; }
.pager button:disabled { opacity: .4; cursor: default; }
.empty { grid-column: 1 / -1; text-align: center; color: var(--muted); padding: 40px; }
.c-info, .c-rev, .c-chart, .c-ov, .c-ads { min-width: 0; display: flex; flex-direction: column; gap: 8px; }
.c-ov:empty, .c-ads:empty, .c-chart:empty { display: none; }
.thead { display: none; }
@media (min-width: 1151px) {
  body.rows main { grid-template-columns: minmax(0, 1fr); gap: 8px; }
  body.rows .thead { display: grid; position: sticky; top: 49px; z-index: 4; background: var(--bg);
    padding: 6px 12px 4px; font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
  body.rows .store, body.rows .thead { grid-template-columns: 230px 270px minmax(260px, 1fr) 220px 250px; column-gap: 16px; }
  body.rows .store { display: grid; align-items: start; padding: 10px 12px; }
  body.rows .c-ov:empty, body.rows .c-ads:empty, body.rows .c-chart:empty { display: flex; }
  body.rows .c-chart img { max-height: 190px; width: auto; max-width: 100%; }
  body.rows .rev { grid-template-columns: minmax(0, 1fr); }
  body.rows .rev > div { display: grid; grid-template-columns: 56px auto minmax(0, 1fr); align-items: baseline; gap: 10px; }
  body.rows .rev > div + div { border-left: 0; border-top: 1px solid var(--line); }
  body.rows .rev .c { text-align: right; }
  body.rows .c-ov .sec, body.rows .c-ads .sec { display: none; }
  body.rows .ads { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
dialog { border: 0; padding: 0; background: transparent; max-width: 96vw; }
dialog img { max-width: 96vw; max-height: 92vh; border-radius: 8px; display: block; }
dialog::backdrop { background: rgba(0,0,0,.78); }
</style>
</head>
<body>
<div class="wrap"><header>
  <h1>Ads Finder Report</h1>
  <div class="sub" id="sub"></div>
</header></div>
<div class="bar"><div class="wrap">
  <input type="search" id="q" placeholder="Tìm store, page, nội dung ad...">
  <select id="kw"><option value="">Tất cả từ khóa</option></select>
  <select id="sort">
    <option value="revenue">Sắp xếp: doanh thu tháng</option>
    <option value="ads">Sắp xếp: số ad</option>
    <option value="days">Sắp xếp: chạy lâu nhất</option>
  </select>
  <select id="view">
    <option value="rows">Hiển thị: mỗi store 1 dòng</option>
    <option value="grid">Hiển thị: lưới 4 cột</option>
  </select>
  <select id="per">
    <option value="25">25 store / trang</option>
    <option value="50">50 store / trang</option>
    <option value="100">100 store / trang</option>
    <option value="0">Tất cả</option>
  </select>
  <label class="chk"><input type="checkbox" id="onlysh" checked> Chỉ store có dữ liệu ShopHunter</label>
  <span class="sub" id="count"></span>
</div></div>
<div class="wrap"><div class="thead"><div>Store</div><div>Doanh thu</div><div>Revenue Trends</div><div>Store Overview</div><div>Ads</div></div>
<main id="list"></main>
<nav class="pager" id="pager"></nav></div>
<dialog id="zoom"><img alt=""></dialog>
<script type="application/json" id="data">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = (v) => v == null ? '—' : '$' + (v >= 1e6 ? (v/1e6).toFixed(1) + 'M' : v >= 1e3 ? (v/1e3).toFixed(1) + 'K' : v.toFixed(0));
const trend = (c) => /^\s*[-−▼↓]/.test(c) ? 'down' : /^\s*[+▲↑]/.test(c) ? 'up' : '';

const KW = DATA.meta.keywords;
$('#sub').textContent = `${DATA.meta.label} · ${KW.length} từ khóa: ${KW.slice(0, 8).join(', ')}${KW.length > 8 ? '…' : ''} · ${DATA.meta.country} · ${DATA.meta.generated} · ${DATA.stores.length} store Shopify`;
$('#sub').title = KW.join(', ');
let page = 1;
for (const k of DATA.meta.keywords) $('#kw').insertAdjacentHTML('beforeend', `<option>${esc(k)}</option>`);

function revenueBlock(rows) {
  const pick = ['Day', 'Week', 'Month'].map(k => rows.find(r => r[0].toLowerCase().includes(k.toLowerCase())));
  const cells = pick.every(Boolean) ? pick : rows.filter(r => r[0]).slice(0, 3);
  if (!cells.length) return '';
  return '<div class="rev">' + cells.map(([l, v, c]) =>
    `<div><div class="l">${esc(l)}</div><div class="v" title="${esc(v)}">${esc(v)}</div>` +
    `<div class="c ${trend(c || '')}" title="${esc(c)}">${esc(c || ' ')}</div></div>`).join('') + '</div>';
}

function kvBlock(title, rows) {
  const items = rows.filter(r => r[0]);
  if (!items.length) return '';
  return `<div><div class="sec">${esc(title)}</div><div class="kv">` + items.map(([l, v, c]) =>
    `<div><div class="l">${esc(l)}</div><div class="v" title="${esc(v)} ${esc(c)}">${esc(v)}${c ? ` <span class="${trend(c)}">${esc(c)}</span>` : ''}</div></div>`).join('') +
    '</div></div>';
}

function shParts(s) {
  const sh = s.sh;
  const parts = {rev: '', chart: '', ov: ''};
  if (!sh) { parts.rev = '<p class="note">Chưa tra ShopHunter (vượt giới hạn số store mỗi lượt).</p>'; return parts; }
  const revName = DATA.meta.boxes.find(b => /revenue/i.test(b) && !DATA.meta.image_boxes.includes(b) && sh.boxes[b]);
  if (revName) parts.rev = revenueBlock(sh.boxes[revName]);
  for (const [b, img] of Object.entries(sh.images))
    parts.chart += `<img loading="lazy" src="${esc(img)}" alt="${esc(b)} ${esc(s.domain)}" data-zoom>`;
  for (const b of DATA.meta.boxes)
    if (b !== revName && sh.boxes[b] && !sh.images[b]) parts.ov += kvBlock(b, sh.boxes[b]);
  if (sh.error) parts.ov += `<p class="err">${esc(sh.error)}</p>`;
  return parts;
}

function card(s, i) {
  const shots = s.ads.filter(a => a.img).slice(0, 4).map(a => `
    <div class="ad"><img loading="lazy" src="${esc(a.img)}" alt="Ad ${esc(a.id)}" data-zoom>
      <a href="https://www.facebook.com/ads/library/?id=${esc(a.id)}" target="_blank" rel="noopener">${a.days != null ? a.days + 'n' : 'Ad'}</a></div>`).join('');
  const p = shParts(s);
  return `<section class="store">
    <div class="c-info">
      <div class="hd"><span class="rank">#${i + 1}</span>
        <h2 title="${esc(s.domain)}"><a href="${esc(s.store_url || 'https://' + s.domain)}" target="_blank" rel="noopener">${esc(s.domain)}</a></h2>
      </div>
      <div class="links">${s.sh && s.sh.shop_url ? `<a href="${esc(s.sh.shop_url)}" target="_blank" rel="noopener">ShopHunter</a>` : ''}
        ${s.link ? `<a href="${esc(s.link)}" target="_blank" rel="noopener">Trang ad</a>` : ''}</div>
      <div class="chips">
        <span class="chip">Tháng <b>${money(s.revenue)}</b></span>
        <span class="chip">Ads <b>${s.ads_count}</b></span>
        <span class="chip">Lâu nhất <b>${s.days ?? '—'} ngày</b></span>
        ${s.versions > s.ads_count ? `<span class="chip">Phiên bản <b>${s.versions}</b></span>` : ''}
      </div>
      ${s.pages.length ? `<div class="note">Page: ${esc(s.pages.join(', '))}</div>` : ''}
      ${s.body ? `<div class="body" title="${esc(s.body)}">“${esc(s.body)}”</div>` : ''}
    </div>
    <div class="c-rev">${p.rev}</div>
    <div class="c-chart chart">${p.chart}</div>
    <div class="c-ov">${p.ov}</div>
    <div class="c-ads">${shots ? `<div class="sec">Ads (${s.ads_count})</div><div class="ads">${shots}</div>` : ''}</div>
  </section>`;
}

function render() {
  document.body.classList.toggle('rows', $('#view').value === 'rows');
  try { localStorage.setItem('af-view', $('#view').value); } catch (e) {}
  const q = $('#q').value.toLowerCase(), kw = $('#kw').value, only = $('#onlysh').checked, sort = $('#sort').value;
  let list = DATA.stores.filter(s =>
    (!kw || s.keywords.includes(kw)) &&
    (!only || (s.sh && s.sh.status === 'ok')) &&
    (!q || (s.domain + ' ' + s.pages.join(' ') + ' ' + s.body).toLowerCase().includes(q)));
  const key = { revenue: s => s.revenue ?? -1, ads: s => s.ads_count, days: s => s.days ?? -1 }[sort];
  list.sort((a, b) => key(b) - key(a) || b.ads_count - a.ads_count);
  const per = +$('#per').value || list.length || 1;
  const pages = Math.max(1, Math.ceil(list.length / per));
  page = Math.min(page, pages);
  const start = (page - 1) * per;
  $('#count').textContent = `${list.length} / ${DATA.stores.length} store`;
  $('#list').innerHTML = list.length
    ? list.slice(start, start + per).map((s, i) => card(s, start + i)).join('')
    : '<div class="empty">Không có store nào khớp bộ lọc.</div>';
  $('#pager').innerHTML = pages > 1
    ? `<button data-go="-1" ${page === 1 ? 'disabled' : ''}>‹ Trước</button> Trang ${page} / ${pages} <button data-go="1" ${page === pages ? 'disabled' : ''}>Sau ›</button>`
    : '';
}
$('#pager').addEventListener('click', e => {
  const b = e.target.closest('[data-go]');
  if (!b) return;
  page += +b.dataset.go;
  render();
  window.scrollTo({top: 0});
});
try {
  const v = localStorage.getItem('af-view'); if (v) $('#view').value = v;
  const n = localStorage.getItem('af-per'); if (n) $('#per').value = n;
} catch (e) {}
['q', 'kw', 'sort', 'onlysh', 'per'].forEach(id => $('#' + id).addEventListener('input', () => { page = 1; render(); }));
$('#view').addEventListener('input', render);
$('#per').addEventListener('input', () => { try { localStorage.setItem('af-per', $('#per').value); } catch (e) {} });
document.addEventListener('click', e => {
  if (e.target.matches('[data-zoom]')) { const d = $('#zoom'); d.querySelector('img').src = e.target.src; d.showModal(); }
  else if (e.target.closest('dialog')) $('#zoom').close();
});
render();
</script>
</body>
</html>
"""
