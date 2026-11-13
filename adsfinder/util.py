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


def parse_fb_date(s):
    """'Nov 2, 2026' or 'November 2, 2026' -> date."""
    if not s:
        return None
    s = s.replace(".", "").strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
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
