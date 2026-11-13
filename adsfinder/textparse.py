"""Turn the text of a ShopHunter box into label/value pairs."""
import re

_CHANGE = re.compile(r"^[▲▼↑↓+\-−]?\s*\d+(?:[.,]\d+)?\s*%(\s*(vs|from).*)?$", re.I)
_DATE = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b", re.I)


def looks_value(line):
    if len(line) > 40:
        return False
    if _DATE.search(line):
        return True
    return bool(re.search(r"\d", line)) or line.lower() in {"yes", "no", "n/a", "-", "—"}


def box_pairs(text, title=""):
    """Return [[label, value], ...]. Lines that pair with nothing get an empty label."""
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    if lines and title and lines[0].lower().startswith(title.lower()):
        lines = lines[1:]
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        if _CHANGE.match(line) and out and out[-1][0]:
            out[-1][1] = f"{out[-1][1]} ({line})"
            i += 1
        elif nxt is not None and not looks_value(line) and looks_value(nxt):
            out.append([line, nxt])
            i += 2
        elif ":" in line and len(line) < 80:
            k, v = line.split(":", 1)
            out.append([k.strip(), v.strip()])
            i += 1
        else:
            out.append(["", line])
            i += 1
    return out
