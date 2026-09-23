"""Fetch furnished 2-bed whole-property rentals near the mapped stations.

Writes data/listings.js. Run after build_data.py: python3 fetch_listings.py

Sources:
- OpenRent: its public search page embeds every London listing (id, lat/lon, price,
  filter flags); titles come from /search/propertiesbyid, 20 at a time.
- Rightmove: search result pages (/property-to-rent/find.html, allowed by robots.txt)
  embed 24 listings each as JSON. Rightmove caps a search at ~1,000 results, so we
  query in price bands. Note Rightmove's terms restrict use of this data to Rightmove.
Requests are rate-limited. If one source fails, its listings from the previous run are kept.
"""
import datetime
import json
import math
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA = Path(__file__).parent / "data"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

MAX_RENT = 3000        # pcm; above this even a per-head split busts the single's budget
MAX_DIST_M = 1000      # walking circles are 800 m; allow a little slack ("or thereabouts")

# Budget model (see README): rent split 40/60 single/couple, bills split per head.
SINGLE_BUDGET = 1000
BUDGET_SLACK = 50      # "around £1,000"
SINGLE_RENT_SHARE = 0.40
EST_BILLS_PCM = 370    # 2-bed, 3 adults: council tax ~150, energy ~130, water ~45, broadband ~30, TV ~15


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def js_array(src, name):
    m = re.search(r"%s = \[(.*?)\];" % name, src, re.S)
    return json.loads("[" + m.group(1).strip().rstrip(",") + "]")


