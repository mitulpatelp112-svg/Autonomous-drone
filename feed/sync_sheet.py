#!/usr/bin/env python3
"""Pull the drone build workbook from SharePoint and write feed/data.json.

Read-only: the workbook is downloaded and parsed, never written back.

    python3 feed/sync_sheet.py            # download + parse
    python3 feed/sync_sheet.py local.xlsx # parse a local copy instead
"""
import datetime as dt
import hashlib
import http.cookiejar
import io
import json
import os
import re
import sys
import urllib.request

import openpyxl

SHARE_URL = (
    "https://studentuncc-my.sharepoint.com/:x:/g/personal/mpate183_charlotte_edu/"
    "IQDsuxazQJ82SpIsXuKB2604AWyWIvZJR2nDEfddNOIa2ec?e=Zj4fVf&download=1"
)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def download():
    # SharePoint sets an auth cookie on the redirect, so keep a cookie jar.
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    opener.addheaders = [("User-Agent", "Mozilla/5.0 drone-feed-sync")]
    with opener.open(SHARE_URL, timeout=60) as resp:
        body = resp.read()
        name = os.path.basename(urllib.request.unquote(resp.geturl().split("?")[0]))
        return body, name, resp.headers.get("Last-Modified")


def clean(v):
    if v is None:
        return None
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def rows_of(ws):
    out = []
    for r in ws.iter_rows(values_only=True):
        r = [clean(c) for c in r]
        while r and r[-1] is None:
            r.pop()
        out.append(r)
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def find_header(rows, *needles):
    """Index of the first row containing every needle (case-insensitive)."""
    for i, r in enumerate(rows):
        cells = [norm(c) for c in r if c is not None]
        if all(any(n in c for c in cells) for n in needles):
            return i
    return None


def col_map(header, wanted):
    m = {}
    for key, needles in wanted.items():
        for j, h in enumerate(header):
            if h is not None and any(n in norm(h) for n in needles):
                m[key] = j
                break
    return m


def get(r, m, key):
    j = m.get(key)
    return r[j] if j is not None and j < len(r) else None


def parse_master(rows):
    h = find_header(rows, "system", "component")
    if h is None:
        return None
    m = col_map(rows[h], {
        "system": ["system"], "pick": ["pick"], "component": ["component"],
        "specs": ["spec"], "weight_g": ["weight"], "unit_price": ["unit price"],
        "qty": ["qty"], "line_total": ["line total"], "compat": ["compatib"],
        "source": ["source", "link"],
    })
    title = next((r[0] for r in rows[:h] if r and r[0]), None)
    mission = next((r[0] for r in rows[:h] if r and r[0] and "mission" in norm(r[0])), None)
    items, subtotal = [], None
    for r in rows[h + 1:]:
        if not any(c is not None for c in r):
            continue
        first = norm(r[0] if r else "")
        if "subtotal" in first or "total" in first and not get(r, m, "component"):
            subtotal = next((c for c in r[1:] if isinstance(c, (int, float))), None)
            continue
        if not get(r, m, "component"):
            continue
        items.append({k: get(r, m, k) for k in m})
    return {"title": title, "mission": mission, "items": items, "subtotal": subtotal}


def parse_cart(rows):
    h = find_header(rows, "component", "link")
    if h is None:
        return None
    m = col_map(rows[h], {"component": ["component"], "link": ["link"], "specs": ["spec"]})
    items = []
    for r in rows[h + 1:]:
        if get(r, m, "component"):
            items.append({k: get(r, m, k) for k in m})
    return {"items": items}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_motor(rows):
    h = find_header(rows, "voltage", "pull")
    if h is None:
        return None
    hdr = [norm(c) for c in rows[h]]
    # Two "current" columns: the first is no-load current, the second is load current.
    cur = [j for j, c in enumerate(hdr) if c.startswith("current")]
    idx = lambda key: next((j for j, c in enumerate(hdr) if c.startswith(key)), None)
    cols = {
        "v": idx("voltage"), "rpm": idx("rpm"), "pull": idx("pull"), "power": idx("power"),
        "prop": idx("battery") if idx("battery") is not None else idx("prop"),
        "i0": cur[0] if len(cur) > 1 else None, "i": cur[-1] if cur else None,
    }
    pts = []
    for r in rows[h + 1:]:
        p = {k: (r[j] if j is not None and j < len(r) else None) for k, j in cols.items()}
        if num(p["v"]) is None or num(p["pull"]) is None or num(p["i"]) is None:
            continue
        pts.append({
            "v": num(p["v"]), "i0": num(p["i0"]), "rpm": num(p["rpm"]),
            "i": num(p["i"]), "pull": num(p["pull"]), "power": num(p["power"]),
            "prop": str(p["prop"] or "").replace(" Prop", "").strip(),
        })
    return {"points": pts}


def parse_efficiency(rows):
    h = find_header(rows, "voltage", "propeller", "combo")
    if h is None:
        h = find_header(rows, "voltage", "propeller", "low")
    if h is None:
        return None
    hdr = [norm(c) for c in rows[h]]
    j_combo = next((j for j, c in enumerate(hdr) if c == "combo"), None)
    j_rank = next((j for j, c in enumerate(hdr) if c == "rank"), None)
    choice, best = None, None
    for r in rows[h + 1:]:
        if num(r[0] if r else None) is None:
            break
        combo = {"v": num(r[0]), "prop": str(r[1] or "").replace(" Prop", "").strip()}
        note = next((c for c in r[(j_combo or 0) + 1:] if isinstance(c, str)), None)
        if note:
            choice = dict(combo, note=note)
        if j_rank is not None and j_rank < len(r) and num(r[j_rank]) == 1:
            best = combo
    return {"choice": choice, "best": best}


def main():
    if len(sys.argv) > 1:
        body = open(sys.argv[1], "rb").read()
        name, modified = os.path.basename(sys.argv[1]), None
    else:
        body, name, modified = download()
    if not body.startswith(b"PK"):
        sys.exit("Download did not return an .xlsx file (sharing link expired or access denied?)")
    wb = openpyxl.load_workbook(io.BytesIO(body), data_only=True)

    sheets = {ws.title.strip(): rows_of(ws) for ws in wb.worksheets}
    pick = lambda *keys: next((v for k, v in sheets.items() if any(x in norm(k) for x in keys)), [])
    data = {
        "source": {
            "file": name,
            "share_url": SHARE_URL.replace("&download=1", ""),
            "modified": modified,
            "sha256": hashlib.sha256(body).hexdigest()[:16],
            "synced_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "sheets": list(sheets),
        },
        "master": parse_master(pick("master", "build")),
        "cart": parse_cart(pick("cart")),
        "motor": parse_motor(pick("motor")),
        "efficiency": parse_efficiency(pick("efficien")),
    }
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print(f"Wrote {OUT}: {name}, sheets={list(sheets)}, sha={data['source']['sha256']}")


if __name__ == "__main__":
    main()
