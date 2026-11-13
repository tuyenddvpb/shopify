"""Runs the whole pipeline against fake Ad Library / store / ShopHunter pages.

Needs Playwright and a Chromium binary: set CHROME_BIN or it is skipped.
"""
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from argparse import Namespace
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FIX = Path(__file__).parent / "fixtures"
CHROME = os.environ.get("CHROME_BIN", "")

ROUTES = {
    "/ads/library/": "adlib.html",
    "/store": "store.html",
    "/shops/track": "track.html",
    "/collections/shops": "collections.html",
    "/shop/": "shop.html",
}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        path = self.path.split("?")[0]
        for prefix, name in ROUTES.items():
            if path.startswith(prefix):
                body = (FIX / name).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
                return
        self.send_error(404)

    def log_message(self, *a):
        pass


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@unittest.skipUnless(CHROME and Path(CHROME).exists(), "CHROME_BIN not set")
class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.http.server_port}"
        self.cdp_port = free_port()
        self.chrome = subprocess.Popen(
            [CHROME, "--headless=new", "--no-sandbox", f"--remote-debugging-port={self.cdp_port}",
             f"--user-data-dir={self.tmp}/profile", "--window-size=1300,900", "--no-proxy-server",
             "--host-resolver-rules=MAP *.test 127.0.0.1", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(2)

    def tearDown(self):
        self.chrome.terminate()
        self.chrome.wait()
        self.http.shutdown()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, adlib_path, no_shophunter=False):
        from adsfinder import __main__ as cli
        from adsfinder import config
        from adsfinder.db import DB

        cfg_path = Path(self.tmp) / "config.json"
        cfg_path.write_text(json.dumps({
            "adlibrary_url": self.base + adlib_path,
            "shophunter_track_url": self.base + "/shops/track",
            "shophunter_collections_url": self.base + "/collections/shops",
            "cdp_url": f"http://127.0.0.1:{self.cdp_port}",
            "data_dir": str(Path(self.tmp) / "data"),
            "reports_dir": str(Path(self.tmp) / "reports"),
            "delay_seconds": [0, 0],
            "shophunter_wait_seconds": 30,
            "open_report": False,
        }))
        cfg = config.load(cfg_path)
        args = Namespace(keywords=["posture corrector"], max_ads=None, max_stores=None,
                         no_shophunter=no_shophunter, refresh=False, no_open=True)
        cli.cmd_run(args, cfg)
        db = DB(cfg["data_dir"])
        return db, {a["library_id"]: dict(a) for a in db.run_ads(1)}

    def test_vietnamese_ad_library(self):
        _db, ads = self._run("/ads/library/vi/", no_shophunter=True)
        self.assertEqual(len(ads), 5)
        self.assertEqual(ads["1111111111"]["started"], "2026-09-01")
        self.assertEqual(ads["1111111111"]["versions"], 3)
        self.assertEqual(ads["1111111111"]["domain"], "posture.test")
        self.assertIn("Fix your posture", ads["1111111111"]["body"])

    def test_full_run(self):
        db, ads = self._run("/ads/library/")
        self.assertEqual(len(ads), 5)
        a1 = ads["1111111111"]
        self.assertEqual(a1["started"], "2026-09-01")
        self.assertEqual(a1["versions"], 3)
        self.assertEqual(a1["page_name"], "Comfy Posture")
        self.assertEqual(a1["domain"], "posture.test")
        self.assertTrue(Path(a1["shot_path"]).exists())
        self.assertEqual(ads["3333333333"]["domain"], "")  # amazon link is excluded

        store = db.get_store("posture.test")
        self.assertEqual(store["is_shopify"], 1)
        self.assertEqual(store["myshopify"], "posture-store.myshopify.com")

        # Way 1: our Recent Activity row turns Tracked -> View Shop (not axzenia.com's row)
        sh = db.get_shophunter("posture.test")
        self.assertEqual(sh["status"], "ok", sh["error"])
        self.assertTrue(sh["shop_url"].endswith("/shop/posture.test"), sh["shop_url"])
        self.assertIsNone(sh["error"])

        # "Not a Shopify Store" (also after retrying the myshopify URL): no data, no wrong page
        zen = db.get_shophunter("zenblux.test")
        self.assertEqual(zen["status"], "rejected")
        self.assertIsNone(zen["shop_url"])

        # Way 2: Tracked but no View Shop -> found by scrolling /collections/shops
        nb = db.get_shophunter("nobtn.test")
        self.assertEqual(nb["status"], "ok", nb["error"])
        self.assertTrue(nb["shop_url"].endswith("/shop/nobtn.test"), nb["shop_url"])

        boxes = json.loads(sh["boxes_json"])
        self.assertIn(["Month", "$45.2K", "+5K (+12%)"], boxes["Revenue Performance"]["pairs"])
        self.assertIn(["Country", "US", ""], boxes["Store Overview"]["pairs"])
        self.assertIn(["SKUs", "24", ""], boxes["Store Overview"]["pairs"])
        self.assertNotIn("Top Products", boxes["Revenue Trends"]["text"])
        self.assertIn("Revenue Trends", json.loads(sh["images_json"]))

        report = Path(db.get_run(1)["report_path"])
        html = report.read_text(encoding="utf-8")
        self.assertIn("45.2K", html)
        data = json.loads(html.split('id="data">')[1].split("</script>")[0].replace("<\\/", "</"))
        self.assertEqual({s["domain"] for s in data["stores"]}, {"posture.test", "zenblux.test", "nobtn.test"})
        self.assertEqual(next(s for s in data["stores"] if s["domain"] == "posture.test")["revenue"], 45200)
        self.assertIn("data:image", html)
        if os.environ.get("REPORT_OUT"):
            shutil.copy(report, os.environ["REPORT_OUT"])


if __name__ == "__main__":
    unittest.main()