def haversine_m(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


BILLS_YES = re.compile(r"(bills?|utilities)\s+(are\s+)?(all\s+)?included|(inclusive of|including|incl\.?)\s+(all\s+)?(bills|utilities)|all[- ]inclusive|bills inc\b", re.I)
BILLS_NO = re.compile(r"(bills?|utilities)\s+(are\s+)?(not|excluded)|(excluding|exclusive of|excl\.?)\s+(bills|utilities)", re.I)
# "Rent with all bills included is £2,850" = bills are an optional extra on top of the listed rent.
BILLS_OPTIONAL = re.compile(r"bills\s+included\s+(is|for|at|from|would be)\s*£|£[\d,]+\s*(pcm\s*)?(with|including|incl?\.?)\s+(all\s+)?bills|bills\s+can\s+be\s+included|option(al)?\s+to\s+include\s+bills", re.I)
ROOM_SHARE = re.compile(r"\b(double room|single room|en-?suite room|room (to rent|available|in a)|rooms? to let|house ?share|flat ?share|shared (house|flat|accommodation)|co-?living)\b", re.I)


def bills_from_text(text):
    """True/False if the text says so, None if bills aren't mentioned."""
    if BILLS_NO.search(text) or BILLS_OPTIONAL.search(text):
        return False
    if BILLS_YES.search(text):
        return True
    return None


def budget(price, bills_included):
    bills = 0 if bills_included else EST_BILLS_PCM
    single_rent = price * SINGLE_RENT_SHARE
    single_all_in = single_rent + bills / 3
    per_head_all_in = price / 3 + bills / 3
    limit = SINGLE_BUDGET + BUDGET_SLACK
    if single_all_in <= limit:
        tier = "in"            # within budget including (estimated) bills at a 40/60 split
    elif single_rent <= limit:
        tier = "rent"          # rent share fits; estimated bills push it over
    elif per_head_all_in <= limit:
        tier = "perhead"       # only fits if the couple pays two-thirds
    else:
        tier = None
    return {
        "tier": tier,
        "singleRent": round(single_rent),
        "singleAllIn": round(single_all_in),
        "coupleRent": round(price - single_rent),
        "coupleAllIn": round(price - single_rent + bills * 2 / 3),
        "perHeadAllIn": round(per_head_all_in),
    }


def nearest_station(stations, lat, lon):
    dist, st = min(((haversine_m(lat, lon, s["lat"], s["lon"]), s) for s in stations), key=lambda t: t[0])
    best_line, best = min(st["times"].items(), key=lambda kv: kv[1]["min"])
    return {"station": st["name"], "stationDistM": round(dist), "stationMin": best["min"],
            "stationLine": best_line, "stationTo": best["to"]}


def fetch_openrent(stations):
    page = get("https://www.openrent.co.uk/properties-to-rent/london?term=London")
    cols = {n: js_array(page, n) for n in (
        "PROPERTYIDS", "PROPERTYLISTLATITUDES", "PROPERTYLISTLONGITUDES", "islivelistBool", "prices",
        "bedrooms", "bathrooms", "isshared", "isstudio", "furnished", "bills", "propertyTypes",
        "availableFrom", "minimumTenancy")}
    print(f"OpenRent London listings: {len(cols['PROPERTYIDS'])}")

    candidates = []
    for i, pid in enumerate(cols["PROPERTYIDS"]):
        if not (cols["islivelistBool"][i] == 1 and cols["bedrooms"][i] == 2 and cols["furnished"][i] == 1
                and cols["isshared"][i] == 0 and cols["isstudio"][i] == 0 and cols["prices"][i] <= MAX_RENT):
            continue
        lat, lon = cols["PROPERTYLISTLATITUDES"][i], cols["PROPERTYLISTLONGITUDES"][i]
        near = nearest_station(stations, lat, lon)
        if near["stationDistM"] > MAX_DIST_M:
            continue
        b = budget(cols["prices"][i], cols["bills"][i] == 1)
        if not b["tier"]:
            continue
        candidates.append({
            "id": f"or-{pid}", "_pid": pid, "lat": lat, "lon": lon, "price": cols["prices"][i],
            "billsIncluded": cols["bills"][i] == 1, "billsStated": True, "bathrooms": cols["bathrooms"][i],
            "availableInDays": cols["availableFrom"][i], "minTenancyMonths": cols["minimumTenancy"][i],
            **near, **b,
        })

    details = {}
    ids = [c["_pid"] for c in candidates]
    for k in range(0, len(ids), 20):
        q = "&".join(f"ids={i}" for i in ids[k:k + 20])
        for d in json.loads(get("https://www.openrent.co.uk/search/propertiesbyid?" + q)):
            details[d["id"]] = d
        time.sleep(1.0)

    listings = []
    for c in candidates:
        d = details.get(c.pop("_pid"))
        if not d or d.get("letAgreed"):
            continue
        listings.append({
            **c,
            "title": d["title"],
            "summary": re.sub(r"\s+", " ", d.get("description", "")).strip(),
            "furnishing": next((x for x in d.get("details", []) if "urnish" in x), "Furnished"),
            "image": ("https:" + d["imageUrl"]) if d.get("imageUrl", "").startswith("//") else d.get("imageUrl"),
            "url": f"https://www.openrent.co.uk/{c['id'][3:]}",
            "source": "OpenRent",
            "updated": d.get("lastUpdated"),
        })
    print(f"OpenRent: {len(listings)} near stations and in budget range")
    return listings


RIGHTMOVE_BANDS = [(None, 2000), (2000, 2250), (2250, 2500), (2500, 2750), (2750, MAX_RENT)]


def rightmove_page(min_price, max_price, index):
    params = {
        "locationIdentifier": "REGION^87490",  # London
        "minBedrooms": 2, "maxBedrooms": 2, "maxPrice": max_price,
        "furnishTypes": "furnished", "propertyTypes": "flat,detached,semi-detached,terraced",
        "includeLetAgreed": "false", "index": index,
    }
    if min_price:
        params["minPrice"] = min_price
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?" + urllib.parse.urlencode(params)
    html = get(url)
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1))["props"]["pageProps"]["searchResults"]


