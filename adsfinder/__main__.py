"""Command line: python -m adsfinder run "keyword 1" "keyword 2"."""
import argparse
import os
import sys
import webbrowser
from pathlib import Path

from . import config as config_mod
from .db import DB
from .util import domain_of, log, pause


def _open(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # noqa: S606 - opening our own report
        else:
            webbrowser.open(Path(path).resolve().as_uri())
    except Exception:  # noqa: BLE001
        pass


def cmd_run(args, cfg):
    from playwright.sync_api import sync_playwright

    from . import adlibrary, shophunter, stores
    from .browser import connect

    keywords = args.keywords or cfg["keywords"]
    if not keywords:
        sys.exit('Chưa có từ khóa. Ví dụ: python -m adsfinder run "posture corrector"')
    if args.max_ads:
        cfg["max_ads_per_keyword"] = args.max_ads
    if args.max_stores is not None:
        cfg["max_stores_per_run"] = args.max_stores

    data = Path(cfg["data_dir"])
    db = DB(data)
    run_id = db.start_run(keywords)
    log(f"Bắt đầu lượt #{run_id}: {', '.join(keywords)}")

    try:
        with sync_playwright() as p:
            _browser, context = connect(p, cfg)
            page = context.new_page()
            try:
                # 1. Ad Library
                all_ads = []
                for kw in keywords:
                    try:
                        ads = adlibrary.search(page, kw, cfg, data / "shots", data / "debug")
                    except Exception as e:  # noqa: BLE001
                        log(f"  Lỗi khi tìm '{kw}': {e}")
                        ads = []
                    for ad in ads:
                        db.save_ad(run_id, kw, ad)
                    all_ads += ads
                    pause(cfg)

                # 2. Stores
                groups = stores.group_by_store(all_ads, cfg["exclude_domains"])
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
                    done = 0
                    for d in todo:
                        if done >= cfg["max_stores_per_run"]:
                            log(f"Đã đủ {done} store cho lượt này (max_stores_per_run).")
                            break
                        if not args.refresh and db.get_shophunter(d, cfg["shophunter_cache_hours"]):
                            log(f"ShopHunter: {d} đã có dữ liệu gần đây, dùng lại.")
                            continue
                        target = domain_of(info[d]["final_url"] or "") or d
                        log(f"ShopHunter: {target} ({len(groups[d])} ad)")
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
    run = db.get_run(args.run)
    if not run:
        sys.exit("Chưa có lượt chạy nào.")
    path = report.build(db, run["id"], cfg)
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
    r.add_argument("--max-ads", type=int, help="số ad tối đa mỗi từ khóa")
    r.add_argument("--max-stores", type=int, help="số store tối đa tra ShopHunter")
    r.add_argument("--no-shophunter", action="store_true", help="chỉ lấy ads, không tra ShopHunter")
    r.add_argument("--refresh", action="store_true", help="tra lại ShopHunter dù đã có dữ liệu gần đây")
    r.add_argument("--no-open", action="store_true", help="không tự mở report")
    r.set_defaults(func=cmd_run)

    rp = sub.add_parser("report", help="xuất lại report của một lượt")
    rp.add_argument("--run", type=int, help="số lượt (mặc định lượt mới nhất)")
    rp.add_argument("--no-open", action="store_true")
    rp.set_defaults(func=cmd_report)

    c = sub.add_parser("check", help="kiểm tra kết nối Chrome")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args(argv)
    cfg = config_mod.load(args.config)
    args.func(args, cfg)


if __name__ == "__main__":
    main()
