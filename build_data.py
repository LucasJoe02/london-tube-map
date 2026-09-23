"""Build data/network.js and data/boroughs.js from the raw TfL + borough files.

Re-fetch raw data with ./fetch_data.sh, then run: python3 build_data.py
"""
import heapq
import json
import math
from pathlib import Path

DATA = Path(__file__).parent / "data"

# Keyed by TfL hub id, so every line's platforms at the station count
# (e.g. Elizabeth line at Liverpool Street, DLR at Bank).
TARGETS = {
    "HUBOLD": "Old Street",
    "HUBZMG": "Moorgate",
    "HUBLST": "Liverpool Street",
    "HUBBAN": "Bank",
}

# Extra per-line destinations: the District line doesn't call at Bank, but
# Monument is connected to it underground. Times stop at Monument platforms.
LINE_TARGETS = {
    "district": {"940GZZLUMMT": "Monument (Bank)"},
}

LINES = {
    "northern": ("Northern", "#000000"),
    "central": ("Central", "#DC241F"),
    "circle": ("Circle", "#FFD329"),
    "hammersmith-city": ("Hammersmith & City", "#F4A9BE"),
    "metropolitan": ("Metropolitan", "#9B0058"),
    "waterloo-city": ("Waterloo & City", "#93CEBA"),
    "elizabeth": ("Elizabeth line", "#6950A1"),
    "dlr": ("DLR", "#00A4A7"),
    "weaver": ("Weaver line", "#823A62"),  # London Overground
    "district": ("District", "#007D32"),
}

# Rough journey-time model: fixed dwell/accel cost per hop plus running time.
DWELL_MIN = 0.8
MIN_PER_KM = 1.2  # ~50 km/h average running speed between stops
MIN_PER_KM_BY_LINE = {"elizabeth": 1.0}  # faster, longer-distance trains


def haversine_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def clean_name(name):
    for suffix in (" Underground Station", " DLR Station", " Rail Station", " (London)", " (Circle Line)", " (H&C Line)"):
        name = name.replace(suffix, "")
    return name.strip()


def station_key(sp):
    """Interchanges share one marker: group platforms by TfL hub where there is one."""
    parent = sp.get("topMostParentId") or sp["id"]
    return parent if parent.startswith("HUB") else sp["id"]


stations = {}  # output markers, keyed by station_key
nodes = {}     # raw stop id -> (lat, lon, station_key); graph nodes stay per platform
lines_out = {}

for line_id, (line_name, colour) in LINES.items():
    raw = json.loads((DATA / f"raw-{line_id}.json").read_text())

    for seq in raw["stopPointSequences"]:
        for sp in seq["stopPoint"]:
            key = station_key(sp)
            nodes[sp["id"]] = (sp["lat"], sp["lon"], key)
            stations.setdefault(key, {
                "id": key,
                "name": clean_name(sp["name"]),
                "lat": sp["lat"],
                "lon": sp["lon"],
                "zone": sp.get("zone"),
                "times": {},
            })

    # Adjacency graph for this line from its ordered routes.
    graph = {}
    for route in raw["orderedLineRoutes"]:
        ids = route["naptanIds"]
        for a, b in zip(ids, ids[1:]):
            if a not in nodes or b not in nodes:
                continue
            w = DWELL_MIN + MIN_PER_KM_BY_LINE.get(line_id, MIN_PER_KM) * haversine_km(nodes[a][:2], nodes[b][:2])
            graph.setdefault(a, {})[b] = w
            graph.setdefault(b, {})[a] = w

    # Multi-source Dijkstra from whichever target stations this line serves.
    dist, nearest = {}, {}
    heap = []
    extra = LINE_TARGETS.get(line_id, {})
    for n in graph:
        label = TARGETS.get(nodes[n][2]) or extra.get(nodes[n][2])
        if label:
            dist[n] = 0.0
            nearest[n] = label
            heapq.heappush(heap, (0.0, n))
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, math.inf):
            continue
        for v, w in graph.get(u, {}).items():
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                nearest[v] = nearest[u]
                heapq.heappush(heap, (nd, v))

    for nid, d in dist.items():
        times = stations[nodes[nid][2]]["times"]
        if line_id not in times or d < times[line_id]["min"]:
            times[line_id] = {"min": round(d, 1), "to": nearest[nid]}

    geometry = [json.loads(ls)[0] for ls in raw["lineStrings"]]  # [[lon, lat], ...]
    lines_out[line_id] = {
        "id": line_id,
        "name": line_name,
        "colour": colour,
        "geometry": [[[round(lat, 6), round(lon, 6)] for lon, lat in g] for g in geometry],
    }

network = {
    "targets": [{"id": k, "name": v, "lat": stations[k]["lat"], "lon": stations[k]["lon"]} for k, v in TARGETS.items()]
    + [{"id": k, "name": v, "lat": stations[k]["lat"], "lon": stations[k]["lon"], "secondary": True}
       for per_line in LINE_TARGETS.values() for k, v in per_line.items()],
    "lines": lines_out,
    "stations": sorted(stations.values(), key=lambda s: s["name"]),
}
(DATA / "network.js").write_text("window.NETWORK = " + json.dumps(network, separators=(",", ":")) + ";\n")


def round_coords(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 5), round(c[1], 5)]
    return [round_coords(x) for x in c]


boroughs = json.loads((DATA / "boroughs-raw.geojson").read_text())
for f in boroughs["features"]:
    f["properties"] = {"name": f["properties"]["name"]}
    f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"])
(DATA / "boroughs.js").write_text("window.BOROUGHS = " + json.dumps(boroughs, separators=(",", ":")) + ";\n")

print(f"{len(stations)} stations, {len(lines_out)} lines, {len(boroughs['features'])} boroughs")
missing = [t for t in TARGETS if t not in stations]
print("missing targets:", missing or "none")
