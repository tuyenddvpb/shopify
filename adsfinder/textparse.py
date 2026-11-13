"""Turn the text of a ShopHunter box into [label, value, change] rows.

ShopHunter prints the value above its label, sometimes with a change line:
    $2197.60 / +109.7 (+5.3%) / Day / $15K / -40K (-71.5%) / Week ...
    US / Country / 6/12/2024 / Store Creation Date ...
Other layouts (label above value, "Label: value") are handled too.
"""
import re

_CHANGE = re.compile(r"^[▲▼↑↓+\-−]\s*[$€£]?\d[\d.,]*\s*[kKmMbB]?\s*(\([+\-−]?\d[\d.,]*\s*%\))?$|^[▲▼↑↓+\-−]?\s*\d+(?:[.,]\d+)?\s*%$")
_DATE = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b", re.I)


def is_change(line):
    return bool(_CHANGE.match(line.strip()))


def looks_value(line):
    line = line.strip()
    if len(line) > 40:
        return False
    if re.search(r"\d", line) or _DATE.search(line):
        return True
    if re.fullmatch(r"[A-Z]{2,3}", line):           # US, USD
        return True
    return line.lower() in {"yes", "no", "n/a", "na", "-", "—", "none"}


def box_pairs(text, title=""):
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    if lines and title and lines[0].lower().startswith(title.lower()):
        lines = lines[1:]
    if not lines:
        return []
    if looks_value(lines[0]) and not looks_value(lines[-1]):
        return _value_first(lines)
    return _label_first(lines)


def _value_first(lines):
    out, buf = [], []
    for line in lines:
        if looks_value(line) or is_change(line):
            buf.append(line)
            continue
        if buf:
            value = buf[0]
            change = " ".join(buf[1:])
            out.append([line, value, change])
            buf = []
        else:
            out.append(["", line, ""])
    out.extend(["", v, ""] for v in buf)
    return out


def _label_first(lines):
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        if is_change(line) and out and out[-1][0]:
            out[-1][2] = (out[-1][2] + " " + line).strip()
            i += 1
        elif nxt is not None and not looks_value(line) and looks_value(nxt):
            out.append([line, nxt, ""])
            i += 2
        elif ":" in line and len(line) < 80:
            k, v = line.split(":", 1)
            out.append([k.strip(), v.strip(), ""])
            i += 1
        else:
            out.append(["", line, ""])
            i += 1
    return out