def fetch_rightmove(stations):
    raw = {}
    for lo, hi in RIGHTMOVE_BANDS:
        index, band_count = 0, None
        while True:
            res = rightmove_page(lo, hi, index)
            band_count = res.get("resultCount")
            for p in res["properties"]:
                raw[p["id"]] = p
            nxt = (res.get("pagination") or {}).get("next")
            time.sleep(1.5)
            if not nxt or int(nxt) <= index:
                break
            index = int(nxt)
        print(f"  Rightmove £{lo or 0}-{hi}: {band_count} results")
    print(f"Rightmove unique listings fetched: {len(raw)}")

    listings, skipped = [], {"far": 0, "budget": 0, "share": 0, "students": 0, "openrent": 0}
    for p in raw.values():
        if p.get("students"):
            skipped["students"] += 1
            continue
        if "openrent" in (p.get("formattedBranchName") or "").lower():
            skipped["openrent"] += 1
            continue
        price = p["price"]["amount"]
        if p["price"].get("frequency") == "weekly":
            price = round(price * 52 / 12)
        if p.get("bedrooms") != 2 or price > MAX_RENT:
            continue
        text = " ".join([p.get("summary") or "", p.get("propertyTypeFullDescription") or ""]
                        + [f.get("description", "") for f in p.get("keyFeatures") or []])
        if ROOM_SHARE.search(text):
            skipped["share"] += 1
            continue
        lat, lon = p["location"]["latitude"], p["location"]["longitude"]
        near = nearest_station(stations, lat, lon)
        if near["stationDistM"] > MAX_DIST_M:
            skipped["far"] += 1
            continue
        bills = bills_from_text(text)
        b = budget(price, bills is True)
        if not b["tier"]:
            skipped["budget"] += 1
            continue
        img = (p.get("propertyImages") or {}).get("images") or p.get("images") or []
        listings.append({
            "id": f"rm-{p['id']}", "lat": lat, "lon": lon, "price": price,
            "billsIncluded": bills is True, "billsStated": bills is not None,
            "bathrooms": p.get("bathrooms"),
            "availableInDays": None, "minTenancyMonths": None,
            **near, **b,
            "title": f"{p.get('propertyTypeFullDescription', '2 bedroom property').capitalize()}, {p.get('displayAddress', '')}",
            "summary": re.sub(r"\s+", " ", p.get("summary") or "").strip(),
            "furnishing": "Furnished",
            "image": img[0]["srcUrl"] if img else None,
            "url": "https://www.rightmove.co.uk/properties/" + str(p["id"]),
            "source": "Rightmove",
            "agent": (p.get("formattedBranchName") or "").replace(" by ", "", 1).strip(),
            "updated": p.get("addedOrReduced"),
        })
    print(f"Rightmove: {len(listings)} near stations and in budget range; skipped {skipped}")
    return listings


def dedupe(listings):
    """Drop repeats: same source listed twice, or the same flat on both sites (same price, <150 m apart)."""
    kept = []
    for l in sorted(listings, key=lambda l: l["source"] != "OpenRent"):  # prefer OpenRent's richer flags
        if any(k["price"] == l["price"] and haversine_m(k["lat"], k["lon"], l["lat"], l["lon"]) < 150
               and (k["source"] != l["source"] or k["title"] == l["title"]) for k in kept):
            continue
        kept.append(l)
    return kept


def previous_listings(source):
    """Listings for `source` from the last successful run, so one site failing doesn't wipe the map."""
    path = DATA / "listings.js"
    if not path.exists():
        return [], None
    prev = json.loads(path.read_text()[len("window.LISTINGS = "):-2])
    return [l for l in prev["listings"] if l["source"] == source], prev.get("sources", {}).get(source, prev.get("fetched"))


def main():
    network = json.loads((DATA / "network.js").read_text()[len("window.NETWORK = "):-2])
    stations = network["stations"]
    today = datetime.date.today().isoformat()

    listings, sources, failed = [], {}, []
    for name, fetch in (("OpenRent", fetch_openrent), ("Rightmove", fetch_rightmove)):
        try:
            got = fetch(stations)
            if not got:
                raise RuntimeError("returned no listings")
            listings += got
            sources[name] = today
        except Exception as e:  # blocked, page format changed, network error...
            old, when = previous_listings(name)
            print(f"WARNING: {name} fetch failed ({e!r}); keeping {len(old)} listings from {when}")
            listings += old
            sources[name] = when
            failed.append(name)

    before = len(listings)
    listings = dedupe(listings)
    print(f"Removed {before - len(listings)} duplicates")

    listings.sort(key=lambda l: l["price"])
    out = {
        "fetched": max((d for d in sources.values() if d), default=today),
        "sources": sources,
        "model": {"singleBudget": SINGLE_BUDGET, "slack": BUDGET_SLACK, "singleRentShare": SINGLE_RENT_SHARE,
                  "estBills": EST_BILLS_PCM, "maxDistM": MAX_DIST_M},
        "listings": listings,
    }
    (DATA / "listings.js").write_text("window.LISTINGS = " + json.dumps(out, separators=(",", ":")) + ";\n")
    from collections import Counter
    print(f"Wrote {len(listings)} listings:", dict(Counter((l["source"], l["tier"]) for l in listings)))
    if len(failed) == 2:
        raise SystemExit("Both sources failed")


if __name__ == "__main__":
    main()
