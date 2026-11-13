import unittest
from datetime import date

from adsfinder import adlibrary, config, stores
from adsfinder.textparse import box_pairs
from adsfinder.util import days_since, domain_of, money_to_float, parse_fb_date, unwrap_fb_link


class UtilTests(unittest.TestCase):
    def test_unwrap_and_domain(self):
        u = unwrap_fb_link("https://l.facebook.com/l.php?u=https%3A%2F%2Fwww.shop.com%2Fproducts%2Fa%3Fx%3D1&h=z")
        self.assertEqual(u, "https://www.shop.com/products/a?x=1")
        self.assertEqual(domain_of(u), "shop.com")
        self.assertEqual(unwrap_fb_link("https://shop.com/a"), "https://shop.com/a")

    def test_dates(self):
        self.assertEqual(parse_fb_date("Nov 2, 2026"), date(2026, 11, 2))
        self.assertEqual(parse_fb_date("September 12, 2026"), date(2026, 9, 12))
        self.assertIsNone(parse_fb_date("yesterday"))
        self.assertEqual(parse_fb_date("2 Th11, 2026"), date(2026, 11, 2))
        self.assertEqual(parse_fb_date("2 thg 11, 2026"), date(2026, 11, 2))
        self.assertEqual(parse_fb_date("ngày 2 tháng 11 năm 2026"), date(2026, 11, 2))
        self.assertEqual(days_since("2026-11-01", today=date(2026, 11, 13)), 12)

    def test_money(self):
        self.assertEqual(money_to_float("$45.2K"), 45200)
        self.assertEqual(money_to_float("$1,204,000"), 1204000)
        self.assertEqual(money_to_float("$1.5M / mo"), 1_500_000)
        self.assertIsNone(money_to_float("n/a"))


class ParseTests(unittest.TestCase):
    def test_box_pairs_label_first(self):
        text = "Revenue Performance\nMonthly Revenue\n$45.2K\n+12%\nDaily Revenue\n$1,507\nStatus: Active\nGrowing fast"
        self.assertEqual(
            box_pairs(text, "Revenue Performance"),
            [["Monthly Revenue", "$45.2K", "+12%"], ["Daily Revenue", "$1,507", ""], ["Status", "Active", ""],
             ["", "Growing fast", ""]],
        )

    def test_box_pairs_value_first(self):
        # what ShopHunter's View Shop page actually prints
        text = ("Revenue Performance\n$2197.60\n+109.7 (+5.3%)\nDay\n$15K\n-40K (-71.5%)\nWeek\n"
                "$159K\n-6747.1 (-4%)\nMonth")
        self.assertEqual(box_pairs(text, "Revenue Performance"), [
            ["Day", "$2197.60", "+109.7 (+5.3%)"], ["Week", "$15K", "-40K (-71.5%)"], ["Month", "$159K", "-6747.1 (-4%)"]])
        text = "Store Overview\nUS\nCountry\n6/12/2024\nStore Creation Date\n9\nSKUs\n7 users\nTracked by"
        self.assertEqual(box_pairs(text, "Store Overview"), [
            ["Country", "US", ""], ["Store Creation Date", "6/12/2024", ""], ["SKUs", "9", ""], ["Tracked by", "7 users", ""]])

    def test_revenue_pick(self):
        from adsfinder.report import _revenue
        self.assertEqual(_revenue({"Revenue Performance": [["Day", "$2197.60", ""], ["Week", "$15K", ""], ["Month", "$159K", ""]]}), 159000)
        self.assertAlmostEqual(_revenue({"Revenue Performance": [["Day", "$100", ""]]}), 3000)

    def test_shopify_detection(self):
        self.assertTrue(stores.shopify_in('<script src="https://cdn.shopify.com/x.js">', {}))
        self.assertTrue(stores.shopify_in("", {"X-ShopId": "123"}))
        self.assertFalse(stores.shopify_in("<html>wordpress</html>", {}))

    def test_normalize_skips_excluded_links(self):
        cfg = config.load()
        ad = adlibrary.normalize({
            "library_id": "1", "started_text": "Nov 1, 2026", "versions": 2,
            "links": ["https://www.amazon.com/dp/1", "https://l.facebook.com/l.php?u=https%3A%2F%2Fwww.cool.shop%2Fp"],
        }, cfg)
        self.assertEqual(ad["domain"], "cool.shop")
        self.assertEqual(ad["started"], "2026-11-01")

    def test_group_by_store(self):
        ads = [{"domain": "a.com"}, {"domain": "b.com"}, {"domain": "b.com"}, {"domain": ""}]
        self.assertEqual(list(stores.group_by_store(ads, [])), ["b.com", "a.com"])


class KeywordFileTests(unittest.TestCase):
    def test_read_and_gather(self):
        import tempfile
        from argparse import Namespace
        from pathlib import Path

        from adsfinder.__main__ import gather_keywords, read_keywords

        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "kw.txt"
            f.write_text("\ufeff# my list\nposture corrector\n\n  neck massager  \nposture corrector\n", encoding="utf-8")
            self.assertEqual(read_keywords(f), ["posture corrector", "neck massager", "posture corrector"])
            cfg = {"keywords": ["from config"], "keywords_file": ""}
            args = Namespace(keywords=["knee brace"], file=str(f))
            self.assertEqual(gather_keywords(args, cfg), ["knee brace", "posture corrector", "neck massager"])
            self.assertEqual(gather_keywords(Namespace(keywords=[], file=None), cfg), ["from config"])
            self.assertEqual(gather_keywords(Namespace(keywords=[], file=None), cfg, use_config=False), [])


if __name__ == "__main__":
    unittest.main()
