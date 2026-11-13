"""SQLite storage for ads, stores, ShopHunter results and runs."""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS ads (
    library_id TEXT PRIMARY KEY,
    keywords TEXT,
    country TEXT,
    page_name TEXT,
    page_url TEXT,
    started TEXT,
    versions INTEGER,
    body TEXT,
    video_url TEXT,
    poster_url TEXT,
    link_url TEXT,
    domain TEXT,
    shot_path TEXT,
    scraped_at TEXT
);
CREATE TABLE IF NOT EXISTS stores (
    domain TEXT PRIMARY KEY,
    final_url TEXT,
    is_shopify INTEGER,
    checked_at TEXT,
    note TEXT
);
CREATE TABLE IF NOT EXISTS shophunter (
    domain TEXT PRIMARY KEY,
    status TEXT,
    shop_url TEXT,
    boxes_json TEXT,
    images_json TEXT,
    error TEXT,
    fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT,
    keywords TEXT,
    report_path TEXT
);
CREATE TABLE IF NOT EXISTS run_ads (
    run_id INTEGER,
    library_id TEXT,
    keyword TEXT,
    PRIMARY KEY (run_id, library_id, keyword)
);
"""


def now():
    return datetime.now().isoformat(timespec="seconds")


class DB:
    def __init__(self, data_dir):
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(Path(data_dir) / "adsfinder.db"))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    # runs
    def start_run(self, keywords):
        cur = self.conn.execute(
            "INSERT INTO runs (started_at, keywords) VALUES (?, ?)", (now(), json.dumps(keywords))
        )
        self.conn.commit()
        return cur.lastrowid

    def finish_run(self, run_id, report_path):
        self.conn.execute("UPDATE runs SET report_path=? WHERE id=?", (str(report_path), run_id))
        self.conn.commit()

    def get_run(self, run_id=None):
        if run_id:
            return self.conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        return self.conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()

    # ads
    def save_ad(self, run_id, keyword, ad):
        old = self.conn.execute(
            "SELECT keywords FROM ads WHERE library_id=?", (ad["library_id"],)
        ).fetchone()
        kws = set(json.loads(old["keywords"])) if old else set()
        kws.add(keyword)
        self.conn.execute(
            """INSERT OR REPLACE INTO ads (library_id, keywords, country, page_name, page_url,
               started, versions, body, video_url, poster_url, link_url, domain, shot_path, scraped_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ad["library_id"], json.dumps(sorted(kws)), ad.get("country"), ad.get("page_name"),
                ad.get("page_url"), ad.get("started"), ad.get("versions"), ad.get("body"),
                ad.get("video_url"), ad.get("poster_url"), ad.get("link_url"), ad.get("domain"),
                ad.get("shot_path"), now(),
            ),
        )
        self.conn.execute(
            "INSERT OR IGNORE INTO run_ads (run_id, library_id, keyword) VALUES (?,?,?)",
            (run_id, ad["library_id"], keyword),
        )
        self.conn.commit()

    def run_ads(self, run_id):
        return self.conn.execute(
            """SELECT a.*, GROUP_CONCAT(r.keyword, '|') AS run_keywords
               FROM run_ads r JOIN ads a ON a.library_id = r.library_id
               WHERE r.run_id=? GROUP BY a.library_id""",
            (run_id,),
        ).fetchall()

    # stores
    def get_store(self, domain, max_age_hours=None):
        row = self.conn.execute("SELECT * FROM stores WHERE domain=?", (domain,)).fetchone()
        if row and max_age_hours is not None and _older(row["checked_at"], max_age_hours):
            return None
        return row

    def save_store(self, domain, final_url, is_shopify, note=""):
        self.conn.execute(
            "INSERT OR REPLACE INTO stores (domain, final_url, is_shopify, checked_at, note) VALUES (?,?,?,?,?)",
            (domain, final_url, 1 if is_shopify else 0 if is_shopify is False else None, now(), note),
        )
        self.conn.commit()

    # shophunter
    def get_shophunter(self, domain, max_age_hours=None):
        row = self.conn.execute("SELECT * FROM shophunter WHERE domain=?", (domain,)).fetchone()
        if row and max_age_hours is not None and _older(row["fetched_at"], max_age_hours):
            return None
        return row

    def save_shophunter(self, domain, result):
        self.conn.execute(
            """INSERT OR REPLACE INTO shophunter (domain, status, shop_url, boxes_json, images_json, error, fetched_at)
               VALUES (?,?,?,?,?,?,?)""",
            (
                domain, result.get("status"), result.get("shop_url"),
                json.dumps(result.get("boxes") or {}, ensure_ascii=False),
                json.dumps(result.get("images") or {}), result.get("error"), now(),
            ),
        )
        self.conn.commit()


def _older(ts, hours):
    try:
        return datetime.fromisoformat(ts) < datetime.now() - timedelta(hours=hours)
    except (TypeError, ValueError):
        return True
