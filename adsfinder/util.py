"""Small helpers shared by the pipeline steps."""
import random
import re
import time
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def pause(cfg):
    lo, hi = cfg.get("delay_seconds", [2, 5])
    time.sleep(random.uniform(lo, hi))


def wait_for_user(msg):
    print()
    print("=" * 70)
    print(msg)
    print("=" * 70)
    try:
        input("Xong thì nhấn Enter để tiếp tục... ")
    except EOFError:
        pass


def domain_of(url):
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def unwrap_fb_link(url):
    """l.facebook.com/l.php?u=<real> -> <real>."""
    try:
        u = urlparse(url)
    except ValueError:
        return url
    if (u.hostname or "").endswith("facebook.com") and u.path.startswith("/l.php"):
        real = parse_qs(u.query).get("u")
        if real:
            return real[0]
    return url


def is_excluded(domain, excluded):
    return not domain or any(domain == d or domain.endswith("." + d) for d in excluded)


_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_fb_date(s):
    """Ad Library start date in English or Vietnamese -> date.

    'Nov 2, 2026', 'November 2, 2026', '2 Th11, 2026', '2 thg 11, 2026',
    'ngày 2 tháng 11 năm 2026', '02/11/2026'."""
    if not s:
        return None
    m = re.search(r"\b([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})", s)
    if m and m.group(1).lower() in _MONTHS:
        return _mkdate(int(m.group(3)), _MONTHS[m.group(1).lower()], int(m.group(2)))
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?,?\s+(\d{4})", s)
    if m and m.group(2).lower() in _MONTHS:
        return _mkdate(int(m.group(3)), _MONTHS[m.group(2).lower()], int(m.group(1)))
    nums = re.findall(r"\d+", s)
    for i, n in enumerate(nums):
        if len(n) == 4 and i >= 2:  # day, month, year (Vietnamese order)
            return _mkdate(int(n), int(nums[i - 1]), int(nums[i - 2]))
    return None


def _mkdate(y, mo, d):
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def days_since(d, today=None):
    if not d:
        return None
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return ((today or date.today()) - d).days


_MONEY = re.compile(r"([-+]?[$€£]?\s*[-+]?\d[\d,]*(?:\.\d+)?)\s*([kKmMbB])?")


def money_to_float(s):
    """'$45.2K' -> 45200.0, '$1,204,000' -> 1204000.0, otherwise None."""
    if not s:
        return None
    m = _MONEY.search(s)
    if not m:
        return None
    num = re.sub(r"[^\d.\-]", "", m.group(1))
    try:
        v = float(num)
    except ValueError:
        return None
    mult = {"k": 1e3, "m": 1e6, "b": 1e9}.get((m.group(2) or "").lower(), 1)
    return v * mult
