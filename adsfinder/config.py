"""Load settings from config.json, falling back to defaults."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    # Meta Ad Library
    "adlibrary_url": "https://www.facebook.com/ads/library/",
    "country": "US",
    "keywords": [],
    "search_type": "keyword_unordered",  # or "keyword_exact_phrase"
    "media_type": "video",               # "all", "image", "video"
    "max_ads_per_keyword": 40,
    "min_days_running": 0,               # skip ads younger than this
    # Chrome you start with start-chrome.bat
    "cdp_url": "http://127.0.0.1:9222",
    # ShopHunter
    "shophunter_track_url": "https://app.shophunter.io/shops/track",
    "shophunter_collections_url": "https://app.shophunter.io/collections/shops",
    "shophunter_wait_seconds": 180,      # how long to wait for "Tracked"
    "shophunter_cache_hours": 24,        # reuse results younger than this
    "max_stores_per_run": 15,
    "shophunter_boxes": ["Store Overview", "Revenue Performance", "Revenue Trends"],
    "shophunter_image_boxes": ["Revenue Trends"],
    # Pacing between actions, seconds [min, max]
    "delay_seconds": [2, 5],
    "store_check_hours": 72,
    "exclude_domains": [
        "facebook.com", "fb.com", "fb.me", "instagram.com", "messenger.com",
        "whatsapp.com", "amazon.com", "amzn.to", "walmart.com", "ebay.com",
        "etsy.com", "tiktok.com", "youtube.com", "google.com", "apple.com",
        "linktr.ee", "bit.ly",
    ],
    "data_dir": "data",
    "reports_dir": "reports",
    "open_report": True,
}


def load(path=None):
    cfg = dict(DEFAULTS)
    p = Path(path) if path else ROOT / "config.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            cfg.update(json.load(f))
    cfg["data_dir"] = str((ROOT / cfg["data_dir"]).resolve())
    cfg["reports_dir"] = str((ROOT / cfg["reports_dir"]).resolve())
    return cfg
