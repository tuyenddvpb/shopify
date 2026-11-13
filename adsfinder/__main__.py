"""Command line: python -m adsfinder run "keyword 1" "keyword 2"."""
import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path

from . import config as config_mod
from .db import DB
from . import util
from .util import Watch, domain_of, log, pause


def _open(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # noqa: S606 - opening our own report
        else:
            webbrowser.open(Path(path).resolve().as_uri())
    except Exception:  # noqa: BLE001
        pass


def read_keywords(path):
    """One keyword per line; blank lines and lines starting with # are skipped."""
    p = Path(path)
    if not p.exists():
        sys.exit(f"Không thấy file từ khóa: {p}")
    out = []
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def gather_keywords(args, cfg, use_config=True):
    kws = list(args.keywords or [])
    path = args.file or (cfg.get("keywords_file") if use_config and not kws else None)
    if path:
        p = Path(path)
        kws += read_keywords(p if p.exists() or p.is_absolute() else config_mod.ROOT / p)
    if not kws and use_config:
        kws = list(cfg["keywords"])
    return list(dict.fromkeys(k.strip() for k in kws if k.strip()))  # dedupe, keep order


def cmd_run(args, cfg):
    from playwright.sync_api import sync_playwright

    from . import adlibrary, shophunter, stores
    from .browser import connect

    keywords = gather_keywords(args, cfg, use_config=not args.resume)
    # options given on the command line; remembered per run so --resume keeps them
    given = {}
    if args.max_ads:
        given["max_ads_per_keyword"] = args.max_ads
    if args.max_stores is not None:
        given["max_stores_per_run"] = args.max_stores
    if getattr(args, "no_chrome_check", False):
        given["store_check_chrome"] = False

    data = Path(cfg["data_dir"])
    util.DEBUG_DIR = data / "debug"
    db = DB(data)
    done = set()
    if args.resume:
        last = db.get_run()
        if not last:
            sys.exit("Chưa có lượt nào để chạy tiếp.")
        run_id = last["id"]
        old = json.loads(last["keywords"])
        keywords = list(dict.fromkeys(old + keywords))
        db.set_run_keywords(run_id, keywords)
        done = db.done_keywords(run_id)
        options = {**db.run_options(run_id), **given}
        db.set_run_options(run_id, options)
        log(f"Chạy tiếp lượt #{run_id}: {len(done)}/{len(keywords)} từ khóa đã xong.")
    else:
        if not keywords:
            sys.exit('Chưa có từ khóa. Ví dụ: python -m adsfinder run "posture corrector" '
                     'hoặc python -m adsfinder run --file keywords.txt')
        options = given
        run_id = db.start_run(keywords, options)
        log(f"Bắt đầu lượt #{run_id}: {len(keywords)} từ khóa")
    cfg.update(options)
    if options:
        log("Tùy chọn: " + ", ".join(f"{k}={v}" for k, v in options.items()))

    try:
        with sync_playwright() as p:
            _browser, context = connect(p, cfg)
            page = context.new_page()
            try:
                # 1. Ad Library
                todo_kw = [k for k in keywords if k not in done]
                for i, kw in enumerate(todo_kw, 1):
                    log(f"[{len(done) + i}/{len(keywords)}]")
                    try:
                        with Watch(f"Ad Library '{kw}'"):
                            ads = adlibrary.search(page, kw, cfg, data / "shots", data / "debug")
                    except Exception as e:  # noqa: BLE001
                        log(f"  Lỗi khi tìm '{kw}': {e} (chạy lại với --resume để thử lại)")
                        continue
                    for ad in ads:
                        db.save_ad(run_id, kw, ad)
                    db.mark_keyword_done(run_id, kw, len(ads))
                    pause(cfg)

                # 2. Stores (every ad of this run, including earlier sessions when resuming)
                groups = stores.group_by_store(db.run_ads(run_id), cfg["exclude_domains"])
                if not groups:
                    log("Không có store nào để kiểm tra: không đọc được ad nào có link store. "
                        "Xem ảnh và HTML trong data/debug/ rồi gửi lại để sửa.")
                log(f"Kiểm tra {len(groups)} store...")
                info = stores.resolve_all(db, groups, cfg, context)

                # 3. ShopHunter
                if args.no_shophunter:
                    log("Bỏ qua ShopHunter (--no-shophunter).")
                else:
                    todo = [d for d in groups if info[d]["is_shopify"] != 0]
                    fresh = [] if args.refresh else [
                        d for d in todo if db.get_shophunter(d, cfg["shophunter_cache_hours"])]
                    left = [d for d in todo if d not in fresh]
                    limit = cfg["max_stores_per_run"]
                    log(f"ShopHunter: {len(todo)} store Shopify, {len(fresh)} đã có dữ liệu, "
                        f"cần tra {len(left)}, lần này tra tối đa {limit}.")
                    done = 0
                    for d in left:
                        if done >= limit:
                            log(f"Đã tra {done} store, chạm giới hạn {limit} (max_stores_per_run). "
                                f"Còn {len(left) - done} store chưa tra: chạy "
                                f"'python -m adsfinder run --resume --max-stores N' để tra tiếp.")
                            break
                        target = domain_of(info[d]["final_url"] or "") or d
                        log(f"ShopHunter: {target} ({len(groups[d])} ad)")
                        with Watch(f"ShopHunter {target}", dump_after=cfg["shophunter_wait_seconds"] + 120):
                            res = shophunter.analyze(context, target, cfg, data / "shophunter", data / "debug",
                                                     myshopify=info[d].get("myshopify") or "")
                        db.save_shophunter(d, res)
                        log(f"  -> {res['status']}" + (f" ({res['error']})" if res.get("error") else ""))
                        done += 1
                        pause(cfg)
            finally:
                try:
                    page.close()
                except Exception:  # noqa: BLE001
                    pass
    except KeyboardInterrupt:
        log("Đã dừng giữa chừng, vẫn xuất report với dữ liệu đã có.")

    from . import report
    path = report.build(db, run_id, cfg)
    log(f"Report: {path}")
    if cfg.get("open_report") and not args.no_open:
        _open(path)


def cmd_report(args, cfg):
    from . import report

    db = DB(cfg["data_dir"])
    if args.days:
        ids = db.runs_since(args.days)
        if not ids:
            sys.exit(f"Không có lượt nào trong {args.days} ngày qua.")
        label = f"{args.days} ngày qua ({len(ids)} lượt)"
    else:
        run = db.get_run(args.run)
        if not run:
            sys.exit("Chưa có lượt chạy nào." if not args.run else f"Không có lượt #{args.run}.")
        ids, label = run["id"], None
    path = report.build(db, ids, cfg, embed=args.embed, label=label)
    log(f"Report: {path}")
    if not args.no_open:
        _open(path)


def cmd_check(args, cfg):
    from playwright.sync_api import sync_playwright

    from .browser import connect

    with sync_playwright() as p:
        _b, context = connect(p, cfg)
        for pg in context.pages:
            print(" -", pg.url)
    print("Kết nối Chrome OK.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="adsfinder", description="Meta Ad Library -> store -> ShopHunter -> HTML report")
    ap.add_argument("--config", help="đường dẫn config.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="chạy đủ các bước")
    r.add_argument("keywords", nargs="*", help="từ khóa (mặc định lấy trong config.json)")
    r.add_argument("--file", "-f", help="file từ khóa, mỗi dòng một từ (vd keywords.txt)")
    r.add_argument("--resume", action="store_true",
                   help="chạy tiếp lượt gần nhất, bỏ qua từ khóa đã xong (có thể thêm từ khóa mới)")
    r.add_argument("--max-ads", type=int, help="số ad tối đa mỗi từ khóa")
    r.add_argument("--max-stores", type=int, help="số store tối đa tra ShopHunter")
    r.add_argument("--no-shophunter", action="store_true", help="chỉ lấy ads, không tra ShopHunter")
    r.add_argument("--no-chrome-check", action="store_true",
                   help="không mở Chrome khi kiểm tra store lỗi (store đó ghi 'chưa rõ')")
    r.add_argument("--refresh", action="store_true", help="tra lại ShopHunter dù đã có dữ liệu gần đây")
    r.add_argument("--no-open", action="store_true", help="không tự mở report")
    r.set_defaults(func=cmd_run)

    rp = sub.add_parser("report", help="xuất lại report của một lượt")
    rp.add_argument("--run", type=int, help="số lượt (mặc định lượt mới nhất)")
    rp.add_argument("--days", type=int, help="gộp mọi lượt trong N ngày qua vào một report")
    emb = rp.add_mutually_exclusive_group()
    emb.add_argument("--embed", dest="embed", action="store_true", default=None,
                     help="nhúng ảnh vào file HTML (một file duy nhất, dễ gửi)")
    emb.add_argument("--no-embed", dest="embed", action="store_false",
                     help="lưu ảnh ra reports/assets/ (file HTML nhẹ, mở nhanh)")
    rp.add_argument("--no-open", action="store_true")
    rp.set_defaults(func=cmd_report)

    c = sub.add_parser("check", help="kiểm tra kết nối Chrome")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args(argv)
    cfg = config_mod.load(args.config)
    args.func(args, cfg)


if __name__ == "__main__":
    main()
