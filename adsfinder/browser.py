"""Attach to the Chrome window started by start-chrome.bat."""
import sys
from datetime import datetime
from pathlib import Path

from .util import log

HELP = """
Không kết nối được Chrome ở {url}.

Cách sửa:
  1. Tắt hết cửa sổ Chrome đang mở bằng start-chrome.bat (nếu có).
  2. Bấm đúp start-chrome.bat trong thư mục app để mở Chrome có cổng điều khiển.
  3. Lần đầu: đăng nhập Facebook và ShopHunter trong cửa sổ Chrome đó.
  4. Chạy lại lệnh.
"""


def connect(playwright, cfg):
    url = cfg["cdp_url"]
    try:
        browser = playwright.chromium.connect_over_cdp(url, timeout=15000)
    except Exception as e:  # noqa: BLE001 - show a friendly message for any connect error
        print(HELP.format(url=url), file=sys.stderr)
        print(f"Chi tiết lỗi: {e}", file=sys.stderr)
        sys.exit(2)
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    log(f"Đã kết nối Chrome ({len(context.pages)} tab đang mở).")
    return browser, context


def dump_debug(page, debug_dir, name):
    """Save a screenshot and the HTML of a page so selectors can be fixed later."""
    try:
        Path(debug_dir).mkdir(parents=True, exist_ok=True)
        stem = Path(debug_dir) / f"{datetime.now():%Y%m%d-%H%M%S}-{_safe(name)}"
        page.screenshot(path=f"{stem}.png", full_page=True)
        Path(f"{stem}.html").write_text(page.content(), encoding="utf-8")
        log(f"  Đã lưu ảnh và HTML để kiểm tra: {stem}.png")
    except Exception as e:  # noqa: BLE001
        log(f"  Không lưu được file debug: {e}")


def _safe(name):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:60]
