"""Store checks must never hang: servers that stall or drip bytes forever."""
import socket
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from adsfinder import config, stores
from adsfinder.db import DB


class Slow(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path.startswith("/shopify"):
            body = b'<html><script src="https://cdn.shopify.com/a.js"></script>' + b"x" * 8000 + b"</html>"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/drip"):
            self.send_response(200)
            self.end_headers()
            try:
                for _ in range(600):           # one byte a second for 10 minutes
                    self.wfile.write(b"x")
                    self.wfile.flush()
                    time.sleep(1)
            except OSError:
                pass
        else:                                   # /stall: never answer
            time.sleep(600)

    def log_message(self, *a):
        pass


class StoreCheckTests(unittest.TestCase):
    def setUp(self):
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Slow)
        self.srv.daemon_threads = True
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.srv.shutdown()
        self.tmp.cleanup()

    def test_stalled_servers_do_not_block(self):
        cfg = config.load()
        cfg.update(store_check_timeout=3, store_check_workers=4)
        db = DB(self.tmp.name)
        groups = {
            "ok.example": [{"link_url": self.base + "/shopify"}],
            "stall.example": [{"link_url": self.base + "/stall"}],
            "drip.example": [{"link_url": self.base + "/drip"}],
        }
        t0 = time.monotonic()
        info = stores.resolve_all(db, groups, cfg, context=None)
        self.assertLess(time.monotonic() - t0, 10)
        self.assertEqual(info["ok.example"]["is_shopify"], 1)
        self.assertIsNone(info["stall.example"]["is_shopify"])
        self.assertIn(info["drip.example"]["is_shopify"], (None, 0))


if __name__ == "__main__":
    unittest.main()
